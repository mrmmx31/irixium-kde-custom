# Decorações IRIX no perfil do usuário

Há duas opções independentes:

- **Irixium moderno** — tema Aurorae em `aurorae/Irixium/`;
- **IRIX Classic** — decoração KWin independente em `classic-rewrite-rc1/package/`.

Instale o moderno sem tocar no sistema:

```sh
bash aurorae/instalar-user.sh
```

O Classic usa seu instalador próprio:

```sh
bash classic-rewrite-rc1/instalar.sh --verificar
bash classic-rewrite-rc1/instalar.sh
```

Depois de instalar ambas, alterne apenas a seleção do usuário:

```sh
bash aurorae/selecionar-user.sh moderno
bash aurorae/selecionar-user.sh classic
```

Os scripts escrevem somente em `~/.local/share`, `~/.config/kwinrc` e no
estado do usuário. Não instalam `MenuButton.qml`, `AuroraeButtonGroup.qml` ou
qualquer outro componente em `/usr`.
