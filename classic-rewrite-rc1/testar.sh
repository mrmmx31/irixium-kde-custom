#!/bin/sh
set -eu
base=$(CDPATH= cd -- "$(dirname -- "$0")" && pwd)
case "${1:-}" in
    --qml)
        runner=$(command -v qmltestrunner6 || true)
        for f in /usr/lib/qt6/bin/qmltestrunner /usr/lib/x86_64-linux-gnu/qt6/bin/qmltestrunner; do
            if [ -z "$runner" ] && [ -x "$f" ]; then runner=$f; fi
        done
        if [ -z "$runner" ]; then
            printf '%s\n' 'Qt 6 qmltestrunner não encontrado. Testes QML NÃO executados. Nenhuma dependência foi instalada.' >&2
            exit 77
        fi
        exec "$runner" -input "$base/tests/qml"
        ;;
    --janelas)
        runner=$(command -v qml6 || true)
        for f in /usr/lib/qt6/bin/qml /usr/lib/x86_64-linux-gnu/qt6/bin/qml; do
            if [ -z "$runner" ] && [ -x "$f" ]; then runner=$f; fi
        done
        if [ -z "$runner" ]; then
            printf '%s\n' 'Executor qml do Qt 6 não encontrado. Nenhuma janela foi aberta e nenhuma dependência foi instalada.' >&2
            exit 77
        fi
        exec "$runner" "$base/tests/janelas.qml"
        ;;
    '')
        command -v python3 >/dev/null || { echo 'Python 3 ausente.' >&2; exit 1; }
        command -v node >/dev/null || { echo 'Node.js é necessário somente para os testes de desenvolvimento.' >&2; exit 1; }
        python3 -m unittest discover -s "$base/tests" -v
        node "$base/tests/test_input.js"
        node "$base/tests/test_graphics.js"
        node "$base/tests/test_preview.js"
        ;;
    *) printf '%s\n' 'Uso: testar.sh [--qml | --janelas]' >&2; exit 2 ;;
esac
