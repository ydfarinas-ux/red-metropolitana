# Agencia Metropolitana de Transporte: Fase 1 (arquitectura de datos)

Pipeline por capas (Bronze → Staging → Silver → Gold) que integra Transmetro, Transurbano, MetroRiel y Aerómetro.

| Pieza | Tecnología (la recomendada por el curso) |
|---|---|
| Streaming | Kafka en Docker (KRaft) |
| Lake / Bronze | Carpetas + Parquet, particionado por fecha de ingesta |
| Staging y warehouse | DuckDB |
| Transformación | dbt (dbt-duckdb) |
| CDC | Procesamiento del archivo de log |
| Orquestación | Prefect |

## Requisitos

- Python 3.12 (dbt todavía no funciona con Python 3.14)
- Docker Desktop, solo si se quiere correr el streaming con Kafka real. Para la Fase 1 usamos el modo simulado.

## Instalación

```bash
pymanager install 3.12               # si no tienes Python 3.12 (instalador oficial de python.org)
python3.12 -m venv .venv
.venv\Scripts\python.exe -m pip install -r requirements.txt
copy .env.example .env               # poner una PSEUDO_SALT propia y STREAMING_MODO=simulado
```

En Linux/Mac: `python3.12 -m venv .venv`, `.venv/bin/pip install -r requirements.txt` y `cp .env.example .env`.

## Cómo correr el flujo completo

Con el `.venv` activado (`.venv\Scripts\activate`), o escribiendo `.venv\Scripts\python.exe` en lugar de `python`.

```bash
# 1. Datos: poner los 9 archivos en datos_red/ (o generarlos con el script del curso)
python generar_red_metropolitana.py

# 2. Pipeline completo, dos veces (idempotencia)
python flows/pipeline.py --corrida 1
python flows/pipeline.py --corrida 2
python herramientas/comparar.py   # 0 diferencias -> IDENTICOS

# 3. DDL de Gold (se regenera y se valida)
python herramientas/ddl.py
```

Con Kafka real: `docker compose up -d` y en `.env` poner `STREAMING_MODO=kafka`. Se usan el mismo productor y el mismo consumidor.

Para empezar de cero: borrar `lake/`, `warehouse/` y `evidencia/`.

## Estructura

```
ingesta/            1.1 vías de carga: batch.py, cdc.py, productor.py, consumidor.py, streaming.py, simulado.py
dbt/models/staging  1.2 staging tipado (se vacía cada corrida)
dbt/models/cdc      1.2 padrón vigente (CDC) y catálogos de llaves por operador
dbt/models/silver   1.3 unificación, zona conformada, identidad, cuarentena, SCD2
dbt/models/gold     1.4 dimensiones y hechos
dbt/tests           pruebas de conservación (no se pierde ningún registro)
flows/pipeline.py   1.5 orquestación Prefect
evidencia/          conteos y métricas de cada corrida (1.5)
entregables/        tablas de conclusiones exportadas a CSV (cuarentena, conteos, CDC)
docs/               entregables de conclusiones por sección
```

## Entregables de la Fase 1

Datos y conclusiones en un solo archivo: **`Datos y conclusiones Fase 1.docx`** (y `.pdf`).

**Mapa completo de qué archivo cumple cada punto: [ENTREGA.md](ENTREGA.md).**

| Sección | Código | Conclusiones y datos |
|---|---|---|
| 1.1 Ingesta y Bronze | `ingesta/` | [docs/1.1-ingesta-bronze.md](docs/1.1-ingesta-bronze.md) |
| 1.2 Staging y CDC | `dbt/models/staging`, `dbt/models/cdc` | [docs/1.2-staging-cdc.md](docs/1.2-staging-cdc.md) |
| 1.3 Silver | `dbt/models/silver` | [docs/1.3-silver.md](docs/1.3-silver.md) |
| 1.4 Gold | `dbt/models/gold`, [docs/1.4-ddl-gold.sql](docs/1.4-ddl-gold.sql) | [docs/1.4-modelo-dimensional.md](docs/1.4-modelo-dimensional.md) |
| 1.5 Idempotencia | `flows/pipeline.py` | [docs/1.5-idempotencia.md](docs/1.5-idempotencia.md), `evidencia/` |

Verificación punto por punto contra el enunciado: [docs/checklist-fase1.md](docs/checklist-fase1.md).

## Consultas útiles

```bash
duckdb warehouse/red-metropolitana.duckdb
```
```sql
SELECT * FROM control.ingest_log;              -- conteos por archivo
SELECT * FROM silver.padron_resumen_cdc;       -- CDC antes / después
SELECT * FROM silver.padron_resumen_por_operador;
SELECT * FROM silver.silver_calidad_resumen;   -- cuarentena por regla
SELECT * FROM silver.silver_identidad_diagnostico;
```

## Seguridad

No hay credenciales en el repositorio. La sal de seudonimización (`PSEUDO_SALT`) vive en `.env`, que está en `.gitignore`. Gold solo contiene `usuario_sk`, nunca la tarjeta ni el nombre.
