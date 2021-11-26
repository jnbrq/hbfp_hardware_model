proc execute_synthesizer {DESIGN} {
    file mkdir "RPT/$DESIGN"
    file mkdir "DB/$DESIGN"

    puts "DESIGN = $DESIGN"

    set_host_options -max_cores 8
    remove_design -designs

    set target_library "$::env(TSMC_DIR)/28nm/cln28hpm/stclib/9-track/Front_End/timing_power_noise/NLDM/tcbn28hpmbwp35_120a/tcbn28hpmbwp35ss0p81v125c.db"
    set link_library   "$::env(TSMC_DIR)/28nm/cln28hpm/stclib/9-track/Front_End/timing_power_noise/NLDM/tcbn28hpmbwp35_120a/tcbn28hpmbwp35ss0p81v125c.db"

    analyze -f verilog "HDL/$DESIGN.v" > "RPT/$DESIGN/analyze.log"
    elaborate "$DESIGN" > "RPT/$DESIGN/elaborate.log"

    create_clock -name "global_clk" -period 20.0 "clock"
    set_input_delay 0.1 -clock global_clk [all_inputs]
    set_output_delay 0.2 -clock global_clk [all_outputs]

    report_block_abstraction > "RPT/$DESIGN/report_block_abstraction.log"
    check_block_abstraction > "RPT/$DESIGN/check_block_abstraction.log"
    report_top_implementation_options > "RPT/$DESIGN/report_top_implementation_options.log"

    set_app_var power_default_toggle_rate 1.0

    set start_time [clock seconds]
    puts "==> compilation started @\[[clock format $start_time -format %H:%M:%S]\]"

    compile_ultra > "RPT/$DESIGN/compile_ultra.log"

    set end_time [clock seconds]
    puts "==> compilation finished @\[[clock format $end_time -format %H:%M:%S]\]"

    set duration [expr $end_time - $start_time]
    puts "==> Duration: [expr $duration/60] min [expr $duration % 60] sec"

    report_timing > "RPT/$DESIGN/timing.log"
    report_power -hierarchy -levels 1 > "RPT/$DESIGN/power.log"
    report_area -hierarchy > "RPT/$DESIGN/area.log"
    report_clock_gating > "RPT/$DESIGN/clock_gating.log"
    report_qor > "RPT/$DESIGN/qor.log"

    write_file -hierarchy -format ddc -output "DB/$DESIGN/mapped.ddc"

    remove_design -all
}

execute_synthesizer "$env(SYN_DESIGN)"
exit
