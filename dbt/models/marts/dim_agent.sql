select agent_id, queue, region, hired_on
from {{ ref('stg_agents') }}
