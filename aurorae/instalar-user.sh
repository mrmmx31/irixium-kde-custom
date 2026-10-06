#!/bin/sh
set -eu

base=$(CDPATH= cd -- "$(dirname -- "$0")" && pwd)
data_home=${XDG_DATA_HOME:-"$HOME/.local/share"}
destination="$data_home/aurorae/themes/Irixium"
source="$base/Irixium"
state="${XDG_STATE_HOME:-"$HOME/.local/state"}/irixium-user"

activate=0
case "${1:-}" in
  ""|--instalar) ;;
  --ativar) activate=1 ;;
  *)
    printf '%s\n' "Uso: $0 [--instalar|--ativar]" >&2
    exit 2
    ;;
esac

if [ ! -d "$source" ]; then
  printf '%s\n' "Origem ausente: $source" >&2
  exit 1
fi
mkdir -p "$state" "$(dirname "$destination")"
if [ -e "$destination" ] || [ -L "$destination" ]; then
  stamp=$(date -u +%Y%m%dT%H%M%SZ)
  backup="$state/Irixium.$stamp"
  mv "$destination" "$backup"
  printf '%s\n' "Backup do Irixium local: $backup"
fi
cp -a "$source" "$destination"
printf '%s\n' "Irixium moderno instalado no perfil do usuário: $destination"
if [ "$activate" -eq 1 ]; then
  kwriteconfig6 --file "$HOME/.config/kwinrc" \
    --group org.kde.kdecoration2 --key library org.kde.kwin.aurorae
  kwriteconfig6 --file "$HOME/.config/kwinrc" \
    --group org.kde.kdecoration2 --key theme __aurorae__svg__Irixium
  printf '%s\n' 'Irixium moderno selecionado no perfil do usuário.'
fi
