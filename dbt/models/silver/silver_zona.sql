-- Dimensión zona conformada: una sola lista de territorios (zonas de la ciudad y municipios) para los cuatro sistemas.
select zona_key, nombre_oficial, tipo_territorio, municipio from {{ ref('territorios') }}
