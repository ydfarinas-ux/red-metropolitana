-- Recalcular desde Silver sin Gold, y contrastar población, ventanas e importes.
with esperado as (
 select usuario_sk, count(*) as n90,
 count(*) filter (where ts_local >= cast('{{ var("fecha_corte_features", "2026-07-16") }}' as date) - interval '30 days') as n30,
 count(*) filter (where ts_local >= cast('{{ var("fecha_corte_features", "2026-07-16") }}' as date) - interval '7 days') as n7,
 sum(monto_q) as gasto
 from {{ ref('silver_abordajes') }}
 where ts_local >= cast('{{ var("fecha_corte_features", "2026-07-16") }}' as date) - interval '90 days'
 and ts_local < cast('{{ var("fecha_corte_features", "2026-07-16") }}' as date)
 group by usuario_sk
)
select coalesce(e.usuario_sk,f.usuario_sk) as usuario_sk
from esperado e full join {{ ref('features_usuario') }} f using (usuario_sk)
where e.usuario_sk is null or f.usuario_sk is null
 or e.n90 != f.viajes_90d or e.n30 != f.viajes_30d or e.n7 != f.viajes_7d
 or abs(e.gasto-f.gasto_q_90d) > 0.000001
