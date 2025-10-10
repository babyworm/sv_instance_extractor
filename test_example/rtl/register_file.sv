`include "defines.svh"

module register_file (
  input  logic                   clk,
  input  logic                   rst_n,
  input  logic [4:0]             rd_addr1,
  output logic [`DATA_WIDTH-1:0] rd_data1,
  input  logic [4:0]             rd_addr2,
  output logic [`DATA_WIDTH-1:0] rd_data2,
  input  logic                   wr_en,
  input  logic [4:0]             wr_addr,
  input  logic [`DATA_WIDTH-1:0] wr_data
);

  logic [`DATA_WIDTH-1:0] regs [31:0];

  always_ff @(posedge clk or negedge rst_n) begin
    if (!rst_n) begin
      for (int i = 0; i < 32; i++) begin
        regs[i] <= '0;
      end
    end else if (wr_en && wr_addr != 5'b0) begin
      regs[wr_addr] <= wr_data;
    end
  end

  assign rd_data1 = (rd_addr1 == 5'b0) ? '0 : regs[rd_addr1];
  assign rd_data2 = (rd_addr2 == 5'b0) ? '0 : regs[rd_addr2];

endmodule
