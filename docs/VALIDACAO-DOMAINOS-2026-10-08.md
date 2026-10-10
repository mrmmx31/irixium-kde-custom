# Validação do desenho Irix Classic DomainOS — 2026-10-08

O esquema de cores se chama **DomainOS SR10.4**, conforme a confirmação do
usuário. `IrixClassicDomainOS` é uma opção independente. Os 38 arquivos do
Plasma Style Classic original permanecem idênticos ao inventário registrado
antes desta adição. Os 27 componentes anteriores, os dois perfis globais e a
configuração dos sons permanecem iguais; o catálogo acrescenta três opções,
totalizando 30 componentes.

## Desenho e fontes

O painel usa a composição fornecida pelo usuário, com base de 1942×218 pixels:
quatro instrumentos, sete itens na Iconbox, dois quadros de áreas, bandeja
2×3, setas ▶/▲ e cinco atalhos na faixa inferior. Os símbolos fixos e as
texturas são novos desenhos vetoriais inspirados na referência HP nítida.
Os bitmaps da Iconbox são cópias verificadas dos ícones IRIX do repositório.
As capturas de referência não são distribuídas no pacote.

Os testes nativos atuais confirmaram a fonte bitmap Adobe Courier Bold 14
e Nimbus Sans, esta última resolvida como `Nimbus Sans [UKWN]`, sem
substituição de família. Courier é uma experiência monoespaçada solicitada
pelo usuário; a identificação exata do bitmap original permanece pendente. O desenho
reconstrói as texturas e relevos sem copiar o borrado da imagem de projeto.
As molduras das setas e bandeja preservam quatro bandas em escala 100% e duas
em 50%; os instrumentos usam molduras simples de dois pixels por lado,
com quatro pixels de separação visual entre as faces vizinhas.
Os realces claros se mantêm na grade de pixels da exibição; o marcador de
Procrastination e sua borda compartilham o amarelo da referência. O selo
GNU/LINUX usa a paleta azul, inscrição bitmap escura em duas linhas sobre
trama clara e placa simples elevada, conforme a revisão solicitada.
Terminal/teclado, paleta/ferramentas e ferramenta retangular foram refinados.
São reconstruções vetoriais dos desenhos, não recortes das referências; a
revisão visual pelo usuário continua sendo necessária.

## Verificações executadas

| Verificação | Resultado | Limite da evidência |
| --- | --- | --- |
| `tests/test_components.py` e `tests/test_user_bundle.py` | 20 testes aprovados | Catálogo, independência dos defaults e instalação/restauração dos três novos recursos, preservando preferências, layouts e esquema vizinho |
| `tests/test_domainos.py` e `tests/test_domainos_artwork_palette.py` | 8 testes aprovados | Baseline Classic, origem/hash dos SVGs, cópias SGI, paleta azul e duas linhas do selo e nome/hash do esquema SR10.4 |
| `plasma/tools/prever-domainos.py` | 227 verificações aprovadas | Pressão/cancelamento dos 30 botões; divisórias preservadas; topo dos quatro módulos; conjuntos centrados; proporções nativas do gráfico/Mail; metal, rodapé, selo e lente em 50% |
| `plasma/tools/testar-domainos-package.py` | 25 verificações aprovadas por esquema claro/escuro | KPackage real em `plasmawindowed`, fullRepresentation visível em 1942×218, 101 imagens carregadas, fontes resolvidas e zero erros QML |
| `plasma/IrixClassicDomainOS/tools/verify_artwork.py` | 25 verificações aprovadas | Qt6 QSvgRenderer, KSvg, quatro sulcos/caps/trama na fonte SVG, controles e opacidade; o fallback KSvg esticado tem limitação de frequência da trama, documentada |
| Instalador completo e auditoria em XDG temporário | 30 componentes instalados e auditados, zero falhas | Instalação offline, cópias de compatibilidade de cursores/GTK e restauração, com seleção/layouts/áreas preservados |

O builder/verifier do Style também foi executado novamente sem alterações dos
hashes de saída. As ferramentas não deixam `__pycache__` no componente instalado.
O teste da galeria captura o mesmo QML que o applet carrega; não é um mockup
separado. Os testes usam diretórios privados, e a prova do KPackage utiliza
Xvfb com D-Bus sem ativação de serviços da sessão real.

## Revisão do acabamento Motif pelo Xephyr

