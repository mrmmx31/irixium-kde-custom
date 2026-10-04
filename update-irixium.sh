#!/bin/sh
set -eu

bundle_dir=$(CDPATH= cd -- "$(dirname -- "$0")" && pwd)
aurorae_dir="$HOME/.local/share/aurorae/themes/Irixium"
qml_dir="/usr/lib/x86_64-linux-gnu/qt6/qml/org/kde/kwin/decoration"
qml_target="$qml_dir/MenuButton.qml"
qml_backup="$qml_dir/MenuButton.qml.irixium-original"
system_asset_dir="/usr/share/kwin/aurorae/Irixium"

mkdir -p "$aurorae_dir"
install -m 0644 "$bundle_dir/applications.png" "$aurorae_dir/applications.png"
install -m 0644 "$bundle_dir/Irixiumrc" "$aurorae_dir/Irixiumrc"

if [ "$(id -u)" -eq 0 ]; then
    install -m 0644 "$bundle_dir/MenuButton.qml" "$qml_target"
    install -d -m 0755 "$system_asset_dir"
    install -m 0644 "$bundle_dir/applications.png" "$system_asset_dir/applications.png"
else
    pkexec sh -c '
        set -eu
        source=$1
        target=$2
        backup=$3
        asset=$4
        asset_dir=$5
        if [ ! -e "$backup" ]; then
            install -m 0644 "$target" "$backup"
        fi
        install -m 0644 "$source" "$target"
        install -d -m 0755 "$asset_dir"
        install -m 0644 "$asset" "$asset_dir/applications.png"
    ' sh "$bundle_dir/MenuButton.qml" "$qml_target" "$qml_backup" "$bundle_dir/applications.png" "$system_asset_dir"
fi

if command -v qdbus6 >/dev/null 2>&1; then
    qdbus6 org.kde.KWin /KWin reconfigure >/dev/null 2>&1 || true
fi

if command -v kwriteconfig6 >/dev/null 2>&1; then
    kwriteconfig6 --file kwinrc --group org.kde.kdecoration2 --key BorderSize Normal
    kwriteconfig6 --file kwinrc --group org.kde.kdecoration2 --key ButtonsOnLeft MNS
    kwriteconfig6 --file kwinrc --group org.kde.kdecoration2 --key theme __aurorae__svg__Irixium
fi

printf '%s\n' "Irixium customização reaplicada."
printf '%s\n' "Entre novamente na sessão para o KWin recarregar o componente QML."
