"""2.4 Predicciones de abandono para una fecha de corte, con el modelo guardado (no reentrena).

Uso:
    python predecir.py --datos datos_red --fecha-corte 2026-08-30

Qué hace:
  1. Carga el modelo guardado en modelos/ (pipeline completo de scikit-learn + umbral + versión).
  2. Busca un warehouse construido exactamente con los archivos de --datos (compara el MD5 de cada archivo con
     control.ingest_log). Si el warehouse del proyecto los tiene, lo usa; si no, corre el flujo del Proyecto 1
     (Bronze -> dbt Silver) en .prediccion/ sin tocar el warehouse principal.
  3. Calcula la población y las 23 features del corte con el MISMO código de la Fase 1 (proyecto2/features.py):
     solo eventos anteriores a las 00:00 de la fecha de corte.
  4. Escribe un CSV con unidad_id, tarjetas, puntaje y contactar (puntaje >= umbral del modelo).

Prueba de invariancia: con 30 días más de datos el CSV debe salir idéntico, porque nada de lo que se calcula
usa eventos posteriores al corte (ni las features, ni la población, ni las tarjetas de la unidad).
"""
import argparse
import hashlib
import json
import os
import subprocess
import sys
import time
from datetime import date
from pathlib import Path

RAIZ = Path(__file__).resolve().parent
sys.path.insert(0, str(RAIZ / 'proyecto2'))

import duckdb   # noqa: E402
import joblib   # noqa: E402

import features   # noqa: E402
from config import VENTANA_DIAS, ruta_warehouse   # noqa: E402
from datos_modelo import preparar   # noqa: E402

ARCHIVOS = ['aerometro_boardings.csv', 'am_estaciones.csv', 'cdc_padron_usuarios.csv', 'metroriel_viajes.jsonl',
            'mr_estaciones.csv', 'tm_estaciones.csv', 'transmetro_validaciones.csv', 'transurbano_transacciones.csv',
            'tu_paradas.csv']
MODELO_POR_DEFECTO = RAIZ / 'modelos' / 'modelo_abandono_v1.0.0.joblib'


def cargar_env():
    """Misma precedencia que flows/pipeline.py: variables del proceso antes que .env (la sal del seudónimo vive ahí)."""
    if (RAIZ / '.env').exists():
        for linea in (RAIZ / '.env').read_text(encoding='utf-8').splitlines():
            if linea.strip() and not linea.startswith('#') and '=' in linea:
                k, v = linea.split('=', 1)
                os.environ.setdefault(k.strip(), v.split('#', 1)[0].strip())


def md5(ruta):
    h = hashlib.md5()
    with open(ruta, 'rb') as f:
        for bloque in iter(lambda: f.read(1 << 20), b''):
            h.update(bloque)
    return h.hexdigest()


def warehouse_con_datos(datos, forzar):
    """Devuelve la ruta de un warehouse cuyo Bronze se cargó exactamente con los archivos de `datos`."""
    faltan = [a for a in ARCHIVOS if not (datos / a).exists()]
    if faltan:
        raise SystemExit(f'Faltan archivos en {datos}: {faltan}')
    hashes = {md5(datos / a) for a in ARCHIVOS}

    def coincide(wh):
        if not Path(wh).exists():
            return False
        try:
            with duckdb.connect(str(wh), read_only=True) as con:
                cargados = {h for (h,) in con.execute('select file_hash from control.ingest_log').fetchall()}
                silver = con.execute("select count(*) from information_schema.tables where table_schema = 'silver' "
                                     "and table_name = 'silver_abordajes'").fetchone()[0]
        except duckdb.Error:
            return False
        return cargados == hashes and silver == 1

    principal = ruta_warehouse()
    if not forzar and coincide(principal):
        print(f'  warehouse del proyecto construido con estos archivos: {principal}')
        return principal
    destino = RAIZ / '.prediccion' / hashlib.md5(''.join(sorted(hashes)).encode()).hexdigest()[:12]
    wh = destino / 'warehouse.duckdb'
    if not forzar and coincide(wh):
        print(f'  se reutiliza el warehouse de predicción {wh}')
        return str(wh)
    print(f'  construyendo Silver con los archivos de {datos} en {destino} (flujo del Proyecto 1, sin tocar el principal)')
    env = os.environ.copy()
    env.update(DATOS_RED=str(datos), BRONZE_PATH=str(destino / 'lake' / 'bronze'), WAREHOUSE_PATH=str(wh),
               EVIDENCIA_PATH=str(destino / 'evidencia'), STREAMING_MODO='simulado', PYTHONIOENCODING='utf-8')
    (destino / 'evidencia').mkdir(parents=True, exist_ok=True)
    with (destino / 'evidencia' / 'pipeline.log').open('w', encoding='utf-8') as log:
        r = subprocess.run([sys.executable, str(RAIZ / 'flows' / 'pipeline.py'), '--desde-cero', '--solo-carga'],
                           cwd=RAIZ, env=env, stdout=log, stderr=subprocess.STDOUT)
    if r.returncode:
        raise SystemExit(f'Falló el flujo; ver {destino / "evidencia" / "pipeline.log"}')
    return str(wh)


