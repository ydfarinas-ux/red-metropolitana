-- Viajes completos de MetroRiel (entrada + salida). Es la información que los otros tres sistemas no tienen.
select
    'MR:' || e.evento_id                          as trayecto_id,
    e.evento_id                                   as viaje_id_origen,
    i.usuario_sk, i.persona_id,
    'MR:' || e.estacion_id                        as estacion_origen_key,
    'MR:' || e.salida_estacion_id                 as estacion_destino_key,
    e.zona_key                                    as zona_origen_key,
    e.salida_zona_key                             as zona_destino_key,
    e.ts_local                                    as ts_entrada_local,
    e.salida_ts_local                             as ts_salida_local,
    round(date_diff('second', e.ts_local, e.salida_ts_local) / 60.0, 2) as duracion_min,
    e.duracion_origen_s,
    abs(so.orden - sd.orden)                      as estaciones_recorridas,
    e.monto_q, e._source_file, e._ingested_at
from {{ ref('silver_eventos_evaluados') }} e
join {{ ref('silver_identidad_usuario') }} i on i.sistema = e.sistema and i.llave_origen = e.usuario_llave_origen
join {{ ref('silver_estaciones') }} so on so.estacion_key = 'MR:' || e.estacion_id
join {{ ref('silver_estaciones') }} sd on sd.estacion_key = 'MR:' || e.salida_estacion_id
where e.motivo_rechazo is null and e.sistema = 'MR'
