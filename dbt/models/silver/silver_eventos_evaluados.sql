-- Todos los eventos de operación en un esquema común, con cada regla de calidad evaluada.
-- De aquí salen: silver_cuarentena (motivo_rechazo no nulo), silver_abordajes, silver_trayectos_metroriel
-- y silver_transacciones_rechazadas_tu.
with todos as (
    select * from {{ ref('stg_tm_validaciones') }}
    union all by name select * from {{ ref('stg_tu_transacciones') }}
    union all by name select * from {{ ref('stg_mr_viajes') }}
    union all by name select * from {{ ref('stg_am_boardings') }}
),
u as (   -- momento de ingesta del ARCHIVO (en streaming cada mensaje trae su propia hora)
    select *, min(_ingested_at) over (partition by sistema, _file_hash) as _ingesta_archivo from todos
),
base as (
    select u.*,
        (u._ingested_at at time zone 'UTC') at time zone 'America/Guatemala' as ingesta_local,
        e.estacion_key is not null                                     as estacion_en_catalogo,
        e.zona_key,
        es.zona_key                                                    as salida_zona_key,
        u.salida_estacion_id is null or es.estacion_key is not null    as salida_en_catalogo,
        -- repetición del mismo evento: en OTRO archivo = reingesta; en el MISMO archivo = torniquete
        dense_rank()  over (partition by u.sistema, u.evento_id order by u._ingesta_archivo, u._file_hash) as n_archivo,
        row_number()  over (partition by u.sistema, u.evento_id, u._file_hash order by u._linea, u.payload) as n_en_archivo
    from u
    left join {{ ref('silver_estaciones') }} e  on e.estacion_key  = u.sistema || ':' || u.estacion_id
    left join {{ ref('silver_estaciones') }} es on es.estacion_key = u.sistema || ':' || u.salida_estacion_id
)
select *,
    -- UNA regla por registro, en orden de prioridad (la primera que falla es el motivo)
    case
        when n_archivo > 1                                      then 'DUPLICADO_REINGESTA'
        when n_en_archivo > 1                                   then 'DUPLICADO_TORNIQUETE'
        when usuario_llave_origen is null or trim(usuario_llave_origen) = '' then 'USUARIO_NULO'
        when estacion_id is null                                then 'PARADA_NULA'
        when not estacion_en_catalogo                           then 'ESTACION_DESCONOCIDA'
        when ts_local is null                                   then 'FECHA_INVALIDA'
        when ts_local > ingesta_local                           then 'FECHA_FUTURA'
        when sistema = 'MR' and (salida_estacion_id is null or salida_ts_local is null) then 'VIAJE_SIN_SALIDA'
        when sistema = 'MR' and (salida_ts_local <= ts_local or not salida_en_catalogo
                                 or salida_estacion_id = estacion_id)                  then 'SALIDA_INCONSISTENTE'
        when zona_key is null                                   then 'ZONA_INVALIDA'
        when monto_q is null or monto_q < 0                     then 'MONTO_INVALIDO'
        when tipo_evento = 'ESTADO_DESCONOCIDO'                 then 'ESTADO_DESCONOCIDO'
    end as motivo_rechazo
from base
