# GTK2 recipe adapter — I167

## Situação consolidada — 2026-10-29

Esta seção prevalece sobre notas históricas abaixo quando elas descrevem um
gate já superado. R680 registrou que faltava abrir o launcher público; R683
depois exercitou `backend.py --preview` com GTK2 2.24.33 em Xvfb/bwrap privado,
sem Xephyr. As quatro setas passaram no ciclo nativo pressionar/soltar em duas
paletas e a cena reportou os 16 controles. Essa prova da rota isolada não é
comparação histórica ao vivo nem aceite visual; o recibo marcou a receita da
cena como parcial.

R685 identificou a cobertura ainda faltante dos estados de limite. R693
verificou o painter GTK2 instalado em Xvfb: a seta no limite conserva o desenho
normal sem liberar input, enquanto o widget inteiro insensível usa o estado
disabled. Isso valida a separação de estados no engine, não prova como o VUE
histórico desenhava esses casos.

R708 instalou no perfil `lsi` o alinhamento medido das células de seta e o gap
nativo de 4 px, preservando os papéis KDE dinâmicos, e enviou reload sem fechar
os clientes. R710 provou, em KDED/D-Bus privados, a troca de esquema KDE até a
regeneração da paleta GTK2; a notificação de reload às janelas e o renderer
GTK4 foram interceptados, portanto isso não prova repaint visível de clientes
abertos. R711 confirmou que a receita GTK2 instalada corresponde à fonte; R722
confirmou o engine carregado no XChat GTK2 real. R721 comparou as quatro células
normais da VM SR10.4 com a referência salva em escala 1:1: 225/225 pixels por
célula. R723 não encontrou caminhos pessoais nos pacotes e instaladores. Não é
necessário reinstalar para testar o tema atual.

Pendências atuais: a avaliação visual do usuário em V03 continua aberta;
I517 (seta VUE pressionada/liberada) e I518 (arraste do thumb) seguem sem
autorização própria. Não enviar esses inputs à VM. A estimativa técnica I167 é
95%, sem representar fidelidade visual. Consulte os recibos R683, R685, R693,
R708, R710, R711, R721, R722 e R723 na fila de revisão antes de repetir
qualquer prova.

## Estado confirmado em 2026-10-21

A rota pública atual já monta os 16 controles GTK2 em cenas nativas e oferece
prévia acoplada e separada. A prova nova cobre presença/métricas dos 16 tipos
em quatro esquemas e duas origens; a interação pública confirma push, toggle,
check, radio e as quatro setas das barras nos esquemas DomainOS e Breeze Dark.
Consulte `docs/review/I167-GTK2-PUBLIC-XEPHYR-20261021-R23.json`.

Isso ainda não significa que a receita DomainOS esteja aplicada a todos os 16
tipos: o recibo declara `recipe_applied=false`. A aparência permanece parcial,
sem alegação de fidelidade histórica. O canvas do laboratório e a janela
destacada também precisam manter o mesmo fluxo de navegação; na Xephyr :81 a
janela separada ficou mapeada sobre o laboratório e a janela principal passou
a `IsUnMapped`. Investigar esse comportamento antes de usar a prévia destacada
como comparação contínua.

Module `gtk2_recipe.py` translates proposed scrollbar geometry into native
GtkRange/GtkScrollbar style properties. It reads the GTK2 recipe independently
from GTK3 and preserves the input. Sparse geometric overrides take precedence.
An incompatible thickness is rejected instead of clamped or silently resized.
No color, font or personal profile is modified by this geometry stage.

Runtime GTK2 2.24.33 and its pixmap engine are available. The private native
probe verified horizontal/vertical requested and allocated thicknesses15/23/31
with three recipes. GtkAlignment prevents the fixture container from stretching
the vertical bar across its allocated width. The native thumb minimum21 remains
a runtime property, not a claimed DomainOS C default or historical measurement.

The GTK2 adapter is partial: full translation of all controls/states and
historical visual approval remain incomplete. A tested geometry module and a
public scene do not by themselves prove a full theme.
The GTK2 GIR requires explicit GValue and GtkRequisition output arguments; the
failed fixture calls were preserved and corrected without production workarounds.