def tarjetas_por_unidad(con, fecha_corte):
    """Llaves originales de la unidad vistas en la ventana de features [t - 28 días, t): no dependen de datos futuros."""
    t = date.fromisoformat(fecha_corte)
    return con.execute(f"""
        select usuario_sk as unidad_id, string_agg(distinct usuario_llave_origen, ';' order by usuario_llave_origen) as tarjetas
        from silver.silver_abordajes
        where ts_local >= timestamp '{t} 00:00:00' - interval {VENTANA_DIAS} day and ts_local < timestamp '{t} 00:00:00'
        group by usuario_sk
    """).df()


def main():
    p = argparse.ArgumentParser(description='Predicciones de abandono a 30 días para una fecha de corte')
    p.add_argument('--datos', required=True, help='carpeta con los 9 archivos de la Agencia')
    p.add_argument('--fecha-corte', required=True, help='AAAA-MM-DD (las 00:00 hora local de ese día)')
    p.add_argument('--modelo', default=str(MODELO_POR_DEFECTO))
    p.add_argument('--salida', help='CSV de salida (por defecto predicciones/predicciones_corte_<fecha>.csv)')
    p.add_argument('--reconstruir', action='store_true', help='reconstruye Silver aunque ya exista un warehouse con esos datos')
    a = p.parse_args()

    t0 = time.perf_counter()
    cargar_env()
    fecha = date.fromisoformat(a.fecha_corte).isoformat()
    datos = Path(a.datos)
    datos = (datos if datos.is_absolute() else Path.cwd() / datos).resolve()

    paquete = joblib.load(a.modelo)          # solo se carga: este script nunca llama a fit
    modelo, umbral = paquete['pipeline'], paquete['umbral']
    print(f"  modelo {paquete['version']} ({paquete['nombre']}), umbral {umbral:.4f}")

    t1 = time.perf_counter()
    wh = warehouse_con_datos(datos, a.reconstruir)
    seg_silver = time.perf_counter() - t1

    t2 = time.perf_counter()
    with duckdb.connect(wh, read_only=True) as con:
        df = features.calcular(con, fecha)
        tarjetas = tarjetas_por_unidad(con, fecha)
    df = preparar(df.drop(columns=['etiqueta']))
    seg_features = time.perf_counter() - t2
    if df.empty:
        raise SystemExit(f'La población del corte {fecha} está vacía: ¿los datos cubren los 28 días anteriores?')

    t3 = time.perf_counter()
    puntaje = modelo.predict_proba(df[paquete['features']])[:, 1]
    seg_prediccion = time.perf_counter() - t3

    salida = df[['unidad_id']].merge(tarjetas, on='unidad_id', how='left', validate='one_to_one')
    salida['puntaje'] = puntaje.round(6)
    salida['contactar'] = (puntaje >= umbral).astype(int)
    salida = salida.sort_values('unidad_id').reset_index(drop=True)

    ruta = Path(a.salida) if a.salida else RAIZ / 'predicciones' / f'predicciones_corte_{fecha}.csv'
    ruta.parent.mkdir(parents=True, exist_ok=True)
    salida.to_csv(ruta, index=False, lineterminator='\n')

    resumen = {'fecha_corte': fecha, 'modelo': paquete['version'], 'umbral': umbral, 'poblacion': len(salida),
               'contactar': int(salida.contactar.sum()), 'puntaje_medio': round(float(puntaje.mean()), 4),
               'sha256_csv': hashlib.sha256(ruta.read_bytes()).hexdigest(),
               'segundos': {'silver': round(seg_silver, 2), 'features': round(seg_features, 2),
                            'prediccion': round(seg_prediccion, 3), 'total': round(time.perf_counter() - t0, 2)}}
    ruta.with_suffix('.json').write_text(json.dumps(resumen, indent=2, ensure_ascii=False), encoding='utf-8')
    print(json.dumps(resumen, indent=2, ensure_ascii=False))
    print(f'  CSV: {ruta}')


if __name__ == '__main__':
    main()
