# 输入 / 输出文件说明

## 1. 核心输入

### primary_metals_config.yaml

用途：

- 定义 primary metals 观察对象
- 提供主市场推导所需配置
- 驱动研究计划生成
- 驱动 final review
- 驱动 final research trading plan
- 驱动 one-command orchestrator

注意：

- 不应提交真实敏感配置
- 不应提交本地 config.yaml
- 不应提交 .venv/

## 2. 核心命令

    python main.py --report-template-daily-log-telegram-ready-output <primary_metals_config.yaml>

## 3. 核心输出

### Markdown 报告

- 汇总研究结果
- 便于人工阅读
- 便于归档和复盘

### Daily Log

- 记录每日研究输出
- 形成历史轨迹
- 便于后续回溯

### Telegram-ready Text

- 生成适合 Telegram 发送的文本
- 当前属于 ready-output / stub 阶段
- 不代表已经完成真实 Telegram Bot 推送

### Final Research Trading Plan

- 汇总最终研究型交易计划
- 提供人工复核依据
- 不触发自动交易

## 4. 输出边界

所有输出均为：

- research-only
- read-only
- manual-only
- no auto trade

## 5. 不应进入 Git 的内容

不得提交：

- config.yaml
- .venv/

原因：

- config.yaml 可能包含本地配置或敏感信息
- .venv/ 是本地 Python 虚拟环境
- 两者均不属于项目源代码或文档交付物
