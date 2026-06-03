from __future__ import annotations

import argparse
import csv
from dataclasses import dataclass
from datetime import datetime, timezone
from pathlib import Path
from typing import Dict, List, Optional, Sequence, Tuple, Union
from zoneinfo import ZoneInfo


SYMBOLS = ("GLD", "SLV")
MARKET = "US"

DATA_DELAY_FLAGS = ("real_time", "delayed", "frozen", "no_price", "source_conflict")
CONFIDENCE_VALUES = ("high", "medium", "low")

CSV_FIELDS = (
    "date_jst",
    "market",
    "symbol",
    "strategy",
    "price",
    "source",
    "data_delay_flag",
    "signal",
    "entry_zone",
    "exit_zone",
    "stop_loss",
    "time_trigger",
    "event_trigger",
    "risk_pct",
    "confidence",
    "action_allowed",
    "result",
    "notes",
)

PathLike = Union[str, Path]


@dataclass(frozen=True)
class QuoteState:
    symbol: str
    price: Optional[float]
    source: str
    data_delay_flag: str
    confidence: str
    action_allowed: str
    conflict_sources: str
    quote_time: str
    diagnostic_reason: str


def _now_utc() -> datetime:
    return datetime.now(timezone.utc).replace(microsecond=0)


def _read_rows(path: PathLike) -> List[Dict[str, str]]:
    csv_path = Path(path)
    if not csv_path.exists():
        return []
    with csv_path.open(newline="", encoding="utf-8") as f:
        return [{k: str(v or "") for k, v in row.items()} for row in csv.DictReader(f)]


def _symbol(row: Dict[str, str]) -> str:
    return str(row.get("symbol") or row.get("display_symbol") or "").strip().upper()


def _source(row: Dict[str, str]) -> str:
    return str(row.get("quote_source") or row.get("source") or "unknown").strip() or "unknown"


def _price(row: Dict[str, str]) -> Optional[float]:
    for field in ("last_price", "price", "close", "bid", "ask"):
        raw = str(row.get(field, "")).strip()
        if not raw:
            continue
        try:
            value = float(raw)
        except ValueError:
            continue
        if value > 0:
            return value
    return None


def _contains_any(text: str, values: Sequence[str]) -> bool:
    lowered = text.lower()
    return any(value in lowered for value in values)


def _has_source_conflict(rows: Sequence[Dict[str, str]]) -> bool:
    priced = [row for row in rows if _price(row) is not None]
    if len(priced) < 2:
        return False
    prices = {round(float(_price(row) or 0.0), 4) for row in priced}
    statuses = {
        str(row.get("data_delay_flag") or row.get("data_status") or row.get("staleness_status") or "").strip().lower()
        for row in priced
    }
    statuses.discard("")
    sources = {_source(row) for row in priced}
    return len(sources) > 1 and (len(prices) > 1 or len(statuses) > 1)


def _classify_delay(rows: Sequence[Dict[str, str]]) -> Tuple[str, Optional[float], str, str]:
    if not rows:
        return "no_price", None, "missing_source", "no quote rows found"
    if _has_source_conflict(rows):
        priced_rows = [row for row in rows if _price(row) is not None]
        source_text = ";".join(f"{_source(row)}={_price(row)}" for row in priced_rows)
        return "source_conflict", _price(priced_rows[-1]) if priced_rows else None, source_text, "conflicting source prices or statuses"

    latest = rows[-1]
    price = _price(latest)
    source = _source(latest)
    status_text = " ".join(
        str(latest.get(field, ""))
        for field in ("data_delay_flag", "data_status", "staleness_status", "quote_status", "normalized_status", "diagnostic_category")
    )
    if price is None:
        return "no_price", None, source, latest.get("diagnostic_reason") or "no valid positive price"
    if _contains_any(status_text, ("conflict",)):
        return "source_conflict", price, source, latest.get("diagnostic_reason") or "source conflict status supplied"
    if _contains_any(status_text, ("frozen",)):
        return "frozen", price, source, latest.get("diagnostic_reason") or "frozen quote"
    if _contains_any(status_text, ("delayed", "stale")):
        return "delayed", price, source, latest.get("diagnostic_reason") or "delayed quote"
    if _contains_any(status_text, ("real_time", "realtime", "live", "available", "normalized")):
        return "real_time", price, source, latest.get("diagnostic_reason") or "real-time quote accepted"
    return "delayed", price, source, latest.get("diagnostic_reason") or "unknown freshness treated as delayed"


