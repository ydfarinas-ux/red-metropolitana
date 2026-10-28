"""1.4 Líneas base y regresión logística regularizada (L2, L1 y Elastic Net) en el corte A.

Solo se lee el corte A: la etiqueta del corte B no se toca en la Fase 1.
Todos los modelos, también las líneas base, se evalúan con los mismos 5 folds estratificados.

Uso: python proyecto2/modelos.py
"""
import json
import subprocess
import time
import warnings
from datetime import datetime

import duckdb
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
import numpy as np
import pandas as pd
from joblib import Parallel, delayed
from sklearn.base import clone
from sklearn.compose import ColumnTransformer
from sklearn.exceptions import ConvergenceWarning
from sklearn.linear_model import LogisticRegression
from sklearn.metrics import average_precision_score, roc_auc_score
from sklearn.model_selection import StratifiedKFold
from sklearn.pipeline import Pipeline
from sklearn.preprocessing import OneHotEncoder, StandardScaler

if __package__:
    from .config import RAIZ, SALIDA, SEMILLA, ruta_warehouse
    from .features import FEATURES
else:
    from config import RAIZ, SALIDA, SEMILLA, ruta_warehouse
    from features import FEATURES

CATEGORICAS = ['perfil']
NUMERICAS = [f for f in FEATURES if f not in CATEGORICAS]
N_FOLDS = 5
CS = np.logspace(-4, 2, 13)          # lambda = 1 / C: un C grande castiga poco
# en scikit-learn 1.9 el castigo se elige con l1_ratio (penalty está obsoleto)
CASTIGOS = {
    'L2': dict(l1_ratio=0.0, solver='lbfgs'),
    'L1': dict(l1_ratio=1.0, solver='saga'),
    'Elastic Net 0.5': dict(l1_ratio=0.5, solver='saga'),
}
COLUMNAS = {'L2': 'logistica_l2', 'L1': 'logistica_l1', 'Elastic Net 0.5': 'logistica_elastic_net'}
COLORES = {'L2': '#2a78d6', 'L1': '#eb6834', 'Elastic Net 0.5': '#1baf7a'}
BASES = {
    'Base 1: constante (tasa del corte A)': 'base1_constante',
    'Base 2: días desde el último viaje': 'base2_dias_desde_ultimo_viaje',
    'Base 3: menos viajes en 28 días': 'base3_menos_viajes_28d',
}


def cargar():
    with duckdb.connect(ruta_warehouse(), read_only=True) as con:
        df = con.execute("select * from proyecto2.features_cortes where corte = 'A' order by unidad_id").df()
    df['en_padron'] = df['en_padron'].astype(int)
    return df


def pipeline(castigo, C):
    prep = ColumnTransformer([('num', StandardScaler(), NUMERICAS),
                              ('cat', OneHotEncoder(handle_unknown='ignore'), CATEGORICAS)])
    modelo = LogisticRegression(C=C, max_iter=3000, tol=1e-3, random_state=SEMILLA, **CASTIGOS[castigo])
    return Pipeline([('prep', prep), ('modelo', modelo)])


def ajustar(castigo, C, fold, X, y, tr, va):
    """El escalado se ajusta solo con el entrenamiento del fold, así no hay fuga en la validación."""
    with warnings.catch_warnings():
        warnings.simplefilter('ignore', ConvergenceWarning)
        m = pipeline(castigo, C).fit(X.iloc[tr], y[tr])
    ap_tr = average_precision_score(y[tr], m.predict_proba(X.iloc[tr])[:, 1])
    return castigo, C, fold, m.predict_proba(X.iloc[va])[:, 1], ap_tr


def evaluar(y, puntaje, folds):
    """Precisión promedio y ROC-AUC por fold sobre las predicciones fuera de fold."""
    ap = [average_precision_score(y[folds == k], puntaje[folds == k]) for k in range(N_FOLDS)]
    roc = [roc_auc_score(y[folds == k], puntaje[folds == k]) for k in range(N_FOLDS)]
    return np.mean(ap), np.std(ap), np.mean(roc), np.std(roc)


