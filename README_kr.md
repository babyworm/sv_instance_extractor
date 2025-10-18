# SystemVerilog 인스턴스 추출기

SystemVerilog 파일을 분석하여 모듈 인스턴스를 추출하고 컴파일을 위한 파일 목록을 생성하는 Python 도구입니다.

## 기능

- 🔍 **자동 모듈 검색**: SystemVerilog 파일을 스캔하고 의존성 트리를 구축합니다.
- 📦 **라이브러리 지원**: 라이브러리 모듈을 별도의 파일 목록으로 분리합니다.
- 📤 **라이브러리 추출**: 필요할 때 참조된 라이브러리 소스만 깨끗한 디렉토리로 복사합니다.
- 📝 **인클루드 파일 처리**: `.svh` 헤더 및 SystemVerilog 패키지를 올바르게 처리합니다.
- 🏷️ **접두사 지원**: 이름 충돌을 피하기 위해 사용자 지정 접두사로 라이브러리 모듈의 이름을 변경합니다.
- 📊 **보고서 생성**: 텍스트, JSON 또는 마크다운 형식으로 상세한 보고서를 생성합니다.
- ⚡ **스마트 파싱**: 파라미터화된 인스턴스 및 여러 줄의 모듈 선언을 처리합니다.

## 설치

설치가 필요 없습니다! Python 3.6 이상이 설치되어 있는지 확인하십시오.

```bash
# 저장소 복제
git clone <your-repo-url>
cd sv_instance_extractor

# 스크립트를 실행 가능하게 만들기 (선택 사항)
chmod +x sv_instance_extractor.py
```

## 빠른 시작

### 기본 사용법

최상위 모듈에서 파일 목록 생성:

```bash
./sv_instance_extractor.py -i top.sv -idir ./rtl
```

### 라이브러리 사용

라이브러리 모듈을 `lib.f`로 분리:

```bash
./sv_instance_extractor.py -i top.sv -idir ./rtl -lib ./ip_library
```

### 인클루드 파일 사용

헤더 파일 및 패키지 처리:

```bash
./sv_instance_extractor.py -i top.sv -idir ./rtl --include ./include --include ./packages
```

### 접두사 사용 (모듈 격리)

라이브러리 모듈 이름 변경 및 모든 인스턴스 업데이트:

```bash
./sv_instance_extractor.py -i top.sv -idir ./rtl -lib ./ip_library --prefix=IP -o ./output
```

## 예제 스크립트

`examples/` 디렉토리에는 대표적인 시나리오가 정리되어 있습니다.

- `examples/run_basic.sh` – 기본 `list.f`/`lib.f` 생성.
- `examples/run_with_prefix.sh` – `--prefix` 흐름을 적용하고 수정된 RTL을 확인.
- `examples/run_export_lib.sh` – 사용된 라이브러리 소스만 별도 디렉토리로 복사.
- `examples/run_programmatic.py` – Python 코드에서 `InstanceExtractor`를 호출하고 보고서를 생성.

저장소 루트에서 다음과 같이 실행할 수 있습니다.

```bash
bash examples/run_basic.sh
python3 examples/run_programmatic.py
```

모든 스크립트는 결과를 `examples/output/` 아래에 기록하므로 확인 후 다시 실행할 수 있습니다.

## 명령줄 옵션

### 필수 옵션

| 옵션 | 설명 |
|--------|-------------|
| `-i`, `--input <파일>` | 분석할 최상위 SystemVerilog 파일 |

### 검색 경로 옵션

| 옵션 | 설명 |
|--------|-------------|
| `-idir <디렉토리>` | 모듈 검색 디렉토리 (여러 번 사용 가능) |
| `-lib <디렉토리>` | 라이브러리 모듈 디렉토리 - 별도의 `lib.f` 생성 (여러 번 사용 가능) |
| `--include <디렉토리>` | `.svh` 헤더 및 패키지를 위한 인클루드 파일 디렉토리 (여러 번 사용 가능) |

### 출력 옵션

