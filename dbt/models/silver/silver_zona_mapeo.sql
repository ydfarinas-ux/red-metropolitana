-- Evidencia de la conformación: cada forma en que una fuente escribe la zona -> el territorio oficial.
-- 'Zona 10' (TM, MR, AM), 'Z10' (TU), 'MIXCO' (TU) y 'Mixco' (TM, AM, CDC) apuntan al mismo zona_key.
with valores as (
    select distinct 'TM' as fuente, zona_origen as valor from {{ ref('stg_tm_estaciones') }}
    union select 'TU', zona_origen from {{ ref('stg_tu_paradas') }}
    union select 'MR', zona_origen from {{ ref('stg_mr_estaciones') }}
    union select 'AM', zona_origen from {{ ref('stg_am_estaciones') }}
    union select 'CDC', zona_residencia_origen from {{ ref('stg_cdc_padron') }}
)
select v.fuente, v.valor as valor_origen, {{ normalizar_territorio('v.valor') }} as clave_normalizada,
       t.zona_key, t.nombre_oficial, t.zona_key is not null as es_valida
from valores v
left join {{ ref('territorios') }} t on t.clave_normalizada = {{ normalizar_territorio('v.valor') }}
where v.valor is not null
