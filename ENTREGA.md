# Entrega de la Fase 1: qué archivo cumple cada punto

Los datos y conclusiones de todos los puntos están juntos en **`Datos y conclusiones Fase 1.docx`** (y en PDF). Abajo está el detalle de cada archivo.

## Archivos de script (código)

| Punto | Lo que se pide | Archivo(s) |
|---|---|---|
| **1.1** | Productor que publica en Kafka línea por línea (Transmetro y Aerómetro) | `ingesta/productor.py`; el consumidor que escribe a Bronze es `ingesta/consumidor.py`, y Kafka se levanta con `docker-compose.yml` |
| **1.1** | Carga batch (catálogos y MetroRiel) | `ingesta/batch.py` |
| **1.1** | Carga del CDC | `ingesta/cdc.py` |
| **1.1** | Carga de Transurbano por la vía elegida (batch) | `ingesta/batch.py`, fuente `transurbano_transacciones`; la vía está declarada en `ingesta/comun.py` → `FUENTES` |
| **1.2** | Modelo de CDC de Transmetro que aplica INSERT, UPDATE y DELETE en orden de secuencia | `dbt/models/cdc/cdc_operaciones.sql` (aplica las operaciones por `seq`), `dbt/models/cdc/padron_vigente.sql`, `dbt/models/cdc/padron_transmetro_vigente.sql` |
| **1.2** | Modelos que extraen las llaves distintas de Transurbano, MetroRiel y Aerómetro | `dbt/models/cdc/cat_usuarios_transurbano.sql`, `cat_usuarios_metroriel.sql`, `cat_usuarios_aerometro.sql` |
| **1.3** | Unificación de formatos | `dbt/models/staging/stg_*.sql` (fechas, UTC → hora local, centavos → quetzales) y `dbt/models/silver/silver_eventos_evaluados.sql` (esquema común) |
| **1.3** | Dimensión zona | `dbt/models/silver/silver_zona.sql`, `silver_zona_mapeo.sql`, `silver_estaciones.sql`, macro `normalizar_territorio` en `dbt/macros/utilidades.sql`, seed `dbt/seeds/territorios.csv` |
| **1.3** | Identidad de usuario | `dbt/models/silver/silver_identidad_usuario.sql`, `silver_identidad_diagnostico.sql` |
| **1.3** | Reglas de calidad que envían a cuarentena | `dbt/models/silver/silver_eventos_evaluados.sql` (reglas), `silver_cuarentena.sql`, `silver_calidad_resumen.sql`; las pruebas de que no se pierde nada están en `dbt/tests/` |
| **1.3** | SCD Tipo 2 del padrón | `dbt/models/silver/silver_padron_scd2.sql` |
| **1.4** | DDL de hechos y dimensiones de Gold | `docs/1.4-ddl-gold.sql` (validado en una base vacía); los modelos que construyen esas tablas están en `dbt/models/gold/` |
| **1.5** | Flujo de orquestación que corre el pipeline completo | `flows/pipeline.py` (Prefect) |

## Archivos de conclusiones y datos

| Punto | Lo que se pide | Documento | Datos (CSV) |
|---|---|---|---|
| **1.1** | Tabla de conteos por archivo | `docs/1.1-ingesta-bronze.md` | `entregables/1.1-conteos-por-archivo.csv` |
| **1.1** | Justificación de la vía de Transurbano | `docs/1.1-ingesta-bronze.md` | — |
| **1.1** | Decisión justificada: Bronze en lake o warehouse | `docs/1.1-ingesta-bronze.md` (lake) | — |
| **1.2** | Conteo de tarjetas antes y después de los borrados (activas y de baja) | `docs/1.2-staging-cdc.md` | `entregables/1.2-padron-antes-despues.csv`, `entregables/1.2-padron-antes-despues-por-operador.csv` |
| **1.2** | Conteo de usuarios únicos por operador | `docs/1.2-staging-cdc.md` | `entregables/1.2-usuarios-unicos-por-operador.csv` |
| **1.3** | Tabla de cuarentena con motivo de rechazo | `docs/1.3-silver.md` | `entregables/1.3-cuarentena.csv` (12,336 registros) |
| **1.3** | Conteo de registros por regla de calidad | `docs/1.3-silver.md` | `entregables/1.3-conteo-por-regla-de-calidad.csv` |
| **1.3** | Estrategia de identidad con supuestos y límites | `docs/1.3-silver.md` | `entregables/1.3-identidad-usuario-diagnostico.csv` |
| **1.4** | Diagrama del modelo | `docs/1.4-diagrama-modelo.png` (y `.svg`) | — |
| **1.4** | Matriz del bus | `docs/1.4-modelo-dimensional.md` | — |
| **1.4** | Grano de la tabla principal en una frase | `docs/1.4-modelo-dimensional.md` | — |
| **1.4** | Clasificación de medidas | `docs/1.4-modelo-dimensional.md` | `entregables/1.4-filas-en-gold.csv` |
| **1.5** | Evidencia de dos corridas con conteos idénticos | `docs/1.5-idempotencia.md` | `evidencia/conteos-corrida-1.csv`, `evidencia/conteos-corrida-2.csv`, `evidencia/comparacion-corridas.csv` |

## Cifras clave (medidas con los datos oficiales)

| | |
|---|---|
| Filas ingeridas | 1,730,184 (todas cuadran archivo = Bronze) |
| Padrón de Transmetro | 15,611 activas antes de borrados → 14,834 activas y 2,598 de baja después |
| Padrón completo (TM+TU+MR) | 20,148 activas antes → 19,110 activas y 3,352 de baja después |
| Usuarios únicos | TM 43,255 · TU 36,567 · MR 22,885 · AM 14,496 |
| Cuarentena | 1,115 duplicados de torniquete · 4,189 paradas nulas · 814 fechas futuras · 3,589 viajes sin salida · 2,629 del CDC |
| Gold | 1,647,569 abordajes · 295,511 trayectos de MetroRiel |
| Idempotencia | 52 tablas, 0 diferencias entre la corrida 1 y la 2 |

Verificación más detallada contra el enunciado (incluidas las penalizaciones): `docs/checklist-fase1.md`.
