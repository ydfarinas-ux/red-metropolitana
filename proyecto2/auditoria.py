"""Prueba de recorte de los nueve archivos crudos, con control negativo.

python proyecto2/auditoria.py
python proyecto2/auditoria.py --version-anterior
La segunda opción reproduce las fórmulas flotantes originales; sus diferencias
pueden variar con el paralelismo y la plataforma. Nunca se fuerzan los conteos.
"""
import argparse
import csv
import json
import os
from pathlib import Path
import shutil
import subprocess
import sys
import time
from datetime import date, datetime, timedelta, timezone

import duckdb
import numpy as np
import pandas as pd

if __package__:
    from . import features
    from .config import CORTES, RAIZ, SALIDA, ruta_warehouse
else:
    import features
    from config import CORTES, RAIZ, SALIDA, ruta_warehouse

RECORTE = RAIZ / '.recorte'
ARCHIVOS = {
    'transmetro_validaciones.csv': ('fecha_hora', lambda v: v[:10] < CORTES['A']),
    'transurbano_transacciones.csv': ('fecha', lambda v: datetime.strptime(v, '%d/%m/%Y').date() < date.fromisoformat(CORTES['A'])),
    'aerometro_boardings.csv': ('timestamp_utc', lambda v: v < '2026-07-01T06:00:00Z'),
    'cdc_padron_usuarios.csv': ('commit_ts', lambda v: v[:10] < CORTES['A']),
    'metroriel_viajes.jsonl': None,
    **{nombre: None for nombre in ('tm_estaciones.csv', 'tu_paradas.csv', 'mr_estaciones.csv', 'am_estaciones.csv')},
}


def cargar_entorno():
    """Misma precedencia que pipeline: variables del proceso antes que .env."""
    if (RAIZ / '.env').exists():
        for linea in (RAIZ / '.env').read_text(encoding='utf-8').splitlines():
            if linea.strip() and not linea.startswith('#') and '=' in linea:
                k, v = linea.split('=', 1)
                os.environ.setdefault(k.strip(), v.split('#', 1)[0].strip())


def recortar(origen):
    """Filtra en binario para preservar exactamente los bytes de cada línea."""
    destino = RECORTE / 'datos_red'
    destino.mkdir(parents=True, exist_ok=True)
    conteos = {}
    for nombre, regla in ARCHIVOS.items():
        entrada, salida = origen / nombre, destino / nombre
        if nombre.endswith('estaciones.csv') or nombre == 'tu_paradas.csv':
            shutil.copyfile(entrada, salida)
            with entrada.open('rb') as f:
                conteos[nombre] = sum(bool(l.strip()) for l in f) - 1
            continue
        n = 0
        with entrada.open('rb') as src, salida.open('wb') as dst:
            if regla:
                encabezado = next(src)
                dst.write(encabezado)
                columnas = next(csv.reader([encabezado.decode('utf-8-sig')]))
                indice = columnas.index(regla[0])
            for linea in src:
                try:
                    if regla:
                        valores = next(csv.reader([linea.decode('utf-8')]))
                        conservar = regla[1](valores[indice])
                    else:
                        conservar = json.loads(linea)['entry']['ts'][:10] < CORTES['A']
                except (ValueError, KeyError, IndexError, TypeError):
                    conservar = False
                if conservar:
                    dst.write(linea)
                    n += 1
        conteos[nombre] = n
    return conteos


def comparar(completa, recortada, columnas):
    """Merge uno a uno; nulos iguales y tolerancia absoluta 1e-9."""
    unidos = completa.merge(recortada, on='unidad_id', how='outer',
                             suffixes=('_completo', '_recorte'), indicator=True, validate='one_to_one')
    ambos = unidos.loc[unidos['_merge'] == 'both']
    diferencias = {}
    for columna in columnas:
        a, b = ambos[columna + '_completo'], ambos[columna + '_recorte']
        if pd.api.types.is_numeric_dtype(a.dtype) and pd.api.types.is_numeric_dtype(b.dtype):
            iguales = np.isclose(a.to_numpy(dtype=float, na_value=np.nan),
                                b.to_numpy(dtype=float, na_value=np.nan), atol=1e-9, rtol=0, equal_nan=True)
        else:
            iguales = (a.eq(b) | (a.isna() & b.isna())).fillna(False).to_numpy(dtype=bool)
        n = int((~iguales).sum())
        if n:
            diferencias[columna] = n
    return {'filas_comparadas': len(ambos),
            'filas_en_un_solo_lado': int((unidos['_merge'] != 'both').sum()),
            'diferencias': sum(diferencias.values()), 'features_con_diferencias': diferencias,
            'features_comparadas': columnas}


def calcular(con, anterior=False):
    sql = features.sql_features(CORTES['A'])
    if anterior:
        sql = sql.replace('sum(cast(round(monto_q * 100) as bigint)) / 100.0 gasto_q_28d',
                          'round(sum(monto_q), 2) gasto_q_28d')
        sql = sql.replace('((2 * sum(cast(round(monto_q * 100) as bigint)) * 100 + count(*)) // (2 * count(*))) / 10000.0 tarifa_promedio_q',
                          'round(avg(monto_q), 4) tarifa_promedio_q')
    return con.execute(sql).df().drop(columns='etiqueta')


