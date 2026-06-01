from __future__ import annotations

from datetime import datetime, timezone
from typing import Dict, Optional

from src.public_data_intake_preparation import SAFETY_RULES, SOURCE_CANDIDATES


PHASE = "Phase 1001-1120"
STATUS = "PRODUCTIZED_UI_PUBLIC_DATA_INTAKE_READY"
UI_GENERATION = "V10_PRODUCTIZED_RESEARCH_WORKBENCH"
NO_TEXT = "NO"


def _now_timestamp() -> str:
    return datetime.now(timezone.utc).replace(microsecond=0).isoformat()


def build_user_facing_content_snapshot(generated_at: Optional[str] = None) -> Dict[str, object]:
    return {
        "phase": PHASE,
        "status": "USER_FACING_CONTENT_READY",
        "title": "AI 投研工作台",
        "subtitle": "本地只读研究平台 · GLD / SLV · 无实时行情 · 无交易权限",
        "today_status": "本地投研平台已就绪",
        "available_now": ["研究框架", "本地报告", "数据源状态", "风险边界"],
        "unavailable_now": ["实时行情", "交易建议", "账户读取", "Telegram 实发"],
        "next_step": "准备公共行情导入",
        "generated_at_utc": generated_at or _now_timestamp(),
    }


def build_developer_details_snapshot(generated_at: Optional[str] = None) -> Dict[str, object]:
    return {
        "phase": PHASE,
        "status": "DEVELOPER_DETAILS_COLLAPSED_BY_DEFAULT",
        "collapsed_by_default": "YES",
        "technical_status": {
            "legacy_mvp_status": "UI_DRIVEN_LOCAL_RESEARCH_PLATFORM_MVP_READY",
            "market_data_status": "BLOCKED_BY_SUBSCRIPTION",
            "ibkr_error_code": "10089",
            "allowed_http_methods": "GET_ONLY",
            "terminal_fallback": "CLI fallback",
            "source_connection_implemented": NO_TEXT,
            "live_market_data_enabled": NO_TEXT,
        },
        "fallback_commands": [
            "python3 main.py --productized-ui-public-data-intake-pack",
            "python3 main.py --public-data-intake-prep",
            "python3 main.py --local-ui-server",
        ],
        "generated_at_utc": generated_at or _now_timestamp(),
    }


def build_productized_dashboard_sections_snapshot(generated_at: Optional[str] = None) -> Dict[str, object]:
    return {
        "phase": PHASE,
        "status": "PRODUCTIZED_DASHBOARD_SECTIONS_READY",
        "sections": [
            "今日状态",
            "GLD / SLV 研究框架",
            "数据源状态",
            "本地报告",
            "风险边界",
            "下一步操作",
            "公共行情导入准备",
        ],
        "source_candidates": [item["candidate_code"] for item in SOURCE_CANDIDATES],
        "safety_rules": list(SAFETY_RULES),
        "generated_at_utc": generated_at or _now_timestamp(),
    }


def build_productized_next_actions_snapshot(generated_at: Optional[str] = None) -> Dict[str, object]:
    return {
        "phase": PHASE,
        "status": "PRODUCTIZED_NEXT_ACTIONS_READY",
        "next_actions": [
            "查看本地报告",
            "查看数据源准备说明",
            "确认公共延迟源条款",
            "准备手动 CSV fallback",
            "保持外部动作禁用",
        ],
        "disabled_actions": [
            "获取实时行情",
            "读取账户",
            "读取持仓",
            "生成交易信号",
            "发送 Telegram",
            "解冻 JP / CN",
        ],
        "generated_at_utc": generated_at or _now_timestamp(),
    }


def build_productized_ui_snapshot(generated_at: Optional[str] = None) -> Dict[str, object]:
    timestamp = generated_at or _now_timestamp()
    return {
        "phase": PHASE,
        "status": "PRODUCTIZED_UI_READY",
        "ui_generation": UI_GENERATION,
        "user_facing_content_status": "USER_FACING_CONTENT_READY",
        "developer_details_status": "DEVELOPER_DETAILS_COLLAPSED_BY_DEFAULT",
        "public_data_intake_status": "PUBLIC_DATA_INTAKE_PREPARATION_READY",
        "generated_at_utc": timestamp,
    }
