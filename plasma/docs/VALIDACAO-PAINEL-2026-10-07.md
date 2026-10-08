# Painel Classic: validação local

O painel usa uma fileira de tarefas em poços quadrados de ícones, com legendas
separadas dentro de um Iconbox rebaixado. O relevo de pressão acompanha
diretamente o estado do mouse. Os cinco widgets têm identificadores próprios;
seus modelos e interações vêm do Plasma Desktop 6.3.6.
Os arquivos ORIGEM.json registram fontes, licenças e alterações.

## Rodada de 2026-10-08: bandeja, relógio e áreas de trabalho

A revisão seguinte trabalha somente nas fontes e prévias isoladas. A instalação
e a conferência nas sessões lsi e p001532 foram adiadas pelo usuário até o final
do goal. Os resultados das instalações anteriores abaixo permanecem históricos.

- Bandeja: aro de instrumento com 4 px, poço teal rebaixado de 2 px e conteúdo
  nativo com margem total de 6 px. O plugin e o containment internos continuam
  os mesmos; expansão e ações dos itens não foram alteradas.
- Relógio: mostrador creme com marcas e ponteiros chapados, encaixado num poço
  quadrado. A moldura usa diretamente `representation.pressed` e o conteúdo
  desloca 1 px durante a pressão. Os 16 IDs/hints do recurso são válidos;
  `Hand.qml`, origem do horário e configurações permanecem preservados.
  Renderizações nativas isoladas de 64 × 56 px conferiram o mostrador de 44 px
  sem timezone e a opção com timezone elidida. Pressão, tamanho estável e
  cancelamento fora também passaram no host isolado.
- Pager: o KDE desenha a moldura acima das miniaturas das janelas. Os centros
  opacos antigos as escondiam; os novos centros transparentes deixam a camada
  nativa visível sobre o fundo sólido do painel. Os 65 IDs, os 20 hints e as
  margens de 4 px foram preservados. Seleção e relevo usam somente o aro.
  No pager KDE nativo, duas janelas Qt reais em KWin/Xvfb privado ficaram
  visíveis nas miniaturas, e cliques alternaram entre duas áreas e voltaram à
  primeira. A comparação com o mesmo aro de centro opaco e com o recurso do
  commit 87e3681 mostrou 0 de 260 pixels da janela visíveis em ambos; o centro
  transparente mostrou 260 de 260 em cada área. Esse teste usa um host isolado,
  não um painel de usuário. Arraste e conferência nas sessões permanecem para
  a validação final.

A galeria desenha retângulos ilustrativos de janelas abaixo da moldura do pager,
seguindo a ordem de camadas do KDE. Não representa um modelo real de desktops.
O relógio da galeria usa os SVGs de produção, com horário demonstrativo. A
prévia conserva 1440 × 64 px e a posição dos grupos; ela não comprova a
geometria nem o comportamento de uma sessão instalada.

## Rodada de 2026-10-08: superfícies de workstation do fim dos anos 80

As referências seguintes fornecidas pelo usuário pediram um desenho mais
severo e denso, com textura de bitmap e molduras mecânicas. O painel cinza,
os encaixes dos instrumentos e os campos teal agora têm stipple regular em
pixels inteiros. `hint-tile-center` repete os centros; as bordas usam o mosaico
nativo do KSvg. O pager conserva seus centros transparentes. A faixa Iconbox
usa a mesma altura de 8 px e mantém os anchors e a fonte anteriores.

- A prévia de 1440 × 64 px e a galeria de controles passaram por 56 verificações
  de entrada. Elas usam recursos de produção, mas conteúdo demonstrativo.
- Applications: sete casos em hosts nativos isolados conservaram exatamente as
  dimensões anteriores, inclusive texto sem ícone, arquivo retangular, painel
  vertical e Planar. A margem interna de 6 px e o limite de 32 px se aplicam ao
  painel. Pressão sustentada, deslocamento imediato de 1 px e cancelamento fora
  passaram. Os modais KIO próprios do fixture foram fechados antes da entrada;
  essa preparação está registrada no resultado.
  Outros dois casos verificaram imagens personalizadas 1:80 e 80:1. O mínimo
  deliberado de 16 px evita um botão de 1 px no caso estreito; há espaço para
  a moldura e o deslocamento. Os nove casos passaram também em manter o ícone
  dentro da margem ao pressionar. Os extremos foram testados somente na fonte
  atual, sem comparação anterior fictícia.
