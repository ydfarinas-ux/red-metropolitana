-- Resolución de identidad entre los cuatro sistemas (estrategia, supuestos y límites en docs/1.3-silver.md).
--  1) TM 'TC-00012345', TU '0000012345' y MR 'MR0012345' -> parte numérica (12345) -> persona P12345.
--     Supuesto: los tres operadores comparten la numeración de la persona. Se valida el formato de cada llave.
--  2) AM trae un hash de 12 caracteres que no contiene el número. Por defecto NO se vincula.
--     Con var('vincular_aerometro') = true se prueba la regla md5('am' || numero)[:12] (análisis de sensibilidad).
--  3) Lo que no se puede vincular queda como persona propia de su sistema: no se inventa el vínculo.
with llaves as (
    select distinct sistema, usuario_llave_origen as llave_origen
    from {{ ref('silver_eventos_evaluados') }}
    where usuario_llave_origen is not null and trim(usuario_llave_origen) <> ''
    union
    select operador_tarjeta, tarjeta from {{ ref('padron_vigente') }}
),
numericas as (
    select sistema, llave_origen,
        case when {{ operador_de_llave('llave_origen') }} = sistema then {{ llave_numerica('llave_origen') }} end as numero
    from llaves where sistema in ('TM', 'TU', 'MR')
),
aerometro as (
    select l.sistema, l.llave_origen,
    {% if var('vincular_aerometro') %}
        c.numero
    from llaves l
    left join (select distinct numero, left(md5('am' || cast(numero as varchar)), 12) as hash12
               from numericas where numero is not null) c on c.hash12 = lower(l.llave_origen)
    {% else %}
        null::bigint as numero
    from llaves l
    {% endif %}
    where l.sistema = 'AM'
),
unido as (
    select sistema, llave_origen, numero,
           case when numero is not null then 'numero_normalizado' else 'sin_vinculo' end as metodo_vinculo
    from numericas
    union all
    select sistema, llave_origen, numero,
           case when numero is not null then 'hash_md5_am' else 'sin_vinculo' end
    from aerometro
)
select
    sistema, llave_origen, metodo_vinculo,
    case when numero is not null then 'P' || cast(numero as varchar) else sistema || ':' || llave_origen end as persona_id,
    {{ seudonimo("case when numero is not null then 'P' || cast(numero as varchar) else sistema || ':' || llave_origen end") }} as usuario_sk
from unido
