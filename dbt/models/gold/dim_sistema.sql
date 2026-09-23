select row_number() over (order by sistema_codigo) as sistema_key, sistema_codigo, sistema_nombre,
       tipo_transporte, unidad_registro
from {{ ref('sistemas') }}
