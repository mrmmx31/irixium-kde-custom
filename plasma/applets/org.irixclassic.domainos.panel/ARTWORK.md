Os desenhos do painel Irix Classic DomainOS
=========================================

Os SVGs em `contents/images` foram construídos para este repositório a partir
de retângulos, polígonos e linhas em uma grade rígida. Usam a organização do projeto
fornecido pelo usuário e a linguagem visual do painel HP da segunda referência.
As imagens de referência não são distribuídas. Não há recortes, texturas raster,
imagem embutida, marca HP, fonte proprietária, filtro ou gradiente nos SVGs.

Os novos desenhos e a nova paleta usam GPL-3.0-or-later, como as adições originais
do projeto; o texto da licença está em `LICENSE` na raiz do repositório. Essa
declaração se refere aos arquivos novos. Não atribui autoria, licença ou direitos
sobre as capturas e o software HP. O pinguim monocromático é uma nova figura
geométrica desenhada aqui, sem usar um arquivo da ilustração Tux de Larry Ewing.

`contents/images/ORIGEM.json` registra as referências, seus hashes SHA-256 e os
hashes dos desenhos. `palette.json` permite conferir as cores de modo direto.
A inscrição GNU/LINUX também é feita de pequenos retângulos, sem depender de
uma fonte instalada ou de conversão de texto em imagem.

O selo acompanha o azul predominante da chapa. A inscrição aparece em duas
linhas, `GNU/` e `LINUX`, com letras de bloco construídas na grade inteira,
hastes uniformes e espaçamento regular. O realce fica fora do contorno escuro
e não fecha os espaços internos dos glifos. O pinguim e a inscrição têm
20 pixels de altura total, centrados na placa de 26 pixels, com folgas de
três pixels acima/abaixo e uma linha livre entre GNU/ e LINUX.
A revisão de fidelidade corrige a inversão anterior: letras e pictograma
escuros `#3e536e`, realce `#c4d5ed` no alto/esquerda e trama pontilhada sob o
desenho, sem retângulo sólido embutido. A placa usa moldura simples elevada,
clara no topo/esquerda e escura embaixo/direita, como a identificação HP.
O pinguim e a inscrição continuam sendo desenhos originais, sem usar a marca
HP ou uma fonte proprietária. A placa oferece apenas o relevo pressionado,
sem atribuir uma ação de ajuda.
A gaveta de aplicativos usa `applications.svg`, um desenho original de
32 × 24 com três janelas de programas quadradas e sobrepostas, inspirado na
linguagem gráfica de 1987. Usa apenas `#3e536e` e `#c4d5ed`, com fundo
transparente. O botão `domainosApplicationsDrawer` ocupa X = 587, largura 118
e altura 52 na faixa inferior, no lugar da antiga célula vazia; o desenho
é exibido em 64 × 48 unidades canônicas. O relevo responde à pressão e ao
cancelamento, sem abrir uma gaveta ou lançar aplicativos. A associação futura
de aplicativos fixados aguarda o documento funcional do usuário.
Terminal/teclado, paleta e ferramenta retangular foram refinados pela
referência HP sem atribuir ações aos desenhos. As molduras QML e do Style
usam um topo claro/turquesa e sombra profunda, invertidos na pressão. O QML
mantém as bandas na grade de pixels da exibição: quatro em escala 100% e duas
em 50%, preservando a margem do desenho. Nos quatro instrumentos esquerdos,
as duas linhas do relevo têm a mesma cor: clara no alto/esquerda e escura
embaixo/direita. A junção das molduras separa as faces por quatro pixels,
como no original, sem um intervalo vazio. Os quatro botões de 166 × 150
unidades terminam diretamente na iconbox e no metal; não recebem um segundo
relevo do contêiner à direita ou embaixo. A trama é desenhada no tamanho final,
com pixels alternados, e não reduzida junto com os módulos. O marcador e a
borda do segundo quadro de área usam o mesmo amarelo.

Referências e medidas
--------------------

