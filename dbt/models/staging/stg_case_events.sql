-- Every lifecycle event of every case: created, assigned, first_response, escalated,
-- resolved, reopened. A reopened case has a second resolved event.
select
    event_id,
    case_id,
    event_type,
    cast(occurred_at as timestamp) as occurred_at,
    agent_id
from {{ raw_table('case_events') }}