def _confidence(flag: str) -> str:
    if flag == "real_time":
        return "high"
    if flag == "delayed":
        return "low"
    return "low"


def _action_allowed(flag: str) -> str:
    return "true" if flag in {"real_time", "delayed"} else "false"


def _price_text(price: Optional[float]) -> str:
    return "" if price is None else f"{price:.2f}"


def _zone(price: Optional[float], low: float, high: float) -> str:
    if price is None:
        return "等待有效报价"
    return f"{price * low:.2f}-{price * high:.2f}"


def _signal(flag: str) -> str:
    return {
        "real_time": "人工研究计划可用",
        "delayed": "仅观察或低置信计划",
        "frozen": "仅参考，不行动",
        "no_price": "不交易，等待有效报价",
        "source_conflict": "数据源冲突，降级复核",
    }[flag]


def _result(flag: str) -> str:
    if flag == "real_time":
        return "正常研究计划"
    if flag == "delayed":
        return "降级为观察/低置信计划"
    if flag == "frozen":
        return "仅参考"
    if flag == "source_conflict":
        return "降级并复核冲突来源"
    return "不交易，等待有效报价"


def _strategy(symbol: str, flag: str) -> str:
    if flag == "real_time":
        return f"{symbol} 1-5日人工观察计划"
    if flag == "delayed":
        return f"{symbol} 延迟报价低置信观察"
    if flag == "frozen":
        return f"{symbol} 冻结报价参考框架"
    if flag == "source_conflict":
        return f"{symbol} 数据冲突复核框架"
    return f"{symbol} 无有效报价等待"


def build_quote_states(
    *,
    quote_csv: PathLike = "operator_real_quote_normalization.csv",
    symbols: Sequence[str] = SYMBOLS,
) -> List[QuoteState]:
    source_rows = _read_rows(quote_csv)
    rows_by_symbol: Dict[str, List[Dict[str, str]]] = {symbol: [] for symbol in symbols}
    for row in source_rows:
        symbol = _symbol(row)
        if symbol in rows_by_symbol:
            rows_by_symbol[symbol].append(row)

    states: List[QuoteState] = []
    for symbol in symbols:
        rows = rows_by_symbol.get(symbol, [])
        flag, price, source, reason = _classify_delay(rows)
        latest = rows[-1] if rows else {}
        states.append(
            QuoteState(
                symbol=symbol,
                price=price,
                source=source,
                data_delay_flag=flag,
                confidence=_confidence(flag),
                action_allowed=_action_allowed(flag),
                conflict_sources=source if flag == "source_conflict" else "",
                quote_time=latest.get("quote_time", ""),
                diagnostic_reason=reason,
            )
        )
    return states


