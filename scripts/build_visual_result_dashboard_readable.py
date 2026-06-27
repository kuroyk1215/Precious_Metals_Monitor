from __future__ import annotations

import argparse
import json
import math
from dataclasses import dataclass
from datetime import datetime, timezone
from html import escape
from pathlib import Path
from typing import Any, Dict, Iterable, List, Mapping, Optional, Sequence, Tuple, Union
from zoneinfo import ZoneInfo

PathLike = Union[str, Path]

PERIODS: Tuple[Tuple[str, str], ...] = (
    ("short", "短期"),
    ("medium", "中期"),
    ("long", "长期"),
)

DEFAULT_ASSETS: Tuple[Tuple[str, str], ...] = (
    ("Gold / GLD", "GLD"),
    ("Silver / SLV", "SLV"),
)

OK_TOKENS = (
    "ok",
    "pass",
    "passed",
    "eligible",
    "fresh",
    "valid",
    "stable",
    "normal",
    "available",
    "judgable",
    "sufficient",
    "ready",
    "true",
    "yes",
)
DATA_WARNING_TOKENS = (
    "stale",
    "expired",
    "missing",
    "delayed",
    "late",
    "frozen",
    "no_data",
    "no data",
    "unknown",
    "unavailable",
    "degraded",
    "warning",
    "warn",
)
SAMPLE_BLOCK_TOKENS = (
    "watch_only",
    "watch only",
    "insufficient",
    "too_small",
    "small_sample",
    "low_sample",
    "low sample",
    "sparse",
    "blocked",
    "degraded",
    "fail",
    "failed",
    "missing",
    "unknown",
)
INTERVAL_BLOCK_TOKENS = (
    "unstable_distribution",
    "blocked_too_wide",
    "too_wide",
    "wide",
    "unstable",
    "invalid",
    "blocked",
    "fail",
    "failed",
    "missing",
    "unknown",
)
UP_TOKENS = ("偏涨", "上涨", "上行", "看涨", "up", "upside", "positive", "rise", "rising", "bull")
DOWN_TOKENS = ("偏跌", "下跌", "下行", "看跌", "down", "downside", "negative", "fall", "falling", "bear")
NEUTRAL_TOKENS = ("震荡", "中性", "横盘", "neutral", "range", "sideways", "flat", "mixed")


@dataclass(frozen=True)
class GateState:
    asset_ok: bool
    data_warning: bool
    sample_blocked: bool
    interval_blocked: bool
    reasons: Tuple[str, ...]

    @property
    def judgable(self) -> bool:
        return self.asset_ok and not self.data_warning and not self.sample_blocked and not self.interval_blocked


@dataclass(frozen=True)
class PeriodView:
    key: str
    label: str
    direction: str
    p10: Optional[float]
    p50: Optional[float]
    p90: Optional[float]
    raw: Mapping[str, Any]


@dataclass(frozen=True)
class AssetView:
    name: str
    symbol: str
    market: str
    direction: str
    gate: GateState
    periods: Tuple[PeriodView, ...]
    asset_eligibility: str
    data_vintage: str
    sample_quality: str
    interval_status: str
    raw: Mapping[str, Any]


def _now() -> datetime:
    return datetime.now(timezone.utc).replace(microsecond=0)


def _read_json(path: PathLike) -> Any:
    with Path(path).open("r", encoding="utf-8") as f:
        return json.load(f)


def _text(value: Any, *, default: str = "") -> str:
    if value is None:
        return default
    if isinstance(value, bool):
        return "true" if value else "false"
    if isinstance(value, (dict, list, tuple)):
        try:
            return json.dumps(value, ensure_ascii=False, sort_keys=True)
        except TypeError:
            return str(value)
    text = str(value).strip()
    return text if text else default


def _compact_text(value: Any, *, max_len: int = 72) -> str:
    text = " ".join(_text(value, default="unknown").split())
    return text if len(text) <= max_len else text[: max_len - 1] + "…"


def _lookup(mapping: Mapping[str, Any], keys: Sequence[str], default: Any = "") -> Any:
    for key in keys:
        if key in mapping and mapping[key] not in (None, ""):
            return mapping[key]
    return default


def _nested_status(value: Any) -> str:
    if isinstance(value, Mapping):
        return _compact_text(
            _lookup(
                value,
                ("status", "state", "gate", "result", "quality", "label", "value", "reason"),
                value,
            )
        )
    return _compact_text(value)


