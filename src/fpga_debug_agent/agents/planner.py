from __future__ import annotations

from fpga_debug_agent.agents.base import Agent
from fpga_debug_agent.models import AgentResult, Finding, RunContext


class PlannerAgent(Agent):
    name = "planner"

    def run(self, ctx: RunContext) -> AgentResult:
        tasks: list[str] = []
        if ctx.files.rtl_files:
            tasks.append("Parse RTL hierarchy, clocks, resets, FSMs and CDC candidates")
        if ctx.files.xdc_files:
            tasks.append("Validate XDC clocks, IO delays and asynchronous clock groups")
        if ctx.files.timing_reports:
            tasks.append("Trace failing setup/hold timing paths and classify root causes")
        if ctx.files.sim_logs:
            tasks.append("Inspect simulation logs for assertions, mismatches and protocol failures")
        tasks.append("Generate repair suggestions, patch templates and Vivado rerun script")

        findings: list[Finding] = []
        if not ctx.files.rtl_files:
            findings.append(
                Finding(
                    agent=self.name,
                    severity="warning",
                    title="No RTL files found",
                    detail="No .v or .sv files were discovered under the project root.",
                    recommendation="Place RTL files under rtl/ or pass a project root that contains source files.",
                )
            )
        if not ctx.files.timing_reports:
            findings.append(
                Finding(
                    agent=self.name,
                    severity="info",
                    title="No timing report found",
                    detail="Timing analysis will be limited to structural RTL and XDC checks.",
                    recommendation="Export report_timing_summary and report_timing from Vivado into a reports/ directory.",
                )
            )

        return AgentResult(
            name=self.name,
            summary=f"Planned {len(tasks)} analysis tasks.",
            findings=findings,
            data={"tasks": tasks},
        )
