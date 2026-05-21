#!/usr/bin/env bash
set -euo pipefail

CONFIG_PATH="config.yaml"

for arg in "$@"; do
  case "$arg" in
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

CSV_PATH="ibkr_jp_contract_route_discovery_matrix.csv"
REPORT_PATH="reports/ibkr_jp_contract_route_discovery_matrix_report.md"

mkdir -p reports

echo "[INFO] IBKR JP contract route discovery matrix dry-run started: ${RUN_TS}"

python3 - <<PY
from pathlib import Path
import csv
import yaml

config_path = Path("${CONFIG_PATH}")
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

gate_failures = []
if not read_only_required:
    gate_failures.append("read_only_required must be true")
if real_connection_allowed:
    gate_failures.append("real_connection_allowed must be false in dry-run")
if contract_qualification_allowed:
    gate_failures.append("contract_qualification_allowed must be false in dry-run")
if market_data_request_allowed:
    gate_failures.append("market_data_request_allowed must be false")
if historical_data_request_allowed:
    gate_failures.append("historical_data_request_allowed must be false")
if trading_actions_allowed:
    gate_failures.append("trading_actions_allowed must be false")

decision = "NO_GO"
gate_status = "PASS" if not gate_failures else "FAIL"
notes = "; ".join(gate_failures) if gate_failures else "Route discovery matrix generated locally. No IBKR request executed."

jp_symbols = [
    ("1540.T", "1540", "gold_etf"),
    ("1542.T", "1542", "silver_etf"),
]

candidate_routes = [
    {"exchange": "SMART", "primary_exchange": "TSEJ", "currency": "JPY", "sec_type": "STK", "route_family": "smart_tsej"},
    {"exchange": "TSEJ", "primary_exchange": "TSEJ", "currency": "JPY", "sec_type": "STK", "route_family": "direct_tsej"},
    {"exchange": "TSE", "primary_exchange": "TSEJ", "currency": "JPY", "sec_type": "STK", "route_family": "tse_primary_tsej"},
    {"exchange": "SMART", "primary_exchange": "", "currency": "JPY", "sec_type": "STK", "route_family": "smart_no_primary"},
]

rows = []

for display_symbol, symbol, instrument_type in jp_symbols:
    for priority, route in enumerate(candidate_routes, start=1):
        rows.append({
            "run_id": "${RUN_ID}",
            "run_timestamp": "${RUN_TS}",
            "timezone": "Asia/Tokyo",
            "branch": "${BRANCH}",
            "commit": "${COMMIT}",
            "workflow": "ibkr_jp_contract_route_discovery_matrix_dryrun",
            "decision": decision,
            "gate_status": gate_status,
            "display_symbol": display_symbol,
            "symbol": symbol,
            "market": "JP",
            "instrument_type": instrument_type,
            "route_status": "CANDIDATE",
            "candidate_priority": str(priority),
            "route_family": route["route_family"],
            "sec_type": route["sec_type"],
            "exchange": route["exchange"],
            "primary_exchange": route["primary_exchange"],
            "currency": route["currency"],
            "local_symbol": "",
            "trading_class": "",
            "read_only_required": str(read_only_required).lower(),
            "real_connection_allowed": str(real_connection_allowed).lower(),
            "contract_qualification_allowed": str(contract_qualification_allowed).lower(),
            "market_data_request_allowed": str(market_data_request_allowed).lower(),
            "historical_data_request_allowed": str(historical_data_request_allowed).lower(),
            "trading_actions_allowed": str(trading_actions_allowed).lower(),
            "ibkr_connection_triggered": "false",
            "contract_qualification_triggered": "false",
            "market_data_request_triggered": "false",
            "historical_data_request_triggered": "false",
            "broker_execution_triggered": "false",
            "manual_review_required": "true",
            "action_allowed": "false",
            "notes": notes,
        })

