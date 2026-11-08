# Guion de la defensa (Proyecto 2)

Cada integrante debe poder explicar **cualquier** decisión, no solo la suya. Abajo están todas las decisiones con sus alternativas y por qué se descartaron, más las preguntas de fondo que seguro van a hacer.

## Prueba de invariancia en vivo (hacerla así)

1. Copiar los datos nuevos (con 30 días más) a `datos_red/`, reemplazando los anteriores.
2. `.venv\Scripts\python.exe flows\pipeline.py --desde-cero`
3. `.venv\Scripts\python.exe predecir.py --datos datos_red --fecha-corte 2026-08-30 --salida predicciones\defensa.csv`
4. Comparar: `certutil -hashfile predicciones\defensa.csv SHA256` contra `certutil -hashfile predicciones\predicciones_corte_2026-08-30.csv SHA256`, o en PowerShell `Compare-Object (Get-Content predicciones\defensa.csv) (Get-Content predicciones\predicciones_corte_2026-08-30.csv)` (sin salida = idénticos).
5. Correrlo en la misma máquina y con el mismo `.env` con el que se generó el CSV entregado (`unidad_id` depende de `PSEUDO_SALT`).

Por qué va a salir igual: ya lo ensayamos con el corte B, que tiene 30 días de datos después: datos completos contra datos recortados al corte → SHA-256 idéntico (`entregables/proyecto2/2.4-ensayo-invariancia.json`).

## Presentación de 15 minutos

| Min | Tema | Lo que hay que decir |
|---|---|---|
| 0-2 | Problema | Clasificación binaria por persona y fecha de corte: ¿deja de viajar en 30 días? Features solo antes del corte. A entrena, B se evalúa una vez, C se entrega |
| 2-4 | Datos, unidad y etiqueta (Fase 1) | Persona, población, A 7,095 / 59,491 = 0.1193; B 6,387 / 58,113 = 0.1099; costo de la unidad: 414 positivos de Aerómetro siguieron viajando |
| 4-6 | Fugas | Prueba de recorte con 0 diferencias y control negativo; pipeline dentro de cada fold; B una sola vez; invariancia ensayada |
| 6-9 | Modelos | Tabla con líneas base al lado; logística 0.413 → HGB 0.439; sesgo-varianza; importancias |
| 9-11 | Umbral y test B | G = 10·VP − 5·FP; umbral 0.33 = 1/3; en B: Q8,270, precisión 0.421, recall 0.415; por qué bajó |
| 11-13 | Segmentos | 4 segmentos, tasas 21 % / 14 % / 4 % / 2 % y una acción por segmento |
| 13-15 | Producción | predecir.py, modelo versionado, ficha, 7,268 contactos para el corte C |

## Decisiones (qué, alternativas, por qué)

### Fase 1

- **Unidad = persona.** Alternativa: tarjeta. Con la tarjeta, alguien que cambia de operador (deja Transurbano y sigue en Transmetro con el mismo número) cuenta como abandono aunque siga en la red. Costo de la persona: Aerómetro no se puede enlazar (hash sin número) y 414 de 7,095 positivos de A son personas de Aerómetro que siguieron viajando con otra tarjeta.
- **Ventana de 28 días.** Es la más larga que cabe en el corte A (datos desde el 1 de junio) y debe medir lo mismo en los tres cortes.
- **Métrica = precisión promedio.** Alternativas: exactitud (engaña con 11 % de positivos: decir "nadie se va" da 88 %), ROC-AUC (se reporta, pero premia ordenar bien a los negativos, que no importan porque no se contactan). La campaña contacta a los de más riesgo: importa que los que se van estén arriba.
- **Logística L2 con λ = 100.** Se compararon L2, L1 y Elastic Net con 13 valores de λ; las tres quedan en 0.412-0.413, la curva es plana hasta λ = 100 porque hay muchos datos para pocas features.

### 2.1 Ensemble

