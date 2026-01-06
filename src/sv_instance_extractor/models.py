"""
Data models for SystemVerilog Instance Extractor.

This module contains dataclasses that represent the core data structures
used throughout the application.
"""

from dataclasses import dataclass, field
from pathlib import Path
from typing import Dict, List, Optional


@dataclass
class ModuleInfo:
    """Information about a SystemVerilog module.

    Attributes:
        name: The module name as defined in SystemVerilog.
        file_path: Path to the file containing the module definition.
        instances: List of module types instantiated within this module.
        is_library: Whether this module comes from a library directory.
        is_package: Whether this is a SystemVerilog package (not a module).
        renamed_to: New name if prefix was applied (library modules only).
        output_path: Path where the modified file was written (prefix mode).
    """

    name: str
    file_path: Path
    instances: List[str] = field(default_factory=list)
    is_library: bool = False
    is_package: bool = False
    renamed_to: Optional[str] = None
    output_path: Optional[Path] = None


@dataclass
class FileModification:
    """Track modifications made to a file during processing.

    Attributes:
        original_path: Original file path before processing.
        output_path: Path where the modified file was written.
        status: One of 'copied', 'modified', or 'renamed'.
        modifications: List of human-readable modification descriptions.
    """

    original_path: Path
    output_path: Path
    status: str
    modifications: List[str] = field(default_factory=list)


@dataclass
class Report:
    """Complete report of an extraction run.

    Contains all metadata, statistics, and details about what was
    processed and generated.

    Attributes:
        command: The full command line that was executed.
        generated_at: Timestamp when the report was generated.
        top_file: Path to the top-level input file.
        search_dirs: List of directories searched for RTL modules.
        library_dirs: List of directories containing library modules.
        include_dirs: List of directories containing include files.
        output_dir: Directory where output files were written.
        prefix: Prefix applied to library module names (if any).
        total_modules: Total number of modules found in dependency tree.
        rtl_modules: Number of RTL (non-library) modules.
        library_modules: Number of library modules.
        include_files: Number of .svh include files found.
        package_files: Number of SystemVerilog package files found.
        files_copied: Number of files copied (prefix mode).
        files_modified: Number of files modified (prefix mode).
        modules: Dictionary of all discovered modules by name.
        library_modules_info: List of library module information.
        include_files_list: List of paths to include files.
        package_files_list: List of paths to package files.
        file_modifications: List of all file modifications made.
        warnings: List of warning messages generated during processing.
        errors: List of error messages generated during processing.
        generated_files: List of paths to files that were generated.
    """

    command: str
    generated_at: str
    top_file: Path
    search_dirs: List[Path]
    library_dirs: List[Path]
    include_dirs: List[Path]
    output_dir: Optional[Path]
    prefix: Optional[str]

    total_modules: int = 0
    rtl_modules: int = 0
    library_modules: int = 0
    include_files: int = 0
    package_files: int = 0
    files_copied: int = 0
    files_modified: int = 0

    modules: Dict[str, ModuleInfo] = field(default_factory=dict)
    library_modules_info: List[ModuleInfo] = field(default_factory=list)
    include_files_list: List[Path] = field(default_factory=list)
    package_files_list: List[Path] = field(default_factory=list)
    file_modifications: List[FileModification] = field(default_factory=list)
    warnings: List[str] = field(default_factory=list)
    errors: List[str] = field(default_factory=list)
    generated_files: List[Path] = field(default_factory=list)
