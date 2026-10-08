# Irix Classic DomainOS: requisitos e critérios de verificação

O objetivo é acrescentar uma segunda opção de Plasma Style, chamada **Irix
Classic DomainOS**, e um painel unificado com a composição do projeto enviado
pelo usuário. O Irix Classic atual continua disponível como opção independente.
A referência original HP orienta a nitidez dos desenhos; o projeto do usuário
orienta a disposição, as proporções e os elementos presentes.

A etapa atual prepara o desenho, os recursos do estilo e sua apresentação nativa
isolada. Cada função de botão depende de confirmação do usuário antes de ser
implementada. Os requisitos funcionais abaixo continuam rastreados como parte do
projeto: uma captura ilustrativa não os implementa nem os comprova. Concluir os
critérios D0–D10 conclui a etapa de desenho, não todas as funções do memorial.

## Referências e geometria

Foram inspecionados os dois arquivos originais anexados ao objetivo:

| Referência | Arquivo original | Dimensões | SHA-256 |
| --- | --- | --- | --- |
| Projeto do usuário | `image-1.png` | 2103 × 748 px | `c05a35c30621437fe37585a46b6ce6ec80e5740031dcd48f28b9e976a7526d26` |
| Painel original HP | `image-2.png` | 1025 × 99 px | `508aba94232ee0bf24e01d76cb10e7a43dcd3c1a2a8aab1e225f9654d4179c45` |

Na primeira imagem, o retângulo do corpo é `[112, 296, 2054, 514)`: **1942 ×
218 px**. Os intervalos usam o limite final exclusivo. Essa medida foi obtida
diretamente do PNG original; os limiares de média RGB abaixo de 200 e 220
produzem o mesmo retângulo. Pixels muito claros do fundo e do borrão não
determinam a geometria. Uma apresentação da imagem reduzida a 2048 px de largura
não é a base das medidas.

A referência canônica do painel é 1942 × 218. A comparação no canvas completo
usa 2103 × 748 e coloca o painel em `(112, 296)`. Uma escala 0,5 corresponde a
971 × 109; o tamanho de uma captura deve declarar sua escala. A moldura e seus
filetes podem exigir ajuste ao pixel da tela, mas a escala não muda a ordem dos
módulos ou inventa elementos para ocupar as áreas vazias.

A linha escura que divide os andares está em `y = 450` no PNG original. O andar
superior ocupa `[296, 450)`, com 154 px; a faixa inferior ocupa `[450, 514)`, com
64 px. No sistema local do painel, a divisão é `y = 154`.

| Módulo superior | Intervalo X absoluto | X local | Largura canônica |
| --- | --- | --- | --- |
| Relógio, data, gráfico e correio | `[112, 609)` | 0 | 497 |
| Iconbox e suas duas setas | `[609, 1383)` | 497 | 774 |
| Dois quadros de áreas de trabalho | `[1383, 1724)` | 1271 | 341 |
| Bandeja com seis ícones | `[1724, 1926)` | 1612 | 202 |
| Dois botões laterais direitos | `[1926, 2054)` | 1814 | 128 |

Esses cortes adotam as transições persistentes entre sombra e luz das molduras:
607–608/609–611, 1381–1382/1383–1384, 1722–1723/1724–1726 e
1923–1925/1926–1927. O borrão da referência deixa ambiguidade de aproximadamente
1–2 px na fronteira semântica. Os intervalos inteiros acima são uma convenção
reprodutível para construir e comparar o desenho, sem atribuir precisão
inexistente a cada traço borrado.

| Campo da faixa inferior | Intervalo X absoluto | Intervalo local | Largura |
| --- | --- | --- | --- |
| Selo GNU/LINUX | `[112, 356)` | `[0, 244)` | 244 |
| Chapa vazia esquerda | `[356, 703)` | `[244, 591)` | 347 |
| Segundo campo vazio | `[703, 821)` | `[591, 709)` | 118 |
| Atalho 1: desenho de terminal | `[821, 930)` | `[709, 818)` | 109 |
| Atalho 2: desenho de paleta/ferramentas | `[930, 1046)` | `[818, 934)` | 116 |
| Atalho 3: ferramenta retangular | `[1046, 1164)` | `[934, 1052)` | 118 |
| Atalho 4: desenho de cadeado | `[1164, 1282)` | `[1052, 1170)` | 118 |
| Atalho 5: desenho de interrogação | `[1282, 1401)` | `[1170, 1289)` | 119 |
| Chapa vazia direita e pequeno indicador | `[1401, 2054)` | `[1289, 1942)` | 653 |

