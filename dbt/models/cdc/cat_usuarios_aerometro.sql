-- 1.2 Catálogo mínimo de usuarios de aerometro: SOLO la llave.
-- Este operador nunca entregó padrón: no hay nombre, fecha de alta ni ningún atributo, y no se inventan.
select distinct usuario_llave_origen as llave_usuario
from {{ ref('stg_am_boardings') }}
where usuario_llave_origen is not null and trim(usuario_llave_origen) <> ''
