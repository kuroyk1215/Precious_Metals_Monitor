from __future__ import annotations

import argparse
import json
from datetime import datetime, timezone
from pathlib import Path
from typing import Dict, Optional, Sequence, Union


PHASE = "Phase 1001-1120"
STATUS = "PUBLIC_DATA_INTAKE_PREPARATION_READY"
NO_TEXT = "NO"
SYMBOLS = ["GLD", "SLV"]

PUBLIC_DATA_INTAKE_PREPARATION_SNAPSHOT = "dashboard/data/public_data_intake_preparation_snapshot.json"
PUBLIC_MARKET_DATA_SOURCE_CANDIDATES_SNAPSHOT = "dashboard/data/public_market_data_source_candidates_snapshot.json"
PUBLIC_DATA_FIELD_CONTRACT_SNAPSHOT = "dashboard/data/public_data_field_contract_snapshot.json"
PUBLIC_DATA_SAFETY_GUARD_SNAPSHOT = "dashboard/data/public_data_safety_guard_snapshot.json"
PUBLIC_DATA_INTAKE_REPORT = "reports/public_data_intake_preparation_report.md"

FIELD_CONTRACT = (
    "symbol",
    "market",
    "source_name",
    "source_type",
    "timestamp_utc",
    "price_status",
    "last_price_status",
    "currency",
    "data_delay_status",
    "terms_review_status",
    "reliability_status",
    "ingestion_status",
)

SOURCE_CANDIDATES = (
    {
        "candidate_code": "PUBLIC_DELAYED_SOURCE_CANDIDATE",
        "user_label": "公共延迟源",
        "source_type": "PUBLIC_DELAYED",
        "decision_status": "OPTIONAL_TERMS_AND_STABILITY_PENDING",
        "panel_copy": "可选，低成本；条款和稳定性待确认。",
    },
    {
        "candidate_code": "MANUAL_CSV_SOURCE",
        "user_label": "手动 CSV",
        "source_type": "LOCAL_MANUAL_FILE",
        "decision_status": "SAFEST_FALLBACK_NOW",
        "panel_copy": "当前最安全 fallback；适合先验证流程。",
    },
    {
        "candidate_code": "PAID_MARKET_DATA_API_CANDIDATE",
        "user_label": "付费 API",
        "source_type": "PAID_API",
        "decision_status": "NOT_PRIORITIZED_NOW",
        "panel_copy": "暂不优先；后续评估。",
    },
    {
        "candidate_code": "IBKR_SUBSCRIPTION_OPTION",
        "user_label": "IBKR Network B / ARCA",
        "source_type": "IBKR_SUBSCRIPTION",
        "decision_status": "OPTIONAL_NOT_SUBSCRIBED_NOT_CONNECTED",
        "panel_copy": "可选，开通后支持更稳定行情；当前未订阅未连接。",
    },
    {
        "candidate_code": "HYBRID_ROUTER_DESIGN",
        "user_label": "Hybrid Router",
        "source_type": "ROUTER_DESIGN",
        "decision_status": "FUTURE_MULTI_MARKET_DESIGN",
        "panel_copy": "未来多市场扩展方案。",
    },
)

SAFETY_RULES = (
    "no source -> no price",
    "no price -> no signal",
    "no approved terms -> no automated ingestion",
    "no verified freshness -> framework only",
)

PathLike = Union[str, Path]


def _now_timestamp() -> str:
    return datetime.now(timezone.utc).replace(microsecond=0).isoformat()


def _write_json(path: PathLike, payload: Dict[str, object]) -> None:
    output_path = Path(path)
    output_path.parent.mkdir(parents=True, exist_ok=True)
    output_path.write_text(json.dumps(payload, indent=2, sort_keys=True, ensure_ascii=False) + "\n", encoding="utf-8")


def _write_text(path: PathLike, text: str) -> None:
    output_path = Path(path)
    output_path.parent.mkdir(parents=True, exist_ok=True)
    output_path.write_text(text, encoding="utf-8")


