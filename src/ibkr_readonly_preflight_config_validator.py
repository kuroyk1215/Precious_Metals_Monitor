from __future__ import annotations

import csv
from dataclasses import dataclass
from datetime import datetime
from pathlib import Path
from typing import Any, Iterable, Optional
from zoneinfo import ZoneInfo


TRUE_TEXT = "true"
FALSE_TEXT = "false"
PASS_TEXT = "PASS"
FAIL_TEXT = "FAIL"
MISSING_TEXT = "missing"

DEFAULT_WARNING_FLAGS = (
    "PREFLIGHT_CONFIG_VALIDATOR_DEFINED",
    "READ_ONLY_REQUIRED",
    "ACCOUNT_MODE_EXPLICIT_REQUIRED",
    "LOCAL_TWS_HOST_REQUIRED",
    "EXPLICIT_PORT_REQUIRED",
    "EXPLICIT_CLIENT_ID_REQUIRED",
    "REAL_CONNECTION_BLOCKED",
    "TWS_CONNECTION_BLOCKED",
    "IBKR_API_REQUEST_BLOCKED",
    "CONTRACT_QUALIFICATION_BLOCKED",
    "MARKET_DATA_REQUEST_BLOCKED",
    "HISTORICAL_DATA_REQUEST_BLOCKED",
    "ORDER_BLOCKED",
    "CANCEL_BLOCKED",
    "REBALANCE_BLOCKED",
    "AUTO_TRADE_BLOCKED",
    "phase14c_ibkr_readonly_preflight_config_validator",
)


@dataclass(frozen=True)
class PreflightConfigValidationRow:
    check_id: str
    check_name: str
    source_layer: str
    input_source: str
    required_config_key: str
    expected_value: str
    actual_value: str
    validation_status: str
    action_allowed: str
    real_connection_allowed: str
    tws_connection_allowed: str
    ibkr_api_request_allowed: str
    contract_qualification_allowed: str
    market_data_request_allowed: str
    historical_data_request_allowed: str
    order_action_allowed: str
    cancel_action_allowed: str
    rebalance_action_allowed: str
    auto_trade_allowed: str
    warning_flags: str
    notes: str
    timestamp_jst: str
    timestamp_et: str


FIELDNAMES = [
    "check_id",
    "check_name",
    "source_layer",
    "input_source",
    "required_config_key",
    "expected_value",
    "actual_value",
    "validation_status",
    "action_allowed",
    "real_connection_allowed",
    "tws_connection_allowed",
    "ibkr_api_request_allowed",
    "contract_qualification_allowed",
    "market_data_request_allowed",
    "historical_data_request_allowed",
    "order_action_allowed",
    "cancel_action_allowed",
    "rebalance_action_allowed",
    "auto_trade_allowed",
    "warning_flags",
    "notes",
    "timestamp_jst",
    "timestamp_et",
]


def _now_pair() -> tuple[str, str]:
    now_utc = datetime.now(ZoneInfo("UTC"))
    return (
        now_utc.astimezone(ZoneInfo("Asia/Tokyo")).isoformat(),
        now_utc.astimezone(ZoneInfo("America/New_York")).isoformat(),
    )


def _flags(extra: Iterable[str] = ()) -> str:
    values = list(DEFAULT_WARNING_FLAGS)
    for item in extra:
        if item and item not in values:
            values.append(item)
    return ";".join(values)


def _coerce_scalar(value: str) -> Any:
    value = value.strip()
    if not value:
        return ""
    if value in {"null", "Null", "NULL", "~"}:
        return None
    lowered = value.lower()
    if lowered == "true":
        return True
    if lowered == "false":
        return False

    if (
        (value.startswith('"') and value.endswith('"'))
        or (value.startswith("'") and value.endswith("'"))
    ):
        return value[1:-1]

    try:
        return int(value)
    except ValueError:
        return value


