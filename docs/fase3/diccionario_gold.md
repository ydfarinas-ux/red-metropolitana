# Diccionario Gold - 91 campos

Responsables académicos asignados por dominio y confirmados para la entrega. Cada campo conserva fuentes, expresión SQL y modelo.

## dim_estacion

Responsable: Yasmely Dubraska Fariñas Aldana (1329223)

| Campo | Tipo | Significado | Fuente | Transformación SQL |
|---|---|---|---|---|
| estacion_key | BIGINT | Clave técnica de estación; row_number ordenado por código conformado. | datos_red/am_estaciones.csv; datos_red/mr_estaciones.csv; datos_red/tm_estaciones.csv; datos_red/tu_paradas.csv; seeds\sistemas.csv; seeds\territorios.csv | ROW_NUMBER() OVER (ORDER BY e.estacion_key) AS estacion_key |
| estacion_codigo | VARCHAR | Clave conformada sistema:identificador de estación. | datos_red/am_estaciones.csv; datos_red/mr_estaciones.csv; datos_red/tm_estaciones.csv; datos_red/tu_paradas.csv; seeds\sistemas.csv; seeds\territorios.csv | e.estacion_key AS estacion_codigo |
| sistema_key | BIGINT | Clave técnica del operador; row_number ordenado por código de sistema. | datos_red/am_estaciones.csv; datos_red/mr_estaciones.csv; datos_red/tm_estaciones.csv; datos_red/tu_paradas.csv; seeds\sistemas.csv; seeds\territorios.csv | s.sistema_key |
| sistema_codigo | VARCHAR | Código de operador: TM, TU, MR o AM. | datos_red/am_estaciones.csv; datos_red/mr_estaciones.csv; datos_red/tm_estaciones.csv; datos_red/tu_paradas.csv; seeds\sistemas.csv; seeds\territorios.csv | e.sistema AS sistema_codigo |
| estacion_id_origen | VARCHAR | Identificador de estación o parada del catálogo del operador. | datos_red/am_estaciones.csv; datos_red/mr_estaciones.csv; datos_red/tm_estaciones.csv; datos_red/tu_paradas.csv; seeds\sistemas.csv; seeds\territorios.csv | e.estacion_id_origen |
| nombre_estacion | VARCHAR | Nombre de estación/parada del catálogo. | datos_red/am_estaciones.csv; datos_red/mr_estaciones.csv; datos_red/tm_estaciones.csv; datos_red/tu_paradas.csv; seeds\sistemas.csv; seeds\territorios.csv | e.nombre AS nombre_estacion |
| linea_ruta_eje | VARCHAR | Agrupador operativo: línea TM, ruta TU o eje AM; conservado del catálogo. | datos_red/am_estaciones.csv; datos_red/mr_estaciones.csv; datos_red/tm_estaciones.csv; datos_red/tu_paradas.csv; seeds\sistemas.csv; seeds\territorios.csv | e.agrupador AS linea_ruta_eje |
| orden_metroriel | INTEGER | Orden de estación en el trazado MR; nulo donde no aplica. | datos_red/am_estaciones.csv; datos_red/mr_estaciones.csv; datos_red/tm_estaciones.csv; datos_red/tu_paradas.csv; seeds\sistemas.csv; seeds\territorios.csv | e.orden AS orden_metroriel |
| lat | DOUBLE | Latitud del catálogo de estaciones, en grados. | datos_red/am_estaciones.csv; datos_red/mr_estaciones.csv; datos_red/tm_estaciones.csv; datos_red/tu_paradas.csv; seeds\sistemas.csv; seeds\territorios.csv | e.lat |
| lon | DOUBLE | Longitud del catálogo de estaciones, en grados. | datos_red/am_estaciones.csv; datos_red/mr_estaciones.csv; datos_red/tm_estaciones.csv; datos_red/tu_paradas.csv; seeds\sistemas.csv; seeds\territorios.csv | e.lon |
| zona_key | INTEGER | Clave territorial conformada, incluye zonas capitalinas y municipios; -1 significa desconocida en el snapshot del padrón. | datos_red/am_estaciones.csv; datos_red/mr_estaciones.csv; datos_red/tm_estaciones.csv; datos_red/tu_paradas.csv; seeds\sistemas.csv; seeds\territorios.csv | e.zona_key |

Modelo: dbt/models/gold/dim_estacion.sql

## dim_fecha

Responsable: Jose Rodrigo Herrera Muralles (1042619)

