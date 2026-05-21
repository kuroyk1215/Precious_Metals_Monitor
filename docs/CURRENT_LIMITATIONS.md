# 当前限制

## 1. 数据限制

当前 MVP 不保证所有市场数据均为实时数据。

不同市场、不同品种的数据状态可能包括：

- real_time
- delayed
- inferred
- unavailable

因此，所有结果必须经过人工复核。

## 2. IBKR 限制

当前系统保持 read-only 设计边界。

默认不执行：

- placeOrder
- cancelOrder
- automatic buy/sell
- auto rebalance
- uncontrolled reqMktData
- uncontrolled reqHistoricalData

## 3. Telegram 限制

当前 Telegram 相关能力处于 stub / ready-output 阶段。

系统可以生成 Telegram-ready text，但不代表已经完成：

- 真实 Bot token 配置
- 真实频道推送
- 推送失败重试
- 推送失败告警
- 多频道路由
- 权限隔离

## 4. Scheduler 限制

当前 scheduler 为 stub 阶段。

尚未完成：

- 真实定时任务部署
- 失败恢复
- 日志轮转
- 多时区调度
- 云端 24 小时运行
- 异常告警

## 5. 交易限制

系统不提供自动交易能力。

交易必须满足：

- 人工复核
- 人工确认
- 人工下单
- 外部交易终端执行

系统输出不构成自动下单信号。

## 6. 配置限制

不得提交：

- config.yaml
- .venv/

本地敏感配置必须保持在 Git 管理之外。

## 7. MVP 边界声明

当前 MVP 是研究辅助系统，不是自动化交易系统。

所有输出均为：

- research-only
- read-only
- manual-only
- no auto trade
