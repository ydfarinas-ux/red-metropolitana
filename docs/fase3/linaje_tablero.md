# 3.1 Linaje del tablero

Origen de la evidencia: manifest generado por dbt. Los seeds territoriales, calendarios y de sistemas son fuentes maestras; no proceden de un archivo transaccional crudo.

## demanda.csv

Gold: fct_abordaje, dim_fecha, dim_sistema, dim_zona, dim_tiempo

Dependencias trazables:
- cdc_operaciones -> models\cdc\cdc_operaciones.sql
- dim_estacion -> models\gold\dim_estacion.sql
- dim_fecha -> models\gold\dim_fecha.sql
- dim_sistema -> models\gold\dim_sistema.sql
- dim_tiempo -> models\gold\dim_tiempo.sql
- dim_zona -> models\gold\dim_zona.sql
- fct_abordaje -> models\gold\fct_abordaje.sql
- padron_vigente -> models\cdc\padron_vigente.sql
- silver_abordajes -> models\silver\silver_abordajes.sql
- silver_estaciones -> models\silver\silver_estaciones.sql
- silver_eventos_evaluados -> models\silver\silver_eventos_evaluados.sql
- silver_identidad_usuario -> models\silver\silver_identidad_usuario.sql
- silver_zona -> models\silver\silver_zona.sql
- stg_am_boardings -> models\staging\stg_am_boardings.sql
- stg_am_estaciones -> models\staging\stg_am_estaciones.sql
- stg_cdc_padron -> models\staging\stg_cdc_padron.sql
- stg_mr_estaciones -> models\staging\stg_mr_estaciones.sql
- stg_mr_viajes -> models\staging\stg_mr_viajes.sql
- stg_tm_estaciones -> models\staging\stg_tm_estaciones.sql
- stg_tm_validaciones -> models\staging\stg_tm_validaciones.sql
- stg_tu_paradas -> models\staging\stg_tu_paradas.sql
- stg_tu_transacciones -> models\staging\stg_tu_transacciones.sql
- festivos_gt -> seeds\festivos_gt.csv
- sistemas -> seeds\sistemas.csv
- territorios -> seeds\territorios.csv
- aerometro_boardings -> models\sources.yml
- am_estaciones -> models\sources.yml
- cdc_padron_usuarios -> models\sources.yml
- metroriel_viajes -> models\sources.yml
- mr_estaciones -> models\sources.yml
- tm_estaciones -> models\sources.yml
- transmetro_validaciones -> models\sources.yml
- transurbano_transacciones -> models\sources.yml
- tu_paradas -> models\sources.yml

## cobertura.csv

Gold: dim_zona

Dependencias trazables:
- dim_zona -> models\gold\dim_zona.sql
- silver_estaciones -> models\silver\silver_estaciones.sql
- silver_zona -> models\silver\silver_zona.sql
- stg_am_estaciones -> models\staging\stg_am_estaciones.sql
- stg_mr_estaciones -> models\staging\stg_mr_estaciones.sql
- stg_tm_estaciones -> models\staging\stg_tm_estaciones.sql
- stg_tu_paradas -> models\staging\stg_tu_paradas.sql
- territorios -> seeds\territorios.csv
- am_estaciones -> models\sources.yml
- mr_estaciones -> models\sources.yml
- tm_estaciones -> models\sources.yml
- tu_paradas -> models\sources.yml

## multimodalidad.csv

Gold: fct_abordaje, dim_sistema

