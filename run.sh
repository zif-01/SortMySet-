#!/usr/bin/env bash
set -euo pipefail

cd "$(dirname "${BASH_SOURCE[0]}")"

VENV_DIR="${VENV_DIR:-.venv}"
if [[ ! -x "$VENV_DIR/bin/python" ]]; then
    ./install.sh
fi

if [[ "$#" -eq 0 ]]; then
    exec "$VENV_DIR/bin/sortmyset-gui"
fi

if [[ "$1" == "gui" ]]; then
    shift
    exec "$VENV_DIR/bin/sortmyset-gui" "$@"
fi

exec "$VENV_DIR/bin/sortmyset" "$@"
