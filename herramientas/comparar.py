"""1.5 Compara los conteos de dos corridas lado a lado: evidencia/comparacion-corridas.csv"""
import csv, sys
from pathlib import Path
EV = Path(__file__).resolve().parent.parent / "evidencia"
a, b = (sys.argv[1], sys.argv[2]) if len(sys.argv) > 2 else ("1", "2")
leer = lambda n: {(r["capa"], r["tabla"]): int(r["filas"]) for r in csv.DictReader(open(EV / f"conteos-corrida-{n}.csv"))}
c1, c2 = leer(a), leer(b)
filas = [(k[0], k[1], c1.get(k), c2.get(k), c1.get(k) == c2.get(k)) for k in sorted(set(c1) | set(c2))]
with open(EV / "comparacion-corridas.csv", "w", newline="") as f:
    w = csv.writer(f); w.writerow(["capa", "tabla", f"filas_corrida_{a}", f"filas_corrida_{b}", "identico"]); w.writerows(filas)
dif = [x for x in filas if not x[4]]
print(f"{len(filas)} tablas comparadas, {len(dif)} diferencias -> {'IDENTICOS' if not dif else 'NO IDENTICOS'}")
sys.exit(1 if dif else 0)
