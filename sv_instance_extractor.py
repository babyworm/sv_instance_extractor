#!/usr/bin/env python3
"""
SystemVerilog Instance Extractor
Analyzes SystemVerilog files to extract module instances and generate filelists.
"""

import argparse
import re
import os
import sys
import json
import shutil
from pathlib import Path
from typing import Dict, List, Set, Tuple, Optional
from dataclasses import dataclass, field
from datetime import datetime
from collections import defaultdict


@dataclass
class ModuleInfo:
    """Information about a SystemVerilog module"""
    name: str
    file_path: Path
    instances: List[str] = field(default_factory=list)
    is_library: bool = False
    is_package: bool = False
    renamed_to: Optional[str] = None
    output_path: Optional[Path] = None


@dataclass
class FileModification:
    """Track file modifications"""
    original_path: Path
    output_path: Path
    status: str  # 'copied', 'modified', 'renamed'
    modifications: List[str] = field(default_factory=list)


@dataclass
class Report:
    """Report data structure"""
    command: str
    generated_at: str
    top_file: Path
    search_dirs: List[Path]
    library_dirs: List[Path]
    include_dirs: List[Path]
    output_dir: Optional[Path]
    prefix: Optional[str]

    # Statistics
    total_modules: int = 0
    rtl_modules: int = 0
    library_modules: int = 0
    include_files: int = 0
    package_files: int = 0
    files_copied: int = 0
    files_modified: int = 0

    # Details
    modules: Dict[str, ModuleInfo] = field(default_factory=dict)
    library_modules_info: List[ModuleInfo] = field(default_factory=list)
    include_files_list: List[Path] = field(default_factory=list)
    package_files_list: List[Path] = field(default_factory=list)
    file_modifications: List[FileModification] = field(default_factory=list)
    warnings: List[str] = field(default_factory=list)
    errors: List[str] = field(default_factory=list)
    generated_files: List[Path] = field(default_factory=list)


class SVParser:
    """SystemVerilog parser for modules, packages, and instances"""

    # Regex patterns
    MODULE_DEF_PATTERN = re.compile(r'^\s*module\s+(\w+)', re.MULTILINE)
    PACKAGE_DEF_PATTERN = re.compile(r'^\s*package\s+(\w+)', re.MULTILINE)
    # Match module instances with optional parameters (can span multiple lines)
    # Pattern: module_type [#(params)] instance_name (
    INSTANCE_PATTERN = re.compile(
        r'^\s*(\w+)\s+'                         # module type
        r'(?:#\s*\((?:[^()]*|\([^()]*\))*\)\s*)?'  # optional parameters (including nested parens)
        r'(\w+)\s*\(',                          # instance name
        re.MULTILINE | re.DOTALL
    )

    @staticmethod
    def find_modules(content: str) -> List[str]:
        """Find all module definitions in content"""
        return SVParser.MODULE_DEF_PATTERN.findall(content)

    @staticmethod
    def find_packages(content: str) -> List[str]:
        """Find all package definitions in content"""
        return SVParser.PACKAGE_DEF_PATTERN.findall(content)

    @staticmethod
    def find_instances(content: str) -> List[Tuple[str, str]]:
        """Find all module instances in content (module_type, instance_name)"""
        instances = []
        for match in SVParser.INSTANCE_PATTERN.finditer(content):
            module_type = match.group(1)
            instance_name = match.group(2)
            # Filter out SystemVerilog keywords and definition keywords
            if module_type not in ['if', 'for', 'case', 'while', 'begin', 'end',
                                   'initial', 'always', 'always_comb', 'always_ff',
                                   'module', 'package', 'interface', 'function', 'task',
                                   'property', 'sequence', 'covergroup', 'class']:
                instances.append((module_type, instance_name))
        return instances

    @staticmethod
    def replace_module_name(content: str, old_name: str, new_name: str) -> str:
        """Replace module name in module definition"""
        module_pattern = re.compile(r'(\bmodule\s+)' + re.escape(old_name) + r'(\b)')
        endmodule_pattern = re.compile(r'(endmodule\s*:?\s*)' + re.escape(old_name) + r'\b')

        content = module_pattern.sub(r'\1' + new_name + r'\2', content)
        content = endmodule_pattern.sub(lambda m: m.group(1) + new_name, content)
        return content

    @staticmethod
    def replace_instance_type(content: str, old_type: str, new_type: str) -> Tuple[str, List[int]]:
        """Replace module instance type and return modified content and line numbers"""
        lines = content.split('\n')
        modified_lines = []
        pattern = re.compile(r'\b' + re.escape(old_type) + r'\b')

        for i, line in enumerate(lines, 1):
            if pattern.search(line):
                modified_lines.append(i)
                line = pattern.sub(new_type, line)
            lines[i-1] = line

        return '\n'.join(lines), modified_lines


