-- DDL de la capa Gold (DuckDB / PostgreSQL compatible salvo tipos menores).
-- Generado desde el warehouse con herramientas/ddl.py. dbt construye estas tablas;
-- este archivo documenta su estructura, llaves primarias y foráneas.

CREATE SCHEMA IF NOT EXISTS gold;

CREATE TABLE gold.dim_fecha (
    fecha_key                INTEGER NOT NULL,
    fecha                    DATE,
    anio                     BIGINT,
    mes                      BIGINT,
    dia                      BIGINT,
    dia_semana_num           BIGINT,
    nombre_dia               VARCHAR,
    es_fin_de_semana         BOOLEAN,
    es_festivo               BOOLEAN,
    nombre_festivo           VARCHAR,
    es_dia_habil             BOOLEAN,
    PRIMARY KEY (fecha_key)
);

CREATE TABLE gold.dim_tiempo (
    tiempo_key               BIGINT NOT NULL,
    fecha_key                INTEGER,
    fecha                    DATE,
    hora                     BIGINT,
    franja_horaria           VARCHAR,
    es_dia_habil             BOOLEAN,
    es_fin_de_semana         BOOLEAN,
    es_festivo               BOOLEAN,
    es_hora_pico             BOOLEAN,
    PRIMARY KEY (tiempo_key),
    FOREIGN KEY (fecha_key) REFERENCES gold.dim_fecha (fecha_key)
);

CREATE TABLE gold.dim_sistema (
    sistema_key              BIGINT NOT NULL,
    sistema_codigo           VARCHAR,
    sistema_nombre           VARCHAR,
    tipo_transporte          VARCHAR,
    unidad_registro          VARCHAR,
    PRIMARY KEY (sistema_key)
);

CREATE TABLE gold.dim_zona (
    zona_key                 INTEGER NOT NULL,
    nombre_zona              VARCHAR,
    tipo_territorio          VARCHAR,
    municipio                VARCHAR,
    tiene_transmetro         BOOLEAN,
    tiene_transurbano        BOOLEAN,
    tiene_metroriel          BOOLEAN,
    tiene_aerometro          BOOLEAN,
    modos_con_estacion       BIGINT,
    estaciones               BIGINT,
    tiene_servicio           BOOLEAN,
    en_trazado_metroriel     BOOLEAN,
    PRIMARY KEY (zona_key)
);

CREATE TABLE gold.dim_estacion (
    estacion_key             BIGINT NOT NULL,
    estacion_codigo          VARCHAR,
    sistema_key              BIGINT,
    sistema_codigo           VARCHAR,
    estacion_id_origen       VARCHAR,
    nombre_estacion          VARCHAR,
    linea_ruta_eje           VARCHAR,
    orden_metroriel          INTEGER,
    lat                      DOUBLE,
    lon                      DOUBLE,
    zona_key                 INTEGER,
    PRIMARY KEY (estacion_key),
    FOREIGN KEY (sistema_key) REFERENCES gold.dim_sistema (sistema_key),
    FOREIGN KEY (zona_key) REFERENCES gold.dim_zona (zona_key)
);

CREATE TABLE gold.dim_usuario (
    usuario_sk               VARCHAR NOT NULL,
    sistemas_con_tarjeta     BIGINT,
    sistemas                 VARCHAR,
    es_multisistema          BOOLEAN,
    en_padron                BOOLEAN,
    padron_activo            BOOLEAN,
    perfil                   VARCHAR,
    zona_residencia_key      INTEGER,
    vinculo_aerometro        VARCHAR,
    PRIMARY KEY (usuario_sk)
);

CREATE TABLE gold.fct_abordaje (
    abordaje_key             BIGINT NOT NULL,
    abordaje_id_origen       VARCHAR,
    tipo_validacion          VARCHAR,
    tiempo_key               BIGINT,
    fecha_key                INTEGER,
    usuario_sk               VARCHAR,
    sistema_key              BIGINT,
    estacion_key             BIGINT,
    zona_key                 INTEGER,
    fecha_hora_local         TIMESTAMP,
    cantidad_abordajes       INTEGER,
    monto_q                  DOUBLE,
    PRIMARY KEY (abordaje_key),
    FOREIGN KEY (tiempo_key) REFERENCES gold.dim_tiempo (tiempo_key),
    FOREIGN KEY (fecha_key) REFERENCES gold.dim_fecha (fecha_key),
    FOREIGN KEY (usuario_sk) REFERENCES gold.dim_usuario (usuario_sk),
    FOREIGN KEY (sistema_key) REFERENCES gold.dim_sistema (sistema_key),
    FOREIGN KEY (estacion_key) REFERENCES gold.dim_estacion (estacion_key),
    FOREIGN KEY (zona_key) REFERENCES gold.dim_zona (zona_key)
);

CREATE TABLE gold.fct_trayecto_metroriel (
    trayecto_key             BIGINT NOT NULL,
    trayecto_id_origen       VARCHAR,
    tiempo_key               BIGINT,
    fecha_key                INTEGER,
    usuario_sk               VARCHAR,
    estacion_origen_key      BIGINT,
    estacion_destino_key     BIGINT,
    zona_origen_key          INTEGER,
    zona_destino_key         INTEGER,
    ts_entrada_local         TIMESTAMP,
    ts_salida_local          TIMESTAMP,
    cantidad_trayectos       INTEGER,
    duracion_min             DOUBLE,
    estaciones_recorridas    INTEGER,
    monto_q                  DOUBLE,
    PRIMARY KEY (trayecto_key),
    FOREIGN KEY (tiempo_key) REFERENCES gold.dim_tiempo (tiempo_key),
    FOREIGN KEY (fecha_key) REFERENCES gold.dim_fecha (fecha_key),
    FOREIGN KEY (usuario_sk) REFERENCES gold.dim_usuario (usuario_sk),
    FOREIGN KEY (estacion_origen_key) REFERENCES gold.dim_estacion (estacion_key),
    FOREIGN KEY (estacion_destino_key) REFERENCES gold.dim_estacion (estacion_key),
    FOREIGN KEY (zona_origen_key) REFERENCES gold.dim_zona (zona_key),
    FOREIGN KEY (zona_destino_key) REFERENCES gold.dim_zona (zona_key)
);

CREATE TABLE gold.fct_padron_diario (
    fecha_key                INTEGER NOT NULL,
    zona_key                 INTEGER NOT NULL,
    perfil                   VARCHAR NOT NULL,
    operador_tarjeta         VARCHAR NOT NULL,
    tarjetas_activas         BIGINT,
    altas_del_dia            BIGINT,
    bajas_del_dia            BIGINT,
    PRIMARY KEY (fecha_key, zona_key, perfil, operador_tarjeta),
    FOREIGN KEY (fecha_key) REFERENCES gold.dim_fecha (fecha_key)
);
