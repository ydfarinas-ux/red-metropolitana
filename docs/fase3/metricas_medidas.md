# Métricas medidas de la entrega

Fecha de corrida: 12/10/2026. Datos sintéticos del 01/06 al 15/07/2026.

## Volumen Gold

| Tabla | Filas |
|---|---|
| dim_estacion | 468 |
| dim_fecha | 365 |
| dim_sistema | 4 |
| dim_tiempo | 8,760 |
| dim_usuario | 70,380 |
| dim_zona | 26 |
| fct_abordaje | 1,647,569 |
| fct_padron_diario | 8,612 |
| fct_trayecto_metroriel | 295,511 |

## Calidad y CDC

| Sistema | Motivo | Registros | % de fuente |
|---|---|---|---|
| CDC | CDC_SIN_TARJETA | 2,206 | 7.105% |
| CDC | CDC_UPDATE_SOBRE_BAJA | 423 | 1.362% |
| MR | VIAJE_SIN_SALIDA | 3,589 | 1.2% |
| TM | DUPLICADO_TORNIQUETE | 1,115 | 0.307% |
| TU | PARADA_NULA | 4,189 | 0.503% |
| TU | FECHA_FUTURA | 814 | 0.098% |

CDC: {"eventos_en_log": 31050, "eventos_en_cuarentena": 2629, "eventos_aplicados": 28421, "altas_aplicadas": 10003, "cambios_aplicados": 14646, "bajas_aplicadas": 3772, "tarjetas_activas_antes_de_borrados": 20148, "tarjetas_activas_despues": 19110, "tarjetas_dadas_de_baja": 3352, "tarjetas_en_padron": 22462, "reactivaciones": 281, "updates_de_tarjetas_previas_al_log": 11740, "bajas_de_tarjetas_previas_al_log": 2877}

Cobertura: 15 de 26 territorios con estaciones; 11 sin ellas. Usuarios activos del período: 70,380; multimodales observados: 36,827 (52.33%).

## Rendimiento e idempotencia

| Medición | Corrida 1 | Corrida 2 |
|---|---|---|
| bronze_batch, segundos | 1.85 | 0.54 |
| bronze_cdc, segundos | 0.24 | 0.07 |
| bronze_streaming, segundos | 12.45 | 0.23 |
| vaciar_staging, segundos | 0.03 | 0.09 |
| dbt_build, segundos | 91.72 | 51.43 |
| Consulta SQL de referencia, ms | 58.3 | 38.5 |
| datos_crudos, MB reportados por pipeline | 137.07 | 137.07 |
| bronze, MB reportados por pipeline | 31.32 | 31.32 |
| warehouse_staging_silver_gold, MB reportados por pipeline | 490.22 | 716.71 |

Los tamaños Staging/Silver/Gold se reportan combinados porque viven en el mismo archivo DuckDB; no se inventa una distribución física exacta por schema. La consulta SQL cronometrada no es latencia de render de Tableau. Evidencia de idempotencia: 52 tablas, cero diferencias. La unidad MB conserva la etiqueta del pipeline.