A segunda imagem fornece os filetes claros/escuros, o tratamento dos instrumentos,
a face azul do relógio, os desenhos de correio e os detalhes da faixa inferior.
Ela tem seis botões de áreas, de One a Six, e quatro utilitários grandes à
direita. O projeto do usuário substitui essa região por iconbox, dois quadros de
áreas, bandeja 2 × 3 e dois botões laterais. O selo passa a ser GNU/LINUX; o
logotipo Hewlett-Packard não ocupa seu lugar. A primeira imagem tem **cinco**
desenhos de atalhos na faixa inferior, embora o texto do memorial enumere quatro
funções. O terceiro desenho não recebe uma função presumida.

Os botões na lateral direita são **▶ acima e ▲ abaixo**. Eles não devem ser
desenhados como duas setas verticais apenas porque o memorial usa a expressão
“paginação vertical”. As funções desses dois botões permanecem pendentes.

## Matriz da etapa de desenho

Cada evidência deve ser obtida do estado atual dos arquivos ou da execução
nativa. A existência de um teste ou manifesto, isoladamente, não comprova o
resultado visual.

| ID | Requisito | Evidência para concluir |
| --- | --- | --- |
| D0 | Manter o Plasma Style e o painel Irix Classic atuais como opção independente | Comparar hashes da base Classic; preservar seus IDs, defaults do tema global, `profiles.classic` e o mapeamento de migração do painel existente |
| D1 | Acrescentar o estilo e o applet com identidades próprias, instaláveis offline por usuário | Metadados descobertos como `IrixClassicDomainOS` e `org.irixclassic.domainos.panel`; catálogo e instalação em XDG temporário; configurações e layouts de outros perfis intactos |
| D2 | Unificar os contêineres em QML para a chapa formar dois andares contínuos | Captura nativa do mesmo componente usado pelo applet; comparar molduras, módulos, proporções e divisão 154/64 com a referência |
| D3 | Manter relógio circular azul, data monoespaçada de traços rígidos, gráfico azul/branco e correio exatamente na composição esquerda do projeto | Captura geral e detalhe; confirmar os quatro campos, desenhos e cores, sem trocar a face por um relógio digital ou medidor moderno; uma fonte/desenho bitmap local não altera a fonte global do usuário |
| D4 | Desenhar iconbox com sete itens e duas setas Motif laterais | Conferir a ordem `Desk`, `xterm`, `winterm`, `john`, `Index`, `Downl`, `xterm`, as etiquetas curtas e os ícones no padrão IRIX Classic |
| D5 | Desenhar dois quadros de áreas e miniaturas geométricas | Conferir `Work` e `Procrastination` no exemplo e a borda amarela do segundo quadro; identificar explicitamente os dados como ilustração do desenho |
| D6 | Desenhar bandeja compacta com seis ícones fixos e dois botões direitos | Conferir matriz 2 × 3, relevo, desenhos inspirados na referência HP e setas ▶/▲; não apresentar os ícones ilustrativos como status real de serviços |
| D7 | Preservar toda a faixa inferior, seus campos vazios e cinco atalhos | Captura com selo GNU/LINUX monocromático fosco, filetes horizontais, cinco desenhos centrais e indicador pequeno à direita; conferir os intervalos da referência |
| D8 | Usar a estética UNIX sóbria da referência e preservar os ícones IRIX fora dos elementos fixos | Paleta própria azul aço, chapa opaca e botões ortogonais; relevos por filetes sólidos, sem blur, cantos arredondados ou transições decorativas; círculos do relógio e dos desenhos originais permanecem |
| D9 | Verificar renderização nativa e estados visuais sem atribuir ações novas aos botões | Prints normal/pressionado/cancelado, geometria estável e logs sem erros QML; componente de produção compartilhado entre preview e applet; teste não chama aplicações, redes, bloqueio ou troca de área |
| D10 | Manter todas as funções ainda não confirmadas pendentes e todos os perfis protegidos | Revisão dos handlers e bindings, relatório de isolamento, invariantes de configurações reais e lista F abaixo; instalar recursos não altera quantidade/nomes de desktops nem substitui o painel em uso |

