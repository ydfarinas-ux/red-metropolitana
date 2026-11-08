"""2.2 (primera parte) Umbral según el escenario de costos, elegido SOLO con las predicciones fuera de fold del corte A.

Escenario (igual para todos los grupos): contactar cuesta Q5; si el usuario se iba a ir, la campaña lo retiene
en el 25 % de los casos; un usuario retenido vale Q60.

Ganancia de contactar a un grupo con VP abandonos reales y FP usuarios que no se iban:
    G = VP · (0.25 · 60 − 5) − FP · 5 = 10 · VP − 5 · FP
Para un usuario con probabilidad p de irse, contactarlo conviene si 0.25 · 60 · p − 5 > 0, es decir p > 1/3.

Uso: python proyecto2/umbral.py
"""
import json

import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
import numpy as np
import pandas as pd
from sklearn.metrics import average_precision_score

if __package__:
    from .config import SALIDA
    from .datos_modelo import (COSTO_CONTACTO, TASA_RETENCION, UMBRAL_TEORICO,
                               VALOR_RETENIDO, anotar_bitacora, commit_y_fecha, ganancia)
else:
    from config import SALIDA
    from datos_modelo import (COSTO_CONTACTO, TASA_RETENCION, UMBRAL_TEORICO,
                              VALOR_RETENIDO, anotar_bitacora, commit_y_fecha, ganancia)

MODELO_PRODUCCION = 'hgb'            # decisión de 2.1 (columna de oof-fase2-corte-a.csv)
UMBRALES = np.round(np.arange(0.01, 0.991, 0.01), 2)


def curva(y, p):
    filas = []
    for u in UMBRALES:
        g, vp, fp = ganancia(y, p >= u)
        contactados = vp + fp
        filas.append(dict(umbral=u, contactados=contactados, vp=vp, fp=fp, fn=int(y.sum()) - vp,
                          precision=vp / contactados if contactados else np.nan, recall=vp / y.sum(), ganancia_q=g))
    return pd.DataFrame(filas)


