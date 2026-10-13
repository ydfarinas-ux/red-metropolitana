# 3.2 Ejecución y reproducción

## Requisitos y ejecución base

Python 3.12, dependencias fijadas en `requirements.txt`, modo simulado de streaming. Docker solo para Kafka real. Desde la raíz del proyecto, seguir el README original:

```powershell
python3.12 -m venv .venv
.venv\Scripts\python.exe -m pip install -r requirements.txt
Copy-Item .env.example .env
# Completar PSEUDO_SALT propia y STREAMING_MODO=simulado sin versionar .env.
.venv\Scripts\python.exe generar_red_metropolitana.py
.venv\Scripts\python.exe flows/pipeline.py --corrida 1
.venv\Scripts\python.exe flows/pipeline.py --corrida 2
.venv\Scripts\python.exe herramientas/comparar.py
.venv\Scripts\python.exe herramientas/ddl.py
```

PowerShell no necesita activar el entorno si se usa su ejecutable. Si `python3.12` no existe, usar el ejecutable de Python 3.12 instalado. En esta máquina se usó Python 3.12 del instalador oficial. Prefect requiere poder conectarse a localhost: si hay un perfil con API ajena, seleccionar uno local sin `PREFECT_API_URL`, con servidor efímero habilitado; no cambiar el código del flujo. El entorno aislado bloqueó la conexión local y la ejecución se completó con acceso a ese servidor autorizado.

## Generar documentación dbt

Cargar la sal de `.env` en el proceso sin imprimirla; configurar `WAREHOUSE_PATH` y `BRONZE_PATH` con rutas absolutas al proyecto. Desde `dbt`, con el entorno activo:

```powershell
dbt docs generate --static --profiles-dir .
```

Nunca publicar `dbt/target` completo sin revisar secretos del SQL compilado. Las copias de `docs/fase3/linaje_dbt` están saneadas. Abrir `static_index.html`, archivo autocontenido de dbt, y usar el grafo para explorar sus dependencias. Se preservan `manifest.json`, `catalog.json` y aristas para auditoría.

## Tableau y evidencias

Abrir `entregables/fase2/Red_Metropolitana_Fase2_Tableau.twbx` con Tableau. Incluye sus cuatro CSV agregados, siete hojas y tres dashboards. Las consultas SQL de cada exportación y sus verificaciones están en la entrega de fase 3. El filtro por sistema del dashboard 01 afecta sus gráficos de demanda; las otras fuentes resumen el período completo.

Las corridas preservan `evidencia/conteos-corrida-1.csv`, `conteos-corrida-2.csv`, `comparacion-corridas.csv`, métricas JSON y bitácora. Comparación: 52 tablas, 0 diferencias. dbt: 39 modelos + 3 seeds + 66 pruebas = 108 resultados exitosos. DDL validado: 9 tablas Gold. La generación de docs no reconstruye la fase 1.

## Reproducción y límites

Mismos archivos, catálogo, variables y sal producen las mismas identidades y conteos. Cambiar la sal cambia seudónimos; usar otra fecha de corte o regla de identidad cambia métricas. No borrar datos para reproducir sin preservar evidencia. Los tamaños de DuckDB cambian por almacenamiento y reconstrucciones aunque las filas sean idénticas. La dimensión fecha está fijada a 2026 y limita otros períodos. La consulta de rendimiento medida por el pipeline es SQL de referencia en DuckDB; no es el tiempo de render completo de Tableau.

## Historial

Existe historial real previo. `historial_git.txt` registra commits existentes con fecha, sin fabricar una evolución retrospectiva. Esta formalización se añade como un cambio documental actual.
