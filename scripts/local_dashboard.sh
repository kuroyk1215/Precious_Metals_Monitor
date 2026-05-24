#!/usr/bin/env bash
set -euo pipefail

ROOT="."
OUTPUT_HTML="reports/dashboard.html"

while [[ $# -gt 0 ]]; do
  case "$1" in
    --root=*) ROOT="${1#--root=}"; shift ;;
    --root) ROOT="${2:?--root requires a path}"; shift 2 ;;
    --output-html=*) OUTPUT_HTML="${1#--output-html=}"; shift ;;
    --output-html) OUTPUT_HTML="${2:?--output-html requires a path}"; shift 2 ;;
    *) echo "[FAIL] Unknown argument: $1"; exit 2 ;;
  esac
done

python3 -m src.local_dashboard \
  --root "$ROOT" \
  --output-html "$OUTPUT_HTML"
