-- Catálogo Transurbano: 41 rutas, "paradas" (no estaciones). Zona en columna 'sector', MAYÚSCULAS y sin "Zona": 'Z4', 'MIXCO'.
select cod_parada as estacion_id, ruta as agrupador, descripcion as nombre, sector as zona_origen, null::integer as orden,
       null::double as lat, null::double as lon, _source_file, _ingested_at
from {{ source('bronze', 'tu_paradas') }}
qualify row_number() over (partition by cod_parada order by _ingested_at desc) = 1
