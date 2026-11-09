-- A customer holds exactly one tier on any day: periods must be contiguous and must
-- not overlap.
select customer_id, valid_from, valid_to, next_from
from (
    select
        customer_id,
        valid_from,
        valid_to,
        lead(valid_from) over (partition by customer_id order by valid_from) as next_from
    from {{ ref('dim_customer') }}
) as p
where valid_to <= valid_from
   or (next_from is not null and next_from <> valid_to)
