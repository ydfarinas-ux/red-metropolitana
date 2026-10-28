"""Parámetros del Proyecto 2. Los tres cortes usan el mismo código, solo cambia la fecha."""
import os
from pathlib import Path

RAIZ = Path(__file__).resolve().parent.parent

# fecha de corte t = 00:00 hora local del día de la decisión
CORTES = {"A": "2026-07-01", "B": "2026-07-31", "C": "2026-08-30"}
VENTANA_DIAS = 28        # features: [t - 28 días, t)
HORIZONTE_DIAS = 30      # etiqueta: [t, t + 30 días)
MIN_ABORDAJES = 2        # población: al menos 2 abordajes válidos en la ventana
SEMILLA = 2026

SALIDA = RAIZ / "entregables" / "proyecto2"


def ruta_warehouse():
    p = Path(os.environ.get("WAREHOUSE_PATH", "warehouse/red-metropolitana.duckdb"))
    return str(p if p.is_absolute() else RAIZ / p)
