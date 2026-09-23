-- Registros malos: NO se descartan. Se guardan con su motivo, el dato crudo y de qué archivo vinieron.
-- Incluye los eventos de operación y las operaciones del CDC que no se pudieron aplicar.
select
    sistema, evento_id, motivo_rechazo,
    case motivo_rechazo
        when 'DUPLICADO_REINGESTA'  then 'El mismo evento llegó en más de un archivo'
        when 'DUPLICADO_TORNIQUETE' then 'Lectura repetida: mismo evento dos veces en el mismo archivo (se conserva la primera)'
        when 'USUARIO_NULO'         then 'El registro no trae llave de usuario'
        when 'PARADA_NULA'          then 'Código de estación/parada vacío'
        when 'ESTACION_DESCONOCIDA' then 'La estación ' || estacion_id || ' no existe en el catálogo del operador'
        when 'FECHA_INVALIDA'       then 'La fecha no se pudo interpretar: ' || coalesce(fecha_original, '(vacía)')
        when 'FECHA_FUTURA'         then 'Fecha ' || cast(ts_local as varchar) || ' posterior a la ingesta ' || cast(ingesta_local as varchar)
        when 'VIAJE_SIN_SALIDA'     then 'Viaje de MetroRiel sin validación de salida'
        when 'SALIDA_INCONSISTENTE' then 'Salida anterior a la entrada, en la misma estación o en estación inexistente'
        when 'ZONA_INVALIDA'        then 'La estación no tiene una zona reconocida'
        when 'MONTO_INVALIDO'       then 'Monto vacío o negativo'
        when 'ESTADO_DESCONOCIDO'   then 'Código de estado de Transurbano no documentado: ' || coalesce(detalle_tipo, '(vacío)')
    end as detalle,
    usuario_llave_origen, estacion_id, fecha_original,
    payload as registro_crudo,
    _source_file as archivo_origen, _ingested_at as ingerido_en
from {{ ref('silver_eventos_evaluados') }}
where motivo_rechazo is not null

union all

select
    'CDC', cast(secuencia as varchar), motivo_no_aplicada,
    case motivo_no_aplicada
        when 'CDC_SIN_TARJETA'        then 'La operación no trae una tarjeta identificable (' || coalesce(tarjeta, 'vacía') || ')'
        when 'CDC_UPDATE_SOBRE_BAJA'  then 'UPDATE sobre una tarjeta que ya estaba dada de baja: no se aplica'
        when 'CDC_OPERACION_INVALIDA' then 'Operación desconocida: ' || coalesce(operacion, '(vacía)')
        else 'Registro de CDC sin secuencia o sin fecha'
    end,
    tarjeta, null, cast(ts_operacion as varchar),
    to_json(struct_pack(secuencia, operacion, ts_operacion, tarjeta, perfil, zona_residencia_origen, estado))::varchar,
    _source_file, _ingested_at
from {{ ref('cdc_operaciones') }}
where motivo_no_aplicada is not null