* `image-1.png`, 2103 × 748: projeto do usuário, com espaço branco acima e abaixo.
  O painel ocupa aproximadamente x = 112 a 2054, y = 296 a 514. O bloco principal
  vai até y = 450, e a sub-barra ocupa o restante. O selo GNU/LINUX fica na
  esquerda da sub-barra; relógio, data, gráfico e Mail ficam no primeiro bloco
  da faixa principal. A divisão central é Iconbox, seguida por dois desktops e
  uma bandeja com seis ícones e setas ▶ e ▲ à direita.
* `image-2.png`, 1025 × 99: painel HP usado para conferir os desenhos nítidos.
  O painel ocupa aproximadamente x = 49 a 983, y = 5 a 94. A faixa principal tem
  cerca de 61 pixels e a faixa inferior cerca de 27. Relógio, campo de data e
  gráfico compartilham a mesma base azul.

Na revisão pelo print DomainOS SR10.4 do Virtual OS Museum, o azul do relógio
foi alinhado a `#3297c7`. Os fundos dos instrumentos alternam `#194b63` e
`#a3d0e6` em uma trama de 2 × 2 pixels. A barra inferior usa `#3e536e` e
`#c4d5ed` em uma base pontilhada; somente o centro recebe quatro sulcos de
três linhas (clara, alternada e escura), com caps escuro/claro. A trama
continua acima e abaixo desse grupo, sem repetir os riscos pela altura toda.
Na escala 50%, o metal tem 26 pixels e margens pontilhadas de quatro pixels.
Ele termina em um friso ciano `#7acac5` de dois pixels e uma sombra ciano
`#406b68` de dois pixels, ambos parte do chassi, como na referência SR10.4.
Essas duas bandas continuam pela direita, com espaço próprio fora das molduras
internas. O topo e a esquerda têm duas linhas claras e duas ciano. A faixa
metálica começa em X = 8 e termina em X = 1934,
evita cobrir as laterais do chassi e conserva seus 26 pixels de altura em 50%.
O total de 1942 × 218 continua igual: módulos superiores vão até y = 158,
metal até y = 210, friso até y = 214 e sombra até y = 218.
O indicador azul tem uma lente de 13 × 7 dentro de um aro claro de 17 × 12.
O conjunto de 19 × 14 inclui o encaixe escuro de dois pixels acima/esquerda,
que interrompe os sulcos e define a profundidade do aro. Sua ampliação não
move a lente; a quina superior direita recebe a sombra interna.
Os realces `#c5e8e6` e `#7acac5` deixam as bordas Motif nítidas. A construção
continua sendo vetorial, sem reproduzir o ruído de compressão ou os
contornos borrados do projeto. A textura repete uma trama de 2 × 2 pixels;
os quatro sulcos da faixa inferior são desenhados pelo QML na grade final.

Assets para o QML
-----------------

| Arquivo | Grade nativa | Uso |
| --- | --- | --- |
| `metal-weave.svg` | 64 × 64, repetição 2 × 2 | Fundo tramado dos blocos |
| `metal-lines.svg` | 64 × 24, repetição 2 × 2 | Trama de base da sub-barra |
| `clock-face.svg` | 64 × 64 | Círculo azul, centro (32,32), raio 29, quatro marcas cardinais |
| `clock-reference.svg` | 64 × 64 | Ponteiros estáticos da referência de desenho |
| `graph-reference.svg` | 60 × 35 | Gráfico branco/azul na proporção da referência SR10.4 |
| `graph-grid.svg` | 48 × 40 | Campo auxiliar sem atividade; não exibido na composição atual |
| `mail.svg` | 56 × 27 | Cartão postal claro na proporção da referência SR10.4 |
| `gnu-linux.svg` | 104 × 24 | Selo azul da sub-barra; GNU/LINUX em duas linhas |
| `applications.svg` | 32 × 24 | Três janelas quadradas sobrepostas; gaveta de aplicativos ainda sem função |
| `terminal.svg` | 32 × 24 | Terminal e teclado fixos |
| `preferences.svg` | 32 × 24 | Paleta/ferramentas com recortes; função pendente |
| `drawer.svg` | 32 × 24 | Faixa de ferramentas; função pendente |
| `lock.svg` | 32 × 24 | Cadeado fixo |
| `help.svg` | 32 × 24 | Interrogação fixa |
| `network.svg` | 32 × 32 | Rede na bandeja de diagnóstico |
| `speaker.svg` | 32 × 32 | Volume na bandeja |
| `envelope.svg` | 32 × 32 | Correio na bandeja |
| `storage.svg` | 32 × 32 | Cilindro de armazenamento na bandeja |
| `workstation.svg` | 32 × 32 | Monitor com LED verde quadrado |
| `indicator.svg` | 32 × 32 | Indicador verde circular |
| `indicator-lens.svg` | 19 × 14 | Lente azul e encaixe da faixa metálica |
| `arrow-left.svg`, `arrow-right.svg` | 32 × 32 | Paginação horizontal da Iconbox |
| `arrow-up.svg`, `arrow-down.svg` | 32 × 32 | Paginação vertical da bandeja |

