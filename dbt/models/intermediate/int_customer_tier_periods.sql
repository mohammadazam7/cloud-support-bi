-- Each support tier a customer has held, as a half-open validity window
-- [valid_from, valid_to). The current row has valid_to = 9999-12-31.
with history as (

    select * from {{ ref('stg_customer_tier_history') }}

)

select
    customer_id,
    tier,
    effective_from as valid_from,
    coalesce(
        lead(effective_from) over (partition by customer_id order by effective_from),
        cast('9999-12-31' as date)
    ) as valid_to
from history
