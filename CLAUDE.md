# SystemVerilog Instance Extractor

## Project Overview

SystemVerilog top 파일을 분석하여 인스턴스된 모듈들을 찾고, 해당 모듈의 파일들을 filelist로 생성하는 도구입니다.

## Requirements

### System Requirements

- **Python**: 3.6 이상
- **OS**: Linux, macOS, Windows (WSL)
- **Dependencies**: 없음 (Python 표준 라이브러리만 사용)

### Installation

```bash
# Repository 클론
git clone <repository-url>
cd sv_instance_extractor

# 실행 권한 부여
chmod +x sv_instance_extractor.py
chmod +x run_tests.sh

# Python 버전 확인
python3 --version  # Should be 3.6 or higher
```

### Quick Verification

설치 후 다음 명령어로 동작 확인:

```bash
# Help 메시지 확인
./sv_instance_extractor.py --help

# 테스트 실행
./run_tests.sh
```

### No Package Installation Required

이 프로젝트는 외부 패키지가 필요하지 않습니다:
- ✅ `argparse`: Python 표준 라이브러리 (argument parsing)
- ✅ `re`: Python 표준 라이브러리 (regex)
- ✅ `pathlib`: Python 표준 라이브러리 (path handling)
- ✅ `json`: Python 표준 라이브러리 (JSON output)
- ✅ `dataclasses`: Python 3.7+ 표준 라이브러리 (Python 3.6은 backport 필요)

**Python 3.6 사용 시**:
```bash
# dataclasses backport 설치 (3.6만 해당)
pip3 install dataclasses
```

**Python 3.7+ 사용 시**: 추가 설치 불필요

### Development Setup

개발 환경 설정 (선택사항):

```bash
# Virtual environment 생성 (권장)
python3 -m venv venv
source venv/bin/activate  # Linux/macOS
# or
venv\Scripts\activate     # Windows

# Code style checker (optional)
pip3 install black flake8 mypy

# Format code
black sv_instance_extractor.py

# Lint code
flake8 sv_instance_extractor.py

# Type check
mypy sv_instance_extractor.py
```

## Core Functionality

### 기본 동작
1. SystemVerilog top 파일을 입력으로 받음
2. 파일 내의 모든 module instance를 파싱
3. 지정된 디렉토리들에서 instance된 모듈의 정의 파일을 검색
4. 발견된 파일들의 filelist 생성
5. 중복 제거: 같은 모듈이 여러 번 instance되어도 filelist에는 한 번만 포함

### Library 모듈 처리
- Library로 지정된 디렉토리의 모듈들은 별도의 `lib.f` 파일로 관리
- 일반 모듈들과 구분하여 관리

### Include 파일 처리
- `--include` 디렉토리의 파일들은 특별하게 처리:
  - **`.svh` 파일**: 개별 파일로 list에 포함하지 않음. Top-level list에서 `+incdir+<dir>` 지시어로만 처리
  - **Package `.sv` 파일**: Top-level list의 맨 처음에 한 번만 포함 (중복 제거)
  - Include 디렉토리의 파일들은 모듈 검색 대상이 아님

## Command Line Options

### Required Options

| Option | Description |
|--------|-------------|
| `-i <file>` | 분석할 top-level SystemVerilog 파일 경로 |

### Search Path Options

| Option | Description |
|--------|-------------|
| `-idir <dir>` | 모듈 검색 디렉토리 (여러 번 사용 가능) |
| `-lib <dir>` | Library 모듈 디렉토리 (별도 lib.f 생성). 하위 디렉토리도 탐색해야 함. |
| `--include=<dir>` | Include 파일 디렉토리 (.svh, package .sv) (여러 번 사용 가능) |

### Output Options

| Option | Description |
|--------|-------------|
| `-o <dir>`, `--output=<dir>` | 출력 디렉토리 (기본값: `./output_rtl`) |
| `--gen-lib=<dest>` | Library 파일을 지정된 위치에 복사. Library 모듈 디렉토리에 있는 하위 디렉토리 무시하고, 하나의 디렉토리로 copy할 것 |
| `--prefix=<prefix>` | Library 모듈에 prefix 추가 |
| `--report=<file>` | 작업 결과 리포트 파일 생성 (기본값: `report.txt`). 지정하지 않으면 stdout으로 출력 |
| `--report-format=<fmt>` | 리포트 형식: `text` (기본값), `json`, `markdown` |

