-- GRANO: una fila por cada abordaje (validación de entrada) de un usuario en una estación de cualquiera de los cuatro sistemas.
select
    row_number() over (order by a.abordaje_id)   as abordaje_key,
    a.abordaje_id                                as abordaje_id_origen,    -- dimensión degenerada
    a.tipo_validacion,                                                      -- degenerada: ENTRADA/TRANSBORDO (TM), cabina (AM), estado (TU)
    cast(strftime(a.fecha, '%Y%m%d') as integer) * 100 + a.hora as tiempo_key,
    cast(strftime(a.fecha, '%Y%m%d') as integer) as fecha_key,
    a.usuario_sk,
    s.sistema_key,
    e.estacion_key,
    a.zona_key,
    a.ts_local                                   as fecha_hora_local,
    1                                            as cantidad_abordajes,     -- aditiva
    a.monto_q                                                               -- aditiva
from {{ ref('silver_abordajes') }} a
join {{ ref('dim_sistema') }} s  on s.sistema_codigo = a.sistema
join {{ ref('dim_estacion') }} e on e.estacion_codigo = a.estacion_key