def nombre_logistica(castigo, lam):
    return f'Logística {castigo} (lambda={round(lam, 2):g})'


def graficar(curva, elegidos, tasa):
    fig, ax = plt.subplots(figsize=(8, 5))
    for castigo in CASTIGOS:
        c = curva[curva.castigo == castigo]
        ax.errorbar(c['lambda'], c.ap_media, yerr=c.ap_desv, color=COLORES[castigo], lw=2, marker='o', ms=4,
                    capsize=3, label=castigo)
        e = c[c['lambda'] == elegidos[castigo]]
        ax.plot(e['lambda'], e.ap_media, 'o', ms=9, mfc='none', mec='black', mew=1.5)
    ax.axhline(tasa, color='gray', ls='--', lw=1, label=f'Base 1: constante ({tasa:.4f})')
    ax.plot([], [], 'o', ms=9, mfc='none', mec='black', mew=1.5, label='λ elegido')
    ax.set_xscale('log')
    ax.set_xlabel('λ = 1 / C (castigo, escala logarítmica)')
    ax.set_ylabel('Precisión promedio de validación (media de 5 folds)')
    ax.set_title('Regresión logística regularizada en el corte A: precisión promedio contra λ')
    ax.grid(alpha=0.3)
    ax.spines[['top', 'right']].set_visible(False)
    ax.legend(frameon=False)
    fig.tight_layout()
    fig.savefig(SALIDA / '1.4-metrica-vs-lambda.png', dpi=150)
    plt.close(fig)


