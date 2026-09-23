"""Utilidades compartidas por las tres vías de ingesta (batch, streaming y CDC)."""
import hashlib, os, csv
from datetime import datetime, date, timezone
from pathlib import Path
import duckdb, pyarrow as pa, pyarrow.parquet as pq

RAIZ = Path(__file__).resolve().parent.parent


def _ruta(var, defecto):
    """Rutas relativas se resuelven desde la raíz del proyecto, no desde donde se ejecuta el script."""
    p = Path(os.getenv(var, defecto))
    return p if p.is_absolute() else RAIZ / p


DATOS = _ruta("DATOS_RED", "datos_red")
BRONZE = _ruta("BRONZE_PATH", "lake/bronze")
WAREHOUSE = str(_ruta("WAREHOUSE_PATH", "warehouse/red-metropolitana.duckdb"))

# fuente -> (archivo, vía). La vía de cada fuente está justificada en docs/1.1-ingesta-bronze.md
FUENTES = {
    "tm_estaciones":                 ("tm_estaciones.csv", "batch"),
    "tu_paradas":                    ("tu_paradas.csv", "batch"),
    "mr_estaciones":                 ("mr_estaciones.csv", "batch"),
    "am_estaciones":                 ("am_estaciones.csv", "batch"),
    "metroriel_viajes":              ("metroriel_viajes.jsonl", "batch"),
    "transurbano_transacciones":     ("transurbano_transacciones.csv", "batch"),   # vía a criterio: batch
    "transmetro_validaciones":       ("transmetro_validaciones.csv", "streaming"),
    "aerometro_boardings":           ("aerometro_boardings.csv", "streaming"),
    "cdc_padron_usuarios":           ("cdc_padron_usuarios.csv", "cdc"),
}


def conectar():
    Path(WAREHOUSE).parent.mkdir(parents=True, exist_ok=True)
    con = duckdb.connect(WAREHOUSE)
    con.execute("CREATE SCHEMA IF NOT EXISTS control")
    con.execute("""CREATE TABLE IF NOT EXISTS control.ingest_log(
        file_hash TEXT PRIMARY KEY, fuente TEXT, archivo TEXT, via TEXT,
        filas_origen BIGINT, filas_bronze BIGINT, ruta_bronze TEXT, ingerido_en TIMESTAMP)""")
    return con


def hash_archivo(ruta):
    h = hashlib.md5()
    with open(ruta, "rb") as f:
        for bloque in iter(lambda: f.read(1 << 20), b""):
            h.update(bloque)
    return h.hexdigest()


def filas_en_origen(ruta):
    """Filas de datos en el archivo crudo (sin encabezado en CSV)."""
    with open(ruta, "rb") as f:
        n = sum(1 for linea in f if linea.strip())
    return n - 1 if str(ruta).endswith(".csv") else n


def ya_ingerido(con, file_hash):
    return con.execute("SELECT 1 FROM control.ingest_log WHERE file_hash = ?", [file_hash]).fetchone() is not None


def ruta_particion(fuente, file_hash):
    """Bronze particionado por fecha de ingesta. El nombre del archivo es el hash: re-escribirlo es idempotente."""
    p = BRONZE / f"fuente={fuente}" / f"fecha_ingesta={date.today().isoformat()}"
    p.mkdir(parents=True, exist_ok=True)
    return p / f"{file_hash}.parquet"


def registrar(con, file_hash, fuente, archivo, via, filas_origen, ruta):
    filas_bronze = con.execute(f"SELECT count(*) FROM read_parquet('{ruta}')").fetchone()[0]
    con.execute("INSERT INTO control.ingest_log VALUES (?,?,?,?,?,?,?,?)",
                [file_hash, fuente, archivo, via, filas_origen, filas_bronze, str(ruta),
                 datetime.now(timezone.utc).replace(tzinfo=None)])
    estado = "OK" if filas_origen == filas_bronze else "DIFERENCIA"
    print(f"  [{via:9s}] {fuente:28s} origen={filas_origen:>8,}  bronze={filas_bronze:>8,}  {estado}")
    return filas_bronze


def escribir_parquet(filas, ruta):
    """Escribe una lista de dicts como Parquet, todo como texto: Bronze no castea."""
    tabla = pa.Table.from_pylist(filas)
    tabla = tabla.cast(pa.schema([pa.field(c, pa.string()) for c in tabla.column_names]))
    pq.write_table(tabla, ruta)
