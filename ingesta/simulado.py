"""Corre la vía streaming sin Docker (mismo productor/consumidor, transporte en memoria)."""
import sys
from comun import conectar
from streaming import simular

if __name__ == "__main__":
    con = conectar(); simular(con); con.close()
