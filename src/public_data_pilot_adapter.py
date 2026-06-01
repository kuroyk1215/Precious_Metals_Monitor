from __future__ import annotations

import argparse
from datetime import datetime, timezone
from typing import Dict, Optional, Sequence

from src.public_data_source_registry import build_public_data_source_registry


def _now_timestamp() -> str:
    return datetime.now(timezone.utc).replace(microsecond=0).isoformat()


def build_public_data_pilot_dry_run(generated_at: Optional[str] = None) -> Dict[str, object]:
    return {
        "status": "PUBLIC_DATA_PILOT_DRY_RUN_READY",
        "public_data_auto_fetch_enabled": "NO",
        "public_data_fetch_requires_explicit_allow": "YES",
        "default_network_behavior": "DISABLED",
        "supported_symbols": ["GLD", "SLV"],
        "registry": build_public_data_source_registry(generated_at),
        "field_contract": [
            "symbol",
            "market",
            "timestamp_utc",
            "price",
            "currency",
            "source_name",
            "source_type",
            "data_delay_status",
            "freshness_status",
            "terms_review_status",
        ],
        "request_plan": [
            "operator explicitly reviews terms",
            "operator passes --allow-public-network",
            "pilot reads GLD / SLV only",
            "pilot labels source and freshness",
            "pilot failure leaves store unchanged",
        ],
        "risk_boundary": [
            "default no network",
            "no fabricated data",
            "no trading advice",
            "no automatic UI trigger",
        ],
        "generated_at_utc": generated_at or _now_timestamp(),
    }


def public_data_pilot_fetch(allow_public_network: bool = False) -> Dict[str, object]:
    if not allow_public_network:
        return {
            "status": "PUBLIC_DATA_PILOT_FETCH_DISABLED",
            "network_request_made": "NO",
            "reason": "EXPLICIT_ALLOW_PUBLIC_NETWORK_REQUIRED",
        }
    return {
        "status": "PUBLIC_DATA_PILOT_FETCH_NOT_IMPLEMENTED",
        "network_request_made": "NO",
        "reason": "PILOT_FETCH_INTERFACE_ONLY",
    }


def main(argv: Optional[Sequence[str]] = None) -> int:
    parser = argparse.ArgumentParser(description="Public data pilot dry-run or explicitly gated fetch.")
    parser.add_argument("--fetch", action="store_true")
    parser.add_argument("--allow-public-network", action="store_true")
    args = parser.parse_args(argv)
    if args.fetch:
        result = public_data_pilot_fetch(args.allow_public_network)
        print("[PUBLIC_DATA_PILOT_FETCH] generated")
        print(f"status={result['status']}")
        print(f"network_request_made={result['network_request_made']}")
        return 0 if args.allow_public_network else 2
    snapshot = build_public_data_pilot_dry_run()
    print("[PUBLIC_DATA_PILOT_DRY_RUN] generated")
    print(f"status={snapshot['status']}")
    print(f"public_data_auto_fetch_enabled={snapshot['public_data_auto_fetch_enabled']}")
    print(f"public_data_fetch_requires_explicit_allow={snapshot['public_data_fetch_requires_explicit_allow']}")
    return 0
