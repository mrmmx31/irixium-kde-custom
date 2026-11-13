# Índice de regras e continuidade DomainOS

Consultar ao iniciar ou retomar trabalho. A referência histórica é exclusivamente
Domain/OS SR10.4 com HP VUE 2.01. Ler a regra antes de alterar o desenho.

| Assunto | Fonte que deve orientar a implementação |
| --- | --- |
| Cores dinâmicas e exceções | [Regra de cores](DOMAINOS-REGRAS-CORES.md): todas as famílias seguem a paleta KDE; somente LED/Pager têm exceção com contraste. |
| Geometria, iluminação e rolagem | [Especificação](DOMAINOS-REGRAS-ROLAGEM.md) e [contrato único](../tools/domainos_scrollbar_rules.json). |
| Preferências já decididas | [Decisões consolidadas](DOMAINOS-DECISOES-CONSOLIDADAS.md) e [preferências](DOMAINOS-PREFERENCIAS.md). |
| Etapa ativa e defeitos pendentes | [Fila visual](DOMAINOS-FILA-REVISAO-VISUAL.md). Uma família por vez; fila atual da prancheta e GTK3 como primeiro tradutor visual. |
| Evidências e limites técnicos | [Matriz](DOMAINOS-MATRIZ-VALIDACAO-R2.md), [comparação GTK3](DOMAINOS-COMPARACAO-ROLAGEM-GTK3.md) e [cores das setas](DOMAINOS-CORES-SETAS-REVISAO.md). |
| Retorno do usuário | [Prancheta consolidada](DOMAINOS-PRANCHETA-UNIFICADA.md): cinco seções, incluindo Prancheta e pesquisa; revisões anteriores preservadas, abas/menu e respostas parciais em JSON. PR08 registra a arquitetura modular entregue. |
| Segurança de entrada de texto | [Regra obrigatória](../AGENTS.md), [edição/recuperação](../tools/work-board/README.md) e [prova corretiva](review/WORK-BOARD-EDICAO-20261010-R2.json). |
| Autorização das próximas tarefas | [Prancheta ativa](DOMAINOS-PRANCHETA-UNIFICADA.md): ler `ai-work-board/respostas.json`, autorização salva por item e revisão exata; fontes antigas são históricas. |
| Protocolos reutilizáveis por outras IAs | [Índice de skills](../skills/INDEX.md), com revisão visual e controle da sessão MAME existente. |
| VM histórica principal | [Regras da VM](DOMAINOS-REGRAS-VM.md), identidade do clone, caminhos persistentes, perfil, rede privada, captura do mouse, despertar físico e restauração; consulte também a [skill MAME](../skills/mame-live-control/SKILL.md) para inspeção e entrada interativa. |
| Distribuição atual das regras | [Recibo R2](review/DISTRIBUICAO-REGRAS-R2.json): índice, política de cores e skills no pacote; scripts preservados e pacote R1 intacto. |

A regra de cores nos limites da rolagem GTK3 foi aplicada e conferida em quatro
paletas. A execução atual segue a fila autorizada da prancheta Motif, que apoia
o laboratório de ajuste manual. I093 e I094 foram entregues; I096 é a próxima etapa
registrada, sujeita às respostas salvas. A moldura principal da tabela GTK3
preenchida permanece como o próximo ajuste visual do tema.
Documentação distribuída não equivale a auditoria concluída das demais famílias
ou aprovação visual do usuário.

## Laboratório de temas — nova etapa

A ferramenta Motif C99/MVC passa a integrar o goal em 2026-10-10.
[Escopo e arquitetura](DOMAINOS-LABORATORIO-TEMAS.md). O usuário conduz os
ajustes; receitas, medidas e evidências permanecem separadas. GTK3 é o primeiro
tradutor; a existência de uma prévia não comprova um adaptador concluído.

Prioridades da prancheta I094: [recibo e limites](review/WORK-BOARD-PRIORIDADES-20261010.json), contrato PRIORIDADES.md no AI Work Board. Instalação concluída; handoff lsi aguarda liberação temporária I093. Urgência não concede autorização.

I094 revisão 3: geometria vazia/maximizada corrigida, testada e instalada; a nova reabertura aguarda botão temporário. Consulte o recibo atualizado. Não inferir aceite humano pela entrega técnica.

I094 entregue no lsi com geometria corrigida e handoff preservado. I084 revisão 9 confirmado pela pessoa; próxima etapa autorizada I096 (fechamento manual urgente).

I086 entregue na sessão lsi: entrada direta, recuperação e renomeação solicitada
concluídas com registro humano/journal preservados. Novas propostas de PR01
revisão 3: I098/I099/I100 aguardam análise, sem autorização automática.
Consulte a fila e os recibos atuais antes de retomar etapas anteriores.

I088 revisão 4 entregue: ampliação por coluna e redimensionamento, vinte fluxos
Motif e regressão do Bate-papo. Reabertura pessoal concluída com journal e
registros humanos idênticos. [Recibo](review/WORK-BOARD-AMPLIAR-PAINEIS-20261010.json).
Avaliação humana pendente; consultar a fila e respostas atuais antes da etapa seguinte.

T09 — execução e recuperação: [perda do display/atualização](review/T09-PERDA-DISPLAY-20261011.json) e [journal durável/retomada de prévia](review/T09-RECUPERACAO-20261016.json). A build privada atual passou journal, editor real, crash/timeout, cancelamento, retomada explícita e grupos próprios. A repetição da perda de display ficou limitada pelo `/tmp` cheio; a evidência histórica permanece identificada com seu escopo. Não inferir avaliação visual ou entrega fora do Xephyr.

