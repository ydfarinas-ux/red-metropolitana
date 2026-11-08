"""2.3 Segmentación del corte A con KMeans y visualización con PCA.

- Se usan las 22 features numéricas del corte A (el perfil del padrón es categórico y queda fuera del KMeans;
  se reporta su composición por segmento). Antes de KMeans y PCA todo se escala con StandardScaler.
- k se elige con el método del codo (inercia) y la silueta (calculada sobre una muestra fija de 10,000 filas).
- La tasa de abandono por segmento es descriptiva: no prueba que el segmento cause el abandono.
- El segmento NO se usa como feature del clasificador, así que KMeans no necesita ajustarse dentro de la validación cruzada.

Uso: python proyecto2/segmentos.py
"""
import json

import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
import numpy as np
import pandas as pd
from sklearn.cluster import KMeans
from sklearn.decomposition import PCA
from sklearn.metrics import silhouette_score
from sklearn.preprocessing import StandardScaler

if __package__:
    from .config import SALIDA, SEMILLA
    from .datos_modelo import NUMERICAS, anotar_bitacora, cargar_corte, commit_y_fecha
else:
    from config import SALIDA, SEMILLA
    from datos_modelo import NUMERICAS, anotar_bitacora, cargar_corte, commit_y_fecha

KS = range(2, 11)
K_ELEGIDO = 4
MUESTRA_SILUETA = 10_000
COLUMNAS_TABLA = ['viajes_28d', 'viajes_7d', 'dias_activos_28d', 'dias_desde_ultimo_viaje', 'modos_distintos_28d',
                  'prop_transurbano', 'prop_aerometro', 'pagos_rechazados_28d', 'gasto_q_28d']
COLORES = ['#2a78d6', '#eb6834', '#1baf7a', '#8b5cf6', '#e0b000', '#9aa3ad']

ACCIONES = {
    'Ocasionales que se enfrían': 'Recarga de cortesía (la campaña) solo a quienes el modelo pone sobre el umbral: aquí se '
                                  'concentran los abandonos y cada contacto acertado deja Q10.',
    'Usuarios de Aerómetro': 'No regalar recarga: viajan por vuelos y su "abandono" suele ser falta de viaje, no pérdida. '
                             'Mensaje de bajo costo antes del regreso y mejorar el enlace de su tarjeta con la persona.',
    'Regulares': 'No contactar con recarga (abandono bajo). Encuesta corta o aviso de cambios de ruta para mantenerlos.',
    'Intensivos multimodales': 'Atender los pagos rechazados (recarga automática o alerta de saldo bajo) en lugar de '
                               'descuentos: casi no abandonan, pero son los que más gastan.',
}


def nombrar(medianas):
    """Nombres por reglas sobre las medianas, para que no dependan del número que KMeans le pone a cada grupo."""
    nombres = {}
    resto = list(medianas.index)
    aero = medianas.loc[resto, 'prop_aerometro'].idxmax()
    nombres[aero] = 'Usuarios de Aerómetro'
    resto.remove(aero)
    intensivo = medianas.loc[resto, 'viajes_28d'].idxmax()
    nombres[intensivo] = 'Intensivos multimodales'
    resto.remove(intensivo)
    orden = medianas.loc[resto, 'dias_desde_ultimo_viaje'].sort_values()
    nombres[orden.index[0]] = 'Regulares'
    nombres[orden.index[-1]] = 'Ocasionales que se enfrían'
    return nombres


