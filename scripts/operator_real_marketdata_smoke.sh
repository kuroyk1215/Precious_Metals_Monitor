#!/usr/bin/env bash
set -u -o pipefail

REPO_ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
cd "$REPO_ROOT"

PYTHON_BIN="${PYTHON:-python3}"
CONFIG_PATH="config.yaml"
CONTRACT_MAP_CSV="ibkr_verified_contract_map.csv"
MARKET_DATA_TYPE="auto"
OUTPUT_CSV="operator_real_marketdata_smoke_summary.csv"
OUTPUT_REPORT="reports/operator_real_marketdata_smoke_report.md"
SNAPSHOT_CSV="ibkr_market_data_snapshot.csv"
SMOKE_SCRIPT="${PHASE442_SMOKE_SCRIPT:-$REPO_ROOT/scripts/ibkr_market_data_snapshot_oneshot.sh}"

while [[ $# -gt 0 ]]; do
  case "$1" in
    --config=*) CONFIG_PATH="${1#--config=}"; shift ;;
    --config) CONFIG_PATH="${2:?--config requires a path}"; shift 2 ;;
    --contract-map=*) CONTRACT_MAP_CSV="${1#--contract-map=}"; shift ;;
    --contract-map) CONTRACT_MAP_CSV="${2:?--contract-map requires a path}"; shift 2 ;;
    --market-data-type=*) MARKET_DATA_TYPE="${1#--market-data-type=}"; shift ;;
    --market-data-type) MARKET_DATA_TYPE="${2:?--market-data-type requires a value}"; shift 2 ;;
    --output-csv=*) OUTPUT_CSV="${1#--output-csv=}"; shift ;;
    --output-csv) OUTPUT_CSV="${2:?--output-csv requires a path}"; shift 2 ;;
    --output-report=*) OUTPUT_REPORT="${1#--output-report=}"; shift ;;
    --output-report) OUTPUT_REPORT="${2:?--output-report requires a path}"; shift 2 ;;
    --snapshot-csv=*) SNAPSHOT_CSV="${1#--snapshot-csv=}"; shift ;;
    --snapshot-csv) SNAPSHOT_CSV="${2:?--snapshot-csv requires a path}"; shift 2 ;;
    --smoke-script=*) SMOKE_SCRIPT="${1#--smoke-script=}"; shift ;;
    --smoke-script) SMOKE_SCRIPT="${2:?--smoke-script requires a path}"; shift 2 ;;
    *) echo "[FAIL] Unknown argument: $1"; exit 2 ;;
  esac
done

mkdir -p reports
STARTED_AT="$("$PYTHON_BIN" - <<'PY'
from datetime import datetime, timezone
print(datetime.now(timezone.utc).replace(microsecond=0).isoformat())
PY
)"
BACKUP_CONFIG="$(mktemp /tmp/phase442_config_backup.XXXXXX)"
RESTORE_ATTEMPTED="false"
RESTORE_OK="false"
CONFIG_FILE_MODIFIED="false"
SMOKE_EXIT_CODE="-1"
WRAPPER_EXIT_CODE="0"
SUMMARY_EXIT_CODE="0"
NOTES="manual_only_read_only_marketdata_smoke"

restore_config() {
  if [[ -f "$BACKUP_CONFIG" ]]; then
    cp "$BACKUP_CONFIG" "$CONFIG_PATH"
    RESTORE_ATTEMPTED="true"
  fi
}

