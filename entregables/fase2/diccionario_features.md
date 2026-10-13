# Diccionario de features - 2.3

Tabla `features.features_usuario`: 70380 usuarios, 14 campos.

| Campo | Tipo | Definición | Transformación |
|---|---|---|---|
| usuario_sk | VARCHAR | Identidad seudonimizada de Silver; llave de la fila. No identidad civil. | silver_abordajes.usuario_sk |
| fecha_corte | DATE | 2026-07-16 a las 00:00, hora local; corte exclusivo. | Variable fecha_corte_features |
| viajes_7d | BIGINT | Número de abordajes limpios en [corte-7 días, corte). | COUNT de Silver |
| viajes_30d | BIGINT | Número de abordajes limpios en [corte-30 días, corte). | COUNT de Silver |
| viajes_90d | BIGINT | Número de abordajes limpios en [corte-90 días, corte). No viaje puerta a puerta. | COUNT de Silver |
| modos_distintos_90d | BIGINT | Cantidad de sistemas utilizados en 90 días; entre 1 y 4. | COUNT DISTINCT sistema |
| dias_desde_ultimo_viaje | BIGINT | Días calendario desde la última fecha de abordaje hasta el corte. | DATE_DIFF desde MAX fecha |
| proporcion_hora_pico_90d | DOUBLE | Fracción [0,1] de abordajes en días hábiles, excluyendo festivos, horas 06-08 o 17-19. | Silver.fecha/hora y seed festivos_gt |
| gasto_q_90d | DECIMAL(38,2) | Importe registrado acumulado, en GTQ; suma decimal de dos posiciones. | SUM de Silver.monto_q DECIMAL(18,2) |
| gasto_promedio_q_90d | DOUBLE | Importe registrado medio por abordaje en GTQ. | gasto_q_90d / viajes_90d |
| dias_historial_disponible_90d | BIGINT | Días desde el inicio observado de la fuente hasta el corte, máximo 90. Es cobertura de fuente, no antigüedad del usuario. | MIN fecha de Silver anterior al corte |
| ventana_90d_completa | BOOLEAN | Indica si existe al menos 90 días de historia de fuente anterior al corte. | dias_historial_disponible_90d = 90 |
| modo_mas_usado_90d | VARCHAR | Sistema con más abordajes en la ventana; empate por código ascendente. | COUNT por usuario/sistema y ROW_NUMBER |
| zona_origen_frecuente_90d | INTEGER | Zona de la estación de abordaje más frecuente; empate por zona_key ascendente. No domicilio ni origen puerta a puerta. | COUNT por usuario/zona y ROW_NUMBER |

## Población, ventana y uso

Una fila por usuario con al menos un abordaje válido en los 90 días anteriores al corte exclusivo **2026-07-16 00:00:00 America/Guatemala**. Se observa del 01/06 al 15/07/2026: 45 días. La ventana de 90 días es incompleta; los días anteriores sin archivos no deben interpretarse como inactividad. Ningún evento en el corte o posterior entra en los predictores.

La fuente es exclusivamente `silver_abordajes`, más el seed de feriados; no se lee Gold. Se eliminan tarjeta, persona_id, llave original y marcas individuales; se conserva usuario_sk para enlazar futuros resultados bajo acceso restringido. La identidad de Aerómetro sigue separada de TM/TU/MR. Una fila corresponde a la identidad resuelta, que puede no ser una persona civil.

**Uso posible:** predecir si un usuario dejará de abordar en los siguientes 30 días para orientar medidas de retención y continuidad de servicio. Sería útil a la Agencia para priorizar seguimiento agregado por zona y modo. La tabla contiene predictores; no se entrenó un modelo ni se fabricaron etiquetas. Se necesitan 30 días posteriores al corte para construir el resultado objetivo y varias cohortes históricas para validar temporalmente. Excluir usuario_sk como predictor y aplicar codificación de categorías dentro de cada partición de entrenamiento.

Los importes son pagos registrados; no representan necesariamente gasto completo del usuario. Las counts son abordajes, no trayectos puerta a puerta.

## Verificación

Seis controles dbt: usuario único y no nulo; corte no nulo; modo válido; invariantes de ventanas/importes; conciliación independiente desde Silver. Dos builds produjeron el mismo contenido SHA-256. Prueba con datos controlados: límites 7/30/90 días, exclusión de futuro, feriado, empates y recencia. Las evidencias están en `validacion_features.json` y `validacion_limites_features.json`.
