`include "defines.svh"

module cpu_core (
  input  logic                   clk,
  input  logic                   rst_n,
  input  logic [`DATA_WIDTH-1:0] instruction,
  output logic [`ADDR_WIDTH-1:0] pc,
  input  logic [`DATA_WIDTH-1:0] mem_rd_data,
  output logic                   mem_wr_en,
  output logic [`ADDR_WIDTH-1:0] mem_addr,
  output logic [`DATA_WIDTH-1:0] mem_wr_data
);

  import common_pkg::*;

  // Internal signals
  logic [`DATA_WIDTH-1:0] alu_a, alu_b, alu_result;
  logic [2:0]             alu_op;
  logic                   alu_overflow;

  logic [4:0]             reg_rd_addr1, reg_rd_addr2;
  logic [`DATA_WIDTH-1:0] reg_rd_data1, reg_rd_data2;
  logic                   reg_wr_en;
  logic [4:0]             reg_wr_addr;
  logic [`DATA_WIDTH-1:0] reg_wr_data;

  state_t current_state, next_state;

  // ALU instance
  alu u_alu (
    .a(alu_a),
    .b(alu_b),
    .op(alu_op),
    .result(alu_result),
    .overflow(alu_overflow)
  );

  // Register file instance
  register_file u_reg_file (
    .clk(clk),
    .rst_n(rst_n),
    .rd_addr1(reg_rd_addr1),
    .rd_data1(reg_rd_data1),
    .rd_addr2(reg_rd_addr2),
    .rd_data2(reg_rd_data2),
    .wr_en(reg_wr_en),
    .wr_addr(reg_wr_addr),
    .wr_data(reg_wr_data)
  );

  // PC counter
  always_ff @(posedge clk or negedge rst_n) begin
    if (!rst_n) begin
      pc <= '0;
      current_state <= STATE_IDLE;
    end else begin
      pc <= pc + 1;
      current_state <= next_state;
    end
  end

  // FSM
  always_comb begin
    next_state = current_state;
    case (current_state)
      STATE_IDLE: next_state = STATE_RUN;
      STATE_RUN:  next_state = STATE_WAIT;
      STATE_WAIT: next_state = STATE_DONE;
      STATE_DONE: next_state = STATE_IDLE;
    endcase
  end

  // Decode and execute (simplified)
  assign alu_a = reg_rd_data1;
  assign alu_b = reg_rd_data2;
  assign alu_op = instruction[2:0];
  assign reg_wr_data = alu_result;

endmodule
