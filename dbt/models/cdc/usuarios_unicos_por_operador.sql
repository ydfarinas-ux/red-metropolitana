-- 1.2 Conteo de usuarios únicos por operador (llaves distintas en su archivo de operación).
select 'Transmetro' as operador, 'transmetro_validaciones.csv' as archivo, count(distinct usuario_llave_origen) as usuarios_unicos
from {{ ref('stg_tm_validaciones') }} where usuario_llave_origen is not null
union all select 'Transurbano', 'transurbano_transacciones.csv', count(*) from {{ ref('cat_usuarios_transurbano') }}
union all select 'MetroRiel',   'metroriel_viajes.jsonl',        count(*) from {{ ref('cat_usuarios_metroriel') }}
union all select 'Aerómetro',   'aerometro_boardings.csv',       count(*) from {{ ref('cat_usuarios_aerometro') }}
