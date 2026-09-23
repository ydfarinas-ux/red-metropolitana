-- 1.2 Conteo antes / después de aplicar los borrados (entregable).
with ops as (select * from {{ ref('cdc_operaciones') }}),
ok as (select * from ops where motivo_no_aplicada is null),
pv as (select * from {{ ref('padron_vigente') }})
select
    (select count(*) from ops)                                                       as eventos_en_log,
    (select count(*) from ops where motivo_no_aplicada is not null)                  as eventos_en_cuarentena,
    (select count(*) from ok)                                                        as eventos_aplicados,
    (select count(*) from ok where operacion = 'INSERT')                             as altas_aplicadas,
    (select count(*) from ok where operacion = 'UPDATE')                             as cambios_aplicados,
    (select count(*) from ok where operacion = 'DELETE')                             as bajas_aplicadas,
    -- ANTES: el padrón aplicando solo INSERT y UPDATE, como si los DELETE no hubieran llegado
    (select count(distinct tarjeta) from ops where operador_tarjeta is not null and operacion in ('INSERT', 'UPDATE')) as tarjetas_activas_antes_de_borrados,
    (select count(*) from pv where activa)                                           as tarjetas_activas_despues,
    (select count(*) from pv where not activa)                                       as tarjetas_dadas_de_baja,
    (select count(*) from pv)                                                        as tarjetas_en_padron,
    (select count(*) from ok where observacion = 'reactivacion')                     as reactivaciones,
    (select count(*) from ok where observacion = 'tarjeta_previa_al_log')            as updates_de_tarjetas_previas_al_log,
    (select count(*) from ok where observacion = 'baja_de_tarjeta_previa_al_log')    as bajas_de_tarjetas_previas_al_log