| Campo | Tipo | Significado | Fuente | Transformación SQL |
|---|---|---|---|---|
| fecha_key | INTEGER | Clave del día YYYYMMDD; se relaciona con dim_fecha. | Calendario generado en dim_fecha.sql (2026-01-01 a 2026-12-31) | CAST(STRFTIME(d.fecha, '%Y%m%d') AS INT) AS fecha_key |
| fecha | DATE | Día del calendario generado de 2026, en fecha local. | Calendario generado en dim_fecha.sql (2026-01-01 a 2026-12-31) | d.fecha |
| anio | BIGINT | Año de la fecha del calendario. | Calendario generado en dim_fecha.sql (2026-01-01 a 2026-12-31) | YEAR(d.fecha) AS anio |
| mes | BIGINT | Mes calendario numérico 1 a 12. | Calendario generado en dim_fecha.sql (2026-01-01 a 2026-12-31) | MONTH(d.fecha) AS mes |
| dia | BIGINT | Día del mes calendario. | Calendario generado en dim_fecha.sql (2026-01-01 a 2026-12-31) | DAY(d.fecha) AS dia |
| dia_semana_num | BIGINT | Día ISO de la semana: lunes=1 a domingo=7. | Calendario generado en dim_fecha.sql (2026-01-01 a 2026-12-31) | ISODOW(d.fecha) AS dia_semana_num /* 1 = lunes */ |
| nombre_dia | VARCHAR | Nombre en español del día de la semana. | Calendario generado en dim_fecha.sql (2026-01-01 a 2026-12-31) | CASE ISODOW(d.fecha) WHEN 1 THEN 'lunes' WHEN 2 THEN 'martes' WHEN 3 THEN 'miércoles' WHEN 4 THEN 'jueves' WHEN 5 THEN 'viernes' WHEN 6 THEN 'sábado' ELSE 'domingo' END AS nombre_dia |
| es_fin_de_semana | BOOLEAN | Verdadero sábado o domingo según el día ISO. | Calendario generado en dim_fecha.sql (2026-01-01 a 2026-12-31) | ISODOW(d.fecha) >= 6 AS es_fin_de_semana |
| es_festivo | BOOLEAN | La fecha coincide con el seed festivos_gt; cobertura limitada al calendario configurado. | Calendario generado y dbt/seeds/festivos_gt.csv | NOT f.fecha IS NULL AS es_festivo |
| nombre_festivo | VARCHAR | Nombre del feriado en festivos_gt; nulo cuando no coincide. | Calendario generado y dbt/seeds/festivos_gt.csv | f.nombre_festivo |
| es_dia_habil | BOOLEAN | Lunes a viernes, excluyendo festivos del seed. | Calendario generado y dbt/seeds/festivos_gt.csv | ISODOW(d.fecha) <= 5 AND f.fecha IS NULL AS es_dia_habil |

Modelo: dbt/models/gold/dim_fecha.sql

## dim_sistema

Responsable: Jose Rodrigo Herrera Muralles (1042619)

| Campo | Tipo | Significado | Fuente | Transformación SQL |
|---|---|---|---|---|
| sistema_key | BIGINT | Clave técnica del operador; row_number ordenado por código de sistema. | seeds\sistemas.csv | ROW_NUMBER() OVER (ORDER BY sistema_codigo) AS sistema_key |
| sistema_codigo | VARCHAR | Código de operador: TM, TU, MR o AM. | seeds\sistemas.csv | sistema_codigo |
| sistema_nombre | VARCHAR | Nombre legible del operador según sistemas.csv. | seeds\sistemas.csv | sistema_nombre |
| tipo_transporte | VARCHAR | Categoría de transporte indicada por el seed de sistemas. | seeds\sistemas.csv | tipo_transporte |
| unidad_registro | VARCHAR | Unidad de registro original del operador; no redefine el grano de fct_abordaje. | seeds\sistemas.csv | unidad_registro |

Modelo: dbt/models/gold/dim_sistema.sql

## dim_tiempo

Responsable: Jose Rodrigo Herrera Muralles (1042619)

| Campo | Tipo | Significado | Fuente | Transformación SQL |
|---|---|---|---|---|
| tiempo_key | BIGINT | Clave fecha-hora local YYYYMMDDHH; se relaciona con dim_tiempo. | dim_fecha (calendario generado y festivos_gt.csv) + horas generadas 0 a 23 | f.fecha_key * 100 + h.hora AS tiempo_key /* yyyymmddhh */ |
| fecha_key | INTEGER | Clave del día YYYYMMDD; se relaciona con dim_fecha. | dim_fecha (calendario generado y festivos_gt.csv) + horas generadas 0 a 23 | f.fecha_key |
| fecha | DATE | Día del calendario generado de 2026, en fecha local. | dim_fecha (calendario generado y festivos_gt.csv) + horas generadas 0 a 23 | f.fecha |
| hora | BIGINT | Hora local 0 a 23. | dim_fecha (calendario generado y festivos_gt.csv) + horas generadas 0 a 23 | h.hora |
| franja_horaria | VARCHAR | Mañana 05-11; tarde 12-17; noche 18-21; madrugada resto. | dim_fecha (calendario generado y festivos_gt.csv) + horas generadas 0 a 23 | CASE WHEN h.hora BETWEEN 5 AND 11 THEN 'mañana' WHEN h.hora BETWEEN 12 AND 17 THEN 'tarde' WHEN h.hora BETWEEN 18 AND 21 THEN 'noche' ELSE 'madrugada' END AS franja_horaria |
| es_dia_habil | BOOLEAN | Lunes a viernes, excluyendo festivos del seed. | dim_fecha (calendario generado y festivos_gt.csv) + horas generadas 0 a 23 | f.es_dia_habil |
| es_fin_de_semana | BOOLEAN | Verdadero sábado o domingo según el día ISO. | dim_fecha (calendario generado y festivos_gt.csv) + horas generadas 0 a 23 | f.es_fin_de_semana |
| es_festivo | BOOLEAN | La fecha coincide con el seed festivos_gt; cobertura limitada al calendario configurado. | dim_fecha (calendario generado y festivos_gt.csv) + horas generadas 0 a 23 | f.es_festivo |
| es_hora_pico | BOOLEAN | Día hábil y hora 06-08 o 17-19, incluyendo los minutos completos de cada hora. | dim_fecha (calendario generado y festivos_gt.csv) + horas generadas 0 a 23 | f.es_dia_habil AND (h.hora BETWEEN 6 AND 8 OR h.hora BETWEEN 17 AND 19) AS es_hora_pico |

