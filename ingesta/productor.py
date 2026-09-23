"""Productor Kafka: publica transmetro_validaciones.csv y aerometro_boardings.csv línea por línea."""
import json, os, sys, time
from kafka import KafkaProducer
from comun import conectar
from streaming import FUENTES_STREAMING, TOPIC, mensajes

BOOTSTRAP = os.getenv("KAFKA_BOOTSTRAP", "localhost:9092")
PAUSA = float(os.getenv("KAFKA_PAUSA_SEG", "0"))     # >0 para ver la simulación "en vivo"


def main():
    con = conectar()
    prod = KafkaProducer(bootstrap_servers=BOOTSTRAP, acks="all", linger_ms=20,
                         key_serializer=str.encode,
                         value_serializer=lambda v: json.dumps(v, ensure_ascii=False).encode())
    for fuente in FUENTES_STREAMING:
        n = 0
        for llave, msg in mensajes(fuente, con):
            prod.send(TOPIC.format(fuente=fuente), key=llave, value=msg)
            n += 1
            if PAUSA: time.sleep(PAUSA)
        prod.flush()
        if n: print(f"  publicado {fuente}: {n-1:,} eventos + marcador de fin")
    prod.close(); con.close()


if __name__ == "__main__":
    sys.exit(main())
