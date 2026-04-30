from __future__ import annotations

from collections import Counter
from datetime import datetime

from fpga_debug_agent.models import RunContext


def render_markdown_report(ctx: RunContext) -> str:
    findings = list(ctx.all_findings())
    sev = Counter(f.severity for f in findings)
    lines: list[str] = []
    lines.append("# FPGA Multi-Agent Debug Report")
    lines.append("")
    lines.append(f"Generated: {datetime.now().isoformat(timespec='seconds')}")
    lines.append(f"Project root: `{ctx.files.root}`")
    if ctx.top:
        lines.append(f"Top module: `{ctx.top}`")
    lines.append("")
    lines.append("## Input Summary")
    lines.append(f"- RTL files: {len(ctx.files.rtl_files)}")
    lines.append(f"- XDC files: {len(ctx.files.xdc_files)}")
    lines.append(f"- Timing reports: {len(ctx.files.timing_reports)}")
    lines.append(f"- Simulation logs: {len(ctx.files.sim_logs)}")
    lines.append("")
    lines.append("## Agent Execution Summary")
    for result in ctx.results:
        lines.append(f"- `{result.name}`: {result.summary}")
    lines.append("")
    lines.append("## Finding Summary")
    for key in ["error", "warning", "info"]:
        lines.append(f"- {key}: {sev.get(key, 0)}")
    lines.append("")
    if not findings:
        lines.append("No findings were produced.")
    else:
        for finding in findings:
            lines.append(finding.to_markdown())
    lines.append("")
    lines.append("## Generated Artifacts")
    for result in ctx.results:
        for name, path in result.artifacts.items():
            lines.append(f"- `{name}` from `{result.name}`: `{path}`")
    lines.append("")
    return "\n".join(lines)
