from pathlib import Path
import csv
import subprocess

from src.theoretical_pricing_engine import build_theoretical_price_rows, write_theoretical_price_csv, write_theoretical_price_report


def _snapshot_rows(xau='2350', xag='28.5', jpy='155', cny='7.2', sge='unavailable'):
    return {
        'XAUUSD': {'factor': 'XAUUSD', 'value': xau, 'source_status': 'ok', 'warning_flags': 'manual_mock_data'},
        'XAGUSD': {'factor': 'XAGUSD', 'value': xag, 'source_status': 'ok', 'warning_flags': 'manual_mock_data'},
        'USDJPY': {'factor': 'USDJPY', 'value': jpy, 'source_status': 'ok', 'warning_flags': 'manual_mock_data'},
        'USDCNY': {'factor': 'USDCNY', 'value': cny, 'source_status': 'ok', 'warning_flags': 'manual_mock_data'},
        'SGE_AU99_99': {'factor': 'SGE_AU99_99', 'value': sge, 'source_status': 'unavailable' if sge == 'unavailable' else 'ok', 'warning_flags': 'no_realtime_source' if sge == 'unavailable' else 'manual_mock_data'},
    }


def test_generate_three_etf_rows_and_proxy_for_518880():
    rows = build_theoretical_price_rows(_snapshot_rows(), {'jst': 'Asia/Tokyo', 'et': 'America/New_York'}, {'1540.T': 0.1, '1542.T': 0.1, '518880.SH': 0.001})
    assert len(rows) == 3
    symbols = {r.etf_symbol for r in rows}
    assert symbols == {'1540.T', '1542.T', '518880.SH'}
    cn = [r for r in rows if r.etf_symbol == '518880.SH'][0]
    assert 'sge_unavailable_external_proxy' in cn.warning_flags


def test_1540_unavailable_when_xau_or_usdjpy_missing():
    rows = build_theoretical_price_rows(_snapshot_rows(xau='unavailable'), {'jst': 'Asia/Tokyo', 'et': 'America/New_York'}, {'1540.T': 0.1, '1542.T': 0.1, '518880.SH': 0.001})
    jp = [r for r in rows if r.etf_symbol == '1540.T'][0]
    assert jp.pricing_status == 'unavailable'


def test_1542_unavailable_when_xag_or_usdjpy_missing():
    rows = build_theoretical_price_rows(_snapshot_rows(xag='unavailable'), {'jst': 'Asia/Tokyo', 'et': 'America/New_York'}, {'1540.T': 0.1, '1542.T': 0.1, '518880.SH': 0.001})
    jp = [r for r in rows if r.etf_symbol == '1542.T'][0]
    assert jp.pricing_status == 'unavailable'


def test_csv_fields_and_report_generation(tmp_path: Path):
    rows = build_theoretical_price_rows(_snapshot_rows(), {'jst': 'Asia/Tokyo', 'et': 'America/New_York'}, {'1540.T': 0.1, '1542.T': 0.1, '518880.SH': 0.001})
    csv_path = tmp_path / 'theoretical_price_snapshot.csv'
    md_path = tmp_path / 'theoretical_price_report.md'
    write_theoretical_price_csv(csv_path, rows)
    write_theoretical_price_report(md_path, rows, 'upstream_factor_snapshot.csv', '2026-05-05T00:00:00+08:00')
    with open(csv_path, newline='', encoding='utf-8') as f:
        data = list(csv.DictReader(f))
    required = {'etf_symbol', 'theoretical_price', 'currency', 'pricing_status', 'metal_factor', 'metal_value', 'fx_factor', 'fx_value', 'conversion_factor', 'source_status', 'warning_flags', 'notes', 'timestamp_jst', 'timestamp_et'}
    assert required.issubset(set(data[0].keys()))
    assert md_path.exists()


def test_cli_theoretical_pricing_runs():
    subprocess.run(['python3', 'main.py', '--config', 'config.yaml', '--upstream-factors'], check=True)
    subprocess.run(['python3', 'main.py', '--config', 'config.yaml', '--theoretical-pricing', 'upstream_factor_snapshot.csv'], check=True)
    assert Path('theoretical_price_snapshot.csv').exists()
    assert Path('reports/theoretical_price_report.md').exists()
