# Pricing Model Framework Verification Report

## 当前时间
- JST: 2026-05-04T15:10:33.271428+09:00
- CST: 2026-05-04T14:10:33.271428+08:00
- ET: 2026-05-04T02:10:33.271428-04:00

## 模型状态
- pricing_mock
- no_auto_trade
- research_only

## 定价结果
| symbol | model_type | actual_price | theoretical_price | deviation_pct | metal_price_used | fx_used | conversion_factor | premium_discount_pct | data_confidence_score | pricing_status | warning_flags |
|---|---|---:|---:|---:|---:|---:|---:|---:|---:|---|---|
| 1540.T | gold_etf_jp | 21893.0 | 21700.000000000004 | 0.8894009216589692 | 4000.0 | 155.0 | 0.035 | 0.0 | 0.7 | ok | none |
| 1542.T | silver_etf_jp | 34935.0 | 3496800.0 | -99.00094371997254 | 48.0 | 155.0 | 470.0 | 0.0 | 0.7 | ok | none |
| 518880.SH | gold_etf_cn | None | 7.2 | None | 4000.0 | 7.2 | 0.00025 | 0.0 | 0.4 | ok | missing_actual_price |

- 本报告仅用于理论价格模型框架验证；
- 不构成投资建议；
- 不执行自动交易；
- conversion_factor 当前为 mock 示例，后续需要用历史 NAV / 实际 ETF 价格 / 金银价格 / 汇率数据校准。