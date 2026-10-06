#!/bin/sh
set -eu

base=$(CDPATH= cd -- "$(dirname -- "$0")/.." && pwd)
service_dir="${XDG_CONFIG_HOME:-$HOME/.config}/systemd/user"
service="$service_dir/irix-classic-user.service"
mkdir -p "$service_dir"

cat >"$service" <<EOF
[Unit]
Description=Garantir decoração IRIX Classic no perfil do usuário
After=graphical-session.target
PartOf=graphical-session.target

[Service]
Type=oneshot
ExecStart=$base/hooks/irix-classic-user.sh

[Install]
WantedBy=graphical-session.target
EOF

systemctl --user daemon-reload
systemctl --user enable irix-classic-user.service
systemctl --user start irix-classic-user.service
printf '%s\n' "Hook instalado e executado: $service"
