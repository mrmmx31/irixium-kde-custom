#!/usr/bin/env bash
set -euo pipefail

ROOT="$(cd -- "$(dirname -- "${BASH_SOURCE[0]}")" && pwd -P)"
CANONICAL_DISK="$ROOT/runtime/discos/dn3500_sr10.4.assistant-20261018.awd"
PRIVATE_DISK="$ROOT/private/dn3500_sr10.4.assistant-20261018.awd"
LEGACY_DIR="$HOME/tempia/ia-tema/vm/shared/domainos-assistant-vm-20261018"
LEGACY_DISK="$LEGACY_DIR/discos/dn3500_sr10.4.assistant-20261018.awd"

for disk in "$CANONICAL_DISK" "$PRIVATE_DISK"; do
  if [[ ! -f "$disk" ]]; then
    echo "Disco ausente em $disk; não restaure nem substitua automaticamente. Consulte docs/DOMAINOS-REGRAS-VM.md." >&2
    exit 2
  fi
done

canonical_identity="$(stat -Lc '%d:%i:%s' -- "$CANONICAL_DISK")"
for disk in "$PRIVATE_DISK"; do
  identity="$(stat -Lc '%d:%i:%s' -- "$disk")"
  if [[ "$canonical_identity" != "$identity" ]]; then
    echo "Os caminhos não apontam para o mesmo disco; pare e investigue antes de usar qualquer um." >&2
    printf 'canônico: %s\noutro:    %s (%s)\n' "$canonical_identity" "$identity" "$disk" >&2
    exit 3
  fi
done
if [[ -e "$LEGACY_DISK" ]]; then
  identity="$(stat -Lc '%d:%i:%s' -- "$LEGACY_DISK")"
  if [[ "$canonical_identity" != "$identity" ]]; then
    echo "O caminho legado do Tempia aponta para outro disco; pare e investigue." >&2
    printf 'canônico: %s\nlegado:   %s (%s)\n' "$canonical_identity" "$identity" "$LEGACY_DISK" >&2
    exit 3
  fi
  echo "Symlink legado do Tempia também resolve para o disco canônico."
else
  echo "Symlink legado do Tempia ausente; o runtime no repositório continua autônomo."
fi

printf 'Disco canônico preservado; os nomes no repositório são o mesmo arquivo (%s bytes).\n' "${canonical_identity##*:}"
python3 "$ROOT/verify_mame_isolation.py" --expected-disk "$CANONICAL_DISK"
