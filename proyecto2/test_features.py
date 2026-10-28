"""Pruebas de límites temporales sin depender de datos privados.

Ejecutar: python -m unittest discover -s proyecto2 -p "test_*.py"
"""
import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch

import duckdb
import pandas as pd

import auditoria
import features


class FeaturesTest(unittest.TestCase):
    def setUp(self):
        self.con = duckdb.connect()
        self.con.execute("""
            create schema silver;
            create table silver.silver_abordajes (
                usuario_sk varchar, persona_id varchar, ts_local timestamp,
                fecha date, hora integer, sistema varchar, monto_q double,
                estacion_key varchar, zona_key varchar);
            insert into silver.silver_abordajes
            select 'u', 'P1', cast(ts as timestamp), cast(ts as date),
                   hour(cast(ts as timestamp)), 'TM', 1.30, 'TM:1', 'Z1'
            from (values ('2026-06-02 23:59:59'), ('2026-06-03 00:00:00'),
                         ('2026-06-17 06:00:00'), ('2026-06-24 08:00:00'),
                         ('2026-06-30 19:00:00'), ('2026-07-01 00:00:00'),
                         ('2026-07-30 12:00:00')) e(ts);
            create table silver.cdc_operaciones (
                numero_persona bigint, operacion varchar, motivo_no_aplicada varchar, ts_operacion timestamp);
            create table silver.festivos_gt (fecha date);
            insert into silver.festivos_gt values ('2026-06-17');
            create table silver.silver_transacciones_rechazadas_tu (usuario_sk varchar, ts_local timestamp);
            insert into silver.silver_transacciones_rechazadas_tu values
                ('u','2026-06-03'), ('u','2026-07-01');
            create table silver.silver_padron_scd2 (
                usuario_sk varchar, perfil varchar, valido_desde timestamp,
                valido_hasta timestamp, operacion_origen varchar);
            insert into silver.silver_padron_scd2 values
                ('u','anterior','2026-06-01','2026-07-01','INSERT'),
                ('u','futuro','2026-07-01','9999-12-31','UPDATE');
            create table silver.padron_vigente (
                tarjeta varchar, operador_tarjeta varchar, perfil varchar, ultima_secuencia bigint);
            insert into silver.padron_vigente values ('TC1','TM','futuro',2);
            create table silver.silver_identidad_usuario (
                usuario_sk varchar, sistema varchar, llave_origen varchar);
            insert into silver.silver_identidad_usuario values ('u','TM','TC1');
        """)

    def tearDown(self):
        self.con.close()

    def test_limites_y_estado_justo_antes_del_corte(self):
        df = features.calcular(self.con, '2026-07-01')
        self.assertEqual(df.columns.tolist(), ['unidad_id', 'fecha_corte'] + features.FEATURES + ['etiqueta'])
        r = df.iloc[0]
        for campo, valor in {'viajes_28d': 4, 'viajes_14d': 3, 'viajes_7d': 2,
                             'tendencia_14d': 2, 'dias_activos_28d': 4,
                             'semanas_activas_28d': 3, 'dias_desde_ultimo_viaje': 1,
                             'dias_desde_primer_viaje_28d': 28, 'pagos_rechazados_28d': 1,
                             'cambios_padron_28d': 0, 'prop_hora_pico_28d': .5,
                             'gasto_q_28d': 5.2, 'tarifa_promedio_q': 1.3,
                             'perfil': 'anterior', 'en_padron': True, 'etiqueta': 0}.items():
            self.assertEqual(r[campo], valor, campo)

    def test_recorte_invariante_y_control_negativo(self):
        completo = auditoria.calcular(self.con)
        neg_completo = auditoria.perfil_final(self.con, completo)
        self.con.execute("""
            delete from silver.silver_abordajes where ts_local >= timestamp '2026-07-01';
            delete from silver.silver_transacciones_rechazadas_tu where ts_local >= timestamp '2026-07-01';
            delete from silver.silver_padron_scd2 where valido_desde >= timestamp '2026-07-01';
            update silver.silver_padron_scd2 set valido_hasta = timestamp '9999-12-31';
            update silver.padron_vigente set perfil = 'anterior', ultima_secuencia = 1;
        """)
        recortado = auditoria.calcular(self.con)
        resultado = auditoria.comparar(completo, recortado, ['fecha_corte'] + features.FEATURES)
        self.assertEqual(resultado['diferencias'], 0)
        self.assertEqual(resultado['filas_en_un_solo_lado'], 0)
        negativo = auditoria.comparar(neg_completo, auditoria.perfil_final(self.con, recortado), ['perfil_final'])
        self.assertEqual(negativo['diferencias'], 1)

    def test_tarifa_redondea_mitad_con_enteros(self):
        self.con.execute("delete from silver.silver_abordajes")
        self.con.execute("""
            insert into silver.silver_abordajes
            select 'u','P1',timestamp '2026-06-30',date '2026-06-30',0,'TM',
                   case when i < 42 then 1.20 else 1.45 end,'TM:1','Z1'
            from range(48) r(i)
        """)
        fila = features.calcular(self.con, '2026-07-01').iloc[0]
        self.assertEqual(fila['gasto_q_28d'], 59.1)
        self.assertEqual(fila['tarifa_promedio_q'], 1.2313)

    def test_comparacion_nulos_tolerancia_y_filas_ausentes(self):
        a = pd.DataFrame({'unidad_id': ['a','b','c'], 'x': [1., float('nan'), 3.], 'texto': ['a',None,'c']})
        b = pd.DataFrame({'unidad_id': ['a','b','d'], 'x': [1.+1e-10, float('nan'), 3.], 'texto': ['b',None,'c']})
        r = auditoria.comparar(a, b, ['x','texto'])
        self.assertEqual(r['filas_en_un_solo_lado'], 2)
        self.assertEqual(r['features_con_diferencias'], {'texto': 1})