Pure check: `python3 -B tools/theme-lab/tests/test_gtk2_recipe.py`.
Private native check: `xvfb-run -a env GTK_MODULES= GTK2_RC_FILES=/dev/null
I167_PRIVATE_PROBE=1 /usr/bin/python3 -B tools/theme-lab/tests/probe_gtk2_runtime.py
--recipe RECIPE.json` (one shell command). Recipe must contain its geometry object.
These are native API/geometry tests, not pixel fidelity approval.

## Pixmap painting stage

`paint_scrollbars` now requires native effective KDE state roles and produces
private engine assets. It never falls back to historical RGB values. Normal
range endpoints keep their enclosing palette; named whole-insensitive/backdrop
fixtures select independent state-role masks. The future scene must maintain
these widget names; the GTK2 style enum alone does not distinguish endpoint
insensitivity from whole-widget insensitivity or expose a backdrop state.

GTK2's official `gtkrange.c` expose path1910 forces painting outside the
steppers off when stepper-spacing>0. Geometry therefore reserves the visual
gap in each stepper's longitudinal allocation and pads the directional glyph
toward the thumb; native spacing is0, preserving a continuous enclosing frame.
The input region includes this padding; no unavailable arrow is enabled.
The pixmap engine's file/stretch FALSE tiled the first mask; overlay_file with
overlay_stretch FALSE correctly centers it. The failed captures are retained.

Sixteen native captures in four role schemes and four states show only current
face/light/shadow colors inside both ranges. Sixty-four directional masks match
the generated glyph/padding pixels exactly. These masks reuse the shared
direction-specific geometry algorithm, not GTK3 style defaults. They do not
prove pressed interaction, all other controls or final historical fidelity.
Custom per-state relief and arrow-button/content fitting paint are rejected
explicitly pending implementation; geometric piece shadows are independent.
Native test: `test_gtk2_paint_native.py`; evidence I167-PINTURA-NATIVA-20261011.json.

## Native interaction and sparse relief

Forty-eight real press/release cycles cover four directions, four role palettes
and normal/endpoint/whole-insensitive cases.384directional mask comparisons
match exactly; value changes by one step only when available, and release
restores idle relief without further movement. Xdotool targets only the private
fixture's own mapped window, and releases the button in cleanup.

Arrow/thumb overrides accept normal/pressed/disabled/backdrop; trough accepts
normal/disabled/backdrop. GtkRange always paints the trough with ACTIVE, so that
enum maps to idle enclosing relief, not a held action. A requested pressed-thumb
override enables the native activate-slider paint property; dragging proof is
still pending. Unknown/unsupported overrides fail explicitly and preserve data.
Five pure checks cover inheritance, bounds, alpha/size preservation, independent
assets and unsupported state rejection. Four custom native cycles prove sunken
idle arrows, flat held arrows and restored sunken relief; raised trough/sunken
thumb sample edges are checked only in the natural15px/minimum21px fixture.

`test_gtk2_interaction_native.py` runs private input cycles.
`verify_gtk2_relief_fixture.py` verifies saved custom captures, without input.
Evidence: I167-INTERACAO-RELEVOS-20261011.json. Hover/focus, isolated buttons,
content fitting, remaining controls and product scenes are not completed.


## Arraste nativo do cursor — 2026-10-11

O ensaio privado usa GtkRange.get_slider_range para localizar o cursor, sem inferir sua largura. Oito arrastes reais (horizontal/vertical em quatro paletas KDE) aumentaram o ajuste durante o movimento e conservaram o valor ao soltar. Relevo customizado normal afundado/pressionado plano foi observado nos pixels do cursor nos dois estados. Fixture de 200px explícita; não comprova outras dimensões, hover, foco ou integração da cena. Recibo: docs/review/I167-ARRASTE-CURSOR-20261011.json. Adaptador continua parcial; não instalado.


## Geração privada conectada ao backend

