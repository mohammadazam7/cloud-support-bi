-- Customer dimension as a type 2 slowly changing dimension on support tier.
-- One row per customer per tier period; facts join on the period that contains the
-- event date, so history is reported against the tier the customer held at the time.
with periods as (

    select * from {{ ref('int_customer_tier_periods') }}

),

customers as (

    select * from {{ ref('stg_customers') }}

)

select
    {{ dbt.hash("p.customer_id || '|' || cast(p.valid_from as " ~ dbt.type_string() ~ ")") }}
        as customer_key,
    p.customer_id,
    c.customer_name,
    c.region,
    c.signup_date,
    p.tier,
    t.tier_name,
    p.valid_from,
    p.valid_to,
    p.valid_to = cast('9999-12-31' as date) as is_current
from periods as p
inner join customers as c on p.customer_id = c.customer_id
inner join {{ ref('tiers') }} as t on p.tier = t.tier
