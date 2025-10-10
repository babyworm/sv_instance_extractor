#!/bin/bash

# SystemVerilog Instance Extractor - Test Suite
# This script runs comprehensive tests to validate all functionality

set -e  # Exit on error

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
cd "$SCRIPT_DIR"

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# Test counter
TESTS_RUN=0
TESTS_PASSED=0
TESTS_FAILED=0

# Function to print test header
print_test() {
    echo -e "${BLUE}━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━${NC}"
    echo -e "${BLUE}TEST $1: $2${NC}"
    echo -e "${BLUE}━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━${NC}"
    TESTS_RUN=$((TESTS_RUN + 1))
}

# Function to check test result
check_result() {
    if [ $? -eq 0 ]; then
        echo -e "${GREEN}✓ PASSED${NC}"
        TESTS_PASSED=$((TESTS_PASSED + 1))
        return 0
    else
        echo -e "${RED}✗ FAILED${NC}"
        TESTS_FAILED=$((TESTS_FAILED + 1))
        return 1
    fi
}

# Function to verify file exists
verify_file() {
    if [ -f "$1" ]; then
        echo -e "${GREEN}  ✓ File exists: $1${NC}"
        return 0
    else
        echo -e "${RED}  ✗ File missing: $1${NC}"
        return 1
    fi
}

# Function to verify directory exists
verify_dir() {
    if [ -d "$1" ]; then
        echo -e "${GREEN}  ✓ Directory exists: $1${NC}"
        return 0
    else
        echo -e "${RED}  ✗ Directory missing: $1${NC}"
        return 1
    fi
}

# Function to verify file contains string
verify_content() {
    if grep -qF -- "$2" "$1"; then
        echo -e "${GREEN}  ✓ Content found in $1: $2${NC}"
        return 0
    else
        echo -e "${RED}  ✗ Content not found in $1: $2${NC}"
        return 1
    fi
}

echo -e "${YELLOW}╔════════════════════════════════════════════════════════════╗${NC}"
echo -e "${YELLOW}║   SystemVerilog Instance Extractor - Test Suite           ║${NC}"
echo -e "${YELLOW}╚════════════════════════════════════════════════════════════╝${NC}"
echo ""

# Check Python version
echo -e "${BLUE}Checking Python version...${NC}"
python3 --version
if [ $? -ne 0 ]; then
    echo -e "${RED}Python 3 not found!${NC}"
    exit 1
fi
echo ""

# Clean previous test outputs
echo -e "${BLUE}Cleaning previous test outputs...${NC}"
rm -rf test_results
mkdir -p test_results
rm -f list.f lib.f report*.txt report*.json report*.md
echo -e "${GREEN}✓ Cleaned${NC}"
echo ""

# ============================================================================
# TEST 1: Basic filelist generation
# ============================================================================
print_test "1" "Basic Filelist Generation"
python3 sv_instance_extractor.py \
    -i test_example/rtl/top.sv \
    -idir test_example/rtl \
    > test_results/test1_output.txt 2>&1
check_result

verify_file "list.f" && \
verify_content "list.f" "test_example/rtl/top.sv" && \
verify_content "list.f" "test_example/rtl/alu.sv"
check_result
mv list.f test_results/test1_list.f
echo ""

# ============================================================================
# TEST 2: Library separation
# ============================================================================
print_test "2" "Library Module Separation"
python3 sv_instance_extractor.py \
    -i test_example/rtl/top.sv \
    -idir test_example/rtl \
    -lib test_example/lib \
    > test_results/test2_output.txt 2>&1
check_result

RESULT=0
verify_file "list.f" || RESULT=1
verify_file "lib.f" || RESULT=1
verify_content "lib.f" "test_example/lib/adder.sv" || RESULT=1
verify_content "lib.f" "test_example/lib/fifo.sv" || RESULT=1
verify_content "list.f" "-f lib.f" || RESULT=1
mv list.f test_results/test2_list.f
mv lib.f test_results/test2_lib.f
if [ $RESULT -eq 0 ]; then
    TESTS_PASSED=$((TESTS_PASSED + 1))
    echo -e "${GREEN}✓ ALL CHECKS PASSED${NC}"
else
    TESTS_FAILED=$((TESTS_FAILED + 1))
    echo -e "${RED}✗ SOME CHECKS FAILED${NC}"
fi
echo ""

# ============================================================================
# TEST 3: Include file handling
# ============================================================================
print_test "3" "Include File Handling"
python3 sv_instance_extractor.py \
    -i test_example/rtl/top.sv \
    -idir test_example/rtl \
    -lib test_example/lib \
    --include test_example/include \
    --include test_example/packages \
    > test_results/test3_output.txt 2>&1
check_result

RESULT=0
verify_file "list.f" || RESULT=1
verify_content "list.f" "common_pkg.sv" || RESULT=1
verify_content "list.f" "+incdir+test_example/include" || RESULT=1
verify_content "list.f" "+incdir+test_example/packages" || RESULT=1
mv list.f test_results/test3_list.f
mv lib.f test_results/test3_lib.f 2>/dev/null || true
if [ $RESULT -eq 0 ]; then
    TESTS_PASSED=$((TESTS_PASSED + 1))
    echo -e "${GREEN}✓ ALL CHECKS PASSED${NC}"
else
    TESTS_FAILED=$((TESTS_FAILED + 1))
    echo -e "${RED}✗ SOME CHECKS FAILED${NC}"
fi
echo ""

