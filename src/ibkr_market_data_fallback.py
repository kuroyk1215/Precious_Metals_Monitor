from __future__ import annotations

from dataclasses import dataclass
from typing import Optional


@dataclass
class SnapshotAttemptResult:
    requested_market_data_type: str
    effective_market_data_type: str
    fallback_stage: str
    error_code: str
    error_message: str
    live_permission_status: str
    delayed_permission_status: str
    delayed_frozen_permission_status: str
    price_source_priority: str
    data_delay_flag: str
    snapshot_attempt_count: int
    fallback_reason: str
    fallback_terminal_status: str
    data_status: str
    snapshot_status: str


def classify_error(error_code: str, error_message: str) -> str:
    message = (error_message or "").lower()
    if error_code == "354" or "delayed market data available" in message or "not subscribed" in message:
        return "live_not_subscribed"
    return "other"


def fallback_terminal_from_prices(has_price: bool) -> str:
    return "usable_price" if has_price else "empty_price"


def build_attempt_result(
    requested_market_data_type: str,
    effective_market_data_type: Optional[str],
    fallback_stage: str,
    error_code: str,
    error_message: str,
    has_price: bool,
    snapshot_attempt_count: int,
    fallback_reason: str,
) -> SnapshotAttemptResult:
    err_type = classify_error(error_code, error_message)
    live_permission_status = "denied" if err_type == "live_not_subscribed" else "unknown"
    entered_delayed_path = (
        requested_market_data_type == "delayed"
        or effective_market_data_type in {"delayed", "delayed_frozen"}
        or fallback_stage in {"live_to_delayed", "delayed_to_delayed_frozen"}
    )
    entered_delayed_frozen_path = (
        requested_market_data_type == "delayed_frozen"
        or effective_market_data_type == "delayed_frozen"
        or fallback_stage == "delayed_to_delayed_frozen"
    )
    delayed_permission_status = "allowed" if entered_delayed_path else "unknown"
    delayed_frozen_permission_status = "allowed" if entered_delayed_frozen_path else "unknown"

    data_delay_map = {
        "live": "real_time",
        "frozen": "frozen",
        "delayed": "delayed",
        "delayed_frozen": "delayed_frozen",
    }
    delay_flag = data_delay_map.get(effective_market_data_type or "", "unavailable")

    if has_price:
        snapshot_status = (
            "DELAYED_FROZEN_SNAPSHOT_RETURNED" if (effective_market_data_type == "delayed_frozen") else
            "DELAYED_SNAPSHOT_RETURNED" if (effective_market_data_type == "delayed") else
            "SNAPSHOT_RETURNED"
        )
        data_status = "snapshot_available"
    else:
        snapshot_status = (
            "DELAYED_FROZEN_SNAPSHOT_EMPTY" if (effective_market_data_type == "delayed_frozen") else
            "DELAYED_SNAPSHOT_EMPTY" if (effective_market_data_type == "delayed") else
            "SNAPSHOT_EMPTY"
        )
        data_status = "snapshot_empty"

    return SnapshotAttemptResult(
        requested_market_data_type=requested_market_data_type,
        effective_market_data_type=effective_market_data_type or "unknown",
        fallback_stage=fallback_stage,
        error_code=error_code,
        error_message=error_message,
        live_permission_status=live_permission_status,
        delayed_permission_status=delayed_permission_status,
        delayed_frozen_permission_status=delayed_frozen_permission_status,
        price_source_priority="live>delayed>delayed_frozen",
        data_delay_flag=delay_flag,
        snapshot_attempt_count=snapshot_attempt_count,
        fallback_reason=fallback_reason,
        fallback_terminal_status=fallback_terminal_from_prices(has_price),
        data_status=data_status,
        snapshot_status=snapshot_status,
    )