A comparação com o [print DomainOS SR10.4 do Virtual OS Museum](https://virtualosmuseum.org/images/more_screenshots/Domain_OS%20SR10.4%20-%2001%20VUE%20desktop.png)
mostrou que a primeira versão perdia os realces ao reduzir filetes para meio
pixel. As faces dos instrumentos também estavam lisas, e a barra inferior
tinha seis tons com contraste menor que a referência. Essa revisão corrige
essas diferenças de acabamento, mantendo a composição de 1942×218 e suas
proporções na exibição de 971×109.

Os fundos usam uma trama de duas cores (`#194b63`/`#a3d0e6`, 2×2 px). A faixa
metálica usa `#3e536e`/`#c4d5ed`, com linhas clara, alternada e escura (2×3 px).
O topo dos relevos começa em `#c5e8e6`/`#7acac5`. Texturas são desenhadas no
tamanho final de exibição, e bandas são ajustadas à grade de pixels. Pressão
inverte o relevo imediatamente, sem timer ou animação no componente.

A prévia interativa foi reaberta em um display Xephyr separado, com HOME/XDG
temporários e D-Bus privado. Ela mostra a referência acima e o QML de produção
abaixo. Os hashes de `kdeglobals`, `plasmarc`, configuração de widgets do
Plasma e `kwinrc` da sessão lsi permaneceram iguais. Nenhum recurso foi aplicado
à sessão principal ou a p001532.

Evidências desta revisão: `/tmp/irix-domainos-motif-20261008/galeria/RESULT.json`,
`/tmp/irix-domainos-motif-20261008/pacote-nativo-final/RESULTADO.json`,
`/tmp/irix-domainos-style-motif-20261008/verification.json` e
`/tmp/irix-domainos-motif-20261008/comparacao-xephyr.png`.
O primeiro ensaio nativo detectou a edição concorrente do README e foi
repetido depois de concluir a documentação do pacote; a execução final passou.

## Revisão de simetria, selo e indicador

A solicitação seguinte substitui o selo neutro por letras e pictograma azuis,
com composição em duas linhas no tratamento da marca HP. O contêiner perde a
placa lisa elevada: passa a ter trama, moldura fina rebaixada e 256 unidades
de largura (128 pixels na exibição). O arquivo SVG continua sendo uma figura
original, com tipografia bitmap local, sem copiar o logotipo HP ou uma fonte
proprietária.

Os grupos superiores esquerdo e direito passam a ter 668 unidades cada. A
iconbox ocupa 598, conserva os sete bitmaps de 64×64 e ajusta suas etiquetas.
Os instrumentos têm retângulos iguais, margens e gaps iguais, perfil fino e
não compartilham mais o segundo invólucro rebaixado. Setas e bandeja mantêm o
perfil composto solicitado.

O poço da bandeja e seu grid ficam centralizados nos dois eixos. Folgas
laterais de 8 unidades e verticais de 10 evitam encostar os botões na moldura.
O indicador inferior, de 36×26 e face `#78a0d5`, tem centro Y=30 na barra de
altura 60 e afastamento direito de 52 (26 pixels em 50%).

A janela Xephyr foi reaberta para avaliação manual e permanece aberta até o
usuário fechá-la. Evidências desta revisão em
`/tmp/irix-domainos-layout-20261008/`; as configurações reais não são aplicadas.

## Revisão da faixa metálica pela referência HP

A próxima comparação confirmou três desvios de acabamento: selo com cores e
relevo invertidos; riscos repetidos pela altura da faixa; indicador com
moldura composta em vez de lente embutida. Foram corrigidos os quatro itens
solicitados pelo usuário, incluindo os símbolos centrais:

- Selo escuro `#3e536e` sobre trama `#c4d5ed`/`#3e536e`, moldura simples clara
  no topo/esquerda e escura embaixo/direita; apenas feedback de pressão.
- Quatro sulcos centrais, cada um com linha clara, alternada e escura, com caps
  escuro/claro e trama antes/depois. O QML preserva a grade de pixels finais.
- Lente de 17×12, interior azul 13×7, aro claro e sombra interna, reconstruída
  em SVG nativo e posicionada no mesmo eixo e afastamento da revisão anterior.
- Terminal, paleta, ferramentas, cadeado e interrogação refeitos em canvases
  32×24 e apenas duas cores, com silhuetas, retícula e sombras estreitas da
  referência. A exibição em 64×48 canônicos conserva o tamanho físico em 50%.

No Style, somente o SVG command-rail mudou em relação ao acabamento Motif
anterior; suas cores locais continuam byte-idênticas. O hint-tile-center foi
retirado desse recurso para evitar repetir os quatro sulcos verticalmente.
1906 IDs/bounds permanecem; a única exceção é esse hint não visual. A trama do
fallback KSvg esticado não conserva a frequência física; o applet QML usado
no Xephyr a conserva. O builder dos 45 arquivos permanece determinístico.

Evidências atuais em `/tmp/irix-domainos-rail-20261008/` (galeria, pacote
nativo, comparação Xephyr) e
`/tmp/irix-domainos-style-four-grooves-20261008/`. Não houve aplicação do tema à
sessão lsi nem alteração de p001532. A janela de comparação permanece aberta.

No lançamento desta comparação, os hashes de `kdeglobals`, `plasmarc`,
`kwinrc` e `kcmfonts` permaneceram iguais. O arquivo de configuração do painel
real, `plasma-org.kde.plasma.desktop-appletsrc`, mudou durante esse intervalo.
Não há cópia textual anterior para identificar a diferença ou estabelecer a
causa; portanto, este lançamento não certifica que todas as configurações
ficaram byte-idênticas. O launcher usa HOME/XDG e barramento privados e não
escreve nesse arquivo real. Nenhuma configuração foi restaurada para evitar
sobrescrever mudanças da sessão do usuário.

A revisão SR10.4 acrescenta prints pressionados representativos do relógio,
Iconbox, pager, bandeja, navegação e atalho inferior, além de Mail. Os relatórios
anteriores à correção de versão e aos refinamentos continuam sendo evidência
histórica; o conjunto SR10.4 deve ser usado para conferir as fontes atuais.

## Correção do encaixe e da tipografia do selo

A revisão visual do usuário identificou o limite da validação anterior: o
indicador tinha apenas o aro interno de 17×12, sem a sombra do encaixe externo.
O SVG agora mede 19×14 e acrescenta dois pixels escuros acima/esquerda, uma
quina clara inferior e a sombra interna superior direita. O item foi movido
quatro unidades acima/esquerda e ampliado, preservando a posição da lente
azul, o centro do aro e a distância da borda direita. A verificação gráfica
passa a exigir esse encaixe em pixels renderizados na escala 50%.

As letras anteriores tinham colunas esticadas, hastes de espessuras diferentes
e um desenho deslocado que cobria partes do glifo. A inscrição GNU/LINUX foi
redesenhada com corpo sólido, altura de oito pixels, hastes de dois pixels,
larguras proporcionais, espaçamento regular e realce somente acima/esquerda,
fora do contorno escuro. Mantém a paleta, o pinguim e a chapa pontilhada.

As evidências dessa revisão ficam em
`/tmp/irix-domainos-seal-lens-20261008/`. A comparação usa o SVG e o QML do
repositório na prévia isolada; os testes verificam renderização e feedback de
pressão, sem certificar uma reprodução pixel a pixel da tipografia HP.
Passaram cinco testes de integridade, 173 verificações gráficas e 21
verificações do KPackage nativo. A primeira tentativa nativa foi impedida de
criar o socket privado do D-Bus no sandbox; a execução isolada fora dele
passou. A nova janela Xephyr foi conferida com hashes dos dois SVGs e do QML
atuais, sem diagnósticos QML. Neste lançamento e na conferência final, os
cinco arquivos protegidos da sessão lsi permaneceram byte-idênticos.

## Altura do metal e rodapé ciano

A faixa metálica SR10.4 ocupa y = 789 a 814 na referência: 26 pixels.
A versão anterior ocupava 30 pixels, com seis linhas de trama acima e abaixo
dos sulcos em vez das quatro originais. Também terminava em tons escuros
distintos, omitindo o friso ciano que pertence ao chassi: y = 815–816 em
`#7acac5`, seguido da sombra y = 817–818 em `#406b68`.

O metal QML agora tem altura 52 e posição Y = 158; o friso e a sombra têm
altura 4 cada, em Y = 210 e 214. O painel continua 1942 × 218. Os módulos
superiores receberam duas unidades de margem em cada extremidade vertical,
preservando a simetria. A inscrição, os cinco símbolos e a lente permanecem
com o mesmo tamanho e posição no painel; as bordas do selo continuam livres.

Passaram cinco testes de integridade, 178 verificações gráficas e 21
verificações nativas. A conferência em 50% exige metal de 26 pixels, quatro
linhas de trama em cada margem, rodapé de duas linhas ciano e duas de sombra,
e bordas do selo preservadas. Capturas e relatórios desta revisão ficam em
`/tmp/irix-domainos-rail-height-20261008/`; o Xephyr usa a produção atual e
permanece aberto para avaliação manual. Não houve aplicação do tema à sessão
principal nem mudança de p001532.

## Quatro botões esquerdos encostados e mais altos

A referência mostra quatro retângulos de 76×59 pixels, encostados pelas
próprias molduras, sem espaço vazio entre eles. A versão anterior tinha
retângulos de 76×57, intervalos de seis pixels e margens verticais de dez.

Os botões agora medem 164×146 unidades (82×73 em 50%), com posições X
6/170/334/498 e Y = 4. As molduras encostam, as margens laterais são iguais
(três pixels) e as verticais são dois pixels. A largura total do grupo
permanece 668 unidades. Relógio, data, gráfico e Mail foram recentrados dentro
dos retângulos maiores. Os demais blocos, o rodapé e o tamanho total do painel
não foram alterados nesta revisão.

Passaram 179 verificações gráficas e 21 verificações nativas. A comparação e
os relatórios estão em `/tmp/irix-domainos-left-buttons-20261008/`. A nova
verificação exige molduras encostadas; a captura e o teste de pressão permitem
avaliar as dimensões na sessão isolada. O Xephyr permanece aberto.

## Fase e decisões pendentes

Hora/data, gráfico, janelas, miniaturas das áreas e status da bandeja são
amostras de desenho. **Nenhuma função de botão está aprovada ou implementada.**
Os botões apenas mostram pressão/cancelamento, sem timer ou animação no produto.
Os tempos de espera dos runners servem exclusivamente para capturar a imagem.

Não foram testadas ativação de janelas minimizadas, troca/criação de áreas,
ações de bandeja, lançadores, bloqueio, ajuda, coleta real de sensores ou
migração de painel. Essas funções e a seleção final permanecem registradas
como pendentes em [DOMAINOS-REQUISITOS.md](DOMAINOS-REQUISITOS.md), F01–F31.
A instalação dos arquivos não seleciona o novo Style/esquema nem modifica o
painel. `aplicar-tema.sh classic` mantém o comportamento anterior.

Os três novos recursos também foram disponibilizados no perfil **lsi**,
com recibo próprio em `~/.local/state/irixium-domainos-design`. A comparação
antes/depois confirmou as configurações protegidas e o Style Classic intactos.
A auditoria local passou para os 30 componentes e para a seleção Classic,
sem divergências. Nenhum painel DomainOS foi inserido. **p001532 não recebeu
estas novas opções nesta etapa**; não há certificação de execução nelas nesse
perfil.

Após a confirmação de **SR10.4** pela referência VUE indicada pelo usuário,
o esquema foi renomeado no catálogo e no perfil lsi. A cópia SR14.4 instalada
na etapa anterior foi retirada somente depois de conferir seu hash contra o
recibo de instalação, mantendo um backup da retirada. Os arquivos instalados
correspondem à revisão refinada; a auditoria local SR10.4 passou novamente.
As configurações protegidas e o Classic continuaram iguais antes/depois.


## Folgas do selo, lateral ciano e separação por relevo

A comparação seguinte corrigiu três diferenças apontadas pelo usuário. O Tux
geométrico e as duas linhas GNU/LINUX ocupam 20 pixels de altura em uma placa
de 26, com três pixels livres acima e abaixo. A linha livre entre a inscrição
superior e inferior passa de duas para uma, conforme o intervalo medido na
referência HP. Letras de oito pixels e hastes de dois continuam preservadas.

A faixa direita do chassi agora tem dois pixels ciano e dois de sombra,
contínuos até o rodapé. Ela tem espaço próprio fora dos módulos: a iconbox
passa a 594 unidades, e pager/bandeja/setas começam em X = 1266/1608/1810.
A faixa metálica começa em X = 8 e tem 1926 unidades, preservando sua altura
26 e o rodapé ciano 2 + 2 em 50%. O indicador mantém 26 pixels de folga à
borda interna direita. O recorte da referência na prévia foi corrigido para
946 × 93 pixels, incluindo as duas colunas de sombra à direita e a primeira
coluna clara à esquerda que antes eram cortadas.

Os quatro instrumentos mantêm os retângulos de 82 × 73 em 50%, sem espaço
vazio entre as molduras. A correção está na espessura do relevo: dois pixels
escuros da moldura anterior e dois claros da seguinte separam suas faces,
como na referência. O topo/esquerda usa `#a3d0e6`, e embaixo/direita usa
`#194b63`; a pressão inverte essas cores imediatamente.

Passaram cinco testes de integridade, 185 verificações gráficas e 21 do
KPackage nativo, sem diagnósticos QML. Os testes novos conferem as junções dos
botões, continuidade da faixa ciano direita, moldura interna preservada,
bordas superior/esquerda e linhas de trama livres acima/abaixo do selo. O primeiro
ensaio detectou que a faixa ciano esquerda cobria uma coluna da moldura do
selo; reservar sua largura antes do metal corrigiu esse problema.

Evidências em `/tmp/irix-domainos-borders-seal-20261008/`. A prévia Xephyr usa
o componente atual do repositório e permanece disponível para avaliação
manual. Os testes verificam essas medidas e o feedback de pressão, sem
certificar uma reprodução integral pixel a pixel do painel HP.


## Moldura única à direita e abaixo dos quatro instrumentos

A avaliação seguinte apontou o relevo extra do contêiner depois da moldura dos
botões à direita e abaixo. O bloco conserva suas 668 × 154 unidades; os quatro
botões passam a 166 × 150, com posições X = 4/170/336/502 e Y = 4. O último
termina exatamente na iconbox, e os quatro terminam na faixa metálica. O
contêiner agora é apenas um Item, sem um segundo Bevel. Os desenhos foram
recentrados, mantendo o relógio e os ponteiros no mesmo centro da grade.

As divisórias entre as faces conservam quatro pixels em 50%: dois escuros e
dois claros. A borda inferior tem apenas os dois pixels escuros do botão,
seguidos imediatamente pelos dois claros da barra metálica. À direita, o
último botão tem seus dois pixels escuros seguidos pelo relevo da iconbox.
O selo, as outras regiões e o tamanho total do painel permanecem iguais.

Passaram cinco testes de integridade, 191 verificações gráficas e 21 do
KPackage nativo. Os testes adicionais verificam a borda inferior de cada
botão e a junção com a iconbox em pixels, além de conservar os testes das
três divisórias e da pressão/cancelamento. Evidências desta revisão em
`/tmp/irix-domainos-instrument-edges-20261008/`; a prévia Xephyr apresenta as
fontes atuais para avaliação manual.


## Topo dos módulos central/direito e proporções dos instrumentos

A faixa ciano do chassi cobria os dois pixels de relevo superior da iconbox,
pager, bandeja e navegação. Esses módulos agora começam em Y = 8 e têm altura
150, mantendo o término em Y = 158. Sua moldura externa usa o perfil simples
original: duas linhas `#a3d0e6` no topo/esquerda e duas `#194b63` embaixo/direita.
Na imagem em 50%, o topo completo mostra duas linhas claras do chassi, duas
ciano e duas claras próprias do módulo. Os controles internos mantêm o relevo
composto solicitado anteriormente; a junção depois do Mail agora tem duas
linhas escuras e duas claras uniformes.

Poço, sete tarefas e setas da iconbox compartilham o centro vertical, com
botões/setas de altura 98 em Y = 26 e poço de 114 em Y = 18. Os sete botões
passam a largura 66 e posições X = 60 + índice × 68, deixando quatro unidades
iguais junto às duas setas. Os bitmaps SGI continuam 64×64, com arredondamento
óptico de até meio pixel nas células de 33 pixels. Os cartões do pager são
158×126, em X = 8/176 e Y = 12; seus rodapés ilustrativos não transbordam o
mapa. Poço/grid da bandeja e as duas setas direitas também ficam centrados.

A medição final dos quatro instrumentos originais encontrou face azul do
relógio de 48×48 (49×49 contando marcas), data/gráfico de 60×35 e Mail de
56×27. A ampliação uniforme usa 83/76, conforme a largura atual do botão;
o espaço adicional na altura vira folga, evitando deformar os desenhos.
O gráfico e o Mail foram reconstruídos nesses aspectos; suas caixas em 50%
são 66×38 e 61×29 com PreserveAspectFit. Data usa 66×38 e DejaVu Sans Mono. O
relógio tem mostrador de 57×57, ponteiros afilados com raios 23/15 e centro
comum. O mostrador inclui margens transparentes; seu círculo ocupa cerca de
52 pixels. A medição usa caixas de desenho, sem afirmar igualdade integral
dos pixels com o software original.

Passaram cinco testes de integridade, 214 verificações gráficas e 21 nativas,
sem diagnósticos QML. O primeiro teste de aspecto usava uma tolerância abstrata
de razão; ela foi substituída pela tolerância concreta de um pixel no tamanho
exibido, coerente com as medidas arredondadas. Os SVGs nativos também são
verificados em suas dimensões completas e com alpha 255, de modo que o canvas
alto antigo não passaria despercebido. Evidências desta revisão em
`/tmp/irix-domainos-upper-instruments-20261008/`.


Na conferência final dos instrumentos, a versão com texto pequeno na data
foi substituída por DejaVu Sans Mono bold, tamanho 30 e entrelinha fixa 36.
O texto branco agora ocupa 51×29 em 50%, compatível com a ampliação dos
47×27 originais; a medição também verifica a centragem horizontal. O relógio
passou de doze marcas maiores para as quatro pequenas marcas cardinais da
referência. Duas verificações adicionais conferem a inscrição renderizada e
as marcas vetoriais, totalizando 214 verificações gráficas aprovadas. O teste
nativo final está em `pacote-nativo-final/RESULTADO.json` nessa pasta de evidências.


## Ampliação dos desenhos sem alterar os botões e revisão da fonte da data

A avaliação do usuário mostrou que a ampliação anterior pela largura deixou
os desenhos pequenos dentro das células mais altas. Esta revisão usa a razão
75/59 entre as alturas dos botões, preservando as proporções dos símbolos.
Os quatro botões continuam em 166×150 unidades, com as mesmas posições,
molduras e divisórias. Em 50%, o círculo azul tem 61×61 pixels, suas marcas
ocupam 62×62 e os ponteiros têm alcances aproximados de 27/18. Data/gráfico
usam 76×44,33; Mail usa 71×34,23. As caixas dos SVGs preservam o aspecto por
PreserveAspectFit. A verificação agora mede paintedWidth/paintedHeight do Qt,
pois a caixa de um Image pode conter folga além da imagem efetivamente pintada.

A fonte DejaVu Sans Mono foi retirada da data. O manual histórico
[HP VUE 2.01 — vuestyle, página 6](https://typewritten.org/Manual/Apollo/Domain%3AOS/SR10.4/man1X/vuestyle.bsd.html)
documenta Swiss742 Bold para fontes de sistema. Isso indica uma família
histórica provável, mas não prova o recurso de fonte da data desta captura.
O cotejo dos oito glifos visíveis encontrou diferenças no bitmap Helvetica,
registradas em `/tmp/irix-domainos-font-identification-20261008/`. Portanto,
a data usa explicitamente uma aproximação: Adobe Helvetica Bold 14 do X11,
em PCF Latin-1 de font-adobe-75dpi, com a licença Adobe/DEC e origem incluídas
em `contents/fonts`. FontLoader registra essa fonte somente no processo Qt
que carrega o applet; não instala fontes, não chama fc-cache e não altera
preferências. O texto mantém o strike nativo de 14 pixels, entrelinha 17 e
escala uniforme 2×75/59, para evitar substituição por fonte vetorial de outro
tamanho. Sua inscrição branca mede 55×35 pixels em 50%. O bitmap Swiss742
original da data ainda não foi recuperado nem declarado como reprodução exata.

Passaram 218 verificações gráficas, 21 do KPackage nativo e cinco testes de
integridade. O teste confirma Adobe Helvetica de 14 pixels com exactMatch,
proporções pintadas dos SVGs, folga até os relevos e feedback imediato de
pressão/cancelamento, sem erros QML. A comparação direta das capturas anterior
e atual confirmou que os pixels das quatro molduras, dos módulos central e
direito, do chassi e da faixa metálica não mudaram. As doze definições de
botões preservaram integralmente x/y/largura/altura.

Evidências em `/tmp/irix-domainos-icon-scale-font-20261008/`. A janela Xephyr
foi atualizada com os fontes de produção e ficou aberta para avaliação manual.
Seu lançamento usou perfil e D-Bus privados; os cinco hashes de configurações
protegidas permaneceram iguais antes/depois do lançamento. Os botões continuam
com as ações pendentes de confirmação individual.


## Símbolo da futura gaveta e preferência nativa de antialiasing

O campo vazio inferior X=587/largura118 recebeu um botão gráfico com
applications.svg. O desenho original tem 32×24 pixels e representa três
janelas retangulares de programas sobrepostas, usando somente #3e536e e
#c4d5ed. Aparece em 64×48 unidades canônicas, com o mesmo relevo/trama do
campo anterior. Os cinco atalhos antigos, as dimensões dos botões e a
composição restante são preservados. A pressão e o cancelamento são apenas
feedback visual. O usuário reservou o botão para a futura gaveta de aplicativos
fixados por “pin to task manager” e pediu explicitamente não implementar essa
função nesta fase; F32 registra a pendência até seu documento.

A data permanece em NativeRendering com o PCF de um bit, escala e entrelinha
preservadas. Foi retirado antialiasing:false para manter QFont::PreferDefault,
permitindo ao Fontconfig usar a preferência do usuário. PlainText e smooth:false
ficam explícitos. A revisão do código Qt 6.8 mostrou que smooth controla
imagens embutidas no texto; os glifos NativeRendering já usam Nearest no shader
de máscara. Portanto, smooth:false não é apresentado como correção de um
borrão dos glifos. Não foi acrescentado filtro, timer, helper C++ ou leitura/
escrita das configurações do usuário.

O teste adicional foi executado em OpenGL real com dois perfis privados de
Fontconfig: antialias=false e true. A data teve apenas azul/branco nos dois,
com estratégia padrão e sem avisos QML, pois os glifos PCF são naturalmente
binários. A fonte vetorial de controle teve duas cores com AA desligado e
222 com AA ligado, comprovando que a preferência chega ao renderer. Esses
ensaios usam DPR=1 e não constituem uma garantia sobre todas as políticas
internas do Qt em HiDPI. Fontes de confirmação: código oficial Qt 6.8,
qquicktext.cpp/setFont, qfontconfigdatabase.cpp/createFontEngine e
qsgdefaultglyphnode_p.cpp/updateSampledImage, registrados com hashes na
pasta /tmp/irix-domainos-aa-review-20261008/.

Passaram 227 verificações gráficas, 22 do KPackage nativo e cinco testes de
integridade. O KPackage carregou o novo SVG e o botão da gaveta, sem erros QML.
Os testes também cobrem pressão/cancelamento do novo botão e a preservação do
slot. Evidências em /tmp/irix-domainos-applications-aa-20261008/, incluindo
prints OpenGL com AA ligado/desligado. O Xephyr foi atualizado e deixado aberto
para avaliação manual, usando somente seu perfil/barramento privados; os cinco
hashes de configurações protegidas permaneceram iguais antes/depois do
lançamento.


## Experiência com Courier na data

A pedido do usuário, a data passou a usar Adobe Courier Bold 14 do X11,
com a mesma licença Adobe/DEC e origem registradas em `contents/fonts`.
O FontLoader permanece privado ao processo do applet. A troca preserva
strike de 14 pixels, entrelinha 17, ampliação uniforme 2×75/59 e estratégia
nativa padrão; não instala fontes nem altera preferências de antialiasing.
O bitmap permanece pixelizado, com somente branco e azul no campo da data.

A inscrição `Feb 27`/`Thu` ocupa 65×35 pixels em 50%, centralizada no botão
83×75 por um ajuste óptico de 3/4 unidades canônicas. O campo azul continua
76×44,33 pixels. A largura rasterizada pode variar um pixel com a posição
fracionária na grade; o teste compara o tamanho nominal arredondado com
tolerância de um pixel. Nenhum botão, relevo ou outro desenho foi redimensionado.

Passaram 227 verificações gráficas, 22 do KPackage nativo e cinco testes de
integridade. A galeria confirma Adobe Courier de 14 pixels com exactMatch
sem fonte vetorial substituta; o KPackage carregou o mesmo recurso, sem
erros QML. Evidências em `/tmp/irix-domainos-courier-20261008/`.

O Xephyr foi atualizado e ficou aberto para teste manual. Seus hashes
correspondem aos fontes atuais, sem avisos QML, e os cinco arquivos de
configuração protegidos permaneceram iguais antes/depois do lançamento.
A comparação pixel a pixel do print anterior com o novo limita as diferenças
à inscrição da data; todos os demais elementos são idênticos.


## Backup aprovado e conexão às cores nativas do KDE

Antes de qualquer alteração de paleta, o protótipo aprovado foi copiado para
`/home/lsi/Downloads/backups/irix-classic-domainos-prototipo-aprovado-20261008-160442`.
A pasta contém 107 arquivos inventariados, incluindo o ZIP, fontes completos
do applet, Style/esquema, prints e validações; SHA256SUMS confirma a cópia.
Arquivos e diretórios foram deixados somente para leitura. Esse backup não
será atualizado nem eliminado. Os testes posteriores usam a cópia de
preparação em /tmp, sem escrever no backup de Downloads.

A versão de trabalho acompanha QtQuick.SystemPalette. Os SVGs originais são
embutidos em Artwork.js e recoloridos numa passagem, preservando coordenadas,
caminhos, transparência e tamanho. URLs dependem somente da paleta; não são
recalculadas por redimensionamento ou pressão. Luz/sombra conservam sua
profundidade relativa, com tons calibrados sobre a cor da janela. Texto,
campos dos instrumentos e seleção usam os papéis nativos do esquema. A cor
do foco e do LED ilustrativo passa a usar o destaque da paleta. Os PNGs SGI
não mudam; as janelas ilustradas no pager conservam cores de conteúdo.

O modo de referência (followSystemColors=false) mantém os pixels do protótipo;
não se afirma equivalência completa de cores do modo conectado com a paleta
fixa anterior. A galeria de referência passou 227 verificações, e o recorte
971×109 coincidiu pixel a pixel com o print aprovado. Os oito testes de
integridade/recoloração também passaram, incluindo colisões entre cores e
preservação de cada pixel/transparência dos 25 SVGs.

O ensaio de troca em execução passou 64 verificações com Breeze Claro,
Breeze Escuro e Irixium. O mesmo painel atualiza os desenhos sem recriação;
resize e pressão preservam suas URLs; a pressão é conferida imediatamente,
e o cancelamento restaura todos os pixels. Courier14 permanece exata e com
estratégia nativa padrão, sem avisos QML. Evidências:
`/tmp/irix-domainos-paleta-independent-final/RESULTADO.json` e
`COMPARACAO-PALETAS.png` nessa pasta.

Os testes KPackage nativos finais passaram 25 verificações por esquema claro
ou escuro. Usam QT_QPA_PLATFORMTHEME=kde, kdeglobals privado e o Style DomainOS
com sua própria paleta azul: mesmo assim, os papéis da aplicação e do painel
coincidiram com o esquema KDE escolhido. Todos os SVGs efetivamente carregados
usaram fontes recoloridas; os bitmaps SGI e fontes resolveram sem fallback.
Não houve erros QML. Evidências em
`/tmp/irix-domainos-paleta-20261008/nativo-claro-final/` e
`nativo-escuro-final/`. A prova nativa DomainOS anterior também passou.

O Xephyr de comparação ficou aberto com o protótipo fixo acima e o candidato
abaixo. Os botões Atual lsi/DomainOS/Claro/Escuro modificam apenas a paleta da
aplicação privada. Os hashes dos fontes atuais correspondem aos da prévia;
os cinco arquivos protegidos da configuração lsi ficaram iguais no lançamento.
O print está em `/tmp/irix-domainos-paleta-20261008/COMPARACAO-XEPHYR.png`.
A substituição do painel em uso continua aguardando a aprovação do usuário.


## Seleção visível e troca simulada no pager e na Iconbox

Esta etapa intermediária foi substituída, no pager, pela revisão de luz e
pressão momentânea descrita abaixo. As evidências da Iconbox continuam válidas.

O usuário apontou que Procrastination quase não se distinguia em lsi e
DomainOS. O contorno anterior usava Highlight junto de fundos muito próximos,
com aproximadamente 1,03:1 de contraste no DomainOS. O pager conectado passou
a preencher o cabeçalho com Highlight, usando HighlightedText na inscrição
e no marcador. Acrescenta um aro interno contrastante de um pixel em 50% e
mantém duas bandas de relevo pressionado. A Iconbox aplica essas cores à
placa do nome e mantém seu relevo pressionado no item selecionado. Proporções,
texturas e bitmaps não mudaram.

A prévia habilita simulateSelection. Cliques com mouse trocam somente os
índices locais Work/Procrastination e dos sete ícones, independentemente;
o anterior recupera a aparência normal. A seleção se confirma ao soltar
dentro do botão, e arrastar para fora cancela. Não há timer, transição,
comando, ativação de janela ou mudança de desktop real. O applet mantém
simulateSelection=false por padrão; os cliques nesse modo não alteram índices.

Passaram 480 verificações de seleção por mouse real no Qt, incluindo os
quatro esquemas Atual lsi, DomainOS, Breeze Claro e Breeze Escuro, exclusividade,
restauração do item anterior, pressão imediata, cancelamento, pixels de título/
texto/aro/relevo, fontes de imagens e geometria intactas. Também passaram as
64 verificações da troca de paleta, 227 da galeria de referência, oito testes
de integridade/recoloração e 25 verificações KPackage por esquema lsi/DomainOS.
Não houve avisos QML. O modo de referência continuou idêntico, pixel a pixel,
ao print aprovado. O backup em Downloads permanece intocado.

Os testes respeitam os pares Highlight/HighlightedText do esquema selecionado,
sem inventar cores para impor um contraste maior. Os contrastes medidos desses
pares foram 7,335:1 em lsi, 3,288:1 em DomainOS, 2,491:1 no claro e 2,428:1 no
escuro. A distinção combina preenchimento, texto, marcador e relevo persistente.

Evidências em `/tmp/irix-domainos-selecao-20261008/`, com folhas separadas
`teste-selecao-completo/COMPARACAO-PAGER.png` e `COMPARACAO-ICONBOX.png`, dezesseis
prints de estados, relatórios e `COMPARACAO-XEPHYR.png`. O Xephyr foi atualizado
e deixado aberto para teste manual, mantendo os hashes das configurações
protegidas iguais no lançamento e os fontes atuais correspondentes à prévia.
A substituição da sessão real continua dependendo da aprovação do usuário.


## Pager luminoso, pressão momentânea e esquemas amarelos

Após comparar os estados, o usuário preferiu a lâmpada e a moldura fina
amarelas originais, com cabeçalho normal. Refinou a pressão: somente a área
ainda não selecionada afunda enquanto o botão está segurado; ao soltar, sobe
e mantém a luz. A área já selecionada permanece elevada durante novos cliques.
Sair com o ponteiro cancela a pressão e preserva a seleção anterior. A Iconbox
mantém seu tratamento de seleção. Nenhum timer ou transição foi acrescentado.

Na orientação seguinte, o usuário exigiu proteção em temas amarelos. O painel
mantém `#dddd28` nas quatro paletas aprovadas e no modo de referência. Quando
um fundo/recesso amarelo esconde essa indicação, calcula dois tons da mesma
família: normal e pressionado. Considera ambas as superfícies, incluindo o
brilho durante a pressão. A busca limitada depende só da paleta; clicar não
recalcula cores nem URLs dos SVGs.

Passaram **2437 verificações** em oito paletas: lsi, DomainOS, Breeze Claro,
Breeze Escuro, amarelo idêntico à lâmpada, pastel, ouro e amarelo escuro. As
sondas leem relevo/posição imediatamente nos eventos de pressão e liberação,
testam cliques repetidos, cancelamento, seleção exclusiva e todos os sete
itens da Iconbox. Após soltar, somente lâmpada/contorno mudam os pixels do
pager. Ao clicar na área já selecionada, o corpo fica imóvel. O retorno
amarelo→lsi restaura os mesmos pixels; modo de referência e configurações
protegidas permanecem iguais, sem erros QML.

| Fundo amarelo | Menor contraste em repouso | Menor contraste ao segurar |
| --- | --- | --- |
| Igual à lâmpada original | 4,480:1 | 3,084:1 |
| Pastel | 4,036:1 | 3,176:1 |
| Ouro | 4,379:1 | 3,329:1 |

No amarelo escuro, a luz original já tem contraste suficiente e não muda.
Também passaram 227 verificações da galeria, com comparação pixel a pixel
com o protótipo aprovado, 64 da troca de paleta, oito testes de integridade
e 25 verificações KPackage nativas por esquema lsi/amarelo. Evidências em
`/tmp/irix-domainos-pager-contraste-20261008/`, especialmente
`teste-selecao-final/RESULTADO.json`, `COMPARACAO-PAGER.png` e
`COMPARACAO-ICONBOX.png` nessa subpasta.

O Xephyr foi atualizado e deixado aberto, com o botão Amarelo para avaliação
manual. A comparação usa os fontes atuais e mantém os hashes das configurações
reais iguais. O backup congelado de Downloads permanece intocado; o painel
real não foi substituído.


## Verificação para publicação

A suíte completa `python3 -m unittest discover -s tests` passou seus 167 testes.
A verificação nativa dos recursos do Style passou 25 verificações adicionais,
com os 38 arquivos da base Classic preservados. `gerar-domainos-paleta.py
--check` confirmou que Artwork.js corresponde aos SVGs atuais, e
`git diff --check` não encontrou erros de espaço em branco. O texto do próximo
goal está em `docs/DOMAINOS-GOAL-ATUAL.txt`, registrando o desenho concluído e
as integrações reais pendentes. Essas verificações não aplicam o painel
DomainOS às sessões reais. Evidências dos recursos nativos em
`/tmp/irix-domainos-commit-20261008/style/verification.json`.
