#!/usr/bin/env bash
set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
REPO_ROOT="$(cd "${SCRIPT_DIR}/.." && pwd)"
cd "${REPO_ROOT}"

LIST_DIR="examples/output/export_list"
LIB_DIR="examples/output/export_lib"
rm -rf "${LIST_DIR}" "${LIB_DIR}"
mkdir -p "${LIST_DIR}" "${LIB_DIR}"

python3 sv_instance_extractor.py \
  -i test_example/rtl/top.sv \
  -idir test_example/rtl \
  -lib test_example/lib \
  --gen-lib "${LIB_DIR}" \
  -o "${LIST_DIR}"

echo
echo "Library export example complete."
echo "  Filelist: ${LIST_DIR}/list.f"
echo "  Exported libraries: ${LIB_DIR}/"
