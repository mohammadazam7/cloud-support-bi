select
    agent_id,
    queue,
    region,
    cast(hired_on as date) as hired_on
from {{ source('raw', 'agents') }}
