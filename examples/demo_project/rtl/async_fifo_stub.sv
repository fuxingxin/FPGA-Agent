module async_fifo_stub #(
    parameter WIDTH = 8,
    parameter DEPTH = 16
)(
    input  wire             wr_clk,
    input  wire             rd_clk,
    input  wire             rst_n,
    input  wire             wr_en,
    input  wire [WIDTH-1:0] din,
    input  wire             rd_en,
    output reg  [WIDTH-1:0] dout,
    output wire             full,
    output wire             empty
);
    // Demo-only stub. Real designs should use gray-coded pointers or a vendor FIFO IP.
    reg [WIDTH-1:0] mem [0:DEPTH-1];
    reg [$clog2(DEPTH)-1:0] wptr;
    reg [$clog2(DEPTH)-1:0] rptr;

    always @(posedge wr_clk or negedge rst_n) begin
        if (!rst_n) begin
            wptr <= '0;
        end else if (wr_en && !full) begin
            mem[wptr] <= din;
            wptr <= wptr + 1'b1;
        end
    end

    always @(posedge rd_clk or negedge rst_n) begin
        if (!rst_n) begin
            rptr <= '0;
            dout <= '0;
        end else if (rd_en && !empty) begin
            dout <= mem[rptr];
            rptr <= rptr + 1'b1;
        end
    end

    assign full  = 1'b0;
    assign empty = 1'b0;
endmodule
