-- 1.2 Padrón vigente: una fila por tarjeta, resultado de aplicar el log de CDC en orden de secuencia.
-- DELETE = baja lógica (activa = false). La tarjeta NO se borra: si se borrara, se perdería el historial de sus viajes.
-- El log mezcla tarjetas de TM, TU y MR: operador_tarjeta dice de quién es cada una (ver decisión en docs/1.2-staging-cdc.md).
with aplicadas as (
    select *,
        -- el DELETE llega sin cuerpo: se arrastra el último valor conocido de cada atributo
        last_value(perfil ignore nulls) over w                  as perfil_f,
        last_value(zona_residencia_origen ignore nulls) over w  as zona_residencia_f,
        count(*) over (partition by tarjeta)                    as operaciones_aplicadas,
        row_number() over (partition by tarjeta order by secuencia desc) as rn_desc
    from {{ ref('cdc_operaciones') }}
    where motivo_no_aplicada is null
    window w as (partition by tarjeta order by secuencia rows between unbounded preceding and current row)
)
select
    a.tarjeta, a.operador_tarjeta,
    'P' || cast(a.numero_persona as varchar)                    as persona_id,
    a.perfil_f                                                  as perfil,
    t.zona_key                                                  as zona_residencia_key,
    a.zona_residencia_f                                         as zona_residencia_origen,
    a.activa_tras                                               as activa,
    case when not a.activa_tras then a.ts_operacion end         as fecha_baja,
    a.operacion                                                 as ultima_operacion,
    a.secuencia                                                 as ultima_secuencia,
    a.ts_operacion                                              as ultima_actualizacion,
    a.operaciones_aplicadas
from aplicadas a
left join {{ ref('territorios') }} t on t.clave_normalizada = {{ normalizar_territorio('a.zona_residencia_f') }}
where a.rn_desc = 1
