-- Rows returned are failures: a reporting row that still shows a real name, a full
-- email address or the customer id.
select r.customer_key
from {{ ref('rpt_customers') }} as r
inner join {{ ref('dim_customer') }} as d on r.customer_key = d.customer_key
inner join {{ ref('stg_customers') }} as c on d.customer_id = c.customer_id
where r.customer_label = c.customer_name
   or position(lower(c.customer_name) in lower(r.customer_label)) > 0
   or position('@' in r.email_domain) > 0
   or position(d.customer_id in r.customer_label) > 0