## Advanced Features

### 1. Include File Handling (`--include=INC_DIR`)

**목적**: SystemVerilog의 header 파일과 package를 올바르게 처리

**동작**:
- Include 디렉토리에서 `.svh`와 package `.sv` 파일을 식별
- `.svh` 파일: 개별적으로 list에 추가하지 않고 `+incdir+` 지시어만 사용
- Package `.sv` 파일: Top-level list의 최상단에 한 번만 추가

**예시**:
```bash
sv_instance_extractor -i top.sv -idir ./rtl --include ./include --include ./packages
```

**Include 디렉토리 구조**:
```
./include/
  ├── defines.svh
  ├── macros.svh
  └── config.svh

./packages/
  ├── common_pkg.sv
  └── types_pkg.sv
```

**생성되는 list.f**:
```systemverilog
// SystemVerilog packages (from --include directories)
./packages/common_pkg.sv
./packages/types_pkg.sv

// Include directories
+incdir+./include
+incdir+./packages

// RTL files
./rtl/top.sv
./rtl/module1.sv
./rtl/module2.sv
```

**처리 규칙**:
1. Package 파일 (.sv)은 다른 모듈보다 먼저 컴파일되어야 함
2. `.svh` 파일은 `include` directive로 참조되므로 직접 컴파일 대상이 아님
3. 같은 package가 여러 번 발견되어도 list에는 한 번만 포함
4. `+incdir+` 지시어는 중복 제거하여 포함

### 2. Library Generation (`--gen-lib=DEST`)

**목적**: Library 디렉토리에서 실제 사용되는 모듈만 추출하여 복사

**동작**:
- `-lib`으로 지정된 디렉토리의 모듈 중 실제 instance된 것만 선택
- `DEST` 위치에 파일들을 복사
- 복사된 파일들에 대한 `lib.f` 생성

**예시**:
```bash
sv_instance_extractor -i top.sv -idir ./rtl -lib ./library -gen-lib ./extracted_lib
```

**결과**:
```
./extracted_lib/
  ├── module1.sv
  ├── module2.sv
  └── lib.f
```

### 3. Prefix Addition (`--prefix=XXX`)

**목적**: Library 모듈에 prefix를 추가하여 naming conflict 방지

**동작**:
1. Library 모듈의 이름을 `XXX_modulename`으로 변경
2. 파일 이름도 `XXX_modulename.sv`로 변경하여 복사
3. Library 모듈을 instance하는 모든 파일에서 instance 이름 변경
4. `-idir`로 지정된 파일들도 수정하여 OUTPUT 디렉토리에 복사

**필수 조건**:
- `-o` 또는 `--output` 옵션과 함께 사용해야 함
- 지정하지 않으면 기본값 `./output_rtl` 사용

**예시**:
```bash
sv_instance_extractor -i top.sv -idir ./rtl -lib ./library --prefix=LIB -o ./output_rtl
```

**변경 예시**:

원본 library 모듈 (`adder.sv`):
```systemverilog
module adder (
  input  logic [7:0] a, b,
  output logic [7:0] sum
);
  assign sum = a + b;
endmodule
```

변경된 library 모듈 (`LIB_adder.sv`):
```systemverilog
module LIB_adder (
  input  logic [7:0] a, b,
  output logic [7:0] sum
);
  assign sum = a + b;
endmodule
```

원본 top 파일 (`top.sv`):
```systemverilog
module top;
  adder u_adder (
    .a(a),
    .b(b),
    .sum(sum)
  );
endmodule
```

변경된 top 파일 (`output_rtl/top.sv`):
```systemverilog
module top;
  LIB_adder u_adder (
    .a(a),
    .b(b),
    .sum(sum)
  );
endmodule
```

### Output Directory Structure

`--prefix` 옵션 사용 시:
```
./output_rtl/
  ├── rtl/                    # -idir의 파일들 (수정된 버전)
  │   ├── top.sv
  │   └── submodule.sv
  ├── lib/                    # Library 파일들 (prefix 적용)
  │   ├── LIB_adder.sv
  │   ├── LIB_multiplier.sv
  │   └── lib.f
  └── list.f                  # 전체 filelist
```

## Implementation Requirements

### 1. Parsing
- SystemVerilog module definition 파싱
- Module instance 파싱 (다양한 instance 문법 지원)
  - Named port connections: `module_name inst_name (.port(signal), ...);`
  - Positional port connections: `module_name inst_name (signal1, signal2, ...);`
  - Mixed connections
