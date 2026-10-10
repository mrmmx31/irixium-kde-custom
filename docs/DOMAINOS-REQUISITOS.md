# Irix Classic DomainOS: requisitos e critérios de verificação

**Revisão funcional R2 — mantenedor `mrmmx31`.** Branch `#irixfiles`;
base consultada `2f9f6277736ee6c6187cd010d4dd4f4990bb4822`.

## Atualização de precedência — 2026-10-10

As decisões explícitas posteriores abaixo prevalecem sobre os contratos antigos
do corpo R2 quando houver diferença. O texto original continua preservado como
histórico; esta atualização registra comportamento solicitado, não prova de
execução ou aceite.

| Tema | Decisão vigente |
| --- | --- |
| Gaveta e favoritos | Ler os favoritos do menu Applications do KDE e acompanhar sua ordem, em seção separada. Manter os fixados próprios da barra independentes; sua importação continua explícita e não altera a origem. |
| Preferências na gaveta | Item permanente, fixo e não removível no topo; depois vêm os fixados da barra e, com separadores, os favoritos do KDE. |
| Dicas e prévias | Dicas gerais da barra desligadas por padrão; dicas textuais da Iconbox ligadas. Miniaturas e realce das janelas ao passar o mouse são alternativas desligadas por padrão, habilitadas nas preferências. |
| Clique simples na Iconbox | Selecionar imediatamente e abrir a lista, inclusive para uma única janela, sem restaurá-la por esse clique. Ctrl/Shift conservam a seleção acumulativa. |
| Duplo clique individual | Minimizar a janela ativa, restaurar a minimizada ou ativar a inativa. Um grupo mantém a escolha explícita de membros, sem operação coletiva implícita. |
| Título no seletor | Sem checkbox marcado, restaurar/ativar a janela do título. Durante a seleção por checkbox, o título marca/desmarca; esvaziar a seleção recupera a restauração direta. |
| Roda na Iconbox | Percorrer os itens como as setas laterais, sem ativar janelas. Alternar janelas pela roda permanece opção nas preferências. |

O [manual funcional atual](../plasma/applets/org.irixclassic.domainos.panel/FUNCTIONAL.md)
descreve os gestos e os padrões; a [matriz de validação](DOMAINOS-MATRIZ-VALIDACAO-R2.md)
separa implementação, provas e limites. A entrega da suíte completa em p001532
está em andamento. Esse registro não declara instalação concluída, ativação do
tema ou aceite pessoal nessa sessão, nem antecipa o aceite da prévia no lsi.

## Escopo e precedência

Acrescentar o Plasma Style **Irix Classic DomainOS** e conectar seu painel aprovado
às funções reais do KDE, preservando a opção Irix Classic existente. A referência
histórica é Domain/OS SR10.4 / HP VUE; a aparência aprovada não impõe regressão de
recursos modernos. O desenho, a conexão às cores e a seleção simulada são o estado
de protótipo descrito na base. As funções aprovadas abaixo ainda exigem implementação
e evidência próprias; não foram executadas nesta revisão documental.

A prancheta PCU-VUE-KDE-R1 tem 28 respostas completas. Esclarecimentos posteriores
fecharam as dúvidas de Iconbox, operações em lote, gaveta, Pager, bandeja, medidores,
lente e preferências. São fontes complementares, não uma alteração do JSON original.
Ver [rastreamento](DOMAINOS-DECISOES-CONSOLIDADAS.md),
[preferências](DOMAINOS-PREFERENCIAS.md) e [goal](DOMAINOS-GOAL-ATUAL.md).
A entrada legada [DOMAINOS-GOAL-ATUAL.txt](DOMAINOS-GOAL-ATUAL.txt) mantém conteúdo igual.

**Nomenclatura:** `REQ-F01` significa o F01 deste memorial; `RESP-F01` significa a
resposta F01 da prancheta (gestos). Os F01–F32 originais são preservados, com F33–F35
acrescentados para requisitos transversais novos. D0–D10 continuam critérios visuais.

