#!/usr/bin/env bash
set -euo pipefail

REPO_ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
cd "$REPO_ROOT"

PYTHON_BIN="${PYTHON:-python3}"
if [[ -x "$REPO_ROOT/.venv/bin/python" && "${PYTHON:-}" == "" ]]; then
  PYTHON_BIN="$REPO_ROOT/.venv/bin/python"
fi

PYTHONPATH="$REPO_ROOT" "$PYTHON_BIN" -m src.operator_daily_checklist "$@"
