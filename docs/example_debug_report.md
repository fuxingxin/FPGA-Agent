# FPGA Multi-Agent Debug Report

Generated: 2026-04-30T02:21:23
Project root: `/mnt/data/fpga-debug-agent/examples/demo_project`
Top module: `top_lvds_rx`

## Input Summary
- RTL files: 3
- XDC files: 1
- Timing reports: 1
- Simulation logs: 1

## Agent Execution Summary
- `planner`: Planned 5 analysis tasks.
- `rtl_parser`: Parsed 3 RTL modules and detected 5 clock names.
- `constraint_checker`: Checked 1 XDC files, 2 primary clocks and 1 input delay commands.
- `timing_analyzer`: Parsed 1 timing reports and found 1 failing paths.
- `simulation_analyzer`: Parsed 1 simulation logs and found 3 issues.
- `repair_agent`: Generated 3 repair suggestions from 13 upstream findings.
- `closed_loop_executor`: Generated Vivado rerun script.

## Finding Summary
- error: 4
- warning: 8
- info: 5

### [WARNING] Module `async_fifo_stub` contains multiple clock domains
- Agent: `rtl_parser`
- Location: `/mnt/data/fpga-debug-agent/examples/demo_project/rtl/async_fifo_stub.sv`:1
- Detail: The module has sequential blocks driven by more than one clock. This can be correct, but CDC synchronizers or async FIFOs must be explicit.
  - clocks=['rd_clk', 'wr_clk']
- Recommendation: Check whether signals cross between these clocks and add two-flop synchronizers or async FIFO handshakes where required.

### [WARNING] Module `top_lvds_rx` contains multiple clock domains
- Agent: `rtl_parser`
- Location: `/mnt/data/fpga-debug-agent/examples/demo_project/rtl/top_lvds_rx.sv`:1
- Detail: The module has sequential blocks driven by more than one clock. This can be correct, but CDC synchronizers or async FIFOs must be explicit.
  - clocks=['clk_pix', 'sys_clk']
- Recommendation: Check whether signals cross between these clocks and add two-flop synchronizers or async FIFO handshakes where required.

### [WARNING] Clock `clk_dst` may be unconstrained or renamed
- Agent: `constraint_checker`
- Detail: The clock was detected in RTL sequential logic, but no obvious matching create_clock or create_generated_clock was found in XDC.
  - detected RTL clock: clk_dst
- Recommendation: Confirm that this clock is constrained directly or derived through a generated clock constraint.

### [WARNING] Clock `rd_clk` may be unconstrained or renamed
- Agent: `constraint_checker`
- Detail: The clock was detected in RTL sequential logic, but no obvious matching create_clock or create_generated_clock was found in XDC.
  - detected RTL clock: rd_clk
- Recommendation: Confirm that this clock is constrained directly or derived through a generated clock constraint.

### [WARNING] Clock `wr_clk` may be unconstrained or renamed
- Agent: `constraint_checker`
- Detail: The clock was detected in RTL sequential logic, but no obvious matching create_clock or create_generated_clock was found in XDC.
  - detected RTL clock: wr_clk
- Recommendation: Confirm that this clock is constrained directly or derived through a generated clock constraint.

### [WARNING] Multiple clocks but no set_clock_groups constraint
- Agent: `constraint_checker`
- Location: `/mnt/data/fpga-debug-agent/examples/demo_project/constrs/top.xdc`
- Detail: Multiple primary clocks were found. If any are asynchronous, unconstrained CDC paths may appear as false timing violations or hide real CDC issues.
  - create_clock count=2
- Recommendation: Add set_clock_groups -asynchronous between unrelated clocks; do not use false_path to hide functional CDC paths without a synchronizer.

### [WARNING] Input delay missing explicit -max/-min split
- Agent: `constraint_checker`
- Location: `/mnt/data/fpga-debug-agent/examples/demo_project/constrs/top.xdc`:10
- Detail: DDR/source-synchronous interfaces usually need both max and min delay constraints, often with rising/falling edge variants.
  - -clock clk_pix 0.800 [get_ports {lvds_data[*]}]
- Recommendation: Use set_input_delay -max and -min; for DDR add -clock_fall and -add_delay constraints where appropriate.

### [INFO] Potential DDR input delay without falling-edge constraint
- Agent: `constraint_checker`
- Location: `/mnt/data/fpga-debug-agent/examples/demo_project/constrs/top.xdc`:10
- Detail: The command looks like it may constrain a DDR or source-synchronous data bus, but no -clock_fall option was detected.
  - -clock clk_pix 0.800 [get_ports {lvds_data[*]}]
- Recommendation: For DDR input buses, define both rise and fall capture windows using -clock_fall -add_delay when required by the interface timing model.

### [ERROR] Negative setup slack detected
- Agent: `timing_analyzer`
- Location: `/mnt/data/fpga-debug-agent/examples/demo_project/reports/timing_summary.rpt`
- Detail: Timing summary reports WNS=-0.612 ns.
- Recommendation: Inspect the worst failing paths, reduce combinational depth, or add pipeline registers after confirming constraints are correct.

