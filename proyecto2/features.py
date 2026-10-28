"""1.3 Features desde Silver con ventanas anteriores al corte (hora local).

Uso: python proyecto2/features.py [--fecha-corte AAAA-MM-DD]
"""
import argparse
import csv
from datetime import date

import duckdb
import pandas as pd

if __package__:
    from .config import CORTES, VENTANA_DIAS, SALIDA, ruta_warehouse
    # poblacion mantiene los imports de script del proyecto original.
    import sys
    from pathlib import Path
    sys.path.insert(0, str(Path(__file__).resolve().parent))
    from .poblacion import sql_poblacion
else:
    from config import CORTES, VENTANA_DIAS, SALIDA, ruta_warehouse
    from poblacion import sql_poblacion


DICCIONARIO = [
    ('viajes_28d', 'Cantidad de abordajes válidos', '28 días', 'silver.silver_abordajes'),
    ('viajes_14d', 'Cantidad de abordajes válidos recientes', '14 días', 'silver.silver_abordajes'),
    ('viajes_7d', 'Cantidad de abordajes válidos de la última semana', '7 días', 'silver.silver_abordajes'),
    ('tendencia_14d', 'Viajes de los últimos 14 días menos los de los 14 anteriores', '28 días', 'silver.silver_abordajes'),
    ('dias_activos_28d', 'Días distintos con al menos un viaje', '28 días', 'silver.silver_abordajes'),
    ('semanas_activas_28d', 'Semanas de siete días hacia atrás con al menos un viaje', '28 días', 'silver.silver_abordajes'),
    ('dias_desde_ultimo_viaje', 'Días entre el último viaje de la ventana y el corte', '28 días', 'silver.silver_abordajes'),
    ('dias_desde_primer_viaje_28d', 'Días entre el primer viaje de la ventana y el corte', '28 días', 'silver.silver_abordajes'),
    ('modos_distintos_28d', 'Operadores distintos utilizados', '28 días', 'silver.silver_abordajes'),
    ('prop_transmetro', 'Proporción de viajes en Transmetro', '28 días', 'silver.silver_abordajes'),
    ('prop_transurbano', 'Proporción de viajes en Transurbano', '28 días', 'silver.silver_abordajes'),
    ('prop_metroriel', 'Proporción de viajes en MetroRiel', '28 días', 'silver.silver_abordajes'),
    ('prop_aerometro', 'Proporción de viajes en Aerómetro', '28 días', 'silver.silver_abordajes'),
    ('prop_hora_pico_28d', 'Proporción en días laborales no festivos de 6 a 8 o de 17 a 19 horas', '28 días', 'silver.silver_abordajes; silver.festivos_gt'),
    ('prop_fin_semana_28d', 'Proporción de viajes en sábado o domingo', '28 días', 'silver.silver_abordajes'),
    ('gasto_q_28d', 'Suma de tarifas en quetzales usando centavos enteros', '28 días', 'silver.silver_abordajes'),
    ('tarifa_promedio_q', 'Tarifa media en quetzales redondeada a cuatro decimales', '28 días', 'silver.silver_abordajes'),
    ('estaciones_distintas_28d', 'Estaciones o paradas distintas utilizadas', '28 días', 'silver.silver_abordajes'),
    ('zonas_distintas_28d', 'Zonas distintas de abordaje', '28 días', 'silver.silver_abordajes'),
    ('pagos_rechazados_28d', 'Intentos de pago rechazados por Transurbano', '28 días', 'silver.silver_transacciones_rechazadas_tu'),
    ('en_padron', 'Existe una versión del padrón vigente justo antes del corte', 'estado al corte', 'silver.silver_padron_scd2'),
    ('perfil', 'Perfil de la versión vigente más reciente o sin_padron', 'estado al corte', 'silver.silver_padron_scd2'),
    ('cambios_padron_28d', 'Actualizaciones aplicadas al padrón en la ventana', '28 días', 'silver.silver_padron_scd2'),
]
FEATURES = [fila[0] for fila in DICCIONARIO]


