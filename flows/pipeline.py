"""
1.5 Orquestación del flujo completo con Prefect.

    Bronze (batch + CDC + streaming)  ->  vaciar staging  ->  dbt build (staging, silver, gold + pruebas)
    ->  verificar linaje (Gold nunca lee Bronze)  ->  conteos de la corrida  ->  exportar entregables (CSV)

Idempotencia:
  * Bronze: cada archivo se identifica por su hash MD5; si ya está en control.ingest_log no se vuelve a cargar.
  * Staging: se hace DROP SCHEMA al inicio de cada corrida (se vacía; Bronze se acumula).
  * Silver y Gold: modelos dbt materializados como tabla, se reconstruyen desde Bronze -> mismo resultado.
  * Kafka: cada mensaje lleva llave <hash>:<línea>; el consumidor deduplica re-entregas.

Uso:
    python flows/pipeline.py --corrida 1
    python flows/pipeline.py --corrida 2        # debe dar conteos idénticos
    STREAMING_MODO=kafka python flows/pipeline.py --corrida 1   (con docker compose up -d)
"""
import argparse, csv, json, os, subprocess, sys, time
from datetime import datetime
from pathlib import Path

RAIZ = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(RAIZ / "ingesta"))

# carga .env si existe (sin dependencias extra)
if (RAIZ / ".env").exists():
    for linea in (RAIZ / ".env").read_text().splitlines():
        if linea.strip() and not linea.startswith("#") and "=" in linea:
            k, v = linea.split("=", 1)
            os.environ.setdefault(k.strip(), v.split("#", 1)[0].strip())

# las rutas relativas siempre se resuelven desde la raíz del proyecto (dbt corre dentro de dbt/)
for var, defecto in (("WAREHOUSE_PATH", "warehouse/red-metropolitana.duckdb"), ("BRONZE_PATH", "lake/bronze"),
                     ("DATOS_RED", "datos_red")):
    ruta = Path(os.environ.get(var, defecto))
    os.environ[var] = str(ruta if ruta.is_absolute() else RAIZ / ruta)

from prefect import flow, task, get_run_logger   # noqa: E402
import duckdb                                    # noqa: E402
import batch, cdc, comun, streaming              # noqa: E402

EVIDENCIA = RAIZ / "evidencia"
EVIDENCIA.mkdir(exist_ok=True)
DURACIONES = {}


def cronometrar(nombre):
    def deco(fn):
        def envuelta(*a, **k):
            t0 = time.perf_counter()
            r = fn(*a, **k)
            DURACIONES[nombre] = round(time.perf_counter() - t0, 2)
            return r
        envuelta.__name__ = fn.__name__
        return envuelta
    return deco


@task(retries=2, retry_delay_seconds=5)
@cronometrar("bronze_batch")
def ingesta_batch():
    batch.main()


@task(retries=2, retry_delay_seconds=5)
@cronometrar("bronze_cdc")
def ingesta_cdc():
    cdc.main()


@task(retries=2, retry_delay_seconds=10)
@cronometrar("bronze_streaming")
def ingesta_streaming():
    modo = os.getenv("STREAMING_MODO", "simulado")
    get_run_logger().info(f"vía streaming en modo: {modo}")
    if modo == "kafka":
        consumidor = subprocess.Popen([sys.executable, str(RAIZ / "ingesta" / "consumidor.py")])
        subprocess.run([sys.executable, str(RAIZ / "ingesta" / "productor.py")], check=True)
        consumidor.wait(timeout=600)
        if consumidor.returncode != 0:
            raise RuntimeError("el consumidor Kafka terminó con error")
    else:
        con = comun.conectar()
        streaming.simular(con)
        con.close()


@task
@cronometrar("vaciar_staging")
def vaciar_staging():
    con = duckdb.connect(os.environ["WAREHOUSE_PATH"])
    con.execute("DROP SCHEMA IF EXISTS staging CASCADE")
    con.close()
    get_run_logger().info("staging vaciado")


@task(retries=1)
@cronometrar("dbt_build")
def dbt_build():
    # usa el dbt del mismo entorno de Python (así funciona aunque no se active el venv)
    dbt = Path(sys.executable).parent / ("dbt.exe" if os.name == "nt" else "dbt")
    r = subprocess.run([str(dbt) if dbt.exists() else "dbt", "build", "--profiles-dir", ".", "--target-path", "target"],
                       cwd=RAIZ / "dbt", capture_output=True, text=True, encoding="utf-8", errors="replace")
    (EVIDENCIA / "ultimo-dbt-build.log").write_text(r.stdout)
    resumen = [l for l in r.stdout.splitlines() if "Done." in l]
    get_run_logger().info(resumen[-1] if resumen else r.stdout[-2000:])
    if r.returncode != 0:
        raise RuntimeError("dbt build falló, ver evidencia/ultimo-dbt-build.log")


