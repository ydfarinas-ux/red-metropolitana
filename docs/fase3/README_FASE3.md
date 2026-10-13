# Fase 3 - Red Metropolitana

Entrega basada en el repositorio existente y las corridas del 12/10/2026. Añade la documentación de la capa de features de fase 2; preserva la lógica de la fase 1 y de Gold.

| Componente | Archivos |
|---|---|
| 3.1 Diccionario completo, 91 campos | `diccionario_gold.csv`, `.json`, `.md`; descripciones en `dbt/models/gold/gold.yml` |
| 3.1 Definiciones y responsables | `definiciones_y_responsables.md` |
| 3.1 Calidad | `reglas_calidad.md` |
| 3.1 Linaje dbt | `linaje_dbt/static_index.html`, `manifest.json`, `catalog.json`, `aristas_linaje.json`; `linaje_tablero.md` y consultas de exportación |
| 3.2 Reproducción y decisiones | `reproducibilidad.md`, `bitacora_decisiones.md`, `historial_git.txt` y README principal |
| 3.3 Seguridad, una página | `Seguridad_datos_personales.pdf` y fuente Markdown |
| Resumen para defensa | `Gobernanza_y_reproducibilidad.pdf` |
| Métricas y evidencia | `metricas_medidas.md`, `metricas_verificadas.json`, comparación de corridas y `metricas_extension_fase2.md` |

Abrir la documentación dbt autocontenida `linaje_dbt/static_index.html` y explorar el grafo. Los responsables académicos están asignados a Yasmely, Jose Rodrigo y Walter en `definiciones_y_responsables.md`, el diccionario y la documentación dbt. Los controles de acceso y retención son política declarada: el prototipo no los automatiza.

Fase 2 completa: `entregables/fase2/README_FASE2.md` reúne el tablero, la recomendación de dos páginas y las features con diccionario, corte y validaciones. El grafo dbt incorpora `features_usuario` conectado a Silver.
