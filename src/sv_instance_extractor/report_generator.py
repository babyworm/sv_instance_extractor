import json
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from .models import Report


class ReportGenerator:
    def __init__(self, report: "Report"):
        self.report = report

    def generate(self, format_type: str) -> str:
        if format_type == "json":
            return self._generate_json()
        elif format_type == "markdown":
            return self._generate_markdown()
        else:
            return self._generate_text()

    def _generate_text(self) -> str:
        lines = []
        lines.append("=" * 80)
        lines.append("SystemVerilog Instance Extractor Report")
        lines.append("=" * 80)
        lines.append(f"Generated: {self.report.generated_at}")
        lines.append(f"Command: {self.report.command}")
        lines.append("")

        lines.append("=" * 80)
        lines.append("SUMMARY")
        lines.append("=" * 80)
        lines.append(f"Top File          : {self.report.top_file}")
        if self.report.search_dirs:
            lines.append(
                f"Search Directories: {', '.join(str(d) for d in self.report.search_dirs)}"
            )
        if self.report.library_dirs:
            lines.append(
                f"Library Directories: {', '.join(str(d) for d in self.report.library_dirs)}"
            )
        if self.report.include_dirs:
            lines.append(
                f"Include Directories: {', '.join(str(d) for d in self.report.include_dirs)}"
            )
        if self.report.output_dir:
            lines.append(f"Output Directory  : {self.report.output_dir}")
        if self.report.prefix:
            lines.append(f"Prefix Applied    : {self.report.prefix}")
        lines.append("")

        lines.append("Statistics:")
        lines.append(f"  - Total modules found    : {self.report.total_modules}")
        lines.append(f"  - RTL modules            : {self.report.rtl_modules}")
        lines.append(f"  - Library modules        : {self.report.library_modules}")
        lines.append(f"  - Include files (.svh)   : {self.report.include_files}")
        lines.append(f"  - Package files (.sv)    : {self.report.package_files}")
        if self.report.files_copied > 0:
            lines.append(f"  - Files copied           : {self.report.files_copied}")
            lines.append(f"  - Files modified         : {self.report.files_modified}")
        lines.append("")

        lines.append("Generated Files:")
        for gen_file in self.report.generated_files:
            lines.append(f"  - {gen_file}")
        lines.append("")

        if self.report.warnings:
            lines.append("=" * 80)
            lines.append("WARNINGS")
            lines.append("=" * 80)
            for warning in self.report.warnings:
                lines.append(f"  - {warning}")
            lines.append("")

        if self.report.errors:
            lines.append("=" * 80)
            lines.append("ERRORS")
            lines.append("=" * 80)
            for error in self.report.errors:
                lines.append(f"  - {error}")
            lines.append("")

        lines.append("=" * 80)
        lines.append("END OF REPORT")
        lines.append("=" * 80)

        return "\n".join(lines)

    def _generate_json(self) -> str:
        data = {
            "metadata": {
                "generated_at": self.report.generated_at,
                "command": self.report.command,
            },
            "configuration": {
                "top_file": str(self.report.top_file),
                "search_dirs": [str(d) for d in self.report.search_dirs],
                "library_dirs": [str(d) for d in self.report.library_dirs],
                "include_dirs": [str(d) for d in self.report.include_dirs],
                "output_dir": str(self.report.output_dir)
                if self.report.output_dir
                else None,
                "prefix": self.report.prefix,
            },
            "statistics": {
                "total_modules": self.report.total_modules,
                "rtl_modules": self.report.rtl_modules,
                "library_modules": self.report.library_modules,
                "include_files": self.report.include_files,
                "package_files": self.report.package_files,
                "files_copied": self.report.files_copied,
                "files_modified": self.report.files_modified,
            },
            "generated_files": [str(f) for f in self.report.generated_files],
            "warnings": self.report.warnings,
            "errors": self.report.errors,
        }
        return json.dumps(data, indent=2)

    def _generate_markdown(self) -> str:
        lines = []
        lines.append("# SystemVerilog Instance Extractor Report")
        lines.append("")
        lines.append(f"**Generated**: {self.report.generated_at}")
        lines.append(f"**Command**: `{self.report.command}`")
        lines.append("")
        lines.append("---")
        lines.append("")

        lines.append("## Summary")
        lines.append("")
        lines.append("| Item | Value |")
        lines.append("|------|-------|")
        lines.append(f"| Top File | `{self.report.top_file}` |")
        if self.report.search_dirs:
            lines.append(
                f"| Search Directories | {', '.join(f'`{d}`' for d in self.report.search_dirs)} |"
            )
        if self.report.library_dirs:
            lines.append(
                f"| Library Directories | {', '.join(f'`{d}`' for d in self.report.library_dirs)} |"
            )
        if self.report.output_dir:
            lines.append(f"| Output Directory | `{self.report.output_dir}` |")
        if self.report.prefix:
            lines.append(f"| Prefix Applied | `{self.report.prefix}` |")
        lines.append("")

        lines.append("### Statistics")
        lines.append("")
        lines.append("| Metric | Count |")
        lines.append("|--------|-------|")
        lines.append(f"| Total modules found | {self.report.total_modules} |")
        lines.append(f"| RTL modules | {self.report.rtl_modules} |")
        lines.append(f"| Library modules | {self.report.library_modules} |")
        lines.append(f"| Include files (.svh) | {self.report.include_files} |")
        lines.append(f"| Package files (.sv) | {self.report.package_files} |")
        if self.report.files_copied > 0:
            lines.append(f"| Files copied | {self.report.files_copied} |")
            lines.append(f"| Files modified | {self.report.files_modified} |")
        lines.append("")

        lines.append("### Generated Files")
        for gen_file in self.report.generated_files:
            lines.append(f"- `{gen_file}`")
        lines.append("")

        if self.report.warnings:
            lines.append("### Warnings")
            for warning in self.report.warnings:
                lines.append(f"- {warning}")
            lines.append("")

        if self.report.errors:
            lines.append("### Errors")
            for error in self.report.errors:
                lines.append(f"- {error}")
            lines.append("")
        else:
            lines.append("### Errors")
            lines.append("None")
            lines.append("")

        return "\n".join(lines)
