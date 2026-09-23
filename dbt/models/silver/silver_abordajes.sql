-- Registros LIMPIOS de abordaje de los cuatro sistemas, formato unificado:
-- hora local de Guatemala, montos en quetzales, zona conformada (de la estación), usuario seudonimizado.
-- MetroRiel: el abordaje es la ENTRADA del viaje; el trayecto completo vive en silver_trayectos_metroriel.
-- Transurbano: solo transacciones OK (estado 1, 2, 3); las rechazadas no son abordajes.
select
    e.sistema || ':' || e.evento_id              as abordaje_id,
    e.sistema, e.evento_id                       as evento_id_origen,
    e.detalle_tipo                               as tipo_validacion,
    i.usuario_sk, i.persona_id, e.usuario_llave_origen,
    e.sistema || ':' || e.estacion_id            as estacion_key,
    e.zona_key,
    e.ts_local, cast(e.ts_local as date) as fecha, hour(e.ts_local) as hora,
    e.monto_q,
    e._source_file, e._ingested_at
from {{ ref('silver_eventos_evaluados') }} e
join {{ ref('silver_identidad_usuario') }} i on i.sistema = e.sistema and i.llave_origen = e.usuario_llave_origen
where e.motivo_rechazo is null and e.tipo_evento in ('ABORDAJE', 'VIAJE')
