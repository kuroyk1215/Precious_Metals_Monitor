#!/usr/bin/env bash
set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
REPO_ROOT="$(cd "$SCRIPT_DIR/.." && pwd)"
PYTHON_BIN="${PYTHON:-$REPO_ROOT/.venv/bin/python}"

PYTHONPATH="$REPO_ROOT${PYTHONPATH:+:$PYTHONPATH}" "$PYTHON_BIN" -m src.operator_telegram_dry_run_payload payload "$@"
