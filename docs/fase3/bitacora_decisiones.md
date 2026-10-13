# 3.2 Bitácora de decisiones

Registro de formalización del 12/10/2026. Resume decisiones observables en el código y sus límites; no simula una bitácora previa a la implementación.

| Decisión | Justificación | Límite y evidencia |
|---|---|---|
| Abordaje como grano común | TM y AM entregan validaciones; TU transacciones; MR viajes completos. La entrada MR permite comparar los cuatro. | No equivale a viaje puerta a puerta. Modelos `fct_abordaje` y `silver_abordajes`. |
| Hecho MR separado | Preservar origen, destino y duración sin perder información. | No sumar con abordajes de la red. `fct_trayecto_metroriel`. |
| Vinculación TM/TU/MR por número | Normalizar formatos de tarjeta, apoyado por el padrón sintético. | Supuesto de numeración compartida; puede unir personas diferentes en producción. `silver_identidad_usuario`. |
| AM conserva identidad separada | Su hash no aporta vínculo fiable con otros operadores. | Total de usuarios puede estar sobreestimado; multimodalidad con AM queda subestimada. `vincular_aerometro=false`. |
| Seudonimización en Silver | Gold no requiere la tarjeta original. | MD5 con sal no constituye anonimización ni protección criptográfica recomendada para producción. Macro `seudonimo`. |
| Zona por catálogo | Unificar zona de estación y preservar territorios sin estaciones. | Zona de abordaje distinta de residencia. Macro `normalizar_territorio`; seed `territorios`. |
| Cuarentena con primera regla | Conservar registro crudo, motivo y linaje sin descartar silenciosamente. | Un evento puede fallar varias reglas pero solo cuenta bajo la primera. `silver_eventos_evaluados`. |
| Rechazos TU separados | Estados 7 y 9 son transacciones válidas rechazadas, no abordajes ni errores de calidad. | 41,390 conservados aparte. `silver_transacciones_rechazadas_tu`. |
| Fecha futura contra ingesta | La regla usa `_ingested_at`, no la fecha de hoy. | Depende de la marca de ingesta registrada. Evita cambiar clasificación al repetir una corrida. |
| CDC y SCD2 | Conservar historial de perfil, zona y estado por tarjeta. | DELETE abre una versión inactiva; las versiones no se suman como personas. |
| Deduplicación por archivo/evento | Hash de archivo evita reingesta; ID del evento evita duplicaciones operativas. | En TU el ID es hash de contenido y puede colapsar dos transacciones idénticas genuinas. |
| Streaming simulado | Es el modo definido en README para esta entrega. | Prueba la vía local, no una infraestructura Kafka de producción. |
| Separar fuentes del tablero | Distintos granos para demanda, cobertura, usuarios y corredor. | Agregados de usuarios y corredor cubren todo el período; no tratarlos como detalle diario. |

Se ejecutó el README del repositorio restaurado: generación de datos, corrida 1, corrida 2, comparación y DDL. No se reescribió el pipeline para producir el tablero. Las dos corridas reportaron 108 resultados correctos (modelos, seeds y pruebas), y 52 tablas con conteos idénticos.

El diccionario de fase 3 añade descripciones a `dbt/models/gold/gold.yml`; no cambia el SQL ni los tests. `dbt docs generate --static` genera catálogo y grafo a partir del proyecto y el warehouse existente. Las copias de entrega tienen la sal retirada porque dbt puede incorporarla al SQL compilado.


## Extensión actual de fases 2 y 3

- Se añadió `features_usuario` desde Silver con corte exclusivo 16/07/2026, ventanas 7/30/90 días y empates determinísticos. Se declara cobertura de 45 días.
- Se detectó variación de punto flotante al repetir importes y se resolvió usando sumas DECIMAL de dos posiciones y proporciones por conteos. Dos builds producen contenido idéntico.
- Se verificaron seis controles dbt y una prueba de límites con datos controlados; no se entrenó ningún modelo ni se generaron etiquetas ficticias.
- La recomendación formal de dos páginas propone estudiar una conexión alimentadora Zona 11-Zona 12, basada en las fuentes del tablero. No decide una estación exacta sin evidencia de accesibilidad.
- El usuario confirmó la distribución de dominios: Yasmely, territorio/estaciones; Jose Rodrigo, sistemas/calendario/métricas; Walter, identidad/CDC/calidad.
- La seguridad incluye explícitamente las features como detalle sensible con acceso restringido y retención de 180 días. Se actualizó el grafo dbt, los diccionarios, README y entrega PDF.
