from __future__ import annotations

from fpga_debug_agent.agents.base import Agent
from fpga_debug_agent.models import AgentResult, Finding, RunContext
from fpga_debug_agent.parsers.timing_report import parse_timing_report


class TimingAnalyzerAgent(Agent):
    name = "timing_analyzer"

    def run(self, ctx: RunContext) -> AgentResult:
        reports = [parse_timing_report(path) for path in ctx.files.timing_reports]
        findings: list[Finding] = []

        for report in reports:
            if report.wns is not None and report.wns < 0:
                findings.append(
                    Finding(
                        agent=self.name,
                        severity="error",
                        title="Negative setup slack detected",
                        detail=f"Timing summary reports WNS={report.wns} ns.",
                        file=report.source,
                        recommendation="Inspect the worst failing paths, reduce combinational depth, or add pipeline registers after confirming constraints are correct.",
                    )
                )
            if report.whs is not None and report.whs < 0:
                findings.append(
                    Finding(
                        agent=self.name,
                        severity="error",
                        title="Negative hold slack detected",
                        detail=f"Timing summary reports WHS={report.whs} ns.",
                        file=report.source,
                        recommendation="Check clock skew, very short data paths, IO min delays and accidental generated-clock relationships.",
                    )
                )

            for path in report.failing_paths[:20]:
                root = "unknown"
                rec = "Review this path in Vivado and map endpoint/startpoint back to RTL."
                if path.path_type == "setup":
                    if path.logic_levels is not None and path.logic_levels >= 6:
                        root = "deep combinational path"
                        rec = "Insert pipeline registers, split arithmetic/comparison logic, or retime the stage boundary."
                    elif path.clock_group and "async" in path.clock_group.lower():
                        root = "possible CDC constraint issue"
                        rec = "Verify set_clock_groups -asynchronous or synchronizer structure for this path."
                    else:
                        root = "setup path violation"
                        rec = "Check whether the clock period is realistic and whether the path should be pipelined or constrained."
                elif path.path_type == "hold":
                    root = "hold path violation"
                    rec = "Avoid manually fixing hold in RTL first; inspect clocking, generated clocks, input min delay and placement/skew."

                evidence = []
                if path.startpoint:
                    evidence.append(f"Startpoint: {path.startpoint}")
                if path.endpoint:
                    evidence.append(f"Endpoint: {path.endpoint}")
                if path.logic_levels is not None:
                    evidence.append(f"Logic levels: {path.logic_levels}")
                evidence.extend(path.evidence[:5])

                findings.append(
                    Finding(
                        agent=self.name,
                        severity="error",
                        title=f"Failing {path.path_type} path: {root}",
                        detail=f"Slack is {path.slack} ns.",
                        file=path.source_file,
                        evidence=evidence,
                        recommendation=rec,
                    )
                )

        data = {
            "reports": [
                {
                    "source": r.source,
                    "wns": r.wns,
                    "tns": r.tns,
                    "whs": r.whs,
                    "ths": r.ths,
                    "failing_path_count": len(r.failing_paths),
                    "failing_paths": [p.__dict__ for p in r.failing_paths[:50]],
                }
                for r in reports
            ]
        }
        ctx.write_json(ctx.out_dir / "timing_summary.json", data)
        return AgentResult(
            name=self.name,
            summary=f"Parsed {len(reports)} timing reports and found {sum(len(r.failing_paths) for r in reports)} failing paths.",
            findings=findings,
            artifacts={"timing_summary": str(ctx.out_dir / "timing_summary.json")},
            data=data,
        )
