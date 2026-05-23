# Operator Manual

## Daily Dry Run

Run the daily dry-run packet without connecting to IBKR market data and without sending Telegram:

```bash
bash scripts/ibkr_local_daily_runner.sh --telegram-dry-run
```

Default behavior is dry-run. It does not connect to IBKR, does not request market data, and does not send Telegram.

## Execution C Manual Validation

Execution C is an explicit operator validation step:

```bash
bash scripts/ibkr_execution_c_pipeline_validation.sh --execute-market-data --market-data-type=auto --telegram-dry-run
```

This may request IBKR market data only because the operator supplied `--execute-market-data`. It remains research-only, reference-only, and manual-review-only.

## Telegram Send Gate Manual Test

Telegram sending is guarded by an explicit send flag and a local approval file:

```bash
bash scripts/ibkr_telegram_send_gate.sh --send-telegram --approval-file=.telegram_send_approval.local
```

Default behavior does not send Telegram. The approval file is local-only and must not be committed.

## Files To Check

After a dry-run or Execution C validation, inspect these local outputs:

- `ibkr_execution_c_validation_packet.csv`
- `ibkr_daily_operator_packet.csv`
- `reports/ibkr_daily_operator_packet_report.md`

The operator packet is the daily handoff. The Execution C validation packet records whether market data validation was explicitly requested and whether the result remains reference-only.

## Forbidden Operations

The system must not:

- automatically place orders
- read accounts
- read positions
- read funds
- request historical data
- grant trade authorization

Safety markers must remain:

- `action_allowed=false`
- `broker_execution_triggered=false`
- `historical_data_request_triggered=false`
- `account_read_triggered=false`
- `position_read_triggered=false`

## Real Use Flow

1. Run the daily dry-run.
2. Run Execution C only when the operator intentionally validates IBKR market data.
3. Review CSV packets and reports manually.
4. Make any trading decision outside this system.

The system does not give order authorization and does not convert a research signal into a broker action.
