#!/bin/sh
set -eu

bundle_dir=$(CDPATH= cd -- "$(dirname -- "$0")" && pwd)
aurorae_dir="$HOME/.local/share/aurorae/themes/Irixium"
qml_dir="/usr/lib/x86_64-linux-gnu/qt6/qml/org/kde/kwin/decoration"
qml_target="$qml_dir/MenuButton.qml"
qml_backup="$qml_dir/MenuButton.qml.irixium-original"
aurorae_group_target="/usr/share/kwin/aurorae/AuroraeButtonGroup.qml"
aurorae_group_backup="/usr/share/kwin/aurorae/AuroraeButtonGroup.qml.irixium-original"
system_asset_dir="/usr/share/kwin/aurorae/Irixium"

mkdir -p "$aurorae_dir"
cp -a "$bundle_dir/aurorae/Irixium/." "$aurorae_dir/"

if [ "$(id -u)" -eq 0 ]; then
    install -m 0644 "$bundle_dir/MenuButton.qml" "$qml_target"
    install -m 0644 "$bundle_dir/AuroraeButtonGroup.qml" "$aurorae_group_target"
    install -d -m 0755 "$system_asset_dir"
    install -m 0644 "$bundle_dir/aurorae/Irixium/applications.png" "$system_asset_dir/applications.png"
else
    pkexec sh -c '
        set -eu
        source=$1
        target=$2
        backup=$3
        asset=$4
        asset_dir=$5
        group_source=$6
        group_target=$7
        group_backup=$8
        if [ ! -e "$backup" ]; then
            install -m 0644 "$target" "$backup"
        fi
        install -m 0644 "$source" "$target"
        if [ ! -e "$group_backup" ]; then
            install -m 0644 "$group_target" "$group_backup"
        fi
        install -m 0644 "$group_source" "$group_target"
        install -d -m 0755 "$asset_dir"
        install -m 0644 "$asset" "$asset_dir/applications.png"
    ' sh "$bundle_dir/MenuButton.qml" "$qml_target" "$qml_backup" "$bundle_dir/aurorae/Irixium/applications.png" "$system_asset_dir" "$bundle_dir/AuroraeButtonGroup.qml" "$aurorae_group_target" "$aurorae_group_backup"
fi

if command -v qdbus6 >/dev/null 2>&1; then
    qdbus6 org.kde.KWin /KWin reconfigure >/dev/null 2>&1 || true
fi

if command -v kwriteconfig6 >/dev/null 2>&1; then
    kwriteconfig6 --file kwinrc --group org.kde.kdecoration2 --key BorderSize Normal
    kwriteconfig6 --file kwinrc --group org.kde.kdecoration2 --key ButtonsOnLeft M
    kwriteconfig6 --file kwinrc --group org.kde.kdecoration2 --key ButtonsOnRight HXA
    kwriteconfig6 --file kwinrc --group org.kde.kdecoration2 --key theme __aurorae__svg__Irixium
    kwriteconfig6 --file kdeglobals --group General --key XftAntialias false
    kwriteconfig6 --file kdeglobals --group General --key XftSubPixel none
    kwriteconfig6 --file kdeglobals --group General --key font 'Nimbus Sans [urw],12,-1,5,400,0,0,0,0,0,0,0,0,0,0,1'
    kwriteconfig6 --file kdeglobals --group General --key fixed 'Nimbus Sans [urw],12,-1,5,400,0,0,0,0,0,0,0,0,0,0,1'
    kwriteconfig6 --file kdeglobals --group General --key smallestReadableFont 'Nimbus Sans [urw],10,-1,5,400,1,0,0,0,0,0,0,0,0,0,1,Italic'
    kwriteconfig6 --file kdeglobals --group General --key toolBarFont 'Nimbus Sans [urw],12,-1,5,400,1,0,0,0,0,0,0,0,0,0,1,Italic'
    kwriteconfig6 --file kdeglobals --group General --key menuFont 'Nimbus Sans [urw],12,-1,5,400,1,0,0,0,0,0,0,0,0,0,1,Italic'
    kwriteconfig6 --file kdeglobals --group WM --key activeFont 'Nimbus Sans [urw],12,-1,5,700,1,0,0,0,0,0,0,0,0,0,1,Bold Italic'
fi

printf '%s\n' "Irixium customização reaplicada; o botão personalizado é limitado ao tema Irixium."
printf '%s\n' "Entre novamente na sessão para o KWin recarregar o componente QML."
