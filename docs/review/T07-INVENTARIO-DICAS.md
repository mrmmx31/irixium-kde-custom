# T07 — cobertura de orientação

Recursos atribuídos e testes de integridade não substituem hover nativo nem avaliação humana.

| Grupo | Cobertura atual | Falta |
| --- | --- | --- |
| 1. Ações principais | Nove ações Motif com hover nativo | Layouts adicionais |
| 2. Seletores e medidas | Combo/Spin e campos; px e fatores explicados | Semântica dinâmica de cinco peças/eixos passou; hover das setas internas corrigido e comprovado em um layout/quatro paletas; Desfazer/campo/setas SpinBox desabilitados passaram; demais classes e layouts pendentes |
| 3. Ajuda | Dez assuntos × três níveis; navegação/cópia nativas | Entrega pessoal |
| 4. Seletor de arquivos | Onze componentes; quatro paletas; edição preservada; hover de filtro/caminho/Cancelar/Filtrar passou | Outros filhos e tamanhos de diálogo |
| 5. Menu de texto | Seis dicas; hover Copiar, posição e clipboard passaram em quatro paletas e após troca de papéis; popup e atalhos preservados | Demais ações/tamanhos. Popup automático: clique direito completo, hover/clique Copiar e troca visível passaram em quatro esquemas; Shift+F10 preservado; sem dica tardia1100ms |
| 6. Histórico e peças | Cinco ações de histórico usam helper UTF-8; quatro áreas roláveis e dicas internas conferidas | Hover das cinco ações passou nas quatro paletas; Dica de Desfazer desabilitado corrigida por observação do contêiner e clique segue bloqueado; campo/setas SpinBox desabilitados passaram. Demais controles/layouts |
| 7. Referência Motif | Dezesseis tipos, duas montagens | Outros tamanhos/estados |
| 8. Cena GTK3 | Dezesseis tipos; R59 passou 64/64 nos quatro cantos em 1280×800 e R72 passou 64/64 em 800×600. R81 validou provider isolado; R85 composição GTK3/CSS de usuário em cinco pares de papéis; R91 exportador GtkConfig real reemitiu GTK3/GTK4 em DomainOS e BreezeDark; R92 abriu dica nativa com as cores exportadas em processo novo; R112 passou os 16 tipos em BreezeDark com o tema DomainOS realmente selecionado. R116 revisou semanticamente os 16 textos e esclareceu “grupo de rádio” como opções mostradas na amostra. | As duas resoluções cobrem uma cena/layout. R91 cobre emissão de arquivos; R92 confirma consumo do esquema exportado; R112 combina os 16 tipos, hover real e pixels dos papéis Tooltip BreezeDark. Processo GTK3 já aberto manteve as cores anteriores mesmo após setGtkTheme; o fluxo do projeto pede reabertura dos apps GTK. Ainda faltam outras aplicações/estados e avaliação humana; matrizes de todas as paletas não foram combinadas. Adwaita/Sans 10 nos ensaios correspondentes; avisos não fatais Gdk.Screen.get_width/get_height permanecem. |
| 9. Cena GTK2 | Dezesseis tipos e 31 widgets/descendentes; R97 passou 64/64 em 1280×800; R98 passou os cinco casos focados; R106 passou 64/64 em 800×600 com quatro cantos reais; R107 passou oito casos em quatro papéis de cor; R108 passou gerador DomainOS real e hover nativo em três esquemas KDE; R113 passou os 16 tipos sob BreezeDark; R115 passou 48/48 (16 tipos × DomainOS, BreezeLight e BreezeDark) com pixels Tooltip correspondentes aos RCs gerados | R106 corrigiu o harness: a fixture GTK2 aplica `--button-x` e coloca controles junto à borda; dicas dentro da tela, sem cobrir o dono e fechando ao sair. Isso supera as falhas históricas de Progress apenas nas condições equivalentes testadas. R107 confirmou pixels Tooltip em fixtures RC, R108 usou o gerador para três esquemas num botão, e R115 combinou as três paletas geradas com a cena inteira de 16 tipos. Permanecem pendentes a troca/reexportação em processo GTK2 recém-aberto, outros layouts/aplicações/estados, comparação histórica e aprovação humana. Ver recibos R97/R98/R106/R107/R108/R113/R115. |
| 10. Demais galerias | GTK4 R56: 31/31 em 1280×800 e R64 31/31 em 800×600; R86 verificou Tooltip em cinco paletas (4.326 pixels de fundo e 43 de texto por captura); R87 revalidou hover após classe semântica: 31/31, atraso 500 ms, estabilidade 400 ms, dismiss ao sair, clique/rolagem nas duas barras verticais; R110 combinou hover real do helper GTK4 com leitura de pixels Tooltip em DomainOS, Irixium, BreezeLight e BreezeDark; R111 passou pelo export KDE real, refresh GTK4 e consumidor GTK4 novo sob BreezeDark; R114 passou 31/31 com o tema Reload realmente selecionado e CSS GTK4 atualizado pelo export BreezeDark; R119 tornou explícitos ação, faixa/unidade e página no hint do GtkScrollbar da sessão de preview; R123 validou o texto exato no popover vertical após 500 ms, geometria, roda e dismiss; R124 validou o Tooltip GTK nativo horizontal, texto idêntico, visibilidade entre 300–600 ms, estabilidade, geometria e dismiss; R120/R121 revisaram os hints QtQuick5/6, separando estados desabilitados e botão alternável; R127 encontrou o gap dos sete controles desabilitados do QtQuick5; R128 confirmou a rota passiva 7/7; R130 isolou-os em um ToolTip nativo próprio, preservou o atraso anexado e aprovou a matriz combinada de 27/27 alvos em QtQuick5 e QtQuick6, com atraso, estabilidade, geometria e dismiss; R131/R132 compararam pixels dos popups em DomainOS, BreezeLight, BreezeDark e Irixium, cobrindo a rota QtQuick5 separada e a dica QtQuick6 anexada; faltam outras posições e matrizes de paleta dos demais tipos; R48 cobre uma célula de tabela e as duas barras em QtQuick5/6. R88 adaptou dicas Qt Quick locais para papéis Tooltip e passou cinco paletas com hover real; R90 cobriu hover e cores da dica horizontal Qt Quick em cinco esquemas; Qt Widgets/Kvantum R55: menus Qt5/6 e R89 revalidou o help strip de submenu Qt6; R117 revisou seis descrições Qt6 que antes eram genéricas e validou 10 ações/8 linhas; R118 auditou Qt5 na mesma galeria e corrigiu texto de submenu específico da versão; 10 ações/8 linhas passaram; QtQuick5 R61/R62 e QtQuick6 R54/R63: 23/23 em 1280×800 e 800×600; Plasma R73: ScrollBar vertical/horizontal com dicas nativas de 500 ms, estáveis 400 ms, dentro da janela, sem cobrir as barras/rótulo e fechadas ao sair; R122: dimensões declaradas (15 px largura/altura), efeito do arraste e limite sem conteúdo real; ambas passaram hover, geometria e mudança de posição | R86/R110 cobrem pixels; R87 geometria GTK4 na paleta original; R114 combina matriz inteira e hover com o tema/código de paleta BreezeDark, sem captura de pixel de cada dica. R88 dica vertical Qt Quick e R90 dica horizontal continuam escopos diferentes. R89 cobre Qt6/QFusion apenas. R123 cobre o popover vertical e R124 o Tooltip nativo horizontal GTK4, cada caminho com seu recibo. Uma geometria por aplicação; R73 usou fallback BreezeLight, sem validar cores. Estados/paletas alternativos, demais controles/layouts Plasma, outras posições/paletas e aprovação manual continuam pendentes |