- Quicklaunch: três modelos nativos em configurações com e sem nomes conservaram
  as células de 70 × 64 px e a ordem. Ícones de até 32 px ficam centralizados
  dentro do aro, e ícone/legenda deslocam 1 px ao pressionar. Layout, DND e
  handlers permanecem iguais. A rodada nativa seguinte verificou cancelamento
  fora e popup real; a reordenação por arraste continua para o teste final na
  sessão instalada, conforme detalhado abaixo. A tentativa anterior que travou
  no processamento de eventos permanece registrada como falha.
- A fixture de Quicklaunch usa URLs `file://` dos arquivos desktop descartáveis;
  o TasksModel continua usando `applications:`. Nenhuma URL de perfil foi alterada.
- Relógio de 64 × 56 px e bandeja de 240 × 56 px carregaram sem erros QML com
  os novos SVGs pontilhados. O containment nativo da bandeja anexou corretamente;
  o host privado final ficou vazio, sem itens pessoais ou serviços reais de
  rede. Esta conferência cobre alojamento, carregamento e renderização; a
  galeria preenchida tem ícones demonstrativos. Os testes anteriores
  de interação do relógio continuam vinculados à sua lógica inalterada.
- O Iconbox atual também carregou no host nativo e passou em pressão sustentada
  e cancelamento. Esse host usa um launcher fixado; os testes anteriores de
  ações com janelas reais permanecem vinculados aos handlers inalterados.
- Os 11 testes de fonte do painel e a auditoria dos 22 componentes passaram.

Esta rodada permanece em fontes e hosts privados. A instalação nas sessões,
a renovação do pacote de p001532 e a revisão final da barra ainda estão
pendentes, conforme o adiamento solicitado pelo usuário.

### Quicklaunch: cancelamento, popup e ciclo de arraste nativos

O host privado da rodada de 2026-10-08 carregou os arquivos de produção do
commit `b23e655`, com três arquivos desktop descartáveis `file://` e comandos
`/bin/false`. A entrada veio do XTEST por `xdotool`; um observador assíncrono
registrou os delegados e estados nativos, sem escrever o modelo ou substituir
handlers. Xvfb, os diretórios XDG e o D-Bus eram privados, sem ativação de
serviços. Nenhuma sessão pessoal foi acessada.

- Soltura fora: o MouseArea medido começa em x=5 dentro da primeira célula.
  Pressionar em (306, 232) mostrou o prefixo `pressed`; soltar em (304, 232)
  cancelou e voltou a `normal`, conservando os três atalhos e sua ordem.
  O deslocamento de 2 px ficou abaixo do limiar nativo de arraste de 10 px.
  A captura pressionada mudou 974 pixels na região de 70 × 64 px da tarefa.
- Popup: o botão nativo abriu três delegados reais numa janela de 403 × 120 px;
  Escape fechou essa janela. O teste não lançou os atalhos.
- DND: o DragArea nativo iniciou a operação e encerrou após a soltura. Os
  estados `dragActive`, `dragging` e de pressão ficaram desligados ao final,
  sem perder ou duplicar os três atalhos.
- Reordenação: arrastar a primeira célula até a terceira não mudou a ordem
  nesse host. Uma única comparação com o `IconItem.qml` original instalado do
  KDE reproduziu o mesmo resultado. Ambos registraram
  `cannot grab mouse: no event is currently being delivered`. Essa evidência
  delimita a falha do ensaio, mas não aprova a reordenação: seu gate continua
  falso e o relatório completo continua marcado como falha.

As fontes permaneceram idênticas, os hosts terminaram com código 0 e não
apareceram erros QML de referência, tipo ou carregamento. O resumo local está em
`/tmp/irixclassic-quicklaunch-native-interactions-20261008-v4/RESUMO.json`; a
comparação está em
`/tmp/irixclassic-quicklaunch-native-interactions-20261008-upstream/RESULTADO.json`.
A verificação de reordenação no painel real das sessões lsi e p001532 permanece
para a rodada final. O ciclo de arraste concluído não substitui essa prova.

## Fechamento das fontes: atalhos de perfis novos

O layout novo deixou de concatenar `/usr/share/applications` com uma preferência
que podia estar vazia. O navegador vem de `defaultApplication("browser", true)`;
o Quicklaunch Classic resolve seus identificadores desktop por
`QtCore.StandardPaths`, respeitando `XDG_DATA_HOME` e `XDG_DATA_DIRS`.
Os tokens do modelo/configuração permanecem iguais. Metadados, lançamento,
edição e exportação recebem a URL local resolvida. Arquivos ausentes não lançam
outro aplicativo. A resolução aceita nomes desktop e caminhos relativos;
identificadores achatados de subdiretórios não são reconstruídos.