def main():
    t0 = time.perf_counter()
    SALIDA.mkdir(parents=True, exist_ok=True)
    df = cargar()
    X, y = df[FEATURES], df['etiqueta'].to_numpy().astype(int)
    folds = np.empty(len(df), dtype=int)
    divisiones = list(StratifiedKFold(n_splits=N_FOLDS, shuffle=True, random_state=SEMILLA).split(X, y))
    for k, (_, va) in enumerate(divisiones):
        folds[va] = k
    tasa = y.mean()
    print(f'  corte A: {len(df):,} filas, {y.sum():,} positivos ({tasa:.4f})')

    # líneas base: no entrenan nada, el puntaje sale directo de los datos
    puntajes = {
        'base1_constante': np.full(len(df), tasa),
        'base2_dias_desde_ultimo_viaje': df['dias_desde_ultimo_viaje'].to_numpy(dtype=float),
        'base3_menos_viajes_28d': -df['viajes_28d'].to_numpy(dtype=float),
    }
    filas = []
    for nombre, col in BASES.items():
        p = puntajes[col]
        ap_tr = np.mean([average_precision_score(y[tr], p[tr]) for tr, _ in divisiones])
        filas.append((nombre, ap_tr, *evaluar(y, p, folds), np.nan))

    # logística: 3 castigos x 13 valores de C x 5 folds = 195 modelos en paralelo
    trabajos = [delayed(ajustar)(castigo, C, k, X, y, tr, va)
                for castigo in CASTIGOS for C in CS for k, (tr, va) in enumerate(divisiones)]
    oof, ap_tr = {}, {}
    for castigo, C, k, p, a in Parallel(n_jobs=-1)(trabajos):
        oof.setdefault((castigo, C), np.empty(len(df)))[divisiones[k][1]] = p
        ap_tr.setdefault((castigo, C), []).append(a)

    curva = []
    for (castigo, C), p in oof.items():
        ap_m, ap_d, roc_m, _ = evaluar(y, p, folds)
        curva.append((castigo, C, 1 / C, ap_m, ap_d, roc_m, np.mean(ap_tr[(castigo, C)])))
    curva = pd.DataFrame(curva, columns=['castigo', 'C', 'lambda', 'ap_media', 'ap_desv', 'roc_media', 'ap_entrenamiento'])

    # para cada castigo, el lambda con la mejor precisión promedio media
    elegidos, ap_elegido = {}, {}
    for castigo in CASTIGOS:
        mejor = curva.loc[curva[curva.castigo == castigo].ap_media.idxmax()]
        elegidos[castigo], ap_elegido[castigo] = mejor['lambda'], mejor.ap_media
        p = oof[(castigo, mejor.C)]
        puntajes[COLUMNAS[castigo]] = p
        filas.append((nombre_logistica(castigo, mejor['lambda']), mejor.ap_entrenamiento,
                      *evaluar(y, p, folds), mejor['lambda']))
    modelos = pd.DataFrame(filas, columns=['modelo', 'ap_entrenamiento', 'ap_media', 'ap_desv',
                                           'roc_auc_media', 'roc_auc_desv', 'lambda']).round(4)
    modelos.to_csv(SALIDA / '1.4-modelos.csv', index=False)
    metricas = ['ap_media', 'ap_desv', 'roc_media', 'ap_entrenamiento']
    curva.assign(**{c: curva[c].round(4) for c in metricas}).to_csv(SALIDA / '1.4-curva-lambda.csv', index=False)
    graficar(curva, elegidos, tasa)

    # mejor logística entrenada con todo el corte A
    mejor_castigo = max(ap_elegido, key=ap_elegido.get)
    with warnings.catch_warnings():
        warnings.simplefilter('ignore', ConvergenceWarning)
        m = pipeline(mejor_castigo, 1 / elegidos[mejor_castigo]).fit(X, y)
    nombres = [n.split('__', 1)[1] for n in m.named_steps['prep'].get_feature_names_out()]
    coef = pd.DataFrame({'feature': nombres, 'coeficiente': m.named_steps['modelo'].coef_[0]})
    coef.sort_values('coeficiente', ascending=False).round(4).to_csv(SALIDA / '1.4-coeficientes.csv', index=False)

    # folds y predicciones fuera de fold para el ensemble y el umbral de la Fase 2
    df[['unidad_id']].assign(fold=folds).to_csv(SALIDA / 'folds-corte-a.csv', index=False)
    df[['unidad_id']].assign(fold=folds, etiqueta=y, **puntajes).to_csv(SALIDA / 'oof-corte-a.csv', index=False)

    mejor = modelos[modelos.modelo == nombre_logistica(mejor_castigo, elegidos[mejor_castigo])].iloc[0]
    commit = subprocess.run(['git', 'rev-parse', '--short', 'HEAD'], cwd=RAIZ, capture_output=True, text=True).stdout.strip()
    fecha = datetime.now().astimezone().isoformat(timespec='seconds')
    resumen = {
        'fecha': fecha, 'commit': commit, 'filas_corte_a': len(df), 'positivos': int(y.sum()),
        'tasa_positiva': round(tasa, 4), 'folds': N_FOLDS, 'semilla': SEMILLA,
        'mejor_logistica': {'modelo': mejor.modelo, 'castigo': mejor_castigo, 'lambda': mejor['lambda'],
                            'ap_media': mejor.ap_media, 'roc_auc_media': mejor.roc_auc_media},
        'lambda_elegido': {c: round(lam, 4) for c, lam in elegidos.items()},
        'duracion_segundos': round(time.perf_counter() - t0, 1),
    }
    (SALIDA / '1.4-resumen.json').write_text(json.dumps(resumen, indent=2, ensure_ascii=False), encoding='utf-8')
    with (RAIZ / 'proyecto2' / 'bitacora.md').open('a', encoding='utf-8') as f:
        f.write(f'\n- {fecha} · commit {commit} · 1.4 modelos en el corte A: {len(df):,} filas, tasa positiva '
                f'{tasa:.4f}, 5 folds estratificados (semilla {SEMILLA}). Mejor logística: {mejor.modelo}, '
                f'precisión promedio {mejor.ap_media:.4f} ± {mejor.ap_desv:.4f} (ROC-AUC {mejor.roc_auc_media:.4f}).\n')
    print(modelos.to_string(index=False))


if __name__ == '__main__':
    main()