finalize() {
  local exit_code="$1"
  trap - EXIT INT TERM
  WRAPPER_EXIT_CODE="$exit_code"
  restore_config
  if cmp -s "$BACKUP_CONFIG" "$CONFIG_PATH"; then
    RESTORE_OK="true"
    CONFIG_FILE_MODIFIED="false"
  else
    RESTORE_OK="false"
    CONFIG_FILE_MODIFIED="true"
  fi
  ENDED_AT="$("$PYTHON_BIN" - <<'PY'
from datetime import datetime, timezone
print(datetime.now(timezone.utc).replace(microsecond=0).isoformat())
PY
)"
  PYTHONPATH="$REPO_ROOT${PYTHONPATH:+:$PYTHONPATH}" "$PYTHON_BIN" -m src.operator_real_marketdata_smoke_summary \
    --config-path "$CONFIG_PATH" \
    --snapshot-csv "$SNAPSHOT_CSV" \
    --output-csv "$OUTPUT_CSV" \
    --output-report "$OUTPUT_REPORT" \
    --started-at "$STARTED_AT" \
    --ended-at "$ENDED_AT" \
    --wrapper-exit-code "$WRAPPER_EXIT_CODE" \
    --smoke-exit-code "$SMOKE_EXIT_CODE" \
    --config-restored "$RESTORE_OK" \
    --config-file-modified "$CONFIG_FILE_MODIFIED" \
    --real-connection-allowed-during-run true \
    --market-data-request-allowed-during-run true \
    --notes "$NOTES"
  SUMMARY_EXIT_CODE=$?
  rm -f "$BACKUP_CONFIG"
  if [[ "$SUMMARY_EXIT_CODE" -ne 0 ]]; then
    exit "$SUMMARY_EXIT_CODE"
  fi
  exit "$exit_code"
}

trap 'finalize 130' INT
trap 'finalize 143' TERM
trap 'finalize $?' EXIT

cp "$CONFIG_PATH" "$BACKUP_CONFIG"

PYTHONPATH="$REPO_ROOT${PYTHONPATH:+:$PYTHONPATH}" "$PYTHON_BIN" - "$CONFIG_PATH" <<'PY'
from pathlib import Path
import sys
import yaml

path = Path(sys.argv[1])
cfg = yaml.safe_load(path.read_text(encoding="utf-8")) or {}
ibkr = cfg.get("ibkr", {}) if isinstance(cfg, dict) else {}
required = {
    "read_only_required": True,
    "contract_qualification_allowed": False,
    "historical_data_request_allowed": False,
    "trading_actions_allowed": False,
}
failures = []
for key, expected in required.items():
    if ibkr.get(key) is not expected:
        failures.append(f"{key}_must_be_{str(expected).lower()}")
if failures:
    raise SystemExit("[FAIL] Phase 442 precheck failed: " + ",".join(failures))
PY
PRECHECK_EXIT=$?
if [[ "$PRECHECK_EXIT" -ne 0 ]]; then
  NOTES="precheck_failed_safe_defaults_preserved"
  exit "$PRECHECK_EXIT"
fi

PYTHONPATH="$REPO_ROOT${PYTHONPATH:+:$PYTHONPATH}" "$PYTHON_BIN" - "$CONFIG_PATH" <<'PY'
from pathlib import Path
import sys
import yaml

path = Path(sys.argv[1])
cfg = yaml.safe_load(path.read_text(encoding="utf-8")) or {}
ibkr = cfg.setdefault("ibkr", {})
ibkr["real_connection_allowed"] = True
ibkr["market_data_request_allowed"] = True
ibkr["contract_qualification_allowed"] = False
ibkr["historical_data_request_allowed"] = False
ibkr["trading_actions_allowed"] = False
path.write_text(yaml.safe_dump(cfg, sort_keys=False), encoding="utf-8")
PY
OPEN_GATE_EXIT=$?
if [[ "$OPEN_GATE_EXIT" -ne 0 ]]; then
  NOTES="temporary_gate_open_failed"
  exit "$OPEN_GATE_EXIT"
fi

echo "[INFO] Phase 442 real marketdata smoke started"
echo "[INFO] Temporary gates opened: real_connection_allowed=true market_data_request_allowed=true"
echo "[INFO] Permanent gates remain false: contract qualification, historical data, trading actions"

bash "$SMOKE_SCRIPT" \
  --execute \
  --config="$CONFIG_PATH" \
  --contract-map="$CONTRACT_MAP_CSV" \
  --market-data-type="$MARKET_DATA_TYPE"
SMOKE_EXIT_CODE=$?
if [[ "$SMOKE_EXIT_CODE" -ne 0 ]]; then
  NOTES="marketdata_smoke_script_failed_exit_code_${SMOKE_EXIT_CODE}"
  exit "$SMOKE_EXIT_CODE"
fi

NOTES="marketdata_smoke_script_completed_audit_generated"
echo "[PASS] Phase 442 real marketdata smoke wrapper completed"
