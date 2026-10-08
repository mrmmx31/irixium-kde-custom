# Irix Classic DomainOS: requisitos e critérios de verificação

O objetivo é acrescentar uma segunda opção de Plasma Style, chamada **Irix
Classic DomainOS**, e um painel unificado com a composição do projeto enviado
pelo usuário. O Irix Classic atual continua disponível como opção independente.
A referência original HP orienta a nitidez dos desenhos; o projeto do usuário
orienta a disposição, as proporções e os elementos presentes.

O desenho foi aprovado e sua renderização isolada foi verificada. A conexão
às cores KDE e a seleção simulada também estão implementadas e verificadas.
A próxima etapa conecta os componentes às funções reais. Cada nova função de
botão depende da confirmação do usuário antes de ser implementada; decisões
já confirmadas continuam válidas. Os requisitos funcionais abaixo permanecem
rastreados: uma captura ilustrativa não os implementa nem os comprova. Os
critérios D0–D10 descrevem a etapa de desenho, não todas as funções do memorial.
O texto atualizado para retomar o goal está em
[DOMAINOS-GOAL-ATUAL.txt](DOMAINOS-GOAL-ATUAL.txt).

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

### Ajuste de proporções solicitado durante a revisão no Xephyr

As tabelas acima registram as medidas do projeto inicial. Na revisão seguinte,
o usuário pediu ampliar os quatro instrumentos, reduzir a iconbox e igualar a
largura dos grupos esquerdo e direito. A geometria vigente mantém a chapa de
1942×218, com os módulos superiores em coordenadas locais:

| Módulo | X | Largura |
| --- | --- | --- |
| Quatro instrumentos | 4 | 668 |
| Iconbox | 672 | 594 |
| Pager | 1266 | 342 |
| Bandeja | 1608 | 202 |
| Setas direitas | 1810 | 124 |

Pager, bandeja e setas somam **668**, como o grupo esquerdo. Os quatro
instrumentos têm 166×150, posições X 4/170/336/502 e Y = 4. As molduras
encostam sem espaço vazio entre elas. O primeiro começa depois da lateral
ciano do chassi; o último termina na iconbox, e todos terminam na barra
metálica abaixo, sem uma segunda moldura do contêiner. Em 50% são botões de
83×75. Os desenhos são recentrados dentro dos botões. As faces originais
de data/gráfico têm 60×35 e a do Mail tem 56×27. A ampliação dos desenhos
segue aproximadamente a razão entre as alturas dos botões, 75/59, mantendo
os quatro botões e seus relevos inalterados. O relógio usa um canvas de
134×134 unidades, ou 67×67 pixels em 50%: o azul ocupa cerca de 61×61 e as
quatro marcas cardinais têm extensão de 62 pixels. Seus ponteiros afilados
compartilham o centro e têm raios aproximados de 27/18 pixels em 50%.
A face de data é 152×88,67 unidades, ou 76×44,33 pixels em 50%. Gráfico e
Mail usam caixas de 152×90 e 142×70, respectivamente, com `PreserveAspectFit`;
as faces pintadas medem 76×44,33 e 71×34,23 pixels em 50%, sem deformação.

