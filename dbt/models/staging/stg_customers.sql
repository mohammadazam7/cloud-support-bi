select
    customer_id,
    customer_name,
    contact_email,
    region,
    cast(signup_date as date) as signup_date
from {{ raw_table('customers') }}
