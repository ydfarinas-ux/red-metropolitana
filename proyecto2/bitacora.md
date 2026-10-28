# Bitácora del Proyecto 2

Cada corrida que se reporta en el informe queda anotada aquí, con su fecha y su commit, para poder repetirla.

## Decisiones

- **Unidad: la persona** (`usuario_sk`), con la estrategia de identidad del Proyecto 1: TM, TU y MR se enlazan por número y Aerómetro queda aparte.
- **Cortes:** A = 2026-07-01, B = 2026-07-31, C = 2026-08-30. Ventana de features de 28 días y etiqueta de 30 días, iguales en los tres cortes.
- **Población:** al menos 2 abordajes válidos en los 28 días antes del corte y ningún DELETE del CDC aplicado antes del corte (a cualquiera de las tarjetas de la persona).
- **El corte B no se usa en la Fase 1.** Su etiqueta se calcula pero ningún script de la Fase 1 la lee.

## Corridas

- 2026-10-26 18:31 · primera carga de los datos del Proyecto 2 desde cero: los 9 archivos cuadran con los conteos esperados del LEEME.txt (0 diferencias) y pasan las 115 pruebas de dbt.
- 2026-10-27 · corrida con el comando único (`flows/pipeline.py --desde-cero`): 0 diferencias en los conteos, 115 pruebas de dbt, población A 7,095 / 59,491 = 0.1193, B 6,387 / 58,113 = 0.1099 y C 57,701 sin etiqueta. Costo de la unidad en A: 414 de 7,095 positivos son personas de Aerómetro que siguieron viajando con otra tarjeta. En esta corrida el streaming simulado tardó 1,420 s (la máquina estaba ocupada; en la carga anterior tardó 48 s).
