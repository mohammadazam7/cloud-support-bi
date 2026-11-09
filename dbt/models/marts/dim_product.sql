select product_code, product_name, product_family
from {{ ref('products') }}
