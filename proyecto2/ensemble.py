"""2.1 Ensembles (Random Forest y HistGradientBoosting) con los mismos 5 folds del corte A de la Fase 1.

- Métrica: precisión promedio (average precision), igual que en 1.4; también se reporta ROC-AUC.
- Se mide la métrica en entrenamiento y en validación de cada fold para ubicar a cada modelo en el balance sesgo-varianza.
- La importancia por permutación se calcula en el fold de validación, nunca en el de entrenamiento.
- Solo se lee el corte A.

Uso: python proyecto2/ensemble.py
"""
import json
import time
import warnings

import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
import numpy as np
import pandas as pd
from sklearn.base import clone
from sklearn.ensemble import HistGradientBoostingClassifier, RandomForestClassifier
from sklearn.exceptions import ConvergenceWarning
from sklearn.inspection import permutation_importance
from sklearn.linear_model import LogisticRegression
from sklearn.metrics import average_precision_score, roc_auc_score
from sklearn.pipeline import Pipeline

if __package__:
    from .config import SALIDA, SEMILLA
    from .datos_modelo import (CATEGORICAS, NUMERICAS, N_FOLDS, anotar_bitacora, cargar_corte, commit_y_fecha,
                               folds_fase1, prep_arboles, prep_lineal)
    from .features import FEATURES
else:
    from config import SALIDA, SEMILLA
    from datos_modelo import (CATEGORICAS, NUMERICAS, N_FOLDS, anotar_bitacora, cargar_corte, commit_y_fecha,
                              folds_fase1, prep_arboles, prep_lineal)
    from features import FEATURES

IDX_CAT = [len(NUMERICAS) + i for i in range(len(CATEGORICAS))]   # posición del perfil después del ColumnTransformer


def hgb(learning_rate, max_leaf_nodes, min_samples_leaf=40, l2=1.0):
    """learning_rate cumple el papel de α; max_iter alto con parada temprana sobre un 10 % del entrenamiento del fold."""
    return Pipeline([('prep', prep_arboles()),
                     ('modelo', HistGradientBoostingClassifier(
                         learning_rate=learning_rate, max_leaf_nodes=max_leaf_nodes, min_samples_leaf=min_samples_leaf,
                         l2_regularization=l2, max_iter=500, early_stopping=True, validation_fraction=0.1,
                         n_iter_no_change=30, scoring='loss', categorical_features=IDX_CAT, random_state=SEMILLA))])


def rf(min_samples_leaf):
    return Pipeline([('prep', prep_arboles()),
                     ('modelo', RandomForestClassifier(n_estimators=300, min_samples_leaf=min_samples_leaf,
                                                       max_features='sqrt', n_jobs=-1, random_state=SEMILLA))])


def logistica_l2(lam):
    return Pipeline([('prep', prep_lineal()),
                     ('modelo', LogisticRegression(C=1 / lam, l1_ratio=0.0, solver='lbfgs', max_iter=3000, tol=1e-3,
                                                   random_state=SEMILLA))])


# Configuraciones evaluadas. Todas con los mismos folds; la elegida es la de mejor precisión promedio media.
HGB_CONFIGS = {
    'HGB lr=0.05, hojas=15': dict(learning_rate=0.05, max_leaf_nodes=15),
    'HGB lr=0.05, hojas=31': dict(learning_rate=0.05, max_leaf_nodes=31),
    'HGB lr=0.1, hojas=15': dict(learning_rate=0.1, max_leaf_nodes=15),
    'HGB lr=0.1, hojas=31': dict(learning_rate=0.1, max_leaf_nodes=31),
}
RF_CONFIGS = {
    'Random Forest (hojas de 1, sin podar)': 1,
    'Random Forest (mínimo 50 por hoja)': 50,
}


