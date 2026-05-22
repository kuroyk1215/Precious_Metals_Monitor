#!/usr/bin/env bash
set -euo pipefail

echo "[INFO] Phase 305-320 IBKR one-command daily research pipeline check"

PATH=.venv/bin:$PATH python -m py_compile main.py src/*.py
PATH=.venv/bin:$PATH PYTHONPATH=. python -m pytest -q

PATH=.venv/bin:$PATH bash scripts/ibkr_daily_research_pipeline.sh | tee /tmp/phase305_320_daily_pipeline_check.out

if ! grep -q "pipeline_status=NO_GO" /tmp/phase305_320_daily_pipeline_check.out; then
  echo "[FAIL] Default dry-run pipeline did not report pipeline_status=NO_GO"
  exit 1
fi

if ! grep -q "execution_c_mode=dry_run" /tmp/phase305_320_daily_pipeline_check.out; then
  echo "[FAIL] Default pipeline did not remain dry_run"
  exit 1
fi

for required in \
  "action_allowed=false" \
  "broker_execution_triggered=false" \
  "historical_data_request_triggered=false" \
  "account_read_triggered=false" \
  "position_read_triggered=false"; do
  if ! grep -q "$required" /tmp/phase305_320_daily_pipeline_check.out; then
    echo "[FAIL] Default pipeline output missing $required"
    exit 1
  fi
done

python - <<'PY'
import csv
from pathlib import Path

operator_csv = Path("ibkr_daily_operator_packet.csv")
summary_csv = Path("ibkr_daily_research_pipeline_summary.csv")
pipeline_report = Path("reports/ibkr_daily_research_pipeline_report.md")
operator_report = Path("reports/ibkr_daily_operator_packet_report.md")
for path in (operator_csv, summary_csv, pipeline_report, operator_report):
    if not path.exists():
        raise SystemExit(f"[FAIL] Missing pipeline output: {path}")

operator_rows = list(csv.DictReader(operator_csv.open(newline="", encoding="utf-8")))
if not operator_rows:
    raise SystemExit("[FAIL] Operator packet is empty")
for row in operator_rows:
    for key in (
        "action_allowed",
        "broker_execution_triggered",
        "historical_data_request_triggered",
        "account_read_triggered",
        "position_read_triggered",
    ):
        if row[key] != "false":
            raise SystemExit(f"[FAIL] Operator packet {key} must be false")
    if row["manual_review_required"] != "true":
        raise SystemExit("[FAIL] Operator packet manual_review_required must be true")

summary_rows = list(csv.DictReader(summary_csv.open(newline="", encoding="utf-8")))
if not summary_rows:
    raise SystemExit("[FAIL] Pipeline summary is empty")
if any(row["execution_c_mode"] != "dry_run" for row in summary_rows):
    raise SystemExit("[FAIL] Pipeline summary must remain dry_run by default")
if any(row["step_name"] == "market_data_snapshot" and row["step_status"] == "PASS" for row in summary_rows):
    raise SystemExit("[FAIL] Default dry-run must not execute market data snapshot")
if any(row["broker_execution_triggered"] != "false" for row in summary_rows):
    raise SystemExit("[FAIL] Pipeline summary broker_execution_triggered must be false")
if any(row["historical_data_request_triggered"] != "false" for row in summary_rows):
    raise SystemExit("[FAIL] Pipeline summary historical_data_request_triggered must be false")
if any(row["account_read_triggered"] != "false" for row in summary_rows):
    raise SystemExit("[FAIL] Pipeline summary account_read_triggered must be false")
if any(row["position_read_triggered"] != "false" for row in summary_rows):
    raise SystemExit("[FAIL] Pipeline summary position_read_triggered must be false")

print("[PASS] Default dry-run pipeline outputs validated")
PY

if rg -nE "\.(placeOrder|cancelOrder|whatIfOrder|bracketOrder|exerciseOptions|reqGlobalCancel)\s*\(" src/ibkr_daily_operator_packet.py scripts/ibkr_daily_operator_packet.sh scripts/ibkr_daily_research_pipeline.sh >/dev/null 2>&1; then
  echo "[FAIL] Forbidden broker trading call found"
  exit 1
fi

if rg -nE "\.(reqAccount|reqPositions|accountSummary|managedAccounts)\s*\(" src/ibkr_daily_operator_packet.py scripts/ibkr_daily_operator_packet.sh scripts/ibkr_daily_research_pipeline.sh >/dev/null 2>&1; then
  echo "[FAIL] Forbidden account or position read found"
  exit 1
fi

echo "[PASS] Phase 305-320 one-command daily research pipeline check completed"