Atualização R103 (2026-10-19): GTK3 passou novamente 64/64 em Xephyr 800×600,
nos quatro cantos, cobrindo 16 controles com atraso de 500 ms, estabilidade de
400 ms, dica dentro da tela, sem sobreposição e fechamento ao sair. Fecha uma
segunda geometria para essa cena GTK3; não amplia a validação de paletas ou a
fidelidade visual. Recibo `T07-GTK3-HINTS-800X600-20261019-R103.json`; dados em
`~/tempia/t07-gtk3-800x600-r103-20261019/`.

Atualização R104 (2026-10-19): traversei a árvore nativa do Theme Lab em Xephyr
:83 e validei 178 controles interativos. Há 141 recursos de dica diretamente e
37 compostos com dica nas superfícies interativas internas; nenhum sem dica.
Isto cobre presença/ligação, não o texto semântico de cada dica nem hover manual
individual. Recibo `T07-MOTIF-INTERACTIVE-HINT-COVERAGE-20261019-R104.json`.

Atualização R106 (2026-10-19): GTK2 passou 64/64 em Xephyr 800×600, nos quatro
cantos, incluindo Progress inferior esquerdo e controles junto à borda direita.
O teste R105 foi interrompido após 31 casos porque o fixture não aplicava
`--button-x`; saída parcial preservada e excluída. Corrigida a fixture e validada
a posição direita por smoke test antes da matriz final. Recibo
`T07-GTK2-HINTS-800X600-20261019-R106.json`; dados em
`~/tempia/t07-gtk2-800x600-r106-20261019/`.

Atualização R107 (2026-10-19): em Xephyr :83/1280×800, oito dicas GTK2 nativas
passaram em dois contextos (diálogo separado e painel integrado) com fixtures
de papéis Tooltip DomainOS, BreezeLight, BreezeDark e amarelo sintético. Fundo e
texto tiveram pixels exatos, atraso 500 ms, estabilidade 400 ms, zero
interseção com o controle, tela respeitada e dismiss ao sair. Esta prova é de
renderização GTK2 sob RCs isoladas; não comprova que o gerador ou o tema GTK2
instalado acompanhe a troca de esquema KDE. Recibo
`T07-GTK2-HINT-PALETTES-20261019-R107.json`; dados em
`~/tempia/t07-gtk2-palettes-r107-20261019/`.

GTK1/GTK5 não recebem prévia substituta. O laboratório informa suporte conforme o runtime e o adaptador; não declarar dicas concluídas para uma família ainda ausente.

R82 tentou carregar a folha CSS DomainOS completa em cópia privada. A geometria
GTK3 passou, mas a captura da superfície manteve as cores DomainOS ao testar
Irixium; `Gtk.Settings` indicou Adwaita e a sonda não confirmou os papéis
efetivamente resolvidos. Status inconclusivo de harness, sem defeito atribuído
ao produto. [Recibo R82](T07-GTK3-THEME-CSS-20261018-R82.json); execução em
`~/tempia/t07-gtk3-tooltip-theme-css-20261018-r82/`. Antes de retomar, provar
as cores efetivas no `GtkStyleContext`.

Auditoria Motif: recursos e quatro paletas passaram; teste amplo de métricas passou em duas execuções após sincronizar a captura com eventos Xt/X11. Falha anterior preservada. [Recibo](T07-SINCRONIZACAO-PIXELS-MOTIF-20261011.json). Isso não certifica fidelidade histórica nem todos os layouts.

Estimativa histórica de 92% superada pelos recibos posteriores R55–R61. A etapa segue parcial: falta resolver ou delimitar a falha GTK2 R58, ampliar layouts/estados/paletas onde o inventário ainda limita a prova e obter avaliação/entrega humana. Percentuais são progresso de escopo técnico, não fidelidade visual.

Popup automático do editor corrigiu o percurso de mouse antes pendente: duas postagens completas por esquema passaram, com menu permanecendo aberto após soltar. [Recibo](T07-POPUP-AUTOMATICO-MOTIF-20261011.json). Estimativa técnica atual: cerca de 95% dos marcos de cobertura do T07; ainda há falha GTK2, limites de paleta/layout e entrega humana coordenada. Não representa fidelidade nem aprovação humana.

Atualização 2026-10-18 — GTK3 em viewport pequeno: R72 repetiu a matriz
completa em Xephyr :81 a 800×600. Os 16 controles foram colocados nos quatro
cantos e passaram 64/64 casos: dica nativa após 500 ms, geometria estável por
400 ms, dentro da tela, sem interseção com o controle e fechada ao sair. O
botão push continuou acionável após a dica. Execuções foram isoladas por HOME,
XDG e temporários privados; runtime GTK3 3.24.49, Adwaita/Sans 10, sem CSS
injetado ou troca de esquema. A resolução foi restaurada a 1280×800. Recibo
[`R72`](T07-GTK3-800X600-20261018-R72.json); matriz detalhada em
`~/tempia/t07-gtk3-small-viewport-20261019-r3/`. Duas tentativas anteriores
foram preservadas como diagnóstico de um ponto neutro `(0,0)` inadequado no
probe, sem as classificar como falha do produto. Isso completa apenas a
segunda geometria da mesma cena GTK3; paletas KDE, texto/pixels, outras
aplicações e aceite manual continuam pendentes.

Histórico: [prova nativa](T07-HOVER-HISTORICO-MOTIF-20261011.json). Uma montagem rolada, cinco ações habilitadas; ausência de popup no Desfazer desabilitado é limitação observada, não cobertura concluída.

[Dicas dinâmicas](T07-DICAS-DINAMICAS-MOTIF-20261011.json): recursos seguem a peça/eixo; unidade do relevo do cursor corrigida para pixels. SpinBox desenha setas internas, que não são filhos com dicas próprias: recursos dos campos não certificam hover dessas setas.

[Setas internas SpinBox](T07-DICAS-SETAS-SPINBOX-20261011.json): ponte restrita resolveu ausência nativa; dicas com atraso e papéis atuais, cliques de incremento/decremento e repetição preservados. A observação anterior de falta de cobertura permanece histórica, superada somente no escopo deste recibo.

[Desabilitados Motif](T07-DICAS-DESABILITADOS-MOTIF-20261011.json): ausência anterior no Undo foi resolvida; observação passiva dos ancestrais mantém bloqueio de input. Prova também cobre campo e região das setas do SpinBox desabilitado. Demais classes/gadgets/layouts não são certificados por analogia.


Atualização 2026-10-17 — Qt Widgets: as galerias Qt5 e Qt6 passaram com
36 botões e 10 QAction com hints; combos, spins inteiros/decimais, sliders
horizontais/verticais, campos de texto, editores e barras têm recursos verificados.
Hover cronometrado e geometria foram exercitados em botão, combo, os dois tipos
de spin e os dois eixos de slider. Foi reproduzida e corrigida a sobreposição da
dica sobre o slider vertical: a galeria reposiciona a dica nativa somente quando
ela cruza o controle; quando não há posição externa disponível, ela é ocultada.
Recebo `T07-QTWIDGETS-HINTS-20261017.json`. QFusionStyle limita a prova de
aparência; faltam hover de cada ação de menu, outras famílias/layouts e avaliação
manual.


Atualização 2026-10-17 — Qt Widgets: além da cobertura geral de dicas, hover
real de uma QAction alternável do menu passou em Qt5/Qt6. A dica não cobriu a
linha, ficou estável e fechou ao sair. A posição nativa da dica é movida somente
se cruzar o controle ou linha do menu; sem espaço livre, a dica se oculta.
Recibo `T07-QTWIDGETS-HINTS-20261017.json`; outras ações/layouts continuam
pendentes.


Atualização 2026-10-18 — GTK2: a atribuição nativa cobre 16 tipos/31 widgets;
hover frio passou em todos os 16 no Xephyr :74, com atraso 500 ms, dica dentro
da tela/fora do controle, estabilidade de 400 ms e dispensa ao sair. O botão
push continua acionável. Quatro fixtures de papéis (DomainOS, Breeze claro,
Breeze escuro e amarelo sintético) passaram em prévia acoplada e separada; os
pixels coincidem com os valores fornecidos à fixture. Isso valida o renderizador
nativo GTK2 com RC semântica, não a geração/instalação do esquema. Recibo
`T07-GTK2-HINTS-XEPHYR-RECHECK-20261018.json`; artefatos em
`~/tempia/t07-gtk2-hover-matrix-20261018-r2/` e
`~/tempia/t07-gtk2-tooltip-palettes-20261018-r2/`. T07 continua parcial.

