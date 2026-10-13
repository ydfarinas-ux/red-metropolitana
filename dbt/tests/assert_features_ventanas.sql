-- Contadores anidados, proporción, modos y duración válida de observación.
select * from {{ ref('features_usuario') }}
where viajes_7d < 0 or viajes_7d > viajes_30d or viajes_30d > viajes_90d
   or viajes_90d <= 0 or modos_distintos_90d not between 1 and 4
   or dias_desde_ultimo_viaje not between 1 and 90
   or proporcion_hora_pico_90d not between 0 and 1
   or dias_historial_disponible_90d not between 0 and 90
   or ventana_90d_completa != (dias_historial_disponible_90d = 90)
   or abs(gasto_promedio_q_90d * viajes_90d - gasto_q_90d) > 0.000001
