# 使用流程

## 1. 进入项目目录

    cd ~/Precious_Metals_Monitor

## 2. 检查工作区

    git status --short

允许存在但不得提交：

    M config.yaml
    ?? .venv/

不得提交：

    config.yaml
    .venv/

## 3. 检查测试

    PYTHONPATH=. pytest -q

当前 MVP 预期测试结果：

    428 passed

## 4. 准备输入文件

核心输入文件：

    primary_metals_config.yaml

该文件用于驱动 primary metals 主链路。

## 5. 执行主命令

    python main.py --report-template-daily-log-telegram-ready-output <primary_metals_config.yaml>

## 6. 检查输出

执行完成后检查：

- reports/
- daily log
- Markdown report
- Telegram-ready text
- final research trading plan

## 7. 人工复核

所有输出均为：

- research-only
- read-only
- manual-only
- no auto trade

输出不得直接等同于交易指令。

## 8. 人工执行

如需交易，必须由用户在外部交易终端中人工完成。

系统不连接自动下单链路，不执行任何订单行为。