def main():
    df = cargar_corte('A')
    X = StandardScaler().fit_transform(df[NUMERICAS])
    y = df['etiqueta'].to_numpy().astype(int)
    muestra = np.random.RandomState(SEMILLA).choice(len(X), MUESTRA_SILUETA, replace=False)

    filas = []
    for k in KS:
        km = KMeans(n_clusters=k, n_init=10, random_state=SEMILLA).fit(X)
        filas.append(dict(k=k, inercia=round(km.inertia_, 1),
                          silueta=round(silhouette_score(X[muestra], km.labels_[muestra]), 4)))
    eleccion = pd.DataFrame(filas)
    eleccion['caida_inercia_pct'] = (-eleccion.inercia.pct_change() * 100).round(1)
    eleccion.to_csv(SALIDA / '2.3-eleccion-k.csv', index=False)

    fig, (a1, a2) = plt.subplots(1, 2, figsize=(11, 4.2))
    a1.plot(eleccion.k, eleccion.inercia, 'o-', color='#2a78d6')
    a1.axvline(K_ELEGIDO, color='black', ls=':', lw=1)
    a1.set_title('Método del codo')
    a1.set_xlabel('k')
    a1.set_ylabel('Inercia (suma de distancias²)')
    a2.plot(eleccion.k, eleccion.silueta, 'o-', color='#eb6834')
    a2.axvline(K_ELEGIDO, color='black', ls=':', lw=1, label=f'k elegido = {K_ELEGIDO}')
    a2.set_title(f'Silueta (muestra de {MUESTRA_SILUETA:,} filas)')
    a2.set_xlabel('k')
    a2.set_ylabel('Silueta media')
    a2.legend(frameon=False)
    for a in (a1, a2):
        a.grid(alpha=0.3)
        a.spines[['top', 'right']].set_visible(False)
    fig.suptitle('2.3 Elección de k en el corte A (features escaladas)')
    fig.tight_layout()
    fig.savefig(SALIDA / '2.3-codo-silueta.png', dpi=150)
    plt.close(fig)

    km = KMeans(n_clusters=K_ELEGIDO, n_init=10, random_state=SEMILLA).fit(X)
    df['segmento_k'] = km.labels_
    medianas = df.groupby('segmento_k')[NUMERICAS].median()
    nombres = nombrar(medianas)
    df['segmento'] = df.segmento_k.map(nombres)

    tabla = df.groupby('segmento').agg(tamano=('unidad_id', 'size'), positivos=('etiqueta', 'sum'))
    tabla['positivos'] = tabla.positivos.astype(int)
    tabla['porcentaje_poblacion'] = (tabla.tamano / len(df)).round(4)
    tabla['tasa_abandono'] = (tabla.positivos / tabla.tamano).round(4)
    tabla['cuenta'] = [f'{p:,} / {n:,} = {p / n:.4f}' for p, n in zip(tabla.positivos, tabla.tamano)]
    med = df.groupby('segmento')[COLUMNAS_TABLA].median().add_prefix('mediana_')
    tabla = tabla.join(med)
    tabla['en_padron_pct'] = df.groupby('segmento').en_padron.mean().round(3)
    tabla['accion'] = tabla.index.map(ACCIONES)
    tabla = tabla.sort_values('tasa_abandono', ascending=False)
    tabla.reset_index().to_csv(SALIDA / '2.3-segmentos.csv', index=False)

    pca = PCA(n_components=2, random_state=SEMILLA).fit(X)
    Z = pca.transform(X)
    var = pca.explained_variance_ratio_
    cargas = pd.DataFrame(pca.components_.T, index=NUMERICAS, columns=['PC1', 'PC2']).round(4)
    cargas.to_csv(SALIDA / '2.3-pca-cargas.csv')
    fig, ax = plt.subplots(figsize=(8, 6))
    vista = np.random.RandomState(SEMILLA).choice(len(Z), 12_000, replace=False)
    for i, nombre in enumerate(tabla.index):
        m = (df.segmento.to_numpy() == nombre)
        sel = vista[m[vista]]
        ax.scatter(Z[sel, 0], Z[sel, 1], s=4, alpha=0.45, color=COLORES[i],
                   label=f'{nombre} (n={tabla.loc[nombre, "tamano"]:,}, abandono {tabla.loc[nombre, "tasa_abandono"]:.1%})')
    ax.set_xlabel(f'PC1 ({var[0]:.1%} de la varianza)')
    ax.set_ylabel(f'PC2 ({var[1]:.1%} de la varianza)')
    ax.set_title(f'2.3 Segmentos KMeans (k={K_ELEGIDO}) en dos componentes principales · varianza explicada {var.sum():.1%}')
    ax.legend(frameon=False, fontsize=8, markerscale=3)
    ax.spines[['top', 'right']].set_visible(False)
    fig.tight_layout()
    fig.savefig(SALIDA / '2.3-pca-segmentos.png', dpi=150)
    plt.close(fig)

    composicion = pd.crosstab(df.segmento, df.perfil, normalize='index').round(3)
    composicion.to_csv(SALIDA / '2.3-perfil-por-segmento.csv')

    commit, fecha = commit_y_fecha()
    elegido = eleccion.set_index('k').loc[K_ELEGIDO]
    resumen = {'fecha': fecha, 'commit': commit, 'k': K_ELEGIDO, 'filas': len(df),
               'silueta_k_elegido': float(elegido.silueta), 'silueta_maxima': {'k': int(eleccion.loc[eleccion.silueta.idxmax(), 'k']),
                                                                              'valor': float(eleccion.silueta.max())},
               'pca_varianza_explicada': [round(float(v), 4) for v in var],
               'pca_varianza_total': round(float(var.sum()), 4),
               'segmentos': tabla[['tamano', 'tasa_abandono', 'cuenta']].reset_index().to_dict(orient='records')}
    (SALIDA / '2.3-resumen.json').write_text(json.dumps(resumen, indent=2, ensure_ascii=False), encoding='utf-8')
    anotar_bitacora(f"{fecha} · commit {commit} · 2.3 KMeans k={K_ELEGIDO} en el corte A escalado (silueta "
                    f"{elegido.silueta:.4f}); PCA 2 componentes explica {var.sum():.1%}. Segmentos: " +
                    '; '.join(f"{n} {r.tamano:,} ({r.tasa_abandono:.1%} abandono)" for n, r in tabla.iterrows()) + '.')
    print(eleccion.to_string(index=False))
    print(tabla.drop(columns=['accion']).to_string())
    print(json.dumps(resumen, indent=2, ensure_ascii=False))


if __name__ == '__main__':
    main()
