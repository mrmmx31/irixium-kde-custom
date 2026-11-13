IRIX Classic para Wine - 0.1.0 - GPL-3.0-or-later

Aplicar somente ao prefixo explicitamente escolhido (Wine win64):
  python3 manage.py --prefix "$HOME/.wine"
  python3 manage.py --prefix "$HOME/.wine" --verificar
  python3 manage.py --prefix "$HOME/.wine" --exibir
Restaurar a aparência anterior:
  python3 manage.py --prefix "$HOME/.wine" --restaurar

Execute sem sudo. Backup em PREFIX/.irixclassic-theme/backups/.
Reabra os aplicativos para carregar o tema. Fontes existentes são preservadas.
Aplicativos que desenham controles próprios podem ignorar o estilo do Wine.
Não há instalação global nem alteração automática de outros prefixos.
O .msstyles contém os desenhos reais; o .theme oferece somente a paleta.

Fontes e documentação:
https://github.com/mrmmx31/irixium-kde-custom/tree/%23irixfiles/wine
