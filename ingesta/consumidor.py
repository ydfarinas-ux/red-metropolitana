"""Consumidor Kafka: lee los tópicos de streaming y escribe a Bronze (Parquet particionado por fecha)."""
import json, os, sys
from kafka import KafkaConsumer
from comun import conectar
from streaming import FUENTES_STREAMING, TOPIC, Acumulador

BOOTSTRAP = os.getenv("KAFKA_BOOTSTRAP", "localhost:9092")
INACTIVIDAD_MS = int(os.getenv("KAFKA_TIMEOUT_MS", "15000"))


def main():
    con = conectar()
    cons = KafkaConsumer(*[TOPIC.format(fuente=f) for f in FUENTES_STREAMING],
                         bootstrap_servers=BOOTSTRAP, group_id="bronze-writer",
                         auto_offset_reset="earliest", enable_auto_commit=False,
                         consumer_timeout_ms=INACTIVIDAD_MS,
                         value_deserializer=lambda b: json.loads(b.decode()))
    acc = Acumulador(con)
    for m in cons:
        acc.procesar(m.value)
        if m.value.get("fin"):
            cons.commit()          # se confirma el offset solo cuando el archivo ya está en Bronze
    cons.close(); con.close()
    print(f"  consumidor: {acc.completados} archivo(s) escritos a Bronze")


if __name__ == "__main__":
    sys.exit(main())