Laboratório: [preparação de entrega e dez grupos](DOMAINOS-LABORATORIO-ENTREGA.md). T10 final continua para o fim; inventário de runtime não conclui adaptadores ou aprovação visual.

T02 catálogo: [árvore e primeiro percurso nativo](review/T02-CATALOGO-ARVORE-20261011.json). Dados existentes de visibilidade/seleção/posições preservados; matriz de categorias, teclado e famílias ainda na fila.

T02 seleção de família: [defeito do callback e comparação de receitas](review/T02-CATALOGO-FAMILIAS-20261011.json). Ler limites do prefixo da matriz e do teclado; não converter o ensaio inteiro que falhou em aprovação.

T02 teclado: [matriz completa atual e ativação por Enter](review/T02-CATALOGO-TECLADO-20261011.json). Supera apenas os limites anteriores de catálogo/Espaço/Enter; não comprova teclado do combobox, entrega ou fidelidade.

T04 GTK2: [indicador nativo, paleta por geração e fluxo real](review/T04-GTK2-PROGRESS-20261011.json). Próximo: persistência da prévia separada. Controle nativo integrado não comprova adaptador completo ou fidelidade histórica.

I167 GTK2: [combobox/popup R36](review/I167-GTK2-COMBO-20261023-R36.json), [spin R37](review/I167-GTK2-SPIN-20261023-R37.json) e [recarga de paleta em janela aberta R55](review/I167-GTK2-PALETTE-RELOAD-20261024-R55.json) são passos técnicos isolados. R55 validou a atualização após evento GTK direcionado, mas não o emissor KDE/XSettings da sessão. R123 confirmou o plugin GTKConfig real em KDED restrito. R124 combinou plugin real, observador de produção e runtime GTK2: a janela GTK2 privada mudou 101.038 pixels e o fundo passou de RGB 120,160,213 para 209,67,91. O worker terminou com erro depois, na atualização GTK4: o `setGtkTheme` do pacote KDE escreve SettingsIni GTK3/4, mas o helper GTK4 verifica também o gtkrc GTK2 durante a alternância `-Reload`. Esse defeito cruzado foi só registrado; nenhuma implementação GTK4 foi alterada nesta etapa. Recibo [R124](review/I167-GTK2-KDED-OBSERVER-INTEGRATED-20261025-R124.json). Para GtkEntry, R68 mediu moldura de foco 2 px e R76 comparou caret GTK2 1×18 px com VUE (haste de 14 px, terminais de 5×1 px, total 16 px); o engine GTK2 comum não expressa os terminais. R86 encontrou a VM principal preta e o clone com VUE visível, mas sem GtkEntry focado. R87 confirmou que não há janela X acessível dos PIDs principal/clone; R88 repetiu o estado do clone com igualdade de pixels no diálogo e área útil. A única janela MAME pertence a outra sessão e foi preservada. Seleção e blink SR10.4 seguem sem comparação pareada. O spin usa a amostra Motif local do Theme Lab e não mede a VM SR10.4; integração pública e revisão histórica GTK2 continuam pendentes. O XChat permanece sem alteração até o fechamento dessa etapa.

R125 corrigiu a identificação da janela: o Find Files visível é o cliente XID `0x280008e`, dentro do frame `0x14000aa`, ambos `IsViewable`; `0x28000c3` é um auxiliar 5×5 desmapeado. A captura nativa atual torna possível continuar a comparação GtkEntry. Ela não prova foco/blink nem substitui a comparação pareada; consulte [R125](review/I167-GTK2-SR104-FINDFILES-20261025-R125.json). O timeout X 600/600 não foi demonstrado como causa do preto. Clone MAME permaneceu sem entrada do usuário ou alteração de configuração.

T04 persistência: [percurso nativo GTK3](review/T04-PREVIA-SEPARADA-GTK3-20261011.json), produto igual ao da entrega GTK2. Próxima entrada de texto exige Undo/Redo e atalhos antes de liberação; ausência de handler observada no código GTK3 requer prova nativa própria.

I167 GTK2 R126: [comparação pareada do GtkEntry em foco](review/I167-GTK2-ENTRY-FOCUSED-PAIR-20261025-R126.json). A VM SR10.4 voltou do quadro preto com um toque MAME de Shift liberado após um frame. A moldura 2 px coincide exatamente na alocação 338×34; a face VUE RGB 42,128,169 diverge do papel KDE View GTK2 RGB 102,136,181, que continua dinâmico. Investigar o color set VUE antes de alterar a tradução. A [errata R125/R126](review/I167-R125-EVIDENCE-ERRATUM-20261025-R126.json) registra que o arquivo de captura citado em R125 foi sobrescrito e não pôde ser recuperado; não usar seu hash antigo como prova presente.
R126 confirmou `Vuefile*secondaryColorSetId: 5` e o fundo global do resource database `#7848A075D500`; o arquivo Vuefile não contém RGB do campo. O diretório `~/.vue/palettes` existe, mas ainda falta listá-lo com sincronização confiável; a busca ampla em `/usr` não é evidência. Esse mapeamento precisa ser entendido antes de alterar GTK2.

