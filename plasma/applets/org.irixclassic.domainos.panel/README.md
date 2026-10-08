# Irix Classic DomainOS — Design

Este applet reúne o desenho do novo painel em uma única chapa. Ele segue as
proporções do projeto fornecido pelo usuário: relógio azul, data, gráfico e Mail
à esquerda; Iconbox com ícones IRIX; dois quadros de áreas de trabalho; bandeja
em duas linhas de três ícones; setas e faixa inferior com uma gaveta de
aplicativos e cinco atalhos. O Style
`IrixClassicDomainOS` e o esquema opcional **DomainOS SR10.4** são componentes
separados. O Classic existente continua disponível.

Esta versão é **um desenho executável para revisão**. Hora/data, gráfico,
janelas, miniaturas das áreas e dispositivos são amostras fixas da referência.
Os botões mostram o relevo pressionado enquanto o mouse permanece sobre eles e
voltam ao estado normal ao soltar ou sair. Na simulação, o item selecionado da
Iconbox mantém seu relevo pressionado e sua placa de seleção. No pager, somente
a área ainda não selecionada afunda durante a pressão; ao soltar, sobe e mantém
a luz acesa. A área já selecionada permanece elevada durante novos cliques.
Nenhum deles lança aplicativos,
troca áreas, bloqueia a sessão ou modifica dispositivos. A lista de decisões
pendentes está em [DOMAINOS-REQUISITOS.md](../../../docs/DOMAINOS-REQUISITOS.md).
Cada função será implementada depois de sua confirmação pelo usuário.

O desenho tem base de 1942 × 218 pixels, com escala uniforme e sem deformação
dos módulos. Na escala de 50%, ocupa 971 × 109 pixels e os símbolos da bandeja
têm 16 pixels. Bordas e trama conservam a grade de pixels do tamanho final:
a redução mantém os realces e a trama 2 × 2. A faixa inferior tem apenas
quatro sulcos centrais, com quatro pixels de trama acima e abaixo em 50%, como
a referência HP. O metal tem 26 pixels de altura; abaixo dele, o chassi termina
em dois pixels de ciano e dois de sombra ciano. A mesma faixa ciano/sombra
continua pela direita, fora das molduras internas. O tamanho total é preservado. O
widget pede essas dimensões ao Plasma, mas não cria um painel,
não altera a altura do painel atual e não força áreas de trabalho. Selecionar
um Plasma Style também não substitui o layout dos widgets.

A revisão de proporções iguala os grupos superiores esquerdo e direito em
668 unidades, reduzindo a iconbox para 594 e preservando seus sete exemplos.
Os quatro botões esquerdos têm 166 × 150 unidades (83 × 75 pixels em 50%),
com molduras encostadas. Terminam diretamente na iconbox à direita e na faixa
metálica abaixo, sem uma moldura adicional do contêiner.
Os desenhos preservam as proporções da referência, ampliados aproximadamente
pela razão entre as alturas dos botões, 75/59. Em 50%, as faces de data/gráfico
medem 76 × 44,33 pixels e o cartão de Mail mede 71 × 34,23. O relógio tem canvas
de 67 × 67, círculo azul de cerca de 61 pixels e extensão das marcas cardinais
de 62 pixels. Os ponteiros afilados, com raios aproximados de 27 e 18 pixels,
compartilham o centro do mostrador. A ampliação dos desenhos conserva os quatro
botões de 83 × 75 pixels e seus relevos.
Os instrumentos usam molduras simples de dois pixels por lado em 50%, como
no painel HP. As faces ficam separadas pelos quatro pixels dos relevos vizinhos,
sem espaço vazio. Iconbox, pager, bandeja e navegação têm o mesmo relevo
simples externo, começando abaixo do friso ciano; seus controles internos
conservam o relevo composto. Os conjuntos ficam recentrados nos dois eixos,
com sete bitmaps SGI preservados e dois cartões do pager iguais. A bandeja
tem folgas internas iguais, e o indicador inferior
fica centralizado e afastado da direita como na referência. A lente tem
13 × 7 pixels azuis dentro de um aro claro de 17 × 12, com sombra interna.
O encaixe externo de 19 × 14 acrescenta dois pixels de sombra acima e à
esquerda, interrompendo os sulcos e definindo o relevo sem deslocar a lente.
O selo GNU/LINUX usa letras escuras em duas linhas sobre trama clara e uma
moldura simples elevada. As letras têm hastes uniformes e espaçamento regular;
o realce não sobrepõe o interior escuro dos glifos. O desenho tem 20 pixels de
altura dentro da placa de 26, com três pixels livres em cada extremidade e
interlinha de um pixel, conforme a referência HP.
Os cinco símbolos inferiores foram reconstruídos em duas cores, em canvases
32 × 24 que mantêm o tamanho físico da referência na exibição de 50%.
A gaveta de aplicativos ocupa a antiga célula vazia anterior aos cinco
atalhos. Seu desenho mostra três pequenas janelas quadradas sobrepostas,
na mesma paleta azul da chapa. Nesta etapa, o botão oferece somente relevo
pressionado e cancelamento ao sair; a futura associação de aplicativos por
“pin to task manager” aguarda o documento funcional do usuário.

O instalador da suite disponibiliza os arquivos somente para o usuário que o
executa, sem selecionar o novo Style ou o esquema de cores. O widget aparece
como **Irix Classic DomainOS — Design** em Adicionar widgets. Sua inserção e a
troca definitiva do painel ainda dependem das decisões da próxima fase.

Para gerar prints e testar o relevo fora da sessão real:

```sh
python3 plasma/tools/prever-domainos.py --saida /tmp/domainos-design
```

