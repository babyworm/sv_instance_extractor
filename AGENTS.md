# Repository Guidelines

## Project Structure & Module Organization
Keep `sv_instance_extractor.py` as the single CLI entry point; break out shared helpers into private functions before introducing new modules. Place new sample designs under `test_example/` using the existing layout (`rtl/`, `lib/`, `include/`, `packages/`) so automated checks discover them. Store contributor docs beside existing `README.md` files and avoid adding build artefacts to source folders.

## Build, Test, and Development Commands
Run `python3 sv_instance_extractor.py --help` to confirm CLI changes and surface new flags. Use `python3 sv_instance_extractor.py -i test_example/rtl/top.sv -idir test_example/rtl` for a fast smoke test against the bundled RTL. Install dev tooling with `python3 -m pip install -r requirements-dev.txt` and run `pytest` for unit-level coverage. Execute `./run_tests.sh` before publishing work; it covers library mode, prefix rewriting, and report generation, writing diagnostics to `test_results/`. Point reviewers to `examples/` scripts when introducing new workflows and update them alongside CLI changes.

## Coding Style & Naming Conventions
Follow Python 3.6+ standards with 4-space indentation and no tabs. Use snake_case for functions and variables, CapWords for classes, and prefix internal helpers with `_` when not part of the public API. Prefer `pathlib.Path` over raw strings, reuse existing dataclasses, and document non-trivial routines with short docstrings. Keep CLI option names lowercase with hyphenated long flags, mirroring current argparse choices.

## Testing Guidelines
Augment `tests/` with focused pytest cases whenever a helper or edge case is introduced, and keep fixtures isolated with `tmp_path`. Expand `run_tests.sh` when adding behaviours; group new scenarios as additional numbered sections. Test names should describe behaviour (“Instance Extraction - Nested Modules”) and echo the module name in the output file assertions. Generated artefacts (`list.f`, `lib.f`, `report*`) belong in `test_results/`; clean them after bespoke experiments to avoid accidental commits. Aim to cover both success paths and failure handling (missing files, conflicting prefixes).

## Commit & Pull Request Guidelines
Write imperative, capitalised commit subjects under ~72 characters (e.g., `Add prefix guard for library renames`). Include concise bodies when context matters. For pull requests, link related issues, outline verification steps (commands run, artefacts inspected), and attach snippets of any new report output. Ensure documentation stays aligned with user-facing flags and update `README.md` when workflows change.