### [ERROR] Failing setup path: deep combinational path
- Agent: `timing_analyzer`
- Location: `/mnt/data/fpga-debug-agent/examples/demo_project/reports/timing_summary.rpt`
- Detail: Slack is -0.612 ns.
  - Startpoint: d0_reg[3] (rising edge-triggered cell FDRE clocked by clk_pix)
  - Endpoint: pixel_sum_reg[9] (rising edge-triggered cell FDRE clocked by clk_pix)
  - Logic levels: 9
  - Slack (VIOLATED) : -0.612ns
  - Source: d0_reg[3]/Q
  - Destination: pixel_sum_reg[9]/D
  - Startpoint: d0_reg[3] (rising edge-triggered cell FDRE clocked by clk_pix)
  - Endpoint: pixel_sum_reg[9] (rising edge-triggered cell FDRE clocked by clk_pix)
- Recommendation: Insert pipeline registers, split arithmetic/comparison logic, or retime the stage boundary.

### [WARNING] Simulation warning
- Agent: `simulation_analyzer`
- Location: `/mnt/data/fpga-debug-agent/examples/demo_project/sim/sim.log`:3
- Detail: WARNING: frame_sync observed close to clk_pix edge in demo waveform
- Recommendation: Map the message to the corresponding testbench assertion and inspect the waveform around this timestamp.

### [ERROR] Simulation error
- Agent: `simulation_analyzer`
- Location: `/mnt/data/fpga-debug-agent/examples/demo_project/sim/sim.log`:4
- Detail: ERROR: scoreboard mismatch at sample 128 expected=0x1020 actual=0x1010
- Recommendation: Map the message to the corresponding testbench assertion and inspect the waveform around this timestamp.

### [ERROR] Simulation error
- Agent: `simulation_analyzer`
- Location: `/mnt/data/fpga-debug-agent/examples/demo_project/sim/sim.log`:5
- Detail: Simulation finished with 1 error
- Recommendation: Map the message to the corresponding testbench assertion and inspect the waveform around this timestamp.

### [INFO] CDC hardening template
- Agent: `repair_agent`
- Detail: For one-bit control pulses crossing unrelated clocks, use a two-flop synchronizer plus edge detection. For multi-bit buses, use async FIFO, gray-coded counters, or a valid/ack handshake. Do not simply add false_path without a functional synchronizer.
- Recommendation: For one-bit control pulses crossing unrelated clocks, use a two-flop synchronizer plus edge detection. For multi-bit buses, use async FIFO, gray-coded counters, or a valid/ack handshake. Do not simply add false_path without a functional synchronizer.

### [INFO] Setup timing closure patch
- Agent: `repair_agent`
- Detail: Classify the failing path before editing RTL. If the constraints are correct and the path has many logic levels, split arithmetic/comparison logic across pipeline stages. Preserve valid/ready alignment by delaying sideband control signals by the same number of cycles.
- Recommendation: Classify the failing path before editing RTL. If the constraints are correct and the path has many logic levels, split arithmetic/comparison logic across pipeline stages. Preserve valid/ready alignment by delaying sideband control signals by the same number of cycles.

### [INFO] Source-synchronous IO constraint patch
- Agent: `repair_agent`
- Detail: For DDR LVDS or IDDR/ISERDES inputs, define create_clock on the forwarded clock and provide set_input_delay -max/-min for both rising and falling capture edges. Add -clock_fall and -add_delay when constraining the falling-edge data window.
- Recommendation: For DDR LVDS or IDDR/ISERDES inputs, define create_clock on the forwarded clock and provide set_input_delay -max/-min for both rising and falling capture edges. Add -clock_fall and -add_delay when constraining the falling-edge data window.

### [INFO] Vivado execution skipped
- Agent: `closed_loop_executor`
- Location: `/mnt/data/fpga-debug-agent/runs/demo/run_vivado_debug.tcl`
- Detail: A Vivado Tcl script was generated, but the run stayed in dry-run mode or VIVADO_BIN is not configured.
- Recommendation: Set VIVADO_BIN and run with --execute to enable closed-loop synthesis/report generation.


## Generated Artifacts
- `rtl_summary` from `rtl_parser`: `/mnt/data/fpga-debug-agent/runs/demo/rtl_summary.json`
- `xdc_summary` from `constraint_checker`: `/mnt/data/fpga-debug-agent/runs/demo/xdc_summary.json`
- `timing_summary` from `timing_analyzer`: `/mnt/data/fpga-debug-agent/runs/demo/timing_summary.json`
- `simulation_summary` from `simulation_analyzer`: `/mnt/data/fpga-debug-agent/runs/demo/simulation_summary.json`
- `suggested_repairs` from `repair_agent`: `/mnt/data/fpga-debug-agent/runs/demo/suggested_repairs.md`
- `cdc_sync_template` from `repair_agent`: `/mnt/data/fpga-debug-agent/runs/demo/cdc_sync_2ff.sv`
- `vivado_tcl` from `closed_loop_executor`: `/mnt/data/fpga-debug-agent/runs/demo/run_vivado_debug.tcl`
