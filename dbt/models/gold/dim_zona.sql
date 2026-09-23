-- Dimensión zona conformada (zonas de la ciudad y municipios) + cobertura: qué modos tienen estación en cada una.
with cob as (
    select zona_key,
        bool_or(sistema = 'TM') as tiene_transmetro, bool_or(sistema = 'TU') as tiene_transurbano,
        bool_or(sistema = 'MR') as tiene_metroriel,  bool_or(sistema = 'AM') as tiene_aerometro,
        count(distinct sistema) as modos_con_estacion, count(*) as estaciones
    from {{ ref('silver_estaciones') }} where zona_key is not null group by 1
)
select z.zona_key, z.nombre_oficial as nombre_zona, z.tipo_territorio, z.municipio,
       coalesce(tiene_transmetro, false) as tiene_transmetro, coalesce(tiene_transurbano, false) as tiene_transurbano,
       coalesce(tiene_metroriel, false)  as tiene_metroriel,  coalesce(tiene_aerometro, false)  as tiene_aerometro,
       coalesce(modos_con_estacion, 0) as modos_con_estacion, coalesce(estaciones, 0) as estaciones,
       coalesce(modos_con_estacion, 0) > 0 as tiene_servicio,
       z.nombre_oficial in ('Zona 12', 'Zona 8', 'Zona 1', 'Zona 6', 'Zona 17') as en_trazado_metroriel
from {{ ref('silver_zona') }} z left join cob using (zona_key)
