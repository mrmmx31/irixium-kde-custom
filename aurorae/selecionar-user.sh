#!/bin/sh
set -eu

case "${1:-}" in
  moderno)
    if [ ! -d "${XDG_DATA_HOME:-"$HOME/.local/share"}/aurorae/themes/Irixium" ]; then
      printf '%s\n' 'Irixium moderno não está instalado no perfil do usuário.' >&2
      exit 1
    fi
    theme=__aurorae__svg__Irixium
    ;;
  classic)
    if [ ! -d "${XDG_DATA_HOME:-"$HOME/.local/share"}/kwin/decorations/irixium_irix_classic_v4" ]; then
      printf '%s\n' 'IRIX Classic não está instalado no perfil do usuário.' >&2
      exit 1
    fi
    theme=irixium_irix_classic_v4
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
printf 'Decoração selecionada no perfil do usuário: %s\n' "$theme"
printf '%s\n' 'Entre novamente na sessão se o KWin não recarregar a decoração imediatamente.'