O nome mostrado é **Irix Classic DomainOS**. O diretório e o ID do estilo são
`IrixClassicDomainOS`; o applet usa `org.irixclassic.domainos.panel`. O catálogo
instala recursos adicionais sem mudar a escolha do perfil Classic. O esquema
KDE separado é **DomainOS SR14.4**, no arquivo `colors/DomainOS-SR14.4.colors`;
o usuário confirmou a identificação 14.4. Ele permite comparar as cores, e sua
instalação não autoriza aplicá-lo automaticamente aos aplicativos ou a outro
usuário.

## Funções pendentes: confirmação por botão e por ação

Todos os itens desta tabela estão **pendentes de confirmação**. A aprovação de
um item não aprova os vizinhos, todos os botões da faixa ou uma mudança de
configuração do KWin. Cada confirmação deve registrar a ação, o alvo e os
gestos autorizados antes de adicionar o handler. Pressionar e soltar para avaliar
apenas o relevo faz parte do teste do desenho.

| ID | Controle ou comportamento | Decisão que deve ser confirmada |
| --- | --- | --- |
| F01 | Selo GNU/LINUX | Selo inerte ou acesso à ajuda; qual aplicativo/comando e qual gesto |
| F02 | Relógio analógico | Fonte do horário, segundos visíveis ou não, fuso e comportamento de clique |
| F03 | Bloco de data/calendário | Idioma/formato rígido, aplicativo ou popup e gesto de abertura |
| F04 | Monitor gráfico | CPU, rede ou combinação; fontes reais, escalas, amostragem e ação ao clicar |
| F05 | Correio no bloco esquerdo | Aplicativo/conta/alvo, indicador real de correio e ação; o desenho não implica integração com uma conta |
| F06 | Entrada automática de janelas minimizadas na iconbox | Somente janelas minimizadas; filtros por tela/atividade/desktop, ordem e exclusão de launchers/startups; determinar a migração do gerenciador atual separadamente |
| F07 | Botão de uma janela na iconbox | Restaurar/ativar, clique simples ou duplo e foco; nenhuma ação de fechar é presumida |
| F08 | Menu, arrastar e gestos auxiliares da iconbox | Ações do menu contextual, arraste, botão do meio, roda e teclado, cada gesto aprovado separadamente |
| F09 | Seta esquerda da iconbox | Avançar por item ou página, limites e comportamento quando não houver conteúdo anterior |
| F10 | Seta direita da iconbox | Avançar por item ou página, limites e comportamento quando não houver conteúdo posterior |
| F11 | Quadro Work do pager | Qual desktop real representa; clique, teclado, seleção e eventual comportamento ao clicar no desktop atual |
| F12 | Quadro Procrastination do pager | Qual desktop real representa; clique, teclado e seleção |
| F13 | Quantidade e nomes de desktops | Confirmar explicitamente a criação/redução para dois e os nomes Work/Procrastination no KWin do usuário escolhido; não inferir autorização da ilustração |
| F14 | Miniaturas do pager e gestos adicionais | Geometria por tela, janelas visíveis/minimizadas, arraste entre áreas, roda e demais ações |
| F15 | Rede na bandeja | Fonte do status e popup/ação; confirmar separadamente qualquer alteração de conexão |
| F16 | Volume na bandeja | Fonte do status, popup e gestos; confirmar alterações de volume/mute |
| F17 | Correio na bandeja | Diferenciar deste desenho o correio F05; definir fonte, alvo e ação sem presumir duplicação |
| F18 | Armazenamento na bandeja | Fonte do status, popup e operações permitidas; nenhuma montagem/ejeção automática |
| F19 | Monitoramento na bandeja | Fonte do status e alvo/aplicativo da abertura |
| F20 | Sexto indicador da bandeja | Definir o significado do indicador circular verde e seus estados/ações |
| F21 | Botão ▶ na lateral direita | Determinar se pagina itens, expande ocultos ou executa outra ação; direção do desenho não define sua função |
| F22 | Botão ▲ na lateral direita | Determinar ação, relação com F21, limites e modo de fechar eventual popup |
| F23 | Política de itens da bandeja | Identificar os itens críticos e os itens “Sempre ocultos”; confirmar mudanças na seleção individual existente |
| F24 | Atalho inferior 1: terminal | Executável/alvo, argumentos e gesto de lançamento |
| F25 | Atalho inferior 2: paleta/ferramentas | Preferências ou outro utilitário; alvo e gesto |
| F26 | Atalho inferior 3: ferramenta retangular | Identidade e função a decidir; não omitir o quinto desenho nem transformar este em launcher por suposição |
| F27 | Atalho inferior 4: cadeado | Bloqueio ou outra função, método e gesto; não executar bloqueio nos testes do desenho |
| F28 | Atalho inferior 5: interrogação | Ajuda, alvo e gesto; confirmar se é distinto do selo F01 |
| F29 | Indicador pequeno à direita da faixa inferior | Significado, estados e eventual ação |
| F30 | Inserção/troca do painel na sessão real | Usuário, tela, altura, posição, substituição ou coexistência, preservação dos widgets/configurações e caminho de restauração |
| F31 | Alternância de Plasma Style e esquema de cores | Quais recursos mudar, seleção independente do tema global, comportamento da auditoria e restauração; sem reaplicar layouts |

