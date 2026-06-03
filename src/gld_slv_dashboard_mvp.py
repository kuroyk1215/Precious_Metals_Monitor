from __future__ import annotations

import argparse
import csv
from datetime import datetime, time, timezone
from html import escape
from pathlib import Path
from typing import Dict, List, Optional, Sequence, Tuple, Union
from zoneinfo import ZoneInfo


SYMBOLS = ("GLD", "SLV")
PathLike = Union[str, Path]


def _now() -> datetime:
    return datetime.now(timezone.utc).replace(microsecond=0)


def _read_csv_rows(path: PathLike) -> List[Dict[str, str]]:
    csv_path = Path(path)
    if not csv_path.exists():
        return []
    with csv_path.open(newline="", encoding="utf-8") as f:
        rows = [{k: str(v or "") for k, v in row.items()} for row in csv.DictReader(f)]
    return [row for row in rows if row.get("symbol", "").upper() in SYMBOLS]


def _read_report_summary(path: PathLike) -> str:
    report_path = Path(path)
    if not report_path.exists():
        return "no data available"
    lines = [line.strip() for line in report_path.read_text(encoding="utf-8").splitlines() if line.strip()]
    return " ".join(lines[:8]) if lines else "no data available"


def _fallback_row(symbol: str, summary: str) -> Dict[str, str]:
    return {
        "date_jst": "",
        "market": "US",
        "symbol": symbol,
        "strategy": "no data available",
        "price": "",
        "source": "reports/latest_gld_slv_research.md" if summary != "no data available" else "no data available",
        "data_delay_flag": "no_price",
        "signal": "no data available",
        "action_rating": "NO_TRADE",
        "entry_zone": "no data available",
        "exit_zone": "no data available",
        "stop_loss": "no data available",
        "invalidation_level": "no data available",
        "time_trigger": "no data available",
        "event_trigger": "no data available",
        "risk_pct": "0",
        "position_unit_note": "no data available",
        "cash_account_note": "IBKR cash account only; settled cash only; avoid GFV / freeriding",
        "overnight_allowed": "false",
        "review_required": "true",
        "confidence": "low",
        "action_allowed": "false",
        "result": "不交易，等待有效报价",
        "notes": summary,
    }


def load_dashboard_rows(
    *,
    csv_path: PathLike = "logs/research_log_US.csv",
    report_path: PathLike = "reports/latest_gld_slv_research.md",
) -> List[Dict[str, str]]:
    rows = _read_csv_rows(csv_path)
    by_symbol = {row.get("symbol", "").upper(): row for row in rows}
    summary = "" if rows else _read_report_summary(report_path)
    return [by_symbol.get(symbol) or _fallback_row(symbol, summary) for symbol in SYMBOLS]


def _value(row: Dict[str, str], field: str, default: str = "N/A") -> str:
    value = str(row.get(field, "")).strip()
    return value if value else default


def _price(row: Dict[str, str]) -> str:
    if row.get("data_delay_flag") == "no_price":
        return "N/A - no_price"
    return _value(row, "price")


def _risk_light(flag: str) -> str:
    return {
        "real_time": "real_time: research plan available",
        "delayed": "delayed: WATCH/C only, no strong action",
        "frozen": "frozen: reference only",
        "no_price": "no_price: not tradable",
        "source_conflict": "source_conflict: downgraded review",
    }.get(flag, "unknown: review required")


def _windows(now: datetime) -> List[Tuple[str, str, str]]:
    et_zone = ZoneInfo("America/New_York")
    jst_zone = ZoneInfo("Asia/Tokyo")
    et_date = now.astimezone(et_zone).date()
    items = (
        ("10:00 ET", "建仓观察", time(10, 0)),
        ("14:30 ET", "第一退出检查", time(14, 30)),
        ("15:10 ET", "第二退出检查", time(15, 10)),
        ("15:50 ET", "尾盘退出检查", time(15, 50)),
    )
    output: List[Tuple[str, str, str]] = []
    for et_label, note, et_time in items:
        et_dt = datetime.combine(et_date, et_time, tzinfo=et_zone)
        output.append((et_label, et_dt.astimezone(jst_zone).strftime("%H:%M JST"), note))
    return output


