-- Toda operación del CDC se aplicó o está en cuarentena.
select 1 from (select count(*) n from {{ ref('cdc_operaciones') }}) a,
              (select count(*) n from {{ ref('stg_cdc_padron') }}) b
where a.n <> b.n
