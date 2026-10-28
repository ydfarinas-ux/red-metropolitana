"""1.1 Tabla de conteos (esperadas contra cargadas en Bronze) y tiempo de cada etapa del flujo."""
import csv
import duckdb
from config import RAIZ, SALIDA, ruta_warehouse


def main(duraciones=None):
    SALIDA.mkdir(parents=True, exist_ok=True)
    esperadas = {r["archivo"]: int(r["filas_esperadas"]) for r in csv.DictReader(open(RAIZ / "proyecto2" / "conteos-esperados.csv", encoding="utf-8"))}
    con = duckdb.connect(ruta_warehouse(), read_only=True)
    cargadas = dict(con.execute("select archivo, filas_bronze from control.ingest_log").fetchall())
    con.close()
    with open(SALIDA / "1.1-conteos.csv", "w", newline="", encoding="utf-8") as f:
        w = csv.writer(f); w.writerow(["archivo", "filas_esperadas", "filas_cargadas", "diferencia"])
        for archivo in sorted(esperadas):
            c = cargadas.get(archivo, 0)
            w.writerow([archivo, esperadas[archivo], c, c - esperadas[archivo]])
    if duraciones:
        with open(SALIDA / "1.1-tiempos.csv", "w", newline="", encoding="utf-8") as f:
            w = csv.writer(f); w.writerow(["etapa", "segundos"])
            for etapa, seg in duraciones.items():
                w.writerow([etapa, seg])
            w.writerow(["total", round(sum(duraciones.values()), 2)])
    print("  1.1 conteos y tiempos guardados en entregables/proyecto2/")


if __name__ == "__main__":
    main()