class FileSearcher:
    """Search for SystemVerilog files in directories"""

    @staticmethod
    def find_sv_files(directory: Path, recursive: bool = True) -> List[Path]:
        """Find all .sv and .v files in directory"""
        files = []
        pattern = '**/*' if recursive else '*'
        for ext in ['.sv', '.v']:
            files.extend(directory.glob(f'{pattern}{ext}'))
        return sorted(files)

    @staticmethod
    def find_svh_files(directory: Path) -> List[Path]:
        """Find all .svh files in directory"""
        return sorted(directory.glob('**/*.svh'))

    @staticmethod
    def find_module_file(module_name: str, search_dirs: List[Path]) -> Optional[Path]:
        """Find file containing module definition"""
        for search_dir in search_dirs:
            sv_files = FileSearcher.find_sv_files(search_dir)
            for sv_file in sv_files:
                try:
                    content = sv_file.read_text(encoding='utf-8', errors='ignore')
                    modules = SVParser.find_modules(content)
                    if module_name in modules:
                        return sv_file
                except Exception as e:
                    print(f"Warning: Could not read {sv_file}: {e}", file=sys.stderr)
        return None


class InstanceExtractor:
    """Main class for extracting instances and generating filelists"""

    def __init__(self, args):
        self.args = args
        self.modules: Dict[str, ModuleInfo] = {}
        self.report = Report(
            command=' '.join(sys.argv),
            generated_at=datetime.now().strftime('%Y-%m-%d %H:%M:%S'),
            top_file=Path(args.input),
            search_dirs=[Path(d) for d in args.idir] if args.idir else [],
            library_dirs=[Path(d) for d in args.lib] if args.lib else [],
            include_dirs=[Path(d) for d in args.include] if args.include else [],
            output_dir=Path(args.output) if args.output else None,
            prefix=args.prefix
        )
        self.visited_modules: Set[str] = set()
        self.module_hierarchy: Dict[str, List[str]] = defaultdict(list)

    def run(self):
        """Main execution flow"""
        try:
            # Step 1: Process include directories
            self._process_include_dirs()

            # Step 2: Find all modules in search directories
            self._scan_all_modules()

            # Step 3: Build dependency tree from top file
            top_file = Path(self.args.input)
            if not top_file.exists():
                raise FileNotFoundError(f"Top file not found: {top_file}")

            content = top_file.read_text(encoding='utf-8', errors='ignore')
            top_modules = SVParser.find_modules(content)
            if not top_modules:
                raise ValueError(f"No module found in top file: {top_file}")

            top_module = top_modules[0]
            self._build_dependency_tree(top_module)

            # Step 4: Generate filelists
            if self.args.prefix:
                self._apply_prefix_and_copy()
            else:
                self._generate_filelists()

            # Step 5: Generate report
            self._generate_report()

            print(f"\n✓ Successfully generated filelists")
            if self.report.warnings:
                print(f"⚠ {len(self.report.warnings)} warning(s)")

        except Exception as e:
            self.report.errors.append(str(e))
            print(f"✗ Error: {e}", file=sys.stderr)
            sys.exit(1)

    def _process_include_dirs(self):
        """Process include directories for .svh and package files"""
        if not self.args.include:
            return

        for inc_dir in self.args.include:
            inc_path = Path(inc_dir)
            if not inc_path.exists():
                self.report.warnings.append(f"Include directory not found: {inc_dir}")
                continue

            # Find .svh files
            svh_files = FileSearcher.find_svh_files(inc_path)
            self.report.include_files_list.extend(svh_files)

            # Find package files (.sv with package definition)
            sv_files = FileSearcher.find_sv_files(inc_path)
            for sv_file in sv_files:
                try:
                    content = sv_file.read_text(encoding='utf-8', errors='ignore')
                    packages = SVParser.find_packages(content)
                    if packages:
                        self.report.package_files_list.append(sv_file)
                        for pkg_name in packages:
                            self.modules[pkg_name] = ModuleInfo(
                                name=pkg_name,
                                file_path=sv_file,
                                is_package=True
                            )
                except Exception as e:
                    self.report.warnings.append(f"Could not read {sv_file}: {e}")

        self.report.include_files = len(self.report.include_files_list)
        self.report.package_files = len(self.report.package_files_list)

    def _scan_all_modules(self):
        """Scan all search directories for modules"""
        all_search_dirs = []
        if self.args.idir:
            all_search_dirs.extend([Path(d) for d in self.args.idir])
        if self.args.lib:
            all_search_dirs.extend([Path(d) for d in self.args.lib])

        lib_dirs = [Path(d) for d in self.args.lib] if self.args.lib else []

        for search_dir in all_search_dirs:
            if not search_dir.exists():
                self.report.warnings.append(f"Search directory not found: {search_dir}")
                continue

            sv_files = FileSearcher.find_sv_files(search_dir)
            for sv_file in sv_files:
                try:
                    content = sv_file.read_text(encoding='utf-8', errors='ignore')
                    module_names = SVParser.find_modules(content)

                    for mod_name in module_names:
                        if mod_name not in self.modules or self.modules[mod_name].is_package:
                            # Check if file is in library directory
                            is_lib = False
                            for lib_dir in lib_dirs:
                                try:
                                    sv_file.relative_to(lib_dir)
                                    is_lib = True
                                    break
                                except ValueError:
                                    continue

                            self.modules[mod_name] = ModuleInfo(
                                name=mod_name,
                                file_path=sv_file,
                                is_library=is_lib
                            )
                except Exception as e:
                    self.report.warnings.append(f"Could not read {sv_file}: {e}")

    def _build_dependency_tree(self, module_name: str, parent: Optional[str] = None):
        """Recursively build dependency tree"""
        if module_name in self.visited_modules:
            return

        if module_name not in self.modules:
            self.report.warnings.append(f"Module '{module_name}' not found in search paths")
            return

        self.visited_modules.add(module_name)
        module_info = self.modules[module_name]

        # Skip packages
        if module_info.is_package:
            return

        try:
            content = module_info.file_path.read_text(encoding='utf-8', errors='ignore')
            instances = SVParser.find_instances(content)

            for inst_type, inst_name in instances:
                if inst_type in self.modules:
                    module_info.instances.append(inst_type)
                    self.module_hierarchy[module_name].append(inst_type)
                    self._build_dependency_tree(inst_type, module_name)
        except Exception as e:
            self.report.warnings.append(f"Error processing {module_info.file_path}: {e}")

    def _generate_filelists(self):
        """Generate filelists without prefix"""
        output_dir = Path(self.args.output) if self.args.output else Path.cwd()
        output_dir.mkdir(parents=True, exist_ok=True)

        # Generate main list.f
        list_file = output_dir / 'list.f'
        lib_dir = Path(self.args.gen_lib) if self.args.gen_lib else output_dir
        lib_dir.mkdir(parents=True, exist_ok=True)
        lib_file = lib_dir / 'lib.f'

        with open(list_file, 'w', encoding='utf-8') as f:
            # Write packages first
            if self.report.package_files_list:
                f.write("// SystemVerilog Packages\n")
                for pkg_file in sorted(set(self.report.package_files_list)):
                    f.write(f"{pkg_file}\n")
                f.write("\n")

            # Write include directories
            if self.args.include:
                f.write("// Include Directories\n")
                for inc_dir in sorted(set(self.args.include)):
                    f.write(f"+incdir+{inc_dir}\n")
                f.write("\n")

            # Write RTL files
            rtl_files = []
            lib_files = []

            for mod_name in self.visited_modules:
                if mod_name in self.modules:
                    mod_info = self.modules[mod_name]
                    if mod_info.is_package:
                        continue
                    if mod_info.is_library:
                        lib_files.append(mod_info.file_path)
                    else:
                        rtl_files.append(mod_info.file_path)

            unique_lib_files = sorted(set(lib_files))
            lib_dest_map = {}

            if unique_lib_files:
                if self.args.gen_lib:
                    for lib_file_path in unique_lib_files:
                        dest_path = self._copy_library_to_dir(Path(lib_file_path))
                        lib_dest_map[lib_file_path] = dest_path
                else:
                    for lib_file_path in unique_lib_files:
                        lib_dest_map[lib_file_path] = lib_file_path

            if rtl_files:
                f.write("// RTL Files\n")
                for rtl_file in sorted(set(rtl_files)):
                    f.write(f"{rtl_file}\n")

            # Reference to library file if exists
            if unique_lib_files:
                f.write("\n// Library Files\n")
                try:
                    lib_reference = Path(os.path.relpath(lib_file, output_dir))
                except ValueError:
                    lib_reference = lib_file
                f.write(f"-f {lib_reference}\n")

        self.report.generated_files.append(list_file)

        # Generate lib.f if there are library modules
        if unique_lib_files:
            with open(lib_file, 'w', encoding='utf-8') as f:
                f.write("// Library Files\n")
                for lib_file_path in unique_lib_files:
                    entry_path = lib_dest_map[lib_file_path]
                    entry = Path(entry_path).name if self.args.gen_lib else entry_path
                    f.write(f"{entry}\n")
            self.report.generated_files.append(lib_file)

        # Update statistics
        self.report.rtl_modules = len([m for m in self.visited_modules
                                       if m in self.modules and not self.modules[m].is_library
                                       and not self.modules[m].is_package])
        self.report.library_modules = len([m for m in self.visited_modules
                                          if m in self.modules and self.modules[m].is_library])
        self.report.total_modules = len(self.visited_modules)

    def _copy_library_to_dir(self, lib_file_path: Path) -> Path:
        """Copy a library file to the --gen-lib directory"""
        if not self.args.gen_lib:
            return lib_file_path

        destination_dir = Path(self.args.gen_lib)
        destination_dir.mkdir(parents=True, exist_ok=True)
        destination = destination_dir / lib_file_path.name
        shutil.copy2(lib_file_path, destination)
        return destination

    def _apply_prefix_and_copy(self):
        """Apply prefix to library modules and copy files"""
        output_dir = Path(self.args.output) if self.args.output else Path('./output_rtl')
        output_dir.mkdir(parents=True, exist_ok=True)

        lib_dir = Path(self.args.gen_lib) if self.args.gen_lib else output_dir / 'lib'
        lib_dir.mkdir(parents=True, exist_ok=True)

        prefix = self.args.prefix

        # Track which library modules need renaming
        lib_module_renames = {}

        for mod_name in self.visited_modules:
            if mod_name in self.modules:
                mod_info = self.modules[mod_name]
                if mod_info.is_library:
                    new_name = f"{prefix}_{mod_name}"
                    lib_module_renames[mod_name] = new_name
                    mod_info.renamed_to = new_name

        # Copy and modify library files
        for mod_name, new_name in lib_module_renames.items():
            mod_info = self.modules[mod_name]
            try:
                content = mod_info.file_path.read_text(encoding='utf-8', errors='ignore')
                modified_content = SVParser.replace_module_name(content, mod_name, new_name)

                # Generate new filename
                new_filename = f"{new_name}.sv"
                output_path = lib_dir / new_filename
                output_path.write_text(modified_content, encoding='utf-8')

                mod_info.output_path = output_path

                file_mod = FileModification(
                    original_path=mod_info.file_path,
                    output_path=output_path,
                    status='renamed',
                    modifications=[f"Module renamed: {mod_name} -> {new_name}"]
                )
                self.report.file_modifications.append(file_mod)
                self.report.library_modules_info.append(mod_info)

            except Exception as e:
                self.report.errors.append(f"Error processing library module {mod_name}: {e}")

        # Copy and modify RTL files
        search_dirs = [Path(d) for d in self.args.idir] if self.args.idir else []

        for mod_name in self.visited_modules:
            if mod_name not in self.modules or self.modules[mod_name].is_library:
                continue

            mod_info = self.modules[mod_name]
            if mod_info.is_package:
                continue

            # Find relative path from search directories
            relative_path = None
            for search_dir in search_dirs:
                try:
                    relative_path = mod_info.file_path.relative_to(search_dir)
                    output_path = output_dir / relative_path
                    break
                except ValueError:
                    continue

            if relative_path is None:
                # File is not in search dirs, skip
                continue

            try:
                content = mod_info.file_path.read_text(encoding='utf-8', errors='ignore')
                modified = False
                modified_lines = []

                # Replace library module instances
                for old_name, new_name in lib_module_renames.items():
                    new_content, lines = SVParser.replace_instance_type(content, old_name, new_name)
                    if lines:
                        content = new_content
                        modified = True
                        modified_lines.extend(lines)

                # Create output directory and write file
                output_path.parent.mkdir(parents=True, exist_ok=True)
                output_path.write_text(content, encoding='utf-8')

                status = 'modified' if modified else 'copied'
                file_mod = FileModification(
                    original_path=mod_info.file_path,
                    output_path=output_path,
                    status=status,
                    modifications=[f"Library instance updated at lines: {modified_lines}"] if modified else []
                )
                self.report.file_modifications.append(file_mod)

            except Exception as e:
                self.report.errors.append(f"Error copying {mod_info.file_path}: {e}")

        # Copy include directories if specified
        if self.args.include:
            inc_output = output_dir / 'include'
            inc_output.mkdir(parents=True, exist_ok=True)

            for inc_dir in self.args.include:
                inc_path = Path(inc_dir)
                if inc_path.exists():
                    try:
                        # Copy all files from include directory
                        for item in inc_path.rglob('*'):
                            if item.is_file():
                                rel_path = item.relative_to(inc_path)
                                dest = inc_output / rel_path
                                dest.parent.mkdir(parents=True, exist_ok=True)
                                shutil.copy2(item, dest)
                    except Exception as e:
                        self.report.warnings.append(f"Error copying include directory {inc_dir}: {e}")

        # Generate filelists in output directory
        self._generate_output_filelists(output_dir, lib_dir, lib_module_renames)

        # Update statistics
        self.report.rtl_modules = len([m for m in self.visited_modules
                                       if m in self.modules and not self.modules[m].is_library
                                       and not self.modules[m].is_package])
        self.report.library_modules = len(lib_module_renames)
        self.report.total_modules = len(self.visited_modules)
        self.report.files_copied = len(self.report.file_modifications)
        self.report.files_modified = len([f for f in self.report.file_modifications if f.status == 'modified'])

    def _generate_output_filelists(self, output_dir: Path, lib_dir: Path, lib_renames: Dict[str, str]):
        """Generate filelists in output directory"""
        list_file = output_dir / 'list.f'
        lib_file = lib_dir / 'lib.f'

        with open(list_file, 'w', encoding='utf-8') as f:
            # Write packages first
            if self.report.package_files_list:
                f.write("// SystemVerilog Packages\n")
                for pkg_file in sorted(set(self.report.package_files_list)):
                    f.write(f"{pkg_file}\n")
                f.write("\n")

            # Write include directories
            if self.args.include:
                f.write("// Include Directories\n")
                inc_output = output_dir / 'include'
                f.write(f"+incdir+{inc_output}\n")
                f.write("\n")

            # Write RTL files
            f.write("// RTL Files\n")
            for mod_name in self.visited_modules:
                if mod_name in self.modules:
                    mod_info = self.modules[mod_name]
                    if mod_info.is_package or mod_info.is_library:
                        continue

                    # Find output path
                    for file_mod in self.report.file_modifications:
                        if file_mod.original_path == mod_info.file_path:
                            f.write(f"{file_mod.output_path}\n")
                            break

            # Reference to library file
            f.write("\n// Library Files\n")
            try:
                lib_reference = Path(os.path.relpath(lib_file, output_dir))
            except ValueError:
                lib_reference = lib_file
            f.write(f"-f {lib_reference}\n")

        self.report.generated_files.append(list_file)

        # Generate lib.f
        with open(lib_file, 'w', encoding='utf-8') as f:
            f.write("// Library Files\n")
            for mod_info in self.report.library_modules_info:
                if mod_info.output_path:
                    f.write(f"{mod_info.output_path}\n")

        self.report.generated_files.append(lib_file)

    def _generate_report(self):
        """Generate report based on format"""
        report_file = self.args.report if hasattr(self.args, 'report') and self.args.report else None
        report_format = self.args.report_format if hasattr(self.args, 'report_format') and self.args.report_format else 'text'

        if report_format == 'json':
            report_content = self._generate_json_report()
        elif report_format == 'markdown':
            report_content = self._generate_markdown_report()
        else:
            report_content = self._generate_text_report()

        if report_file:
            with open(report_file, 'w', encoding='utf-8') as f:
                f.write(report_content)
            print(f"\n✓ Report generated: {report_file}")
        else:
            print("\n" + "="*80)
            print(report_content)

    def _generate_text_report(self) -> str:
        """Generate text format report"""
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
            lines.append(f"Search Directories: {', '.join(str(d) for d in self.report.search_dirs)}")
        if self.report.library_dirs:
            lines.append(f"Library Directories: {', '.join(str(d) for d in self.report.library_dirs)}")
        if self.report.include_dirs:
            lines.append(f"Include Directories: {', '.join(str(d) for d in self.report.include_dirs)}")
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

        return '\n'.join(lines)

    def _generate_json_report(self) -> str:
        """Generate JSON format report"""
        data = {
            "metadata": {
                "generated_at": self.report.generated_at,
                "command": self.report.command
            },
            "configuration": {
                "top_file": str(self.report.top_file),
                "search_dirs": [str(d) for d in self.report.search_dirs],
                "library_dirs": [str(d) for d in self.report.library_dirs],
                "include_dirs": [str(d) for d in self.report.include_dirs],
                "output_dir": str(self.report.output_dir) if self.report.output_dir else None,
                "prefix": self.report.prefix
            },
            "statistics": {
                "total_modules": self.report.total_modules,
                "rtl_modules": self.report.rtl_modules,
                "library_modules": self.report.library_modules,
                "include_files": self.report.include_files,
                "package_files": self.report.package_files,
                "files_copied": self.report.files_copied,
                "files_modified": self.report.files_modified
            },
            "generated_files": [str(f) for f in self.report.generated_files],
            "warnings": self.report.warnings,
            "errors": self.report.errors
        }
        return json.dumps(data, indent=2)

    def _generate_markdown_report(self) -> str:
        """Generate Markdown format report"""
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
            lines.append(f"| Search Directories | {', '.join(f'`{d}`' for d in self.report.search_dirs)} |")
        if self.report.library_dirs:
            lines.append(f"| Library Directories | {', '.join(f'`{d}`' for d in self.report.library_dirs)} |")
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
                lines.append(f"- ⚠️ {warning}")
            lines.append("")

        if self.report.errors:
            lines.append("### Errors")
            for error in self.report.errors:
                lines.append(f"- ❌ {error}")
            lines.append("")
        else:
            lines.append("### Errors")
            lines.append("✅ None")
            lines.append("")

        return '\n'.join(lines)


