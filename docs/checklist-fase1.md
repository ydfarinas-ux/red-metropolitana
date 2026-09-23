# Verificación de la Fase 1 contra el enunciado

Cada requisito del enunciado, dónde se cumple y la evidencia medida. Todo se verificó con los datos del script oficial `generar_red_metropolitana.py`.

## Reglas del diagrama ("lo que se evaluará")

| Regla | Cumple | Cómo se garantiza |
|---|:-:|---|
| Gold NUNCA lee Bronze | ✓ | Todos los modelos Gold usan `ref()` a Silver. La tarea `verificar_linaje` revisa `manifest.json` en **cada corrida** y falla si un modelo Gold depende de una fuente. |
| Los malos registros van a cuarentena, no se descartan | ✓ | `silver_cuarentena`: 12,336 registros con motivo y registro crudo. La prueba `assert_ningun_registro_se_pierde` falla si algún evento desaparece. |
| El staging se vacía, Bronze se acumula | ✓ | `DROP SCHEMA staging` en cada corrida. Bronze solo agrega archivos nuevos, identificados por hash. |
| Features de ML salen de Silver, no de Gold | — | Es de la Fase 2 (2.3). Silver ya tiene el detalle atómico con `usuario_sk` (`silver_abordajes`) para construirlas. |

## 1.1 Ingesta y Bronze (8 pts)

| Requisito | Cumple | Dónde |
|---|:-:|---|
| Streaming (Kafka): validaciones TM y boardings AM, publicando el CSV línea por línea | ✓ | `ingesta/productor.py`, `ingesta/consumidor.py`, `docker-compose.yml` |
| Batch: los 4 catálogos y los viajes de MetroRiel | ✓ | `ingesta/batch.py` |
| CDC: padrón de usuarios | ✓ | `ingesta/cdc.py` |
| Transurbano a criterio, con argumento y consecuencia | ✓ | Batch. Consecuencia: llega con retraso y el transbordo cercano en tiempo real queda incompleto. `docs/1.1-ingesta-bronze.md` |
| Bronze tal como llegó, con marca de tiempo de ingesta y particionado por fecha | ✓ | `_ingested_at`, `fecha_ingesta=` en la ruta; todo como texto y el JSON anidado |
| Lake o warehouse, justificado considerando el JSON anidado | ✓ | Lake (Parquet). `docs/1.1-ingesta-bronze.md` |
| Entregable: scripts por vía, tabla de conteos por archivo, justificación TU | ✓ | `ingesta/`, `docs/1.1-ingesta-bronze.md` (1,730,184 filas, todas cuadran) |

## 1.2 Staging y CDC (9 pts)

| Requisito | Cumple | Dónde |
|---|:-:|---|
| Padrón vigente a partir de `cdc_padron_usuarios.csv` | ✓ | `dbt/models/cdc/padron_vigente.sql` y `padron_transmetro_vigente.sql` |
| Tres operaciones en orden de secuencia | ✓ | `cdc_operaciones.sql`, ordenado por `seq` |
| DELETE marca inactiva, no borra | ✓ | `activa = false` + `fecha_baja`. El padrón tiene 22,462 tarjetas con 3,352 de baja |
| Documentar activas y dadas de baja | ✓ | Transmetro: antes 15,611 activas; después 14,834 activas y 2,598 de baja. Padrón completo: 20,148 → 19,110 activas y 3,352 de baja |
| Catálogo mínimo de llaves de TU, MR y AM, solo la llave, sin inventar | ✓ | `cat_usuarios_*` con una sola columna: 36,567 / 22,885 / 14,496 |
| Entregable: modelo CDC con conteo antes/después y catálogos con usuarios únicos | ✓ | `docs/1.2-staging-cdc.md` |
| Hallazgo: el padrón mezcla TM/TU/MR | ✓ | Documentado. Registro central con operador por tarjeta, padrón TM aparte, `SIN-TARJETA` a cuarentena |
| Los DELETE sin cuerpo no van a cuarentena por venir incompletos | ✓ | 4,050 DELETE sin cuerpo: 3,772 aplicados, 278 en cuarentena solo por `SIN-TARJETA`, 0 con tarjeta válida rechazados |

