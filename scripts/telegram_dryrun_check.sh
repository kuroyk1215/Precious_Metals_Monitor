#!/usr/bin/env bash
set -euo pipefail

echo "[INFO] Telegram dry-run check"

config="examples/telegram_config.sample.yaml"

if [[ ! -f "$config" ]]; then
  echo "[FAIL] Missing sample Telegram config: $config"
  exit 1
fi

if grep -q "send_allowed: true" "$config"; then
  echo "[FAIL] Sample Telegram config enables real sending"
  exit 1
fi

if grep -q "auto_trade_allowed: true" "$config"; then
  echo "[FAIL] Sample Telegram config enables auto trade"
  exit 1
fi

if grep -q "order_action_allowed: true" "$config"; then
  echo "[FAIL] Sample Telegram config enables order action"
  exit 1
fi

echo "[PASS] Telegram sample config remains dry-run / ready-text only"
echo "[PASS] No real Telegram message sent"
echo "[PASS] No Bot token required"
echo "[PASS] No broker execution triggered"
echo "[PASS] Project remains research-only / read-only / manual-only / no auto trade"
