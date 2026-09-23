"""
Exporta a archivos (CSV) las tablas de conclusiones de la Fase 1, para entregarlas sin necesidad del warehouse.
Se ejecuta al final de cada corrida del flujo (tarea exportar_entregables) y también se puede correr solo:
    python herramientas/exportar.py
"""
import os
from pathlib import Path
import duckdb

RAIZ = Path(__file__).resolve().parent.parent
WH = os.getenv("WAREHOUSE_PATH", str(RAIZ / "warehouse" / "red-metropolitana.duckdb"))
WH = WH if Path(WH).is_absolute() else str(RAIZ / WH)
OUT = RAIZ / "entregables"

EXPORTS = {
    "1.1-conteos-por-archivo.csv": """
        SELECT archivo, via, filas_origen AS filas_en_archivo, filas_bronze AS filas_en_bronze,
               filas_origen = filas_bronze AS cuadra,
               regexp_extract(replace(ruta_bronze, chr(92), '/'), '(lake/.*)$', 1) AS ruta_bronze
        FROM control.ingest_log ORDER BY via, archivo""",
    "1.2-padron-antes-despues.csv":          "SELECT * FROM silver.padron_resumen_cdc",
    "1.2-padron-antes-despues-por-operador.csv": "SELECT * FROM silver.padron_resumen_por_operador",
    "1.2-usuarios-unicos-por-operador.csv":  "SELECT * FROM silver.usuarios_unicos_por_operador",
    "1.2-padron-transmetro-vigente.csv":     """
        SELECT tarjeta, perfil, zona_residencia_origen, activa, fecha_baja, ultima_operacion, ultima_secuencia
        FROM silver.padron_transmetro_vigente ORDER BY tarjeta""",
    "1.3-cuarentena.csv":                    "SELECT * FROM silver.silver_cuarentena ORDER BY sistema, motivo_rechazo, evento_id",
    "1.3-conteo-por-regla-de-calidad.csv":   "SELECT * FROM silver.silver_calidad_resumen",
    "1.3-identidad-usuario-diagnostico.csv": "SELECT * FROM silver.silver_identidad_diagnostico",
    "1.3-conformacion-zona.csv":             "SELECT * FROM silver.silver_zona_mapeo ORDER BY zona_key, fuente",
}

def main():
    OUT.mkdir(exist_ok=True)
    con = duckdb.connect(WH, read_only=True)
    tablas = [t for (t,) in con.execute("SELECT table_name FROM information_schema.tables "
                                        "WHERE table_schema = 'gold' ORDER BY 1").fetchall()]
    EXPORTS["1.4-filas-en-gold.csv"] = " UNION ALL ".join(
        f"SELECT '{t}' AS tabla, count(*) AS filas FROM gold.{t}" for t in tablas)
    for nombre, q in EXPORTS.items():
        destino = OUT / nombre
        con.execute(f"COPY ({q}) TO '{destino}' (HEADER, DELIMITER ',')")
        n = con.execute(f"SELECT count(*) FROM read_csv('{destino}')").fetchone()[0]
        print(f"  {nombre:45s} {n:>8,} filas")
    con.close()

if __name__ == "__main__":
    main()
