#!/usr/bin/env bash
set -euo pipefail

CONFIG_PATH="config.yaml"
EXECUTE="false"

for arg in "$@"; do
  case "$arg" in
    --execute)
      EXECUTE="true"
      ;;
    --config=*)
      CONFIG_PATH="${arg#--config=}"
      ;;
    *)
      echo "[FAIL] Unknown argument: $arg"
      exit 2
      ;;
  esac
done

RUN_TS="$(TZ=Asia/Tokyo date '+%Y-%m-%dT%H:%M:%S%z')"
RUN_ID="$(TZ=Asia/Tokyo date '+%Y%m%d_%H%M%S_JST')"
BRANCH="$(git branch --show-current 2>/dev/null || echo UNKNOWN_BRANCH)"
COMMIT="$(git rev-parse --short HEAD 2>/dev/null || echo UNKNOWN_COMMIT)"

CSV_PATH="ibkr_oneshot_readonly_connection_preflight.csv"
REPORT_PATH="reports/ibkr_oneshot_readonly_connection_preflight_report.md"

mkdir -p reports

echo "[INFO] IBKR one-shot read-only connection preflight started: ${RUN_TS}"

python3 - <<PY
from pathlib import Path
import csv
import sys
import yaml

config_path = Path("${CONFIG_PATH}")
execute = "${EXECUTE}" == "true"
csv_path = Path("${CSV_PATH}")
report_path = Path("${REPORT_PATH}")

if not config_path.exists():
    raise SystemExit("[FAIL] config file not found")

config = yaml.safe_load(config_path.read_text()) or {}
ibkr = config.get("ibkr", {}) or {}

read_only_required = ibkr.get("read_only_required") is True
real_connection_allowed = ibkr.get("real_connection_allowed") is True
contract_qualification_allowed = ibkr.get("contract_qualification_allowed") is True
market_data_request_allowed = ibkr.get("market_data_request_allowed") is True
historical_data_request_allowed = ibkr.get("historical_data_request_allowed") is True
trading_actions_allowed = ibkr.get("trading_actions_allowed") is True

host = str(ibkr.get("host", "127.0.0.1"))
port = int(ibkr.get("port", 7496))
client_id = int(ibkr.get("client_id", 1))

decision = "NO_GO"
connection_attempted = False
connection_succeeded = False
connection_error = ""

gate_failures = []

if not read_only_required:
    gate_failures.append("read_only_required must be true")
if contract_qualification_allowed:
    gate_failures.append("contract_qualification_allowed must be false")
if market_data_request_allowed:
    gate_failures.append("market_data_request_allowed must be false")
if historical_data_request_allowed:
    gate_failures.append("historical_data_request_allowed must be false")
if trading_actions_allowed:
    gate_failures.append("trading_actions_allowed must be false")
if not real_connection_allowed:
    gate_failures.append("real_connection_allowed must be true for execution")
if not execute:
    gate_failures.append("--execute was not provided")

if not gate_failures:
    decision = "GO_CONNECTION_ONLY"
    connection_attempted = True
    try:
        from ib_insync import IB
        ib = IB()
        ib.connect(host, port, clientId=client_id, timeout=5, readonly=True)
        connection_succeeded = ib.isConnected()
        ib.disconnect()
    except Exception as exc:
        connection_succeeded = False
        connection_error = type(exc).__name__ + ": " + str(exc)
else:
    connection_error = "; ".join(gate_failures)

row = {
    "run_id": "${RUN_ID}",
    "run_timestamp": "${RUN_TS}",
    "timezone": "Asia/Tokyo",
    "branch": "${BRANCH}",
    "commit": "${COMMIT}",
    "workflow": "ibkr_oneshot_readonly_connection_preflight",
    "decision": decision,
    "execute_requested": str(execute).lower(),
    "read_only_required": str(read_only_required).lower(),
    "real_connection_allowed": str(real_connection_allowed).lower(),
    "contract_qualification_allowed": str(contract_qualification_allowed).lower(),
    "market_data_request_allowed": str(market_data_request_allowed).lower(),
    "historical_data_request_allowed": str(historical_data_request_allowed).lower(),
    "trading_actions_allowed": str(trading_actions_allowed).lower(),
    "connection_attempted": str(connection_attempted).lower(),
    "connection_succeeded": str(connection_succeeded).lower(),
    "market_data_request_triggered": "false",
    "historical_data_request_triggered": "false",
    "contract_qualification_triggered": "false",
    "broker_execution_triggered": "false",
    "manual_review_required": "true",
    "action_allowed": "false",
    "notes": connection_error,
}

header = list(row.keys())

with csv_path.open("w", newline="") as f:
    writer = csv.DictWriter(f, fieldnames=header)
    writer.writeheader()
    writer.writerow(row)

report_path.write_text(f"""# IBKR One-shot Read-only Connection Preflight Report

## 1. Run metadata

- run_id: {row["run_id"]}
- run_timestamp: {row["run_timestamp"]}
- timezone: Asia/Tokyo
- branch: {row["branch"]}
- commit: {row["commit"]}
- workflow: {row["workflow"]}

## 2. Decision

| field | value |
|---|---|
| decision | {decision} |
| execute_requested | {row["execute_requested"]} |
| connection_attempted | {row["connection_attempted"]} |
| connection_succeeded | {row["connection_succeeded"]} |
| notes | {row["notes"]} |

## 3. Gate posture

| gate | value |
|---|---:|
| read_only_required | {row["read_only_required"]} |
| real_connection_allowed | {row["real_connection_allowed"]} |
| contract_qualification_allowed | {row["contract_qualification_allowed"]} |
| market_data_request_allowed | {row["market_data_request_allowed"]} |
| historical_data_request_allowed | {row["historical_data_request_allowed"]} |
| trading_actions_allowed | {row["trading_actions_allowed"]} |

## 4. Safety assertions

- market_data_request_triggered=false
- historical_data_request_triggered=false
- contract_qualification_triggered=false
- broker_execution_triggered=false
- action_allowed=false
- manual_review_required=true

## 5. Final boundary

This preflight does not request market data, historical data, contract details, account data, or broker execution.

When gates are not satisfied, no IBKR connection is attempted.
""")

print("[PASS] IBKR one-shot read-only connection preflight report generated")
print(f"decision={decision}")
print(f"connection_attempted={str(connection_attempted).lower()}")
print(f"connection_succeeded={str(connection_succeeded).lower()}")
print(f"csv={csv_path}")
print(f"report={report_path}")
PY

echo "[PASS] No market data request triggered"
echo "[PASS] No historical data request triggered"
echo "[PASS] No contract qualification triggered"
echo "[PASS] No broker execution triggered"
echo "[PASS] Project remains research-only / read-only / manual-only / no auto trade"
