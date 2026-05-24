#!/usr/bin/env bash
set -euo pipefail

ROOT="."
OUTPUT_CSV="telegram_notification_gate.csv"
OUTPUT_REPORT="reports/telegram_notification_gate_report.md"
PREVIEW_REPORT="reports/telegram_notification_approval_preview.md"
ARGS=()

while [[ $# -gt 0 ]]; do
  case "$1" in
    --root=*) ROOT="${1#--root=}"; shift ;;
    --root) ROOT="${2:?--root requires a path}"; shift 2 ;;
    --dry-run) ARGS+=("--dry-run"); shift ;;
    --send-approved) ARGS+=("--send-approved"); shift ;;
    --approval-note=*) ARGS+=("--approval-note" "${1#--approval-note=}"); shift ;;
    --approval-note) ARGS+=("--approval-note" "${2:?--approval-note requires text}"); shift 2 ;;
    --output-csv=*) OUTPUT_CSV="${1#--output-csv=}"; shift ;;
    --output-csv) OUTPUT_CSV="${2:?--output-csv requires a path}"; shift 2 ;;
    --output-report=*) OUTPUT_REPORT="${1#--output-report=}"; shift ;;
    --output-report) OUTPUT_REPORT="${2:?--output-report requires a path}"; shift 2 ;;
    --preview-report=*) PREVIEW_REPORT="${1#--preview-report=}"; shift ;;
    --preview-report) PREVIEW_REPORT="${2:?--preview-report requires a path}"; shift 2 ;;
    *) echo "[FAIL] Unknown argument: $1"; exit 2 ;;
  esac
done

if [[ ${#ARGS[@]} -gt 0 ]]; then
  python3 -m src.telegram_notification_gate \
    --root "$ROOT" \
    --output-csv "$OUTPUT_CSV" \
    --output-report "$OUTPUT_REPORT" \
    --preview-report "$PREVIEW_REPORT" \
    "${ARGS[@]}"
else
  python3 -m src.telegram_notification_gate \
    --root "$ROOT" \
    --output-csv "$OUTPUT_CSV" \
    --output-report "$OUTPUT_REPORT" \
    --preview-report "$PREVIEW_REPORT"
fi
