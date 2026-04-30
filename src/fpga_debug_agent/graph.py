from __future__ import annotations

from pathlib import Path

from fpga_debug_agent.agents.planner import PlannerAgent
from fpga_debug_agent.agents.rtl_parser import RTLParserAgent
from fpga_debug_agent.agents.constraint_checker import ConstraintCheckerAgent
from fpga_debug_agent.agents.timing_analyzer import TimingAnalyzerAgent
from fpga_debug_agent.agents.sim_analyzer import SimulationAnalyzerAgent
from fpga_debug_agent.agents.repair_agent import RepairAgent
from fpga_debug_agent.agents.executor import ClosedLoopExecutorAgent
from fpga_debug_agent.config import Settings
from fpga_debug_agent.models import ProjectFiles, RunContext
from fpga_debug_agent.reports.markdown import render_markdown_report


class DebugGraph:
    """Deterministic multi-agent orchestration graph.

    The graph intentionally runs each specialist agent in a stable order and shares
    compact artifacts through RunContext.shared. This makes the result reproducible
    and easy to test. A production deployment can replace any agent with an LLM-backed
    implementation while keeping the same interface.
    """

    def __init__(self, settings: Settings | None = None, part: str = "xc7k325tffg900-2") -> None:
        settings = settings or Settings.from_env()
        self.agents = [
            PlannerAgent(),
            RTLParserAgent(),
            ConstraintCheckerAgent(),
            TimingAnalyzerAgent(),
            SimulationAnalyzerAgent(),
            RepairAgent(),
            ClosedLoopExecutorAgent(settings=settings, part=part),
        ]

    def run(
        self,
        project_root: str | Path,
        out_dir: str | Path,
        top: str | None = None,
        dry_run: bool = True,
    ) -> RunContext:
        files = ProjectFiles.discover(project_root)
        out = Path(out_dir).resolve()
        out.mkdir(parents=True, exist_ok=True)
        ctx = RunContext(files=files, out_dir=out, top=top, dry_run=dry_run)
        ctx.write_json(out / "input_files.json", files.to_jsonable())
        for agent in self.agents:
            result = agent.run(ctx)
            ctx.add_result(result)
        report = render_markdown_report(ctx)
        (out / "debug_report.md").write_text(report, encoding="utf-8")
        ctx.write_json(
            out / "run_results.json",
            {
                "results": [
                    {
                        "name": r.name,
                        "summary": r.summary,
                        "findings": [f.__dict__ for f in r.findings],
                        "artifacts": r.artifacts,
                        "data": r.data,
                    }
                    for r in ctx.results
                ]
            },
        )
        return ctx