def _contains_any(value: Any, tokens: Sequence[str]) -> bool:
    text = _text(value).lower()
    return any(token.lower() in text for token in tokens)


def _is_positive_gate(value: Any) -> bool:
    if value is True:
        return True
    if value is False or value is None:
        return False
    text = _text(value).lower()
    return bool(text) and any(token in text for token in OK_TOKENS) and not any(
        token in text for token in ("not_", "not ", "false", "fail", "blocked", "ineligible", "unavailable")
    )


def _as_float(value: Any) -> Optional[float]:
    if value is None or value == "":
        return None
    if isinstance(value, bool):
        return None
    if isinstance(value, (int, float)):
        if math.isfinite(float(value)):
            return float(value)
        return None
    raw = str(value).strip().replace(",", "")
    if raw.endswith("%"):
        raw = raw[:-1]
    try:
        number = float(raw)
    except ValueError:
        return None
    return number if math.isfinite(number) else None


def _extract_assets(data: Any) -> List[Mapping[str, Any]]:
    if isinstance(data, list):
        return [item for item in data if isinstance(item, Mapping)]
    if not isinstance(data, Mapping):
        return []

    for key in ("assets", "asset_results", "visual_assets", "items", "rows", "results"):
        value = data.get(key)
        if isinstance(value, list):
            return [item for item in value if isinstance(item, Mapping)]
        if isinstance(value, Mapping):
            assets: List[Mapping[str, Any]] = []
            for symbol, item in value.items():
                if isinstance(item, Mapping):
                    merged = dict(item)
                    merged.setdefault("symbol", str(symbol))
                    assets.append(merged)
            return assets

    if any(key in data for key in ("symbol", "asset", "asset_name", "name", "ticker")):
        return [data]

    for value in data.values():
        if isinstance(value, list) and any(isinstance(item, Mapping) for item in value):
            return [item for item in value if isinstance(item, Mapping)]
    return []


def _asset_gate(asset: Mapping[str, Any]) -> GateState:
    eligibility = _lookup(asset, ("asset_eligibility", "eligibility", "eligible", "asset_gate"), "unknown")
    data_vintage = _lookup(asset, ("data_vintage", "data_vintage_status", "vintage", "freshness", "data_quality"), "unknown")
    sample_quality = _lookup(asset, ("sample_quality", "sample_status", "sample_gate", "sample"), "unknown")
    interval_status = _lookup(asset, ("interval_status", "interval_gate", "distribution_status", "interval_quality"), "unknown")

    eligibility_text = _nested_status(eligibility)
    data_text = _nested_status(data_vintage)
    sample_text = _nested_status(sample_quality)
    interval_text = _nested_status(interval_status)

    asset_ok = _is_positive_gate(eligibility)
    data_warning = not _is_positive_gate(data_vintage) or _contains_any(data_vintage, DATA_WARNING_TOKENS)
    sample_blocked = not _is_positive_gate(sample_quality) or _contains_any(sample_quality, SAMPLE_BLOCK_TOKENS)
    interval_blocked = not _is_positive_gate(interval_status) or _contains_any(interval_status, INTERVAL_BLOCK_TOKENS)

    reasons: List[str] = []
    if not asset_ok:
        reasons.append(f"资产门控未通过：{eligibility_text}")
    if data_warning:
        reasons.append(f"数据警告：{data_text}")
    if sample_blocked:
        if _contains_any(sample_quality, ("watch_only", "watch only")):
            reasons.append("样本仅观察：不得输出正常方向判断")
        else:
            reasons.append(f"样本不足：{sample_text}")
    if interval_blocked:
        if _contains_any(interval_status, ("unstable_distribution", "unstable")):
            reasons.append("区间风险：分布不稳定")
        elif _contains_any(interval_status, ("blocked_too_wide", "too_wide", "wide")):
            reasons.append("区间风险：区间过宽")
        else:
            reasons.append(f"区间异常：{interval_text}")

    return GateState(asset_ok=asset_ok, data_warning=data_warning, sample_blocked=sample_blocked, interval_blocked=interval_blocked, reasons=tuple(reasons[:3]))


def _period_mapping(asset: Mapping[str, Any]) -> Mapping[str, Any]:
    for key in ("horizons", "periods", "timeframes", "windows", "multihorizon", "multi_horizon"):
        value = asset.get(key)
        if isinstance(value, Mapping):
            return value
    return asset


