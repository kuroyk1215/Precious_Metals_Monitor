# Operator Manual

## Daily Dry Run

Run the daily dry-run packet without connecting to IBKR market data and without sending Telegram:

```bash
bash scripts/ibkr_local_daily_runner.sh --telegram-dry-run
```

Default behavior is dry-run. It does not connect to IBKR, does not request market data, and does not send Telegram.

## Execution C Manual Validation

Prepare the first-validation map before the first Execution C run:

```bash
bash scripts/prepare_gld_slv_contract_map.sh
```

Execution C is an explicit operator validation step:

```bash
bash scripts/ibkr_execution_c_pipeline_validation.sh --execute-market-data --market-data-type=auto --telegram-dry-run --contract-map=ibkr_verified_contract_map_gld_slv.csv --log-root=logs/ibkr_daily --retention-days=30
```

This may request IBKR market data only because the operator supplied `--execute-market-data`. It remains research-only, reference-only, and manual-review-only.

Do not use `ibkr_verified_contract_map.csv` for first Execution C validation; it may contain JP/CN legacy rows. 1540.T and 1542.T are optional only, and 518880.SH remains non-IBKR.

## Telegram Send Gate Manual Test

Telegram sending is guarded by an explicit send flag and a local approval file:

```bash
bash scripts/ibkr_telegram_send_gate.sh --send-telegram --approval-file=.telegram_send_approval.local
```

Default behavior does not send Telegram. The approval file is local-only and must not be committed.

## Files To Check

After a dry-run or Execution C validation, inspect these local outputs:

- `ibkr_execution_c_validation_packet.csv`
- `ibkr_market_data_snapshot.csv`
- `ibkr_daily_operator_packet.csv`
- `reports/ibkr_daily_operator_packet_report.md`

The operator packet is the daily handoff. The Execution C validation packet records whether market data validation was explicitly requested and whether the result remains reference-only.

After the first real GLD/SLV Execution C run, summarize the existing local outputs without reconnecting to IBKR:

```bash
bash scripts/first_operator_run_post_analysis.sh
```

This post-run analysis reads only local runtime CSV files and reports. It does not request market data, send Telegram, read accounts, read positions, request historical data, or execute broker actions.

## First GLD/SLV Result Pattern

The first real GLD/SLV Execution C run may return IBKR Error 10089 or Error 354. In this project, when delayed data is available, both errors are treated as a recognizable live subscription missing / delayed data available scenario.

The expected result pattern is:

- `snapshot_status=DELAYED_SNAPSHOT_RETURNED`
- `effective_market_data_type=delayed` or `delayed_frozen`
- `validation_decision=REVIEW_READY_REFERENCE_ONLY`
- `action_allowed=false`

`NO_GO` is not the same as a failed chain. Global `NO_GO` means no trade and `action_allowed=false`. Row-level `OPERATOR_REVIEW_READY` means the operator can manually inspect reference-only results. Delayed reference-only data cannot trigger a trade.

After a live test, the operator may turn local gates back off:

```yaml
real_connection_allowed: false
market_data_request_allowed: false
```

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
