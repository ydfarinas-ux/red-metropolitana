-- Conservación: todo evento termina en cuarentena, en abordajes o en transacciones rechazadas de TU. Si falta uno, falla.
with e as (select count(*) n from {{ ref('silver_eventos_evaluados') }}),
     s as (select (select count(*) from {{ ref('silver_cuarentena') }} where sistema <> 'CDC')
                + (select count(*) from {{ ref('silver_abordajes') }})
                + (select count(*) from {{ ref('silver_transacciones_rechazadas_tu') }}) as n)
select e.n as evaluados, s.n as clasificados from e, s where e.n <> s.n
