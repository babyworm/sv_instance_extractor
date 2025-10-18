#!/usr/bin/env bash
set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
REPO_ROOT="$(cd "${SCRIPT_DIR}/.." && pwd)"
cd "${REPO_ROOT}"

OUTPUT_DIR="examples/output/basic"
rm -rf "${OUTPUT_DIR}"
mkdir -p "${OUTPUT_DIR}"

python3 sv_instance_extractor.py \
  -i test_example/rtl/top.sv \
  -idir test_example/rtl \
  -lib test_example/lib \
  -o "${OUTPUT_DIR}"

echo
echo "Basic example complete."
echo "Generated files:"
echo "  ${OUTPUT_DIR}/list.f"
echo "  ${OUTPUT_DIR}/lib.f"
