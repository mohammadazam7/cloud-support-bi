{{
    config(
        materialized='incremental',
        unique_key='event_id',
        incremental_strategy=('merge' if target.type == 'bigquery' else 'delete+insert'),
        on_schema_change='fail',
        partition_by=(
            {'field': 'occurred_date', 'data_type': 'date', 'granularity': 'day'}
            if target.type == 'bigquery' else none
        ),
        cluster_by=(['event_type'] if target.type == 'bigquery' else none),
    )
}}

-- Every case lifecycle event, loaded incrementally. Each run reprocesses a lookback
-- window before the latest loaded event, so events that arrive late are still picked
-- up; the unique key makes the reload idempotent.
select
    e.event_id,
    e.case_id,
    e.event_type,
    e.occurred_at,
    {{ to_date('e.occurred_at') }} as occurred_date,
    e.agent_id
from {{ ref('stg_case_events') }} as e
{% if is_incremental() %}
where e.occurred_at >= (
    select {{ dbt.dateadd('day', -var('event_lookback_days'), 'max(occurred_at)') }}
    from {{ this }}
)
{% endif %}
