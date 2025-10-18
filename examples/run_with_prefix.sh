#!/usr/bin/env bash
set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
REPO_ROOT="$(cd "${SCRIPT_DIR}/.." && pwd)"
cd "${REPO_ROOT}"

OUTPUT_DIR="examples/output/prefixed"
rm -rf "${OUTPUT_DIR}"

python3 sv_instance_extractor.py \
  -i test_example/rtl/top.sv \
  -idir test_example/rtl \
  -lib test_example/lib \
  --include test_example/include \
  --include test_example/packages \
  --prefix=IP \
  -o "${OUTPUT_DIR}"

echo
echo "Prefix example complete."
echo "Inspect ${OUTPUT_DIR}/lib/ for renamed modules and ${OUTPUT_DIR}/list.f for updated references."
