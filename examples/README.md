# Examples

Run these scripts from the repository root to see the extractor in action:

- `examples/run_basic.sh`: Generates `list.f`/`lib.f` for the baseline design.
- `examples/run_with_prefix.sh`: Applies the `--prefix` flow and copies RTL/include files into `examples/output/prefixed/`.
- `examples/run_export_lib.sh`: Demonstrates `--gen-lib`, exporting only referenced library sources.
- `examples/run_programmatic.py`: Shows how to drive `InstanceExtractor` from Python and emit a Markdown report.

All scripts write their results under `examples/output/`. Clean up that directory if you want to rerun from a blank slate.
