"""2.2 (segunda parte) Evaluación ÚNICA del modelo final en el corte B.

Reglas que este script hace cumplir:
  * Se corre una sola vez: si ya existe entregables/proyecto2/2.2-test-b.json, se niega a correr.
  * Exige un árbol de git limpio, para que el commit anotado sea exactamente el código que evaluó.
  * No entrena ni ajusta nada: carga el modelo guardado (entrenado solo con A) y el umbral elegido con A.
  * Si el resultado es peor que en validación, se explica en el informe sin volver a ajustar.

Uso: python proyecto2/test_b.py
"""
import json
import sys

import joblib
import numpy as np
from sklearn.metrics import average_precision_score, confusion_matrix, roc_auc_score

if __package__:
    from .config import CORTES, SALIDA
    from .datos_modelo import DIR_MODELOS, anotar_bitacora, cambios_de_codigo, cargar_corte, commit_y_fecha, ganancia
    from .entrenar_final import VERSION
else:
    from config import CORTES, SALIDA
    from datos_modelo import DIR_MODELOS, anotar_bitacora, cambios_de_codigo, cargar_corte, commit_y_fecha, ganancia
    from entrenar_final import VERSION

REGISTRO = SALIDA / '2.2-test-b.json'


def main():
    if REGISTRO.exists():
        sys.exit(f'El corte B ya se evaluó (ver {REGISTRO.name}). La etiqueta de B se usa una sola vez.')
    if cambios_de_codigo():
        sys.exit('Hay cambios sin commit: haz commit antes de la evaluación única para poder anotar su commit.')

    paquete = joblib.load(DIR_MODELOS / f'modelo_abandono_v{VERSION}.joblib')
    modelo, umbral = paquete['pipeline'], paquete['umbral']
    validacion = json.loads((SALIDA / '2.2-umbral.json').read_text(encoding='utf-8'))
    val_21 = json.loads((SALIDA / '2.1-resumen.json').read_text(encoding='utf-8'))

    b = cargar_corte('B')
    y = b['etiqueta'].to_numpy().astype(int)
    p = modelo.predict_proba(b[paquete['features']])[:, 1]
    contactar = p >= umbral
    tn, fp, fn, vp = confusion_matrix(y, contactar).ravel()
    g, _, _ = ganancia(y, contactar)
    g_todos, vp_t, fp_t = ganancia(y, np.ones_like(y, dtype=bool))

    tasa_a = float(cargar_corte('A')['etiqueta'].mean())
    base2 = b['dias_desde_ultimo_viaje'].to_numpy(dtype=float)
    commit, fecha = commit_y_fecha()
    va = validacion['en_umbral_elegido']
    resultado = {
        'fecha': fecha, 'commit': commit, 'evaluacion_unica': True,
        'modelo': f"modelo_abandono_v{VERSION}.joblib ({paquete['nombre']})", 'umbral': umbral,
        'corte_b': CORTES['B'], 'poblacion': len(b), 'positivos': int(y.sum()),
        'tasa_positiva': round(float(y.mean()), 4),
        'metrica': {
            'precision_promedio': round(average_precision_score(y, p), 4),
            'roc_auc': round(roc_auc_score(y, p), 4),
            'base1_constante_precision_promedio': round(average_precision_score(y, np.full(len(y), tasa_a)), 4),
            'base2_dias_desde_ultimo_viaje_precision_promedio': round(average_precision_score(y, base2), 4),
            'base2_roc_auc': round(roc_auc_score(y, base2), 4),
            'validacion_a_precision_promedio': val_21['mejor_hgb']['ap_media'],
        },
        'matriz_confusion': {'vp': int(vp), 'fp': int(fp), 'fn': int(fn), 'vn': int(tn)},
        'contactados': int(vp + fp),
        'precision': round(vp / (vp + fp), 4), 'recall': round(vp / (vp + fn), 4),
        'ganancia_q': g,
        'cuenta_ganancia': f'G = 10 · {vp:,} − 5 · {fp:,} = {10 * vp:,} − {5 * fp:,} = Q{g:,.0f}',
        'ganancia_por_1000_usuarios_q': round(g / len(b) * 1000, 1),
        'validacion_a': {'precision': va['precision'], 'recall': va['recall'], 'ganancia_q': va['ganancia_q'],
                         'ganancia_por_1000_usuarios_q': round(va['ganancia_q'] / 59491 * 1000, 1)},
        'contactar_a_todos_q': g_todos,
        'cuenta_contactar_a_todos': f'10 · {vp_t:,} − 5 · {fp_t:,} = Q{g_todos:,.0f}',
    }
    REGISTRO.write_text(json.dumps(resultado, indent=2, ensure_ascii=False), encoding='utf-8')
    anotar_bitacora(f"{fecha} · commit {commit} · **TEST B (evaluación única)** con {resultado['modelo']}, umbral {umbral}: "
                    f"precisión promedio {resultado['metrica']['precision_promedio']} (base 2: "
                    f"{resultado['metrica']['base2_dias_desde_ultimo_viaje_precision_promedio']}; validación en A: "
                    f"{val_21['mejor_hgb']['ap_media']}), ROC-AUC {resultado['metrica']['roc_auc']}; VP {vp:,}, FP {fp:,}, "
                    f"FN {fn:,}, VN {tn:,}; precisión {resultado['precision']}, recall {resultado['recall']}; "
                    f"{resultado['cuenta_ganancia']}.")
    print(json.dumps(resultado, indent=2, ensure_ascii=False))


if __name__ == '__main__':
    main()
