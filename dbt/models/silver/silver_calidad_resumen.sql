-- Conteo de registros por regla de calidad y fuente (entregable 1.3).
with t as (
    select sistema, count(*) as total from {{ ref('silver_eventos_evaluados') }} group by 1
    union all select 'CDC', count(*) from {{ ref('cdc_operaciones') }}
),
q as (select sistema, motivo_rechazo, count(*) as registros from {{ ref('silver_cuarentena') }} group by 1, 2)
select q.sistema, q.motivo_rechazo, q.registros,
       round(100.0 * q.registros / t.total, 3) as pct_de_la_fuente, t.total as total_fuente
from q join t using (sistema)
order by q.sistema, q.registros desc
