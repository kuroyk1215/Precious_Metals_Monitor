# P2.3-P2.7 Minimal Development Plan

## Current handoff state

Remote main visible to ChatGPT did not expose `0d15d9a` or `scripts/build_visual_result_dashboard.py` at the time this handoff was prepared. This plan therefore avoids direct main modification and provides a minimal drop-in layer for the local P2.1/P2.2 worktree.

## Non-negotiable scope

- Do not add order placement, cancellation, or modification.
- Do not add account, position, cash, margin, or broker reads.
- Do not add broker integrations.
- Do not add target price, stop loss, take profit, position sizing, or account-level risk modules.
- Do not add automated trading plans.
- Do not add a new prediction engine.
- Do not add a new market data collector except a read-only adapter for existing artifacts.
- Do not bypass `asset_eligibility`, `data_vintage_ledger`, `sample_quality`, or `interval_status`.
- Do not treat `quality_filter_effect`, `metals_multihorizon_review`, or `visual_result` as a trade signal or publishing permission.

## P2.3 Visual readability optimization

Minimal files:

```text
scripts/build_visual_result_dashboard_readable.py
tests/test_visual_dashboard_readability_p2_3.py
```

Expected wrapper insertion after the existing P2.1 visual JSON/dashboard build:

```python
run_step("p2_1_visual_dashboard", [sys.executable, "scripts/build_visual_result_dashboard.py"])
run_step("p2_3_readable_dashboard", [sys.executable, "scripts/build_visual_result_dashboard_readable.py"])
run_step("viewer_index", [sys.executable, "scripts/build_viewer_index.py"])
```

The P2.3 layer reads `work/visual_result.json` and rewrites `reports/latest_dashboard.html` into a more readable daily terminal.

Required page features:

- Top summary: total assets, judgable assets, unavailable assets, data warnings, sample blocks, interval blocks.
- Gold / GLD and Silver / SLV cards.
- Short / medium / long horizon sections.
- P10 / P50 / P90 lightweight SVG box visual.
- One to three fail-closed reasons.
- `sample_quality=watch_only` must be blocked.
- `interval_status=unstable_distribution` or `blocked_too_wide` must display interval risk.

## P2.4 Watchlist visual layer

Minimal future files:

```text
scripts/build_equity_visual_result_adapter.py
tests/test_equity_visual_adapter.py
```

Only read existing artifacts:

- `config/watchlist.json`
- `equity_prediction_review`
- equity logs
- `quality_filter_effect`
- `quality_run_manifest`
- `chatgpt_research_packet`

Do not add a stock prediction engine, market collector, broker interface, target/stop/take-profit, or position advice.

Output fields per stock/ETF:

- asset name / code / market
- direction state: 偏涨 / 偏跌 / 震荡 / 暂不可判断
- 1d / 5d / 20d state
- data quality state
- confidence adjustment
- sample_quality
- interval_status
- unavailable reasons

## P2.5 Daily command center

Extend the existing P2.3 summary, not a new engine.

Additional summary fields:

- total assets
- judgable count
- unavailable count
- expired / missing / delayed data count
- sample insufficient count
- interval abnormal count
- ChatGPT degraded state

Allowed top hints:

- 今日可参考
- 仅低置信参考
- 大部分暂不可判断
- 数据质量不足，建议等待下一次刷新

The hint must only derive from quality gates and existing research artifacts.

## P2.6 ChatGPT summary compression

Per asset, display at most:

```json
{
  "direction_summary": "...",
  "quality_summary": "...",
  "risk_summary": "..."
}
```

If OpenAI analysis is missing or degraded, show:

```text
ChatGPT 研判未通过或未生成，仅展示规则与质量门控结果
```

Do not let ChatGPT content override gates or become publishing/trading permission.

## P2.7 Stability closeout

Wrapper requirements:

- One daily run refreshes:
  - `reports/latest_dashboard.html`
  - `work/visual_result.json`
  - `outputs/index.html`
- On failure:
  - return non-zero
  - print failed step
  - do not present old HTML as a fresh page
- Use temp output plus atomic replace where practical.
- README must document the daily command.
- Tests must cover major failure paths.

Validation:

```bash
python3 -m py_compile scripts/build_visual_result_dashboard.py scripts/build_visual_result_dashboard_readable.py scripts/run_daily_workflow_with_quality_backfill.py
python3 -m unittest discover -s tests
python3 scripts/build_visual_result_dashboard.py
python3 scripts/build_visual_result_dashboard_readable.py
python3 scripts/build_viewer_index.py
python3 scripts/run_daily_workflow_with_quality_backfill.py
```

Smoke scan:

```bash
python3 - <<'PY'
from pathlib import Path
html = Path('reports/latest_dashboard.html').read_text(encoding='utf-8')
required = ['今日整体状态','可判断资产数','暂不可判断资产数','数据警告数量','样本不足数量','区间异常数量','Gold / GLD','Silver / SLV','P10','P50','P90']
missing = [x for x in required if x not in html]
assert not missing, missing
for forbidden in ['目标价','止损','止盈','仓位建议','下单','撤单','改单']:
    assert forbidden not in html, forbidden
print('P2.3 html smoke passed')
PY
```
