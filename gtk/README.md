# Temas GTK

Cada variante é uma pasta instalável independente:

| Pasta | Nome GTK | Escopo |
|---|---|---|
| [Irixium](Irixium/) | `Irixium` | Tema moderno original, preservado byte a byte |
| [IrixClassic](IrixClassic/) | `IrixClassic` | Tradução Classic para GTK2, GTK3 e GTK4 |

O perfil Classic usa `IrixClassic`; o perfil Modern usa `Irixium`. A instalação
da suíte copia a pasta inteira de cada variante para o diretório XDG de temas.
O subdiretório `common/` do Classic contém os recursos compartilhados necessários
às três versões. Selecionar o tema é uma operação separada da cópia dos arquivos.

As configurações GTK3/GTK4 usam `gtk-theme-name`; GTK2 usa seu `gtkrc`. Em KDE,
GTKConfig/XSettings também comunica a escolha aos aplicativos. A documentação
de integração e o helper `tools/select_gtk.py` ficam na raiz da suíte. Estes
temas e hosts de prévia não escrevem preferências do desktop.

[MODERN-PRESERVED.json](MODERN-PRESERVED.json) registra SHA-256 dos 35 arquivos
originais e a mudança de prefixo de `gtk/` para `gtk/Irixium/`. O README e as
licenças originais permanecem dentro dessa pasta, incluindo a declaração
separada de licença de imagens do upstream.

O Classic usa somente os mapas locais GPL-3.0-or-later de `kvantum/tools/` e sua
própria tradução GTK. Veja [origem](IrixClassic/ORIGEM.json),
[compatibilidade e provas](IrixClassic/README.md) e [licença](IrixClassic/LICENSE).
