from __future__ import annotations

from dataclasses import dataclass
from math import isfinite
from pathlib import Path
import csv
from typing import Dict, Iterable, List, Optional, Tuple


SNAPSHOT_INPUT_FIELDS = (
    "display_symbol",
    "contract_map_status",
    "requested_market_data_type",
    "effective_market_data_type",
    "fallback_stage",
    "data_delay_flag",
    "snapshot_status",
    "fallback_terminal_status",
    "bid",
    "ask",
    "last",
    "close",
    "market_price",
    "action_allowed",
    "historical_data_request_triggered",
    "broker_execution_triggered",
)


OUTPUT_FIELDS = (
    "display_symbol",
    "integration_status",
    "input_snapshot_status",
    "data_delay_flag",
    "effective_market_data_type",
    "price_availability_status",
    "usable_reference_price",
    "usable_reference_price_field",
    "data_quality_tier",
    "research_usage",
    "manual_review_required",
    "action_allowed",
    "reject_reason",
    "safety_flags",
)


@dataclass(frozen=True)
class PriceSelection:
    status: str
    value: str
    field: str


def _clean(value: object) -> str:
    return str(value or "").strip()


def _norm(value: object) -> str:
    return _clean(value).lower()


def _parse_price(value: object) -> Optional[float]:
    raw = _clean(value)
    if not raw:
        return None
    try:
        parsed = float(raw)
    except ValueError:
        return None
    if not isfinite(parsed):
        return None
    return parsed


def _format_price(value: float) -> str:
    return f"{value:.10f}".rstrip("0").rstrip(".")


def select_usable_reference_price(row: Dict[str, str]) -> PriceSelection:
    for field in ("market_price", "last", "close"):
        parsed = _parse_price(row.get(field))
        if parsed is not None:
            return PriceSelection("available", _format_price(parsed), field)

    bid = _parse_price(row.get("bid"))
    ask = _parse_price(row.get("ask"))
    if bid is not None and ask is not None:
        return PriceSelection("available", _format_price((bid + ask) / 2), "bid_ask_midpoint")

    return PriceSelection("unavailable", "", "unavailable")


def _safety_reject_flags(row: Dict[str, str]) -> List[str]:
    checks = {
        "action_allowed": row.get("action_allowed"),
        "historical_data_request_triggered": row.get("historical_data_request_triggered"),
        "broker_execution_triggered": row.get("broker_execution_triggered"),
    }
    return [name for name, value in checks.items() if _norm(value) != "false"]


def _quality_for_delay(delay_flag: str, effective_type: str) -> Tuple[str, str]:
    delay = _norm(delay_flag)
    effective = _norm(effective_type)
    if delay in {"real_time", "live", "frozen"} or effective in {"live", "frozen"}:
        return "tier_1_real_time_or_live", "reference_only"
    if delay == "delayed" or effective == "delayed":
        return "tier_2_delayed", "reference_only"
    if delay == "delayed_frozen" or effective == "delayed_frozen":
        return "tier_3_delayed_frozen", "stale_reference_only"
    return "tier_9_unavailable", "unavailable"


def integrate_snapshot_row(row: Dict[str, str]) -> Dict[str, str]:
    safety_flags = _safety_reject_flags(row)
    snapshot_status = _clean(row.get("snapshot_status"))
    snapshot_status_norm = _norm(snapshot_status)
    contract_status = _norm(row.get("contract_map_status"))
    fallback_stage = _norm(row.get("fallback_stage"))
    terminal_status = _norm(row.get("fallback_terminal_status"))
    effective_type = _clean(row.get("effective_market_data_type")) or "unknown"
    delay_flag = _clean(row.get("data_delay_flag")) or "unavailable"
    price = select_usable_reference_price(row)
    quality_tier, research_usage = _quality_for_delay(delay_flag, effective_type)
    reject_reason = ""

    if safety_flags:
        integration_status = "SAFETY_REJECTED"
        quality_tier = "tier_9_unavailable"
        research_usage = "unavailable"
        reject_reason = "safety_flag_not_false"
    elif contract_status == "ibkr_unsupported" or fallback_stage == "unsupported" or "unsupported" in snapshot_status_norm:
        integration_status = "UNSUPPORTED"
        quality_tier = "tier_9_unavailable"
        research_usage = "unsupported"
        reject_reason = "unsupported_contract_or_market_data"
    elif snapshot_status_norm in {"connection_error", "no_go"} or fallback_stage == "connection_error":
        integration_status = "NO_GO"
        quality_tier = "tier_9_unavailable"
        research_usage = "unavailable"
        reject_reason = snapshot_status_norm or fallback_stage or "no_go"
    elif (
        snapshot_status_norm in {"snapshot_empty", "delayed_snapshot_empty", "delayed_frozen_snapshot_empty"}
        or terminal_status == "empty_price"
        or price.status == "unavailable"
    ):
        integration_status = "EMPTY_PRICE"
        quality_tier = "tier_9_unavailable"
        research_usage = "unavailable"
        reject_reason = "no_usable_reference_price"
    elif _norm(effective_type) == "delayed_frozen" or _norm(delay_flag) == "delayed_frozen":
        integration_status = "READY_DELAYED_FROZEN_REFERENCE_ONLY"
    elif _norm(effective_type) == "delayed" or _norm(delay_flag) == "delayed":
        integration_status = "READY_DELAYED_REFERENCE_ONLY"
    elif _norm(effective_type) in {"live", "frozen"} or _norm(delay_flag) in {"real_time", "live", "frozen"}:
        integration_status = "READY_REFERENCE_ONLY"
    else:
        integration_status = "NO_GO"
        quality_tier = "tier_9_unavailable"
        research_usage = "unavailable"
        reject_reason = "unclassified_snapshot_status"

    return {
        "display_symbol": _clean(row.get("display_symbol")),
        "integration_status": integration_status,
        "input_snapshot_status": snapshot_status,
        "data_delay_flag": delay_flag,
        "effective_market_data_type": effective_type,
        "price_availability_status": price.status,
        "usable_reference_price": price.value,
        "usable_reference_price_field": price.field,
        "data_quality_tier": quality_tier,
        "research_usage": research_usage,
        "manual_review_required": "true",
        "action_allowed": "false",
        "reject_reason": reject_reason,
        "safety_flags": ",".join(safety_flags),
    }


def missing_input_row(snapshot_path: str) -> Dict[str, str]:
    return {
        "display_symbol": "",
        "integration_status": "NO_GO",
        "input_snapshot_status": "missing",
        "data_delay_flag": "unavailable",
        "effective_market_data_type": "unknown",
        "price_availability_status": "unavailable",
        "usable_reference_price": "",
        "usable_reference_price_field": "unavailable",
        "data_quality_tier": "tier_9_unavailable",
        "research_usage": "unavailable",
        "manual_review_required": "true",
        "action_allowed": "false",
        "reject_reason": f"market_data_snapshot_missing:{snapshot_path}",
        "safety_flags": "missing_input",
    }


def read_snapshot_rows(path: Path) -> Tuple[str, List[Dict[str, str]]]:
    if not path.exists():
        return "missing", []
    with path.open(newline="") as f:
        rows = list(csv.DictReader(f))
    if not rows:
        return "empty_file", []
    return "present", rows


def build_integration_rows(snapshot_rows: Iterable[Dict[str, str]]) -> List[Dict[str, str]]:
    return [integrate_snapshot_row(row) for row in snapshot_rows]