@task
def verificar_linaje():
    """Regla dura del proyecto: ningún modelo de Gold puede depender de una fuente (Bronze)."""
    manifest = json.loads((RAIZ / "dbt" / "target" / "manifest.json").read_text())
    violaciones = []
    for nodo in manifest["nodes"].values():
        if nodo["resource_type"] == "model" and nodo["schema"] == "gold":
            fuentes = [d for d in nodo["depends_on"]["nodes"] if d.startswith("source.")]
            if fuentes:
                violaciones.append((nodo["name"], fuentes))
    if violaciones:
        raise RuntimeError(f"Gold lee Bronze directamente: {violaciones}")
    get_run_logger().info("linaje OK: ningún modelo Gold lee Bronze")


def tamano_mb(ruta):
    ruta = Path(ruta)
    if ruta.is_file():
        return round(ruta.stat().st_size / 1e6, 2)
    return round(sum(f.stat().st_size for f in ruta.rglob("*") if f.is_file()) / 1e6, 2)


@task
def contar(corrida: int):
    con = duckdb.connect(os.environ["WAREHOUSE_PATH"], read_only=True)
    filas = []
    for (fuente,) in con.execute("SELECT DISTINCT fuente FROM control.ingest_log ORDER BY 1").fetchall():
        n = con.execute(f"SELECT count(*) FROM read_parquet('{os.environ['BRONZE_PATH']}/fuente={fuente}/*/*.parquet')").fetchone()[0]
        filas.append(("bronze", fuente, n))
    filas.append(("control", "ingest_log", con.execute("SELECT count(*) FROM control.ingest_log").fetchone()[0]))
    for esquema, tabla in con.execute("""SELECT table_schema, table_name FROM information_schema.tables
                                         WHERE table_schema IN ('staging','silver','gold') ORDER BY 1, 2""").fetchall():
        filas.append((esquema, tabla, con.execute(f'SELECT count(*) FROM {esquema}."{tabla}"').fetchone()[0]))
    # tiempo de una consulta típica del tablero (demanda por modo, zona y hora)
    t0 = time.perf_counter()
    con.execute("""SELECT s.sistema_nombre, z.nombre_zona, t.hora, sum(f.cantidad_abordajes)
                   FROM gold.fct_abordaje f JOIN gold.dim_sistema s USING (sistema_key)
                   JOIN gold.dim_zona z USING (zona_key) JOIN gold.dim_tiempo t USING (tiempo_key)
                   GROUP BY ALL""").fetchall()
    consulta_ms = round((time.perf_counter() - t0) * 1000, 1)
    con.close()

    EVIDENCIA.mkdir(exist_ok=True)
    with open(EVIDENCIA / f"conteos-corrida-{corrida}.csv", "w", newline="") as f:
        w = csv.writer(f); w.writerow(["capa", "tabla", "filas"]); w.writerows(filas)
    metricas = {"corrida": corrida, "fecha": datetime.now().isoformat(timespec="seconds"),
                "duracion_segundos": DURACIONES, "consulta_tablero_ms": consulta_ms,
                "tamano_mb": {"datos_crudos": tamano_mb(RAIZ / "datos_red"), "bronze": tamano_mb(os.environ["BRONZE_PATH"]),
                              "warehouse_staging_silver_gold": tamano_mb(os.environ["WAREHOUSE_PATH"])}}
    (EVIDENCIA / f"metricas-corrida-{corrida}.json").write_text(json.dumps(metricas, indent=2, ensure_ascii=False))
    with open(EVIDENCIA / "bitacora.log", "a") as f:
        f.write(f"{metricas['fecha']} corrida={corrida} duraciones={DURACIONES} consulta_ms={consulta_ms}\n")
    get_run_logger().info(f"conteos guardados en evidencia/conteos-corrida-{corrida}.csv ({len(filas)} tablas)")


@task
def exportar_entregables():
    """Exporta a entregables/ las tablas de conclusiones (conteos, cuarentena, CDC) como CSV."""
    sys.path.insert(0, str(RAIZ / "herramientas"))
    import exportar as ex
    ex.main()


@flow(name="red-metropolitana-fase1", log_prints=True)
def pipeline(corrida: int = 1):
    ingesta_batch()
    ingesta_cdc()
    ingesta_streaming()
    vaciar_staging()
    dbt_build()
    verificar_linaje()
    contar(corrida)
    exportar_entregables()


if __name__ == "__main__":
    p = argparse.ArgumentParser()
    p.add_argument("--corrida", type=int, default=1)
    pipeline(corrida=p.parse_args().corrida)