`gtk2_generation.py` organiza origem de paleta, presença do engine pixmap, validação de papéis KDE e recibo da proposta. `backend.generate` chama esse módulo para GTK2. Resultado `partially_generated`, `recipe_applied=false` e `scene_integrated=false`: somente scroll_h/scroll_v têm tradução; isso não significa que a prévia pública omita o RC parcial. O lançador passa `--rc`, e a sessão nativa valida o recibo e chama `Gtk.rc_parse`; `recipe_applied=false` registra cobertura incompleta, não prova de efeito visual. Noventa e seis PNGs em quatro esquemas coincidiram com os assets já verificados nativamente. Receita de encaixe não suportada é rejeitada e preservada. Dispatch provado com fixture isolada de disponibilidade; 33 testes do backend passaram. Recibo I167-GERACAO-BACKEND-20261011.json. Próximo: controles/cenas nativas e emissão do trecho relacionado à seleção.


## Fundação da cena GTK2

`scene_contract.py` fornece validação pura de posição, dimensão e visibilidade para GTK2/GTK3, sem misturar receitas. `native_scene_gtk2.py` monta barras reais em janela ou GtkPlug/XEmbed. Outros controles, ancoragem e pressão forçada ainda são rejeitados explicitamente e a proposta permanece intacta. A medição resolve estilo antes da requisição natural; aguarda alocação assíncrona no ensaio XEmbed. Foram24cenas/48controles em4paletas e3estados;96máscaras de setas coincidem com os assets. Quinze regressões da cena GTK3 e3testes de independência/preservação passaram. Recibo I167-CENA-NATIVA-20261011.json. Controlador Motif, eventos e abertura automática ainda não usam esta classe; não foi instalada na janela pessoal. Próximo: completar controles/estados e conectar ciclo de vida nativo.


## Eventos GTK2 e isolamento da família

`preview_event_writer.py` reúne persistência privada dos eventos GTK2/GTK3: hash da proposta, identidade fixa, UTF-8, limite16KiB e arquivo0600 atômico. Campos reservados não podem ser substituídos. `tl_preview_event_family` recebe a família esperada do controlador; API anterior continua GTK3-only. GTK2 não herda a medição específica de peças GTK3. Cena GTK2 emite métricas, seleção/movimento por API e mudança nativa do ajuste; falha no callback informa erro na janela. Controlador usa a receita da família ativa para eventos. Dois processos GTK2 reais (Window/Plug) emitiram14eventos aceitos pelo C;28tentativas com família/hash incorretos recusadas. Build estrito,15regressões de cena e3testes de escrita/falha passaram. Recibo I167-EVENTOS-NATIVOS-20261011.json. Abertura/ciclo de vida e gestos Ctrl ainda não conectados no produto; outras famílias de controles continuam pendentes. Nenhuma entrega pessoal nesta etapa.


## Gestos reais e recuperação de falha

`gestures_gtk2.py` liga Ctrl+clique/Ctrl+arraste ao layout sem operar o ajuste nativo. Coordenadas vêm dos campos root dos registros tipados EventButton/EventMotion fornecidos pelo binding GTK2. Movimento provisório acompanha o ponteiro; a gravação ocorre ao soltar. Falha ao persistir restaura a posição anterior, remove o grab e informa erro no título. Window e Plug reais passaram pelo deslocamento36×24, clique semCtrl e falha artificial de commit seguida de novo clique normal. Doze eventos aceitos pelo leitor C;24leituras com família/hash incorretos rejeitadas. Seis regressões puras passaram. Logs das três falhas iniciais de binding/fixture preservados. Recibo I167-GESTOS-RECUPERACAO-20261011.json. Abertura/reload no controlador principal, interação de controles desabilitados, demais controles e estados continuam pendentes; nenhuma janela pessoal foi reaberta.


## Núcleo de sessão e substituição da montagem

