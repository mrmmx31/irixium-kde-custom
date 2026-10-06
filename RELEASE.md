# Pacote completo Irixium KDE

Este pacote instala, somente no perfil do usuário:

- **Irixium Moderno**, decoração KWin independente (`irixium_modern`) baseada no
  adaptador Aurorae, e Tema Global;
- **IRIX Classic**, decoração KWin independente e Tema Global;
- tema de ícones **IRIX Classic — SGI**;
- wallpaper IRIX Classic;
- scripts para alternar as duas decorações.

## Instalação

Extraia o arquivo e execute:

```sh
cd irixium-kde-complete-1.0.0
bash instalar-irixium.sh
```

Não use `sudo`. O instalador grava somente em `~/.local/share`,
`~/.config/kwinrc` quando uma seleção explícita é feita e no estado do usuário.
Ele não substitui componentes em `/usr/share` ou `/usr/lib`.

Depois, abra **Configurações do Sistema → Aparência → Tema Global**. Os pacotes
disponíveis são **Irixium Moderno** e **IRIX Classic**.

O instalador não escolhe automaticamente um Tema Global nem troca a decoração
ativa. Para alternar apenas a decoração:

```sh
bash aurorae/selecionar-user.sh moderno
bash aurorae/selecionar-user.sh classic
```

O diretório também contém os componentes opcionais de Plasma, Kvantum, GTK,
cursores e sons. Eles são mantidos separados para não alterar configurações do
usuário sem confirmação.
