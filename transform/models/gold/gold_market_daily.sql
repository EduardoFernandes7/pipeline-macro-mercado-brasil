with prices as (
    select * from {{ ref('stg_market_prices') }}
),

metadata as (
    select * from {{ ref('ticker_metadata') }}
)

select
    p.date,
    p.ticker,
    m.company_name,
    m.sector,
    p.close,
    p.volume,
    p.close / lag(p.close) over (partition by p.ticker order by p.date) - 1 as daily_return,
    avg(p.close) over (
        partition by p.ticker order by p.date
        rows between 6 preceding and current row
    ) as sma_7,
    avg(p.close) over (
        partition by p.ticker order by p.date
        rows between 29 preceding and current row
    ) as sma_30
from prices p
left join metadata m on p.ticker = m.ticker
order by p.ticker, p.date
