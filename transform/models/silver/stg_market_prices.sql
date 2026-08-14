with source as (
    select * from {{ source('bronze', 'market_prices') }}
),

deduped as (
    select
        date,
        ticker,
        open,
        high,
        low,
        close,
        volume,
        row_number() over (partition by date, ticker order by date) as rn
    from source
    where close is not null and close > 0
)

select date, ticker, open, high, low, close, volume
from deduped
where rn = 1
