-- Dimensión usuario SEUDONIMIZADA: no hay tarjeta ni llave original. Solo permite saber que es la misma persona.
with p as (
    select usuario_sk, persona_id, count(distinct sistema) as sistemas_con_tarjeta,
           string_agg(distinct sistema, ',' order by sistema) as sistemas,
           bool_or(sistema = 'AM') as tiene_aerometro
    from {{ ref('silver_identidad_usuario') }} group by 1, 2
),
padron as (
    select persona_id, activa, perfil, zona_residencia_key
    from {{ ref('padron_vigente') }}
    qualify row_number() over (partition by persona_id order by ultima_secuencia desc) = 1
)
select p.usuario_sk, p.sistemas_con_tarjeta, p.sistemas, p.sistemas_con_tarjeta > 1 as es_multisistema,
       pd.persona_id is not null as en_padron, pd.activa as padron_activo,
       pd.perfil, pd.zona_residencia_key,
       case when not p.tiene_aerometro then 'no_aplica'
            when p.persona_id like 'AM:%' then 'sin_vinculo' else 'vinculado' end as vinculo_aerometro
from p left join padron pd using (persona_id)
