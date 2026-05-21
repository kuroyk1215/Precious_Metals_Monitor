# Daily Operation Checklist

## 1. Purpose

This checklist defines the daily manual operation flow for Precious_Metals_Monitor MVP v1.0.

The project remains:

- research-only
- read-only
- manual-only
- no auto trade

## 2. Daily start checklist

Before running the workflow:

1. Enter project directory:

       cd ~/Precious_Metals_Monitor

2. Activate virtual environment:

       source .venv/bin/activate

3. Confirm current branch:

       git branch --show-current

4. Confirm local state:

       git status --short

Expected local state may include:

    M config.yaml

5. Confirm acceptance pack:

       ./scripts/check_mvp_v1_acceptance.sh

6. Optional test run:

       python -m pytest -q

7. Clean generated artifacts if needed:

       ./scripts/cleanup_generated_artifacts.sh

## 3. Main operation command

Core MVP command:

    python main.py --report-template-daily-log-telegram-ready-output <primary_metals_config.yaml>

## 4. Output review checklist

After running the workflow, review:

- Markdown report
- daily log
- Telegram-ready text
- final research trading plan
- data_status
- source_status
- fallback_method
- timestamp
- manual review checklist
- no-trade assertion

## 5. Data quality checklist

Escalate manual review if:

- data_status is not real_time
- data is delayed
- data is inferred
- data is unavailable
- timestamp is stale
- fallback_method is used
- FX conversion is required
- ETF diverges from underlying reference

## 6. Manual decision checklist

Before any real market action, confirm externally:

- latest market price
- market session
- spread and liquidity
- available cash
- position size
- risk limit
- invalidation condition
- execution method in external broker terminal

## 7. Forbidden actions

The system must not:

- place orders
- cancel orders
- rebalance positions
- execute broker instructions
- trigger trades from Telegram
- trigger trades from scheduler
- bypass manual review

## 8. End-of-day checklist

After the run:

1. Save or archive useful report output if needed.
2. Run cleanup:

       ./scripts/cleanup_generated_artifacts.sh

3. Confirm local state:

       git status --short

Expected local state:

    M config.yaml

## 9. Safety boundary

All daily operation remains:

- research-only
- read-only
- manual-only
- no auto trade
