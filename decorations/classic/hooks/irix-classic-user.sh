#!/bin/sh
set -eu
base=$(CDPATH= cd -- "$(dirname -- "$0")/.." && pwd)
exec "$base/instalar.sh" --hook --destino irixium_irix_classic_v4
