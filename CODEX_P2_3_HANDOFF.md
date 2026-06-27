# Codex P2.3 Handoff

当前远端 main 暂未看到 `0d15d9a` 与 `scripts/build_visual_result_dashboard.py`，因此本包按“本地最新 P2.1/P2.2 已存在”的方式给出最小补丁。

## Apply

1. 复制 `scripts/build_visual_result_dashboard_readable.py` 到仓库同路径。
2. 复制 `tests/test_visual_dashboard_readability_p2_3.py` 到仓库同路径。
3. 修改 `scripts/run_daily_workflow_with_quality_backfill.py`：

```python
python3 scripts/build_visual_result_dashboard.py
python3 scripts/build_visual_result_dashboard_readable.py
python3 scripts/build_viewer_index.py
```

等价地，若 wrapper 使用 `subprocess.run([...])`，就在现有 dashboard 构建步骤之后插入：

```python
run_step("p2_3_readable_dashboard", [sys.executable, "scripts/build_visual_result_dashboard_readable.py"])
```

## Scope

- 不新增行情采集器。
- 不新增预测引擎。
- 不读取账户、仓位、现金或保证金。
- 不接入券商接口。
- 不生成目标价、止损、止盈、仓位建议。
- 不绕过 `asset_eligibility / data_vintage / sample_quality / interval_status`。

## Expected result

`reports/latest_dashboard.html` 顶部应出现：

- 今日整体状态
- 可判断资产数
- 暂不可判断资产数
- 数据警告数量
- 样本不足数量
- 区间异常数量

每个资产卡片应显示：

- 偏涨 / 偏跌 / 震荡 / 暂不可判断
- 短期 / 中期 / 长期
- P10 / P50 / P90
- 四大门控
- 1-3 条不可判断原因

`sample_quality=watch_only` 必须显示 `暂不可判断`。
`interval_status=unstable_distribution` 或 `blocked_too_wide` 必须显示区间风险。

## Local validation for Codex

```bash
python3 -m py_compile scripts/build_visual_result_dashboard_readable.py
python3 -m unittest tests.test_visual_dashboard_readability_p2_3 -v
python3 scripts/build_visual_result_dashboard_readable.py --allow-missing-input
```

Full validation after merging into the latest local P2.1/P2.2 worktree:

```bash
python3 -m py_compile scripts/build_visual_result_dashboard.py scripts/build_visual_result_dashboard_readable.py scripts/run_daily_workflow_with_quality_backfill.py
python3 -m unittest discover -s tests
python3 scripts/run_daily_workflow_with_quality_backfill.py
ls -l reports/latest_dashboard.html work/visual_result.json outputs/index.html
```
