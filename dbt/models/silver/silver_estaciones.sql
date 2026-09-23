-- Catálogo único de estaciones y paradas de los cuatro sistemas, con zona conformada.
-- Los archivos de operación NO traen zona: la zona de un abordaje es la zona de su estación.
with u as (
    select 'TM' as sistema, * from {{ ref('stg_tm_estaciones') }}
    union all by name select 'TU' as sistema, * from {{ ref('stg_tu_paradas') }}
    union all by name select 'MR' as sistema, * from {{ ref('stg_mr_estaciones') }}
    union all by name select 'AM' as sistema, * from {{ ref('stg_am_estaciones') }}
)
select
    u.sistema || ':' || u.estacion_id       as estacion_key,
    u.sistema, u.estacion_id                as estacion_id_origen,
    u.nombre, u.agrupador, u.orden, u.lat, u.lon,
    u.zona_origen, t.zona_key,
    u._source_file
from u
left join {{ ref('territorios') }} t on t.clave_normalizada = {{ normalizar_territorio('u.zona_origen') }}
