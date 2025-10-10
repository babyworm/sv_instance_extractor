package common_pkg;

  typedef enum logic [1:0] {
    STATE_IDLE,
    STATE_RUN,
    STATE_WAIT,
    STATE_DONE
  } state_t;

  typedef struct packed {
    logic [7:0] data;
    logic       valid;
  } data_bus_t;

endpackage
