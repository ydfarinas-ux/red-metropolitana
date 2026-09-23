-- Todo lo que llegó a Bronze entra a Silver: staging no filtra nada.
with b as (
    select (select count(*) from {{ source('bronze','transmetro_validaciones') }})
         + (select count(*) from {{ source('bronze','transurbano_transacciones') }})
         + (select count(*) from {{ source('bronze','metroriel_viajes') }})
         + (select count(*) from {{ source('bronze','aerometro_boardings') }}) as n),
s as (select count(*) as n from {{ ref('silver_eventos_evaluados') }})
select b.n, s.n from b, s where b.n <> s.n
