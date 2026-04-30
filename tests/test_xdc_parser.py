from pathlib import Path

from fpga_debug_agent.parsers.xdc import parse_xdc_file


def test_parse_xdc() -> None:
    root = Path(__file__).resolve().parents[1]
    xdc = parse_xdc_file(root / "examples" / "demo_project" / "constrs" / "top.xdc")
    assert len(xdc.clocks) == 2
    assert len(xdc.input_delays) == 1