## Plano de bindings nativos, depois das confirmações

### Janelas minimizadas

As fontes locais instaladas em
`/usr/lib/x86_64-linux-gnu/qt6/qml/org/kde/taskmanager/taskmanager.qmltypes` e o
applet atual `org.irixclassic.iconbox` expõem `TaskManager.TasksModel`.
`filterNotMinimized: true` elimina as janelas que **não** estão minimizadas. A
futura iconbox pode usar esse filtro, `launcherList: []` e
`TaskManager.TasksModel.GroupDisabled`, com exclusão explícita de entradas que
não tenham `IsWindow`/`IsMinimized`. Os filtros por desktop, atividade e tela
dependem de F06; não se devem escolher implicitamente.

Os roles `AppId`, `AppPid` e `WinIdList` permitem verificar a identidade das
janelas em testes privados. `Decoration` e o tema IRIX Classic fornecem os ícones
da iconbox. Depois de F07, `requestActivate(QModelIndex)` permite pedir a
ativação pela API nativa; os índices precisam vir do modelo atual, inclusive
depois de filtragem/remoção. Não reutilizar um índice de linha antigo como
identidade de janela.

O KWin já minimiza a janela e o modelo informa seu estado no X11 e no Wayland.
Assim, o comportamento descrito como “interceptar” ou “desviar” pode ser
implementado por observação do modelo e apresentação na iconbox. **Não é
necessário criar regras novas no KWin para ler janelas minimizadas.** Uma regra
extra só se justifica se uma ação futura aprovada exigir um comportamento que
essa API não forneça; seus parâmetros e seu efeito terão de ser confirmados.
A substituição do gerenciador de tarefas do painel é F06/F30, não um efeito da
instalação dos arquivos.

### Áreas de trabalho

`TaskManager.VirtualDesktopInfo` oferece `desktopIds`, `desktopNames`,
`numberOfDesktops` e `currentDesktop`. O backend de pager instalado em
`org.kde.plasma.private.pager` fornece `PagerModel`, um `TasksModel` por área e
geometria das janelas. A futura miniatura pode usar essas informações sem
renomear/criar áreas durante o carregamento do applet.

Work e Procrastination são rótulos da referência nesta fase. Quando F11–F14
forem aprovados, seus vínculos devem persistir **UUIDs/IDs reais estáveis** de
desktop. O gerenciador D-Bus do KWin em `/VirtualDesktopManager`, interface
`org.kde.KWin.VirtualDesktopManager`, fornece a lista `desktops` com posição,
ID e nome; `tools/classic_desktop.py:desktop_state()` já demonstra sua leitura.
Ela permite manter a identidade UUID separada da posição atual e do nome.

O backend de tarefas/pager pode fornecer um identificador nativo string ou um
número de área no X11. A tradução de um UUID aprovado para a posição/ID nativo
atual deve ser explícita e conferida no momento da ação. O nome mostrado não é
identidade, e um índice temporário 0/1 não comprova que um desktop representa
Work ou Procrastination. Após reordenação ou mudanças externas, resolver
novamente o UUID e sua correspondência no modelo antes de qualquer `changePage`;
nunca interpretar arbitrariamente o segundo desktop atual como Procrastination.
Se o UUID desaparecer ou o vínculo não puder ser verificado, não selecionar
outro desktop por aproximação de nome ou posição.

