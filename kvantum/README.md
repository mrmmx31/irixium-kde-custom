# Irixium Kvantum upstream snapshot

This directory contains the Kvantum themes used by the KDE **Application
Style**. `Irixium/` is the preserved modern base; `IrixClassic/` is the
Classic derivative. The suite installs both in the invoking user's XDG
configuration directory. Their canonical artwork retains its original colors.

| Field | Value |
| --- | --- |
| Upstream repository | https://www.opencode.net/phob1an/irixium |
| Theme path | `Kvantum/Irixium/` |
| Theme author | Mark Whittaker |
| Recorded commit | `2384fae31d59d02b81f54901ad6cf496957db91a` |
| License | GPL3 |

## Cores do KDE

Depois de aplicar um esquema em Configurações do Sistema → Cores, execute
na própria sessão KDE, sem sudo:

```sh
python3 tools/apply_kvantum_colors.py
```

O caminho acima é relativo à raiz do checkout. Também é possível aplicar um
esquema instalado e atualizar o Kvantum em um único comando:

```sh
python3 tools/apply_kvantum_colors.py --esquema DomainOS-SR10-4
```

O instalador inclui o mesmo comando no runtime independente do checkout.
Se `XDG_DATA_HOME` não estiver definido, ele fica em
`~/.local/share/irixium/theme-companions/tools/apply_kvantum_colors.py`.
O script segue as variáveis XDG do usuário que o executou; nenhum caminho de
perfil particular está embutido no programa.

O comando requer um dos Temas Globais IRIX, seu Kvantum correspondente,
GTK Config do KDE e o Python da distribuição com PyQt6. Obtém os papéis reais
do KColorScheme pela exportação nativa e a paleta Qt por QGuiApplication,
sem atribuir uma paleta artificial aos aplicativos de teste. Gera somente
cópias locais `IrixClassic-KDE`/`IrixClassic-KDE-Reload` ou
`Irixium-KDE`/`Irixium-KDE-Reload`, preservando fontes, métricas e relevos.

As notificações públicas do Plasma recriam o estilo e recarregam a paleta nas
aplicações abertas. Não há temporizador de repaint, reinício de aplicações,
alteração do código KDE/Kvantum ou seleção de tema GTK pelo comando.
Aplicações com paleta própria podem ignorar a escolha do KDE.

Aguarde a conclusão de uma troca de Tema Global antes de executar o comando.
Se o esquema ou suas fontes mudarem durante a geração, a atualização é recusada
e seus arquivos são recuperados; execute novamente depois que a troca terminar.

Kvantum usa os mesmos campos para `Base`, `AlternateBase` e `Shadow` nos
estados ativo e desativado ao abrir um aplicativo. As variantes usam os valores
ativos nativos nesses campos; por isso esses três papéis desativados podem
diferir do KDE até uma atualização nativa da paleta. Essa limitação é informada
no resultado do comando. Esquemas com `Shadow` ativo e inativo diferentes são
recusados, pois o formato Kvantum também não separa esses dois valores.
O desenho desativado de alguns botões também segue a regra de opacidade do
próprio Kvantum, que não equivale às regras de pintura GTK.

Para verificar sem escrever ou notificar a sessão, ou restaurar as variantes:

```sh
python3 tools/apply_kvantum_colors.py --dry-run
python3 tools/apply_kvantum_colors.py --restaurar
```

Os recibos ficam em `XDG_STATE_HOME/irixium-kvantum-palette/`. A restauração
confere o conteúdo das cópias e preserva uma seleção independente feita depois.
Arquivos editados após a geração e operações interrompidas exigem recuperação
explícita; não são sobrescritos em uma tentativa automática. A atualização ou
remoção da suíte restaura essas cópias antes de substituir suas fontes.
As notificações não formam uma transação gráfica: se a primeira chegar a uma
aplicação e a segunda falhar, recuperar os arquivos não desfaz o evento já
recebido. O erro fica registrado; após conferir a recuperação, execute o comando
novamente ou reabra somente a aplicação afetada.

## Verificação de 10 de outubro de 2026

Em uma sessão KDE privada no Xephyr, o comando foi executado nas famílias
Classic e Irixium com DomainOS SR10.4, Breeze Dark, Irixium e uma paleta amarela
de teste. Duas aplicações Qt existentes permaneceram abertas e foram comparadas
com uma aplicação nova a cada troca. Os 19 papéis observados nas aplicações
existentes acompanharam a paleta nativa nos três estados; a leitura complementar
de aplicações novas verificou os 21 papéis e registrou os limites desativados
descritos acima. Nenhum ensaio atribuiu uma paleta artificial às aplicações.

Os testes também verificam fontes intactas, recibos, concorrência, escolhas
independentes, execução sem escrita e restauração. Os ambientes e capturas
privados não integram o pacote nem são dependências do instalador.
