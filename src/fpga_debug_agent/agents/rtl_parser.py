from __future__ import annotations

import re
from pathlib import Path

from fpga_debug_agent.agents.base import Agent
from fpga_debug_agent.models import AgentResult, Finding, RunContext
from fpga_debug_agent.parsers.verilog import parse_design


class RTLParserAgent(Agent):
    name = "rtl_parser"

    def run(self, ctx: RunContext) -> AgentResult:
        design = parse_design(ctx.files.rtl_files)
        findings: list[Finding] = []

        for module in design.modules:
            module_clocks = sorted({clk for block in module.always_blocks for clk in block.clocks})
            if len(module_clocks) > 1:
                findings.append(
                    Finding(
                        agent=self.name,
                        severity="warning",
                        title=f"Module `{module.name}` contains multiple clock domains",
                        detail=(
                            "The module has sequential blocks driven by more than one clock. "
                            "This can be correct, but CDC synchronizers or async FIFOs must be explicit."
                        ),
                        file=module.file,
                        line=module.line,
                        evidence=[f"clocks={module_clocks}"],
                        recommendation="Check whether signals cross between these clocks and add two-flop synchronizers or async FIFO handshakes where required.",
                    )
                )

            for block in module.always_blocks:
                if block.kind == "seq" and block.blocking_count > 0:
                    findings.append(
                        Finding(
                            agent=self.name,
                            severity="warning",
                            title="Blocking assignment inside sequential always block",
                            detail="Sequential logic usually uses nonblocking assignments to avoid simulation/synthesis mismatch.",
                            file=module.file,
                            line=block.line,
                            evidence=[f"sensitivity={block.sensitivity}", f"blocking_count={block.blocking_count}"],
                            recommendation="Replace clocked blocking assignments with <= unless the statement is a local temporary variable with a deliberate coding style.",
                        )
                    )
                if block.kind == "comb" and block.nonblocking_count > 0:
                    findings.append(
                        Finding(
                            agent=self.name,
                            severity="warning",
                            title="Nonblocking assignment inside combinational always block",
                            detail="Combinational always blocks usually use blocking assignments for deterministic evaluation order.",
                            file=module.file,
                            line=block.line,
                            evidence=[f"sensitivity={block.sensitivity}", f"nonblocking_count={block.nonblocking_count}"],
                            recommendation="Use blocking assignments in always @* or always_comb blocks and assign every output on every path.",
                        )
                    )

            if not any(re.search(r"rst|reset", port, re.I) for port in module.ports) and module.always_blocks:
                findings.append(
                    Finding(
                        agent=self.name,
                        severity="info",
                        title=f"Module `{module.name}` has sequential logic without visible reset port",
                        detail="Resetless pipelines can be valid, but control state machines and valid flags often need deterministic reset behavior.",
                        file=module.file,
                        line=module.line,
                        recommendation="Confirm whether every control register has an intentional power-up state or reset path.",
                    )
                )

        data = {
            "module_count": len(design.modules),
            "modules": [
                {
                    "name": m.name,
                    "file": m.file,
                    "line": m.line,
                    "ports": m.ports,
                    "regs": m.regs,
                    "wires": m.wires,
                    "always_blocks": [
                        {
                            "line": b.line,
                            "kind": b.kind,
                            "sensitivity": b.sensitivity,
                            "clocks": b.clocks,
                            "resets": b.resets,
                            "blocking_count": b.blocking_count,
                            "nonblocking_count": b.nonblocking_count,
                        }
                        for b in m.always_blocks
                    ],
                    "instantiations": m.instantiations,
                }
                for m in design.modules
            ],
            "clocks": sorted(design.clocks),
            "resets": sorted(design.resets),
            "potential_cdc_modules": design.potential_cdc_signals,
        }

        ctx.write_json(ctx.out_dir / "rtl_summary.json", data)
        return AgentResult(
            name=self.name,
            summary=f"Parsed {len(design.modules)} RTL modules and detected {len(design.clocks)} clock names.",
            findings=findings,
            artifacts={"rtl_summary": str(ctx.out_dir / "rtl_summary.json")},
            data=data,
        )
