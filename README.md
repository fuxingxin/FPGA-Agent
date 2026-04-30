# FPGA Debug Agent

A complete, runnable **multi-agent FPGA debug assistant** for Verilog/SystemVerilog projects.
It analyzes RTL, XDC constraints, Vivado timing reports and simulation logs, then generates a structured debug report, repair suggestions and a Vivado Tcl rerun script.

This repository is designed as a practical GitHub project for demonstrating an Agent/AI driven FPGA verification and timing closure workflow.

## Why this project exists

FPGA debug often requires engineers to jump between RTL source files, testbenches, waveform logs, XDC constraints, Vivado timing reports and board-level symptoms. Common issues include:

- CDC mistakes between unrelated clock domains
- async FIFO read/write boundary problems
- source-synchronous LVDS or DDR input delay mistakes
- IDDR/ISERDES and bitslip alignment issues
- negative setup/hold slack after synthesis or implementation
- simulation passes but timing or board behavior fails

This project implements a deterministic multi-agent workflow that can later be connected to an LLM provider for deeper code reasoning.

## Multi-agent architecture

The workflow is split into specialist agents:

1. **Planner Agent**
   - Discovers available project artifacts.
   - Builds the analysis plan.

2. **RTL Parser Agent**
   - Parses Verilog/SystemVerilog files.
   - Extracts modules, ports, registers, wires, always blocks, clocks, resets and multi-clock modules.
   - Detects risky coding patterns such as blocking assignments in clocked always blocks.

3. **Simulation Analyzer Agent**
   - Reads simulation logs.
   - Detects errors, warnings, assertion failures, mismatch messages and incomplete simulation termination.

4. **Timing Analyzer Agent**
   - Reads Vivado timing summary and timing path reports.
   - Extracts WNS/TNS/WHS/THS and failing setup/hold paths.
   - Classifies likely causes such as deep combinational paths or hold path risk.

5. **Constraint Checker Agent**
   - Parses XDC files.
   - Checks `create_clock`, `create_generated_clock`, `set_input_delay`, `set_output_delay`, `set_clock_groups`, `set_false_path` and `set_multicycle_path`.
   - Flags missing clock constraints and incomplete DDR/source-synchronous input delay constraints.

6. **Repair Agent**
   - Aggregates findings from all upstream agents.
   - Generates repair suggestions and reusable RTL templates such as a two-flop CDC synchronizer.

7. **Closed-loop Executor Agent**
   - Generates a Vivado Tcl script for synthesis, timing, CDC report generation and rerun.
   - Can run in dry-run mode, or call Vivado when `VIVADO_BIN` is configured.

## Quick start

```bash
git clone <your-repo-url>
cd fpga-debug-agent
python -m venv .venv
source .venv/bin/activate  # Windows: .venv\Scripts\activate
pip install -e .[dev]
```

Run the demo:

```bash
fpga-debug-agent demo --out runs/demo
```

Open the report:

```bash
cat runs/demo/debug_report.md
```

Run on your own project:

```bash
fpga-debug-agent analyze \
  --project /path/to/fpga/project \
  --top top_module_name \
  --out runs/my_project
```

The tool automatically discovers:

- `.v`, `.sv`, `.vh`, `.svh` RTL files
- `.xdc` constraint files
- timing reports containing `timing` or `slack` in the filename
- simulation logs such as `sim.log`, `xsim.log`, `questa.log`, `modelsim.log`

## Optional Vivado closed-loop execution

By default the tool only generates a Tcl script and does not run Vivado.

Create `.env` or export environment variables:

```bash
export VIVADO_BIN=/path/to/vivado
```

Then run:

```bash
fpga-debug-agent analyze \
  --project examples/demo_project \
  --top top_lvds_rx \
  --out runs/execute_demo \
  --execute
```

Generated outputs include:

- `debug_report.md`
- `rtl_summary.json`
- `xdc_summary.json`
- `timing_summary.json`
- `simulation_summary.json`
- `suggested_repairs.md`
- `cdc_sync_2ff.sv`
- `run_vivado_debug.tcl`

## Optional LLM integration

The repository works without an LLM. It uses rule-based specialist agents by default.

To connect an LLM provider, install:

```bash
pip install -e .[llm]
```

Then configure:

```bash
export OPENAI_API_KEY=your_key
export OPENAI_MODEL=gpt-4.1
```

The included `llm.py` module is intentionally isolated so that teams can replace it with a private model gateway or internal inference service.

## Example report content

The demo project intentionally contains:

- a negative setup slack path with high logic levels
- incomplete input delay constraints
- multiple clocks without an asynchronous clock group
- a blocking assignment in a clocked always block
- a simulation mismatch

The generated report therefore demonstrates the complete multi-agent chain:

```text
RTL parsing -> XDC checking -> timing path analysis -> simulation log analysis -> repair generation -> Vivado Tcl generation
```

## GitHub publishing commands

After creating an empty GitHub repository, publish this project with:

```bash
git init
git add .
git commit -m "Initial commit: multi-agent FPGA debug assistant"
git branch -M main
git remote add origin https://github.com/<your-name>/fpga-debug-agent.git
git push -u origin main
```

## Roadmap

- Parse VCD/FST waveform signal transitions.
- Map Vivado timing endpoints back to exact RTL source lines.
- Add Verilator based syntax checking.
- Add CDC structural pattern recognition for gray-coded async FIFO pointers.
- Generate real unified diff patches for selected repair classes.
- Add a web dashboard for report visualization.

## Disclaimer

This tool is an engineering assistant, not a replacement for FPGA timing signoff. Always review generated suggestions before changing RTL or constraints.
