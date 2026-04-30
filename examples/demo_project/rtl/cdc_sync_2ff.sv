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
