"""Shared configuration for the extraction scripts."""

from pathlib import Path

PROJECT_ROOT = Path(__file__).resolve().parent.parent
DUCKDB_PATH = PROJECT_ROOT / "data" / "warehouse.duckdb"

# Banco Central SGS series codes -> friendly name.
# Full list/search: https://www3.bcb.gov.br/sgspub/localizarseries/localizarSeries.faces
BCB_SERIES = {
    "selic_daily": 11,      # Selic effective daily rate (% a.d.)
    "ipca_monthly": 433,    # IPCA monthly change (%)
    "usd_brl": 1,           # PTAX USD/BRL sell rate
}

# B3-listed tickers (yfinance suffix .SA). Deliberately limited to the 4
# tickers brapi.dev serves keyless (PETR4, VALE3, ITUB4, MGLU3) so the
# fallback path (see market_data.py) always covers the same set as the
# primary one. A free brapi.dev token unlocks full B3 coverage + the
# Ibovespa index itself — see README "Roadmap" for that upgrade.
MARKET_TICKERS = [
    "PETR4.SA",
    "VALE3.SA",
    "ITUB4.SA",
    "MGLU3.SA",
]

# How far back to pull history on every run. The pipeline always rebuilds
# bronze from scratch (see README), so this is the full backfill window,
# not an incremental cursor.
DATA_START_DATE = "2019-01-01"
