# SystemVerilog Instance Extractor

A Python tool that analyzes SystemVerilog files to extract module instances and generate filelists for compilation.

## Features

- 🔍 **Automatic Module Discovery**: Scans SystemVerilog files and builds dependency trees
- 📦 **Library Support**: Separates library modules into dedicated filelists
- 📝 **Include File Handling**: Properly handles `.svh` headers and SystemVerilog packages
- 🏷️ **Prefix Support**: Renames library modules with custom prefixes to avoid naming conflicts
- 📊 **Report Generation**: Creates detailed reports in text, JSON, or Markdown format
- ⚡ **Smart Parsing**: Handles parameterized instances and multiline module declarations

## Installation

No installation required! Just ensure you have Python 3.6+ installed.

```bash
# Clone the repository
git clone <your-repo-url>
cd sv_instance_extractor

# Make the script executable (optional)
chmod +x sv_instance_extractor.py
```

## Quick Start

### Basic Usage

Generate a filelist from a top-level module:

```bash
./sv_instance_extractor.py -i top.sv -idir ./rtl
```

### With Libraries

Separate library modules into `lib.f`:

```bash
./sv_instance_extractor.py -i top.sv -idir ./rtl -lib ./ip_library
```

### With Include Files

Handle header files and packages:

```bash
./sv_instance_extractor.py -i top.sv -idir ./rtl --include ./include --include ./packages
```

### With Prefix (Module Isolation)

Rename library modules and update all instances:

```bash
./sv_instance_extractor.py -i top.sv -idir ./rtl -lib ./ip_library --prefix=IP -o ./output
```

## Command Line Options

### Required Options

| Option | Description |
|--------|-------------|
| `-i`, `--input <file>` | Top-level SystemVerilog file to analyze |

### Search Path Options

| Option | Description |
|--------|-------------|
| `-idir <dir>` | Module search directory (can be used multiple times) |
| `-lib <dir>` | Library module directory - generates separate `lib.f` (can be used multiple times) |
| `--include <dir>` | Include file directory for `.svh` headers and packages (can be used multiple times) |

### Output Options

| Option | Description |
|--------|-------------|
| `-o`, `--output <dir>` | Output directory (default: current directory, or `./output_rtl` with `--prefix`) |
| `--prefix <string>` | Add prefix to library module names (requires `-o` or uses `./output_rtl`) |

### Report Options

| Option | Description |
|--------|-------------|
| `--report <file>` | Generate report file (default: print to stdout) |
| `--report-format <fmt>` | Report format: `text` (default), `json`, or `markdown` |

## Usage Examples

### Example 1: Basic Filelist Generation

```bash
./sv_instance_extractor.py -i test_example/rtl/top.sv -idir test_example/rtl
```

**Output**: `list.f`
```
// RTL Files
test_example/rtl/top.sv
test_example/rtl/cpu_core.sv
test_example/rtl/alu.sv
test_example/rtl/register_file.sv
```

### Example 2: With Library Modules

```bash
./sv_instance_extractor.py -i test_example/rtl/top.sv \
    -idir test_example/rtl \
    -lib test_example/lib
```

**Output**: `list.f` and `lib.f`

`list.f`:
```
// RTL Files
test_example/rtl/top.sv
...

// Library Files
-f lib.f
```

`lib.f`:
```
// Library Files
test_example/lib/adder.sv
test_example/lib/fifo.sv
```

### Example 3: With Include Files

```bash
./sv_instance_extractor.py -i test_example/rtl/top.sv \
    -idir test_example/rtl \
    -lib test_example/lib \
    --include test_example/include \
    --include test_example/packages
```

**Output**: `list.f` with proper ordering
```
// SystemVerilog Packages
test_example/packages/common_pkg.sv

// Include Directories
+incdir+test_example/include
+incdir+test_example/packages

// RTL Files
...

// Library Files
-f lib.f
```

### Example 4: Module Isolation with Prefix

```bash
./sv_instance_extractor.py -i test_example/rtl/top.sv \
    -idir test_example/rtl \
    -lib test_example/lib \
    --include test_example/include \
    --include test_example/packages \
    --prefix=IP \
    -o ./isolated_design
```

**What happens**:
1. Library modules renamed: `adder` → `IP_adder`, `fifo` → `IP_fifo`
2. All RTL files updated to use new names
3. Files copied to `./isolated_design/` with proper structure
4. Include files copied to `./isolated_design/include/`
5. New filelists generated

**Original `alu.sv`**:
```systemverilog
adder #(.WIDTH(32)) u_adder (
  .a(a), .b(b), .sum(sum)
);
```

**Modified `isolated_design/alu.sv`**:
```systemverilog
IP_adder #(.WIDTH(32)) u_adder (
  .a(a), .b(b), .sum(sum)
);
```

### Example 5: Generate JSON Report

```bash
./sv_instance_extractor.py -i test_example/rtl/top.sv \
    -idir test_example/rtl \
    -lib test_example/lib \
    --report=report.json \
    --report-format=json
```

**Output**: `report.json` with complete analysis data (useful for automation)

## Output Files

### Generated Filelists

- **`list.f`**: Main filelist containing:
  1. SystemVerilog packages (from `--include` directories)
  2. `+incdir+` directives for header files
  3. RTL module files
  4. Reference to `lib.f` (if library modules exist)

- **`lib.f`**: Library filelist containing library module files

### Report Format

Reports include:
- **Summary**: Statistics, configuration, generated files
- **Details**: Module list, file modifications, warnings, errors

Available formats:
- **Text**: Human-readable console output
- **JSON**: Machine-readable for automation
- **Markdown**: Pretty documentation format

## How It Works

1. **Parse Top File**: Reads the top-level SystemVerilog file
2. **Find Instances**: Extracts all module instantiations
3. **Build Dependency Tree**: Recursively finds all required modules
4. **Scan Directories**: Searches `-idir` and `-lib` directories for module definitions
5. **Process Includes**: Handles `.svh` files and packages from `--include` directories
6. **Generate Filelists**: Creates properly ordered compilation lists
7. **Apply Transformations** (optional): Renames modules with `--prefix` and updates all instances
8. **Generate Report**: Creates detailed analysis report

## Test Example

The repository includes a complete test example:

```
test_example/
├── include/
│   └── defines.svh          # Header file
├── packages/
│   └── common_pkg.sv        # SystemVerilog package
├── lib/
│   ├── adder.sv             # Library module
│   └── fifo.sv              # Library module
└── rtl/
    ├── top.sv               # Top module
    ├── cpu_core.sv          # CPU core
    ├── alu.sv               # ALU (uses adder)
    └── register_file.sv     # Register file
```

Run the test:
```bash
./sv_instance_extractor.py -i test_example/rtl/top.sv \
    -idir test_example/rtl \
    -lib test_example/lib \
    --include test_example/include \
    --include test_example/packages
```

## Requirements

- Python 3.6 or higher
- No external dependencies (uses only Python standard library)

## Limitations

- Does not handle SystemVerilog `generate` blocks
- Does not process `` `include `` directives within files
- Parameterized modules are treated as single modules
- Does not validate SystemVerilog syntax

## Future Enhancements

See [CLAUDE.md](CLAUDE.md) for detailed specifications and planned features.

## License

[Your License Here]

## Contributing

Contributions are welcome! Please see [CLAUDE.md](CLAUDE.md) for implementation details.