def _card(row: Dict[str, str]) -> str:
    symbol = escape(_value(row, "symbol"))
    fields = (
        ("price", _price(row)),
        ("source", _value(row, "source")),
        ("price_time", _value(row, "date_jst")),
        ("data_delay_flag", _value(row, "data_delay_flag")),
        ("confidence", _value(row, "confidence")),
        ("action_rating", _value(row, "action_rating")),
        ("action_allowed", _value(row, "action_allowed")),
        ("result", _value(row, "result")),
        ("notes", _value(row, "notes")),
    )
    strategy_fields = (
        "signal",
        "entry_zone",
        "exit_zone",
        "stop_loss",
        "invalidation_level",
        "time_trigger",
        "event_trigger",
        "risk_pct",
        "overnight_allowed",
        "review_required",
    )
    field_html = "\n".join(f"<div><dt>{escape(label)}</dt><dd>{escape(value)}</dd></div>" for label, value in fields)
    strategy_html = "\n".join(
        f"<div><dt>{escape(field)}</dt><dd>{escape(_value(row, field))}</dd></div>" for field in strategy_fields
    )
    flag = escape(_value(row, "data_delay_flag", "unknown"))
    return f"""
              <article class="symbol-card risk-{flag}">
                <div class="card-title"><h3>{symbol}</h3><span>US ETF research plan</span><strong>{escape(_risk_light(flag))}</strong></div>
                <dl>{field_html}</dl>
                <h4>策略字段</h4>
                <dl>{strategy_html}</dl>
              </article>"""


