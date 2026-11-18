#!/usr/bin/env bash
set -euo pipefail

cd "$(dirname "${BASH_SOURCE[0]}")"

PYTHON="${PYTHON:-python3}"
VENV_DIR="${VENV_DIR:-.venv}"

if ! command -v "$PYTHON" >/dev/null 2>&1; then
    echo "Python 3.10+ is required, but '$PYTHON' was not found." >&2
    exit 1
fi

"$PYTHON" - <<'PY'
import sys

if sys.version_info < (3, 10):
    raise SystemExit("Python 3.10 or newer is required.")
PY

if [[ ! -d "$VENV_DIR" ]]; then
    echo "Creating virtual environment: $VENV_DIR"
    "$PYTHON" -m venv "$VENV_DIR"
fi

"$VENV_DIR/bin/python" -m pip install --upgrade pip
"$VENV_DIR/bin/python" -m pip install -e ".[audio]"

echo
echo "SortMySet installed."
echo "Start the GUI with: ./run.sh"
