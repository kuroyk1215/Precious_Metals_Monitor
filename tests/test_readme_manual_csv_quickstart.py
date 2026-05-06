from pathlib import Path


def test_readme_manual_csv_quickstart_exists():
    text = Path("README.md").read_text(encoding="utf-8")

    required_phrases = [
        "Manual CSV Research Quickstart",
        "--manual-csv-smoke",
        "--manual-market-data-review-pack",
        "--manual-market-data-pipeline",
        "--generated-output-guard",
        "data/manual_market_data_template.csv",
        "data/manual_market_data_sample_valid.csv",
        "docs/manual_csv_operator_runbook.md",
        "action_allowed=false",
        "no IBKR connection",
        "no reqMktData",
        "no reqHistoricalData",
        "no order",
        "no cancel",
        "no rebalance",
        "no auto trade",
        "no automatic execution",
    ]

    missing = [phrase for phrase in required_phrases if phrase not in text]
    assert not missing, "Missing README quickstart phrases: " + ", ".join(missing)


def test_readme_manual_csv_quickstart_does_not_claim_execution():
    text = Path("README.md").read_text(encoding="utf-8").lower()

    forbidden_claims = [
        "auto order",
        "auto sell",
        "automatic order",
        "automatic trading",
        "places orders",
        "execute orders",
    ]

    hits = [phrase for phrase in forbidden_claims if phrase in text]
    assert not hits, "README contains forbidden execution claims: " + ", ".join(hits)
