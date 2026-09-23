-- 1.2 Padrón vigente de TRANSMETRO: las tarjetas TC- del padrón, con INSERT, UPDATE y DELETE ya aplicados
-- en orden de secuencia (ver cdc_operaciones y padron_vigente). DELETE = activa false; la tarjeta no se borra.
select * from {{ ref('padron_vigente') }} where operador_tarjeta = 'TM'
