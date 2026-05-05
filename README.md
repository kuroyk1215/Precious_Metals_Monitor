# Precious Metals Monitor

本项目用于贵金属相关ETF/矿股的**交易观察、理论价格估算、风险提示与筛选**。

> 严格限制：**不实现自动下单、不实现自动卖出、不实现自动撤单、不调用交易接口**。

## 第一阶段本地验证
```bash
python3 -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
bash scripts/run_mock.sh
# 或
python3 main.py --config config.yaml --watchlist watchlist.yaml --mock
```

预期输出：
- `precious_metals_signal_log.csv`
- `reports/latest_report.md`

## 第二阶段：IBKR 只读行情烟雾测试
1. 启动 TWS 或 IB Gateway。
2. 确认 API 端口（TWS paper 常见 7497，TWS live 常见 7496，Gateway 以用户配置为准）。
3. 运行：
```bash
python3 main.py --config config.yaml --watchlist watchlist.yaml --ibkr-smoke
```
4. 预期输出：
- `reports/ibkr_smoke_report.md`
- `ibkr_smoke_log.csv`
5. 无市场数据订阅时返回 delayed/unavailable 属正常现象。
6. 本项目不会下单，不会卖出，不会撤单。

## 第三阶段：理论价格模型框架验证（只读，当前主入口）
运行：
```bash
python3 main.py --config config.yaml --pricing-mock
```

预期输出：
- `pricing_model_log.csv`
- `reports/pricing_model_report.md`

说明：
- 该流程用于理论价格模型框架验证，不是正式历史校准。
- 不新增自动交易逻辑，不执行下单/卖出/撤单。
- conversion_factor 当前仅为 mock 示例，不是最终交易参数。

## 第三阶段 B：conversion_factor 校准框架（验收入口）
```bash
python main.py --config config.yaml --calibration-csv data/historical_calibration_sample.csv
```

输出：
- `conversion_factor_calibration_log.csv`
- `reports/conversion_factor_calibration_report.md`

说明：
- `data/historical_calibration_sample.csv` 当前是 **synthetic/sample** 数据，不是真实市场历史行情；
- 真实校准需要接入历史 ETF 价格、金银价格、汇率与折溢价序列；
- `recommended_conversion_factor` 仅用于研究，不是交易参数；
- 本项目不自动交易。

## 第三阶段 C：真实历史数据导入与校验器（验收入口）
```bash
python main.py --config config.yaml --validate-history data/historical_import_template.csv
```

输出：
- `data/validated_historical_data.csv`
- `reports/historical_data_validation_report.md`
- `historical_data_validation_log.csv`

说明：
- `--validate-history` 是第三阶段 C 导入与校验入口；
- `--calibration-csv` 是第三阶段 B 的 conversion_factor 校准入口；
- 推荐流程：
  1. 先运行 `--validate-history`；
  2. 检查 `reports/historical_data_validation_report.md`；
  3. 若 `validation_status=ok`，再将 `data/validated_historical_data.csv` 输入 `--calibration-csv`；
  4. 命令：`python main.py --config config.yaml --calibration-csv data/validated_historical_data.csv`。

## 后续实验入口：历史校准（扩展，非第三阶段 B 验收入口）
```bash
python3 main.py --config config.yaml --watchlist watchlist.yaml --calibrate-model
```

## 依赖说明
- `ib_insync` 为可选依赖，仅真实连接 IBKR 时需要。
- `PyYAML` 缺失时会提示：`请先 pip install -r requirements.txt`。

## 免责声明
本系统仅用于研究与交易观察，不构成投资建议。所有交易由用户手动执行。


## Live 只读烟雾测试
用户可以直接连接 Live TWS / Live IB Gateway 做只读行情测试。

默认端口：
- TWS Live: 7496
- TWS Paper: 7497
- IB Gateway Live: 4001
- IB Gateway Paper: 4002

本项目只请求行情，不执行交易。

在 TWS / IB Gateway 设置中建议：
- Enable ActiveX and Socket Clients：开启
- Socket Port：Live TWS 使用 7496，Live Gateway 使用 4001
- Read-Only API：保持开启
- Allow connections from localhost only：建议开启

## Phase 4A: Raw History Builder (Research-only)

推荐流程：

