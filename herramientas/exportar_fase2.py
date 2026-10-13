r"""Exporta datos derivados de Gold para Tableau y la tabla de features de Silver.

Copiar a herramientas/exportar_fase2.py en el proyecto.
Uso: .venv\Scripts\python.exe herramientas/exportar_fase2.py
Respeta WAREHOUSE_PATH del entorno o de .env. No reconstruye la fase 1.
"""
import csv
import json
import os
from pathlib import Path

import duckdb

RAIZ = Path(__file__).resolve().parent.parent
if (RAIZ / '.env').exists():
    for linea in (RAIZ / '.env').read_text(encoding='utf-8-sig').splitlines():
        if linea.strip() and not linea.lstrip().startswith('#') and '=' in linea:
            clave, valor = linea.split('=', 1)
            os.environ.setdefault(clave.strip(), valor.split('#', 1)[0].strip())

DB = Path(os.getenv('WAREHOUSE_PATH', 'warehouse/red-metropolitana.duckdb'))
if not DB.is_absolute():
    DB = RAIZ / DB
if not DB.is_file():
    raise SystemExit(f'No existe el warehouse: {DB}. Restaurar o ejecutar la fase 1 primero.')

CONSULTAS = {
    'demanda.csv': '''
        select d.fecha, s.sistema_codigo, s.sistema_nombre,
               z.zona_key, z.nombre_zona, z.tipo_territorio,
               z.en_trazado_metroriel, t.hora, t.es_dia_habil, t.es_hora_pico,
               sum(f.cantidad_abordajes) as abordajes, sum(f.monto_q) as ingreso_q
        from gold.fct_abordaje f
        join gold.dim_fecha d on d.fecha_key = f.fecha_key
        join gold.dim_sistema s on s.sistema_key = f.sistema_key
        join gold.dim_zona z on z.zona_key = f.zona_key
        join gold.dim_tiempo t on t.tiempo_key = f.tiempo_key
        group by all order by d.fecha, s.sistema_codigo, z.zona_key, t.hora
    ''',
    'cobertura.csv': '''
        select zona_key, nombre_zona, tipo_territorio, municipio,
               tiene_transmetro, tiene_transurbano, tiene_metroriel,
               tiene_aerometro, modos_con_estacion, estaciones,
               tiene_servicio, en_trazado_metroriel
        from gold.dim_zona order by zona_key
    ''',
    'multimodalidad.csv': '''
        with usuarios as (
            select f.usuario_sk, count(distinct f.sistema_key) as modos_usados,
                   string_agg(distinct s.sistema_codigo, ',' order by s.sistema_codigo) as combinacion_modos
            from gold.fct_abordaje f
            join gold.dim_sistema s on s.sistema_key = f.sistema_key
            group by f.usuario_sk
        )
        select modos_usados, combinacion_modos, count(*) as usuarios
        from usuarios group by all order by modos_usados, combinacion_modos
    ''',
    'metroriel.csv': '''
        select z.zona_key, z.nombre_zona, z.tipo_territorio, z.en_trazado_metroriel,
               coalesce(sum(case when s.sistema_codigo in ('TM','TU')
                            then f.cantidad_abordajes else 0 end), 0) as abordajes_tm_tu,
               coalesce(sum(f.cantidad_abordajes), 0) as abordajes_todos_modos,
               coalesce(sum(case when s.sistema_codigo = 'MR'
                            then f.cantidad_abordajes else 0 end), 0) as abordajes_mr
        from gold.dim_zona z
        left join gold.fct_abordaje f on f.zona_key = z.zona_key
        left join gold.dim_sistema s on s.sistema_key = f.sistema_key
        group by all order by abordajes_tm_tu desc, z.zona_key
    ''',
    'features_usuario.csv': 'select * from features.features_usuario order by usuario_sk',
}


def main():
    salida = RAIZ / 'entregables' / 'fase2'
    with duckdb.connect(str(DB), read_only=True) as con:
        # Verifica las consultas antes de exportar; no modifica el warehouse.
        for nombre, consulta in CONSULTAS.items():
            try:
                con.execute('select * from (' + consulta + ') q limit 0')
            except Exception as exc:
                raise SystemExit(f'No se pudo preparar {nombre}: {exc}') from exc
        salida.mkdir(parents=True, exist_ok=True)
        for nombre, consulta in CONSULTAS.items():
            cursor = con.execute(consulta)
            with (salida / nombre).open('w', encoding='utf-8-sig', newline='') as archivo:
                escritor = csv.writer(archivo)
                escritor.writerow([c[0] for c in cursor.description])
                while lote := cursor.fetchmany(10000):
                    escritor.writerows(lote)
            print(salida / nombre)
        meta = {
            'warehouse': str(DB),
            'periodo_gold': [str(x) for x in con.execute(
                'select min(fecha_hora_local), max(fecha_hora_local) from gold.fct_abordaje'
            ).fetchone()],
            'fecha_corte_features': [str(x[0]) for x in con.execute(
                'select distinct fecha_corte from features.features_usuario'
            ).fetchall()],
            'consultas': CONSULTAS,
            'notas': [
                'demanda, multimodalidad y metroriel usan todo el periodo de Gold.',
                'multimodalidad cuenta usuarios que abordaron varios sistemas; no prueba transbordos encadenados.',
                'cobertura mide presencia de estaciones del catalogo; no acceso peatonal ni frecuencia.',
                'features deriva de Silver; no se incorpora al tablero.',
            ],
        }
        (salida / 'linaje_exportaciones.json').write_text(
            json.dumps(meta, ensure_ascii=False, indent=2), encoding='utf-8'
        )


if __name__ == '__main__':
    main()