`gtk2_session.py` valida receita de pintura, paleta corrente e hashes do RC/imagens/engine antes de mudar o estilo. Layout/tamanho podem mudar sem alterar a pintura. A montagem é preparada separadamente e substitui somente o conteúdo da mesma Window/Plug; valores nativos dos ajustes são conservados, handlers antigos removidos. Vinte recargas em duas origens passaram; proposta inválida e RC modificado preservam a cena anterior. Falha artificial ao reparentar restaura filho anterior e handlers, com interação posterior funcional. Quatro paletas continuam gerando96PNGs iguais aos arquivos já provados. Três testes GTK2,15regressões de montagem GTK3 e build estrito passaram. Recibo I167-SESSAO-RECARGA-20261011.json. Núcleo de sessão não é abertura completa pelo controlador Motif: CLI/lifecycle do produto e demais controles/estados continuam pendentes. Interface informa GTK2 parcial explicitamente. Sem instalação/reabertura pessoal.

## Lançamento pelo controlador Motif

O controlador compartilha o agendamento de cenas GTK2/GTK3, mas executa
`preview_gtk2.py --rc` para GTK2 e `preview_gtk.py --theme-directory` para GTK3.
`src/controller/generated_preview.c` valida a família, hash da cena, estado
parcial explícito e caminho canônico dentro de `generated/revisions`. O GTK2
requer exatamente `scroll_h`/`scroll_v` no recibo e um RC regular; o GTK3 continua
exigindo `recipe_applied=true` e uma pasta de tema. O filho GTK2 verifica novamente
RC, imagens, engine e origem da paleta antes de aplicar.

Ensaio completo em bwrap/Xvfb próprios: barras acopladas e separadas medidas,
Atualizar muda a largura 220→280 nas duas origens, receita GTK3 preservada. A
separação pode ser desmarcada pelo checkbox. Esta prova cobre a integração do
lançador das barras; não conclui os demais controles, estados ou fidelidade histórica.
Receitas com componentes ainda sem implementação são recusadas explicitamente.
O fundo do canvas ainda usa a paleta GTK2 padrão: traduzir seus papéis KDE é o
próximo ajuste registrado; não declarar que toda a janela acompanha o esquema.
Não houve instalação ou reabertura de uma janela pessoal.

Ensaio reproduzível:

```sh
make -C tools/theme-lab all build/controller-spin-probe
/usr/bin/python3 -B tools/theme-lab/tests/test_controller_spin.py \
  "$PWD/tools/theme-lab/build/controller-spin-probe" --gtk2-launch
```

O ensaio cria apenas seu próprio Xvfb e perfil bwrap; não conecta ao desktop
pessoal. A execução requer suporte a namespaces de usuário e acesso ao socket
X11 exclusivo do ensaio. Os PNGs aprovados não são substituídos.


## Canvas por papéis KDE (etapa posterior ao lançador)

`gtk2_canvas.py` gera estilos restritos aos nomes Window/Plug e Fixed da prévia,
com os papéis efetivos de janela/texto, sem cor de referência fixa. GTK2 pinta o
fundo de GtkWindow com NORMAL mesmo insensível: o callback de sensibilidade
seleciona o estilo com papéis desabilitados. Ele consulta o filho atual, permitindo
substituição de conteúdo da mesma janela sem reter a cena anterior.

Quatro paletas e duas origens passaram em normal/insensível/restaurado:24capturas,
64máscaras de seta iguais,96assets de barra preservados.20recargas do núcleo
continuam funcionais. Prova limitada ao canvas e às barras; foco/backdrop do
canvas e comparação de texto ainda pendentes. A fonte de cores continua sendo
a paleta KDE escolhida para a prévia. Recibo I167-CANVAS-CORES-20261011.json.

## Rota pública GTK2 revalidada — 2026-10-14

Corrigi duas expectativas antigas do harness público: a busca da janela ainda
incluía um subtítulo removido e o verificador ordenava arquivos de estado junto
com eventos de métricas. Agora ele identifica o título GTK2 estável e filtra
eventos `metrics` antes de comparar alocações. `test_gtk2_public_native.py`
passou em bwrap/Xvfb para DomainOS SR10.4 e Breeze Dark: GTK2 real abriu, o
clique mudou o valor para 34, emitiu cinco eventos e fechou normalmente. Os
pixels das setas e os papéis KDE da barra coincidiram com os assets verificados;
alocações 220×15 e 15×180 px em escala 1:1.

