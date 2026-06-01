import argparse
import sys

from src.monitor import PreciousMetalsMonitor


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Precious Metals Monitor")
    parser.add_argument("--config", default="config.yaml")
    parser.add_argument("--watchlist", default="watchlist.yaml")
    parser.add_argument("--mock", action="store_true", help="run with built-in mock data and skip IBKR")
    parser.add_argument("--ibkr-smoke", action="store_true", help="run IBKR read-only smoke test")
    parser.add_argument("--contract-search", help="search IBKR contracts by query string (read-only)")
    parser.add_argument("--calibrate-model", action="store_true", help="run phase-3 theoretical pricing model calibration (read-only)")
    parser.add_argument("--pricing-mock", action="store_true", help="run phase-3 pricing model framework verification with mock inputs")
    parser.add_argument("--calibration-csv", help="run phase-3B conversion_factor calibration using historical sample csv")
    parser.add_argument("--validate-history", help="run phase-3C historical import validator")
    parser.add_argument("--build-history", help="run phase-4A raw history builder from source manifest")
    parser.add_argument("--source-audit", help="run phase-4B-0 source adapter audit from provider manifest")
    parser.add_argument("--ibkr-historical-plan", action="store_true", help="run phase-4B-1 IBKR historical adapter plan-only workflow")
    parser.add_argument("--ibkr-historical-fetch", action="store_true", help="run phase-4B-2A IBKR historical fetch workflow (dry-run default)")
    parser.add_argument("--execute-ibkr-historical-fetch", action="store_true", help="explicitly execute read-only IBKR historical fetch")
    parser.add_argument("--quality-gate", help="run phase-4C historical data quality gate for candidate csv")
    parser.add_argument("--historical-pipeline-check", action="store_true", help="run phase-4D manual historical pipeline integration check")
    parser.add_argument("--upstream-factors", action="store_true", help="run phase-5B upstream precious metals factor monitor")
    parser.add_argument("--theoretical-pricing", nargs="?", const="", help="run phase-5C ETF theoretical pricing from upstream snapshot csv")
    parser.add_argument("--actual-etf-prices", action="store_true", help="run phase-5D manual/mock ETF actual price snapshot")
    parser.add_argument("--deviation-check", nargs="*", help="run phase-5D deviation check: optional [theoretical_csv actual_csv]")
    parser.add_argument("--reference-signals", nargs="?", const="", help="run phase-5E manual reference signal layer from deviation snapshot csv")
    parser.add_argument("--daily-trade-plan", nargs="?", const="", help="run phase-5F daily manual trade plan from reference signal snapshot csv")
    parser.add_argument("--strategy-plan", nargs="?", const="", help="run phase-5G multi-horizon manual strategy plan from daily trade plan snapshot csv")
    parser.add_argument("--manual-research-pipeline", action="store_true", help="run phase-5H explicit manual end-to-end research pipeline")
    parser.add_argument("--market-data-source-plan", action="store_true", help="run phase-6A real market data source adapter planning only")
    parser.add_argument("--manual-market-data-adapter", nargs="?", const="", help="run phase-6B manual CSV market data adapter skeleton")
    parser.add_argument("--integrate-manual-market-data", nargs="?", const="", help="run phase-6C manual market data snapshot integration")
    parser.add_argument("--manual-market-data-pipeline", nargs="?", const="", help="run phase-6D manual CSV market data end-to-end research pipeline")
    parser.add_argument("--validate-filled-manual-scenario", nargs="?", const="", help="run phase-6E filled manual CSV scenario validation")
    parser.add_argument("--manual-market-data-review-pack", nargs="?", const="", help="run phase-6G manual CSV pipeline output review pack")
    parser.add_argument("--generated-output-guard", action="store_true", help="run phase-6H generated output cleanup guard")
    parser.add_argument("--manual-csv-smoke", nargs="?", const="", help="run phase-6I final manual CSV workflow smoke command")
    parser.add_argument("--market-data-provider-registry", action="store_true", help="run phase-7A market data provider registry skeleton")
    parser.add_argument("--market-data-adapter-contract", action="store_true", help="run phase-7B market data adapter interface contract")
    parser.add_argument("--manual-csv-adapter-interface", nargs="?", const="", help="run phase-7C manual CSV adapter through market data interface")
    parser.add_argument("--adapter-interface-bridge", nargs="?", const="", help="run phase-7D adapter interface to pipeline bridge")
    parser.add_argument("--research-trading-plan", nargs="?", const="", help="run phase-8A final manual research trading plan from review pack csv")
    parser.add_argument("--manual-research-trading-pipeline", nargs="?", const="", help="run phase-8C one-command manual research trading pipeline")
    parser.add_argument("--final-research-review-pack", nargs="?", const="", help="run phase-8D final manual research review pack")
    parser.add_argument("--market-data-provider-readiness", action="store_true", help="run phase-9A market data provider readiness planning")
    parser.add_argument("--market-data-provider-config-audit", nargs="?", const="", help="run phase-9B market data provider config audit")
    parser.add_argument("--market-data-provider-selector", nargs="?", const="", help="run phase-9D market data provider selector and fallback planner")
    parser.add_argument("--live-provider-interface-check", nargs="?", const="", help="run phase-10A live provider interface safety check")
    parser.add_argument("--live-provider-request-gate", nargs="?", const="", help="run phase-10B live provider request gate safety check")
    parser.add_argument("--live-provider-mock-adapter", nargs="?", const="", help="run phase-10C live provider mock adapter")
    parser.add_argument("--live-data-quality-gate", nargs="?", const="", help="run phase-10D live/mock data quality gate")
    parser.add_argument("--live-research-review-pack", nargs="?", const="", help="run phase-10E live/mock research review pack bridge")
    parser.add_argument("--live-final-research-review-pack", nargs="?", const="", help="run phase-10F live/mock final research review pack")
    parser.add_argument("--ibkr-live-provider-adapter-check", nargs="?", const="", help="run phase-10G IBKR live provider adapter skeleton check")
    parser.add_argument("--ibkr-contract-mapping-plan", nargs="?", const="", help="run phase-10H IBKR contract mapping plan")
    parser.add_argument("--ibkr-contract-qualification-dry-run", nargs="?", const="", help="run phase-10I IBKR contract qualification dry-run plan")
    parser.add_argument("--ibkr-contract-qualification-execution-guard", nargs="?", const="", help="run phase-10J IBKR contract qualification execution guard")
    parser.add_argument("--ibkr-readonly-qualification-precheck", nargs="?", const="", help="run phase-10K IBKR read-only qualification precheck")
    parser.add_argument("--ibkr-readonly-qualification-runbook", nargs="?", const="", help="run phase-10L IBKR read-only qualification runbook")
    parser.add_argument("--ibkr-readonly-qualification-go-no-go", nargs="?", const="", help="run phase-10M IBKR read-only qualification go/no-go summary")
    parser.add_argument("--ibkr-readonly-qualification-config-template", nargs="?", const="", help="run phase-11A IBKR read-only qualification config template")
    parser.add_argument("--ibkr-readonly-qualification-config-audit", nargs="?", const="", help="run phase-11B IBKR read-only qualification config audit")
    parser.add_argument("--ibkr-readonly-qualification-config-apply-plan", nargs="?", const="", help="run phase-11C IBKR read-only qualification config apply plan")
    parser.add_argument("--ibkr-readonly-qualification-config-final-gate", nargs="?", const="", help="run phase-11D IBKR read-only qualification config final gate")
    parser.add_argument("--ibkr-readonly-qualification-safety-summary", nargs="?", const="", help="run phase-11E IBKR read-only qualification full safety summary")
    parser.add_argument("--ibkr-readonly-qualification-candidate-resolver", nargs="?", const="", help="run phase-12A IBKR read-only qualification candidate resolver")
    parser.add_argument("--ibkr-readonly-qualification-candidate-review-pack", nargs="?", const="", help="run phase-12B IBKR read-only qualification candidate review pack")
    parser.add_argument("--ibkr-readonly-qualification-candidate-final-gate", nargs="?", const="", help="run phase-12C IBKR read-only qualification candidate final gate")
    parser.add_argument("--ibkr-readonly-qualification-candidate-safety-summary", nargs="?", const="", help="run phase-12D IBKR read-only qualification candidate safety summary")
    parser.add_argument(
        "--ibkr-readonly-qualification-operator-decision-ledger",
        nargs="?",
        const="",
        default=None,
        help="Build Phase 12E IBKR read-only qualification operator decision ledger without connecting to IBKR.",
    )
    parser.add_argument(
        "--ibkr-readonly-qualification-operator-approval-stub",
        nargs="?",
        const="",
        default=None,
        help="Build Phase 12F IBKR read-only qualification operator approval stub without connecting to IBKR.",
    )
    parser.add_argument(
        "--ibkr-readonly-qualification-effective-approval-gate",
        nargs="?",
        const="",
        default=None,
        help="Build Phase 12G IBKR read-only qualification effective approval gate without connecting to IBKR.",
    )
    parser.add_argument(
        "--ibkr-readonly-qualification-final-authorization-packet",
        nargs="?",
        const="",
        default=None,
        help="Build Phase 12H IBKR read-only qualification final authorization packet without connecting to IBKR.",
    )
    parser.add_argument(
        "--ibkr-readonly-qualification-phase12-closure-report",
        nargs="?",
        const="",
        default=None,
        help="Build Phase 12I IBKR read-only qualification Phase 12 closure report without connecting to IBKR.",
    )
    parser.add_argument(
        "--ibkr-readonly-qualification-sandbox-design",
        nargs="?",
        const="",
        default=None,
        help="Build Phase 13A IBKR read-only qualification sandbox design report without connecting to IBKR.",
    )
    parser.add_argument(
        "--ibkr-readonly-qualification-sandbox-input-contract",
        nargs="?",
        const="",
        default=None,
        help="Build Phase 13B IBKR read-only qualification sandbox input contract report without connecting to IBKR.",
    )
    parser.add_argument(
        "--ibkr-readonly-qualification-sandbox-input-validator",
        nargs="?",
        const="",
        default=None,
        help="Build Phase 13C IBKR read-only qualification sandbox input validator report without connecting to IBKR.",
    )
    parser.add_argument(
        "--ibkr-readonly-qualification-sandbox-qualification-simulator",
        nargs="?",
        const="",
        default=None,
        help="Build Phase 13D IBKR read-only qualification sandbox qualification simulator report without connecting to IBKR.",
    )
    parser.add_argument(
        "--ibkr-readonly-qualification-sandbox-result-pack",
        nargs="?",
        const="",
        default=None,
        help="Build Phase 13E IBKR read-only qualification sandbox result pack report without connecting to IBKR.",
    )
    parser.add_argument(
        "--ibkr-readonly-qualification-sandbox-safety-gate",
        nargs="?",
        const="",
        default=None,
        help="Build Phase 13F IBKR read-only qualification sandbox safety gate report without connecting to IBKR.",
    )
    parser.add_argument(
        "--ibkr-readonly-qualification-sandbox-final-review-pack",
        nargs="?",
        const="",
        default=None,
        help="Build Phase 13G IBKR read-only qualification sandbox final review pack report without connecting to IBKR.",
    )
    parser.add_argument(
        "--ibkr-readonly-qualification-sandbox-closure-report",
        nargs="?",
        const="",
        default=None,
        help="Build Phase 13H IBKR read-only qualification sandbox closure report without connecting to IBKR.",
    )
    parser.add_argument(
        "--ibkr-readonly-preflight-guard-design",
        nargs="?",
        const="",
        default=None,
        help="Build Phase 14A IBKR read-only preflight guard design report without connecting to IBKR.",
    )
    parser.add_argument(
        "--ibkr-readonly-preflight-config-contract",
        nargs="?",
        const="",
        default=None,
        help="Build Phase 14B IBKR read-only preflight config contract report without connecting to IBKR.",
    )
    parser.add_argument(
        "--ibkr-readonly-preflight-config-validator",
        nargs="?",
        const="",
        default=None,
        help="Build Phase 14C IBKR read-only preflight config validator report without connecting to IBKR.",
    )
    parser.add_argument(
        "--ibkr-readonly-preflight-config-template",
        nargs="?",
        const="",
        default=None,
        help="Build Phase 14D IBKR read-only preflight config template without connecting to IBKR.",
    )
    parser.add_argument(
        "--ibkr-readonly-preflight-config-apply-plan",
        nargs="?",
        const="",
        default=None,
        help="Build Phase 14E IBKR read-only preflight config apply plan without connecting to IBKR.",
    )
    parser.add_argument(
        "--ibkr-readonly-preflight-final-gate",
        nargs="?",
        const="",
        default=None,
        help="Build Phase 14F IBKR read-only preflight final gate without connecting to IBKR.",
    )
    parser.add_argument(
        "--ibkr-readonly-preflight-safe-config-merge-plan",
        nargs="?",
        const="",
        default=None,
        help="Build Phase 14G IBKR read-only preflight safe config merge plan without connecting to IBKR.",
    )
    parser.add_argument(
        "--ibkr-readonly-preflight-profile-aware-config-plan",
        nargs="?",
        const="",
        default=None,
        help="Build Phase 14H IBKR read-only preflight profile-aware config plan without connecting to IBKR.",
    )
    parser.add_argument(
        "--ibkr-readonly-preflight-profile-aware-final-gate",
        nargs="?",
        const="",
        default=None,
        help="Build Phase 14I IBKR read-only preflight profile-aware final gate without connecting to IBKR.",
    )
    parser.add_argument(
        "--ibkr-readonly-tws-environment-checklist",
        nargs="?",
        const="",
        default=None,
        help="Build Phase 15A IBKR read-only TWS environment checklist without connecting to IBKR.",
    )
    parser.add_argument(
        "--ibkr-readonly-external-readiness-pack",
        nargs="?",
        const="",
        default=None,
        help="Build Phase 15B-15D IBKR read-only external readiness pack without connecting to IBKR.",
    )
    parser.add_argument(
        "--ibkr-readonly-connection-preflight-pack",
        nargs="?",
        const="",
        default=None,
        help="Build Phase 16A-16C IBKR read-only connection preflight pack without connecting to IBKR.",
    )
    parser.add_argument(
        "--ibkr-readonly-authorization-pack",
        nargs="?",
        const="",
        default=None,
        help="Build Phase 16D-16F IBKR read-only authorization pack without connecting to IBKR.",
    )
    parser.add_argument(
        "--ibkr-first-readonly-connect-disconnect",
        nargs="?",
        const="",
        default=None,
        help="Build Phase 17A IBKR first read-only connect/disconnect report. Dry-run unless execute flag is set.",
    )
    parser.add_argument(
        "--execute-ibkr-readonly-connect-disconnect",
        action="store_true",
        help="Explicitly execute Phase 17A connect/disconnect only. No market data, historical data, qualification, or trading.",
    )
    parser.add_argument(
        "--ibkr-readonly-connection-log-heartbeat-guard",
        nargs="?",
        const="",
        default=None,
        help="Build Phase 17C-17D IBKR read-only connection log heartbeat guard. Dry-run unless execute flag is set.",
    )
    parser.add_argument(
        "--execute-ibkr-readonly-heartbeat-guard",
        action="store_true",
        help="Explicitly execute Phase 17C-17D metadata-only connection heartbeat guard.",
    )
    parser.add_argument(
        "--ibkr-readonly-nontrading-account-server-info-pack",
        nargs="?",
        const="",
        default=None,
        help="Build Phase 18A-18C IBKR read-only non-trading account/server info pack. Dry-run unless execute flag is set.",
    )
    parser.add_argument(
        "--execute-ibkr-readonly-nontrading-info",
        action="store_true",
        help="Explicitly execute Phase 18A-18C non-trading account/server info read.",
    )
    parser.add_argument(
        "--ibkr-readonly-contract-info-preflight-pack",
        nargs="?",
        const="",
        default=None,
        help="Build Phase 19A-19C IBKR read-only contract info preflight pack. Dry-run unless execute flag is set.",
    )
    parser.add_argument(
        "--execute-ibkr-readonly-contract-info",
        action="store_true",
        help="Explicitly execute Phase 19A-19C read-only contract details read.",
    )
    parser.add_argument(
        "--ibkr-readonly-market-data-snapshot-preflight-pack",
        nargs="?",
        const="",
        default=None,
        help="Build Phase 20A-20C IBKR read-only market data snapshot preflight pack. Dry-run unless execute flag is set.",
    )
    parser.add_argument(
        "--execute-ibkr-readonly-market-data-snapshot",
        action="store_true",
        help="Explicitly execute Phase 20A-20C one-shot non-streaming market data snapshot.",
    )
    parser.add_argument(
        "--ibkr-readonly-market-data-entitlement-diagnostic",
        nargs="?",
        const="",
        default=None,
        help="Build Phase 20D IBKR market data entitlement / delayed-data diagnostic. Dry-run unless execute flag is set.",
    )
    parser.add_argument(
        "--execute-ibkr-readonly-market-data-entitlement-diagnostic",
        action="store_true",
        help="Explicitly execute Phase 20D market data entitlement diagnostic using one snapshot attempt.",
    )
    parser.add_argument(
        "--primary-metals-market-inference-layer",
        nargs="?",
        const="",
        default=None,
        help="Build Phase 21A-21C primary metals market inference layer without IBKR connection.",
    )
    parser.add_argument(
        "--primary-metals-inference-research-plan-integration",
        nargs="?",
        const="",
        default=None,
        help="Build Phase 22A-22C primary metals inference research plan integration without IBKR connection.",
    )
    parser.add_argument(
        "--primary-metals-final-review-pack-integration",
        nargs="?",
        const="",
        default=None,
        help="Build Phase 23A-23C primary metals final review pack integration without IBKR connection.",
    )
    parser.add_argument(
        "--final-research-trading-plan-output",
        nargs="?",
        const="",
        default=None,
        help="Build Phase 24A-24C final research trading plan output without IBKR connection.",
    )
    parser.add_argument(
        "--final-research-plan-orchestrator",
        nargs="?",
        const="",
        default=None,
        help="Build Phase 25A-27C one-command final research plan orchestrator without IBKR connection.",
    )
    parser.add_argument(
        "--report-template-daily-log-telegram-ready-output",
        nargs="?",
        const="",
        default=None,
        help="Build Phase 28A-30C report template, daily log, and Telegram-ready text without sending.",
    )
    parser.add_argument(
        "--scheduler-stub-final-readme-release-checklist",
        nargs="?",
        const="",
        default=None,
        help="Build Phase 31A-32C scheduler stub, final README, and release checklist without external execution.",
    )
    parser.add_argument(
        "--batch-i-real-market-env-check",
        action="store_true",
        help="Build Phase 469-471 Batch I real-market environment verification skeleton without connecting or sending.",
    )
    parser.add_argument(
        "--batch-i-final-integration-audit-gate",
        action="store_true",
        help="Build Phase 475-477 Batch I final integration audit gate without connecting or sending.",
    )
    parser.add_argument(
        "--batch-j-strategy-threshold-refinement",
        action="store_true",
        help="Build Phase 478-481 Batch J strategy threshold refinement skeleton without connecting or sending.",
    )
    parser.add_argument(
        "--batch-j-final-integration-audit-gate",
        action="store_true",
        help="Build Phase 482-485 Batch J final integration audit gate without connecting or sending.",
    )
    parser.add_argument(
        "--dashboard-artifact-reader",
        action="store_true",
        help="Build Phase 486-489 local read-only dashboard artifact reader summary without UI, connecting, or sending.",
    )
    parser.add_argument(
        "--telegram-dry-run-payload",
        action="store_true",
        help="Build Phase 490-493 Telegram-ready dry-run payload without token read, API call, or real send.",
    )
    parser.add_argument(
        "--telegram-approval-gate",
        action="store_true",
        help="Build Phase 490-493 Telegram human approval gate without token read, API call, or real send.",
    )
    parser.add_argument(
        "--telegram-manual-send-archive",
        action="store_true",
        help="Build Phase 494-497 Telegram manual-send archive skeleton without token read, API call, network send, or real send.",
    )
    parser.add_argument(
        "--multi-market-symbol-universe",
        action="store_true",
        help="Build Phase 498-502 JP/CN/US static symbol universe schema without connecting, quotes, account reads, or trading.",
    )
    parser.add_argument(
        "--multi-market-adapter-skeleton",
        action="store_true",
        help="Build Phase 503-508 JP/CN/US static adapter skeleton without connecting, quotes, qualification, account reads, or trading.",
    )
    parser.add_argument(
        "--multi-market-final-audit-freeze-summary",
        action="store_true",
        help="Build Phase 509-512 multi-market final audit and freeze summary without connecting, sending, reading account/positions, or trading.",
    )
    parser.add_argument(
        "--real-market-env-readiness-preflight",
        action="store_true",
        help="Build Phase 513-516 real-market environment readiness preflight without connecting, probing, sending, reading account/positions, requesting data, qualifying contracts, or trading.",
    )
    parser.add_argument(
        "--ibkr-connection-permission-gate",
        action="store_true",
        help="Build Phase 517-520 IBKR connection permission gate and operator approval packet without connecting, probing, sending, reading account/positions, requesting data, qualifying contracts, or trading.",
    )
    parser.add_argument(
        "--ibkr-connection-operator-runbook",
        action="store_true",
        help="Build Phase 521-524 IBKR connection operator runbook and local checklist without connecting, probing, sending, reading account/positions, requesting data, qualifying contracts, or trading.",
    )
    parser.add_argument(
        "--ibkr-connect-dryrun-approval-packet",
        action="store_true",
        help="Build Phase 525-528 IBKR connect-only dry-run approval packet without connecting, probing, sending, reading account/positions, requesting data, qualifying contracts, or trading.",
    )
    parser.add_argument(
        "--ibkr-connect-execution-skeleton-review",
        action="store_true",
        help="Build Phase 529-532 IBKR connect-only execution skeleton review without execute CLI, connecting, probing, sending, reading account/positions, requesting data, qualifying contracts, or trading.",
    )
    parser.add_argument(
        "--ibkr-connect-final-permission-gate",
        action="store_true",
        help="Build Phase 533-536 IBKR connect final permission gate without connecting, probing, sending, reading account/positions, requesting data, qualifying contracts, or trading.",
    )
    parser.add_argument(
        "--ibkr-connect-only-dryrun-execute",
        action="store_true",
        help="Execute one Phase 537-540 IBKR/TWS/Gateway connect/disconnect dry-run only; requires --operator-approved.",
    )
    parser.add_argument(
        "--ibkr-connection-result-archive",
        action="store_true",
        help="Build Phase 541-544 IBKR connection result archive without connecting, probing, requesting data, reading account/positions, qualifying contracts, trading, or Telegram real send.",
    )
    parser.add_argument(
        "--contract-qualification-permission-gate",
        action="store_true",
        help="Build Phase 545-548 contract qualification permission gate without connecting, probing, requesting data, reading account/positions, qualifying contracts, trading, or Telegram real send.",
    )
    parser.add_argument(
        "--single-symbol-contract-qualification-guard",
        action="store_true",
        help="Build Phase 549-552 single-symbol contract qualification guard without connecting, probing, requesting data, reading account/positions, qualifying contracts, trading, or Telegram real send.",
    )
    parser.add_argument(
        "--us-etf-contract-qualification-execute",
        action="store_true",
        help="Execute one Phase 553-556 GLD/SLV contract qualification run; requires --operator-approved.",
    )
    parser.add_argument(
        "--us-etf-symbol-master-snapshot",
        action="store_true",
        help="Build Phase 557-560 GLD/SLV symbol master snapshot from archived qualification results only.",
    )
    parser.add_argument(
        "--us-etf-market-data-readiness-guard",
        action="store_true",
        help="Build Phase 561-568 GLD/SLV market data permission gate and execute guard artifacts only.",
    )
    parser.add_argument(
        "--us-etf-market-data-execute",
        action="store_true",
        help="Execute one Phase 569-572 GLD/SLV market data request run; requires --operator-approved.",
    )
    parser.add_argument(
        "--us-etf-market-data-classifier-readiness",
        action="store_true",
        help="Build Phase 573-580 GLD/SLV market data permission-denied classifier readiness artifacts only.",
    )
    parser.add_argument(
        "--us-etf-operator-packet-artifact-integration",
        action="store_true",
        help="Build Phase 581-588 GLD/SLV operator packet artifact integration without external actions.",
    )
    parser.add_argument(
        "--us-etf-dashboard-readonly",
        action="store_true",
        help="Build Phase 589-600 GLD/SLV read-only dashboard artifacts without external actions.",
    )
    parser.add_argument(
        "--telegram-manual-send-skeleton",
        action="store_true",
        help="Build Phase 601-616 GLD/SLV Telegram manual-send skeleton artifacts without token read, network access, or real send.",
    )
    parser.add_argument(
        "--us-only-mvp-final-audit-freeze",
        action="store_true",
        help="Build Phase 617-624 US-only GLD/SLV MVP final audit freeze artifacts without external actions.",
    )
    parser.add_argument(
        "--us-only-mvp-archive-handoff-pack",
        action="store_true",
        help="Build Phase 625-632 US-only GLD/SLV MVP archive handoff pack without external actions.",
    )
    parser.add_argument(
        "--dashboard-ui-enhancement-pack",
        action="store_true",
        help="Build Phase 633-640 local static read-only dashboard UI enhancement pack without external actions.",
    )
    parser.add_argument(
        "--dashboard-ui-v2-data-panel-pack",
        action="store_true",
        help="Build Phase 641-648 local static dashboard UI v2 data panel pack without external actions.",
    )
    parser.add_argument(
        "--dashboard-ui-v3-layout-polish-pack",
        action="store_true",
        help="Build Phase 649-656 local static dashboard UI v3 layout polish pack without external actions.",
    )
    parser.add_argument(
        "--dashboard-visual-density-card-system-pack",
        action="store_true",
        help="Build Phase 657-664 local static dashboard visual density card system pack without external actions.",
    )
    parser.add_argument(
        "--dashboard-icon-timeline-artifact-polish-pack",
        action="store_true",
        help="Build Phase 665-672 local static dashboard icon timeline artifact polish pack without external actions.",
    )
    parser.add_argument(
        "--dashboard-chinese-template-soft-polish-pack",
        action="store_true",
        help="Build Phase 673-680 local static dashboard Chinese template-inspired soft polish pack without external actions.",
    )
    parser.add_argument(
        "--dashboard-high-tech-trading-visual-rebuild-pack",
        action="store_true",
        help="Build Phase 681-696 local static dashboard high-tech trading visual rebuild pack without external actions.",
    )
    parser.add_argument(
        "--dashboard-ui-static-visual-freeze-pack",
        action="store_true",
        help="Build Phase 697-704 local static dashboard UI QA and visual freeze pack without external actions.",
    )
    parser.add_argument(
        "--post-ui-freeze-handoff-data-roadmap-pack",
        action="store_true",
        help="Build Phase 705-720 post-UI freeze handoff and data source roadmap pack without external actions.",
    )
    parser.add_argument(
        "--interactive-local-research-platform-ui-shell-pack",
        action="store_true",
        help="Build Phase 721-760 interactive local research platform UI shell pack without external actions.",
    )
    parser.add_argument(
        "--local-backend-api-shell-pack",
        action="store_true",
        help="Build Phase 761-800 localhost read-only backend API shell pack without external actions.",
    )
    parser.add_argument(
        "--ui-driven-local-research-platform-mvp-pack",
        action="store_true",
        help="Build Phase 801-1000 UI-driven local research platform MVP pack without external actions.",
    )
    parser.add_argument(
        "--productized-ui-public-data-intake-pack",
        action="store_true",
        help="Build Phase 1001-1120 productized Chinese research workbench and public data intake preparation pack without external actions.",
    )
    parser.add_argument(
        "--productized-ui-user-surface-cleanup-pack",
        action="store_true",
        help="Build Phase 1121-1160 productized UI user surface cleanup pack without external actions.",
    )
    parser.add_argument(
        "--public-data-intake-prep",
        action="store_true",
        help="Build public data intake preparation artifacts without network, live price ingestion, or trading output.",
    )
    parser.add_argument(
        "--local-workflow-run",
        action="store_true",
        help="Run local read-only workflow preview artifact generation without external actions.",
    )
    parser.add_argument(
        "--local-research-report-build",
        action="store_true",
        help="Build GLD / SLV local research report framework without real market data.",
    )
    parser.add_argument(
        "--local-ui-server",
        action="store_true",
        help="Start the Phase 761-800 localhost read-only dashboard/API server.",
    )
    parser.add_argument("--local-ui-host", default="127.0.0.1", help="Local UI server host, default 127.0.0.1.")
    parser.add_argument("--local-ui-port", type=int, default=8765, help="Local UI server port, default 8765.")
    parser.add_argument(
        "--operator-approved",
        action="store_true",
        help="Operator approval flag required by gated real IBKR execution commands.",
    )
    return parser.parse_args()


