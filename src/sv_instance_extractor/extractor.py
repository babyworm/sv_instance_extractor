import os
import shutil
import sys
from collections import defaultdict
from datetime import datetime
from pathlib import Path
from typing import Dict, List, Optional, Set

from .file_searcher import FileSearcher
from .models import FileModification, ModuleInfo, Report
from .parser import SVParser
from .report_generator import ReportGenerator


class InstanceExtractor:
    def __init__(self, args):
        self.args = args
        self.modules: Dict[str, ModuleInfo] = {}
        self.report = Report(
            command=" ".join(sys.argv),
            generated_at=datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
            top_file=Path(args.input),
            search_dirs=[Path(d) for d in args.idir] if args.idir else [],
            library_dirs=[Path(d) for d in args.lib] if args.lib else [],
            include_dirs=[Path(d) for d in args.include] if args.include else [],
            output_dir=Path(args.output) if args.output else None,
            prefix=args.prefix,
        )
        self.visited_modules: Set[str] = set()
        self.module_hierarchy: Dict[str, List[str]] = defaultdict(list)

    def run(self):
        try:
            self._process_include_dirs()
            self._scan_all_modules()
            self._build_dependency_tree_from_top()

            if self.args.prefix:
                self._apply_prefix_and_copy()
            else:
                self._generate_filelists()

            self._write_report()

            print(f"\n✓ Successfully generated filelists")
            if self.report.warnings:
                print(f"⚠ {len(self.report.warnings)} warning(s)")

        except Exception as e:
            self.report.errors.append(str(e))
            print(f"✗ Error: {e}", file=sys.stderr)
            sys.exit(1)

    def _process_include_dirs(self):
        if not self.args.include:
            return

        for inc_dir in self.args.include:
            inc_path = Path(inc_dir)
            if not inc_path.exists():
                self.report.warnings.append(f"Include directory not found: {inc_dir}")
                continue

            svh_files = FileSearcher.find_svh_files(inc_path)
            self.report.include_files_list.extend(svh_files)

            sv_files = FileSearcher.find_sv_files(inc_path)
            for sv_file in sv_files:
                self._process_package_file(sv_file)

        self.report.include_files = len(self.report.include_files_list)
        self.report.package_files = len(self.report.package_files_list)

    def _process_package_file(self, sv_file: Path):
        try:
            content = sv_file.read_text(encoding="utf-8", errors="ignore")
            packages = SVParser.find_packages(content)
            if packages:
                self.report.package_files_list.append(sv_file)
                for pkg_name in packages:
                    self.modules[pkg_name] = ModuleInfo(
                        name=pkg_name, file_path=sv_file, is_package=True
                    )
        except Exception as e:
            self.report.warnings.append(f"Could not read {sv_file}: {e}")

    def _scan_all_modules(self):
        all_search_dirs = self._get_all_search_dirs()
        lib_dirs = [Path(d) for d in self.args.lib] if self.args.lib else []

        for search_dir in all_search_dirs:
            if not search_dir.exists():
                self.report.warnings.append(f"Search directory not found: {search_dir}")
                continue

            sv_files = FileSearcher.find_sv_files(search_dir)
            for sv_file in sv_files:
                self._scan_file_for_modules(sv_file, lib_dirs)

    def _get_all_search_dirs(self) -> List[Path]:
        all_search_dirs = []
        if self.args.idir:
            all_search_dirs.extend([Path(d) for d in self.args.idir])
        if self.args.lib:
            all_search_dirs.extend([Path(d) for d in self.args.lib])
        return all_search_dirs

    def _scan_file_for_modules(self, sv_file: Path, lib_dirs: List[Path]):
        try:
            content = sv_file.read_text(encoding="utf-8", errors="ignore")
            module_names = SVParser.find_modules(content)

            for mod_name in module_names:
                if mod_name not in self.modules or self.modules[mod_name].is_package:
                    is_lib = self._is_file_in_lib_dirs(sv_file, lib_dirs)
                    self.modules[mod_name] = ModuleInfo(
                        name=mod_name, file_path=sv_file, is_library=is_lib
                    )
        except Exception as e:
            self.report.warnings.append(f"Could not read {sv_file}: {e}")

    def _is_file_in_lib_dirs(self, sv_file: Path, lib_dirs: List[Path]) -> bool:
        for lib_dir in lib_dirs:
            try:
                sv_file.relative_to(lib_dir)
                return True
            except ValueError:
                continue
        return False

    def _build_dependency_tree_from_top(self):
        top_file = Path(self.args.input)
        if not top_file.exists():
            raise FileNotFoundError(f"Top file not found: {top_file}")

        content = top_file.read_text(encoding="utf-8", errors="ignore")
        top_modules = SVParser.find_modules(content)
        if not top_modules:
            raise ValueError(f"No module found in top file: {top_file}")

        top_module = top_modules[0]
        self._build_dependency_tree(top_module)

    def _build_dependency_tree(self, module_name: str, parent: Optional[str] = None):
        if module_name in self.visited_modules:
            return

        if module_name not in self.modules:
            self.report.warnings.append(
                f"Module '{module_name}' not found in search paths"
            )
            return

        self.visited_modules.add(module_name)
        module_info = self.modules[module_name]

        if module_info.is_package:
            return

        try:
            content = module_info.file_path.read_text(encoding="utf-8", errors="ignore")
            instances = SVParser.find_instances(content)

            for inst_type, inst_name in instances:
                if inst_type in self.modules:
                    module_info.instances.append(inst_type)
                    self.module_hierarchy[module_name].append(inst_type)
                    self._build_dependency_tree(inst_type, module_name)
        except Exception as e:
            self.report.warnings.append(
                f"Error processing {module_info.file_path}: {e}"
            )

    def _generate_filelists(self):
        output_dir = Path(self.args.output) if self.args.output else Path.cwd()
        output_dir.mkdir(parents=True, exist_ok=True)

        list_file = output_dir / "list.f"
        lib_dir = Path(self.args.gen_lib) if self.args.gen_lib else output_dir
        lib_dir.mkdir(parents=True, exist_ok=True)
        lib_file = lib_dir / "lib.f"

        rtl_files, lib_files = self._separate_rtl_and_lib_files()
        unique_lib_files = sorted(set(lib_files))
        lib_dest_map = self._copy_lib_files_if_needed(unique_lib_files)

        self._write_list_file(
            list_file, rtl_files, unique_lib_files, lib_file, output_dir
        )

        if unique_lib_files:
            self._write_lib_file(lib_file, unique_lib_files, lib_dest_map)

        self._update_statistics(rtl_files, unique_lib_files)

    def _separate_rtl_and_lib_files(self):
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

        return rtl_files, lib_files

    def _copy_lib_files_if_needed(self, lib_files: List[Path]) -> Dict[Path, Path]:
        lib_dest_map = {}
        if lib_files and self.args.gen_lib:
            for lib_file_path in lib_files:
                dest_path = self._copy_library_to_dir(lib_file_path)
                lib_dest_map[lib_file_path] = dest_path
        else:
            for lib_file_path in lib_files:
                lib_dest_map[lib_file_path] = lib_file_path
        return lib_dest_map

    def _write_list_file(
        self,
        list_file: Path,
        rtl_files: List[Path],
        lib_files: List[Path],
        lib_file: Path,
        output_dir: Path,
    ):
        with open(list_file, "w", encoding="utf-8") as f:
            if self.report.package_files_list:
                f.write("// SystemVerilog Packages\n")
                for pkg_file in sorted(set(self.report.package_files_list)):
                    f.write(f"{pkg_file}\n")
                f.write("\n")

            if self.args.include:
                f.write("// Include Directories\n")
                for inc_dir in sorted(set(self.args.include)):
                    f.write(f"+incdir+{inc_dir}\n")
                f.write("\n")

            if rtl_files:
                f.write("// RTL Files\n")
                for rtl_file in sorted(set(rtl_files)):
                    f.write(f"{rtl_file}\n")

            if lib_files:
                f.write("\n// Library Files\n")
                try:
                    lib_reference = Path(os.path.relpath(lib_file, output_dir))
                except ValueError:
                    lib_reference = lib_file
                f.write(f"-f {lib_reference}\n")

        self.report.generated_files.append(list_file)

    def _write_lib_file(
        self, lib_file: Path, lib_files: List[Path], lib_dest_map: Dict[Path, Path]
    ):
        with open(lib_file, "w", encoding="utf-8") as f:
            f.write("// Library Files\n")
            for lib_file_path in lib_files:
                entry_path = lib_dest_map[lib_file_path]
                entry = Path(entry_path).name if self.args.gen_lib else entry_path
                f.write(f"{entry}\n")
        self.report.generated_files.append(lib_file)

    def _update_statistics(self, rtl_files: List[Path], lib_files: List[Path]):
        self.report.rtl_modules = len(
            [
                m
                for m in self.visited_modules
                if m in self.modules
                and not self.modules[m].is_library
                and not self.modules[m].is_package
            ]
        )
        self.report.library_modules = len(
            [
                m
                for m in self.visited_modules
                if m in self.modules and self.modules[m].is_library
            ]
        )
        self.report.total_modules = len(self.visited_modules)

    def _copy_library_to_dir(self, lib_file_path: Path) -> Path:
        if not self.args.gen_lib:
            return lib_file_path

        destination_dir = Path(self.args.gen_lib)
        destination_dir.mkdir(parents=True, exist_ok=True)
        destination = destination_dir / lib_file_path.name
        shutil.copy2(lib_file_path, destination)
        return destination

    def _apply_prefix_and_copy(self):
        output_dir = (
            Path(self.args.output) if self.args.output else Path("./output_rtl")
        )
        output_dir.mkdir(parents=True, exist_ok=True)

        lib_dir = Path(self.args.gen_lib) if self.args.gen_lib else output_dir / "lib"
        lib_dir.mkdir(parents=True, exist_ok=True)

        lib_module_renames = self._build_lib_rename_map()

        self._copy_and_rename_library_files(lib_dir, lib_module_renames)
        self._copy_and_modify_rtl_files(output_dir, lib_module_renames)
        self._copy_include_dirs_if_needed(output_dir)

        self._generate_output_filelists(output_dir, lib_dir, lib_module_renames)
        self._update_prefix_statistics(lib_module_renames)

    def _build_lib_rename_map(self) -> Dict[str, str]:
        lib_module_renames = {}
        prefix = self.args.prefix

        for mod_name in self.visited_modules:
            if mod_name in self.modules:
                mod_info = self.modules[mod_name]
                if mod_info.is_library:
                    new_name = f"{prefix}_{mod_name}"
                    lib_module_renames[mod_name] = new_name
                    mod_info.renamed_to = new_name

        return lib_module_renames

    def _copy_and_rename_library_files(
        self, lib_dir: Path, lib_module_renames: Dict[str, str]
    ):
        for mod_name, new_name in lib_module_renames.items():
            mod_info = self.modules[mod_name]
            try:
                content = mod_info.file_path.read_text(
                    encoding="utf-8", errors="ignore"
                )
                modified_content = SVParser.replace_module_name(
                    content, mod_name, new_name
                )

                new_filename = f"{new_name}.sv"
                output_path = lib_dir / new_filename
                output_path.write_text(modified_content, encoding="utf-8")

                mod_info.output_path = output_path

                file_mod = FileModification(
                    original_path=mod_info.file_path,
                    output_path=output_path,
                    status="renamed",
                    modifications=[f"Module renamed: {mod_name} -> {new_name}"],
                )
                self.report.file_modifications.append(file_mod)
                self.report.library_modules_info.append(mod_info)

            except Exception as e:
                self.report.errors.append(
                    f"Error processing library module {mod_name}: {e}"
                )

    def _copy_and_modify_rtl_files(
        self, output_dir: Path, lib_module_renames: Dict[str, str]
    ):
        search_dirs = [Path(d) for d in self.args.idir] if self.args.idir else []

        for mod_name in self.visited_modules:
            if mod_name not in self.modules or self.modules[mod_name].is_library:
                continue

            mod_info = self.modules[mod_name]
            if mod_info.is_package:
                continue

            output_path = self._find_output_path_for_module(
                mod_info, search_dirs, output_dir
            )
            if output_path is None:
                continue

            self._copy_and_modify_single_rtl_file(
                mod_info, output_path, lib_module_renames
            )

    def _find_output_path_for_module(
        self, mod_info: ModuleInfo, search_dirs: List[Path], output_dir: Path
    ) -> Optional[Path]:
        for search_dir in search_dirs:
            try:
                relative_path = mod_info.file_path.relative_to(search_dir)
                return output_dir / relative_path
            except ValueError:
                continue
        return None

    def _copy_and_modify_single_rtl_file(
        self,
        mod_info: ModuleInfo,
        output_path: Path,
        lib_module_renames: Dict[str, str],
    ):
        try:
            content = mod_info.file_path.read_text(encoding="utf-8", errors="ignore")
            modified = False
            modified_lines = []

            for old_name, new_name in lib_module_renames.items():
                new_content, lines = SVParser.replace_instance_type(
                    content, old_name, new_name
                )
                if lines:
                    content = new_content
                    modified = True
                    modified_lines.extend(lines)

            output_path.parent.mkdir(parents=True, exist_ok=True)
            output_path.write_text(content, encoding="utf-8")

            status = "modified" if modified else "copied"
            file_mod = FileModification(
                original_path=mod_info.file_path,
                output_path=output_path,
                status=status,
                modifications=[f"Library instance updated at lines: {modified_lines}"]
                if modified
                else [],
            )
            self.report.file_modifications.append(file_mod)

        except Exception as e:
            self.report.errors.append(f"Error copying {mod_info.file_path}: {e}")

    def _copy_include_dirs_if_needed(self, output_dir: Path):
        if not self.args.include:
            return

        inc_output = output_dir / "include"
        inc_output.mkdir(parents=True, exist_ok=True)

        for inc_dir in self.args.include:
            inc_path = Path(inc_dir)
            if inc_path.exists():
                try:
                    for item in inc_path.rglob("*"):
                        if item.is_file():
                            rel_path = item.relative_to(inc_path)
                            dest = inc_output / rel_path
                            dest.parent.mkdir(parents=True, exist_ok=True)
                            shutil.copy2(item, dest)
                except Exception as e:
                    self.report.warnings.append(
                        f"Error copying include directory {inc_dir}: {e}"
                    )

    def _generate_output_filelists(
        self, output_dir: Path, lib_dir: Path, lib_renames: Dict[str, str]
    ):
        list_file = output_dir / "list.f"
        lib_file = lib_dir / "lib.f"

        self._write_output_list_file(list_file, output_dir, lib_file)
        self._write_output_lib_file(lib_file)

        self.report.generated_files.append(list_file)
        self.report.generated_files.append(lib_file)

    def _write_output_list_file(
        self, list_file: Path, output_dir: Path, lib_file: Path
    ):
        with open(list_file, "w", encoding="utf-8") as f:
            if self.report.package_files_list:
                f.write("// SystemVerilog Packages\n")
                for pkg_file in sorted(set(self.report.package_files_list)):
                    f.write(f"{pkg_file}\n")
                f.write("\n")

            if self.args.include:
                f.write("// Include Directories\n")
                inc_output = output_dir / "include"
                f.write(f"+incdir+{inc_output}\n")
                f.write("\n")

            f.write("// RTL Files\n")
            for mod_name in self.visited_modules:
                if mod_name in self.modules:
                    mod_info = self.modules[mod_name]
                    if mod_info.is_package or mod_info.is_library:
                        continue

                    for file_mod in self.report.file_modifications:
                        if file_mod.original_path == mod_info.file_path:
                            f.write(f"{file_mod.output_path}\n")
                            break

            f.write("\n// Library Files\n")
            try:
                lib_reference = Path(os.path.relpath(lib_file, output_dir))
            except ValueError:
                lib_reference = lib_file
            f.write(f"-f {lib_reference}\n")

    def _write_output_lib_file(self, lib_file: Path):
        with open(lib_file, "w", encoding="utf-8") as f:
            f.write("// Library Files\n")
            for mod_info in self.report.library_modules_info:
                if mod_info.output_path:
                    f.write(f"{mod_info.output_path}\n")

    def _update_prefix_statistics(self, lib_module_renames: Dict[str, str]):
        self.report.rtl_modules = len(
            [
                m
                for m in self.visited_modules
                if m in self.modules
                and not self.modules[m].is_library
                and not self.modules[m].is_package
            ]
        )
        self.report.library_modules = len(lib_module_renames)
        self.report.total_modules = len(self.visited_modules)
        self.report.files_copied = len(self.report.file_modifications)
        self.report.files_modified = len(
            [f for f in self.report.file_modifications if f.status == "modified"]
        )

    def _write_report(self):
        report_file = (
            self.args.report
            if hasattr(self.args, "report") and self.args.report
            else None
        )
        report_format = (
            self.args.report_format
            if hasattr(self.args, "report_format") and self.args.report_format
            else "text"
        )

        generator = ReportGenerator(self.report)
        report_content = generator.generate(report_format)

        if report_file:
            with open(report_file, "w", encoding="utf-8") as f:
                f.write(report_content)
            print(f"\n✓ Report generated: {report_file}")
        else:
            print("\n" + "=" * 80)
            print(report_content)
