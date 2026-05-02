# IBKR Smoke Report

## 当前时间
- JST: 2026-05-02T18:56:39.071967+09:00
- CST: 2026-05-02T17:56:39.071967+08:00
- ET: 2026-05-02T05:56:39.071967-04:00

## IBKR 连接状态
- ib_insync_not_installed
- account_mode: live

## 只读安全声明
- 当前连接为 Live 环境时，本项目仍只执行行情读取，不执行任何交易请求。
- read_only_required: true
- trade_execution_enabled: false

## 标的明细
| symbol | market | contract_status | data_status | market_data_type | bid | ask | last | close | source_status | error_message |
|---|---|---|---|---|---:|---:|---:|---:|---|---|
| 518880.SH | CN | needs_manual_contract_config | unavailable | unavailable | None | None | None | None | contract_build_failed | ib_insync_not_installed |
| 1540.T | JP | needs_manual_contract_config | unavailable | unavailable | None | None | None | None | contract_build_failed | ib_insync_not_installed |
| 1542.T | JP | needs_manual_contract_config | unavailable | unavailable | None | None | None | None | contract_build_failed | ib_insync_not_installed |
| GLD | US | needs_manual_contract_config | unavailable | unavailable | None | None | None | None | contract_build_failed | ib_insync_not_installed |

## 问题清单
- 合约无法解析的标的: 无
- 行情不可用的标的: 518880.SH, 1540.T, 1542.T, GLD
- 仅有延迟行情的标的: 无
- 需要手动补充 IBKR 合约参数的标的: 518880.SH, 1540.T, 1542.T, GLD

本报告仅用于行情接入测试，不构成交易建议，不执行自动交易。