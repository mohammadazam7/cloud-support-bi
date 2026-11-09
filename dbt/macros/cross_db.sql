{# Small helpers for the few expressions that differ between DuckDB and BigQuery. #}

{% macro minutes_between(start_ts, end_ts) -%}
    ({{ dbt.datediff(start_ts, end_ts, 'second') }} / 60.0)
{%- endmacro %}

{% macro iso_day_of_week(date_expr) -%}
    {{ return(adapter.dispatch('iso_day_of_week')(date_expr)) }}
{%- endmacro %}

{% macro default__iso_day_of_week(date_expr) -%}
    isodow({{ date_expr }})
{%- endmacro %}

{% macro bigquery__iso_day_of_week(date_expr) -%}
    mod(extract(dayofweek from {{ date_expr }}) + 5, 7) + 1
{%- endmacro %}

{% macro to_date(ts_expr) -%}
    cast({{ ts_expr }} as date)
{%- endmacro %}

{# Raw timestamps are instants in UTC. Convert to a naive UTC timestamp explicitly so
   the result never depends on the session time zone of whoever runs the build. #}
{% macro utc_timestamp(column) -%}
    {{ return(adapter.dispatch('utc_timestamp')(column)) }}
{%- endmacro %}

{% macro default__utc_timestamp(column) -%}
    timezone('UTC', {{ column }})
{%- endmacro %}

{% macro bigquery__utc_timestamp(column) -%}
    {{ column }}
{%- endmacro %}
