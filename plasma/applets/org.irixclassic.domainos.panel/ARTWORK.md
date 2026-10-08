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

A cor mais frequente, quantizada em blocos de oito unidades RGB, no interior do
relógio, da data e do gráfico do segundo PNG foi `(48, 144, 192)`. A cor sólida
`#3296c4` conserva esse azul dentro da variação dos pixels da referência. Os
demais tons foram reconciliados visualmente entre ambas as referências para
obter uma paleta pequena e coerente, sem reproduzir o ruído de compressão ou os
contornos borrados do projeto. A textura é uma trama de quatro pixels; os sulcos
da faixa inferior usam seis linhas de cores sólidas, não uma interpolação.

Assets para o QML
-----------------

| Arquivo | Grade nativa | Uso |
| --- | --- | --- |
| `metal-weave.svg` | 64 × 64, repetição 4 × 4 | Fundo tramado dos blocos |
| `metal-lines.svg` | 64 × 24, repetição vertical 6 | Sulcos da sub-barra |
| `clock-face.svg` | 64 × 64 | Círculo azul, centro (32,32), raio 29, doze marcas |
| `clock-reference.svg` | 64 × 64 | Ponteiros estáticos da referência de desenho |
| `graph-reference.svg` | 48 × 40 | Gráfico branco e azul do projeto |
| `graph-grid.svg` | 48 × 40 | Mesmo campo, sem a amostra de atividade |
| `mail.svg` | 48 × 36 | Cartão postal claro do bloco institucional |
| `gnu-linux.svg` | 104 × 24 | Selo monocromático da sub-barra |
| `terminal.svg` | 32 × 32 | Terminal e teclado fixos |
| `preferences.svg` | 32 × 32 | Engrenagem fixa |
| `drawer.svg` | 32 × 32 | Gaveta de arquivos fixa |
| `lock.svg` | 32 × 32 | Cadeado fixo |
| `help.svg` | 32 × 32 | Interrogação fixa |
| `network.svg` | 32 × 32 | Rede na bandeja de diagnóstico |
| `speaker.svg` | 32 × 32 | Volume na bandeja |
| `envelope.svg` | 32 × 32 | Correio na bandeja |
| `storage.svg` | 32 × 32 | Cilindro de armazenamento na bandeja |
| `workstation.svg` | 32 × 32 | Monitor com LED verde quadrado |
| `indicator.svg` | 32 × 32 | Indicador verde circular |
| `arrow-left.svg`, `arrow-right.svg` | 32 × 32 | Paginação horizontal da Iconbox |
| `arrow-up.svg`, `arrow-down.svg` | 32 × 32 | Paginação vertical da bandeja |

Os arquivos têm `shape-rendering="crispEdges"`. Como o renderer SVG do Qt não
respeitou essa opção em círculos e diagonais durante a conferência, as formas
foram convertidas em fileiras de retângulos inteiros dentro do próprio SVG.
Isso conserva a grade de pixels sem precisar carregar um bitmap. A renderização
foi conferida com o `QSvgRenderer` do Qt 6 instalado: os 23 desenhos usaram
somente suas cores sólidas declaradas e alpha 0 ou 255, sem cores intermediárias
de suavização. A face do relógio é opaca;
o espaço fora do círculo e dos demais símbolos é transparente para receber o
fundo do QML. Os assets são desenhos, sem ações, timers ou animações. A execução
de qualquer função dos botões depende da confirmação solicitada pelo usuário.

Esquema KDE opcional
-------------------

`colors/DomainOS-SR14.4.colors`, nome visível **DomainOS SR14.4**, usa a mesma
paleta. As faces de janela e botão são azul-cinza; a seleção é o azul do relógio,
e a área de conteúdo tem fundo azul-cinza mais escuro e texto claro. O arquivo
nunca altera fontes nem configurações por conta própria. Sua instalação e
seleção são responsabilidade do instalador e dos comandos separados da suite.
