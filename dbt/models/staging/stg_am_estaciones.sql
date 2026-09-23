-- Catálogo Aerómetro: 2 ejes, 7 torres cada uno. Columnas en inglés; 'district' trae 'Zona 7' o 'Mixco'.
select station_code as estacion_id, axis as agrupador, station_name as nombre, district as zona_origen,
       null::integer as orden, null::double as lat, null::double as lon, _source_file, _ingested_at
from {{ source('bronze', 'am_estaciones') }}
qualify row_number() over (partition by station_code order by _ingested_at desc) = 1