def _resolve_period(raw_periods: Mapping[str, Any], key: str) -> Mapping[str, Any]:
    aliases = {
        "short": ("short", "short_term", "短期", "1d", "1D", "near"),
        "medium": ("medium", "medium_term", "mid", "中期", "5d", "5D"),
        "long": ("long", "long_term", "长期", "20d", "20D"),
    }[key]
    for alias in aliases:
        value = raw_periods.get(alias)
        if isinstance(value, Mapping):
            return value
    return {}


def _extract_quantiles(period: Mapping[str, Any]) -> Tuple[Optional[float], Optional[float], Optional[float]]:
    p10 = _as_float(_lookup(period, ("p10", "P10", "q10", "quantile_10", "lower", "low"), None))
    p50 = _as_float(_lookup(period, ("p50", "P50", "q50", "median", "mid", "base"), None))
    p90 = _as_float(_lookup(period, ("p90", "P90", "q90", "quantile_90", "upper", "high"), None))
    return p10, p50, p90


def _infer_direction_from_text(value: Any) -> Optional[str]:
    text = _text(value).lower()
    if not text:
        return None
    if any(token.lower() in text for token in UP_TOKENS):
        return "偏涨"
    if any(token.lower() in text for token in DOWN_TOKENS):
        return "偏跌"
    if any(token.lower() in text for token in NEUTRAL_TOKENS):
        return "震荡"
    if "temporarily_unavailable" in text or "暂不可判断" in text or "unavailable" in text or "blocked" in text:
        return "暂不可判断"
    return None


def _infer_period_direction(period: Mapping[str, Any]) -> str:
    for key in ("direction_status", "direction", "bias", "trend", "status", "judgement", "view"):
        direction = _infer_direction_from_text(period.get(key))
        if direction:
            return direction

    p50_return = _as_float(
        _lookup(
            period,
            ("p50_return", "return_p50", "median_return", "p50_pct", "median_pct", "expected_return"),
            None,
        )
    )
    if p50_return is not None:
        if p50_return > 0:
            return "偏涨"
        if p50_return < 0:
            return "偏跌"
    return "震荡"


def _build_periods(asset: Mapping[str, Any], gate: GateState) -> Tuple[PeriodView, ...]:
    raw_periods = _period_mapping(asset)
    periods: List[PeriodView] = []
    for key, label in PERIODS:
        period = _resolve_period(raw_periods, key)
        p10, p50, p90 = _extract_quantiles(period)
        direction = "暂不可判断" if not gate.judgable else _infer_period_direction(period)
        periods.append(PeriodView(key=key, label=label, direction=direction, p10=p10, p50=p50, p90=p90, raw=period))
    return tuple(periods)


def _overall_direction(gate: GateState, periods: Sequence[PeriodView], asset: Mapping[str, Any]) -> str:
    if not gate.judgable:
        return "暂不可判断"
    for key in ("direction_status", "direction", "bias", "trend", "status", "judgement", "view"):
        direction = _infer_direction_from_text(asset.get(key))
        if direction and direction != "暂不可判断":
            return direction
    votes = [period.direction for period in periods if period.direction in ("偏涨", "偏跌", "震荡")]
    if not votes:
        return "震荡"
    for candidate in ("偏涨", "偏跌", "震荡"):
        if votes.count(candidate) >= 2:
            return candidate
    return votes[0]


def _normalize_asset(asset: Mapping[str, Any]) -> AssetView:
    name = _compact_text(_lookup(asset, ("asset_name", "asset", "name", "display_name"), "Unknown Asset"), max_len=40)
    symbol = _compact_text(_lookup(asset, ("symbol", "ticker", "code"), name), max_len=18)
    market = _compact_text(_lookup(asset, ("market", "exchange", "asset_class"), "Metals"), max_len=20)
    gate = _asset_gate(asset)
    periods = _build_periods(asset, gate)
    direction = _overall_direction(gate, periods, asset)
    return AssetView(
        name=name,
        symbol=symbol,
        market=market,
        direction=direction,
        gate=gate,
        periods=periods,
        asset_eligibility=_nested_status(_lookup(asset, ("asset_eligibility", "eligibility", "eligible", "asset_gate"), "unknown")),
        data_vintage=_nested_status(_lookup(asset, ("data_vintage", "data_vintage_status", "vintage", "freshness", "data_quality"), "unknown")),
        sample_quality=_nested_status(_lookup(asset, ("sample_quality", "sample_status", "sample_gate", "sample"), "unknown")),
        interval_status=_nested_status(_lookup(asset, ("interval_status", "interval_gate", "distribution_status", "interval_quality"), "unknown")),
        raw=asset,
    )


