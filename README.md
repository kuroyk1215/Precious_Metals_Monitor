# Precious Metals Monitor

Precious Metals Monitor is a **read-only research and monitoring toolkit** for precious metals ETFs, miners, and related market indicators.

The project focuses on transparent data intake, theoretical pricing, deviation checks, local research reports, and manual research workflows. It is designed for research and observation only.

## Safety Boundaries

This project does **not**:

- place orders
- cancel orders
- rebalance portfolios
- execute trades
- provide automated buy/sell/hold instructions
- send real Telegram messages without explicit manual approval
- access brokerage account or position data unless explicitly gated by operator approval

All trading decisions remain manual and outside the scope of this repository.

## Core Features

- Precious metals ETF and miner watchlist
- JP / CN / US market symbol universe
- Manual CSV market data intake
- Historical data validation
- Theoretical pricing framework
- Deviation check framework
- Local research report generation
- Local read-only dashboard / UI artifacts
- IBKR read-only connection and market data safety gates
- Telegram-ready dry-run message preparation without automatic sending

## Supported Assets

The current watchlist includes:

- China: `518880.SH`
- Japan: `1540.T`, `1542.T`
- US ETFs: `GLD`, `IAU`, `SLV`, `GDX`, `GDXJ`
- US miners: `NEM`, `GOLD`, `AEM`
- Macro proxies: `SPY`, `QQQ`, `TLT`, `UUP`

## Quick Start

Create a local Python environment:

```bash
python3 -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
```

Run the mock workflow:

```bash
python3 main.py --config config.yaml --watchlist watchlist.yaml --mock
```

Expected outputs:

- `precious_metals_signal_log.csv`
- `reports/latest_report.md`

## Read-only IBKR Smoke Test

This project can run an IBKR read-only smoke test when TWS or IB Gateway is available.

```bash
python3 main.py --config config.yaml --watchlist watchlist.yaml --ibkr-smoke
```

Expected outputs:

- `reports/ibkr_smoke_report.md`
- `ibkr_smoke_log.csv`

The project only requests read-only market data in this mode. It does not place, modify, cancel, or transmit orders.

Default paper configuration:

- TWS Paper: `7497`
- Read-only mode: enabled
- Account mode: `paper`

Live or brokerage-provider access must be explicitly configured by the operator and must remain read-only.

## Manual CSV Research Workflow

The project supports an offline manual CSV workflow for research-only precious metals ETF analysis.

Run the manual CSV smoke check:

```bash
python3 main.py --config config.yaml --manual-csv-smoke data/manual_market_data_sample_valid.csv
```

Generate a review pack:

```bash
python3 main.py --config config.yaml --manual-market-data-review-pack data/manual_market_data_sample_valid.csv
```

Use your own manual CSV:

```bash
cp data/manual_market_data_template.csv my_manual_market_data.csv
python3 main.py --config config.yaml --manual-market-data-pipeline my_manual_market_data.csv
python3 main.py --config config.yaml --manual-market-data-review-pack my_manual_market_data.csv
```

Manual CSV workflows produce research artifacts only. They do not produce execution instructions.

## Data Source Policy

The project separates mock data, manual CSV data, public data preparation, and gated read-only provider access.

Public or brokerage data access must be explicitly enabled by the operator. Default workflows are designed to avoid external network calls and trading actions unless a command is explicitly gated.

Licensed metals price data must be provided through authorized sources or manual CSV inputs.

## Generated Outputs

Generated runtime outputs should usually not be committed, including:

- `*_snapshot.csv`
- `*_summary.csv`
- `*_validation.csv`
- `*_review_pack.csv`
- `reports/*_report.md`

Static files may be committed:

- `data/manual_market_data_template.csv`
- `data/manual_market_data_sample_valid.csv`
- `docs/manual_csv_operator_runbook.md`

Run the generated output guard:

```bash
python3 main.py --config config.yaml --generated-output-guard
```

## Roadmap

- Improve provider-agnostic market data adapter interface
- Add more automated tests for pricing, validation, and deviation modules
- Improve local dashboard usability
- Harden secret handling and read-only execution guards
- Improve release checklist and public documentation
- Add clearer examples for GLD / SLV manual CSV workflows

## Disclaimer

This project is for research and observation only. It is not financial advice, investment advice, or a trading system. All trading decisions and executions are performed manually by the user outside this repository.

## License

This project is released under the MIT License.
