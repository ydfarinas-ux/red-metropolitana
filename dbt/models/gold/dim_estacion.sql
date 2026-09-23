select row_number() over (order by e.estacion_key) as estacion_key,
       e.estacion_key as estacion_codigo, s.sistema_key, e.sistema as sistema_codigo,
       e.estacion_id_origen, e.nombre as nombre_estacion, e.agrupador as linea_ruta_eje,
       e.orden as orden_metroriel, e.lat, e.lon, e.zona_key
from {{ ref('silver_estaciones') }} e
join {{ ref('dim_sistema') }} s on s.sistema_codigo = e.sistema
