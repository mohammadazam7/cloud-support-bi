{{
    config(
        partition_by=(
            {'field': 'created_date', 'data_type': 'date', 'granularity': 'month'}
            if target.type == 'bigquery' else none
        ),
        cluster_by=(['product_code', 'priority'] if target.type == 'bigquery' else none),
    )
}}

-- Additive daily components of every support metric, by the dimensions dashboards slice on.
--
-- Only sums and counts are stored. A ratio such as SLA attainment is computed as
-- sum(numerator) / sum(denominator) over whatever rows a query selects, which gives the
-- right answer at any grain. Averaging pre-computed daily ratios would not: a quiet day
-- would weigh as much as a busy one.
select
    created_date,
    product_code,
    priority,
    tier_at_open as tier,
    channel,
    count(*) as cases,
    sum(case when first_response_sla_met then 1 else 0 end) as first_response_sla_met_cases,
    sum(first_response_minutes) as first_response_minutes_sum,
    sum(resolution_hours) as resolution_hours_sum,
    sum(case when is_escalated then 1 else 0 end) as escalated_cases,
    sum(case when is_reopened then 1 else 0 end) as reopened_cases,
    sum(case when has_csat_response then 1 else 0 end) as csat_responses,
    sum(coalesce(csat_score, 0)) as csat_score_sum,
    sum(case when csat_score >= 4 then 1 else 0 end) as csat_satisfied_responses
from {{ ref('fct_cases') }}
group by created_date, product_code, priority, tier_at_open, channel
