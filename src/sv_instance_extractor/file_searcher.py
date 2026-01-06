import sys
from pathlib import Path
from typing import List, Optional

from .parser import SVParser


class FileSearcher:
    @staticmethod
    def find_sv_files(directory: Path, recursive: bool = True) -> List[Path]:
        files = []
        pattern = "**/*" if recursive else "*"
        for ext in [".sv", ".v"]:
            files.extend(directory.glob(f"{pattern}{ext}"))
        return sorted(files)

    @staticmethod
    def find_svh_files(directory: Path) -> List[Path]:
        return sorted(directory.glob("**/*.svh"))

    @staticmethod
    def find_module_file(module_name: str, search_dirs: List[Path]) -> Optional[Path]:
        for search_dir in search_dirs:
            sv_files = FileSearcher.find_sv_files(search_dir)
            for sv_file in sv_files:
                try:
                    content = sv_file.read_text(encoding="utf-8", errors="ignore")
                    modules = SVParser.find_modules(content)
                    if module_name in modules:
                        return sv_file
                except Exception as e:
                    print(f"Warning: Could not read {sv_file}: {e}", file=sys.stderr)
        return None
