-- Milestones happen in order: created, then first response, then first resolution,
-- then final resolution.
select case_id
from {{ ref('fct_cases') }}
where first_response_at < created_at
   or first_resolved_at < first_response_at
   or final_resolved_at < first_resolved_at
