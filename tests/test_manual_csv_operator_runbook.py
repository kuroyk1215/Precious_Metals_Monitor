from pathlib import Path


def test_manual_csv_operator_runbook_exists_and_has_required_sections():
    path = Path("docs/manual_csv_operator_runbook.md")
    assert path.exists()

    text = path.read_text(encoding="utf-8")

    required_phrases = [
        "Manual CSV Market Data Operator Runbook",
        "Safety Boundary",
        "manual CSV only",
        "explicit manual trigger only",
        "action_allowed=false",
        "no IBKR connection",
        "no reqMktData",
        "no reqHistoricalData",
        "no order",
        "no cancel",
        "no rebalance",
        "no auto trade",
        "no automatic execution",
        "data/manual_market_data_template.csv",
        "data/manual_market_data_sample_valid.csv",
        "--manual-market-data-adapter",
        "--integrate-manual-market-data",
        "--manual-market-data-pipeline",
        "--validate-filled-manual-scenario",
        "Files That Should Usually Not Be Committed",
    ]

    missing = [phrase for phrase in required_phrases if phrase not in text]
    assert not missing, "Missing required runbook phrases: " + ", ".join(missing)


def test_manual_csv_operator_runbook_does_not_claim_auto_execution():
    text = Path("docs/manual_csv_operator_runbook.md").read_text(encoding="utf-8").lower()

    forbidden_claims = [
        "auto order",
        "auto sell",
        "automatic order",
        "automatic trading",
        "places orders",
        "execute orders",
    ]

    hits = [phrase for phrase in forbidden_claims if phrase in text]
    assert not hits, "Runbook contains forbidden execution claims: " + ", ".join(hits)