Forçar dois desktops ou alterar nomes modifica a sessão KWin do usuário alvo e
depende de F13. A presença de duas miniaturas no desenho não autoriza essa
mudança, nem garante que o perfil real tenha duas áreas. Não alterar o perfil de
outro usuário ou configurações compartilhadas.

### Bandeja

O wrapper Classic existente usa a bandeja C++ nativa e seu containment interno.
Isso mantém os applets e os StatusNotifierItems reais. O arquivo instalado
`org.kde.plasma.private.systemtray/contents/config/main.xml` expõe `hiddenItems`,
`shownItems`, `extraItems`, `showAllItems`, `scaleIconsToFit` e `iconSpacing`.
Ele **não** expõe chaves `rows=2` ou `iconSize=16`.

A apresentação instalada calcula `rowsOrColumns` pela espessura e, com
`scaleIconsToFit=false`, usa `Kirigami.Units.iconSizes.smallMedium` (22 px).
Portanto, inserir essas duas chaves inventadas em `appletsrc` não produz uma
grade estrita 2 × 3 com ícones de 16 px. A fase funcional precisa de uma
apresentação própria que retenha os modelos/containments nativos, fixe a grade
visual e implemente a paginação aprovada. A quantidade de linhas e o tamanho
dos ícones devem ser medidos no runtime, não inferidos do arquivo de
configuração.

Os ícones HP fixos do desenho não devem substituir silenciosamente bitmaps
próprios de aplicativos ou simular estados reais de conectividade. Associar
cada desenho a um status, popup ou ação é F15–F22. Filtrar aplicativos não
críticos é F23, preservando os itens e configurações individuais até aprovação.

## Verificação nativa e instalação independente

O preview deve instanciar o mesmo componente QML de composição usado pelo
applet. A galeria pode fornecer os sete itens, dois quadros e seis símbolos da
referência como fixtures explicitamente declaradas. O relatório deve dizer que
são dados de desenho, sem afirmar que houve identificação de janelas, troca de
desktop ou consulta de hardware.

A infraestrutura local possui PyQt6 QtQuick/QtQml, Qt Widgets/Test 6.8.2,
`plasmawindowed`, `xvfb-run` e `dbus-run-session`.
`plasma/tools/prever-painel.py` demonstra `QQmlApplicationEngine`,
`QQuickWindow.grabWindow()` e entrada de ponteiro via `QTest`. O novo runner
deve preparar XDG data/config/cache/state/runtime em `/tmp`, carregar o estilo
DomainOS nesse perfil privado e usar DBus privado sem diretórios de ativação.
Nenhuma ação de botão aprovada para uma fase futura deve ser chamada pelo
teste atual.

Para descoberta e renderização do pacote completo, a implementação usa
`plasma/tools/testar-domainos-package.py` e o interposer de teste
`plasma/tests/domainos-package-host.cpp`. O runner compila o observador Qt 6 e
executa `plasmawindowed org.irixclassic.domainos.panel` com o preload e os
caminhos `IRIX_DOMAINOS_CAPTURE`/`IRIX_DOMAINOS_REPORT`, dentro de Xvfb/DBus
privados. Ele verifica o `fullRepresentation` de produção, as imagens
carregadas e as famílias de fontes efetivamente resolvidas. A captura do pacote
é uma evidência adicional à galeria, não prova uma migração de painel real.
Atrasos de estabilização de captura pertencem somente ao teste; relevo de botão
no applet é derivado diretamente do estado pressionado.

O instalador declarativo pode copiar o novo estilo, o applet e eventual esquema
de cores para os destinos XDG do usuário. Instalar esses recursos não seleciona
o estilo, não recria layouts e não aplica um perfil global. Quando F31 autorizar
a seleção independente, a auditoria deverá reconhecer a variante opcional sem
substituir o default Classic; hoje ela compara a seleção diretamente com
`profiles.classic.plasma`. Uma futura migração precisa verificar e preservar
widgets, IDs, ordem, bandeja interna e configurações antes de alterar a sessão,
com restauração verificável conforme F30.