def main():
    oof = pd.read_csv(SALIDA / 'oof-fase2-corte-a.csv')
    y = oof.etiqueta.to_numpy()
    folds = oof.fold.to_numpy()

    curvas = {m: curva(y, oof[m].to_numpy()) for m in ['logistica_l2', MODELO_PRODUCCION]}
    c = curvas[MODELO_PRODUCCION]
    mejor = c.loc[c.ganancia_q.idxmax()]
    umbral = float(mejor.umbral)

    # estabilidad: umbral óptimo y ganancia en cada fold de validación (cada fold es ~1/5 de A)
    por_fold = []
    for k in sorted(set(folds)):
        ck = curva(y[folds == k], oof[MODELO_PRODUCCION].to_numpy()[folds == k])
        gk, _, _ = ganancia(y[folds == k], oof[MODELO_PRODUCCION].to_numpy()[folds == k] >= umbral)
        por_fold.append(dict(fold=k, umbral_optimo_fold=float(ck.loc[ck.ganancia_q.idxmax()].umbral),
                             ganancia_con_umbral_elegido=gk))
    por_fold = pd.DataFrame(por_fold)

    g_todos, vp_t, fp_t = ganancia(y, np.ones_like(y, dtype=bool))
    g_teorico = curvas[MODELO_PRODUCCION].loc[np.isclose(UMBRALES, round(UMBRAL_TEORICO, 2))].iloc[0]
    g_log = curvas['logistica_l2'].loc[curvas['logistica_l2'].ganancia_q.idxmax()]

    for m, cm in curvas.items():
        cm.round(4).to_csv(SALIDA / f'2.2-curva-ganancia-{m}.csv', index=False)
    por_fold.to_csv(SALIDA / '2.2-umbral-por-fold.csv', index=False)

    fig, ax = plt.subplots(figsize=(8, 5))
    ax.plot(c.umbral, c.ganancia_q, color='#2a78d6', lw=2, label='HistGradientBoosting (producción)')
    cl = curvas['logistica_l2']
    ax.plot(cl.umbral, cl.ganancia_q, color='#9aa3ad', lw=1.5, ls='--', label='Logística L2 (comparación)')
    ax.axvline(umbral, color='black', lw=1)
    ax.plot([umbral], [mejor.ganancia_q], 'o', color='black')
    ax.annotate(f'umbral elegido {umbral:.2f}\nQ{mejor.ganancia_q:,.0f}', (umbral, mejor.ganancia_q),
                xytext=(15, -40), textcoords='offset points', fontsize=9)
    ax.axvline(UMBRAL_TEORICO, color='#eb6834', lw=1, ls=':', label='p = 1/3 (punto de equilibrio teórico)')
    ax.axhline(0, color='gray', lw=0.8)
    ax.set_xlabel('Umbral (contactar si puntaje ≥ umbral)')
    ax.set_ylabel('Ganancia en el corte A (Q, predicciones fuera de fold)')
    ax.set_title('2.2 Ganancia contra umbral: G = 10·VP − 5·FP')
    ax.legend(frameon=False, fontsize=9)
    ax.grid(alpha=0.3)
    ax.spines[['top', 'right']].set_visible(False)
    fig.tight_layout()
    fig.savefig(SALIDA / '2.2-curva-ganancia.png', dpi=150)
    plt.close(fig)

    commit, fecha = commit_y_fecha()
    resumen = {
        'fecha': fecha, 'commit': commit, 'datos': 'corte A, predicciones fuera de fold (5 folds de la Fase 1)',
        'modelo': MODELO_PRODUCCION,
        'escenario': {'costo_contacto_q': COSTO_CONTACTO, 'tasa_retencion': TASA_RETENCION,
                      'valor_retenido_q': VALOR_RETENIDO},
        'formula': 'G = VP·(0.25·60 − 5) − FP·5 = 10·VP − 5·FP',
        'umbral_teorico': round(UMBRAL_TEORICO, 4),
        'umbral_elegido': umbral,
        'en_umbral_elegido': {k: (int(v) if k in ('contactados', 'vp', 'fp', 'fn') else round(float(v), 4))
                              for k, v in mejor.drop('umbral').items()},
        'cuenta': f"G = 10 · {int(mejor.vp):,} − 5 · {int(mejor.fp):,} = {10 * int(mejor.vp):,} − {5 * int(mejor.fp):,} "
                  f"= Q{int(mejor.ganancia_q):,}",
        'en_umbral_1_3': {'umbral': float(g_teorico.umbral), 'ganancia_q': float(g_teorico.ganancia_q),
                          'contactados': int(g_teorico.contactados)},
        'contactar_a_todos': {'ganancia_q': g_todos, 'cuenta': f'10 · {vp_t:,} − 5 · {fp_t:,} = Q{g_todos:,.0f}'},
        'logistica_l2_mejor': {'umbral': float(g_log.umbral), 'ganancia_q': float(g_log.ganancia_q)},
        'ap_oof': {m: round(average_precision_score(y, oof[m]), 4) for m in ['logistica_l2', MODELO_PRODUCCION]},
        'umbral_optimo_por_fold': por_fold.umbral_optimo_fold.tolist(),
    }
    (SALIDA / '2.2-umbral.json').write_text(json.dumps(resumen, indent=2, ensure_ascii=False), encoding='utf-8')
    anotar_bitacora(f"{fecha} · commit {commit} · 2.2 umbral con predicciones fuera de fold del corte A: {umbral:.2f} "
                    f"({resumen['cuenta']}; {int(mejor.contactados):,} contactados, precisión {mejor.precision:.3f}, "
                    f"recall {mejor.recall:.3f}). Umbral teórico 1/3.")
    print(json.dumps(resumen, indent=2, ensure_ascii=False))


if __name__ == '__main__':
    main()
