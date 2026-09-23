-- GRANO: una fila por cada viaje completo de MetroRiel (entrada y salida del mismo usuario).
select
    row_number() over (order by t.trayecto_id)  as trayecto_key,
    t.trayecto_id                               as trayecto_id_origen,
    cast(strftime(t.ts_entrada_local, '%Y%m%d') as integer) * 100 + hour(t.ts_entrada_local) as tiempo_key,
    cast(strftime(t.ts_entrada_local, '%Y%m%d') as integer) as fecha_key,
    t.usuario_sk,
    eo.estacion_key                             as estacion_origen_key,
    ed.estacion_key                             as estacion_destino_key,
    t.zona_origen_key,                                                      -- dim_zona con dos roles
    t.zona_destino_key,
    t.ts_entrada_local, t.ts_salida_local,
    1                                           as cantidad_trayectos,     -- aditiva
    t.duracion_min,                                                         -- aditiva (el promedio NO lo es)
    t.estaciones_recorridas,                                                -- aditiva
    t.monto_q                                                               -- aditiva
from {{ ref('silver_trayectos_metroriel') }} t
join {{ ref('dim_estacion') }} eo on eo.estacion_codigo = t.estacion_origen_key
join {{ ref('dim_estacion') }} ed on ed.estacion_codigo = t.estacion_destino_key
