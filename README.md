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

## Fases 2 y 3

El tablero de la fase 2 está en `entregables/fase2/Red_Metropolitana_Fase2_Tableau.twbx`: incluye los cuatro CSV agregados, siete hojas y tres dashboards. Abrirlo en Tableau; el primer dashboard permite filtrar por sistema. La fase 2 completa está en `entregables/fase2/README_FASE2.md`: recomendación PDF de dos páginas, features de 70,380 usuarios desde Silver, diccionario y corte exclusivo 16/07/2026. Ejecutar `.venv\Scripts\python.exe herramientas/preparar_fase2.py --fecha-corte 2026-07-16` para reconstruir únicamente features y exportar los CSV.

La documentación de la fase 3 está en [docs/fase3/README_FASE3.md](docs/fase3/README_FASE3.md): diccionario de los 91 campos Gold, definiciones oficiales y responsables asignados a integrantes, reglas de calidad, linaje dbt, bitácora de decisiones, reproducibilidad, métricas medidas y seguridad en una página. Abrir `docs/fase3/linaje_dbt/static_index.html` para explorar la documentación y el grafo de dbt sin servidor.

Las copias de documentación dbt de fase 3 tienen la sal retirada del SQL compilado. No compartir directamente `dbt/target`, que puede contenerla. El detalle individual seudonimizado sigue siendo sensible; los roles de acceso y la retención documentados son políticas propuestas, sin automatización en el prototipo.

## Proyecto 2: ¿quién deja de usar la red?

Los datos del Proyecto 2 (90 días, del 1 de junio al 29 de agosto de 2026) reemplazan a los del Proyecto 1: se ponen los 9 archivos en `datos_red/` y se corre **todo desde un entorno vacío con un solo comando**:

```bash
.venv\Scripts\python.exe flows\pipeline.py --desde-cero
```

`--desde-cero` borra el lake, el warehouse y lo compilado por dbt (no hay snapshots ni tablas incrementales). Después carga Bronze, corre dbt (Silver y Gold con sus pruebas) y agrega las tareas nuevas del Proyecto 2.

| Pieza | Archivo |
|---|---|
| Parámetros (cortes, ventanas, semilla) | `proyecto2/config.py` |
| 1.1 Conteos esperados y tiempos por etapa | `proyecto2/conteos-esperados.csv`, `proyecto2/conteos.py` |
| 1.2 Población, etiqueta y costo de la unidad | `proyecto2/poblacion.py` |
| 1.3 Features por corte (la fecha de corte es un parámetro) y diccionario | `proyecto2/features.py` |
| 1.3 Prueba de recorte | `proyecto2/auditoria.py` (`python proyecto2/auditoria.py` o `pipeline.py --auditoria`) |
| Bitácora de corridas | `proyecto2/bitacora.md` |
| Resultados | `entregables/proyecto2/` |

Cortes: A = 2026-07-01 (entrenamiento), B = 2026-07-31 (test, su etiqueta no se usa en la Fase 1), C = 2026-08-30 (uso real, sin etiqueta).

Las 23 features usan exclusivamente Silver y ventanas `[t - N días, t)` con N ≤ 28.
El padrón se consulta con sus versiones SCD2 vigentes justo antes del corte.
`python proyecto2/features.py --fecha-corte AAAA-MM-DD` permite calcular otro corte.

Para reproducir la auditoría desde los archivos crudos, ejecutar primero
`python proyecto2/auditoria.py --version-anterior` y luego
`python proyecto2/auditoria.py`. La primera conserva las fórmulas flotantes
anteriores de gasto y tarifa media para documentar las diferencias observadas;
su conteo puede variar según el paralelismo y la plataforma. La versión final
usa centavos enteros y exige cero diferencias. Ambas reconstruyen Bronze y
Silver en `.recorte/`, excluyen la etiqueta de la comparación y prueban que el
perfil al final de los datos sí cambia (control negativo).
