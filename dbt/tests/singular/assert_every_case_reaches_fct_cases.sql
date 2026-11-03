-- Every staged case must appear in fct_cases exactly once. A case can only drop out if
-- no tier period covers its open date or its SLA target is missing, and both mean the
-- reported numbers are wrong, so this fails the build.
select s.case_id
from {{ ref('stg_cases') }} as s
left join {{ ref('fct_cases') }} as f on s.case_id = f.case_id
where f.case_id is null