Atualização 2026-10-18 — GTK3: o hover frio passou nos 16 tipos da fábrica
`NativeScene.factory`, em Xephyr :74. Cada dica apareceu após 500 ms, ficou
estável por 400 ms, dentro da tela e sem cobrir o controle, e fechou ao sair.
Uma fixture no harness foi ajustada para criar os campos Entry/Spin/Text sem
acionar edição; os widgets e as dicas continuam vindo da fábrica GTK3 real.
Resultado limitado a uma geometria por controle e à paleta ativa da sessão; não
mede texto/pixels renderizados nem a exportação de cores. Recibo
`T07-GTK3-HINTS-XEPHYR-20261018.json`; logs em
`~/tempia/t07-gtk3-hover-matrix-20261018-final/`. Estados alternativos,
paletas GTK3, outros layouts/famílias e avaliação humana continuam pendentes.

Atualização 2026-10-18 — GTK4: o probe em Xephyr :74 percorreu 31 alvos
visíveis com dicas nas duas páginas da galeria nativa. Os 31 exibiram e fecharam
a dica, ficaram dentro da tela e estáveis por 400 ms; o primeiro ciclo confirmou
500 ms de atraso frio. Não houve falha de exibição, mas duas barras verticais
ficaram parcialmente cobertas pela própria dica, sem cobrir o ponto do mouse.
Por isso a família permanece parcial até definir posicionamento ou documentar
esse limite. O alvo GtkListBox exigiu recorte da geometria à viewport; não era
um defeito da aplicação. O teste usou a paleta GTK ativa, não um esquema
alternativo. Recibo `T07-GTK4-HINTS-XEPHYR-20261018.json`; logs em
`~/tempia/t07-gtk4-hover-matrix-20261018/`.


Atualização 2026-10-18 — Qt6 Widgets: duas execuções isoladas tentaram
mostrar a dica de uma QAction com submenu após atraso de 700 ms. Ambas falharam
no item de menu 5 (`QToolTip.isVisible()` falso em
`probe_qt_full_gallery_hints.py:182`). O fallback experimental foi retirado;
`qt_widget_hints.py` voltou exatamente ao hash da versão registrada antes da
tentativa. Evidência: [recibo](T07-QT6-SUBMENU-HINTS-20261018.json) e logs em
`~/tempia/t07-qtwidgets-submenu-fallback-xephyr-20261018/` e
`~/tempia/t07-qtwidgets-submenu-fallback-xephyr-20261018-r2/`. Qt6 submenu
ainda parcial; nenhuma alteração de produção foi mantida.

Atualização 2026-10-18 — GTK4: com o barramento da sessão reutilizado, a matriz
no Xephyr :91 concluiu sem timeout: 31/31 alvos exibiram e fecharam dicas. As
duas dicas das barras verticais ainda cobrem a região da barra. Um protótipo
temporário de XMoveWindow colocou a primeira fora da barra, mas GTK4 reposicionou
a segunda durante o layout inicial; a geometria estável voltou a cruzar a barra.
O agregador do harness marcou incorretamente a não sobreposição usando a posição
transitória; o recibo recalcula a interseção a partir da geometria estável. O
worker foi restaurado byte a byte e nenhuma alteração de produto foi mantida.
T07 permanece parcial. Recibo
`T07-GTK4-X11-REPOSITION-20261018-R1.json`; logs em
`~/tempia/t07-gtk4-reuse-bus-20261018/`.

Atualização 2026-10-18 — a matriz agora verifica a interseção com o controle
durante a posição estável, não só ao aparecer. Em nova execução no mesmo
Xephyr, 29/31 alvos passaram; as duas barras verticais falharam porque a dica
estável cruza o controle. O runner reconheceu o resultado como parcial e saiu
normalmente. Nenhum código de produção foi alterado. Recibo
`T07-GTK4-STABLE-OVERLAP-20261018-R2.json`; saída em
`~/tempia/t07-gtk4-stable-overlap-20261018/`.

Atualização 2026-10-18 — GTK4: a galeria passou a usar popovers laterais para
dicas das barras verticais. A camada de âncoras não recebe eventos, os pais
com dica nativa são suprimidos apenas durante o hover da barra e restaurados ao
sair. Em Xephyr :76 (1280×800), a matriz passou 31/31 controles: atraso frio
500 ms, estabilidade 400 ms, fechamento ao sair e geometria dentro da tela. Nas
duas barras verticais, o clique com a dica aberta alterou a rolagem e a dica do
GtkScrolledWindow voltou após o ponteiro sair. Uma dica longa do campo inativo,
que ultrapassava a borda direita, foi encurtada; a matriz final não teve
overflow. Recibo
`T07-GTK4-POPOVER-PASS-THROUGH-20261018.json`; logs em
`~/tempia/t07-gtk4-popover-debug-20261018/`. É prova de interação e geometria
GTK4, não de cores alternativas ou fidelidade histórica. T07 segue parcial.


Atualização 2026-10-18 — GTK4, geometria estável R3: no Xephyr :92
(1600×1200), GTK 4.18.6, a posição medida do popover ficou ao lado das duas
barras verticais (13 px de separação); a matriz completa passou 31/31 alvos,
com 500 ms de atraso frio, 400 ms estáveis, sem cobrir o ponteiro, dentro da
tela e fechando ao sair. Cada barra vertical foi clicada a 75% do trilho com a
dica aberta; ambos os ajustes mudaram. Corrigi no worker o reset do teste por
alvo: o recibo anterior não tinha exercitado a segunda barra. Uma tentativa R4
com clique nos últimos 8 px falhou; o ponto interno de 75% passou nas duas.
`py_compile` passou. Os logs e hashes estão em
`review/T07-GTK4-STABLE-OVERLAP-20261018-R3.json` e
`~/tempia/t07-gtk4-stable-overlap-r3-20261018/`. O aviso D-Bus/inotify foi
registrado; a matriz terminou com código 0. Esta prova cobre uma geometria e
a paleta GTK padrão, não cores alternativas, fidelidade histórica ou revisão
humana. T07 permanece parcial.

Atualização 2026-10-18 — reabertura da sessão completa da galeria: em Xephyr
:67 com o tema DomainOS SR10.4 e esquema DomainOS-SR10-4, o lançador confirmou
22/22 verificações de sessão e janelas vivas GTK2/3/4, Qt5/6 e QtQuick5/6.
`tooltip_position.py` e `gtk4_hint_popover.py` foram copiados para a galeria
privada com SHA-256 idêntico aos módulos do workspace. Os logs não mostram
erro fatal de importação. Isso supera o bloqueio anterior de inicialização da
galeria completa para esta build. Não enviei hover ou clique porque esta sessão
está aberta para avaliação da pessoa; geometria GTK4 ainda aparece como 0×0 no
status de abertura e QtQuick6 registra `TabButton` com `y` nulo. O ensaio
confirma carga/importação, não atraso, estabilidade, texto/posição das dicas,
ou aceitação visual. Recibo
`T07-FULL-SESSION-XEPHYR-20261018-R1.json`; captura e logs privados em
`~/tempia/domainos-user-preview-20261018/session/`. T07 continua parcial.