def load_asset_views(path: PathLike, *, allow_missing: bool = False) -> Tuple[List[AssetView], bool]:
    json_path = Path(path)
    if not json_path.exists():
        if not allow_missing:
            placeholder = [
                _normalize_asset(
                    {
                        "asset_name": name,
                        "symbol": symbol,
                        "asset_eligibility": "missing visual_result.json",
                        "data_vintage": "missing",
                        "sample_quality": "unknown",
                        "interval_status": "unknown",
                    }
                )
                for name, symbol in DEFAULT_ASSETS
            ]
            return placeholder, False
        return [], False
    data = _read_json(json_path)
    raw_assets = _extract_assets(data)
    if not raw_assets:
        raw_assets = [
            {
                "asset_name": name,
                "symbol": symbol,
                "asset_eligibility": "no asset rows",
                "data_vintage": "missing",
                "sample_quality": "unknown",
                "interval_status": "unknown",
            }
            for name, symbol in DEFAULT_ASSETS
        ]
    return [_normalize_asset(asset) for asset in raw_assets], True


def _summary_counts(assets: Sequence[AssetView]) -> Dict[str, int]:
    return {
        "total": len(assets),
        "judgable": sum(1 for asset in assets if asset.gate.judgable),
        "unavailable": sum(1 for asset in assets if not asset.gate.judgable),
        "data_warnings": sum(1 for asset in assets if asset.gate.data_warning),
        "sample_blocks": sum(1 for asset in assets if asset.gate.sample_blocked),
        "interval_blocks": sum(1 for asset in assets if asset.gate.interval_blocked),
    }


def _class_for_direction(direction: str) -> str:
    return {
        "偏涨": "up",
        "偏跌": "down",
        "震荡": "neutral",
        "暂不可判断": "blocked",
    }.get(direction, "neutral")


def _fmt(value: Optional[float]) -> str:
    if value is None:
        return "—"
    if abs(value) >= 100:
        return f"{value:,.2f}"
    if abs(value) >= 1:
        return f"{value:.3f}".rstrip("0").rstrip(".")
    return f"{value:.4f}".rstrip("0").rstrip(".")


def _box_svg(period: PeriodView) -> str:
    values = [value for value in (period.p10, period.p50, period.p90) if value is not None]
    if len(values) < 3:
        return '<div class="quantile-missing">P10 / P50 / P90 暂无完整数据</div>'
    p10, p50, p90 = period.p10, period.p50, period.p90
    assert p10 is not None and p50 is not None and p90 is not None
    lo = min(p10, p50, p90)
    hi = max(p10, p50, p90)
    if math.isclose(lo, hi):
        lo -= 1
        hi += 1
    def x(value: float) -> float:
        return 10 + (value - lo) / (hi - lo) * 180
    x10, x50, x90 = x(p10), x(p50), x(p90)
    left, right = min(x10, x90), max(x10, x90)
    return f"""
      <svg class="quantile-svg" viewBox="0 0 220 62" role="img" aria-label="P10 P50 P90 分位箱体">
        <line x1="10" y1="31" x2="210" y2="31" class="q-axis" />
        <rect x="{left:.2f}" y="20" width="{max(2.0, right - left):.2f}" height="22" rx="8" class="q-band" />
        <line x1="{x50:.2f}" y1="14" x2="{x50:.2f}" y2="48" class="q-mid" />
        <circle cx="{x10:.2f}" cy="31" r="4" class="q-dot" />
        <circle cx="{x90:.2f}" cy="31" r="4" class="q-dot" />
        <text x="{x10:.2f}" y="58" text-anchor="middle">P10</text>
        <text x="{x50:.2f}" y="10" text-anchor="middle">P50</text>
        <text x="{x90:.2f}" y="58" text-anchor="middle">P90</text>
      </svg>
    """


def _period_html(period: PeriodView) -> str:
    direction_class = _class_for_direction(period.direction)
    return f"""
      <section class="period-card {direction_class}">
        <div class="period-head">
          <span>{escape(period.label)}</span>
          <strong>{escape(period.direction)}</strong>
        </div>
        {_box_svg(period)}
        <div class="quantile-values">
          <span>P10 <b>{escape(_fmt(period.p10))}</b></span>
          <span>P50 <b>{escape(_fmt(period.p50))}</b></span>
          <span>P90 <b>{escape(_fmt(period.p90))}</b></span>
        </div>
      </section>
    """


