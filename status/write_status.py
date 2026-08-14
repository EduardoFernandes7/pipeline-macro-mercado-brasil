"""Write a heartbeat after each pipeline run.

Two things ride on this file: it drives a live README badge, and — because CI
commits it back to main — it's a genuine push that resets GitHub's 60-day
auto-disable clock for scheduled workflows (see README for why that matters).
"""

import datetime as dt
import json

import duckdb

from extract.config import DUCKDB_PATH, PROJECT_ROOT

RUN_RESULTS_PATH = PROJECT_ROOT / "transform" / "target" / "run_results.json"
STATUS_PATH = PROJECT_ROOT / "status" / "status.json"
BADGE_PATH = PROJECT_ROOT / "status" / "badge.json"


def _dbt_test_summary() -> dict:
    if not RUN_RESULTS_PATH.exists():
        return {"tests_passed": None, "tests_total": None, "models_succeeded": None, "models_total": None}

    results = json.loads(RUN_RESULTS_PATH.read_text())["results"]
    tests = [r for r in results if r["unique_id"].startswith("test.")]
    models = [r for r in results if r["unique_id"].startswith("model.")]
    return {
        "tests_passed": sum(1 for t in tests if t["status"] == "pass"),
        "tests_total": len(tests),
        "models_succeeded": sum(1 for m in models if m["status"] == "success"),
        "models_total": len(models),
    }


def _row_counts() -> dict:
    con = duckdb.connect(str(DUCKDB_PATH), read_only=True)
    counts = {
        "gold_market_daily": con.execute("SELECT count(*) FROM gold.gold_market_daily").fetchone()[0],
        "gold_macro_wide": con.execute("SELECT count(*) FROM gold.gold_macro_wide").fetchone()[0],
    }
    con.close()
    return counts


def main() -> None:
    test_summary = _dbt_test_summary()
    status = {
        "last_run_utc": dt.datetime.now(dt.timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ"),
        **test_summary,
        "row_counts": _row_counts(),
    }
    STATUS_PATH.parent.mkdir(parents=True, exist_ok=True)
    STATUS_PATH.write_text(json.dumps(status, indent=2) + "\n")

    all_passed = test_summary["tests_total"] and test_summary["tests_passed"] == test_summary["tests_total"]
    badge = {
        "schemaVersion": 1,
        "label": "pipeline",
        "message": f"{test_summary['tests_passed']}/{test_summary['tests_total']} tests passing"
        if test_summary["tests_total"]
        else "unknown",
        "color": "brightgreen" if all_passed else "red",
    }
    BADGE_PATH.write_text(json.dumps(badge, indent=2) + "\n")

    print(json.dumps(status, indent=2))


if __name__ == "__main__":
    main()
