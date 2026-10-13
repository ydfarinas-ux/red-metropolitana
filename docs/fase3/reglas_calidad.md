# 3.1 Reglas de calidad y tratamiento

Formalización de las reglas ya implementadas. No se afirma que este documento existía antes del código. Se revisan en este orden y se asigna un único motivo por evento:

1. `DUPLICADO_REINGESTA`: repetición del evento en otro archivo; mantener la primera ingesta.
2. `DUPLICADO_TORNIQUETE`: repetición dentro del mismo archivo; mantener la primera fila.
3. `USUARIO_NULO`: llave de usuario ausente.
4. `PARADA_NULA`: estación/parada ausente.
5. `ESTACION_DESCONOCIDA`: estación fuera del catálogo.
6. `FECHA_INVALIDA`: fecha no interpretable.
7. `FECHA_FUTURA`: instante posterior a ingesta local registrada.
8. `VIAJE_SIN_SALIDA`: MR sin estación o fecha de salida.
9. `SALIDA_INCONSISTENTE`: MR con salida anterior/igual a entrada, estación igual o salida fuera del catálogo.
10. `ZONA_INVALIDA`: territorio no conformado.
11. `MONTO_INVALIDO`: importe nulo o negativo.
12. `ESTADO_DESCONOCIDO`: TU fuera de los estados permitidos.

CDC: `CDC_SIN_TARJETA` y `CDC_UPDATE_SOBRE_BAJA` se separan de las operaciones aplicadas. UPDATE tras baja solo se reactiva con la regla explícita existente en CDC.

Tratamiento: conservar en `silver_cuarentena` motivo, explicación, registro crudo y fuente; contabilizar por sistema y regla; restringir el acceso por contener tarjetas e historial individual. El dueño de fuente investiga, corrige en origen y conserva evidencia. No editar Gold para esconder el error; reingresar un archivo corregido y repetir validaciones. Propuesta de plazo de atención: 5 días hábiles para incidencias que alteran métricas, escalamiento al comité si no se resuelven.

Las transacciones TU rechazadas por saldo o tarjeta (7/9) se conservan en otra tabla y no se consideran cuarentena. Conservación operativa verificada: 1,698,666 eventos de transporte = 1,647,569 abordajes + 41,390 rechazos TU + 9,707 en cuarentena. CDC aporta 2,629 casos adicionales; cuarentena total = 12,336. No sumar catálogos al denominador operativo. El porcentaje operativo es 9,707/1,698,666 = 0.5714%; CDC es 2,629/31,050 = 8.4670%.

Controles existentes: pruebas de unicidad, no nulos, relaciones, conservación Bronze/Silver, CDC completo y equivalencia padrón/SCD2. Cero registros observados para una regla no demuestra que la regla sea innecesaria; el generador no activa todos los casos.
