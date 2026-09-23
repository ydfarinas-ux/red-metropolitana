{% test combinacion_unica(model, cols) %}
select {{ cols }}, count(*) as n from {{ model }} group by {{ cols }} having count(*) > 1
{% endtest %}