- Package 파일 식별
  - `package` 키워드로 시작하는 `.sv` 파일
  - Include 디렉토리에서만 검색

### 2. File Search
- 지정된 디렉토리들에서 module definition 검색
- 파일 이름과 module 이름이 다를 수 있음을 고려
- 재귀적으로 instance된 모듈들도 추적 (dependency resolution)

### 3. Duplicate Prevention
- 같은 모듈이 여러 번 instance되어도 filelist에는 한 번만 포함
- Set/Dictionary 자료구조로 중복 제거

### 4. Text Transformation (for `--prefix`)
- Module definition에서 module 이름 변경
- Module instance에서 module 타입 이름 변경
- 정규표현식 또는 parser 기반 처리

### 5. File Operations
- 디렉토리 구조 유지하며 파일 복사
- 상대 경로 처리
- 안전한 파일 쓰기 (기존 파일 덮어쓰기 방지 옵션)

### 6. Filelist Generation
- **List 구조**:
  1. SystemVerilog packages (include 디렉토리의 .sv 파일)
  2. `+incdir+` 지시어들
  3. RTL 모듈 파일들
  4. Library 파일들 (또는 `-f lib.f` 참조)
- **중복 제거**: 모든 항목은 한 번만 포함
- **경로 형식**: 상대 경로 또는 절대 경로 옵션

## Example Usage Scenarios

### Scenario 1: 기본 filelist 생성
```bash
sv_instance_extractor -i top.sv -idir ./rtl -idir ./common
```
**출력**: `list.f`

### Scenario 2: Include 디렉토리 포함
```bash
sv_instance_extractor -i top.sv -idir ./rtl --include ./include --include ./packages
```
**출력**: `list.f` (package 파일 + +incdir+ 지시어 + RTL 파일)

**list.f 내용 예시**:
```
// Packages
./packages/common_pkg.sv
./packages/types_pkg.sv

// Include directories
+incdir+./include
+incdir+./packages

// RTL files
./rtl/top.sv
./rtl/module1.sv
```

### Scenario 3: Library 분리
```bash
sv_instance_extractor -i top.sv -idir ./rtl -lib ./ip_library
```
**출력**: `list.f`, `lib.f`

### Scenario 4: Library 추출
```bash
sv_instance_extractor -i top.sv -idir ./rtl -lib ./ip_library --gen-lib ./my_lib
```
**출력**: `list.f`, `./my_lib/lib.f` + 필요한 library 파일들

### Scenario 5: Prefix를 이용한 완전한 isolation
```bash
sv_instance_extractor -i top.sv -idir ./rtl -lib ./ip_library --include ./packages --prefix=IP -o ./isolated_design
```
**출력**:
- `./isolated_design/list.f`
- `./isolated_design/lib/lib.f`
- 모든 소스 파일들이 수정되어 복사됨
- Include 디렉토리도 복사됨

## Error Handling

### 처리해야 할 에러 케이스
1. **Module not found**: Instance된 모듈의 정의를 찾을 수 없음
2. **Duplicate module definition**: 여러 파일에서 같은 이름의 모듈 정의
3. **Circular dependency**: 순환 참조 감지
4. **File I/O errors**: 읽기/쓰기 권한 문제
5. **Parse errors**: 잘못된 SystemVerilog 문법

### 권장 동작
- 명확한 에러 메시지 출력
- 가능한 경우 warning으로 처리하고 계속 진행
- Critical error는 즉시 종료

## Implementation Language Recommendations

- **Python**: 빠른 프로토타이핑, 풍부한 파일/텍스트 처리 라이브러리
- **Perl**: 텍스트 처리 강점, EDA 도구들과의 호환성
- **C++**: 성능이 중요한 경우
- **Rust**: 안전성과 성능 모두 필요한 경우

## Recommended Libraries

### Python
- `argparse`: Command-line parsing
- `pathlib`: 경로 처리
- `re`: 정규표현식
- `pyverilog` 또는 `hdlparse`: Verilog parsing (optional)

### 간단한 파싱 전략
복잡한 parser 없이도 정규표현식으로 충분히 구현 가능:
- Module definition: `^\s*module\s+(\w+)`
- Module instance: `^\s*(\w+)\s+(\w+)\s*\(`
- Package definition: `^\s*package\s+(\w+)`
- Include directive 파일: 확장자로 판단 (`.svh`)

