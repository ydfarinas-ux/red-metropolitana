"""
1.2 Población, etiqueta y costo de la unidad, desde Silver.

Unidad: la persona (usuario_sk), con la estrategia de identidad del Proyecto 1.
Población: al menos 2 abordajes válidos en [t - 28 días, t) y ningún DELETE del CDC aplicado antes de t.
Etiqueta: 1 si no hay ningún abordaje válido, en ningún operador, en [t, t + 30 días); 0 si hay al menos uno.
Solo se usan registros válidos: silver_abordajes ya no tiene lo que está en cuarentena.

Uso:
    python proyecto2/poblacion.py                         # los tres cortes A, B y C
    python proyecto2/poblacion.py --fecha-corte 2026-07-01
"""
import argparse, csv, json
from datetime import date
import duckdb
from config import CORTES, VENTANA_DIAS, HORIZONTE_DIAS, MIN_ABORDAJES, SALIDA, ruta_warehouse


def sql_poblacion(fecha_corte):
    """Una fila por unidad de la población del corte: unidad_id, persona_id, fecha_corte y etiqueta
    (vacía si los datos no cubren los 30 días después del corte)."""
    t = date.fromisoformat(fecha_corte)          # valida la fecha antes de ponerla en el SQL
    return f"""
with par as (select timestamp '{t} 00:00:00' as t, date '{t}' as d),
ventana as (  -- abordajes válidos en [t - 28 días, t)
    select a.usuario_sk, any_value(a.persona_id) as persona_id, count(*) as viajes
    from silver.silver_abordajes a cross join par
    where a.ts_local >= par.t - interval {VENTANA_DIAS} day and a.ts_local < par.t
    group by a.usuario_sk
),
bajas as (    -- personas con un DELETE del CDC aplicado antes del corte
    select distinct 'P' || cast(o.numero_persona as varchar) as persona_id
    from silver.cdc_operaciones o cross join par
    where o.operacion = 'DELETE' and o.motivo_no_aplicada is null and o.ts_operacion < par.t
),
futuro as (   -- abordajes válidos en [t, t + 30 días), en cualquier operador
    select distinct a.usuario_sk
    from silver.silver_abordajes a cross join par
    where a.ts_local >= par.t and a.ts_local < par.t + interval {HORIZONTE_DIAS} day
),
hay_horizonte as (  -- la etiqueta solo existe si los datos cubren los 30 días completos
    select max(fecha) >= (select d from par) + {HORIZONTE_DIAS - 1} as completo from silver.silver_abordajes
)
select v.usuario_sk as unidad_id, v.persona_id, (select d from par) as fecha_corte,
       case when (select completo from hay_horizonte)
            then (case when f.usuario_sk is null then 1 else 0 end) end as etiqueta
from ventana v
left join futuro f using (usuario_sk)
where v.viajes >= {MIN_ABORDAJES}
  and v.persona_id not in (select persona_id from bajas)
order by unidad_id
"""


def calcular(con, fecha_corte):
    return con.execute(sql_poblacion(fecha_corte)).df()


