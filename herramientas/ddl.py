"""Genera docs/1.4-ddl-gold.sql a partir de las tablas Gold construidas, con PK y FK, y lo valida en una BD vacía."""
import duckdb, os
from pathlib import Path
RAIZ = Path(__file__).resolve().parent.parent
WH = os.getenv("WAREHOUSE_PATH", str(RAIZ / "warehouse" / "red-metropolitana.duckdb"))

PK = {"dim_fecha": "fecha_key", "dim_tiempo": "tiempo_key", "dim_sistema": "sistema_key", "dim_zona": "zona_key",
      "dim_estacion": "estacion_key", "dim_usuario": "usuario_sk", "fct_abordaje": "abordaje_key",
      "fct_trayecto_metroriel": "trayecto_key", "fct_padron_diario": "fecha_key, zona_key, perfil, operador_tarjeta"}
FK = {
    "dim_tiempo":   [("fecha_key", "dim_fecha", "fecha_key")],
    "dim_estacion": [("sistema_key", "dim_sistema", "sistema_key"), ("zona_key", "dim_zona", "zona_key")],
    "fct_abordaje": [("tiempo_key", "dim_tiempo", "tiempo_key"), ("fecha_key", "dim_fecha", "fecha_key"),
                     ("usuario_sk", "dim_usuario", "usuario_sk"), ("sistema_key", "dim_sistema", "sistema_key"),
                     ("estacion_key", "dim_estacion", "estacion_key"), ("zona_key", "dim_zona", "zona_key")],
    "fct_trayecto_metroriel": [("tiempo_key", "dim_tiempo", "tiempo_key"), ("fecha_key", "dim_fecha", "fecha_key"),
                     ("usuario_sk", "dim_usuario", "usuario_sk"),
                     ("estacion_origen_key", "dim_estacion", "estacion_key"), ("estacion_destino_key", "dim_estacion", "estacion_key"),
                     ("zona_origen_key", "dim_zona", "zona_key"), ("zona_destino_key", "dim_zona", "zona_key")],
    "fct_padron_diario": [("fecha_key", "dim_fecha", "fecha_key")],   # zona_key admite -1 (desconocida): sin FK dura
}
ORDEN = ["dim_fecha", "dim_tiempo", "dim_sistema", "dim_zona", "dim_estacion", "dim_usuario",
         "fct_abordaje", "fct_trayecto_metroriel", "fct_padron_diario"]

con = duckdb.connect(WH, read_only=True)
out = ["-- DDL de la capa Gold (DuckDB / PostgreSQL compatible salvo tipos menores).",
       "-- Generado desde el warehouse con herramientas/ddl.py. dbt construye estas tablas;",
       "-- este archivo documenta su estructura, llaves primarias y foráneas.", "", "CREATE SCHEMA IF NOT EXISTS gold;", ""]
for t in ORDEN:
    cols = con.execute("""SELECT column_name, data_type FROM information_schema.columns
                          WHERE table_schema='gold' AND table_name=? ORDER BY ordinal_position""", [t]).fetchall()
    lineas = [f"    {c:<24} {tipo}{' NOT NULL' if c in [x.strip() for x in PK[t].split(',')] else ''}" for c, tipo in cols]
    lineas.append(f"    PRIMARY KEY ({PK[t]})")
    for col, ref, refcol in FK.get(t, []):
        lineas.append(f"    FOREIGN KEY ({col}) REFERENCES gold.{ref} ({refcol})")
    out.append(f"CREATE TABLE gold.{t} (\n" + ",\n".join(lineas) + "\n);\n")
con.close()
ddl = "\n".join(out)
(RAIZ / "docs" / "1.4-ddl-gold.sql").write_text(ddl)
duckdb.connect().execute(ddl)          # validación: el DDL corre en una base vacía
print("DDL generado y validado:", len(ORDEN), "tablas")
