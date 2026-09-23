-- Dimensión fecha (grano día). Se genera; no viene de ninguna fuente.
with d as (select cast(range as date) as fecha from range(date '2026-01-01', date '2027-01-01', interval 1 day))
select
    cast(strftime(d.fecha, '%Y%m%d') as integer)  as fecha_key,
    d.fecha, year(d.fecha) as anio, month(d.fecha) as mes, day(d.fecha) as dia,
    isodow(d.fecha)                                as dia_semana_num,       -- 1 = lunes
    case isodow(d.fecha) when 1 then 'lunes' when 2 then 'martes' when 3 then 'miércoles' when 4 then 'jueves'
         when 5 then 'viernes' when 6 then 'sábado' else 'domingo' end as nombre_dia,
    isodow(d.fecha) >= 6                           as es_fin_de_semana,
    f.fecha is not null                            as es_festivo,
    f.nombre_festivo,
    isodow(d.fecha) <= 5 and f.fecha is null       as es_dia_habil
from d left join {{ ref('festivos_gt') }} f on f.fecha = d.fecha
