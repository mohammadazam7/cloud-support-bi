-- One row per case with the timestamp of each lifecycle milestone.
--
-- A case is created, assigned, first responded to, optionally escalated and resolved.
-- A reopened case is resolved again, so it has two resolved events: the first one is
-- kept for the initial resolution time and the last one is when the case was finally
-- closed.
with events as (

    select * from {{ ref('stg_case_events') }}

)

select
    case_id,
    min(case when event_type = 'created' then occurred_at end) as created_at,
    min(case when event_type = 'assigned' then occurred_at end) as assigned_at,
    max(case when event_type = 'assigned' then agent_id end) as assigned_agent_id,
    min(case when event_type = 'first_response' then occurred_at end) as first_response_at,
    min(case when event_type = 'escalated' then occurred_at end) as escalated_at,
    min(case when event_type = 'resolved' then occurred_at end) as first_resolved_at,
    max(case when event_type = 'resolved' then occurred_at end) as final_resolved_at,
    sum(case when event_type = 'reopened' then 1 else 0 end) as reopen_count,
    count(*) as event_count
from events
group by case_id
