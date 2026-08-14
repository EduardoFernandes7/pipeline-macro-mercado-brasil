"""Extraction from the Banco Central do Brasil SGS API (free, keyless)."""

from datetime import date

import pandas as pd
import requests
from tenacity import retry, stop_after_attempt, wait_exponential

from extract.config import BCB_SERIES, DATA_START_DATE

SGS_URL = "https://api.bcb.gov.br/dados/serie/bcdata.sgs.{code}/dados"


@retry(stop=stop_after_attempt(3), wait=wait_exponential(multiplier=1, min=2, max=10))
def _fetch_raw(code: int, start_date: str) -> list[dict]:
    start_ddmmyyyy = date.fromisoformat(start_date).strftime("%d/%m/%Y")
    response = requests.get(
        SGS_URL.format(code=code),
        params={"formato": "json", "dataInicial": start_ddmmyyyy},
        timeout=30,
    )
    response.raise_for_status()
    return response.json()


def fetch_series(code: int, series_name: str, start_date: str = DATA_START_DATE) -> pd.DataFrame:
    """Fetch one SGS series as a tidy (date, series, value) frame."""
    raw = _fetch_raw(code, start_date)
    df = pd.DataFrame(raw)
    df["date"] = pd.to_datetime(df["data"], format="%d/%m/%Y")
    df["value"] = pd.to_numeric(df["valor"], errors="coerce")
    df["series"] = series_name
    return df[["date", "series", "value"]]


def fetch_all(series_map: dict[str, int] = BCB_SERIES, start_date: str = DATA_START_DATE) -> pd.DataFrame:
    """Fetch every configured SGS series and stack them into one long frame."""
    frames = [fetch_series(code, name, start_date) for name, code in series_map.items()]
    return pd.concat(frames, ignore_index=True)


if __name__ == "__main__":
    result = fetch_all()
    print(result.groupby("series")["date"].agg(["min", "max", "count"]))
