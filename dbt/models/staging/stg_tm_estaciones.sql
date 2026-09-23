-- Catálogo Transmetro: 8 líneas, 13 estaciones cada una. Zona escrita 'Zona 4' o nombre de municipio.
select estacion_id, linea as agrupador, nombre, zona as zona_origen, null::integer as orden,
       try_cast(lat as double) as lat, try_cast(lon as double) as lon, _source_file, _ingested_at
from {{ source('bronze', 'tm_estaciones') }}
qualify row_number() over (partition by estacion_id order by _ingested_at desc) = 1   -- versión más reciente del catálogo
