"""Piezas compartidas de la Fase 2: carga de un corte, folds de la Fase 1, preprocesamiento y escenario de costos.

Todo lo que entrena o ajusta algo lee solo el corte A. El corte B solo lo lee proyecto2/test_b.py, una vez.
"""
import os
import subprocess
from datetime import datetime
from pathlib import Path

import duckdb
import numpy as np
import pandas as pd
from sklearn.compose import ColumnTransformer
from sklearn.model_selection import StratifiedKFold
from sklearn.preprocessing import OneHotEncoder, OrdinalEncoder, StandardScaler

if __package__:
    from .config import RAIZ, SALIDA, SEMILLA, ruta_warehouse
    from .features import FEATURES
else:
    from config import RAIZ, SALIDA, SEMILLA, ruta_warehouse
    from features import FEATURES

CATEGORICAS = ['perfil']
NUMERICAS = [f for f in FEATURES if f not in CATEGORICAS]
N_FOLDS = 5

# Escenario de la Agencia (2.2): contactar cuesta Q5; si el usuario se iba a ir, la campaña lo retiene
# en el 25 % de los casos, y un usuario retenido vale Q60.
COSTO_CONTACTO = 5.0
TASA_RETENCION = 0.25
VALOR_RETENIDO = 60.0
BENEFICIO_POSITIVO = TASA_RETENCION * VALOR_RETENIDO - COSTO_CONTACTO   # Q10 por cada abandono contactado
COSTO_NEGATIVO = COSTO_CONTACTO                                         # Q5 por cada contacto que no se iba
UMBRAL_TEORICO = COSTO_CONTACTO / (TASA_RETENCION * VALOR_RETENIDO)     # p > 5 / 15 = 1/3

DIR_MODELOS = RAIZ / 'modelos'


def cargar_corte(corte, fuente=None):
    """Features de un corte.

    Por defecto se lee la tabla versionada en git, entregables/proyecto2/features-cortes.csv (la que exporta
    proyecto2/features.py en el flujo). Así cualquier commit reproduce exactamente sus cifras en cualquier máquina:
    unidad_id es un seudónimo que depende de PSEUDO_SALT (.env), y el orden por unidad_id define los folds de 1.4.
    Con P2_FUENTE=warehouse se lee proyecto2.features_cortes del warehouse local."""
    fuente = fuente or os.environ.get('P2_FUENTE', 'csv')
    wh = Path(ruta_warehouse())
    if fuente == 'warehouse' and wh.exists():
        with duckdb.connect(str(wh), read_only=True) as con:
            existe = con.execute("select count(*) from information_schema.tables "
                                 "where table_schema = 'proyecto2' and table_name = 'features_cortes'").fetchone()[0]
            if existe:
                df = con.execute('select * from proyecto2.features_cortes where corte = ? order by unidad_id',
                                 [corte]).df()
                return preparar(df)
    df = pd.read_csv(SALIDA / 'features-cortes.csv', dtype={'unidad_id': str})
    df = df[df.corte == corte].sort_values('unidad_id').reset_index(drop=True)
    return preparar(df)


def preparar(df):
    """Tipos estables entre warehouse, CSV y predecir.py."""
    df = df.copy()
    df['en_padron'] = df['en_padron'].astype(bool).astype(int)
    df['perfil'] = df['perfil'].astype(str)
    for c in NUMERICAS:
        df[c] = df[c].astype(float)
    return df


def folds_fase1(df):
    """Los mismos 5 folds estratificados de la Fase 1 (1.4), leídos de folds-corte-a.csv.
    Se verifica que coincidan con StratifiedKFold(5, shuffle=True, random_state=SEMILLA)."""
    y = df['etiqueta'].to_numpy().astype(int)
    guardados = pd.read_csv(SALIDA / 'folds-corte-a.csv', dtype={'unidad_id': str})
    folds = df[['unidad_id']].merge(guardados, on='unidad_id', how='left')['fold']
    if folds.isna().any():
        raise RuntimeError('folds-corte-a.csv no corresponde a estas features: corre primero proyecto2/modelos.py')
    folds = folds.to_numpy().astype(int)
    esperados = np.empty(len(df), dtype=int)
    skf = StratifiedKFold(n_splits=N_FOLDS, shuffle=True, random_state=SEMILLA)
    for k, (_, va) in enumerate(skf.split(df[FEATURES], y)):
        esperados[va] = k
    if not np.array_equal(folds, esperados):
        raise RuntimeError('Los folds guardados no coinciden con los de la Fase 1')
    return folds, [(np.where(folds != k)[0], np.where(folds == k)[0]) for k in range(N_FOLDS)]


def prep_lineal():
    return ColumnTransformer([('num', StandardScaler(), NUMERICAS),
                              ('cat', OneHotEncoder(handle_unknown='ignore'), CATEGORICAS)])


def prep_arboles():
    """Los árboles no necesitan escalar; el perfil se codifica como entero y se declara categórico en el modelo."""
    return ColumnTransformer([('num', 'passthrough', NUMERICAS),
                              ('cat', OrdinalEncoder(handle_unknown='use_encoded_value', unknown_value=-1,
                                                     encoded_missing_value=-1), CATEGORICAS)])


def ganancia(y, contactar):
    """G = Q10 · (abandonos contactados) − Q5 · (contactados que no se iban)."""
    y, contactar = np.asarray(y).astype(int), np.asarray(contactar).astype(bool)
    vp = int((contactar & (y == 1)).sum())
    fp = int((contactar & (y == 0)).sum())
    return BENEFICIO_POSITIVO * vp - COSTO_NEGATIVO * fp, vp, fp


def commit_y_fecha():
    r = subprocess.run(['git', 'rev-parse', '--short', 'HEAD'], cwd=RAIZ, capture_output=True, text=True)
    sucio = subprocess.run(['git', 'status', '--porcelain', '--untracked-files=no'], cwd=RAIZ,
                           capture_output=True, text=True).stdout.strip()
    commit = r.stdout.strip() if r.returncode == 0 else 'sin commit disponible'
    return commit + (' (con cambios sin commit)' if sucio else ''), datetime.now().astimezone().isoformat(timespec='seconds')


def anotar_bitacora(texto):
    with (RAIZ / 'proyecto2' / 'bitacora.md').open('a', encoding='utf-8') as f:
        f.write(f'\n- {texto}\n')
