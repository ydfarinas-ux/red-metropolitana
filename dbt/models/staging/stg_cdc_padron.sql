-- Log de CDC tipado. Los DELETE llegan solo con la llave: sus atributos quedan NULL aquí.
-- OJO: la columna 'tarjeta' mezcla formatos de TM, TU y MR (y 'SIN-TARJETA'). Ver docs/1.2-staging-cdc.md
select
    try_cast(seq as bigint)                                     as secuencia,
    upper(trim(op))                                             as operacion,
    try_cast(commit_ts as timestamp)                            as ts_operacion,
    tarjeta,
    {{ operador_de_llave('tarjeta') }}                          as operador_tarjeta,
    {{ llave_numerica('tarjeta') }}                             as numero_persona,
    nullif(perfil, '')                                          as perfil,
    nullif(zona_residencia, '')                                 as zona_residencia_origen,
    nullif(estado, '')                                          as estado,
    _source_file, _ingested_at
from {{ source('bronze', 'cdc_padron_usuarios') }}
qualify row_number() over (partition by seq order by _ingested_at) = 1   -- el mismo evento no se aplica dos veces