rows.append({
    "run_id": "${RUN_ID}",
    "run_timestamp": "${RUN_TS}",
    "timezone": "Asia/Tokyo",
    "branch": "${BRANCH}",
    "commit": "${COMMIT}",
    "workflow": "ibkr_jp_contract_route_discovery_matrix_dryrun",
    "decision": decision,
    "gate_status": gate_status,
    "display_symbol": "518880.SH",
    "symbol": "518880",
    "market": "CN",
    "instrument_type": "gold_etf",
    "route_status": "IBKR_UNSUPPORTED",
    "candidate_priority": "",
    "route_family": "external_or_manual_only",
    "sec_type": "",
    "exchange": "",
    "primary_exchange": "",
    "currency": "",
    "local_symbol": "",
    "trading_class": "",
    "read_only_required": str(read_only_required).lower(),
    "real_connection_allowed": str(real_connection_allowed).lower(),
    "contract_qualification_allowed": str(contract_qualification_allowed).lower(),
    "market_data_request_allowed": str(market_data_request_allowed).lower(),
    "historical_data_request_allowed": str(historical_data_request_allowed).lower(),
    "trading_actions_allowed": str(trading_actions_allowed).lower(),
    "ibkr_connection_triggered": "false",
    "contract_qualification_triggered": "false",
    "market_data_request_triggered": "false",
    "historical_data_request_triggered": "false",
    "broker_execution_triggered": "false",
    "manual_review_required": "true",
    "action_allowed": "false",
    "notes": "Excluded from IBKR route qualification. Use CN/manual/external data source workflow.",
})

header = list(rows[0].keys())

with csv_path.open("w", newline="") as f:
    writer = csv.DictWriter(f, fieldnames=header)
    writer.writeheader()
    writer.writerows(rows)

candidate_count = sum(1 for row in rows if row["route_status"] == "CANDIDATE")
unsupported_count = sum(1 for row in rows if row["route_status"] == "IBKR_UNSUPPORTED")

route_lines = "\\n".join(
    f"| {r['display_symbol']} | {r['route_status']} | {r['candidate_priority']} | {r['exchange']} | {r['primary_exchange']} | {r['currency']} | {r['route_family']} |"
    for r in rows
)

report_path.write_text(f"""# IBKR JP Contract Route Discovery Matrix Dry-run Report

## 1. Run metadata

- run_id: ${RUN_ID}
- run_timestamp: ${RUN_TS}
- timezone: Asia/Tokyo
- branch: ${BRANCH}
- commit: ${COMMIT}
- workflow: ibkr_jp_contract_route_discovery_matrix_dryrun

## 2. Gate decision

| field | value |
|---|---|
| decision | {decision} |
| gate_status | {gate_status} |
| candidate_count | {candidate_count} |
| unsupported_count | {unsupported_count} |
| manual_review_required | true |
| action_allowed | false |

## 3. Route matrix

| display_symbol | route_status | priority | exchange | primary_exchange | currency | route_family |
|---|---|---:|---|---|---|---|
{route_lines}

## 4. Gate posture

| gate | value |
|---|---:|
| read_only_required | {str(read_only_required).lower()} |
| real_connection_allowed | {str(real_connection_allowed).lower()} |
| contract_qualification_allowed | {str(contract_qualification_allowed).lower()} |
| market_data_request_allowed | {str(market_data_request_allowed).lower()} |
| historical_data_request_allowed | {str(historical_data_request_allowed).lower()} |
| trading_actions_allowed | {str(trading_actions_allowed).lower()} |

## 5. Safety assertions

- ibkr_connection_triggered=false
- contract_qualification_triggered=false
- market_data_request_triggered=false
- historical_data_request_triggered=false
- broker_execution_triggered=false
- action_allowed=false
- manual_review_required=true

## 6. Scope correction

518880.SH is excluded from IBKR qualification and must remain under CN/manual/external data source handling.

## 7. Final boundary

This phase generated a local route discovery matrix only.

No IBKR connection occurred, no contract details request occurred, no market data or historical data was requested, and no broker execution occurred.
""")

print("[PASS] IBKR JP contract route discovery matrix generated")
print(f"decision={decision}")
print(f"gate_status={gate_status}")
print(f"candidate_count={candidate_count}")
print(f"unsupported_count={unsupported_count}")
print(f"csv={csv_path}")
print(f"report={report_path}")
PY

echo "[PASS] No IBKR connection triggered"
echo "[PASS] No contract qualification triggered"
echo "[PASS] No market data request triggered"
echo "[PASS] No historical data request triggered"
echo "[PASS] No broker execution triggered"
echo "[PASS] Project remains research-only / read-only / manual-only / no auto trade"