def _parse_basic_yaml(text: str) -> dict[str, Any]:
    result: dict[str, Any] = {}
    current_section: Optional[str] = None

    for raw_line in text.splitlines():
        line = raw_line.split("#", 1)[0].rstrip()
        if not line.strip():
            continue

        if not line.startswith((" ", "\t")):
            if ":" not in line:
                continue
            key, value = line.split(":", 1)
            key = key.strip()
            value = value.strip()
            if not value:
                current_section = key
                result.setdefault(key, {})
            else:
                current_section = None
                result[key] = _coerce_scalar(value)
            continue

        if current_section and ":" in line:
            key, value = line.strip().split(":", 1)
            section = result.setdefault(current_section, {})
            if isinstance(section, dict):
                section[key.strip()] = _coerce_scalar(value.strip())

    return result


def _load_config(path: str | Path) -> tuple[dict[str, Any], str]:
    path = Path(path)
    if not path.exists():
        return {}, f"input_source_missing:{path}"

    text = path.read_text(encoding="utf-8")

    try:
        import yaml  # type: ignore

        loaded = yaml.safe_load(text)
        if isinstance(loaded, dict):
            return loaded, ""
    except Exception:
        pass

    return _parse_basic_yaml(text), ""


def _get_dotted(config: dict[str, Any], dotted_key: str) -> Any:
    current: Any = config
    for part in dotted_key.split("."):
        if not isinstance(current, dict) or part not in current:
            return MISSING_TEXT
        current = current[part]
    return current


def _actual_text(value: Any) -> str:
    if value is MISSING_TEXT:
        return MISSING_TEXT
    if value is None:
        return "null"
    if value is True:
        return TRUE_TEXT
    if value is False:
        return FALSE_TEXT
    return str(value)


def _is_true(value: Any) -> bool:
    return value is True or (isinstance(value, str) and value.lower() == TRUE_TEXT)


def _is_false(value: Any) -> bool:
    return value is False or (isinstance(value, str) and value.lower() == FALSE_TEXT)


def _is_explicit_account_mode(value: Any) -> bool:
    return isinstance(value, str) and value.lower() in {"live", "paper"}


def _is_local_host(value: Any) -> bool:
    return isinstance(value, str) and value in {"127.0.0.1", "localhost"}


def _is_explicit_port(value: Any) -> bool:
    try:
        port = int(value)
    except (TypeError, ValueError):
        return False
    return 1 <= port <= 65535


def _is_explicit_client_id(value: Any) -> bool:
    try:
        client_id = int(value)
    except (TypeError, ValueError):
        return False
    return client_id >= 0


def _make_row(
    *,
    check_id: str,
    check_name: str,
    input_source: str,
    required_config_key: str,
    expected_value: str,
    actual_value: Any,
    passed: bool,
    timestamp_jst: str,
    timestamp_et: str,
    extra_flags: Iterable[str] = (),
) -> PreflightConfigValidationRow:
    status = PASS_TEXT if passed else FAIL_TEXT
    return PreflightConfigValidationRow(
        check_id=check_id,
        check_name=check_name,
        source_layer="Phase 14C",
        input_source=input_source,
        required_config_key=required_config_key,
        expected_value=expected_value,
        actual_value=_actual_text(actual_value),
        validation_status=status,
        action_allowed=FALSE_TEXT,
        real_connection_allowed=FALSE_TEXT,
        tws_connection_allowed=FALSE_TEXT,
        ibkr_api_request_allowed=FALSE_TEXT,
        contract_qualification_allowed=FALSE_TEXT,
        market_data_request_allowed=FALSE_TEXT,
        historical_data_request_allowed=FALSE_TEXT,
        order_action_allowed=FALSE_TEXT,
        cancel_action_allowed=FALSE_TEXT,
        rebalance_action_allowed=FALSE_TEXT,
        auto_trade_allowed=FALSE_TEXT,
        warning_flags=_flags([status, *extra_flags]),
        notes=(
            "Phase 14C local configuration validation only. "
            "No TWS connection, no IBKR connection, no IBKR API request, no real contract qualification, "
            "no market data request, no historical data request, and no trading action is allowed."
        ),
        timestamp_jst=timestamp_jst,
        timestamp_et=timestamp_et,
    )


