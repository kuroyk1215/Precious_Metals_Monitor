# Phase 442 Operator Runbook

## 1. Phase 442 Purpose

Phase 442 adds a standardized real marketdata smoke wrapper for a manual operator. The wrapper is read-only / manual-only / audit-first. It may temporarily allow an IBKR real connection and market data snapshot request, but it does not trade, read accounts, read positions, request historical data, or send Telegram messages.

## 2. Pre-run Checks

- Confirm `config.yaml` has `ibkr.read_only_required: true`.
- Confirm `ibkr.contract_qualification_allowed: false`.
- Confirm `ibkr.historical_data_request_allowed: false`.
- Confirm `ibkr.trading_actions_allowed: false`.
- Confirm TWS or IB Gateway is already controlled by the operator if a live smoke is intended.
- Confirm the run is manual and local; do not schedule this wrapper.

## 3. Temporarily Allowed Gates

Only these two gates may be opened during the wrapper run:

- `ibkr.real_connection_allowed: true`
- `ibkr.market_data_request_allowed: true`

The wrapper restores both fields to the previous file contents on success, failure, or interruption.

## 4. Permanently Forbidden Items

- No automatic trading.
- No account read.
- No position read.
- No historical data request.
- No contract qualification.
- No Telegram real send.
- No order action.
- No cancel action.
- No rebalance action.
- No dashboard or UI expansion.

## 5. How To Run The Wrapper

Run from the repository root:

```bash
bash scripts/operator_real_marketdata_smoke.sh
```

Optional inputs:

```bash
bash scripts/operator_real_marketdata_smoke.sh --contract-map=ibkr_verified_contract_map.csv --market-data-type=auto
```

Generated audit artifacts:

- `operator_real_marketdata_smoke_summary.csv`
- `reports/operator_real_marketdata_smoke_report.md`

## 6. Confirm Config Was Restored

After the wrapper finishes, inspect:

```bash
git status --short config.yaml
rg -n "config_restored|config_file_modified" reports/operator_real_marketdata_smoke_report.md
```

Expected audit values:

- `config_restored=true`
- `config_file_modified=false`

## 7. Confirm Forbidden Paths Were Not Triggered

Inspect the Phase 442 report and summary:

```bash
rg -n "account_read_allowed|position_read_allowed|telegram_send_allowed|req_historical_data_allowed|order_action_allowed|cancel_action_allowed|rebalance_action_allowed|final_safety_status" operator_real_marketdata_smoke_summary.csv reports/operator_real_marketdata_smoke_report.md
```

Expected values:

- `account_read_allowed=false`
- `position_read_allowed=false`
- `telegram_send_allowed=false`
- `req_historical_data_allowed=false`
- `order_action_allowed=false`
- `cancel_action_allowed=false`
- `rebalance_action_allowed=false`

## 8. Failure Handling

If the wrapper fails, first confirm that `config_restored=true` and `config_file_modified=false` in the report. Treat missing market data, connection failure, entitlement errors, or empty prices as audit outcomes, not approval to loosen safety gates. Re-run only after the operator has corrected the external TWS / IB Gateway / entitlement condition.

## 9. Git Submission Notes

Do not submit local runtime state:

- Do not submit `config.yaml`.
- Do not submit `ibkr_market_data_api_errors.csv`.

Only Phase 442 source, script, test, and audit report artifacts should be included.

## 10. Next Phase Entry Conditions

The next phase may begin only when:

- Phase 442 acceptance check passes.
- `config_restored=true`.
- `config_file_modified=false`.
- All forbidden action and read fields remain `false`.
- The operator has reviewed the CSV and Markdown report manually.