Modelo: dbt/models/gold/dim_tiempo.sql

## dim_usuario

Responsable: Walter José Herrera Salvatierra (1109722)

| Campo | Tipo | Significado | Fuente | Transformación SQL |
|---|---|---|---|---|
| usuario_sk | VARCHAR | Seudónimo MD5 de sal concatenada con identidad resuelta; no es una identidad civil ni un dato anónimo. | datos_red/aerometro_boardings.csv; datos_red/am_estaciones.csv; datos_red/cdc_padron_usuarios.csv; datos_red/metroriel_viajes.jsonl; datos_red/mr_estaciones.csv; datos_red/tm_estaciones.csv; datos_red/transmetro_validaciones.csv; datos_red/transurbano_transacciones.csv; datos_red/tu_paradas.csv; seeds\territorios.csv | p.usuario_sk |
| sistemas_con_tarjeta | BIGINT | Número de sistemas presentes en el catálogo de identidad; no exige abordajes válidos en cada uno. | datos_red/aerometro_boardings.csv; datos_red/am_estaciones.csv; datos_red/cdc_padron_usuarios.csv; datos_red/metroriel_viajes.jsonl; datos_red/mr_estaciones.csv; datos_red/tm_estaciones.csv; datos_red/transmetro_validaciones.csv; datos_red/transurbano_transacciones.csv; datos_red/tu_paradas.csv; seeds\territorios.csv | p.sistemas_con_tarjeta |
| sistemas | VARCHAR | Lista de códigos distintos del catálogo de identidad, ordenados y separados por coma. | datos_red/aerometro_boardings.csv; datos_red/am_estaciones.csv; datos_red/cdc_padron_usuarios.csv; datos_red/metroriel_viajes.jsonl; datos_red/mr_estaciones.csv; datos_red/tm_estaciones.csv; datos_red/transmetro_validaciones.csv; datos_red/transurbano_transacciones.csv; datos_red/tu_paradas.csv; seeds\territorios.csv | p.sistemas |
| es_multisistema | BOOLEAN | Más de un sistema en el catálogo de identidad. No usar como sustituto de multimodalidad observada del tablero. | datos_red/aerometro_boardings.csv; datos_red/am_estaciones.csv; datos_red/cdc_padron_usuarios.csv; datos_red/metroriel_viajes.jsonl; datos_red/mr_estaciones.csv; datos_red/tm_estaciones.csv; datos_red/transmetro_validaciones.csv; datos_red/transurbano_transacciones.csv; datos_red/tu_paradas.csv; seeds\territorios.csv | p.sistemas_con_tarjeta > 1 AS es_multisistema |
| en_padron | BOOLEAN | La identidad resuelta aparece en el padrón vigente. | datos_red/aerometro_boardings.csv; datos_red/am_estaciones.csv; datos_red/cdc_padron_usuarios.csv; datos_red/metroriel_viajes.jsonl; datos_red/mr_estaciones.csv; datos_red/tm_estaciones.csv; datos_red/transmetro_validaciones.csv; datos_red/transurbano_transacciones.csv; datos_red/tu_paradas.csv; seeds\territorios.csv | NOT pd.persona_id IS NULL AS en_padron |
| padron_activo | BOOLEAN | Estado de la última tarjeta del padrón por secuencia para esa persona; nulo si no existe vínculo. | datos_red/aerometro_boardings.csv; datos_red/am_estaciones.csv; datos_red/cdc_padron_usuarios.csv; datos_red/metroriel_viajes.jsonl; datos_red/mr_estaciones.csv; datos_red/tm_estaciones.csv; datos_red/transmetro_validaciones.csv; datos_red/transurbano_transacciones.csv; datos_red/tu_paradas.csv; seeds\territorios.csv | pd.activa AS padron_activo |
| perfil | VARCHAR | Perfil del padrón; en snapshots nulos se agrupan como desconocido. | datos_red/aerometro_boardings.csv; datos_red/am_estaciones.csv; datos_red/cdc_padron_usuarios.csv; datos_red/metroriel_viajes.jsonl; datos_red/mr_estaciones.csv; datos_red/tm_estaciones.csv; datos_red/transmetro_validaciones.csv; datos_red/transurbano_transacciones.csv; datos_red/tu_paradas.csv; seeds\territorios.csv | pd.perfil |
| zona_residencia_key | INTEGER | Zona de residencia de la última versión del padrón; no es la zona de abordaje. | datos_red/aerometro_boardings.csv; datos_red/am_estaciones.csv; datos_red/cdc_padron_usuarios.csv; datos_red/metroriel_viajes.jsonl; datos_red/mr_estaciones.csv; datos_red/tm_estaciones.csv; datos_red/transmetro_validaciones.csv; datos_red/transurbano_transacciones.csv; datos_red/tu_paradas.csv; seeds\territorios.csv | pd.zona_residencia_key |
| vinculo_aerometro | VARCHAR | no_aplica sin AM; sin_vinculo para identidad separada de AM; vinculado si se activa el supuesto de vinculación. | datos_red/aerometro_boardings.csv; datos_red/am_estaciones.csv; datos_red/cdc_padron_usuarios.csv; datos_red/metroriel_viajes.jsonl; datos_red/mr_estaciones.csv; datos_red/tm_estaciones.csv; datos_red/transmetro_validaciones.csv; datos_red/transurbano_transacciones.csv; datos_red/tu_paradas.csv; seeds\territorios.csv | CASE WHEN NOT p.tiene_aerometro THEN 'no_aplica' WHEN p.persona_id LIKE 'AM:%' THEN 'sin_vinculo' ELSE 'vinculado' END AS vinculo_aerometro |