Atualização 2026-10-18 — o status GTK4 era coletado dentro do callback de
ativação, antes do mapeamento; por isso a galeria podia reportar 0×0 embora
estivesse visível. O status agora é emitido por timeout GLib depois que o
loop principal processa o mapeamento, com alocação e timeout explicitamente
identificados. Em Xephyr :76, GTK 4.18.6 reportou janela mapeada 850×620 para
850×620 solicitados. `py_compile` e modo de verificação sem GUI passaram. O
probe ficou em HOME/DBus privados dentro de `~/tempia`; encerrei somente o
processo de teste e deixei o servidor Xephyr aberto. Recibo
`T07-GTK4-MAPPED-ALLOCATION-20261018-R43.json`. Isso corrige a medição de
inicialização, não testa dicas nem muda o tema; a prévia pessoal :67 conserva
os scripts copiados antes dessa alteração.

Complemento R43 — o probe usado pelo Theme Lab também aceitou o status novo em
Xephyr `:76`: execução passou, 53 recursos de dicas e 12 barras GTK4; o JSON
trouxe `mapped=true`, alocação 850×620 e nenhum timeout. O probe de integração
não pediu hover; não amplia a matriz de dicas. `TMPDIR` foi apontado para
`~/tempia` e o temporário do probe foi removido ao sair.

Atualização R44 — GTK4 pós-mapeamento e posição das dicas: o status e a inspeção
interna agora são adiados para depois de a janela receber geometria. Exceções
na inspeção tardia ficam registradas em vez de atravessar callback ctypes. O
probe de hover corrigiu a origem das coordenadas: `xdotool getwindowgeometry`
subia ao frame do Openbox e deslocava o ponto em 18 px; consultar o XID cliente
via `xwininfo` alinhou as posições. Na GTK 4.18.6 real em :76, janela 850×620,
o caminho de botão e linha de menu passou com dica externa, estável por 400 ms,
fechamento ao sair e clique/ação preservados. Matriz curta (um alvo em cada
página) passou e removeu/restaurou todas as âncoras. Recibo
`T07-GTK4-POSTMAP-HINTS-20261018-R44.json`, logs em
`~/tempia/t07-gtk4-postmap-r44-20261018/`. Limite: dois alvos de matriz e tema
GTK padrão; isso não comprova as 31 dicas novamente, outra paleta, pixels ou
fidelidade SR10.4. T07 continua parcial.

Atualização R45 — após R44, a matriz GTK4 completa foi repetida na Xephyr
privada `:76`: GTK 4.18.6, 53 recursos, 12 barras e 15 itens de menu; 31/31
alvos mapeados passaram nas duas páginas, com 500 ms de atraso frio, 400 ms
estáveis, dentro da tela, sem cobrir o ponto do mouse e fechando ao sair. A
dica externa das barras não impediu a rolagem; âncoras foram removidas e as
dicas nativas restauradas. Recibo
`T07-GTK4-FULL-MATRIX-20261018-R45.json`; resultado bruto em
`~/tempia/t07-gtk4-full-matrix-r45-20261018.json`. Limites: tema Default,
sem comparação de cores/pixels SR10.4, estados/layouts alternativos ou
aprovação humana. T07 permanece parcial.

Complemento R45 — Qt Widgets 5.15 e 6.8 foram executados em namespace privado
no Xephyr `:76`, usando a paleta DomainOS no perfil de teste. As duas versões
passaram os hovers cronometrados dos oito itens de menu visíveis, inclusive
ações habilitadas/desabilitadas, item alternável, submenu e filho: texto
correto, 400 ms estáveis, sem cobrir linha, dentro da tela e dispensando ao
sair. Qt6 usa faixa de ajuda atrasada para a ação-pai do submenu; a dica nativa
do filho a substitui ao entrar nele. Também passaram os hovers representativos
de botão, combo, spins inteiro/decimal e sliders horizontal/vertical. Recibo
`T07-QTWIDGETS-FULL-MENU-HINTS-20261018-R45.json`; saídas em
`~/tempia/t07-qt5-full-menus-r45-20261018/` e
`~/tempia/t07-qt6-full-menus-r45-20261018/`. Isso não valida a pintura
Kvantum nem substitui comparação histórica; T07 segue parcial.

Atualização R48 — QtQuick5/6, Xephyr privada `:76`: um delegate real da
TableView e as barras horizontal e vertical passaram em cada versão (3/3 por
versão). Sem dica aos 300 ms; exibição medida entre 650 e 850 ms, estável por
400 ms, dentro da tela e sem sobrepor o controle; fechou 250–300 ms após sair.
As coordenadas identificaram a área realmente visível do delegate e das barras.
Uma sonda Qt6 inicial falhou ao renomear controles dinâmicos; o diagnóstico
confirmou as três alocações visíveis e a sonda final, baseada na instrumentação
QtQuick6 já aprovada, passou. Avisos de inotify/portal e TabButton nulo ficaram
registrados como limites do ambiente/galeria, sem falha nos três alvos finais.
Recibo: [`T07-QTQUICK-TABLE-HOVER-20261018-R48.json`](T07-QTQUICK-TABLE-HOVER-20261018-R48.json);
saídas em `~/tempia/t07-qtquick-table-hover-r48-20261018/qt5/` e
`~/tempia/t07-qtquick-table-hover-r48-ref-20261018/qt6/`. Isso cobre somente
um delegate e as duas orientações; rolagem funcional, demais layouts/famílias,
comparação visual e aprovação humana continuam pendentes.

Atualização R47 — QtQuick5/6, Xephyr privada `:76`, esquema DomainOS em perfil
descartável: uma matriz de 18 alvos habilitados por versão (abas, controles da
página principal, botão de captura e editor multilinha) passou. A dica não
apareceu no ponto de 300 ms; a detecção ocorreu entre 700 e 900 ms desde o
movimento, permaneceu 400 ms estável, dentro da tela e fora do retângulo do
controle, e fechou em 150–350 ms após sair. Sete controles desabilitados por
versão foram excluídos: não recebem hover. Os totais de recursos (66/69) também
incluem células repetidas da TableView e barras; não foram usados como cobertura
de hover. Um diagnóstico confirmou que a troca das abas chega à página Tabela,
mas esta rodada não exercitou uma célula nem as duas barras. A primeira sonda
reutilizava nomes dinâmicos entre abas; a sonda corrigida R6 passou no QtQuick5.
QtQuick6 passou com a mesma regra de posição/estabilidade. Uma repetição Qt5
expirou no limite de 90 s e foi preservada; o recibo de sucesso usa a execução
R6 anterior, não a tentativa expirada. Evidência e hashes:
[`T07-QTQUICK-HOVER-20261018-R47.json`](T07-QTQUICK-HOVER-20261018-R47.json);
saídas completas em `~/tempia/t07-qtquick-controls-hover-r47-r6-20261018/qt5/`
e `~/tempia/t07-qtquick-controls-hover-r47-r4-20261018/qt6/`. Isso cobre
somente os alvos listados, não todas as dicas declaradas, menus, paletas ou
fidelidade visual/histórica. Próxima prova: delegate de tabela e barras
horizontal/vertical; T07 permanece parcial.

Atualização R49 — prévia completa aberta para avaliação manual em Xephyr `:71`
(1600×1000), com o pacote `0.2.12-beta.1`, tema global Irix Classic DomainOS,
esquema `DomainOS-SR10-4` e decoração DomainOS. Os 22 checks de isolamento e
inicialização passaram; GTK2/3/4, Qt5/6 e QtQuick5/6 estão abertos junto com o
Plasma/painel. A captura inicial foi conferida. Isso demonstra startup e
disponibilidade das galerias, não fidelidade visual nem aceite humano. A sessão
`:76` usada pelo trabalho T07 foi preservada; encerrei somente a antiga sonda
`:95` de menu Qt6 do T07 e deixei telas de outras tarefas intactas. Recibo:
[`T07-XEPHYR-USER-ADVANCE-20261018-R49.json`](T07-XEPHYR-USER-ADVANCE-20261018-R49.json).
Próximo: avaliação manual do usuário na `:71`; T07 continua parcial.


