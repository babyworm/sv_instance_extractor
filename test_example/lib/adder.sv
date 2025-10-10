module adder #(
  parameter WIDTH = 8
)(
  input  logic [WIDTH-1:0] a,
  input  logic [WIDTH-1:0] b,
  output logic [WIDTH-1:0] sum,
  output logic             carry
);

  assign {carry, sum} = a + b;

endmodule