Modelo: dbt/models/gold/dim_usuario.sql

## dim_zona

Responsable: Yasmely Dubraska Fariñas Aldana (1329223)

| Campo | Tipo | Significado | Fuente | Transformación SQL |
|---|---|---|---|---|
| zona_key | INTEGER | Clave territorial conformada, incluye zonas capitalinas y municipios; -1 significa desconocida en el snapshot del padrón. | dbt/seeds/territorios.csv -> silver_zona | z.zona_key |
| nombre_zona | VARCHAR | Nombre oficial del territorio conforme al seed territorios.csv. | dbt/seeds/territorios.csv -> silver_zona | z.nombre_oficial AS nombre_zona |
| tipo_territorio | VARCHAR | Categoría zona o municipio según el catálogo territorial. | dbt/seeds/territorios.csv -> silver_zona | z.tipo_territorio |
| municipio | VARCHAR | Municipio al que pertenece el territorio del catálogo. | dbt/seeds/territorios.csv -> silver_zona | z.municipio |
| tiene_transmetro | BOOLEAN | Existe al menos una estación TM en el territorio. | datos_red/am_estaciones.csv; datos_red/mr_estaciones.csv; datos_red/tm_estaciones.csv; datos_red/tu_paradas.csv; seeds\territorios.csv | COALESCE(tiene_transmetro, FALSE) AS tiene_transmetro |
| tiene_transurbano | BOOLEAN | Existe al menos una parada TU en el territorio. | datos_red/am_estaciones.csv; datos_red/mr_estaciones.csv; datos_red/tm_estaciones.csv; datos_red/tu_paradas.csv; seeds\territorios.csv | COALESCE(tiene_transurbano, FALSE) AS tiene_transurbano |
| tiene_metroriel | BOOLEAN | Existe al menos una estación MR en el territorio. | datos_red/am_estaciones.csv; datos_red/mr_estaciones.csv; datos_red/tm_estaciones.csv; datos_red/tu_paradas.csv; seeds\territorios.csv | COALESCE(tiene_metroriel, FALSE) AS tiene_metroriel |
| tiene_aerometro | BOOLEAN | Existe al menos una estación AM en el territorio. | datos_red/am_estaciones.csv; datos_red/mr_estaciones.csv; datos_red/tm_estaciones.csv; datos_red/tu_paradas.csv; seeds\territorios.csv | COALESCE(tiene_aerometro, FALSE) AS tiene_aerometro |
| modos_con_estacion | BIGINT | Número de sistemas distintos con estaciones en el catálogo del territorio. | datos_red/am_estaciones.csv; datos_red/mr_estaciones.csv; datos_red/tm_estaciones.csv; datos_red/tu_paradas.csv; seeds\territorios.csv | COALESCE(modos_con_estacion, 0) AS modos_con_estacion |
| estaciones | BIGINT | Número de registros del catálogo de estaciones en el territorio. | datos_red/am_estaciones.csv; datos_red/mr_estaciones.csv; datos_red/tm_estaciones.csv; datos_red/tu_paradas.csv; seeds\territorios.csv | COALESCE(estaciones, 0) AS estaciones |
| tiene_servicio | BOOLEAN | modos_con_estacion mayor que cero; cobertura de catálogo, no acceso peatonal ni frecuencia. | datos_red/am_estaciones.csv; datos_red/mr_estaciones.csv; datos_red/tm_estaciones.csv; datos_red/tu_paradas.csv; seeds\territorios.csv | COALESCE(modos_con_estacion, 0) > 0 AS tiene_servicio |
| en_trazado_metroriel | BOOLEAN | Nombre oficial en Zona 12, Zona 8, Zona 1, Zona 6 o Zona 17. | dbt/seeds/territorios.csv -> silver_zona | z.nombre_oficial IN ('Zona 12', 'Zona 8', 'Zona 1', 'Zona 6', 'Zona 17') AS en_trazado_metroriel |

Modelo: dbt/models/gold/dim_zona.sql

## fct_abordaje

Responsable: Jose Rodrigo Herrera Muralles (1042619)

