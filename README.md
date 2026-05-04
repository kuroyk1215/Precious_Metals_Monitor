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

## 后续实验入口：历史校准（非第三阶段主入口）
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
