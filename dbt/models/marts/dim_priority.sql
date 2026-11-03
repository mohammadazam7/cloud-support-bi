select priority, priority_label, base_target_minutes, priority_rank
from {{ ref('priorities') }}