I167 GTK2 R127: [blink VUE e consulta do ColorSet 5](review/I167-GTK2-ENTRY-VUE-BLINK-AND-COLORSET-20261025-R127.json). Seis amostras sem input confirmam alternância visível do cursor, mas não seu período exato. `~/.vue/palettes` está vazio; origem do ColorSet segue sem resolução. Captura mostra Find Files ainda ativo. Reutilizar R76/R116/R117; próximo localizar a origem VUE por consultas limitadas e retomar a comparação de seleção. Não alterar cores GTK2 por suposição.

I167 GTK2 R128: [paleta CoralReef e relação de cor do campo](review/I167-GTK2-ENTRY-VUE-PALETTE-20261025-R128.json). O perfil ativo aponta para `~/.vue/node_12345:0/palette.vue`; os valores correspondem a `/usr/X11/lib/vue/palettes/CoralReef.vp`. A face do campo é semelhante à quinta linha escurecida, mas o mapeamento de `secondaryColorSetId: 5` não foi provado. Não fixar RGB nem alterar a receita. Próximo verificar recursos nativos específicos ou continuar os estados do GtkEntry com essa incerteza explícita.
I167 GTK2 R129: [face dinâmica e seleção GTK2 do GtkEntry](review/I167-GTK2-ENTRY-VUE-DYNAMIC-HEADER-20261025-R129.json). A face deriva de uma sombra de 0,847 do papel `Header`; seleção invertida continua usando `View`. GTK2 2.24.33 passou em DomainOS, BreezeLight e BreezeDark, com cinco testes de runtime aprovados. Reutilizar R113/R115 para seleção VUE e R116/R117 para métricas; não repetir. R130 provou em GTK2-only o fluxo do plugin GTKConfig, observador de produção, RC dinâmico e repintura de janela aberta com 18 reloads. Aceite humano e adaptação GTK2 completa continuam pendentes; XChat intacto.

I167 GTK2 R131: [despertar controlado do clone SR10.4](review/I167-GTK2-SR104-DISPLAY-WAKE-20261025-R131.json). A tela preta voltou com um Shift de um quadro; o evento foi liberado em frame 2, frameskip 4 e sem throttle. Find Files está visível; nenhuma outra entrada foi enviada. A VM original e a outra sessão não foram tocadas. Próximo: comparação directa GTK2/SR10.4 de um controle ainda sem par.

I167 GTK2 R142 revalidou a disponibilidade: não há processo MAME ativo nem requisição pendente no canal do clone assistente; nenhuma entrada ou reinício foi enviado. Isso não invalida o wake feito pelo usuário, apenas registra que o clone autorizado não está rodando nesta verificação. Próximo: par GtkIconView/VUE para foco, hover e seleção por arrasto quando a mesma cópia estiver ativa. [R142](review/I167-GTK2-SR104-CLONE-AVAILABILITY-20261024-R142.json).

R143 esclarece que o filtro amplo `ps | rg` podia casar o próprio caminho `mame_control.py`; a consulta exata `ps -C mame,mame64,MAME -o pid,etime,comm,args` confirmou ausência do processo. Ver [errata](review/I167-GTK2-SR104-CLONE-AVAILABILITY-ERRATUM-20261024-R143.json).

R144 confirmou novamente a ausência do clone e que os três arquivos GTK2 cobertos por R140 continuam com os mesmos hashes. Não repeti testes sem mudança de entrada. O próximo passo é o par visual GtkIconView/VUE quando a cópia assistente autorizada estiver rodando. [R144](review/I167-GTK2-ICONVIEW-RESUME-GATE-20261024-R144.json).

I167 GTK2 R132: [papel Header dinâmico no botão habilitado](review/I167-GTK2-BUTTON-SR104-COLOR-ROLE-20261024-R132.json). 4 paletas, 24 capturas e prévia pública GTK2 acoplada/separada passaram; só o botão normal foi pareado à VM. Outros estados do botão e a revisão histórica GTK2 continuam abertos.
I167 GTK2 R133: [despertar e captura VUE após repouso](review/I167-GTK2-SR104-DISPLAY-WAKE-20261024-R133.json). Shift acordou a VM e Esc não fechou Find Files; o texto `aaa` permaneceu visível. Não tocar na VM original. Próximo: revelar a lista VUE para comparar GtkTreeView com SR10.4.

I167 GTK2 R231: [setas horizontais aparentam menores que no VUE](review/I167-GTK2-HORIZONTAL-ARROW-SIZE-20261026-R231.json). R224 validou a célula e o bitmap gerado, não o bbox horizontal independente no Trash Can. Medir o glyph a 1:1 e inspecionar clipping/overlay antes de alterar GTK2.
Theme Lab R232: [prévia GTK2 e galerias nativas indisponíveis](review/THEME-LAB-NATIVE-PREVIEW-ISOLATION-20261026-R232.json). A prévia separada recusa a sessão normal sem o namespace privado coordenado; a prévia GTK2 acoplada ainda não está mapeada no canvas. GTK2/GIR já estão instalados. Aguarda decisão sobre Xephyr isolado; nenhum código foi alterado.