Atualização R51 — posicionamento das dicas GTK3, Xephyr própria :572:
A GTK 3.24.49 usava o GtkTooltip nativo, cuja janela cobria uma linha de pixel
do botão Push e Toggle quando o ponteiro ficava no centro. A correção associa
a janela nativa ao controle durante a consulta e, no map, move a mesma janela
para fora da área do controle pelo algoritmo comum; preserva o conteúdo, a
pintura/papéis GTK e o atraso. Se não houver espaço externo no monitor, oculta
a dica em vez de cobrir o controle. A matriz final passou 16/16 controles
(arrow, check, combo, entry, frame, list, progress, push, radio, escalas
h/v, barras h/v, spin, text e toggle): atraso nativo de 500 ms, área dentro
da tela, zero interseção, 400 ms estável e fechamento ao sair. Push ainda
acionou sua ação. As capturas confirmam o intervalo de 6 px no Push/Toggle.
A verificação do ponteiro no probe compara a posição pedida com XQuery antes
de contar ausência de dica. Foram preservadas tentativas inválidas e uma
oscilação isolada não reproduzida em R56, R57 (3/3) e R60. Recibo:
[`T07-GTK3-HINT-POSITION-20261018-R51.json`](T07-GTK3-HINT-POSITION-20261018-R51.json);
matriz e capturas em `~/tempia/t07-gtk3-r60-owned-xephyr-20261018/` e
`~/tempia/t07-gtk3-r55-owned-xephyr-20261018/`. Só uma geometria/paleta; sem
aprovação humana ou alegação de fidelidade histórica. T07 permanece parcial.

Atualização R52 — QtQuick5/6, dicas das barras do ScrollView: adicionei dicas
nativas às barras horizontal e vertical da página Scroll, com texto por eixo,
atraso de 750 ms e nomes de objeto exclusivos por versão. No Xephyr própria
:86, QtQuick5 5.15.15 passou 23 alvos habilitados; as duas barras apareceram
após 550–700 ms, ficaram estáveis por 400 ms e fecharam 150–250 ms após sair.
QtQuick6 6.8.2 passou especificamente as duas barras com 650 ms, estabilidade
de 400 ms e fechamento em 150–200 ms. A matriz QtQuick6 alcançou sete alvos e
o runner rejeitou a cobertura geral por exigir oito; portanto só as duas barras
estão certificadas nessa versão. Recibo
[`T07-QTQUICK-SCROLLVIEW-HINTS-20261018-R52.json`](T07-QTQUICK-SCROLLVIEW-HINTS-20261018-R52.json);
saídas e scripts em `~/tempia/t07-qtquick-scrollview-20261018/`. O runtime
reportou paleta Qt padrão/Fusion, sem a paleta KDE DomainOS; esta é uma prova
funcional das dicas, sem comparação de cores, fidelidade histórica ou aprovação
manual. QtQuick6 ainda emite aviso pré-existente/sem atribuição causal sobre
`TabButton.qml:22`. T07 segue parcial; faltam os demais controles/layouts,
outras famílias e avaliação humana.

Complemento R53 — rechecagem dirigida QtQuick6 6.8.2 em Xephyr própria :87:
os dois alvos que falharam na passagem ampla exploratória — checkbox Mixed
tristate e TextField editável — passaram quando localizados por nomes semânticos
estáveis: dicas após 700/650 ms, 400 ms estáveis e fechamento em 350/300 ms.
Isso reduz a evidência de falha para esses controles nesta execução, mas não
explica conclusivamente a divergência do probe amplo. Uma matriz subsequente
com visibilidade efetiva dos ancestrais alcançou sete alvos; não certifica a
cobertura total. A próxima sonda precisa selecionar páginas realmente visíveis
e preservar a identidade dos controles entre atualizações. Recibo
[`T07-QTQUICK6-RECHECK-20261018-R53.json`](T07-QTQUICK6-RECHECK-20261018-R53.json).
Paleta padrão Qt/Fusion; sem comparação de cores ou aprovação manual.


Atualização R54 — QtQuick6 6.8.2: a sonda temporária agora clica nas três abas nativas e confirma que `TabBar.currentIndex` e `StackLayout.currentIndex` coincidem antes de testar. Em Xephyr privada :400 (1280×800), 23 alvos habilitados passaram: 17 na página Controls, uma célula real e ambas as barras da TableView, além de TextArea e as duas barras do ScrollView. As dicas apareceram em 600–900 ms, ficaram estáveis por 400 ms e fecharam em 150–300 ms; zero falhas e zero alvos ignorados. Sete controles desabilitados foram registrados como não pairáveis. Isso corrige o subdimensionamento das matrizes R52/R53 e não altera a galeria de produção. O estilo QML KDE `org.kde.desktop` foi observado, mas as cores efetivas eram Qt padrão/Fusion; não comprova cores DomainOS nem fidelidade histórica. Persistiu aviso `TabButton.qml:22` sobre `y` nulo, sem impedir a navegação. T07 segue parcial. Recibo [`T07-QTQUICK6-FULL-MATRIX-20261018-R54.json`](T07-QTQUICK6-FULL-MATRIX-20261018-R54.json); sonda e logs em `~/tempia/t07-qtquick-scrollview-20261018/qt6-r54d-fullmatrix/`.

Atualização R55 — Qt Widgets/Kvantum: dica em menus não cobre opções — 2026-10-18

Corrigi a origem geométrica do proprietário da dica: menus Qt podem gerar a
QTipLabel sem encaminhar QEvent.ToolTip de forma consistente ao filtro global.
A galeria agora acompanha a superfície QMenu em Show e MouseMove e reposiciona a
dica sincronicamente no Show da QTipLabel, quando seu retângulo já está medido,
antes do primeiro desenho. A limpeza de proprietário ocorre ao fechar o menu.

Em Xephyr temporária limpa :81, Qt5 5.15.15 e Qt6 6.8.2 com
`Kvantum::Style`, esquema `DomainOS-SR10-4` e tema `DomainOS-SR10-4-KDE`, a dica
do item alternável apareceu fora do menu desde a primeira geometria observada,
ficou estável 400 ms, não alternou a ação e fechou ao sair. A matriz de galeria
completa passou nas duas versões: oito ações de menu por versão, combo, spins,
sliders, controles e diálogos; cada dica de menu ficou fora da linha e do menu,
estável e dispensada ao sair. Os testes de posição passaram 4/4 e a compilação
Python passou. A :81 foi encerrada. Recibo e hashes:
[`T07-QTWIDGETS-KVANTUM-MENU-HINT-20261018-R55.json`](T07-QTWIDGETS-KVANTUM-MENU-HINT-20261018-R55.json);
capturas e saídas integrais estão em
`~/tempia/t07-kvantum-native-hover-20261018/standalone-xephyr/`.

A tentativa inicial na :69 não recebeu eventos de ponteiro porque uma janela
InputOnly de 1600×1000 os interceptava; a prévia foi preservada. Isso foi
isolado do resultado, que passou na :81 limpa. T07 segue parcial: outras
famílias/layouts e revisão humana permanecem em aberto; esta prova não mede
fidelidade visual histórica.

Atualização R56 — GTK4: dica não cobre o controle nem seu painel — 2026-10-18

R3 deixou 30/33 alvos aprovados: o hint genérico de `GtkNotebook` cobria a
galeria, e o tooltip central do `GtkTextView` cobria o editor. Removi o hint do
contêiner; os rótulos de cada aba continuam com dicas individuais. Para lista e
editor, a galeria usa os popovers nativos adiados e anexa o editor quando sua
página oculta é mapeada. O worker agora exige ausência de interseção estável com
a região inteira do controle, qualquer que seja seu tamanho.

Em Xephyr privada `:81` (1280×800), GTK 4.18.6, passaram 31/31 alvos nas duas
páginas: 500 ms de atraso frio, estabilidade de 400 ms, dentro da tela, sem
cobrir o ponteiro ou a região dona, fechamento ao sair. As duas barras verticais
rolaram com as dicas abertas; os quatro popovers encerraram sem resíduos e os
tooltips nativos foram restaurados. UTF-8 passou em 52 recursos lógicos. Recibo
[`T07-GTK4-TOOLTIP-NONOVERLAP-20261018-R56.json`](T07-GTK4-TOOLTIP-NONOVERLAP-20261018-R56.json);
resultado integral em `~/tempia/t07-gtk4-hint-position-20261018/r4/`.

