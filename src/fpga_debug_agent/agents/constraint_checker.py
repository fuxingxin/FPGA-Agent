from __future__ import annotations

import re

from fpga_debug_agent.agents.base import Agent
from fpga_debug_agent.models import AgentResult, Finding, RunContext
from fpga_debug_agent.parsers.xdc import parse_xdc_files


class ConstraintCheckerAgent(Agent):
    name = "constraint_checker"

    def run(self, ctx: RunContext) -> AgentResult:
        xdc_files = parse_xdc_files(ctx.files.xdc_files)
        findings: list[Finding] = []
        rtl_data = ctx.shared.get("rtl_parser", {})
        rtl_clocks = set(rtl_data.get("clocks", []))

        all_clocks = [cmd for xdc in xdc_files for cmd in xdc.clocks]
        all_generated = [cmd for xdc in xdc_files for cmd in xdc.generated_clocks]
        all_input_delays = [cmd for xdc in xdc_files for cmd in xdc.input_delays]
        all_clock_groups = [cmd for xdc in xdc_files for cmd in xdc.clock_groups]

        if rtl_clocks and not all_clocks:
            findings.append(
                Finding(
                    agent=self.name,
                    severity="error",
                    title="RTL clock signals found but no create_clock constraints detected",
                    detail=f"RTL clocks include {sorted(rtl_clocks)} but XDC has no primary clock definition.",
                    recommendation="Add create_clock constraints for all board or source-synchronous clocks before timing signoff.",
                )
            )

        constrained_names = set()
        for cmd in all_clocks + all_generated:
            name_match = re.search(r"-name\s+(\S+)", cmd.args)
            if name_match:
                constrained_names.add(name_match.group(1).strip("{}[]"))
            port_match = re.search(r"get_ports\s+\{?([A-Za-z_]\w*)\}?", cmd.args)
            if port_match:
                constrained_names.add(port_match.group(1))

        for clk in sorted(rtl_clocks):
            if clk not in constrained_names and not any(clk in cmd.args for cmd in all_clocks + all_generated):
                findings.append(
                    Finding(
                        agent=self.name,
                        severity="warning",
                        title=f"Clock `{clk}` may be unconstrained or renamed",
                        detail="The clock was detected in RTL sequential logic, but no obvious matching create_clock or create_generated_clock was found in XDC.",
                        evidence=[f"detected RTL clock: {clk}"],
                        recommendation="Confirm that this clock is constrained directly or derived through a generated clock constraint.",
                    )
                )

        for xdc in xdc_files:
            if len(xdc.clocks) >= 2 and not xdc.clock_groups:
                findings.append(
                    Finding(
                        agent=self.name,
                        severity="warning",
                        title="Multiple clocks but no set_clock_groups constraint",
                        detail="Multiple primary clocks were found. If any are asynchronous, unconstrained CDC paths may appear as false timing violations or hide real CDC issues.",
                        file=xdc.source,
                        evidence=[f"create_clock count={len(xdc.clocks)}"],
                        recommendation="Add set_clock_groups -asynchronous between unrelated clocks; do not use false_path to hide functional CDC paths without a synchronizer.",
                    )
                )

        for cmd in all_input_delays:
            has_max = "-max" in cmd.args
            has_min = "-min" in cmd.args
            has_clock_fall = "-clock_fall" in cmd.args
            if not has_max and not has_min:
                findings.append(
                    Finding(
                        agent=self.name,
                        severity="warning",
                        title="Input delay missing explicit -max/-min split",
                        detail="DDR/source-synchronous interfaces usually need both max and min delay constraints, often with rising/falling edge variants.",
                        file=cmd.file,
                        line=cmd.line,
                        evidence=[cmd.args],
                        recommendation="Use set_input_delay -max and -min; for DDR add -clock_fall and -add_delay constraints where appropriate.",
                    )
                )
            if re.search(r"DDR|IDDR|ISERDES|lvds|data", cmd.args, re.I) and not has_clock_fall:
                findings.append(
                    Finding(
                        agent=self.name,
                        severity="info",
                        title="Potential DDR input delay without falling-edge constraint",
                        detail="The command looks like it may constrain a DDR or source-synchronous data bus, but no -clock_fall option was detected.",
                        file=cmd.file,
                        line=cmd.line,
                        evidence=[cmd.args],
                        recommendation="For DDR input buses, define both rise and fall capture windows using -clock_fall -add_delay when required by the interface timing model.",
                    )
                )

        data = {
            "xdc_files": [
                {
                    "source": x.source,
                    "create_clock": [c.__dict__ for c in x.clocks],
                    "create_generated_clock": [c.__dict__ for c in x.generated_clocks],
                    "set_input_delay": [c.__dict__ for c in x.input_delays],
                    "set_output_delay": [c.__dict__ for c in x.output_delays],
                    "set_clock_groups": [c.__dict__ for c in x.clock_groups],
                    "set_false_path": [c.__dict__ for c in x.false_paths],
                    "set_multicycle_path": [c.__dict__ for c in x.multicycle_paths],
                }
                for x in xdc_files
            ]
        }
        ctx.write_json(ctx.out_dir / "xdc_summary.json", data)
        return AgentResult(
            name=self.name,
            summary=f"Checked {len(xdc_files)} XDC files, {len(all_clocks)} primary clocks and {len(all_input_delays)} input delay commands.",
            findings=findings,
            artifacts={"xdc_summary": str(ctx.out_dir / "xdc_summary.json")},
            data=data,
        )