def _reason_html(asset: AssetView) -> str:
    if asset.gate.judgable:
        return '<li class="ok-reason">质量门控通过，方向仅为研究可读化摘要。</li>'
    reasons = asset.gate.reasons or ("质量门控未通过",)
    return "".join(f"<li>{escape(reason)}</li>" for reason in reasons[:3])


def _asset_html(asset: AssetView) -> str:
    direction_class = _class_for_direction(asset.direction)
    periods = "".join(_period_html(period) for period in asset.periods)
    interval_badge = " risk" if asset.gate.interval_blocked else ""
    return f"""
    <article class="asset-card {direction_class}">
      <header class="asset-head">
        <div>
          <span class="market">{escape(asset.market)}</span>
          <h2>{escape(asset.name)}</h2>
          <p>{escape(asset.symbol)}</p>
        </div>
        <div class="direction-badge {direction_class}">{escape(asset.direction)}</div>
      </header>
      <div class="gate-grid">
        <span><em>asset_eligibility</em><b>{escape(asset.asset_eligibility)}</b></span>
        <span><em>data_vintage</em><b>{escape(asset.data_vintage)}</b></span>
        <span><em>sample_quality</em><b>{escape(asset.sample_quality)}</b></span>
        <span class="interval-badge{interval_badge}"><em>interval_status</em><b>{escape(asset.interval_status)}</b></span>
      </div>
      <div class="period-grid">{periods}</div>
      <div class="reason-box">
        <strong>{'不可判断原因' if not asset.gate.judgable else '质量摘要'}</strong>
        <ul>{_reason_html(asset)}</ul>
      </div>
    </article>
    """


