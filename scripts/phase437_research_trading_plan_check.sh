#!/usr/bin/env bash
set -euo pipefail

echo "[INFO] Phase 437 research trading plan check started"

REPO_ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
FIXTURE_DIR="$(mktemp -d /tmp/phase437_research_plan.XXXXXX)"
export FIXTURE_DIR

PYTHONPATH="$REPO_ROOT" python3 - <<'PY'
from pathlib import Path
import csv
import os

root = Path(os.environ["FIXTURE_DIR"])
(root / "reports").mkdir(parents=True, exist_ok=True)

rows = [
    {
        "top_level_status": "OPERATOR_HANDOFF_REFERENCE_READY",
        "run_id": "fixture_run",
        "run_timestamp": "2026-05-24T12:00:00+00:00",
        "display_symbol": "GLD",
        "symbol": "GLD",
        "reference_price": "",
        "price_status": "no_price",
        "data_delay_flag": "delayed",
        "effective_market_data_type": "delayed",
        "live_subscription_status": "LIVE_NOT_SUBSCRIBED_DELAYED_AVAILABLE",
        "api_error_codes": "10089",
        "operator_status": "OPERATOR_REVIEW_BLOCKED",
        "action_allowed": "false",
        "broker_execution_triggered": "false",
        "historical_data_request_triggered": "false",
        "account_read_triggered": "false",
        "position_read_triggered": "false",
        "telegram_send_triggered": "false",
        "recommended_operator_action": "NO_PRICE_REVIEW_BLOCKED",
    },
    {
        "top_level_status": "OPERATOR_HANDOFF_REFERENCE_READY",
        "run_id": "fixture_run",
        "run_timestamp": "2026-05-24T12:00:00+00:00",
        "display_symbol": "SLV",
        "symbol": "SLV",
        "reference_price": "68.31",
        "price_status": "usable_price",
        "data_delay_flag": "delayed",
        "effective_market_data_type": "delayed",
        "live_subscription_status": "LIVE_NOT_SUBSCRIBED_DELAYED_AVAILABLE",
        "api_error_codes": "10089",
        "operator_status": "OPERATOR_REVIEW_READY",
        "action_allowed": "false",
        "broker_execution_triggered": "false",
        "historical_data_request_triggered": "false",
        "account_read_triggered": "false",
        "position_read_triggered": "false",
        "telegram_send_triggered": "false",
        "recommended_operator_action": "MANUAL_REFERENCE_REVIEW_ONLY",
    },
]
with (root / "latest_daily_operator_handoff_summary.csv").open("w", newline="", encoding="utf-8") as f:
    writer = csv.DictWriter(f, fieldnames=list(rows[0].keys()))
    writer.writeheader()
    writer.writerows(rows)

(root / "reports" / "latest_operator_handoff_summary.md").write_text(
    "# Latest Operator Handoff Summary\n\n- top_level_status=OPERATOR_HANDOFF_REFERENCE_READY\n",
    encoding="utf-8",
)
(root / "latest_run_manifest.csv").write_text(
    "artifact_path,artifact_status\nlatest_daily_operator_handoff_summary.csv,PRESENT\n",
    encoding="utf-8",
)
PY

OUT="$(PYTHONPATH="$REPO_ROOT" bash "$REPO_ROOT/scripts/research_trading_plan.sh" \
  --root "$FIXTURE_DIR" \
  --output-csv "$FIXTURE_DIR/research_trading_plan.csv" \
  --output-report "$FIXTURE_DIR/reports/research_trading_plan_report.md")"
printf '%s\n' "$OUT"

[[ -f "$FIXTURE_DIR/research_trading_plan.csv" ]] || { echo "[FAIL] research_trading_plan.csv missing"; exit 1; }
[[ -f "$FIXTURE_DIR/reports/research_trading_plan_report.md" ]] || { echo "[FAIL] report missing"; exit 1; }

PYTHONPATH="$REPO_ROOT" python3 - <<'PY'
from pathlib import Path
import csv
import os

root = Path(os.environ["FIXTURE_DIR"])
rows = list(csv.DictReader((root / "research_trading_plan.csv").open(newline="", encoding="utf-8")))
assert rows, "empty research plan"
by_symbol = {row["display_symbol"]: row for row in rows}
assert by_symbol["GLD"]["research_plan_status"] == "NO_PRICE_PLAN_BLOCKED", by_symbol["GLD"]
assert by_symbol["GLD"]["manual_observation_bias"] == "NO_PRICE_BLOCKED", by_symbol["GLD"]
assert by_symbol["SLV"]["research_plan_status"] == "REFERENCE_ONLY_PLAN_READY", by_symbol["SLV"]
assert by_symbol["SLV"]["manual_observation_bias"] == "REFERENCE_ONLY", by_symbol["SLV"]

safety_fields = (
    "action_allowed",
    "broker_execution_triggered",
    "historical_data_request_triggered",
    "account_read_triggered",
    "position_read_triggered",
    "telegram_send_triggered",
)
for row in rows:
    for field in safety_fields:
        assert row[field] == "false", (field, row)

action_fields = (
    "research_plan_status",
    "manual_observation_bias",
    "manual_watch_zone",
    "manual_invalid_trigger",
    "manual_exit_review_trigger",
    "risk_note",
)
forbidden = ("BUY", "SELL", "ORDER", "CANCEL", "REBALANCE", "AUTO_TRADE", "EXECUTE", "ENTRY_ORDER", "EXIT_ORDER")
for row in rows:
    for field in action_fields:
        value = row[field].upper()
        assert not any(word in value for word in forbidden), (field, row[field])

report = (root / "reports" / "research_trading_plan_report.md").read_text(encoding="utf-8")
assert "top_level_status=RESEARCH_PLAN_REFERENCE_READY" in report, report
PY

for marker in \
  "top_level_status=RESEARCH_PLAN_REFERENCE_READY" \
  "action_allowed=false" \
  "broker_execution_triggered=false" \
  "historical_data_request_triggered=false" \
  "account_read_triggered=false" \
  "position_read_triggered=false" \
  "telegram_send_triggered=false"
do
  if ! grep -F "$marker" <<<"$OUT" >/dev/null; then
    echo "[FAIL] Missing marker: $marker"
    exit 1
  fi
done

echo "[PASS] Phase 437 research trading plan check completed"
