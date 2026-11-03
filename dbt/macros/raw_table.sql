{#
  Reference a raw-zone table. On DuckDB the Parquet file is read directly; on BigQuery
  the raw tables are loaded into the `raw` dataset by the load job and read from there.
#}
{% macro raw_table(name) -%}
  {%- if target.type == 'duckdb' -%}
    read_parquet('{{ var("raw_root") }}/{{ name }}/{{ name }}.parquet')
  {%- else -%}
    `{{ target.project }}`.raw.{{ name }}
  {%- endif -%}
{%- endmacro %}

{# Schema names without the target prefix, so marts land in `marts`, not `main_marts`. #}
{% macro generate_schema_name(custom_schema_name, node) -%}
  {{ custom_schema_name if custom_schema_name else target.schema }}
{%- endmacro %}
