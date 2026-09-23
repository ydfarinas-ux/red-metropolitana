"""
Vía BATCH: los 4 catálogos, los viajes de MetroRiel (JSON Lines anidado) y Transurbano.

- CSV: se lee todo como texto (all_varchar) para que Bronze guarde el dato tal como llegó.
- JSONL: se conserva la estructura anidada (STRUCT) en Parquet, sin aplanar.
- Idempotente: si el hash del archivo ya está en control.ingest_log, no se vuelve a cargar.
"""
import sys
from comun import FUENTES, DATOS, conectar, hash_archivo, filas_en_origen, ya_ingerido, ruta_particion, registrar


def cargar(fuente, con):
    archivo, via = FUENTES[fuente]
    ruta = DATOS / archivo
    h = hash_archivo(ruta)
    if ya_ingerido(con, h):
        print(f"  [{via:9s}] {fuente:28s} ya ingerido (hash {h[:8]}), se omite")
        return
    destino = ruta_particion(fuente, h)
    if archivo.endswith(".jsonl"):
        # formatos imposibles a propósito: evita que DuckDB convierta los timestamps y se pierda el '-06:00'
        lector = (f"read_json('{ruta}', format='newline_delimited', maximum_depth=-1, "
                  f"timestampformat='%Y%m%d%H%M%S%f', dateformat='%Y%m%d')")
    else:
        lector = f"read_csv('{ruta}', all_varchar=true, header=true)"
    con.execute(f"""
        COPY (SELECT *, (now() AT TIME ZONE 'UTC') AS _ingested_at, '{archivo}' AS _source_file,
                     '{h}' AS _file_hash, '{via}' AS _via
              FROM {lector})
        TO '{destino}' (FORMAT PARQUET)""")
    registrar(con, h, fuente, archivo, via, filas_en_origen(ruta), destino)


def main():
    con = conectar()
    for fuente, (_, via) in FUENTES.items():
        if via == "batch":
            cargar(fuente, con)
    con.close()


if __name__ == "__main__":
    sys.exit(main())