| Campo | Tipo | Significado | Fuente | Transformación SQL |
|---|---|---|---|---|
| abordaje_key | BIGINT | Clave técnica del abordaje; row_number determinístico para esta reconstrucción, no identificador persistente ante nuevos eventos. | datos_red/aerometro_boardings.csv; datos_red/am_estaciones.csv; datos_red/cdc_padron_usuarios.csv; datos_red/metroriel_viajes.jsonl; datos_red/mr_estaciones.csv; datos_red/tm_estaciones.csv; datos_red/transmetro_validaciones.csv; datos_red/transurbano_transacciones.csv; datos_red/tu_paradas.csv; seeds\sistemas.csv; seeds\territorios.csv | ROW_NUMBER() OVER (ORDER BY a.abordaje_id) AS abordaje_key |
| abordaje_id_origen | VARCHAR | Identificador unificado del evento de origen, incluye el operador. TU usa hash del contenido al no traer ID. | datos_red/aerometro_boardings.csv; datos_red/am_estaciones.csv; datos_red/cdc_padron_usuarios.csv; datos_red/metroriel_viajes.jsonl; datos_red/mr_estaciones.csv; datos_red/tm_estaciones.csv; datos_red/transmetro_validaciones.csv; datos_red/transurbano_transacciones.csv; datos_red/tu_paradas.csv; seeds\sistemas.csv; seeds\territorios.csv | a.abordaje_id AS abordaje_id_origen /* dimensión degenerada */ |
| tipo_validacion | VARCHAR | Detalle operativo: tipo TM, código de estado TU o cabina AM; puede ser nulo en MR. | datos_red/aerometro_boardings.csv; datos_red/am_estaciones.csv; datos_red/cdc_padron_usuarios.csv; datos_red/metroriel_viajes.jsonl; datos_red/mr_estaciones.csv; datos_red/tm_estaciones.csv; datos_red/transmetro_validaciones.csv; datos_red/transurbano_transacciones.csv; datos_red/tu_paradas.csv; seeds\sistemas.csv; seeds\territorios.csv | a.tipo_validacion /* degenerada: ENTRADA/TRANSBORDO (TM), cabina (AM), estado (TU) */ |
| tiempo_key | BIGINT | Clave fecha-hora local YYYYMMDDHH; se relaciona con dim_tiempo. | datos_red/aerometro_boardings.csv; datos_red/am_estaciones.csv; datos_red/cdc_padron_usuarios.csv; datos_red/metroriel_viajes.jsonl; datos_red/mr_estaciones.csv; datos_red/tm_estaciones.csv; datos_red/transmetro_validaciones.csv; datos_red/transurbano_transacciones.csv; datos_red/tu_paradas.csv; seeds\sistemas.csv; seeds\territorios.csv | CAST(STRFTIME(a.fecha, '%Y%m%d') AS INT) * 100 + a.hora AS tiempo_key |
| fecha_key | INTEGER | Clave del día YYYYMMDD; se relaciona con dim_fecha. | datos_red/aerometro_boardings.csv; datos_red/am_estaciones.csv; datos_red/cdc_padron_usuarios.csv; datos_red/metroriel_viajes.jsonl; datos_red/mr_estaciones.csv; datos_red/tm_estaciones.csv; datos_red/transmetro_validaciones.csv; datos_red/transurbano_transacciones.csv; datos_red/tu_paradas.csv; seeds\sistemas.csv; seeds\territorios.csv | CAST(STRFTIME(a.fecha, '%Y%m%d') AS INT) AS fecha_key |
| usuario_sk | VARCHAR | Seudónimo MD5 de sal concatenada con identidad resuelta; no es una identidad civil ni un dato anónimo. | datos_red/aerometro_boardings.csv; datos_red/am_estaciones.csv; datos_red/cdc_padron_usuarios.csv; datos_red/metroriel_viajes.jsonl; datos_red/mr_estaciones.csv; datos_red/tm_estaciones.csv; datos_red/transmetro_validaciones.csv; datos_red/transurbano_transacciones.csv; datos_red/tu_paradas.csv; seeds\sistemas.csv; seeds\territorios.csv | a.usuario_sk |
| sistema_key | BIGINT | Clave técnica del operador; row_number ordenado por código de sistema. | datos_red/aerometro_boardings.csv; datos_red/am_estaciones.csv; datos_red/cdc_padron_usuarios.csv; datos_red/metroriel_viajes.jsonl; datos_red/mr_estaciones.csv; datos_red/tm_estaciones.csv; datos_red/transmetro_validaciones.csv; datos_red/transurbano_transacciones.csv; datos_red/tu_paradas.csv; seeds\sistemas.csv; seeds\territorios.csv | s.sistema_key |
| estacion_key | BIGINT | Clave técnica de estación; row_number ordenado por código conformado. | datos_red/aerometro_boardings.csv; datos_red/am_estaciones.csv; datos_red/cdc_padron_usuarios.csv; datos_red/metroriel_viajes.jsonl; datos_red/mr_estaciones.csv; datos_red/tm_estaciones.csv; datos_red/transmetro_validaciones.csv; datos_red/transurbano_transacciones.csv; datos_red/tu_paradas.csv; seeds\sistemas.csv; seeds\territorios.csv | e.estacion_key |
| zona_key | INTEGER | Clave territorial conformada, incluye zonas capitalinas y municipios; -1 significa desconocida en el snapshot del padrón. | datos_red/aerometro_boardings.csv; datos_red/am_estaciones.csv; datos_red/cdc_padron_usuarios.csv; datos_red/metroriel_viajes.jsonl; datos_red/mr_estaciones.csv; datos_red/tm_estaciones.csv; datos_red/transmetro_validaciones.csv; datos_red/transurbano_transacciones.csv; datos_red/tu_paradas.csv; seeds\sistemas.csv; seeds\territorios.csv | a.zona_key |
| fecha_hora_local | TIMESTAMP | Instante del abordaje en America/Guatemala; MR utiliza la entrada. | datos_red/aerometro_boardings.csv; datos_red/am_estaciones.csv; datos_red/cdc_padron_usuarios.csv; datos_red/metroriel_viajes.jsonl; datos_red/mr_estaciones.csv; datos_red/tm_estaciones.csv; datos_red/transmetro_validaciones.csv; datos_red/transurbano_transacciones.csv; datos_red/tu_paradas.csv; seeds\sistemas.csv; seeds\territorios.csv | a.ts_local AS fecha_hora_local |
| cantidad_abordajes | INTEGER | Valor 1 por validación limpia de entrada. Suma aditiva; no representa un viaje puerta a puerta. | datos_red/aerometro_boardings.csv; datos_red/am_estaciones.csv; datos_red/cdc_padron_usuarios.csv; datos_red/metroriel_viajes.jsonl; datos_red/mr_estaciones.csv; datos_red/tm_estaciones.csv; datos_red/transmetro_validaciones.csv; datos_red/transurbano_transacciones.csv; datos_red/tu_paradas.csv; seeds\sistemas.csv; seeds\territorios.csv | 1 AS cantidad_abordajes /* aditiva */ |
| monto_q | DOUBLE | Importe en quetzales GTQ; TU se convierte de centavos a quetzales en staging. No sumar los mismos importes entre ambos hechos MR. | datos_red/aerometro_boardings.csv; datos_red/am_estaciones.csv; datos_red/cdc_padron_usuarios.csv; datos_red/metroriel_viajes.jsonl; datos_red/mr_estaciones.csv; datos_red/tm_estaciones.csv; datos_red/transmetro_validaciones.csv; datos_red/transurbano_transacciones.csv; datos_red/tu_paradas.csv; seeds\sistemas.csv; seeds\territorios.csv | a.monto_q /* aditiva */ |