def build_dashboard_html(
    rows: Sequence[Dict[str, str]],
    *,
    generated_at: Optional[datetime] = None,
) -> str:
    now = generated_at or _now()
    jst = now.astimezone(ZoneInfo("Asia/Tokyo")).strftime("%Y-%m-%d %H:%M:%S JST")
    et = now.astimezone(ZoneInfo("America/New_York")).strftime("%Y-%m-%d %H:%M:%S ET")
    cards = "\n".join(_card(row) for row in rows)
    window_rows = "\n".join(
        f"<li><strong>{escape(et_label)}</strong><span>{escape(jst_label)}</span><em>{escape(note)}</em></li>"
        for et_label, jst_label, note in _windows(now)
    )
    reconciliation = "\n".join(
        f"<li>{escape(_value(row, 'symbol'))}: data_delay_flag={escape(_value(row, 'data_delay_flag'))}; action_rating={escape(_value(row, 'action_rating'))}; action_allowed={escape(_value(row, 'action_allowed'))}; result={escape(_value(row, 'result'))}</li>"
        for row in rows
    )
    return f"""<!doctype html>
<html lang="zh-CN">
  <head>
    <meta charset="utf-8">
    <meta name="viewport" content="width=device-width, initial-scale=1">
    <title>GLD/SLV Research Dashboard</title>
    <link rel="stylesheet" href="assets/style.css">
  </head>
  <body>
    <div class="app-shell">
      <aside class="sidebar" aria-label="左侧导航">
        <div class="brand">
          <span class="brand-mark">AI</span>
          <span class="brand-title">GLD/SLV Research Dashboard</span>
          <span class="brand-subtitle">本地只读研究平台</span>
        </div>
        <nav class="sidebar-nav" aria-label="投研导航">
          <a class="nav-item active" href="#overview"><span class="nav-index">01</span><span>总览</span></a>
          <a class="nav-item" href="#watch"><span class="nav-index">02</span><span>标的观察</span></a>
          <a class="nav-item" href="#data-source"><span class="nav-index">03</span><span>数据源</span></a>
          <a class="nav-item" href="#reports"><span class="nav-index">04</span><span>本地报告</span></a>
          <a class="nav-item" href="#risk"><span class="nav-index">05</span><span>风险边界</span></a>
          <a class="nav-item" href="#settings"><span class="nav-index">06</span><span>设置</span></a>
        </nav>
        <div class="sidebar-foot">Research Only</div>
      </aside>

      <div class="content">
        <header class="hero" id="overview">
          <div class="hero-copy">
            <span class="eyebrow">AI 投研工作台</span>
            <h1>GLD/SLV Research Dashboard</h1>
            <p class="subtitle">本地投研工作台已就绪 · GLD / SLV · Research Only · 自动交易 Disabled</p>
            <p>当前支持 GLD / SLV 研究框架；当前不会读取账户、持仓或发送交易指令。</p>
          </div>
          <div class="hero-panel">
            <span>平台状态</span>
            <strong>本地投研工作台已就绪</strong>
            <small>single ≤2%，daily ≤6%</small>
          </div>
        </header>

        <main class="dashboard-grid">
          <section class="status-strip" aria-label="顶部状态栏">
            <article><span>当前时间 JST</span><strong>{escape(jst)}</strong></article>
            <article><span>当前时间 ET</span><strong>{escape(et)}</strong></article>
            <article><span>模式</span><strong>Research Only</strong></article>
            <article><span>自动交易</span><strong>Disabled</strong></article>
            <article><span>风险原则</span><strong>single ≤2%，daily ≤6%</strong></article>
          </section>

          <section class="panel" id="watch">
            <div class="section-header">
              <div><span class="eyebrow">标的观察</span><h2>GLD / SLV</h2></div>
              <span class="pill">数据源状态：准备中</span>
            </div>
            <div class="symbol-grid">{cards}
            </div>
          </section>

          <section class="panel" id="data-source">
            <div class="section-header">
              <div><span class="eyebrow">数据源</span><h2>数据质量说明</h2></div>
              <span class="pill muted-pill">读取 logs/research_log_US.csv；当前未启用实时行情</span>
            </div>
            <div class="risk-light-grid">
              <article>real_time</article>
              <article>delayed</article>
              <article>frozen</article>
              <article>no_price</article>
              <article>source_conflict</article>
            </div>
            <p class="muted">no_price 必须显示为不可交易状态；delayed / frozen / source_conflict 只用于降级研究复核，不支持强动作。</p>
          </section>

          <section class="panel">
            <div class="section-header">
              <div><span class="eyebrow">US_30mEcho</span><h2>US_30mEcho 时间窗口</h2></div>
              <span class="pill muted-pill">ET / JST</span>
            </div>
            <ul class="time-window-list">{window_rows}</ul>
          </section>

          <section class="panel" id="reports">
            <div class="section-header">
              <div><span class="eyebrow">本地报告</span><h2>一致性对账单</h2></div>
              <span class="pill">GLD / SLV 研究框架</span>
            </div>
            <ul class="risk-copy">
              <li>数据质量说明：所有评级绑定 data_delay_flag 与 confidence。</li>
              <li>风险与退出触发：no_price、frozen、source_conflict 触发退出行动化计划。</li>
              <li>一致性对账单摘要</li>
              {reconciliation}
            </ul>
            <div class="report-grid">
              <a href="../logs/research_log_US.csv"><span>research_log_US.csv</span><small>优先数据源</small></a>
              <a href="../reports/latest_gld_slv_research.md"><span>latest_gld_slv_research.md</span><small>报告摘要 fallback</small></a>
              <a href="../reports/local_research_report_framework_GLD_SLV.md"><span>GLD / SLV 研究框架</span><small>本地只读</small></a>
            </div>
          </section>

          <section class="panel" id="risk">
            <div class="section-header">
              <div><span class="eyebrow">风险边界</span><h2>IBKR cash account only</h2></div>
              <span class="pill danger-pill">外部动作关闭</span>
            </div>
            <ul class="risk-copy">
              <li>IBKR cash account only</li>
              <li>settled cash only</li>
              <li>avoid GFV / freeriding</li>
              <li>research only, no automatic trading</li>
              <li>当前不会获取实时行情</li>
              <li>当前不会读取账户</li>
              <li>当前不会读取持仓</li>
              <li>当前不会生成交易指令</li>
              <li>当前不会发送 Telegram</li>
              <li>当前不会解冻 JP / CN</li>
              <li>未确认数据源前，不显示价格</li>
              <li>无有效价格时，不生成分析信号</li>
              <li>未确认条款前，不启用自动导入</li>
              <li>数据新鲜度未验证前，只生成研究框架</li>
            </ul>
          </section>

          <section class="panel settings-panel" id="settings">
            <div class="section-header">
              <div><span class="eyebrow">设置</span><h2>工作台设置</h2></div>
              <span class="pill muted-pill">普通视图默认启用</span>
            </div>
            <p class="muted">高级模式仅用于本地排查。默认折叠，不占用投研操作区。</p>
            <details class="developer-details">
              <summary>高级信息</summary>
              <div class="advanced-grid">
                <code>开发者状态</code>
                <code>终端兜底命令</code>
                <code>本地 API 状态</code>
                <code>artifact 调试信息</code>
                <code>安全状态码</code>
                <code>PRODUCTIZED_UI_USER_SURFACE_CLEANUP_READY</code>
                <code>PRODUCTIZED_UI_PUBLIC_DATA_INTAKE_READY</code>
                <code>UI_DRIVEN_LOCAL_RESEARCH_PLATFORM_MVP_READY</code>
                <code>BLOCKED_BY_SUBSCRIPTION</code>
                <code>IBKR_ERROR_10089</code>
                <code>GET_ONLY</code>
                <code>CLI fallback</code>
                <code>python3 main.py --final-product-ui-lock-pack</code>
                <code>source_connection_implemented=NO</code>
                <code>live_market_data_enabled=NO</code>
              </div>
              <p class="muted mono">generated_at_utc={escape(now.isoformat())}</p>
            </details>
          </section>
        </main>
      </div>
    </div>
    <footer class="readonly-footer">Research Only · 本地工作台 · 不连接行情源 · 不执行交易</footer>
  </body>
</html>
"""