Os arquivos têm `shape-rendering="crispEdges"`. Como o renderer SVG do Qt não
respeitou essa opção em círculos e diagonais durante a conferência, as formas
foram convertidas em fileiras de retângulos inteiros dentro do próprio SVG.
Isso conserva a grade de pixels sem precisar carregar um bitmap. A conferência
com o `QSvgRenderer` do Qt 6 verifica as cores sólidas declaradas e alpha 0 ou
255, sem cores intermediárias de suavização. A face do relógio é opaca;
o espaço fora do círculo e dos demais símbolos é transparente para receber o
fundo do QML. Os assets são desenhos, sem ações, timers ou animações. A execução
de qualquer função dos botões depende da confirmação solicitada pelo usuário.

Esquema KDE opcional
-------------------

`colors/DomainOS-SR10.4.colors`, nome visível **DomainOS SR10.4**, usa a mesma
paleta. As faces de janela e botão são azul-cinza; a seleção é o azul do relógio,
e a área de conteúdo tem fundo azul-cinza mais escuro e texto claro. O arquivo
nunca altera fontes nem configurações por conta própria. Sua instalação e
seleção são responsabilidade do instalador e dos comandos separados da suite.


Proporções dos instrumentos e topo dos demais módulos
----------------------------------------------------

Na referência SR10.4, as faces de data/gráfico medem 60 × 35, o cartão de
Mail mede 56 × 27 e o azul do relógio ocupa cerca de 48 × 48. A ampliação dos
desenhos segue aproximadamente a razão entre a altura dos botões atuais e
originais, 75/59, preservando o aspecto de cada instrumento. Os quatro botões
continuam com 166 × 150 unidades canônicas, ou 83 × 75 pixels em 50%; apenas
os desenhos internos foram ampliados.

| Instrumento | Caixa canônica no QML | Desenho em 50% |
| --- | --- | --- |
| Relógio | 134 × 134 | Canvas 67 × 67; azul de cerca de 61 × 61 e marcas cardinais com extensão de 62 pixels |
| Data | 152 × 88,67 | Face azul 76 × 44,33 |
| Gráfico | 152 × 90 | Face 76 × 44,33, com `PreserveAspectFit` |
| Mail | 142 × 70 | Cartão 71 × 34,23, com `PreserveAspectFit` |

O mostrador conserva apenas quatro pequenas marcas cardinais, como na
referência. Ponteiros afilados de raios aproximados de 27/18 pixels em 50% e
o mostrador compartilham o centro, sem fonte ou timer no desenho do relógio.

A data usa o PCF Latin-1 `contents/fonts/adobe-courier-bold-14.pcf`, carregado
por `FontLoader` somente no aplicativo. O tamanho bitmap nativo é 14, com
entrelinha fixa 17 e escala uniforme `2*75/59` antes da escala do painel. A
tinta branca do exemplo `Feb 27`/`Thu` ocupa cerca de 65 × 35 pixels na captura
em 50%. O arquivo vem do pacote Xorg `font-adobe-75dpi`; os avisos de licença
e a procedência estão em `contents/fonts/LICENSE` e
`contents/fonts/ORIGEM.json`. Ele não altera a seleção global de fontes nem
exige instalar uma fonte no perfil do usuário.

