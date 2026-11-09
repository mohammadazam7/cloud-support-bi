# 0002. Convert timestamps to UTC explicitly in staging

**Status:** Accepted

## Context

The raw zone stores instants as timestamps with a UTC time zone. In DuckDB, casting
such a value to a plain timestamp converts it to the session's time zone. On a machine
set to America/New_York the first build shifted every case by four or five hours and attributed
cases opened late in the evening to the next date; 22 cases then fell outside their
customer's tier period and disappeared from `fct_cases`. CI, which runs in UTC, would
never have shown it.

## Decision

Staging converts every timestamp with a `utc_timestamp` macro: `timezone('UTC', col)`
on DuckDB, and the column unchanged on BigQuery, where `TIMESTAMP` is already UTC. No
model downstream of staging converts time zones.

## Consequences

- Builds give the same result on any machine, whatever its time zone.
- Reporting in a local time zone is a presentation concern, handled in the BI layer.
- A singular test asserts that every staged case reaches `fct_cases`, which is how the
  original bug was found and would catch a regression.
