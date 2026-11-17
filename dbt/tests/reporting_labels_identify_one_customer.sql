-- Rows returned are failures: a pseudonym shared by two customers, which would merge
-- them on a dashboard.
select r.customer_label
from {{ ref('rpt_customers') }} as r
inner join {{ ref('dim_customer') }} as d on r.customer_key = d.customer_key
group by r.customer_label
having count(distinct d.customer_id) > 1
