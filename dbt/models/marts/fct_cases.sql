{{
    config(
        partition_by=(
            {'field': 'created_date', 'data_type': 'date', 'granularity': 'month'}
            if target.type == 'bigquery' else none
        ),
        cluster_by=(['product_code', 'priority'] if target.type == 'bigquery' else none),
    )
}}

-- One row per support case: its attributes at open, the tier the customer held on the
-- day it was opened, how long each stage took and whether the first-response SLA was met.
with cases as (

    select * from {{ ref('stg_cases') }}

),

lifecycle as (

    select * from {{ ref('int_case_lifecycle') }}

),

customers as (

    select * from {{ ref('dim_customer') }}

),

csat as (

    select case_id, score from {{ ref('stg_csat_responses') }}

),

joined as (

    select
        c.case_id,
        c.customer_id,
        cu.customer_key,
        cu.tier as tier_at_open,
        c.product_code,
        c.priority,
        c.channel,
        c.created_at,
        {{ to_date('c.created_at') }} as created_date,
        l.assigned_agent_id as agent_id,
        l.first_response_at,
        l.escalated_at,
        l.first_resolved_at,
        l.final_resolved_at,
        l.reopen_count,
        {{ minutes_between('c.created_at', 'l.first_response_at') }} as first_response_minutes,
        {{ minutes_between('c.created_at', 'l.first_resolved_at') }} / 60.0 as resolution_hours,
        csat.score as csat_score
    from cases as c
    inner join lifecycle as l on c.case_id = l.case_id
    inner join customers as cu
        on c.customer_id = cu.customer_id
        and {{ to_date('c.created_at') }} >= cu.valid_from
        and {{ to_date('c.created_at') }} < cu.valid_to
    left join csat on c.case_id = csat.case_id

)

select
    cast(j.case_id as string) as case_id,
    cast(j.customer_id as string) as customer_id,
    cast(j.customer_key as string) as customer_key,
    cast(j.tier_at_open as string) as tier_at_open,
    cast(j.product_code as string) as product_code,
    cast(j.priority as string) as priority,
    cast(j.channel as string) as channel,
    j.created_at,
    j.created_date,
    cast(j.agent_id as string) as agent_id,
    j.first_response_at,
    j.escalated_at,
    j.first_resolved_at,
    j.final_resolved_at,
    cast(j.reopen_count as int64) as reopen_count,
    cast(j.first_response_minutes as numeric) as first_response_minutes,
    cast(j.resolution_hours as numeric) as resolution_hours,
    cast(j.csat_score as int64) as csat_score,
    cast(s.first_response_target_minutes as int64) as first_response_target_minutes,
    j.first_response_minutes <= s.first_response_target_minutes as first_response_sla_met,
    j.escalated_at is not null as is_escalated,
    j.reopen_count > 0 as is_reopened,
    j.csat_score is not null as has_csat_response
from joined as j
inner join {{ ref('sla_targets') }} as s
    on j.priority = s.priority
    and j.tier_at_open = s.tier
