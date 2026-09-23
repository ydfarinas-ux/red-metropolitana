-- GRANO: una fila por día, zona de residencia, perfil y operador de la tarjeta del padrón (snapshot periódico).
-- tarjetas_activas es SEMI-ADITIVA: se suma entre zonas, perfiles u operadores, NUNCA entre días.
with v as (select * from {{ ref('silver_padron_scd2') }}),
rango as (select min(cast(valido_desde as date)) as ini, max(cast(valido_desde as date)) as fin from v),
dias as (select f.fecha_key, f.fecha from {{ ref('dim_fecha') }} f, rango where f.fecha between rango.ini and rango.fin)
select
    d.fecha_key,
    coalesce(v.zona_residencia_key, -1)                        as zona_key,        -- -1 = zona desconocida
    coalesce(v.perfil, 'desconocido')                          as perfil,
    v.operador_tarjeta,
    count(*) filter (where v.activa)                           as tarjetas_activas,   -- semi-aditiva
    count(*) filter (where v.operacion_origen = 'INSERT' and cast(v.valido_desde as date) = d.fecha) as altas_del_dia,  -- aditiva
    count(*) filter (where v.operacion_origen = 'DELETE' and cast(v.valido_desde as date) = d.fecha) as bajas_del_dia   -- aditiva
from dias d
join v on v.valido_desde < d.fecha + interval 1 day and v.valido_hasta >= d.fecha + interval 1 day
group by all
