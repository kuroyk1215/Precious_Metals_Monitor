#!/usr/bin/env bash
set -euo pipefail

REPO_ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
cd "$REPO_ROOT"

PYTHON_BIN="${PYTHON:-python3}"
NORMALIZATION_CSV="operator_real_quote_normalization.csv"
RESEARCH_PLAN_CSV="research_trading_plan.csv"
DECISION_GATE_CSV="operator_real_marketdata_decision_gate.csv"
OUTPUT_CSV="operator_real_quote_signal_bridge.csv"
OUTPUT_REPORT="reports/operator_real_quote_signal_bridge_report.md"

while [[ $# -gt 0 ]]; do
  case "$1" in
    --normalization-csv=*) NORMALIZATION_CSV="${1#--normalization-csv=}"; shift ;;
    --normalization-csv) NORMALIZATION_CSV="${2:?--normalization-csv requires a path}"; shift 2 ;;
    --research-plan-csv=*) RESEARCH_PLAN_CSV="${1#--research-plan-csv=}"; shift ;;
    --research-plan-csv) RESEARCH_PLAN_CSV="${2:?--research-plan-csv requires a path}"; shift 2 ;;
    --decision-gate-csv=*) DECISION_GATE_CSV="${1#--decision-gate-csv=}"; shift ;;
    --decision-gate-csv) DECISION_GATE_CSV="${2:?--decision-gate-csv requires a path}"; shift 2 ;;
    --output-csv=*) OUTPUT_CSV="${1#--output-csv=}"; shift ;;
    --output-csv) OUTPUT_CSV="${2:?--output-csv requires a path}"; shift 2 ;;
    --output-report=*) OUTPUT_REPORT="${1#--output-report=}"; shift ;;
    --output-report) OUTPUT_REPORT="${2:?--output-report requires a path}"; shift 2 ;;
    *) echo "[FAIL] Unknown argument: $1"; exit 2 ;;
  esac
done

PYTHONPATH="$REPO_ROOT${PYTHONPATH:+:$PYTHONPATH}" "$PYTHON_BIN" -m src.operator_real_quote_signal_bridge \
  --normalization-csv "$NORMALIZATION_CSV" \
  --research-plan-csv "$RESEARCH_PLAN_CSV" \
  --decision-gate-csv "$DECISION_GATE_CSV" \
  --output-csv "$OUTPUT_CSV" \
  --output-report "$OUTPUT_REPORT"
