from __future__ import annotations

from datetime import datetime, timezone
from typing import Dict, Optional


PHASE = "Phase 801-1000"


def _now_timestamp() -> str:
    return datetime.now(timezone.utc).replace(microsecond=0).isoformat()


def build_operator_daily_packet_snapshot(generated_at: Optional[str] = None) -> Dict[str, object]:
    timestamp = generated_at or _now_timestamp()
    return {
        "phase": PHASE,
        "status": "OPERATOR_DAILY_PACKET_PREVIEW_READY",
        "local_platform_status": "LOCAL_RESEARCH_PLATFORM_MVP_READY",
        "ui_status": "V9_UI_DRIVEN_LOCAL_RESEARCH_PLATFORM_MVP",
        "api_status": "LOCAL_READONLY_API_SHELL_READY",
        "data_source_status": "US_GLD_SLV_DATA_SOURCE_DRY_RUN_READY",
        "risk_status": "ALL_EXTERNAL_ACTIONS_BLOCKED",
        "next_actions": [
            "Start local UI server from terminal when needed",
            "Use browser UI as primary workbench",
            "Review GLD / SLV research framework",
            "Keep JP and CN frozen until data source decision",
        ],
        "contains_real_market_data": "NO",
        "contains_trading_instruction": "NO",
        "generated_at_utc": timestamp,
    }


def build_operator_daily_packet_markdown(generated_at: Optional[str] = None) -> str:
    timestamp = generated_at or _now_timestamp()
    return f"""# Operator Daily Packet Preview

- phase: {PHASE}
- status: OPERATOR_DAILY_PACKET_PREVIEW_READY
- local_platform_status: LOCAL_RESEARCH_PLATFORM_MVP_READY
- UI: V9_UI_DRIVEN_LOCAL_RESEARCH_PLATFORM_MVP
- API: LOCAL_READONLY_API_SHELL_READY
- data_source: US_GLD_SLV_DATA_SOURCE_DRY_RUN_READY
- risk: ALL_EXTERNAL_ACTIONS_BLOCKED
- symbols: GLD / SLV
- JP: FROZEN_PENDING_MARKET_DATA_SUBSCRIPTION
- CN: FROZEN_PENDING_DATA_SOURCE_DECISION
- contains_real_market_data: NO
- contains_trading_instruction: NO
- generated_at_utc: {timestamp}

Next actions:
- Start local UI server from terminal only when needed.
- Use browser UI as the primary local workbench.
- Review data source dry-run and research framework artifacts.
- Keep all external actions disabled.
"""


def build_telegram_preview_snapshot(generated_at: Optional[str] = None) -> Dict[str, object]:
    timestamp = generated_at or _now_timestamp()
    return {
        "phase": PHASE,
        "status": "TELEGRAM_PREVIEW_LOCAL_ONLY_READY",
        "telegram_real_send_enabled": "NO",
        "reads_token": "NO",
        "reads_chat_id": "NO",
        "sends_message": "NO",
        "preview_format": "MARKDOWN_LOCAL_ONLY",
        "generated_at_utc": timestamp,
    }


def build_telegram_preview_markdown(generated_at: Optional[str] = None) -> str:
    timestamp = generated_at or _now_timestamp()
    return f"""# Telegram Preview Local Only

- phase: {PHASE}
- status: TELEGRAM_PREVIEW_LOCAL_ONLY_READY
- telegram_real_send_enabled: NO
- token_read: NO
- chat_id_read: NO
- send_attempted: NO
- generated_at_utc: {timestamp}

Local preview:
GLD / SLV local research platform MVP is ready for offline review. Market data remains blocked by subscription. No external action was performed.
"""


def build_watchlist_policy_snapshot(generated_at: Optional[str] = None) -> Dict[str, object]:
    timestamp = generated_at or _now_timestamp()
    return {
        "phase": PHASE,
        "status": "WATCHLIST_POLICY_READY",
        "us_scope": ["GLD", "SLV"],
        "jp_status": "FROZEN",
        "cn_status": "FROZEN",
        "add_symbol_requires_manual_confirmation": "YES",
        "live_monitor_without_data_source": "NO",
        "generated_at_utc": timestamp,
    }
