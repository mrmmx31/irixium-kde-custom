# Laboratório de temas Motif

Aplicativo C99/Motif organizado em MVC. O usuário edita projetos e compara
controles reais; a ferramenta exporta propostas privadas. Não instala temas
nem modifica a configuração do desktop pessoal.

A interface principal mantém a barra de menus fora dos painéis, uma faixa de
contexto no topo, seis páginas mutuamente exclusivas na lateral e duas áreas
equivalentes de comparação (Motif e família-alvo). O editor de pintura manual
usa a mesma separação: fontes e ferramentas na lateral rolável e somente a arte
editável no canvas amplo. O contrato visual e a proveniência das propostas de
2026-11-11 estão em
`docs/review/THEMELAB-REDESIGN-TARGET-20261111.md`.

## Compilar

No Debian, dependências de compilação:

```sh
sudo apt install build-essential pkg-config libmotif-dev libjson-c-dev libpng-dev libxt-dev libssl-dev
make -C tools/theme-lab
make -C tools/theme-lab check
```

Bibliotecas/bindings adicionais são necessários para as galerias; a ferramenta
mostra os disponíveis. Não afirma cobertura de GTK1/GTK5 sem runtime real.

Para testar no GTK3 um esquema diferente do desktop, compile o leitor de papéis
nativos do KDE. Ele usa um processo sem interface, sem trocar a configuração:

```sh
sudo apt install cmake qt6-base-dev libkf6colorscheme-dev libkf6config-dev
cmake -S tools/theme-lab/native-build -B tools/theme-lab/build/native-colors
cmake --build tools/theme-lab/build/native-colors --parallel 2
```

## Pacote relocável e diagnóstico

O binário descobre a raiz de recursos a partir de seu próprio caminho quando
`--root` é omitido. A estrutura esperada é
`PACKAGE/tools/theme-lab/build/theme-lab`; trocar o diretório atual ou o nome do
usuário não altera essa descoberta. `--root` continua disponível para a árvore
de desenvolvimento, mas é canonicalizado e precisa conter os recursos mínimos.

Uma distribuição autocontida é gerada somente em um diretório novo sob
`~/tempia/domainos-theme-work/`. Ela inclui os scripts, galerias, temas de
referência, as pontes nativas e o bundle canônico R584 verificado. Dados
mutáveis não entram no pacote: cada execução cria uma sessão 0700 própria. O
contêiner `domainos-theme-work` pode ser 0755, desde que pertença ao usuário e
não permita escrita de grupo ou terceiros; a ferramenta não muda seu modo.

```sh
make -C tools/theme-lab BUILD="$HOME/tempia/domainos-theme-work/theme-lab-build" \
  all gtk2-pressure native-colors
python3 -B tools/theme-lab/package_runtime.py \
  --root "$PWD" \
  --build-dir "$HOME/tempia/domainos-theme-work/theme-lab-build" \
  --output "$HOME/tempia/domainos-theme-work/theme-lab-package"
"$HOME/tempia/domainos-theme-work/theme-lab-package/theme-lab"
```

`THEME-LAB-PACKAGE.json` registra SHA-256 de todos os arquivos. O diagnóstico
abaixo confere esse manifesto e separa recursos empacotados, bibliotecas,
bindings e limitações de cada família. Ausência de GTK1/GTK5 permanece uma
indisponibilidade explícita, não uma substituição por outro toolkit.

```sh
python3 -B PACKAGE/tools/theme-lab/runtime_diagnostics.py --root PACKAGE
```

Na sessão normal, o guard X11 exige `DISPLAY` local, Xauthority regular 0600 do
usuário e uma conexão autenticada cujo peer Unix corresponda à tela pedida.
Tanto o socket de pathname quanto o socket abstrato do Xwayland são aceitos;
TCP, autoridade pública, peer de outra tela e falha de autenticação são
recusados. Nenhuma guarda seleciona tema ou escreve no perfil pessoal.

## Abrir na sessão de teste

Com uma prévia criada por `plasma/tools/prever-tema-completo.py`, execute:

```sh
python3 plasma/tools/abrir-laboratorio-temas.py --sessao CAMINHO_DA_SESSAO --raiz .
```

O lançador mantém o Xephyr existente, verifica a identidade do worker e entra
em seus namespaces privados antes de criar namespaces próprios do addon.
Monta fontes e tradutores somente para leitura e usa o HOME/DBus privados.
O diretório X privado deve conter somente o socket esperado. Sua montagem
recursiva permite reutilizar um socket cujo pathname do host foi removido,
sem proxy X (que mudaria a identidade XRes) nem outro servidor. Requer
`nsenter` e `bwrap`; se a identidade ou o socket não corresponderem, aborta. A pipeta mede pixels dessa tela X11; não
captura o desktop Wayland externo. Fechar a prévia encerra seus processos.

Na execução direta do binário, a sessão privada padrão é criada em
`$HOME/tempia/domainos-theme-work/theme-lab-*`, com permissões restritas ao usuário.
Esse local também satisfaz a guarda da prévia GTK2 acoplada na sessão normal. Um
`--work-dir` explícito continua sendo respeitado; o launcher de Xephyr fornece
um diretório isolado próprio.

Para comparar duas versões sem fechar a primeira, acrescente `--nova-instancia`.
Cada instância adicional usa uma pasta de projetos própria; a saída do lançador
mostra esse caminho. Fontes, executáveis e referência são congelados por execução.

Para atualizar conservando dados **salvos**, combine `--nova-instancia` com
`--retomar-manifesto CAMINHO_DO_ADDON_ANTERIOR/MANIFESTO.json`. O lançador copia
`working.json` e os arquivos disponíveis `scene.json`, `editor-journal.json`
e `project-history.json` para uma pasta nova,
registra hashes e preserva família/referência escolhidas. Não importa resultados
de geração antigos nem modifica a origem. A escrita concorrente detectada aborta
a retomada. O worker confere os hashes antes de iniciar a interface.

Isso não lê texto ainda presente somente nos widgets de uma versão antiga.
Antes da troca, coordenar a pausa pela prancheta e salvar/Atualizar a instância
antiga. Se houver erro de validação, manter a janela e corrigir/preservar o texto;
não fechar com base apenas na existência de um JSON. Abrir a atualização e
conferir o projeto antes de encerrar a antiga. Prova isolada do transporte:
`python3 -B plasma/tests/test_lab_resume.py` (oito casos; não prova a entrega
pessoal nem a fidelidade visual).

## Ajustar e guardar

1. Na faixa de contexto, escolha plataforma e esquema de teste. Cada família
   tem receita independente. O esquema altera somente os controles em teste.
   O seletor lateral ou o menu **Exibir** alternam Catálogo, Controle e
   medições, Peça e geometria, Cores e relevo, Modelo e referências e Código da
   proposta sem destruir widgets ou aplicar a receita.
2. No catálogo em árvore, use +/− para expandir ou recolher categorias.
   O checkbox da categoria controla sua visibilidade na montagem e preserva
   as escolhas individuais. O checkbox do controle controla sua presença;
   clicar no nome seleciona qual será editado, sem trocar esse checkbox.
   Escolha então o estado e os valores. A expansão é estado da visão atual;
   visibilidade, seleção e posições são dados salvos do projeto.
   **Atualizar** aplica à montagem central. Com **Atualização automática**, o
   intervalo em milissegundos reúne as alterações antes de atualizar.
3. No canvas, `Ctrl+clique` seleciona e `Ctrl+arraste` posiciona. Cliques comuns
   mantêm a operação nativa. Também é possível digitar X/Y e atualizar.
   O trecho do controle/estado selecionado fica em **Código da proposta**.
   Estados forçados são uma ferramenta de edição, não uma prova histórica.
4. A referência central usa controles **Motif reais**, com receita própria e o
   mesmo esquema de teste. Cliques nela exercitam o Motif e não editam GTK3.
   Na Pintura manual, a lateral contém a referência e uma captura nativa
   independente da família selecionada: GTK2 e GTK3 usam controles reais em
   janela offscreen, recortados na alocação pedida e apresentados sem ocupar o
   canvas editável.
   Uma família sem capturador aparece explicitamente indisponível; nunca recebe
   uma cópia da imagem Motif como substituta.
   **Imagem histórica** abre o PNG atual em outra janela, em escala 1:1;
   o campo Referência PNG permite escolher outra imagem.
   **Pipeta** mede RGB16/RGB8; clique
   esquerdo captura, Esc ou botão direito cancela e 30 s libera o ponteiro.
5. **Prévia separada** abre controles nativos em outra janela. Motif, GTK2,
   GTK3, GTK4, Qt5, Qt6, Kvantum e Plasma têm rota central/acoplada real na
   sessão X11 do Theme Lab. A rota direta cria HOME/XDG privados distintos
   para a prévia acoplada e para a separada; não escreve no perfil pessoal.
   GTK2 e GTK3 montam os controles declarados por seus adaptadores. GTK4
   traduz `push`, `toggle`, `check`, `scroll_h` e `scroll_v`. Os adaptadores
   parciais Qt5/Qt6 montam os 16 tipos do catálogo em widgets Qt reais.
   Kvantum e Plasma traduzem somente as barras horizontal e vertical; Plasma
   usa `Plasma Components.ScrollBar`/KSvg reais, sem inventar setas que o
   componente não oferece. GTK1 e GTK5 aparecem honestamente indisponíveis
   quando não há runtime e galeria implementados; nunca são simulados com uma
   imagem de outra família.
6. **Salvar** guarda um projeto JSON. **Importar** recupera um projeto validado.
7. **Exportar** gera receitas e a proposta GTK3 na pasta de trabalho, sem alterar
   o contrato histórico. As exportações registram entradas e suas origens.

Geração e prévia GTK3 aceitam saída privada em `~/tempia`, no diretório `.qa-*`
do projeto ou no HOME do namespace isolado. `/tmp` não é destino de saída do
laboratório.

Barra, seta, thumb e sombra precisam respeitar as relações da implementação
GTK3: barra = seta + 2 × sombra; thumb transversal = seta; seta ímpar;
moldura = sombra. Padding/fonte iniciais são defaults da ferramenta, não medidas
comprovadas da referência histórica.

## Comparar propostas visuais

`visual_compare.py` gera uma prancha lado a lado sem redimensionamento e um
recibo com hashes, dimensões e proveniência. A diferença absoluta de pixels só
é calculada quando as duas imagens PNG têm dimensões idênticas; tamanhos
distintos ficam explicitamente `not_comparable`, sem escala ou recorte oculto.
Dimensões iguais habilitam a métrica, mas não provam que os conteúdos ocupem
coordenadas correspondentes: o recibo mantém o alinhamento como `unverified`
até a revisão manual.
As saídas são novas evidências privadas e precisam ficar em um diretório vazio,
modo 0700, abaixo de `~/tempia/domainos-theme-work/`:

```sh
python3 -B tools/theme-lab/visual_compare.py atual.png proposta.png \
  --output-dir ~/tempia/domainos-theme-work/comparacao-proposta-01
```

O artefato técnico não aprova uma proposta nem substitui a inspeção de widgets
nativos. Cores finais do tema continuam derivadas dos papéis do esquema KDE.

Cor medida é evidência. O DomainOS usa papéis como
`Colors:Button/BackgroundNormal` do esquema KDE atual; a pipeta não cria cores
finais fixas nos widgets. O campo de fatores regula luz, sombra e trilho.

### Adaptadores Qt5/Qt6 Widgets — receitas parciais

Cada família Qt tem receita, snapshot e galeria independentes. Os 16 tipos do
catálogo têm tradução declarada em Qt5 e Qt6, mantendo widgets e interação
nativos. O QSS deriva exclusivamente dos papéis KDE. A receita inclui
`QPushButton` simples/alternável e os indicadores reais de `QCheckBox` e do par
exclusivo de `QRadioButton`. Para o
`QSlider` horizontal, o estado de janela inativa usa uma propriedade QSS
atualizada nos eventos Activate/Deactivate da janela; `:!active` não é usado,
pois mascara a receita normal também em repouso. Os toggles
mantêm o relevo afundado enquanto selecionados e o liberam no segundo clique;
checkbox e rádio geram assets para estados ligados/desligados, pressionados,
inativos e desabilitados. `QLineEdit` permanece nativo e sua prévia verifica
UTF-8, desfazer/refazer, copiar/colar/recortar e selecionar tudo. `QComboBox`
mantém o popup nativo e usa a seta gerada alinhada ao lado direito; sua prévia
verifica seleção pelo teclado e ponteiro. O `QSlider` horizontal aplica o relevo
da receita mantendo intervalo e entrada nativos; o slider vertical ainda não
está traduzido. O adaptador de
rolagem lê `tools/domainos_scrollbar_rules.json`, resolve os papéis da paleta KDE
selecionada e gera QSS/PNG privados para `QScrollArea`. O `QScrollBar` real
continua dono do intervalo, thumb, roda e input. Um subtipo local pinta as
células fixas das setas sobre o controle depois da pintura Qt, mantendo as
setas visíveis nos limites sem alterar o comportamento de rolagem. Isso é uma
tradução parcial; o botão e as barras continuam sendo widgets Qt reais. Não é
uma renderização Qt nativa pura nem prova de equivalência histórica. Alterar o
esquema exige regenerar a prévia.

