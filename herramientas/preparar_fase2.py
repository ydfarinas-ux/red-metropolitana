"""Construye exclusivamente features desde Silver y exporta los entregables de fase 2."""
import argparse, datetime, json, os, subprocess, sys
from pathlib import Path
RAIZ = Path(__file__).resolve().parent.parent

def main():
    parser = argparse.ArgumentParser()
    parser.add_argument('--fecha-corte', default='2026-07-16', type=datetime.date.fromisoformat,
                        help='Fecha de corte exclusiva local, YYYY-MM-DD')
    args = parser.parse_args()
    for line in (RAIZ / '.env').read_text(encoding='utf-8-sig').splitlines():
        if line.strip() and not line.lstrip().startswith('#') and '=' in line:
            key, value = line.split('=', 1)
            os.environ.setdefault(key.strip(), value.split('#', 1)[0].strip())
    for key, default in [('WAREHOUSE_PATH', 'warehouse/red-metropolitana.duckdb'), ('BRONZE_PATH', 'lake/bronze')]:
        path = Path(os.getenv(key, default))
        os.environ[key] = str(path if path.is_absolute() else RAIZ / path)
    os.environ['DBT_SEND_ANONYMOUS_USAGE_STATS'] = 'false'
    dbt = Path(sys.executable).parent / ('dbt.exe' if os.name == 'nt' else 'dbt')
    subprocess.run([str(dbt), 'build', '--select', 'features_usuario', '--profiles-dir', '.',
                    '--vars', json.dumps({'fecha_corte_features': str(args.fecha_corte)})], cwd=RAIZ/'dbt', check=True)
    subprocess.run([sys.executable, str(RAIZ/'herramientas/exportar_fase2.py')], cwd=RAIZ, check=True)

if __name__ == '__main__':
    main()
