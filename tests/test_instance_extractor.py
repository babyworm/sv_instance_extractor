import os
from argparse import Namespace
from pathlib import Path

import pytest

from sv_instance_extractor import InstanceExtractor


def _make_args(output_dir: Path, **overrides) -> Namespace:
    base = {
        "input": "test_example/rtl/top.sv",
        "idir": ["test_example/rtl"],
        "lib": ["test_example/lib"],
        "include": [],
        "output": str(output_dir),
        "prefix": None,
        "gen_lib": None,
        "report": None,
        "report_format": "text",
    }
    base.update(overrides)
    return Namespace(**base)


def test_generate_filelists_without_prefix(tmp_path):
    args = _make_args(tmp_path)
    extractor = InstanceExtractor(args)
    extractor.run()

    list_file = Path(args.output) / "list.f"
    lib_file = Path(args.output) / "lib.f"

    assert list_file.exists()
    assert lib_file.exists()

    list_content = list_file.read_text()
    assert "test_example/rtl/top.sv" in list_content
    assert "-f lib.f" in list_content


def test_generate_filelists_with_includes(tmp_path):
    args = _make_args(
        tmp_path,
        include=["test_example/include", "test_example/packages"],
    )
    extractor = InstanceExtractor(args)
    extractor.run()

    list_content = (Path(args.output) / "list.f").read_text()
    assert "test_example/packages/common_pkg.sv" in list_content
    assert "+incdir+test_example/include" in list_content
    assert "+incdir+test_example/packages" in list_content


def test_prefix_mode_creates_prefixed_library(tmp_path):
    output_dir = tmp_path / "prefixed"
    args = _make_args(
        output_dir,
        prefix="TEST",
        include=["test_example/include", "test_example/packages"],
    )
    extractor = InstanceExtractor(args)
    extractor.run()

    prefixed_lib = output_dir / "lib" / "TEST_adder.sv"
    assert prefixed_lib.exists()
    assert "module TEST_adder" in prefixed_lib.read_text()

    copied_include = output_dir / "include" / "defines.svh"
    assert copied_include.exists()

    list_content = (output_dir / "list.f").read_text()
    assert "-f lib/lib.f" in list_content


def test_gen_lib_copies_library_sources(tmp_path):
    list_dir = tmp_path / "lists"
    lib_dir = tmp_path / "libs"
    args = _make_args(list_dir, gen_lib=str(lib_dir))
    extractor = InstanceExtractor(args)
    extractor.run()

    copied_adder = lib_dir / "adder.sv"
    copied_fifo = lib_dir / "fifo.sv"
    manifest = lib_dir / "lib.f"
    list_content = (list_dir / "list.f").read_text()

    assert copied_adder.exists()
    assert copied_fifo.exists()
    assert manifest.exists()

    manifest_lines = [
        line.strip() for line in manifest.read_text().splitlines() if line.strip() and not line.startswith("//")
    ]
    assert "adder.sv" in manifest_lines
    assert "fifo.sv" in manifest_lines

    expected_ref = os.path.relpath(manifest, list_dir)
    assert f"-f {expected_ref}" in list_content


def test_prefix_with_gen_lib_uses_relative_manifest(tmp_path):
    output_dir = tmp_path / "prefixed"
    lib_dir = tmp_path / "external_lib"
    args = _make_args(
        output_dir,
        prefix="PRE",
        gen_lib=str(lib_dir),
    )
    extractor = InstanceExtractor(args)
    extractor.run()

    manifest = lib_dir / "lib.f"
    prefixed_file = lib_dir / "PRE_adder.sv"

    assert manifest.exists()
    assert prefixed_file.exists()

    manifest_lines = [
        line.strip() for line in manifest.read_text().splitlines() if line.strip() and not line.startswith("//")
    ]
    # Manifest stores absolute paths when using --gen-lib with prefix mode
    assert any("PRE_adder.sv" in line for line in manifest_lines)

    list_content = (output_dir / "list.f").read_text()
    expected_ref = os.path.relpath(manifest, output_dir)
    assert f"-f {expected_ref}" in list_content


def test_run_exits_when_top_contains_no_module(tmp_path, capsys):
    empty_top = tmp_path / "empty.sv"
    empty_top.write_text("// no module present\n")

    args = _make_args(
        tmp_path / "out",
        input=str(empty_top),
        idir=[str(tmp_path)],
        lib=None,
    )
    extractor = InstanceExtractor(args)

    with pytest.raises(SystemExit):
        extractor.run()

    captured = capsys.readouterr()
    assert "No module found" in captured.err
