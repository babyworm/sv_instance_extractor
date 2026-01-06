#!/usr/bin/env python3
import argparse
import sys
from pathlib import Path

_src_path = str(Path(__file__).resolve().parent / "src")
if _src_path not in sys.path:
    sys.path.insert(0, _src_path)

from sv_instance_extractor.extractor import InstanceExtractor
from sv_instance_extractor.file_searcher import FileSearcher
from sv_instance_extractor.models import FileModification, ModuleInfo, Report
from sv_instance_extractor.parser import SVParser
from sv_instance_extractor.report_generator import ReportGenerator


def create_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        description="SystemVerilog Instance Extractor - Generate filelists from module instances",
        formatter_class=argparse.RawDescriptionHelpFormatter,
    )

    parser.add_argument(
        "-i", "--input", required=True, help="Top-level SystemVerilog file"
    )

    parser.add_argument(
        "-idir",
        action="append",
        help="Module search directory (can be used multiple times)",
    )
    parser.add_argument(
        "-lib",
        action="append",
        help="Library module directory (can be used multiple times)",
    )
    parser.add_argument(
        "--include",
        action="append",
        help="Include file directory for .svh and packages (can be used multiple times)",
    )

    parser.add_argument(
        "-o",
        "--output",
        default=None,
        help="Output directory (default: current directory or ./output_rtl with --prefix)",
    )
    parser.add_argument(
        "--gen-lib", dest="gen_lib", help="Copy library files to specified directory"
    )
    parser.add_argument("--prefix", help="Add prefix to library module names")

    parser.add_argument(
        "--report", help="Generate report file (default: print to stdout)"
    )
    parser.add_argument(
        "--report-format",
        choices=["text", "json", "markdown"],
        default="text",
        help="Report format (default: text)",
    )

    return parser


def validate_args(args, parser):
    if args.prefix and not args.output:
        args.output = "./output_rtl"

    if not args.idir and not args.lib:
        parser.error("At least one of -idir or -lib must be specified")


def main():
    parser = create_parser()
    args = parser.parse_args()
    validate_args(args, parser)

    extractor = InstanceExtractor(args)
    extractor.run()


if __name__ == "__main__":
    main()
