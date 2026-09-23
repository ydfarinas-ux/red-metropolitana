-- 1.2 Conteo antes / después de aplicar los borrados, separado por el operador dueño de cada tarjeta.
-- La fila TM es el padrón de Transmetro que pide el enunciado.
with antes as (   -- aplicando solo INSERT y UPDATE, como si los DELETE no hubieran llegado
    select operador_tarjeta, count(distinct tarjeta) as activas_antes
    from {{ ref('cdc_operaciones') }}
    where operador_tarjeta is not null and operacion in ('INSERT', 'UPDATE')
    group by 1
),
ops as (
    select operador_tarjeta,
           count(*) filter (where operacion = 'INSERT' and motivo_no_aplicada is null) as altas_aplicadas,
           count(*) filter (where operacion = 'UPDATE' and motivo_no_aplicada is null) as cambios_aplicados,
           count(*) filter (where operacion = 'DELETE' and motivo_no_aplicada is null) as bajas_aplicadas,
           count(*) filter (where motivo_no_aplicada is not null)                     as en_cuarentena
    from {{ ref('cdc_operaciones') }} where operador_tarjeta is not null group by 1
),
despues as (
    select operador_tarjeta, count(*) as tarjetas_en_padron,
           count(*) filter (where activa) as activas_despues,
           count(*) filter (where not activa) as dadas_de_baja
    from {{ ref('padron_vigente') }} group by 1
)
select d.operador_tarjeta, o.altas_aplicadas, o.cambios_aplicados, o.bajas_aplicadas, o.en_cuarentena,
       a.activas_antes as tarjetas_activas_antes_de_borrados,
       d.activas_despues as tarjetas_activas_despues, d.dadas_de_baja, d.tarjetas_en_padron
from despues d left join antes a using (operador_tarjeta) left join ops o using (operador_tarjeta)
order by case d.operador_tarjeta when 'TM' then 1 when 'TU' then 2 else 3 end
