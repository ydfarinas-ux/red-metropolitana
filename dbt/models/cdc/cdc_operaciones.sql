-- 1.2 Cada operación del log de CDC con la decisión que se tomó sobre ella (aplicada o no, y por qué).
-- Reglas (en ORDEN DE SECUENCIA, por tarjeta):
--   INSERT  -> la tarjeta queda activa (si ya existía activa, actualiza atributos; si estaba de baja, se REACTIVA).
--   UPDATE  -> cambia atributos. Si es la primera operación de la tarjeta, la tarjeta ya existía antes de que
--              empezara el log (1-jun-2026): se aplica como alta implícita. Si la tarjeta está de baja,
--              NO se aplica (no se modifica una fila borrada) y va a cuarentena.
--   DELETE  -> baja LÓGICA: activa = false. Nunca se borra la fila. Si la tarjeta no se conocía, queda registrada de baja.
--   Sin llave de tarjeta ('SIN-TARJETA') o formato irreconocible -> cuarentena (no se puede saber de quién es).
with log as (select *, row_number() over (partition by tarjeta order by secuencia) as n_op
             from {{ ref('stg_cdc_padron') }}),
estado as (
    select *,
        -- estado activo/inactivo de la tarjeta DESPUÉS de esta operación (el UPDATE no lo cambia)
        last_value(case when operacion = 'INSERT' then true
                        when operacion = 'DELETE' then false
                        when operacion = 'UPDATE' and n_op = 1 then true end ignore nulls)
            over (partition by tarjeta order by secuencia rows between unbounded preceding and current row) as activa_tras,
        lag(operacion) over (partition by tarjeta order by secuencia) as operacion_previa
    from log
),
con_previo as (
    select *, lag(activa_tras) over (partition by tarjeta order by secuencia) as activa_antes from estado
)
select
    secuencia, ts_operacion, operacion, tarjeta, operador_tarjeta, numero_persona,
    perfil, zona_residencia_origen, estado, n_op, activa_antes, activa_tras,
    case
        when operador_tarjeta is null                       then 'CDC_SIN_TARJETA'
        when secuencia is null or ts_operacion is null      then 'CDC_REGISTRO_INVALIDO'
        when operacion not in ('INSERT', 'UPDATE', 'DELETE') then 'CDC_OPERACION_INVALIDA'
        when operacion = 'UPDATE' and activa_antes = false  then 'CDC_UPDATE_SOBRE_BAJA'
    end as motivo_no_aplicada,
    case
        when operacion = 'INSERT' and activa_antes = false  then 'reactivacion'
        when operacion = 'INSERT' and activa_antes = true   then 'insert_repetido'
        when operacion = 'UPDATE' and n_op = 1              then 'tarjeta_previa_al_log'
        when operacion = 'DELETE' and n_op = 1              then 'baja_de_tarjeta_previa_al_log'
        when operacion = 'DELETE' and activa_antes = false  then 'baja_repetida'
    end as observacion,
    _source_file, _ingested_at
from con_previo