# ============================================================================
# TEST 4: Prefix functionality
# ============================================================================
print_test "4" "Prefix Application and File Modification"
python3 sv_instance_extractor.py \
    -i test_example/rtl/top.sv \
    -idir test_example/rtl \
    -lib test_example/lib \
    --include test_example/include \
    --include test_example/packages \
    --prefix=TEST \
    -o test_results/output_prefix \
    > test_results/test4_output.txt 2>&1
check_result

verify_dir "test_results/output_prefix" && \
verify_dir "test_results/output_prefix/lib" && \
verify_file "test_results/output_prefix/list.f" && \
verify_file "test_results/output_prefix/lib/lib.f" && \
verify_file "test_results/output_prefix/lib/TEST_adder.sv" && \
verify_file "test_results/output_prefix/lib/TEST_fifo.sv" && \
verify_content "test_results/output_prefix/lib/TEST_adder.sv" "module TEST_adder" && \
verify_content "test_results/output_prefix/alu.sv" "TEST_adder" && \
verify_content "test_results/output_prefix/top.sv" "TEST_fifo"
check_result
echo ""

# ============================================================================
# TEST 5: Text report generation
# ============================================================================
print_test "5" "Text Report Generation"
python3 sv_instance_extractor.py \
    -i test_example/rtl/top.sv \
    -idir test_example/rtl \
    -lib test_example/lib \
    --report=test_results/report_test5.txt \
    --report-format=text \
    > test_results/test5_output.txt 2>&1
check_result

verify_file "test_results/report_test5.txt" && \
verify_content "test_results/report_test5.txt" "SystemVerilog Instance Extractor Report" && \
verify_content "test_results/report_test5.txt" "SUMMARY" && \
verify_content "test_results/report_test5.txt" "Statistics"
check_result
rm -f list.f lib.f
echo ""

# ============================================================================
# TEST 6: JSON report generation
# ============================================================================
print_test "6" "JSON Report Generation"
python3 sv_instance_extractor.py \
    -i test_example/rtl/top.sv \
    -idir test_example/rtl \
    -lib test_example/lib \
    --report=test_results/report_test6.json \
    --report-format=json \
    > test_results/test6_output.txt 2>&1
check_result

verify_file "test_results/report_test6.json" && \
verify_content "test_results/report_test6.json" '"metadata"' && \
verify_content "test_results/report_test6.json" '"statistics"' && \
python3 -m json.tool test_results/report_test6.json > /dev/null 2>&1  # Validate JSON
check_result
rm -f list.f lib.f
echo ""

# ============================================================================
# TEST 7: Markdown report generation
# ============================================================================
print_test "7" "Markdown Report Generation"
python3 sv_instance_extractor.py \
    -i test_example/rtl/top.sv \
    -idir test_example/rtl \
    -lib test_example/lib \
    --report=test_results/report_test7.md \
    --report-format=markdown \
    > test_results/test7_output.txt 2>&1
check_result

verify_file "test_results/report_test7.md" && \
verify_content "test_results/report_test7.md" "# SystemVerilog Instance Extractor Report" && \
verify_content "test_results/report_test7.md" "## Summary" && \
verify_content "test_results/report_test7.md" "### Statistics"
check_result
rm -f list.f lib.f
echo ""

# ============================================================================
# TEST 8: Help command
# ============================================================================
print_test "8" "Help Command"
python3 sv_instance_extractor.py --help > test_results/test8_help.txt 2>&1
check_result

verify_content "test_results/test8_help.txt" "usage:" && \
verify_content "test_results/test8_help.txt" "INPUT" && \
verify_content "test_results/test8_help.txt" "prefix"
check_result
echo ""

# ============================================================================
# TEST 9: Error handling - missing input file
# ============================================================================
print_test "9" "Error Handling - Missing Input File"
python3 sv_instance_extractor.py \
    -i nonexistent.sv \
    -idir test_example/rtl \
    > test_results/test9_output.txt 2>&1
if [ $? -ne 0 ]; then
    echo -e "${GREEN}✓ Correctly failed for missing file${NC}"
    TESTS_PASSED=$((TESTS_PASSED + 1))
else
    echo -e "${RED}✗ Should have failed for missing file${NC}"
    TESTS_FAILED=$((TESTS_FAILED + 1))
fi
echo ""

# ============================================================================
# Print summary
# ============================================================================
echo ""
echo -e "${YELLOW}╔════════════════════════════════════════════════════════════╗${NC}"
echo -e "${YELLOW}║                      TEST SUMMARY                          ║${NC}"
echo -e "${YELLOW}╚════════════════════════════════════════════════════════════╝${NC}"
echo ""
echo -e "Total Tests Run:    ${BLUE}$TESTS_RUN${NC}"
echo -e "Tests Passed:       ${GREEN}$TESTS_PASSED${NC}"
echo -e "Tests Failed:       ${RED}$TESTS_FAILED${NC}"
echo ""

if [ $TESTS_FAILED -eq 0 ]; then
    echo -e "${GREEN}╔════════════════════════════════════════════════════════════╗${NC}"
    echo -e "${GREEN}║              ALL TESTS PASSED! ✓                           ║${NC}"
    echo -e "${GREEN}╚════════════════════════════════════════════════════════════╝${NC}"
    echo ""
    echo "Test results saved in: test_results/"
    exit 0
else
    echo -e "${RED}╔════════════════════════════════════════════════════════════╗${NC}"
    echo -e "${RED}║              SOME TESTS FAILED! ✗                          ║${NC}"
    echo -e "${RED}╚════════════════════════════════════════════════════════════╝${NC}"
    echo ""
    echo "Check test_results/ for detailed output"
    exit 1
fi
