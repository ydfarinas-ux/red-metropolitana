"""
Lógica común de la vía STREAMING (Transmetro validaciones y Aerómetro boardings).

En producción estos eventos llegan uno a uno desde los torniquetes. Aquí se simula
publicando el CSV línea por línea. Cada mensaje lleva su llave  <hash_archivo>:<numero_linea>,
así el consumidor puede deduplicar si Kafka re-entrega un mensaje (entrega "al menos una vez").
"""
import csv, json
from datetime import datetime, timezone
from comun import FUENTES, DATOS, hash_archivo, filas_en_origen, ya_ingerido, ruta_particion, registrar, escribir_parquet

FUENTES_STREAMING = [f for f, (_, via) in FUENTES.items() if via == "streaming"]
TOPIC = "red.{fuente}"


def mensajes(fuente, con):
    """Genera los mensajes de un archivo, línea por línea. Si el archivo ya se ingirió, no genera nada."""
    archivo, _ = FUENTES[fuente]
    ruta = DATOS / archivo
    h = hash_archivo(ruta)
    if ya_ingerido(con, h):
        print(f"  [streaming] {fuente:28s} ya ingerido (hash {h[:8]}), se omite")
        return
    n = 0
    with open(ruta, newline="", encoding="utf-8") as f:
        for n, fila in enumerate(csv.DictReader(f), 1):
            yield f"{h}:{n}", {"fuente": fuente, "archivo": archivo, "file_hash": h, "linea": n, "datos": fila}
    # marcador de fin de archivo: le dice al consumidor que ya puede escribir el lote a Bronze
    yield f"{h}:fin", {"fuente": fuente, "archivo": archivo, "file_hash": h, "fin": True, "total": n}


class Acumulador:
    """Recibe mensajes, deduplica por (hash, línea) y escribe a Bronze cuando llega el fin del archivo."""

    def __init__(self, con):
        self.con = con
        self.buffers = {}          # file_hash -> {linea: fila}
        self.completados = 0

    def procesar(self, msg):
        h = msg["file_hash"]
        buf = self.buffers.setdefault(h, {})
        if not msg.get("fin"):
            fila = dict(msg["datos"])
            fila["_linea"] = str(msg["linea"])
            fila["_ingested_at"] = datetime.now(timezone.utc).strftime("%Y-%m-%d %H:%M:%S.%f")
            buf[msg["linea"]] = fila              # dict por línea = deduplicación de re-entregas
            return
        if ya_ingerido(self.con, h):
            self.buffers.pop(h, None); return
        filas = [buf[k] for k in sorted(buf)]
        for fila in filas:
            fila["_source_file"], fila["_file_hash"], fila["_via"] = msg["archivo"], h, "streaming"
        destino = ruta_particion(msg["fuente"], h)
        escribir_parquet(filas, destino)
        origen = filas_en_origen(DATOS / msg["archivo"])
        registrar(self.con, h, msg["fuente"], msg["archivo"], "streaming", origen, destino)
        if len(filas) != msg["total"]:
            print(f"  ADVERTENCIA: se esperaban {msg['total']} mensajes y llegaron {len(filas)}")
        self.buffers.pop(h, None)
        self.completados += 1


def simular(con):
    """Modo sin Docker: el mismo productor y el mismo consumidor, conectados en memoria en lugar de Kafka.
    Sirve para desarrollo; la entrega usa Kafka real (productor.py + consumidor.py)."""
    acc = Acumulador(con)
    for fuente in FUENTES_STREAMING:
        for _, msg in mensajes(fuente, con):
            acc.procesar(json.loads(json.dumps(msg)))   # serializa igual que por Kafka
    return acc.completados
