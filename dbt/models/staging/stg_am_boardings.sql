-- Aerómetro: una fila = un abordaje de cabina. Columnas en inglés, timestamp en UTC -> hora local de Guatemala.
select
    'AM'                                                        as sistema,
    cast(boarding_id as varchar)                                as evento_id,
    'ABORDAJE'                                                  as tipo_evento,
    'cabina ' || cabin_number                                   as detalle_tipo,
    user_hash                                                   as usuario_llave_origen,
    nullif(trim(station_code), '')                              as estacion_id,
    try_strptime(timestamp_utc, '%Y-%m-%dT%H:%M:%SZ') at time zone 'UTC' at time zone 'America/Guatemala' as ts_local,
    try_cast(fare as decimal(10, 2))                            as monto_q,
    null::varchar as salida_estacion_id, null::timestamp as salida_ts_local, null::integer as duracion_origen_s,
    timestamp_utc                                               as fecha_original,
    to_json(struct_pack(boarding_id, user_hash, station_code, axis, timestamp_utc, cabin_number, fare))::varchar as payload,
    _source_file, _file_hash, try_cast(_ingested_at as timestamp) as _ingested_at,
    try_cast(_linea as bigint)                                  as _linea
from {{ source('bronze', 'aerometro_boardings') }}