`make -C tools/theme-lab check-qt5-scrollbar-xephyr` exercita a rota pública
Qt5 em uma Xephyr que já esteja aberta e fecha somente a janela de prova.
`make check` testa a receita Qt5 real via plataforma offscreen, o contrato,
paleta e integridade do snapshot sem abrir uma janela.

## Organização

`src/model.c` valida e persiste; `src/view.c` contém widgets e referência;
`src/controller.c` executa ações sem bloquear o loop Xt; `backend.py` identifica
capacidades e traduz receitas. `preview_gtk.py` contém os controles GTK3 reais;
eventos privados correlacionados pelo hash da cena passam pelo controller.
`src/native_colors.cpp` lê estados com KColorScheme e a política do GTKConfig.
A interface usa a biblioteca Motif do sistema.
O código-fonte baixado do Motif atual serve de apoio; a VM SR10.4 continua sendo
a referência histórica para o tema DomainOS.

Escopo e fila: [documento do laboratório](../../docs/DOMAINOS-LABORATORIO-TEMAS.md).


### Medidas nativas (T01 em andamento)

A coluna de ajustes mostra pedido em edição e medidas efetivas da referência
Motif e das prévias GTK3 acoplada/separada. Mínimo, preferido e escala são
distintos; zero não impõe mais o mínimo artificial GTK3 de 140 × 44.
[Contrato e limites](../../docs/DOMAINOS-LAB-METRICAS.md).
Ensaio privado: `make check-native-metrics` (Xvfb, Motif e GTK3).
Percurso completo: `make check-controller-spin` (Xvfb/bwrap privados, controlador,
spins reais e geração GTK3). O resultado distingue input X11 e fixtures pela API
nativa. Requer o leitor KDE compilado e não altera a sessão pessoal.

### Edição e recuperação (T01)

Os campos Motif do laboratório usam um módulo explícito de edição:
Ctrl+Z desfaz, Ctrl+Y/Ctrl+Shift+Z refazem, Ctrl+C/V/X copiam/colam/recortam
e Ctrl+A seleciona tudo. Botão direito ou Shift+F10 abre o menu de edição.
Home/End no filho numérico do SpinBox movem o cursor; não alteram seu valor.
Campos somente de leitura oferecem seleção/cópia, sem aceitar alterações.

O arquivo privado `editor-journal.json`, dentro do diretório de trabalho,
conserva rascunhos e histórias independentes por campo, família e controle.
É separado do projeto, da cena aplicada e das respostas da Prancheta.
O controlador faz checkpoint pelo loop Xt, antes de trocar/importar dados e
ao fechar normalmente. Arquivo inválido é preservado e impede sua substituição.
Falha de gravação mantém o texto em memória e bloqueia ações que poderiam
descartá-lo. Histórias são limitadas a 128 passos/1 MiB por campo, com journal
de até 8 MiB. Aplicar continua sendo uma ação distinta de digitar ou recuperar.

Enquanto a janela está aberta, o loop Xt agenda uma verificação a cada 100 ms.
O callback de edição registra mudanças no histórico do campo; o checkpoint não
relê nem reescreve o journal quando ele está limpo. Quando há alterações, grava
um arquivo temporário, sincroniza-o, renomeia-o atomicamente e sincroniza o
diretório pai. O journal só fica limpo depois que essas etapas terminam. Se uma
sincronização falhar, o texto continua em memória, o aviso permanece visível e
o checkpoint será tentado novamente. A janela entre uma tecla e o próximo
checkpoint agendado não é garantia contra encerramento abrupto ou falta de
energia.

A implementação está em `src/editor/view.c`, `src/editor/store.c` e
`include/text_editor.h`; não depende da aplicação Prancheta. O popup recebe
cores e fonte do campo atual. `make check-editor` verifica persistência,
teclado e clipboard reais, texto UTF-8, recarga do catálogo, reabertura e
histórias independentes na troca de controles. A prova é do laboratório;
não comprova fidelidade histórica de outra família de widgets.
O percurso completo do spin pelo controlador ainda precisa de validação.

### I458 — camada raster manual do Theme Lab

O editor Motif em `src/view/manual_paint_view.c` e o modelo em
`src/paint/model.c` mantêm uma camada separada por família, controle e estado.
Oferece lápis, borracha, linha, retângulo, preenchimento, pipeta, papéis de cor
do esquema KDE, grade, zoom de trabalho e dimensões em pixels de arte. A
comparação reporta a medida nativa dos dois widgets e mantém a camada raster no
canvas principal; o zoom não altera o tamanho lógico informado. Menus Arquivo,
Editar, Exibir e Ajuda ficam em faixa própria, fora da lateral e do canvas.

O arquivo complementar `manual-paint.json`, dentro do diretório de trabalho,
não se mistura ao JSON da Prancheta nem à receita. Cada ação concluída e cada
mudança de dimensão cria um ponto de Undo; Ctrl+Z/Ctrl+Y atuam quando o canvas
tem foco, e os botões Desfazer/Refazer continuam disponíveis. A gravação usa
arquivo temporário e renomeação atômica com permissão privada. Ao ler, valida o
schema e os tipos antes de substituir o modelo em memória; arquivo inválido é
recusado e preservado.

A pipeta e as cores do pincel afetam somente o bitmap de referência. A camada
não é render GTK/Qt/Plasma e não vira CSS/SVG/código automaticamente. O painel
do controle selecionado explicita a ausência de receita até existir um
mapeamento verificável. `make check-manual-paint-model` cobre desenho,
preenchimento, Undo/Redo, troca de contexto, resize, retomada e recusa de JSON
inválido. Isso ainda não conclui a avaliação visual manual nem certifica as
capturas em todas as famílias.

Uso atual do editor:

1. escolha `Plataforma da arte`, `Controle`, `Peça`, `Variante` e `Estado` na
   lateral rolável; em uma barra, `Peça = Seta` isola a arte da seta e
   `Variante = Inicial/Final/Cima/Baixo/Esquerda/Direita` identifica a posição;
2. escolha `Fonte da referência` independentemente da plataforma editada. A
   troca substitui apenas a amostra de referência: não muda a família da arte,
   não redimensiona a camada manual e não altera a prévia nativa;
3. ajuste `Ensaio nativo: comprimento`, `Espessura`, `Posição do cursor` e
   `Página visível` para observar o toolkit em outros tamanhos. Esses quatro
   valores pertencem somente à amostra privada e não alteram a receita nem o
   tamanho da camada manual;
4. a referência selecionada e a captura nativa usam o mesmo zoom visual,
   iniciado em 4:1. Use
   `Amostras -` e `Amostras +` para variar de 1:1 a 8:1; os títulos continuam
   informando as dimensões originais em pixels;
5. com `Peça = Controle inteiro`, use `Copiar referência` ou
   `Copiar prévia nativa` para iniciar o desenho a partir do painel desejado.
   Cada operação substitui somente a camada raster atual e forma um único
   passo de Desfazer/Refazer; uma fonte nunca sobrescreve a outra nem a receita.
   Recortes por peça não são presumidos;
6. ajuste `Largura da arte` e `Altura da arte` somente quando quiser mudar o
   bitmap da peça; reduzir recorta e ampliar acrescenta área vazia;
7. escolha Lápis, Borracha, Linha, Retângulo, Preencher ou Pipeta e desenhe
   apenas no canvas principal. Cada ferramenta aplica um cursor próprio; o
   canvas abre em zoom 4:1, mas o arquivo continua em pixels de arte;
8. use Salvar para persistir a camada separada. Desfazer/Refazer continuam por
   documento, inclusive depois de trocar de peça.

Os seis ComboBoxes do editor observam tanto os callbacks do `XmComboBox`
quanto a lista, o campo visível e os eventos de teclado/mouse internos. Isso é
necessário porque algumas versões OpenMotif atualizam o texto mostrado sem
emitir `XmNselectionCallback`. O catálogo do GTK4 mantém os 16 controles:
botão, alternável, seleção, rolagem horizontal e rolagem vertical têm tradutor
DomainOS; os outros 11 aparecem como `sem tradutor DomainOS`, em vez de serem
omitidos ou substituídos por um dos três botões. GtkScrollbar não fornece setas
nativas, portanto uma seta GTK4 manual permanece arte separada, nunca uma
captura nativa simulada.

Prova do contrato de montagem/caminhos: `python3 -B plasma/tests/test_lab_mounts.py`
(quatro casos com dados simulados; não substitui a abertura nativa). A abertura
nativa no mesmo Xephyr foi registrada no recibo T01.

### I115 — receitas por peça (base do modelo)

O módulo `include/scrollbar_parts.h` / `src/model/scrollbar_parts.c` separa
seta, botão da seta, trilho, cursor e encaixe. Parâmetros explícitos são
salvos em `recipes.<família>.scrollbar_parts`; campos ausentes herdam a
geometria da família. Retirar um override restaura a herança da peça, sem
alterar as demais. Essas medidas são propostas, não defaults históricos.

Projetos antigos continuam legíveis. A primeira receita por peça faz o
salvamento usar schema 2, para versões antigas recusarem o formato em vez
de descartar os ajustes. Valores desconhecidos, booleanos ou fora de
0..128 são recusados; falha de leitura mantém o modelo anterior.

**Etapa parcial:** o seletor de peças já existe. Na família GTK3, a seta tem
campos com spin para tamanho do triângulo e espessura de relevo. `-1` herda
a geometria da família. O tamanho deve ser ímpar, de 3 até o espaço reservado;
não se aumenta o botão para acomodar uma seta maior. Atualizar ou a opção
automática aplica somente à prévia. O botão isolado da seta também oferece espaço interno e moldura próprios.
O trilho também oferece espessura e relevo próprios. O cursor oferece espessura/relevo e distância das setas. O encaixe
permanece com edição indisponível; sua receita salva é preservada.

A tradução GTK3 altera somente máscaras de seta, centradas na alocação original;
o trilho, cursor, encaixe e dimensões CSS permanecem iguais. Os quatro sentidos
usam a mesma receita; as cores continuam expressões dos papéis KDE. No trecho
do controle Seta, o comentário distingue o triângulo proposto do espaço reservado.
Isso não comprova a aparência histórica de um tamanho arbitrário proposto.

Os novos campos reutilizam o editor seguro (Undo/Redo, selecionar tudo,
copiar/recortar/colar, atalhos e menu). O histórico de texto não é Undo do projeto
numérico inteiro; esse requisito continua no I119. As janelas pessoais existentes
não foram recarregadas nesta etapa.

`make check-scroll-parts` verifica o percurso do controlador em Xvfb/bwrap
privados: teclado e clipboard nativos, Undo/Redo, aplicação manual, geração,
medidas GTK3 reais, código da seta e isolamento das outras máscaras. O teste
não instala tema nem marca avaliação humana. As etapas posteriores do trilho,
cursor e encaixe estão descritas abaixo, com provas próprias.


### Botão isolado da seta GTK3

A receita `scrollbar_parts.arrow_button` oferece `padding_px` e `shadow_px`;
`-1` no editor remove o override e herda a receita da família. O ajuste muda
somente o GtkButton isolado do catálogo. Os nós internos de GtkRange não
recebem moldura retangular: o contrato histórico das barras continua próprio.

O espaço interno reduz o mínimo do conteúdo para conservar a medida externa.
A validação exige `glyph + 2*(padding + shadow) <= arrow + 2*shadow_da_família`.
Valores que cobrem o triângulo ou exigem crescimento são recusados. O trecho
de código identifica o alcance isolado. As máscaras das setas e barras não
mudam ao editar somente o botão; cores continuam papéis KDE.

Ensaio privado do controlador, geração e medidas nativas:

```sh
make build/controller-spin-probe
python3 -B tests/test_controller_spin.py build/controller-spin-probe --piece-button --scheme DomainOS-SR10.4
```

O mesmo ensaio aceita BreezeLight, BreezeDark e TestYellow, criado apenas no
perfil artificial. A conferência de pixels cobre a face normal da área GTK3;
não declara todos os estados ou toolkits historicamente equivalentes.


### Trilho GTK3

`scrollbar_parts.trough` guarda `thickness_px` (espessura transversal) e
`shadow_px` (relevo rebaixado), com `-1` para herdar no editor. A espessura
precisa acomodar as alocações reservadas da seta e do cursor e as duas bordas.
O comprimento continua separado, pelas dimensões do controle e pelo GtkRange.

