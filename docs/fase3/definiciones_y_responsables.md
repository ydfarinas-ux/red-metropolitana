# 3.1 Definiciones oficiales y responsables

Fecha de formalización: 12 de octubre de 2026. Versión 1.0. Aplicable a datos sintéticos del curso, período observado 1 de junio a 15 de julio de 2026. Las reglas describen el código existente; su formalización es posterior a la implementación. No se atribuye una aprobación institucional real.

## Contrato de métricas

| Término | Definición y cálculo oficial |
|---|---|
| Abordaje | Una validación de entrada limpia en `gold.fct_abordaje`. TM incluye ENTRADA y TRANSBORDO; TU solo estados 1, 2 y 3; MR aporta la entrada; AM aporta el abordaje de cabina. `SUM(cantidad_abordajes)`. |
| Viajes de la red | En este proyecto, indicador operativo de abordajes, rotulado como tal. No inferir viajes puerta a puerta ni sumar trayectos MR adicionales a sus entradas. |
| Trayecto MetroRiel | Un viaje MR completo con entrada y salida válidas en `fct_trayecto_metroriel`. `SUM(cantidad_trayectos)`. |
| Usuario activo | Identidad seudonimizada con al menos un abordaje limpio dentro de `[inicio, fin)`, hora local. `COUNT(DISTINCT usuario_sk)` en el hecho filtrado. No significa tarjeta activa del padrón. |
| Usuario multimodal observado | Usuario activo con `COUNT(DISTINCT sistema_key)>1` en el mismo período. Se cuentan hechos, no `dim_usuario.es_multisistema`. No demuestra transbordos encadenados. |
| Usuario con tarjetas multisistema | `dim_usuario.es_multisistema`: sistemas en el catálogo de identidad, incluso llaves de eventos rechazados y del padrón. Tiene otra población que el tablero. |
| Cobertura | Presencia de estaciones de cada modo en `dim_zona`, conservando los 26 territorios aunque no tengan registros de operación. No mide alcance peatonal, frecuencia ni capacidad. |
| Territorio sin servicio | `tiene_servicio=false`: ausencia de estaciones en el catálogo. No afirmar ausencia de todo transporte real. |
| Hora pico | Día hábil y 06:00-08:59 o 17:00-19:59. Día hábil: lunes a viernes excluyendo festivos del seed. |
| Demanda del corredor | Abordajes TM/TU en zonas 12, 8, 1, 6 y 17 / abordajes TM/TU totales. Evita justificar MR únicamente con su propia demanda. |
| Importe | GTQ, convertido desde centavos en TU. Aditivo dentro de un hecho; los mismos importes MR no se suman entre hechos. |
| Tarjetas activas del padrón | Stock al cierre del día; semiaditivo, nunca sumar entre días. `altas_del_dia` y `bajas_del_dia` del hecho son versiones presentes al cierre; para todas las operaciones aplicadas usar el resumen CDC. |
| Estaciones recorridas MR | Diferencia absoluta de orden entre origen y destino; mide tramos de separación, no conteo de paradas incluidas. |

## Dueños por dominio

Los responsables se asignan por rol para la propuesta de la Agencia. El grupo debe mapear cada rol a un integrante real antes de la defensa; no se inventan nombres.

| Dominio | Dueño responsable | Custodio técnico | Quién autoriza cambios |
|---|---|---|---|
| Zona y estación | Coordinación territorial AMT | Ingeniería de datos | Coordinación territorial, con validación del operador afectado |
| Sistema y catálogo operativo | Coordinación de operadores AMT | Ingeniería de datos | Mesa de operadores |
| Fecha, horario y métricas | Responsable de analítica AMT | Ingeniería de datos | Comité de métricas AMT |
| Identidad del usuario | Responsable de privacidad AMT | Custodio de identidades | Privacidad y operadores; no unir personas solo por similitud |
| Padrón CDC | Responsable de tarjetas de operadores | Ingeniería de datos | Dueño del padrón con validación de privacidad |
| Calidad y cuarentena | Dueño de la fuente que produjo el error | Ingeniería de datos | Dueño de fuente; comité de métricas si altera conteos oficiales |

Cambios: registrar motivo, versión, impacto en series históricas y aprobador por rol; validar calidad y doble corrida; publicar nuevas definiciones junto a los resultados. Las claves `row_number` pueden cambiar al incorporar datos: no usarlas como identificadores persistentes fuera de una reconstrucción.

## Prueba de fuego

Dos integrantes deben calcular el total con `SUM(cantidad_abordajes)` y, por separado, contar filas limpias del hecho, para idéntico período y filtros. Resultado de referencia para 1 junio-15 julio: 1,647,569. Deben coincidir; diferencias de ventana, fuente, identidad o doble conteo MR invalidan la comparación.