def validar(modelo, X, y, divisiones):
    """Predicciones fuera de fold, métrica de entrenamiento y de validación por fold, y los modelos ajustados."""
    oof = np.empty(len(y))
    ap_tr, ap_va, roc_va, ajustados = [], [], [], []
    for tr, va in divisiones:
        with warnings.catch_warnings():
            warnings.simplefilter('ignore', ConvergenceWarning)
            m = clone(modelo).fit(X.iloc[tr], y[tr])
        p_tr = m.predict_proba(X.iloc[tr])[:, 1]
        oof[va] = m.predict_proba(X.iloc[va])[:, 1]
        ap_tr.append(average_precision_score(y[tr], p_tr))
        ap_va.append(average_precision_score(y[va], oof[va]))
        roc_va.append(roc_auc_score(y[va], oof[va]))
        ajustados.append(m)
    return oof, np.array(ap_tr), np.array(ap_va), np.array(roc_va), ajustados


def diagnostico(ap_tr, ap_va, ap_ref):
    """Regla de lectura: brecha entrenamiento-validación grande = varianza alta;
    validación cerca de la de un modelo simple y sin brecha = sesgo alto."""
    brecha = ap_tr - ap_va
    if brecha > 0.10:
        return 'varianza alta', f'memoriza el entrenamiento: {ap_tr:.3f} contra {ap_va:.3f} en validación (brecha {brecha:.3f})'
    if brecha < 0.01 and ap_va < ap_ref - 0.01:
        return 'sesgo alto', (f'entrenamiento y validación casi iguales ({ap_tr:.3f} / {ap_va:.3f}) pero por debajo '
                              f'del mejor ensemble ({ap_ref:.3f}): el modelo es demasiado simple')
    return 'equilibrado', f'brecha pequeña ({brecha:.3f}) y validación alta ({ap_va:.3f})'


def importancias(ajustados, X, y, divisiones):
    """Permutación en el fold de validación (n_repeats=5) y promedio sobre los 5 folds."""
    tablas = []
    for k, (m, (_, va)) in enumerate(zip(ajustados, divisiones)):
        r = permutation_importance(m, X.iloc[va], y[va], scoring='average_precision', n_repeats=5,
                                   random_state=SEMILLA, n_jobs=1)
        tablas.append(pd.DataFrame({'feature': FEATURES, 'fold': k, 'caida_ap': r.importances_mean}))
    t = pd.concat(tablas).groupby('feature').caida_ap.agg(['mean', 'std']).reset_index()
    t.columns = ['feature', 'caida_ap_media', 'caida_ap_desv']
    return t.sort_values('caida_ap_media', ascending=False).reset_index(drop=True)


def graficar_importancias(imp):
    top = imp.head(10).iloc[::-1]
    fig, ax = plt.subplots(figsize=(8, 5))
    ax.barh(top.feature, top.caida_ap_media, xerr=top.caida_ap_desv, color='#2a78d6', capsize=3)
    ax.set_xlabel('Caída de la precisión promedio al permutar la feature (validación, media de 5 folds)')
    ax.set_title('2.1 Importancia por permutación del ensemble elegido (corte A)')
    ax.spines[['top', 'right']].set_visible(False)
    ax.grid(axis='x', alpha=0.3)
    fig.tight_layout()
    fig.savefig(SALIDA / '2.1-importancias.png', dpi=150)
    plt.close(fig)


def graficar_sesgo_varianza(tabla):
    t = tabla.dropna(subset=['ap_entrenamiento']).copy()
    fig, ax = plt.subplots(figsize=(9, 5))
    y = np.arange(len(t))
    ax.scatter(t.ap_entrenamiento, y, color='#eb6834', label='Entrenamiento', zorder=3)
    ax.scatter(t.ap_media, y, color='#2a78d6', label='Validación', zorder=3)
    for i, (a, b) in enumerate(zip(t.ap_entrenamiento, t.ap_media)):
        ax.plot([a, b], [i, i], color='gray', lw=1)
    ax.set_yticks(y, t.modelo, fontsize=8)
    ax.set_xlabel('Precisión promedio (media de 5 folds del corte A)')
    ax.set_title('2.1 Entrenamiento contra validación: brecha = varianza')
    ax.legend(frameon=False)
    ax.grid(axis='x', alpha=0.3)
    ax.spines[['top', 'right']].set_visible(False)
    fig.tight_layout()
    fig.savefig(SALIDA / '2.1-sesgo-varianza.png', dpi=150)
    plt.close(fig)