| 옵션 | 설명 |
|--------|-------------|
| `-o`, `--output <디렉토리>` | 출력 디렉토리 (기본값: 현재 디렉토리, 또는 `--prefix` 사용 시 `./output_rtl`) |
| `--gen-lib <디렉토리>` | 사용된 라이브러리 모듈을 `<디렉토리>`로 복사하고 그 안에 `lib.f`를 생성 |
| `--prefix <문자열>` | 라이브러리 모듈 이름에 접두사 추가 (`-o` 필요 또는 `./output_rtl` 사용) |

### 보고서 옵션

| 옵션 | 설명 |
|--------|-------------|
| `--report <파일>` | 보고서 파일 생성 (기본값: 표준 출력) |
| `--report-format <형식>` | 보고서 형식: `text` (기본값), `json`, 또는 `markdown` |

## 사용 예제

### 예제 1: 기본 파일 목록 생성

```bash
./sv_instance_extractor.py -i test_example/rtl/top.sv -idir test_example/rtl
```

**출력**: `list.f`
```
// RTL 파일
test_example/rtl/top.sv
test_example/rtl/cpu_core.sv
test_example/rtl/alu.sv
test_example/rtl/register_file.sv
```

### 예제 2: 라이브러리 모듈 사용

```bash
./sv_instance_extractor.py -i test_example/rtl/top.sv \
    -idir test_example/rtl \
    -lib test_example/lib
```

**출력**: `list.f` 및 `lib.f`

`list.f`:
```
// RTL 파일
test_example/rtl/top.sv
...

// 라이브러리 파일
-f lib.f
```

`lib.f`:
```
// 라이브러리 파일
test_example/lib/adder.sv
test_example/lib/fifo.sv
```

### 예제 3: 라이브러리를 별도 디렉토리로 복사

```bash
./sv_instance_extractor.py -i test_example/rtl/top.sv \
    -idir test_example/rtl \
    -lib test_example/lib \
    --gen-lib ./extracted_lib
```

**결과**:
```
list.f
extracted_lib/
  ├── adder.sv
  ├── fifo.sv
  └── lib.f
```

`list.f`는 `extracted_lib/lib.f`를 참조하며, 지정된 디렉토리에는 실제로 사용된 라이브러리 소스만 복사됩니다.

### 예제 4: 인클루드 파일 사용

```bash
./sv_instance_extractor.py -i test_example/rtl/top.sv \
    -idir test_example/rtl \
    -lib test_example/lib \
    --include test_example/include \
    --include test_example/packages
```

**출력**: 적절한 순서로 정렬된 `list.f`
```
// SystemVerilog 패키지
test_example/packages/common_pkg.sv

// 인클루드 디렉토리
+incdir+test_example/include
+incdir+test_example/packages

// RTL 파일
...

// 라이브러리 파일
-f lib.f
```

### 예제 5: 접두사를 사용한 모듈 격리

```bash
./sv_instance_extractor.py -i test_example/rtl/top.sv \
    -idir test_example/rtl \
    -lib test_example/lib \
    --include test_example/include \
    --include test_example/packages \
    --prefix=IP \
    -o ./isolated_design
```

**수행되는 작업**:
1. 라이브러리 모듈 이름 변경: `adder` → `IP_adder`, `fifo` → `IP_fifo`
2. 모든 RTL 파일이 새 이름을 사용하도록 업데이트됨
3. 파일이 적절한 구조로 `./isolated_design/`에 복사됨
4. 인클루드 파일이 `./isolated_design/include/`에 복사됨
5. 새 파일 목록 생성됨

**원본 `alu.sv`**:
```systemverilog
adder #(.WIDTH(32)) u_adder (
  .a(a), .b(b), .sum(sum)
);
```

**수정된 `isolated_design/alu.sv`**:
```systemverilog
IP_adder #(.WIDTH(32)) u_adder (
  .a(a), .b(b), .sum(sum)
);
```

### 예제 6: JSON 보고서 생성

```bash
./sv_instance_extractor.py -i test_example/rtl/top.sv \
    -idir test_example/rtl \
    -lib test_example/lib \
    --report=report.json \
    --report-format=json
```

