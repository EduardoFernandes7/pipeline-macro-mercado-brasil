with source as (
    select * from {{ source('bronze', 'macro_indicators') }}
),

deduped as (
    select
        date,
        series,
        value,
        row_number() over (partition by date, series order by date) as rn
    from source
    where value is not null
)

select date, series, value
from deduped
where rn = 1