def main():
    t0 = time.perf_counter()
    df = cargar_corte('A')
    X, y = df[FEATURES], df['etiqueta'].to_numpy().astype(int)
    folds, divisiones = folds_fase1(df)
    print(f'  corte A: {len(df):,} filas, {y.sum():,} positivos; mismos {N_FOLDS} folds de la Fase 1')

    # tabla de 1.4 (líneas base y logísticas) tal como se reportó en la Fase 1
    previa = pd.read_csv(SALIDA / '1.4-modelos.csv')
    resumen_14 = json.loads((SALIDA / '1.4-resumen.json').read_text(encoding='utf-8'))
    lam = resumen_14['mejor_logistica']['lambda']

    filas, oofs, ajustes = [], {}, {}
    configs = {**{n: hgb(**c) for n, c in HGB_CONFIGS.items()}, **{n: rf(h) for n, h in RF_CONFIGS.items()}}
    for nombre, modelo in configs.items():
        t = time.perf_counter()
        oof, ap_tr, ap_va, roc_va, ajustados = validar(modelo, X, y, divisiones)
        oofs[nombre], ajustes[nombre] = oof, ajustados
        iters = [m.named_steps['modelo'].n_iter_ for m in ajustados] if nombre.startswith('HGB') else None
        filas.append(dict(modelo=nombre, ap_entrenamiento=ap_tr.mean(), ap_media=ap_va.mean(), ap_desv=ap_va.std(),
                          roc_auc_media=roc_va.mean(), roc_auc_desv=roc_va.std(),
                          iteraciones=f"{min(iters)}-{max(iters)}" if iters else '',
                          segundos=round(time.perf_counter() - t, 1)))
        print(f'  {nombre:40s} AP entrenamiento {ap_tr.mean():.4f} | validación {ap_va.mean():.4f} ± {ap_va.std():.4f}')
    ens = pd.DataFrame(filas)
    ens.round(4).to_csv(SALIDA / '2.1-configuraciones.csv', index=False)

    mejor_hgb = ens[ens.modelo.str.startswith('HGB')].sort_values('ap_media', ascending=False).iloc[0]
    mejor_rf = ens[ens.modelo.str.startswith('Random')].sort_values('ap_media', ascending=False).iloc[0]
    mejor_ens = max([mejor_hgb, mejor_rf], key=lambda r: r.ap_media)

    # la logística L2 elegida en 1.4, re-entrenada con los mismos folds para tener su tiempo y comprobar sus cifras
    t = time.perf_counter()
    oof_log, ap_tr_log, ap_va_log, roc_log, _ = validar(logistica_l2(lam), X, y, divisiones)
    seg_log = round(time.perf_counter() - t, 1)
    oofs['logistica_l2'] = oof_log
    fila_log = previa[previa.modelo.str.startswith('Logística L2')].iloc[0]
    assert abs(fila_log.ap_media - ap_va_log.mean()) < 5e-4, 'la logística no reproduce la cifra de 1.4'

    # tabla final: la de 1.4 más los ensembles, todas con los mismos folds
    tabla = pd.concat([previa.drop(columns=['lambda']),
                       ens.loc[ens.modelo.isin([mejor_hgb.modelo, mejor_rf.modelo]),
                               ['modelo', 'ap_entrenamiento', 'ap_media', 'ap_desv', 'roc_auc_media', 'roc_auc_desv']],
                       ens.loc[~ens.modelo.isin([mejor_hgb.modelo, mejor_rf.modelo]) & ens.modelo.str.startswith('Random'),
                               ['modelo', 'ap_entrenamiento', 'ap_media', 'ap_desv', 'roc_auc_media', 'roc_auc_desv']]],
                      ignore_index=True)
    tabla.round(4).to_csv(SALIDA / '2.1-modelos.csv', index=False)

    # sesgo-varianza: una línea por modelo entrenado (las líneas base no aprenden nada)
    sv = []
    for _, r in tabla.iterrows():
        if r.modelo.startswith('Base'):
            continue
        tipo, porque = diagnostico(r.ap_entrenamiento, r.ap_media, mejor_ens.ap_media)
        sv.append(dict(modelo=r.modelo, ap_entrenamiento=round(r.ap_entrenamiento, 4), ap_validacion=round(r.ap_media, 4),
                       brecha=round(r.ap_entrenamiento - r.ap_media, 4), diagnostico=tipo, por_que=porque))
    pd.DataFrame(sv).to_csv(SALIDA / '2.1-sesgo-varianza.csv', index=False)
    graficar_sesgo_varianza(tabla)

    # importancias por permutación del ensemble elegido, en validación
    imp = importancias(ajustes[mejor_ens.modelo], X, y, divisiones)
    imp.round(5).to_csv(SALIDA / '2.1-importancias.csv', index=False)
    graficar_importancias(imp)

    # predicciones fuera de fold para elegir el umbral en 2.2 (solo corte A)
    pd.DataFrame({'unidad_id': df.unidad_id, 'fold': folds, 'etiqueta': y,
                  'logistica_l2': oof_log, 'random_forest': oofs[mejor_rf.modelo],
                  'hgb': oofs[mejor_hgb.modelo]}).to_csv(SALIDA / 'oof-fase2-corte-a.csv', index=False)

    commit, fecha = commit_y_fecha()
    mejora = mejor_ens.ap_media - ap_va_log.mean()
    resumen = {
        'fecha': fecha, 'commit': commit, 'folds': N_FOLDS, 'semilla': SEMILLA,
        'mejor_hgb': {'modelo': mejor_hgb.modelo, **HGB_CONFIGS[mejor_hgb.modelo],
                      'ap_media': round(mejor_hgb.ap_media, 4), 'ap_desv': round(mejor_hgb.ap_desv, 4)},
        'mejor_rf': {'modelo': mejor_rf.modelo, 'ap_media': round(mejor_rf.ap_media, 4)},
        'logistica_l2': {'lambda': lam, 'ap_media': round(ap_va_log.mean(), 4), 'ap_desv': round(ap_va_log.std(), 4),
                         'segundos_5_folds': seg_log},
        'mejora_ap_ensemble_sobre_logistica': round(mejora, 4),
        'mejora_en_desviaciones': round(mejora / max(ap_va_log.std(), mejor_ens.ap_desv), 1),
        'folds_donde_gana_ensemble': int(sum(
            average_precision_score(y[folds == k], oofs[mejor_ens.modelo][folds == k]) >
            average_precision_score(y[folds == k], oof_log[folds == k]) for k in range(N_FOLDS))),
        'top10_permutacion': imp.head(10).feature.tolist(),
        'duracion_segundos': round(time.perf_counter() - t0, 1),
    }
    (SALIDA / '2.1-resumen.json').write_text(json.dumps(resumen, indent=2, ensure_ascii=False), encoding='utf-8')
    anotar_bitacora(f"{fecha} · commit {commit} · 2.1 ensembles en el corte A con los folds de la Fase 1: mejor HGB "
                    f"{mejor_hgb.modelo} AP {mejor_hgb.ap_media:.4f} ± {mejor_hgb.ap_desv:.4f}; mejor RF {mejor_rf.modelo} "
                    f"AP {mejor_rf.ap_media:.4f}; logística L2 AP {ap_va_log.mean():.4f}. Mejora del ensemble: {mejora:+.4f}.")
    print(tabla.round(4).to_string(index=False))
    print(json.dumps(resumen, indent=2, ensure_ascii=False))


if __name__ == '__main__':
    main()