def build_ibkr_readonly_preflight_config_validator_rows(
    input_source: str | Path = "config.yaml",
) -> list[PreflightConfigValidationRow]:
    timestamp_jst, timestamp_et = _now_pair()
    input_source_text = str(input_source)
    config, load_error = _load_config(input_source)

    rows: list[PreflightConfigValidationRow] = []

    if load_error:
        rows.append(
            _make_row(
                check_id="INPUT_SOURCE",
                check_name="Input source must exist and be readable",
                input_source=input_source_text,
                required_config_key="input_source",
                expected_value="existing_readable_yaml_file",
                actual_value=load_error,
                passed=False,
                timestamp_jst=timestamp_jst,
                timestamp_et=timestamp_et,
                extra_flags=["INPUT_SOURCE_MISSING"],
            )
        )
    else:
        rows.append(
            _make_row(
                check_id="INPUT_SOURCE",
                check_name="Input source must exist and be readable",
                input_source=input_source_text,
                required_config_key="input_source",
                expected_value="existing_readable_yaml_file",
                actual_value=input_source_text,
                passed=True,
                timestamp_jst=timestamp_jst,
                timestamp_et=timestamp_et,
                extra_flags=["INPUT_SOURCE_READABLE"],
            )
        )

    check_specs = [
        (
            "READ_ONLY_REQUIRED",
            "Read-only must be explicitly required",
            "ibkr.read_only_required",
            "true",
            _is_true,
            "READ_ONLY_REQUIRED_NOT_TRUE",
        ),
        (
            "ACCOUNT_MODE",
            "Account mode must be explicit",
            "ibkr.account_mode",
            "live_or_paper",
            _is_explicit_account_mode,
            "ACCOUNT_MODE_NOT_EXPLICIT",
        ),
        (
            "HOST",
            "TWS host must be local only",
            "ibkr.host",
            "127.0.0.1_or_localhost",
            _is_local_host,
            "HOST_NOT_LOCAL",
        ),
        (
            "PORT",
            "TWS port must be explicit",
            "ibkr.port",
            "integer_1_to_65535",
            _is_explicit_port,
            "PORT_NOT_EXPLICIT",
        ),
        (
            "CLIENT_ID",
            "IBKR client id must be explicit",
            "ibkr.client_id",
            "explicit_integer",
            _is_explicit_client_id,
            "CLIENT_ID_NOT_EXPLICIT",
        ),
        (
            "REAL_CONNECTION",
            "Real connection switch must remain disabled at validation phase",
            "ibkr.real_connection_allowed",
            "false",
            _is_false,
            "REAL_CONNECTION_SWITCH_NOT_FALSE",
        ),
        (
            "CONTRACT_QUALIFICATION",
            "Contract qualification switch must remain disabled",
            "ibkr.contract_qualification_allowed",
            "false",
            _is_false,
            "CONTRACT_QUALIFICATION_SWITCH_NOT_FALSE",
        ),
        (
            "MARKET_DATA",
            "Market data request switch must remain disabled",
            "ibkr.market_data_request_allowed",
            "false",
            _is_false,
            "MARKET_DATA_SWITCH_NOT_FALSE",
        ),
        (
            "HISTORICAL_DATA",
            "Historical data request switch must remain disabled",
            "ibkr.historical_data_request_allowed",
            "false",
            _is_false,
            "HISTORICAL_DATA_SWITCH_NOT_FALSE",
        ),
        (
            "TRADING_ACTIONS",
            "Trading action switch must remain disabled",
            "ibkr.trading_actions_allowed",
            "false",
            _is_false,
            "TRADING_ACTIONS_SWITCH_NOT_FALSE",
        ),
    ]

    for check_id, check_name, key, expected, validator, fail_flag in check_specs:
        actual = _get_dotted(config, key)
        passed = bool(validator(actual))
        rows.append(
            _make_row(
                check_id=check_id,
                check_name=check_name,
                input_source=input_source_text,
                required_config_key=key,
                expected_value=expected,
                actual_value=actual,
                passed=passed,
                timestamp_jst=timestamp_jst,
                timestamp_et=timestamp_et,
                extra_flags=[] if passed else [fail_flag],
            )
        )

    non_final_passed = all(row.validation_status == PASS_TEXT for row in rows)
    rows.append(
        _make_row(
            check_id="FINAL",
            check_name="Final IBKR read-only preflight config validation decision",
            input_source=input_source_text,
            required_config_key="phase14c.preflight_config_validator_status",
            expected_value="PASS",
            actual_value=PASS_TEXT if non_final_passed else FAIL_TEXT,
            passed=non_final_passed,
            timestamp_jst=timestamp_jst,
            timestamp_et=timestamp_et,
            extra_flags=(
                ["PHASE14C_PREFLIGHT_CONFIG_VALIDATOR_PASS"]
                if non_final_passed
                else ["PHASE14C_PREFLIGHT_CONFIG_VALIDATOR_FAIL"]
            ),
        )
    )

    return rows