A regra de precedência é: decisão explícita mais recente; respostas e justificativas
da prancheta; proposta original apenas no que foi aceito e não substituído; descrição
técnica antiga como contexto. Detalhes novos do redator aparecem como **proposta de
implementação**, não como aprovação expressa. Lacunas técnicas devem ser registradas;
não devem ser preenchidas silenciosamente por analogias a Windows, IRIX ou KDE.

**As seções de geometria e a matriz visual a seguir são registros da base aprovada.**
Suas expressões “apenas desenho”, “aguardar documento” e “sem função” descrevem o
protótipo anterior à integração. Não se sobrepõem aos requisitos funcionais R2 e
não reabrem decisões já tomadas. A seção posterior substitui a antiga lista que
marcava todos os F01–F32 como pendentes. Preservar as medições, fontes e paleta;
nenhum arquivo de fonte, imagem ou código é distribuído por este pacote documental.

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
“paginação vertical”. As funções desses dois botões eram pendentes na base visual; a R2 as define em REQ-F21/REQ-F22.

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
livres acima/abaixo na placa de 26 pixels e interlinha de um pixel. Na base visual ele mostrava
apenas pressão/cancelamento; a função de menu geral é definida em REQ-F01.

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
o QML exibe o símbolo em 64×48 unidades. Na base visual o botão oferecia apenas pressão e
cancelamento. A R2 confirma a associação dos aplicativos de “pin to task manager”
à gaveta, conforme REQ-F32. O desenho não altera os cinco atalhos inferiores;
lançadores fixos e tarefas continuam sendo conceitos separados.

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

## Requisitos funcionais consolidados — F01–F35

**Situação comum:** decisão funcional aprovada; integração/aceite técnico ainda não
comprovados pelo protótipo. “Aprovado” nesta tabela não é “implementado”. REQ-F14
contém um subrecurso explicitamente adiado; REQ-F33 inclui uma estrutura sugerida de
páginas, distinguida no documento próprio. Não usar novamente a tabela antiga de
pendências para bloquear os comandos já aprovados.