## 1.3 Silver (12 pts)

| Requisito | Cumple | Dónde |
|---|:-:|---|
| Fechas a un estándar, montos a quetzales, Aerómetro de UTC a hora local | ✓ | `dbt/models/staging/stg_*.sql` |
| Zona conformada: Z10, Zona 10 y district apuntan a la misma zona | ✓ | Macro `normalizar_territorio` + seed `territorios.csv`; `silver_zona_mapeo` (60 valores, todos conformados) |
| Identidad del usuario: estrategia propuesta y justificada | ✓ | `silver_identidad_usuario`. Supuestos, límites y análisis de sensibilidad en `docs/1.3-silver.md` |
| Duplicados de torniquete | ✓ | 1,115 (`DUPLICADO_TORNIQUETE`) |
| Códigos de parada nulos | ✓ | 4,189 (`PARADA_NULA`) |
| Fechas del futuro | ✓ | 814 (`FECHA_FUTURA`) |
| Viajes sin salida | ✓ | 3,589 (`VIAJE_SIN_SALIDA`) |
| Malos a cuarentena, no a la basura | ✓ | `silver_cuarentena` |
| Padrón historizado con SCD Tipo 2 | ✓ | `silver_padron_scd2` (28,421 versiones) |
| Entregable: modelos, tabla de cuarentena con motivo, conteo por regla | ✓ | `silver_cuarentena`, `silver_calidad_resumen`, `docs/1.3-silver.md` |

## 1.4 Diseño dimensional y Gold (15 pts)

| Requisito | Cumple | Dónde |
|---|:-:|---|
| Grano de la tabla principal en una frase (con el cuidado de MetroRiel) | ✓ | "Un abordaje de un usuario en una estación de cualquiera de los cuatro sistemas". El abordaje de MR (estación y hora de entrada) está en `fct_abordaje` y el trayecto completo en su propia tabla |
| Matriz del bus | ✓ | `docs/1.4-modelo-dimensional.md` |
| Al menos dos tablas de hechos con dimensiones conformadas | ✓ | Tres: `fct_abordaje`, `fct_trayecto_metroriel` y `fct_padron_diario` |
| Dimensión tiempo con hora del día, día hábil y hora pico | ✓ | `dim_tiempo` (grano hora) + `dim_fecha` (asuetos) |
| Medidas clasificadas: aditivas, semi-aditivas y no aditivas | ✓ | `docs/1.4-modelo-dimensional.md` (`tarjetas_activas` es la semi-aditiva) |
| Entregable: diagrama, matriz del bus y DDL | ✓ | `docs/1.4-diagrama-modelo.png` (y `.pdf`), matriz en `docs/1.4-modelo-dimensional.md` y `docs/1.4-ddl-gold.sql` (validado en una base vacía) |

## 1.5 Orquestación e idempotencia (5 pts)

| Requisito | Cumple | Dónde |
|---|:-:|---|
| Flujo completo orquestado | ✓ | `flows/pipeline.py` (Prefect, con reintentos y bitácora) |
| Correr dos veces sin duplicar: correr, contar, volver a correr, contar | ✓ | `evidencia/conteos-corrida-1.csv` = `conteos-corrida-2.csv` (52 tablas, `diff` vacío) |
| Demostrable el día de la presentación | ✓ | Mismos dos comandos, desde cero, en `README.md`. Streaming simulado (válido para Fase 1 según el ingeniero) |

## Penalizaciones: todas evitadas

| Penalización | Estado |
|---|---|
| Gold que lea de Bronze pierde todo 1.4 | Evitada y verificada automáticamente en cada corrida |
| Descartar registros en silencio pierde la mitad de 1.3 | Evitada: cuarentena con conteo y prueba de conservación |
| Flujo no idempotente pierde 1.5 completo | Evitada: dos corridas idénticas |
| Tablero no rastreable al dato crudo pierde la mitad de 2.1 (Fase 2) | Preparado: cada fila de Silver guarda `_source_file`, y dbt genera el linaje (`dbt docs generate`) |

## Pendiente

- Crear el repositorio en Git con commits propios a lo largo del trabajo (el enunciado pide historial real).
