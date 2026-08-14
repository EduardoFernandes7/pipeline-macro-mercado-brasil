{# dbt's default generate_schema_name macro concatenates the target schema
   with a model's custom +schema config (e.g. "main_gold"). This standard
   override (from dbt Labs' own docs) uses the custom schema name as-is, so
   +schema: gold really means the "gold" schema. #}

{% macro generate_schema_name(custom_schema_name, node) -%}
    {%- if custom_schema_name is none -%}
        {{ target.schema }}
    {%- else -%}
        {{ custom_schema_name | trim }}
    {%- endif -%}
{%- endmacro %}
