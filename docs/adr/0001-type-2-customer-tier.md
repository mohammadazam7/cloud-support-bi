# 0001. Keep customer tier history as a type 2 dimension

**Status:** Accepted

## Context

A customer's support tier (Standard, Enhanced, Premium) sets the first-response target
for every case they open, and 68 of the 1,200 customers (5.7%) upgrade during the
synthetic year. Storing
only the current tier (type 1) would re-attribute every past case to the new tier: a customer
who upgraded in June would make January's Premium SLA attainment look worse, because
January's cases were really answered against Standard targets.

## Decision

`dim_customer` has one row per customer per tier period, with `valid_from` and
`valid_to` as a half-open range and a hashed `customer_key` per row. `fct_cases` joins
on the period that contains the case's open date and stores that `customer_key` and
`tier_at_open`. The source already provides the tier history, so the periods are built
in `int_customer_tier_periods` with a window function rather than with a dbt snapshot.

## Consequences

- SLA results by tier are reported against the tier in force when each case was opened.
- Facts must join through the period, never on `customer_id` alone; a singular test
  checks that every case finds exactly one period and that periods never overlap.
- If the tier history arrived as a mutable current-state table instead, this would
  become a dbt snapshot; the mart and its tests would not change.