def sql_features(fecha_corte):
    """Una fila por unidad de sql_poblacion; la etiqueta nunca es una feature."""
    t = date.fromisoformat(fecha_corte)
    return f"""
with pob as ({sql_poblacion(fecha_corte)}),
par as (select timestamp '{t} 00:00:00' t, date '{t}' d),
ev as (
    select a.* from silver.silver_abordajes a cross join par
    where a.ts_local >= t - interval {VENTANA_DIAS} day and a.ts_local < t
),
viajes as (
    select usuario_sk,
        count(*) viajes_28d,
        count(*) filter (where ts_local >= t - interval 14 day) viajes_14d,
        count(*) filter (where ts_local >= t - interval 7 day) viajes_7d,
        viajes_14d - (viajes_28d - viajes_14d) tendencia_14d,
        count(distinct e.fecha) dias_activos_28d,
        count(distinct cast(floor((date_diff('day', e.fecha, d) - 1) / 7) as integer)) semanas_activas_28d,
        date_diff('day', max(e.fecha), any_value(d)) dias_desde_ultimo_viaje,
        date_diff('day', min(e.fecha), any_value(d)) dias_desde_primer_viaje_28d,
        count(distinct sistema) modos_distintos_28d,
        avg(case when sistema = 'TM' then 1.0 else 0 end) prop_transmetro,
        avg(case when sistema = 'TU' then 1.0 else 0 end) prop_transurbano,
        avg(case when sistema = 'MR' then 1.0 else 0 end) prop_metroriel,
        avg(case when sistema = 'AM' then 1.0 else 0 end) prop_aerometro,
        avg(case when isodow(e.fecha) <= 5 and f.fecha is null
            and (hora between 6 and 8 or hora between 17 and 19) then 1.0 else 0 end) prop_hora_pico_28d,
        avg(case when isodow(e.fecha) >= 6 then 1.0 else 0 end) prop_fin_semana_28d,
        sum(cast(round(monto_q * 100) as bigint)) / 100.0 gasto_q_28d,
        ((2 * sum(cast(round(monto_q * 100) as bigint)) * 100 + count(*)) // (2 * count(*))) / 10000.0 tarifa_promedio_q,
        count(distinct estacion_key) estaciones_distintas_28d,
        count(distinct zona_key) zonas_distintas_28d
    from ev e cross join par left join silver.festivos_gt f on f.fecha = e.fecha
    group by usuario_sk
),
rechazos as (
    select usuario_sk, count(*) pagos_rechazados_28d
    from silver.silver_transacciones_rechazadas_tu cross join par
    where ts_local >= t - interval {VENTANA_DIAS} day and ts_local < t group by usuario_sk
),
padron as (
    select usuario_sk, true en_padron, arg_max(perfil, valido_desde) perfil
    from silver.silver_padron_scd2 cross join par
    where valido_desde < t and valido_hasta >= t and usuario_sk is not null group by usuario_sk
),
cambios as (
    select usuario_sk, count(*) cambios_padron_28d
    from silver.silver_padron_scd2 cross join par
    where operacion_origen = 'UPDATE' and valido_desde >= t - interval {VENTANA_DIAS} day
        and valido_desde < t group by usuario_sk
)
select pob.unidad_id, pob.fecha_corte,
    {', '.join('v.' + nombre for nombre in FEATURES[:19])},
    coalesce(r.pagos_rechazados_28d, 0) pagos_rechazados_28d,
    coalesce(p.en_padron, false) en_padron, coalesce(p.perfil, 'sin_padron') perfil,
    coalesce(c.cambios_padron_28d, 0) cambios_padron_28d, pob.etiqueta
from pob join viajes v on pob.unidad_id = v.usuario_sk
left join rechazos r on pob.unidad_id = r.usuario_sk
left join padron p on pob.unidad_id = p.usuario_sk
left join cambios c on pob.unidad_id = c.usuario_sk
order by pob.unidad_id
"""


def calcular(con, fecha_corte):
    return con.execute(sql_features(fecha_corte)).df()


def main(cortes=None):
    SALIDA.mkdir(parents=True, exist_ok=True)
    tablas = []
    with duckdb.connect(ruta_warehouse()) as con:
        for nombre, fc in (cortes or CORTES).items():
            df = calcular(con, fc)
            df.insert(0, 'corte', nombre)
            tablas.append(df)
            print(f'  features corte {nombre}: {len(df):,} unidades')
        todo = pd.concat(tablas, ignore_index=True)
        con.register('features_df', todo)
        con.execute('create schema if not exists proyecto2')
        con.execute('create or replace table proyecto2.features_cortes as select * from features_df')
    todo.to_csv(SALIDA / 'features-cortes.csv', index=False)
    with (SALIDA / '1.3-diccionario.csv').open('w', newline='', encoding='utf-8') as f:
        w = csv.writer(f)
        w.writerow(['feature', 'que_mide', 'ventana', 'tabla_silver'])
        w.writerows(DICCIONARIO)


if __name__ == '__main__':
    p = argparse.ArgumentParser()
    p.add_argument('--fecha-corte')
    a = p.parse_args()
    main({'X': a.fecha_corte} if a.fecha_corte else None)
