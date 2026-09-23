-- MetroRiel: JSON anidado, una fila = un VIAJE COMPLETO (entry + exit). ISO 8601 en hora local, quetzales.
select
    'MR'                                                        as sistema,
    cast(trip_id as varchar)                                    as evento_id,
    'VIAJE'                                                     as tipo_evento,
    null::varchar                                               as detalle_tipo,
    card                                                        as usuario_llave_origen,
    nullif(cast(entry.station as varchar), '')                  as estacion_id,
    try_cast(entry.ts as timestamp)                             as ts_local,
    try_cast(fare_gtq as decimal(10, 2))                        as monto_q,
    nullif(cast(exit.station as varchar), '')                   as salida_estacion_id,
    try_cast(exit.ts as timestamp)                              as salida_ts_local,
    try_cast(duration_s as integer)                             as duracion_origen_s,
    entry.ts                                                    as fecha_original,
    to_json(struct_pack(trip_id, card, entry, exit, fare_gtq, duration_s))::varchar as payload,
    _source_file, _file_hash, _ingested_at, null::bigint as _linea
from {{ source('bronze', 'metroriel_viajes') }}
