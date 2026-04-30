module top_lvds_rx(
    input  wire       sys_clk,
    input  wire       clk_pix,
    input  wire       rst_n,
    input  wire [7:0] lvds_data,
    input  wire       frame_sync_async,
    output reg [15:0] pixel_sum,
    output reg        valid_out
);
    wire frame_sync_pix;
    cdc_sync_2ff u_sync_frame (
        .clk_dst(clk_pix),
        .rst_n(rst_n),
        .async_in(frame_sync_async),
        .sync_out(frame_sync_pix)
    );

    reg [7:0] d0, d1, d2, d3;
    reg [15:0] comb_a, comb_b, comb_c;

    always @(posedge clk_pix or negedge rst_n) begin
        if (!rst_n) begin
            d0 <= 8'd0;
            d1 <= 8'd0;
            d2 <= 8'd0;
            d3 <= 8'd0;
            pixel_sum <= 16'd0;
            valid_out <= 1'b0;
        end else begin
            d0 <= lvds_data;
            d1 <= d0;
            d2 <= d1;
            d3 <= d2;
            // Intentionally deep demo expression. The agent should suggest pipelining if timing fails.
            comb_a = (d0 * d1) + (d2 * d3); // deliberate blocking assignment in clocked block for demo finding
            comb_b = comb_a + {8'd0, d0} + {8'd0, d1};
            comb_c = comb_b ^ {8'd0, d2};
            pixel_sum <= comb_c + {8'd0, d3};
            valid_out <= frame_sync_pix;
        end
    end

    reg sys_toggle;
    always @(posedge sys_clk or negedge rst_n) begin
        if (!rst_n) begin
            sys_toggle <= 1'b0;
        end else begin
            sys_toggle <= ~sys_toggle;
        end
    end
endmodule