I167 GTK2 R233/R234: as quatro células de seta normais da barra GTK2 coincidem
pixel a pixel com as células SR10.4 15×15 na prévia isolada; estados pressionado
e insensível e revisão visual humana continuam pendentes. Consulte
[R233](review/I167-GTK2-HORIZONTAL-ARROW-COMPARISON-20261026-R233.json) e
[R234](review/I167-GTK2-VERTICAL-ARROW-COMPARISON-20261026-R234.json). R246
preserva a nova percepção de brilho das faces da decoração, sem delta RGB nas
capturas existentes; não há base para fixar cor fora do esquema KDE.
[R246](review/I167-DOMAINOS-DECORATION-COLOR-FOLLOWUP-20261026-R246.json).
R262 confirmou as faces e os relevos na VM e no Xephyr :60. R271 mediu a face
ativa coral `#fe8282` na janela Wayland principal; o tom inativo nessa sessão
segue sem captura. [R262](review/I167-DOMAINOS-DECORATION-COLOR-RECHECK-20261026-R262.json),
[R271](review/I167-DOMAINOS-DECORATION-WAYLAND-ACTIVE-20261026-R271.json).
R258 acordou a VM preta com Shift liberado e mediu pequenos deslocamentos X/Y
sem clique. O alvo XmpIcon continua sem hover comprovado; não há mudança na
receita GTK2. [R258](review/I167-XMPICON-POINTER-AXIS-CALIBRATION-20261026-R258.json).
R272 adicionou seleção direcional à captura de setas da prévia GTK2. R273
executou as quatro direções em prévia separada e acoplada: 53 pixels mudam
enquanto pressionadas e a célula retorna exatamente ao soltá-la. A seta inferior
pressionada também coincide com R236; os outros três estados pressionados ainda
precisam de pareamento histórico. [R272](review/I167-GTK2-STEPPER-DIRECTION-CAPTURE-20261026-R272.json),
[R273](review/I167-GTK2-STEPPER-DIRECTION-STATES-20261026-R273.json).

R488 comprova as quatro direções GTK2 normal/pressionada/liberada em BreezeClassic,
BreezeDark e KvBeige (0/225 pixels por estado; 53 mudam ao pressionar, 0 após
soltar), contra os assets do próprio esquema. R489 confirma o probe do clone
assistente, mas a tela está preta; Q499 segue pendente e nenhuma entrada foi
enviada. A comparação histórica pressionada permanece aberta. [R488](review/I167-GTK2-ALTERNATE-SCHEMES-INTERACTION-MATRIX-20261027-R488.json),
[R489](review/I167-MAME-CURRENT-SCREEN-READONLY-20261027-R489.json).
R490 acrescenta 64 máscaras reais GTK2 normal/limite/insensível/backdrop em
quatro esquemas, todas iguais aos assets do próprio esquema; os estados não
equivalem a hover ou a pressão histórica no VUE. [R490](review/I167-GTK2-REAL-ENGINE-PALETTE-STATES-20261027-R490.json).
R491 comparou as quatro células normais do GTK2 real ao VUE em escala 1:1:
0/900 pixels diferentes, incluindo o registro direito corrigido x=526. Estados
de interação permanecem abertos. [R491](review/I167-GTK2-LIVE-ENGINE-NORMAL-CELLS-VUE-COMPARISON-20261027-R491.json).
Errata: R491 é fixture do Theme Lab, não runtime instalado. R492 incluiu o
recuo `trough-border=2`, removeu a faixa indevida de 11 pixels da seta inferior
normal/hover e obteve 0/225 em cada seta no GTK2 2.24.33 privado com arte
derivada dos papéis KDE. O renderer e a paleta foram instalados com backup;
readback do wrapper instalado também passou 0/225. Evento de recarga enviado a
181 janelas, sem reinícios; aceite visual pendente.
[R492](review/I167-GTK2-INSTALLED-DOWN-STEPPER-EDGE-20261027-R492.json).
R495 corrigiu a regressão de 11 pixels externos no asset inferior pressionado
introduzida na receita posterior: o delta normal/pressionado instalado voltou
a 53 pixels, todos no glyph central, como medido no VUE e registrado em R434.
Os papéis KDE seguem dinâmicos. Gerador e paleta foram atualizados no perfil do
usuário com backups; a recarga chegou a 130 janelas sem erros nem reinícios.
Suíte GTK2: 24/24. Revisão visual humana e os demais estados GTK2 continuam
abertos. [R495](review/I167-GTK2-DOWN-STEPPER-PRESSED-DELTA-REPAIR-20261027-R495.json).


I167 GTK2 R324: a cópia própria da VM está visível no HP VUE, mas a janela
File Manager mostra somente setas verticais; o recorte inferior é a fileira de
ícones. R305 continua provando match de 0/225 px por célula para as setas
normais, sem prova de estados pressionados ou da renderização GTK2 ao vivo.
Não mudar os assets por inferência; concluir a comparação horizontal e estados
com a prévia GTK2 isolada após escolha do usuário.
[R324](review/I167-GTK2-VUE-DESKTOP-20261026-R324.json).


I167 GTK2 R325: a seta vertical superior do File Manager VUE na VM viva coincide
0/225 pixels com o asset GTK2 de 15×15; a candidata inferior difere somente na primeira linha e não foi aceita como
par alinhado. Alt+V e F10 não abriram o menu, sem
alterar a janela. O alvo horizontal e a revisão interativa GTK2 ainda faltam.
[R325](review/I167-GTK2-LIVE-VUE-VERTICAL-ARROW-20261026-R325.json).

