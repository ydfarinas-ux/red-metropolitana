# Bitácora del Proyecto 2

Cada corrida que se reporta en el informe queda anotada aquí, con su fecha y su commit, para poder repetirla.

## Decisiones

- **Unidad: la persona** (`usuario_sk`), con la estrategia de identidad del Proyecto 1: TM, TU y MR se enlazan por número y Aerómetro queda aparte.
- **Cortes:** A = 2026-07-01, B = 2026-07-31, C = 2026-08-30. Ventana de features de 28 días y etiqueta de 30 días, iguales en los tres cortes.
- **Población:** al menos 2 abordajes válidos en los 28 días antes del corte y ningún DELETE del CDC aplicado antes del corte (a cualquiera de las tarjetas de la persona).
- **El corte B no se usa en la Fase 1.** Su etiqueta se calcula pero ningún script de la Fase 1 la lee.
- **Features 1.3:** ventanas anteriores al corte, padrón SCD2 justo antes del corte y tarifas agregadas en centavos enteros. La auditoría recorta los archivos crudos sin reescribir sus líneas y reconstruye un warehouse independiente. El perfil final del padrón se usa como control negativo.
- **Verificación local de 1.3 (27 de octubre de 2026, Guatemala):** pasaron cinco pruebas con datos sintéticos (límites temporales, estado del padrón, control negativo, redondeo y recorte que conserva bytes). Al inicio solo estaban los datos del Proyecto 1; después se recibió `P2_datos_red.zip` y se reconstruyó todo con los nueve archivos nuevos. Los resultados medidos se registran en Corridas.
- **Control negativo:** se comparan perfiles por persona, tratando la ausencia de perfil en ambos lados como igualdad. La cifra de 49,115 del prompt incluye 35,202 ausencias en ambos lados; los cambios reales medidos son 13,913. La fuga se detecta sin contar esas ausencias como diferencias.

## Corridas

- 2026-10-27T23:41:47-06:00 · commit d121aca · reconstrucción con `P2_datos_red.zip` y `flows/pipeline.py --desde-cero`: Completed(), conteos de los nueve archivos correctos y 115 pruebas de dbt aprobadas. Total de etapas: 107.80 s; features: 5.84 s. A: 59,491 personas y 7,095 positivos; B: 58,113 personas y 6,387 positivos; C: 57,701 sin etiqueta. Validación final: CSV y warehouse coinciden, 0 duplicados, 0 nulos en features. Medianas de A para etiqueta 0/1: viajes_28d 11/4, viajes_7d 3/0, días desde último viaje 2/11.

- 2026-10-26 18:31 · primera carga de los datos del Proyecto 2 desde cero: los 9 archivos cuadran con los conteos esperados del LEEME.txt (0 diferencias) y pasan las 115 pruebas de dbt.
- 2026-10-27 · corrida con el comando único (`flows/pipeline.py --desde-cero`): 0 diferencias en los conteos, 115 pruebas de dbt, población A 7,095 / 59,491 = 0.1193, B 6,387 / 58,113 = 0.1099 y C 57,701 sin etiqueta. Costo de la unidad en A: 414 de 7,095 positivos son personas de Aerómetro que siguieron viajando con otra tarjeta. En esta corrida el streaming simulado tardó 1,420 s (la máquina estaba ocupada; en la carga anterior tardó 48 s).

- 2026-10-27T23:43:18-06:00 · commit d121aca · prueba de recorte (fórmulas flotantes anteriores): 59,491 filas, 46 diferencias, 0 filas en un solo lado; features: tarifa_promedio_q. Control negativo perfil final: 13,913 diferencias, detectado=True. La suma y el promedio en punto flotante pueden variar por el orden de agregación en paralelo; los valores a mitad de redondeo pueden cambiar en el cuarto decimal. Esto no demuestra por sí solo una fuga temporal.

- 2026-10-27T23:45:33-06:00 · commit d121aca · prueba de recorte (centavos enteros): 59,491 filas, 0 diferencias, 0 filas en un solo lado; features: ninguna. Control negativo perfil final: 13,913 diferencias, detectado=True.

- 2026-10-28T15:58:38-06:00 · commit d3ea4b0 · 1.4 modelos en el corte A: 59,491 filas, tasa positiva 0.1193, 5 folds estratificados (semilla 2026). Mejor logística: Logística L2 (lambda=100), precisión promedio 0.4129 ± 0.0112 (ROC-AUC 0.8312).

- 2026-10-28T16:00:41-06:00 · commit d3ea4b0 · prueba de recorte (centavos enteros): 59,491 filas, 0 diferencias, 0 filas en un solo lado; features: ninguna. Control negativo perfil final: 13,913 diferencias, detectado=True.

- 2026-10-28 · commit d3ea4b0 · corrida final del informe con las cuatro partes juntas (`flows/pipeline.py --desde-cero --auditoria`): Completed(), 0 diferencias en los conteos, 115 pruebas de dbt, A 7,095 / 59,491 = 0.1193, B 6,387 / 58,113 = 0.1099, C 57,701 sin etiqueta, prueba de recorte con 0 diferencias y mejor logística L2 (λ = 100) con precisión promedio 0.4129. Total 582.85 s (la máquina estaba ocupada; el streaming simulado tardó 101 s).