A sessão usou tema GTK `Default` e fonte Sans 10. O aviso D-Bus/inotify por
limite de arquivos continuou, mas os serviços exigidos ativaram e a matriz
terminou normalmente. Isso valida geometria/interação da galeria nessa sessão;
não cobre cores alternativas, fidelidade SR10.4, outras aplicações/layouts ou
aceite humano. T07 segue ativo para cobrir o restante de seu escopo.

Atualização R57 — GTK2/GTK3 em quatro bordas — 2026-10-18

A dica nativa longa do botão principal foi testada nos quatro cantos da tela
Xephyr :81 (1280×800): GTK2 2.24.33 e GTK3 3.24.49, oito casos no total.
Em todos, atraso frio de 500 ms, estabilidade de 400 ms, retângulo dentro da
tela e sem sobreposição ao botão; a dica fechou ao sair e o botão continuou
acionável. Recibo [`T07-GTK2-GTK3-EDGE-HINTS-20261018-R57.json`](T07-GTK2-GTK3-EDGE-HINTS-20261018-R57.json); resultados brutos em
`~/tempia/t07-gtk2-gtk3-edge-hints-20261018/`.

Escopo limitado a um botão por toolkit, um tamanho de janela e uma geometria
por canto; tema GTK Default, Sans 10. Não certifica os outros controles, cores,
aplicações/layouts, fidelidade histórica nem aprovação humana. Permanecem as
lacunas de estado e layout já listadas no inventário.

Complemento R58 — GTK2, 16 controles nas quatro posições — 2026-10-18

Em Xephyr :81 (1280×800), testei 16 tipos de controle em quatro posições
(64 casos): 63 passaram com atraso frio de 500 ms, estabilidade de 400 ms,
dica dentro da tela, sem cobrir o controle e fechamento ao sair. O único caso
falho foi `progress` no canto superior esquerdo; repetido mais três vezes,
falhou 3/3. O callback de dica foi alcançado, mas a janela `gtk-tooltip` não chegou a mapear. ProgressBars GTK2 isoladas, inclusive com o binder compartilhado,
mostraram dicas; a causa permanece restrita e não isolada à cena gerada/probe.
Não alterei código do tema. Recibo
[`T07-GTK2-EDGE-HINTS-ALL-CONTROLS-20261018-R58.json`](T07-GTK2-EDGE-HINTS-ALL-CONTROLS-20261018-R58.json); resultados em
`~/tempia/t07-gtk2-all-controls-edges-20261018/`.

Atualização R59 — GTK3, 16 controles nas quatro posições — 2026-10-18

Em Xephyr :81 (1280×800), 16 tipos de controle testados em quatro posições
(64 casos) passaram: atraso frio 500 ms, estabilidade 400 ms, dentro da tela,
sem sobrepor o controle e fechamento ao sair; o botão push continuou acionável.
Recibo [`T07-GTK3-EDGE-HINTS-ALL-CONTROLS-20261018-R59.json`](T07-GTK3-EDGE-HINTS-ALL-CONTROLS-20261018-R59.json); resultados em
`~/tempia/t07-gtk3-all-controls-edges-20261018/`. Todos os processos emitiram
o mesmo aviso não fatal de API depreciada `Gdk.Screen.get_width`; nenhum caso
falhou. Tema Default/Sans 10, um layout; não certifica cores, texto renderizado,
fidelidade histórica nem aprovação humana. A falha GTK2 R58 permanece em aberto.

Investigação R60 — GTK2 ProgressBar no canto superior esquerdo — 2026-10-18

A falha R58 continua no percurso da cena GTK2: uma repetição com espera de
2,5 s e três variações isolando a janela tooltip fictícia, LayoutGestures e
Placement não fizeram a dica aparecer. Em contrapartida, uma ProgressBar nativa
isolada com o mesmo binder, RC gerado, papéis do canvas, chamada de ensure_style,
size request e configuração pós-mapeamento mostrou a dica na mesma geometria.
Isso exclui uma falha geral da classe/binder, mas ainda não localiza a diferença
dentro de NativeSession ou do probe. Nenhum código de produto/teste foi alterado;
as sondas temporárias estão sob `~/tempia/t07-gtk2-all-controls-edges-20261018/`.
Recibo [`T07-GTK2-PROGRESS-HINT-ISOLATION-20261018-R60.json`](T07-GTK2-PROGRESS-HINT-ISOLATION-20261018-R60.json). GTK2 continua parcial.

Atualização R61 — QtQuick5 matriz completa — 2026-10-18

Na Xephyr :81 (1280×800), o probe clicou cada aba e confirmou que `TabBar` e
`StackLayout` ficaram no mesmo índice: Controls (17 alvos habilitados), Table
(uma célula e as barras horizontal/vertical) e Scroll (TextArea e as duas barras
do ScrollView). Foram 23/23 dicas ativas sem falhas ou alvos ignorados; sete
controles desabilitados foram registrados separadamente. Atraso declarado de
750 ms, aparecimento observado entre 750–900 ms, estabilidade de 400 ms e
dispensa em 150–300 ms. As geometrias passaram dentro da tela e fora do controle.
QtQuick 5.15.15/PyQt 5.15.11, XCB, HOME/XDG/DBus privados. O perfil solicitou
DomainOS-SR10.4, mas a paleta efetiva foi Qt/Fusion padrão; não há conclusão de
cor, aparência histórica ou aceite humano. Recibo
[`R61`](T07-QTQUICK5-FULL-MATRIX-20261018-R61.json); saída integral e captura em
`~/tempia/t07-qtquick5-full-matrix-20261018-r61/`. Nenhuma alteração de tema ou
produto. Próximo: seguir a outra lacuna T07 sem repetir R54/R61; R58/R60 continua
aberto sem hipótese discriminante para a cena GTK2.

Complementos R62/R63 — QtQuick5/6 em viewport 800×600 — 2026-10-18

Mantendo a mesma Xephyr da prova anterior, reduzi temporariamente o framebuffer
para 800×600 e restaurei 1280×800 ao terminar. QtQuick5 passou 23/23 alvos ativos
em R62 e QtQuick6 passou 23/23 em R63: abas/StackLayout sincronizados, sete
controles desabilitados à parte, nenhum skip/falha e dicas contidas na tela e fora
dos controles. Estabilidade 400 ms; Qt5 mostrou em 750–900 ms e fechou em
150–350 ms; Qt6 mostrou em 750–850 ms e fechou em 150–350 ms. Qt 5.15.15/PyQt
5.15.11 e Qt 6.8.2/PyQt 6.9.0. Qt6 manteve três avisos não fatais
`TabButton.qml:22` sobre `y` nulo. A paleta efetiva foi Qt/Fusion padrão nas duas
versões; sem alegação de cor, fidelidade histórica ou aceitação. Recibos
[`R62`](T07-QTQUICK5-800X600-20261018-R62.json) e
[`R63`](T07-QTQUICK6-800X600-20261018-R63.json), saídas sob `~/tempia/`.


Complemento R64 — GTK4 4.18.6 em viewport 800×600 — 2026-10-18

Após R56, repeti a matriz completa na Xephyr :81 em 800×600. Duas execuções
consecutivas passaram 31/31 (26 alvos na primeira página, cinco na segunda),
sem falha/skip: atraso frio 500 ms, estabilidade 400 ms, dentro da tela, sem
sobrepor o controle/ponteiro e fechando ao sair. As duas barras verticais
responderam ao clique com a dica aberta. Para corrigir os excessos encontrados
nas primeiras execuções, o botão de menu usa o popover atrasado; a lista ancora
pela região realmente visível no viewport rolável; controles quase tão largos
quanto a janela deixam margem no texto da dica; checkbox/radio usam textos
curtos. A coordenada é calculada na mesma janela nativa e a captura de movimento
usa fase capture para filhos internos. Recibo
[`R64`](T07-GTK4-800X600-20261018-R64.json), saídas e tentativas diagnósticas
em `~/tempia/t07-gtk4-800x600-*20261018*/`. Xephyr voltou a 1280×800.