I167 GTK2 R326: GTK2 2.24.33 carregou por `Gtk.rc_parse` o wrapper instalado e,
separadamente, o include gerado. Ambos produziram métricas efetivas 11/15/2 em
GtkHScrollbar e GtkVScrollbar, embora o wrapper-base declare 16/16/0. Uma janela
GTK2 comparativa própria em Xephyr exibe as barras SR10.4 e viva a 1:1; a
avaliação visual do usuário segue pendente.
[R326](review/I167-GTK2-INSTALLED-RC-EFFECTIVE-METRICS-20261026-R326.json).

I167 GTK2 R327: `trough-under-steppers=false`, como na receita do Theme Lab,
altera a pintura nativa GTK2 sem mudar a geometria efetiva 11/15/2. O teste
isolado não prova melhora histórica: falta registrar a célula do widget contra
a referência SR10.4 nas coordenadas exatas. Não aplicar essa propriedade ao
tema instalado antes desse pareamento.
[R327](review/I167-GTK2-TROUGH-UNDER-STEPPERS-DIAGNOSTIC-20261026-R327.json).

Errata R327 / I167 R328: o pareamento a 1:1 confirmou que a candidata
`trough-under-steppers=false` piora as duas setas horizontais: 85/121 pixels
diferentes no tema instalado e 192/174 na candidata, em células de 225 pixels.
Mesmo buscando deslocamentos locais, a candidata fica com 138/132 diferenças,
contra 85/95. Rejeitar essa propriedade como correção. A causa restante está
na renderização efetiva do stepper GTK2 e segue em análise; nada foi instalado.
[R328](review/I167-GTK2-STEPPER-PROPERTY-EXACT-COMPARISON-20261026-R328.json).
R329 corrige a coordenada da célula direita conforme R296 (`x=526`, não
`x=527`): passam a valer 85/117 diferenças instaladas e 138/139 no melhor
alinhamento candidato; a conclusão não muda. [R329](review/I167-GTK2-RIGHT-ARROW-REGISTRATION-ERRATUM-20261026-R329.json).
I167 GTK2 R330: [análise da composição pixmap do stepper](review/I167-GTK2-STEPPER-OVERLAY-SOURCE-ANALYSIS-20261026-R330.json). As células 15×15 e sua composição alpha centrada coincidem com SR10.4; causa de runtime ainda aberta.
I167 GTK2 R331 identificou o redimensionamento indevido de 15×15 para 15×11 pelo pixmap engine quando a imagem completa era declarada como `file`. R332 aplica `overlay_file` sem esticar em 20 regras de estado/direção, preservando os parâmetros nativos 11/15/2, a alocação 54×15/15×54 e o recuo. Os quatro controles incrementam/decrementam enquanto pressionados e retornam à imagem normal ao soltar. Receita GTK2 base e KDE, manifesto e perfil do usuário foram alinhados; paleta KDE foi regenerada com sucesso. Permanecem pareamento visual no aplicativo real e diferença residual de registro na célula horizontal direita. [R332](review/I167-GTK2-STEPPER-OVERLAY-INSTALL-20261027-R332.json).
I167 GTK2 R333: instância assistente correta identificada (PID 3971377, disco canônico); VM sem pausa, frameskip 4, throttle desligado, mouse desacoplado e ponte limpa. Snapshot nativo está escuro, sem VUE/barra visível. A outra VM (prancheta) usa disco distinto e ficou intocada. Nenhum evento foi enviado porque o foco Wayland/XWayland ativo não pôde ser autenticado/restaurado com segurança. R332 continua provando a integração GTK2 isolada; falta nova captura histórica viva para inspeção visual final. [R333](review/I167-DOMAINOS-LIVE-STATE-WAKE-20261027-R333.json).
I167 GTK2 R365: corrigida no gerador a composição dos quatro pixels externos das células horizontais normais via trough ativo e papéis KDE. Probe coincide 0/225 em ambas as células com a referência viva SR10.4; testes GTK2 7/7. Não instalado nem aceito visualmente; estados restantes e validação humana continuam abertos. [R365](review/I167-GTK2-ACTIVE-TROUGH-CORNER-FIX-20261027-R365.json).
I167 GTK2 R368 corrige R365: a regra ACTIVE foi separada por orientação para não afetar a vertical. O probe do gerador real mantém as células horizontais em 0/225 e a barra vertical em 0/8145 diferenças contra o controle sem derivação. Persistem 3/225 diferenças na seta vertical superior, também presentes no controle. 7/7 testes; nada instalado ou aceito visualmente. [R368](review/I167-GTK2-STEPPER-ORIENTATION-ISOLATION-20261027-R368.json).
I167 GTK2 R370 resolve os três cantos externos da seta vertical superior com um asset ACTIVE por orientação e amostras derivadas da paleta KDE: célula VUE/GTK2 em 0/225 diferenças. As duas células horizontais seguem 0/225. A seta inferior continua sem registro confiável; nenhuma instalação ou entrada na VM. [R370](review/I167-GTK2-VERTICAL-UP-STEPPER-CORNERS-20261027-R370.json).
I167 GTK2 R372 compara a máscara normal/pressionada da seta inferior gerada com o ciclo SR10.4: 53 pixels alterados nas mesmas coordenadas; prova de assets, sem interação GTK/VM ao vivo. [R372](review/I167-GTK2-DOWN-STEPPER-PRESS-TRANSITION-20261027-R372.json).
I167 GTK2 R374 valida a seta inferior pressionada no runtime GTK2/Xvfb privado: 53 pixels do glyph mudam, faixa externa estável, 0/225 contra assets normal/pressionado/solto. Sem aplicação real ou VM. [R374](review/I167-GTK2-DOWN-STEPPER-HELD-XVFB-20261027-R374.json).
I167 GTK2 R375: seta superior normal/pressionada/solta coincide com assets a 0/225 em GTK2/Xvfb; 46 pixels visíveis do ciclo SR10.4 mantêm pares RGB exatos. Referência histórica retida, não captura VM nova. [R375](review/I167-GTK2-UP-STEPPER-HELD-XVFB-20261027-R375.json).
I167 GTK2 R378 comprova left/right normais, pressionadas e soltas em 0/225 contra assets gerados; 53 pixels no hold e restauração exata. Celulas registradas em x=2/526; a captura VM atual está preta, sem novo dado histórico horizontal. [R378](review/I167-GTK2-HORIZONTAL-STEPPER-HELD-XVFB-20261027-R378.json).
I167 GTK2 R379 encontra 8 pixels de diferença nas quatro células INSENSITIVE contra seus assets gerados; discrepâncias nos cantos externos servidos pelo underlay. Aparência histórica desabilitada segue não verificada. [R379](review/I167-GTK2-DISABLED-STEPPER-UNDERLAY-20261027-R379.json).
I167 GTK2 R380 corrige a composição dos cantos INSENSITIVE: underlays separados por orientação usam pixels dos assets direcionais desabilitados gerados dos papéis KDE. GTK2 2.24.33/Xvfb coincide 0/225 nas quatro setas; suíte 8/8. Aparência XtInsensitive histórica ainda não verificada. Nada instalado nem VM alterada. [R380](review/I167-GTK2-DISABLED-STEPPER-UNDERLAY-FIX-20261027-R380.json).
I167 R381: após nova observação, a tela do clone assistente estava em repouso; Shift de um quadro via campo do MAME restaurou VUE e foi liberado, sem reinício, captura de mouse ou alteração do perfil. [R381](review/I167-MAME-SCREEN-WAKE-RECHECK-20261027-R381.json).
I167 GTK2 R382 compara novamente as quatro células normais na captura nativa viva do Trash Can: 0/225 em cada direção contra os assets DomainOS. Nenhum clique; estados pressed/disabled históricos continuam fora deste recibo. [R382](review/I167-GTK2-LIVE-NORMAL-STEPPERS-20261027-R382.json).
I167 GTK2 R383: hover PRELIGHT real em Xvfb casa 0/225 com os assets gerados. A arte PRELIGHT de left/right/up é igual à normal; apenas down muda 11 pixels. Sem comparação VUE hover, isso fica como assimetria candidata e não autoriza alteração. [R383](review/I167-GTK2-STEPPER-HOVER-PRELIGHT-XVFB-20261027-R383.json).
I167 R384 confirma VUE visível no clone canônico e mouse desacoplado, mas sem ponteiro sobre alvo; nenhum evento enviado. R385 rastreia a diferença PRELIGHT inferior ao reparo de borda que atualiza normal/pressed, mas não focused, embora os assets de origem sejam iguais. Defeito da receita registrado antes da correção; hover histórico continua sem prova. [R384](review/I167-MAME-CURRENT-FRAME-20261027-R384.json), [R385](review/I167-GTK2-PRELIGHT-EDGE-ASYMMETRY-20261027-R385.json).
I167 R386 aplica a mesma banda role-derived ao down PRELIGHT e mantém a mesma saída visual entre NORMAL/PRELIGHT em duas paletas; oito testes da geração GTK2 passaram. Ainda sem captura de hover pós-correção no runtime e sem prova histórica VUE. [R386](review/I167-GTK2-PRELIGHT-EDGE-CONSISTENCY-20261027-R386.json).
I167 R387 confirma no runtime GTK2 2.24.33/Xvfb que hover das quatro setas coincide 0/225 com os assets NORMAL e PRELIGHT; o salto de 11 pixels em down de R383 foi eliminado. Sem comparação de hover na VM. [R387](review/I167-GTK2-PRELIGHT-RUNTIME-RECHECK-20261027-R387.json).
I167 R388 revalida o perfil do usuário: tema DomainOS selecionado, métricas GTK2 15/11/2 e quatro células normais 15×15 iguais à origem atual. Arquivos atuais não provam o tema já carregado em janelas abertas; revisão de aplicação continua aberta. [R388](review/I167-GTK2-USER-PROFILE-GEOMETRY-20261027-R388.json).
I167 R393 confirma que um pulso de Shift de um quadro via ponte MAME acordou esta cópia SR10.4 e foi liberado, sem mudar perfil; classificar como entrada injetada, não física. R394 confirma que o GTK2 2.24.33 recém-aberto com o tema instalado selecionado coincide 0/225 nas quatro células normais com a referência VUE. A seta menor relatada não se reproduz neste renderer; XChat aberto pode manter recursos antigos em memória. [R393](review/I167-MAME-SCREEN-WAKE-RECHECK-20261027-R393.json), [R394](review/I167-GTK2-INSTALLED-THEME-STEPPERS-20261027-R394.json).
I167 R395 registra que os XChat abertos iniciaram antes da atualização do gtkrc selecionado. Estilo antigo em memória é uma hipótese plausível, não confirmada; não capturei conversa ou janela, nem reiniciei aplicações. [R395](review/I167-GTK2-OPEN-PROCESS-TIMING-20261027-R395.json).
I167 R440 deriva o estado pressionado horizontal GTK2 pela troca de luz/sombra do contrato e o compara aos assets (0/225); é inferência de desenho, não captura pressionada do VUE. R441 adiciona uma prancheta visual legível com normal VUE/GTK2 pareado e assets pressionados GTK2 explicitamente identificados; não amplia a prova de pixels nem registra avaliação humana. A seta horizontal pressionada no convidado e a revisão visual continuam pendentes. [R440](review/I167-GTK2-HORIZONTAL-HELD-CONTRACT-DERIVATION-20261027-R440.json), [R441](review/I167-GTK2-HORIZONTAL-ARROW-REVIEW-AID-20261027-R441.json).
I167 R444 é uma captura somente de leitura atual: a área do desktop convidado está uniformemente preta, sem alvo GTK2/VUE; R437 anterior tinha desktop visível e barra horizontal. Perfil preservado e sem entrada. A guarda de segurança ainda detecta o MAME separado da prancheta, portanto não tentei acordar o convidado. [R444](review/I167-DOMAINOS-CURRENT-SCREEN-READONLY-20261027-R444.json).
I167 R445 é uma revalidação somente de leitura pixel-idêntica à R444: o convidado permanece preto; perfil 4/sem throttle, sem pausa, sem captura ou pedido pendente. A VM da Prancheta permanece ativa e a guarda de entrada bloqueia ações gráficas. Nenhum input foi enviado. Comparação GTK2 horizontal pressionada segue pendente. [R445](review/I167-DOMAINOS-CURRENT-SCREEN-READONLY-20261027-R445.json).
I167 R446 confirma por Telnet que o Domain/OS e a sessão X/VUE seguem ativos, com 31 filhos na raiz. `xset q` mostra blanking com timeout de 600 s; isso é compatível com, mas não prova, a causa da captura preta. Consulta sem entrada ou alteração de configuração. A VM separada segue bloqueando o teste gráfico. [R446](review/I167-DOMAINOS-X11-SCREENSAVER-STATUS-20261027-R446.json).
I167 R448 confirma que os `gtkrc` instalados incluem exatamente o bloco gerenciado de paleta KDE sobre a receita base do repositório; os dois perfis instalados coincidem e o journal preserva o hash-base correto. A diferença é esperada, não um desvio de recipe nem prova de seta menor. O teste visual horizontal pressionado no VUE ainda depende da liberação da guarda MAME. [R448](review/I167-GTK2-INSTALLED-RC-MANAGED-INCLUDE-20261027-R448.json).
I167 R449 confirma novamente, por captura nativa somente de leitura, que os 1024×800 pixels do framebuffer convidado estão pretos enquanto a faixa Apollo permanece visível. O clone está ativo, despausado e com perfil preservado; a VM distinta da Prancheta segue ativando a guarda de entrada. Nenhuma tecla foi enviada. O teste horizontal pressionado aguarda liberação da VM concorrente e o despertar único documentado. [R449](review/I167-DOMAINOS-CURRENT-SCREEN-READONLY-20261027-R449.json).
I167 R450 corrige o mapa de pendências: a regra tem seis estados VUE ainda não verificados diretamente (up/left/right pressionadas, hover, disabled e thumb drag). R52 verifica quatro direções no GTK2, R51 compara com as linhas gravadas do ciclo inferior e R434 vê 37/53 pixels no hold vivo, sem fechar os estados restantes. R394 sustenta 0/225 nas quatro células normais, portanto não mudar sua geometria sem nova diferença medida. [R450](review/I167-GTK2-NATIVE-STATE-GAP-AUDIT-20261027-R450.json).
I167 R451 confirma que a geração GTK2 substitui as cores literais da receita-base por papéis KDE nos esquemas escuro e amarelo; reload determinístico e GtkIconView passaram 2/2. Isso não prova o esquema já carregado em aplicação aberta nem a aparência histórica no VUE. Nenhuma VM foi alterada. [R451](review/I167-GTK2-ROLE-PALETTE-TRANSLATION-AUDIT-20261027-R451.json).
I167 R452 confirma 36 regressões focadas do GTK2: ativos de scrollbar 4/4, paleta/receita 10/10 e runtime 22/22. A prova automatizada sustenta a geração e composição atuais, não os estados visuais nativos pendentes em R450. R394 continua válida para as quatro setas normais em 0/225; não redimensionar sem uma nova divergência medida. [R452](review/I167-GTK2-RECIPE-REGRESSION-20261027-R452.json).
I167 R453 refaz a comparação pixel a pixel das capturas citadas: as setas horizontais no renderer GTK2 completo de R392 coincidem 0/225 com a VUE; R343 tem somente as quatro diferenças de canto já descritas em R344. Não se sustenta a hipótese de glyph horizontal encurtado; falta avaliar a aplicação aberta e o olho do usuário. [R453](review/I167-GTK2-HORIZONTAL-CROP-REVALIDATION-20261027-R453.json).
I167 R454 confirma XChat GTK2 2.24.33 em janelas visíveis e seleção de tema DomainOS no perfil atual, mas não o que cada janela já carregou em memória. Nenhum conteúdo foi capturado ou lido; a avaliação visual do app permanece aberta e a entrada na VM segue bloqueada pela instância da Prancheta. [R454](review/I167-GTK2-LIVE-XCHAT-PROCESS-AUDIT-20261027-R454.json).
I167 R455 registra tentativa de localizar as setas em três janelas XChat por busca pixel exata em captura apenas em memória. Não houve correspondência; resultado inconclusivo quanto a widget/tema carregado, sem inferência de defeito. Nenhum conteúdo foi guardado, foco alterado ou processo tocado. [R455](review/I167-GTK2-XCHAT-INMEMORY-ARROW-MATCH-20261027-R455.json).
I167 R456 traz uma captura fresca da VM do tema: framebuffer convidado de 1024×800 ainda preto, faixa Apollo visível; MAME despausado, frameskip 4, sem throttle, ponte limpa. A instância distinta da Prancheta mantém a guarda ativa; não foi enviado evento de despertar. [R456](review/I167-DOMAINOS-CURRENT-SCREEN-READONLY-20261027-R456.json).
I167 R457 confirma que os quatro assets GTK2 instalados coincidem com o checkout, mas os XChat internos Codex HOM/PRD já estavam abertos antes da atualização. R458 corrige que esses processos não são evidência sobre o XChat pessoal do usuário; retire a hipótese de cache velho como explicação do relato pessoal. As células horizontais normais continuam 0/225 em R394/R453. [R458](review/I167-GTK2-XCHAT-TARGET-IDENTITY-ERRATUM-20261027-R458.json).
I167 R459 confirma por inventário de processo que não há XChat pessoal aberto; restam dois clientes Codex HOM/PRD e duas prévias GTK2 do projeto. Não se leu conteúdo nem se tocou nas janelas. A comparação visual da VM continua atrás da guarda ativa de dois MAMEs. [R459](review/I167-GTK2-LIVE-TARGET-INVENTORY-20261027-R459.json).
I167 R460 confirma por captura nova de leitura que o framebuffer SR10.4 está preto (819.200/819.200 pixels), embora a faixa Apollo esteja visível; perfil 4/sem throttle, sem pausa, captura solta e canal limpo. O clone e a VM distinta da Prancheta seguem ativos, portanto a guarda impede entrada. A captura não presume que a VM não tenha sido acordada anteriormente pelo usuário. [R460](review/I167-DOMAINOS-CURRENT-SCREEN-READONLY-20261027-R460.json).
Errata R402: o recorte de pós-limpeza não mostra o cursor, então a alegada posição inferior esquerda não é evidência. R413 confirma que o ponteiro fica visível sob override, mas o movimento relativo reverteu após Y 164→194 e não produz alinhamento seguro; XTest não recapturou o hook. Nenhuma seta foi pressionada; captura e janela foram restauradas. [R402](review/I167-MAME-POINTER-COUNTER-ALIGNMENT-ERRATUM-20261027-R402.json), [R413](review/I167-MAME-POINTER-RELATIVE-COUNTER-CALIBRATION-20261027-R413.json).

