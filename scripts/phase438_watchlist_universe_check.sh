#!/usr/bin/env bash
set -euo pipefail

echo "[INFO] Phase 438 watchlist universe check started"

REPO_ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
FIXTURE_DIR="$(mktemp -d /tmp/phase438_watchlist_universe.XXXXXX)"
export FIXTURE_DIR

mkdir -p "$FIXTURE_DIR/config" "$FIXTURE_DIR/reports"
cp "$REPO_ROOT/config/watchlist_us.csv" "$FIXTURE_DIR/config/watchlist_us.csv"
cp "$REPO_ROOT/config/watchlist_jp.csv" "$FIXTURE_DIR/config/watchlist_jp.csv"
cp "$REPO_ROOT/config/watchlist_cn.csv" "$FIXTURE_DIR/config/watchlist_cn.csv"

OUT="$(PYTHONPATH="$REPO_ROOT" bash "$REPO_ROOT/scripts/watchlist_universe.sh" \
  --root "$FIXTURE_DIR" \
  --output-csv "$FIXTURE_DIR/watchlist_universe.csv" \
  --output-report "$FIXTURE_DIR/reports/watchlist_universe_report.md")"
printf '%s\n' "$OUT"

[[ -f "$REPO_ROOT/config/watchlist_us.csv" ]] || { echo "[FAIL] config/watchlist_us.csv missing"; exit 1; }
[[ -f "$REPO_ROOT/config/watchlist_jp.csv" ]] || { echo "[FAIL] config/watchlist_jp.csv missing"; exit 1; }
[[ -f "$REPO_ROOT/config/watchlist_cn.csv" ]] || { echo "[FAIL] config/watchlist_cn.csv missing"; exit 1; }
[[ -f "$FIXTURE_DIR/watchlist_universe.csv" ]] || { echo "[FAIL] watchlist_universe.csv missing"; exit 1; }
[[ -f "$FIXTURE_DIR/reports/watchlist_universe_report.md" ]] || { echo "[FAIL] reports/watchlist_universe_report.md missing"; exit 1; }

PYTHONPATH="$REPO_ROOT" python3 - <<'PY'
from pathlib import Path
import csv
import os

root = Path(os.environ["FIXTURE_DIR"])
rows = list(csv.DictReader((root / "watchlist_universe.csv").open(newline="", encoding="utf-8")))
assert rows, "empty watchlist universe"
by_symbol = {row["display_symbol"]: row for row in rows}

for symbol in ("GLD", "SLV"):
    row = by_symbol[symbol]
    assert row["ibkr_universe_allowed"] == "true", row
    assert row["first_validation_allowed"] == "true", row
    assert row["universe_status"] == "ACTIVE_FIRST_VALIDATION", row

for symbol in ("1540", "1542"):
    row = by_symbol[symbol]
    assert row["ibkr_universe_allowed"] == "false", row
    assert row["first_validation_allowed"] == "false", row
    assert row["universe_status"] == "OPTIONAL_MANUAL_REVIEW", row

cn = by_symbol["518880"]
assert cn["ibkr_universe_allowed"] == "false", cn
assert cn["universe_status"] in {"IBKR_EXCLUDED", "MANUAL_EXTERNAL_ONLY"}, cn
assert cn["validation_status"] == "BLOCKED_FROM_IBKR", cn
assert "518880" not in [row["display_symbol"] for row in rows if row["ibkr_universe_allowed"] == "true"], rows

for row in rows:
    assert row["action_allowed"] == "false", row
    assert row["manual_review_required"] == "true", row

forbidden = ("BUY", "SELL", "ORDER", "CANCEL", "REBALANCE", "AUTO_TRADE", "EXECUTE")
for row in rows:
    for field in ("universe_status", "validation_status", "notes"):
        value = row[field].upper()
        assert not any(word in value for word in forbidden), (field, row)

report = (root / "reports" / "watchlist_universe_report.md").read_text(encoding="utf-8")
assert "top_level_status=WATCHLIST_UNIVERSE_REVIEW_REQUIRED" in report or "top_level_status=WATCHLIST_UNIVERSE_READY" in report, report
assert "broker_connection_triggered=false" in report, report
assert "market_data_request_triggered=false" in report, report
assert "historical_data_request_triggered=false" in report, report
assert "account_read_triggered=false" in report, report
assert "position_read_triggered=false" in report, report
assert "telegram_send_triggered=false" in report, report
assert "trading_action_triggered=false" in report, report
PY

if rg -n "connect\\(|reqMktData|reqHistoricalData|reqAccount|accountSummary|positions\\(|reqPositions|placeOrder|sendMessage|real_connection_allowed: true|market_data_request_allowed: true|historical_data_request_allowed: true|trading_actions_allowed: true" \
  "$REPO_ROOT/src/watchlist_universe.py" "$REPO_ROOT/scripts/watchlist_universe.sh" >/tmp/phase438_forbidden_scan.txt
then
  cat /tmp/phase438_forbidden_scan.txt
  echo "[FAIL] Forbidden live/account/historical/trading/telegram call introduced"
  exit 1
fi

for marker in \
  "top_level_status=WATCHLIST_UNIVERSE_REVIEW_REQUIRED" \
  "offline_only=true" \
  "action_allowed=false" \
  "manual_review_required=true"
do
  if ! grep -F "$marker" <<<"$OUT" >/dev/null; then
    echo "[FAIL] Missing marker: $marker"
    exit 1
  fi
done

echo "[PASS] Phase 438 watchlist universe check completed"
