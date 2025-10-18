from sv_instance_extractor import SVParser


def test_find_modules_and_packages():
    content = """
    package util_pkg;
    endpackage : util_pkg

    module top_level;
    endmodule : top_level

    module worker;
    endmodule
    """
    modules = SVParser.find_modules(content)
    packages = SVParser.find_packages(content)

    assert set(modules) == {"top_level", "worker"}
    assert packages == ["util_pkg"]


def test_find_instances_skips_keywords():
    content = """
    module demo;
      if (cond) begin end
      always_comb begin end
      adder u_add (.a(a));
      fifo u_fifo (.clk(clk));
    endmodule
    """
    instances = SVParser.find_instances(content)

    assert ("adder", "u_add") in instances
    assert ("fifo", "u_fifo") in instances
    keyword_types = {mod for mod, _ in instances if mod in {"if", "always_comb"}}
    assert not keyword_types


def test_replace_module_name_updates_endlabel():
    original = """
    module fifo_wrapper;
    endmodule : fifo_wrapper
    """
    updated = SVParser.replace_module_name(original, "fifo_wrapper", "lib_fifo_wrapper")

    assert "module lib_fifo_wrapper" in updated
    assert "endmodule : lib_fifo_wrapper" in updated


def test_replace_instance_type_does_not_touch_partial_matches():
    original = """
    module top;
      fifo_ctrl u_ctrl();
      fifo u_target();
    endmodule
    """
    updated, lines = SVParser.replace_instance_type(original, "fifo", "pref_fifo")

    assert "fifo_ctrl u_ctrl" in updated
    assert "pref_fifo u_target" in updated
    assert lines  # should report the modified line number
