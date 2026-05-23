#!/usr/bin/env bash
set -euo pipefail

CONTRACT_MAP="ibkr_verified_contract_map.csv"
MARKET_DATA_TYPE="auto"
LOG_ROOT="logs/ibkr_daily"
RETENTION_DAYS="30"
OUTPUT_CSV="rc_manual_execution_rehearsal_packet.csv"
OUTPUT_REPORT="reports/rc_manual_execution_rehearsal_report.md"
COMMAND_PREVIEW="reports/rc_execution_c_command_preview.md"

for arg in "$@"; do
  case "$arg" in
    --contract-map=*)
      CONTRACT_MAP="${arg#--contract-map=}"
      ;;
    --market-data-type=*)
      MARKET_DATA_TYPE="${arg#--market-data-type=}"
      ;;
    --log-root=*)
      LOG_ROOT="${arg#--log-root=}"
      ;;
    --retention-days=*)
      RETENTION_DAYS="${arg#--retention-days=}"
      ;;
    --output-csv=*)
      OUTPUT_CSV="${arg#--output-csv=}"
      ;;
    --output-report=*)
      OUTPUT_REPORT="${arg#--output-report=}"
      ;;
    --command-preview=*)
      COMMAND_PREVIEW="${arg#--command-preview=}"
      ;;
    *)
      echo "[FAIL] Unknown argument: $arg"
      exit 2
      ;;
  esac
done

case "$MARKET_DATA_TYPE" in
  auto|live|frozen|delayed|delayed_frozen) ;;
  *) echo "[FAIL] Invalid --market-data-type: $MARKET_DATA_TYPE"; exit 2 ;;
esac

mkdir -p "$(dirname "$OUTPUT_REPORT")" "$(dirname "$COMMAND_PREVIEW")"

echo "[INFO] RC manual execution rehearsal started"

export CONTRACT_MAP MARKET_DATA_TYPE LOG_ROOT RETENTION_DAYS OUTPUT_CSV OUTPUT_REPORT COMMAND_PREVIEW
python3 - <<'PY'
from pathlib import Path
import os
import subprocess

from src.release_hardening_audit import check_required_text
from src.rc_manual_execution_rehearsal import (
    build_rc_manual_execution_rehearsal_decision,
    write_command_preview,
    write_rehearsal_csv,
    write_rehearsal_report,
)

required_scripts = [
    "scripts/ibkr_execution_c_pipeline_validation.sh",
    "scripts/ibkr_local_daily_runner.sh",
    "scripts/ibkr_daily_research_pipeline.sh",
    "scripts/release_hardening_audit.sh",
]
missing_inputs = []

required_scripts_ok = True
for script in required_scripts:
    if not Path(script).exists():
        required_scripts_ok = False
        missing_inputs.append(f"required_script_missing:{script}")

contract_map_ok = Path(os.environ["CONTRACT_MAP"]).exists()
if not contract_map_ok:
    missing_inputs.append(f"contract_map_missing:{os.environ['CONTRACT_MAP']}")

universe_doc = Path("docs/MARKET_UNIVERSE_POLICY.md")
operator_doc = Path("docs/OPERATOR_MANUAL.md")
universe_policy_ok = universe_doc.exists() and operator_doc.exists()
policy_missing = check_required_text(
    universe_doc,
    [
        "user watchlist only",
        "GLD",
        "SLV",
        "1540.T",
        "1542.T",
        "518880.SH",
        "excluded from IBKR",
    ],
)
if policy_missing:
    universe_policy_ok = False
    missing_inputs.extend(f"universe_policy_missing:{marker}" for marker in policy_missing)
if not operator_doc.exists():
    missing_inputs.append("operator_manual_missing:docs/OPERATOR_MANUAL.md")

branch = subprocess.run(
    ["git", "branch", "--show-current"],
    check=True,
    capture_output=True,
    text=True,
).stdout.strip()
git_branch_ok = branch.startswith("phase401-416") or branch == "main"
if not git_branch_ok:
    missing_inputs.append(f"git_branch_unexpected:{branch}")

config_status = subprocess.run(
    ["git", "status", "--short", "--", "config.yaml"],
    check=True,
    capture_output=True,
    text=True,
).stdout.strip()
config_local_only_ok = config_status == ""
if not config_local_only_ok:
    missing_inputs.append("config_yaml_not_stashed_or_not_local_only")

git_worktree_ok = True
command_preview_ok = True

decision = build_rc_manual_execution_rehearsal_decision(
    git_branch_ok=git_branch_ok,
    git_worktree_ok=git_worktree_ok,
    config_local_only_ok=config_local_only_ok,
    required_scripts_ok=required_scripts_ok,
    contract_map_ok=contract_map_ok,
    universe_policy_ok=universe_policy_ok,
    command_preview_ok=command_preview_ok,
    missing_inputs=missing_inputs,
    market_data_type=os.environ["MARKET_DATA_TYPE"],
    contract_map=os.environ["CONTRACT_MAP"],
    log_root=os.environ["LOG_ROOT"],
    retention_days=os.environ["RETENTION_DAYS"],
)

write_rehearsal_csv(Path(os.environ["OUTPUT_CSV"]), decision)
write_rehearsal_report(Path(os.environ["OUTPUT_REPORT"]), decision)
write_command_preview(Path(os.environ["COMMAND_PREVIEW"]), decision)

print("[PASS] RC manual execution rehearsal generated" if decision.rehearsal_status == "RC_REHEARSAL_READY" else "[FAIL] RC manual execution rehearsal blocked")
for field in decision.__dataclass_fields__:
    print(f"{field}={getattr(decision, field)}")
print(f"csv={os.environ['OUTPUT_CSV']}")
print(f"report={os.environ['OUTPUT_REPORT']}")
print(f"command_preview={os.environ['COMMAND_PREVIEW']}")

if decision.rehearsal_status != "RC_REHEARSAL_READY":
    raise SystemExit(1)
PY