Doze casos nativos passaram em Qt 6.8.2: diretório local, diretório XDG adicional,
precedência, caminho relativo, espaços/percentuais, URLs antigas preservadas,
arquivo ausente e entradas inválidas. A comparação usa igualdade de QUrl para
URLs resolvidas e igualdade textual exata para URLs antigas. Clique e Return
lançaram dois comandos descartáveis que criaram marcadores em `/tmp`; o payload
MIME e os tokens também foram conferidos. Não houve erros QML nem acesso às
sessões pessoais. O relatório é
`/tmp/irixclassic-quicklaunch-xdg-20261008-final/RESULTADO.json`.
Seu resultado de resolução/lançamento passou; a reordenação física permanece
pendente, separada dessa aprovação. A tentativa anterior foi preservada.

A suíte completa `bash testar-integracao.sh` passou novamente nesta rodada:
722 testes Python em nove grupos, além das verificações dos botões da decoração.
O log é `/tmp/irix-integracao-final-20261008.log`. A atualização e a inspeção
visual das sessões ainda precisam do procedimento final por usuário.

## Refinamento após inspeção visual

O primeiro desenho ainda envolvia cada tarefa em uma placa completa. A revisão
do usuário pediu uma aparência mais próxima do Iconbox SGI e do Motif/CDE.
O Classic também ainda usava o switch circular com gradientes herdado do
Irixium. O arquivo instalado e o cache correspondiam a esse recurso; não foi
demonstrada uma troca de estilo ou um override de ambiente para Breeze.

- O novo alojamento Iconbox tem 56 px de altura, com título de 8 px e tarefas
  de 42 px: poços de 28 px para ícones de 24 px e legendas separadas de 14 px.
  A fonte Nimbus Sans itálica efetiva de lsi foi verificada em um host KDE
  isolado; o tamanho local de 10 px da legenda mantém a família e o estilo.
- O switch é um recurso Classic próprio: alavanca retangular de 20 × 20 px,
  ranhuras, relevo invertido ao pressionar, foco quadrado e trilho de 38 × 10 px.
  Liga/desliga usa os controles Plasma nativos.
- A galeria final passou por 56 verificações de entrada real; foco e alternância
  por Space do switch passaram por outras sete verificações.
- O teste final com três janelas reais no KWin isolado passou: pressão imediata
  e sustentada, cancelamento, minimização da ativa, ativação da inativa e
  restauração da minimizada. A geometria da tarefa permanece igual após cancelar.
  O teste encontrou e corrigiu o alvo automático do DragHandler: `target: null`
  conserva o reconhecimento de arraste sem deslocar o delegado no layout.
- Instalação e recarga somente em lsi passaram pela auditoria dos 22 componentes.
  Painel 1822, limites de 1440 × 64 px, IDs, ordem e os 17 itens da bandeja foram
  preservados. O vínculo interno `lastScreen` da bandeja mudou de -1 para 0,
  correspondente à tela do painel; essa associação foi registrada separadamente.

A confirmação de p001532 abaixo pertence ao primeiro desenho. O refinamento
novo ainda não foi instalado nessa sessão; o pacote de atualização é separado
e exige execução pelo próprio usuário.

## Resultados

- A suíte `bash testar-integracao.sh` passou, incluindo os testes do painel.
- Os 25 testes da migração verificaram configuração recursiva, ordem, atalhos,
  transferência da bandeja, reversão, falhas e recusa de alterações concorrentes.
- Aplicação e restauração reais passaram em um Plasma isolado por Xvfb e D-Bus.
  O teste preservou os 14 componentes internos da bandeja daquele perfil.
- A galeria Qt/KSvg passou por 56 verificações de pressão, cancelamento, soltura,
  tarefa ativa, switches, sliders nas duas orientações, listas, botões e
  resolução de ícones do menu.
- Os cinco widgets carregaram em hosts Plasma nativos isolados. O lançador
  mostrou o prefixo pressionado enquanto o mouse permaneceu abaixado, mudou
  935 pixels na região da tarefa e cancelou o efeito ao soltar fora.
