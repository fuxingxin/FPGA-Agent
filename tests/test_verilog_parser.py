from pathlib import Path

from fpga_debug_agent.parsers.verilog import parse_design


def test_parse_demo_design() -> None:
    root = Path(__file__).resolve().parents[1]
    rtl = list((root / "examples" / "demo_project" / "rtl").glob("*.sv"))
    design = parse_design(rtl)
    names = {m.name for m in design.modules}
    assert "top_lvds_rx" in names
    assert "clk_pix" in design.clocks
    assert "rst_n" in design.resets