def build_dashboard_html(assets: Sequence[AssetView], *, generated_at: Optional[datetime] = None, source_path: str = "work/visual_result.json") -> str:
    now = generated_at or _now()
    jst = now.astimezone(ZoneInfo("Asia/Tokyo")).strftime("%Y-%m-%d %H:%M:%S JST")
    counts = _summary_counts(assets)
    cards = "".join(_asset_html(asset) for asset in assets)
    overall = "可参考" if counts["judgable"] and counts["unavailable"] == 0 else "部分可参考" if counts["judgable"] else "暂不可判断"
    return f"""<!doctype html>
<html lang="zh-CN">
<head>
  <meta charset="utf-8">
  <meta name="viewport" content="width=device-width, initial-scale=1">
  <title>AI 投研视觉终端</title>
  <style>
    :root {{
      --bg: #0b1020;
      --panel: #121a2f;
      --panel-2: #17213a;
      --text: #edf3ff;
      --muted: #9ca9bf;
      --line: rgba(255,255,255,.11);
      --up: #45d483;
      --down: #ff6b7a;
      --neutral: #d8b75e;
      --blocked: #8e99ad;
      --risk: #ffb04d;
    }}
    * {{ box-sizing: border-box; }}
    body {{ margin: 0; background: radial-gradient(circle at top left, #1d2b50, var(--bg) 44%); color: var(--text); font-family: -apple-system, BlinkMacSystemFont, "Segoe UI", "PingFang SC", "Hiragino Sans GB", "Microsoft YaHei", sans-serif; }}
    main {{ width: min(1180px, calc(100vw - 32px)); margin: 0 auto; padding: 28px 0 40px; }}
    .hero {{ display: grid; grid-template-columns: 1fr auto; gap: 20px; align-items: end; margin-bottom: 18px; }}
    .eyebrow, .market {{ color: var(--muted); font-size: 12px; letter-spacing: .12em; text-transform: uppercase; }}
    h1, h2, p {{ margin: 0; }}
    h1 {{ font-size: clamp(28px, 4vw, 46px); line-height: 1.08; }}
    .hero p {{ margin-top: 10px; color: var(--muted); }}
    .overall-pill {{ min-width: 180px; border: 1px solid var(--line); background: rgba(255,255,255,.06); border-radius: 20px; padding: 16px; text-align: right; }}
    .overall-pill span {{ color: var(--muted); display: block; font-size: 12px; }}
    .overall-pill strong {{ font-size: 26px; }}
    .summary-grid {{ display: grid; grid-template-columns: repeat(6, 1fr); gap: 10px; margin: 18px 0; }}
    .summary-grid article {{ border: 1px solid var(--line); background: rgba(18,26,47,.86); border-radius: 18px; padding: 14px; min-height: 88px; }}
    .summary-grid span {{ display: block; color: var(--muted); font-size: 12px; }}
    .summary-grid strong {{ display: block; margin-top: 8px; font-size: 28px; }}
    .asset-grid {{ display: grid; grid-template-columns: repeat(2, minmax(0, 1fr)); gap: 16px; }}
    .asset-card {{ border: 1px solid var(--line); background: linear-gradient(180deg, rgba(23,33,58,.95), rgba(12,18,32,.96)); border-radius: 24px; padding: 18px; box-shadow: 0 22px 60px rgba(0,0,0,.26); }}
    .asset-card.up {{ border-color: rgba(69,212,131,.38); }}
    .asset-card.down {{ border-color: rgba(255,107,122,.38); }}
    .asset-card.neutral {{ border-color: rgba(216,183,94,.38); }}
    .asset-card.blocked {{ border-color: rgba(142,153,173,.48); }}
    .asset-head {{ display: flex; justify-content: space-between; gap: 12px; align-items: flex-start; margin-bottom: 14px; }}
    .asset-head h2 {{ margin-top: 4px; font-size: 24px; }}
    .asset-head p {{ margin-top: 4px; color: var(--muted); }}
    .direction-badge {{ border-radius: 999px; padding: 9px 12px; font-weight: 800; white-space: nowrap; background: rgba(255,255,255,.08); }}
    .direction-badge.up {{ color: var(--up); }}
    .direction-badge.down {{ color: var(--down); }}
    .direction-badge.neutral {{ color: var(--neutral); }}
    .direction-badge.blocked {{ color: var(--blocked); }}
    .gate-grid {{ display: grid; grid-template-columns: repeat(2, minmax(0, 1fr)); gap: 8px; margin-bottom: 14px; }}
    .gate-grid span {{ border: 1px solid var(--line); background: rgba(255,255,255,.045); border-radius: 14px; padding: 10px; min-width: 0; }}
    .gate-grid em {{ display: block; color: var(--muted); font-size: 11px; font-style: normal; margin-bottom: 5px; }}
    .gate-grid b {{ display: block; overflow: hidden; text-overflow: ellipsis; white-space: nowrap; font-size: 13px; }}
    .interval-badge.risk {{ border-color: rgba(255,176,77,.55); box-shadow: inset 0 0 0 1px rgba(255,176,77,.18); }}
    .period-grid {{ display: grid; grid-template-columns: repeat(3, minmax(0, 1fr)); gap: 10px; }}
    .period-card {{ border: 1px solid var(--line); background: var(--panel-2); border-radius: 16px; padding: 12px; min-width: 0; }}
    .period-head {{ display: flex; justify-content: space-between; gap: 8px; align-items: center; margin-bottom: 8px; }}
    .period-head span {{ color: var(--muted); }}
    .period-card.up strong {{ color: var(--up); }}
    .period-card.down strong {{ color: var(--down); }}
    .period-card.neutral strong {{ color: var(--neutral); }}
    .period-card.blocked strong {{ color: var(--blocked); }}
    .quantile-svg {{ width: 100%; height: 72px; display: block; }}
    .q-axis {{ stroke: rgba(255,255,255,.16); stroke-width: 2; }}
    .q-band {{ fill: rgba(255,255,255,.12); stroke: rgba(255,255,255,.25); }}
    .q-mid {{ stroke: white; stroke-width: 2.8; }}
    .q-dot {{ fill: rgba(255,255,255,.7); }}
    .quantile-svg text {{ fill: var(--muted); font-size: 10px; }}
    .quantile-values {{ display: grid; grid-template-columns: repeat(3, 1fr); gap: 4px; color: var(--muted); font-size: 11px; }}
    .quantile-values b {{ color: var(--text); font-size: 12px; }}
    .quantile-missing {{ height: 72px; display: grid; place-items: center; color: var(--blocked); font-size: 12px; border: 1px dashed var(--line); border-radius: 12px; text-align: center; padding: 8px; }}
    .reason-box {{ margin-top: 14px; border: 1px solid var(--line); background: rgba(0,0,0,.16); border-radius: 16px; padding: 12px; }}
    .reason-box strong {{ display: block; margin-bottom: 6px; }}
    .reason-box ul {{ margin: 0; padding-left: 18px; color: var(--muted); }}
    .reason-box li + li {{ margin-top: 4px; }}
    .ok-reason {{ color: #b9c8dd; }}
    .footer {{ color: var(--muted); margin-top: 20px; font-size: 12px; display: flex; justify-content: space-between; gap: 12px; border-top: 1px solid var(--line); padding-top: 14px; }}
    @media (max-width: 980px) {{ .summary-grid {{ grid-template-columns: repeat(3, 1fr); }} .asset-grid {{ grid-template-columns: 1fr; }} }}
    @media (max-width: 720px) {{ main {{ width: min(100vw - 20px, 1180px); padding-top: 16px; }} .hero {{ grid-template-columns: 1fr; }} .overall-pill {{ text-align: left; }} .summary-grid {{ grid-template-columns: repeat(2, 1fr); }} .period-grid, .gate-grid {{ grid-template-columns: 1fr; }} .footer {{ flex-direction: column; }} }}
  </style>
</head>
<body>
  <main>
    <header class="hero">
      <div>
        <span class="eyebrow">Daily Visual Research Terminal</span>
        <h1>今日整体状态</h1>
        <p>来源：{escape(source_path)}；生成时间：{escape(jst)}。所有方向均受 asset_eligibility、data_vintage、sample_quality、interval_status 约束。</p>
      </div>
      <aside class="overall-pill"><span>今日状态</span><strong>{escape(overall)}</strong></aside>
    </header>

    <section class="summary-grid" aria-label="今日整体状态">
      <article><span>总资产数</span><strong>{counts['total']}</strong></article>
      <article><span>可判断资产数</span><strong>{counts['judgable']}</strong></article>
      <article><span>暂不可判断资产数</span><strong>{counts['unavailable']}</strong></article>
      <article><span>数据警告数量</span><strong>{counts['data_warnings']}</strong></article>
      <article><span>样本不足数量</span><strong>{counts['sample_blocks']}</strong></article>
      <article><span>区间异常数量</span><strong>{counts['interval_blocks']}</strong></article>
    </section>

    <section class="asset-grid" aria-label="资产卡片">
      {cards}
    </section>

    <footer class="footer">
      <span>本页面为本地研究可读化视图，不覆盖质量门控。</span>
      <span>P10 / P50 / P90 仅展示已有产物中的区间信息。</span>
    </footer>
  </main>
</body>
</html>
"""