def main() -> int:
    args = parse_args()

    if args.ibkr_connect_only_dryrun_execute:
        from src.operator_ibkr_connect_only_dryrun_execute import (
            OUTPUT_FIELDS,
            generate_ibkr_connect_only_dryrun_execute,
            output_status_values,
        )

        rows = generate_ibkr_connect_only_dryrun_execute(
            operator_approved=args.operator_approved,
            config_path=args.config,
        )
        row = rows[0]
        values = output_status_values(row)
        print("[IBKR_CONNECT_ONLY_DRYRUN_EXECUTE] generated")
        for field in OUTPUT_FIELDS:
            print(f"{field}={values[field]}")
        print(f"connect_only_dryrun_status={values['connect_only_dryrun_status']}")
        print(f"ibkr_connected={values['ibkr_connected']}")
        print(f"ibkr_disconnected={values['ibkr_disconnected']}")
        print(f"error_type={row['error_type']}")
        print("csv=operator_ibkr_connect_only_dryrun_execute.csv")
        print("report=reports/operator_ibkr_connect_only_dryrun_execute_report.md")
        if not args.operator_approved:
            print("DENIED / OPERATOR_APPROVAL_REQUIRED")
            return 2
        print(
            "NOTICE: Phase 537-540 connect-only dry-run executed at most one real connect/disconnect attempt. "
            "No market data request, no account reads, no position reads, no historical data request, "
            "no contract qualification, no orders, no cancellation, no rebalance, no Telegram real send, "
            "and no production-ready or market-data-verified reclassification."
        )
        return 0

    if args.ibkr_connection_result_archive:
        from src.operator_ibkr_connection_result_archive import main as archive_main

        return archive_main([])

    if args.contract_qualification_permission_gate:
        from src.operator_contract_qualification_permission_gate import main as gate_main

        return gate_main([])

    if args.single_symbol_contract_qualification_guard:
        from src.operator_single_symbol_contract_qualification_guard import main as guard_main

        return guard_main([])

    if args.us_etf_contract_qualification_execute:
        from src.operator_us_etf_contract_qualification_execute import main as qualification_main

        argv = ["--config", args.config]
        if args.operator_approved:
            argv.append("--operator-approved")
        return qualification_main(argv)

    if args.us_etf_symbol_master_snapshot:
        from src.operator_us_etf_symbol_master_snapshot import main as symbol_master_main

        return symbol_master_main([])

    if args.us_etf_market_data_readiness_guard:
        from src.operator_us_etf_market_data_readiness_guard import main as readiness_guard_main

        return readiness_guard_main([])

    if args.us_etf_market_data_execute:
        from src.operator_us_etf_market_data_execute import main as market_data_execute_main

        argv = ["--config", args.config]
        if args.operator_approved:
            argv.append("--operator-approved")
        return market_data_execute_main(argv)

    if args.us_etf_market_data_classifier_readiness:
        from src.operator_us_etf_market_data_classifier_readiness import (
            main as classifier_readiness_main,
        )

        return classifier_readiness_main([])

    if args.us_etf_operator_packet_artifact_integration:
        from src.operator_us_etf_operator_packet_artifact_integration import (
            main as operator_packet_main,
        )

        return operator_packet_main([])

    if args.us_etf_dashboard_readonly:
        from src.operator_us_etf_dashboard_readonly import main as dashboard_readonly_main

        return dashboard_readonly_main([])

    if args.telegram_manual_send_skeleton:
        from src.operator_telegram_manual_send_skeleton import (
            main as telegram_manual_send_skeleton_main,
        )

        return telegram_manual_send_skeleton_main([])

    if args.us_only_mvp_final_audit_freeze:
        from src.operator_us_only_mvp_final_audit_freeze import (
            main as us_only_mvp_final_audit_freeze_main,
        )

        return us_only_mvp_final_audit_freeze_main([])

    if args.us_only_mvp_archive_handoff_pack:
        from src.operator_us_only_mvp_archive_handoff_pack import (
            main as us_only_mvp_archive_handoff_pack_main,
        )

        return us_only_mvp_archive_handoff_pack_main([])

    if args.dashboard_ui_enhancement_pack:
        from src.operator_dashboard_ui_enhancement_pack import (
            main as dashboard_ui_enhancement_pack_main,
        )

        return dashboard_ui_enhancement_pack_main([])

    if args.dashboard_ui_v2_data_panel_pack:
        from src.operator_dashboard_ui_v2_data_panel_pack import (
            main as dashboard_ui_v2_data_panel_pack_main,
        )

        return dashboard_ui_v2_data_panel_pack_main([])

    if args.dashboard_ui_v3_layout_polish_pack:
        from src.operator_dashboard_ui_v3_layout_polish_pack import (
            main as dashboard_ui_v3_layout_polish_pack_main,
        )

        return dashboard_ui_v3_layout_polish_pack_main([])

    if args.dashboard_visual_density_card_system_pack:
        from src.operator_dashboard_visual_density_card_system_pack import (
            main as dashboard_visual_density_card_system_pack_main,
        )

        return dashboard_visual_density_card_system_pack_main([])

    if args.dashboard_icon_timeline_artifact_polish_pack:
        from src.operator_dashboard_icon_timeline_artifact_polish_pack import (
            main as dashboard_icon_timeline_artifact_polish_pack_main,
        )

        return dashboard_icon_timeline_artifact_polish_pack_main([])

    if args.dashboard_chinese_template_soft_polish_pack:
        from src.operator_dashboard_chinese_template_soft_polish_pack import (
            main as dashboard_chinese_template_soft_polish_pack_main,
        )

        return dashboard_chinese_template_soft_polish_pack_main([])

    if args.dashboard_high_tech_trading_visual_rebuild_pack:
        from src.operator_dashboard_high_tech_trading_visual_rebuild_pack import (
            main as dashboard_high_tech_trading_visual_rebuild_pack_main,
        )

        return dashboard_high_tech_trading_visual_rebuild_pack_main([])

    if args.dashboard_ui_static_visual_freeze_pack:
        from src.operator_dashboard_ui_static_visual_freeze_pack import (
            main as dashboard_ui_static_visual_freeze_pack_main,
        )

        return dashboard_ui_static_visual_freeze_pack_main([])

    if args.post_ui_freeze_handoff_data_roadmap_pack:
        from src.operator_post_ui_freeze_handoff_data_roadmap_pack import (
            main as post_ui_freeze_handoff_data_roadmap_pack_main,
        )

        return post_ui_freeze_handoff_data_roadmap_pack_main([])

    if args.interactive_local_research_platform_ui_shell_pack:
        from src.operator_interactive_local_research_platform_ui_shell_pack import (
            main as interactive_local_research_platform_ui_shell_pack_main,
        )

        return interactive_local_research_platform_ui_shell_pack_main([])

    if args.local_backend_api_shell_pack:
        from src.operator_local_backend_api_shell_pack import main as local_backend_api_shell_pack_main

        return local_backend_api_shell_pack_main([])

    if args.ui_driven_local_research_platform_mvp_pack:
        from src.operator_ui_driven_local_research_platform_mvp_pack import (
            main as ui_driven_local_research_platform_mvp_pack_main,
        )

        return ui_driven_local_research_platform_mvp_pack_main([])

    if args.productized_ui_public_data_intake_pack:
        from src.operator_productized_ui_public_data_intake_pack import (
            main as productized_ui_public_data_intake_pack_main,
        )

        return productized_ui_public_data_intake_pack_main([])

    if args.productized_ui_user_surface_cleanup_pack:
        from src.operator_productized_ui_user_surface_cleanup_pack import (
            main as productized_ui_user_surface_cleanup_pack_main,
        )

        return productized_ui_user_surface_cleanup_pack_main([])

    if args.public_data_intake_prep:
        from src.public_data_intake_preparation import main as public_data_intake_prep_main

        return public_data_intake_prep_main([])

    if args.local_workflow_run:
        from src.local_workflow_automation import main as local_workflow_run_main

        return local_workflow_run_main([])

    if args.local_research_report_build:
        from src.local_research_report_builder import main as local_research_report_build_main

        return local_research_report_build_main([])

    if args.local_ui_server:
        from src.local_backend_api_shell import run_local_ui_server

        run_local_ui_server(host=args.local_ui_host, port=args.local_ui_port)
        return 0

    monitor = PreciousMetalsMonitor(args.config, args.watchlist, mock_mode=(args.mock or args.ibkr_smoke or bool(args.contract_search) or args.calibrate_model or args.pricing_mock or bool(args.calibration_csv) or bool(args.validate_history) or bool(args.build_history) or bool(args.source_audit) or args.ibkr_historical_plan or args.ibkr_historical_fetch or bool(args.quality_gate) or args.historical_pipeline_check or args.upstream_factors or args.theoretical_pricing is not None or args.actual_etf_prices or args.deviation_check is not None or args.reference_signals is not None or args.daily_trade_plan is not None or args.strategy_plan is not None or args.manual_research_pipeline or args.market_data_source_plan or args.manual_market_data_adapter is not None or args.integrate_manual_market_data is not None or args.manual_market_data_pipeline is not None or args.validate_filled_manual_scenario is not None or args.manual_market_data_review_pack is not None or args.generated_output_guard or args.manual_csv_smoke is not None or args.market_data_provider_registry or args.market_data_adapter_contract or args.manual_csv_adapter_interface is not None or args.adapter_interface_bridge is not None or args.research_trading_plan is not None or args.manual_research_trading_pipeline is not None or args.final_research_review_pack is not None or args.market_data_provider_readiness or args.market_data_provider_config_audit is not None or args.market_data_provider_selector is not None or args.live_provider_interface_check is not None or args.live_provider_request_gate is not None or args.live_provider_mock_adapter is not None or args.live_data_quality_gate is not None or args.live_research_review_pack is not None or args.live_final_research_review_pack is not None or args.ibkr_live_provider_adapter_check is not None or args.ibkr_contract_mapping_plan is not None or args.ibkr_contract_qualification_dry_run is not None or args.ibkr_contract_qualification_execution_guard is not None or args.ibkr_readonly_qualification_precheck is not None or args.ibkr_readonly_qualification_runbook is not None or args.ibkr_readonly_qualification_go_no_go is not None or args.ibkr_readonly_qualification_config_template is not None or args.ibkr_readonly_qualification_config_audit is not None or args.ibkr_readonly_qualification_config_apply_plan is not None or args.ibkr_readonly_qualification_config_final_gate is not None or args.ibkr_readonly_qualification_safety_summary is not None or args.ibkr_readonly_qualification_candidate_resolver is not None or args.ibkr_readonly_qualification_candidate_review_pack is not None or args.ibkr_readonly_qualification_candidate_final_gate is not None or args.ibkr_readonly_qualification_candidate_safety_summary is not None or args.ibkr_readonly_qualification_operator_decision_ledger is not None or args.ibkr_readonly_qualification_operator_approval_stub is not None or args.ibkr_readonly_qualification_effective_approval_gate is not None or args.ibkr_readonly_qualification_final_authorization_packet is not None or args.ibkr_readonly_qualification_phase12_closure_report is not None or args.ibkr_readonly_qualification_sandbox_design is not None or args.ibkr_readonly_qualification_sandbox_input_contract is not None or args.ibkr_readonly_qualification_sandbox_input_validator is not None or args.ibkr_readonly_qualification_sandbox_qualification_simulator is not None or args.ibkr_readonly_qualification_sandbox_result_pack is not None or args.ibkr_readonly_qualification_sandbox_safety_gate is not None or args.ibkr_readonly_qualification_sandbox_final_review_pack is not None or args.ibkr_readonly_qualification_sandbox_closure_report is not None or args.ibkr_readonly_preflight_guard_design is not None or args.ibkr_readonly_preflight_config_contract is not None or args.ibkr_readonly_preflight_config_validator is not None or args.ibkr_readonly_preflight_config_template is not None or args.ibkr_readonly_preflight_config_apply_plan is not None or args.ibkr_readonly_preflight_final_gate is not None or args.ibkr_readonly_preflight_safe_config_merge_plan is not None or args.ibkr_readonly_preflight_profile_aware_config_plan is not None or args.ibkr_readonly_preflight_profile_aware_final_gate is not None or args.ibkr_readonly_tws_environment_checklist is not None or args.ibkr_readonly_external_readiness_pack is not None or args.ibkr_readonly_connection_preflight_pack is not None or args.ibkr_readonly_authorization_pack is not None or args.ibkr_first_readonly_connect_disconnect is not None or args.ibkr_readonly_connection_log_heartbeat_guard is not None or args.ibkr_readonly_nontrading_account_server_info_pack is not None or args.ibkr_readonly_contract_info_preflight_pack is not None or args.ibkr_readonly_market_data_snapshot_preflight_pack is not None or args.ibkr_readonly_market_data_entitlement_diagnostic is not None or args.primary_metals_market_inference_layer is not None or args.primary_metals_inference_research_plan_integration is not None or args.primary_metals_final_review_pack_integration is not None or args.final_research_trading_plan_output is not None or args.final_research_plan_orchestrator is not None or args.report_template_daily_log_telegram_ready_output is not None or args.scheduler_stub_final_readme_release_checklist is not None or args.batch_i_real_market_env_check or args.batch_i_final_integration_audit_gate or args.batch_j_strategy_threshold_refinement or args.batch_j_final_integration_audit_gate or args.dashboard_artifact_reader or args.telegram_dry_run_payload or args.telegram_approval_gate or args.telegram_manual_send_archive or args.multi_market_symbol_universe or args.multi_market_adapter_skeleton or args.multi_market_final_audit_freeze_summary or args.real_market_env_readiness_preflight or args.ibkr_connection_permission_gate or args.ibkr_connection_operator_runbook or args.ibkr_connect_dryrun_approval_packet or args.ibkr_connect_execution_skeleton_review or args.ibkr_connect_final_permission_gate))


    if args.upstream_factors:
        rows, csv_path, md_path = monitor.run_upstream_factors()
        statuses = sorted({r.source_status for r in rows})
        overall = "ok" if statuses == ["ok"] else ("unavailable" if statuses == ["unavailable"] else "partial")
        print(f"[UPSTREAM_FACTORS] factors={len(rows)} status={overall}")
        print(f"snapshot_csv={csv_path}")
        print(f"report={md_path}")
        print("NOTICE: Research-only upstream factor monitor. No trading / no order / no auto calibration.")
        return 0
    if args.theoretical_pricing is not None:
        input_path = args.theoretical_pricing if args.theoretical_pricing else None
        rows, csv_path, md_path = monitor.run_theoretical_pricing(input_path)
        statuses = sorted({r.pricing_status for r in rows})
        overall = "ok" if statuses == ["ok"] else ("unavailable" if statuses == ["unavailable"] else "partial")
        print(f"[THEORETICAL_PRICING] etfs={len(rows)} status={overall}")
        print(f"snapshot_csv={csv_path}")
        print(f"report={md_path}")
        print("NOTICE: Research-only theoretical pricing input layer. No trading / no order / no IBKR connection / no reqHistoricalData / no auto calibration / no auto pipeline chaining.")
        return 0


    if args.actual_etf_prices:
        rows, csv_path, md_path = monitor.run_actual_etf_prices()
        print(f"[ACTUAL_ETF_PRICES] etfs={len(rows)} status=manual_mock_only")
        print(f"snapshot_csv={csv_path}")
        print(f"report={md_path}")
        print("NOTICE: Manual/mock only. Not real-time market data. No IBKR connection / no reqMktData / no reqHistoricalData / no trading.")
        return 0

    if args.deviation_check is not None:
        paths = args.deviation_check
        if len(paths) > 2:
            print("--deviation-check accepts at most 2 paths: [theoretical_csv actual_csv]", file=sys.stderr)
            return 2
        theoretical_path = paths[0] if len(paths) >= 1 else None
        actual_path = paths[1] if len(paths) >= 2 else None
        rows, csv_path, md_path = monitor.run_deviation_check(theoretical_path, actual_path)
        statuses = sorted({r.deviation_status for r in rows})
        overall = "ok" if statuses == ["ok"] else ("unavailable" if statuses == ["unavailable"] else "partial")
        print(f"[DEVIATION_CHECK] etfs={len(rows)} status={overall}")
        print(f"snapshot_csv={csv_path}")
        print(f"report={md_path}")
        print("NOTICE: Deviation-only phase. No buy/sell/trade output / no IBKR connection / no reqMktData / no reqHistoricalData / no auto calibration / no auto pipeline chaining.")
        return 0

    if args.reference_signals is not None:
        input_path = args.reference_signals if args.reference_signals else None
        rows, csv_path, md_path = monitor.run_reference_signals(input_path)
        labels = sorted({r.reference_label for r in rows})
        print(f"[REFERENCE_SIGNALS] etfs={len(rows)} labels={','.join(labels)} action_allowed=false")
        print(f"snapshot_csv={csv_path}")
        print(f"report={md_path}")
        print("NOTICE: Observation-only reference layer. action_allowed=false / no IBKR connection / no reqMktData / no reqHistoricalData / no auto calibration / no auto pipeline chaining.")
        return 0

    if args.daily_trade_plan is not None:
        input_path = args.daily_trade_plan if args.daily_trade_plan else None
        rows, csv_path, md_path = monitor.run_daily_trade_plan(input_path)
        labels = sorted({r.plan_label for r in rows})
        print(f"[DAILY_TRADE_PLAN] etfs={len(rows)} labels={','.join(labels)} action_allowed=false")
        print(f"snapshot_csv={csv_path}")
        print(f"report={md_path}")
        print("NOTICE: Manual observation-only daily plan. action_allowed=false / no IBKR connection / no reqMktData / no reqHistoricalData / no auto calibration / no auto pipeline chaining.")
        return 0

    if args.strategy_plan is not None:
        input_path = args.strategy_plan if args.strategy_plan else None
        rows, csv_path, md_path = monitor.run_strategy_plan(input_path)
        labels = sorted({r.strategy_label for r in rows})
        print(f"[STRATEGY_PLAN] etfs={len(rows)} labels={','.join(labels)} action_allowed=false")
        print(f"snapshot_csv={csv_path}")
        print(f"report={md_path}")
        print("NOTICE: Multi-horizon manual observation framework. action_allowed=false / no IBKR connection / no reqMktData / no reqHistoricalData / no auto calibration / no auto pipeline chaining.")
        return 0

    if args.manual_research_pipeline:
        rows, csv_path, md_path = monitor.run_manual_research_pipeline()
        statuses = sorted({r.status for r in rows})
        print(f"[MANUAL_RESEARCH_PIPELINE] steps={len(rows)} statuses={','.join(statuses)} action_allowed=false")
        print(f"summary_csv={csv_path}")
        print(f"report={md_path}")
        print("NOTICE: Explicit manual research run only. action_allowed=false / no IBKR connection / no reqMktData / no reqHistoricalData / no auto calibration / no automatic execution.")
        return 0

    if args.market_data_source_plan:
        rows, csv_path, md_path = monitor.run_market_data_source_plan()
        statuses = sorted({r.adapter_status for r in rows})
        print(f"[MARKET_DATA_SOURCE_PLAN] targets={len(rows)} statuses={','.join(statuses)} planning_only=true")
        print(f"plan_csv={csv_path}")
        print(f"report={md_path}")
        print("NOTICE: Planning only. No IBKR connection / no reqMktData / no reqHistoricalData / no order / no cancel / no rebalance / no auto trade.")
        return 0

    if args.manual_market_data_adapter is not None:
        input_path = args.manual_market_data_adapter if args.manual_market_data_adapter else None
        rows, csv_path, md_path = monitor.run_manual_market_data_adapter(input_path)
        statuses = sorted({r.normalized_status for r in rows})
        print(f"[MANUAL_MARKET_DATA_ADAPTER] rows={len(rows)} statuses={','.join(statuses)} manual_csv_only=true")
        print(f"snapshot_csv={csv_path}")
        print(f"report={md_path}")
        print("NOTICE: Manual CSV only. No IBKR connection / no reqMktData / no reqHistoricalData / no order / no cancel / no rebalance / no auto trade.")
        return 0

    if args.integrate_manual_market_data is not None:
        input_path = args.integrate_manual_market_data if args.integrate_manual_market_data else None
        upstream_rows, actual_rows, summary_rows, upstream_csv, actual_csv, summary_csv, report = monitor.run_integrate_manual_market_data(input_path)
        statuses = sorted({r.output_status for r in summary_rows})
        print(f"[INTEGRATE_MANUAL_MARKET_DATA] upstream={len(upstream_rows)} actual={len(actual_rows)} statuses={','.join(statuses)} manual_snapshot_only=true")
        print(f"upstream_csv={upstream_csv}")
        print(f"actual_csv={actual_csv}")
        print(f"summary_csv={summary_csv}")
        print(f"report={report}")
        print("NOTICE: Manual snapshot integration only. No IBKR connection / no reqMktData / no reqHistoricalData / no order / no cancel / no rebalance / no auto trade / no automatic pipeline chaining.")
        return 0

    if args.manual_market_data_pipeline is not None:
        input_path = args.manual_market_data_pipeline if args.manual_market_data_pipeline else None
        rows, csv_path, md_path = monitor.run_manual_market_data_pipeline(input_path)
        statuses = sorted({r.status for r in rows})
        print(f"[MANUAL_MARKET_DATA_PIPELINE] steps={len(rows)} statuses={','.join(statuses)} action_allowed=false")
        print(f"summary_csv={csv_path}")
        print(f"report={md_path}")
        print("NOTICE: Explicit manual CSV research pipeline only. action_allowed=false / no IBKR connection / no reqMktData / no reqHistoricalData / no order / no cancel / no rebalance / no auto trade.")
        return 0

    if args.validate_filled_manual_scenario is not None:
        input_path = args.validate_filled_manual_scenario if args.validate_filled_manual_scenario else None
        rows, csv_path, md_path = monitor.run_validate_filled_manual_scenario(input_path)
        statuses = sorted({r.status for r in rows})
        print(f"[FILLED_MANUAL_SCENARIO] checks={len(rows)} statuses={','.join(statuses)} action_allowed=false")
        print(f"validation_csv={csv_path}")
        print(f"report={md_path}")
        print("NOTICE: Filled manual CSV scenario validation only. action_allowed=false / no IBKR connection / no reqMktData / no reqHistoricalData / no order / no cancel / no rebalance / no auto trade.")
        return 0

    if args.manual_market_data_review_pack is not None:
        input_path = args.manual_market_data_review_pack if args.manual_market_data_review_pack else None
        rows, csv_path, md_path = monitor.run_manual_market_data_review_pack(input_path)
        labels = sorted({r.strategy_label for r in rows})
        print(f"[MANUAL_MARKET_DATA_REVIEW_PACK] etfs={len(rows)} labels={','.join(labels)} action_allowed=false")
        print(f"review_csv={csv_path}")
        print(f"report={md_path}")
        print("NOTICE: Manual CSV review only. action_allowed=false / no IBKR connection / no reqMktData / no reqHistoricalData / no order / no cancel / no rebalance / no auto trade.")
        return 0

    if args.generated_output_guard:
        rows, csv_path, md_path = monitor.run_generated_output_guard()
        print(f"[GENERATED_OUTPUT_GUARD] detected={len(rows)} report_only=true")
        print(f"guard_csv={csv_path}")
        print(f"report={md_path}")
        print("NOTICE: Report only. No file deletion / no IBKR connection / no reqMktData / no reqHistoricalData / no order / no cancel / no rebalance / no auto trade.")
        return 0

    if args.manual_csv_smoke is not None:
        input_path = args.manual_csv_smoke if args.manual_csv_smoke else None
        rows, csv_path, md_path = monitor.run_manual_csv_smoke(input_path)
        statuses = sorted({r.status for r in rows})
        print(f"[MANUAL_CSV_SMOKE] steps={len(rows)} statuses={','.join(statuses)} action_allowed=false")
        print(f"summary_csv={csv_path}")
        print(f"report={md_path}")
        print("NOTICE: Manual CSV smoke only. report_only=true / action_allowed=false / no IBKR connection / no reqMktData / no reqHistoricalData / no order / no cancel / no rebalance / no auto trade.")
        return 0

    if args.market_data_provider_registry:
        rows, csv_path, md_path = monitor.run_market_data_provider_registry()
        statuses = sorted({r.provider_status for r in rows})
        print(f"[MARKET_DATA_PROVIDER_REGISTRY] providers={len(rows)} statuses={','.join(statuses)} registry_only=true")
        print(f"registry_csv={csv_path}")
        print(f"report={md_path}")
        print("NOTICE: Registry only. No connection / no API request / no IBKR connection / no reqMktData / no reqHistoricalData / no order / no cancel / no rebalance / no auto trade.")
        return 0

    if args.market_data_adapter_contract:
        rows, csv_path, md_path = monitor.run_market_data_adapter_contract()
        groups = sorted({r.field_group for r in rows})
        print(f"[MARKET_DATA_ADAPTER_CONTRACT] rows={len(rows)} groups={','.join(groups)} interface_only=true")
        print(f"contract_csv={csv_path}")
        print(f"report={md_path}")
        print("NOTICE: Interface contract only. No connection / no API request / no IBKR connection / no reqMktData / no reqHistoricalData / no order / no cancel / no rebalance / no auto trade.")
        return 0

    if args.manual_csv_adapter_interface is not None:
        input_path = args.manual_csv_adapter_interface if args.manual_csv_adapter_interface else None
        rows, csv_path, md_path = monitor.run_manual_csv_adapter_interface(input_path)
        statuses = sorted({r.adapter_status for r in rows})
        print(f"[MANUAL_CSV_ADAPTER_INTERFACE] rows={len(rows)} statuses={','.join(statuses)} local_csv_only=true")
        print(f"snapshot_csv={csv_path}")
        print(f"report={md_path}")
        print("NOTICE: Manual CSV adapter interface only. No connection / no API request / no IBKR connection / no reqMktData / no reqHistoricalData / no order / no cancel / no rebalance / no auto trade.")
        return 0

    if args.adapter_interface_bridge is not None:
        input_path = args.adapter_interface_bridge if args.adapter_interface_bridge else None
        rows, summary_rows, snapshot_csv, summary_csv, md_path = monitor.run_adapter_interface_bridge(input_path)
        statuses = sorted({r.bridge_status for r in summary_rows})
        print(f"[ADAPTER_INTERFACE_BRIDGE] rows={len(rows)} statuses={','.join(statuses)} local_csv_bridge=true")
        print(f"snapshot_csv={snapshot_csv}")
        print(f"summary_csv={summary_csv}")
        print(f"report={md_path}")
        print("NOTICE: Adapter bridge only. No connection / no API request / no IBKR connection / no reqMktData / no reqHistoricalData / no order / no cancel / no rebalance / no auto trade.")
        return 0


























    if args.batch_i_real_market_env_check:
        from src.operator_batch_i_real_market_env_check import generate_batch_i_real_market_env_check

        result = generate_batch_i_real_market_env_check(config_path=args.config)
        gate = result["gate"]
        environment = result["environment"]
        print("[BATCH_I_REAL_MARKET_ENV_CHECK] generated")
        print(
            "gate_status={}:real_market_environment_status={}:manual_only=true research_only=true observation_only=true".format(
                gate["gate_status"],
                environment["real_market_environment_status"],
            )
        )
        print("env_csv=operator_batch_i_real_market_env_check.csv")
        print("permission_csv=operator_batch_i_marketdata_permission_check.csv")
        print("review_csv=operator_batch_i_safe_unavailable_review.csv")
        print("gate_csv=operator_batch_i_real_market_env_gate.csv")
        print("env_report=reports/operator_batch_i_real_market_env_check.md")
        print("permission_report=reports/operator_batch_i_marketdata_permission_check.md")
        print("review_report=reports/operator_batch_i_safe_unavailable_review.md")
        print("gate_report=reports/operator_batch_i_real_market_env_gate_report.md")
        print(
            "NOTICE: Batch I skeleton only. manual-only / research-only / observation-only. "
            "No trading / no account reads / no position reads / no historical data request / "
            "no Telegram real send / no forced TWS or IB Gateway connection."
        )
        return 0

    if args.batch_i_final_integration_audit_gate:
        from src.operator_batch_i_final_integration_audit_gate import generate_batch_i_final_integration_audit_gate

        row = generate_batch_i_final_integration_audit_gate()
        print("[BATCH_I_FINAL_INTEGRATION_AUDIT_GATE] generated")
        print(
            "audit_gate_status={}:batch_i_gate_status={}:final_packet_batch_i_gate_status={}".format(
                row["audit_gate_status"],
                row["batch_i_gate_status"],
                row["final_packet_batch_i_gate_status"],
            )
        )
        print("csv=operator_batch_i_final_integration_audit_gate.csv")
        print("report=reports/operator_batch_i_final_integration_audit_gate_report.md")
        print(
            "NOTICE: Integration audit PASS only. Not live production PASS, not real market data PASS, "
            "and no trading/account/position/historical-data/Telegram-real-send path is invoked."
        )
        return 0

    if args.batch_j_strategy_threshold_refinement:
        from src.operator_batch_j_strategy_threshold_refinement import generate_batch_j_strategy_threshold_refinement

        result = generate_batch_j_strategy_threshold_refinement()
        gate = result["gate"]
        print("[BATCH_J_STRATEGY_THRESHOLD_REFINEMENT] generated")
        print(
            "gate_status={}:batch_i_env_gate_status={}:threshold_profile_status={}".format(
                gate["gate_status"],
                gate["batch_i_env_gate_status"],
                gate["threshold_profile_status"],
            )
        )
        print("csv=operator_batch_j_strategy_threshold_refinement.csv")
        print("report=reports/operator_batch_j_strategy_threshold_refinement_report.md")
        print("gate_csv=operator_batch_j_strategy_threshold_gate.csv")
        print("gate_report=reports/operator_batch_j_strategy_threshold_gate_report.md")
        print(
            "NOTICE: Batch J PASS only means threshold framework generation succeeded. "
            "It is not live production approval, not real market data verification, not strategy execution approval, "
            "and no trading/account/position/historical-data/Telegram-real-send path is invoked."
        )
        return 0

    if args.batch_j_final_integration_audit_gate:
        from src.operator_batch_j_final_integration_audit_gate import generate_batch_j_final_integration_audit_gate

        row = generate_batch_j_final_integration_audit_gate()
        print("[BATCH_J_FINAL_INTEGRATION_AUDIT_GATE] generated")
        print(
            "audit_gate_status={}:batch_j_gate_status={}:final_packet_batch_j_gate_status={}".format(
                row["audit_gate_status"],
                row["batch_j_gate_status"],
                row["final_packet_batch_j_gate_status"],
            )
        )
        print("csv=operator_batch_j_final_integration_audit_gate.csv")
        print("report=reports/operator_batch_j_final_integration_audit_gate_report.md")
        print(
            "NOTICE: Batch J integration audit PASS only. Not live production PASS, not real market data PASS, "
            "not strategy execution PASS, and no trading/account/position/historical-data/Telegram-real-send path is invoked."
        )
        return 0

    if args.dashboard_artifact_reader:
        from src.operator_dashboard_artifact_reader import generate_dashboard_artifact_reader

        row = generate_dashboard_artifact_reader()
        print("[DASHBOARD_ARTIFACT_READER] generated")
        print(
            "dashboard_status={}:final_packet_status={}:operator_display_mode={}".format(
                row["dashboard_status"],
                row["final_packet_status"],
                row["operator_display_mode"],
            )
        )
        print("csv=operator_dashboard_artifact_reader.csv")
        print("json=operator_dashboard_artifact_reader.json")
        print("report=reports/operator_dashboard_artifact_reader.md")
        print(
            "NOTICE: Local read-only dashboard artifacts only. No UI frontend, no web service, no IBKR, "
            "no account/position/historical-data reads, no Telegram real send, and no trading/order/cancel/rebalance."
        )
        return 0

    if args.telegram_dry_run_payload:
        from src.operator_telegram_dry_run_payload import generate_telegram_dry_run_payload

        row = generate_telegram_dry_run_payload()
        print("[TELEGRAM_DRY_RUN_PAYLOAD] generated")
        print(
            "telegram_payload_status={}:dashboard_status={}:no_real_send=true:manual_approval_required=true".format(
                row["telegram_payload_status"],
                row["dashboard_status"],
            )
        )
        print("csv=operator_telegram_dry_run_payload.csv")
        print("json=operator_telegram_dry_run_payload.json")
        print("report=reports/operator_telegram_dry_run_payload.md")
        print(
            "NOTICE: Telegram dry-run payload only. No Telegram API, no token read, no network send, "
            "no real send, no IBKR/account/position/historical-data reads, and no trading/order/cancel/rebalance."
        )
        return 0

    if args.telegram_approval_gate:
        from src.operator_telegram_dry_run_payload import generate_telegram_approval_gate

        row = generate_telegram_approval_gate()
        print("[TELEGRAM_APPROVAL_GATE] generated")
        print(
            "approval_gate_status={}:telegram_payload_status={}:no_real_send=true:telegram_real_send_allowed=false".format(
                row["approval_gate_status"],
                row["telegram_payload_status"],
            )
        )
        print("csv=operator_telegram_approval_gate.csv")
        print("report=reports/operator_telegram_approval_gate_report.md")
        print(
            "NOTICE: Human approval review gate only. No Telegram API, no token read, no network send, "
            "no real send, no auto push, and no trading/order/cancel/rebalance."
        )
        return 0

    if args.telegram_manual_send_archive:
        from src.operator_telegram_dry_run_payload import generate_telegram_manual_send_archive

        row = generate_telegram_manual_send_archive()
        print("[TELEGRAM_MANUAL_SEND_ARCHIVE] generated")
        print(
            "manual_send_archive_status={}:telegram_payload_status={}:approval_gate_status={}:send_executed=false:no_real_send=true:telegram_real_send_allowed=false".format(
                row["manual_send_archive_status"],
                row["telegram_payload_status"],
                row["approval_gate_status"],
            )
        )
        print("csv=operator_telegram_manual_send_archive.csv")
        print("report=reports/operator_telegram_manual_send_archive_report.md")
        print(
            "NOTICE: Manual-send archive skeleton only. No Telegram API, no token read, no network send, "
            "no real send, no auto push, no background task, no IBKR/account/position/historical-data reads, "
            "and no trading/order/cancel/rebalance."
        )
        return 0

    if args.multi_market_symbol_universe:
        from src.operator_multi_market_symbol_universe import generate_multi_market_symbol_universe

        result = generate_multi_market_symbol_universe()
        gate = result["schema_gate"]
        print("[MULTI_MARKET_SYMBOL_UNIVERSE] generated")
        print(
            "schema_gate_status={}:jp_symbol_count={}:cn_symbol_count={}:us_symbol_count={}:manual_only=true:research_only=true:observation_only=true".format(
                gate["schema_gate_status"],
                gate["jp_symbol_count"],
                gate["cn_symbol_count"],
                gate["us_symbol_count"],
            )
        )
        print("csv=operator_multi_market_symbol_universe.csv")
        print("json=operator_multi_market_symbol_universe.json")
        print("report=reports/operator_multi_market_symbol_universe.md")
        print("schema_gate_csv=operator_multi_market_symbol_schema_gate.csv")
        print("schema_gate_report=reports/operator_multi_market_symbol_schema_gate_report.md")
        print(
            "NOTICE: Static multi-market symbol universe only. No IBKR/TWS/Gateway connection, no real quotes, "
            "no account reads, no position reads, no historical data request, no Telegram real send, "
            "no trading/order/cancel/rebalance, and no buy/sell points or automatic trading advice."
        )
        return 0

    if args.multi_market_adapter_skeleton:
        from src.operator_multi_market_adapter_skeleton import generate_multi_market_adapter_skeleton

        result = generate_multi_market_adapter_skeleton()
        gate = result["adapter_gate"]
        print("[MULTI_MARKET_ADAPTER_SKELETON] generated")
        print(
            "adapter_gate_status={}:multi_market_schema_gate_status={}:jp_symbol_count={}:cn_symbol_count={}:us_symbol_count={}:manual_only=true:research_only=true:observation_only=true".format(
                gate["adapter_gate_status"],
                gate["multi_market_schema_gate_status"],
                gate["jp_symbol_count"],
                gate["cn_symbol_count"],
                gate["us_symbol_count"],
            )
        )
        print("csv=operator_multi_market_adapter_skeleton.csv")
        print("json=operator_multi_market_adapter_skeleton.json")
        print("report=reports/operator_multi_market_adapter_skeleton.md")
        print("adapter_gate_csv=operator_multi_market_adapter_gate.csv")
        print("adapter_gate_report=reports/operator_multi_market_adapter_gate_report.md")
        print(
            "NOTICE: Static multi-market adapter skeleton only. No IBKR/TWS/Gateway connection, no real quotes, "
            "no market data request, no contract qualification, no account reads, no position reads, "
            "no historical data request, no Telegram real send, no trading/order/cancel/rebalance, "
            "and no buy/sell points or automatic trading advice."
        )
        return 0

    if args.multi_market_final_audit_freeze_summary:
        from src.operator_multi_market_final_audit_freeze_summary import generate_multi_market_final_audit_freeze_summary

        row = generate_multi_market_final_audit_freeze_summary()
        print("[MULTI_MARKET_FINAL_AUDIT_FREEZE_SUMMARY] generated")
        print(
            "final_audit_status={}:batch_i_status={}:batch_j_status={}:dashboard_status={}:telegram_manual_archive_status={}:multi_market_adapter_gate_status={}".format(
                row["final_audit_status"],
                row["batch_i_status"],
                row["batch_j_status"],
                row["dashboard_status"],
                row["telegram_manual_archive_status"],
                row["multi_market_adapter_gate_status"],
            )
        )
        print("csv=operator_multi_market_final_audit_gate.csv")
        print("report=reports/operator_multi_market_final_audit_gate_report.md")
        print("freeze_summary=Precious_Metals_Monitor_Phase468-512_Post_MVP_Multi_Market_Freeze_Summary.md")
        print(
            "NOTICE: Final audit and freeze summary only. manual-only / research-only / observation-only. "
            "Not live production, not real market data verified, no IBKR/TWS/Gateway connection, no market data request, "
            "no contract qualification, no account reads, no position reads, no historical data request, "
            "no Telegram real send, and no trading/order/cancel/rebalance."
        )
        return 0





    if args.real_market_env_readiness_preflight:
        from src.operator_real_market_env_readiness_preflight import (
            FINAL_DECISION,
            NEXT_PHASE_CANDIDATE,
            READINESS_STATUS,
            generate_real_market_env_readiness_preflight,
        )

        rows = generate_real_market_env_readiness_preflight(config_path=args.config)
        print("[REAL_MARKET_ENV_READINESS_PREFLIGHT] generated")
        print(f"final_decision={FINAL_DECISION}")
        print(f"readiness_status={READINESS_STATUS}")
        print("external_connections_attempted=NO")
        print("ibkr_connected=NO")
        print("market_data_requested=NO")
        print("account_read_attempted=NO")
        print("positions_read_attempted=NO")
        print("historical_data_requested=NO")
        print("contract_qualification_attempted=NO")
        print("orders_submitted=NO")
        print("telegram_real_send_attempted=NO")
        print(f"next_phase_candidate={NEXT_PHASE_CANDIDATE}")
        print(f"checks={len(rows)}")
        print("csv=operator_real_market_env_readiness_preflight.csv")
        print("report=reports/operator_real_market_env_readiness_preflight_report.md")
        print(
            "NOTICE: Phase 513-516 readiness preflight artifacts only. "
            "No IBKR/TWS/Gateway connection, no network probe, no market data request, "
            "no account reads, no position reads, no historical data request, no contract qualification, "
            "no orders, no Telegram real send, and POST_MVP_MULTI_MARKET_FREEZE_READY is not reclassified."
        )
        return 0

    if args.ibkr_connection_permission_gate:
        from src.operator_ibkr_connection_permission_gate import (
            STATUS_FIELDS,
            STATUS_VALUES,
            generate_ibkr_connection_permission_gate,
        )

        rows = generate_ibkr_connection_permission_gate()
        print("[IBKR_CONNECTION_PERMISSION_GATE] generated")
        for field in STATUS_FIELDS:
            print(f"{field}={STATUS_VALUES[field]}")
        print(f"gates={len(rows)}")
        print("csv=operator_ibkr_connection_permission_gate.csv")
        print("report=reports/operator_ibkr_connection_permission_gate_report.md")
        print(
            "NOTICE: Phase 517-520 permission packet only. "
            "No IBKR/TWS/Gateway connection, no network probe, no market data request, "
            "no account reads, no position reads, no historical data request, no contract qualification, "
            "no orders, no cancellation, no rebalance, no Telegram real send, "
            "and no production-ready or real-market-data-verified reclassification."
        )
        return 0

    if args.ibkr_connection_operator_runbook:
        from src.operator_ibkr_connection_operator_runbook import (
            STATUS_FIELDS,
            STATUS_VALUES,
            generate_ibkr_connection_operator_runbook,
        )

        rows = generate_ibkr_connection_operator_runbook()
        print("[IBKR_CONNECTION_OPERATOR_RUNBOOK] generated")
        for field in STATUS_FIELDS:
            print(f"{field}={STATUS_VALUES[field]}")
        print(f"steps={len(rows)}")
        print("csv=operator_ibkr_connection_operator_runbook.csv")
        print("report=reports/operator_ibkr_connection_operator_runbook_report.md")
        print(
            "NOTICE: Phase 521-524 runbook/checklist artifacts only. "
            "No IBKR/TWS/Gateway connection, no network probe, no market data request, "
            "no account reads, no position reads, no historical data request, no contract qualification, "
            "no orders, no cancellation, no rebalance, no Telegram real send, and no connection approval."
        )
        return 0

    if args.ibkr_connect_dryrun_approval_packet:
        from src.operator_ibkr_connect_dryrun_approval_packet import (
            STATUS_FIELDS,
            STATUS_VALUES,
            generate_ibkr_connect_dryrun_approval_packet,
        )

        rows = generate_ibkr_connect_dryrun_approval_packet()
        print("[IBKR_CONNECT_DRYRUN_APPROVAL_PACKET] generated")
        for field in STATUS_FIELDS:
            print(f"{field}={STATUS_VALUES[field]}")
        print(f"approvals={len(rows)}")
        print("csv=operator_ibkr_connect_dryrun_approval_packet.csv")
        print("report=reports/operator_ibkr_connect_dryrun_approval_packet_report.md")
        print(
            "NOTICE: Phase 525-528 approval packet artifacts only. "
            "No IBKR/TWS/Gateway connection, no network probe, no market data request, "
            "no account reads, no position reads, no historical data request, no contract qualification, "
            "no orders, no cancellation, no rebalance, no Telegram real send, "
            "and no connect command is emitted."
        )
        return 0

    if args.ibkr_connect_execution_skeleton_review:
        from src.operator_ibkr_connect_execution_skeleton_review import (
            STATUS_FIELDS,
            STATUS_VALUES,
            generate_ibkr_connect_execution_skeleton_review,
        )

        rows = generate_ibkr_connect_execution_skeleton_review()
        print("[IBKR_CONNECT_EXECUTION_SKELETON_REVIEW] generated")
        for field in STATUS_FIELDS:
            print(f"{field}={STATUS_VALUES[field]}")
        print(f"reviews={len(rows)}")
        print("csv=operator_ibkr_connect_execution_skeleton_review.csv")
        print("report=reports/operator_ibkr_connect_execution_skeleton_review_report.md")
        print(
            "NOTICE: Phase 529-532 execution skeleton review artifacts only. "
            "No execute CLI, no IBKR/TWS/Gateway connection, no network probe, no market data request, "
            "no account reads, no position reads, no historical data request, no contract qualification, "
            "no orders, no cancellation, no rebalance, and no Telegram real send."
        )
        return 0

    if args.ibkr_connect_final_permission_gate:
        from src.operator_ibkr_connect_final_permission_gate import (
            STATUS_FIELDS,
            STATUS_VALUES,
            generate_ibkr_connect_final_permission_gate,
        )

        rows = generate_ibkr_connect_final_permission_gate()
        print("[IBKR_CONNECT_FINAL_PERMISSION_GATE] generated")
        for field in STATUS_FIELDS:
            print(f"{field}={STATUS_VALUES[field]}")
        print(f"gates={len(rows)}")
        print("csv=operator_ibkr_connect_final_permission_gate.csv")
        print("report=reports/operator_ibkr_connect_final_permission_gate_report.md")
        print(
            "NOTICE: Phase 533-536 final permission gate artifacts only. "
            "No IBKR/TWS/Gateway connection, no network probe, no market data request, "
            "no account reads, no position reads, no historical data request, no contract qualification, "
            "no orders, no cancellation, no rebalance, no Telegram real send, "
            "and no production-ready or real-market-data-verified reclassification."
        )
        return 0

    if args.scheduler_stub_final_readme_release_checklist is not None:
        from pathlib import Path

        from src.scheduler_stub_final_readme_release_checklist import (
            build_scheduler_stub_final_readme_release_checklist_rows,
            write_final_mvp_readme,
            write_scheduler_stub_final_readme_release_checklist_csv,
            write_scheduler_stub_final_readme_release_checklist_report,
        )

        input_source = (
            args.scheduler_stub_final_readme_release_checklist
            if args.scheduler_stub_final_readme_release_checklist
            else args.config
        )

        rows = build_scheduler_stub_final_readme_release_checklist_rows(input_source)

        csv_path = Path(
            monitor.config["runtime"].get(
                "scheduler_stub_final_readme_release_checklist_csv",
                "scheduler_stub_final_readme_release_checklist.csv",
            )
        )
        md_path = Path(
            monitor.config["runtime"].get(
                "scheduler_stub_final_readme_release_checklist_report",
                "reports/scheduler_stub_final_readme_release_checklist_report.md",
            )
        )
        readme_path = Path(
            monitor.config["runtime"].get(
                "final_mvp_readme",
                "reports/final_mvp_readme.md",
            )
        )

        write_scheduler_stub_final_readme_release_checklist_csv(csv_path, rows)
        write_scheduler_stub_final_readme_release_checklist_report(md_path, rows, input_source)
        write_final_mvp_readme(readme_path, rows)

        statuses = sorted({r.status for r in rows})
        decisions = sorted({r.release_decision for r in rows})
        scheduler_started = sum(1 for r in rows if r.scheduler_job_started == "true")
        telegram_api_called = sum(1 for r in rows if r.telegram_api_called == "true")
        readme_ready = sum(1 for r in rows if r.readme_ready == "true")
        checklist_ready = sum(1 for r in rows if r.release_checklist_ready == "true")
        final_action_allowed = sum(1 for r in rows if r.final_action_allowed == "true")

        print(
            "[SCHEDULER_STUB_FINAL_README_RELEASE_CHECKLIST] "
            f"rows={len(rows)} statuses={','.join(statuses)} "
            f"release_decisions={','.join(decisions)} "
            f"scheduler_job_started={scheduler_started} "
            f"telegram_api_called={telegram_api_called} "
            f"readme_ready={readme_ready} "
            f"release_checklist_ready={checklist_ready} "
            f"final_action_allowed={final_action_allowed} "
            "ibkr_connection_allowed=false market_data_request_allowed=false "
            "historical_data_request_allowed=false contract_details_request_allowed=false"
        )
        print(f"scheduler_stub_final_readme_release_checklist_csv={csv_path}")
        print(f"final_mvp_readme={readme_path}")
        print(f"report={md_path}")
        print(
            "NOTICE: Phase 31A-32C scheduler stub / final README / release checklist only. "
            "No background job / no Telegram API call / no IBKR connection / no TWS connection / "
            "no market data request / no historical data / no contract details / no qualification / no trading."
        )
        return 0

    if args.report_template_daily_log_telegram_ready_output is not None:
        from pathlib import Path

        from src.report_template_daily_log_telegram_ready_output import (
            append_report_template_daily_log,
            build_report_template_daily_log_telegram_rows,
            write_report_template_daily_log_telegram_csv,
            write_report_template_daily_log_telegram_report,
            write_telegram_ready_text,
        )

        input_source = (
            args.report_template_daily_log_telegram_ready_output
            if args.report_template_daily_log_telegram_ready_output
            else args.config
        )

        rows = build_report_template_daily_log_telegram_rows(input_source)

        csv_path = Path(
            monitor.config["runtime"].get(
                "report_template_daily_log_telegram_csv",
                "report_template_daily_log_telegram_ready_output.csv",
            )
        )
        md_path = Path(
            monitor.config["runtime"].get(
                "report_template_daily_log_telegram_report",
                "reports/report_template_daily_log_telegram_ready_output_report.md",
            )
        )
        daily_log_path = Path(
            monitor.config["runtime"].get(
                "final_research_plan_daily_log_csv",
                "final_research_plan_daily_log.csv",
            )
        )
        telegram_path = Path(
            monitor.config["runtime"].get(
                "telegram_ready_text",
                "reports/telegram_ready_text.txt",
            )
        )

        csv_path.parent.mkdir(parents=True, exist_ok=True)
        md_path.parent.mkdir(parents=True, exist_ok=True)
        daily_log_path.parent.mkdir(parents=True, exist_ok=True)
        telegram_path.parent.mkdir(parents=True, exist_ok=True)

        write_report_template_daily_log_telegram_csv(csv_path, rows)
        append_report_template_daily_log(daily_log_path, rows)
        write_report_template_daily_log_telegram_report(md_path, rows, input_source)
        write_telegram_ready_text(telegram_path, rows)

        actual_rows = [r for r in rows if r.row_id != "FINAL"]
        statuses = sorted({r.status for r in rows})
        telegram_statuses = sorted({r.telegram_status for r in rows})
        report_count = sum(1 for r in actual_rows if r.report_section_available == "true")
        daily_log_count = sum(1 for r in actual_rows if r.daily_log_ready == "true")
        telegram_ready_count = sum(1 for r in actual_rows if r.telegram_text_ready == "true")
        telegram_api_called = sum(1 for r in rows if r.telegram_api_called == "true")
        final_action_allowed = sum(1 for r in rows if r.final_action_allowed == "true")

        print(
            "[REPORT_TEMPLATE_DAILY_LOG_TELEGRAM_READY_OUTPUT] "
            f"rows={len(rows)} statuses={','.join(statuses)} "
            f"telegram_statuses={','.join(telegram_statuses)} "
            f"report_section_available={report_count} "
            f"daily_log_ready={daily_log_count} "
            f"telegram_text_ready={telegram_ready_count} "
            f"telegram_api_called={telegram_api_called} "
            f"final_action_allowed={final_action_allowed} "
            "ibkr_connection_allowed=false market_data_request_allowed=false "
            "historical_data_request_allowed=false contract_details_request_allowed=false"
        )
        print(f"report_template_daily_log_telegram_csv={csv_path}")
        print(f"daily_log_csv={daily_log_path}")
        print(f"telegram_ready_text={telegram_path}")
        print(f"report={md_path}")
        print(
            "NOTICE: Phase 28A-30C report template / daily log / Telegram-ready text only. "
            "No Telegram API call / no IBKR connection / no TWS connection / no market data request / "
            "no historical data / no contract details / no qualification / no trading."
        )
        return 0

    if args.final_research_plan_orchestrator is not None:
        from pathlib import Path

        from src.final_research_plan_orchestrator import (
            build_final_research_plan_orchestrator_rows,
            write_final_research_plan_orchestrator_csv,
            write_final_research_plan_orchestrator_report,
        )

        input_source = (
            args.final_research_plan_orchestrator
            if args.final_research_plan_orchestrator
            else args.config
        )

        rows = build_final_research_plan_orchestrator_rows(input_source)

        csv_path = Path(
            monitor.config["runtime"].get(
                "final_research_plan_orchestrator_csv",
                "final_research_plan_orchestrator.csv",
            )
        )
        md_path = Path(
            monitor.config["runtime"].get(
                "final_research_plan_orchestrator_report",
                "reports/final_research_plan_orchestrator_report.md",
            )
        )
        csv_path.parent.mkdir(parents=True, exist_ok=True)
        md_path.parent.mkdir(parents=True, exist_ok=True)

        write_final_research_plan_orchestrator_csv(csv_path, rows)
        write_final_research_plan_orchestrator_report(md_path, rows, input_source)

        actual_rows = [r for r in rows if r.row_id != "FINAL"]
        statuses = sorted({r.status for r in rows})
        decisions = sorted({r.plan_decision for r in rows})
        routes = sorted({r.data_route for r in rows})
        orchestrator_count = sum(1 for r in actual_rows if r.orchestrator_available == "true")
        one_command_count = sum(1 for r in actual_rows if r.one_command_output_available == "true")
        direction_count = sum(1 for r in actual_rows if r.market_direction_summary_allowed == "true")
        theoretical_count = sum(1 for r in actual_rows if r.theoretical_range_allowed == "true")
        manual_review_count = sum(1 for r in actual_rows if r.manual_review_required == "true")
        final_action_allowed = sum(1 for r in rows if r.final_action_allowed == "true")

        print(
            "[FINAL_RESEARCH_PLAN_ORCHESTRATOR] "
            f"rows={len(rows)} statuses={','.join(statuses)} "
            f"plan_decisions={','.join(decisions)} "
            f"data_routes={','.join(routes)} "
            f"orchestrator_available={orchestrator_count} "
            f"one_command_output_available={one_command_count} "
            f"market_direction_summary_allowed={direction_count} "
            f"theoretical_range_allowed={theoretical_count} "
            f"manual_review_required={manual_review_count} "
            f"final_action_allowed={final_action_allowed} "
            "ibkr_connection_allowed=false market_data_request_allowed=false "
            "historical_data_request_allowed=false contract_details_request_allowed=false"
        )
        print(f"final_research_plan_orchestrator_csv={csv_path}")
        print(f"report={md_path}")
        print(
            "NOTICE: Phase 25A-27C final research plan orchestrator only. "
            "No IBKR connection / no TWS connection / no market data request / "
            "no historical data / no contract details / no qualification / no trading."
        )
        return 0

    if args.final_research_trading_plan_output is not None:
        from pathlib import Path

        from src.final_research_trading_plan_output import (
            build_final_research_trading_plan_rows,
            write_final_research_trading_plan_csv,
            write_final_research_trading_plan_report,
        )

        input_source = (
            args.final_research_trading_plan_output
            if args.final_research_trading_plan_output
            else args.config
        )

        rows = build_final_research_trading_plan_rows(input_source)

        csv_path = Path(
            monitor.config["runtime"].get(
                "final_research_trading_plan_output_csv",
                "final_research_trading_plan_output.csv",
            )
        )
        md_path = Path(
            monitor.config["runtime"].get(
                "final_research_trading_plan_output_report",
                "reports/final_research_trading_plan_output_report.md",
            )
        )
        csv_path.parent.mkdir(parents=True, exist_ok=True)
        md_path.parent.mkdir(parents=True, exist_ok=True)

        write_final_research_trading_plan_csv(csv_path, rows)
        write_final_research_trading_plan_report(md_path, rows, input_source)

        actual_rows = [r for r in rows if r.row_id != "FINAL"]
        statuses = sorted({r.status for r in rows})
        decisions = sorted({r.plan_decision for r in rows})
        final_plan_count = sum(1 for r in actual_rows if r.final_research_plan_available == "true")
        direction_count = sum(1 for r in actual_rows if r.market_direction_summary_allowed == "true")
        theoretical_count = sum(1 for r in actual_rows if r.theoretical_range_allowed == "true")
        low_confidence_count = sum(1 for r in actual_rows if r.execution_price_confidence == "LOW")
        manual_review_count = sum(1 for r in actual_rows if r.manual_review_required == "true")
        final_action_allowed = sum(1 for r in rows if r.final_action_allowed == "true")

        print(
            "[FINAL_RESEARCH_TRADING_PLAN_OUTPUT] "
            f"rows={len(rows)} statuses={','.join(statuses)} "
            f"plan_decisions={','.join(decisions)} "
            f"final_research_plan_available={final_plan_count} "
            f"market_direction_summary_allowed={direction_count} "
            f"theoretical_range_allowed={theoretical_count} "
            f"low_execution_price_confidence={low_confidence_count} "
            f"manual_review_required={manual_review_count} "
            f"final_action_allowed={final_action_allowed} "
            "ibkr_connection_allowed=false market_data_request_allowed=false "
            "historical_data_request_allowed=false contract_details_request_allowed=false"
        )
        print(f"final_research_trading_plan_output_csv={csv_path}")
        print(f"report={md_path}")
        print(
            "NOTICE: Phase 24A-24C final research trading plan output only. "
            "No IBKR connection / no TWS connection / no market data request / "
            "no historical data / no contract details / no qualification / no trading."
        )
        return 0

    if args.primary_metals_final_review_pack_integration is not None:
        from pathlib import Path

        from src.primary_metals_final_review_pack_integration import (
            build_primary_metals_final_review_pack_rows,
            write_primary_metals_final_review_pack_csv,
            write_primary_metals_final_review_pack_report,
        )

        input_source = (
            args.primary_metals_final_review_pack_integration
            if args.primary_metals_final_review_pack_integration
            else args.config
        )

        rows = build_primary_metals_final_review_pack_rows(input_source)

        csv_path = Path(
            monitor.config["runtime"].get(
                "primary_metals_final_review_pack_csv",
                "primary_metals_final_review_pack.csv",
            )
        )
        md_path = Path(
            monitor.config["runtime"].get(
                "primary_metals_final_review_pack_report",
                "reports/primary_metals_final_review_pack_report.md",
            )
        )
        csv_path.parent.mkdir(parents=True, exist_ok=True)
        md_path.parent.mkdir(parents=True, exist_ok=True)

        write_primary_metals_final_review_pack_csv(csv_path, rows)
        write_primary_metals_final_review_pack_report(md_path, rows, input_source)

        actual_rows = [r for r in rows if r.row_id != "FINAL"]
        statuses = sorted({r.status for r in rows})
        decisions = sorted({r.final_decision for r in rows})
        final_review_count = sum(1 for r in actual_rows if r.final_review_available == "true")
        direction_count = sum(1 for r in actual_rows if r.final_direction_summary_allowed == "true")
        theoretical_count = sum(1 for r in actual_rows if r.final_theoretical_range_allowed == "true")
        low_confidence_count = sum(1 for r in actual_rows if r.execution_price_confidence == "LOW")
        high_exec_allowed = sum(
            1 for r in actual_rows if r.final_high_confidence_execution_allowed == "true"
        )
        final_action_allowed = sum(1 for r in rows if r.final_action_allowed == "true")

        print(
            "[PRIMARY_METALS_FINAL_REVIEW_PACK_INTEGRATION] "
            f"rows={len(rows)} statuses={','.join(statuses)} "
            f"final_decisions={','.join(decisions)} "
            f"final_review_available={final_review_count} "
            f"final_direction_summary_allowed={direction_count} "
            f"final_theoretical_range_allowed={theoretical_count} "
            f"low_execution_price_confidence={low_confidence_count} "
            f"final_high_confidence_execution_allowed={high_exec_allowed} "
            f"final_action_allowed={final_action_allowed} "
            "ibkr_connection_allowed=false market_data_request_allowed=false "
            "historical_data_request_allowed=false contract_details_request_allowed=false"
        )
        print(f"primary_metals_final_review_pack_csv={csv_path}")
        print(f"report={md_path}")
        print(
            "NOTICE: Phase 23A-23C primary metals final review pack integration only. "
            "No IBKR connection / no TWS connection / no market data request / "
            "no historical data / no contract details / no qualification / no trading."
        )
        return 0

    if args.primary_metals_inference_research_plan_integration is not None:
        from pathlib import Path

        from src.primary_metals_inference_research_plan_integration import (
            build_primary_metals_inference_research_plan_rows,
            write_primary_metals_inference_research_plan_csv,
            write_primary_metals_inference_research_plan_report,
        )

        input_source = (
            args.primary_metals_inference_research_plan_integration
            if args.primary_metals_inference_research_plan_integration
            else args.config
        )

        rows = build_primary_metals_inference_research_plan_rows(input_source)

        csv_path = Path(
            monitor.config["runtime"].get(
                "primary_metals_inference_research_plan_csv",
                "primary_metals_inference_research_plan.csv",
            )
        )
        md_path = Path(
            monitor.config["runtime"].get(
                "primary_metals_inference_research_plan_report",
                "reports/primary_metals_inference_research_plan_report.md",
            )
        )
        csv_path.parent.mkdir(parents=True, exist_ok=True)
        md_path.parent.mkdir(parents=True, exist_ok=True)

        write_primary_metals_inference_research_plan_csv(csv_path, rows)
        write_primary_metals_inference_research_plan_report(md_path, rows, input_source)

        actual_rows = [r for r in rows if r.row_id != "FINAL"]
        statuses = sorted({r.status for r in rows})
        research_plan_count = sum(1 for r in actual_rows if r.research_plan_available == "true")
        theoretical_range_count = sum(1 for r in actual_rows if r.theoretical_range_allowed == "true")
        low_confidence_count = sum(1 for r in actual_rows if r.execution_price_confidence == "LOW")
        high_trade_allowed = sum(
            1 for r in actual_rows if r.high_confidence_buy_sell_point_allowed == "true"
        )
        action_allowed = sum(1 for r in rows if r.action_allowed == "true")

        print(
            "[PRIMARY_METALS_INFERENCE_RESEARCH_PLAN_INTEGRATION] "
            f"rows={len(rows)} statuses={','.join(statuses)} "
            f"research_plan_available={research_plan_count} "
            f"theoretical_range_allowed={theoretical_range_count} "
            f"low_execution_price_confidence={low_confidence_count} "
            f"high_confidence_buy_sell_point_allowed={high_trade_allowed} "
            f"action_allowed={action_allowed} "
            "ibkr_connection_allowed=false market_data_request_allowed=false "
            "historical_data_request_allowed=false contract_details_request_allowed=false"
        )
        print(f"primary_metals_inference_research_plan_csv={csv_path}")
        print(f"report={md_path}")
        print(
            "NOTICE: Phase 22A-22C primary metals inference research-plan integration only. "
            "No IBKR connection / no TWS connection / no market data request / "
            "no historical data / no contract details / no qualification / no trading."
        )
        return 0

    if args.primary_metals_market_inference_layer is not None:
        from pathlib import Path

        from src.primary_metals_market_inference_layer import (
            build_primary_metals_market_inference_rows,
            write_primary_metals_market_inference_csv,
            write_primary_metals_market_inference_report,
        )

        input_source = (
            args.primary_metals_market_inference_layer
            if args.primary_metals_market_inference_layer
            else args.config
        )

        rows = build_primary_metals_market_inference_rows(input_source)

        csv_path = Path(
            monitor.config["runtime"].get(
                "primary_metals_market_inference_csv",
                "primary_metals_market_inference.csv",
            )
        )
        md_path = Path(
            monitor.config["runtime"].get(
                "primary_metals_market_inference_report",
                "reports/primary_metals_market_inference_report.md",
            )
        )
        csv_path.parent.mkdir(parents=True, exist_ok=True)
        md_path.parent.mkdir(parents=True, exist_ok=True)

        write_primary_metals_market_inference_csv(csv_path, rows)
        write_primary_metals_market_inference_report(md_path, rows, input_source)

        statuses = sorted({r.status for r in rows})
        actual_rows = [r for r in rows if r.row_id != "FINAL"]
        market_signal_count = sum(1 for r in actual_rows if r.market_signal_available == "true")
        theoretical_count = sum(1 for r in actual_rows if r.theoretical_value_available == "true")
        low_confidence_count = sum(1 for r in actual_rows if r.execution_price_confidence == "LOW")
        high_trade_allowed = sum(
            1 for r in actual_rows if r.high_confidence_buy_sell_point_allowed == "true"
        )
        action_allowed = sum(1 for r in rows if r.action_allowed == "true")

        print(
            "[PRIMARY_METALS_MARKET_INFERENCE_LAYER] "
            f"rows={len(rows)} statuses={','.join(statuses)} "
            f"market_signal_available={market_signal_count} "
            f"theoretical_value_available={theoretical_count} "
            f"low_execution_price_confidence={low_confidence_count} "
            f"high_confidence_buy_sell_point_allowed={high_trade_allowed} "
            f"action_allowed={action_allowed} "
            "ibkr_connection_allowed=false market_data_request_allowed=false "
            "historical_data_request_allowed=false contract_details_request_allowed=false"
        )
        print(f"primary_metals_market_inference_csv={csv_path}")
        print(f"report={md_path}")
        print(
            "NOTICE: Phase 21A-21C primary metals market inference only. "
            "No IBKR connection / no TWS connection / no market data request / "
            "no historical data / no contract details / no qualification / no trading."
        )
        return 0

    if args.ibkr_readonly_market_data_entitlement_diagnostic is not None:
        from pathlib import Path

        from src.ibkr_readonly_market_data_entitlement_diagnostic import (
            build_ibkr_readonly_market_data_entitlement_diagnostic_rows,
            write_ibkr_readonly_market_data_entitlement_diagnostic_csv,
            write_ibkr_readonly_market_data_entitlement_diagnostic_report,
        )

        input_source = (
            args.ibkr_readonly_market_data_entitlement_diagnostic
            if args.ibkr_readonly_market_data_entitlement_diagnostic
            else args.config
        )

        rows = build_ibkr_readonly_market_data_entitlement_diagnostic_rows(
            input_source,
            execute=args.execute_ibkr_readonly_market_data_entitlement_diagnostic,
        )

        csv_path = Path(
            monitor.config["runtime"].get(
                "ibkr_readonly_market_data_entitlement_diagnostic_csv",
                "ibkr_readonly_market_data_entitlement_diagnostic.csv",
            )
        )
        md_path = Path(
            monitor.config["runtime"].get(
                "ibkr_readonly_market_data_entitlement_diagnostic_report",
                "reports/ibkr_readonly_market_data_entitlement_diagnostic_report.md",
            )
        )
        csv_path.parent.mkdir(parents=True, exist_ok=True)
        md_path.parent.mkdir(parents=True, exist_ok=True)

        write_ibkr_readonly_market_data_entitlement_diagnostic_csv(csv_path, rows)
        write_ibkr_readonly_market_data_entitlement_diagnostic_report(md_path, rows, input_source)

        statuses = sorted({r.diagnostic_status for r in rows})
        market_statuses = sorted({r.market_data_status for r in rows})
        profiles = sorted({r.selected_profile for r in rows})
        final_row = rows[-1]
        snapshot_success = sum(1 for r in rows if r.row_id == "SNAPSHOT_RESULT_SUMMARY" and r.snapshot_request_succeeded == "true")
        price_available = sum(1 for r in rows if r.row_id == "SNAPSHOT_RESULT_SUMMARY" and r.price_available == "true")

        print(
            "[IBKR_READONLY_MARKET_DATA_ENTITLEMENT_DIAGNOSTIC] "
            f"rows={len(rows)} selected_profile={','.join(profiles)} "
            f"diagnostic_statuses={','.join(statuses)} "
            f"market_data_statuses={','.join(market_statuses)} "
            f"execute_requested={args.execute_ibkr_readonly_market_data_entitlement_diagnostic} "
            f"snapshot_success={snapshot_success} price_available={price_available} "
            f"ibkr_error_code={final_row.ibkr_error_code} "
            f"delayed_data_enabled={final_row.delayed_data_enabled} "
            "streaming_market_data_allowed=false historical_data_request_allowed=false "
            "contract_qualification_allowed=false action_allowed=false"
        )
        print(f"market_data_entitlement_diagnostic_csv={csv_path}")
        print(f"report={md_path}")
        print(
            "NOTICE: Phase 20D market data entitlement diagnostic only. "
            "It classifies one non-streaming snapshot result. "
            "No streaming market data / no historical data / no real contract qualification / "
            "no order action / no cancellation action / no rebalance / no auto trade."
        )
        return 0

    if args.ibkr_readonly_market_data_snapshot_preflight_pack is not None:
        from pathlib import Path

        from src.ibkr_readonly_market_data_snapshot_preflight_pack import (
            build_ibkr_readonly_market_data_snapshot_preflight_pack_rows,
            write_ibkr_readonly_market_data_snapshot_preflight_pack_csv,
            write_ibkr_readonly_market_data_snapshot_preflight_pack_report,
        )

        input_source = (
            args.ibkr_readonly_market_data_snapshot_preflight_pack
            if args.ibkr_readonly_market_data_snapshot_preflight_pack
            else args.config
        )

        rows = build_ibkr_readonly_market_data_snapshot_preflight_pack_rows(
            input_source,
            execute=args.execute_ibkr_readonly_market_data_snapshot,
        )

        csv_path = Path(
            monitor.config["runtime"].get(
                "ibkr_readonly_market_data_snapshot_preflight_pack_csv",
                "ibkr_readonly_market_data_snapshot_preflight_pack.csv",
            )
        )
        md_path = Path(
            monitor.config["runtime"].get(
                "ibkr_readonly_market_data_snapshot_preflight_pack_report",
                "reports/ibkr_readonly_market_data_snapshot_preflight_pack_report.md",
            )
        )
        csv_path.parent.mkdir(parents=True, exist_ok=True)
        md_path.parent.mkdir(parents=True, exist_ok=True)

        write_ibkr_readonly_market_data_snapshot_preflight_pack_csv(csv_path, rows)
        write_ibkr_readonly_market_data_snapshot_preflight_pack_report(md_path, rows, input_source)

        statuses = sorted({r.status for r in rows})
        profiles = sorted({r.selected_profile for r in rows})
        actual_rows = [r for r in rows if r.row_id == "MARKET_DATA_SNAPSHOT_READ"]
        connection_attempts = sum(1 for r in actual_rows if r.connection_attempted == "true")
        connect_success = sum(1 for r in actual_rows if r.connect_succeeded == "true")
        snapshot_success = sum(1 for r in actual_rows if r.market_data_snapshot_read_succeeded == "true")
        price_available = sum(1 for r in actual_rows if r.price_available == "true")
        current_allowed = sum(1 for r in actual_rows if r.current_call_allowed == "true")

        print(
            "[IBKR_READONLY_MARKET_DATA_SNAPSHOT_PREFLIGHT_PACK] "
            f"rows={len(rows)} selected_profile={','.join(profiles)} "
            f"statuses={','.join(statuses)} "
            f"execute_requested={args.execute_ibkr_readonly_market_data_snapshot} "
            f"connection_attempts={connection_attempts} connect_success={connect_success} "
            f"snapshot_success={snapshot_success} price_available={price_available} "
            f"current_call_allowed={current_allowed} "
            "streaming_market_data_allowed=false historical_data_request_allowed=false "
            "contract_qualification_allowed=false action_allowed=false"
        )
        print(f"market_data_snapshot_preflight_pack_csv={csv_path}")
        print(f"report={md_path}")
        print(
            "NOTICE: Phase 20A-20C market data snapshot read-only. "
            "Default is dry-run. Execute flag allows one non-streaming snapshot for one contract only. "
            "No streaming market data / no historical data / no real contract qualification / "
            "no order action / no cancellation action / no rebalance / no auto trade."
        )
        return 0

    if args.ibkr_readonly_contract_info_preflight_pack is not None:
        from pathlib import Path

        from src.ibkr_readonly_contract_info_preflight_pack import (
            build_ibkr_readonly_contract_info_preflight_pack_rows,
            write_ibkr_readonly_contract_info_preflight_pack_csv,
            write_ibkr_readonly_contract_info_preflight_pack_report,
        )

        input_source = (
            args.ibkr_readonly_contract_info_preflight_pack
            if args.ibkr_readonly_contract_info_preflight_pack
            else args.config
        )

        rows = build_ibkr_readonly_contract_info_preflight_pack_rows(
            input_source,
            execute=args.execute_ibkr_readonly_contract_info,
        )

        csv_path = Path(
            monitor.config["runtime"].get(
                "ibkr_readonly_contract_info_preflight_pack_csv",
                "ibkr_readonly_contract_info_preflight_pack.csv",
            )
        )
        md_path = Path(
            monitor.config["runtime"].get(
                "ibkr_readonly_contract_info_preflight_pack_report",
                "reports/ibkr_readonly_contract_info_preflight_pack_report.md",
            )
        )
        csv_path.parent.mkdir(parents=True, exist_ok=True)
        md_path.parent.mkdir(parents=True, exist_ok=True)

        write_ibkr_readonly_contract_info_preflight_pack_csv(csv_path, rows)
        write_ibkr_readonly_contract_info_preflight_pack_report(md_path, rows, input_source)

        statuses = sorted({r.status for r in rows})
        profiles = sorted({r.selected_profile for r in rows})
        actual_rows = [r for r in rows if r.row_id == "CONTRACT_INFO_READ"]
        connection_attempts = sum(1 for r in actual_rows if r.connection_attempted == "true")
        connect_success = sum(1 for r in actual_rows if r.connect_succeeded == "true")
        contract_info_success = sum(1 for r in actual_rows if r.contract_info_read_succeeded == "true")
        current_allowed = sum(1 for r in actual_rows if r.current_call_allowed == "true")

        print(
            "[IBKR_READONLY_CONTRACT_INFO_PREFLIGHT_PACK] "
            f"rows={len(rows)} selected_profile={','.join(profiles)} "
            f"statuses={','.join(statuses)} "
            f"execute_requested={args.execute_ibkr_readonly_contract_info} "
            f"connection_attempts={connection_attempts} connect_success={connect_success} "
            f"contract_info_success={contract_info_success} current_call_allowed={current_allowed} "
            "market_data_request_allowed=false historical_data_request_allowed=false "
            "contract_qualification_allowed=false action_allowed=false"
        )
        print(f"contract_info_preflight_pack_csv={csv_path}")
        print(f"report={md_path}")
        print(
            "NOTICE: Phase 19A-19C contract info read-only. "
            "Default is dry-run. Execute flag allows contract details metadata only. "
            "No market data / no historical data / no real contract qualification / "
            "no order action / no cancellation action / no rebalance / no auto trade."
        )
        return 0

    if args.ibkr_readonly_nontrading_account_server_info_pack is not None:
        from pathlib import Path

        from src.ibkr_readonly_nontrading_account_server_info_pack import (
            build_ibkr_readonly_nontrading_account_server_info_pack_rows,
            write_ibkr_readonly_nontrading_account_server_info_pack_csv,
            write_ibkr_readonly_nontrading_account_server_info_pack_report,
        )

        input_source = (
            args.ibkr_readonly_nontrading_account_server_info_pack
            if args.ibkr_readonly_nontrading_account_server_info_pack
            else args.config
        )

        rows = build_ibkr_readonly_nontrading_account_server_info_pack_rows(
            input_source,
            execute=args.execute_ibkr_readonly_nontrading_info,
        )

        csv_path = Path(
            monitor.config["runtime"].get(
                "ibkr_readonly_nontrading_account_server_info_pack_csv",
                "ibkr_readonly_nontrading_account_server_info_pack.csv",
            )
        )
        md_path = Path(
            monitor.config["runtime"].get(
                "ibkr_readonly_nontrading_account_server_info_pack_report",
                "reports/ibkr_readonly_nontrading_account_server_info_pack_report.md",
            )
        )
        csv_path.parent.mkdir(parents=True, exist_ok=True)
        md_path.parent.mkdir(parents=True, exist_ok=True)

        write_ibkr_readonly_nontrading_account_server_info_pack_csv(csv_path, rows)
        write_ibkr_readonly_nontrading_account_server_info_pack_report(md_path, rows, input_source)

        statuses = sorted({r.status for r in rows})
        profiles = sorted({r.selected_profile for r in rows})
        actual_rows = [r for r in rows if r.row_id == "NONTRADING_INFO_READ"]
        connection_attempts = sum(1 for r in actual_rows if r.connection_attempted == "true")
        connect_success = sum(1 for r in actual_rows if r.connect_succeeded == "true")
        info_success = sum(1 for r in actual_rows if r.nontrading_info_read_succeeded == "true")
        current_allowed = sum(1 for r in actual_rows if r.current_call_allowed == "true")

        print(
            "[IBKR_READONLY_NONTRADING_ACCOUNT_SERVER_INFO_PACK] "
            f"rows={len(rows)} selected_profile={','.join(profiles)} "
            f"statuses={','.join(statuses)} "
            f"execute_requested={args.execute_ibkr_readonly_nontrading_info} "
            f"connection_attempts={connection_attempts} connect_success={connect_success} "
            f"nontrading_info_success={info_success} current_call_allowed={current_allowed} "
            "market_data_request_allowed=false historical_data_request_allowed=false "
            "contract_qualification_allowed=false contract_details_request_allowed=false "
            "action_allowed=false"
        )
        print(f"nontrading_account_server_info_pack_csv={csv_path}")
        print(f"report={md_path}")
        print(
            "NOTICE: Phase 18A-18C non-trading account/server info only. "
            "Default is dry-run. Execute flag allows connection metadata, managed account metadata, "
            "and account summary metadata only. No market data / no historical data / "
            "no real contract qualification / no contract details / no order action / "
            "no cancellation action / no rebalance / no auto trade."
        )
        return 0

    if args.ibkr_readonly_connection_log_heartbeat_guard is not None:
        from pathlib import Path

        from src.ibkr_readonly_connection_log_heartbeat_guard import (
            build_ibkr_readonly_connection_log_heartbeat_guard_rows,
            write_ibkr_readonly_connection_log_heartbeat_guard_csv,
            write_ibkr_readonly_connection_log_heartbeat_guard_report,
        )

        input_source = (
            args.ibkr_readonly_connection_log_heartbeat_guard
            if args.ibkr_readonly_connection_log_heartbeat_guard
            else args.config
        )

        rows = build_ibkr_readonly_connection_log_heartbeat_guard_rows(
            input_source,
            execute=args.execute_ibkr_readonly_heartbeat_guard,
        )

        csv_path = Path(
            monitor.config["runtime"].get(
                "ibkr_readonly_connection_log_heartbeat_guard_csv",
                "ibkr_readonly_connection_log_heartbeat_guard.csv",
            )
        )
        md_path = Path(
            monitor.config["runtime"].get(
                "ibkr_readonly_connection_log_heartbeat_guard_report",
                "reports/ibkr_readonly_connection_log_heartbeat_guard_report.md",
            )
        )
        csv_path.parent.mkdir(parents=True, exist_ok=True)
        md_path.parent.mkdir(parents=True, exist_ok=True)

        write_ibkr_readonly_connection_log_heartbeat_guard_csv(csv_path, rows)
        write_ibkr_readonly_connection_log_heartbeat_guard_report(md_path, rows, input_source)

        statuses = sorted({r.status for r in rows})
        profiles = sorted({r.selected_profile for r in rows})
        actual_rows = [r for r in rows if r.row_id == "FIRST_CONNECT_SUMMARY"]
        connection_attempts = sum(1 for r in actual_rows if r.connection_attempted == "true")
        connect_success = sum(1 for r in actual_rows if r.connect_succeeded == "true")
        metadata_available = sum(1 for r in rows if r.heartbeat_metadata_available == "true")
        current_allowed = sum(1 for r in actual_rows if r.current_call_allowed == "true")

        print(
            "[IBKR_READONLY_CONNECTION_LOG_HEARTBEAT_GUARD] "
            f"rows={len(rows)} selected_profile={','.join(profiles)} "
            f"statuses={','.join(statuses)} "
            f"execute_requested={args.execute_ibkr_readonly_heartbeat_guard} "
            f"connection_attempts={connection_attempts} connect_success={connect_success} "
            f"metadata_available={metadata_available} current_call_allowed={current_allowed} "
            "market_data_request_allowed=false historical_data_request_allowed=false "
            "contract_qualification_allowed=false action_allowed=false"
        )
        print(f"connection_log_heartbeat_guard_csv={csv_path}")
        print(f"report={md_path}")
        print(
            "NOTICE: Phase 17C-17D connection log heartbeat guard only. "
            "Default is dry-run. Execute flag reuses connect/disconnect metadata only. "
            "No market data / no historical data / no real contract qualification / "
            "no order action / no cancellation action / no rebalance / no auto trade."
        )
        return 0

    if args.ibkr_first_readonly_connect_disconnect is not None:
        from pathlib import Path

        from src.ibkr_readonly_first_connect_disconnect import (
            build_ibkr_readonly_first_connect_disconnect_rows,
            write_ibkr_readonly_first_connect_disconnect_csv,
            write_ibkr_readonly_first_connect_disconnect_report,
        )

        input_source = (
            args.ibkr_first_readonly_connect_disconnect
            if args.ibkr_first_readonly_connect_disconnect
            else args.config
        )

        rows = build_ibkr_readonly_first_connect_disconnect_rows(
            input_source,
            execute=args.execute_ibkr_readonly_connect_disconnect,
        )

        csv_path = Path(
            monitor.config["runtime"].get(
                "ibkr_readonly_first_connect_disconnect_csv",
                "ibkr_readonly_first_connect_disconnect.csv",
            )
        )
        md_path = Path(
            monitor.config["runtime"].get(
                "ibkr_readonly_first_connect_disconnect_report",
                "reports/ibkr_readonly_first_connect_disconnect_report.md",
            )
        )
        csv_path.parent.mkdir(parents=True, exist_ok=True)
        md_path.parent.mkdir(parents=True, exist_ok=True)

        write_ibkr_readonly_first_connect_disconnect_csv(csv_path, rows)
        write_ibkr_readonly_first_connect_disconnect_report(md_path, rows, input_source)

        statuses = sorted({r.status for r in rows})
        profiles = sorted({r.selected_profile for r in rows})
        status_text = ",".join(statuses) if statuses else "none"
        profile_text = ",".join(profiles) if profiles else "none"
        actual_connection_rows = [r for r in rows if r.row_id == "CONNECT_DISCONNECT"]
        connection_attempts = sum(
            1 for r in actual_connection_rows if r.connection_attempted == "true"
        )
        connect_success = sum(
            1 for r in actual_connection_rows if r.connect_succeeded == "true"
        )
        current_allowed = sum(
            1 for r in actual_connection_rows if r.current_call_allowed == "true"
        )

        print(
            "[IBKR_FIRST_READONLY_CONNECT_DISCONNECT] "
            f"rows={len(rows)} selected_profile={profile_text} statuses={status_text} "
            f"execute_requested={args.execute_ibkr_readonly_connect_disconnect} "
            f"connection_attempts={connection_attempts} connect_success={connect_success} "
            f"current_call_allowed={current_allowed} "
            "market_data_request_allowed=false historical_data_request_allowed=false "
            "contract_qualification_allowed=false action_allowed=false"
        )
        print(f"first_connect_disconnect_csv={csv_path}")
        print(f"report={md_path}")
        print(
            "NOTICE: Phase 17A connect/disconnect only. "
            "Default is dry-run. Execute flag allows only connect/disconnect and connection metadata. "
            "No market data / no historical data / no real contract qualification / "
            "no order action / no cancellation action / no rebalance / no auto trade."
        )
        return 0

    if args.ibkr_readonly_authorization_pack is not None:
        from pathlib import Path

        from src.ibkr_readonly_authorization_pack import (
            build_ibkr_readonly_authorization_pack_rows,
            write_ibkr_readonly_authorization_pack_csv,
            write_ibkr_readonly_authorization_pack_report,
        )

        input_source = (
            args.ibkr_readonly_authorization_pack
            if args.ibkr_readonly_authorization_pack
            else args.config
        )

        rows = build_ibkr_readonly_authorization_pack_rows(input_source)

        csv_path = Path(
            monitor.config["runtime"].get(
                "ibkr_readonly_authorization_pack_csv",
                "ibkr_readonly_authorization_pack.csv",
            )
        )
        md_path = Path(
            monitor.config["runtime"].get(
                "ibkr_readonly_authorization_pack_report",
                "reports/ibkr_readonly_authorization_pack_report.md",
            )
        )
        csv_path.parent.mkdir(parents=True, exist_ok=True)
        md_path.parent.mkdir(parents=True, exist_ok=True)

        write_ibkr_readonly_authorization_pack_csv(csv_path, rows)
        write_ibkr_readonly_authorization_pack_report(md_path, rows, input_source)

        statuses = sorted({r.authorization_status for r in rows})
        profiles = sorted({r.selected_profile for r in rows})
        status_text = ",".join(statuses) if statuses else "none"
        profile_text = ",".join(profiles) if profiles else "none"
        operator_approved = sum(1 for r in rows if r.operator_approved == "true")
        next_allowed = sum(1 for r in rows if r.next_real_connection_phase_allowed == "true")
        current_allowed = sum(1 for r in rows if r.current_connection_allowed == "true")

        print(
            "[IBKR_READONLY_AUTHORIZATION_PACK] "
            f"rows={len(rows)} selected_profile={profile_text} statuses={status_text} "
            f"operator_approved={operator_approved} "
            f"current_connection_allowed={current_allowed} "
            f"next_real_connection_phase_allowed={next_allowed} "
            "config_file_modified=false real_connection_allowed=false "
            "tws_connection_allowed=false ibkr_api_request_allowed=false action_allowed=false"
        )
        print(f"authorization_pack_csv={csv_path}")
        print(f"report={md_path}")
        print(
            "NOTICE: IBKR read-only authorization pack only. "
            "No config file modification / no TWS connection / no IBKR connection / "
            "no reqMktData / no reqHistoricalData / no real contract qualification / "
            "no order / no cancellation action / no rebalance / no auto trade."
        )
        return 0

    if args.ibkr_readonly_connection_preflight_pack is not None:
        from pathlib import Path

        from src.ibkr_readonly_connection_preflight_pack import (
            build_ibkr_readonly_connection_preflight_pack_rows,
            write_ibkr_readonly_connection_preflight_pack_csv,
            write_ibkr_readonly_connection_preflight_pack_report,
        )

        input_source = (
            args.ibkr_readonly_connection_preflight_pack
            if args.ibkr_readonly_connection_preflight_pack
            else args.config
        )

        rows = build_ibkr_readonly_connection_preflight_pack_rows(input_source)

        csv_path = Path(
            monitor.config["runtime"].get(
                "ibkr_readonly_connection_preflight_pack_csv",
                "ibkr_readonly_connection_preflight_pack.csv",
            )
        )
        md_path = Path(
            monitor.config["runtime"].get(
                "ibkr_readonly_connection_preflight_pack_report",
                "reports/ibkr_readonly_connection_preflight_pack_report.md",
            )
        )
        csv_path.parent.mkdir(parents=True, exist_ok=True)
        md_path.parent.mkdir(parents=True, exist_ok=True)

        write_ibkr_readonly_connection_preflight_pack_csv(csv_path, rows)
        write_ibkr_readonly_connection_preflight_pack_report(md_path, rows, input_source)

        statuses = sorted({r.preflight_status for r in rows})
        profiles = sorted({r.selected_profile for r in rows})
        status_text = ",".join(statuses) if statuses else "none"
        profile_text = ",".join(profiles) if profiles else "none"
        current_allowed = sum(1 for r in rows if r.current_call_allowed == "true")
        next_allowed = sum(1 for r in rows if r.next_connection_phase_allowed == "true")

        print(
            "[IBKR_READONLY_CONNECTION_PREFLIGHT_PACK] "
            f"rows={len(rows)} selected_profile={profile_text} statuses={status_text} "
            f"current_call_allowed={current_allowed} "
            f"next_connection_phase_allowed={next_allowed} "
            "config_file_modified=false real_connection_allowed=false "
            "tws_connection_allowed=false ibkr_api_request_allowed=false action_allowed=false"
        )
        print(f"connection_preflight_pack_csv={csv_path}")
        print(f"report={md_path}")
        print(
            "NOTICE: IBKR read-only connection preflight pack only. "
            "No config file modification / no TWS connection / no IBKR connection / "
            "no reqMktData / no reqHistoricalData / no real contract qualification / "
            "no order / no cancel / no rebalance / no auto trade."
        )
        return 0

    if args.ibkr_readonly_external_readiness_pack is not None:
        from pathlib import Path

        from src.ibkr_readonly_external_readiness_pack import (
            build_ibkr_readonly_external_readiness_pack_rows,
            write_ibkr_readonly_external_readiness_pack_csv,
            write_ibkr_readonly_external_readiness_pack_report,
        )

        input_source = (
            args.ibkr_readonly_external_readiness_pack
            if args.ibkr_readonly_external_readiness_pack
            else args.config
        )

        rows = build_ibkr_readonly_external_readiness_pack_rows(input_source)

        csv_path = Path(
            monitor.config["runtime"].get(
                "ibkr_readonly_external_readiness_pack_csv",
                "ibkr_readonly_external_readiness_pack.csv",
            )
        )
        md_path = Path(
            monitor.config["runtime"].get(
                "ibkr_readonly_external_readiness_pack_report",
                "reports/ibkr_readonly_external_readiness_pack_report.md",
            )
        )
        csv_path.parent.mkdir(parents=True, exist_ok=True)
        md_path.parent.mkdir(parents=True, exist_ok=True)

        write_ibkr_readonly_external_readiness_pack_csv(csv_path, rows)
        write_ibkr_readonly_external_readiness_pack_report(md_path, rows, input_source)

        statuses = sorted({r.readiness_status for r in rows})
        profiles = sorted({r.selected_profile for r in rows})
        status_text = ",".join(statuses) if statuses else "none"
        profile_text = ",".join(profiles) if profiles else "none"
        operator_required = sum(1 for r in rows if r.operator_review_required == "true")
        next_allowed = sum(1 for r in rows if r.next_connection_phase_allowed == "true")

        print(
            "[IBKR_READONLY_EXTERNAL_READINESS_PACK] "
            f"rows={len(rows)} selected_profile={profile_text} statuses={status_text} "
            f"operator_review_required={operator_required} "
            f"next_connection_phase_allowed={next_allowed} "
            "config_file_modified=false real_connection_allowed=false "
            "tws_connection_allowed=false ibkr_api_request_allowed=false action_allowed=false"
        )
        print(f"external_readiness_pack_csv={csv_path}")
        print(f"report={md_path}")
        print(
            "NOTICE: IBKR read-only external readiness pack only. "
            "No config file modification / no TWS connection / no IBKR connection / "
            "no reqMktData / no reqHistoricalData / no real contract qualification / "
            "no order / no cancel / no rebalance / no auto trade."
        )
        return 0

    if args.ibkr_readonly_tws_environment_checklist is not None:
        from pathlib import Path

        from src.ibkr_readonly_tws_environment_checklist import (
            build_ibkr_readonly_tws_environment_checklist_rows,
            write_ibkr_readonly_tws_environment_checklist_csv,
            write_ibkr_readonly_tws_environment_checklist_report,
        )

        input_source = (
            args.ibkr_readonly_tws_environment_checklist
            if args.ibkr_readonly_tws_environment_checklist
            else args.config
        )

        rows = build_ibkr_readonly_tws_environment_checklist_rows(input_source)

        csv_path = Path(
            monitor.config["runtime"].get(
                "ibkr_readonly_tws_environment_checklist_csv",
                "ibkr_readonly_tws_environment_checklist.csv",
            )
        )
        md_path = Path(
            monitor.config["runtime"].get(
                "ibkr_readonly_tws_environment_checklist_report",
                "reports/ibkr_readonly_tws_environment_checklist_report.md",
            )
        )
        csv_path.parent.mkdir(parents=True, exist_ok=True)
        md_path.parent.mkdir(parents=True, exist_ok=True)

        write_ibkr_readonly_tws_environment_checklist_csv(csv_path, rows)
        write_ibkr_readonly_tws_environment_checklist_report(md_path, rows, input_source)

        statuses = sorted({r.checklist_status for r in rows})
        profiles = sorted({r.selected_profile for r in rows})
        status_text = ",".join(statuses) if statuses else "none"
        profile_text = ",".join(profiles) if profiles else "none"
        manual_count = sum(1 for r in rows if r.manual_check_required == "true")

        print(
            "[IBKR_READONLY_TWS_ENVIRONMENT_CHECKLIST] "
            f"rows={len(rows)} selected_profile={profile_text} statuses={status_text} "
            f"manual_required={manual_count} "
            "config_file_modified=false real_connection_allowed=false "
            "tws_connection_allowed=false ibkr_api_request_allowed=false action_allowed=false"
        )
        print(f"tws_environment_checklist_csv={csv_path}")
        print(f"report={md_path}")
        print(
            "NOTICE: IBKR read-only TWS environment checklist only. "
            "No config file modification / no TWS connection / no IBKR connection / "
            "no reqMktData / no reqHistoricalData / no real contract qualification / "
            "no order / no cancel / no rebalance / no auto trade."
        )
        return 0

    if args.ibkr_readonly_preflight_profile_aware_final_gate is not None:
        from pathlib import Path

        from src.ibkr_readonly_preflight_profile_aware_config_plan import SUPPORTED_PROFILES
        from src.ibkr_readonly_preflight_profile_aware_final_gate import (
            build_ibkr_readonly_preflight_profile_aware_final_gate_rows,
            write_ibkr_readonly_preflight_profile_aware_final_gate_csv,
            write_ibkr_readonly_preflight_profile_aware_final_gate_report,
        )

        raw_selector = args.ibkr_readonly_preflight_profile_aware_final_gate
        if raw_selector in SUPPORTED_PROFILES:
            input_source = args.config
            requested_profile = raw_selector
        else:
            input_source = raw_selector if raw_selector else args.config
            requested_profile = "auto"

        rows = build_ibkr_readonly_preflight_profile_aware_final_gate_rows(
            input_source,
            requested_profile,
        )

        csv_path = Path(
            monitor.config["runtime"].get(
                "ibkr_readonly_preflight_profile_aware_final_gate_csv",
                "ibkr_readonly_preflight_profile_aware_final_gate.csv",
            )
        )
        md_path = Path(
            monitor.config["runtime"].get(
                "ibkr_readonly_preflight_profile_aware_final_gate_report",
                "reports/ibkr_readonly_preflight_profile_aware_final_gate_report.md",
            )
        )
        csv_path.parent.mkdir(parents=True, exist_ok=True)
        md_path.parent.mkdir(parents=True, exist_ok=True)

        write_ibkr_readonly_preflight_profile_aware_final_gate_csv(csv_path, rows)
        write_ibkr_readonly_preflight_profile_aware_final_gate_report(md_path, rows, input_source)

        decisions = sorted({r.final_gate_decision for r in rows})
        statuses = sorted({r.gate_status for r in rows})
        profiles = sorted({r.selected_profile for r in rows})
        decision_text = ",".join(decisions) if decisions else "none"
        status_text = ",".join(statuses) if statuses else "none"
        profile_text = ",".join(profiles) if profiles else "none"
        final_rows = [r for r in rows if r.gate_id == "FINAL"]
        final_decision = final_rows[0].final_gate_decision if final_rows else "NO_GO"

        print(
            "[IBKR_READONLY_PREFLIGHT_PROFILE_AWARE_FINAL_GATE] "
            f"rows={len(rows)} selected_profile={profile_text} statuses={status_text} "
            f"decisions={decision_text} final_decision={final_decision} "
            "config_file_modified=false real_connection_allowed=false "
            "tws_connection_allowed=false ibkr_api_request_allowed=false action_allowed=false"
        )
        print(f"profile_aware_final_gate_csv={csv_path}")
        print(f"report={md_path}")
        print(
            "NOTICE: IBKR read-only preflight profile-aware final gate only. "
            "No config file modification / no TWS connection / no IBKR connection / "
            "no reqMktData / no reqHistoricalData / no real contract qualification / "
            "no order / no cancel / no rebalance / no auto trade."
        )
        return 0

    if args.ibkr_readonly_preflight_profile_aware_config_plan is not None:
        from pathlib import Path

        from src.ibkr_readonly_preflight_profile_aware_config_plan import (
            SUPPORTED_PROFILES,
            build_ibkr_readonly_preflight_profile_aware_config_plan_rows,
            write_ibkr_readonly_preflight_profile_aware_config_plan_csv,
            write_ibkr_readonly_preflight_profile_aware_config_plan_report,
        )

        raw_selector = args.ibkr_readonly_preflight_profile_aware_config_plan
        if raw_selector in SUPPORTED_PROFILES:
            input_source = args.config
            requested_profile = raw_selector
        else:
            input_source = raw_selector if raw_selector else args.config
            requested_profile = "auto"

        rows = build_ibkr_readonly_preflight_profile_aware_config_plan_rows(
            input_source,
            requested_profile,
        )

        csv_path = Path(
            monitor.config["runtime"].get(
                "ibkr_readonly_preflight_profile_aware_config_plan_csv",
                "ibkr_readonly_preflight_profile_aware_config_plan.csv",
            )
        )
        md_path = Path(
            monitor.config["runtime"].get(
                "ibkr_readonly_preflight_profile_aware_config_plan_report",
                "reports/ibkr_readonly_preflight_profile_aware_config_plan_report.md",
            )
        )
        csv_path.parent.mkdir(parents=True, exist_ok=True)
        md_path.parent.mkdir(parents=True, exist_ok=True)

        write_ibkr_readonly_preflight_profile_aware_config_plan_csv(csv_path, rows)
        write_ibkr_readonly_preflight_profile_aware_config_plan_report(md_path, rows, input_source)

        actions = sorted({r.planned_action for r in rows})
        statuses = sorted({r.profile_plan_status for r in rows})
        profiles = sorted({r.selected_profile for r in rows})
        action_text = ",".join(actions) if actions else "none"
        status_text = ",".join(statuses) if statuses else "none"
        profile_text = ",".join(profiles) if profiles else "none"
        overwrite_count = sum(1 for r in rows if r.would_overwrite_existing == "true")

        print(
            "[IBKR_READONLY_PREFLIGHT_PROFILE_AWARE_CONFIG_PLAN] "
            f"rows={len(rows)} selected_profile={profile_text} actions={action_text} "
            f"statuses={status_text} overwrite_existing={overwrite_count} "
            "apply_mode=profile_aware_plan_only config_file_modified=false "
            "real_connection_allowed=false tws_connection_allowed=false "
            "ibkr_api_request_allowed=false action_allowed=false"
        )
        print(f"profile_aware_config_plan_csv={csv_path}")
        print(f"report={md_path}")
        print(
            "NOTICE: IBKR read-only preflight profile-aware config plan only. "
            "No config file modification / no TWS connection / no IBKR connection / "
            "no reqMktData / no reqHistoricalData / no real contract qualification / "
            "no order / no cancel / no rebalance / no auto trade."
        )
        return 0

    if args.ibkr_readonly_preflight_safe_config_merge_plan is not None:
        from pathlib import Path

        from src.ibkr_readonly_preflight_safe_config_merge_plan import (
            build_ibkr_readonly_preflight_safe_config_merge_plan_rows,
            write_ibkr_readonly_preflight_safe_config_merge_plan_csv,
            write_ibkr_readonly_preflight_safe_config_merge_plan_report,
        )

        input_source = (
            args.ibkr_readonly_preflight_safe_config_merge_plan
            if args.ibkr_readonly_preflight_safe_config_merge_plan
            else args.config
        )

        rows = build_ibkr_readonly_preflight_safe_config_merge_plan_rows(input_source)

        csv_path = Path(
            monitor.config["runtime"].get(
                "ibkr_readonly_preflight_safe_config_merge_plan_csv",
                "ibkr_readonly_preflight_safe_config_merge_plan.csv",
            )
        )
        md_path = Path(
            monitor.config["runtime"].get(
                "ibkr_readonly_preflight_safe_config_merge_plan_report",
                "reports/ibkr_readonly_preflight_safe_config_merge_plan_report.md",
            )
        )
        csv_path.parent.mkdir(parents=True, exist_ok=True)
        md_path.parent.mkdir(parents=True, exist_ok=True)

        write_ibkr_readonly_preflight_safe_config_merge_plan_csv(csv_path, rows)
        write_ibkr_readonly_preflight_safe_config_merge_plan_report(md_path, rows, input_source)

        actions = sorted({r.merge_action for r in rows})
        statuses = sorted({r.merge_plan_status for r in rows})
        action_text = ",".join(actions) if actions else "none"
        status_text = ",".join(statuses) if statuses else "none"
        overwrite_count = sum(1 for r in rows if r.would_overwrite_existing == "true")

        print(
            "[IBKR_READONLY_PREFLIGHT_SAFE_CONFIG_MERGE_PLAN] "
            f"rows={len(rows)} actions={action_text} statuses={status_text} "
            f"overwrite_existing={overwrite_count} "
            "apply_mode=manual_merge_plan_only config_file_modified=false "
            "real_connection_allowed=false tws_connection_allowed=false "
            "ibkr_api_request_allowed=false action_allowed=false"
        )
        print(f"safe_config_merge_plan_csv={csv_path}")
        print(f"report={md_path}")
        print(
            "NOTICE: IBKR read-only preflight safe config merge plan only. "
            "No config file modification / no TWS connection / no IBKR connection / "
            "no reqMktData / no reqHistoricalData / no real contract qualification / "
            "no order / no cancel / no rebalance / no auto trade."
        )
        return 0

    if args.ibkr_readonly_preflight_final_gate is not None:
        from pathlib import Path

        from src.ibkr_readonly_preflight_final_gate import (
            build_ibkr_readonly_preflight_final_gate_rows,
            write_ibkr_readonly_preflight_final_gate_csv,
            write_ibkr_readonly_preflight_final_gate_report,
        )

        input_source = (
            args.ibkr_readonly_preflight_final_gate
            if args.ibkr_readonly_preflight_final_gate
            else args.config
        )

        rows = build_ibkr_readonly_preflight_final_gate_rows(input_source)

        csv_path = Path(
            monitor.config["runtime"].get(
                "ibkr_readonly_preflight_final_gate_csv",
                "ibkr_readonly_preflight_final_gate.csv",
            )
        )
        md_path = Path(
            monitor.config["runtime"].get(
                "ibkr_readonly_preflight_final_gate_report",
                "reports/ibkr_readonly_preflight_final_gate_report.md",
            )
        )
        csv_path.parent.mkdir(parents=True, exist_ok=True)
        md_path.parent.mkdir(parents=True, exist_ok=True)

        write_ibkr_readonly_preflight_final_gate_csv(csv_path, rows)
        write_ibkr_readonly_preflight_final_gate_report(md_path, rows, input_source)

        decisions = sorted({r.final_gate_decision for r in rows})
        statuses = sorted({r.gate_status for r in rows})
        decision_text = ",".join(decisions) if decisions else "none"
        status_text = ",".join(statuses) if statuses else "none"
        final_rows = [r for r in rows if r.gate_id == "FINAL"]
        final_decision = final_rows[0].final_gate_decision if final_rows else "NO_GO"

        print(
            "[IBKR_READONLY_PREFLIGHT_FINAL_GATE] "
            f"rows={len(rows)} statuses={status_text} decisions={decision_text} "
            f"final_decision={final_decision} "
            "config_file_modified=false real_connection_allowed=false "
            "tws_connection_allowed=false ibkr_api_request_allowed=false action_allowed=false"
        )
        print(f"preflight_final_gate_csv={csv_path}")
        print(f"report={md_path}")
        print(
            "NOTICE: IBKR read-only preflight final gate only. "
            "No config file modification / no TWS connection / no IBKR connection / "
            "no reqMktData / no reqHistoricalData / no real contract qualification / "
            "no order / no cancel / no rebalance / no auto trade."
        )
        return 0

    if args.ibkr_readonly_preflight_config_apply_plan is not None:
        from pathlib import Path

        from src.ibkr_readonly_preflight_config_apply_plan import (
            build_ibkr_readonly_preflight_config_apply_plan_rows,
            write_ibkr_readonly_preflight_config_apply_plan_csv,
            write_ibkr_readonly_preflight_config_apply_plan_report,
        )

        input_source = (
            args.ibkr_readonly_preflight_config_apply_plan
            if args.ibkr_readonly_preflight_config_apply_plan
            else args.config
        )

        rows = build_ibkr_readonly_preflight_config_apply_plan_rows(input_source)

        csv_path = Path(
            monitor.config["runtime"].get(
                "ibkr_readonly_preflight_config_apply_plan_csv",
                "ibkr_readonly_preflight_config_apply_plan.csv",
            )
        )
        md_path = Path(
            monitor.config["runtime"].get(
                "ibkr_readonly_preflight_config_apply_plan_report",
                "reports/ibkr_readonly_preflight_config_apply_plan_report.md",
            )
        )
        csv_path.parent.mkdir(parents=True, exist_ok=True)
        md_path.parent.mkdir(parents=True, exist_ok=True)

        write_ibkr_readonly_preflight_config_apply_plan_csv(csv_path, rows)
        write_ibkr_readonly_preflight_config_apply_plan_report(md_path, rows, input_source)

        changes = sorted({r.planned_change for r in rows})
        statuses = sorted({r.plan_status for r in rows})
        change_text = ",".join(changes) if changes else "none"
        status_text = ",".join(statuses) if statuses else "none"
        print(
            "[IBKR_READONLY_PREFLIGHT_CONFIG_APPLY_PLAN] "
            f"rows={len(rows)} changes={change_text} statuses={status_text} "
            "apply_mode=plan_only config_file_modified=false "
            "real_connection_allowed=false tws_connection_allowed=false "
            "ibkr_api_request_allowed=false action_allowed=false"
        )
        print(f"preflight_config_apply_plan_csv={csv_path}")
        print(f"report={md_path}")
        print(
            "NOTICE: IBKR read-only preflight config apply plan only. "
            "No config file modification / no TWS connection / no IBKR connection / "
            "no reqMktData / no reqHistoricalData / no real contract qualification / "
            "no order / no cancel / no rebalance / no auto trade."
        )
        return 0

    if args.ibkr_readonly_preflight_config_template is not None:
        from pathlib import Path

        from src.ibkr_readonly_preflight_config_template import (
            build_ibkr_readonly_preflight_config_template_rows,
            write_ibkr_readonly_preflight_config_template_csv,
            write_ibkr_readonly_preflight_config_template_report,
            write_ibkr_readonly_preflight_config_template_yaml,
        )

        input_source = (
            args.ibkr_readonly_preflight_config_template
            if args.ibkr_readonly_preflight_config_template
            else args.config
        )

        rows = build_ibkr_readonly_preflight_config_template_rows(input_source)

        csv_path = Path(
            monitor.config["runtime"].get(
                "ibkr_readonly_preflight_config_template_csv",
                "ibkr_readonly_preflight_config_template.csv",
            )
        )
        yaml_path = Path(
            monitor.config["runtime"].get(
                "ibkr_readonly_preflight_config_template_yaml",
                "ibkr_readonly_preflight_config_template.yaml",
            )
        )
        md_path = Path(
            monitor.config["runtime"].get(
                "ibkr_readonly_preflight_config_template_report",
                "reports/ibkr_readonly_preflight_config_template_report.md",
            )
        )
        csv_path.parent.mkdir(parents=True, exist_ok=True)
        yaml_path.parent.mkdir(parents=True, exist_ok=True)
        md_path.parent.mkdir(parents=True, exist_ok=True)

        write_ibkr_readonly_preflight_config_template_csv(csv_path, rows)
        write_ibkr_readonly_preflight_config_template_yaml(yaml_path, rows)
        write_ibkr_readonly_preflight_config_template_report(md_path, rows, input_source, yaml_path)

        statuses = sorted({r.template_status for r in rows})
        status_text = ",".join(statuses) if statuses else "none"
        print(
            "[IBKR_READONLY_PREFLIGHT_CONFIG_TEMPLATE] "
            f"rows={len(rows)} statuses={status_text} "
            "apply_mode=template_only config_file_modified=false "
            "real_connection_allowed=false tws_connection_allowed=false "
            "ibkr_api_request_allowed=false action_allowed=false"
        )
        print(f"preflight_config_template_csv={csv_path}")
        print(f"preflight_config_template_yaml={yaml_path}")
        print(f"report={md_path}")
        print(
            "NOTICE: IBKR read-only preflight config template only. "
            "No config file modification / no TWS connection / no IBKR connection / "
            "no reqMktData / no reqHistoricalData / no real contract qualification / "
            "no order / no cancel / no rebalance / no auto trade."
        )
        return 0

    if args.ibkr_readonly_preflight_config_validator is not None:
        from pathlib import Path

        from src.ibkr_readonly_preflight_config_validator import (
            build_ibkr_readonly_preflight_config_validator_rows,
            write_ibkr_readonly_preflight_config_validator_csv,
            write_ibkr_readonly_preflight_config_validator_report,
        )

        input_source = (
            args.ibkr_readonly_preflight_config_validator
            if args.ibkr_readonly_preflight_config_validator
            else args.config
        )

        rows = build_ibkr_readonly_preflight_config_validator_rows(input_source)

        csv_path = Path(
            monitor.config["runtime"].get(
                "ibkr_readonly_preflight_config_validator_csv",
                "ibkr_readonly_preflight_config_validator.csv",
            )
        )
        md_path = Path(
            monitor.config["runtime"].get(
                "ibkr_readonly_preflight_config_validator_report",
                "reports/ibkr_readonly_preflight_config_validator_report.md",
            )
        )
        csv_path.parent.mkdir(parents=True, exist_ok=True)
        md_path.parent.mkdir(parents=True, exist_ok=True)

        write_ibkr_readonly_preflight_config_validator_csv(csv_path, rows)
        write_ibkr_readonly_preflight_config_validator_report(md_path, rows, input_source)

        statuses = sorted({r.validation_status for r in rows})
        status_text = ",".join(statuses) if statuses else "none"
        final_status = "PASS" if all(r.validation_status == "PASS" for r in rows) else "FAIL"
        print(
            "[IBKR_READONLY_PREFLIGHT_CONFIG_VALIDATOR] "
            f"rows={len(rows)} statuses={status_text} final_status={final_status} "
            "real_connection_allowed=false tws_connection_allowed=false "
            "ibkr_api_request_allowed=false action_allowed=false"
        )
        print(f"preflight_config_validator_csv={csv_path}")
        print(f"report={md_path}")
        print(
            "NOTICE: IBKR read-only preflight config validator only. "
            "No TWS connection / no IBKR connection / no reqMktData / no reqHistoricalData / "
            "no real contract qualification / no order / no cancel / no rebalance / no auto trade."
        )
        return 0

    if args.ibkr_readonly_preflight_config_contract is not None:
        from pathlib import Path

        from src.ibkr_readonly_preflight_config_contract import (
            build_ibkr_readonly_preflight_config_contract_rows,
            write_ibkr_readonly_preflight_config_contract_csv,
            write_ibkr_readonly_preflight_config_contract_report,
        )

        input_source = (
            args.ibkr_readonly_preflight_config_contract
            if args.ibkr_readonly_preflight_config_contract
            else "data/market_data_provider_config.yaml"
        )

        rows = build_ibkr_readonly_preflight_config_contract_rows(input_source)

        csv_path = Path(
            monitor.config["runtime"].get(
                "ibkr_readonly_preflight_config_contract_csv",
                "ibkr_readonly_preflight_config_contract.csv",
            )
        )
        md_path = Path(
            monitor.config["runtime"].get(
                "ibkr_readonly_preflight_config_contract_report",
                "reports/ibkr_readonly_preflight_config_contract_report.md",
            )
        )
        csv_path.parent.mkdir(parents=True, exist_ok=True)
        md_path.parent.mkdir(parents=True, exist_ok=True)

        write_ibkr_readonly_preflight_config_contract_csv(csv_path, rows)
        write_ibkr_readonly_preflight_config_contract_report(md_path, rows, input_source)

        statuses = sorted({r.preflight_config_contract_status for r in rows})
        status_text = ",".join(statuses) if statuses else "none"
        print(
            "[IBKR_READONLY_PREFLIGHT_CONFIG_CONTRACT] "
            f"rows={len(rows)} statuses={status_text} "
            "read_only_required=true account_mode_explicit_required=true "
            "real_connection_allowed=false tws_connection_allowed=false "
            "ibkr_api_request_allowed=false action_allowed=false"
        )
        print(f"preflight_config_contract_csv={csv_path}")
        print(f"report={md_path}")
        print(
            "NOTICE: IBKR read-only preflight config contract only. "
            "No TWS connection / no IBKR connection / no reqMktData / no reqHistoricalData / "
            "no real contract qualification / no order / no cancel / no rebalance / no auto trade."
        )
        return 0

    if args.ibkr_readonly_preflight_guard_design is not None:
        from pathlib import Path

        from src.ibkr_readonly_preflight_guard_design import (
            build_ibkr_readonly_preflight_guard_design_rows,
            write_ibkr_readonly_preflight_guard_design_csv,
            write_ibkr_readonly_preflight_guard_design_report,
        )

        input_source = (
            args.ibkr_readonly_preflight_guard_design
            if args.ibkr_readonly_preflight_guard_design
            else "data/market_data_provider_config.yaml"
        )

        rows = build_ibkr_readonly_preflight_guard_design_rows(input_source)

        csv_path = Path(
            monitor.config["runtime"].get(
                "ibkr_readonly_preflight_guard_design_csv",
                "ibkr_readonly_preflight_guard_design.csv",
            )
        )
        md_path = Path(
            monitor.config["runtime"].get(
                "ibkr_readonly_preflight_guard_design_report",
                "reports/ibkr_readonly_preflight_guard_design_report.md",
            )
        )
        csv_path.parent.mkdir(parents=True, exist_ok=True)
        md_path.parent.mkdir(parents=True, exist_ok=True)

        write_ibkr_readonly_preflight_guard_design_csv(csv_path, rows)
        write_ibkr_readonly_preflight_guard_design_report(md_path, rows, input_source)

        statuses = sorted({r.preflight_guard_status for r in rows})
        status_text = ",".join(statuses) if statuses else "none"
        print(
            "[IBKR_READONLY_PREFLIGHT_GUARD_DESIGN] "
            f"rows={len(rows)} statuses={status_text} "
            "design_only=true required_before_real_connection=true "
            "real_connection_allowed=false tws_connection_allowed=false "
            "ibkr_api_request_allowed=false action_allowed=false"
        )
        print(f"preflight_guard_design_csv={csv_path}")
        print(f"report={md_path}")
        print(
            "NOTICE: IBKR read-only preflight guard design only. "
            "No TWS connection / no IBKR connection / no reqMktData / no reqHistoricalData / "
            "no real contract qualification / no order / no cancel / no rebalance / no auto trade."
        )
        return 0

    if args.ibkr_readonly_qualification_sandbox_closure_report is not None:
        from pathlib import Path

        from src.ibkr_readonly_qualification_sandbox_closure_report import (
            build_ibkr_readonly_qualification_sandbox_closure_report_rows,
            write_ibkr_readonly_qualification_sandbox_closure_report_csv,
            write_ibkr_readonly_qualification_sandbox_closure_report_report,
        )

        input_source = (
            args.ibkr_readonly_qualification_sandbox_closure_report
            if args.ibkr_readonly_qualification_sandbox_closure_report
            else "data/market_data_provider_config.yaml"
        )

        rows = build_ibkr_readonly_qualification_sandbox_closure_report_rows(input_source)

        csv_path = Path(
            monitor.config["runtime"].get(
                "ibkr_readonly_qualification_sandbox_closure_report_csv",
                "ibkr_readonly_qualification_sandbox_closure_report.csv",
            )
        )
        md_path = Path(
            monitor.config["runtime"].get(
                "ibkr_readonly_qualification_sandbox_closure_report",
                "reports/ibkr_readonly_qualification_sandbox_closure_report.md",
            )
        )
        csv_path.parent.mkdir(parents=True, exist_ok=True)
        md_path.parent.mkdir(parents=True, exist_ok=True)

        write_ibkr_readonly_qualification_sandbox_closure_report_csv(csv_path, rows)
        write_ibkr_readonly_qualification_sandbox_closure_report_report(md_path, rows, input_source)

        statuses = sorted({r.sandbox_closure_status for r in rows})
        status_text = ",".join(statuses) if statuses else "none"
        complete_count = sum(1 for r in rows if r.sandbox_closure_status == "COMPLETE")
        print(
            "[IBKR_READONLY_QUALIFICATION_SANDBOX_CLOSURE_REPORT] "
            f"rows={len(rows)} statuses={status_text} complete={complete_count} "
            "sandbox_final_review_status=READY_FOR_REVIEW sandbox_safety_gate_status=CLOSED "
            "simulated_result_only=true real_qualification_allowed=false "
            "tws_connection_allowed=false ibkr_api_request_allowed=false action_allowed=false"
        )
        print(f"sandbox_closure_report_csv={csv_path}")
        print(f"report={md_path}")
        print(
            "NOTICE: IBKR read-only qualification sandbox closure report only. "
            "Phase 13 sandbox loop is complete but execution remains blocked. "
            "No TWS connection / no IBKR connection / no reqMktData / no reqHistoricalData / "
            "no order / no cancel / no rebalance / no auto trade."
        )
        return 0

    if args.ibkr_readonly_qualification_sandbox_final_review_pack is not None:
        from pathlib import Path

        from src.ibkr_readonly_qualification_sandbox_final_review_pack import (
            build_ibkr_readonly_qualification_sandbox_final_review_pack_rows,
            write_ibkr_readonly_qualification_sandbox_final_review_pack_csv,
            write_ibkr_readonly_qualification_sandbox_final_review_pack_report,
        )

        input_source = (
            args.ibkr_readonly_qualification_sandbox_final_review_pack
            if args.ibkr_readonly_qualification_sandbox_final_review_pack
            else "data/market_data_provider_config.yaml"
        )

        rows = build_ibkr_readonly_qualification_sandbox_final_review_pack_rows(input_source)

        csv_path = Path(
            monitor.config["runtime"].get(
                "ibkr_readonly_qualification_sandbox_final_review_pack_csv",
                "ibkr_readonly_qualification_sandbox_final_review_pack.csv",
            )
        )
        md_path = Path(
            monitor.config["runtime"].get(
                "ibkr_readonly_qualification_sandbox_final_review_pack_report",
                "reports/ibkr_readonly_qualification_sandbox_final_review_pack_report.md",
            )
        )
        csv_path.parent.mkdir(parents=True, exist_ok=True)
        md_path.parent.mkdir(parents=True, exist_ok=True)

        write_ibkr_readonly_qualification_sandbox_final_review_pack_csv(csv_path, rows)
        write_ibkr_readonly_qualification_sandbox_final_review_pack_report(md_path, rows, input_source)

        statuses = sorted({r.sandbox_final_review_status for r in rows})
        status_text = ",".join(statuses) if statuses else "none"
        review_count = sum(1 for r in rows if r.sandbox_result_accepted_for_review == "true")
        print(
            "[IBKR_READONLY_QUALIFICATION_SANDBOX_FINAL_REVIEW_PACK] "
            f"rows={len(rows)} statuses={status_text} review_accepted={review_count} "
            "sandbox_safety_gate_status=CLOSED simulated_result_only=true "
            "real_qualification_allowed=false tws_connection_allowed=false "
            "ibkr_api_request_allowed=false action_allowed=false"
        )
        print(f"sandbox_final_review_pack_csv={csv_path}")
        print(f"report={md_path}")
        print(
            "NOTICE: IBKR read-only qualification sandbox final review pack only. "
            "Sandbox outputs are for review only; safety gate remains CLOSED. "
            "No TWS connection / no IBKR connection / no reqMktData / no reqHistoricalData / "
            "no order / no cancel / no rebalance / no auto trade."
        )
        return 0

    if args.ibkr_readonly_qualification_sandbox_safety_gate is not None:
        from pathlib import Path

        from src.ibkr_readonly_qualification_sandbox_safety_gate import (
            build_ibkr_readonly_qualification_sandbox_safety_gate_rows,
            write_ibkr_readonly_qualification_sandbox_safety_gate_csv,
            write_ibkr_readonly_qualification_sandbox_safety_gate_report,
        )

        input_source = (
            args.ibkr_readonly_qualification_sandbox_safety_gate
            if args.ibkr_readonly_qualification_sandbox_safety_gate
            else "data/market_data_provider_config.yaml"
        )

        rows = build_ibkr_readonly_qualification_sandbox_safety_gate_rows(input_source)

        csv_path = Path(
            monitor.config["runtime"].get(
                "ibkr_readonly_qualification_sandbox_safety_gate_csv",
                "ibkr_readonly_qualification_sandbox_safety_gate.csv",
            )
        )
        md_path = Path(
            monitor.config["runtime"].get(
                "ibkr_readonly_qualification_sandbox_safety_gate_report",
                "reports/ibkr_readonly_qualification_sandbox_safety_gate_report.md",
            )
        )
        csv_path.parent.mkdir(parents=True, exist_ok=True)
        md_path.parent.mkdir(parents=True, exist_ok=True)

        write_ibkr_readonly_qualification_sandbox_safety_gate_csv(csv_path, rows)
        write_ibkr_readonly_qualification_sandbox_safety_gate_report(md_path, rows, input_source)

        statuses = sorted({r.sandbox_safety_gate_status for r in rows})
        status_text = ",".join(statuses) if statuses else "none"
        review_count = sum(1 for r in rows if r.sandbox_result_accepted_for_review == "true")
        print(
            "[IBKR_READONLY_QUALIFICATION_SANDBOX_SAFETY_GATE] "
            f"rows={len(rows)} statuses={status_text} review_accepted={review_count} "
            "simulated_result_only=true real_qualification_allowed=false "
            "tws_connection_allowed=false ibkr_api_request_allowed=false action_allowed=false"
        )
        print(f"sandbox_safety_gate_csv={csv_path}")
        print(f"report={md_path}")
        print(
            "NOTICE: IBKR read-only qualification sandbox safety gate only. "
            "Sandbox results are accepted for review only; safety gate remains CLOSED. "
            "No TWS connection / no IBKR connection / no reqMktData / no reqHistoricalData / "
            "no order / no cancel / no rebalance / no auto trade."
        )
        return 0

    if args.ibkr_readonly_qualification_sandbox_result_pack is not None:
        from pathlib import Path

        from src.ibkr_readonly_qualification_sandbox_result_pack import (
            build_ibkr_readonly_qualification_sandbox_result_pack_rows,
            write_ibkr_readonly_qualification_sandbox_result_pack_csv,
            write_ibkr_readonly_qualification_sandbox_result_pack_report,
        )

        input_source = (
            args.ibkr_readonly_qualification_sandbox_result_pack
            if args.ibkr_readonly_qualification_sandbox_result_pack
            else "data/market_data_provider_config.yaml"
        )

        rows = build_ibkr_readonly_qualification_sandbox_result_pack_rows(input_source)

        csv_path = Path(
            monitor.config["runtime"].get(
                "ibkr_readonly_qualification_sandbox_result_pack_csv",
                "ibkr_readonly_qualification_sandbox_result_pack.csv",
            )
        )
        md_path = Path(
            monitor.config["runtime"].get(
                "ibkr_readonly_qualification_sandbox_result_pack_report",
                "reports/ibkr_readonly_qualification_sandbox_result_pack_report.md",
            )
        )
        csv_path.parent.mkdir(parents=True, exist_ok=True)
        md_path.parent.mkdir(parents=True, exist_ok=True)

        write_ibkr_readonly_qualification_sandbox_result_pack_csv(csv_path, rows)
        write_ibkr_readonly_qualification_sandbox_result_pack_report(md_path, rows, input_source)

        statuses = sorted({r.sandbox_result_pack_status for r in rows})
        status_text = ",".join(statuses) if statuses else "none"
        simulated_count = sum(1 for r in rows if r.sandbox_qualification_status == "SIMULATED")
        print(
            "[IBKR_READONLY_QUALIFICATION_SANDBOX_RESULT_PACK] "
            f"rows={len(rows)} statuses={status_text} simulated_results={simulated_count} "
            "simulated_result_only=true real_qualification_allowed=false "
            "tws_connection_allowed=false ibkr_api_request_allowed=false action_allowed=false"
        )
        print(f"sandbox_result_pack_csv={csv_path}")
        print(f"report={md_path}")
        print(
            "NOTICE: IBKR read-only qualification sandbox result pack only. "
            "Simulated results are not real IBKR qualification. "
            "No TWS connection / no IBKR connection / no reqMktData / no reqHistoricalData / "
            "no order / no cancel / no rebalance / no auto trade."
        )
        return 0

    if args.ibkr_readonly_qualification_sandbox_qualification_simulator is not None:
        from pathlib import Path

        from src.ibkr_readonly_qualification_sandbox_qualification_simulator import (
            build_ibkr_readonly_qualification_sandbox_qualification_simulator_rows,
            write_ibkr_readonly_qualification_sandbox_qualification_simulator_csv,
            write_ibkr_readonly_qualification_sandbox_qualification_simulator_report,
        )

        input_source = (
            args.ibkr_readonly_qualification_sandbox_qualification_simulator
            if args.ibkr_readonly_qualification_sandbox_qualification_simulator
            else "data/market_data_provider_config.yaml"
        )

        rows = build_ibkr_readonly_qualification_sandbox_qualification_simulator_rows(input_source)

        csv_path = Path(
            monitor.config["runtime"].get(
                "ibkr_readonly_qualification_sandbox_qualification_simulator_csv",
                "ibkr_readonly_qualification_sandbox_qualification_simulator.csv",
            )
        )
        md_path = Path(
            monitor.config["runtime"].get(
                "ibkr_readonly_qualification_sandbox_qualification_simulator_report",
                "reports/ibkr_readonly_qualification_sandbox_qualification_simulator_report.md",
            )
        )
        csv_path.parent.mkdir(parents=True, exist_ok=True)
        md_path.parent.mkdir(parents=True, exist_ok=True)

        write_ibkr_readonly_qualification_sandbox_qualification_simulator_csv(csv_path, rows)
        write_ibkr_readonly_qualification_sandbox_qualification_simulator_report(md_path, rows, input_source)

        statuses = sorted({r.sandbox_qualification_status for r in rows})
        status_text = ",".join(statuses) if statuses else "none"
        simulated_count = sum(1 for r in rows if r.sandbox_qualification_status == "SIMULATED")
        not_simulated_count = sum(1 for r in rows if r.sandbox_qualification_status == "NOT_SIMULATED")
        print(
            "[IBKR_READONLY_QUALIFICATION_SANDBOX_QUALIFICATION_SIMULATOR] "
            f"rows={len(rows)} statuses={status_text} simulated={simulated_count} not_simulated={not_simulated_count} "
            "real_qualification_allowed=false tws_connection_allowed=false "
            "ibkr_api_request_allowed=false action_allowed=false"
        )
        print(f"sandbox_qualification_simulator_csv={csv_path}")
        print(f"report={md_path}")
        print(
            "NOTICE: IBKR read-only qualification sandbox qualification simulator only. "
            "No real qualification / no TWS connection / no IBKR connection / "
            "no reqMktData / no reqHistoricalData / no order / no cancel / no rebalance / no auto trade."
        )
        return 0

    if args.ibkr_readonly_qualification_sandbox_input_validator is not None:
        from pathlib import Path

        from src.ibkr_readonly_qualification_sandbox_input_validator import (
            build_ibkr_readonly_qualification_sandbox_input_validator_rows,
            write_ibkr_readonly_qualification_sandbox_input_validator_csv,
            write_ibkr_readonly_qualification_sandbox_input_validator_report,
        )

        input_source = (
            args.ibkr_readonly_qualification_sandbox_input_validator
            if args.ibkr_readonly_qualification_sandbox_input_validator
            else "data/market_data_provider_config.yaml"
        )

        rows = build_ibkr_readonly_qualification_sandbox_input_validator_rows(input_source)

        csv_path = Path(
            monitor.config["runtime"].get(
                "ibkr_readonly_qualification_sandbox_input_validator_csv",
                "ibkr_readonly_qualification_sandbox_input_validator.csv",
            )
        )
        md_path = Path(
            monitor.config["runtime"].get(
                "ibkr_readonly_qualification_sandbox_input_validator_report",
                "reports/ibkr_readonly_qualification_sandbox_input_validator_report.md",
            )
        )
        csv_path.parent.mkdir(parents=True, exist_ok=True)
        md_path.parent.mkdir(parents=True, exist_ok=True)

        write_ibkr_readonly_qualification_sandbox_input_validator_csv(csv_path, rows)
        write_ibkr_readonly_qualification_sandbox_input_validator_report(md_path, rows, input_source)

        statuses = sorted({r.sandbox_input_validation_status for r in rows})
        status_text = ",".join(statuses) if statuses else "none"
        allowed_count = sum(1 for r in rows if r.input_allowed == "true")
        rejected_count = sum(1 for r in rows if r.rejection_required == "true")
        print(
            "[IBKR_READONLY_QUALIFICATION_SANDBOX_INPUT_VALIDATOR] "
            f"rows={len(rows)} statuses={status_text} allowed_inputs={allowed_count} rejected_inputs={rejected_count} "
            "sandbox_execution_allowed=false tws_connection_allowed=false "
            "ibkr_api_request_allowed=false action_allowed=false"
        )
        print(f"sandbox_input_validator_csv={csv_path}")
        print(f"report={md_path}")
        print(
            "NOTICE: IBKR read-only qualification sandbox input validator only. "
            "No real TWS input / no real IBKR runtime input / no TWS connection / no IBKR connection / "
            "no real contract qualification / no reqMktData / no reqHistoricalData / "
            "no order / no cancel / no rebalance / no auto trade."
        )
        return 0

    if args.ibkr_readonly_qualification_sandbox_input_contract is not None:
        from pathlib import Path

        from src.ibkr_readonly_qualification_sandbox_input_contract import (
            build_ibkr_readonly_qualification_sandbox_input_contract_rows,
            write_ibkr_readonly_qualification_sandbox_input_contract_csv,
            write_ibkr_readonly_qualification_sandbox_input_contract_report,
        )

        input_source = (
            args.ibkr_readonly_qualification_sandbox_input_contract
            if args.ibkr_readonly_qualification_sandbox_input_contract
            else "data/market_data_provider_config.yaml"
        )

        rows = build_ibkr_readonly_qualification_sandbox_input_contract_rows(input_source)

        csv_path = Path(
            monitor.config["runtime"].get(
                "ibkr_readonly_qualification_sandbox_input_contract_csv",
                "ibkr_readonly_qualification_sandbox_input_contract.csv",
            )
        )
        md_path = Path(
            monitor.config["runtime"].get(
                "ibkr_readonly_qualification_sandbox_input_contract_report",
                "reports/ibkr_readonly_qualification_sandbox_input_contract_report.md",
            )
        )
        csv_path.parent.mkdir(parents=True, exist_ok=True)
        md_path.parent.mkdir(parents=True, exist_ok=True)

        write_ibkr_readonly_qualification_sandbox_input_contract_csv(csv_path, rows)
        write_ibkr_readonly_qualification_sandbox_input_contract_report(md_path, rows, input_source)

        statuses = sorted({r.sandbox_input_contract_status for r in rows})
        status_text = ",".join(statuses) if statuses else "none"
        print(
            "[IBKR_READONLY_QUALIFICATION_SANDBOX_INPUT_CONTRACT] "
            f"rows={len(rows)} statuses={status_text} "
            "requires_explicit_sandbox_input=true accepts_real_tws_input=false "
            "accepts_real_ibkr_runtime_input=false sandbox_execution_allowed=false "
            "ibkr_api_request_allowed=false action_allowed=false"
        )
        print(f"sandbox_input_contract_csv={csv_path}")
        print(f"report={md_path}")
        print(
            "NOTICE: IBKR read-only qualification sandbox input contract only. "
            "No real TWS input / no real IBKR runtime input / no TWS connection / no IBKR connection / "
            "no real contract qualification / no reqMktData / no reqHistoricalData / "
            "no order / no cancel / no rebalance / no auto trade."
        )
        return 0

    if args.ibkr_readonly_qualification_sandbox_design is not None:
        from pathlib import Path

        from src.ibkr_readonly_qualification_sandbox_design import (
            build_ibkr_readonly_qualification_sandbox_design_rows,
            write_ibkr_readonly_qualification_sandbox_design_csv,
            write_ibkr_readonly_qualification_sandbox_design_report,
        )

        input_source = (
            args.ibkr_readonly_qualification_sandbox_design
            if args.ibkr_readonly_qualification_sandbox_design
            else "data/market_data_provider_config.yaml"
        )

        rows = build_ibkr_readonly_qualification_sandbox_design_rows(input_source)

        csv_path = Path(
            monitor.config["runtime"].get(
                "ibkr_readonly_qualification_sandbox_design_csv",
                "ibkr_readonly_qualification_sandbox_design.csv",
            )
        )
        md_path = Path(
            monitor.config["runtime"].get(
                "ibkr_readonly_qualification_sandbox_design_report",
                "reports/ibkr_readonly_qualification_sandbox_design_report.md",
            )
        )
        csv_path.parent.mkdir(parents=True, exist_ok=True)
        md_path.parent.mkdir(parents=True, exist_ok=True)

        write_ibkr_readonly_qualification_sandbox_design_csv(csv_path, rows)
        write_ibkr_readonly_qualification_sandbox_design_report(md_path, rows, input_source)

        statuses = sorted({r.sandbox_design_status for r in rows})
        status_text = ",".join(statuses) if statuses else "none"
        print(
            "[IBKR_READONLY_QUALIFICATION_SANDBOX_DESIGN] "
            f"rows={len(rows)} statuses={status_text} "
            "sandbox_execution_allowed=false real_ibkr_connection_allowed=false "
            "tws_connection_allowed=false ibkr_api_request_allowed=false action_allowed=false"
        )
        print(f"sandbox_design_csv={csv_path}")
        print(f"report={md_path}")
        print(
            "NOTICE: IBKR read-only qualification sandbox design only. "
            "No TWS connection / no IBKR connection / no real contract qualification / "
            "no reqMktData / no reqHistoricalData / no order / no cancel / no rebalance / no auto trade."
        )
        return 0

    if args.ibkr_readonly_qualification_phase12_closure_report is not None:
        from pathlib import Path

        from src.ibkr_readonly_qualification_phase12_closure_report import (
            build_ibkr_readonly_qualification_phase12_closure_report_rows,
            write_ibkr_readonly_qualification_phase12_closure_report_csv,
            write_ibkr_readonly_qualification_phase12_closure_report_report,
        )

        input_source = (
            args.ibkr_readonly_qualification_phase12_closure_report
            if args.ibkr_readonly_qualification_phase12_closure_report
            else "data/market_data_provider_config.yaml"
        )

        rows = build_ibkr_readonly_qualification_phase12_closure_report_rows(input_source)

        csv_path = Path(
            monitor.config["runtime"].get(
                "ibkr_readonly_qualification_phase12_closure_report_csv",
                "ibkr_readonly_qualification_phase12_closure_report.csv",
            )
        )
        md_path = Path(
            monitor.config["runtime"].get(
                "ibkr_readonly_qualification_phase12_closure_report",
                "reports/ibkr_readonly_qualification_phase12_closure_report.md",
            )
        )
        csv_path.parent.mkdir(parents=True, exist_ok=True)
        md_path.parent.mkdir(parents=True, exist_ok=True)

        write_ibkr_readonly_qualification_phase12_closure_report_csv(csv_path, rows)
        write_ibkr_readonly_qualification_phase12_closure_report_report(md_path, rows, input_source)

        statuses = sorted({r.phase12_closure_status for r in rows})
        status_text = ",".join(statuses) if statuses else "none"
        print(
            "[IBKR_READONLY_QUALIFICATION_PHASE12_CLOSURE_REPORT] "
            f"rows={len(rows)} statuses={status_text} "
            "final_authorization_status=BLOCKED final_authorization_allowed=false "
            "effective_approval_gate_status=CLOSED approval_effective=false "
            "qualification_allowed=false tws_connection_allowed=false "
            "api_request_allowed=false action_allowed=false"
        )
        print(f"phase12_closure_report_csv={csv_path}")
        print(f"report={md_path}")
        print(
            "NOTICE: IBKR read-only qualification Phase 12 closure report only. "
            "Phase 12 is complete but final authorization remains BLOCKED. "
            "No TWS connection / no IBKR connection / no real contract qualification / "
            "no reqMktData / no reqHistoricalData / no order / no cancel / no rebalance / no auto trade."
        )
        return 0

    if args.ibkr_readonly_qualification_final_authorization_packet is not None:
        from pathlib import Path

        from src.ibkr_readonly_qualification_final_authorization_packet import (
            build_ibkr_readonly_qualification_final_authorization_packet_rows,
            write_ibkr_readonly_qualification_final_authorization_packet_csv,
            write_ibkr_readonly_qualification_final_authorization_packet_report,
        )

        input_source = (
            args.ibkr_readonly_qualification_final_authorization_packet
            if args.ibkr_readonly_qualification_final_authorization_packet
            else "data/market_data_provider_config.yaml"
        )

        rows = build_ibkr_readonly_qualification_final_authorization_packet_rows(input_source)

        csv_path = Path(
            monitor.config["runtime"].get(
                "ibkr_readonly_qualification_final_authorization_packet_csv",
                "ibkr_readonly_qualification_final_authorization_packet.csv",
            )
        )
        md_path = Path(
            monitor.config["runtime"].get(
                "ibkr_readonly_qualification_final_authorization_packet_report",
                "reports/ibkr_readonly_qualification_final_authorization_packet_report.md",
            )
        )
        csv_path.parent.mkdir(parents=True, exist_ok=True)
        md_path.parent.mkdir(parents=True, exist_ok=True)

        write_ibkr_readonly_qualification_final_authorization_packet_csv(csv_path, rows)
        write_ibkr_readonly_qualification_final_authorization_packet_report(md_path, rows, input_source)

        statuses = sorted({r.final_authorization_status for r in rows})
        status_text = ",".join(statuses) if statuses else "none"
        print(
            "[IBKR_READONLY_QUALIFICATION_FINAL_AUTHORIZATION_PACKET] "
            f"rows={len(rows)} statuses={status_text} "
            "final_authorization_allowed=false effective_approval_gate_status=CLOSED "
            "approval_effective=false qualification_allowed=false tws_connection_allowed=false "
            "api_request_allowed=false action_allowed=false"
        )
        print(f"final_authorization_packet_csv={csv_path}")
        print(f"report={md_path}")
        print(
            "NOTICE: IBKR read-only qualification final authorization packet only. "
            "Final authorization remains BLOCKED. "
            "No TWS connection / no IBKR connection / no real contract qualification / "
            "no reqMktData / no reqHistoricalData / no order / no cancel / no rebalance / no auto trade."
        )
        return 0

    if args.ibkr_readonly_qualification_effective_approval_gate is not None:
        from pathlib import Path

        from src.ibkr_readonly_qualification_effective_approval_gate import (
            build_ibkr_readonly_qualification_effective_approval_gate_rows,
            write_ibkr_readonly_qualification_effective_approval_gate_csv,
            write_ibkr_readonly_qualification_effective_approval_gate_report,
        )

        input_source = (
            args.ibkr_readonly_qualification_effective_approval_gate
            if args.ibkr_readonly_qualification_effective_approval_gate
            else "data/market_data_provider_config.yaml"
        )

        rows = build_ibkr_readonly_qualification_effective_approval_gate_rows(input_source)

        csv_path = Path(
            monitor.config["runtime"].get(
                "ibkr_readonly_qualification_effective_approval_gate_csv",
                "ibkr_readonly_qualification_effective_approval_gate.csv",
            )
        )
        md_path = Path(
            monitor.config["runtime"].get(
                "ibkr_readonly_qualification_effective_approval_gate_report",
                "reports/ibkr_readonly_qualification_effective_approval_gate_report.md",
            )
        )
        csv_path.parent.mkdir(parents=True, exist_ok=True)
        md_path.parent.mkdir(parents=True, exist_ok=True)

        write_ibkr_readonly_qualification_effective_approval_gate_csv(csv_path, rows)
        write_ibkr_readonly_qualification_effective_approval_gate_report(md_path, rows, input_source)

        gate_statuses = sorted({r.effective_approval_gate_status for r in rows})
        gate_text = ",".join(gate_statuses) if gate_statuses else "none"
        print(
            "[IBKR_READONLY_QUALIFICATION_EFFECTIVE_APPROVAL_GATE] "
            f"rows={len(rows)} gate_statuses={gate_text} "
            "approval_effective=false effective_approval_allowed=false "
            "candidate_final_gate_status=CLOSED candidate_safety_status=BLOCKED "
            "qualification_allowed=false tws_connection_allowed=false "
            "api_request_allowed=false action_allowed=false"
        )
        print(f"effective_approval_gate_csv={csv_path}")
        print(f"report={md_path}")
        print(
            "NOTICE: IBKR read-only qualification effective approval gate only. "
            "Gate remains CLOSED and approval_effective=false. "
            "No TWS connection / no IBKR connection / no real contract qualification / "
            "no reqMktData / no reqHistoricalData / no order / no cancel / no rebalance / no auto trade."
        )
        return 0

    if args.ibkr_readonly_qualification_operator_approval_stub is not None:
        from pathlib import Path

        from src.ibkr_readonly_qualification_operator_approval_stub import (
            build_ibkr_readonly_qualification_operator_approval_stub_rows,
            write_ibkr_readonly_qualification_operator_approval_stub_csv,
            write_ibkr_readonly_qualification_operator_approval_stub_report,
        )

        input_source = (
            args.ibkr_readonly_qualification_operator_approval_stub
            if args.ibkr_readonly_qualification_operator_approval_stub
            else "data/market_data_provider_config.yaml"
        )

        rows = build_ibkr_readonly_qualification_operator_approval_stub_rows(input_source)

        csv_path = Path(
            monitor.config["runtime"].get(
                "ibkr_readonly_qualification_operator_approval_stub_csv",
                "ibkr_readonly_qualification_operator_approval_stub.csv",
            )
        )
        md_path = Path(
            monitor.config["runtime"].get(
                "ibkr_readonly_qualification_operator_approval_stub_report",
                "reports/ibkr_readonly_qualification_operator_approval_stub_report.md",
            )
        )
        csv_path.parent.mkdir(parents=True, exist_ok=True)
        md_path.parent.mkdir(parents=True, exist_ok=True)

        write_ibkr_readonly_qualification_operator_approval_stub_csv(csv_path, rows)
        write_ibkr_readonly_qualification_operator_approval_stub_report(md_path, rows, input_source)

        statuses = sorted({r.operator_approval_status for r in rows})
        status_text = ",".join(statuses) if statuses else "none"
        print(
            "[IBKR_READONLY_QUALIFICATION_OPERATOR_APPROVAL_STUB] "
            f"rows={len(rows)} statuses={status_text} "
            "approval_effective=false candidate_final_gate_status=CLOSED candidate_safety_status=BLOCKED "
            "qualification_allowed=false tws_connection_allowed=false "
            "api_request_allowed=false action_allowed=false"
        )
        print(f"operator_approval_stub_csv={csv_path}")
        print(f"report={md_path}")
        print(
            "NOTICE: IBKR read-only qualification operator approval stub only. "
            "Operator approval remains PENDING and approval_effective=false. "
            "No TWS connection / no IBKR connection / no real contract qualification / "
            "no reqMktData / no reqHistoricalData / no order / no cancel / no rebalance / no auto trade."
        )
        return 0

    if args.ibkr_readonly_qualification_operator_decision_ledger is not None:
        from pathlib import Path

        from src.ibkr_readonly_qualification_operator_decision_ledger import (
            build_ibkr_readonly_qualification_operator_decision_ledger_rows,
            write_ibkr_readonly_qualification_operator_decision_ledger_csv,
            write_ibkr_readonly_qualification_operator_decision_ledger_report,
        )

        input_path = (
            args.ibkr_readonly_qualification_operator_decision_ledger
            if args.ibkr_readonly_qualification_operator_decision_ledger
            else "data/market_data_provider_config.yaml"
        )

        rows = build_ibkr_readonly_qualification_operator_decision_ledger_rows(input_path)

        csv_path = Path(
            monitor.config["runtime"].get(
                "ibkr_readonly_qualification_operator_decision_ledger_csv",
                "ibkr_readonly_qualification_operator_decision_ledger.csv",
            )
        )
        md_path = Path(
            monitor.config["runtime"].get(
                "ibkr_readonly_qualification_operator_decision_ledger_report",
                "reports/ibkr_readonly_qualification_operator_decision_ledger_report.md",
            )
        )
        csv_path.parent.mkdir(parents=True, exist_ok=True)
        md_path.parent.mkdir(parents=True, exist_ok=True)

        write_ibkr_readonly_qualification_operator_decision_ledger_csv(csv_path, rows)
        write_ibkr_readonly_qualification_operator_decision_ledger_report(md_path, rows, input_path)

        statuses = sorted({r.operator_decision_status for r in rows})
        status_text = ",".join(statuses) if statuses else "none"
        print(
            "[IBKR_READONLY_QUALIFICATION_OPERATOR_DECISION_LEDGER] "
            f"rows={len(rows)} statuses={status_text} "
            "candidate_final_gate_status=CLOSED candidate_safety_status=BLOCKED "
            "qualification_allowed=false tws_connection_allowed=false "
            "api_request_allowed=false action_allowed=false"
        )
        print(f"operator_decision_ledger_csv={csv_path}")
        print(f"report={md_path}")
        print(
            "NOTICE: IBKR read-only qualification operator decision ledger only. "
            "Operator decision remains PENDING and candidate safety remains BLOCKED. "
            "No TWS connection / no IBKR connection / no real contract qualification / "
            "no reqMktData / no reqHistoricalData / no order / no cancel / no rebalance / no auto trade."
        )
        return 0

    if args.ibkr_readonly_qualification_candidate_safety_summary is not None:
        from pathlib import Path
        from src.ibkr_contract_mapping_plan import (
            build_ibkr_contract_mapping_plan_rows,
            load_ibkr_contract_mapping_config,
        )
        from src.ibkr_contract_qualification_dry_run import build_ibkr_contract_qualification_dry_run_rows
        from src.ibkr_contract_qualification_execution_guard import build_ibkr_contract_qualification_execution_guard_rows
        from src.ibkr_readonly_qualification_safety_summary import IBKRReadOnlyQualificationSafetySummaryRow
        from src.ibkr_readonly_qualification_candidate_resolver import build_ibkr_readonly_qualification_candidate_resolver_rows
        from src.ibkr_readonly_qualification_candidate_review_pack import build_ibkr_readonly_qualification_candidate_review_pack_rows
        from src.ibkr_readonly_qualification_candidate_final_gate import build_ibkr_readonly_qualification_candidate_final_gate_rows
        from src.ibkr_readonly_qualification_candidate_safety_summary import (
            build_ibkr_readonly_qualification_candidate_safety_summary_rows,
            write_ibkr_readonly_qualification_candidate_safety_summary_csv,
            write_ibkr_readonly_qualification_candidate_safety_summary_report,
        )

        input_path = args.ibkr_readonly_qualification_candidate_safety_summary if args.ibkr_readonly_qualification_candidate_safety_summary else "data/market_data_provider_config.yaml"

        mapping_config = load_ibkr_contract_mapping_config("data/market_data_provider_config.yaml")
        mapping_rows = build_ibkr_contract_mapping_plan_rows(mapping_config, monitor.config["runtime"]["timezone"])
        dry_rows = build_ibkr_contract_qualification_dry_run_rows(mapping_rows, monitor.config["runtime"]["timezone"])
        guard_rows = build_ibkr_contract_qualification_execution_guard_rows(dry_rows, monitor.config["runtime"]["timezone"])

        safety_rows = [
            IBKRReadOnlyQualificationSafetySummaryRow(
                section_id="FINAL",
                section_name="Final IBKR read-only qualification full safety summary",
                source_layer="Phase 10G-10M + Phase 11A-11D",
                input_row_count="0",
                blocked_or_closed_count="0",
                pass_or_ready_count="0",
                summary_status="BLOCKED",
                overall_status="BLOCKED",
                apply_allowed="false",
                qualification_allowed="false",
                tws_connection_allowed="false",
                contract_qualification_allowed="false",
                market_data_request_allowed="false",
                historical_data_request_allowed="false",
                api_request_allowed="false",
                action_allowed="false",
                blocking_summary="overall_status_blocked_until_explicit_future_phase_design_and_manual_operator_review",
                warning_flags="overall_blocked_by_default",
                notes="synthetic safety summary row for candidate safety summary",
                timestamp_jst="",
                timestamp_et="",
            )
        ]

        resolver_rows = build_ibkr_readonly_qualification_candidate_resolver_rows(
            mapping_rows,
            dry_rows,
            guard_rows,
            safety_rows,
            monitor.config["runtime"]["timezone"],
        )
        review_rows = build_ibkr_readonly_qualification_candidate_review_pack_rows(
            resolver_rows,
            monitor.config["runtime"]["timezone"],
        )
        gate_rows = build_ibkr_readonly_qualification_candidate_final_gate_rows(
            resolver_rows,
            review_rows,
            monitor.config["runtime"]["timezone"],
        )
        rows = build_ibkr_readonly_qualification_candidate_safety_summary_rows(
            resolver_rows,
            review_rows,
            gate_rows,
            monitor.config["runtime"]["timezone"],
        )

        csv_path = Path(monitor.config["runtime"].get("ibkr_readonly_qualification_candidate_safety_summary_csv", "ibkr_readonly_qualification_candidate_safety_summary.csv"))
        md_path = Path(monitor.config["runtime"].get("ibkr_readonly_qualification_candidate_safety_summary_report", "reports/ibkr_readonly_qualification_candidate_safety_summary_report.md"))
        csv_path.parent.mkdir(parents=True, exist_ok=True)
        md_path.parent.mkdir(parents=True, exist_ok=True)

        write_ibkr_readonly_qualification_candidate_safety_summary_csv(csv_path, rows)
        write_ibkr_readonly_qualification_candidate_safety_summary_report(md_path, rows, input_path)

        statuses = sorted({r.candidate_safety_status for r in rows})
        status_text = chr(44).join(statuses) if statuses else "none"
        print(f"[IBKR_READONLY_QUALIFICATION_CANDIDATE_SAFETY_SUMMARY] rows={len(rows)} statuses={status_text} candidate_final_gate_status=CLOSED qualification_allowed=false tws_connection_allowed=false api_request_allowed=false action_allowed=false")
        print(f"candidate_safety_summary_csv={csv_path}")
        print(f"report={md_path}")
        print("NOTICE: IBKR read-only qualification candidate safety summary only. Candidate safety status remains BLOCKED and candidate final gate remains CLOSED. No TWS connection / no IBKR connection / no real contract qualification / no reqMktData / no reqHistoricalData / no order / no cancel / no rebalance / no auto trade.")
        return 0

    if args.ibkr_readonly_qualification_candidate_final_gate is not None:
        from pathlib import Path
        from src.ibkr_contract_mapping_plan import (
            build_ibkr_contract_mapping_plan_rows,
            load_ibkr_contract_mapping_config,
        )
        from src.ibkr_contract_qualification_dry_run import build_ibkr_contract_qualification_dry_run_rows
        from src.ibkr_contract_qualification_execution_guard import build_ibkr_contract_qualification_execution_guard_rows
        from src.ibkr_readonly_qualification_safety_summary import IBKRReadOnlyQualificationSafetySummaryRow
        from src.ibkr_readonly_qualification_candidate_resolver import build_ibkr_readonly_qualification_candidate_resolver_rows
        from src.ibkr_readonly_qualification_candidate_review_pack import build_ibkr_readonly_qualification_candidate_review_pack_rows
        from src.ibkr_readonly_qualification_candidate_final_gate import (
            build_ibkr_readonly_qualification_candidate_final_gate_rows,
            write_ibkr_readonly_qualification_candidate_final_gate_csv,
            write_ibkr_readonly_qualification_candidate_final_gate_report,
        )

        input_path = args.ibkr_readonly_qualification_candidate_final_gate if args.ibkr_readonly_qualification_candidate_final_gate else "data/market_data_provider_config.yaml"

        mapping_config = load_ibkr_contract_mapping_config("data/market_data_provider_config.yaml")
        mapping_rows = build_ibkr_contract_mapping_plan_rows(mapping_config, monitor.config["runtime"]["timezone"])
        dry_rows = build_ibkr_contract_qualification_dry_run_rows(mapping_rows, monitor.config["runtime"]["timezone"])
        guard_rows = build_ibkr_contract_qualification_execution_guard_rows(dry_rows, monitor.config["runtime"]["timezone"])

        safety_rows = [
            IBKRReadOnlyQualificationSafetySummaryRow(
                section_id="FINAL",
                section_name="Final IBKR read-only qualification full safety summary",
                source_layer="Phase 10G-10M + Phase 11A-11D",
                input_row_count="0",
                blocked_or_closed_count="0",
                pass_or_ready_count="0",
                summary_status="BLOCKED",
                overall_status="BLOCKED",
                apply_allowed="false",
                qualification_allowed="false",
                tws_connection_allowed="false",
                contract_qualification_allowed="false",
                market_data_request_allowed="false",
                historical_data_request_allowed="false",
                api_request_allowed="false",
                action_allowed="false",
                blocking_summary="overall_status_blocked_until_explicit_future_phase_design_and_manual_operator_review",
                warning_flags="overall_blocked_by_default",
                notes="synthetic safety summary row for candidate final gate",
                timestamp_jst="",
                timestamp_et="",
            )
        ]

        resolver_rows = build_ibkr_readonly_qualification_candidate_resolver_rows(
            mapping_rows,
            dry_rows,
            guard_rows,
            safety_rows,
            monitor.config["runtime"]["timezone"],
        )
        review_rows = build_ibkr_readonly_qualification_candidate_review_pack_rows(
            resolver_rows,
            monitor.config["runtime"]["timezone"],
        )
        rows = build_ibkr_readonly_qualification_candidate_final_gate_rows(
            resolver_rows,
            review_rows,
            monitor.config["runtime"]["timezone"],
        )

        csv_path = Path(monitor.config["runtime"].get("ibkr_readonly_qualification_candidate_final_gate_csv", "ibkr_readonly_qualification_candidate_final_gate.csv"))
        md_path = Path(monitor.config["runtime"].get("ibkr_readonly_qualification_candidate_final_gate_report", "reports/ibkr_readonly_qualification_candidate_final_gate_report.md"))
        csv_path.parent.mkdir(parents=True, exist_ok=True)
        md_path.parent.mkdir(parents=True, exist_ok=True)

        write_ibkr_readonly_qualification_candidate_final_gate_csv(csv_path, rows)
        write_ibkr_readonly_qualification_candidate_final_gate_report(md_path, rows, input_path)

        statuses = sorted({r.candidate_final_gate_status for r in rows})
        status_text = chr(44).join(statuses) if statuses else "none"
        print(f"[IBKR_READONLY_QUALIFICATION_CANDIDATE_FINAL_GATE] rows={len(rows)} statuses={status_text} qualification_allowed=false tws_connection_allowed=false api_request_allowed=false action_allowed=false")
        print(f"candidate_final_gate_csv={csv_path}")
        print(f"report={md_path}")
        print("NOTICE: IBKR read-only qualification candidate final gate only. Candidate final gate remains CLOSED. No TWS connection / no IBKR connection / no real contract qualification / no reqMktData / no reqHistoricalData / no order / no cancel / no rebalance / no auto trade.")
        return 0

    if args.ibkr_readonly_qualification_candidate_review_pack is not None:
        from pathlib import Path
        from src.ibkr_contract_mapping_plan import (
            build_ibkr_contract_mapping_plan_rows,
            load_ibkr_contract_mapping_config,
        )
        from src.ibkr_contract_qualification_dry_run import build_ibkr_contract_qualification_dry_run_rows
        from src.ibkr_contract_qualification_execution_guard import build_ibkr_contract_qualification_execution_guard_rows
        from src.ibkr_readonly_qualification_safety_summary import IBKRReadOnlyQualificationSafetySummaryRow
        from src.ibkr_readonly_qualification_candidate_resolver import build_ibkr_readonly_qualification_candidate_resolver_rows
        from src.ibkr_readonly_qualification_candidate_review_pack import (
            build_ibkr_readonly_qualification_candidate_review_pack_rows,
            write_ibkr_readonly_qualification_candidate_review_pack_csv,
            write_ibkr_readonly_qualification_candidate_review_pack_report,
        )

        input_path = args.ibkr_readonly_qualification_candidate_review_pack if args.ibkr_readonly_qualification_candidate_review_pack else "data/market_data_provider_config.yaml"

        mapping_config = load_ibkr_contract_mapping_config("data/market_data_provider_config.yaml")
        mapping_rows = build_ibkr_contract_mapping_plan_rows(mapping_config, monitor.config["runtime"]["timezone"])
        dry_rows = build_ibkr_contract_qualification_dry_run_rows(mapping_rows, monitor.config["runtime"]["timezone"])
        guard_rows = build_ibkr_contract_qualification_execution_guard_rows(dry_rows, monitor.config["runtime"]["timezone"])

        safety_rows = [
            IBKRReadOnlyQualificationSafetySummaryRow(
                section_id="FINAL",
                section_name="Final IBKR read-only qualification full safety summary",
                source_layer="Phase 10G-10M + Phase 11A-11D",
                input_row_count="0",
                blocked_or_closed_count="0",
                pass_or_ready_count="0",
                summary_status="BLOCKED",
                overall_status="BLOCKED",
                apply_allowed="false",
                qualification_allowed="false",
                tws_connection_allowed="false",
                contract_qualification_allowed="false",
                market_data_request_allowed="false",
                historical_data_request_allowed="false",
                api_request_allowed="false",
                action_allowed="false",
                blocking_summary="overall_status_blocked_until_explicit_future_phase_design_and_manual_operator_review",
                warning_flags="overall_blocked_by_default",
                notes="synthetic safety summary row for candidate review pack",
                timestamp_jst="",
                timestamp_et="",
            )
        ]

        resolver_rows = build_ibkr_readonly_qualification_candidate_resolver_rows(
            mapping_rows,
            dry_rows,
            guard_rows,
            safety_rows,
            monitor.config["runtime"]["timezone"],
        )
        rows = build_ibkr_readonly_qualification_candidate_review_pack_rows(
            resolver_rows,
            monitor.config["runtime"]["timezone"],
        )

        csv_path = Path(monitor.config["runtime"].get("ibkr_readonly_qualification_candidate_review_pack_csv", "ibkr_readonly_qualification_candidate_review_pack.csv"))
        md_path = Path(monitor.config["runtime"].get("ibkr_readonly_qualification_candidate_review_pack_report", "reports/ibkr_readonly_qualification_candidate_review_pack_report.md"))
        csv_path.parent.mkdir(parents=True, exist_ok=True)
        md_path.parent.mkdir(parents=True, exist_ok=True)

        write_ibkr_readonly_qualification_candidate_review_pack_csv(csv_path, rows)
        write_ibkr_readonly_qualification_candidate_review_pack_report(md_path, rows, input_path)

        statuses = sorted({r.review_pack_status for r in rows})
        status_text = chr(44).join(statuses) if statuses else "none"
        print(f"[IBKR_READONLY_QUALIFICATION_CANDIDATE_REVIEW_PACK] rows={len(rows)} statuses={status_text} qualification_allowed=false tws_connection_allowed=false api_request_allowed=false action_allowed=false")
        print(f"candidate_review_pack_csv={csv_path}")
        print(f"report={md_path}")
        print("NOTICE: IBKR read-only qualification candidate review pack only. Operator review required. No TWS connection / no IBKR connection / no real contract qualification / no reqMktData / no reqHistoricalData / no order / no cancel / no rebalance / no auto trade.")
        return 0

    if args.ibkr_readonly_qualification_candidate_resolver is not None:
        from pathlib import Path
        from src.ibkr_contract_mapping_plan import (
            build_ibkr_contract_mapping_plan_rows,
            load_ibkr_contract_mapping_config,
        )
        from src.ibkr_contract_qualification_dry_run import build_ibkr_contract_qualification_dry_run_rows
        from src.ibkr_contract_qualification_execution_guard import build_ibkr_contract_qualification_execution_guard_rows
        from src.ibkr_readonly_qualification_safety_summary import IBKRReadOnlyQualificationSafetySummaryRow
        from src.ibkr_readonly_qualification_candidate_resolver import (
            build_ibkr_readonly_qualification_candidate_resolver_rows,
            write_ibkr_readonly_qualification_candidate_resolver_csv,
            write_ibkr_readonly_qualification_candidate_resolver_report,
        )

        input_path = args.ibkr_readonly_qualification_candidate_resolver if args.ibkr_readonly_qualification_candidate_resolver else "data/market_data_provider_config.yaml"

        mapping_config = load_ibkr_contract_mapping_config("data/market_data_provider_config.yaml")
        mapping_rows = build_ibkr_contract_mapping_plan_rows(mapping_config, monitor.config["runtime"]["timezone"])
        dry_rows = build_ibkr_contract_qualification_dry_run_rows(mapping_rows, monitor.config["runtime"]["timezone"])
        guard_rows = build_ibkr_contract_qualification_execution_guard_rows(dry_rows, monitor.config["runtime"]["timezone"])

        safety_rows = [
            IBKRReadOnlyQualificationSafetySummaryRow(
                section_id="FINAL",
                section_name="Final IBKR read-only qualification full safety summary",
                source_layer="Phase 10G-10M + Phase 11A-11D",
                input_row_count="0",
                blocked_or_closed_count="0",
                pass_or_ready_count="0",
                summary_status="BLOCKED",
                overall_status="BLOCKED",
                apply_allowed="false",
                qualification_allowed="false",
                tws_connection_allowed="false",
                contract_qualification_allowed="false",
                market_data_request_allowed="false",
                historical_data_request_allowed="false",
                api_request_allowed="false",
                action_allowed="false",
                blocking_summary="overall_status_blocked_until_explicit_future_phase_design_and_manual_operator_review",
                warning_flags="overall_blocked_by_default",
                notes="synthetic safety summary row for candidate resolver",
                timestamp_jst="",
                timestamp_et="",
            )
        ]

        rows = build_ibkr_readonly_qualification_candidate_resolver_rows(
            mapping_rows,
            dry_rows,
            guard_rows,
            safety_rows,
            monitor.config["runtime"]["timezone"],
        )

        csv_path = Path(monitor.config["runtime"].get("ibkr_readonly_qualification_candidate_resolver_csv", "ibkr_readonly_qualification_candidate_resolver.csv"))
        md_path = Path(monitor.config["runtime"].get("ibkr_readonly_qualification_candidate_resolver_report", "reports/ibkr_readonly_qualification_candidate_resolver_report.md"))
        csv_path.parent.mkdir(parents=True, exist_ok=True)
        md_path.parent.mkdir(parents=True, exist_ok=True)

        write_ibkr_readonly_qualification_candidate_resolver_csv(csv_path, rows)
        write_ibkr_readonly_qualification_candidate_resolver_report(md_path, rows, input_path)

        statuses = sorted({r.candidate_resolver_status for r in rows})
        status_text = chr(44).join(statuses) if statuses else "none"
        print(f"[IBKR_READONLY_QUALIFICATION_CANDIDATE_RESOLVER] rows={len(rows)} statuses={status_text} qualification_allowed=false tws_connection_allowed=false api_request_allowed=false action_allowed=false")
        print(f"candidate_resolver_csv={csv_path}")
        print(f"report={md_path}")
        print("NOTICE: IBKR read-only qualification candidate resolver only. Overall status remains BLOCKED. No TWS connection / no IBKR connection / no real contract qualification / no reqMktData / no reqHistoricalData / no order / no cancel / no rebalance / no auto trade.")
        return 0

    if args.ibkr_readonly_qualification_safety_summary is not None:
        from pathlib import Path
        from src.ibkr_live_provider_adapter_check import (
            build_ibkr_live_provider_adapter_check_rows,
            load_ibkr_live_provider_adapter_config,
        )
        from src.ibkr_contract_mapping_plan import (
            build_ibkr_contract_mapping_plan_rows,
            load_ibkr_contract_mapping_config,
        )
        from src.ibkr_contract_qualification_dry_run import build_ibkr_contract_qualification_dry_run_rows
        from src.ibkr_contract_qualification_execution_guard import build_ibkr_contract_qualification_execution_guard_rows
        from src.ibkr_readonly_qualification_precheck import build_ibkr_readonly_qualification_precheck_rows
        from src.ibkr_readonly_qualification_runbook import build_ibkr_readonly_qualification_runbook_rows
        from src.ibkr_readonly_qualification_go_no_go import build_ibkr_readonly_qualification_go_no_go_rows
        from src.ibkr_readonly_qualification_config_template import (
            build_ibkr_readonly_qualification_config_template_rows,
            default_ibkr_readonly_qualification_template,
        )
        from src.ibkr_readonly_qualification_config_audit import build_ibkr_readonly_qualification_config_audit_rows
        from src.ibkr_readonly_qualification_config_apply_plan import build_ibkr_readonly_qualification_config_apply_plan_rows
        from src.ibkr_readonly_qualification_config_final_gate import build_ibkr_readonly_qualification_config_final_gate_rows
        from src.ibkr_readonly_qualification_safety_summary import (
            build_ibkr_readonly_qualification_safety_summary_rows,
            write_ibkr_readonly_qualification_safety_summary_csv,
            write_ibkr_readonly_qualification_safety_summary_report,
        )

        input_path = args.ibkr_readonly_qualification_safety_summary if args.ibkr_readonly_qualification_safety_summary else "config.yaml"

        provider_config = load_ibkr_live_provider_adapter_config("data/market_data_provider_config.yaml")
        mapping_config = load_ibkr_contract_mapping_config("data/market_data_provider_config.yaml")

        adapter_rows = build_ibkr_live_provider_adapter_check_rows(provider_config, monitor.config["runtime"]["timezone"])
        mapping_rows = build_ibkr_contract_mapping_plan_rows(mapping_config, monitor.config["runtime"]["timezone"])
        dry_run_rows = build_ibkr_contract_qualification_dry_run_rows(mapping_rows, monitor.config["runtime"]["timezone"])
        guard_rows = build_ibkr_contract_qualification_execution_guard_rows(dry_run_rows, monitor.config["runtime"]["timezone"])
        precheck_rows = build_ibkr_readonly_qualification_precheck_rows({}, monitor.config["runtime"]["timezone"])
        runbook_rows = build_ibkr_readonly_qualification_runbook_rows(precheck_rows, monitor.config["runtime"]["timezone"])
        go_no_go_rows = build_ibkr_readonly_qualification_go_no_go_rows(
            adapter_rows,
            mapping_rows,
            dry_run_rows,
            guard_rows,
            precheck_rows,
            runbook_rows,
            monitor.config["runtime"]["timezone"],
        )

        template_rows = build_ibkr_readonly_qualification_config_template_rows(monitor.config["runtime"]["timezone"])
        audit_config = default_ibkr_readonly_qualification_template()
        audit_rows = build_ibkr_readonly_qualification_config_audit_rows(audit_config, monitor.config["runtime"]["timezone"])
        apply_rows = build_ibkr_readonly_qualification_config_apply_plan_rows(audit_rows, monitor.config["runtime"]["timezone"])
        gate_rows = build_ibkr_readonly_qualification_config_final_gate_rows(
            template_rows,
            audit_rows,
            apply_rows,
            monitor.config["runtime"]["timezone"],
        )

        rows = build_ibkr_readonly_qualification_safety_summary_rows(
            go_no_go_rows,
            gate_rows,
            monitor.config["runtime"]["timezone"],
        )

        csv_path = Path(monitor.config["runtime"].get("ibkr_readonly_qualification_safety_summary_csv", "ibkr_readonly_qualification_safety_summary.csv"))
        md_path = Path(monitor.config["runtime"].get("ibkr_readonly_qualification_safety_summary_report", "reports/ibkr_readonly_qualification_safety_summary_report.md"))
        csv_path.parent.mkdir(parents=True, exist_ok=True)
        md_path.parent.mkdir(parents=True, exist_ok=True)

        write_ibkr_readonly_qualification_safety_summary_csv(csv_path, rows)
        write_ibkr_readonly_qualification_safety_summary_report(md_path, rows, input_path)

        statuses = sorted({r.overall_status for r in rows})
        status_text = chr(44).join(statuses) if statuses else "none"
        print(f"[IBKR_READONLY_QUALIFICATION_SAFETY_SUMMARY] rows={len(rows)} statuses={status_text} apply_allowed=false qualification_allowed=false tws_connection_allowed=false api_request_allowed=false action_allowed=false")
        print(f"safety_summary_csv={csv_path}")
        print(f"report={md_path}")
        print("NOTICE: IBKR read-only qualification full safety summary only. Overall status remains BLOCKED. No config mutation / no TWS connection / no IBKR connection / no real contract qualification / no reqMktData / no reqHistoricalData / no order / no cancel / no rebalance / no auto trade.")
        return 0

    if args.ibkr_readonly_qualification_config_final_gate is not None:
        from pathlib import Path
        from src.ibkr_readonly_qualification_config_template import (
            build_ibkr_readonly_qualification_config_template_rows,
            default_ibkr_readonly_qualification_template,
        )
        from src.ibkr_readonly_qualification_config_audit import build_ibkr_readonly_qualification_config_audit_rows
        from src.ibkr_readonly_qualification_config_apply_plan import build_ibkr_readonly_qualification_config_apply_plan_rows
        from src.ibkr_readonly_qualification_config_final_gate import (
            build_ibkr_readonly_qualification_config_final_gate_rows,
            write_ibkr_readonly_qualification_config_final_gate_csv,
            write_ibkr_readonly_qualification_config_final_gate_report,
        )

        input_path = args.ibkr_readonly_qualification_config_final_gate if args.ibkr_readonly_qualification_config_final_gate else monitor.config["runtime"].get(
            "ibkr_readonly_qualification_config_template_yaml",
            "data/ibkr_readonly_qualification_config_template.yaml",
        )

        template_rows = build_ibkr_readonly_qualification_config_template_rows(monitor.config["runtime"]["timezone"])
        audit_config = default_ibkr_readonly_qualification_template()
        audit_rows = build_ibkr_readonly_qualification_config_audit_rows(audit_config, monitor.config["runtime"]["timezone"])
        apply_rows = build_ibkr_readonly_qualification_config_apply_plan_rows(audit_rows, monitor.config["runtime"]["timezone"])
        rows = build_ibkr_readonly_qualification_config_final_gate_rows(
            template_rows,
            audit_rows,
            apply_rows,
            monitor.config["runtime"]["timezone"],
        )

        csv_path = Path(monitor.config["runtime"].get("ibkr_readonly_qualification_config_final_gate_csv", "ibkr_readonly_qualification_config_final_gate.csv"))
        md_path = Path(monitor.config["runtime"].get("ibkr_readonly_qualification_config_final_gate_report", "reports/ibkr_readonly_qualification_config_final_gate_report.md"))
        csv_path.parent.mkdir(parents=True, exist_ok=True)
        md_path.parent.mkdir(parents=True, exist_ok=True)

        write_ibkr_readonly_qualification_config_final_gate_csv(csv_path, rows)
        write_ibkr_readonly_qualification_config_final_gate_report(md_path, rows, input_path)

        statuses = sorted({r.final_gate_status for r in rows})
        status_text = chr(44).join(statuses) if statuses else "none"
        print(f"[IBKR_READONLY_QUALIFICATION_CONFIG_FINAL_GATE] rows={len(rows)} statuses={status_text} apply_allowed=false qualification_allowed=false tws_connection_allowed=false api_request_allowed=false action_allowed=false")
        print(f"config_final_gate_csv={csv_path}")
        print(f"report={md_path}")
        print("NOTICE: IBKR read-only qualification config final gate only. Final gate remains CLOSED. No config mutation / no TWS connection / no IBKR connection / no real contract qualification / no reqMktData / no reqHistoricalData / no order / no cancel / no rebalance / no auto trade.")
        return 0

    if args.ibkr_readonly_qualification_config_apply_plan is not None:
        from pathlib import Path
        from src.ibkr_readonly_qualification_config_audit import (
            build_ibkr_readonly_qualification_config_audit_rows,
            load_ibkr_readonly_qualification_config_audit_config,
        )
        from src.ibkr_readonly_qualification_config_apply_plan import (
            build_ibkr_readonly_qualification_config_apply_plan_rows,
            write_ibkr_readonly_qualification_config_apply_plan_csv,
            write_ibkr_readonly_qualification_config_apply_plan_report,
        )

        input_path = args.ibkr_readonly_qualification_config_apply_plan if args.ibkr_readonly_qualification_config_apply_plan else monitor.config["runtime"].get(
            "ibkr_readonly_qualification_config_template_yaml",
            "data/ibkr_readonly_qualification_config_template.yaml",
        )
        audit_config = load_ibkr_readonly_qualification_config_audit_config(input_path)
        audit_rows = build_ibkr_readonly_qualification_config_audit_rows(audit_config, monitor.config["runtime"]["timezone"])
        rows = build_ibkr_readonly_qualification_config_apply_plan_rows(audit_rows, monitor.config["runtime"]["timezone"])

        csv_path = Path(monitor.config["runtime"].get("ibkr_readonly_qualification_config_apply_plan_csv", "ibkr_readonly_qualification_config_apply_plan.csv"))
        md_path = Path(monitor.config["runtime"].get("ibkr_readonly_qualification_config_apply_plan_report", "reports/ibkr_readonly_qualification_config_apply_plan_report.md"))
        csv_path.parent.mkdir(parents=True, exist_ok=True)
        md_path.parent.mkdir(parents=True, exist_ok=True)

        write_ibkr_readonly_qualification_config_apply_plan_csv(csv_path, rows)
        write_ibkr_readonly_qualification_config_apply_plan_report(md_path, rows, input_path)

        statuses = sorted({r.apply_plan_status for r in rows})
        status_text = chr(44).join(statuses) if statuses else "none"
        print(f"[IBKR_READONLY_QUALIFICATION_CONFIG_APPLY_PLAN] rows={len(rows)} statuses={status_text} apply_allowed=false qualification_allowed=false tws_connection_allowed=false api_request_allowed=false action_allowed=false")
        print(f"config_apply_plan_csv={csv_path}")
        print(f"report={md_path}")
        print("NOTICE: IBKR read-only qualification config apply plan only. No config mutation / no TWS connection / no IBKR connection / no real contract qualification / no reqMktData / no reqHistoricalData / no order / no cancel / no rebalance / no auto trade.")
        return 0

    if args.ibkr_readonly_qualification_config_audit is not None:
        from pathlib import Path
        from src.ibkr_readonly_qualification_config_audit import (
            build_ibkr_readonly_qualification_config_audit_rows,
            load_ibkr_readonly_qualification_config_audit_config,
            write_ibkr_readonly_qualification_config_audit_csv,
            write_ibkr_readonly_qualification_config_audit_report,
        )

        input_path = args.ibkr_readonly_qualification_config_audit if args.ibkr_readonly_qualification_config_audit else monitor.config["runtime"].get(
            "ibkr_readonly_qualification_config_template_yaml",
            "data/ibkr_readonly_qualification_config_template.yaml",
        )
        audit_config = load_ibkr_readonly_qualification_config_audit_config(input_path)
        rows = build_ibkr_readonly_qualification_config_audit_rows(audit_config, monitor.config["runtime"]["timezone"])

        csv_path = Path(monitor.config["runtime"].get("ibkr_readonly_qualification_config_audit_csv", "ibkr_readonly_qualification_config_audit.csv"))
        md_path = Path(monitor.config["runtime"].get("ibkr_readonly_qualification_config_audit_report", "reports/ibkr_readonly_qualification_config_audit_report.md"))
        csv_path.parent.mkdir(parents=True, exist_ok=True)
        md_path.parent.mkdir(parents=True, exist_ok=True)

        write_ibkr_readonly_qualification_config_audit_csv(csv_path, rows)
        write_ibkr_readonly_qualification_config_audit_report(md_path, rows, input_path)

        statuses = sorted({r.config_audit_status for r in rows})
        status_text = chr(44).join(statuses) if statuses else "none"
        print(f"[IBKR_READONLY_QUALIFICATION_CONFIG_AUDIT] rows={len(rows)} statuses={status_text} qualification_allowed=false tws_connection_allowed=false api_request_allowed=false action_allowed=false")
        print(f"config_audit_csv={csv_path}")
        print(f"report={md_path}")
        print("NOTICE: IBKR read-only qualification config audit only. No TWS connection / no IBKR connection / no real contract qualification / no reqMktData / no reqHistoricalData / no order / no cancel / no rebalance / no auto trade.")
        return 0

    if args.ibkr_readonly_qualification_config_template is not None:
        from pathlib import Path
        from src.ibkr_readonly_qualification_config_template import (
            build_ibkr_readonly_qualification_config_template_rows,
            write_ibkr_readonly_qualification_config_template_csv,
            write_ibkr_readonly_qualification_config_template_report,
            write_ibkr_readonly_qualification_template_yaml,
        )

        template_path = Path(
            monitor.config["runtime"].get(
                "ibkr_readonly_qualification_config_template_yaml",
                "data/ibkr_readonly_qualification_config_template.yaml",
            )
        )
        rows = build_ibkr_readonly_qualification_config_template_rows(monitor.config["runtime"]["timezone"])

        csv_path = Path(monitor.config["runtime"].get("ibkr_readonly_qualification_config_template_csv", "ibkr_readonly_qualification_config_template.csv"))
        md_path = Path(monitor.config["runtime"].get("ibkr_readonly_qualification_config_template_report", "reports/ibkr_readonly_qualification_config_template_report.md"))
        csv_path.parent.mkdir(parents=True, exist_ok=True)
        md_path.parent.mkdir(parents=True, exist_ok=True)
        template_path.parent.mkdir(parents=True, exist_ok=True)

        write_ibkr_readonly_qualification_config_template_csv(csv_path, rows)
        write_ibkr_readonly_qualification_config_template_report(md_path, rows, str(template_path))
        write_ibkr_readonly_qualification_template_yaml(template_path)

        statuses = sorted({r.template_status for r in rows})
        status_text = chr(44).join(statuses) if statuses else "none"
        print(f"[IBKR_READONLY_QUALIFICATION_CONFIG_TEMPLATE] rows={len(rows)} statuses={status_text} qualification_allowed=false tws_connection_allowed=false api_request_allowed=false action_allowed=false")
        print(f"config_template_csv={csv_path}")
        print(f"config_template_yaml={template_path}")
        print(f"report={md_path}")
        print("NOTICE: IBKR read-only qualification config template only. Template remains disabled by default. No TWS connection / no IBKR connection / no real contract qualification / no reqMktData / no reqHistoricalData / no order / no cancel / no rebalance / no auto trade.")
        return 0

    if args.ibkr_readonly_qualification_go_no_go is not None:
        from pathlib import Path
        from src.ibkr_live_provider_adapter_check import (
            build_ibkr_live_provider_adapter_check_rows,
            load_ibkr_live_provider_adapter_config,
        )
        from src.ibkr_contract_mapping_plan import (
            build_ibkr_contract_mapping_plan_rows,
            load_ibkr_contract_mapping_config,
        )
        from src.ibkr_contract_qualification_dry_run import build_ibkr_contract_qualification_dry_run_rows
        from src.ibkr_contract_qualification_execution_guard import build_ibkr_contract_qualification_execution_guard_rows
        from src.ibkr_readonly_qualification_precheck import build_ibkr_readonly_qualification_precheck_rows
        from src.ibkr_readonly_qualification_runbook import build_ibkr_readonly_qualification_runbook_rows
        from src.ibkr_readonly_qualification_go_no_go import (
            build_ibkr_readonly_qualification_go_no_go_rows,
            write_ibkr_readonly_qualification_go_no_go_csv,
            write_ibkr_readonly_qualification_go_no_go_report,
        )

        input_path = args.ibkr_readonly_qualification_go_no_go if args.ibkr_readonly_qualification_go_no_go else "config.yaml"
        provider_config = load_ibkr_live_provider_adapter_config("data/market_data_provider_config.yaml")
        mapping_config = load_ibkr_contract_mapping_config("data/market_data_provider_config.yaml")

        adapter_rows = build_ibkr_live_provider_adapter_check_rows(provider_config, monitor.config["runtime"]["timezone"])
        mapping_rows = build_ibkr_contract_mapping_plan_rows(mapping_config, monitor.config["runtime"]["timezone"])
        dry_run_rows = build_ibkr_contract_qualification_dry_run_rows(mapping_rows, monitor.config["runtime"]["timezone"])
        guard_rows = build_ibkr_contract_qualification_execution_guard_rows(dry_run_rows, monitor.config["runtime"]["timezone"])
        precheck_rows = build_ibkr_readonly_qualification_precheck_rows({}, monitor.config["runtime"]["timezone"])
        runbook_rows = build_ibkr_readonly_qualification_runbook_rows(precheck_rows, monitor.config["runtime"]["timezone"])
        rows = build_ibkr_readonly_qualification_go_no_go_rows(
            adapter_rows,
            mapping_rows,
            dry_run_rows,
            guard_rows,
            precheck_rows,
            runbook_rows,
            monitor.config["runtime"]["timezone"],
        )

        csv_path = Path(monitor.config["runtime"].get("ibkr_readonly_qualification_go_no_go_csv", "ibkr_readonly_qualification_go_no_go.csv"))
        md_path = Path(monitor.config["runtime"].get("ibkr_readonly_qualification_go_no_go_report", "reports/ibkr_readonly_qualification_go_no_go_report.md"))
        csv_path.parent.mkdir(parents=True, exist_ok=True)
        md_path.parent.mkdir(parents=True, exist_ok=True)

        write_ibkr_readonly_qualification_go_no_go_csv(csv_path, rows)
        write_ibkr_readonly_qualification_go_no_go_report(md_path, rows, input_path)

        statuses = sorted({r.go_no_go_status for r in rows})
        status_text = chr(44).join(statuses) if statuses else "none"
        print(f"[IBKR_READONLY_QUALIFICATION_GO_NO_GO] rows={len(rows)} statuses={status_text} qualification_allowed=false tws_connection_allowed=false api_request_allowed=false action_allowed=false")
        print(f"go_no_go_csv={csv_path}")
        print(f"report={md_path}")
        print("NOTICE: IBKR read-only qualification go/no-go summary only. Final status remains NO_GO. No TWS connection / no IBKR connection / no real contract qualification / no reqMktData / no reqHistoricalData / no order / no cancel / no rebalance / no auto trade.")
        return 0

    if args.ibkr_readonly_qualification_runbook is not None:
        from pathlib import Path
        from src.ibkr_readonly_qualification_precheck import (
            build_ibkr_readonly_qualification_precheck_rows,
            load_ibkr_readonly_qualification_precheck_config,
        )
        from src.ibkr_readonly_qualification_runbook import (
            build_ibkr_readonly_qualification_runbook_rows,
            write_ibkr_readonly_qualification_runbook_csv,
            write_ibkr_readonly_qualification_runbook_report,
        )

        input_path = args.ibkr_readonly_qualification_runbook if args.ibkr_readonly_qualification_runbook else "config.yaml"
        precheck_config = load_ibkr_readonly_qualification_precheck_config(input_path)
        precheck_rows = build_ibkr_readonly_qualification_precheck_rows(precheck_config, monitor.config["runtime"]["timezone"])
        rows = build_ibkr_readonly_qualification_runbook_rows(precheck_rows, monitor.config["runtime"]["timezone"])

        csv_path = Path(monitor.config["runtime"].get("ibkr_readonly_qualification_runbook_csv", "ibkr_readonly_qualification_runbook.csv"))
        md_path = Path(monitor.config["runtime"].get("ibkr_readonly_qualification_runbook_report", "reports/ibkr_readonly_qualification_runbook_report.md"))
        csv_path.parent.mkdir(parents=True, exist_ok=True)
        md_path.parent.mkdir(parents=True, exist_ok=True)

        write_ibkr_readonly_qualification_runbook_csv(csv_path, rows)
        write_ibkr_readonly_qualification_runbook_report(md_path, rows, input_path)

        statuses = sorted({r.runbook_status for r in rows})
        status_text = chr(44).join(statuses) if statuses else "none"
        print(f"[IBKR_READONLY_QUALIFICATION_RUNBOOK] rows={len(rows)} statuses={status_text} qualification_allowed=false tws_connection_allowed=false api_request_allowed=false action_allowed=false")
        print(f"runbook_csv={csv_path}")
        print(f"report={md_path}")
        print("NOTICE: IBKR read-only qualification runbook only. No TWS connection / no IBKR connection / no real contract qualification / no reqMktData / no reqHistoricalData / no order / no cancel / no rebalance / no auto trade.")
        return 0

    if args.ibkr_readonly_qualification_precheck is not None:
        from pathlib import Path
        from src.ibkr_readonly_qualification_precheck import (
            build_ibkr_readonly_qualification_precheck_rows,
            load_ibkr_readonly_qualification_precheck_config,
            write_ibkr_readonly_qualification_precheck_csv,
            write_ibkr_readonly_qualification_precheck_report,
        )

        input_path = args.ibkr_readonly_qualification_precheck if args.ibkr_readonly_qualification_precheck else "config.yaml"
        precheck_config = load_ibkr_readonly_qualification_precheck_config(input_path)
        rows = build_ibkr_readonly_qualification_precheck_rows(precheck_config, monitor.config["runtime"]["timezone"])

        csv_path = Path(monitor.config["runtime"].get("ibkr_readonly_qualification_precheck_csv", "ibkr_readonly_qualification_precheck.csv"))
        md_path = Path(monitor.config["runtime"].get("ibkr_readonly_qualification_precheck_report", "reports/ibkr_readonly_qualification_precheck_report.md"))
        csv_path.parent.mkdir(parents=True, exist_ok=True)
        md_path.parent.mkdir(parents=True, exist_ok=True)

        write_ibkr_readonly_qualification_precheck_csv(csv_path, rows)
        write_ibkr_readonly_qualification_precheck_report(md_path, rows, input_path)

        statuses = sorted({r.precheck_status for r in rows})
        status_text = chr(44).join(statuses) if statuses else "none"
        print(f"[IBKR_READONLY_QUALIFICATION_PRECHECK] rows={len(rows)} statuses={status_text} qualification_allowed=false tws_connection_allowed=false api_request_allowed=false action_allowed=false")
        print(f"precheck_csv={csv_path}")
        print(f"report={md_path}")
        print("NOTICE: IBKR read-only qualification precheck only. No TWS connection / no IBKR connection / no real contract qualification / no reqMktData / no reqHistoricalData / no order / no cancel / no rebalance / no auto trade.")
        return 0

    if args.ibkr_contract_qualification_execution_guard is not None:
        from pathlib import Path
        from src.ibkr_contract_mapping_plan import (
            build_ibkr_contract_mapping_plan_rows,
            load_ibkr_contract_mapping_config,
        )
        from src.ibkr_contract_qualification_dry_run import build_ibkr_contract_qualification_dry_run_rows
        from src.ibkr_contract_qualification_execution_guard import (
            build_ibkr_contract_qualification_execution_guard_rows,
            write_ibkr_contract_qualification_execution_guard_csv,
            write_ibkr_contract_qualification_execution_guard_report,
        )

        input_path = args.ibkr_contract_qualification_execution_guard if args.ibkr_contract_qualification_execution_guard else monitor.config["runtime"].get("market_data_provider_config_yaml", "data/market_data_provider_config.yaml")
        mapping_config = load_ibkr_contract_mapping_config(input_path)
        mapping_rows = build_ibkr_contract_mapping_plan_rows(mapping_config, monitor.config["runtime"]["timezone"])
        dry_run_rows = build_ibkr_contract_qualification_dry_run_rows(mapping_rows, monitor.config["runtime"]["timezone"])
        rows = build_ibkr_contract_qualification_execution_guard_rows(dry_run_rows, monitor.config["runtime"]["timezone"], explicit_execution_flag=False)

        csv_path = Path(monitor.config["runtime"].get("ibkr_contract_qualification_execution_guard_csv", "ibkr_contract_qualification_execution_guard.csv"))
        md_path = Path(monitor.config["runtime"].get("ibkr_contract_qualification_execution_guard_report", "reports/ibkr_contract_qualification_execution_guard_report.md"))
        csv_path.parent.mkdir(parents=True, exist_ok=True)
        md_path.parent.mkdir(parents=True, exist_ok=True)

        write_ibkr_contract_qualification_execution_guard_csv(csv_path, rows)
        write_ibkr_contract_qualification_execution_guard_report(md_path, rows, input_path)

        statuses = sorted({r.execution_guard_status for r in rows})
        status_text = chr(44).join(statuses) if statuses else "none"
        print(f"[IBKR_CONTRACT_QUALIFICATION_EXECUTION_GUARD] rows={len(rows)} statuses={status_text} qualification_allowed=false tws_connection_allowed=false api_request_allowed=false action_allowed=false")
        print(f"execution_guard_csv={csv_path}")
        print(f"report={md_path}")
        print("NOTICE: IBKR contract qualification execution guard only. No TWS connection / no IBKR connection / no real contract qualification / no reqMktData / no reqHistoricalData / no order / no cancel / no rebalance / no auto trade.")
        return 0

    if args.ibkr_contract_qualification_dry_run is not None:
        from pathlib import Path
        from src.ibkr_contract_mapping_plan import (
            build_ibkr_contract_mapping_plan_rows,
            load_ibkr_contract_mapping_config,
        )
        from src.ibkr_contract_qualification_dry_run import (
            build_ibkr_contract_qualification_dry_run_rows,
            write_ibkr_contract_qualification_dry_run_csv,
            write_ibkr_contract_qualification_dry_run_report,
        )

        input_path = args.ibkr_contract_qualification_dry_run if args.ibkr_contract_qualification_dry_run else monitor.config["runtime"].get("market_data_provider_config_yaml", "data/market_data_provider_config.yaml")
        mapping_config = load_ibkr_contract_mapping_config(input_path)
        mapping_rows = build_ibkr_contract_mapping_plan_rows(mapping_config, monitor.config["runtime"]["timezone"])
        rows = build_ibkr_contract_qualification_dry_run_rows(mapping_rows, monitor.config["runtime"]["timezone"])

        csv_path = Path(monitor.config["runtime"].get("ibkr_contract_qualification_dry_run_csv", "ibkr_contract_qualification_dry_run.csv"))
        md_path = Path(monitor.config["runtime"].get("ibkr_contract_qualification_dry_run_report", "reports/ibkr_contract_qualification_dry_run_report.md"))
        csv_path.parent.mkdir(parents=True, exist_ok=True)
        md_path.parent.mkdir(parents=True, exist_ok=True)

        write_ibkr_contract_qualification_dry_run_csv(csv_path, rows)
        write_ibkr_contract_qualification_dry_run_report(md_path, rows, input_path)

        statuses = sorted({r.qualification_dry_run_status for r in rows})
        status_text = chr(44).join(statuses) if statuses else "none"
        print(f"[IBKR_CONTRACT_QUALIFICATION_DRY_RUN] rows={len(rows)} statuses={status_text} qualification_allowed=false tws_connection_allowed=false api_request_allowed=false action_allowed=false")
        print(f"qualification_dry_run_csv={csv_path}")
        print(f"report={md_path}")
        print("NOTICE: IBKR contract qualification dry-run only. No TWS connection / no IBKR connection / no real contract qualification / no reqMktData / no reqHistoricalData / no order / no cancel / no rebalance / no auto trade.")
        return 0

    if args.ibkr_contract_mapping_plan is not None:
        from pathlib import Path
        from src.ibkr_contract_mapping_plan import (
            build_ibkr_contract_mapping_plan_rows,
            load_ibkr_contract_mapping_config,
            write_ibkr_contract_mapping_plan_csv,
            write_ibkr_contract_mapping_plan_report,
        )

        input_path = args.ibkr_contract_mapping_plan if args.ibkr_contract_mapping_plan else monitor.config["runtime"].get("market_data_provider_config_yaml", "data/market_data_provider_config.yaml")
        mapping_config = load_ibkr_contract_mapping_config(input_path)
        rows = build_ibkr_contract_mapping_plan_rows(mapping_config, monitor.config["runtime"]["timezone"])

        csv_path = Path(monitor.config["runtime"].get("ibkr_contract_mapping_plan_csv", "ibkr_contract_mapping_plan.csv"))
        md_path = Path(monitor.config["runtime"].get("ibkr_contract_mapping_plan_report", "reports/ibkr_contract_mapping_plan_report.md"))
        csv_path.parent.mkdir(parents=True, exist_ok=True)
        md_path.parent.mkdir(parents=True, exist_ok=True)

        write_ibkr_contract_mapping_plan_csv(csv_path, rows)
        write_ibkr_contract_mapping_plan_report(md_path, rows, input_path)

        statuses = sorted({r.mapping_status for r in rows})
        status_text = chr(44).join(statuses) if statuses else "none"
        print(f"[IBKR_CONTRACT_MAPPING_PLAN] rows={len(rows)} statuses={status_text} tws_connection_allowed=false market_data_request_allowed=false api_request_allowed=false action_allowed=false")
        print(f"contract_mapping_csv={csv_path}")
        print(f"report={md_path}")
        print("NOTICE: IBKR contract mapping plan only. No TWS connection / no IBKR connection / no contract qualification / no reqMktData / no reqHistoricalData / no order / no cancel / no rebalance / no auto trade.")
        return 0

    if args.ibkr_live_provider_adapter_check is not None:
        from pathlib import Path
        from src.ibkr_live_provider_adapter_check import (
            build_ibkr_live_provider_adapter_check_rows,
            load_ibkr_live_provider_adapter_config,
            write_ibkr_live_provider_adapter_check_csv,
            write_ibkr_live_provider_adapter_check_report,
        )

        input_path = args.ibkr_live_provider_adapter_check if args.ibkr_live_provider_adapter_check else monitor.config["runtime"].get("market_data_provider_config_yaml", "data/market_data_provider_config.yaml")
        provider_config = load_ibkr_live_provider_adapter_config(input_path)
        rows = build_ibkr_live_provider_adapter_check_rows(provider_config, monitor.config["runtime"]["timezone"])

        csv_path = Path(monitor.config["runtime"].get("ibkr_live_provider_adapter_check_csv", "ibkr_live_provider_adapter_check.csv"))
        md_path = Path(monitor.config["runtime"].get("ibkr_live_provider_adapter_check_report", "reports/ibkr_live_provider_adapter_check_report.md"))
        csv_path.parent.mkdir(parents=True, exist_ok=True)
        md_path.parent.mkdir(parents=True, exist_ok=True)

        write_ibkr_live_provider_adapter_check_csv(csv_path, rows)
        write_ibkr_live_provider_adapter_check_report(md_path, rows, input_path)

        statuses = sorted({r.adapter_status for r in rows})
        status_text = chr(44).join(statuses) if statuses else "none"
        print(f"[IBKR_LIVE_PROVIDER_ADAPTER_CHECK] rows={len(rows)} statuses={status_text} tws_connection_allowed=false market_data_request_allowed=false api_request_allowed=false action_allowed=false")
        print(f"ibkr_adapter_check_csv={csv_path}")
        print(f"report={md_path}")
        print("NOTICE: IBKR live provider adapter skeleton only. No TWS connection / no IBKR connection / no reqMktData / no reqHistoricalData / no order / no cancel / no rebalance / no auto trade.")
        return 0

    if args.live_final_research_review_pack is not None:
        from pathlib import Path
        from src.live_provider_mock_adapter import (
            build_live_provider_mock_adapter_rows,
            load_live_provider_mock_adapter_config,
        )
        from src.live_data_quality_gate import build_live_data_quality_gate_rows
        from src.live_research_review_pack import build_live_research_review_pack_rows
        from src.live_final_research_review_pack import (
            build_live_final_research_review_pack_rows,
            write_live_final_research_review_pack_csv,
            write_live_final_research_review_pack_report,
        )

        input_path = args.live_final_research_review_pack if args.live_final_research_review_pack else monitor.config["runtime"].get("market_data_provider_config_yaml", "data/market_data_provider_config.yaml")
        provider_config = load_live_provider_mock_adapter_config(input_path)
        mock_rows = build_live_provider_mock_adapter_rows(provider_config, monitor.config["runtime"]["timezone"])
        mock_rows_by_target = {row.target_id: row.__dict__ for row in mock_rows}
        quality_rows = build_live_data_quality_gate_rows(mock_rows_by_target, monitor.config["runtime"]["timezone"])
        research_rows = build_live_research_review_pack_rows(quality_rows, monitor.config["runtime"]["timezone"])
        research_rows_by_target = {row.target_id: row.__dict__ for row in research_rows}
        rows = build_live_final_research_review_pack_rows(research_rows_by_target, monitor.config["runtime"]["timezone"])

        csv_path = Path(monitor.config["runtime"].get("live_final_research_review_pack_csv", "live_final_research_review_pack.csv"))
        md_path = Path(monitor.config["runtime"].get("live_final_research_review_pack_report", "reports/live_final_research_review_pack_report.md"))
        csv_path.parent.mkdir(parents=True, exist_ok=True)
        md_path.parent.mkdir(parents=True, exist_ok=True)

        write_live_final_research_review_pack_csv(csv_path, rows)
        write_live_final_research_review_pack_report(md_path, rows, input_path)

        statuses = sorted({r.final_plan_status for r in rows})
        status_text = chr(44).join(statuses) if statuses else "none"
        print(f"[LIVE_FINAL_RESEARCH_REVIEW_PACK] rows={len(rows)} statuses={status_text} api_request_allowed=false action_allowed=false")
        print(f"live_final_research_review_pack_csv={csv_path}")
        print(f"report={md_path}")
        print("NOTICE: Live/mock final research review pack only. No API request / no IBKR connection / no reqMktData / no reqHistoricalData / no order / no cancel / no rebalance / no auto trade.")
        return 0

    if args.live_research_review_pack is not None:
        from pathlib import Path
        from src.live_provider_mock_adapter import (
            build_live_provider_mock_adapter_rows,
            load_live_provider_mock_adapter_config,
        )
        from src.live_data_quality_gate import build_live_data_quality_gate_rows
        from src.live_research_review_pack import (
            build_live_research_review_pack_rows,
            write_live_research_review_pack_csv,
            write_live_research_review_pack_report,
        )

        input_path = args.live_research_review_pack if args.live_research_review_pack else monitor.config["runtime"].get("market_data_provider_config_yaml", "data/market_data_provider_config.yaml")
        provider_config = load_live_provider_mock_adapter_config(input_path)
        mock_rows = build_live_provider_mock_adapter_rows(provider_config, monitor.config["runtime"]["timezone"])
        mock_rows_by_target = {row.target_id: row.__dict__ for row in mock_rows}
        quality_rows = build_live_data_quality_gate_rows(mock_rows_by_target, monitor.config["runtime"]["timezone"])
        rows = build_live_research_review_pack_rows(quality_rows, monitor.config["runtime"]["timezone"])

        csv_path = Path(monitor.config["runtime"].get("live_research_review_pack_csv", "live_research_review_pack.csv"))
        md_path = Path(monitor.config["runtime"].get("live_research_review_pack_report", "reports/live_research_review_pack_report.md"))
        csv_path.parent.mkdir(parents=True, exist_ok=True)
        md_path.parent.mkdir(parents=True, exist_ok=True)

        write_live_research_review_pack_csv(csv_path, rows)
        write_live_research_review_pack_report(md_path, rows, input_path)

        statuses = sorted({r.research_pack_status for r in rows})
        status_text = chr(44).join(statuses) if statuses else "none"
        print(f"[LIVE_RESEARCH_REVIEW_PACK] rows={len(rows)} statuses={status_text} api_request_allowed=false action_allowed=false")
        print(f"live_research_review_pack_csv={csv_path}")
        print(f"report={md_path}")
        print("NOTICE: Live/mock research review pack bridge only. No API request / no IBKR connection / no reqMktData / no reqHistoricalData / no order / no cancel / no rebalance / no auto trade.")
        return 0

    if args.live_data_quality_gate is not None:
        from pathlib import Path
        from src.live_provider_mock_adapter import (
            build_live_provider_mock_adapter_rows,
            load_live_provider_mock_adapter_config,
        )
        from src.live_data_quality_gate import (
            build_live_data_quality_gate_rows,
            write_live_data_quality_gate_csv,
            write_live_data_quality_gate_report,
        )

        input_path = args.live_data_quality_gate if args.live_data_quality_gate else monitor.config["runtime"].get("market_data_provider_config_yaml", "data/market_data_provider_config.yaml")
        provider_config = load_live_provider_mock_adapter_config(input_path)
        mock_rows = build_live_provider_mock_adapter_rows(provider_config, monitor.config["runtime"]["timezone"])
        mock_rows_by_target = {row.target_id: row.__dict__ for row in mock_rows}
        rows = build_live_data_quality_gate_rows(mock_rows_by_target, monitor.config["runtime"]["timezone"])

        csv_path = Path(monitor.config["runtime"].get("live_data_quality_gate_csv", "live_data_quality_gate.csv"))
        md_path = Path(monitor.config["runtime"].get("live_data_quality_gate_report", "reports/live_data_quality_gate_report.md"))
        csv_path.parent.mkdir(parents=True, exist_ok=True)
        md_path.parent.mkdir(parents=True, exist_ok=True)

        write_live_data_quality_gate_csv(csv_path, rows)
        write_live_data_quality_gate_report(md_path, rows, input_path)

        statuses = sorted({r.quality_status for r in rows})
        status_text = chr(44).join(statuses) if statuses else "none"
        print(f"[LIVE_DATA_QUALITY_GATE] rows={len(rows)} statuses={status_text} api_request_allowed=false action_allowed=false")
        print(f"quality_gate_csv={csv_path}")
        print(f"report={md_path}")
        print("NOTICE: Live/mock data quality gate only. No API request / no IBKR connection / no reqMktData / no reqHistoricalData / no order / no cancel / no rebalance / no auto trade.")
        return 0

    if args.live_provider_mock_adapter is not None:
        from pathlib import Path
        from src.live_provider_mock_adapter import (
            build_live_provider_mock_adapter_rows,
            load_live_provider_mock_adapter_config,
            write_live_provider_mock_adapter_csv,
            write_live_provider_mock_adapter_report,
        )

        input_path = args.live_provider_mock_adapter if args.live_provider_mock_adapter else monitor.config["runtime"].get("market_data_provider_config_yaml", "data/market_data_provider_config.yaml")
        provider_config = load_live_provider_mock_adapter_config(input_path)
        rows = build_live_provider_mock_adapter_rows(provider_config, monitor.config["runtime"]["timezone"])

        csv_path = Path(monitor.config["runtime"].get("live_provider_mock_adapter_csv", "live_provider_mock_adapter.csv"))
        md_path = Path(monitor.config["runtime"].get("live_provider_mock_adapter_report", "reports/live_provider_mock_adapter_report.md"))
        csv_path.parent.mkdir(parents=True, exist_ok=True)
        md_path.parent.mkdir(parents=True, exist_ok=True)

        write_live_provider_mock_adapter_csv(csv_path, rows)
        write_live_provider_mock_adapter_report(md_path, rows, input_path)

        statuses = sorted({r.data_status for r in rows})
        status_text = chr(44).join(statuses) if statuses else "none"
        print(f"[LIVE_PROVIDER_MOCK_ADAPTER] rows={len(rows)} statuses={status_text} api_request_allowed=false action_allowed=false")
        print(f"mock_adapter_csv={csv_path}")
        print(f"report={md_path}")
        print("NOTICE: Live provider mock adapter only. No API request / no IBKR connection / no reqMktData / no reqHistoricalData / no order / no cancel / no rebalance / no auto trade.")
        return 0

    if args.live_provider_request_gate is not None:
        from pathlib import Path
        from src.live_provider_request_gate import (
            build_live_provider_request_gate_rows,
            load_live_provider_request_gate_config,
            write_live_provider_request_gate_csv,
            write_live_provider_request_gate_report,
        )

        input_path = args.live_provider_request_gate if args.live_provider_request_gate else monitor.config["runtime"].get("market_data_provider_config_yaml", "data/market_data_provider_config.yaml")
        provider_config = load_live_provider_request_gate_config(input_path)
        rows = build_live_provider_request_gate_rows(provider_config, monitor.config["runtime"]["timezone"])

        csv_path = Path(monitor.config["runtime"].get("live_provider_request_gate_csv", "live_provider_request_gate.csv"))
        md_path = Path(monitor.config["runtime"].get("live_provider_request_gate_report", "reports/live_provider_request_gate_report.md"))
        csv_path.parent.mkdir(parents=True, exist_ok=True)
        md_path.parent.mkdir(parents=True, exist_ok=True)

        write_live_provider_request_gate_csv(csv_path, rows)
        write_live_provider_request_gate_report(md_path, rows, input_path)

        statuses = sorted({r.gate_status for r in rows})
        status_text = chr(44).join(statuses) if statuses else "none"
        print(f"[LIVE_PROVIDER_REQUEST_GATE] rows={len(rows)} statuses={status_text} api_request_allowed=false action_allowed=false")
        print(f"request_gate_csv={csv_path}")
        print(f"report={md_path}")
        print("NOTICE: Live provider request gate safety check only. No API request / no IBKR connection / no reqMktData / no reqHistoricalData / no order / no cancel / no rebalance / no auto trade.")
        return 0

    if args.live_provider_interface_check is not None:
        from pathlib import Path
        from src.live_market_data_provider_interface import (
            build_live_provider_interface_check_rows,
            load_live_provider_interface_config,
            write_live_provider_interface_check_csv,
            write_live_provider_interface_check_report,
        )

        input_path = args.live_provider_interface_check if args.live_provider_interface_check else monitor.config["runtime"].get("market_data_provider_config_yaml", "data/market_data_provider_config.yaml")
        provider_config = load_live_provider_interface_config(input_path)
        rows = build_live_provider_interface_check_rows(provider_config, monitor.config["runtime"]["timezone"])

        csv_path = Path(monitor.config["runtime"].get("live_provider_interface_check_csv", "live_provider_interface_check.csv"))
        md_path = Path(monitor.config["runtime"].get("live_provider_interface_check_report", "reports/live_provider_interface_check_report.md"))
        csv_path.parent.mkdir(parents=True, exist_ok=True)
        md_path.parent.mkdir(parents=True, exist_ok=True)

        write_live_provider_interface_check_csv(csv_path, rows)
        write_live_provider_interface_check_report(md_path, rows, input_path)

        statuses = sorted({r.interface_status for r in rows})
        status_text = chr(44).join(statuses) if statuses else "none"
        print(f"[LIVE_PROVIDER_INTERFACE_CHECK] rows={len(rows)} statuses={status_text} api_request_allowed=false action_allowed=false")
        print(f"interface_check_csv={csv_path}")
        print(f"report={md_path}")
        print("NOTICE: Live provider interface safety check only. No API request / no IBKR connection / no reqMktData / no reqHistoricalData / no order / no cancel / no rebalance / no auto trade.")
        return 0

    if args.market_data_provider_selector is not None:
        from pathlib import Path
        from src.market_data_provider_selector import (
            build_market_data_provider_selector_rows,
            load_market_data_provider_selector_config,
            write_market_data_provider_selector_csv,
            write_market_data_provider_selector_report,
        )

        input_path = args.market_data_provider_selector if args.market_data_provider_selector else monitor.config["runtime"].get("market_data_provider_config_yaml", "data/market_data_provider_config.yaml")
        provider_config = load_market_data_provider_selector_config(input_path)
        rows = build_market_data_provider_selector_rows(provider_config, monitor.config["runtime"]["timezone"])

        csv_path = Path(monitor.config["runtime"].get("market_data_provider_selector_csv", "market_data_provider_selector.csv"))
        md_path = Path(monitor.config["runtime"].get("market_data_provider_selector_report", "reports/market_data_provider_selector_report.md"))
        csv_path.parent.mkdir(parents=True, exist_ok=True)
        md_path.parent.mkdir(parents=True, exist_ok=True)

        write_market_data_provider_selector_csv(csv_path, rows)
        write_market_data_provider_selector_report(md_path, rows, input_path)

        statuses = sorted({r.selection_status for r in rows})
        status_text = chr(44).join(statuses) if statuses else "none"
        print(f"[MARKET_DATA_PROVIDER_SELECTOR] rows={len(rows)} statuses={status_text} live_request_allowed=false action_allowed=false")
        print(f"selector_csv={csv_path}")
        print(f"report={md_path}")
        print("NOTICE: Provider selector planning only. No API request / no IBKR connection / no reqMktData / no reqHistoricalData / no order / no cancel / no rebalance / no auto trade.")
        return 0

    if args.market_data_provider_config_audit is not None:
        from pathlib import Path
        from src.market_data_provider_config_audit import (
            build_market_data_provider_config_audit_rows,
            load_market_data_provider_config,
            write_market_data_provider_config_audit_csv,
            write_market_data_provider_config_audit_report,
        )

        input_path = args.market_data_provider_config_audit if args.market_data_provider_config_audit else monitor.config["runtime"].get("market_data_provider_config_yaml", "data/market_data_provider_config.yaml")
        provider_config = load_market_data_provider_config(input_path)
        rows = build_market_data_provider_config_audit_rows(provider_config, monitor.config["runtime"]["timezone"])

        csv_path = Path(monitor.config["runtime"].get("market_data_provider_config_audit_csv", "market_data_provider_config_audit.csv"))
        md_path = Path(monitor.config["runtime"].get("market_data_provider_config_audit_report", "reports/market_data_provider_config_audit_report.md"))
        csv_path.parent.mkdir(parents=True, exist_ok=True)
        md_path.parent.mkdir(parents=True, exist_ok=True)

        write_market_data_provider_config_audit_csv(csv_path, rows)
        write_market_data_provider_config_audit_report(md_path, rows, input_path)

        statuses = sorted({r.config_status for r in rows})
        status_text = chr(44).join(statuses) if statuses else "none"
        print(f"[MARKET_DATA_PROVIDER_CONFIG_AUDIT] providers={len(rows)} statuses={status_text} action_allowed=false")
        print(f"config_audit_csv={csv_path}")
        print(f"report={md_path}")
        print("NOTICE: Provider config audit only. No API request / no IBKR connection / no reqMktData / no reqHistoricalData / no order / no cancel / no rebalance / no auto trade.")
        return 0

    if args.market_data_provider_readiness:
        from pathlib import Path
        from src.market_data_provider_readiness import (
            build_market_data_provider_readiness_rows,
            load_market_data_provider_readiness_config,
            write_market_data_provider_readiness_csv,
            write_market_data_provider_readiness_report,
        )

        config_path = monitor.config["runtime"].get("market_data_provider_config_yaml", "data/market_data_provider_config.yaml")
        provider_config = load_market_data_provider_readiness_config(config_path)
        rows = build_market_data_provider_readiness_rows(monitor.config["runtime"]["timezone"], provider_config)

        csv_path = Path(monitor.config["runtime"].get("market_data_provider_readiness_csv", "market_data_provider_readiness.csv"))
        md_path = Path(monitor.config["runtime"].get("market_data_provider_readiness_report", "reports/market_data_provider_readiness_report.md"))
        csv_path.parent.mkdir(parents=True, exist_ok=True)
        md_path.parent.mkdir(parents=True, exist_ok=True)

        write_market_data_provider_readiness_csv(csv_path, rows)
        write_market_data_provider_readiness_report(md_path, rows)

        statuses = sorted({r.readiness_status for r in rows})
        status_text = chr(44).join(statuses) if statuses else "none"
        print(f"[MARKET_DATA_PROVIDER_READINESS] rows={len(rows)} statuses={status_text} live_request_allowed=false action_allowed=false")
        print(f"readiness_csv={csv_path}")
        print(f"report={md_path}")
        print("NOTICE: Provider readiness planning only. No API request / no IBKR connection / no reqMktData / no reqHistoricalData / no order / no cancel / no rebalance / no auto trade.")
        return 0

    if args.final_research_review_pack is not None:
        from pathlib import Path
        from src.final_research_review_pack import (
            build_final_research_review_pack_rows,
            load_csv_by_key,
            write_final_research_review_pack_csv,
            write_final_research_review_pack_report,
        )

        input_csv = args.final_research_review_pack if args.final_research_review_pack else monitor.config["runtime"].get("manual_market_data_sample_valid_csv", "data/manual_market_data_sample_valid.csv")

        pipeline_args = type("PipelineArgs", (), {})()
        pipeline_args.manual_research_trading_pipeline = input_csv

        # Reuse the same pipeline building logic by invoking the underlying monitor methods directly.
        pipeline_rows, pipeline_csv, pipeline_report = monitor.run_manual_market_data_pipeline(input_csv)
        review_rows, review_csv, review_report = monitor.run_manual_market_data_review_pack(input_csv)

        from src.research_trading_plan_generator import (
            build_research_trading_plan_rows,
            load_review_pack_by_symbol,
            write_research_trading_plan_csv,
            write_research_trading_plan_report,
        )
        from src.manual_research_trading_pipeline import (
            build_manual_research_trading_pipeline_step_row,
            summarize_step_status,
            write_manual_research_trading_pipeline_summary_csv,
            write_manual_research_trading_pipeline_report,
        )

        tz_cfg = monitor.config["runtime"]["timezone"]
        review_by_symbol = load_review_pack_by_symbol(review_csv)
        trading_rows = build_research_trading_plan_rows(review_by_symbol, tz_cfg)

        trading_csv = Path(monitor.config["runtime"].get("research_trading_plan_csv", "research_trading_plan.csv"))
        trading_report = Path(monitor.config["runtime"].get("research_trading_plan_report", "reports/research_trading_plan_report.md"))
        trading_csv.parent.mkdir(parents=True, exist_ok=True)
        trading_report.parent.mkdir(parents=True, exist_ok=True)
        write_research_trading_plan_csv(trading_csv, trading_rows)
        write_research_trading_plan_report(trading_report, trading_rows, review_csv)

        summary_rows = [
            build_manual_research_trading_pipeline_step_row(1, "Phase 6D", "manual_market_data_pipeline", summarize_step_status([getattr(r, "status", "") for r in pipeline_rows]), pipeline_csv, pipeline_report, len(pipeline_rows), tz_cfg, f"input_csv={input_csv}"),
            build_manual_research_trading_pipeline_step_row(2, "Phase 6G", "manual_market_data_review_pack", summarize_step_status([getattr(r, "strategy_label", "") for r in review_rows]), review_csv, review_report, len(review_rows), tz_cfg, "review pack from manual pipeline"),
            build_manual_research_trading_pipeline_step_row(3, "Phase 8A", "research_trading_plan", summarize_step_status([r.plan_status for r in trading_rows]), str(trading_csv), str(trading_report), len(trading_rows), tz_cfg, "final research trading plan"),
        ]

        summary_csv = Path(monitor.config["runtime"].get("manual_research_trading_pipeline_summary_csv", "manual_research_trading_pipeline_summary.csv"))
        summary_report = Path(monitor.config["runtime"].get("manual_research_trading_pipeline_report", "reports/manual_research_trading_pipeline_report.md"))
        summary_csv.parent.mkdir(parents=True, exist_ok=True)
        summary_report.parent.mkdir(parents=True, exist_ok=True)
        write_manual_research_trading_pipeline_summary_csv(summary_csv, summary_rows)
        write_manual_research_trading_pipeline_report(summary_report, summary_rows, input_csv)

        trading_by_symbol = load_csv_by_key(str(trading_csv), "etf_symbol")
        final_rows = build_final_research_review_pack_rows(trading_by_symbol, tz_cfg)

        final_csv = Path(monitor.config["runtime"].get("final_research_review_pack_csv", "final_research_review_pack.csv"))
        final_report = Path(monitor.config["runtime"].get("final_research_review_pack_report", "reports/final_research_review_pack_report.md"))
        final_csv.parent.mkdir(parents=True, exist_ok=True)
        final_report.parent.mkdir(parents=True, exist_ok=True)

        write_final_research_review_pack_csv(final_csv, final_rows)
        write_final_research_review_pack_report(final_report, final_rows, input_csv, str(summary_csv), str(trading_csv))

        labels = sorted({r.final_review_label for r in final_rows})
        label_text = chr(44).join(labels) if labels else "none"
        print(f"[FINAL_RESEARCH_REVIEW_PACK] rows={len(final_rows)} labels={label_text} action_allowed=false")
        print(f"final_csv={final_csv}")
        print(f"final_report={final_report}")
        print(f"pipeline_summary_csv={summary_csv}")
        print(f"trading_plan_csv={trading_csv}")
        print("NOTICE: Final research review pack only. action_allowed=false / no IBKR connection / no reqMktData / no reqHistoricalData / no order / no cancel / no rebalance / no auto trade.")
        return 0

    if args.manual_research_trading_pipeline is not None:
        from pathlib import Path
        from src.research_trading_plan_generator import (
            build_research_trading_plan_rows,
            load_review_pack_by_symbol,
            write_research_trading_plan_csv,
            write_research_trading_plan_report,
        )
        from src.manual_research_trading_pipeline import (
            build_manual_research_trading_pipeline_step_row,
            summarize_step_status,
            write_manual_research_trading_pipeline_report,
            write_manual_research_trading_pipeline_summary_csv,
        )

        input_csv = args.manual_research_trading_pipeline if args.manual_research_trading_pipeline else monitor.config["runtime"].get("manual_market_data_sample_valid_csv", "data/manual_market_data_sample_valid.csv")
        tz_cfg = monitor.config["runtime"]["timezone"]

        pipeline_rows, pipeline_csv, pipeline_report = monitor.run_manual_market_data_pipeline(input_csv)
        pipeline_status = summarize_step_status([getattr(r, "status", "") for r in pipeline_rows])

        review_rows, review_csv, review_report = monitor.run_manual_market_data_review_pack(input_csv)
        review_status = summarize_step_status([getattr(r, "strategy_label", "") for r in review_rows])

        review_by_symbol = load_review_pack_by_symbol(review_csv)
        trading_rows = build_research_trading_plan_rows(review_by_symbol, tz_cfg)

        trading_csv = Path(monitor.config["runtime"].get("research_trading_plan_csv", "research_trading_plan.csv"))
        trading_report = Path(monitor.config["runtime"].get("research_trading_plan_report", "reports/research_trading_plan_report.md"))
        trading_csv.parent.mkdir(parents=True, exist_ok=True)
        trading_report.parent.mkdir(parents=True, exist_ok=True)
        write_research_trading_plan_csv(trading_csv, trading_rows)
        write_research_trading_plan_report(trading_report, trading_rows, review_csv)

        trading_status = summarize_step_status([r.plan_status for r in trading_rows])

        summary_rows = [
            build_manual_research_trading_pipeline_step_row(1, "Phase 6D", "manual_market_data_pipeline", pipeline_status, pipeline_csv, pipeline_report, len(pipeline_rows), tz_cfg, f"input_csv={input_csv}"),
            build_manual_research_trading_pipeline_step_row(2, "Phase 6G", "manual_market_data_review_pack", review_status, review_csv, review_report, len(review_rows), tz_cfg, "review pack from manual pipeline"),
            build_manual_research_trading_pipeline_step_row(3, "Phase 8A", "research_trading_plan", trading_status, str(trading_csv), str(trading_report), len(trading_rows), tz_cfg, "final research trading plan"),
        ]

        summary_csv = Path(monitor.config["runtime"].get("manual_research_trading_pipeline_summary_csv", "manual_research_trading_pipeline_summary.csv"))
        summary_report = Path(monitor.config["runtime"].get("manual_research_trading_pipeline_report", "reports/manual_research_trading_pipeline_report.md"))
        summary_csv.parent.mkdir(parents=True, exist_ok=True)
        summary_report.parent.mkdir(parents=True, exist_ok=True)

        write_manual_research_trading_pipeline_summary_csv(summary_csv, summary_rows)
        write_manual_research_trading_pipeline_report(summary_report, summary_rows, input_csv)

        statuses = sorted({r.status for r in summary_rows})
        status_text = chr(44).join(statuses) if statuses else "none"
        print(f"[MANUAL_RESEARCH_TRADING_PIPELINE] steps={len(summary_rows)} statuses={status_text} action_allowed=false")
        print(f"summary_csv={summary_csv}")
        print(f"report={summary_report}")
        print(f"trading_plan_csv={trading_csv}")
        print(f"trading_plan_report={trading_report}")
        print("NOTICE: One-command manual research trading pipeline only. action_allowed=false / no IBKR connection / no reqMktData / no reqHistoricalData / no order / no cancel / no rebalance / no auto trade.")
        return 0

    if args.research_trading_plan is not None:
        from pathlib import Path
        from src.research_trading_plan_generator import (
            build_research_trading_plan_rows,
            load_review_pack_by_symbol,
            write_research_trading_plan_csv,
            write_research_trading_plan_report,
        )

        input_path = args.research_trading_plan if args.research_trading_plan else monitor.config["runtime"].get("manual_market_data_review_pack_csv", "manual_market_data_review_pack.csv")
        review_rows = load_review_pack_by_symbol(input_path)
        rows = build_research_trading_plan_rows(review_rows, monitor.config["runtime"]["timezone"])

        csv_path = Path(monitor.config["runtime"].get("research_trading_plan_csv", "research_trading_plan.csv"))
        md_path = Path(monitor.config["runtime"].get("research_trading_plan_report", "reports/research_trading_plan_report.md"))
        csv_path.parent.mkdir(parents=True, exist_ok=True)
        md_path.parent.mkdir(parents=True, exist_ok=True)

        write_research_trading_plan_csv(csv_path, rows)
        write_research_trading_plan_report(md_path, rows, input_path)

        statuses = sorted({r.plan_status for r in rows})
        print(f"[RESEARCH_TRADING_PLAN] etfs={len(rows)} statuses={chr(44).join(statuses) if statuses else none} action_allowed=false")
        print(f"plan_csv={csv_path}")
        print(f"report={md_path}")
        print("NOTICE: Final manual research trading plan only. action_allowed=false / no IBKR connection / no reqMktData / no reqHistoricalData / no order / no cancel / no rebalance / no auto trade.")
        return 0

    if args.pricing_mock:
        rows, csv_path, md_path = monitor.run_pricing_mock("data/mock_pricing_inputs.yaml")
        print(f"[PRICING_MOCK] symbols={len(rows)}")
        print(f"csv={csv_path}")
        print(f"markdown={md_path}")
        print("NOTICE: Pricing mock is research-only model framework verification. No auto order / no auto sell / no cancel.")
        return 0

    if args.ibkr_smoke:
        quotes, csv_path, md_path, conn_status = monitor.run_ibkr_smoke(preferred_data_type="delayed")
        print(f"[IBKR_SMOKE] status={conn_status} symbols={len(quotes)}")
        print(f"csv={csv_path}")
        print(f"markdown={md_path}")
        print("NOTICE: Read-only smoke test only. No auto order / no auto sell / no cancel.")
        return 0

    if args.contract_search:
        rows, csv_path, md_path, conn_status = monitor.run_contract_search(args.contract_search)
        print(f"[IBKR_CONTRACT_SEARCH] status={conn_status} query={args.contract_search} candidates={len(rows)}")
        print(f"csv={csv_path}")
        print(f"markdown={md_path}")
        print("NOTICE: Read-only contract discovery only. No auto order / no auto sell / no cancel.")
        return 0

    if args.source_audit:
        rows, report_md, log_csv = monitor.run_source_audit(args.source_audit)
        print(f"[SOURCE_ADAPTER_AUDIT] providers={len(rows)}")
        print(f"report={report_md}")
        print(f"log_csv={log_csv}")
        print("NOTICE: Source audit is research-only workflow. No auto order / no auto sell / no cancel.")
        return 0


    if args.ibkr_historical_plan:
        rows, plan_csv, report_md, raw_csv = monitor.run_ibkr_historical_plan()
        print(f"[IBKR_HISTORICAL_PLAN] symbols={len(rows)}")
        print(f"plan_csv={plan_csv}")
        print(f"report={report_md}")
        print(f"raw_csv={raw_csv}")
        print("NOTICE: IBKR historical adapter is plan-only in Phase 4B-1. No reqHistoricalData call / no auto order / no auto sell / no cancel.")
        return 0


    if args.ibkr_historical_fetch:
        rows, raw_csv, report_md, log_csv = monitor.run_ibkr_historical_fetch(execute=args.execute_ibkr_historical_fetch)
        print(f"[IBKR_HISTORICAL_FETCH] mode={'execute' if args.execute_ibkr_historical_fetch else 'dry_run'} symbols={len(rows)}")
        print(f"raw_csv={raw_csv}")
        print(f"report={report_md}")
        print(f"log_csv={log_csv}")
        if args.execute_ibkr_historical_fetch:
            print("NOTICE: Read-only historical fetch requested by explicit user switch. No auto order / no auto sell / no cancel.")
        else:
            print("NOTICE: Dry-run only. No TWS connection / no reqHistoricalData call / no auto order / no auto sell / no cancel.")
        return 0

    if args.quality_gate:
        summary, report_md, log_csv = monitor.run_historical_quality_gate(args.quality_gate)
        print(f"[HISTORICAL_QUALITY_GATE] status={summary['status']} total_rows={summary['total_rows']}")
        print(f"symbols={','.join(summary['symbols'])}")
        print(f"date_range={summary['start_date']}->{summary['end_date']}")
        print(f"warning_flags={';'.join(summary['warning_flags']) if summary['warning_flags'] else 'none'}")
        print(f"fail_reasons={';'.join(summary['fail_reasons']) if summary['fail_reasons'] else 'none'}")
        print(f"report={report_md}")
        print(f"log_csv={log_csv}")
        print("NOTICE: Historical quality gate is research-only. No IBKR connection / no reqHistoricalData / no auto validate-history / no auto calibration-csv / no auto order / no auto sell / no cancel.")
        return 0


    if args.historical_pipeline_check:
        summary, report_md, log_csv = monitor.run_historical_pipeline_check()
        print(f"[HISTORICAL_PIPELINE_CHECK] status={summary['status']}")
        print(f"current_blocking_step={summary['current_blocking_step']}")
        print(f"warning_flags={';'.join(summary['warning_flags']) if summary['warning_flags'] else 'none'}")
        print(f"notes={summary['notes']}")
        print(f"report={report_md}")
        print(f"log_csv={log_csv}")
        print("NOTICE: Manual-only / research-only integration check. No auto chain / no auto ibkr-historical-fetch / no auto quality-gate / no auto validate-history / no auto calibration-csv / no auto trade.")
        return 0

    if args.build_history:
        rows, candidate_csv, report_md, log_csv = monitor.run_build_history(args.build_history)
        print(f"[HISTORICAL_DATA_BUILD] symbols={len(rows)}")
        print(f"candidate_csv={candidate_csv}")
        print(f"report={report_md}")
        print(f"log_csv={log_csv}")
        print("NOTICE: Raw history build is research-only workflow. No auto order / no auto sell / no cancel.")
        return 0

    if args.validate_history:
        rows, validated_csv, report_md, log_csv = monitor.run_validate_history(args.validate_history)
        print(f"[HISTORICAL_DATA_VALIDATION] symbols={len(rows)}")
        print(f"validated_csv={validated_csv}")
        print(f"report={report_md}")
        print(f"log_csv={log_csv}")
        print("NOTICE: Historical validation is research-only workflow. No auto order / no auto sell / no cancel.")
        return 0

    if args.calibration_csv:
        rows, csv_path, md_path = monitor.run_conversion_factor_calibration_csv(args.calibration_csv)
        print(f"[CONVERSION_FACTOR_CALIBRATION] symbols={len(rows)}")
        print(f"csv={csv_path}")
        print(f"markdown={md_path}")
        print("NOTICE: Calibration is read-only research workflow. No auto order / no auto sell / no cancel.")
        return 0

    if args.calibrate_model:
        rows, json_path, md_path = monitor.run_model_calibration(force_mock=True)
        print(f"[MODEL_CALIBRATION] symbols={len(rows)}")
        print(f"json={json_path}")
        print(f"markdown={md_path}")
        print("NOTICE: Calibration is read-only research workflow. No auto order / no auto sell / no cancel.")
        return 0

    if args.mock:
        ok, msg = False, "mock_mode_enabled"
    else:
        ok, msg = monitor.test_ibkr_connection()
    print(f"[IBKR] connection={ok} detail={msg}")

    rows, csv_path, md_path = monitor.run(ibkr_connected=ok, force_mock=args.mock)
    print(f"generated_rows={len(rows)}")
    print(f"csv={csv_path}")
    print(f"markdown={md_path}")
    print("NOTICE: No auto order / no auto sell / no cancel / manual execution only.")
    return 0


if __name__ == "__main__":
    try:
        raise SystemExit(main())
    except RuntimeError as exc:
        print(str(exc), file=sys.stderr)
        raise SystemExit(2)
