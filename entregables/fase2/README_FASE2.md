# Fase 2 completa

- **2.1:** `Red_Metropolitana_Fase2_Tableau.twbx`: siete hojas, tres dashboards y cuatro CSV agregados desde Gold.
- **2.2:** `Recomendacion_movilidad.pdf`: recomendación en dos páginas basada en las cifras del mismo tablero. Fuente editable `Recomendacion_movilidad.md` y evidencia `cifras_recomendacion.json`.
- **2.3:** `features_usuario.csv`: 70,380 filas y 14 campos; tabla dbt `features.features_usuario`, desde Silver. Diccionario en CSV/JSON/Markdown; corte exclusivo 16/07/2026. Solo 45 días observados: ventana de 90 días incompleta. No incluye un modelo ML.

## Ejecutar desde la raíz

```powershell
.venv\Scripts\python.exe herramientas/preparar_fase2.py --fecha-corte 2026-07-16
```

Requiere fase 1 ejecutada, `.env` propio y el warehouse existente. El comando construye únicamente features, ejecuta sus controles y exporta los cinco CSV. El libro Tableau ya contiene sus cuatro fuentes; features es un consumidor separado. Cambiar la fecha de corte exige actualizar el diccionario y regenerar las exportaciones. Para nuevos datos del tablero, actualizar las fuentes en Tableau y recalcular la recomendación.

Fuentes Tableau: `demanda.csv`, `cobertura.csv`, `multimodalidad.csv` y `metroriel.csv`. Consultas y corte: `linaje_exportaciones.json`. El CSV de features sigue siendo dato individual sensible aunque esté seudonimizado; para producción requiere acceso restringido.