def write_dashboard(path: PathLike, html: str) -> None:
    output_path = Path(path)
    output_path.parent.mkdir(parents=True, exist_ok=True)
    output_path.write_text(html, encoding="utf-8")


def generate_readable_dashboard(
    *,
    input_json: PathLike = "work/visual_result.json",
    output_html: PathLike = "reports/latest_dashboard.html",
    generated_at: Optional[datetime] = None,
    allow_missing_input: bool = False,
) -> Tuple[List[AssetView], bool]:
    assets, input_ok = load_asset_views(input_json, allow_missing=allow_missing_input)
    html = build_dashboard_html(assets, generated_at=generated_at, source_path=str(input_json))
    write_dashboard(output_html, html)
    return assets, input_ok


def _build_arg_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description="Render a readable P2.3 visual research dashboard from work/visual_result.json.")
    parser.add_argument("--input-json", default="work/visual_result.json")
    parser.add_argument("--output-html", default="reports/latest_dashboard.html")
    parser.add_argument("--allow-missing-input", action="store_true")
    return parser


def main(argv: Optional[Sequence[str]] = None) -> int:
    args = _build_arg_parser().parse_args(argv)
    assets, input_ok = generate_readable_dashboard(
        input_json=args.input_json,
        output_html=args.output_html,
        allow_missing_input=args.allow_missing_input,
    )
    counts = _summary_counts(assets)
    print("[PASS] P2.3 readable visual dashboard generated")
    print(f"output_html={args.output_html}")
    print(
        "summary="
        f"total={counts['total']},judgable={counts['judgable']},unavailable={counts['unavailable']},"
        f"data_warnings={counts['data_warnings']},sample_blocks={counts['sample_blocks']},interval_blocks={counts['interval_blocks']}"
    )
    if not input_ok and not args.allow_missing_input:
        print(f"[FAIL] input json missing or empty: {args.input_json}")
        return 2
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
