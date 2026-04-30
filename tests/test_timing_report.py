from pathlib import Path

from fpga_debug_agent.parsers.timing_report import parse_timing_report


def test_parse_demo_timing_report() -> None:
    root = Path(__file__).resolve().parents[1]
    report = parse_timing_report(root / "examples" / "demo_project" / "reports" / "timing_summary.rpt")
    assert report.wns == -0.612
    assert len(report.failing_paths) == 1
    assert report.failing_paths[0].logic_levels == 9
