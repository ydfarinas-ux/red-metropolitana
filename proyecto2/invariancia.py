"""2.4 Ensayo de la prueba de invariancia antes de la defensa.

El día de la calificación se reciben los mismos datos con 30 días más y predecir.py debe dar, para el corte C,
exactamente el mismo CSV. Ese escenario se puede ensayar hoy con el corte B, que tiene 30 días de datos posteriores:

  1. predecir.py con los datos completos (1 jun - 29 ago) y fecha de corte B (31 jul).
  2. predecir.py con los mismos archivos recortados en binario a lo anterior al 31 de julio (como si fuera el día del corte).
  3. Los dos CSV deben ser idénticos byte a byte (mismo SHA-256).

Además se compara la predicción del corte C que se entrega contra una corrida nueva de predecir.py.
Uso: python proyecto2/invariancia.py --datos datos_red
"""
import argparse
import csv
import hashlib
import json
import shutil
import subprocess
import sys
from datetime import date, datetime
from pathlib import Path

if __package__:
    from .config import CORTES, RAIZ, SALIDA
    from .datos_modelo import anotar_bitacora, commit_y_fecha
else:
    from config import CORTES, RAIZ, SALIDA
    from datos_modelo import anotar_bitacora, commit_y_fecha

TRABAJO = RAIZ / '.invariancia'


def reglas(corte):
    t = date.fromisoformat(corte)
    return {
        'transmetro_validaciones.csv': ('fecha_hora', lambda v: v[:10] < corte),
        'transurbano_transacciones.csv': ('fecha', lambda v: datetime.strptime(v, '%d/%m/%Y').date() < t),
        'aerometro_boardings.csv': ('timestamp_utc', lambda v: v < f'{corte}T06:00:00Z'),   # 00:00 en Guatemala
        'cdc_padron_usuarios.csv': ('commit_ts', lambda v: v[:10] < corte),
    }


def recortar(origen, destino, corte):
    """Igual que la prueba de recorte de 1.3: conserva los bytes exactos de cada línea anterior al corte."""
    destino.mkdir(parents=True, exist_ok=True)
    r = reglas(corte)
    conteos = {}
    for entrada in sorted(origen.iterdir()):
        salida = destino / entrada.name
        if entrada.name in r:
            columna, conservar = r[entrada.name]
            n = 0
            with entrada.open('rb') as src, salida.open('wb') as dst:
                encabezado = next(src)
                dst.write(encabezado)
                indice = next(csv.reader([encabezado.decode('utf-8-sig')])).index(columna)
                for linea in src:
                    try:
                        ok = conservar(next(csv.reader([linea.decode('utf-8')]))[indice])
                    except (ValueError, IndexError):
                        ok = False
                    if ok:
                        dst.write(linea)
                        n += 1
        elif entrada.name == 'metroriel_viajes.jsonl':
            n = 0
            with entrada.open('rb') as src, salida.open('wb') as dst:
                for linea in src:
                    try:
                        ok = json.loads(linea)['entry']['ts'][:10] < corte
                    except (ValueError, KeyError, TypeError):
                        ok = False
                    if ok:
                        dst.write(linea)
                        n += 1
        else:
            shutil.copyfile(entrada, salida)
            n = None
        conteos[entrada.name] = n
    return conteos


def predecir(datos, corte, salida):
    subprocess.run([sys.executable, str(RAIZ / 'predecir.py'), '--datos', str(datos), '--fecha-corte', corte,
                    '--salida', str(salida)], cwd=RAIZ, check=True)
    return hashlib.sha256(salida.read_bytes()).hexdigest()


def main():
    p = argparse.ArgumentParser()
    p.add_argument('--datos', default=str(RAIZ / 'datos_red'))
    a = p.parse_args()
    datos = Path(a.datos).resolve()
    shutil.rmtree(TRABAJO / 'datos_recortados', ignore_errors=True)
    TRABAJO.mkdir(exist_ok=True)

    corte = CORTES['B']
    conteos = recortar(datos, TRABAJO / 'datos_recortados', corte)
    sha_completo = predecir(datos, corte, TRABAJO / 'corte_b_datos_completos.csv')
    sha_recorte = predecir(TRABAJO / 'datos_recortados', corte, TRABAJO / 'corte_b_datos_hasta_el_corte.csv')

    entregado = RAIZ / 'predicciones' / f"predicciones_corte_{CORTES['C']}.csv"
    sha_c_entregado = hashlib.sha256(entregado.read_bytes()).hexdigest() if entregado.exists() else None
    sha_c_nuevo = predecir(datos, CORTES['C'], TRABAJO / 'corte_c_repeticion.csv')

    commit, fecha = commit_y_fecha()
    resultado = {
        'fecha': fecha, 'commit': commit,
        'ensayo_corte_b': {'fecha_corte': corte, 'datos_completos_hasta': '2026-08-29',
                           'datos_recortados_hasta': '2026-07-30', 'lineas_conservadas': conteos,
                           'sha256_con_30_dias_mas': sha_completo, 'sha256_solo_hasta_el_corte': sha_recorte,
                           'identicos': sha_completo == sha_recorte},
        'corte_c': {'sha256_entregado': sha_c_entregado, 'sha256_repeticion': sha_c_nuevo,
                    'identicos': sha_c_entregado == sha_c_nuevo},
    }
    (SALIDA / '2.4-ensayo-invariancia.json').write_text(json.dumps(resultado, indent=2, ensure_ascii=False), encoding='utf-8')
    anotar_bitacora(f"{fecha} · commit {commit} · 2.4 ensayo de invariancia: corte B con 30 días más contra datos hasta el "
                    f"corte → idénticos={resultado['ensayo_corte_b']['identicos']}; corte C entregado contra repetición → "
                    f"idénticos={resultado['corte_c']['identicos']}.")
    print(json.dumps(resultado, indent=2, ensure_ascii=False))
    if not (resultado['ensayo_corte_b']['identicos'] and resultado['corte_c']['identicos']):
        raise SystemExit('La prueba de invariancia falló')


if __name__ == '__main__':
    main()
