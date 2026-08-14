"""Load raw extracted data into DuckDB as the bronze layer.

Bronze is a full-refresh copy of whatever the extract layer returns right
now, not an append/upsert. Re-running this script just recreates the bronze
tables from the source APIs (see README for why: both sources return full
history for free, so idempotent full rebuilds are simpler than incremental
loads and there's nothing stale to reconcile).
"""

import logging

import duckdb

from extract import bcb_sgs, market_data
from extract.config import DUCKDB_PATH

logger = logging.getLogger(__name__)


def load_bronze() -> None:
    DUCKDB_PATH.parent.mkdir(parents=True, exist_ok=True)
    con = duckdb.connect(str(DUCKDB_PATH))
    con.execute("CREATE SCHEMA IF NOT EXISTS bronze")

    macro_df = bcb_sgs.fetch_all()
    con.execute("CREATE OR REPLACE TABLE bronze.macro_indicators AS SELECT * FROM macro_df")

    market_df = market_data.fetch_all()
    con.execute("CREATE OR REPLACE TABLE bronze.market_prices AS SELECT * FROM market_df")

    macro_count = con.execute("SELECT count(*) FROM bronze.macro_indicators").fetchone()[0]
    market_count = con.execute("SELECT count(*) FROM bronze.market_prices").fetchone()[0]
    logger.info("bronze.macro_indicators: %s rows", macro_count)
    logger.info("bronze.market_prices: %s rows", market_count)

    con.close()


if __name__ == "__main__":
    logging.basicConfig(level=logging.INFO)
    load_bronze()