| ID estável | Controle ou comportamento | Decisão consolidada | Origem |
| --- | --- | --- | --- |
| REQ-F01 | Placa GNU/LINUX | Abrir menu geral de aplicativos pela placa existente. Não limitar a ajuda a esse emblema. | RESP-A01; esclarecimento do lançador |
| REQ-F02 | Relógio analógico | Hora local; clique abre consulta de hora/fusos suspensa, não duplica o calendário. | RESP-A02 |
| REQ-F03 | Data e calendário | Seguir localidade completa do sistema; abrir calendário suspenso e agenda se configurada. | RESP-A03 |
| REQ-F04 | Instrumento gráfico | Recepção e envio de rede simultâneos por padrão; métrica substituível em preferências; clique abre gr_osview suspenso. | RESP-A04; rodada Q7 |
| REQ-F05 | Correio institucional | Abrir cliente configurado; Thunderbird como preferência informada. Estado/contagem somente com integração real autorizada. | RESP-A05 |
| REQ-F06 | Conteúdo da Iconbox | Tarefas reais, abertas e minimizadas segundo filtros do perfil. Só minimizadas é opcional. Agrupamento configurável; fixados na gaveta. | RESP-B01/B04; Q1/Q4; REQ-F35 |
| REQ-F07 | Seleção e ativação | Clique simples seleciona sem ativar; duplo clique restaura/ativa. Resposta visual imediata. | RESP-B02; Q2 |
| REQ-F08 | Menus e gestos da Iconbox | Manter menu direito existente e adicionar organização; Ctrl/Shift e grupos conforme REQ-F34. Encerrar à força em submenu. | RESP-B02/B05; Q2/Q3; REQ-F34 |
| REQ-F09 | Seta esquerda da Iconbox | Voltar um conjunto/página de ícones; indisponível no limite; sem mudar o painel. | RESP-B03 |
| REQ-F10 | Seta direita da Iconbox | Avançar um conjunto/página de ícones; indisponível no limite; total de tarefas não limitado às células. | RESP-B03; Q1 |
| REQ-F11 | Primeiro cartão de desktop | Vincular ao desktop real por identidade estável; clique ativa. Estado luminoso/relevo aprovado permanece. | RESP-C01/C02 |
| REQ-F12 | Segundo cartão de desktop | Mesma regra do primeiro; cartão existente não cria/renomeia desktop durante carregamento. | RESP-C01/C02 |
| REQ-F13 | Quantidade e nomes de desktops | Permitir criação/remoção/renomeação explícitas, mínimo um; um ocupa módulo, dois lado a lado, mais acessíveis por navegação. | RESP-C01; Q5 |
| REQ-F14 | Miniaturas e navegação do Pager | Geometria, não screenshots; roda percorre cartões por padrão, troca de desktop é opção. Arraste entre miniaturas adiado. | RESP-C02/C03/C04; Q5 |
| REQ-F15 | Rede na bandeja | Estado e controle do provedor real; não conectar/desconectar ao abrir a gaveta. | RESP-D01/D05 |
| REQ-F16 | Volume na bandeja | Manter ação, menu e ajustes nativos; rolagem de volume restrita ao item correspondente. | RESP-D05 |
| REQ-F17 | Correio/mensagens na bandeja | Item real configurado pelo usuário; não duplicar integração nem inventar status por existir envelope de exemplo. | RESP-A05/D01/D05 |
| REQ-F18 | Armazenamento na bandeja | Item real de dispositivos, ações explícitas e capacidades do provedor; sem ejetar por navegação. | RESP-D01/D05 |
| REQ-F19 | Monitoramento na bandeja | Preservar item real escolhido e seu alvo; desenho ilustrativo não comprova um serviço de monitoramento. | RESP-D01/D05 |
| REQ-F20 | Sexta posição da bandeja | Entrada real escolhida; nenhum LED permanentemente normal sem fonte. Os seis símbolos do protótipo não fixam seis serviços universais. | RESP-D01/D05 |
| REQ-F21 | ▶ à direita | Excedentes configurados como visíveis; continuação deslocada prioritária, paginação alternativa. Incluir ocultos é preferência. | RESP-D02/D03; Q6 |
| REQ-F22 | ▲ à direita | Status e notificações; preservar acesso aos itens ocultos. Não repetir compulsoriamente a ▶ nem limpar histórico ao abrir. | RESP-D04; Q6 |
| REQ-F23 | Política da bandeja | Seis posições 2×3, ordem/visibilidade configuráveis; preservar atenção e provedores; sem ocultação global indiscriminada. | RESP-D01/D02/D05; Q6 |
| REQ-F24 | Terminal do rodapé | Nova sessão/janela do terminal preferido como usuário normal, sem comando adicional. | RESP-E01 |
| REQ-F25 | Paleta/preferências do rodapé | Abrir System Settings em Appearance & Style. Central própria do painel é requisito distinto. | RESP-E02; REQ-F33 |
| REQ-F26 | Sessão do rodapé | Abrir opções de sessão incluindo suspensão e hibernação conforme disponibilidade; nenhuma ação destrutiva automática. | RESP-E03 |
| REQ-F27 | Cadeado | Solicitar bloqueio real, sem encerrar aplicações; informar impossibilidade/falha. | RESP-E04 |
| REQ-F28 | Ajuda | Menu na ordem: ajuda local do painel, xman, ajuda KDE. xman acompanha esquema e contraste; ajuda distribuída com o produto. | RESP-E05 |
| REQ-F29 | Lente de atividade | Acompanhar operação observável; opção de permanência adicional após conclusão desligada por padrão; não atrasar comando. | RESP-E06/F01; Q8 |
| REQ-F30 | Inserção e migração do painel | Instalação por usuário; painel ativo só substituído com autorização; preservar widgets, identidades e restauração. | RESP-F02; goal original |
| REQ-F31 | Plasma Style e cores | Variantes independentes; esquema escolhido respeitado sem reaplicar layouts ou alterar outros perfis. | RESP-F02/F03; desenho aprovado |
| REQ-F32 | Gaveta de fixados | Usar domainosApplicationsDrawer; lista própria com importação opcional; clique solicita nova janela/instância. | RESP-B01; Q4; esclarecimento de localização |
| REQ-F33 | Central de preferências | Organizar por ferramenta em navegação semelhante ao System Settings, preservando padrões e alternativas aprovadas. | RESP-B04/F01; esclarecimento final 2 |
| REQ-F34 | Seleção de grupos e operações em lote | Membros escolhidos por checkboxes e seleção acumulada entre grupos; não selecionar grupo inteiro implicitamente; organizar no desktop/monitor atuais. | RESP-B02; Q2/Q3; esclarecimento final 1 |
| REQ-F35 | Filtro automático da Iconbox | Opcional: contar janelas antes de filtrar e agrupar; maior que limiar liga só minimizadas, menor/igual volta à apresentação normal. | Q1; confirmação final 2 |

