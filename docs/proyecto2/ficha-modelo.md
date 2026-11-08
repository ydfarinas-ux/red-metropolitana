# Ficha del modelo: abandono de la red a 30 días (v1.0.0)

> **Aviso: los datos son simulados.** No corresponden a ningún operador ni usuario real. Las cifras sirven para el curso, no para decidir sobre personas reales.

| Campo | Valor |
|---|---|
| Archivo | `modelos/modelo_abandono_v1.0.0.joblib` (pipeline completo de scikit-learn 1.9.1: preprocesamiento + modelo, el umbral y los metadatos). Lo carga `predecir.py`, que no reentrena |
| Modelo | `HistGradientBoostingClassifier` (learning_rate = 0.1, max_leaf_nodes = 15, min_samples_leaf = 40, l2 = 1.0, parada temprana sobre un 10 % del entrenamiento; 103 árboles; semilla 2026) |
| Pregunta | Con lo que se sabe de una persona hasta la fecha de corte, ¿qué tan probable es que no vuelva a usar la red en los 30 días siguientes? |
| Datos y periodo | Los 9 archivos de la Agencia (Transmetro, Transurbano, MetroRiel, Aerómetro, CDC del padrón y catálogos), 1 de junio al 29 de agosto de 2026, cargados con el flujo del Proyecto 1 (Bronze → Silver). Solo registros válidos: la cuarentena no entra |
| Unidad | La persona (`usuario_sk`): tarjetas de Transmetro, Transurbano y MetroRiel enlazadas por su número; cada tarjeta de Aerómetro es una persona aparte porque su hash no se puede enlazar |
| Población | Personas con al menos 2 abordajes válidos en los 28 días antes del corte y sin un DELETE del CDC aplicado antes del corte. A: 59,491 · B: 58,113 · C: 57,701 |
| Etiqueta | 1 si la persona no tiene ningún abordaje válido, en ningún operador, en los 30 días que empiezan a las 00:00 de la fecha de corte; 0 si tiene al menos uno. A: 7,095 / 59,491 = 0.1193 · B: 6,387 / 58,113 = 0.1099 |
| Features | 23, todas de Silver con ventanas `[t − N días, t)` y N ≤ 28 (diccionario: `entregables/proyecto2/1.3-diccionario.csv`). Las más importantes por permutación: días desde el último viaje, pagos rechazados, perfil, viajes de 14 días y tendencia |
| Entrenamiento | Todo el corte A (fecha de corte 1 de julio). La configuración se eligió con validación cruzada estratificada de 5 folds solo en A |
| Métrica | Precisión promedio (área bajo precisión-recall): la campaña contacta a los de más riesgo y los positivos son ~11 % |
| Validación (A, 5 folds) | Precisión promedio **0.4388 ± 0.0113** (ROC-AUC 0.8446). Líneas base: constante 0.1193; días desde el último viaje 0.3892. Logística L2: 0.4129 |
| Test (B, una sola vez) | 8 nov 2026 12:21 (Guatemala), commit `556830f`. Precisión promedio **0.3905** (base 2: 0.3482; constante: 0.1099), ROC-AUC 0.8429 |
| Umbral y costo | Escenario: contactar Q5, retención 25 %, valor Q60 → G = 10·VP − 5·FP; equilibrio teórico p = 1/3. Umbral elegido con las predicciones fuera de fold de A: **0.33** (G = Q12,155 en A). En B: VP 2,653, FP 3,652, FN 3,734, VN 48,074 → precisión 0.421, recall 0.415, **G = 10 · 2,653 − 5 · 3,652 = Q8,270** |
| Corte C | `predicciones/predicciones_corte_2026-08-30.csv`: 57,701 personas, 7,268 a contactar (ganancia esperada según el modelo: Q17,177) |
| Fugas revisadas | (1) Prueba de recorte de 1.3: features de A con datos completos contra archivos crudos recortados al 30 de junio → 0 diferencias en 59,491 filas, con control negativo que sí detecta el perfil final. (2) Escalado y codificación dentro del pipeline, ajustados solo con el entrenamiento de cada fold. (3) Umbral elegido sin ver B; B evaluado una vez (`test_b.py` se niega a correr dos veces). (4) Ensayo de invariancia: predicciones del corte B con 30 días más de datos contra datos hasta el corte → CSV idéntico (SHA-256 igual). (5) Las tarjetas del CSV salen solo de la ventana anterior al corte |
| Limitaciones | Los 414 positivos de Aerómetro de A que siguieron viajando con otra tarjeta son falsos abandonos de la unidad (5.8 % de los positivos). El modelo se entrenó con un solo mes (junio → julio): en B la precisión promedio bajó de 0.439 a 0.391, igual que la línea base (de 0.389 a 0.348), así que el problema cambió con el mes; conviene reentrenar cada mes y vigilar la tasa de abandono. El puntaje ordena bien (ROC-AUC estable) pero la calibración depende de la tasa del mes. La tasa de retención del 25 % es un supuesto del escenario. `unidad_id` es un seudónimo que depende de `PSEUDO_SALT` (.env): las predicciones se deben generar y comparar con el mismo `.env` |
| Reproducir | `python predecir.py --datos datos_red --fecha-corte 2026-08-30` (Python 3.12, `requirements.txt` con versiones fijas, semilla 2026) |