1. 构建 raw candidate：

```bash
python main.py --config config.yaml --build-history data/source_manifest_template.yaml
```

2. 校验 candidate：

```bash
python main.py --config config.yaml --validate-history data/real_historical_candidate.csv
```

3. 若 validation_status=ok，再校准：

```bash
python main.py --config config.yaml --calibration-csv data/validated_historical_data.csv
```

说明：
- `data/raw/*_sample.csv` 是 synthetic sample，不是真实市场数据。
- Phase 4A 不联网、不抓取、不调用交易 API。
- Phase 4A 只做 raw CSV 合并为标准历史 CSV。
- 真实 API / 授权数据源接入放在 Phase 4B。

## Phase 4B-0: Source Adapter Framework (Research-only)

推荐流程：

1. source audit：
```bash
python main.py --config config.yaml --source-audit data/source_provider_manifest_template.yaml
```

2. raw build：
```bash
python main.py --config config.yaml --build-history data/source_manifest_template.yaml
```

3. validate：
```bash
python main.py --config config.yaml --validate-history data/real_historical_candidate.csv
```

4. calibration：
```bash
python main.py --config config.yaml --calibration-csv data/validated_historical_data.csv
```

明确：
- Phase 4B-0 只是数据源审计框架；
- 不联网；
- 不调用 reqHistoricalData；
- 不抓取 LBMA/SGE/BOJ/FRED；
- 真实 adapter 实现在 Phase 4B-1 之后；
- licensed metals price 必须用授权或人工 CSV。

## Phase 4B-1: IBKR historical bars adapter skeleton（plan-only）

命令：

```bash
python main.py --config config.yaml --ibkr-historical-plan
```

说明：
- 本阶段只生成 IBKR historical request plan；
- 默认不连接 TWS；
- 默认不调用 reqHistoricalData；
- 输出 raw CSV candidate 表头（`data/raw/ibkr_jp_etf_prices_candidate.csv`）；
- 后续 Phase 4B-2 才允许在显式开关下调用 reqHistoricalData；
- 不修改既有 smoke / fallback 行为。

## Phase 4B-2A: IBKR historical fetch explicit switch + dry-run default

Dry-run（默认，不连接 TWS，不调用 reqHistoricalData）：

```bash
python main.py --config config.yaml --ibkr-historical-fetch
```

Execute（仅显式开关触发，只读 historical fetch）：

```bash
python main.py --config config.yaml --ibkr-historical-fetch --execute-ibkr-historical-fetch
```

说明：
- 默认 dry-run；
- 不连接 TWS；
- 不调用 reqHistoricalData；
- execute 需要显式开关；
- 本阶段允许返回 `adapter_not_implemented`；
- 输出 raw CSV 后仍需用户运行：

```bash
python main.py --config config.yaml --validate-history data/raw/ibkr_jp_etf_prices_candidate.csv
```

- 不自动 calibration；
- 不下单、不撤单、不调仓。

## Phase 4B-2B: IBKR historical bars read-only execute

- 只有在 `--execute-ibkr-historical-fetch` 显式开关下，才允许通过 TWS `reqHistoricalData` 尝试读取历史日线 bars；
- 默认 dry-run 仍不连接 TWS；
- execute 前提：
  1. TWS 或 IB Gateway 正在运行；
  2. API 已开启；
  3. Read-Only API 开启；
  4. localhost 连接允许；
  5. 对目标市场数据有权限；
- historical data 可用性受 IBKR/TWS 权限及历史数据限制影响；
- 仅请求 1540.T / 1542.T，顺序请求，不并发；
- 输出 raw CSV 后，用户必须手动运行：

```bash
python main.py --config config.yaml --validate-history data/raw/ibkr_jp_etf_prices_candidate.csv
```

- 不自动 calibration；
- 不交易。

## Phase 4C Historical Quality Gate

Run research-only gate:

```bash
python main.py --config config.yaml --quality-gate data/raw/ibkr_jp_etf_prices_candidate.csv
```

Outputs:
- reports/historical_quality_gate_report.md
- historical_quality_gate_log.csv

Safety boundary: research-only, no IBKR connection, no reqHistoricalData, no trading/order/cancel, no auto validate-history, no auto calibration-csv.

