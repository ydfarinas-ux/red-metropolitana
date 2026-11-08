"""2.2 / 2.4 Entrena el modelo de producción con TODO el corte A y lo guarda con su versión.

- Modelo: el HistGradientBoosting elegido en 2.1 (misma configuración y semilla).
- Umbral: el elegido en 2.2 con las predicciones fuera de fold del corte A (2.2-umbral.json).
- Se guarda el pipeline completo (preprocesamiento + modelo), el umbral y los metadatos en
  modelos/modelo_abandono_v<versión>.joblib. predecir.py solo lo carga, no reentrena.
- Este script no lee el corte B.

Uso: python proyecto2/entrenar_final.py
"""
import hashlib
import json
import platform
import time

import joblib
import sklearn

if __package__:
    from .config import CORTES, HORIZONTE_DIAS, SALIDA, SEMILLA, VENTANA_DIAS
    from .datos_modelo import DIR_MODELOS, anotar_bitacora, cargar_corte, commit_y_fecha
    from .ensemble import HGB_CONFIGS, hgb
    from .features import FEATURES
else:
    from config import CORTES, HORIZONTE_DIAS, SALIDA, SEMILLA, VENTANA_DIAS
    from datos_modelo import DIR_MODELOS, anotar_bitacora, cargar_corte, commit_y_fecha
    from ensemble import HGB_CONFIGS, hgb
    from features import FEATURES

VERSION = '1.0.0'


def main():
    t0 = time.perf_counter()
    df = cargar_corte('A')
    y = df['etiqueta'].to_numpy().astype(int)
    resumen_21 = json.loads((SALIDA / '2.1-resumen.json').read_text(encoding='utf-8'))
    resumen_22 = json.loads((SALIDA / '2.2-umbral.json').read_text(encoding='utf-8'))
    nombre = resumen_21['mejor_hgb']['modelo']
    modelo = hgb(**HGB_CONFIGS[nombre]).fit(df[FEATURES], y)
    segundos = round(time.perf_counter() - t0, 2)

    commit, fecha = commit_y_fecha()
    DIR_MODELOS.mkdir(exist_ok=True)
    ruta = DIR_MODELOS / f'modelo_abandono_v{VERSION}.joblib'
    paquete = {
        'version': VERSION, 'nombre': nombre, 'pipeline': modelo, 'umbral': resumen_22['umbral_elegido'],
        'features': FEATURES, 'entrenado_con': f"corte A ({CORTES['A']}), {len(df):,} personas, {int(y.sum()):,} positivos",
        'ventana_features_dias': VENTANA_DIAS, 'horizonte_etiqueta_dias': HORIZONTE_DIAS, 'semilla': SEMILLA,
        'iteraciones': int(modelo.named_steps['modelo'].n_iter_),
        'fecha_entrenamiento': fecha, 'commit': commit, 'sklearn': sklearn.__version__, 'python': platform.python_version(),
    }
    joblib.dump(paquete, ruta)
    sha = hashlib.sha256(ruta.read_bytes()).hexdigest()
    meta = {k: v for k, v in paquete.items() if k != 'pipeline'}
    meta.update(archivo=ruta.name, sha256=sha, segundos_entrenamiento=segundos)
    (DIR_MODELOS / f'modelo_abandono_v{VERSION}.json').write_text(json.dumps(meta, indent=2, ensure_ascii=False),
                                                                  encoding='utf-8')
    anotar_bitacora(f"{fecha} · commit {commit} · modelo de producción {ruta.name}: {nombre} entrenado con todo el corte A "
                    f"({len(df):,} filas, {meta['iteraciones']} iteraciones, {segundos} s), umbral {paquete['umbral']}, "
                    f"sha256 {sha[:12]}.")
    print(json.dumps(meta, indent=2, ensure_ascii=False))


if __name__ == '__main__':
    main()
