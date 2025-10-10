`include "defines.svh"

module top (
  input  logic                   clk,
  input  logic                   rst_n,
  input  logic [`DATA_WIDTH-1:0] data_in,
  output logic [`DATA_WIDTH-1:0] data_out
);

  import common_pkg::*;

  logic [`DATA_WIDTH-1:0] instruction;
  logic [`ADDR_WIDTH-1:0] pc;
  logic [`DATA_WIDTH-1:0] mem_rd_data;
  logic                   mem_wr_en;
  logic [`ADDR_WIDTH-1:0] mem_addr;
  logic [`DATA_WIDTH-1:0] mem_wr_data;

  logic                   fifo_full, fifo_empty;
  logic [`DATA_WIDTH-1:0] fifo_rd_data;

  // CPU Core instance
  cpu_core u_cpu (
    .clk(clk),
    .rst_n(rst_n),
    .instruction(instruction),
    .pc(pc),
    .mem_rd_data(mem_rd_data),
    .mem_wr_en(mem_wr_en),
    .mem_addr(mem_addr),
    .mem_wr_data(mem_wr_data)
  );

  // FIFO for output buffering (using library module)
  fifo #(
    .DEPTH(16),
    .WIDTH(`DATA_WIDTH)
  ) u_output_fifo (
    .clk(clk),
    .rst_n(rst_n),
    .wr_en(mem_wr_en),
    .wr_data(mem_wr_data),
    .full(fifo_full),
    .rd_en(!fifo_empty),
    .rd_data(fifo_rd_data),
    .empty(fifo_empty)
  );

  assign data_out = fifo_rd_data;

endmodule
