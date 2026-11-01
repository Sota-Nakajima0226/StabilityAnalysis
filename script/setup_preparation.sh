#!/usr/bin/env bash
set -euo pipefail

ROOT_DIR="$(cd "$(dirname "$0")/.." && pwd)"
PYTHON_BIN="${PYTHON_BIN:-python}"

if ! command -v "$PYTHON_BIN" >/dev/null 2>&1; then
  echo "Error: $PYTHON_BIN is not found."
  echo "Please activate the conda environment and install dependencies first."
  exit 1
fi

cd "$ROOT_DIR"

echo "[1/2] Creating tables..."
"$PYTHON_BIN" analysis/sqlite/create_table.py

echo "[2/2] Inserting master data..."
"$PYTHON_BIN" analysis/sqlite/insert_master_data.py

echo "Preparation completed."
