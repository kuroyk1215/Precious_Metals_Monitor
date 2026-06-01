from __future__ import annotations

from datetime import datetime, timezone
from typing import Dict, Optional


PHASE = "Phase 801-1000"
NO_TEXT = "NO"


def now_timestamp() -> str:
    return datetime.now(timezone.utc).replace(microsecond=0).isoformat()


def build_data_source_dry_run_snapshot(generated_at: Optional[str] = None) -> Dict[str, object]:
    return {
        "phase": PHASE,
        "status": "US_GLD_SLV_DATA_SOURCE_DRY_RUN_READY",
        "symbols": ["GLD", "SLV"],
        "source_connection_implemented": NO_TEXT,
        "live_market_data_enabled": NO_TEXT,
        "realtime_market_data_verified": NO_TEXT,
        "market_data_status": "BLOCKED_BY_SUBSCRIPTION",
        "ibkr_error_code": 10089,
        "data_sources": [
            {"name": "IBKR Network B / ARCA", "status": "NOT_SUBSCRIBED_NOT_CONNECTED"},
            {"name": "FREE_DELAYED_PUBLIC_SOURCE", "status": "CANDIDATE_NOT_CONNECTED"},
            {"name": "MANUAL_CSV_SOURCE", "status": "FALLBACK_READY_AS_DESIGN_ONLY"},
            {"name": "PAID_MARKET_DATA_API", "status": "CANDIDATE_NOT_CONNECTED"},
            {"name": "HYBRID_SOURCE_ROUTER", "status": "DESIGN_ONLY"},
        ],
        "blocked_actions": [
            "IBKR_CONNECT",
            "MARKET_DATA_REQUEST",
            "HISTORICAL_DATA_REQUEST",
            "CONTRACT_QUALIFICATION",
            "EXTERNAL_NETWORK_REQUEST",
        ],
        "generated_at_utc": generated_at or now_timestamp(),
    }