`test_gtk2_generation.py` também passou: 96 PNGs coincidiram com as capturas
nativas sintéticas previamente verificadas, em quatro esquemas. Recibo
`docs/review/I167-GTK2-PUBLIC-NATIVE-20261014.json`; capturas sintéticas ficam
em `docs/referencias/domainos-sr104/i167-public-native/20261014/`.
Escopo limitado: a rota pública ainda monta somente as duas barras neste teste;
receita aplicada é falsa e não há alegação de comparação com a VM ou fidelidade
histórica. O catálogo segue com seis tipos aceitos de dezesseis (37,5% de
cobertura de tipos; não percentual de fidelidade). Resta integrar a prévia
pública e atualizar a auditoria por tipo/estado, além das famílias de controles
pendentes descritas acima.

## Rota pública completa — 2026-10-14

`I167-COBERTURA-CONTROLES-20261014.json` registra os 16 tipos como gerados e
aceitos pela cena; a montagem conjunta usa oito cenas GTK2 nativas (quatro
esquemas, Window/Plug). `test_gtk2_public_native.py` abre a cena DomainOS de 16
controles pela rota pública real do backend, publica 36 eventos e confirma
cliques em push/toggle/check/radio; a janela encerra normalmente com exit 0.
Recibo: `I167-GTK2-ALL-CONTROLS-PUBLIC-20261014.json`.

Isso fecha cobertura de tipos e integração da rota pública, não todos os estados
ou interações, nem fidelidade histórica. Xephyr :68 continua viva, mas a captura
atual só mostra “QUIT Mwm?” sobre fundo preto e não há processo MAME. A
comparação visual SR10.4 permanece pendente; a sessão foi preservada sem input.

## Fundação GtkEntry — I200, 2026-10-14

A receita GTK2 gera a pintura da `GtkEntry` a partir dos papéis KDE atuais; a
cena isolada também monta o controle nativo em janela e `GtkPlug`, com geometria
explícita e papéis separados para normal, desabilitado e backdrop. A comparação
de papéis efetivos foi feita em quatro esquemas: DomainOS, Breeze Light, Breeze
Dark e amarelo sintético. São 24 cenas (4 esquemas × 3 estados × 2 origens),
com alocação pedida e obtida de 260×44 px. Isso é uma prova de base do controle,
não uma aprovação visual histórica nem a integração com o controlador da
ferramenta.

A edição nativa foi exercitada em Xvfb isolado com UTF-8 (`Ação — ç`), seleção
total, substituição, copiar/colar/recortar, quatro passos de Undo por Ctrl+Z,
Redo por Ctrl+Y e Ctrl+Shift+Z, além das seis ações necessárias no menu de
edição. Não prova persistência do histórico após reiniciar o aplicativo. O teste
repetível é `python3 -B tools/theme-lab/tests/test_gtk2_entry_keyboard_native.py`;
recibo e capturas: `docs/review/I200-GTK2-ENTRY-FOUNDATION-20261014.json` e
`docs/referencias/domainos-sr104/i200-gtk2-entry/20261014/`. Nenhum tema ou
perfil pessoal foi instalado ou alterado.

## Montagem conjunta dos 16 tipos — I167, 2026-10-14

A matriz de cobertura de 11 de outubro estava defasada em relação ao código
atual. `backend.snippet` agora é exercitado para cada ID do catálogo e emite
fragmento GTK2 nomeado; `scene_records` admite todos os 16. O ensaio nativo
`python3 -B tools/theme-lab/tests/test_gtk2_all_controls_native.py` gerou os
controles juntos em quatro paletas e em janela separada/acoplada (oito cenas).
Cada widget nativo ficou mapeado, com alocação e coordenadas dentro do canvas.
`test_gtk2_snippet.py` também cobre a emissão dos 16 trechos.

Isso atualiza a cobertura de tipos para 16/16. Ainda não equivale a uma sessão
única do controlador Motif com interação de todos os controles, nem valida todos
os estados ou fidelidade visual frente à VM. A rota pública GTK2 tem sua prova
separada e ainda cobre scrollbars. Recibos e capturas atuais:
`docs/review/I167-COBERTURA-CONTROLES-20261014.json` e
`docs/referencias/domainos-sr104/i167-all-controls/20261014/`.

