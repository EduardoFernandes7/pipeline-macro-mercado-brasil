-- No keyless source gives us the real Ibovespa index (see README), so the
-- "market" side of this correlation is an equal-weighted average return
-- across the 4 tracked B3 tickers -- a basket proxy, not the real index.
with basket as (
    select date, avg(daily_return) as daily_return
    from {{ ref('gold_market_daily') }}
    group by date
),

macro as (
    select
        date,
        selic_daily,
        usd_brl / lag(usd_brl) over (order by date) - 1 as usd_brl_change
    from {{ ref('gold_macro_wide') }}
),

joined as (
    select
        basket.daily_return as basket_return,
        macro.selic_daily,
        macro.usd_brl_change
    from basket
    inner join macro on basket.date = macro.date
    where basket.daily_return is not null and macro.usd_brl_change is not null
)

select
    corr(basket_return, selic_daily) as corr_basket_selic,
    corr(basket_return, usd_brl_change) as corr_basket_usd_brl,
    count(*) as n_observations
from joined