Limites: tema GTK Default/Sans 10, uma galeria e uma geometria; sem comparação
de pixels/paletas ou aprovação humana. Ambos os processos registraram aviso não fatal do D-Bus sobre limite de inotify, mas todos os serviços foram ativados e
a prova terminou. GTK2 mantém a falha R58/R60; outras famílias/layouts e revisão
humana de T07 permanecem pendentes.

### R80 — papel de cor do hint Plasma — 2026-10-18

Em Qt 6.8.2, `Kirigami.Theme` do `QQC2.ToolTip` recebeu o papel Tooltip e seus
valores coincidiram com as quatro paletas de entrada. Contudo, inspeção do QML
resolvido (`org.kde.breeze/ToolTip.qml`), do objeto real e de uma captura da
tela mostrou que o `Rectangle` de fundo permanece em Window (papel 1). Em
Breeze Light, o pixel do popup foi `#eff0f1` em vez do papel Tooltip `#f7f7f7`;
em Breeze Dark foi `#202326` em vez de `#292c30`. Em DomainOS SR10.4 e Irixium,
Tooltip e Window coincidem, portanto não discriminam o erro. O texto foi
comparado pelo valor de `Kirigami.Theme.textColor`, sem captura de pixel isolada.
Não alterei Qt/KDE nem o produto. Evidência completa:
[`R80`](T07-PLASMA-TOOLTIP-PALETTE-20261018-R80.json), com scripts registrados
em T07 e capturas sob `~/tempia/t07-plasma-tooltip-colors-20261018-r80/`.
Essa descoberta não corrige o hint; qualquer implementação própria precisa de
escopo autorizado e deve continuar usando papéis dinâmicos. T07 permanece parcial.

Atualização R85 — GTK3 3.24.49, Xephyr privada :81: a fixture selecionou o tema
DomainOS pela configuração GTK, sem provider manual; o CSS de usuário importou
`colors.css` no caminho normal. Cinco pares de papéis (DomainOS, Irixium, Breeze
Light/Dark e amarelo sintético) passaram no estilo resolvido e nos pixels do
tooltip (29.966 de fundo e 238 de texto por captura), atraso de 500 ms,
estabilidade de 400 ms, posição sem sobreposição e dismiss ao sair. As cores
vieram de cópias privadas no formato da saída GTKConfig: não houve cinco trocas
reais do esquema nem execução do exportador. Uma galeria, um botão e avaliação
humana pendente. Recibo [R85](T07-GTK3-AUTO-THEME-USER-CSS-20261018-R85.json);
artefatos em `~/tempia/t07-gtk3-live-provider-20261018-r85/`.

Atualização R86 — GTK4 4.18.6: a dica lateral real do laboratório recebeu uma
classe CSS semântica e agora usa `tooltip_background_breeze` e
`tooltip_text_breeze`, incluindo borda derivada do papel de fundo. DomainOS,
Irixium, Breeze claro/escuro e amarelo sintético passaram na captura da
superfície nativa: 4.326 pixels de fundo, 43 de texto e dimensão 243×27 em cada
caso. A invocação direta do callback restringe esta prova a estilo/pixels; não
revalida atraso, geometria de hover ou fechamento. Recibo
[R86](T07-GTK4-POPOVER-TOOLTIP-ROLES-20261018-R86.json); artefatos em
`~/tempia/t07-gtk4-hint-colors-20261018-r86/`.

Atualização R87 — revalidação de interação após R86: a Xephyr privada `:83`
percorreu 31 alvos GTK4 nas duas páginas. Os 31 passaram com atraso frio de
500 ms, posição final estável por 400 ms, dentro da tela, sem cruzar o controle
nem o ponto do mouse e dismiss ao sair. As duas barras verticais foram clicadas
com a dica aberta e alteraram o ajuste de rolagem. Três dicas reposicionaram-se
durante o layout inicial e foram avaliadas pela posição estável final. Limite:
uma geometria, uma paleta ativa, galeria nativa; as cores são comprovadas
separadamente por R86. Xephyr `:83` encerrada após o teste. Recibo
[R87](T07-GTK4-HINT-HOVER-RECHECK-20261018-R87.json); artefatos em
`~/tempia/t07-gtk4-hover-recheck-20261018-r87/`.

Atualização R88 — Qt Quick: corrigi as dicas Qt Quick controladas pelo projeto
com `contentItem` e fundo explicitamente associados ao papel Tooltip. Em cinco
esquemas, fundo/texto capturados coincidiram com os papéis; hover, atraso,
estabilidade e fechamento passaram na galeria. O componente do tooltip do
`ConfigGeneral.qml` também passou em Breeze claro e amarelo numa fixture
isolada, acima do botão e sem cobri-lo. O KCM completo e a dica horizontal não
foram executados; o QML instalado do KDE permaneceu intacto. Recibo
[R88](T07-QTQUICK-TOOLTIP-ROLES-20261018-R88.json); artefatos em
`~/tempia/t07-qtquick-tooltip-role-20261018-r88/`.

Atualização R89 — Qt6 submenu: revalidei os arquivos atuais, que mudaram após
R4. A galeria completa passou em Xephyr `:83` com perfil bwrap privado e
Openbox somente nesse display: 36 botões, 65 widgets e oito linhas de menu,
incluindo submenu. A dica do pai apareceu após 500 ms, não cobriu a linha,
permaneceu estável por 400 ms com o filho aberto e cedeu à dica nativa do filho.
Um probe adicional confirmou que o texto original do QLabel retorna após sair
dos menus. A primeira execução sem gerenciador de janelas falhou antes do teste
de submenu por falta da dica inicial; com Openbox passou, portanto não atribuo
a falha ao produto. QFusion/Fusion: sem prova de cores KDE/Kvantum ou fidelidade
histórica. Recibo [R89](T07-QT6-SUBMENU-RECHECK-20261019-R89.json); artefatos
em `~/tempia/t07-qtwidgets-submenu-r5-xephyr-20261019/`.

Atualização R90 — Qt Quick, dica da barra horizontal: complementei R88, que
hoverou apenas a vertical. O runtime `org.kde.desktop` recebeu os papéis
Tooltip efetivos em Irixium, DomainOS, amarelo sintético, Breeze claro e escuro;
em cinco casos, `colorSet=Tooltip`, fundo/texto e pixels da dica coincidiram,
hover real apareceu após o atraso configurado, ficou abaixo da barra sem
cobri-la e fechou ao sair. O primeiro probe Irixium começou antes de o QML
mapear a janela; reexecução com 700 ms de estabilização passou e substitui
somente essa amostra inválida. Não houve mudança de fonte. Recibo
[R90](T07-QTQUICK-HORIZONTAL-HINT-20261019-R90.json); artefatos em
`~/tempia/t07-qtquick-horizontal-hint-r90-20261019/`. T07 segue parcial.


Atualização R83 — a folha CSS GTK3 completa agora foi carregada por provider isolado e os valores efetivos foram lidos em `GtkStyleContext`. O caminho do tooltip nativo é `tooltip:dir-ltr.background`; antes, o seletor `tooltip` perdia em especificidade para `.background`, mantendo a paleta DomainOS quando os papéis Tooltip eram diferentes. Ajustei os seletores e os descendentes para continuarem usando aliases KDE. DomainOS, Irixium, Breeze Light, Breeze Dark e amarelo sintético passaram em cinco casos: provider sem erros, papéis efetivos e pixels de fundo/texto coincidiram; atraso 500 ms, estabilidade 400 ms, sem sobreposição e dismiss ao sair. Recibo [R83](T07-GTK3-TOOLTIP-FULL-THEME-20261018-R83.json), artefatos em `~/tempia/t07-gtk3-theme-tooltip-effective-20261018-r83/`. Limite: aliases foram substituídos em cópias privadas, sem validar a reemissão pelo exportador/daemon instalado; um controle/layout e estado normal. T07 permanece parcial.

