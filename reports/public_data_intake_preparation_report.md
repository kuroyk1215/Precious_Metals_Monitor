# Public Data Intake Preparation

- status: PUBLIC_DATA_INTAKE_PREPARATION_READY
- public_data_connection_implemented: NO
- external_market_data_request_enabled: NO
- real_price_ingestion_enabled: NO
- live_market_data_enabled: NO
- symbols: GLD / SLV

## Source Candidates

- PUBLIC_DELAYED_SOURCE_CANDIDATE: 公共延迟源，可选，低成本；条款和稳定性待确认。
- MANUAL_CSV_SOURCE: 手动 CSV，当前最安全 fallback；适合先验证流程。
- PAID_MARKET_DATA_API_CANDIDATE: 付费 API，暂不优先；后续评估。
- IBKR_SUBSCRIPTION_OPTION: IBKR Network B / ARCA，可选，开通后支持更稳定行情；当前未订阅未连接。
- HYBRID_ROUTER_DESIGN: Hybrid Router，未来多市场扩展方案。

## Field Contract

- symbol
- market
- source_name
- source_type
- timestamp_utc
- price_status
- last_price_status
- currency
- data_delay_status
- terms_review_status
- reliability_status
- ingestion_status

## Safety Guard

- no source -> no price
- no price -> no signal
- no approved terms -> no automated ingestion
- no verified freshness -> framework only

generated_at_utc: 2026-06-01T10:30:33+00:00
