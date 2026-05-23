#!/usr/bin/env bash
set -euo pipefail

OUTPUT_CSV="release_hardening_audit.csv"
OUTPUT_REPORT="reports/release_hardening_audit_report.md"

mkdir -p "$(dirname "$OUTPUT_REPORT")"

echo "[INFO] Release hardening audit started"

export OUTPUT_CSV OUTPUT_REPORT
python3 - <<'PY'
from pathlib import Path
import os
import subprocess

from src.release_hardening_audit import (
    _ACCOUNT_READS,
    _HISTORICAL_REQUESTS,
    _TRADING_CALLS,
    build_release_hardening_audit_decision,
    check_gitignore_markers,
    check_required_text,
    scan_call_patterns,
    write_release_hardening_audit_csv,
    write_release_hardening_audit_report,
)

default_paths = [
    "src/release_hardening_audit.py",
    "src/ibkr_execution_c_validation.py",
    "src/ibkr_local_daily_runner.py",
    "src/ibkr_daily_marketdata_integration.py",
    "src/ibkr_daily_operator_packet.py",
    "src/ibkr_telegram_notification_packet.py",
    "src/ibkr_telegram_send_gate.py",
    "scripts/release_hardening_audit.sh",
    "scripts/ibkr_execution_c_pipeline_validation.sh",
    "scripts/ibkr_local_daily_runner.sh",
    "scripts/ibkr_daily_research_pipeline.sh",
    "scripts/ibkr_telegram_notification_packet.sh",
    "scripts/ibkr_telegram_send_gate.sh",
]

trading_hits = scan_call_patterns(default_paths, _TRADING_CALLS)
account_hits = scan_call_patterns(default_paths, _ACCOUNT_READS)
historical_hits = scan_call_patterns(default_paths, _HISTORICAL_REQUESTS)

local_runner = Path("scripts/ibkr_local_daily_runner.sh").read_text(encoding="utf-8")
execution_c = Path("scripts/ibkr_execution_c_pipeline_validation.sh").read_text(encoding="utf-8")
telegram_gate = Path("scripts/ibkr_telegram_send_gate.sh").read_text(encoding="utf-8")
default_external_request_ok = (
    'EXECUTE_MARKET_DATA="false"' in local_runner
    and 'EXECUTE_MARKET_DATA="false"' in execution_c
)
default_telegram_send_ok = (
    'TELEGRAM_SEND_ENABLED="false"' in local_runner
    and 'SEND_TELEGRAM="false"' in telegram_gate
)

git_status = subprocess.run(
    ["git", "status", "--short", "--", "config.yaml"],
    check=True,
    capture_output=True,
    text=True,
)
config_file_ok = git_status.stdout.strip() == ""

runtime_artifact_ok = not check_gitignore_markers(".gitignore")

universe_required = [
    "user watchlist only",
    "GLD",
    "SLV",
    "1540.T",
    "1542.T",
    "518880.SH",
    "excluded from IBKR",
    "action_allowed=false",
]
universe_missing = check_required_text("docs/MARKET_UNIVERSE_POLICY.md", universe_required)
universe_policy_ok = not universe_missing
ibkr_universe_policy_ok = not universe_missing
cn_market_policy_ok = not check_required_text(
    "docs/MARKET_UNIVERSE_POLICY.md",
    ["manual market data adapter", "CSV import", "non-IBKR", "broker API"],
)

operator_manual_ok = not check_required_text(
    "docs/OPERATOR_MANUAL.md",
    [
        "ibkr_local_daily_runner.sh --telegram-dry-run",
        "ibkr_execution_c_pipeline_validation.sh --execute-market-data",
        "ibkr_telegram_send_gate.sh --send-telegram",
        "ibkr_execution_c_validation_packet.csv",
        "ibkr_daily_operator_packet.csv",
        "reports/ibkr_daily_operator_packet_report.md",
    ],
)

release_checklist_ok = not check_required_text(
    "docs/RELEASE_CANDIDATE_CHECKLIST.md",
    ["GLD/SLV", "CN ETF excluded from IBKR", "Final no-trade safety checklist"],
)

dashboard_ready_ok = not check_required_text(
    "docs/DASHBOARD_OUTPUT_MANIFEST.md",
    [
        "ibkr_market_data_snapshot.csv",
        "ibkr_daily_operator_packet.csv",
        "ibkr_execution_c_validation_packet.csv",
        "release_hardening_audit.csv",
        "does not implement UI",
        "does not read",
    ],
)

decision = build_release_hardening_audit_decision(
    forbidden_trading_hits=trading_hits,
    forbidden_account_hits=account_hits,
    forbidden_historical_hits=historical_hits,
    default_external_request_ok=default_external_request_ok,
    default_telegram_send_ok=default_telegram_send_ok,
    config_file_ok=config_file_ok,
    runtime_artifact_ok=runtime_artifact_ok,
    universe_policy_ok=universe_policy_ok,
    ibkr_universe_policy_ok=ibkr_universe_policy_ok,
    cn_market_policy_ok=cn_market_policy_ok,
    dashboard_ready_ok=dashboard_ready_ok and release_checklist_ok,
    operator_manual_ok=operator_manual_ok,
)

write_release_hardening_audit_csv(Path(os.environ["OUTPUT_CSV"]), decision)
write_release_hardening_audit_report(Path(os.environ["OUTPUT_REPORT"]), decision)

print("[PASS] Release hardening audit generated" if decision.audit_status == "RELEASE_AUDIT_PASS" else "[FAIL] Release hardening audit blocked")
for field in decision.__dataclass_fields__:
    print(f"{field}={getattr(decision, field)}")
print(f"csv={os.environ['OUTPUT_CSV']}")
print(f"report={os.environ['OUTPUT_REPORT']}")

if decision.audit_status != "RELEASE_AUDIT_PASS":
    raise SystemExit(1)
PY
