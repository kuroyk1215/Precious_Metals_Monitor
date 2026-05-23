from __future__ import annotations

from dataclasses import dataclass
from typing import Iterable, List, Optional

from src.ibkr_market_data_fallback import LIVE_NOT_SUBSCRIBED_DELAYED_AVAILABLE, classify_error


@dataclass(frozen=True)
class IbkrMarketDataError:
    request_id: str
    error_code: str
    error_message: str
    classification: str


class IbkrMarketDataErrorCapture:
    def __init__(self) -> None:
        self.errors: List[IbkrMarketDataError] = []

    def record(self, request_id: object, error_code: object, error_message: object) -> None:
        code = str(error_code or "").strip()
        message = str(error_message or "").strip()
        classification = classify_error(code, message)
        self.errors.append(
            IbkrMarketDataError(
                request_id=str(request_id or "").strip(),
                error_code=code,
                error_message=message,
                classification=classification,
            )
        )

    def latest_delayed_available(self, start_index: int = 0) -> Optional[IbkrMarketDataError]:
        for error in reversed(self.errors[start_index:]):
            if error.classification == LIVE_NOT_SUBSCRIBED_DELAYED_AVAILABLE:
                return error
        return None


def attach_ib_error_capture(ib: object, capture: IbkrMarketDataErrorCapture) -> None:
    event = getattr(ib, "errorEvent", None)
    if event is None:
        return

    def on_error(request_id: object, error_code: object, error_message: object, contract: object = None) -> None:
        capture.record(request_id, error_code, error_message)

    event += on_error


def delayed_available_error_from_rows(rows: Iterable[dict[str, str]]) -> Optional[IbkrMarketDataError]:
    capture = IbkrMarketDataErrorCapture()
    for row in rows:
        capture.record(row.get("request_id", ""), row.get("error_code", ""), row.get("error_message", ""))
    return capture.latest_delayed_available()
