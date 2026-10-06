#!/bin/sh
set -eu

base=$(CDPATH= cd -- "$(dirname -- "$0")" && pwd)
data_home=${XDG_DATA_HOME:-"$HOME/.local/share"}
state="${XDG_STATE_HOME:-"$HOME/.local/state"}/irixium-kde-release"
stamp=$(date -u +%Y%m%dT%H%M%SZ)

backup_and_copy() {
  source=$1
  destination=$2
  if [ -e "$destination" ] || [ -L "$destination" ]; then
    backup="$state/$stamp/$(basename "$destination")"
    mkdir -p "$(dirname "$backup")"
    mv "$destination" "$backup"
    printf 'Backup criado: %s\n' "$backup"
  fi
  mkdir -p "$(dirname "$destination")"
  cp -a "$source" "$destination"
}

if [ "$(id -u)" -eq 0 ]; then
  printf '%s\n' 'Execute como usuário normal, sem sudo.' >&2
  exit 1
fi

printf '%s\n' '== Irixium KDE: instalação no perfil do usuário =='
bash "$base/aurorae/instalar-user.sh"

printf '%s\n' 'Instalando IRIX Classic...'
bash "$base/classic-rewrite-rc1/instalar.sh" \
  --hook --destino irixium_irix_classic_v4

printf '%s\n' 'Instalando ícones IRIX Classic — SGI...'
python3 "$base/icons/tools/install_theme.py"

printf '%s\n' 'Instalando os dois Temas Globais...'
backup_and_copy "$base/look-and-feel/org.magpie.irixium.desktop" \
  "$data_home/plasma/look-and-feel/org.magpie.irixium.desktop"
backup_and_copy "$base/look-and-feel/org.magpie.irixclassic.desktop" \
  "$data_home/plasma/look-and-feel/org.magpie.irixclassic.desktop"

printf '%s\n' 'Instalando wallpaper no perfil do usuário...'
backup_and_copy "$base/wallpapers/IrixClassic" \
  "$data_home/wallpapers/IrixClassic"

printf '\n%s\n' 'Instalação concluída sem modificar /usr.'
printf '%s\n' 'Abra Configurações do Sistema → Aparência → Tema Global.'
printf '%s\n' 'As opções disponíveis são: Irixium Moderno e IRIX Classic.'
printf '%s\n' 'Para selecionar a decoração separadamente:'
printf '%s\n' "  bash \"$base/aurorae/selecionar-user.sh\" moderno"
printf '%s\n' "  bash \"$base/aurorae/selecionar-user.sh\" classic"
