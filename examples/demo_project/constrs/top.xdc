create_clock -period 5.000 -name sys_clk [get_ports sys_clk]
create_clock -period 3.968 -name clk_pix [get_ports clk_pix]

set_property PACKAGE_PIN Y18 [get_ports sys_clk]
set_property IOSTANDARD LVCMOS33 [get_ports sys_clk]
set_property PACKAGE_PIN W20 [get_ports clk_pix]
set_property IOSTANDARD LVCMOS33 [get_ports clk_pix]

# Demo intentionally includes incomplete input delay to trigger constraint checker.
set_input_delay -clock clk_pix 0.800 [get_ports {lvds_data[*]}]

# For real unrelated clocks, add something like:
# set_clock_groups -asynchronous -group [get_clocks sys_clk] -group [get_clocks clk_pix]
