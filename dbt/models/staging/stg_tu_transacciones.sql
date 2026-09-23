-- Transurbano: una fila = una TRANSACCIÓN. Fecha 'DD/MM/YYYY' y hora en columnas separadas, monto en CENTAVOS,
-- estado numérico: 1, 2, 3 = OK (abordaje cobrado) · 7 = SALDO_INSUF · 9 = TARJETA_INVALIDA.
-- No trae ID de transacción: se construye uno determinístico con el hash del contenido de la fila.
select
    'TU'                                                        as sistema,
    md5(concat_ws('|', fecha, hora, num_tarjeta, cod_parada, ruta, monto_centavos, cod_estado)) as evento_id,
    case when cod_estado in ('1', '2', '3') then 'ABORDAJE'
         when cod_estado = '7' then 'RECHAZO_SALDO_INSUF'
         when cod_estado = '9' then 'RECHAZO_TARJETA_INVALIDA'
         else 'ESTADO_DESCONOCIDO' end                           as tipo_evento,
    cod_estado                                                  as detalle_tipo,
    num_tarjeta                                                 as usuario_llave_origen,
    nullif(trim(cod_parada), '')                                as estacion_id,
    try_strptime(fecha || ' ' || hora, '%d/%m/%Y %H:%M:%S')     as ts_local,
    try_cast(monto_centavos as integer) / 100.0                 as monto_q,             -- centavos -> quetzales
    null::varchar as salida_estacion_id, null::timestamp as salida_ts_local, null::integer as duracion_origen_s,
    fecha || ' ' || hora                                        as fecha_original,
    to_json(struct_pack(fecha, hora, num_tarjeta, cod_parada, ruta, monto_centavos, cod_estado))::varchar as payload,
    _source_file, _file_hash, _ingested_at, null::bigint as _linea
from {{ source('bronze', 'transurbano_transacciones') }}