## Detalhamento das decisões novas

### Iconbox: conteúdo, contagem e filtro automático

**Decisão confirmada:** manter o padrão atual de tarefas abertas e minimizadas,
respeitando o escopo configurado de telas, atividades e desktops. O filtro manual
“somente minimizadas” é uma alternativa. A contagem de tarefas não tem teto funcional
igual à quantidade de ícones visíveis; as setas dão acesso ao restante.

O modo automático é opcional. A preferência contém habilitação e limiar numérico,
cujo valor inicial não foi escolhido pelo usuário nesta conversa. Não converter um
exemplo de documentação em valor aprovado. Sem habilitação explícita, a opção não
muda o filtro do perfil.

Para decidir a ativação automática, **N** é a quantidade de janelas reais no escopo
normal da Iconbox, antes de aplicar “somente minimizadas” e independentemente do
agrupamento. Um grupo de quatro janelas contribui com quatro, não com um. Lançadores
fixos e ícones da bandeja do sistema não pertencem à contagem. **L** é o limiar.

| Situação, com modo automático habilitado | Apresentação |
| --- | --- |
| N é maior que L | Apenas janelas minimizadas do mesmo escopo |
| N é igual a L ou menor | Volta à apresentação normal do perfil |
| Um grupo é expandido/recolhido | Não muda N por esse motivo |
| A janela é minimizada/restaurada | Não muda N por esse motivo; sua inclusão visual depende do modo vigente |
| Uma janela entra/sai do escopo ou abre/fecha | Recontar com os mesmos critérios |

É um filtro de apresentação. Não minimizar janelas para satisfazer a regra, não
fechar tarefas e não reduzir o limite total. Contar o resultado já filtrado geraria
uma condição circular; a regra aprovada usa o conjunto anterior ao filtro.

**Detalhamento proposto para implementação:** apresentar a escolha manual “só
minimizadas” e a escolha automática como modos distintos, evitando dois checkboxes
contraditórios. Se o usuário escolher o modo manual, não fazê-lo desaparecer porque
N diminuiu. Essa organização da preferência precisa de ensaio de interface; a regra
N/L em si já foi confirmada. Mostrar claramente que o filtro automático está ativo,
sem acrescentar botões ou mudar as proporções aprovadas.

### Seleção, grupos e menu de operações

**Decisões confirmadas:**

- Clique simples em janela individual seleciona imediatamente, sem restaurá-la.
  Duplo clique restaura/ativa. Não esperar um segundo clique para mostrar a seleção.
- Ctrl acrescenta/retira itens; Shift seleciona um intervalo. A seleção não é a
  mesma coisa que a janela atualmente ativa.
- Ao selecionar um grupo, apresentar suas janelas com checkboxes. O usuário marca
  membros, conserva essas escolhas e passa aos próximos itens/grupos. Não incluir
  todas as janelas do grupo por suposição.
