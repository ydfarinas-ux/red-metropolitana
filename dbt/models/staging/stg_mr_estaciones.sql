-- Catálogo MetroRiel: 22 estaciones con id numérico, de Centra Sur (1) a Centra Norte (22).
select cast(id_estacion as varchar) as estacion_id, 'MetroRiel' as agrupador, nombre_estacion as nombre,
       zona_nombre as zona_origen, try_cast(id_estacion as integer) as orden,
       null::double as lat, null::double as lon, _source_file, _ingested_at
from {{ source('bronze', 'mr_estaciones') }}
qualify row_number() over (partition by id_estacion order by _ingested_at desc) = 1
