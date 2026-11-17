-- Customers as dashboards may see them. The marts keep the real name for the few jobs
-- that need it; everything that reaches a BI tool reads this view instead.
--   customer_label   a stable pseudonym, so a customer can be followed across charts
--                    without being named
--   email_domain     the part after the @, enough to group by organisation
-- Region stays in the clear because row-level access is filtered on it.
select
    d.customer_key,
    'Customer ' || upper(substr({{ dbt.hash('d.customer_id') }}, 1, 8)) as customer_label,
    lower({{ dbt.split_part('c.contact_email', "'@'", 2) }}) as email_domain,
    d.region,
    d.signup_date,
    d.tier,
    d.tier_name,
    d.valid_from,
    d.valid_to,
    d.is_current
from {{ ref('dim_customer') }} as d
inner join {{ ref('stg_customers') }} as c on d.customer_id = c.customer_id
