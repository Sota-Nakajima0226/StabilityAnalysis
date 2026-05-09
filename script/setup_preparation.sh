#!/usr/bin/env bash
set -euo pipefail

ROOT_DIR="$(cd "$(dirname "$0")/.." && pwd)"
PYTHON_BIN="$ROOT_DIR/.venv/bin/python"

if [ ! -x "$PYTHON_BIN" ]; then
  echo "Error: $PYTHON_BIN is not found or not executable."
  echo "Please create venv and install dependencies first."
  exit 1
fi

cd "$ROOT_DIR"

echo "[1/2] Creating tables..."
"$PYTHON_BIN" analysis/sqlite/create_table.py

echo "[2/2] Inserting master data..."
"$PYTHON_BIN" analysis/sqlite/insert_master_data.py

echo "Preparation completed."