O laboratório gera `gtk3-lab-trough-frame`, separado da máscara original usada
pela moldura de GtkViewport. Os ajustes não modificam receitas ou máscaras
da seta/cursor. A alocação efetiva dos nós internos depende do GTK: mudanças
do espaço disponível não equivalem a mudar o tamanho desenhado do triângulo.
Conferir as medidas nativas antes de afirmar equivalência.

```sh
make build/controller-spin-probe
python3 -B tests/test_controller_spin.py build/controller-spin-probe --piece-trough --scheme DomainOS-SR10.4
```

Esse ensaio usa campos Motif reais e aplica a receita pelo controlador; mede
as duas orientações. Não substitui a comparação histórica dos estados na VM.


`make check-trough-pixels` gera quatro temas privados a partir de KColorScheme
e compara pixels reais do trilho de 17 px/relevo 1 com a moldura GtkViewport
preservada em 2 px. Cobre normal, hover, pressionado, solto, backdrop GTK
explícito, insensível e insensível/backdrop; confirma estados nativos da seta
inferior e seu input bloqueado quando insensível. Não substitui a comparação
histórica dos estados na VM ou mede alocação interna dos nós GtkRange.
O script usa bwrap, um HOME privado e seu próprio Xvfb; preserva resultados.


### Cursor GTK3

`scrollbar_parts.thumb` guarda `cross_px`, `shadow_px` e `gap_px`. O editor
mostra três spins somente nesta peça, com `-1` para herdar. A espessura deve
caber no trilho, conter o relevo e permitir margens inteiras simétricas. O
comprimento continua calculado pelo GtkRange e pelo tamanho da página; o
limite mínimo do backend é preservado e não é um default Motif comprovado.

O desenho modifica somente a máscara elevada `gtk3-thumb-frame`. Margens
transversais controlam a espessura efetiva; a distância modifica apenas o
espaço entre as regiões das setas e o movimento do cursor, não seus triângulos.

```sh
python3 -B tests/test_trough_native.py --thumb
python3 -B tests/test_controller_spin.py build/controller-spin-probe --piece-thumb --scheme DomainOS-SR10.4
```

O primeiro confere pixels do cursor 9/relevo 1/distância 3 em quatro paletas,
incluindo os estados atuais GTK3 e as posições extremas via get_slider_range.
O segundo verifica os campos reais, geração e edição do novo campo de distância.
Ambos usam perfis privados; não instalam tema nem alteram a sessão pessoal.

### Encaixe GTK3 independente

A peça `fitting` possui `gap_px` (distância conteúdo–barra) e `inset_px`
(moldura rebaixada de GtkViewport). `-1` no editor herda a geometria da família.
Usa máscara privada `gtk3-lab-view-frame`, preservando as máscaras e parâmetros
de seta, botão, trilho e cursor. Não cria moldura equivalente em GtkTreeView.
As cores seguem os papéis KDE, incluindo estados sem foco e insensível.

`make check-fitting-pixels` confere duas orientações e quatro paletas em GTK3
real. `make check-scroll-fitting` percorre os campos na GUI Motif e a geração
privada, incluindo Undo/Redo e clipboard. Esses ensaios não comprovam defaults
históricos da VM ou recuperação Undo do projeto inteiro (I119).

### Eixo longitudinal das barras (I116)

Selecionar uma barra muda o campo do eixo longo para Comprimento e trava o
campo transversal. A edição preserva o pedido transversal já salvo, inclusive
0 (automático) ou uma dimensão explícita de projeto antigo. Para ajustar a
espessura temática, usar a receita Trilho. Pedido automático não promete uma
alocação fixa: o toolkit pode impor seu mínimo, exibido nas métricas reais.
Controles sem orientação continuam com largura e altura editáveis.

A política de edição fica em `src/model/control_dimensions.c`, usada pela GUI;
a importação não apaga dimensões antigas. `make check-axis-lock` confere teclado,
Undo/Redo, trava dos campos e medidas GTK3 nas duas orientações. A escolha de
qual extremidade permanece ancorada durante o crescimento ainda é uma etapa
pendente do I116; esta entrega não presume que todos queiram o mesmo sentido.

`python3 -B tests/test_controller_spin.py build/controller-spin-probe --axis-limits`
confere barras horizontais/verticais nas duas prévias GTK3, incluindo pedido
1 pixel e automático. Na receita testada em escala 1, ambos produziram um
comprimento nativo de 48 pixels e espessura 15. É uma medida da amostra atual,
não constante adotada pelo modelo ou default histórico. A referência Motif
mantém sua própria receita; igualdade pareada será tratada no I117.

### Persistência da extremidade fixa — base I116

`length_anchor` é um vetor de 16 inteiros no schema 2: 0 mantém a extremidade
inicial; 1 mantém a final, somente para barras horizontal/vertical. Sem o vetor,
projetos anteriores preservam a origem inicial. Com âncora final, a coordenada
longitudinal de `positions` é a extremidade fixa. O cálculo da origem subtrai
o comprimento **nativo alocado**. O pedido pode ser automático ou resultar em
uma dimensão diferente. Trocar a âncora usa a medida nativa atual e preserva a origem.
Cálculos fora do canvas são recusados; não há deslocamento silencioso.

A persistência, matemática e posicionamento GTK3 estão testados em controles
reais nas prévias acoplada e separada. A posição considera também o deslocamento
do controle dentro da célula, após a disposição GTK; callbacks antigos são
cancelados na troca da cena. O consumidor Motif também foi comprovado nas duas
áreas nativas: a extremidade usa o tamanho real, e as restrições XmForm conservam
a posição ao mostrar o painel. Posição incompatível com o tamanho oculta o
controle com aviso; corrigir a receita o exibe novamente. O seletor Início/Fim
fica disponível para barras Motif, GTK2 e GTK3. A troca usa a medida atual,
considerando o deslocamento GTK dentro da célula, e recusa medidas ausentes
ou alterações ainda não aplicadas. É possível trocar de volta sem mover o
controle. O controlador salva a nova representação da posição na cena, com
hash novo para rejeitar eventos anteriores. A edição de comprimento mantém
seu modo manual/automático. Famílias além dessas continuam recusando âncora final.
O fluxo completo GTK3 do controlador passou; entrega pessoal coordenada ainda pendente.

Integração GTK2 de T04: a requisição natural medida foi49px, mas GtkFixed
aceitou um pedido explícito de1px. O posicionamento acompanha a alocação por
callback coalescido/cancelável; resize durante Ctrl-arraste conserva a coordenada
provisória do último evento entregue. Release grava sua própria coordenada;
falha de gravação restaura a posição anterior e libera o grab. Rebuild desconecta
os handlers da janela temporária antes de religar à janela mantida. Com uma barra
menor que a requisição natural, GtkRange pode informar cursor fora de sua área:
essa medida é preservada em `range_geometry_unavailable`; a alocação/posição
continuam válidas, sem declarar um retângulo de cursor utilizável.

Geração/cena e oito casos do seletor GTK2 real passaram nas duas origens,
com pedidos120/1/automático/160 em ambos os eixos. Consulte o recibo
`docs/review/T04-GTK2-ANCORAS-PIPELINE-20261011.json`. SaveLoad, histórico,
reinício e a regressão do harness GTK3 ainda são verificações pendentes desta
integração; a opção não foi entregue à sessão pessoal. Estas provas funcionais
não certificam aparência histórica ou adaptadores de outras famílias.


Na auditoria I116, a fila de eventos usa nomes monotônicos e seleciona os
32 primeiros em ordem, com memória fixa, em vez da ordem de readdir. A cena
antiga é invalidada antes da destruição dos widgets. Eventos de métricas podem
conter posição física no GtkFixed; ausência continua explícita, sem inventar
coordenadas. O fluxo completo passou após corrigir a leitura da seleção Motif: o callback
fornecia item_position=0, enquanto XmNselectedPosition indicava 1. O ensaio
usa clique X11 real, salva schema 2 e mede oito casos nas prévias acoplada e
separada, conservando a extremidade e os valores das demais receitas. Consulte
docs/review/I116-FLUXO-CONTROLADOR-20261011.json; a auditoria anterior permanece
como histórico. Pedidos 1/0 alocam o mínimo GTK3 de 48 nesta amostra, não um
default histórico. A entrega pessoal ainda depende da coordenação de edição.

### Comparação de fontes — I117 em andamento

Métricas efêmeras podem incluir `font_kind` (1: medido, 2: sem texto próprio)
e `font_description` UTF-8 limitada a 383 bytes. Ambos são opcionais juntos;
eventos anteriores permanecem válidos e mostram fonte não medida. O controle
sem texto envia descrição vazia; dados inválidos não substituem métricas atuais.
Motif lê FontList/FontSet do controle ou do filho textual Combo/Spin/Frame,
mostrando quantidade e primeira fonte do conjunto. GTK3 identifica a fonte
carregada pelo contexto Pango do texto filho (primeiro rádio no grupo). Isso
não identifica todos os fallbacks por glifo, nem a fonte histórica SR10.4.
A medição não altera fonte, esquema do desktop ou receitas de outras famílias.
Provas: I117-FONTES-NATIVAS-20261011.json; pareamento e entrega ainda pendentes.

### Pareamento de barras — I117 em andamento

A referência da barra selecionada acompanha a posição física local e a
sensibilidade efetiva da amostra GTK3 acoplada. É uma transformação efêmera
de visão: tamanho e receita Motif permanecem independentes. A posição GTK
lógica é multiplicada pela escala; ausência/incompatibilidade restaura a
referência, sem inventar coordenadas. Selecionar outra peça ou invalidar o
cache restaura a barra anterior. O IPC `sensitive` é booleano opcional estrito.
Pressionado/backdrop não recebem uma equivalência Motif fictícia. Ambas as
barras começam em 35, intervalo 0..100 e página 20; ainda não há sincronização
da rolagem interativa. Prova I117-PAREAMENTO-BARRAS-20261011.json.

### Medidas públicas das peças GTK3 — I117

