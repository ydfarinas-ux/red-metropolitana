-- Transurbano registra TRANSACCIONES, no abordajes. Las rechazadas (7 = saldo insuficiente, 9 = tarjeta inválida)
-- son datos correctos de un intento de pago que NO terminó en abordaje: no inflan la demanda y no son cuarentena.
-- Se conservan porque dicen algo útil (fricción en el cobro por parada y por hora).
select e.sistema || ':' || e.evento_id as transaccion_id, e.tipo_evento as motivo_rechazo_pago,
       e.detalle_tipo as cod_estado, i.usuario_sk, i.persona_id,
       e.sistema || ':' || e.estacion_id as estacion_key, e.zona_key, e.ts_local, e.monto_q,
       e._source_file, e._ingested_at
from {{ ref('silver_eventos_evaluados') }} e
join {{ ref('silver_identidad_usuario') }} i on i.sistema = e.sistema and i.llave_origen = e.usuario_llave_origen
where e.motivo_rechazo is null and e.tipo_evento in ('RECHAZO_SALDO_INSUF', 'RECHAZO_TARJETA_INVALIDA')
