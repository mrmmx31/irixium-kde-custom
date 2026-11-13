# DomainOS 0.2.9 — menus nativos e barras de rolagem

A 0.2.8 corrigiu a aplicação do esquema, a arte e os controles próprios QML.
A 0.2.9 estende a correção ao QMenu das tarefas e às barras de rolagem das
listas próprias. A paleta vem de PlasmaCore.Theme. As duas luzes autorizadas
continuam amarelas com a proteção de contraste existente; o Pager não mudou.

## Menu real do KDE

O adaptador conserva o QMenu, as QAction, os submenus e os comandos nativos.
A pintura local recebe todos os pincéis Active/Inactive/Disabled da QPalette;
layout, teclado e métricas continuam fornecidos pelo estilo de aplicação.
O relevo usa Light, Midlight, Dark e Shadow. Não se altera QApplication,
o estilo global nem a paleta de outros widgets.

A prova final de produção passou **42/42** verificações, carregando o applet
preparado pelo empacotador público. DomainOS, Breeze Dark e Irixium foram
aplicados pelo CLI instalado no mesmo engine. O menu real abriu inteiro desde
o primeiro quadro, com 14 ações visíveis, submenus opacos preservados, âncora
acima do painel e medidas independentes da escala da arte em 50%/100%.
A face pintada seguiu cada esquema, e o escopo foi liberado ao fechar.

Um defeito real de primeira abertura foi reproduzido antes da correção: o
polish do Kvantum sobrescrevia o texto da paleta ainda herdada. O adaptador
agora conclui esse polish antes de aplicar explicitamente os mesmos pincéis
nativos ao menu local. As provas negativas anteriores foram preservadas.
O setter público mantém a paleta recebida; a máscara explícita só pertence
à paleta aplicada aos widgets do escopo.

A prova C++ dirigida também cobriu seleção, checkbox, exclusividade, RTL,
cabeçalho, submenus acrescentados depois, cliques sem duplicação, limpeza da
fonte nativa e conservação de widgets externos. O módulo utiliza API pública
Qt e import relativo dentro do próprio applet.

## Barras de rolagem

A nova face opaca cobre somente a pintura do componente desktop. Os retângulos
são calculados por QStyle.subControlRect com a mesma QStyleOption do componente
instalado. A comparação com seu groove e a presença de setas utilizáveis
protegem o fallback. A camada não recebe eventos, não acrescenta timer e
não escreve visible, opacity, states ou transitions dos itens nativos.

Essa escolha corrige um problema encontrado no protótipo privado: ocultar um
StyleItem interrompia seu polish e deixava o hit-test antigo após mover a
alça. Alterar só a opacidade também permitia que estados de hover revelassem
novamente a pintura anterior. Essas tentativas foram descartadas e não
aplicadas à sessão pessoal. O overdraw mantém a atualização e a entrada do
componente desktop, inclusive sua repetição e seus limites de rolagem.

O teste dirigido final de Kvantum passou **55/55** verificações: posição após
mudanças e cliques sem uma consulta de teste que atualize o StyleItem, hover,
saída, dois esquemas e conservação dos estados nativos. O teste Breeze passou
**25/25**, conservando o desenho original quando as áreas de seta de três pixels
não atendem ao contrato da face Motif. A ausência do módulo passou outras
**25/25** verificações, preservando a entrada e a pintura originais. As medidas
também receberam provas
privadas separadas em Kvantum, Breeze e DPR 2; isso não representa validação
universal de todos os estilos e escalas.

As listas de aplicativos, gaveta, status, grupo, títulos, miniaturas e legenda
mantêm as políticas anteriores. A rolagem horizontal continua desligada nas
listas que já a desativavam. A paleta opcional ausente usa os papéis nativos
do painel, sem fabricar uma cor de fallback fixa.

O ensaio integrado identificou outra diferença que o componente separado não
revela: substituir a barra inline do ScrollView também remove os bindings de
posição e tamanho que o estilo desktop declara naquele local. O controle
independente confirmou 250 pixels na barra padrão contra 70 na substituição
incompleta. DomainOSViewScrollBar agora conserva esses bindings nas 14 barras
das sete views, inclusive parent, z, padding, mirrored e active cruzado.
A view de miniaturas também passa a vincular contentHeight à grade: o Item
invisível do escopo de cores impedia a inferência de conteúdo único. Isso
corrige o overflow sem mudar os handlers nem as ações das miniaturas.
A revisão independente confirmou esses vínculos e a preservação dos bytes
da camada de pintura já testada. Sua prova dirigida passou **27/27**:
duas orientações, RTL, background com padding assimétrico, dimensões até o
viewport, parent correto, active cruzado e fallback sem o módulo.

A prova integrada final passou **70/70**, sem erros QML, construindo as sete
views de produção e conferindo as 14 barras e seus fallbacks. Grade de
miniaturas e legenda têm overflow real. O quadro de status também limita sua
altura implícita, além da declarada: Popup.Window antes expandia de 420 para
838 pixels seguindo a altura implícita do conteúdo. A correção reaproveita
o reset público de altura já empregado na lista de grupo, com limite de
420 e viewport rolável. As tentativas incompletas anteriores foram preservadas
e o primeiro ZIP preparado não foi instalado; o pacote final é uma nova revisão.

## Pacote e instalação

O módulo inclui fontes C++ completas e licença; o binário e seu manifesto são
gerados somente no estágio do pacote. A compilação/validação desta entrega
atende GNU/Linux AMD64 e Qt 6.8+, com os requisitos efetivos de ABI registrados.
Não instala Qt ou SDK no sistema e não cria um módulo QML global.

As provas públicas dirigidas passaram **18/18** contratos de build/preflight e
**9/9** de pacote: duas compilações idênticas, identidade das fontes, leitura
ELF/metadados sem executar o plugin, compatibilidade de ABI, rejeição de payload
alterado, timeout encerrando os processos próprios do compilador e falha antes
de qualquer instalação. Extração independente, instalação pré-compilada sem
SDK, no-op e restauração dos quatro recursos foram conferidos em perfis privados.
A ponte já habilitada aceita a atualização guardada de dez para onze módulos;
sua prova própria passou **9/9** contratos.

O instalador conserva quatro destinos do usuário. A recarga autorizada da
própria sessão é uma etapa separada, necessária para trocar um plugin já
carregado. A conferência da entrega registra os bytes/modos dos recursos,
IDs e General de todos os painéis/applets, o esquema selecionado e oito
arquivos de configuração protegidos. Provas privadas não substituem o aceite
visual pessoal. Nenhum teste autoriza alterações globais, em outro usuário
ou no backup congelado de Downloads.

As provas de arte, calendário, correio e pins da 0.2.8 continuam com seus
limites. O XPI de contagem do Thunderbird não foi instalado no perfil pessoal.
O arraste de janelas entre miniaturas do Pager continua adiado por decisão.
