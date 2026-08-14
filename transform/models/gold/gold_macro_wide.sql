with macro as (
    select * from {{ ref('stg_macro_indicators') }}
),

pivoted as (
    select
        date,
        max(case when series = 'selic_daily' then value end) as selic_daily,
        max(case when series = 'usd_brl' then value end) as usd_brl,
        max(case when series = 'ipca_monthly' then value end) as ipca_monthly
    from macro
    group by date
),

-- IPCA only publishes once a month, so most days have no reading here.
-- Forward-fill it: a running count of non-null readings groups every day
-- with the reading that precedes it, then max() over that group carries
-- the last known value forward. Portable pattern, works on any SQL engine.
ipca_filled as (
    select
        *,
        count(ipca_monthly) over (
            order by date rows between unbounded preceding and current row
        ) as ipca_fill_group
    from pivoted
)

select
    date,
    selic_daily,
    usd_brl,
    max(ipca_monthly) over (partition by ipca_fill_group) as ipca_monthly_last_known
from ipca_filled
order by date
