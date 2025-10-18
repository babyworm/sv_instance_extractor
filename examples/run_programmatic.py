#!/usr/bin/env python3
"""Programmatic example using InstanceExtractor from Python code."""

from argparse import Namespace
from pathlib import Path
import sys

REPO_ROOT = Path(__file__).resolve().parent.parent
if str(REPO_ROOT) not in sys.path:
    sys.path.insert(0, str(REPO_ROOT))

from sv_instance_extractor import InstanceExtractor


def main() -> None:
    repo_root = REPO_ROOT
    output_dir = repo_root / "examples" / "output" / "programmatic"
    output_dir.mkdir(parents=True, exist_ok=True)

    args = Namespace(
        input=str(repo_root / "test_example" / "rtl" / "top.sv"),
        idir=[str(repo_root / "test_example" / "rtl")],
        lib=[str(repo_root / "test_example" / "lib")],
        include=[str(repo_root / "test_example" / "packages")],
        output=str(output_dir),
        prefix=None,
        gen_lib=None,
        report=str(output_dir / "report.md"),
        report_format="markdown",
    )

    extractor = InstanceExtractor(args)
    extractor.run()

    print("Programmatic example complete.")
    print(f"Filelist: {output_dir / 'list.f'}")
    print(f"Report:   {output_dir / 'report.md'}")


if __name__ == "__main__":
    main()