def write_ibkr_readonly_preflight_config_validator_csv(
    path: str | Path,
    rows: Iterable[PreflightConfigValidationRow],
) -> None:
    path = Path(path)
    path.parent.mkdir(parents=True, exist_ok=True)
    row_list = list(rows)

    with path.open("w", encoding="utf-8", newline="") as f:
        writer = csv.DictWriter(f, fieldnames=FIELDNAMES)
        writer.writeheader()
        for row in row_list:
            writer.writerow({name: getattr(row, name) for name in FIELDNAMES})


def write_ibkr_readonly_preflight_config_validator_report(
    path: str | Path,
    rows: Iterable[PreflightConfigValidationRow],
    input_source: str | Path,
) -> None:
    path = Path(path)
    path.parent.mkdir(parents=True, exist_ok=True)
    row_list = list(rows)

    pass_count = sum(1 for row in row_list if row.validation_status == PASS_TEXT)
    fail_count = sum(1 for row in row_list if row.validation_status == FAIL_TEXT)
    final_status = PASS_TEXT if fail_count == 0 else FAIL_TEXT
    action_allowed_count = sum(1 for row in row_list if row.action_allowed == TRUE_TEXT)

    lines = [
        "# Phase 14C IBKR Read-Only Preflight Config Validator Report",
        "",
        "- phase: Phase 14C",
        "- scope: IBKR read-only preflight config validator",
        f"- input_source: {input_source}",
        f"- row_count: {len(row_list)}",
        f"- pass_count: {pass_count}",
        f"- fail_count: {fail_count}",
        f"- final_validation_status: {final_status}",
        f"- action_allowed_count: {action_allowed_count}",
        "- action_allowed: false",
        "- real_connection_allowed: false",
        "- tws_connection_allowed: false",
        "- ibkr_api_request_allowed: false",
        "- contract_qualification_allowed: false",
        "- market_data_request_allowed: false",
        "- historical_data_request_allowed: false",
        "- order_action_allowed: false",
        "- cancel_action_allowed: false",
        "- rebalance_action_allowed: false",
        "- auto_trade_allowed: false",
        "",
        "## Validation Rows",
        "",
        "| check_id | required_config_key | expected_value | actual_value | validation_status | action_allowed |",
        "|---|---|---|---|---|---|",
    ]

    for row in row_list:
        lines.append(
            "| "
            + " | ".join(
                [
                    row.check_id,
                    row.required_config_key,
                    row.expected_value,
                    row.actual_value,
                    row.validation_status,
                    row.action_allowed,
                ]
            )
            + " |"
        )

    lines.extend(
        [
            "",
            "## Final Decision",
            "",
            f"- Phase 14C final validation status: {final_status}",
            "- This phase validates local configuration only.",
            "- Passing validation does not authorize a real IBKR connection.",
            "- Passing validation does not authorize contract qualification, market data requests, historical data requests, or trading actions.",
            "- Any failed row must be corrected before later real read-only connection phases.",
            "",
            "## Safety Statement",
            "",
            "- no configuration file is modified",
            "- no TWS connection",
            "- no IBKR connection",
            "- no IBKR API request",
            "- no real contract qualification",
            "- no reqMktData",
            "- no reqHistoricalData",
            "- no order",
            "- no cancel",
            "- no rebalance",
            "- no auto trade",
            "",
        ]
    )

    path.write_text("\n".join(lines), encoding="utf-8")
