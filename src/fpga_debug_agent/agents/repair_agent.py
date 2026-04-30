from __future__ import annotations

from collections import Counter

from fpga_debug_agent.agents.base import Agent
from fpga_debug_agent.models import AgentResult, Finding, RunContext


class RepairAgent(Agent):
    name = "repair_agent"

    def run(self, ctx: RunContext) -> AgentResult:
        findings = list(ctx.all_findings())
        titles = Counter(f.title for f in findings)
        suggestions: list[str] = []
        generated_findings: list[Finding] = []

        def add(title: str, body: str) -> None:
            suggestions.append(f"## {title}\n\n{body}\n")
            generated_findings.append(
                Finding(
                    agent=self.name,
                    severity="info",
                    title=title,
                    detail=body.split("\n")[0],
                    recommendation=body,
                )
            )

        if any("Blocking assignment" in f.title for f in findings):
            add(
                "Sequential assignment cleanup patch",
                "Review clocked always blocks that use `=`. Replace with `<=` for registers, while keeping purely local temporary combinational variables separate. This reduces simulation/synthesis mismatch risk.",
            )

        if any("multiple clock" in f.title.lower() or "CDC" in f.title for f in findings):
            add(
                "CDC hardening template",
                "For one-bit control pulses crossing unrelated clocks, use a two-flop synchronizer plus edge detection. For multi-bit buses, use async FIFO, gray-coded counters, or a valid/ack handshake. Do not simply add false_path without a functional synchronizer.",
            )

        if any("Negative setup slack" in f.title or "deep combinational" in f.title for f in findings):
            add(
                "Setup timing closure patch",
                "Classify the failing path before editing RTL. If the constraints are correct and the path has many logic levels, split arithmetic/comparison logic across pipeline stages. Preserve valid/ready alignment by delaying sideband control signals by the same number of cycles.",
            )

        if any("Input delay" in f.title or "DDR" in f.title for f in findings):
            add(
                "Source-synchronous IO constraint patch",
                "For DDR LVDS or IDDR/ISERDES inputs, define create_clock on the forwarded clock and provide set_input_delay -max/-min for both rising and falling capture edges. Add -clock_fall and -add_delay when constraining the falling-edge data window.",
            )

        if not suggestions:
            add(
                "No high-confidence patch generated",
                "The current run did not detect a deterministic repair. Add a Vivado timing path report, simulation log, and the failing RTL module to enable a stronger patch proposal.",
            )

        patch_text = "\n".join(suggestions)
        template = """// Two-flop synchronizer template for one-bit CDC control signals.
module cdc_sync_2ff #(
    parameter INIT = 1'b0
)(
    input  wire clk_dst,
    input  wire rst_n,
    input  wire async_in,
    output wire sync_out
);
    reg s1, s2;
    always @(posedge clk_dst or negedge rst_n) begin
        if (!rst_n) begin
            s1 <= INIT;
            s2 <= INIT;
        end else begin
            s1 <= async_in;
            s2 <= s1;
        end
    end
    assign sync_out = s2;
endmodule
"""
        (ctx.out_dir / "suggested_repairs.md").write_text(patch_text, encoding="utf-8")
        (ctx.out_dir / "cdc_sync_2ff.sv").write_text(template, encoding="utf-8")
        return AgentResult(
            name=self.name,
            summary=f"Generated {len(suggestions)} repair suggestions from {len(findings)} upstream findings.",
            findings=generated_findings,
            artifacts={
                "suggested_repairs": str(ctx.out_dir / "suggested_repairs.md"),
                "cdc_sync_template": str(ctx.out_dir / "cdc_sync_2ff.sv"),
            },
            data={"suggestion_count": len(suggestions), "finding_title_histogram": dict(titles)},
        )
