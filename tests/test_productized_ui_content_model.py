from __future__ import annotations

from src.productized_ui_content_model import (
    UI_GENERATION,
    build_developer_details_snapshot,
    build_productized_dashboard_sections_snapshot,
    build_productized_next_actions_snapshot,
    build_productized_ui_snapshot,
    build_user_facing_content_snapshot,
)


def test_user_facing_content_snapshot_uses_productized_chinese_copy() -> None:
    snapshot = build_user_facing_content_snapshot("2026-06-01T00:00:00+00:00")

    assert snapshot["title"] == "AI 投研工作台"
    assert "本地只读研究平台" in snapshot["subtitle"]
    assert snapshot["today_status"] == "本地投研平台已就绪"
    assert "研究框架" in snapshot["available_now"]
    assert "实时行情" in snapshot["unavailable_now"]
    assert snapshot["next_step"] == "准备公共行情导入"


def test_developer_details_keep_technical_status_collapsed() -> None:
    snapshot = build_developer_details_snapshot("2026-06-01T00:00:00+00:00")

    assert snapshot["status"] == "DEVELOPER_DETAILS_COLLAPSED_BY_DEFAULT"
    assert snapshot["collapsed_by_default"] == "YES"
    assert snapshot["technical_status"]["market_data_status"] == "BLOCKED_BY_SUBSCRIPTION"
    assert snapshot["technical_status"]["allowed_http_methods"] == "GET_ONLY"


def test_productized_sections_and_next_actions_are_complete() -> None:
    sections = build_productized_dashboard_sections_snapshot("2026-06-01T00:00:00+00:00")
    actions = build_productized_next_actions_snapshot("2026-06-01T00:00:00+00:00")
    ui = build_productized_ui_snapshot("2026-06-01T00:00:00+00:00")

    for label in ("今日状态", "GLD / SLV 研究框架", "数据源状态", "本地报告", "风险边界", "下一步操作", "公共行情导入准备"):
        assert label in sections["sections"]
    assert "查看本地报告" in actions["next_actions"]
    assert "获取实时行情" in actions["disabled_actions"]
    assert ui["ui_generation"] == UI_GENERATION