Esse teste usa PyQt6 e um perfil XDG temporário. `--interativo` mantém a janela
de revisão aberta na própria sessão; os botões continuam sem ações. O teste
nativo adicional carrega o KPackage de produção em `plasmawindowed`, usando
Xvfb e um barramento D-Bus privado:

```sh
python3 plasma/tools/testar-domainos-package.py --saida /tmp/domainos-package
```

São ferramentas de desenvolvimento opcionais, não dependências do widget.
O applet utiliza Qt Quick e Plasma 6. A data carrega a fonte bitmap **Adobe
Courier Bold 14** pelo `FontLoader` privado do applet, em
`contents/fonts/adobe-courier-bold-14.pcf`. O texto usa tamanho nativo 14,
entrelinha 17 e escala uniforme `2*75/59`; sua tinta branca ocupa cerca de
65 × 35 pixels na captura em 50%. A data usa renderização nativa, texto simples
e `smooth: false`, com estratégia padrão para seguir as preferências nativas
Qt/Fontconfig, sem impor `antialiasing: false`. No Qt 6.8 os glifos nativos
já usam Nearest; `smooth` só controla imagens embutidas no texto, não é a
causa ou a correção da filtragem dos glifos. O PCF é uma fonte bitmap de um
bit e pode permanecer pixelizado mesmo com antialiasing ativado. Os testes
OpenGL confirmam duas cores na data e verificam a preferência com uma fonte
vetorial de controle. Os demais rótulos usam Nimbus Sans.
O manual original HP VUE2.01 documenta Swiss742 Bold como fonte de sistema,
mas não permite confirmar o bitmap específico da data da referência. A
Courier é uma experiência monoespaçada solicitada pelo usuário, sem alegar
reprodução exata dessa fonte.
O PCF Latin-1 vem de `font-adobe-75dpi`; sua licença e procedência estão em
`contents/fonts/LICENSE` e `contents/fonts/ORIGEM.json`. A fonte é carregada
somente no aplicativo, sem instalação global ou mudança das preferências do
usuário. O relatório nativo registra a família efetivamente resolvida.

[ARTWORK.md](ARTWORK.md) descreve os desenhos, as referências e a paleta.
`contents/images/ORIGEM.json` registra os hashes dos novos SVGs;
`ICONBOX-ORIGEM.json` identifica as cópias dos ícones IRIX já existentes no
repositório. As capturas de referência não fazem parte do pacote. O painel não
contém timers, animações, filtros, sombras desfocadas ou transições de relevo.


## Conexão com as cores do KDE

A versão de trabalho usa `QtQuick.SystemPalette` e acompanha a paleta nativa
Qt/KDE da sessão, incluindo alterações em execução. Fundos, texto e campos
dos instrumentos usam os papéis Window, Base, WindowText, Highlight e
HighlightedText. Os relevos e o metal derivam tons claros/escuros da cor da
janela, conservando a profundidade relativa do desenho aprovado. O indicador
de exemplo usa a cor de destaque; continua sem representar um estado real.
As miniaturas do pager continuam ilustrativas; os bitmaps SGI não são recoloridos.

Os SVGs originais permanecem em `contents/images`. `Artwork.js` contém os
mesmos XMLs para substituição de cores em uma passagem, evitando leituras de
arquivos durante a renderização. As URLs dos desenhos dependem somente da
paleta; redimensionar ou pressionar botões não recalcula os SVGs. Nenhum timer,
Canvas, shader ou helper nativo foi acrescentado ao produto. Para atualizar
os templates após editar um SVG, execute `plasma/tools/gerar-domainos-paleta.py`.

`followSystemColors: false` é o modo de referência dos testes e reproduz o
protótipo aprovado exatamente; não muda a paleta da sessão. A prévia de
comparação mostra o protótipo congelado e a versão conectada lado a lado.
A versão de trabalho não foi instalada nem aplicada às sessões reais.


## Simulação de seleção do pager e da Iconbox

A prévia habilita `simulateSelection: true`: clicar em Work/Procrastination
ou em um dos sete ícones troca somente o índice selecionado dos exemplos.
O pager conserva o cabeçalho normal, com a lâmpada e a moldura fina originais
em amarelo `#dddd28`. Somente a área ainda não selecionada afunda ao pressionar;
soltar restaura imediatamente o relevo e confirma a seleção pela luz. Clicar
na área já selecionada não desloca nem afunda seu conteúdo. Arrastar para fora
antes de soltar cancela o clique e preserva a seleção anterior.

Nos esquemas amarelos em que essa luz se confunde com o fundo ou o recesso,
o indicador usa outro tom do mesmo amarelo. A proteção considera as duas
superfícies e o brilho durante a pressão, buscando contraste de 4:1 em repouso
e 3:1 ao segurar. Quando esses limiares não são possíveis nas duas superfícies,
escolhe o maior contraste mínimo entre os tons candidatos. A seleção continua
indicada também pelo contorno. Esse cálculo depende somente da paleta; cliques
e redimensionamento não o repetem. Os esquemas já aprovados e o modo de
referência conservam a luz original.

A Iconbox usa Highlight/HighlightedText na placa do nome e mantém o relevo
pressionado no item selecionado. O anterior volta ao estado normal. Nenhum
timer ou transição foi acrescentado.

Os índices são independentes (`selectedWorkspaceIndex`, `selectedTaskIndex`).
A simulação é desativada por padrão no applet e não ativa janelas nem troca
áreas de trabalho reais. O modo de referência mantém os pixels aprovados.
O teste isolado `plasma/tools/testar-domainos-selecao.py --saida /tmp/selecao`
exercita o mouse e gera comparativos nos esquemas lsi, DomainOS, claro, escuro
e quatro variantes amarelas da fixture.