Modelo: dbt/models/gold/fct_abordaje.sql

## fct_padron_diario

Responsable: Walter José Herrera Salvatierra (1109722)

| Campo | Tipo | Significado | Fuente | Transformación SQL |
|---|---|---|---|---|
| fecha_key | INTEGER | Clave del día YYYYMMDD; se relaciona con dim_fecha. | datos_red/aerometro_boardings.csv; datos_red/am_estaciones.csv; datos_red/cdc_padron_usuarios.csv; datos_red/metroriel_viajes.jsonl; datos_red/mr_estaciones.csv; datos_red/tm_estaciones.csv; datos_red/transmetro_validaciones.csv; datos_red/transurbano_transacciones.csv; datos_red/tu_paradas.csv; seeds\festivos_gt.csv; seeds\territorios.csv | d.fecha_key |
| zona_key | INTEGER | Clave territorial conformada, incluye zonas capitalinas y municipios; -1 significa desconocida en el snapshot del padrón. | datos_red/aerometro_boardings.csv; datos_red/am_estaciones.csv; datos_red/cdc_padron_usuarios.csv; datos_red/metroriel_viajes.jsonl; datos_red/mr_estaciones.csv; datos_red/tm_estaciones.csv; datos_red/transmetro_validaciones.csv; datos_red/transurbano_transacciones.csv; datos_red/tu_paradas.csv; seeds\festivos_gt.csv; seeds\territorios.csv | COALESCE(v.zona_residencia_key, -1) AS zona_key /* -1 = zona desconocida */ |
| perfil | VARCHAR | Perfil del padrón; en snapshots nulos se agrupan como desconocido. | datos_red/aerometro_boardings.csv; datos_red/am_estaciones.csv; datos_red/cdc_padron_usuarios.csv; datos_red/metroriel_viajes.jsonl; datos_red/mr_estaciones.csv; datos_red/tm_estaciones.csv; datos_red/transmetro_validaciones.csv; datos_red/transurbano_transacciones.csv; datos_red/tu_paradas.csv; seeds\festivos_gt.csv; seeds\territorios.csv | COALESCE(v.perfil, 'desconocido') AS perfil |
| operador_tarjeta | VARCHAR | Operador identificado por el formato de tarjeta en el padrón CDC. | datos_red/aerometro_boardings.csv; datos_red/am_estaciones.csv; datos_red/cdc_padron_usuarios.csv; datos_red/metroriel_viajes.jsonl; datos_red/mr_estaciones.csv; datos_red/tm_estaciones.csv; datos_red/transmetro_validaciones.csv; datos_red/transurbano_transacciones.csv; datos_red/tu_paradas.csv; seeds\festivos_gt.csv; seeds\territorios.csv | v.operador_tarjeta |
| tarjetas_activas | BIGINT | Tarjetas activas al cierre del día, por zona/perfil/operador. Semiaditiva: nunca sumar entre fechas. | datos_red/aerometro_boardings.csv; datos_red/am_estaciones.csv; datos_red/cdc_padron_usuarios.csv; datos_red/metroriel_viajes.jsonl; datos_red/mr_estaciones.csv; datos_red/tm_estaciones.csv; datos_red/transmetro_validaciones.csv; datos_red/transurbano_transacciones.csv; datos_red/tu_paradas.csv; seeds\festivos_gt.csv; seeds\territorios.csv | COUNT(*) FILTER(WHERE v.activa) AS tarjetas_activas /* semi-aditiva */ |
| altas_del_dia | BIGINT | Versiones INSERT que permanecen en el snapshot al cierre del día. No equivale necesariamente a todos los INSERT del log. | datos_red/aerometro_boardings.csv; datos_red/am_estaciones.csv; datos_red/cdc_padron_usuarios.csv; datos_red/metroriel_viajes.jsonl; datos_red/mr_estaciones.csv; datos_red/tm_estaciones.csv; datos_red/transmetro_validaciones.csv; datos_red/transurbano_transacciones.csv; datos_red/tu_paradas.csv; seeds\festivos_gt.csv; seeds\territorios.csv | COUNT(*) FILTER(WHERE v.operacion_origen = 'INSERT' AND CAST(v.valido_desde AS DATE) = d.fecha) AS altas_del_dia /* aditiva */ |
| bajas_del_dia | BIGINT | Versiones DELETE que permanecen en el snapshot al cierre del día. No equivale necesariamente a todos los DELETE del log. | datos_red/aerometro_boardings.csv; datos_red/am_estaciones.csv; datos_red/cdc_padron_usuarios.csv; datos_red/metroriel_viajes.jsonl; datos_red/mr_estaciones.csv; datos_red/tm_estaciones.csv; datos_red/transmetro_validaciones.csv; datos_red/transurbano_transacciones.csv; datos_red/tu_paradas.csv; seeds\festivos_gt.csv; seeds\territorios.csv | COUNT(*) FILTER(WHERE v.operacion_origen = 'DELETE' AND CAST(v.valido_desde AS DATE) = d.fecha) AS bajas_del_dia /* aditiva */ |

