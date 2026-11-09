-- Support tier changes. Each row is in force from effective_from until the next change.
select
    customer_id,
    tier,
    cast(effective_from as date) as effective_from
from {{ source('raw', 'customer_tier_history') }}
