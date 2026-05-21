# Phase 33+ 路线图

## Phase 33：MVP 文档收口

目标：

- 完成 MVP 总结文档
- 完成使用流程文档
- 完成输入 / 输出文件说明
- 完成当前限制说明
- 完成 Phase 33+ 路线图

不做：

- 不新增功能代码
- 不修改 main.py
- 不修改 src/ 逻辑
- 不修改交易逻辑
- 不修改 IBKR 安全边界
- 不提交 config.yaml
- 不提交 .venv/

## Phase 34：配置样例与运行手册

目标：

- 增加 sample primary_metals_config.yaml
- 增加本地运行手册
- 增加常见错误排查
- 增加报告生成示例

边界：

- research-only
- read-only
- manual-only
- no auto trade

## Phase 35：Telegram 实接入前评估

目标：

- 明确 Bot token 管理方式
- 明确频道 / 用户 ID 配置
- 明确失败重试机制
- 明确是否只推送文本
- 明确不触发交易动作

边界：

- Telegram 只允许推送研究文本
- 不允许推送端触发交易

## Phase 36：Scheduler 实部署前评估

目标：

- 评估 macOS cron / launchd
- 评估云服务器部署
- 设计日志留存策略
- 设计失败告警策略
- 设计多时区调度策略

边界：

- Scheduler 只允许触发研究链路
- 不允许触发交易链路

## Phase 37：数据源增强

目标：

- 明确 IBKR 数据可用性
- 明确 JP / CN / US 市场数据差异
- 增加 fallback 规则说明
- 增加 data_status 质量标记
- 区分 real_time / delayed / inferred / unavailable

边界：

- 数据增强不等于交易授权
- 数据请求必须受安全配置约束

## Phase 38：策略解释层增强

目标：

- 强化 final research trading plan 的解释能力
- 增加短期 / 中期 / 长期分层
- 增加风险触发条件
- 增加人工复核 checklist
- 增加失效条件说明

边界：

- 输出仍是研究计划
- 不生成自动订单

## Phase 39：只读实盘数据准入

目标：

- 仅在所有安全 gate 通过后评估
- 明确 read-only
- 明确无交易权限
- 明确无下单路径
- 明确无 cancel 路径

边界：

- 不允许 placeOrder
- 不允许 cancelOrder
- 不允许 auto trade

## Phase 40：个人自用应用 UI 评估

目标：

- 评估本地 Web UI
- 评估 Streamlit
- 评估 FastAPI
- 评估 React 前端
- 显示报告、日志、Telegram-ready 文本

边界：

- UI 只展示和辅助复核
- 不内置自动交易
- 不内置自动下单
