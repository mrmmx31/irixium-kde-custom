#!/bin/sh
set -eu
base=$(CDPATH= cd -- "$(dirname -- "$0")" && pwd)
cd "$base"
if [ "${1:-}" = "--qml" ]; then
    exec python3 tools/test_qml.py
fi
python3 -m unittest discover -s tests -p 'test_*.py' -v
if command -v node >/dev/null 2>&1; then
    node tests/test_geometry.js
else
    printf '%s\n' 'Node.js ausente. Os testes JavaScript não foram executados.' >&2
    exit 77
fi
