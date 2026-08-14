"""Extraction of B3 daily prices, via yfinance with a brapi.dev fallback.

yfinance scrapes Yahoo Finance rather than calling a stable, official API, so
it occasionally 429s or breaks after a Yahoo change (confirmed live during
this project's build: every ticker hit YFRateLimitError on the first run).
Each ticker gets a retry with backoff, and if it still fails we fall back to
brapi.dev's free B3 quote API before giving up on that ticker (the pipeline
keeps going either way). MARKET_TICKERS is deliberately limited to the 4
symbols brapi.dev serves without an API key, so the fallback always covers
the same tickers as the primary source.
"""

import datetime as dt
import logging

import pandas as pd
import requests
import yfinance as yf
from tenacity import retry, stop_after_attempt, wait_exponential

from extract.config import DATA_START_DATE, MARKET_TICKERS

logger = logging.getLogger(__name__)

COLUMNS = ["date", "ticker", "open", "high", "low", "close", "volume"]

BRAPI_URL = "https://brapi.dev/api/quote/{symbol}"


@retry(stop=stop_after_attempt(3), wait=wait_exponential(multiplier=1, min=2, max=10))
def _fetch_yfinance_raw(ticker: str, start_date: str) -> pd.DataFrame:
    data = yf.Ticker(ticker).history(start=start_date, auto_adjust=True)
    if data.empty:
        raise ValueError(f"yfinance returned no rows for {ticker}")
    return data


def _standardize_yfinance(raw: pd.DataFrame, ticker: str) -> pd.DataFrame:
    df = raw.reset_index()[["Date", "Open", "High", "Low", "Close", "Volume"]]
    df.columns = ["date", "open", "high", "low", "close", "volume"]
    df["date"] = pd.to_datetime(df["date"]).dt.tz_localize(None)
    df["ticker"] = ticker
    return df[COLUMNS]


def _to_brapi_symbol(ticker: str) -> str:
    return ticker.removesuffix(".SA")


@retry(stop=stop_after_attempt(3), wait=wait_exponential(multiplier=1, min=2, max=10))
def fetch_ticker_brapi(ticker: str, start_date: str = DATA_START_DATE) -> pd.DataFrame:
    symbol = _to_brapi_symbol(ticker)
    response = requests.get(
        BRAPI_URL.format(symbol=symbol), params={"range": "max", "interval": "1d"}, timeout=30
    )
    response.raise_for_status()
    payload = response.json()
    prices = (payload.get("results") or [{}])[0].get("historicalDataPrice") or []
    if not prices:
        raise ValueError(f"brapi.dev returned no historical prices for {symbol}")

    df = pd.DataFrame(prices)
    df["date"] = pd.to_datetime(df["date"], unit="s")
    df["ticker"] = ticker
    df = df[df["date"] >= pd.Timestamp(start_date)]
    return df[COLUMNS]


def fetch_ticker(ticker: str, start_date: str = DATA_START_DATE) -> pd.DataFrame:
    try:
        raw = _fetch_yfinance_raw(ticker, start_date)
        return _standardize_yfinance(raw, ticker)
    except Exception as exc:
        logger.warning("yfinance failed for %s after retries (%s); trying brapi.dev", ticker, exc)

    try:
        return fetch_ticker_brapi(ticker, start_date)
    except Exception as exc:
        logger.warning("brapi.dev fallback also failed for %s (%s); skipping it this run", ticker, exc)
        return pd.DataFrame(columns=COLUMNS)


def fetch_all(tickers: list[str] = MARKET_TICKERS, start_date: str = DATA_START_DATE) -> pd.DataFrame:
    frames = [fetch_ticker(t, start_date) for t in tickers]
    frames = [f for f in frames if not f.empty]
    return pd.concat(frames, ignore_index=True)


if __name__ == "__main__":
    logging.basicConfig(level=logging.INFO)
    result = fetch_all()
    print(result.groupby("ticker")["date"].agg(["min", "max", "count"]))
