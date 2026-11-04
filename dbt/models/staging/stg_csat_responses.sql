select
    case_id,
    {{ utc_timestamp('submitted_at') }} as submitted_at,
    cast(score as integer) as score
from {{ source('raw', 'csat_responses') }}