def build_public_data_intake_preparation_snapshot(generated_at: Optional[str] = None) -> Dict[str, object]:
    return {
        "phase": PHASE,
        "status": STATUS,
        "symbols": SYMBOLS,
        "public_data_connection_implemented": NO_TEXT,
        "external_market_data_request_enabled": NO_TEXT,
        "real_price_ingestion_enabled": NO_TEXT,
        "live_market_data_enabled": NO_TEXT,
        "automated_ingestion_enabled": NO_TEXT,
        "report_generation_from_real_price_enabled": NO_TEXT,
        "generated_at_utc": generated_at or _now_timestamp(),
    }


def build_source_candidates_snapshot(generated_at: Optional[str] = None) -> Dict[str, object]:
    return {
        "phase": PHASE,
        "status": "PUBLIC_MARKET_DATA_SOURCE_CANDIDATES_READY",
        "candidates": list(SOURCE_CANDIDATES),
        "generated_at_utc": generated_at or _now_timestamp(),
    }


def build_field_contract_snapshot(generated_at: Optional[str] = None) -> Dict[str, object]:
    return {
        "phase": PHASE,
        "status": "PUBLIC_DATA_FIELD_CONTRACT_READY",
        "fields": list(FIELD_CONTRACT),
        "real_price_value_fields_enabled": NO_TEXT,
        "generated_at_utc": generated_at or _now_timestamp(),
    }


def build_safety_guard_snapshot(generated_at: Optional[str] = None) -> Dict[str, object]:
    return {
        "phase": PHASE,
        "status": "PUBLIC_DATA_SAFETY_GUARD_READY",
        "rules": list(SAFETY_RULES),
        "public_data_connection_implemented": NO_TEXT,
        "external_market_data_request_enabled": NO_TEXT,
        "real_price_ingestion_enabled": NO_TEXT,
        "generated_at_utc": generated_at or _now_timestamp(),
    }


def build_public_data_intake_report(generated_at: Optional[str] = None) -> str:
    timestamp = generated_at or _now_timestamp()
    candidates = "\n".join(
        f"- {item['candidate_code']}: {item['user_label']}，{item['panel_copy']}" for item in SOURCE_CANDIDATES
    )
    fields = "\n".join(f"- {field}" for field in FIELD_CONTRACT)
    rules = "\n".join(f"- {rule}" for rule in SAFETY_RULES)
    return f"""# Public Data Intake Preparation

- status: {STATUS}
- public_data_connection_implemented: NO
- external_market_data_request_enabled: NO
- real_price_ingestion_enabled: NO
- live_market_data_enabled: NO
- symbols: GLD / SLV

## Source Candidates

{candidates}

## Field Contract

{fields}

## Safety Guard

{rules}

generated_at_utc: {timestamp}
"""


def generate_public_data_intake_preparation(generated_at: Optional[str] = None) -> Dict[str, object]:
    timestamp = generated_at or _now_timestamp()
    snapshot = build_public_data_intake_preparation_snapshot(timestamp)
    _write_json(PUBLIC_DATA_INTAKE_PREPARATION_SNAPSHOT, snapshot)
    _write_json(PUBLIC_MARKET_DATA_SOURCE_CANDIDATES_SNAPSHOT, build_source_candidates_snapshot(timestamp))
    _write_json(PUBLIC_DATA_FIELD_CONTRACT_SNAPSHOT, build_field_contract_snapshot(timestamp))
    _write_json(PUBLIC_DATA_SAFETY_GUARD_SNAPSHOT, build_safety_guard_snapshot(timestamp))
    _write_text(PUBLIC_DATA_INTAKE_REPORT, build_public_data_intake_report(timestamp))
    return snapshot


def main(argv: Optional[Sequence[str]] = None) -> int:
    parser = argparse.ArgumentParser(description="Generate public data intake preparation artifacts without external requests.")
    parser.parse_args(argv)
    snapshot = generate_public_data_intake_preparation()
    print("[PUBLIC_DATA_INTAKE_PREP] generated")
    print(f"phase={snapshot['phase']}")
    print(f"status={snapshot['status']}")
    print(f"public_data_connection_implemented={snapshot['public_data_connection_implemented']}")
    print(f"external_market_data_request_enabled={snapshot['external_market_data_request_enabled']}")
    print(f"real_price_ingestion_enabled={snapshot['real_price_ingestion_enabled']}")
    print(f"report={PUBLIC_DATA_INTAKE_REPORT}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