def main():
    parser = argparse.ArgumentParser(
        description='SystemVerilog Instance Extractor - Generate filelists from module instances',
        formatter_class=argparse.RawDescriptionHelpFormatter
    )

    # Required arguments
    parser.add_argument('-i', '--input', required=True,
                       help='Top-level SystemVerilog file')

    # Search path arguments
    parser.add_argument('-idir', action='append',
                       help='Module search directory (can be used multiple times)')
    parser.add_argument('-lib', action='append',
                       help='Library module directory (can be used multiple times)')
    parser.add_argument('--include', action='append',
                       help='Include file directory for .svh and packages (can be used multiple times)')

    # Output arguments
    parser.add_argument('-o', '--output', default=None,
                       help='Output directory (default: current directory or ./output_rtl with --prefix)')
    parser.add_argument('--gen-lib', dest='gen_lib',
                       help='Copy library files to specified directory')
    parser.add_argument('--prefix',
                       help='Add prefix to library module names')

    # Report arguments
    parser.add_argument('--report',
                       help='Generate report file (default: print to stdout)')
    parser.add_argument('--report-format', choices=['text', 'json', 'markdown'],
                       default='text',
                       help='Report format (default: text)')

    args = parser.parse_args()

    # Validation
    if args.prefix and not args.output:
        args.output = './output_rtl'

    if not args.idir and not args.lib:
        parser.error("At least one of -idir or -lib must be specified")

    # Run extractor
    extractor = InstanceExtractor(args)
    extractor.run()


if __name__ == '__main__':
    main()