class RecorteTest(unittest.TestCase):
    def test_preserva_bytes_y_filtra_fechas_locales_y_utc(self):
        auditoria.RECORTE.mkdir(parents=True, exist_ok=True)
        with tempfile.TemporaryDirectory(dir=auditoria.RECORTE) as tmp:
            raiz = Path(tmp)
            origen = raiz / 'origen'
            origen.mkdir()
            for nombre in auditoria.ARCHIVOS:
                (origen / nombre).write_bytes(b'id,nombre\r\n1,"Estacion, uno"\r\n')
            ejemplos = {
                'transmetro_validaciones.csv': b'fecha_hora,x\r\n2026-06-30 23:59:59,"a,b"\r\n2026-07-01 00:00:00,c\r\n',
                'transurbano_transacciones.csv': b'fecha,x\r\n30/06/2026,a\r\n01/07/2026,b\r\nfecha_invalida,c\r\n',
                'aerometro_boardings.csv': b'timestamp_utc,x\r\n2026-07-01T05:59:59Z,a\r\n2026-07-01T06:00:00Z,b\r\n',
                'cdc_padron_usuarios.csv': b'commit_ts,x\r\n2026-06-30T23:59:59,a\r\n2026-07-01T00:00:00,b\r\n',
                'metroriel_viajes.jsonl': b'{"entry": {"ts": "2026-06-30T23:59:59"}}\r\n{"entry": {"ts": "2026-07-01T00:00:00"}}\r\n',
            }
            for nombre, contenido in ejemplos.items():
                (origen / nombre).write_bytes(contenido)
            with patch.object(auditoria, 'RECORTE', raiz / 'recorte'):
                conteos = auditoria.recortar(origen)
            self.assertTrue(all(n == 1 for n in conteos.values()))
            for nombre in auditoria.ARCHIVOS:
                original = (origen / nombre).read_bytes()
                obtenido = (raiz / 'recorte' / 'datos_red' / nombre).read_bytes()
                if nombre in ejemplos:
                    lineas = original.splitlines(keepends=True)
                    esperado = b''.join(lineas[:1] if nombre.endswith('jsonl') else lineas[:2])
                else:
                    esperado = original
                self.assertEqual(obtenido, esperado, nombre)


if __name__ == '__main__':
    unittest.main()
