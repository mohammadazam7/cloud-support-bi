# 0003. Store additive metric components, not ratios

**Status:** Accepted

## Context

Dashboards slice support metrics by day, week, product, priority, tier and channel in
any combination. A table of pre-computed daily ratios (SLA attainment per day, say)
cannot be rolled up correctly: averaging daily ratios gives a quiet Sunday with 40 cases
the same weight as a Monday with 400.

## Decision

`agg_support_daily` stores only counts and sums (cases, cases that met the SLA, minutes
to first response, survey responses, score totals and so on). Every ratio metric in
`metrics/metrics.yml` names its numerator and denominator columns, and the metric layer
computes `sum(numerator) / sum(denominator)` over whatever rows a query selects.
Metrics that cannot be built from sums (the median first-response time) are computed
from `fct_cases`; the backlog averages daily levels from `fct_backlog_daily`.

## Consequences

- Ratios are correct at every grain and for every filter.
- Adding a ratio metric usually means adding a component column, a change to one model
  and one YAML entry.
- Percentiles cost a scan of `fct_cases`; at this volume that is cheap, and on BigQuery
  the month partition limits it.