## Testing Strategy

### Automated Test Suite

프로젝트에는 포괄적인 자동화 테스트 스크립트가 포함되어 있습니다.

#### Running Tests

```bash
# 전체 테스트 실행
./run_tests.sh

# Python으로 직접 실행
bash run_tests.sh
```

#### Test Coverage

자동화 테스트는 다음 항목들을 검증합니다:

1. **Basic Filelist Generation**
   - 단순한 module hierarchy 파싱
   - 기본 list.f 생성
   - 모든 RTL 파일 포함 여부

2. **Library Module Separation**
   - Library 모듈 식별
   - 별도 lib.f 생성
   - list.f에서 `-f lib.f` 참조

3. **Include File Handling**
   - `.svh` 파일 처리 (`+incdir+` 지시어)
   - Package 파일 최상단 배치
   - 올바른 컴파일 순서

4. **Prefix Application**
   - Library 모듈 이름 변경
   - 파일명 변경
   - Instance 참조 업데이트
   - 디렉토리 구조 복사

5. **Report Generation**
   - Text format 생성 및 검증
   - JSON format 생성 및 유효성
   - Markdown format 생성 및 검증

6. **Error Handling**
   - 존재하지 않는 파일 처리
   - 올바른 에러 메시지
   - 적절한 종료 코드

7. **Command Line Interface**
   - Help 메시지 표시
   - 옵션 파싱
   - 인자 검증

#### Test Results

테스트 실행 후 `test_results/` 디렉토리에 다음 파일들이 생성됩니다:
- `testN_output.txt`: 각 테스트의 표준 출력
- `testN_list.f`: 생성된 filelist
- `testN_lib.f`: 생성된 library filelist
- `report_testN.*`: 생성된 리포트 파일
- `output_prefix/`: Prefix 테스트 결과

### Manual Test Cases

자동화 테스트 외에 수동으로 확인해야 할 항목:

1. **Complex Instance Syntax**
   - Named port connections
   - Positional port connections
   - Mixed connections
   - Parameterized instances (single/multi-line)

2. **Deep Module Hierarchy**
   - 5단계 이상의 깊은 nesting
   - 순환 참조 감지

3. **Multiple Instance of Same Module**
   - 중복 제거 동작 확인
   - 한 번만 filelist에 포함

4. **Large Projects**
   - 100+ 모듈 프로젝트
   - 성능 측정

5. **Edge Cases**
   - 빈 파일
   - 주석만 있는 파일
   - 매우 긴 파일명/경로
   - 특수 문자 포함 경로

### Test Example Structure

```
test_example/
├── include/
│   └── defines.svh          # Header with macros
├── packages/
│   └── common_pkg.sv        # Package with types
├── lib/
│   ├── adder.sv             # Parameterized library module
│   └── fifo.sv              # Complex library module
└── rtl/
    ├── top.sv               # Top-level (uses lib modules)
    ├── cpu_core.sv          # Mid-level (uses alu, reg_file)
    ├── alu.sv               # Uses lib/adder
    └── register_file.sv     # Leaf module
```

이 구조는 다음을 테스트합니다:
- Multi-level hierarchy (3 levels)
- Library module usage
- Include files and packages
- Parameterized instances
- Multiple instances of same module

### Continuous Integration

CI/CD 환경에서 사용 가능:

```yaml
# GitHub Actions example
- name: Run Tests
  run: |
    chmod +x run_tests.sh
    ./run_tests.sh
```

### Performance Benchmarks

참고용 성능 수치:
- 소규모 프로젝트 (10 modules): < 1초
- 중규모 프로젝트 (100 modules): < 5초
- 대규모 프로젝트 (1000 modules): < 30초

## Report Generation

작업 완료 후 자동으로 리포트를 생성하여 변경 사항을 추적할 수 있습니다.

### Report Content

#### Summary Section
간략한 작업 요약 정보:
- 실행 시간 및 날짜
- 사용된 옵션들
- 처리된 파일 통계
- 발견된 모듈 통계
- 생성된 출력 파일들

#### Detail Section
상세한 작업 내역:
- 발견된 모든 모듈 목록
- 각 모듈의 파일 경로
- Instance hierarchy
- Prefix 변경 내역 (적용 시)
- 복사된 파일 목록
- Warning/Error 메시지

### Report Format Examples