## Máscaras de visibilidade na geração — 2026-10-29

Na revisão estática de `gtk2_generation.py`, encontrei que a geração consultava
`scene_contract.scene()` apenas para validar a receita. Os painters opcionais
usavam diretamente `visible_controls`, ignorando a máscara
`visible_categories`; push/toggle e as duas barras também entravam no recibo
mesmo quando ocultos. Isso fazia o fragmento parecer mais abrangente que a
cena selecionada.

A geração agora usa os IDs retornados pela cena (categoria **e** controle) para
decidir quais painters de controle chamar. O recibo distingue `scene_controls`,
`translated_controls` e `untranslated_controls`, em ordem canônica do catálogo.
Quando nenhuma barra está visível, o RC contém somente o canvas e os controles
selecionados; quando uma ou ambas estão visíveis, o painter de barras continua
compartilhando o snapshot de geometria/paleta. Controles sem geometria exigida
permanecem explicitamente não traduzidos, sem fallback declarado como receita.

Esta é uma correção de seleção do pipeline, não uma alteração visual nos assets
instalados. Foi revisada estaticamente; não executei testes neste passo. A
prévia nativa e a comparação SR10.4 continuam necessárias para validar a rota
depois desta mudança. Estados pressionados/hover/desabilitados, interação
histórica e aceitação visual permanecem em aberto; I517 continua sendo o gate
separado para entrada na VM.

## Validação de fontes do cache e cenas sem barras — R676, 2026-10-29

A revisão do caminho de prévia encontrou duas lacunas relacionadas à mudança
acima. A prévia GTK2 podia reaproveitar `latest.json` mesmo quando o hash de um
gerador listado no recibo `sources` já não correspondia ao arquivo atual; a
validação da sessão também exigia `scrollbar_style_id` em qualquer cena, mesmo
quando nenhum controle de barra estava selecionado.

O cache GTK2 agora é invalidado quando qualquer fonte registrada está ausente,
fora da raiz privada, insegura ou com hash diferente. `validate_snapshot()` só
exige identidade e bindings de scrollbar quando a cena atual contém uma barra,
e recusa um recibo cujos hashes de fonte não correspondam ao código atual. Isso
permite que uma mudança no gerador alcance a próxima prévia e impede que uma
receita antiga seja aceita silenciosamente.

A revisão estática foi complementada por duas verificações sem interface:
`test_gtk2_preview_route.py` passou 5 casos, incluindo invalidação por fonte
desatualizada, e `test_gtk2_generation_visibility.py` passou a cena somente com
moldura sem exigir identidade de scrollbar. O recibo passou a registrar também
`backend.py` e `scene_contract.py`, dependências que determinam a geração e a
máscara de controles. Ainda falta validar a pintura na
prévia nativa isolada. Isso não altera o tema instalado no usuário `lsi` nem
comprova fidelidade visual.
Consulte [R676](../../docs/review/I167-GTK2-CACHE-SOURCE-VALIDATION-20261029-R676.json).

## Cena sem scrollbar renderizada em GTK2 nativo — R677, 2026-10-29

Gerei uma proposta com apenas `frame`, validei o recibo sem exigir estilo de
scrollbar e renderizei a cena real por `NativeSession`/`GtkOffscreenWindow` em
um Xvfb privado. A alocação foi 72×30 px e a captura está em
[`R677`](../../records/ia-tema/I167/R677/gtk2-frame-only.png). Isso comprova o
render nativo do controle e a rota de cena vazia de barras, mas não é a abertura
pública pelo bwrap/Xephyr, não foi comparado ao SR10.4 e não constitui aceite
visual. A prévia pública continua aguardando escolha do usuário.

## Gate C do controlador — R680

