module fifo #(
  parameter DEPTH = 16,
  parameter WIDTH = 8
)(
  input  logic             clk,
  input  logic             rst_n,
  input  logic             wr_en,
  input  logic [WIDTH-1:0] wr_data,
  output logic             full,
  input  logic             rd_en,
  output logic [WIDTH-1:0] rd_data,
  output logic             empty
);

  logic [WIDTH-1:0] mem [DEPTH-1:0];
  logic [$clog2(DEPTH)-1:0] wr_ptr, rd_ptr;
  logic [$clog2(DEPTH):0] count;

  always_ff @(posedge clk or negedge rst_n) begin
    if (!rst_n) begin
      wr_ptr <= '0;
      rd_ptr <= '0;
      count  <= '0;
    end else begin
      if (wr_en && !full) begin
        mem[wr_ptr] <= wr_data;
        wr_ptr <= wr_ptr + 1;
        count <= count + 1;
      end
      if (rd_en && !empty) begin
        rd_ptr <= rd_ptr + 1;
        count <= count - 1;
      end
    end
  end

  assign rd_data = mem[rd_ptr];
  assign full = (count == DEPTH);
  assign empty = (count == 0);

endmodule
