{{ config(materialized='table', schema='features') }}

-- Una fila por usuario con al menos un abordaje en los 90 días previos al corte.
-- Corte exclusivo: NO se incorporan eventos del día de corte ni posteriores.
-- Ejecutar con --vars '{fecha_corte_features: "AAAA-MM-DD"}'.
-- Cada "viaje" en estas features significa abordaje; NO viaje puerta a puerta.
with parametros as (
    select cast('{{ var("fecha_corte_features", "2026-07-16") }}' as date) as fecha_corte
), cobertura as (
    select p.fecha_corte,
           greatest(0, least(90, date_diff('day', min(a.fecha), p.fecha_corte))) as dias_historial_disponible_90d
    from parametros p left join {{ ref('silver_abordajes') }} a on a.ts_local < p.fecha_corte
    group by p.fecha_corte
), historial as (
    select a.usuario_sk, a.abordaje_id, a.sistema, a.zona_key,
           a.ts_local, a.fecha, a.hora, a.monto_q, p.fecha_corte,
           (isodow(a.fecha) <= 5 and f.fecha is null
            and (a.hora between 6 and 8 or a.hora between 17 and 19)) as es_hora_pico
    from {{ ref('silver_abordajes') }} a
    cross join parametros p
    left join {{ ref('festivos_gt') }} f on f.fecha = a.fecha
    where a.ts_local >= p.fecha_corte - interval '90 days'
      and a.ts_local < p.fecha_corte
), agregado as (
    select usuario_sk, fecha_corte,
           count(*) filter (where ts_local >= fecha_corte - interval '7 days') as viajes_7d,
           count(*) filter (where ts_local >= fecha_corte - interval '30 days') as viajes_30d,
           count(*) as viajes_90d,
           count(distinct sistema) as modos_distintos_90d,
           date_diff('day', max(fecha), fecha_corte) as dias_desde_ultimo_viaje,
           count(*) filter (where es_hora_pico) * 1.0 / count(*) as proporcion_hora_pico_90d,
           sum(cast(monto_q as decimal(18,2))) as gasto_q_90d,
           sum(cast(monto_q as decimal(18,2))) / count(*) as gasto_promedio_q_90d
    from historial group by usuario_sk, fecha_corte
), modos as (
    select usuario_sk, sistema, count(*) as n
    from historial group by usuario_sk, sistema
    qualify row_number() over (partition by usuario_sk order by n desc, sistema) = 1
), zonas as (
    select usuario_sk, zona_key, count(*) as n
    from historial group by usuario_sk, zona_key
    qualify row_number() over (partition by usuario_sk order by n desc, zona_key) = 1
)
select a.*, c.dias_historial_disponible_90d,
       c.dias_historial_disponible_90d = 90 as ventana_90d_completa, m.sistema as modo_mas_usado_90d,
       z.zona_key as zona_origen_frecuente_90d
from agregado a
join cobertura c using (fecha_corte)
join modos m using (usuario_sk)
join zonas z using (usuario_sk)

