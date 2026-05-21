#!/usr/bin/env bash
set -euo pipefail

echo "[INFO] Local automation dry-run pack"

./scripts/check_mvp_v1_acceptance.sh
./scripts/daily_manual_check.sh
./scripts/scheduler_wrapper_dryrun.sh
./scripts/telegram_dryrun_check.sh

echo "[PASS] Local automation dry-run pack completed"
echo "[PASS] No scheduler installed"
echo "[PASS] No Telegram message sent"
echo "[PASS] No broker execution triggered"
echo "[PASS] Project remains research-only / read-only / manual-only / no auto trade"