A data carrega `contents/fonts/adobe-courier-bold-14.pcf` por `FontLoader`
privado do aplicativo: tamanho bitmap nativo 14, entrelinha fixa 17 e escala
uniforme `2*75/59` antes da escala do painel. A inscrição branca ocupa cerca
de 65×35 pixels na captura em 50%. O PCF Latin-1 vem de `font-adobe-75dpi`,
com licença e procedência em `contents/fonts/LICENSE` e
`contents/fonts/ORIGEM.json`; não instala fontes globalmente nem altera a
fonte escolhida pelo usuário. O [manual HP VUE2.01 do SR10.4](https://typewritten.org/Manual/Apollo/Domain%3AOS/SR10.4/man1X/vuestyle.bsd.html)
documenta Swiss742 Bold como fonte histórica de sistema, mas não confirma
o bitmap específico da data. Adobe Courier Bold é a experiência monoespaçada
solicitada pelo usuário, sem alegar reprodução exata da fonte da captura.
O texto usa `Text.NativeRendering`, `Text.PlainText` e `smooth: false`, com
estratégia padrão para respeitar as preferências nativas de Qt/Fontconfig.
Não há `antialiasing: false` forçado nem leitura/escrita de configurações
globais. O sampler de glifos NativeRendering do Qt 6.8 já usa Nearest;
`smooth` só controla imagens embutidas, não é tratado como correção de AA
dos glifos. O PCF permanece naturalmente binário mesmo com antialiasing
ativado. A preferência foi comprovada em OpenGL usando dois perfis privados
de Fontconfig e uma fonte vetorial de controle. Fonte, escala e entrelinha
são preservadas, sem timers ou auxiliares C++ adicionais.

O relevo dos instrumentos tem duas linhas claras no topo/esquerda e duas
escuras embaixo/direita em 50%, com perfil simples e quatro pixels entre as faces vizinhas,
como na referência HP. Os demais módulos superiores começam em Y = 8 e têm
altura 150, expondo suas duas linhas claras próprias abaixo do chassi ciano.
As molduras externas também são simples; os controles internos mantêm o
perfil composto. Os sete exemplos da iconbox ficam centrados, com botões
66×98 em Y = 26, intervalos iguais e bitmaps de 64×64 preservados. Os dois
cartões do pager têm 158×126, X = 8/176 e Y = 12; suas amostras ficam contidas
no mapa. A bandeja tem poço em Y = 14, linhas em 24/78, e as setas direitas
ficam em Y = 16/80, mantendo folgas verticais iguais.

O poço da bandeja fica centralizado, com folgas iguais à esquerda/direita e
acima/abaixo do grid. O indicador inferior mede 38×28, com aro interno 34×24
centralizado verticalmente na barra e 52 unidades afastado da direita. Na
escala 50%, o conjunto mede 19×14, com aro de 17×12 e distância de 26 pixels;
sua lente azul tem 13×7. O encaixe tem dois pixels de sombra acima/esquerda,
aro claro e sombra interna inferior/direita. A ampliação do encaixe preserva
a posição da lente.

O selo GNU/LINUX usa a paleta azul do corpo, substituindo a orientação anterior
de cinzas neutros. A revisão seguinte corrigiu a inversão: a inscrição bitmap
em duas linhas é escura sobre trama clara, sem retângulo sólido, e sua moldura
simples é elevada. O desenho das letras tem hastes uniformes e realce apenas
fora do contorno escuro. O desenho tem 20 pixels de altura, com três pixels
livres acima/abaixo na placa de 26 pixels e interlinha de um pixel. Ele mostra
apenas pressão/cancelamento; não abre ajuda.

A faixa metálica tem quatro sulcos centrais de três linhas, com caps e trama
acima/abaixo. Na revisão de altura, ela ocupa y = 158 a 210 (52 unidades;
26 pixels em 50%), com quatro pixels de trama acima e abaixo. O chassi termina
com friso ciano em y = 210 a 214 e sombra ciano em y = 214 a 218, dois pixels
cada em 50%. O contêiner dos quatro instrumentos ocupa 154 unidades de altura;
seus botões continuam com 150, assim como os demais módulos superiores.
Os conteúdos mantêm as margens equilibradas; o painel total continua 1942 × 218.
A faixa metálica ocupa X = 8 a 1934: 1926 unidades. As laterais do chassi têm
espaço próprio: em 50%, a direita apresenta dois pixels ciano e dois de sombra;
a esquerda, dois claros e dois ciano. O topo tem dois claros e dois ciano. O rodapé
mantém as mesmas cores e altura. A lente conserva sua folga interna de
26 pixels à direita. Não se repete o desenho dos riscos pela altura inteira. Os cinco
símbolos inferiores usam duas cores e canvases 32×24; terminal/teclado,
paleta com recortes, faixa de ferramentas, cadeado e interrogação seguem as
silhuetas da referência HP, sem atribuir ações por seu desenho.

A célula antes vazia em X = 587, largura 118 e altura 52 na faixa inferior
agora contém o botão `domainosApplicationsDrawer`. Seu `applications.svg`
de 32×24 desenha três janelas quadradas sobrepostas em `#3e536e`/`#c4d5ed`;
o QML exibe o símbolo em 64×48 unidades. O botão oferece apenas pressão e
cancelamento. O usuário propôs associar futuramente os aplicativos de
“pin to task manager” a essa gaveta, mas pediu aguardar seu documento antes
de implementar o comportamento. Essa função é F32; não altera os cinco
atalhos inferiores nem a iconbox de janelas minimizadas.

## Matriz da etapa de desenho

Cada evidência deve ser obtida do estado atual dos arquivos ou da execução
nativa. A existência de um teste ou manifesto, isoladamente, não comprova o
resultado visual.

| ID | Requisito | Evidência para concluir |
| --- | --- | --- |
| D0 | Manter o Plasma Style e o painel Irix Classic atuais como opção independente | Comparar hashes da base Classic; preservar seus IDs, defaults do tema global, `profiles.classic` e o mapeamento de migração do painel existente |
| D1 | Acrescentar o estilo e o applet com identidades próprias, instaláveis offline por usuário | Metadados descobertos como `IrixClassicDomainOS` e `org.irixclassic.domainos.panel`; catálogo e instalação em XDG temporário; configurações e layouts de outros perfis intactos |
| D2 | Unificar os contêineres em QML para a chapa formar dois andares contínuos | Captura nativa do mesmo componente; comparar molduras e módulos, metal de 26 pixels e rodapé ciano de 2 + 2 pixels em 50%, preservando o painel total |
| D3 | Manter relógio circular azul, data bitmap proporcional de traços rígidos, gráfico azul/branco e correio na composição esquerda do projeto | Captura geral e detalhe; confirmar os quatro campos, desenhos e cores, sem trocar a face por um relógio digital ou medidor moderno; registrar a experiência Courier solicitada pelo usuário e a família histórica provável Swiss742 e verificar o carregamento privado da fonte |
| D4 | Desenhar iconbox com sete itens e duas setas Motif laterais | Conferir a ordem `Desk`, `xterm`, `winterm`, `john`, `Index`, `Downl`, `xterm`, as etiquetas curtas e os ícones no padrão IRIX Classic |
| D5 | Desenhar dois quadros de áreas e miniaturas geométricas | Conferir `Work` e `Procrastination` no exemplo e a borda amarela do segundo quadro; identificar explicitamente os dados como ilustração do desenho |
| D6 | Desenhar bandeja compacta com seis ícones fixos e dois botões direitos | Conferir matriz 2 × 3, relevo, desenhos inspirados na referência HP e setas ▶/▲; não apresentar os ícones ilustrativos como status real de serviços |
| D7 | Preservar a faixa inferior, os espaços de chapa e os cinco atalhos, com a nova gaveta de aplicativos na célula anterior aos atalhos | Captura com selo GNU/LINUX escuro sobre trama clara e placa simples elevada; quatro sulcos centrais, símbolo da gaveta com três janelas, cinco desenhos de duas cores e lente com aro claro/sombra interna |
| D8 | Usar a estética UNIX sóbria da referência e preservar os ícones IRIX fora dos elementos fixos | Paleta própria azul aço, chapa opaca e botões ortogonais; relevos por filetes sólidos, sem blur, cantos arredondados ou transições decorativas; círculos do relógio e dos desenhos originais permanecem |
| D9 | Verificar renderização nativa e estados visuais sem atribuir ações novas aos botões | Prints normal/pressionado/cancelado, geometria estável e logs sem erros QML; componente de produção compartilhado entre preview e applet; teste não chama aplicações, redes, bloqueio ou troca de área |
| D10 | Manter todas as funções ainda não confirmadas pendentes e todos os perfis protegidos | Revisão dos handlers e bindings, relatório de isolamento, invariantes de configurações reais e lista F abaixo; instalar recursos não altera quantidade/nomes de desktops nem substitui o painel em uso |

O nome mostrado é **Irix Classic DomainOS**. O diretório e o ID do estilo são
`IrixClassicDomainOS`; o applet usa `org.irixclassic.domainos.panel`. O catálogo
instala recursos adicionais sem mudar a escolha do perfil Classic. O esquema
KDE separado é **DomainOS SR10.4**, no arquivo `colors/DomainOS-SR10.4.colors`;
o usuário confirmou a identificação 10.4 pela [referência VUE](https://virtualosmuseum.org/images/more_screenshots/Domain_OS%20SR10.4%20-%2001%20VUE%20desktop.png).
Ele permite comparar as cores, e sua
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
| F32 | Gaveta de aplicativos fixados | Aguardar o documento funcional do usuário para definir a associação de “pin to task manager”, os aplicativos, sua persistência e os gestos da gaveta; nesta etapa somente o desenho e o relevo de pressão/cancelamento |

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


## Protótipo aprovado e cópia congelada

O usuário aprovou o desenho com Courier bitmap em 08/10/2026 e solicitou
um backup acessível sem percorrer commits. A cópia foi criada antes da
conexão às cores do KDE em:

`/home/lsi/Downloads/backups/irix-classic-domainos-prototipo-aprovado-20261008-160442`

Essa pasta contém os fontes, prints, validações, ZIP e SHA256SUMS, foi
validada e está somente para leitura. **Não atualizar, substituir nem apagar
essa pasta ou seus arquivos.** Ela permanece como referência aprovada.
Qualquer revisão pertence à versão de trabalho; backups futuros devem usar
outra pasta. A conexão às cores será comparada com esse modelo, e a
substituição do painel em uso exige a aprovação final do usuário.

A conexão aos papéis nativos Window/Base/WindowText/Highlight/
HighlightedText já está implementada e verificada, recolorindo os mesmos SVGs.
Os relevos usam
profundidade tonal relativa à cor da janela, inclusive em esquemas escuros.
O modo de referência (`followSystemColors: false`) mantém os pixels aprovados.
Miniaturas, horário/data e dispositivos ainda são ilustrações; suas ações
continuam nas pendências F. Nenhuma sessão real deve ser alterada nesta fase.


## Seleção simulada autorizada na fase visual

Em 08/10/2026, o usuário solicitou simular a troca entre Work/Procrastination
e entre os itens da Iconbox. Essa autorização permite somente seleção dos
exemplos dentro da prévia, com índices locais independentes. Não autoriza
ativar janelas, trocar desktops reais ou substituir o painel da sessão.
`simulateSelection` permanece false por padrão no applet.

Após a comparação, o usuário preferiu restaurar a lâmpada e a moldura fina
amarelas do pager original (`#dddd28`), mantendo cabeçalho e texto normais.
Essa luz conserva sua cor nos esquemas já aprovados. Na orientação seguinte,
o usuário exigiu proteção do contraste em temas amarelos: se o fundo ou o
recesso amarelo esconderem a indicação, escolher outro tom do mesmo amarelo
considerando ambas as superfícies e os estados normal/pressionado. A proteção
acompanha somente a paleta, sem cálculos novos ao clicar. O modo de referência
continua usando a cor original. Somente a área ainda não
selecionada afunda enquanto pressionada; ao soltar, sobe e mantém a luz acesa.
A área já selecionada permanece elevada durante novos cliques. Arrastar para
fora cancela a pressão e preserva a seleção anterior. O relevo acompanha o
estado do mouse, sem timer, transição ou atraso artificial.

A Iconbox mantém a placa Highlight/HighlightedText e o relevo pressionado
persistente no item selecionado. Seu item anterior volta ao normal. A seleção
é confirmada ao soltar dentro do botão, e as proporções permanecem iguais.
O backup aprovado de Downloads permanece intocado.
