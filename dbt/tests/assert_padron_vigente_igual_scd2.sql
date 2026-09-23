-- El padrón vigente (CDC) y la versión vigente del SCD2 deben coincidir tarjeta por tarjeta.
select v.tarjeta
from {{ ref('padron_vigente') }} v
full join (select * from {{ ref('silver_padron_scd2') }} where es_vigente) s using (tarjeta)
where s.tarjeta is null or v.tarjeta is null or v.activa <> s.activa
   or coalesce(v.zona_residencia_key, -1) <> coalesce(s.zona_residencia_key, -1)
   or coalesce(v.perfil, '') <> coalesce(s.perfil, '')
