-- Padrón historizado con SCD Tipo 2: una fila por VERSIÓN de cada tarjeta.
-- Cada operación APLICADA del CDC abre una versión y cierra la anterior. El DELETE abre una versión con activa = false.
with ops as (
    select *,
        last_value(perfil ignore nulls) over w                  as perfil_f,
        last_value(zona_residencia_origen ignore nulls) over w  as zona_residencia_f
    from {{ ref('cdc_operaciones') }}
    where motivo_no_aplicada is null
    window w as (partition by tarjeta order by secuencia rows between unbounded preceding and current row)
)
select
    o.tarjeta || '#' || row_number() over (partition by o.tarjeta order by o.secuencia) as version_key,
    o.tarjeta, o.operador_tarjeta,
    i.usuario_sk,
    row_number() over (partition by o.tarjeta order by o.secuencia)            as version,
    o.perfil_f as perfil,
    t.zona_key as zona_residencia_key,
    o.activa_tras                                                              as activa,
    o.operacion                                                                as operacion_origen,
    o.observacion,
    o.secuencia,
    o.ts_operacion                                                             as valido_desde,
    coalesce(lead(o.ts_operacion) over (partition by o.tarjeta order by o.secuencia),
             timestamp '9999-12-31 23:59:59')                                  as valido_hasta,
    lead(o.ts_operacion) over (partition by o.tarjeta order by o.secuencia) is null as es_vigente
from ops o
left join {{ ref('territorios') }} t on t.clave_normalizada = {{ normalizar_territorio('o.zona_residencia_f') }}
left join {{ ref('silver_identidad_usuario') }} i on i.sistema = o.operador_tarjeta and i.llave_origen = o.tarjeta
