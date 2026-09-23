-- Transmetro: una fila = un abordaje (ENTRADA o TRANSBORDO entre líneas). Fecha 'YYYY-MM-DD HH:MM:SS' hora local, quetzales.
-- No trae zona: la zona sale del catálogo de estaciones.
select
    'TM'                                                        as sistema,
    cast(validacion_id as varchar)                              as evento_id,
    'ABORDAJE'                                                  as tipo_evento,
    tipo                                                        as detalle_tipo,        -- ENTRADA / TRANSBORDO
    tarjeta                                                     as usuario_llave_origen,
    nullif(trim(estacion_id), '')                               as estacion_id,
    try_strptime(fecha_hora, '%Y-%m-%d %H:%M:%S')               as ts_local,
    try_cast(tarifa as decimal(10, 2))                          as monto_q,
    null::varchar as salida_estacion_id, null::timestamp as salida_ts_local, null::integer as duracion_origen_s,
    fecha_hora                                                  as fecha_original,
    to_json(struct_pack(validacion_id, tarjeta, estacion_id, linea, fecha_hora, tarifa, tipo))::varchar as payload,
    _source_file, _file_hash, try_cast(_ingested_at as timestamp) as _ingested_at,
    try_cast(_linea as bigint)                                  as _linea
from {{ source('bronze', 'transmetro_validaciones') }}
