-- One row per case as it was opened. Codes are kept as text keys into the dimensions.
select
    case_id,
    customer_id,
    product_code,
    priority,
    channel,
    {{ utc_timestamp('created_at') }} as created_at,
    subject
from {{ raw_table('cases') }}
