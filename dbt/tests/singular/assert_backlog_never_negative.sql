select * from {{ ref('fct_backlog_daily') }} where open_cases < 0
