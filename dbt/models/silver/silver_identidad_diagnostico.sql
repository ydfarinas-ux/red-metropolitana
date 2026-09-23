-- ¿Qué tan bien funcionó la vinculación? Por sistema: llaves, método de vínculo, personas que usan otro sistema.
with viajeros as (   -- personas que efectivamente viajaron (abordajes limpios)
    select distinct sistema, persona_id from {{ ref('silver_abordajes') }}
),
n_sistemas as (select persona_id, count(distinct sistema) as sistemas from viajeros group by 1)
select i.sistema,
       count(*)                                                        as llaves_distintas,
       count(*) filter (where metodo_vinculo = 'numero_normalizado')   as vinculadas_por_numero,
       count(*) filter (where metodo_vinculo = 'hash_md5_am')          as vinculadas_por_hash,
       count(*) filter (where metodo_vinculo = 'sin_vinculo')          as sin_vinculo,
       count(*) filter (where n.sistemas > 1)                          as viajeros_que_usan_otro_sistema
from {{ ref('silver_identidad_usuario') }} i
left join n_sistemas n using (persona_id)
group by 1 order by 1
