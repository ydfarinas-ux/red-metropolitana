# Fase 3 - Red Metropolitana

Entrega basada en el repositorio existente y las corridas del 12/10/2026. No modifica el pipeline de fase 1 ni la lógica de Gold.

| Componente | Archivos |
|---|---|
| 3.1 Diccionario completo, 91 campos | `diccionario_gold.csv`, `.json`, `.md`; descripciones en `dbt/models/gold/gold.yml` |
| 3.1 Definiciones y responsables | `definiciones_y_responsables.md` |
| 3.1 Calidad | `reglas_calidad.md` |
| 3.1 Linaje dbt | `linaje_dbt/static_index.html`, `manifest.json`, `catalog.json`, `aristas_linaje.json`; `linaje_tablero.md` y consultas de exportación |
| 3.2 Reproducción y decisiones | `reproducibilidad.md`, `bitacora_decisiones.md`, `historial_git.txt` y README principal |
| 3.3 Seguridad, una página | `Seguridad_datos_personales.pdf` y fuente Markdown |
| Resumen para defensa | `Gobernanza_y_reproducibilidad.pdf` |
| Métricas y evidencia | `metricas_medidas.md`, `metricas_verificadas.json` y comparación de corridas |

Abrir la documentación dbt autocontenida `linaje_dbt/static_index.html` y explorar el grafo. Los nombres de roles son asignaciones institucionales propuestas, pendientes de asociar a integrantes del grupo. Los controles de acceso y retención son política declarada: el prototipo no los automatiza.

Fase 2 existente: el libro Tableau está en `entregables/fase2/Red_Metropolitana_Fase2_Tableau.twbx`. La entrega actual documenta el tablero; no afirma que exista una recomendación formal independiente ni una tabla de features integrada a dbt.