**출력**: 전체 분석 데이터가 포함된 `report.json` (자동화에 유용)

## 출력 파일

### 생성된 파일 목록

- **`list.f`**: 다음을 포함하는 주 파일 목록:
  1. SystemVerilog 패키지 (`--include` 디렉토리에서)
  2. 헤더 파일을 위한 `+incdir+` 지시문
  3. RTL 모듈 파일
  4. `lib.f` 참조 (라이브러리 모듈이 있는 경우)

- **`lib.f`**: 라이브러리 모듈 파일을 포함하는 라이브러리 목록 (`--gen-lib` 사용 시 해당 디렉토리에 생성)

### 보고서 형식

보고서 포함 내용:
- **요약**: 통계, 설정, 생성된 파일
- **세부 정보**: 모듈 목록, 파일 수정, 경고, 오류

사용 가능한 형식:
- **텍스트**: 사람이 읽을 수 있는 콘솔 출력
- **JSON**: 자동화를 위한 기계 판독 가능 형식
- **마크다운**: 깔끔한 문서 형식

## 작동 방식

1. **최상위 파일 파싱**: 최상위 SystemVerilog 파일을 읽습니다.
2. **인스턴스 찾기**: 모든 모듈 인스턴스화를 추출합니다.
3. **의존성 트리 구축**: 필요한 모든 모듈을 재귀적으로 찾습니다.
4. **디렉토리 스캔**: `-idir` 및 `-lib` 디렉토리에서 모듈 정의를 검색합니다.
5. **인클루드 처리**: `--include` 디렉토리의 `.svh` 파일 및 패키지를 처리합니다.
6. **파일 목록 생성**: 적절하게 정렬된 컴파일 목록을 생성합니다.
7. **변환 적용** (선택 사항): `--prefix`로 모듈 이름을 바꾸고 모든 인스턴스를 업데이트합니다.
8. **보고서 생성**: 상세 분석 보고서를 생성합니다.

## 테스트 예제

저장소에는 완전한 테스트 예제가 포함되어 있습니다:

```
test_example/
├── include/
│   └── defines.svh          # 헤더 파일
├── packages/
│   └── common_pkg.sv        # SystemVerilog 패키지
├── lib/
│   ├── adder.sv             # 라이브러리 모듈
│   └── fifo.sv              # 라이브러리 모듈
└── rtl/
    ├── top.sv               # 최상위 모듈
    ├── cpu_core.sv          # CPU 코어
    ├── alu.sv               # ALU (adder 사용)
    └── register_file.sv     # 레지스터 파일
```

테스트 실행:
```bash
./sv_instance_extractor.py -i test_example/rtl/top.sv \
    -idir test_example/rtl \
    -lib test_example/lib \
    --include test_example/include \
    --include test_example/packages
```

## 테스트

### 단위 테스트

```bash
python3 -m venv .venv
source .venv/bin/activate
python3 -m pip install -r requirements-dev.txt
pytest
deactivate
```

`pytest`는 임시 디렉토리를 사용해 파서 유틸리티와 추출기 동작을 검증합니다. 가상 환경을 사용하면 시스템 Python에 영향을 주지 않고 개발 의존성을 관리할 수 있습니다.

### 통합 테스트

```bash
./run_tests.sh
```

이 스크립트는 보고서 생성과 오류 처리 등 전체 CLI 시나리오를 점검합니다.

## 요구 사항

- Python 3.6 이상
- 외부 의존성 없음 (Python 표준 라이브러리만 사용)

## 한계

- SystemVerilog `generate` 블록을 처리하지 않습니다.
- 파일 내의 `` `include `` 지시문을 처리하지 않습니다.
- 파라미터화된 모듈은 단일 모듈로 취급됩니다.
- SystemVerilog 구문을 검증하지 않습니다.

## 향후 개선 사항

자세한 사양 및 계획된 기능은 [CLAUDE.md](CLAUDE.md)를 참조하십시오.

## 라이선스

[여기에 라이선스]

## 기여

기여를 환영합니다! 구현에 대한 자세한 내용은 [CLAUDE.md](CLAUDE.md)를 참조하십시오.