- **HistGradientBoosting (lr = 0.1, 15 hojas) va a producción.** Alternativas: Random Forest (mejor 0.4226) y la logística (0.4129). Gana +0.026 de precisión promedio sobre la logística (2.3 desviaciones estándar) y gana en los 5 folds; en dinero, en A deja Q12,155 contra Q10,875 de la logística (+12 %). Su complejidad es baja en la práctica: entrena en 1 segundo, se guarda igual con joblib y la importancia por permutación explica qué usa.
- **Sesgo-varianza.** Logística: entrenamiento 0.414 y validación 0.413, casi sin brecha pero por debajo del ensemble → sesgo alto (una suma lineal de features no capta relaciones no lineales ni interacciones entre ellas, que los árboles sí). RF sin podar: 0.997 contra 0.371 → varianza alta (memoriza). HGB y RF con 50 por hoja: brecha ~0.05 con la mejor validación → equilibrados.
- **learning_rate cumple el papel de α.** Con lr = 0.05 hacen falta más árboles y queda casi igual (0.438); con 31 hojas sube el entrenamiento y baja la validación (más varianza).
- **Importancia por permutación en validación**, no en entrenamiento: en entrenamiento mide lo que el modelo memorizó; en validación mide cuánto cae la métrica con datos que no vio. La primera es días desde el último viaje (cae 0.229).

### 2.2 Umbral

- **Fórmula.** Contactar a alguien que se iba: 0.25 · 60 − 5 = Q10; a alguien que no se iba: −Q5. G = 10·VP − 5·FP. Para una persona con probabilidad p: conviene si 15p − 5 > 0 → p > 1/3.
- **Umbral 0.33.** Se eligió con las predicciones fuera de fold de A (no con B). Coincide con el 1/3 teórico porque el HGB está bien calibrado. Por fold el óptimo va de 0.33 a 0.38.
- **Test B una sola vez**, commit `556830f`. Precisión promedio 0.3905 (peor que 0.4388 en validación). No se reajustó. Explicación: en B bajó la tasa de abandono (0.1193 → 0.1099) y la línea base cayó en la misma proporción (0.389 → 0.348, −10 %; el modelo −11 %); el ROC-AUC casi no cambió (0.845 → 0.843): el modelo ordena igual de bien, pero hay menos positivos y el mes es distinto. Sigue ganando a la línea base y deja Q8,270 frente a −Q194,760 de contactar a todos.

### 2.3 Segmentos

- **k = 4.** La silueta máxima es k = 2, pero solo separa "intensivos" del resto. Los picos de k = 6-7 separan por operador (Transmetro, Transurbano, MetroRiel, Aerómetro) con la misma tasa de abandono (13-15 %), que no sirve para retener. En k = 4 la inercia deja de caer rápido (11 % y 9 % hasta 4, luego 7 % y menos) y los segmentos tienen tasas muy distintas: 21 %, 14 %, 4 % y 2 %.
- **Escalado.** Sin escalar, gasto y viajes (decenas) dominarían a las proporciones (0 a 1).
- **El segmento no es feature del clasificador**, así que KMeans no tiene que ir dentro de la validación cruzada. La tasa por segmento es descriptiva: no prueba que el segmento cause el abandono.

### 2.4 Producción

- **predecir.py no reentrena**: carga el `.joblib` (pipeline completo, umbral y versión).
- **Tarjetas** salen de la ventana anterior al corte: si salieran de toda la data, una tarjeta nueva en septiembre cambiaría el CSV.
- **Versiones fijas** en `requirements.txt`; se fijó fastapi 0.150.0 porque la 0.156 o más nueva rompe prefect 3.8.6.

## Preguntas de fondo

- **¿Dónde pudo haber fuga y cómo lo saben?** Features que usen datos posteriores (prueba de recorte: 0 diferencias); escalado ajustado con todo A antes de la validación (va dentro del Pipeline de cada fold); umbral o hiperparámetros elegidos mirando B (B se usó una vez, registrado); perfil del padrón final en vez del vigente al corte (SCD2, control negativo que sí detecta 13,913 cambios si se usara el final); tarjetas o población con datos futuros (ensayo de invariancia con B idéntico).
- **¿Por qué esa métrica?** Ver arriba: positivos raros y la decisión es a quién contactar primero.
- **¿De dónde sale el umbral?** De maximizar G = 10·VP − 5·FP sobre las predicciones fuera de fold de A; coincide con el 1/3 teórico.
- **¿Por qué el ensemble si es más complejo?** Gana en los 5 folds, +12 % de ganancia, entrena en 1 s; la logística queda como respaldo interpretable.
- **¿Qué harían con más tiempo?** Reentrenar con A + B para producción, vigilar la tasa mensual, enlazar Aerómetro con otra fuente.
