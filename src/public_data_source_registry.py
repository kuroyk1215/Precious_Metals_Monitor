from __future__ import annotations

from datetime import datetime, timezone
from typing import Dict, List, Optional


def _now_timestamp() -> str:
    return datetime.now(timezone.utc).replace(microsecond=0).isoformat()


def build_public_data_source_registry(generated_at: Optional[str] = None) -> Dict[str, object]:
    return {
        "status": "PUBLIC_DATA_SOURCE_REGISTRY_READY",
        "candidates": [
            {
                "source_name": "Stooq",
                "source_type": "public_historical",
                "default_status": "CANDIDATE_NOT_CONNECTED",
                "supports_us_etf": "LIKELY",
                "terms_review_status": "REVIEW_REQUIRED",
                "freshness_status": "UNKNOWN_UNTIL_FETCH",
            },
            {
                "source_name": "Alpha Vantage",
                "source_type": "public_api",
                "default_status": "CANDIDATE_NOT_CONNECTED",
                "api_key_required": "YES",
                "free_tier_available": "YES",
                "premium_intraday_limitation": "YES",
                "terms_review_status": "REVIEW_REQUIRED",
                "freshness_status": "UNKNOWN_UNTIL_FETCH",
            },
            {
                "source_name": "Yahoo Finance",
                "source_type": "unofficial_public_web",
                "default_status": "NOT_RECOMMENDED_FOR_AUTOMATION",
                "terms_risk": "HIGH",
                "enabled": "NO",
            },
        ],
        "generated_at_utc": generated_at or _now_timestamp(),
    }


def source_names(registry: Dict[str, object]) -> List[str]:
    return [str(item["source_name"]) for item in registry["candidates"]]  # type: ignore[index]