#### 1. Text Format (기본)
```
================================================================================
SystemVerilog Instance Extractor Report
================================================================================
Generated: 2025-10-10 14:30:22
Command: sv_instance_extractor -i top.sv -idir ./rtl -lib ./ip --prefix=LIB -o ./output

================================================================================
SUMMARY
================================================================================
Top Module        : top
Search Directories: ./rtl
Library Directory : ./ip
Output Directory  : ./output
Prefix Applied    : LIB

Statistics:
  - Total modules found    : 45
  - RTL modules           : 38
  - Library modules       : 7
  - Include files (.svh)  : 12
  - Package files (.sv)   : 3
  - Files copied          : 45
  - Files modified        : 15

Generated Files:
  - ./output/list.f
  - ./output/lib/lib.f
  - ./output/report.txt

================================================================================
DETAILS
================================================================================

[RTL Modules] (38 modules)
  1. top                    -> ./rtl/top.sv
  2. cpu_core               -> ./rtl/cpu/cpu_core.sv
  3. alu                    -> ./rtl/cpu/alu.sv
  ...

[Library Modules] (7 modules)
  1. adder                  -> ./ip/adder.sv
     Renamed to: LIB_adder -> ./output/lib/LIB_adder.sv
     Instances modified in:
       - ./output/rtl/cpu/alu.sv (line 45)
       - ./output/rtl/cpu/multiplier.sv (line 23)

  2. fifo                   -> ./ip/memory/fifo.sv
     Renamed to: LIB_fifo  -> ./output/lib/LIB_fifo.sv
     Instances modified in:
       - ./output/rtl/bus/buffer.sv (line 67)
  ...

[Include Files] (12 files)
  - ./include/defines.svh
  - ./include/macros.svh
  ...

[Packages] (3 files)
  - ./packages/common_pkg.sv
  - ./packages/types_pkg.sv
  - ./packages/utils_pkg.sv

[Module Hierarchy]
top
├── cpu_core
│   ├── alu
│   │   ├── LIB_adder (modified)
│   │   └── LIB_multiplier (modified)
│   └── decoder
├── memory_controller
│   └── LIB_fifo (modified)
└── peripheral_bus
    └── apb_bridge

[Files Copied]
Source                          -> Destination
----------------------------------------
./rtl/top.sv                   -> ./output/rtl/top.sv (modified)
./rtl/cpu/cpu_core.sv          -> ./output/rtl/cpu/cpu_core.sv
./rtl/cpu/alu.sv               -> ./output/rtl/cpu/alu.sv (modified)
./ip/adder.sv                  -> ./output/lib/LIB_adder.sv (renamed)
./ip/memory/fifo.sv            -> ./output/lib/LIB_fifo.sv (renamed)
...

[Warnings]
  - Module 'unused_module' defined in ./rtl/old/unused.sv but never instantiated

[Errors]
  - None

================================================================================
END OF REPORT
================================================================================
```

#### 2. JSON Format
```json
{
  "metadata": {
    "generated_at": "2025-10-10T14:30:22",
    "command": "sv_instance_extractor -i top.sv -idir ./rtl -lib ./ip --prefix=LIB -o ./output",
    "tool_version": "1.0.0"
  },
  "configuration": {
    "top_file": "top.sv",
    "search_dirs": ["./rtl"],
    "library_dirs": ["./ip"],
    "include_dirs": [],
    "output_dir": "./output",
    "prefix": "LIB"
  },
  "statistics": {
    "total_modules": 45,
    "rtl_modules": 38,
    "library_modules": 7,
    "include_files": 12,
    "package_files": 3,
    "files_copied": 45,
    "files_modified": 15
  },
  "modules": {
    "rtl": [
      {
        "name": "top",
        "file": "./rtl/top.sv",
        "instances": ["cpu_core", "memory_controller", "peripheral_bus"]
      },
      {
        "name": "cpu_core",
        "file": "./rtl/cpu/cpu_core.sv",
        "instances": ["alu", "decoder"]
      }
    ],
    "library": [
      {
        "original_name": "adder",
        "renamed_name": "LIB_adder",
        "original_file": "./ip/adder.sv",
        "output_file": "./output/lib/LIB_adder.sv",
        "instances_modified": [
          {
            "file": "./output/rtl/cpu/alu.sv",
            "line": 45
          },
          {
            "file": "./output/rtl/cpu/multiplier.sv",
            "line": 23
          }
        ]
      }
    ]
  },
  "includes": {
    "header_files": [
      "./include/defines.svh",
      "./include/macros.svh"
    ],
    "packages": [
      "./packages/common_pkg.sv",
      "./packages/types_pkg.sv"
    ]
  },
  "outputs": {
    "filelists": [
      "./output/list.f",
      "./output/lib/lib.f"
    ]
  },
  "warnings": [
    "Module 'unused_module' defined in ./rtl/old/unused.sv but never instantiated"
  ],
  "errors": []
}
```

