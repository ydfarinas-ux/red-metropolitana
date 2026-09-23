"""
Vía CDC: log de cambios del padrón de usuarios de Transmetro (INSERT / UPDATE / DELETE).

Bronze guarda el log crudo completo, en el orden en que llegó. Aplicar las operaciones
(orden de secuencia, DELETE = baja lógica) se hace en dbt: models/staging/cdc/.
"""
import sys
from comun import FUENTES, DATOS, conectar, hash_archivo, filas_en_origen, ya_ingerido, ruta_particion, registrar


def main():
    con = conectar()
    archivo, via = FUENTES["cdc_padron_usuarios"]
    ruta = DATOS / archivo
    h = hash_archivo(ruta)
    if ya_ingerido(con, h):
        print(f"  [{via:9s}] cdc_padron_usuarios           ya ingerido (hash {h[:8]}), se omite")
        return
    destino = ruta_particion("cdc_padron_usuarios", h)
    con.execute(f"""
        COPY (SELECT *, (now() AT TIME ZONE 'UTC') AS _ingested_at, '{archivo}' AS _source_file,
                     '{h}' AS _file_hash, 'cdc' AS _via
              FROM read_csv('{ruta}', all_varchar=true, header=true))
        TO '{destino}' (FORMAT PARQUET)""")
    registrar(con, h, "cdc_padron_usuarios", archivo, via, filas_en_origen(ruta), destino)
    con.close()


if __name__ == "__main__":
    sys.exit(main())