- Após formar uma seleção de duas ou mais janelas e soltar Ctrl/Shift, abrir o menu
  de operações em lote. Escape fecha sem executar. O botão direito continua abrindo
  o menu existente, ampliado com organização.
- Para organizar, reunir o conjunto escolhido no desktop/monitor atuais. Mosaico,
  disposição em colunas, disposição em linhas, maximizar e minimizar em massa são
  comandos distintos. O rótulo deve explicar a disposição, sem ambiguidade entre
  “vertical” e “horizontal”.

**Detalhamento proposto para tornar o novo seletor de grupos utilizável:** manter a
lista aberta ao marcar uma caixa; preservar a seleção acumulada ao fechar a lista
para passar a outro grupo; distinguir visualmente seleção parcial de completa,
por exemplo mostrando “2 de 4”, sem alterar a chapa principal. A lista é um seletor,
não o menu de organização: marcar uma caixa não ativa nem executa ação na janela.
A liberação de Ctrl/Shift durante a navegação da lista não deve interromper cada
marcação com o menu de operações. Suspender esse automatismo enquanto o seletor de
grupo estiver aberto e avaliá-lo ao concluir o gesto fora dele é uma solução proposta,
não um novo gesto já confirmado pelo usuário. Documentar e testar a sequência final.

Exemplo de intenção aprovada: escolher os terminais A e C de um grupo de quatro,
depois a janela B de outro grupo; a operação tem três alvos, não todas as janelas
dos dois aplicativos. Não interpretar o fechamento do popup como a ordem de
restaurar o grupo. O gesto de duplo clique sobre o resumo de um grupo, diferentemente
de uma janela individual, não foi detalhado; preservar a escolha explícita de membros
sem introduzir ativação coletiva silenciosa.

**Critérios técnicos propostos de integridade da seleção:** guardar identidade das
janelas, não posições transitórias da lista; janela nova no grupo não entra na seleção
sem escolha; janela fechada deixa de ser alvo e não transfere seleção à linha seguinte.
A operação deve informar alvos que deixaram de existir ou não aceitam a ação.
Esses critérios evitam atingir janelas que o usuário não escolheu.

O menu contextual normal deve continuar disponível. Fechar normalmente respeita o
fluxo do aplicativo; “matar processo” fica em submenu. Identificação do processo,
confirmação e efeitos sobre várias janelas do mesmo processo são questões de segurança
a validar na implementação; não equiparar a seleção de uma janela à autorização
para encerrar todos os processos do aplicativo.

### Gaveta: lançadores não são tarefas

**Decisão confirmada:** o botão é `domainosApplicationsDrawer`, na célula que era
vazia, imediatamente antes do terminal. Não usar `domainosShortcut_drawer` para essa
função: esse terceiro atalho representa Sessão. O emblema abre o menu geral e a
gaveta abre apenas os fixados, como entradas distintas.

A lista pertence ao painel DomainOS. A importação dos fixados existentes é opcional
e não cria sincronização contínua com outra instância. Favoritos do menu de aplicativos
continuam conceito separado. Retirar um pin não fecha a tarefa nem desinstala o programa.
Acionar um pin solicita nova janela/instância; não o substitui pela tarefa aberta.
A janela criada aparece na Iconbox segundo os filtros desta. Se o aplicativo não
oferecer nova janela, respeitar sua capacidade real; não prometer comportamento
universal de múltiplas instâncias.

A posição da gaveta já está aprovada. Ordenação, gerenciamento dos pins e importação
pertencem à página específica de preferências; não ocupam as células de tarefas.

### Pager, bandeja e navegação sem efeitos colaterais

O Pager tem um módulo fixo. Com uma área, a miniatura continua visível e usa seu
espaço; com duas, aparecem dois cartões; com mais, há navegação e setas inferiores.
A roda apenas percorre os cartões por padrão. Trocar a área imediatamente pela roda
é opção explicitamente alternativa. O clique no cartão ativa a área, e clicar na
atual não executa outro comando. Não apagar/renomear desktops para reproduzir a imagem.

