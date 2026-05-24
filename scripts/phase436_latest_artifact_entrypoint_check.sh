#!/usr/bin/env bash
set -euo pipefail

echo "[INFO] Phase 436 latest artifact entrypoint check started"

REPO_ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
FIXTURE_DIR="$(mktemp -d /tmp/phase436_latest.XXXXXX)"
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
        "asset_route": "ARCA",
        "data_source_route": "SYMBOL_BASED_FIRST_VALIDATION",
        "snapshot_status": "DELAYED_SNAPSHOT_RETURNED",
        "effective_market_data_type": "delayed",
        "data_delay_flag": "delayed",
        "latest_price": "221.10",
        "reference_price": "221.10",
        "price_status": "usable_price",
        "operator_status": "OPERATOR_REVIEW_READY",
        "final_research_bucket": "delayed_reference",
        "api_error_codes": "10089",
        "error_10089_detected": "true",
        "error_354_detected": "false",
        "live_subscription_status": "LIVE_NOT_SUBSCRIBED_DELAYED_AVAILABLE",
        "reference_only_status": "LIVE_NOT_SUBSCRIBED_DELAYED_AVAILABLE_REFERENCE_ONLY",
        "delayed_reference_count": "1",
        "manual_review_required": "true",
        "action_allowed": "false",
        "broker_execution_triggered": "false",
        "historical_data_request_triggered": "false",
        "account_read_triggered": "false",
        "position_read_triggered": "false",
        "telegram_send_triggered": "false",
        "recommended_operator_action": "MANUAL_REFERENCE_REVIEW_ONLY",
    }
]
with (root / "daily_operator_handoff_summary.csv").open("w", newline="", encoding="utf-8") as f:
    writer = csv.DictWriter(f, fieldnames=list(rows[0].keys()))
    writer.writeheader()
    writer.writerows(rows)

(root / "reports" / "daily_operator_handoff_summary.md").write_text(
    "# Daily Operator Handoff Summary\n\n- top_level_status=OPERATOR_HANDOFF_REFERENCE_READY\n",
    encoding="utf-8",
)
PY

OUT="$(PYTHONPATH="$REPO_ROOT" bash "$REPO_ROOT/scripts/latest_artifact_entrypoint.sh" --root "$FIXTURE_DIR")"
printf '%s\n' "$OUT"

for path in \
  "$FIXTURE_DIR/latest_daily_operator_handoff_summary.csv" \
  "$FIXTURE_DIR/reports/latest_operator_handoff_summary.md" \
  "$FIXTURE_DIR/latest_run_manifest.csv" \
  "$FIXTURE_DIR/reports/latest_run_manifest.md"
do
  [[ -f "$path" ]] || { echo "[FAIL] Missing output: $path"; exit 1; }
done

PYTHONPATH="$REPO_ROOT" python3 - <<'PY'
from pathlib import Path
import csv
import os

root = Path(os.environ["FIXTURE_DIR"])
manifest_rows = list(csv.DictReader((root / "latest_run_manifest.csv").open(newline="", encoding="utf-8")))
by_path = {row["artifact_path"]: row for row in manifest_rows}

for artifact_path in ("daily_operator_handoff_summary.csv", "reports/daily_operator_handoff_summary.md"):
    assert artifact_path in by_path, artifact_path
    assert by_path[artifact_path]["artifact_status"] in {"PRESENT", "COPIED"}, by_path[artifact_path]

summary_rows = list(csv.DictReader((root / "latest_daily_operator_handoff_summary.csv").open(newline="", encoding="utf-8")))
assert summary_rows, "latest summary has no rows"
safety_fields = (
    "action_allowed",
    "broker_execution_triggered",
    "historical_data_request_triggered",
    "account_read_triggered",
    "position_read_triggered",
    "telegram_send_triggered",
)
for row in summary_rows:
    for field in safety_fields:
        assert row[field] == "false", (field, row)
    text = " ".join(
        value
        for key, value in row.items()
        if key == "recommended_operator_action" or "action" in key.lower()
    ).upper()
    assert not any(word in text for word in ("BUY", "SELL", "ORDER", "CANCEL", "REBALANCE", "AUTO_TRADE", "TRADE")), row

report = (root / "reports" / "latest_run_manifest.md").read_text(encoding="utf-8")
for marker in (
    "action_allowed=false",
    "broker_execution_triggered=false",
    "historical_data_request_triggered=false",
    "account_read_triggered=false",
    "position_read_triggered=false",
    "telegram_send_triggered=false",
):
    assert marker in report, marker
PY

for marker in \
  "latest_entrypoint_status=LATEST_ENTRYPOINT_READY" \
  "operator_handoff_summary_status=PRESENT" \
  "manifest_status=READY" \
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

echo "[PASS] Phase 436 latest artifact entrypoint check completed"