def build_log_rows(states: Sequence[QuoteState], *, generated_at: Optional[datetime] = None) -> List[Dict[str, str]]:
    now = generated_at or _now_utc()
    date_jst = now.astimezone(ZoneInfo("Asia/Tokyo")).date().isoformat()
    rows: List[Dict[str, str]] = []
    for state in states:
        price = state.price
        notes = state.diagnostic_reason
        if state.data_delay_flag == "source_conflict":
            notes = f"{notes}; conflict_sources={state.conflict_sources}"
        rows.append(
            {
                "date_jst": date_jst,
                "market": MARKET,
                "symbol": state.symbol,
                "strategy": _strategy(state.symbol, state.data_delay_flag),
                "price": _price_text(price),
                "source": state.source,
                "data_delay_flag": state.data_delay_flag,
                "signal": _signal(state.data_delay_flag),
                "entry_zone": _zone(price, 0.985, 0.998),
                "exit_zone": _zone(price, 1.025, 1.055),
                "stop_loss": _zone(price, 0.965, 0.965),
                "time_trigger": "1-5个交易日复核；2-8周更新中期框架；3-12个月重估长期假设",
                "event_trigger": "美元实际利率、DXY、实际收益率、ETF资金流、地缘风险、金银比异常",
                "risk_pct": "0.25-0.75" if state.action_allowed == "true" else "0",
                "confidence": state.confidence,
                "action_allowed": state.action_allowed,
                "result": _result(state.data_delay_flag),
                "notes": notes,
            }
        )
    return rows


def write_log_csv(path: PathLike, rows: Sequence[Dict[str, str]]) -> None:
    output_path = Path(path)
    output_path.parent.mkdir(parents=True, exist_ok=True)
    with output_path.open("w", newline="", encoding="utf-8") as f:
        writer = csv.DictWriter(f, fieldnames=list(CSV_FIELDS), lineterminator="\n")
        writer.writeheader()
        writer.writerows(rows)


def _report_row_lines(rows: Sequence[Dict[str, str]]) -> List[str]:
    lines: List[str] = []
    for row in rows:
        lines.append(
            f"- {row['symbol']}: price={row['price'] or 'N/A'}; source={row['source']}; data_delay_flag={row['data_delay_flag']}; confidence={row['confidence']}; action_allowed={row['action_allowed']}; signal={row['signal']}"
        )
    return lines


def build_markdown_report(rows: Sequence[Dict[str, str]], *, generated_at: Optional[datetime] = None) -> str:
    now = generated_at or _now_utc()
    jst = now.astimezone(ZoneInfo("Asia/Tokyo")).isoformat()
    et = now.astimezone(ZoneInfo("America/New_York")).isoformat()
    flags = ", ".join(DATA_DELAY_FLAGS)
    confidences = ", ".join(CONFIDENCE_VALUES)
    return "\n".join(
        [
            "# GLD/SLV Core Research Loop",
            "",
            "## 安全边界",
            "",
            "- scope: GLD / SLV only",
            "- 不新增市场，不新增股票池",
            "- 不自动下单",
            "- 不读取账户持仓、账户资金或任何账户敏感字段",
            "- 输出仅用于研究、日志、数据质量闸门和测试",
            "",
            "## 一致预期",
            "",
            "- 黄金与白银 ETF 的核心驱动仍是美元实际利率、美元指数、通胀预期、避险需求与 ETF 资金流。",
            "- GLD 更偏黄金 beta 与宏观避险，SLV 波动更高且受工业需求与金银比扰动更明显。",
            "- 若报价非 real_time，所有计划必须降级；no_price 明确为不交易，等待有效报价。",
            "",
            "## 实时数据",
            "",
            f"- generated_jst: {jst}",
            f"- generated_et: {et}",
            f"- supported_data_delay_flag: {flags}",
            f"- supported_confidence: {confidences}",
            *_report_row_lines(rows),
            "",
            "## 既有认知",
            "",
            "- 研究框架保留为人工执行前的观察清单，不形成自动化执行指令。",
            "- GLD/SLV 只在有效报价、低冲突、人工复核通过后进入下一步计划。",
            "",
            "## 短期策略：1-5 个交易日",
            "",
            "- real_time: 可使用正常人工研究计划，关注回撤买点、反弹减仓点与失效位。",
            "- delayed: 仅观察或低置信计划，等待开盘/报价刷新后复核。",
            "- frozen/source_conflict/no_price: 不行动化，仅记录风险与等待条件。",
            "",
            "## 中期策略：2-8 周",
            "",
            "- 以实际利率趋势、DXY方向、ETF流入流出与金银比为主线。",
            "- 若 SLV 相对 GLD 强弱出现异常，优先复核白银工业需求与流动性风险。",
            "",
            "## 长期策略：3-12 个月",
            "",
            "- GLD 关注降息路径、央行购金、美元信用与避险周期。",
            "- SLV 关注工业周期、库存、太阳能/电子需求与黄金白银相对估值。",
            "",
            "## 今日买点",
            "",
            *[f"- {row['symbol']}: {row['entry_zone']}；{row['signal']}" for row in rows],
            "",
            "## 今日卖点",
            "",
            *[f"- {row['symbol']}: {row['exit_zone']}；若风险事件反转或报价降级则暂停计划" for row in rows],
            "",
            "## 止损/失效位",
            "",
            *[f"- {row['symbol']}: {row['stop_loss']}；若 data_delay_flag={row['data_delay_flag']} 且 action_allowed={row['action_allowed']}，按降级规则执行" for row in rows],
            "",
            "## IBKR 现金账户约束",
            "",
            "- 现金账户只按 settled cash 做人工复核；不得假设可用未结算资金。",
            "- GFV / freeriding 风险：避免用未结算卖出资金再次买入并在结算前卖出。",
            "- 本报告不读取账户资金、持仓、position 或 account 字段。",
            "",
            "## ET / JST 时间窗口",
            "",
            "- ET: 美股盘前、常规交易时段、盘后分别记录；关键计划以常规时段有效报价为准。",
            "- JST: 次日清晨复盘 ET 收盘数据，盘中如仅有延迟/冻结数据则保持观察。",
            "",
            "## 风险与退出触发",
            "",
            "- 报价变为 no_price、frozen 或 source_conflict 时退出行动化计划。",
            "- 实际利率急升、DXY突破、ETF资金大幅流出、地缘风险快速降温会触发防守复核。",
            "- SLV 额外关注工业金属回落、流动性恶化与金银比快速反转。",
            "",
            "## 一致性对账单",
            "",
            *[f"- {row['symbol']}: data_delay_flag={row['data_delay_flag']}; confidence={row['confidence']}; action_allowed={row['action_allowed']}; result={row['result']}; notes={row['notes']}" for row in rows],
        ]
    ) + "\n"


