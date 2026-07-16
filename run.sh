#!/usr/bin/env bash
set -e

DIR="$(cd "$(dirname "$0")" && pwd)"
cd "$DIR"

VENV=".venv"

if [ ! -d "$VENV" ]; then
    echo "[lavi] creando venv..."
    python3 -m venv --system-site-packages "$VENV"
    source "$VENV/bin/activate"
    pip install -r requirements.txt
    echo "[lavi] dependencias instaladas"
else
    source "$VENV/bin/activate"
fi

exec python -m lavi.main "$@"