- I167: revalidação mais recente do framebuffer da VM assistente e da guarda MAME: [R461](review/I167-DOMAINOS-CURRENT-SCREEN-READONLY-20261027-R461.json).

- I167: auditoria de retomada da autorização GTK2, dos processos MAME e dos pré-requisitos atuais: [R462](review/I167-RESUME-STATE-20261027-R462.json).

- I167: captura nativa de leitura atual, byte-idêntica a R461; a guarda da segunda VM continua ativa: [R463](review/I167-DOMAINOS-CURRENT-SCREEN-READONLY-20261027-R463.json).
- I167 GTK2 R496: renderização pós-R495 do tema instalado confirma as células horizontais esquerda/direita em 15×15 e glyphs 11×11, ambas 0/225 contra SR10.4/VUE em escala 1:1. Estados interativos e aceitação visual continuam abertos: [R496](review/I167-GTK2-POST-R495-INSTALLED-HORIZONTAL-RENDER-20261027-R496.json).
- I167 GTK2 R497: widget instalado em GTK2 2.24.33/Xvfb reproduz a célula inferior pressionada/solta; 53 pixels mudam e os 37 pixels visíveis no ciclo VUE coincidem em posição e cor. Os 16 restantes estão cobertos pelo cursor da referência. [R497](review/I167-GTK2-POST-R495-DOWN-HELD-INSTALLED-20261027-R497.json).
- I167 GTK2 R498: seta superior pós-R495, normal/pressionada/solta, 0/225 contra assets; 46 transições visíveis no ciclo VUE preservado coincidem por posição e RGB. Sete transições GTK2 ficam fora da máscara visível da captura antiga; não é captura nova da VM canônica. [R498](review/I167-GTK2-POST-R495-UP-HELD-INSTALLED-20261027-R498.json).
- I167 GTK2 R500: auditoria conjunta pós-R495 das quatro células normais GTK2 instaladas contra SR10.4/VUE: 900 pixels, zero diferenças; células 15×15 e glyphs 11×11 em todas as direções. [R500](review/I167-GTK2-POST-R495-FOUR-DIRECTION-NORMAL-20261027-R500.json).
I167 GTK2 R710 valida em isolamento a transição nativa KDE BreezeLight→BreezeDark pelo KDED GTKConfig, observador e runtime GTK2: papel #fcfcfc→#292c30, paleta atualizada, engine preservado. GTK4/render e reload em janelas foram interceptados; R713 foi invalidado por notificação no barramento real e CSS GTK3/4 com conteúdo DomainOS inalterado. [R710](review/I167-GTK2-REAL-SCHEME-TRANSITION-20261029-R710.json).
