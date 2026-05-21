# IBKR Read-Only Gate Checklist

## 1. Purpose

This checklist defines the minimum safety gates before any future IBKR read-only live data workflow is enabled.

The project remains:

- research-only
- read-only
- manual-only
- no auto trade

## 2. Configuration gates

Required settings:

- read_only_required: true
- trading_actions_allowed: false
- order_action_allowed: false
- cancel_action_allowed: false
- rebalance_action_allowed: false

Any config that allows trading actions must fail admission.

## 3. Code path gates

The project must confirm that the following are not used for execution:

- placeOrder
- cancelOrder
- bracketOrder
- exerciseOptions
- auto rebalance
- auto trade
- broker-side order routing

## 4. Request gates

Market data and historical data requests must be explicitly gated.

Recommended defaults:

- market_data_request_allowed: false
- historical_data_request_allowed: false

Future enablement must be reviewed separately.

## 5. Credential gates

Do not commit:

- account ID
- broker credentials
- TWS password
- API token
- Telegram Bot token
- private config.yaml

## 6. Logging gates

Logs must not expose:

- broker credentials
- account numbers
- API keys
- Telegram Bot token
- private endpoints

Logs may include:

- timestamp
- symbol
- data_status
- source_status
- fallback_method
- run result
- no-trade assertion result

## 7. Data quality gates

Every IBKR-derived record should include:

- symbol
- exchange
- currency
- data_status
- source_status
- timestamp
- fallback_method
- has_valid_price
- quality_note

## 8. Failure gates

If IBKR connection fails:

- mark source unavailable
- preserve report generation if possible
- do not trigger trade fallback
- do not retry indefinitely
- do not send broker instructions

## 9. Manual review gate

Even if IBKR data is available, all outputs remain manual review only.

Required boundary:

    research-only / read-only / manual-only / no auto trade