#### 3. Markdown Format
````markdown
# SystemVerilog Instance Extractor Report

**Generated**: 2025-10-10 14:30:22
**Command**: `sv_instance_extractor -i top.sv -idir ./rtl -lib ./ip --prefix=LIB -o ./output`

---

## Summary

| Item | Value |
|------|-------|
| Top Module | top |
| Search Directories | ./rtl |
| Library Directory | ./ip |
| Output Directory | ./output |
| Prefix Applied | LIB |

### Statistics

| Metric | Count |
|--------|-------|
| Total modules found | 45 |
| RTL modules | 38 |
| Library modules | 7 |
| Include files (.svh) | 12 |
| Package files (.sv) | 3 |
| Files copied | 45 |
| Files modified | 15 |

### Generated Files
- `./output/list.f`
- `./output/lib/lib.f`
- `./output/report.txt`

---

## Details

### RTL Modules (38)
1. `top` → `./rtl/top.sv`
2. `cpu_core` → `./rtl/cpu/cpu_core.sv`
3. `alu` → `./rtl/cpu/alu.sv`

### Library Modules (7)

#### 1. adder → LIB_adder
- **Original**: `./ip/adder.sv`
- **Output**: `./output/lib/LIB_adder.sv`
- **Instances modified**:
  - `./output/rtl/cpu/alu.sv` (line 45)
  - `./output/rtl/cpu/multiplier.sv` (line 23)

#### 2. fifo → LIB_fifo
- **Original**: `./ip/memory/fifo.sv`
- **Output**: `./output/lib/LIB_fifo.sv`
- **Instances modified**:
  - `./output/rtl/bus/buffer.sv` (line 67)

### Module Hierarchy
```
top
├── cpu_core
│   ├── alu
│   │   ├── LIB_adder (modified)
│   │   └── LIB_multiplier (modified)
│   └── decoder
├── memory_controller
│   └── LIB_fifo (modified)
└── peripheral_bus
    └── apb_bridge
```

### Files Copied
| Source | Destination | Status |
|--------|-------------|--------|
| `./rtl/top.sv` | `./output/rtl/top.sv` | modified |
| `./rtl/cpu/cpu_core.sv` | `./output/rtl/cpu/cpu_core.sv` | copied |
| `./rtl/cpu/alu.sv` | `./output/rtl/cpu/alu.sv` | modified |
| `./ip/adder.sv` | `./output/lib/LIB_adder.sv` | renamed |

### Warnings
- ⚠️ Module 'unused_module' defined in `./rtl/old/unused.sv` but never instantiated

### Errors
✅ None
````

### Implementation Notes

리포트 생성 시 추적해야 할 정보:
1. **실행 컨텍스트**: 명령어, 옵션, 시간
2. **입력 정보**: Top 파일, 검색 경로들
3. **발견 정보**: 모듈, 파일, 패키지, include
4. **변환 정보**: Prefix 적용, 파일 이름 변경
5. **출력 정보**: 생성된 파일들, 복사된 파일들
6. **의존성 정보**: Module hierarchy, instance 관계
7. **이슈 정보**: Warning, Error 메시지

### Use Cases for Report

1. **변경 추적**: 어떤 파일이 수정되었는지 확인
2. **디버깅**: 문제 발생 시 어디서 변경되었는지 추적
3. **문서화**: 프로젝트 구조 이해
4. **검증**: 모든 필요한 모듈이 포함되었는지 확인
5. **자동화**: JSON 출력을 다른 스크립트에서 파싱하여 활용

## Future Enhancements

- Generate block 내의 instance 처리
- Parameterized module 지원
- Interface 지원
- Filelist format 선택 (VCS, Verilator, Vivado, etc.)
- Incremental update (이미 생성된 filelist 재활용)
- Dependency graph 시각화
- Unused module 탐지
- GUI 또는 Web interface
- Package import 자동 분석
