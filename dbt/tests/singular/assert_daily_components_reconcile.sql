-- The daily aggregate must add back up to the case fact: no case lost or counted twice.
with a as (
    select sum(cases) as cases, sum(first_response_sla_met_cases) as met
    from {{ ref('agg_support_daily') }}
),
f as (
    select count(*) as cases, sum(case when first_response_sla_met then 1 else 0 end) as met
    from {{ ref('fct_cases') }}
)
select a.*, f.cases as fact_cases, f.met as fact_met
from a cross join f
where a.cases <> f.cases or a.met <> f.met
