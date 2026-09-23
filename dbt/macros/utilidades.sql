{# Conformación de zona. Cualquier forma de escribirla se lleva a una clave única:
   'Zona 10', 'Z10', 'ZONA 10', 'District 10' -> 'Z10'      'Mixco', 'MIXCO' -> 'MIXCO'
   Luego se compara contra seeds/territorios.csv. Si no hay coincidencia, el registro va a cuarentena. #}
{% macro normalizar_territorio(col) -%}
    case
        when {{ col }} is null or trim({{ col }}) = '' then null
        when regexp_matches(upper(trim({{ col }})), '^(ZONA|Z|DISTRICT|DISTRITO)\s*0*[0-9]+$')
            then 'Z' || cast(cast(regexp_extract(trim({{ col }}), '([0-9]+)$', 1) as integer) as varchar)
        else upper(strip_accents(trim(regexp_replace({{ col }}, '\s+', ' ', 'g'))))
    end
{%- endmacro %}

{# Deja solo los dígitos de una llave: 'TC-00012345', '0000012345', 'MR0012345' -> 12345 #}
{% macro llave_numerica(col) -%}
    try_cast(nullif(regexp_replace({{ col }}, '[^0-9]', '', 'g'), '') as bigint)
{%- endmacro %}

{# Operador al que pertenece una llave de tarjeta, por su formato #}
{% macro operador_de_llave(col) -%}
    case
        when {{ col }} is null or trim({{ col }}) = '' or upper({{ col }}) = 'SIN-TARJETA' then null
        when regexp_matches({{ col }}, '^TC-[0-9]+$') then 'TM'
        when regexp_matches({{ col }}, '^MR[0-9]+$')  then 'MR'
        when regexp_matches({{ col }}, '^[0-9]{10}$') then 'TU'
    end
{%- endmacro %}

{# Seudonimización: hash con sal secreta (variable de entorno PSEUDO_SALT, nunca en el repo) #}
{% macro seudonimo(col) -%}
    md5('{{ env_var("PSEUDO_SALT", "cambiar-en-.env") }}' || cast({{ col }} as varchar))
{%- endmacro %}