O `Text` da data usa `Text.NativeRendering`, `Text.PlainText` e `smooth: false`.
A rasterização segue as preferências nativas de Qt/Fontconfig, sem forçar
`antialiasing: false`. No Qt 6.8, os glifos nativos já usam Nearest;
`smooth` só controla imagens embutidas no texto, não é apresentado como
correção de filtragem dos glifos. O PCF de um bit permanece naturalmente
binário mesmo com antialiasing ativado. Dois perfis privados em OpenGL
confirmam a data azul/branco, enquanto uma fonte vetorial de controle
demonstra a mudança de rasterização solicitada pelo usuário. O ajuste
não acrescenta timers, auxiliares C++ ou acesso às configurações globais,
nem promete reprodução exata do bitmap Swiss742 original.

O [manual HP VUE2.01 do Domain/OS SR10.4](https://typewritten.org/Manual/Apollo/Domain%3AOS/SR10.4/man1X/vuestyle.bsd.html),
página 6, documenta Swiss742 Bold como fonte de sistema em vários perfis de
tamanho/resolução. Essa é a família histórica provável, mas o recurso
específico da data e seu bitmap não foram confirmados. A Courier bitmap
distribuída pelo Xorg é a experiência monoespaçada solicitada pelo usuário. Seus glifos
não são apresentados como cópia exata da Swiss742 da captura.

Os módulos central e direito começam em Y = 8 e têm altura 150. Suas molduras
externas simples mostram duas linhas claras próprias abaixo das duas claras e
duas ciano do chassi; a faixa ciano não cobre mais o relevo. Os controles
internos mantêm suas molduras compostas. Os bitmaps SGI da iconbox continuam
64 × 64 e são posicionados na grade nativa, com tolerância óptica de meio pixel
em células de largura ímpar. Os dois cartões do pager são iguais e centrados;
suas amostras inferiores ficam contidas no mapa.


## Recoloração pela paleta da sessão

`DomainOSPalette.qml` centraliza os papéis nativos da paleta Qt e os tons do
relevo. `PaletteImage.qml` aplica as URLs recoloridas geradas por `Artwork.js`,
sem mudar o tamanho, viewBox, caminhos ou transparência dos SVGs. As texturas
continuam em Image.Tile no pixel final, e os PNGs SGI conservam seus arquivos
originais. Os templates são gerados deterministicamente a partir dos SVGs;
`gerar-domainos-paleta.py --check` detecta desenhos desatualizados.
O modo de referência mantém as cores e pixels aprovados para comparação.


## Estado selecionado nos exemplos

O pager conserva cabeçalho e texto normais; a seleção usa a lâmpada vertical
e a moldura fina amarela originais (`#dddd28`). O contorno tem a extensão
completa do cartão e espessura de três unidades canônicas. Apenas o cartão
ainda não selecionado afunda durante a pressão, deslocando o conteúdo duas
unidades canônicas; ao soltar ou cancelar, recupera imediatamente a posição
e o relevo normal. Um cartão já selecionado permanece elevado ao clicar.

Se o fundo ou o recesso amarelo esconderem a luz original, `pagerTones` escolhe
tons da mesma família amarela para repouso e pressão. A busca é limitada a
49 luminosidades e considera o contraste mínimo nas duas superfícies: busca
4:1 em repouso e 3:1 durante a pressão, ou o melhor contraste disponível quando
a paleta não permite ambos. O cálculo ocorre somente na troca de paleta,
preservando as cores originais nos quatro esquemas aprovados e na referência.

A Iconbox aplica Highlight/HighlightedText à placa do nome e mantém o relevo
persistente, sem recolorir o bitmap SGI. Cor e relevo são atualizados por
bindings; os SVGs não são recalculados na troca de seleção. A geometria em
repouso é fixa.
A seleção simulada requer a opção explícita da prévia; o modelo de comparação
com cores fixas permanece preservado.
