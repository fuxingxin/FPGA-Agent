from __future__ import annotations

from fpga_debug_agent.agents.base import Agent
from fpga_debug_agent.models import AgentResult, Finding, RunContext
from fpga_debug_agent.parsers.sim_log import parse_sim_log


class SimulationAnalyzerAgent(Agent):
    name = "simulation_analyzer"

    def run(self, ctx: RunContext) -> AgentResult:
        logs = [parse_sim_log(path) for path in ctx.files.sim_logs]
        findings: list[Finding] = []

        for log in logs:
            if not log.has_finish:
                findings.append(
                    Finding(
                        agent=self.name,
                        severity="warning",
                        title="Simulation log does not show a clean finish",
                        detail="The log may be truncated or the testbench may have stopped before reaching its expected completion condition.",
                        file=log.source,
                        recommendation="Check timeout, reset release, valid/ready handshakes and scoreboard termination conditions.",
                    )
                )
            for issue in log.issues[:30]:
                findings.append(
                    Finding(
                        agent=self.name,
                        severity="error" if issue.severity in {"error", "fatal"} else "warning",
                        title=f"Simulation {issue.severity}",
                        detail=issue.text,
                        file=log.source,
                        line=issue.line,
                        recommendation="Map the message to the corresponding testbench assertion and inspect the waveform around this timestamp.",
                    )
                )

        data = {
            "logs": [
                {
                    "source": l.source,
                    "has_finish": l.has_finish,
                    "has_fatal": l.has_fatal,
                    "issue_count": len(l.issues),
                    "issues": [i.__dict__ for i in l.issues[:100]],
                }
                for l in logs
            ]
        }
        ctx.write_json(ctx.out_dir / "simulation_summary.json", data)
        return AgentResult(
            name=self.name,
            summary=f"Parsed {len(logs)} simulation logs and found {sum(len(l.issues) for l in logs)} issues.",
            findings=findings,
            artifacts={"simulation_summary": str(ctx.out_dir / "simulation_summary.json")},
            data=data,
        )