`range_geometry` é um objeto opcional nas métricas das barras 10/11, com
axis, slider_start/end, area_x/y/width/height e coordinate_space
`gtk_widget_window_px`. O intervalo vem da caixa de margem do cursor; a área
contém trilho **e** setas. Não é uma medida do trilho isolado, da silhueta da
seta ou da largura transversal do cursor. Dados faltantes continuam desconhecidos.
A posição deste objeto não é a posição do controle no GtkFixed; o resumo
identifica ambos os espaços. Refresco limitado acompanha mudanças de valor.
[Intervalo do cursor](https://docs.gtk.org/gtk3/method.Range.get_slider_range.html)
e [área conjunta](https://docs.gtk.org/gtk3/method.Range.get_range_rect.html).
Prova: I117-MEDIDAS-RANGE-GTK3-20261011.json, com falha da amostra curta
preservada e repetição em amostra longa medida. Geometria interna Motif pendente.

### Diagnóstico de caixas Motif — I117

`native_parts_motif.c` isola a inspeção somente leitura dos campos de layout
de XmScrollBar no Motif 2.3.8. Exige mesma versão compilada/runtime, classe
exata e tamanho da estrutura; cada retângulo precisa caber na alocação real.
Outro runtime, classe ou caixa inválida resulta em medida indisponível.
São caixas locais de cursor, área de movimento e setas; não silhuetas nem
defaults históricos SR10.4. A receita continua independente e preservada.
`make -C tools/theme-lab check-motif-internals` verifica as caixas e pixels
do cursor em Xvfb privado e a recusa de uma identificação de versão divergente.
O fixture LD_PRELOAD é só do teste privado, nunca da sessão do usuário.
Prova: I117-PECAS-MOTIF-20261011.json, com captura recortada inválida preservada
e repetição após visibilidade nativa. Não publicar uma prova de retângulos como
certificação completa do desenho de outra biblioteca.

### Entradas iniciais compartilhadas (I117)

`sample_controls.json` define textos/valores iniciais comparáveis.
`sample_contract.py` valida o contrato e gera `include/sample_controls.h`;
`make all` confere a geração. GTK3 lê o mesmo contrato validado. A snapshot
privada inclui ambos os arquivos e o launcher detecta binário anterior ao
contrato. Não é receita, texto vivo, esquema de cores ou default histórico.
Entradas comuns não sincronizam edições durante o uso. Rádio individual, lista de três linhas (segunda selecionada) e moldura sem
título extra compartilham conteúdo com Motif. GTK3 usa GtkListBox dentro de
GtkScrolledWindow, enquanto Motif usa XmList: classes, mínimos e pintura
continuam próprios. Nível Motif continua um Scale explicitamente substituto
de ProgressBar. Não afirmar igualdade de tamanho
natural ou fidelidade por igualdade de texto/valor.

### Diagnóstico interno GTK3 (I117)

`native_parts_gtk.py` lê caixas de margem do runtime GTK3 3.24.49 de hash
verificado em Linux x86_64. O módulo somente lê o processo atual; não muda
a biblioteca ou a paleta. Tipos registrados, proprietário, limites e APIs
públicas do Range são conferidos. Leitura de memória usa `/proc/self/mem`
com tamanho limitado e erro recuperável, sem dereferenciar ponteiro bruto.
Outro build/runtime retorna indisponível e conserva medidas públicas.
Caixas são locais ao widget, em pixels lógicos; cursor, trilho e duas setas
não significam silhueta pintada, borda CSS ou default histórico do SR10.4.
A origem é explícita no resumo e IPC; o launcher congela o módulo na snapshot.
Fontes consultadas: GTK 3.24.49 `gtkrange.c` e `gtkcssgadget.c` (LGPL2+).

### Comparação integrada (I117)

`make check-native-comparison` usa controlador real e montagem GTK3 em
namespace/HOME/Xvfb descartáveis. Confere fontes/escalas de 16 controles nas
duas prévias, seleção/aplicação, medidas das barras e redimensionamento,
receitas independentes e final do resumo Motif. O harness espera seleção
observada; não espera evento de movimento quando o mouse já está no ponto.
A prova de pixels `test_trough_native.py --thumb` distingue caixa de margem
nativa do cursor pintado e compara papéis KDE em quatro paletas/estados.
O resumo não tem mais corte fixo em 1KB; alocação de wrap acompanha o texto,
e falha de memória preserva o conteúdo sem quebra, em vez de truncá-lo.

## Editor de relevo por estado (I118, parcial)

O grupo de ajuste da peça tem seletores de estado da receita e relevo. O estado escolhido não força GtkRange: pressione a seta real para observar a interação. Na primeira tradução, normal e pressionado da seta GTK3 aceitam plano/elevado/rebaixado; Herdar remove somente o override desse estado. Outros estados e peças mostram suporte pendente, preservando seus dados. A escolha do estado nesse grupo é navegação local e não altera o estado de demonstração global da prévia.

Os pixels dessa tradução passaram em quatro paletas; o percurso integrado de edição/salvamento/recarga continua em validação. `check-relief-controller` testa o controlador real em ambiente descartável; `check-part-relief-editor` é um teste de callbacks do widget e não equivale a entrada real pelo ponteiro. A atualização da sessão pessoal ainda não foi entregue.

### Inspeção do estado da peça (I118)

O seletor de estado da peça solicita um trecho com `--recipe-state`, separado
do `edit_state` da amostra. Navegar entre estados não aplica a receita à cena
nativa. Editar o relevo salva a proposta privada e respeita a opção de
atualização automática; o modo manual continua dependendo de Atualizar.
A tradução inicial da seta contempla Normal e Pressionado. Hover/Foco ainda
exibem indisponibilidade explícita. O backend não altera a entrada para gerar
o trecho; regras que excluem `:active`/`:backdrop` não aparecem como aplicáveis
a esses estados. Isso é inspeção de código, não prova histórica ou de pintura.

I118: Normal/Pressionado e Desabilitado/Sem foco têm tradução de relevo da
seta GTK3. Desabilitado distingue contexto ativo e backdrop; não confunde o
botão inativo no limite de uma barra sensível com a barra toda desabilitada.
O ensaio `check-arrow-context-pixels` verifica pintura/caixas em quatro
paletas, com sensibilidade nativa e flag BACKDROP controlada. Não comprova
transições de foco do WM nem defaults históricos desabilitados do SR10.4.
Hover/Foco personalizados continuam pendentes e explicitamente indisponíveis.

Hover da seta GTK3 agora é independente e não substitui Pressionado.
O editor inspeciona seu CSS sem aplicar a cena manual. O runtime GTK3.24.49
informa `GtkScrollbar.can_focus=false`; Foco fica indisponível nesse contrato,
com motivo visível. `GtkButton.can_focus=true` não certifica foco do stepper
interno: a seta isolada será tratada como outra peça. A receita futura continua
preservada. `check-arrow-hover-pixels` mede ponteiro real e contexto backdrop
controlado; não altera a sessão pessoal nem comprova foco do gerenciador.


O contrato de estados da moldura contínua GTK3 está em [TRILHO-ESTADOS-GTK3.md](TRILHO-ESTADOS-GTK3.md). A máscara externa e o trilho interno têm capacidades distintas; ver o recibo I118 antes de declarar cobertura nativa.
# Fundação GTK2 do botão alternável (I167)

`gtk2_toggles.py` emite uma proposta privada para GtkToggleButton. A I193 integra
esse controle à cena, geração, trecho de código e recibo C. Usa a geometria da
receita e os papéis efetivos KDE do botão;
o relevo selecionado é independente de PRELIGHT/INSENSITIVE. Na fonte oficial
GTK 2.24.33, `_gtk_button_paint` usa o detalhe `button` apesar do argumento
`togglebutton` passado pelo chamador. As regras RC distinguem `shadow = IN/OUT`.

O ensaio nativo cobre seleção persistente, dois cliques reais, bloqueio de entrada
insensível, retorno normal e backdrop explícito. Foco, estado inconsistente,
indicador de botão padrão e backdrop automático continuam fora desta entrega.
O controle está disponível na montagem GTK2. A seleção é um estado nativo de
execução, separado do projeto: cada origem mantém seu próprio estado após
Aplicar; importar um projeto limpa o cache. O ensaio do controlador verifica
cliques reais e o relevo desenhado, sem confundir esse estado com autorização.
Evidências: `docs/review/I167-TOGGLE-FUNDACAO-20261011.json` na raiz do repositório.

# Fundação GTK2 do checkbox (I167)

`gtk2_checks.py` emite CHECK por seleção nativa (shadow IN/OUT), usando overlay
sem repetição. O fundo e o texto acompanham papéis KDE da janela; o indicador
acompanha papéis do botão. O recurso Motif local informa `XmNindicatorSize=13`, mas a caixa visível na captura ocupa 10×10 px. O GTK2 usa a métrica pintada (10 px), sem reutilizar `arrow_px` da seta de rolagem. Na comparação de posições, o espaçamento GTK2 3 px aproxima o início do rótulo da amostra; a amostra informa `XmNspacing=4`. As chaves opcionais `check_indicator_px` e `check_indicator_spacing_px` mantêm a geometria da barra independente. Esses números são da amostra Motif local, não da VM SR10.4. Geometria que não comporte o relevo é recusada.

Fonte GTK 2.24.33 e engine pixmap foram conferidos; não são evidência histórica
da biblioteca SR10.4. Seleção, dois cliques reais, entrada insensível, mudança
de tamanho e papéis foram verificados isoladamente nas quatro paletas.
Foco, estado inconsistente, RTL e backdrop automático continuam pendentes.
A I194 integra CHECK à montagem, geração, trecho de código e recibo C. A seleção
nativa é preservada na substituição da cena e transportada por origem para os
reinícios do controlador; importar um projeto limpa o cache efêmero, sem gravar
marcação no modelo. A prova isolada original fica em
`docs/review/I167-CHECK-FUNDACAO-20261011.json`; consulte os recibos I194 para
os ensaios da integração.

# Fundação GTK2 das opções exclusivas (I167)

`gtk2_radios.py` é o ponto de entrada OPTION. `gtk2_indicators.py` compartilha
papéis e emissão RC com o checkbox, mas mantém sua geometria independente. A
captura do `XmToggleButton` local com `XmONE_OF_MANY` mede a silhueta visível em
13×13 px, embora o recurso do Motif também informe 13; o adaptador reserva 15 px
para o indicador GTK2 e desenha a máscara Motif com margem transparente de 1 px.
O espaçamento GTK2 2 alinha o contorno visível à coordenada local do Motif. Isso
é tradução visual da amostra Motif 2.3.8, não métrica comprovada na VM SR10.4.
Os números de cor ainda vêm dos papéis KDE; nenhuma cor final é embutida.

Quatro paletas e 44 capturas nativas confirmam relevo, seleção de grupo, clique
repetido e bloqueio desabilitado. As máscaras normal/selecionada coincidem em
169/169 pixels cada com a referência Motif local após normalizar os papéis. O
GTK2 pede 83×23 px e o widget Motif local 79×25 px; a fonte e a posição do texto
continuam diferentes. A receita traduz o radio na geração. Ainda faltam prévia
pública com a fonte atualizada, avaliação humana, foco/inconsistência/RTL e spins
próprios para esses dois parâmetros na ferramenta. Consulte o recibo
`docs/review/I167-GTK2-RADIO-20261022-R32.json` e seus artefatos em `~/tempia`.


# Cobertura real do adaptador GTK2

A auditoria de 2026-10-14 atualiza a contagem de 6/16 do recibo de 11 de outubro: os 16 tipos emitem trecho GTK2 e a cena admite todos. Um teste nativo montou os 16 juntos em oito cenas (quatro paletas, Window e Plug acoplado), conferindo mapeamento e coordenadas dentro do canvas. Isso é 100% de cobertura de tipos, não conclusão do adaptador, cobertura de estados ou fidelidade histórica. O recibo antigo permanece como histórico; a cobertura atual está em `docs/review/I167-COBERTURA-CONTROLES-20261014.json`.

| Grupo | Atividade | Estado |
| --- | --- | --- |
| 1 | Push, toggle, checkbox, radio e duas barras | Integrados, com limites nos recibos |
| 2 | Entrada simples | Integrada T04; geração/cena/controlador e edição segura verificadas |
| 3 | Texto multilinha | Integrado T04; rolagem, edição segura e fluxo de controlador verificados |
| 4 | Combobox | Integrado T04; menu/roda/gestos nativos, paleta e fluxo de controlador verificados |
| 5 | Spin | Integrado T04; edição numérica segura, setas e reconstrução/persistência verificadas |
| 6 | Escalas horizontal/vertical | Integradas; reconstrução e controlador nas duas orientações verificados |
| 7 | Seta isolada | Integrada; geometria independente, gestos, reconstrução e controlador verificados |
| 8 | Progresso | Integrado T04; paleta por geração e fluxo nativo verificados |
| 9 | Lista e moldura | Lista e moldura integradas; estado da lista, fonte/padding/tamanho da moldura, gestos e controlador verificados |
| 10 | Estados, edição segura e comparação histórica | Provas parciais; falta cobertura completa |

Recibos: `docs/review/I167-COBERTURA-CONTROLES-20261014.json` e `docs/review/I167-GTK2-ALL-CONTROLS-PUBLIC-20261014.json`; o recibo de 11 de outubro permanece como auditoria histórica. Resultado/capturas da montagem conjunta: `docs/referencias/domainos-sr104/i167-all-controls/20261014/`. A rota pública atual monta os 16 tipos em GTK2 real e clica push/toggle/check/radio; outros controles/estados e comparação histórica continuam com escopo separado. Nenhum item antigo foi eliminado.
## Dicas e ajuda do laboratório — T07 parcial

`make check-ui-hints` verifica hover Motif em display privado e os recursos
de cores/fonte em quatro paletas. As dicas recebem os papéis da interface;
o esquema escolhido apenas para a prévia não altera sua paleta. ComboBox e
SpinBox recebem dicas nos componentes internos, e parágrafos longos quebram
em espaços sem dividir caracteres UTF-8. As amostras Motif nas duas áreas têm
orientações específicas. O menu **Ajuda** abre dez assuntos em janela separada,
somente leitura, com seleção/cópia e os níveis novice, intermediate e expert.
Textos ficam em `src/model/help_topics.c`; widgets em `src/view/ui_help.c`.
O nível inicia em intermediate e é conservado enquanto a aplicação está aberta;
não é uma preferência persistida no projeto. A ajuda não modifica a receita.
Dicas dos controles estrangeiros e validação de outros layouts/fontes
ainda estão na fila.
As provas de recursos FontSet não certificam todos os glyphs renderizados.

`make check-help-topics` verifica os trinta textos UTF-8 e índices do modelo.
`make check-ui-help` usa Xvfb, xdotool e xclip para testar menu, assuntos,
troca de nível, cópia UTF-8, seleção e fechamento/reabertura. Esses testes
usam um display próprio e dados artificiais; não usam o clipboard pessoal.
Na revisão T07 r4, o fluxo nativo também passou diretamente no Xephyr :68:
menu Ajuda, seleção de assunto e nível, texto somente leitura, cópia UTF-8,
fechamento/reabertura e preservação do projeto. O teste guarda a captura do
clipboard em `TMPDIR` (ou `~/tempia` quando não definido), sem usar `/tmp`.
Recibo: `../../docs/review/T07-HELP-XEPHYR-20261016.json`. Avisos FontSet de
glyphs ausentes permaneceram e limitam a conclusão visual/tipográfica.


O seletor de salvar/importar projeto e abrir referência recebe dicas nos onze componentes nativos; o menu de edição fornece seis explicações de atalhos. Seletores abertos acompanham a paleta da interface preservando texto/histórico. `make check-file-dialog-hints` verifica quatro esquemas em Xvfb privado, edição e callbacks artificiais sem gravar projetos reais. A fixture posiciona o cursor explicitamente; esta prova não valida Home/End nem fidelidade de glyphs.

As cenas GTK3 e GTK2 usam `control_hints.py` para dicas específicas por controle e seus filhos. `make check-foreign-control-hints` confere os recursos em fábricas GTK reais (16 tipos GTK3; seis tipos GTK2 disponíveis), em Xvfb separado por ABI. A prova cobre atribuição, não atraso/posicionamento de hover. Dicas herdam os estilos do toolkit; não armazenam cores finais.

`make check-gtk3-hint-hover` verifica hover push em 940×700: atraso nativo, limites, não sobreposição, estabilidade de 400 ms e saída. `make check-gtk2-hint-hover` verifica as mesmas propriedades GTK2; `gtk2_hint_position.py` posiciona a própria janela de dica no mapa sem substituir sua pintura ou temporização. A antiga falha de 6 px foi superada: R106 passou 64/64 casos nas quatro posições em 800×600 e R115 passou 48/48 casos (16 controles × três paletas). Probes GTK fixam X11 e conferem display privado antes de criar widgets; Xvfb por si só não neutraliza um backend Wayland herdado. O handler GTK3 informa a área em coordenadas do controle composto pela [API GTK](https://docs.gtk.org/gtk3/method.Tooltip.set_tip_area.html).

Correção posterior: sobreposição do push GTK2 resolvida por `gtk2_hint_position.py`, que move a própria janela nativa da dica no map e preserva temporização/pintura. `tooltip_position.py` calcula espaço abaixo/acima/laterais dentro do monitor; sem espaço exterior, a dica é escondida. `make check-tooltip-position` testa os limites geométricos; `tests/test_gtk2_hint_palettes.py --output <pasta-privada>` verifica duas origens e quatro estilos de papéis KDE por pixels. Essa fixture não certifica geração/instalação de temas. Popup alheio não é reposicionado; contexto do dono é uma referência fraca, limpa ao unmap. O teste GTK2 que falhava6px passou após a correção; evidência T07-POSICAO-DICA-GTK2-20261011.json.

Galerias Qt5/Qt6 usam `plasma/tests/galerias-nativas/qt_widget_hints.py`: dicas por classe, valores mínimo/máximo/passo lidos do widget, explicações existentes preservadas, menus habilitados. Não altera estilo/paleta. `make check-qt-gallery-hint-helper` testa helper nativo nos dois runtimes. `tests/run_qt_gallery_namespace.py` executa main real com guardas originais no bwrap de Xvfb, usando perfil e bus descartáveis; esse ensaio não certifica hover ou aparência Kvantum. Prova T07-DICAS-GALERIAS-QT-20261011.json.

T07: hover nativo de um push na galeria completa passou em Qt5 e Qt6 com namespace privado: atraso, limites/não sobreposição, estabilidade e saída. Evidência `docs/review/T07-HOVER-QT-20261011.json`. Demais controles/layouts e diálogos seguem pendentes; não certifica pintura Kvantum.

Dicas dinâmicas Qt: QFileDialog e Sobre recebem recursos após criação; navegação, nome/filtro e confirmar/cancelar têm explicação específica. Provas Qt5/Qt6 em `docs/review/T07-DIALOGOS-QT-20261011.json`. Portais externos não são controles QWidget configuráveis; a escolha nativa da plataforma continua preservada.

T07 GTK4:26 controles lógicos da galeria C ABI têm dicas UTF-8 verificadas por getters nativos em perfil/Xvfb privados. Teste `T07_PRIVATE_PROBE=1 xvfb-run -a python3 -B tools/theme-lab/tests/probe_gtk4_gallery_hints.py`. Recursos somente; hover, menus/filhos internos e tradução de cores ainda não comprovados. Recibo `docs/review/T07-DICAS-GTK4-20261011.json`.

T07 GTK4 interno: árvore real contém12 barras e15 linhas de menu com dicas específicas, somadas aos26 controles lógicos;53 recursos UTF-8 passaram em getters. Prova `docs/review/T07-DICAS-INTERNAS-GTK4-20261011.json`. Não certifica hover nem widgets posteriores.

GTK4 hover: `T07_PRIVATE_PROBE=1 xvfb-run -a python3 -B tools/theme-lab/tests/probe_gtk4_gallery_hints.py --hover` verifica botão da galeria de produção em loop nativo: atraso, limites/não sobreposição, estabilidade, saída e clique posterior. Recibo `docs/review/T07-HOVER-GTK4-20261011.json`; escopo um push/layout, Default, não fidelidade histórica.

GTK4 menu: prova nativa abre Native MenuButton, confere5 linhas mapeadas com dicas, executa a ação de exemplo, reabre e fecha por Escape; refresh ao map preserva pintura e sinais. Recibo `docs/review/T07-MENU-GTK4-20261011.json`. Hover geométrico das linhas e demais submenus/dropdown permanecem pendentes.

QtQuick KDE hints: produção QtQuick5/6 guardada observou31/27 recursos attached ToolTip e recebeu clique real. `run_qt_gallery_namespace.py --quick --major 5|6 --output NOVA_PASTA` em Xvfb privado. Recibo `docs/review/T07-DICAS-QTQUICK-20261011.json`. Não certifica hover, menus abertos ou Plasma SVG;3 avisos KDE TabButton no Qt6 conservados.

QtQuick5/6 hover: push real passou atraso, posição exterior, estabilidade e saída; menu abriu/recebeu ação real/fechou. Dicas do menu preservam o delegate KDE e são atribuídas ao aboutToShow. Prova `docs/review/T07-HOVER-QTQUICK-20261011.json`; avisos KDE Qt5 implicitWidth e Qt6 TabButton mantidos, baseline pendente.

Revalidação T07 em 2026-10-17: o hover de duas linhas do menu passou em QtQuick 5.15.15 e 6.8.2, além do botão, em :71. O texto é específico por linha; a dica fica à direita do delegate real do estilo KDE, espera 750 ms, não cobre a linha, permanece estável e some ao sair. O menu só fecha depois do clique na ação. A sonda anterior consultava `Menu.itemAt()` (dados da ação), não o delegate renderizado; essa era a causa da verificação inconclusiva em Qt5. Restam dois avisos `Menu.qml` implicitWidth no Qt5, já presentes na linha de base sem dicas; não alterei o QML do sistema. No Qt6 continuam três avisos `TabButton.qml` já presentes na linha de base. Capturas e resultados em `~/tempia/t07-qtquick-menu-row-20261017-r43-qt5/` e `r44-qt6/`; recibo `docs/review/T07-QTQUICK-MENU-ROW-HOVER-20261017.json`. Isso não cobre todas as classes/layouts, SVG Plasma ou a avaliação manual.

Baseline QtQuick: `--quick --quick-baseline` no runner usa QML sem dicas do commit9a67cc83d763e1e5a910a891dbfc77979fc562d8. Avisos Qt5 Menu/Qt6 TabButton coincidem com atual, com paleta/fonte/style iguais. Prova `docs/review/T07-BASELINE-QTQUICK-20261011.json`; comprova preexistência no ensaio, não root cause ou fidelidade histórica.

Auditoria T07 Motif: navegação das barras internas e5 ações de histórico recebem helper de dicas comum; quatro paletas passaram recursos/ajuda. Recibo `docs/review/T07-AUDITORIA-MOTIF-20261011.json`. Teste amplo de pixels do cursor falhou separadamente; desenho não certificado por estes testes de dicas.

T07: `make check-file-dialog-hover` verifica dicas nativas do seletor de produção em quatro controles, com atraso, limites, ausência de sobreposição, estabilidade e fechamento; segue com a regressão de edição/clipboard/paleta/cancelar/confirmar. Prova limitada ao layout testado; recibo `docs/review/T07-HOVER-SELETOR-MOTIF-20261011.json`.

T07: `make check-editor-menu-hover` exercita a dica de Copiar no popup de edição em quatro paletas iniciais e após troca de papéis. O módulo `src/view/ui_menu_hints.c` usa widgets Motif e APIs Xt públicas, com atraso750ms/duração6000ms; coloca a dica fora do menu, herda fonte/cores do comando e cancela ao sair/clicar/desmapear. Não troca traduções, grab, foco ou comandos do editor. Em uma tela onde não cabe fora do menu, a dica não é exibida. Esses tempos são política do laboratório, não medidas do SR10.4.

A atualização de paleta agora percorre os menus existentes do editor e a dica aberta. `check-editor-menu-hover` também troca papéis enquanto a dica está visível e confere posição, seleção e clipboard. Recibo `docs/review/T07-PALETA-DICA-ABERTA-MOTIF-20261011.json` registra escopo e uma falha intermitente de entrada fria ainda sem causa estabelecida.

O ensaio de dicas do popup usa o atalho já existente Shift+F10 e clique esquerdo em Copiar. A soltura do botão de postagem na borda pode fechar o menu Motif; esse percurso de mouse é uma revisão separada, não certificado pelo teste de dicas. O módulo rejeita EnterNotify de NotifyUngrab e confirma visibilidade/posição real do ponteiro antes de postar; o teste aguarda1100ms após ativar para verificar ausência de dica tardia.

Correção posterior do percurso de mouse: menus do editor usam `XmPOPUP_AUTOMATIC`, criados antes do primeiro input; RowColumn controla a postagem e a captura. `check-editor-menu-hover` agora exercita clique direito completo nas quatro paletas, hover e clique esquerdo Copiar. Shift+F10 continua disponível e foi verificado separadamente, assim como ajuda/read-only e regressão Motif. Os registros anteriores de percurso pendente são históricos; recibo atual `docs/review/T07-POPUP-AUTOMATICO-MOTIF-20261011.json`.

`make check-history-hint-hover` verifica cinco comandos de histórico reais com atraso/posição/estabilidade/saída em quatro paletas. O Desfazer desabilitado conserva seu recurso, mas o runtime Motif não posta dica nessa condição: limitação registrada em T07-HOVER-HISTORICO-MOTIF-20261011.json. A prova não certifica callbacks de histórico nem outros layouts.

`make check-dynamic-hints` audita recursos nativos dos campos de peças/eixos após trocar receita, incluindo unidade, herança, visibilidade e sensibilidade em quatro paletas. Não certifica hover nem adaptadores de outras famílias. As setas do XmSpinBox são desenhadas pelo manager e não são widgets-filhos; hover próprio permanece na fila. Recibo T07-DICAS-DINAMICAS-MOTIF-20261011.json.

`make check-spin-hint-hover` verifica a ponte de dicas das setas desenhadas pelo XmSpinBox em quatro paletas: atraso, posição, estabilidade, papéis atuais/troca ao vivo, incremento/decremento, repetição e ausência de dica tardia. A ponte não substitui traduções, grabs ou callbacks. Limite: um layout habilitado; estados desabilitados e demais geometrias continuam na fila. Recibo T07-DICAS-SETAS-SPINBOX-20261011.json.

Dicas desabilitadas: `make check-history-hint-hover` inclui Undo insensível e clique sem ativação; `make check-spin-hint-hover` inclui campo/setas de um SpinBox insensível e valor inalterado, em quatro paletas. A ponte observa ancestrais porque Xt não despacha eventos para a primitiva insensível; não habilita ações e não substitui atalhos. Recibo T07-DICAS-DESABILITADOS-MOTIF-20261011.json; demais classes/gadgets/layouts não estão certificados.

Entrega isolada: o launcher congela os módulos Python de runtime junto aos entry points do laboratório/galerias, incluindo helpers de dicas e cenas. Testes de closure e retomada: `python3 -B plasma/tests/test_lab_runtime_files.py` e `python3 -B plasma/tests/test_lab_resume.py`. Prova T07-DEPENDENCIAS-ENTREGA-20261011.json não substitui startup nativo da nova fixture.

### Exportação e diferenças de projeto (T08, parcial)

`--export --project proposta.json --applied-project cena.json --output <saída-privada>`
usa `exports/revisions/` abaixo da saída; não substitui o `latest.json` usado pela
prévia. `COMPARISON.json` identifica os snapshots e as mudanças. `DELTA.json`
contém apenas as alterações do modelo, hashes canônicos da base/proposta, famílias
afetadas e proveniência das regras. A função `proposal_export.replay_delta`
reconstrói a proposta somente a partir da base exata; recusa divergência/corrupção.
Isso é validação interna, ainda não um comando de importação da interface.

A geração de exportação omite famílias com receita inalterada. Uma mudança no ID
do esquema inclui todas as famílias, mantendo o estado de suporte explícito nos
recibos. O projeto completo e a cena continuam preservados como evidência.
Arquivos comuns da família traduzida ainda acompanham a geração: o pacote mínimo
por arquivo e a detecção de mudanças externas da paleta são etapas pendentes.
Comparar modelos não comprova pintura nativa, prévia viva ou instalação.

Verificação sem GUI: `python3 -B tools/theme-lab/tests/test_proposal_export.py`.

A comparação externa da exportação usa a geração salva em `latest.json` da cena:
verifica identidade do projeto normalizado e recibos, depois hashes das origens
de paleta/leitores GTK2 e GTK3. Mudança ou remoção dessas entradas inclui a família
na geração, mesmo sem mudança do ID de esquema. Proveniência ausente é
`unknown`, nunca `unchanged`; a proposta é regenerada. A última checagem recusa
mudança ocorrida durante a exportação numa família que havia sido omitida.
Os adaptadores ainda ausentes não ganham uma falsa prova de paleta/aplicação.
Essa comparação não substitui a inspeção dos arquivos gerados ou a pintura nativa.

O diretório `PACKAGE/` é o pacote de mudanças por arquivo. Cada família gerada
contém `FILES.json` e `payload/` com somente arquivos novos/alterados; os arquivos
iguais à geração base ficam em `reuse`, com hash obrigatório. Remoções também são
registradas. `artifact_delta.reconstruct_files` confere toda a base e os bytes do
payload antes de criar um resultado independente. Recusa conteúdo divergente,
links, caminhos externos e substituição de uma pasta existente. A base não muda.
Sem base traduzida verificável, o modo é `snapshot`, explicitamente, e inclui os
arquivos necessários à família. `DEPENDENCIES.json` registra engines, origens de
paleta/leitores e fontes das regras; essas dependências externas não são instaladas
pelo pacote. `ORIGEM.json` não participa do delta de arquivos de execução, pois sua
proveniência já acompanha os documentos do pacote. As pastas de geração completas
ficam como evidência privada; `PACKAGE/` é a saída compacta a revisar.

A reconstrução dos arquivos de tema tem CLI e interface Motif. A importação do delta de projeto está descrita abaixo. Teste de
arquivos não comprova pintura ou fidelidade Motif.

Ao concluir uma exportação, o controlador abre um relatório Motif próprio,
modeless e somente leitura: caminho do pacote, hashes, mudanças do modelo,
origens externas, arquivos gerados/reutilizados e limites da comparação. A janela
usa os papéis atuais da interface; permite selecionar/copiar e fechar pelo botão
ou pela moldura. Não ocupa o painel do trecho de código e não altera o projeto.
Implementação modular: `ui_export_review.h` / `src/view/ui_export_review.c`;
conteúdo formatado por `proposal_export.review_text`. Teste nativo privado:
`make -C tools/theme-lab check-export-review`. Esse ensaio cobre o relatório;
o clique de exportação completo e os diálogos de projeto têm o ensaio próprio
`tests/test_controller_spin.py build/controller-spin-probe --project-io`, em
namespace descartável. Não exige fechar a janela pessoal.

### Importar proposta sem aplicar à prévia

Carregar preserva receitas de famílias sem tradutor e registra a proposta no
histórico do projeto. A cena aplicada permanece independente; somente Aplicar
atualiza a prévia. Receitas pendentes não passam a ter suporte nativo por serem
carregadas. Cancelar ou carregar JSON inválido conserva projeto e cena anteriores.
Salvar conserva ajustes e receitas; `exported_at` é renovado na serialização.

Para reconstruir uma proposta a partir de `DELTA.json` e sua base exata:

```sh
python3 -B tools/theme-lab/backend.py --import-delta \
  --project base/PROJECT.json --delta pacote/DELTA.json --output saida-privada
```

O resultado JSON informa `project_path`, apontando para um novo
`imports/revision-.../PROJECT.json`. Abra esse arquivo em Carregar e confira a
proposta antes de Aplicar. A base não é substituída. A importação confere hashes,
operações, estrutura e validação integral do projeto antes de publicar a revisão;
base divergente ou projeto inválido é recusado. Cada importação tem diretório
próprio e recibo `IMPORT.json`. O comando não instala arquivos de tema nem aplica
o esquema ao desktop. Este fluxo importa dados do projeto; a reconstrução do
payload de arquivos de tema continua sendo uma operação separada.

Ao reabrir uma pasta de trabalho existente, o controlador recupera a cena
aplicada de `scene.json` separadamente do projeto/histórico. A proposta não é
aplicada pela reabertura. Uma cena salva inválida impede a inicialização e é
preservada para recuperação. O ensaio `--project-io` reinicia a aplicação Motif,
verifica Undo/Redo persistido e recusa de cena corrompida; não certifica a pintura
ou o arranque de todos os adaptadores.

O ensaio `--project-resume-gtk` verifica separadamente duas reaberturas GTK3:
a cena continua com o tamanho aplicado, enquanto o editor recupera tamanhos
pendentes e até outra família selecionada. Cena semanticamente igual conserva
os bytes e o hash; geração/medidas usam a família aplicada. Ctrl+clique no
controle da cena seleciona sua família no editor, capturando antes os ajustes
pendentes da outra receita. Ctrl+arraste modifica a posição desse controle,
sem aplicar os demais ajustes pendentes. Isso não comprova a pintura Qt6 nem
fidelidade histórica.

O modo `--project-transfer-gtk` usa o `resume_snapshot` do lançador em duas
transferências privadas, antes de reabrir o controlador real. Confere os quatro
arquivos de dados por bytes/hash e exclui gerados herdados; a prévia GTK3 gera
seus arquivos novamente. Esse ensaio não substitui a entrega na sessão pessoal.

O botão **Importar delta** oferece o mesmo contrato na interface: primeiro
escolha o PROJECT.json da base exata, depois DELTA.json. Não precisa carregar
a base como projeto de trabalho. Cancelar qualquer etapa preserva o projeto;
base divergente é recusada. O backend roda em processo separado. Uma importação
válida entra como proposta com Undo/Redo; a cena não muda até Aplicar. Se houve
edição enquanto o job rodava, a guarda de revisão conserva os ajustes e informa
o caminho reconstruído para carregamento posterior. O ensaio nativo cobre
cancelamentos, base divergente, importação válida e histórico. O mesmo ensaio
segura o job real antes do exec com barreira limitada a 15 segundos somente no
probe; digitação X11 durante o job comprova preservação do modelo, campo, cena
e Undo após a resposta real. O produto não contém essa barreira. A reconstrução de arquivos de tema
continua separada da importação de dados do projeto.

### Reconstruir arquivos exportados

```sh
python3 -B tools/theme-lab/backend.py --reconstruct-files \
  --file-delta pacote/gtk3/FILES.json \
  --base-directory /caminho/da/geracao-base/tema \
  --output /caminho/da/saida-privada
```

Em modo snapshot, omita `--base-directory`. Use o diretório real dos arquivos
certificados da base, não o diretório geral da geração. O comando confere
inventários, hashes da base/payload e dependências antes de criar a revisão.
Retorna `theme_directory` e grava `RECONSTRUCTION.json` junto à pasta `theme/`.
As revisões usam UUID; não substituem a base, o pacote nem outras revisões.
A saída deve ser absoluta e ficar fora da base/pacote. Diretórios novos têm
modo0700; uma saída existente precisa ser privada e pertencer ao usuário.

Esse comando reconstrói os bytes exportados. Não instala nem comprova que
correspondem aos papéis KDE atuais: `palette_revalidated=false`. Regenerar/conferir
as origens de paleta e revisar a proposta continua necessário antes da instalação.
A reconstrução valida e
retém os bytes antes de escrever; monta arquivos e recibo juntos em staging
privado no mesmo filesystem, publicando por `renameat2(RENAME_NOREPLACE)`.
Um destino criado durante a operação é preservado, inclusive vazio. Exceções
limpam o staging desta operação sem publicar revisão parcial. Sem suporte a
renameat2, a publicação é recusada; não há fallback de substituição.

SIGKILL ou queda pode deixar staging oculto; ele não é revisão publicada. Não
apagar automaticamente pastas desconhecidas. Esse contrato não garante
durabilidade após queda de energia e não teve ensaio de crash. Teste específico:
`python3 -B tools/theme-lab/tests/test_private_publication.py`.

O botão **Reconstruir arquivos** escolhe FILES.json. O backend inspeciona apenas
se há dependência de base; isso não certifica hashes. Quando necessário, aparece
um seletor de pasta para o diretório dos arquivos certificados. Snapshot segue
sem esse segundo diálogo. A reconstrução completa valida todas as entradas,
publica uma revisão privada e abre relatório somente leitura com caminho,
origem/hash, contagens e limites. Não altera projeto, cena, base ou tema instalado.
Campos do seletor de pasta usam o editor comum com Undo/Redo e atalhos; controles
recebem fonte/papéis atuais da interface e dicas. O ensaio nativo `--project-io`
cobre snapshot GTK3 realmente exportado, delta com seleção de pasta, cancelamentos,
base errada, bytes/hashes e relatório, além dos demais fluxos T08. Não certifica
pintura histórica ou entrega pessoal.

### Recuperação de execução (T09, parcial)

O ensaio `tests/test_controller_spin.py build/controller-spin-probe
--preview-recovery` usa Xvfb/bwrap privados e encerra somente filhos GTK3
identificados por UID, argumentos, ambiente e pidfd. Verifica preservação de
projeto/cena, digitação nativa após falha e recuperação por Aplicar. Medidas
da prévia morta são removidas; métricas/estados exigem job de origem ativo.
Timeouts, eventos antigos e encerramento completo de descendentes ainda
precisam de provas específicas; este ensaio não certifica outros toolkits.

O modo `--backend-timeout` retém um filho de geração antes do exec somente
no probe e verifica o prazo real de30s do controlador, digitação/Undo/Redo
durante espera e nova geração GTK3 por Aplicar. O produto usa relógio
monotônico para esse prazo e mostra mensagem explícita ao excedê-lo. Prévias
interativas permanecem abertas até ação/falha; não recebem esse prazo de job.
A barreira não existe no binário de produção nem simula saída de backend.
Esse teste não representa uma carga de cálculo pesada ou outras famílias.

O controlador passa `--preview-instance` aos filhos GTK2/GTK3: identidade
32hex diferente em cada abertura, incluindo regeneração da mesma cena. O
emissor inclui o campo reservado `preview_instance`; o controlador confere
identidade, família, origem e hash antes de aceitar o evento. O parser aceita
dados isolados sem identidade por compatibilidade; esses dados não são
aceitos pelo controlador ativo. Identidade não é autenticação de segurança.
O ensaio `--stale-preview` reproduz o erro antigo de arraste após regenerar
a mesma cena e confirma sua rejeição; regressões GTK3/GTK2 conferem entrada
nativa atual e medidas IPC da origem separada fechada. Sentinelas IPC do
teste GTK2 não são medidas nativas ou evidência de fidelidade histórica.

Encerramento T09 usa `src/controller/owned_processes.c`. Somente filhos diretos
que lideram grupos próprios ainda não coletados recebem sinais de grupo.
SIGTERM tem 200 ms de tolerância na saída; SIGKILL antecede a coleta do líder,
evita reutilização do ID e tem polling de coleta limitado a 200 ms. Durante
uso, waitid WNOWAIT coleta sem bloquear; cancelamento tem tolerância monotônica
de 2 s. Jobs cancelados continuam rastreados, mas não bloqueiam admissão de
uma nova prévia da mesma espécie.

O teste `make build/owned-processes-test && build/owned-processes-test` prova
os grupos no kernel. O harness `--cancel-group` prova Carregar cancelando a
geração, Aplicar recuperando GTK3 e atualizando novamente sem barreira de
geração, e Fechar encerrando descendentes resistentes artificiais. Aplicar
enfileira atualização; não cancela a geração. `--display-loss` encerra somente
o Xvfb criado pelo teste e confere processo independente e os quatro arquivos
salvos byte a byte. Não garante texto sem checkpoint, queda de energia ou
controle de descendentes que escapam do grupo. Entrega pessoal ainda pendente.
Provas e limites: `docs/review/T09-PERDA-DISPLAY-20261011.json` na raiz.

Catálogo T02: visão independente em `src/view/control_catalog.c`, API em
`include/control_catalog.h`. O modo `--control-catalog` do harness comprova
cliques reais, recolher/expandir a primeira categoria, máscaras independentes,
seleção pelo nome e Salvar/Carregar sem perder posições. O ensaio complementar registrou a prefixação das cinco categorias e16
checkboxes com Espaço antes de uma falha posterior do seletor; isso não é
uma matriz inteira aprovada. A troca GTK3/Motif por itens nativos passou
após corrigir o callback da família para ler XmNselectedPosition. Rotas
de teclado do combobox continuam sem prova específica. A seleção de outro
nome por Enter passou no ensaio posterior documentado abaixo. Entrega pessoal
permanece pendente.

Detalhes e falhas preservadas: `docs/review/T02-CATALOGO-FAMILIAS-20261011.json`
na raiz. O modo `--catalog-families` não repete a matriz dos16 controles;
mede seleção de família por cliques reais nos itens da lista Motif.

Catálogo T02 — teclado: nomes de controles também aceitam Enter quando têm foco; checkboxes usam Espaço. O ensaio atual `--catalog-matrix` passou as cinco categorias,16 controles e a troca GTK3/Motif, com seleção de outro membro por Enter sem mudar visibilidade. A preparação observa o foco real após rolar. Falhas anteriores preservadas; teclado do combobox e entrega pessoal continuam sem prova. [Recibo](../../docs/review/T02-CATALOGO-TECLADO-20261011.json).

T04 — GtkProgressBar agora integra a cena GTK2, respeitando tamanho, posição, fonte e valor de amostra. Geração usa papéis KDE de conteúdo/seleção e estilos identificados por geração; nomes de imagens incluem hash para evitar recursos antigos. Estado desabilitado é explícito, pois o GTK2 desenha partes com NORMAL/PRELIGHT mesmo quando o widget não aceita interação. `tests/test_gtk2_progress.py` cobre guardas; `probe_gtk2_progress.py` cobre24 cenas em quatro paletas; harness `--gtk2-progress` cobre o controlador/Aplicar/duas prévias/fechar. GUI nativa não recebe cores finais constantes. Identidade é validada contra o RC congelado. GTK2 continua parcial (7/16 tipos); memória de estado da prévia separada ainda não é preferência persistida. [Prova e limites](../../docs/review/T04-GTK2-PROGRESS-20261011.json).

### Preferência de prévia separada

O codec aceita `separate_preview` booleano opcional no projeto (padrão `false`
para arquivos anteriores schema1/2), com preservação no histórico. O checkbox, Salvar/Carregar e Undo/Redo usam essa preferência; ao retomar,
o controlador abre a cena aplicada, preservando ajustes pendentes. Fechar a
janela mantém a escolha salva; desligar o checkbox remove a preferência.
Uma família indisponível conserva a escolha e informa o limite. A preferência
salva não comprova uma prévia aberta ou adaptador disponível. Fluxo nativo de
persistência comprovado em GTK2 e GTK3, usando indicador de progresso; isso não
certifica todos os controles. Motif separado ainda pendente.

### Edição de amostras GTK

`preview_text_history.py` contém histórico limitado; `preview_text_editing.py`
adapta os widgets reais. GTK3 Entry/TextView/SpinButton têm Undo/Redo por teclado
e menu; copiar/recortar/colar/selecionar tudo continuam nativos. O histórico
resiste à reconstrução de controles dentro da mesma cena/processo. São até128
estados/1 MiB de texto, conservando ao menos os dois últimos valores mesmo em
colagens maiores. Não há journal de amostras entre processos; isso é diferente
do journal do editor Motif e do histórico de receitas. GTK2 passou a prova da
camada, mas sua integração GtkEntry/tema continua pendente.

Provas: `tests/test_preview_text_history.py`, `tests/probe_preview_text_editing.py`
em Xvfb/bwrap privado. Relatório `docs/review/T04-EDICAO-NATIVA-GTK-20261011.json`
distingue controles avulsos GTK2 da reconstrução NativeScene real GTK3.

T04 — GtkEntry GTK2 integrado em módulo próprio, com papéis KDE de conteúdo/texto/seleção, padding/sombra/fonte da receita e identidade de geração validada contra RC. Native24 passou quatro paletas e ambas as origens; reconstruções mantêm texto/Undo/Redo no mesmo processo. Controlador real passou Aplicar/redimensionar/Salvar/Carregar/reiniciar, sem aplicar a receita pendente. O trecho selecionado exige origem KDE explícita. Histórico das amostras ainda não cruza processos. Nenhuma aprovação histórica inferida. [Recibo e limites](../../docs/review/T04-GTK2-ENTRY-INTEGRACAO-20261011.json).

T04 — GtkTextView GTK2 real dentro de GtkScrolledWindow: papéis KDE, relevo simbólico, sombra/fonte e margens laterais da receita, rolagem automática, Undo/Redo e clipboard nativos. Matriz24, teclado em duas origens e controlador/persistência passaram. Sensibilidade do editor filho é explícita. Histórico de amostras ainda pertence ao processo, não ao projeto/Motif journal. [Prova e limites](../../docs/review/T04-GTK2-TEXTO-INTEGRACAO-20261011.json).

T04 — ComboBoxText GTK2 integrado: botão/seta dependem dos papéis KDE e o menu continua GTK2 nativo. EventBox InputOnly permite Ctrl+clique/arraste de montagem; clique normal encaminha uma união Gdk.Event ao botão real para conservar o menu após soltar. Roda usa o algoritmo nativo. Native24 (quatro paletas/três estados/duas origens), dois percursos reais de entrada e controlador com Save/Load/histórico/reinícios passaram. Item ativo é preservado nas reconstruções do processo. Foco/pressão forçados e persistência da amostra entre processos continuam pendentes. [Prova e limites](../../docs/review/T04-GTK2-COMBO-INTEGRACAO-20261011.json). Próximo controle GTK2: Spin.

T04 — Spin GTK2 integrado: campo e painéis/setas usam papéis KDE; teclado/mouse e validação numérica são nativos. Texto parcial e valor confirmado são estados distintos. Restauração não executa Enter; o campo é reaplicado após mapear em GTK2/3 para evitar formatação indevida. Native24, duas origens de edição e gestos, controlador e regressão dos três editores GTK3 passaram. Alocação dos painéis continua nativa GTK2, independente da extensão proposta da máscara. Histórico das amostras entre processos e cobertura completa de estados/pixels continuam pendentes. [Prova e limites](../../docs/review/T04-GTK2-SPIN-INTEGRACAO-20261011.json). Próximo: escalas GTK2.

T04 — escalas GTK2 integradas: máscaras/paleta KDE, recibo e bindings estritos, código selecionado, GtkHScale/GtkVScale reais e valores preservados na reconstrução. Matriz48, gestos Ctrl nas duas origens e controladores horizontal/vertical passaram. A configuração proposta pendente não altera a cena retomada. [Provas e limites](../../docs/review/T04-GTK2-ESCALAS-INTEGRACAO-20261011.json). Estados/pixels completos e persistência das amostras entre processos permanecem pendentes. Próximo: seta isolada GTK2.

T04 — seta isolada GTK2 integrada: GtkButton/GtkArrow reais, papéis KDE, geometria/relevo por peça e bindings verificados. Pressão/soltura das quatro direções passou na fundação; a cena usa a direção para baixo. Reconstrução e controlador mantêm as propostas de dimensões e medem o filho nativo visível. Foco/pressão forçados continuam pendentes. [Provas e limites](../../docs/review/T04-GTK2-SETA-INTEGRACAO-20261011.json). Próximo: lista GTK2.

### Inventário de runtimes e falhas independentes

As seis consultas de importação/biblioteca GTK2/3/4, Qt5/6 e QtQuick6 usam concorrência limitada a seis workers e processos separados, sem inicializar uma GUI. Cada consulta mantém prazo10s; metadados opcionais de pacote mantêm3s. A geração continua registrando todas as famílias, inclusive indisponíveis; nenhuma disponibilidade antiga é reutilizada. Timeout, falha ao iniciar ou resposta inválida resultam em `available:false` com motivo e `probe_status`, sem abortar os demais resultados. `available:false` por timeout significa não confirmado nessa consulta, não ausência comprovada da biblioteca. O prazo30s da operação do controlador permanece; a concorrência reduz a soma dos prazos, não garante conclusão sob qualquer carga. Testes: `tests/test_runtime_probe_failures.py`, incluindo barreira de seis consultas para provar sobreposição sem omitir famílias.


### Fundação da pressão demonstrada GTK2

`gtk2_pressed_state.py` encapsula callbacks por botão e fechamento explícito.
Não carrega uma ponte ABI nem habilita `forced_state=1` no renderer: o setter
visual deve ser verificado pelo chamador para seu widget/runtime. Cinco testes
de ownership/falha e ensaio privado com GtkButton GTK2.24.33 comprovam hover,
reset, clique físico posterior e destruição sem setter no widget morrendo.
A ponte C permanece experimental em tests; integração, rebuild nas duas origens
e pintura da receita continuam pendentes.
Recibo: `docs/review/T04-GTK2-PRESSAO-LIFECYCLE-20261011.json`.


### Ponte GTK2 opcional de pressão

`make -C tools/theme-lab gtk2-pressure` compila `native-gtk2/press.c` em
`build/libtheme-lab-gtk2-press.so`, usando pkg-config gtk+-2.0. A interface
Motif principal não passa a depender de GTK2. `gtk2_press_bridge.py` carrega
somente esse artefato relativo à raiz do projeto; falta/incompatibilidade é
explícita. ABI verificada apenas para GTK2.24.33 e GtkButton exato: subclasses
como toggle e outros controles continuam rejeitados. O vínculo mantém a
referência do widget e invalida o ponteiro ao fechar/destruir. Cores e flags
de entrada não são alteradas; reset respeita hover/touchscreen nativos.
Ainda não habilita forced_state=1 no renderer; integração, snapshot imutável
e rebuild das duas origens estão pendentes. Recibo de build/contrato:
`docs/review/T04-GTK2-PRESSAO-PONTE-20261011.json`.


### Renderer GTK2 — ponte explícita de pressão

A cena aceita pressão somente de push quando recebe `press_bridge` verificada.
Sem ponte, e para todos os demais controles, a recusa anterior permanece.
NativeSession faz preflight da ponte antes de alterar RC; cenas normais não
carregam a biblioteca opcional. Criação recusada destrói a janela candidata.
Provas diretas GtkWindow/GtkPlug confirmam transferência,220x80 e fechamento,
mas não certificam NativeSession.replace/rollback, pintura gerada ou controlador
Motif. Backend/controlador mantêm o gate público até esses ensaios e inclusão
do helper no snapshot imutável. Recibo PRESSAO-RENDERER de20261011.


### Sessão gerada GTK2 de pressão — gate nativo

Receita DomainOS gerada a partir dos papéisKDE foi exercitada em NativeSession:
quatro alternâncias normal/pressionado por origem, rollback após transferência
e um clique real mantendo ACTIVE. `released` requer after-handler próprio
(RUN_FIRST), pois o evento GTK2 de release retornaTRUE. Freezer inclui ponte
opcional com C/header e checa freshness/integridade; SDK continua opcional.
Paletas adicionais, controladorMotif, persistência e entrega ainda pendem;
backend/controlador não habilitam pressão pública nesta etapa. Consulte o
recibo T04-GTK2-PRESSAO-SESSAO-GERADA-20261011.json para escopo e falhas retidas.

### Estado atual da pressão GTK2 — capacidade pública e prova do controlador

As etapas anteriores descrevem seus marcos históricos; o gate público já
permite `push` pressionado quando a ponte confirma GTK2.24.33. Backend e
entrada `preview_gtk2.py` executam o preflight antes de gerar/alterar a cena.
Os demais controles continuam exigindo interação nativa para pressão.
O inventário consulta a ponte em subprocesso GTK2, sem iniciar GUI; ausência
ou incompatibilidade não elimina a disponibilidade dos estados normais.

Face e relevo passaram em DomainOS, BreezeLight, BreezeDark e amarelo, nas
duas origens (32 capturas). Isso não certifica texto, foco ou fidelidade à VM.
O ponto de entrada real também passou nas duas origens. Provas:
`docs/review/T04-GTK2-PRESSAO-PIXELS-20261011.json` e
`docs/review/T04-GTK2-PRESSAO-CAPACIDADE-PUBLICA-20261011.json`.

O percurso Motif de seleção, Aplicar, salvar/carregar, Undo/Redo e reinício
continua em verificação privada; não foi entregue na janela pessoal.
Undo/Redo recuperam a proposta; Aplicar altera a cena. O diagnóstico atual
e os resultados parciais estão em
`docs/review/T04-GTK2-PRESSAO-CONTROLADOR-20261011.json`.

Atualização: esse percurso passou no controlador Motif com seleção por ponteiro
no item nativo medido, Aplicar, Undo/Redo com Aplicar explícito, Save/Load e
reinício. As 12 capturas de bordas das duas origens coincidem com a receita;
cena aplicada e demais famílias foram preservadas. A fixture reposiciona a
janela separada recriada para evitar que cubra a acoplada. A prova de teclado
é do combobox Motif isolado, não do percurso completo do controlador.
Resta a entrega congelada coordenada; a janela pessoal ainda não foi atualizada.

### Recuperação de pedido de saída recusado

`make check-quit-recovery` usa somente dados artificiais em Xvfb/bwrap.
Insere largura inválida por teclado nativo, envia SIGTERM ao controlador
privado, verifica preservação do campo, corrige a largura, exige autosave e
repete SIGTERM exigindo saída zero. O controlador usa sigaction para manter
os tratadores instalados e continua o timer quando a validação recusa sair.
Não há encerramento forçado da aplicação pessoal nem descarte de rascunho.
Esta prova não certifica aparência histórica ou todos os casos de saída.

### Históricos acumulados entre famílias

O journal de edição não limita a quantidade de contextos visitados a256.
Mantém o limite de8MiB por arquivo,128 estados por campo,64KiB por estado e
1MiB por histórico. `make check-journal-capacity` inicia310 históricos
artificiais e verifica preservação, autosave e fechamento em Motif nativo.

Uma versão antiga com journal recusado deve permanecer aberta até recuperar
sua memória. A opção explícita `--recuperar-journal` do launcher recebe um
snapshot privado no HOME da mesma sessão, junto com `--retomar-manifesto`.
Preserva o journal da origem, recusa remoção de contextos salvos e registra
separadamente hashes dos arquivos originais e entregues. Não recupera memória
automaticamente nem presume autorização para reabrir aplicações.

### Pressão demonstrativa da seta GTK2 — fundação

`tests/probe_gtk2_arrow_pressure.py` usa apenas Xvfb privado, GtkButton/GtkArrow
e os assets/papéis KDE existentes. Fundação passou16 casos: quatro direções
em DomainOS, Breeze Light, Breeze Dark e esquema amarelo artificial. Capturas
da demonstração e pressão física são idênticas; reset/soltura voltam ao normal,
sem cliques artificiais. A análise das capturas confirma mudança real de
pixels entre normal e pressionado. Foco foi excluído da comparação.
[Recibo e hashes](../../docs/review/T04-GTK2-SETA-PRESSAO-FUNDACAO-20261011.json).

A capacidade foi integrada às fontes, com cenas acoplada/separada verificadas.
Faltam controlador/histórico e entrega coordenada na instância pessoal. A prova
não certifica aparência histórica ou estados de outros controles.
[Prova de sessão](../../docs/review/T04-GTK2-SETA-PRESSAO-SESSAO-20261011.json).


### T04 — fundação do botão GTK4

`gtk4_buttons.py` traduz a receita de botão para CSS privada usando as máscaras
de relevo compartilhadas e os papéis KDE ativos, inativos e desabilitados.
Oito fatias independentes evitam interpolar cores dos cantos nas bordas longas.
GTK4 4.18.6 por C ABI: quatro estados, quatro paletas e redimensionamento;
17.984 pixels de borda sem divergência. Cinco ciclos físicos correspondem à
pressão demonstrativa e restauram a imagem normal; zero cliques artificiais.
Quatro testes puros passaram. [Recibo](../../docs/review/T04-GTK4-BOTAO-FUNDACAO-20261011.json).

Escopo: GtkWindow privado independente; foco e estados combinados não certificados.
Ainda faltam cena/sessão acoplada e separada, controlador/histórico e entrega.
Inventário mantém GTK4 `not_implemented` até integração real; esta fundação
não altera o tema instalado, a aplicação pessoal ou a VM.


### T04 — sessão GTK4 privada e hospedagem experimental

`gtk4_push_api.py`, `gtk4_scene_contract.py`, `gtk4_canvas.py` e
`gtk4_push_session.py` separam C ABI, validação, papéis KDE e substituição
transacional. Importar os módulos não inicializa GTK. O único renderer é push;
qualquer outro controle visível é recusado antes de gerar arquivos.

Prova em quatro paletas e duas origens: quarenta capturas,35.328 pixels de borda
sem diferenças, dicas UTF-8 por getter, CSS inválida recusada, recuperação da
cena após falha de transferência, mouse e Espaço funcionando após rollback.
O caso acoplado hospeda a janela GTK4 real num XmDrawingArea Motif por X11.
[Recibo](../../docs/review/T04-GTK4-BOTAO-SESSAO-PROTOTIPO-20261011.json).

A hospedagem ainda está na fixture de teste, não no processo de prévia de produção.
Faltam validação do hospedeiro, foco/Tab entre toolkits, redimensionamento e perda
do hospedeiro, protocolo de eventos/watch, integração no controlador e entrega.
A ABI X11 atual usa get_xid, descontinuada desde GTK4 4.18; não pressupõe suporte
Wayland ou garantia de versões futuras. Inventário público continua sem adaptador
GTK4 implementado. Não alterou qualquer perfil pessoal.


### T04 — ponte GTK4: identidade, tamanho e perda do host

`native-gtk4/host.c` e `gtk4_host.py` validam o marcador do canvas Motif,
PID/UID e identidade do processo; aceitam apenas filho do processo GTK4.
`make gtk4-host` compila a biblioteca separada. `tl_view_canvas` publica o
marcador no host; essa alteração é metadata e não anuncia um renderer GTK4.
A ponte gerencia tamanho sem se apresentar como GtkPlug/XEmbed.

Prova privada: resize360×240→420×280, recusa de alvo inexistente/filho não
pertencente ao processo, detecção de término do host e de canvas destruído
com processo ainda vivo. A limpeza trata BadWindow somente após perda
verificada; outros erros não são descartados. Erro transitório de observação
conserva handle e propaga o erro. Nove testes puros passaram, biblioteca e
host de produção compilaram em estágio privado.
[Recibo](../../docs/review/T04-GTK4-HOSPEDAGEM-CICLO-20261011.json).

Ainda faltam foco/Tab entre Motif e GTK4, eventos/watch no processo de prévia,
rotas de geração/controlador e entrega. Não foram instaladas novas versões
em perfis pessoais. A ponte usa ABI X11 da instalação atual; não equivale
a suporte Wayland ou à restauração de texto, pois esta etapa só contém botão.


### T04 — protocolo de foco GTK4/Motif

`native-gtk4/focus.c/.h` controla a entrada no filho GTK4 e a saída por
travessia Motif. `gtk4_focus.py` intercepta somente Tab/Shift+Tab da atual
cena com um botão, preservando atalhos modificados. Pedido e resultado são
correlacionados por janela/PID/sequência; enviar não significa concluir.
O host usa seu foco virtual após processar os eventos de retorno ao shell,
e mantém o filho no save-set para desconexão do host.

Prova final: quatro paletas nas duas origens,40 capturas de sessão/35.328 pixels
de borda sem diferenças. Quatro percursos acoplados forward/backward ativam
GTK4 oito vezes e Motif doze vezes. Foco inicial interno, rollback, teclas
e cleanup passaram.36 testes puros passaram. Host de produção compila com
o módulo; regressão GTK2 no controlador real passou12 capturas, Apply,
Undo/Redo, Save/Load e reinício.
[Recibo](../../docs/review/T04-GTK4-FOCO-PROTOCOLO-20261011.json).

A fixture de travessia conserva sua geometria Xt: redimensionamento X11
separado ocorre após navegação, para não cobrir o botão seguinte. Motif2.3.8
foi consultado para o algoritmo de travessia/obscuração; não prova defaults
ou aparência histórica SR10.4. Faltam worker/eventos/watch, rotas de geração
e controlador e entrega. Outros controles/Tab order, pixels do foco e WM
continuam sem certificação. Nenhuma janela pessoal foi reaberta.


### T04 — entrada e ciclo do worker GTK4

`preview_gtk4.py` estabelece as guardas privadas antes de inicializar GTK.
`gtk4_generation.py` prepara/verifica snapshot de projeto, paleta, CSS e PNGs;
`gtk4_worker.py` aplica só artefatos verificados e mantém a janela ao atualizar.
`gtk4_snapshot_job.py` gera em filho próprio para manter o loop GTK livre.
Eventos de clique/métricas usam o writer compartilhado, com família, instância
e hash da cena aceita. Uma revisão incompatível conserva cena e digest antigos.

Checks nativos do processo real passaram acoplado/separado: cliques durante
geração confirmada viva, posição/tamanho50,65/200×70, recuperação após revisão
inválida, sem clique artificial por estado pressionado, TERM durante geração
e perda real do host com recolhimento do filho. Capturas pressionadas têm
1064 pixels de borda por origem, sem divergências. Doze testes puros passaram.
[Recibo](../../docs/review/T04-GTK4-WORKER-PROTOCOLO-20261011.json).

Métricas usam compute_bounds em coordenadas do canvas; GtkFixed.get_child_position
retornava a transformação interna com borda/padding. Emissão é postergada até
o ciclo seguinte ao layout. O teste completo usa `test_gtk4_worker_native.py`
e `--coupled`, com/tmp privado em namespace; artefatos e perfis são descartáveis.
Ainda faltam gestos de seleção/movimento, medidas naturais/fontes, rota pública
de geração/preview e controlador. Inventário GTK4 continua not_implemented;
nenhuma entrega pessoal ou instalação de tema é feita por esses scripts.


### T04 — mínimo/natural e fonte GTK4

A sessão mede GtkButton com CSS enraizada antes de aplicar o pedido explícito.
O worker emite mínimo, natural, requisição de referência e descrição Pango da
fonte do label, com alocação real independente. A string alocada por Pango é
liberada. Métricas aguardam bounds que atinjam o mínimo nativo; valores
transitórios pequenos não são publicados como alocação pronta.

Prova nas duas origens: Sans13px/minimum-natural72×30 permanece igual com
pedidos180×60,200×70 e40×15. Este último aloca72×30; nenhum tamanho fictício
é informado. Automático com fonte20px/padding8 mede/aloca112×48. São medidas
da fixture atual, não números fixos ou defaults históricos.20 testes puros
e os percursos reais de recarga/recusa/geração/encerramento passaram.
[Recibo](../../docs/review/T04-GTK4-MEDIDAS-NATIVAS-20261012.json).
Faltam Ctrl-seleção/movimento, rotas públicas/controlador e entrega; GTK4
continua sem adaptador público completo.

### GTK4: prévia nativa parcial

O adaptador GTK4 atual traduz `push` (GtkButton) com papéis KDE, medidas nativas,
Ctrl+clique para seleção e Ctrl+arraste para posicionamento. Os demais controles
GTK4 são recusados antes de abrir uma cena; receita salva não equivale a renderer.
O controlador C usa a mesma fila de eventos e histórico do projeto.

A ponte X11 é compilada por `make`/`make gtk4-host`. Por padrão, o controlador
procura `build/libtheme-lab-gtk4-host.so` sob `tools/theme-lab` da raiz informada.
Um build em outro diretório pode passar `--gtk4-host-bridge CAMINHO_DA_BIBLIOTECA`.
Não há caminho de perfil pessoal embutido na aplicação.

A prévia acoplada e a separada pedem Cairo por padrão somente nos seus processos GTK4; um
`GSK_RENDERER` explícito é preservado. O renderer automático produziu superfície
preta nas duas origens na prova X11, apesar de medidas e eventos corretos. Cairo e o aviso de
adoção do filho foram conferidos por captura/pixels. A escolha não altera GTK do
perfil, cores, tema instalado ou o processo Motif. As cores permanecem snapshots
qualificados dos papéis KDE selecionados, renovados pela geração privada.

A cena C e a cena normalizada Python podem ter hashes de bytes diferentes. A
abertura verifica igualdade do modelo e um hash ligado aos bytes reais de uma
ou outra cena, além do manifest de CSS/PNG. Eventos usam o hash da cena de
trabalho atual e a identidade da instância; não herdam identidade de outra janela.

Integração técnica em estágio privado; entrega na instância pessoal e demais
controles GTK4 continuam na fila T04. O trecho do botão GTK4 mostra CSS do estado
selecionado, com as mesmas dimensões e camadas do renderer. Ele importa o
`push.css` existente do snapshot para usar seus aliases, sem criar outro arquivo
de cores. Deve ser usado como um arquivo de fragmento distinto, no diretório
dos assets; não substituir `push.css` pelo fragmento que o importa.

Os nomes terminados em `_breeze` nos comentários são aliases do exportador KDE,
não uma paleta Breeze fixa. Os aliases `lab_push_*` usados no trecho são ligados
ao snapshot verificado do esquema selecionado. O parser GTK4 confere os trechos;
essa prova de sintaxe não substitui comparação visual de cada estado.
