select
    case_id,
    cast(submitted_at as timestamp) as submitted_at,
    cast(score as integer) as score
from {{ raw_table('csat_responses') }}
