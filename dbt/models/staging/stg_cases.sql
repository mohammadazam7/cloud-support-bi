-- One row per case as it was opened. Codes are kept as text keys into the dimensions.
select
    case_id,
    customer_id,
    product_code,
    priority,
    channel,
    cast(created_at as timestamp) as created_at,
    subject
from {{ raw_table('cases') }}
