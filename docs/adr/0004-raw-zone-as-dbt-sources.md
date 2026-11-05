# 0004. Declare the raw zone as dbt sources on both targets

**Status:** Accepted

## Context

Staging first read the Parquet files through a custom macro. That worked on DuckDB but
hid the raw tables from dbt: they did not appear in lineage, and dbt had no way to say
whether data had stopped arriving.

## Decision

The raw tables are declared in `models/staging/_sources.yml`. On DuckDB, dbt-duckdb's
`external_location` resolves each source to its Parquet file (the root comes from the
`SUPPORT_BI_RAW` environment variable); on BigQuery the same source names resolve to
tables in the `raw` dataset. Cases, events and surveys carry freshness thresholds: warn
after 2 days without new rows, fail after 4.

## Consequences

- Lineage runs from raw table to metric in dbt docs.
- `dbt source freshness` detects a stalled load, which otherwise looks like a quiet day.
- CI generates a 90-day window that ends on the day it runs, so the freshness check is
  exercised on every pull request rather than skipped.