Criar, remover e renomear são ações explícitas com reflexo real no KWin. A criação de
um perfil novo pode sugerir Work/Procrastination, sem impor esses nomes ao perfil
existente. Janelas em todas as áreas, múltiplos monitores e minimizadas precisam ter
representação coerente com dados reais. A solicitação RESP-C03 de conferir a referência
IRIX permanece pendente de pesquisa; não declarar equivalência histórica integral.

Na bandeja, distinguir:

| Conjunto | Acesso padrão |
| --- | --- |
| Até seis entradas escolhidas como visíveis | Matriz 2×3 |
| Visíveis que excederam seis posições | ▶: continuação deslocada; paginação se necessário |
| Configuradas como ocultas | Quadro de status/acesso aos ocultos da ▲, sem inserção compulsória na ▶ |
| Ocultas quando a opção “incluir ocultos na ▶” estiver ligada | Também acessíveis na continuação; não duplicar/destruir provedores |
| Histórico e controles de notificação | ▲ |

A posição física dos dois botões não muda. A continuação/gaveta não estica a chapa.
A preferência de incluir ocultos não autoriza perder estados de atenção ou tornar
itens inacessíveis. Os ícones fornecidos por aplicativos continuam vinculados a seus
itens reais, com clique/menu próprios. A abertura de uma gaveta não altera volume,
conexões, dispositivos ou “Não perturbe”.

### Medidores, preferências e lente

O instrumento pequeno mostra recepção e envio de rede simultaneamente. A preferência
permite escolher outro objeto de medição. O `gr_osview` existente é a base para o
painel suspenso completo, não um pedido para reescrever todos os sensores.
Interface(s), unidade, escala e janela temporal precisam estar identificadas no
detalhe/preferências. A escolha de medir rede é decisão funcional; a afirmação de
que a referência histórica media rede não foi comprovada por esta consolidação.

O botão de aparência continua indo a Appearance & Style do System Settings. A
**central de preferências do painel** é organizada por ferramenta, conforme pedido
final, e não muda esse atalho por dedução. O acesso à nova central e as convenções
de navegação são detalhados como proposta em `DOMAINOS-PREFERENCIAS.md`.

A lente representa a operação observável. Por padrão, acompanha início e fim.
A opção “Manter luz acesa após a conclusão” tem checkbox e tempo configurável,
desabilitada por padrão. O tempo é **adicional depois da conclusão**, não um tempo
mínimo total de execução. O campo fica sem efeito com a opção desligada.

Se o provedor só confirmar que a solicitação foi enviada, essa é a evidência que
pode ser comunicada; não manter a lente até um “fim” inventado. Falhas precisam ser
informadas, não encobertas pelo prolongamento. Animações opcionais de apresentação
não atrasam comandos, cliques ou repinturas. A aprovação não autoriza importar timers
do antigo menu de duplo clique ou reintroduzir feedback artificialmente bloqueante.

**Detalhe proposto:** com operações simultâneas, a lente permanece acesa enquanto
houver operação observável pendente; o prolongamento começa depois da última. Uma
nova operação cancela o apagamento programado, não a operação. Essa regra é proposta
para ensaio, pois o usuário definiu o comportamento individual, não concorrência.

## Integração com a base existente — orientação, não implementação nesta revisão

As notas técnicas da versão anterior eram hipóteses condicionadas às confirmações.
Elas não podem contrariar as decisões R2. Em especial, não fixar `filterNotMinimized`
ou `GroupDisabled` como política universal: o primeiro passa a seguir o modo escolhido,
e o segundo não representa o agrupamento configurável aprovado.