def write_markdown_report(path: PathLike, rows: Sequence[Dict[str, str]], *, generated_at: Optional[datetime] = None) -> None:
    output_path = Path(path)
    output_path.parent.mkdir(parents=True, exist_ok=True)
    output_path.write_text(build_markdown_report(rows, generated_at=generated_at), encoding="utf-8")


def generate_batch1_research_loop(
    *,
    quote_csv: PathLike = "operator_real_quote_normalization.csv",
    output_report: PathLike = "reports/latest_gld_slv_research.md",
    output_csv: PathLike = "logs/research_log_US.csv",
    generated_at: Optional[datetime] = None,
) -> List[Dict[str, str]]:
    states = build_quote_states(quote_csv=quote_csv)
    rows = build_log_rows(states, generated_at=generated_at)
    write_log_csv(output_csv, rows)
    write_markdown_report(output_report, rows, generated_at=generated_at)
    return rows


def _build_arg_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description="Generate Batch 1 GLD/SLV core research loop outputs.")
    parser.add_argument("--quote-csv", default="operator_real_quote_normalization.csv")
    parser.add_argument("--output-report", default="reports/latest_gld_slv_research.md")
    parser.add_argument("--output-csv", default="logs/research_log_US.csv")
    return parser


def main(argv: Optional[Sequence[str]] = None) -> int:
    args = _build_arg_parser().parse_args(argv)
    rows = generate_batch1_research_loop(
        quote_csv=args.quote_csv,
        output_report=args.output_report,
        output_csv=args.output_csv,
    )
    print("[PASS] Batch 1 GLD/SLV research loop generated")
    for row in rows:
        print(
            f"{row['symbol']}:data_delay_flag={row['data_delay_flag']}:confidence={row['confidence']}:action_allowed={row['action_allowed']}"
        )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
