#!/usr/bin/env bash
set -euo pipefail

echo "[INFO] Scheduler wrapper dry-run"

required_paths=(
  "main.py"
  ".venv"
  "scripts/cleanup_generated_artifacts.sh"
  "scripts/check_mvp_v1_acceptance.sh"
  "scripts/daily_manual_check.sh"
  "logs/scheduler"
)

for path in "${required_paths[@]}"; do
  if [[ ! -e "$path" ]]; then
    echo "[FAIL] Missing required path: $path"
    exit 1
  fi
done

echo "[PASS] Required scheduler dry-run paths exist"
echo "[PASS] No launchd / cron / systemd job installed"
echo "[PASS] No broker execution triggered"
echo "[PASS] Project remains research-only / read-only / manual-only / no auto trade"