Na base consultada existem `org.irixclassic.applications`, `org.irixclassic.iconbox`,
`org.irixclassic.grosview`, `org.irixclassic.quicklaunch` e
`org.irixclassic.systemtray`. O painel integrado é `org.irixclassic.domainos.panel`;
seu `DomainOSPanel.qml` ainda usa dados ilustrativos e seleção local opcional. O
reaproveitamento deve preservar provedores, identidades e recursos úteis, não incorporar
apenas uma cópia visual que descarte comportamento já disponível.

As notas anteriores registram `TaskManager.TasksModel`, dados de desktops e modelos
da bandeja. Confirmar sua disponibilidade na versão realmente instalada antes de
implementar chamadas. Identidades estáveis e validação do alvo são necessárias; um
índice de linha ou rótulo de desktop não é identidade persistente. Não criar regras
KWin só para observar minimização se o modelo já informa o estado.

A grade 2×3 é requisito de apresentação. Não inventar parâmetros universais `rows=2`
ou `iconSize=16`; o memorial anterior já distinguiu esse desenho das opções reais
da bandeja. A integração deve preservar seu containment/provedor e mostrar estados
reais. A conversão das seis imagens ilustrativas em itens reais ainda exige trabalho.

Janelas não são arquivos. Para operações em lote, verificar a API/autorização da
sessão e o suporte de cada janela; não presumir que a mesma manipulação de geometria
esteja disponível da mesma forma em X11 e Wayland. Sem capacidade, registrar
indisponibilidade e a restrição precisa. Isso não autoriza declarar o requisito
implementado, nem abandonar sua investigação porque depende de integração adicional.

## Matriz de verificação funcional proposta

Estes são critérios para a futura implementação. **Não são resultados de testes
executados nesta entrega.** A referência visual e D0–D10 continuam sendo comparadas
sem alterar seus arquivos ou o backup aprovado.

| ID | Ensaio | Critério de resultado |
| --- | --- | --- |
| VF01 | Emblema e gaveta | Emblema abre menu geral; botão próprio abre pins; nenhum substitui o atalho de Sessão |
| VF02 | Relógio/data | Hora/fusos e calendário separados; localidade correta; agenda só quando configurada |
| VF03 | Rede/medidores | Recepção/envio reais e unidades explícitas; trocar métrica nas preferências; fonte ausente não vira zero |
| VF04 | Correio | Cliente escolhido abre; contagem só com fonte autorizada; ausência de fonte não vira “sem mensagens” |
| VF05 | Tarefas e agrupamento | Abertas/minimizadas conforme filtro; grupo não limita contagem; fixados não substituem tarefas |
| VF06 | Clique/seleção | Primeiro clique seleciona sem espera; duplo restaura; direito preserva menu e inclui organização |
| VF07 | Grupo por checkboxes | Escolher parte do grupo e passar a outro conserva os alvos, sem incluir todos ou executar ação ao marcar |
| VF08 | Mudança da lista | Encerrar/reagrupar janelas não transfere seleção para outra identidade |
| VF09 | Organização | Aplicar disposição a 2/3/6 janelas selecionadas no destino atual; distinguir mosaico, maximizar e minimizar |
| VF10 | Filtro automático | N>L liga, N≤L retorna; N é anterior ao filtro e ao agrupamento; nada é minimizado/fechado por essa regra |
| VF11 | Gaveta | Lista própria, importação explícita, pin removido não fecha tarefa; pedido de nova janela não reaproveita task slot como launcher |
| VF12 | Pager | Uma/duas/várias áreas, setas inferiores, roda só navega no padrão e só troca quando a alternativa é ligada |
| VF13 | Miniaturas | Sem conteúdo real capturado; capacidades e estados especiais documentados; arraste adiado não fica parcialmente ativo |
| VF14 | Bandeja | Seis posições, excedentes visíveis na ▶, ocultos/status na ▲, alternativa incluir ocultos, sem perder atenção |
| VF15 | Comandos de sessão | Abrir diálogo não suspende/desliga; bloqueio verdadeiro; falhas informadas; testar ações sensíveis só com autorização |
| VF16 | Ajuda | Ordem painel/xman/KDE, ajuda instalável localmente, contraste no esquema escolhido, ausência do xman explicada |
| VF17 | Lente | Padrão acompanha evento real; tempo adicional adia só apagar; comando concluído não fica bloqueado |
| VF18 | Preferências | Cada função está em sua ferramenta; padrões/alternativas distinguíveis; valores não escolhidos não apresentados como aprovados |
| VF19 | Instalação/restauração | Recursos independentes, preservação de outros perfis e do Classic; reversão comprovada antes de substituir painel ativo |
| VF20 | Desempenho/acessibilidade | Resposta imediata de controles, teclado e foco testáveis; telemetria não impede cliques; desenho estável durante notificações |

