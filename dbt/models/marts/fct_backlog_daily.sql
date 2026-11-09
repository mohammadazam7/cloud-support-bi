-- Open cases at the end of each day, by product and priority.
--
-- A case adds one to the backlog on the day it is opened and removes one on the day it
-- is finally resolved, so the backlog is the running sum of those changes. This reads
-- each case once instead of testing every case against every day.
with changes as (

    select created_date as day, product_code, priority, 1 as delta
    from {{ ref('fct_cases') }}

    union all

    select {{ to_date('final_resolved_at') }} as day, product_code, priority, -1 as delta
    from {{ ref('fct_cases') }}

),

daily as (

    select day, product_code, priority, sum(delta) as net_change
    from changes
    group by day, product_code, priority

),

spine as (

    select d.date_day as day, p.product_code, pr.priority
    from {{ ref('dim_date') }} as d
    cross join {{ ref('dim_product') }} as p
    cross join {{ ref('dim_priority') }} as pr
    where d.date_day between (select min(day) from daily) and (select max(day) from daily)

)

select
    s.day as backlog_date,
    s.product_code,
    s.priority,
    sum(coalesce(d.net_change, 0)) over (
        partition by s.product_code, s.priority
        order by s.day
        rows between unbounded preceding and current row
    ) as open_cases
from spine as s
left join daily as d
    on s.day = d.day
    and s.product_code = d.product_code
    and s.priority = d.priority