def costo_unidad(con, fecha_corte):
    """Costo de usar la persona como unidad.
    - Aerómetro no se enlaza: positivos que son personas solo de Aerómetro, y cuántos de ellos en realidad
      siguieron viajando con otra tarjeta (se mide con la regla md5('am' || número), igual que el análisis
      de sensibilidad del Proyecto 1; no se usa para construir la unidad).
    - Comparación: cuántos positivos habría si la unidad fuera la tarjeta y la persona siguió viajando con otra."""
    t = date.fromisoformat(fecha_corte)
    sql = f"""
    with par as (select timestamp '{t} 00:00:00' as t),
    pob as ({sql_poblacion(fecha_corte)}),
    pos as (select unidad_id from pob where etiqueta = 1),
    ident as (select * from silver.silver_identidad_usuario),
    fut as (select distinct a.persona_id, a.sistema, a.usuario_llave_origen from silver.silver_abordajes a, par
            where a.ts_local >= par.t and a.ts_local < par.t + interval {HORIZONTE_DIAS} day),
    numeros as (select distinct persona_id, substr(persona_id, 2) as numero from ident where persona_id like 'P%'),
    am_pos as (select i.llave_origen as hash from pos join ident i on i.usuario_sk = pos.unidad_id and i.persona_id like 'AM:%'),
    am_enlazable as (select a.hash, n.persona_id from am_pos a join numeros n on substr(md5('am' || n.numero), 1, 12) = a.hash),
    am_siguio as (select distinct e.hash from am_enlazable e join fut f on f.persona_id = e.persona_id),
    -- si la unidad fuera la tarjeta: tarjetas sin viajes después del corte cuya persona sí siguió viajando con otra
    ev as (select a.persona_id, a.usuario_llave_origen as tarjeta, count(*) n from silver.silver_abordajes a, par
           where a.ts_local >= par.t - interval {VENTANA_DIAS} day and a.ts_local < par.t group by 1, 2 having count(*) >= {MIN_ABORDAJES}),
    tarjeta_pos as (select e.* from ev e where not exists (select 1 from fut f where f.usuario_llave_origen = e.tarjeta)),
    tarjeta_pos_falsa as (select t.* from tarjeta_pos t where t.persona_id like 'P%'
                          and exists (select 1 from fut f where f.persona_id = t.persona_id))
    select
        (select count(*) from pos) as positivos_persona,
        (select count(*) from am_pos) as positivos_solo_aerometro,
        (select count(*) from am_siguio) as aerometro_que_siguio_viajando,
        (select count(*) from ident where persona_id like 'AM:%') as tarjetas_aerometro_sin_enlazar,
        (select count(*) from ident where persona_id like 'AM:%'
            and llave_origen not in (select substr(md5('am' || numero), 1, 12) from numeros)) as aerometro_sin_numero_conocido,
        (select count(*) from tarjeta_pos) as positivos_si_unidad_tarjeta,
        (select count(*) from tarjeta_pos_falsa) as tarjeta_positiva_pero_persona_siguio
    """
    return con.execute(sql).df().iloc[0].to_dict()


def main(cortes=None):
    SALIDA.mkdir(parents=True, exist_ok=True)
    cortes = cortes or CORTES
    con = duckdb.connect(ruta_warehouse())
    con.execute("create schema if not exists proyecto2")
    import pandas as pd
    tablas, poblacion, costos = [], [], {}
    for nombre, fc in cortes.items():
        df = calcular(con, fc)
        df.insert(0, "corte", nombre)
        tablas.append(df)
        n = len(df)
        pos = int(df["etiqueta"].sum()) if df["etiqueta"].notna().any() else None
        poblacion.append({"corte": nombre, "fecha_corte": fc, "poblacion": n,
                          "positivos": pos if pos is not None else "",
                          "tasa_positiva": round(pos / n, 4) if pos is not None else "",
                          "cuenta": f"{pos:,} / {n:,} = {pos / n:.4f}" if pos is not None else "etiqueta oculta (sin datos posteriores)"})
        if pos is not None:
            costos[nombre] = costo_unidad(con, fc)
        print(f"  corte {nombre} ({fc}): {n:,} unidades" + (f", {pos:,} positivos" if pos is not None else ", etiqueta oculta"))
    todo = pd.concat(tablas, ignore_index=True)
    con.register("todo_df", todo)
    con.execute("create or replace table proyecto2.poblacion_cortes as select * from todo_df")
    con.close()
    with open(SALIDA / "1.2-poblacion.csv", "w", newline="", encoding="utf-8") as f:
        w = csv.DictWriter(f, fieldnames=list(poblacion[0])); w.writeheader(); w.writerows(poblacion)
    (SALIDA / "1.2-costo-unidad.json").write_text(json.dumps({k: {a: int(b) for a, b in v.items()} for k, v in costos.items()},
                                                             indent=2, ensure_ascii=False), encoding="utf-8")


if __name__ == "__main__":
    p = argparse.ArgumentParser()
    p.add_argument("--fecha-corte")
    a = p.parse_args()
    main({"X": a.fecha_corte} if a.fecha_corte else None)