def perfil_final(con, poblacion):
    con.register('poblacion_auditoria', poblacion[['unidad_id']])
    return con.execute("""
        with final as (
            select i.usuario_sk, arg_max(p.perfil, p.ultima_secuencia) perfil_final
            from silver.padron_vigente p join silver.silver_identidad_usuario i
                on i.sistema = p.operador_tarjeta and i.llave_origen = p.tarjeta
            group by i.usuario_sk
        )
        select a.unidad_id, coalesce(f.perfil_final, 'sin_padron') perfil_final
        from poblacion_auditoria a left join final f on a.unidad_id = f.usuario_sk
        order by a.unidad_id
    """).df()


def registrar_corrida(resultado, version_anterior):
    """Anota los resultados medidos, incluso cuando la auditoría falla."""
    revision = subprocess.run(['git', 'rev-parse', '--short', 'HEAD'], cwd=RAIZ,
                              capture_output=True, text=True)
    commit = revision.stdout.strip() if revision.returncode == 0 else 'sin commit disponible'
    version = 'fórmulas flotantes anteriores' if version_anterior else 'centavos enteros'
    fallaron = ', '.join(resultado['features_con_diferencias']) or 'ninguna'
    negativo = resultado['control_negativo_perfil_final']
    explicacion = (' La suma y el promedio en punto flotante pueden variar por el orden de agregación '
                   'en paralelo; los valores a mitad de redondeo pueden cambiar en el cuarto decimal. '
                   'Esto no demuestra por sí solo una fuga temporal.') if version_anterior else ''
    with (RAIZ / 'proyecto2' / 'bitacora.md').open('a', encoding='utf-8') as f:
        f.write(f"\n- {resultado['fecha']} · commit {commit} · prueba de recorte ({version}): "
                f"{resultado['filas_comparadas']:,} filas, {resultado['diferencias']:,} diferencias, "
                f"{resultado['filas_en_un_solo_lado']:,} filas en un solo lado; features: {fallaron}. "
                f"Control negativo perfil final: {negativo['diferencias']:,} diferencias, "
                f"detectado={negativo['detectado']}.{explicacion}\n")


def main(version_anterior=False):
    inicio = time.perf_counter()
    cargar_entorno()
    origen = Path(os.environ.get('DATOS_RED', 'datos_red'))
    origen = origen if origen.is_absolute() else RAIZ / origen
    with duckdb.connect(ruta_warehouse(), read_only=True) as con:
        completa = calcular(con, version_anterior)
        negativo_completo = perfil_final(con, completa)
    conteos = recortar(origen)
    env = os.environ.copy()
    env.update(DATOS_RED=str(RECORTE / 'datos_red'), BRONZE_PATH=str(RECORTE / 'lake' / 'bronze'),
               WAREHOUSE_PATH=str(RECORTE / 'warehouse.duckdb'), EVIDENCIA_PATH=str(RECORTE / 'evidencia'),
               STREAMING_MODO='simulado', PYTHONIOENCODING='utf-8')
    (RECORTE / 'evidencia').mkdir(parents=True, exist_ok=True)
    with (RECORTE / 'evidencia' / 'pipeline.log').open('w', encoding='utf-8') as log:
        proceso = subprocess.run([sys.executable, str(RAIZ / 'flows' / 'pipeline.py'), '--desde-cero', '--solo-carga'],
                                 cwd=RAIZ, env=env, stdout=log, stderr=subprocess.STDOUT)
    if proceso.returncode:
        raise RuntimeError('Falló el flujo recortado; ver .recorte/evidencia/pipeline.log')
    with duckdb.connect(str(RECORTE / 'warehouse.duckdb'), read_only=True) as con:
        recortada = calcular(con, version_anterior)
        negativo_recorte = perfil_final(con, recortada)
    resultado = comparar(completa, recortada, ['fecha_corte'] + features.FEATURES)
    negativo = comparar(negativo_completo, negativo_recorte, ['perfil_final'])
    resultado.update(fecha=datetime.now(timezone(timedelta(hours=-6))).isoformat(timespec='seconds'),
                     corte=CORTES['A'], datos_recortados_hasta='2026-06-30',
                     registros_por_archivo_recortado=conteos,
                     control_negativo_perfil_final={'diferencias': negativo['diferencias'],
                                                    'detectado': negativo['diferencias'] > 0},
                     segundos=round(time.perf_counter() - inicio, 2))
    SALIDA.mkdir(parents=True, exist_ok=True)
    nombre = '1.3-prueba-recorte-antes.json' if version_anterior else '1.3-prueba-recorte.json'
    (SALIDA / nombre).write_text(json.dumps(resultado, indent=2, ensure_ascii=False), encoding='utf-8')
    registrar_corrida(resultado, version_anterior)
    print(json.dumps(resultado, indent=2, ensure_ascii=False))
    if resultado['filas_en_un_solo_lado'] or (not version_anterior and resultado['diferencias']):
        raise AssertionError('La prueba de recorte detectó diferencias')
    if not resultado['filas_comparadas'] or not resultado['control_negativo_perfil_final']['detectado']:
        raise AssertionError('El control negativo no detectó la fuga o no hay población')
    return resultado


if __name__ == '__main__':
    p = argparse.ArgumentParser()
    p.add_argument('--version-anterior', action='store_true', help='reproduce las fórmulas flotantes previas')
    a = p.parse_args()
    main(a.version_anterior)