`tl_generated_preview` aceita recibos GTK2 na ordem canônica do contrato de
cena, com qualquer subconjunto de controles visíveis. Os IDs de estilo continuam
obrigatórios para os controles opcionais que os usam; controles desconhecidos,
repetidos ou fora de ordem são recusados. A leitura dos recibos append-only
anteriores foi preservada. O build estrito e o teste C do gate passaram; os
detalhes e hashes estão no [recibo R680](../../docs/review/I167-GTK2-CONTROLLER-RECEIPT-GATE-20261029-R680.json).

Esse teste chama a função de validação do controlador diretamente. Ainda falta
abrir a cena pelo launcher público em Xephyr e comparar sua aparência à VM
Domain/OS SR10.4; o resultado não é aprovação visual nem prova do ciclo público.


## Célula completa de stepper — revisão R17 (2026-10-19)

O renderer do GTK 2.24.33 centraliza o `overlay_file` sem esticá-lo. Por isso a pintura triangular não fornece a borda/junção contínua da célula inteira. A receita agora aloca 15 px no eixo longitudinal, mantém `stepper-spacing=0` e desliga `trough-under-steppers`; o PNG opaco contém a célula semântica SR10.4 completa de 15×15. A regra parte das métricas medidas na VM, não de um default C presumido.

A paleta da imagem é resolvida pelos papéis KDE de botão/trilho atuais; não há cor final histórica inserida. O pressionado troca luz e sombra somente na máscara triangular. A geração nativa passou em quatro esquemas e quatro estados. A cena passou em janela e `GtkPlug`/XEmbed, em quatro esquemas e três estados; 96 comparações de máscara deram zero diferenças. Um probe GTK2 direto em Xephyr :83 confirmou os quatro valores de ajuste e os ciclos de relevo pressionar/soltar.

Limites atuais: a rota pública bwrap ainda apresenta input pressionado intermitente (R17 falhou no stepper horizontal direito), e a ponte MAME tem uma solicitação antiga pendente, então não houve captura viva da VM nesta rodada. O resultado compara com os recortes SR10.4 já arquivados e não constitui aprovação humana. Consulte [`I167 R17`](../../docs/review/I167-GTK2-PUBLIC-XEPHYR-20261019-R17.json).

## Máscaras da cena e geração de todos os controles — R675/R676/R678

A geração usa a lista final de `scene_contract.scene(model, 'gtk2')`, portanto
respeita tanto categorias quanto seleção individual dos controles. Quando não há
barra na cena, não chama o painter de scrollbar; a validação requer bindings de
scrollbar somente para uma cena que realmente contenha `scroll_h` ou `scroll_v`.
Os recibos enumeram cenas, controles traduzidos e controles ainda sem tradução.

O teste `test_gtk2_generation_visibility.py` passou em dois casos focados: uma
cena frame-only gera/valida seu fragmento e renderiza um `GtkFrame` real por
`NativeSession` em Xvfb privado; a cena com as cinco categorias e todos os 16
controles visíveis registra 16/16 traduzidos, zero faltantes e fontes atuais.
O segundo caso é geração/validação; não deve ser confundido com renderização
nativa de todos os 16 controles. R677/R678 preservam esses escopos separados.
Nenhum desses ensaios muda o tema GTK2 instalado no perfil do usuário.

## Montagem nativa dos 16 controles — R679

O teste público do harness, em display Xvfb privado, montou a geração atual em
oito cenas GTK2 2.24: quatro esquemas (DomainOS, Breeze Light, Breeze Dark e
amarelo sintético) em janela separada e XEmbed. Os 16 widgets ficaram mapeados,
desenháveis e dentro da área de 1100×1000 px. Nas oito cenas, as 32 células de
seta/stepper (4 direções por cena) coincidiram com os PNGs de papel KDE gerados
na mesma paleta: 7200/7200 pixels.

As capturas e medidas estão em `records/ia-tema/I167/R679/`. Elas mostram uma
montagem de laboratório, não a aparência de uma aplicação DomainOS real. A prova
não compara controles completos com a VM SR10.4, não usa o launcher público
bwrap/Xephyr e não é avaliação humana. O harness e `xvfb-run` usam
`~/tempia/domainos-theme-work/` para arquivos temporários.