- Três janelas Qt descartáveis foram verificadas em um KWin X11 isolado. Os
  estados ativo, inativo e minimizado vieram do TasksModel nativo, com PID e
  identificador X11 conferidos. A pressão teve efeito imediato e permaneceu
  durante a captura de 120 ms, sem executar a ação. Soltar fora cancelou;
  soltar dentro minimizou a janela ativa, ativou a inativa e restaurou a
  minimizada. Os estados também foram conferidos diretamente no X11.
  As regiões pressionadas mudaram 3067, 3697 e 3743 pixels, respectivamente.
- Na sessão Wayland de lsi, a migração preservou o painel 1822, altura de 64 px,
  largura configurada de 1440 px, posição, demais widgets e os 17 componentes
  internos da bandeja. Foram capturadas imagens da barra antes e depois.
- A execução pelo próprio usuário p001532 passou na sessão Wayland: os 22
  componentes instalados conferem com o pacote e o perfil Classic não tem
  divergências de seleção. A migração preservou o painel 342, os limites
  configurados de 1440 × 64 px, posição, ordem e os 16 componentes internos
  da bandeja. Foram substituídos somente os cinco widgets previstos, com
  recibos de restauração no perfil desse usuário. O recorte da captura dessa
  sessão também confirmou a fileira de ícones com legendas, o menu com três
  atalhos à esquerda e as molduras da bandeja e do relógio. O pager preservado
  não aparece nessa captura; seu relevo foi conferido na sessão lsi e na galeria.
- O usuário confirmou na sessão p001532 que o relevo aparece imediatamente ao
  manter uma tarefa pressionada e que os interruptores nos pop-ups de Wi-Fi e
  Bluetooth têm o visual Classic correto.

Os testes isolados não acionam serviços reais de Wi-Fi/Bluetooth nem abrem
aplicativos do usuário. A galeria usa controles reais e tarefas demonstrativas;
o teste dos widgets usa o delegado e o modelo nativos. O teste opcional de
janelas abre somente três janelas Qt descartáveis, em Xvfb e D-Bus
privados, sem ativação de serviços nem um desktop Plasma completo. As capturas
da sessão lsi verificam a composição final do painel.

A instalação e a migração em p001532 foram verificadas por seus próprios
relatórios `RESULTADO.json` e `AUDITORIA.json`. A confirmação manual do relevo de
pressão e dos interruptores de Wi-Fi/Bluetooth foi fornecida pelo usuário após
a captura. Esses campos continuam pendentes no JSON automático, pois o script
não certifica uma inspeção manual; a confirmação está registrada neste documento.
A captura foi produzida pelo Spectacle na própria sessão Wayland e foi
conferido somente o recorte do painel. A imagem estática confirma a composição;
não comprova o comportamento enquanto o mouse permanece pressionado. A opção
`--capturar` do pacote portátil acrescenta a imagem ao relatório existente.

## Reprodução

```sh
bash testar-integracao.sh
python3 plasma/tools/prever-painel.py --testar --offscreen --capturas /tmp/classic-galeria
python3 plasma/tools/testar-widgets.py --saida /tmp/classic-widgets
python3 plasma/tools/testar-widgets.py --widget iconbox --window-tasks --saida /tmp/classic-janelas
```

A última ferramenta exige Xvfb, D-Bus, compilador C++, Pillow e os arquivos de
desenvolvimento de Qt 6 Widgets/Test. Usa somente perfis temporários. As saídas
devem ser novas para conservar evidências de execuções anteriores.
O modo `--window-tasks` exige também `kwin_x11`, `xdotool` e `xprop`.

Para atualizar um painel existente, primeiro instale a suíte e execute
`python3 tools/classic_panel.py --verificar`, seguido do comando sem a opção.
`--restaurar` recupera os widgets anteriores pelo recibo do próprio usuário.
O procedimento exige um único painel Classic e recusa configurações alteradas
depois da migração; o arquivo original permanece guardado no backup.

## Referência visual

O vocabulário se inspira no Indigo Magic da SGI e no Motif: placas encaixadas,
contornos e relevos de workstation UNIX. O Iconbox e o pager adaptam a ideia
das ferramentas separadas da referência, mantendo o espaço compacto do KDE.

- [SGI: Indigo Magic User Interface Guidelines](https://techpubs.jurassic.nl/library/manuals/2000/007-2167-002/sgi_html/ch03.html)
- [OSF/Motif Style Guide, 1993](https://www.bitsavers.org/pdf/openSoftwareFoundation/motif/OSF_Motif_Style_Guide_Revision_1.2_1993.pdf)
