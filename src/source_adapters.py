from __future__ import annotations

import csv
from pathlib import Path
from typing import Any


def load_source_provider_manifest(path: str) -> list[dict[str, Any]]:
    import yaml

    with open(path, "r", encoding="utf-8") as f:
        data = yaml.safe_load(f) or {}
    providers = data.get("providers", [])
    if not isinstance(providers, list):
        return []
    return providers


def normalize_provider_record(record: dict[str, Any]) -> dict[str, Any]:
    return {
        "provider_id": str(record.get("provider_id", "")).strip(),
        "provider_type": str(record.get("provider_type", "")).strip(),
        "status": str(record.get("status", "")).strip(),
        "online_required": bool(record.get("online_required", False)),
        "license_required": record.get("license_required", False),
        "intended_use": str(record.get("intended_use", "")).strip(),
        "symbols": record.get("symbols", []) if isinstance(record.get("symbols", []), list) else [],
        "fields": record.get("fields", []) if isinstance(record.get("fields", []), list) else [],
        "notes": str(record.get("notes", "")).strip(),
    }


def summarize_source_providers(providers: list[dict[str, Any]]) -> list[dict[str, Any]]:
    rows: list[dict[str, Any]] = []
    for raw in providers:
        record = normalize_provider_record(raw)
        warning_flags: list[str] = []
        status = record["status"]
        license_required = record["license_required"]

        if status == "available" and license_required is False:
            readiness_status = "ready"
        elif status == "planned":
            readiness_status = "planned"
        elif status == "manual_required":
            readiness_status = "manual_required"
        elif status == "needs_review":
            readiness_status = "needs_review"
        else:
            readiness_status = "unknown"

        if license_required is True:
            warning_flags.append("license_required")
        if record["online_required"] is True:
            warning_flags.append("online_required")

        not_impl_text = f"{record['intended_use']} {record['notes']}".lower()
        if "not implemented" in not_impl_text:
            warning_flags.append("not_implemented")
        if not record["symbols"]:
            warning_flags.append("missing_symbols")
        if not record["fields"]:
            warning_flags.append("missing_fields")

        rows.append(
            {
                "provider_id": record["provider_id"],
                "provider_type": record["provider_type"],
                "status": status,
                "online_required": str(record["online_required"]).lower(),
                "license_required": str(license_required).lower() if isinstance(license_required, bool) else str(license_required),
                "symbol_count": len(record["symbols"]),
                "field_count": len(record["fields"]),
                "readiness_status": readiness_status,
                "warning_flags": "|".join(warning_flags) if warning_flags else "none",
            }
        )
    return rows


def write_source_audit_log_csv(rows: list[dict[str, Any]], path: str, times: dict[str, str]) -> None:
    fields = [
        "timestamp_jst",
        "timestamp_et",
        "provider_id",
        "provider_type",
        "status",
        "online_required",
        "license_required",
        "symbol_count",
        "field_count",
        "readiness_status",
        "warning_flags",
    ]
    out = Path(path)
    out.parent.mkdir(parents=True, exist_ok=True)
    with out.open("w", newline="", encoding="utf-8") as f:
        writer = csv.DictWriter(f, fieldnames=fields)
        writer.writeheader()
        for row in rows:
            writer.writerow({"timestamp_jst": times["jst"], "timestamp_et": times["et"], **row})


def build_source_audit_report(rows: list[dict[str, Any]], path: str, times: dict[str, str]) -> None:
    lines = [
        "# Source Adapter Audit Report",
        "",
        "## 当前时间",
        f"- JST: {times['jst']}",
        f"- CST: {times['cst']}",
        f"- ET: {times['et']}",
        "",
        "## 模型状态",
        "- source_adapter_audit",
        "- research_only",
        "- no_auto_trade",
        "",
        "## 边界声明",
        "- Phase 4B-0 不联网",
        "- 不调用 IBKR 历史行情接口",
        "- 不抓取网页",
        "- 不接交易 API",
        "- 不输出买卖点",
        "- 不把 sample 当真实市场数据",
        "",
        "## Provider Summary",
        "| provider_id | provider_type | status | online_required | license_required | symbol_count | field_count | readiness_status | warning_flags |",
        "|---|---|---|---|---|---:|---:|---|---|",
    ]
    for r in rows:
        lines.append(
            f"| {r['provider_id']} | {r['provider_type']} | {r['status']} | {r['online_required']} | {r['license_required']} | {r['symbol_count']} | {r['field_count']} | {r['readiness_status']} | {r['warning_flags']} |"
        )
    out = Path(path)
    out.parent.mkdir(parents=True, exist_ok=True)
    out.write_text("\n".join(lines), encoding="utf-8")
