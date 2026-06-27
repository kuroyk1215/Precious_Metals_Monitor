from __future__ import annotations

import json
import tempfile
import unittest
from pathlib import Path

from scripts.build_visual_result_dashboard_readable import generate_readable_dashboard


class VisualDashboardReadabilityP23Tests(unittest.TestCase):
    def test_p2_3_dashboard_compresses_gate_reasons_and_blocks_watch_only(self) -> None:
        with tempfile.TemporaryDirectory() as raw_dir:
            tmp_path = Path(raw_dir)
            input_json = tmp_path / "visual_result.json"
            output_html = tmp_path / "latest_dashboard.html"
            input_json.write_text(
                json.dumps(
                    {
                        "assets": [
                            {
                                "asset_name": "Gold / GLD",
                                "symbol": "GLD",
                                "market": "US ETF",
                                "asset_eligibility": "eligible",
                                "data_vintage": {"status": "fresh"},
                                "sample_quality": "sufficient",
                                "interval_status": "stable",
                                "direction": "upside",
                                "horizons": {
                                    "short": {"direction": "upside", "p10": -0.2, "p50": 0.3, "p90": 1.1},
                                    "medium": {"direction": "neutral", "p10": -0.4, "p50": 0.0, "p90": 0.8},
                                    "long": {"direction": "upside", "p10": 0.1, "p50": 0.7, "p90": 1.8},
                                },
                            },
                            {
                                "asset_name": "Silver / SLV",
                                "symbol": "SLV",
                                "market": "US ETF",
                                "asset_eligibility": "eligible",
                                "data_vintage": {"status": "fresh"},
                                "sample_quality": "watch_only",
                                "interval_status": "unstable_distribution",
                                "direction": "upside",
                                "horizons": {
                                    "short": {"direction": "upside", "p10": -2.2, "p50": 0.8, "p90": 3.7},
                                    "medium": {"direction": "upside", "p10": -3.1, "p50": 1.2, "p90": 5.0},
                                    "long": {"direction": "upside", "p10": -6.0, "p50": 2.4, "p90": 8.8},
                                },
                            },
                        ]
                    },
                    ensure_ascii=False,
                ),
                encoding="utf-8",
            )

            assets, input_ok = generate_readable_dashboard(input_json=input_json, output_html=output_html)

            self.assertTrue(input_ok)
            self.assertEqual(len(assets), 2)
            html = output_html.read_text(encoding="utf-8")
            for required in (
                "今日整体状态",
                "可判断资产数",
                "暂不可判断资产数",
                "数据警告数量",
                "样本不足数量",
                "区间异常数量",
                "Gold / GLD",
                "Silver / SLV",
                "偏涨",
                "暂不可判断",
                "样本仅观察：不得输出正常方向判断",
                "区间风险：分布不稳定",
                "P10",
                "P50",
                "P90",
            ):
                self.assertIn(required, html)
            self.assertLessEqual(html.count("<li>"), 4)

    def test_p2_3_missing_input_writes_fail_closed_page_and_returns_not_ok(self) -> None:
        with tempfile.TemporaryDirectory() as raw_dir:
            tmp_path = Path(raw_dir)
            input_json = tmp_path / "missing_visual_result.json"
            output_html = tmp_path / "latest_dashboard.html"

            assets, input_ok = generate_readable_dashboard(input_json=input_json, output_html=output_html)

            self.assertFalse(input_ok)
            self.assertEqual(len(assets), 2)
            html = output_html.read_text(encoding="utf-8")
            self.assertIn("Gold / GLD", html)
            self.assertIn("Silver / SLV", html)
            self.assertIn("暂不可判断", html)
            self.assertIn("missing visual_result.json", html)


if __name__ == "__main__":
    unittest.main()
