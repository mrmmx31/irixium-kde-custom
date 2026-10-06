#!/bin/sh
set -eu

case "${1:-}" in
  moderno)
    if [ ! -d "${XDG_DATA_HOME:-"$HOME/.local/share"}/kwin/decorations/irixium_modern" ]; then
      printf '%s\n' 'Irixium moderno não está instalado no perfil do usuário.' >&2
      exit 1
    fi
    theme=irixium_modern
    plasma_theme=Irixium
    icon_theme=Irixium
    look_and_feel=org.magpie.irixium.desktop
    ;;
  classic)
    if [ ! -d "${XDG_DATA_HOME:-"$HOME/.local/share"}/kwin/decorations/irixium_irix_classic_v4" ]; then
      printf '%s\n' 'IRIX Classic não está instalado no perfil do usuário.' >&2
      exit 1
    fi
    theme=irixium_irix_classic_v4
    plasma_theme=IrixClassic
    icon_theme=IrixClassic-SGI
    look_and_feel=org.magpie.irixclassic.desktop
    ;;
  *)
    printf '%s\n' "Uso: $0 moderno|classic" >&2
    exit 2
    ;;
esac

kwriteconfig6 --file "$HOME/.config/kwinrc" \
  --group org.kde.kdecoration2 --key library org.kde.kwin.aurorae
kwriteconfig6 --file "$HOME/.config/kwinrc" \
  --group org.kde.kdecoration2 --key theme "$theme"
kwriteconfig6 --file "$HOME/.config/plasmarc" \
  --group Theme --key name "$plasma_theme"
kwriteconfig6 --file "$HOME/.config/kdeglobals" \
  --group KDE --key LookAndFeelPackage "$look_and_feel"
kwriteconfig6 --file "$HOME/.config/kdeglobals" \
  --group Icons --key Theme "$icon_theme"
printf 'Tema selecionado no perfil do usuário: %s\n' "$look_and_feel"
printf 'Decoração: %s; Plasma Style: %s; ícones: %s\n' \
  "$theme" "$plasma_theme" "$icon_theme"
printf '%s\n' 'Entre novamente na sessão se o KWin não recarregar a decoração imediatamente.'
