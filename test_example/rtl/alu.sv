`include "defines.svh"

module alu (
  input  logic [`DATA_WIDTH-1:0] a,
  input  logic [`DATA_WIDTH-1:0] b,
  input  logic [2:0]             op,
  output logic [`DATA_WIDTH-1:0] result,
  output logic                   overflow
);

  import common_pkg::*;

  logic [`DATA_WIDTH-1:0] add_result;
  logic                   add_carry;

  // Use library adder for addition
  adder #(.WIDTH(`DATA_WIDTH)) u_adder (
    .a(a),
    .b(b),
    .sum(add_result),
    .carry(add_carry)
  );

  always_comb begin
    case (op)
      3'b000: result = add_result;           // ADD
      3'b001: result = a - b;                // SUB
      3'b010: result = a & b;                // AND
      3'b011: result = a | b;                // OR
      3'b100: result = a ^ b;                // XOR
      3'b101: result = ~a;                   // NOT
      3'b110: result = a << b[4:0];          // SHL
      3'b111: result = a >> b[4:0];          // SHR
      default: result = '0;
    endcase
  end

  assign overflow = (op == 3'b000) ? add_carry : 1'b0;

endmodule