def write_dashboard(path: PathLike, html: str) -> None:
    output_path = Path(path)
    output_path.parent.mkdir(parents=True, exist_ok=True)
    output_path.write_text(html, encoding="utf-8")


def generate_dashboard_mvp(
    *,
    csv_path: PathLike = "logs/research_log_US.csv",
    report_path: PathLike = "reports/latest_gld_slv_research.md",
    output_html: PathLike = "dashboard/index.html",
    generated_at: Optional[datetime] = None,
) -> List[Dict[str, str]]:
    rows = load_dashboard_rows(csv_path=csv_path, report_path=report_path)
    write_dashboard(output_html, build_dashboard_html(rows, generated_at=generated_at))
    return rows


def _build_arg_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description="Generate the GLD/SLV Research Dashboard MVP.")
    parser.add_argument("--csv-path", default="logs/research_log_US.csv")
    parser.add_argument("--report-path", default="reports/latest_gld_slv_research.md")
    parser.add_argument("--output-html", default="dashboard/index.html")
    return parser


def main(argv: Optional[Sequence[str]] = None) -> int:
    args = _build_arg_parser().parse_args(argv)
    rows = generate_dashboard_mvp(csv_path=args.csv_path, report_path=args.report_path, output_html=args.output_html)
    print("[PASS] GLD/SLV Research Dashboard MVP generated")
    for row in rows:
        print(f"{row.get('symbol')}:data_delay_flag={row.get('data_delay_flag')}:action_rating={row.get('action_rating')}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