### Atualização R91/R92 — troca real de esquema GTK3 e GtkConfig — 2026-10-19

R91 confirmou que o módulo KDE GtkConfig reemite `gtk-3.0/colors.css` e
`gtk-4.0/colors.css` ao receber uma mudança nativa de `General/ColorScheme`:
DomainOS-SR10-4 e BreezeDark produziram os papéis Tooltip esperados e hashes
iguais entre as duas versões GTK. R92 usou esses arquivos em Xephyr `:83`:
a dica GTK3 nativa em processo novo acompanhou BreezeDark com 29.966 pixels de
fundo e 238 de texto, atraso 500 ms, estável 400 ms, sem sobreposição e fechada
ao sair. O processo já aberto manteve a paleta anterior mesmo após
`GtkConfig.setGtkTheme`; `tools/select_gtk.py` orienta reabrir os aplicativos GTK
para carregar todos os controles. Não tratei esse limite documentado como falha
de renderização. Nenhum arquivo pessoal ou de produto foi alterado. Recibos
[R91](T07-GTKCONFIG-REEXPORT-20261019-R91.json) e
[R92](T07-GTK3-SCHEME-REOPEN-20261019-R92.json); artefatos em
`~/tempia/t07-gtkconfig-reexport-20261019/` e
`~/tempia/t07-gtk3-live-reexport-r92-20261019/`. GTK2 Progress, demais
layouts/estados e avaliação humana continuam pendentes.


### Atualização R93 — GTK2 Progress em sessão Xephyr incompatível — 2026-10-19

Não contou como prova: numa Xephyr nova sem os serviços/configuração da sessão T07,
Progress em x=440/600 e push de referência falharam juntos. Xephyr :83 e Openbox
próprios foram encerrados. Manter R58/R74 como falhas observadas e R60 como
diagnóstico não conclusivo. Próximo diagnóstico: capturar eventos `query-tooltip`
e map/unmap em sessão equivalente, sem repetir a matriz completa.

Atualização R97/R98 — GTK2: com Openbox e XSettings privados ativos, os 16
controles passaram nas quatro regiões da tela 1280×800 (64/64), incluindo
ProgressBar e TextView. Em 800×600 passaram os dois locais Progress que haviam
falhado em R74, dois baselines push e TextView inferior esquerdo (5/5). A dica
apareceu após 500 ms, ficou estável 400 ms, permaneceu na tela, não cobriu o
controle e fechou ao sair. R74 permanece no histórico, mas sua falha Progress
não foi reproduzida. Tentativa R96 inválida por diretório gerado fora do
`~/tempia` do HOME privado foi excluída. Recibos
`T07-GTK2-HINTS-1280X800-20261019-R97.json` e
`T07-GTK2-PROGRESS-XEPHYR-20261019-R98.json`; logs e resultados em
`~/tempia/t07-gtk2-matrix-r97-20261019/` e
`~/tempia/t07-gtk2-progress-r98-20261019/`. Limite: paleta única; outros
layouts e avaliação humana continuam pendentes.

Atualização R99 — modelo Motif de ajuda: 10 assuntos × três níveis UTF-8
passaram; o teste de dicas nativas validou nove ações em atraso, estabilidade,
limites, sobreposição e dismiss; quatro esquemas passaram pela paleta de UI e
isolamento da paleta de prévia. GTK2/GTK3 factories atribuíram dicas a 13/30
widgets (sem prova temporal). O fixture de GTK3 ganhou o callback no-op
`bind_text_editor` exigido pelo factory atual.

R99 foi supersedido no escopo do Help por R102. A janela real no Xephyr :83 abriu
o cascade Ajuda, carregou assunto no diálogo, mostrou os três níveis e atualizou
o texto para Expert. A causa da falha anterior era o helper: coordenadas do
widget não incluíam o mapeamento/reparenting do WM e os itens do popup eram
calculados antes de a shell do menu se posicionar. O harness agora aguarda
700 ms pelo shell principal e 250 ms pelo popup, usa XTranslateCoordinates para
widgets com janela e mantém XtTranslateCoords para gadgets. O fluxo nativo
automatizado passou: assunto, níveis, seleção/cópia read-only, edição bloqueada,
fechar/reabrir e preservação do campo de projeto. Teste e binário foram compilados
com `-Werror`. O target `xvfb-run` ficou reabrindo servidores Xvfb sem executar o
filho; a verificação válida foi feita no Xephyr próprio com Openbox, não contar o
wrapper interrompido. Recibo `T07-MOTIF-UI-HINTS-20261019-R102.json`; evidências
em `~/tempia/t07-help-menu-manual-r102/`. Nenhuma alteração de produto ou perfil
pessoal. Resta cobrir outros layouts/famílias e revisão humana; T07 permanece
parcial.

Atualização R133/R134 — QtQuick5 e QtQuick6: os sete controles desabilitados
passaram em quatro esquemas por versão (56/56), com atraso, estabilidade,
geometria, dismiss e pixels do popup registrados. As primeiras tentativas
vazias foram uma corrida de materialização do probe e foram repetidas com espera
explícita. BreezeLight e BreezeDark mostram uma divergência semântica: o ToolTip
QtQuick5 usa o papel Tooltip; o ToolTip anexado QtQuick6 usa o papel Window.
Ativar o QPA KDE em R134 não resolveu a diferença. Falta identificar o
componente/papel efetivo de QtQuick6; não alterar cores com valores estáticos.
Recibos R133/R134; capturas e hashes listados em R133. R137 confirmou em hover
visível a divergência entre o ToolTip anexado (`Window`) e uma variante própria
que declara o papel Tooltip em todas as superfícies. A variante seguiu os papéis
dinâmicos nos quatro esquemas; só Breeze claro/escuro distinguem os papéis.
Ainda falta integrá-la a um controle real de produção e medir atraso, posição,
estabilidade e dismiss. Recibo R137. T07 segue parcial.

Atualização R138: numa cópia isolada da galeria de produção, um Button QtQuick6
real usou a dica própria com papéis Tooltip, atraso total de 750 ms, estabilidade
de 400 ms, posição acima sem cobrir o botão e dismiss 250 ms após sair. Os seis
hints anexados restantes mantiveram o comportamento e também passaram a matriz.
Isso prova o padrão em um controle, não sua integração no produto. Próximo:
avaliar um adaptador reutilizável QtQuick e validar posições/paletas antes de
qualquer mudança de produção. Recibo R138; T07 segue parcial.

Atualização R148 — QtQuick6/DomainOS: a galeria de produção tinha um gap de
evento nas dicas das barras. O `visibleChanged` do popup não atualizava o
diagnóstico do dono em todos os quatro scrollbars. Agora `hoveredChanged` no
ScrollBar prepara o papel Tooltip antes do atraso nativo, mantendo a conexão de
popup visível. Célula TableView e barras horizontal/vertical de TableView e
ScrollView passaram 5/5; `colorSet=4`, fundo `#78a0d5` e texto `#ffffff` iguais
ao papel ativo da paleta KDE DomainOS. R54 cobre a matriz hover/atraso anterior;
esta execução não repetiu a matriz inteira. O teste de galeria continuou até a
amostra de menu e falhou no hint de menu (código de menu inalterado; R141 tem
prova anterior). R149 da matriz completa expirou em 90 s com avisos do bus
privado sobre inotify/portal e não conta. Recibo
`T07-QTQUICK6-SCROLLBAR-TOOLTIP-ROLE-20261019-R148.json`; artefatos em
`~/tempia/t07-qtquick-attached-role-r139-20261019/final-qt6-domainos-r148-hover-role/`.
T07 segue parcial; não há avaliação visual humana.