Dependencias trazables:
- cdc_operaciones -> models\cdc\cdc_operaciones.sql
- dim_estacion -> models\gold\dim_estacion.sql
- dim_sistema -> models\gold\dim_sistema.sql
- fct_abordaje -> models\gold\fct_abordaje.sql
- padron_vigente -> models\cdc\padron_vigente.sql
- silver_abordajes -> models\silver\silver_abordajes.sql
- silver_estaciones -> models\silver\silver_estaciones.sql
- silver_eventos_evaluados -> models\silver\silver_eventos_evaluados.sql
- silver_identidad_usuario -> models\silver\silver_identidad_usuario.sql
- stg_am_boardings -> models\staging\stg_am_boardings.sql
- stg_am_estaciones -> models\staging\stg_am_estaciones.sql
- stg_cdc_padron -> models\staging\stg_cdc_padron.sql
- stg_mr_estaciones -> models\staging\stg_mr_estaciones.sql
- stg_mr_viajes -> models\staging\stg_mr_viajes.sql
- stg_tm_estaciones -> models\staging\stg_tm_estaciones.sql
- stg_tm_validaciones -> models\staging\stg_tm_validaciones.sql
- stg_tu_paradas -> models\staging\stg_tu_paradas.sql
- stg_tu_transacciones -> models\staging\stg_tu_transacciones.sql
- sistemas -> seeds\sistemas.csv
- territorios -> seeds\territorios.csv
- aerometro_boardings -> models\sources.yml
- am_estaciones -> models\sources.yml
- cdc_padron_usuarios -> models\sources.yml
- metroriel_viajes -> models\sources.yml
- mr_estaciones -> models\sources.yml
- tm_estaciones -> models\sources.yml
- transmetro_validaciones -> models\sources.yml
- transurbano_transacciones -> models\sources.yml
- tu_paradas -> models\sources.yml

## metroriel.csv

Gold: dim_zona, fct_abordaje, dim_sistema

Dependencias trazables:
- cdc_operaciones -> models\cdc\cdc_operaciones.sql
- dim_estacion -> models\gold\dim_estacion.sql
- dim_sistema -> models\gold\dim_sistema.sql
- dim_zona -> models\gold\dim_zona.sql
- fct_abordaje -> models\gold\fct_abordaje.sql
- padron_vigente -> models\cdc\padron_vigente.sql
- silver_abordajes -> models\silver\silver_abordajes.sql
- silver_estaciones -> models\silver\silver_estaciones.sql
- silver_eventos_evaluados -> models\silver\silver_eventos_evaluados.sql
- silver_identidad_usuario -> models\silver\silver_identidad_usuario.sql
- silver_zona -> models\silver\silver_zona.sql
- stg_am_boardings -> models\staging\stg_am_boardings.sql
- stg_am_estaciones -> models\staging\stg_am_estaciones.sql
- stg_cdc_padron -> models\staging\stg_cdc_padron.sql
- stg_mr_estaciones -> models\staging\stg_mr_estaciones.sql
- stg_mr_viajes -> models\staging\stg_mr_viajes.sql
- stg_tm_estaciones -> models\staging\stg_tm_estaciones.sql
- stg_tm_validaciones -> models\staging\stg_tm_validaciones.sql
- stg_tu_paradas -> models\staging\stg_tu_paradas.sql
- stg_tu_transacciones -> models\staging\stg_tu_transacciones.sql
- sistemas -> seeds\sistemas.csv
- territorios -> seeds\territorios.csv
- aerometro_boardings -> models\sources.yml
- am_estaciones -> models\sources.yml
- cdc_padron_usuarios -> models\sources.yml
- metroriel_viajes -> models\sources.yml
- mr_estaciones -> models\sources.yml
- tm_estaciones -> models\sources.yml
- transmetro_validaciones -> models\sources.yml
- transurbano_transacciones -> models\sources.yml
- tu_paradas -> models\sources.yml

## Archivo crudo por fuente Bronze

| Fuente | Archivo |
|---|---|
| aerometro_boardings | datos_red/aerometro_boardings.csv |
| am_estaciones | datos_red/am_estaciones.csv |
| cdc_padron_usuarios | datos_red/cdc_padron_usuarios.csv |
| metroriel_viajes | datos_red/metroriel_viajes.jsonl |
| mr_estaciones | datos_red/mr_estaciones.csv |
| tm_estaciones | datos_red/tm_estaciones.csv |
| transmetro_validaciones | datos_red/transmetro_validaciones.csv |
| transurbano_transacciones | datos_red/transurbano_transacciones.csv |
| tu_paradas | datos_red/tu_paradas.csv |