## Estado de execução e pendências remanescentes

As decisões funcionais principais desta rodada estão fechadas. A afirmação anterior
“todos os itens aguardam confirmação” está superada. Não gerar nova prancheta de 28
itens para perguntar as mesmas coisas. Permanecem:

**Implementação e verificação:** ligar dados reais, testar comportamento e capacidades,
preparar preferências, empacotar documentação e validar instalação/restauração. Esta
consolidação não executou essas tarefas e não muda a fase real do código.

**Adiado por decisão do usuário:** arrastar janelas entre miniaturas do Pager. Manter
no próximo ciclo; não adiar por associação os menus de movimentação ou a organização
em lote. A gaveta de fixados não permanece adiada.

**Precisão a registrar no desenvolvimento:** valores iniciais/ranges do limiar e do
tempo extra da lente não foram escolhidos; fluxo fino de conclusão do seletor de
grupo, comando sobre resumo de grupo e monitor considerado “atual” precisam ser
explicados no ensaio. As soluções propostas acima não podem ser citadas como respostas
expressas do usuário. Um impedimento nesses detalhes não autoriza trocar uma decisão
já aprovada sem consulta.

**Pesquisa histórica solicitada:** RESP-C03 requer confronto com a referência IRIX.
A função exata original de alguns glifos e do gráfico não foi comprovada por esta
revisão. As funções escolhidas para a adaptação não devem ser apresentadas como
certeza sobre o HP VUE original.

## Instalação e evidências

O preview deve usar o componente efetivo de composição, sem que fixtures sejam
apresentadas como dados reais. Os ensaios funcionais devem distinguir consulta de
estado, pedido de ação, execução confirmada e falha. Prints de relevo provam desenho,
não provam mudança de desktop, leitura de rede ou funcionamento da bandeja.

Instalar arquivos por usuário não seleciona automaticamente outro estilo, não
recria o painel e não altera a sessão de outro perfil. A migração do painel ativo
exige autorização específica e restauração verificável. Os perfis lsi e p001532
continuam sujeitos à autorização de cada sessão. O backup descrito abaixo é só
referência. Os caminhos/ferramentas de teste listados no memorial original são contexto
da base, não uma afirmação de que foram executados novamente nesta revisão.

## Registro da base visual e backup (histórico)

Os trechos abaixo conservam o histórico da base aprovada. Referências a funções
pendentes descrevem aquele estado anterior à consolidação R2; para decisões vigentes,
prevalecem REQ-F01–REQ-F35. Não alterar os recursos ou o backup por esta documentação.

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
Na base consultada, miniaturas, horário/data e dispositivos eram ilustrações;
as ações agora confirmadas em F01–F35 ainda precisam de integração. Nenhuma
sessão real deve ser alterada só por esta revisão documental.


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

**Correção funcional solicitada em 09/10/2026:** minimizar uma janela selecionada
deve levantar os relevos do seu botão e rótulo no Iconbox. A seleção, o destaque
de cor e os checkboxes são preservados para operações em lote. Num grupo, esse
estado elevado corresponde a todas as janelas minimizadas; grupos mistos mantêm
o relevo anterior. A pressão física do mouse continua imediata, mesmo numa tarefa
minimizada. Essa correção não altera o backup da fase visual.
