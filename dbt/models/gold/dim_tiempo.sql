-- Dimensión tiempo (grano hora): hora del día, día hábil y hora pico.
-- Hora pico (definición oficial): día hábil y 06:00-08:59 o 17:00-19:59.
select
    f.fecha_key * 100 + h.hora                        as tiempo_key,      -- yyyymmddhh
    f.fecha_key, f.fecha, h.hora,
    case when h.hora between 5 and 11 then 'mañana' when h.hora between 12 and 17 then 'tarde'
         when h.hora between 18 and 21 then 'noche' else 'madrugada' end as franja_horaria,
    f.es_dia_habil, f.es_fin_de_semana, f.es_festivo,
    f.es_dia_habil and (h.hora between 6 and 8 or h.hora between 17 and 19) as es_hora_pico
from {{ ref('dim_fecha') }} f
cross join (select range as hora from range(0, 24)) h