Modelo: dbt/models/gold/fct_padron_diario.sql

## fct_trayecto_metroriel

Responsable: Jose Rodrigo Herrera Muralles (1042619)

| Campo | Tipo | Significado | Fuente | Transformación SQL |
|---|---|---|---|---|
| trayecto_key | BIGINT | Clave técnica row_number por trayecto; puede cambiar al agregar nuevos eventos. | datos_red/aerometro_boardings.csv; datos_red/am_estaciones.csv; datos_red/cdc_padron_usuarios.csv; datos_red/metroriel_viajes.jsonl; datos_red/mr_estaciones.csv; datos_red/tm_estaciones.csv; datos_red/transmetro_validaciones.csv; datos_red/transurbano_transacciones.csv; datos_red/tu_paradas.csv; seeds\sistemas.csv; seeds\territorios.csv | ROW_NUMBER() OVER (ORDER BY t.trayecto_id) AS trayecto_key |
| trayecto_id_origen | VARCHAR | Identificador conformado del viaje completo MetroRiel. | datos_red/aerometro_boardings.csv; datos_red/am_estaciones.csv; datos_red/cdc_padron_usuarios.csv; datos_red/metroriel_viajes.jsonl; datos_red/mr_estaciones.csv; datos_red/tm_estaciones.csv; datos_red/transmetro_validaciones.csv; datos_red/transurbano_transacciones.csv; datos_red/tu_paradas.csv; seeds\sistemas.csv; seeds\territorios.csv | t.trayecto_id AS trayecto_id_origen |
| tiempo_key | BIGINT | Clave fecha-hora local YYYYMMDDHH; se relaciona con dim_tiempo. | datos_red/aerometro_boardings.csv; datos_red/am_estaciones.csv; datos_red/cdc_padron_usuarios.csv; datos_red/metroriel_viajes.jsonl; datos_red/mr_estaciones.csv; datos_red/tm_estaciones.csv; datos_red/transmetro_validaciones.csv; datos_red/transurbano_transacciones.csv; datos_red/tu_paradas.csv; seeds\sistemas.csv; seeds\territorios.csv | CAST(STRFTIME(t.ts_entrada_local, '%Y%m%d') AS INT) * 100 + HOUR(t.ts_entrada_local) AS tiempo_key |
| fecha_key | INTEGER | Clave del día YYYYMMDD; se relaciona con dim_fecha. | datos_red/aerometro_boardings.csv; datos_red/am_estaciones.csv; datos_red/cdc_padron_usuarios.csv; datos_red/metroriel_viajes.jsonl; datos_red/mr_estaciones.csv; datos_red/tm_estaciones.csv; datos_red/transmetro_validaciones.csv; datos_red/transurbano_transacciones.csv; datos_red/tu_paradas.csv; seeds\sistemas.csv; seeds\territorios.csv | CAST(STRFTIME(t.ts_entrada_local, '%Y%m%d') AS INT) AS fecha_key |
| usuario_sk | VARCHAR | Seudónimo MD5 de sal concatenada con identidad resuelta; no es una identidad civil ni un dato anónimo. | datos_red/aerometro_boardings.csv; datos_red/am_estaciones.csv; datos_red/cdc_padron_usuarios.csv; datos_red/metroriel_viajes.jsonl; datos_red/mr_estaciones.csv; datos_red/tm_estaciones.csv; datos_red/transmetro_validaciones.csv; datos_red/transurbano_transacciones.csv; datos_red/tu_paradas.csv; seeds\sistemas.csv; seeds\territorios.csv | t.usuario_sk |
| estacion_origen_key | BIGINT | Clave de dim_estacion con rol de entrada del trayecto MR. | datos_red/aerometro_boardings.csv; datos_red/am_estaciones.csv; datos_red/cdc_padron_usuarios.csv; datos_red/metroriel_viajes.jsonl; datos_red/mr_estaciones.csv; datos_red/tm_estaciones.csv; datos_red/transmetro_validaciones.csv; datos_red/transurbano_transacciones.csv; datos_red/tu_paradas.csv; seeds\sistemas.csv; seeds\territorios.csv | eo.estacion_key AS estacion_origen_key |
| estacion_destino_key | BIGINT | Clave de dim_estacion con rol de salida del trayecto MR. | datos_red/aerometro_boardings.csv; datos_red/am_estaciones.csv; datos_red/cdc_padron_usuarios.csv; datos_red/metroriel_viajes.jsonl; datos_red/mr_estaciones.csv; datos_red/tm_estaciones.csv; datos_red/transmetro_validaciones.csv; datos_red/transurbano_transacciones.csv; datos_red/tu_paradas.csv; seeds\sistemas.csv; seeds\territorios.csv | ed.estacion_key AS estacion_destino_key |
| zona_origen_key | INTEGER | Territorio conformado de la estación de entrada MR. | datos_red/aerometro_boardings.csv; datos_red/am_estaciones.csv; datos_red/cdc_padron_usuarios.csv; datos_red/metroriel_viajes.jsonl; datos_red/mr_estaciones.csv; datos_red/tm_estaciones.csv; datos_red/transmetro_validaciones.csv; datos_red/transurbano_transacciones.csv; datos_red/tu_paradas.csv; seeds\sistemas.csv; seeds\territorios.csv | t.zona_origen_key /* dim_zona con dos roles */ |
| zona_destino_key | INTEGER | Territorio conformado de la estación de salida MR. | datos_red/aerometro_boardings.csv; datos_red/am_estaciones.csv; datos_red/cdc_padron_usuarios.csv; datos_red/metroriel_viajes.jsonl; datos_red/mr_estaciones.csv; datos_red/tm_estaciones.csv; datos_red/transmetro_validaciones.csv; datos_red/transurbano_transacciones.csv; datos_red/tu_paradas.csv; seeds\sistemas.csv; seeds\territorios.csv | t.zona_destino_key |
| ts_entrada_local | TIMESTAMP | Instante local de entrada del trayecto MR. | datos_red/aerometro_boardings.csv; datos_red/am_estaciones.csv; datos_red/cdc_padron_usuarios.csv; datos_red/metroriel_viajes.jsonl; datos_red/mr_estaciones.csv; datos_red/tm_estaciones.csv; datos_red/transmetro_validaciones.csv; datos_red/transurbano_transacciones.csv; datos_red/tu_paradas.csv; seeds\sistemas.csv; seeds\territorios.csv | t.ts_entrada_local |
| ts_salida_local | TIMESTAMP | Instante local de salida del trayecto MR. | datos_red/aerometro_boardings.csv; datos_red/am_estaciones.csv; datos_red/cdc_padron_usuarios.csv; datos_red/metroriel_viajes.jsonl; datos_red/mr_estaciones.csv; datos_red/tm_estaciones.csv; datos_red/transmetro_validaciones.csv; datos_red/transurbano_transacciones.csv; datos_red/tu_paradas.csv; seeds\sistemas.csv; seeds\territorios.csv | t.ts_salida_local |
| cantidad_trayectos | INTEGER | Valor 1 por trayecto completo MR válido; sumar solo dentro de este hecho. | datos_red/aerometro_boardings.csv; datos_red/am_estaciones.csv; datos_red/cdc_padron_usuarios.csv; datos_red/metroriel_viajes.jsonl; datos_red/mr_estaciones.csv; datos_red/tm_estaciones.csv; datos_red/transmetro_validaciones.csv; datos_red/transurbano_transacciones.csv; datos_red/tu_paradas.csv; seeds\sistemas.csv; seeds\territorios.csv | 1 AS cantidad_trayectos /* aditiva */ |
| duracion_min | DOUBLE | Duración del trayecto en minutos según Silver; promedio requiere SUM(duracion_min)/SUM(cantidad_trayectos). | datos_red/aerometro_boardings.csv; datos_red/am_estaciones.csv; datos_red/cdc_padron_usuarios.csv; datos_red/metroriel_viajes.jsonl; datos_red/mr_estaciones.csv; datos_red/tm_estaciones.csv; datos_red/transmetro_validaciones.csv; datos_red/transurbano_transacciones.csv; datos_red/tu_paradas.csv; seeds\sistemas.csv; seeds\territorios.csv | t.duracion_min /* aditiva (el promedio NO lo es) */ |
| estaciones_recorridas | INTEGER | Diferencia absoluta de orden entre estaciones MR en Silver; mide separación por tramos, no cuenta ambas estaciones extremas. | datos_red/aerometro_boardings.csv; datos_red/am_estaciones.csv; datos_red/cdc_padron_usuarios.csv; datos_red/metroriel_viajes.jsonl; datos_red/mr_estaciones.csv; datos_red/tm_estaciones.csv; datos_red/transmetro_validaciones.csv; datos_red/transurbano_transacciones.csv; datos_red/tu_paradas.csv; seeds\sistemas.csv; seeds\territorios.csv | t.estaciones_recorridas /* aditiva */ |
| monto_q | DOUBLE | Importe en quetzales GTQ; TU se convierte de centavos a quetzales en staging. No sumar los mismos importes entre ambos hechos MR. | datos_red/aerometro_boardings.csv; datos_red/am_estaciones.csv; datos_red/cdc_padron_usuarios.csv; datos_red/metroriel_viajes.jsonl; datos_red/mr_estaciones.csv; datos_red/tm_estaciones.csv; datos_red/transmetro_validaciones.csv; datos_red/transurbano_transacciones.csv; datos_red/tu_paradas.csv; seeds\sistemas.csv; seeds\territorios.csv | t.monto_q /* aditiva */ |

Modelo: dbt/models/gold/fct_trayecto_metroriel.sql
