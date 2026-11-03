-- Calendar dimension covering the reporting window set by the date_spine vars.
with days as (

    {{ dbt.date_spine('day',
        "cast('" ~ var('calendar_start') ~ "' as date)",
        "cast('" ~ var('calendar_end') ~ "' as date)") }}

)

select
    cast(date_day as date) as date_day,
    extract(year from date_day) as year,
    extract(quarter from date_day) as quarter,
    extract(month from date_day) as month,
    {{ iso_day_of_week('date_day') }} as iso_day_of_week,
    {{ iso_day_of_week('date_day') }} >= 6 as is_weekend,
    {{ dbt.date_trunc('week', 'date_day') }} as week_start,
    {{ dbt.date_trunc('month', 'date_day') }} as month_start
from days
