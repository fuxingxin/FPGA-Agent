from __future__ import annotations

from fpga_debug_agent.agents.base import Agent
from fpga_debug_agent.config import Settings
from fpga_debug_agent.models import AgentResult, Finding, RunContext
from fpga_debug_agent.runners.vivado import generate_vivado_tcl, run_vivado


class ClosedLoopExecutorAgent(Agent):
    name = "closed_loop_executor"

    def __init__(self, settings: Settings | None = None, part: str = "xc7k325tffg900-2") -> None:
        self.settings = settings or Settings.from_env()
        self.part = part

    def run(self, ctx: RunContext) -> AgentResult:
        tcl = generate_vivado_tcl(
            root=ctx.files.root,
            rtl_files=ctx.files.rtl_files,
            xdc_files=ctx.files.xdc_files,
            out_dir=ctx.out_dir,
            top=ctx.top,
            part=self.part,
        )
        tcl_path = ctx.out_dir / "run_vivado_debug.tcl"
        tcl_path.write_text(tcl, encoding="utf-8")

        findings: list[Finding] = []
        data = {"tcl_path": str(tcl_path), "executed": False, "returncode": None}
        if ctx.dry_run or not self.settings.vivado_bin:
            findings.append(
                Finding(
                    agent=self.name,
                    severity="info",
                    title="Vivado execution skipped",
                    detail="A Vivado Tcl script was generated, but the run stayed in dry-run mode or VIVADO_BIN is not configured.",
                    file=str(tcl_path),
                    recommendation="Set VIVADO_BIN and run with --execute to enable closed-loop synthesis/report generation.",
                )
            )
        else:
            proc = run_vivado(self.settings.vivado_bin, tcl_path, ctx.files.root)
            data.update({"executed": True, "returncode": proc.returncode})
            log_path = ctx.out_dir / "vivado_run.log"
            log_path.write_text(proc.stdout, encoding="utf-8", errors="ignore")
            severity = "info" if proc.returncode == 0 else "error"
            findings.append(
                Finding(
                    agent=self.name,
                    severity=severity,
                    title="Vivado batch run completed" if proc.returncode == 0 else "Vivado batch run failed",
                    detail=f"Return code: {proc.returncode}. Log: {log_path}",
                    file=str(log_path),
                    recommendation="Re-run the analyzer on the newly generated timing and CDC reports to continue the closed-loop flow.",
                )
            )

        return AgentResult(
            name=self.name,
            summary="Generated Vivado rerun script." + (" Executed Vivado." if data["executed"] else ""),
            findings=findings,
            artifacts={"vivado_tcl": str(tcl_path)},
            data=data,
        )
