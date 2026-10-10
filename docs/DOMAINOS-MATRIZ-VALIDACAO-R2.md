# Revisão independente R2 — F01–F35

## Revisão visual reaberta em 2026-10-10

O estado atual segue a [regra comum](DOMAINOS-REGRAS-ROLAGEM.md), levantada antes
da tradução: FTP leu 10 recursos e o xrdb atual não declara as medidas do
XmScrollBar. As medidas 15/2/11/1/4 vêm do Trash Can SR10.4; pressionar/soltar
a seta inferior foi observado na VM. GTK3 já lê o contrato, com 620/620 ensaios
nativos, 18/18 de desenho/integridade e 4/4 focados do refactor. Sua moldura
principal de TreeView preenchida continua pendente. As outras famílias não
recebem conclusão por analogia; o [relatório GTK3](DOMAINOS-COMPARACAO-ROLAGEM-GTK3.md)
delimita o resultado.

A prévia completa R13 abriu com 18/18 verificações iniciais. O clique real do
Terminal passou 12/12, incluindo token QML, helper com StartupNotify, modelo
nativo TaskManager, luz/cursor durante a inicialização e limpeza sem cauda.
O semiperíodo observado teve mediana de 516 ms para o temporizador de 500 ms.
O ensaio usa X11 e um cliente temporário; não comprova prontidão de aplicações
pessoais, Wayland ou inicialização que o modelo KDE omite por coincidir com
janela já aberta. A configuração Terminal foi restaurada após o ensaio.

As configurações pessoais ficaram fora das alterações e a VM manteve seu
perfil de desempenho. O backup aprovado não foi atualizado ou eliminado.
Os registros anteriores abaixo conservam sua revisão e suas limitações;
este adendo não transforma o projeto inteiro em concluído.

Os relatos da seta GTK3 e da seta no System Settings reabrem a revisão visual
dos controles de rolagem. A [fila de trabalho](DOMAINOS-FILA-REVISAO-VISUAL.md)
registra as famílias separadamente e usa o Trash Can real do SR10.4 como
referência. As provas históricas abaixo conservam seu escopo; elas não encerram
a comparação de setas, botões, trilhos e encaixes nas outras famílias.

## Reabertura do aceite: troca de tema global e GTK

O relato mais recente em lsi/p001532 reabre o aceite pessoal de aparência.
Na prévia completa, a omissão de `kdedefaults` foi reproduzida e corrigida no
launcher. CLI/precedência nativos passaram 27/27; a ponte opcional de estilos
passou 16/16, respeitando seleção explícita e fallback. As cinco trocas reais
Breeze/Classic/Irixium preservaram a barra e mudaram os pixels da paleta;
a consulta ao modelo nativo complementa o gate de arquivo ainda não gravado
do bruto 10/11. Decorações e controles Qt foram conferidos nas capturas.
Essas provas usam uma sessão descartável e não encerram o aceite pessoal.

GTK continua pendente para **cores**, apesar da seleção de desenho disponível.
GTK3/4 receberam papéis de cores azuis, amarelos e escuros e conservaram
preenchimentos fixos no CSS atual: 59/59 de reprodução, não de correção.
O aplicador da suíte já seleciona GTK/Kvantum sem reinstalação, mas a aparência
nativa do tema global não executa esse helper automaticamente. Não se criou
hook, serviço ou polling para contornar isso. Os seletores agora confirmam os
nomes em GTK2/3/4 antes do sucesso e guardam os CSS gerados para recuperação:
27/27 +13/13 testes transacionais. Recarga ao vivo e escritas KDE assíncronas
ficam fora dessa prova de arquivos.

Veja a [validação atual](VALIDACAO-DOMAINOS-0.2.11-2026-10-09.md)
e [cobertura GTK](../gtk/README.md). A adaptação de cores GTK e a validação nas
duas sessões permanecem trabalho aberto; não declarar a integração concluída
por testes exclusivos da barra. As provas anteriores abaixo permanecem como
registros do escopo e revisão em que foram executadas.

## Atualização 0.2.11 preparada para teste

A revisão da fonte demonstrou outra falha recuperável: exceções de layout,
gravação ou sincronização de visibilidade podiam deixar `refreshing` ou
`synchronizingVisibility` ativos, impedindo atualizações posteriores. O teste
dirigido executou o QML de produção com provedores próprios: antes da correção,
14/26 critérios passaram; os 12 restantes reproduziram o guard preso e sua
consequência. Com quatro blocos `try/finally`, passaram 26/26. A apresentação e
a luz foram conferidas novamente na fonte corrigida: 50/50.

Os blocos cobrem `refresh`, `applyVisibility`, inicialização em `attach` e o sinal
nativo `valueChanged`. A ordem de sucesso permanece igual; as exceções continuam
observáveis e a próxima chamada válida pode recuperar a atualização. Não há
timer, retry automático ou alteração de desenho. O teste também confirma que
falha em `writeConfig` pode deixar valores em memória: liberar o guard não
representa rollback transacional nem gravação bem-sucedida.

Provas privadas:

- `/tmp/irix-domainos-tray-refresh-failure-before-011-r3/RESULTADO.json`.
- `/tmp/irix-domainos-tray-refresh-failure-after-011-r1/RESULTADO.json`.
- `/tmp/irix-domainos-tray-activity-guard-fix-20261009-r2/RESULTADO.json`.

O [teste público de recuperação](../plasma/tests/test_domainos_tray_refresh_failure.py)
roda offscreen com HOME/XDG próprios. A primeira tentativa do ensaio de
apresentação foi recusada pela restrição de socket do sandbox; seu log foi
preservado e a execução seguinte usou apenas Xvfb/DBus privados. A correção está
na fonte do repositório e no ZIP0.2.11 verificado, ainda sem instalação pessoal.
O ZIP0.2.10 e as prévias já abertas continuam representando a entrega anterior.

O primeiro ZIP0.2.11 preparado, anterior à revisão de portabilidade abaixo,
contém 267 entradas e tem SHA256
`571fd0971f1a502d72cf210f23a736952a459846a6644ff29e3afdbec45c12a1`.
Os nove testes de pacote, instalação, repetição e restauração passaram na raiz
privada `/tmp/irix-domainos-release-011-stage-20261009`; o módulo nativo e os
cinco arquivos de entrada de sua compilação são exatos aos da 0.2.10. A revisão
independente conferiu os checksums e a mudança funcional restrita à bandeja.

### Prévia completa acessível aos dois usuários

O atalho anterior da sessão completa dependia do repositório em `/home/lsi`,
cujo diretório tem modo 0700. Isso impedia p001532 de acessar as fontes. Os 31
componentes públicos foram preparados em
`/tmp/irix-tema-completo-recursos-0.2.11`, com leitura e travessia públicas.
Os quatro recursos DomainOS vieram do ZIP verificado; os demais conservam os
bytes atuais do repositório. Os dois componentes de ícones usam snapshots
públicos em `/tmp`, verificados arquivo a arquivo contra a fonte atual.

Na primeira preparação, os atalhos `/tmp/irix-tema-completo-011` e
`/tmp/irix-tema-completo` passaram a usar essa raiz pública. Foram conferidos
com `sh -n` e `--help`; o atalho anterior foi
preservado em arquivo privado. Essa preparação não abriu, recarregou ou fechou
nenhuma prévia, nem comprova execução gráfica em p001532. Uma execução futura
continua usando HOME/XDG, barramentos e namespaces descartáveis próprios.

Relatórios privados:

- `/tmp/irix-tema-completo-recursos-011-verificacao-20261009.json`: oito critérios,
  31 componentes e 29.447 arquivos lógicos com bytes e acessibilidade conferidos.
- `/tmp/irix-tema-completo-atalhos-011-20261009.json`: seis critérios de preparação,
  sintaxe, ajuda e preservação do atalho anterior.

### Portabilidade do instalador publicado

A revisão seguinte removeu os nomes pessoais restantes dos guardas da galeria
completa e da busca de referência da decoração. A comparação recebe a imagem
por `--referencia`; o namespace exige somente seu HOME fictício. São sete
casos/49 verificações positivas, sem GUI ou serviços, em
`/tmp/irix-tema-completo-guardas-011-20261009-r1/RESULTADO-r1.json`.

O hook Classic opcional agora instala runtime autocontido no XDG do próprio
usuário. `tests/test_hook_migration.py` passou 13/13 sem skips, incluindo apagar
o checkout extraído antes de executar duas vezes o runtime com ferramentas
KDE reais. Serviços personalizados, seleção e bytes de kwinrc foram preservados;
rollback e restauração dos arquivos foram testados. Chamadas ao systemd foram
interceptadas, sem serviço pessoal. Recibo:
`/tmp/irix-classic-hook-portable-20261009-r1/RESULTADO.json`.

O helper compartilhado é incluído no SUPPORT do novo pacote DomainOS, mas seu
instalador independente não aciona o hook nem instala assets Classic. A suíte
completa continua exigindo o checkout completo, conforme sua documentação.

O CLI real da suíte, chamado de outro diretório com `--verificar --sem-cache`
e raízes privadas com espaços, terminou rc1 na ausência de `Qt6Qml.pc` do SDK.
Fontes, HOME/XDG e raízes cursor/GTK permaneceram iguais e nenhum binário foi
gerado. É uma dependência real da compilação pelo checkout, agora documentada;
não é aceite da instalação completa nem requisito do ZIP pré-compilado.
Recibo: `/tmp/irix-suite-dry-cli-portable-20261009-r1/RESULTADO.json`.

### Pacote portátil R2 preparado

O ZIP seguinte está em
`/tmp/irixclassic-domainos-0.2.11-final-r2-20261009/irixclassic-domainos-0.2.11.zip`:
268 arquivos, 902.748 bytes, SHA256
`fb41f8a6fb28cd8b9635b78c3484607af9c24b18c91bd85fdbf623ffbe3b4675`.
Os nove testes de extração/instalação/repetição/restauração passaram em perfil
privado, e a revisão somente leitura passou 18/18. Conferiu helper/imports,
catálogo de quatro destinos, fontes atuais, manifesto/ELF/ABI e ausência de
caminhos pessoais nos arquivos de execução. Módulo nativo e cinco entradas de
compilação continuam idênticos à 0.2.10. Recibos:

- `/tmp/irixclassic-domainos-0.2.11-final-r2-20261009/RESULTADO.json`.
- `/tmp/irix-domainos-final-011-r2-readonly-audit-20261009/RESULTADO.json`.

A cópia pública seguinte, `/tmp/irix-tema-completo-recursos-0.2.11-r2`, passou
oito critérios: 31 componentes/29.447 arquivos lógicos, bytes, acessibilidade,
ícones e galerias conferidos. Os atalhos futuros agora apontam para R2, com
seis critérios positivos de sintaxe/ajuda/backup. Artefatos anteriores não
foram sobrescritos; não houve instalação pessoal nem abertura/recarga de GUI.
Recibos `irix-tema-completo-recursos-011-r2-verificacao-20261009.json` e
`irix-tema-completo-atalhos-011-r2-20261009.json` ficam em `/tmp`.

As três prévias pessoais existentes foram apenas consultadas: supervisores
32559/:61, 49000/:62 e 54891/:63 presentes, do próprio UID e sem ENCERRADO.json.
Continuam representando 0.2.10, sem carregar automaticamente os arquivos R2.
No estágio R2, F16 permanecia parcial: no ensaio privado, wheel do Volume no
slot funcionava e no overflow falhava. O ponteiro coincide com o popup, mas a observação
QWheelEvent registra a janela host; o observador XI2 não registra o ID XCB de
destino. Clipping/opacidade efetivos não foram medidos. Nenhuma causa definitiva
de dispatch nem correção de volume havia sido promovida nessa preparação.

### Prova posterior da roda e da ponte portátil

A [validação 0.2.11](VALIDACAO-DOMAINOS-0.2.11-2026-10-09.md) registra a causa
da rota de roda no Qt 6.8.2/XCB e a correção local às duas gavetas. O módulo
nativo final passou **121/121** no stage: Volume real por XTest em slot,
gaveta, reabertura e reparentamento; um despacho por gesto; SNI somente no
alvo; menus, representação completa e mute/unmute nativos. O estacionamento
invisível deixou de receber entrada. A origem visual e habilitação foram
restauradas, com nove itens e o mesmo compacto. Zero erros QML, configurações
e fontes intactas. Recibo: `/tmp/irix-domainos-popup-wheel-final-011-20261009.json`.

F16 tem agora prova positiva para roda discreta `NoScrollPhase` em
Qt 6.8.2/XCB, com áudio próprio/null sink. Outras fases mantêm a rota original;
seus guardas foram conferidos por QPA, sem alegar teste físico de touchpad.
Wayland, outras versões e perfis pessoais continuam fora desse alcance.
O módulo final `60734648…` tem sete fontes de compilação, portanto difere do
R2 congelado. A recuperação sem módulo carregado foi conferida novamente:
26/26 em `/tmp/irix-domainos-tray-refresh-wheel-fallback-20261009-r2/RESULTADO.json`.

A ponte opcional de estilos passou **10/10**, incluindo XDG com espaços,
`%`, `$`, aspas e barra invertida e execução após apagar a origem. O parser
real do systemd 257 aceitou a unidade sem avisos; nenhum serviço foi iniciado.
A busca em 2.908 arquivos textuais publicáveis de 31 componentes não encontrou
caminhos dos perfis de desenvolvimento. As receitas e os limites constam da
mesma validação. Nenhum ZIP anterior ou Xephyr existente foi substituído.

### Pacote portátil R3 preparado

O ZIP final dessa preparação está em
`/tmp/irixclassic-domainos-0.2.11-final-r3-20261009/irixclassic-domainos-0.2.11.zip`:
272 arquivos, 918.179 bytes, SHA256
`1baa17b2014e008752a3a3315e723e7aa2800060d374a6c384930383525f90ce`.
Contém o mesmo módulo `60734648…` da prova 121/121, sem recompilação posterior.
O R2 anterior permanece congelado com seu hash original.

A revisão independente passou **25/25** verificações e executou os **nove
testes reais de pacote, 9/9**. A extração usa caminho com espaços, `%`, `$`,
aspas e barra invertida, outro diretório de trabalho e HOME/XDG privados.
Instalar, repetir e restaurar conservou bytes, modos, quatro configurações
protegidas e recursos alheios; repetição não criou novo backup. Os quatro
destinos, 47 arquivos de suporte, sete entradas nativas, ELF/ABI e fontes
atuais foram conferidos. Quatro CLIs `--help` e a cadeia de imports extraída
não escreveram no HOME/XDG. A ponte usa `$$` no comando e `$` no ambiente.
A busca geral de caminhos pessoais em 252 textos e strings do módulo não
encontrou dependências pessoais. A leitura de ABI não carrega código nem
substitui a prova funcional separada da roda.

Recibo: `/tmp/irix-domainos-final-011-r3-independent-audit-20261009/RESULTADO.json`,
SHA256 `0e02b25c9e6ab2e4142eb5a2f963b3f8ed71f0ff88cd9dc0137dabce11f7cec3`.
`PACKAGE-TEST.log` e `EXTRACTION-INSTALL-RESTORE.json` preservam a execução real.

A próxima prévia completa usa a nova raiz pública
`/tmp/irix-tema-completo-recursos-0.2.11-r3`: 31 componentes e 29.451 arquivos
lógicos. Os quatro recursos DomainOS são exatos ao ZIP; os outros 27 são
exatos ao checkout atual. Dois snapshots públicos de ícones continuam como
dependências desta exportação de teste, após comparação de conjunto e bytes.
Não são caminhos pessoais nem entram como dependência do instalador publicado.
A exportação passou 13 verificações de integridade, escopo e acesso público.

Os atalhos futuros `/tmp/irix-tema-completo` e `/tmp/irix-tema-completo-011`
agora apontam para R3. Sintaxe e `--help` de ambos passaram, sem criar dados
no perfil privado; os bytes e modos dos atalhos anteriores foram salvos em
um diretório novo. Isso não abriu, recarregou ou fechou nenhuma prévia, não
instalou recursos pessoais e não é aceite gráfico em p001532. Recibos:

- `/tmp/irix-tema-completo-recursos-011-r3-verificacao-20261009.json`.
- `/tmp/irix-tema-completo-atalhos-011-r3-20261009/RESULTADO.json`.

O CLI real da suíte completa passou em outro diretório com
`--verificar --sem-cache`, HOME/XDG e raízes de compatibilidade privadas com
espaços, usando o SDK Qt QML real já extraído via variável explícita.
Foram **12/12** contratos e **36 destinos**, todos privados. As auditorias
reais de ícones, cursores e manifestos de decoração passaram. O plano informa
`compiled:false`: não houve compilação, instalação ou serviço. HOME/XDG
continuaram ausentes; as oito configurações protegidas, sete fontes nativas,
ausência de arquivos gerados e hash do ZIP foram conferidos antes/depois.
A falha anterior sem `Qt6Qml.pc` permanece como prova da dependência real.

Recibo: `/tmp/irix-suite-dry-cli-portable-sdk-20261009-r1/RESULTADO.json`,
SHA256 `f50ce885e20358b4d7eef857a374f64919b3a7aafdbcc43d3ae9727dd461ef5a`.
Essa verificação não substitui a instalação/restauração executada do pacote
independente nem a avaliação de uma sessão gráfica completa.

### Provedor de dispositivos nativo vazio

O `org.kde.plasma.devicenotifier` instalado passou 22/22 critérios com a bandeja
corrigida. Slot, ▲/ocultos e ▶/incluir ocultos abriram a mesma representação
nativa e o mesmo `DeviceFilterControl`, com zero dispositivos e zero montados.
Os gestos foram enviados pelo QPA do Qt em Xvfb próprio; o system bus permaneceu
desconectado. Não houve montagem/ejeção, UDisks ou dispositivos/SNI fabricados.
Isso complementa F18/F21/F22 sem representar teste de hardware ou de excesso
de itens visíveis. Os ensaios anteriores falhos foram preservados.

Prova: `/tmp/irix-domainos-devicenotifier-native-empty-011-r3/RESULTADO.json`,
SHA256 `4ca827413b3c1aa9c042d09f6c8bf6dba811ff2450489c69fefffdcb602bf20b`.
`ALCANCE.json` registra os limites, avisos upstream e encerramento dos processos
desse fixture. Os Xephyr pessoais continuam abertos a pedido do mantenedor.

### Pesquisa solicitada do Pager IRIX — RESP-C03

A pesquisa posterior encontrou confirmação documental do mapa geométrico no
**IRIX 6.5.11**, sem usar essa versão como fonte da decoração DomainOS SR10.4.
O [Desktop User's Guide da SGI, 007-1342-170](https://irix7.com/techpubs/007-1342-170.pdf)
identifica a versão na página preliminar iii e a revisão de janeiro de 2001.
Na página impressa 96 (página 128 do PDF), descreve os mapas como retângulos
que indicam posição, tamanho relativo e forma das janelas. Passar o ponteiro
mostra o nome; o guia oferece alternativas de nome e ocultação. As páginas
89–90 documentam a troca de área por duplo clique e o movimento por arraste
entre mapas. Na página 95, o clique em uma janela do mapa seleciona o alvo
para uma operação pelo menu. Isso não prova ativação da janela por clique
simples, comportamento próprio pedido para esta adaptação.

O [IRIX Interactive Desktop User Interface Guidelines da SGI, 007-2167-006](https://irix7.com/techpubs/007-2167-006.pdf),
página impressa 66 (página 94 do PDF), figura 3-15, descreve representações
miniaturizadas das janelas principais e rótulos ao passar o ponteiro;
janelas de suporte e diálogos não participam desses mapas nessa edição.
É documentação original da SGI preservada em um arquivo público, distinta
de uma demonstração executada aqui. As duas edições descrevem padrões de
rótulo diferentes; não se generaliza o default a todas as versões do IRIX.

RESP-C03 tem agora evidência histórica para **representação geométrica**,
em vez de uma inferência pela palavra “snapshot”. Não é prova de equivalência
integral de gestos, cores, tratamento de diálogos ou todas as versões.
O Pager KDE mantém as decisões atuais do usuário; o arraste continua adiado
para a próxima versão. Esta pesquisa não altera desenho, código ou backup.

## Versão entregue: atualização 0.2.10

A [validação 0.2.10](VALIDACAO-DOMAINOS-0.2.10-2026-10-09.md) acrescenta as
provas abaixo. O arquivo distribuído e seu binário nativo permanecem congelados;
esta atualização da matriz não recompila nem reinstala o painel. Os relatórios
privados citados ficam em `/tmp`; não fazem parte da distribuição.

| Requisito | Evidência atual | Limite que permanece |
| --- | --- | --- |
| F13 — gestão do Pager | 93/93 em KWin privado, com 18 gestos físicos: cancelar criação/renomeação/remoção não muda áreas; aceitar executa exatamente uma operação; a última área conserva o UUID. Quantidade e identidades originais restauradas. | Estilo Classic indisponível nesse ensaio específico; a prova é funcional. Arraste entre miniaturas continua adiado por decisão. |
| F27 — bloqueio | 23/23 com ksmserver e kscreenlocker_greet instalados, sem modo de teste: DBus confirma Active, outro cliente X recebe AlreadyGrabbed para teclado e ponteiro e a aplicação própria continua viva. O controlador de produção registra confirmação e encerra o pedido. | Sessão descartável com barramento, identidade e autenticação isolados. Comprova bloqueio real nela; não testa desbloqueio/PAM dos perfis pessoais. |
| F29 — bandeja e lente | 50/50 com componentes de produção: abrir e fechar pelo mesmo botão, quadro observado, cauda opcional somente após retorno, limpeza de false/exceção e funcionamento sem rastreador. Nenhum timer novo no despacho. | Os provedores substitutos estão declarados. Retorno de uma chamada SNI não comprova conclusão de uma operação opaca do aplicativo. A duração pessoal de 300 ms continua preservada. |
| F33 — reset geral e por categoria | Os 45 defaults nativos são exatos após Aplicar, reabertura e reinício; Cancelar/Descartar, reset de Correio, demais categorias e segunda instância foram conferidos. | Resultado bruto preservado: 26/27, com falha somente no gate de zero diagnóstico QML por seis TypeError do PromptDialog Kirigami. Análise separada confirma os contratos funcionais, sem converter o bruto em aprovação integral. |
| F30 / VF19 — entrega | ZIP0.2.10 verificado, quatro recursos exatos no lsi, somente o applet precisou mudar. IDs/General, oito configurações, ponte, migração e escolha de cores preservados; uma recarga. Pacote portátil R11 passou 20/20; prévia isolada do painel passou 11/11 e Pager 9/9. | A entrega atual não instala nem testa a sessão p001532. Pacote portátil e instalação não equivalem a aceite pessoal. Restauração usa a transação documentada; não substitui configurações de outros usuários. |
| F31 / VF20 — sessão completa e cores | Plasma completo no Xephyr: 14/14 na abertura, aplicações Qt6 com Kvantum e GTK3/4 reais, decorações/ícones/cursores/monitor. Seis aplicações nativas de esquema passaram 24/24 na paleta do painel, incluindo amarelo para contraste. Chapa aprovada conserva 971 × 109; somente a janela privada compensa as margens nativas para 1003 px. | O Kvantum existente adapta parcialmente as superfícies; GTK Classic conserva cores de seu CSS ao trocar somente o esquema KDE. Não alegar adaptação completa desses estilos. Rede, áudio, dispositivos e autenticação pessoais não estão acessíveis nessa sessão. As prévias válidas permanecem abertas a pedido do mantenedor. |

Artefatos que fundamentam essas linhas:

- `/tmp/irix-domainos-pager-crud-dialogs-010-r5/RESULTADO.json`.
- `/tmp/irix-domainos-real-lock-009-r8/RESULTADO.json` e `LOCKED.png`.
- `/tmp/irix-domainos-tray-activity-010-r4/RESULTADO.json`.
- `/tmp/irix-domainos-reset-geral-45-009-20261009-r3/RESULTADO.json` e
  `RESULTADO-ANALISADO.json`.
- `/tmp/irix-domainos-entrega-010-lsi-20261009.json` (`verified`).
- `/tmp/irix-domainos-release-010-stage-20261009/PACKAGE-TEST.log`:
  nove testes do pacote, instalação e restauração em raiz privada.
- `/tmp/irix-domainos-teste-pacote-r11-010-verificacao/RESULTADO.json` e
  `/tmp/irix-domainos-teste-final-010-lsi-20261009/RESULTADO.json`.
- `/tmp/irix-tema-completo-010-lsi-r5-20261009/RESULTADO.json`,
  `CORES/RESULTADO.json` e `RESUMO.json`.

O ZIP0.2.10 tem SHA256
`f771d21aac3360412509fd461ac24944e3189535a770d5a4a2d1285123c5204e`.
O ensaio de cores aplicou DomainOS, Breeze Dark, Breeze Light, Irixium, um amarelo
privado de contraste e DomainOS novamente. Ele não alterou as oito configurações
protegidas do perfil real. A sessão continua disponível para avaliação manual;
seu encerramento ainda não ocorreu e não é apresentado como teste concluído de
limpeza. As ferramentas públicas de prévia completa foram acrescentadas ao
repositório; o observador, os relatórios e o esquema amarelo são privados.

As provas anteriores continuam com seu alcance: nenhum desses resultados declara
concluído todo o goal, todas as integrações pessoais ou todos os estilos GTK/Qt.
As pendências técnicas e o aceite do mantenedor precisam ser avaliados separadamente.

## Registro anterior: atualização 0.2.9

A correção corrente está descrita na [validação 0.2.9](VALIDACAO-DOMAINOS-0.2.9-2026-10-09.md).
As provas de arte e aplicação nativa da [0.2.8](VALIDACAO-DOMAINOS-0.2.8-2026-10-09.md)
conservam seu alcance próprio.
As linhas históricas abaixo conservam seus resultados e limites; não representam
uma execução integral da versão corrente nem substituem a avaliação pessoal final.

| Requisito | Evidência posterior à matriz | Limite que permanece |
| --- | --- | --- |
| F03 / VF02 — agenda | Fonte nativa Manaus–AM–Brasil de 2026: 138 verificações; cada um dos 15 feriados tem exatamente um evento e uma linha visível. Instalador regional opcional conferido no lsi sem diferenças a aplicar. | Somente 2026; pontos facultativos excluídos. Não houve leitura de agenda pessoal. |
| F05 / VF04 — correio | Extensão/host testados com Thunderbird 140 em perfil descartável e contagem real de pastas. Cadeia até o botão do painel tem prova própria; host e XPI preparados no lsi. | XPI ainda não instalado pelo gerenciador de extensões do perfil pessoal; fonte ausente não representa zero mensagens. |
| F08 / F34 — grupos e menus | Seleção acumulada, pins temporários por identidade/PID e destinos do grupo remanescente têm provas dirigidas. Menu nativo em X11 foi conferido em 50%/100%, inteiro na primeira abertura. | Ensaios privados; cliques pessoais de lsi/p001532 continuam separados. |
| F29 / VF17 — lente | Amarelo com proteção de contraste; conclusão imediata preserva a apresentação até um quadro, sem atrasar o comando. 24 verificações OpenGL. | Não equivale a benchmark nem a teste físico do ponteiro na sessão pessoal. |
| F33 / VF18 — novas preferências | ConfigView/AppletConfiguration do Plasma: Aplicar, Cancelar/Descartar, reabertura e reinício das opções de feriados/contagem; reset da categoria Correio preserva a fonte do calendário e a segunda instância. | Relatório analisado 74/75: contratos funcionais passaram; o gate de zero diagnóstico global falha pelos oito TypeError do PromptDialog Kirigami, preservados. Não houve teste pessoal. |
| F31 — cores | Base 0.2.8: nome instalado sem ponto intermediário, PlasmaCore.Theme, cinco aplicações nativas no mesmo engine (201/201), pintura25/25 e checkbox30/30. Extensão0.2.9: QMenu real42/42 com DomainOS, Breeze Dark e Irixium; paleta local Active/Inactive/Disabled sem alterar estilo ou QApplication. ScrollBar Kvantum55/55, fallbackBreeze25/25 e sem módulo25/25; wrapper27/27, sete views70/70 e paleta opcional14/14. Referência, geometria e luzes preservadas. | Ensaios privados e leitura da paleta instalada não substituem aceite visual pessoal completo, todos os estilos/escalas ou uma captura da sessão Wayland. As métricas e a entrada continuam pertencendo ao estilo nativo. |
| F30 / VF19 — entrega | ZIP0.2.9 R2 verificado e entregue somente no lsi. Quatro destinos têm bytes do ZIP; recursos sem mudança conservaram seus modos anteriores. Ponte previamente habilitada atualizada10→11 e Plasma recarregado uma vez. IDs, General de todos os painéis/widgets, oito configurações e escolha DomainOS preservados. Paleta instalada conferida e três sondas consecutivas responderam. Launcher009 preparado para p001532. | Não houve sessão nem instalação em p001532 nesta entrega. O launcher plasmawindowed usa HOME/XDG privados e tarefas/KWin da sessão em que é executado; não equivale ao isolamento integral Xephyr. Arraste entre miniaturas do Pager permanece adiado por decisão. |

Entrega local final:
`/tmp/irix-domainos-entrega-029-lsi-20261009-r3.json` (`verified`).
O ZIP final R2 tem SHA256
`49975b9c8ad15a44475e15174e3a3b475ee218769f47b21e41165030b9c4937f`.
O binário conferido é o mesmo do ensaio do QMenu real, não uma recompilação posterior.
Os dois relatórios anteriores continuam intactos: o primeiro exigia modos do ZIP
também nos destinos sem alteração; o segundo concluiu ponte, recarga e guardas,
mas usou o formato de token do Bundle ao registrar o recibo da migração.
A conferência final, somente leitura, utilizou a API própria dessa migração,
sem repetir instalação/recarga ou normalizar permissões.
O relatório de paleta usa um engine invisível separado; o monitor comprova três
respostas neste intervalo, sem prometer ausência universal de travamentos.

Prova dirigida das preferências:
`/tmp/irix-domainos-native-calendar-count-configview-007-r1/RESULTADO-ANALISADO.json`.
O resultado bruto e a classificação inicial incorreta do mapa de configuração
permanecem preservados; o mapa contém 45 valores e seus 45 defaults, não apenas
45 chaves.

Esta matriz conserva os escopos históricos da revisão R2. As respostas posteriores
do mantenedor, as correções instaladas e os gates atuais estão na
[auditoria de 9 de outubro](DOMAINOS-AUDITORIA-2026-10-09.md). Em particular, a
central agora tem nove categorias e reset solicitado pelo mantenedor, o painel
já foi ativado no lsi e a ordenação de favoritos de um menu KDE independente
recebeu prova própria de 53 critérios. Não usar as linhas
históricas abaixo como declaração de conclusão da fonte atual.

Escopo: código final dos componentes e contrato autorizado em
[Decisões consolidadas](DOMAINOS-DECISOES-CONSOLIDADAS.md), conforme os
[requisitos F01–F35](DOMAINOS-REQUISITOS.md). O
[relatório principal](VALIDACAO-DOMAINOS-INTEGRACAO-2026-10-08.md) descreve os
ensaios e seus artefatos. Os ensaios funcionais utilizam perfis, barramentos,
compositor e janelas próprios sob `/tmp`. Aprovação de um requisito não significa
prova em todas as sessões/aplicações.

Esta revisão documental não aplica configurações, consulta contas ou altera o
backup em Downloads. O instalador independente já colocou os quatro componentes
no perfil lsi, preservando as oito preferências verificadas e o painel ativo.
Adicionar/substituir o painel e executar testes nas sessões reais de lsi/p001532
dependem da autorização prevista. Instalação de arquivos não é ativação do widget.

O [manual funcional](../plasma/applets/org.irixclassic.domainos.panel/FUNCTIONAL.md)
descreve gestos, capacidades e restrições; o
[contrato de preferências](../plasma/applets/org.irixclassic.domainos.panel/PREFERENCES.md)
documenta o KConfig por instância. Valores iniciais numéricos/enums são defaults
técnicos: mínimo de uma área de trabalho, sem criar nomes/quantidade na carga,
L=−1 não escolhido, agenda sem provedores ativados e tempo adicional da lente
desligado. Eles não são escolhas pessoais atribuídas ao usuário.

| Requisito | Estado | Prova e limite concreto | Severidade residual |
| --- | --- | --- | --- |
| F01 | comprovado isolado | Regressão final de aplicativos 32 conserva catálogo Kicker, gestos reais, busca/categorias, contexto e add/remove favoritos por mouse/teclado; F29 dirigido 32 observa atividade apenas nos despachos. Favoritos 28 anterior é histórico. Gaveta própria separada. | Baixa: favoritos nativos compartilham membros entre menus do mesmo usuário; client ID distingue ordenação. Alcance explícito na UI; nenhuma conta pessoal acessada. |
| F02 | comprovado isolado | Hora e fusos reais, quadro separado do calendário; preferências nativas persistem por instância. | Baixa: conferir localidade/fuso do perfil final. |
| F03 | comprovado isolado | Agenda pública 33: plugin nativo escolhido explicitamente no KConfig privado; evento all-day, agendaUpdated e delegate reais, clique do botão Data, descarregamento ao fechar. Contrato instrumentos 23 preservado. | Baixa: fonte de feriados públicos; nenhuma conta ou agenda pessoal acessada. Apply da página por clique não é alegado. |
| F04 | comprovado isolado | Rx/Tx e telemetria nativos; ausência de sensor e unidades diferentes recusam curva/escala compartilhadas. Intervalo mínimo do backend respeitado; relógio independente. Clique abre gr_osview existente. | Baixa: outros dispositivos/IDs dependem do sistema; não há conversão implícita de unidades. |
| F05 | comprovado isolado | `openMail` → helper → KIO abriu janelas próprias para override e default MIME privado. Desktop Entry resolvido, sem compose URI, espera pelo fim do aplicativo ou mudança global. | Baixa: cliente de teste não comprova Thunderbird/contas; contagem e estado permanecem indisponíveis sem fonte autorizada. |
| F06 | comprovado isolado | TasksModel verdadeiro X11 e Wayland; tarefas abertas/minimizadas, filtros/agrupamento por instância. Arraste manual usa move nativo e conserva janelas/pins. | Baixa: combinação completa de provedores/perfil final ainda merece ensaio. |
| F07 | comprovado isolado | Clique/Ctrl/duplo em janelas próprias; Wayland 30 verificações inclui UUID/PID, foco e configuração real da janela, sem protocolo restrito desativado. | Baixa: aplicações podem recusar operações. |
| F08 | comprovado isolado | Menu de tarefas nativo preservado; submenu forçado separado e helper com PID autenticado/pidfd. Grupos Wayland 62 aplica colunas/minimizar somente nos dois membros escolhidos. New Desktop final r7, 5/5 na comparação e 34/34 atuais: menu capturando A/B recusa grupo acrescido de C; reabertura cria uma área e move exatamente os três membros atuais. | Baixa: New Desktop usa QAction instalado acionado programaticamente em X11 privado, sem navegação física no submenu nem sessão pessoal. Guardas do botão do meio e encerramento forçado conservam provas/limites separados. |
| F09 | comprovado isolado | Navegação à esquerda e limite testados; não altera geometria/quantidade do painel. | Baixa. |
| F10 | comprovado isolado | Navegação à direita, última página e mais de sete tarefas testadas. | Baixa. |
| F11 | comprovado isolado | Desktop UUID nativo; ativação observada, seleção/relevo e cancelamento de pressão preservados. | Baixa. |
| F12 | comprovado isolado | Segundo cartão liga-se ao UUID existente; carga não cria nem renomeia desktops. | Baixa. |
| F13 | comprovado isolado | KWin privado: uma/duas/várias áreas, CRUD explícito por UUID e mínimo de uma. | Baixa: a sessão pode negar gestão. |
| F14 | comprovado isolado | Mapas geométricos e roda que navega sem ativar por padrão; alternativa de ativar provada. | Arraste entre miniaturas **adiado por decisão**; não é bloqueador desta revisão. |
| F15 | parcial | Bandeja e menus são os provedores nativos; abrir quadro não conecta/desconecta. | Baixa: não se mudou conectividade real do usuário. |
| F16 | parcial, falha reproduzida | Volume nativo/PulseAudio/atalhos privados: XTest no slot ajusta 50%→55%→50%; vizinhos e chapa preservam volume. Ensaio r9 passou 55/57. | Alta no overflow: ambas as direções não chegam ao compacto e não mudam volume, embora SNI no mesmo popup receba scroll. Candidatos MouseArea/WheelHandler falharam e foram revertidos; nenhuma correção foi retida. Sessões/áudio pessoais e Wayland não foram testados. |
| F17 | condicional ao provedor configurado | Só entradas reais configuradas; não há envelope fictício nem contagem fabricada. REQ-F17/RESP-A05 condicionam a contagem a uma fonte escolhida e autorizada. | Contagem/estado indisponíveis sem fonte autorizada; item pessoal não exercitado. |
| F18 | parcial | Item/provedor de dispositivos preservado; navegação não ejeta. | Baixa: montagem/ejeção de dispositivos reais não foi exercitada. |
| F19 | parcial | Provedores reais permanecem com suas ações/alvos; apresentação não transforma exemplo em serviço. | Baixa: monitor específico da sessão final depende da escolha local. |
| F20 | comprovado isolado | Bandeja 34 e concorrência dirigida 197: item SNI carregado posteriormente é adotado; seis estados de atenção confirmados no modelo/delegado durante gestos. | Baixa: entrada concreta varia conforme provedores; prova X11 privada, sem serviços pessoais. |
| F21 | comprovado isolado | Continuação dos visíveis, paginação alternativa/fallback e opção de incluir ocultos; ensaio com itens SNI próprios. | Baixa: validar espaço dos monitores finais. |
| F22 | parcial | ▲ oferece provedor nativo de status/notificações e ocultos; abrir não limpa histórico nem muda DND. | Baixa: avisos específicos de aplicações pessoais não foram usados. |
| F23 | comprovado isolado | Ordem/visibilidade próprias, seis células, IDs/títulos nativos via bridge, Apply real e sincronização nativa nos dois sentidos. | Baixa: não configura provedores globalmente. |
| F24 | comprovado isolado | Terminal de teste real, argumentos literais sem shell, novas instâncias e nenhum comando administrativo inicial. | Baixa: comando/terminal escolhido pode ser inválido, com falha explícita. |
| F25 | comprovado isolado | Ensaio dirigido31 invoca openAppearance→helper→System Settings instalado: PID/argv, janela Global Theme, objetos nativos de aparência e plugin kcm_lookandfeel.so mapeado. Oito preferências intactas. | Baixa: API do controlador, sem clique no painel completo; disponibilidade do KCM depende da instalação. |
| F26 | parcial | Menu enumera capacidades e abrir não executa ação; menus19 prova clique físico, três opções visíveis desde a primeira abertura e quatro bordas. Pedidos dependem dos serviços reais. | Moderada: suspender/hibernar/sair não foram executados em sessões pessoais. |
| F27 | pendente sessão real | Transporte/resultado DBus e falha explícita foram testados contra serviço privado de bloqueio. | Moderada: isso não comprova proteção física/bloqueio real do perfil em uso. |
| F28 | comprovado isolado | Manual distribuído e ordem painel/xman/KDE no menu. xman instalado abriu com fundo/texto das duas paletas, contraste observado e falha explícita quando ausente. | Baixa: exige xman e X11/XWayland; recursos extra de Highlight não foram observados na face inicial do Xaw. Ensaio separado31 observa openKdeHelp→helper→KHelpCenter instalado renderizando o manual local do Plasma; API do controlador, sem clique no painel completo. |
| F29 | comprovado isolado | Provas finais: catálogo/contexto dirigido 32 e regressão 32; New Desktop r7 atual 34. Activity de produção observa begin/finish síncronos, categorias/favoritos editados/inativos sem atividade, cauda opt-in só após retorno. Runtime real observa zero pedido no grupo obsoleto e um pedido no atual, com cauda acesa/apagada sem repetir/adiar. Padrão sem cauda preservado. | Baixa: dispatch-returned registra retorno e política de fechar; false não é falha da aplicação. request-accepted não é conclusão do compositor/aplicação. Casos false/exceção são modelos duplos declarados; durações 700/1500 ms são opções técnicas privadas, sem sessão real nem render da lente alegado por esses ensaios. |
| F30 | pendente sessão real | Instalação/restauração privadas provadas; instalação independente final em lsi conferiu os quatro destinos e preservou oito preferências, sem substituir o painel ativo. | Moderada: adicionar/substituir e testar o painel nas sessões lsi/p001532 depende da autorização prevista; não confundir instalação com ativação. |
| F31 | comprovado isolado | Paletas independentes e arte comparada por pixels; package 24/24 e integração 19/19 após a correção dos instrumentos. Alterações posteriores têm provas dirigidas: launcher29, favoritos28, bandeja34/concorrência197 e agenda33/contrato23; F29 dirigido32/regressão32, grupo34/pin30 e prévia26. Menus19 atual cobre abertura inicial, quatro bordas, rótulos e submenu; quadros18 observa sete Popup.Window nas quatro bordas (28 amostras), sem cortes. Instalação lsi5r9 confere os recursos correntes. Produção não reaplica layout nem outro perfil. | Baixa: monitores, escala e esquema específicos da sessão final não são todos cobertos. |
| F32 | comprovado isolado | Gaveta própria: ensaio dirigido30 comprova launchPin→Commands→helper→KIO real, argumentos/PID/janela/tarefa observados, pin conservado e Activity real. Apps32 conserva pin/unpin/ordem/metadata; importação explícita lê somente a fonte escolhida. | Baixa: dirigido pela API após abrir gaveta, X11 privado, sem clique físico na barra inteira ou sessão pessoal. request-accepted não é conclusão da aplicação; instância única pode reutilizar janela. |
| F33 | comprovado isolado | Oito categorias nativas, Configure da própria instância, Apply real para bridge e Cancel→Discard nativo com fechamento/reabertura sem salvar. Persistência/restart/segunda instância; página Monitor recusa intervalo abaixo do mínimo. Middle/wheel preservam defaults anteriores. | Baixa: clique nativo não foi exercitado em todos os campos; busca geral/Restaurar padrões foram sugestões editoriais. |
| F34 | comprovado isolado | Wayland nativo: grupo com três janelas e uma tarefa independente; cliques reais escolhem duas por checkbox, reabertura conserva seleção, colunas/minimização passam pela cadeia de produção e preservam membro/tarefa não selecionados. Acumulação entre dois grupos tem prova Qt separada. Helper X11/Wayland também recusa transientes/pais dependentes antes da mutação. | Baixa: destino técnico é activeScreen do KWin, documentado; API não expõe toda mainWindows/transients. Colunas/minimizar pela UI não substituem provas separadas dos outros modos e guards. |
| F35 | comprovado isolado | Wayland real prova N anterior ao agrupamento/filtro, N>L, N=L e N<L; restauração e fechamento reais atualizam apresentação/contagem sem circularidade. Ativar/trocar filtro não minimiza nem fecha janelas; L=−1 segue não escolhido. | Baixa: quatro janelas próprias não cobrem todos os aplicativos/escopos do perfil pessoal. |

## Evidências finais deste trecho

- `/tmp/irix-domainos-aparencia-ajuda-native-r3/RESULTADO.json`: 31/31; System Settings/kcm_lookandfeel e KHelpCenter/manual do Plasma reais, pelo controlador e helper de produção; namespaces privados, oito preferências e quatro fontes utilizadas intactas, processos próprios encerrados.
- `/tmp/irix-domainos-instalacao-lsi-20261008-r5-native-final/RESULTADO.json`: 5/5 históricos, anteriores a F29/New Desktop; quatro destinos daquela rodada, oito preferências iguais no intervalo, recibo `b82a0b4a995143adb4b8b4f7b7b7094a`; nenhum widget ou painel ativado/substituído.

- `/tmp/irix-domainos-aplicativos-favoritos-native-r3/RESULTADO.json`: 28/28 históricos, antes da correção F29; contexto nativo, add/remove favorito por mouse/teclado e escopo compartilhado do KDE explicitado. Pins/tarefas/perfis pessoais intactos. As duas linhas de autoria restauradas após o teste estão em `COPYRIGHT-NOTICES.json`, sem alteração de código.
- **F29 final dirigido:** `/tmp/irix-domainos-aplicativos-atividade-runtime-curto-final-r3/RESULTADO.json`, **32/32**. Catálogo/favorito/Desktop Action usam Kicker e Desktop Entry privados reais; markers exatos `first`, `first`, `context-first`. Activity de produção, tokens de begin/finish, padrão sem cauda e opt-in técnico 700 ms após retorno. False/exceção são modelos duplos declarados; categorias/metadados/inativos sem atividade.
- **F29 regressão final:** `/tmp/irix-domainos-aplicativos-regressao-atividade-runtime-curto-final-r10/RESULTADO.json`, **32/32**, incluindo os 28 checks anteriores, gesto Qt pressão/processEvents/50 ms/soltura, popup/alvo/owner visíveis, janela ativa e ausência de modal. Pins continuam mock de pedido nesse ramo. R1–r8 falhos preservados; r8 tinha QDialog KIO Error modal com runtime longo, não desaparecimento entre press/release. Runtime curto removeu erro/modal; r9 confirmou primeiro despacho mas observador atingiu deadline. Não se capturou o caminho completo do socket; não atribuir esse erro à prévia de p001532. Resumo: `/tmp/irix-domainos-aplicativos-atividade-F29-final.md`.
- **New Desktop final r7:** `/tmp/irix-domainos-menu-desktop-membership-r7/RESULTADO.json`, **5/5 na comparação e 34/34 atuais**. RAW anterior continua failed em exatamente dois gates: cria outra área e move C fora da captura A/B. Atual recusa alvo alterado sem mutação/emissão; menu reaberto cria uma área e move A/B/C atuais. Runtime/Activity reais registram um pedido `newVirtualDesktop` e um relatório `request-accepted`; cauda opt-in técnica 1500 ms acende/apaga sem repetir/adiar. Prova X11 privada com QAction instalado acionado programaticamente, UUIDs/PIDs/geometrias reais, sem render da lente ou sessão real. R6, comparação 5/5/atual26, é histórico anterior à emissão F29; R1–r5 do observador permanecem preservados. Fontes/hashes/limites em `TEST-SOURCES.json` e `test-sources/`; quatro preferências pessoais, fontes e processos próprios conferidos.
- **Prévia final com saída longa:** `/tmp/irix-domainos-runtime-preview-longo-r2/RESULTADO.json`, **26/26**, incluindo startup11 e Pager9. Saída199/runtime23 caracteres, UID/0700/nonce, abertura e lançamento reais pelo Kicker com XTest, ausência de modal/KIO/QML, quatro trocas de área mantendo painel/referência fora das tarefas, encerramento próprio e remoção do runtime. Guardas de UID/root/symlink são API dirigida; nenhum perfil pessoal usado. Wrapper daquele ensaio `380a74e443e2c4282f2242919f1ffd20f0c859a14718244d172da5a35d4aca70`, anterior à troca das cópias de ícones por links; o resultado histórico não cobre essa troca posterior.
- **Gaveta positiva final:** `/tmp/irix-domainos-pin-lancamento-native-r2/RESULTADO.json`, **30/30**, launchPin→Commands/helper→KIO reais, janela X11 8388615/PID2510306/argv literal conferidos, task sem launcher adicional, pin conservado e Activity token1 imediata/final apagada enquanto app aberto. API após abrir gaveta; request-accepted é retorno do pedido, não conclusão da aplicação. Oito preferências/fontes intactas, pidfd/daemons/runtime próprios limpos. R1 failed do interceptor de teste preservado; nenhuma produção/bundle mudou.
- `/tmp/irix-domainos-concorrencia-native-directed-r16/RESULTADO.json`: 197/197; seis estados de atenção do item SNI próprio consumidos durante pressão, com ACKs e intervalo monotônico, mais CPU/notificações/teclado/geometria. `/tmp/irix-domainos-bandeja-native-attention-refresh-r15/RESULTADO.json`: 34/34 após corrigir adoção dos loaders carregados depois.
- `/tmp/irix-domainos-agenda-publica-native-r4/RESULTADO.json`: 33/33; provedor de feriados públicos no HOME privado, evento/agendaUpdated/delegate nativos e preferência restaurada vazia. `/tmp/irix-domainos-instrumentos-agenda-regressao-final-r1/RESULTADO.json`: 23/23 após corrigir o binding loop de enabledPlugins.

- `/tmp/irix-domainos-preferencias-20261008-mouse-final/RESULTADO.json`: 32 verificações; mapa KConfig real, três defaults anteriores, edição não salva prematuramente, Apply por API e restart/segunda instância. Não afirmar clique nativo nos três novos controles quando o ensaio usa a API.
- `/tmp/irix-domainos-iconbox-20261008-scaled-ancestor-final-r6/RESULTADO.json`: 46 verificações, entradas Qt reais contra Iconbox de produção com tarefas privadas; grupo e menu de organização em QQuickWindows separadas num host de 109 px. Inclui ancestor.scale=0.5: Iconbox global top=645 e popup frame bottom=640, conteúdo nativo de 208 px inteiro acima. Não substitui prova de menu/provider nativo.
- `/tmp/irix-domainos-reorder-native-final-window-r4/RESULTADO.json`: 32 verificações, TasksModel verdadeiro e gesto Qt real em KWin X11 privado; duas reordenações e identidade/estado/pins conservados, já no código final Popup.Window. A tentativa r3 parou antes do barramento devido à restrição de sockets do sandbox, sem iniciar o ensaio nem alterar perfis.
- `/tmp/irix-domainos-tarefas-wayland-host-20261008-r2/RESULTADO.json`: 30 verificações no executável plasmawindowed legitimamente autorizado; não abrange grupos/N automático.
- `/tmp/irix-domainos-grupos-wayland-r5/RESULTADO.json`: **62/62**, cadeia nativa Iconbox → Tasks → WindowOperations → script KWin temporário, em Wayland privado. Usa o `/usr/bin/plasmawindowed` e Desktop Entry instalados, sem identidade artificial ou desativação do protocolo restrito. Clique abre grupo real, checkboxes escolhem exatamente dois UUIDs/PIDs, menu aplica colunas/minimizar e observa geometria/estado no compositor; os demais alvos permanecem intactos. N pré-filtro/pré-grupo, N>L/N=L/N<L, restauração e fechamento são observados em janelas reais. Zero erros QML; perfis e fontes preservados. A revisão r5 acrescenta três verificações de namespaces antes/depois de exec e de saída dos processos próprios; a produção é idêntica. O resultado r3 de 59/59 é histórico e não é somado ao final.
- `/tmp/irix-domainos-janelas-x11-r7-transientes/RESULTADO.json` e `/tmp/irix-domainos-janelas-wayland-r7-transientes/RESULTADO.json`: 55/56 verificações do helper, separadas da UI TaskManager.
- `/tmp/irix-domainos-package-20261008-r4-unidades-final/RESULTADO.json` e `/tmp/irix-domainos-integracao-20261008-r3-unidades-final/RESULTADO.json`: 24/24 e 19/19 após corrigir instrumentos/amostragem, com recursos/paleta/startup nativos. Antecedem as correções de lançamento e de favoritos/bandeja/calendário, provadas separadamente acima/abaixo; não substituem ensaios detalhados de grupos/preferências/comandos.
- `/tmp/irix-domainos-instrumentos-unidades-native-final-r2/RESULTADO.json` e `/tmp/irix-domainos-instrumentos-contrato-final-r2/RESULTADO.json`: 34/34 dirigidos com sensores reais e 23/23 do contrato anterior; unidades incompatíveis não geram escala/curva, min1000 ms respeitado e relógio continua atualizado com sensores60000 ms.
- `/tmp/irix-domainos-preferencias-descarte-native-final-r1/RESULTADO.json`: 18/18; Cancel→Discard por cliques nativos, reabertura preserva configuração salva e segunda instância, sem afirmar clique em todos os campos.
- `/tmp/irix-domainos-lancamentos-mail-xman-native-r2/RESULTADO.json` e `/tmp/irix-domainos-comandos-contrato-final-launch-r3/RESULTADO.json`: 29/29 específicos e 23/23 do contrato de comandos. Janelas próprias de correio observadas e xman real com duas paletas; nenhuma conta pessoal acessada. As cores extras de Highlight do Xaw não foram afirmadas como renderizadas.
- `/tmp/irix-domainos-instalacao-lsi-20261008-r4-launcher/RESULTADO.json`: 5/5, instalação independente real no perfil lsi; quatro destinos atuais conferidos, oito preferências intactas no intervalo, `active_panel_replaced=false`.
- `/tmp/irix-domainos-entrega-20261008-r5-launcher/RESULTADO.json`: 22/22 históricos após o launcher; instalação pública de quatro destinos privados, repetição e restauração.
- `/tmp/irix-domainos-entrega-20261008-r6-native-final/RESULTADO.json`: 22/22 dirigidos sobre fontes finais de favoritos/bandeja/calendário; instalação/repetição/restauração byte a byte dos quatro destinos privados. Recibo restaurado `71af8245db2b46cb8be985a417cf339e`. Não repete nem substitui as 52 guardas anteriores do instalador.
- `/tmp/irix-domainos-validacao-sessoes-r5-verificacao/RESULTADO.json`: 13/13 históricos, com 147 fontes; o helper corrigido é a única diferença para r4.
- `/tmp/irix-domainos-validacao-sessoes-r6-verificacao/RESULTADO.json`: 13/13 históricos; snapshot daquela rodada com149 fontes exatas/152 arquivos, instalador/manifestos/ajuda; sete diferenças para r5, duas fontes novas. Sem instalação em p001532 ou ativação de sessão.
- `/tmp/irix-domainos-teste-pacote-r2-verificacao/RESULTADO.json`: 20/20 históricos; recursos daquela rodada, fontes/licenças/links, ambos os comandos públicos `--verificar`, preferências intactas e pacote r1 preservado. Naquela rodada, `/tmp/irix-domainos-teste` passou a apontar para r2; o launcher corrente aponta para r5; r3/r4 preservam alcance histórico. Nenhuma dessas preparações abriu sessão gráfica.
- **Entrega histórica r7:** `/tmp/irix-domainos-entrega-20261008-r7-native-final/RESULTADO.json`, **22/22**, quatro destinos privados exatos install/repeat/restore; recibo `c85245c2d7d547d99c0377be95a3bd99` restaurado e oito preferências reais intactas.
- **Offline histórico r7:** `/tmp/irix-domainos-validacao-sessoes-r7-verificacao/RESULTADO.json`, **13/13**, 149 fontes/152 arquivos, seis deltas para r6 (três QML/três manuais do applet), manifesto/permissões e --verificar privado sem escrita/display/bus.
- **Portátil histórico r3:** `/tmp/irix-domainos-teste-pacote-r3-verificacao/RESULTADO.json`, **20/20**, 28.510 fontes/28.514 arquivos/2.096 links internos; ambos --verificar exit0, raízes privadas e r2 preservados, runtime-wrapper exato. Naquela rodada, launcher `/tmp/irix-domainos-teste` atualizado atomicamente para r3; essa prova antecede r4/r5. Nenhuma GUI real ou instalação p001532 executada.
- **Instalação histórica lsi r7:** `/tmp/irix-domainos-instalacao-lsi-20261008-r7-current-manuals-final/RESULTADO.json`, **5/5**, quatro destinos exatos, oito preferências iguais no intervalo e recibo `d77376e664f848b39feb42b8cf563a36`. Apenas applet mudou; restauração do último recibo recupera só seus destinos alterados. Nenhum widget ou painel ativado/substituído.
- **Históricos r8/r4:** `/tmp/irix-domainos-entrega-20261009-r8-menus/RESULTADO.json` (22/22), `/tmp/irix-domainos-instalacao-lsi-20261009-r8-menus/RESULTADO.json` (5/5), `/tmp/irix-domainos-validacao-sessoes-r8-menus-verificacao/RESULTADO.json` (13/13) e `/tmp/irix-domainos-teste-pacote-r4-menus-verificacao/RESULTADO.json` (20/20) registram a primeira correção dos menus. Snapshots r8/r4 preservados por bytes, links, modos e UID; essas provas antecedem a correção dos demais quadros.
- **Menus correntes:** `/tmp/irix-domainos-menus-native-r7-quadros/RESULTADO.json`, **19/19**, regressão dos menus na fonte atual. A prova `/tmp/irix-domainos-quadros-native-r1/RESULTADO.json` passou **18/18** com **28 amostras de sete Popup.Window nas quatro bordas**, todos dentro da área disponível; ajuda local teve clique físico, demais quadros foram abertos/cancelados pelas APIs. Baseline `/tmp/irix-domainos-quadros-baseline-r7/RESULTADO.json` reproduziu cortes no topo de grupo/excedentes/status; os quatro diálogos já cabiam sob o WM X11. Bootstrap específico de popups, sem repetir/alegar Pager9 ou os onze gates do bootstrap original; nenhuma ação de energia/dispositivo/tarefa/CRUD foi aceita.
- **Entrega corrente r9:** `/tmp/irix-domainos-entrega-20261009-r9-popups/RESULTADO.json`, **22/22**, instalação/repetição/restauração dos quatro destinos privados com fontes atuais; recibo `6cd0a6f77af14f7693f1c5560c771ccb` restaurado, preferências reais e Classic/perfil global preservados. Não repete as 52 guardas históricas.
- **Offline corrente r9:** `/tmp/irix-domainos-validacao-sessoes-r9-popups-verificacao/RESULTADO.json`, **13/13**, 150 fontes/153 arquivos; checksum, permissões, --verificar privado e preservação byte a byte/modos/UID do snapshot r8. Nenhuma sessão ou instalação pessoal executada ao prepará-lo.
- **Portátil corrente r5:** `/tmp/irix-domainos-teste-pacote-r5-popups-verificacao/RESULTADO.json`, **20/20**, 28.511 fontes/28.515 arquivos/2.096 links internos; ambos --verificar aprovados, raízes privadas intactas e r4 preservado por bytes/links/modos/UID. Corte `/tmp/irix-domainos-teste-pacote-r5-popups-verificacao/CORTE-LAUNCHER.json` passou **8/8**, incluindo o launcher real da prévia executado somente com --verificar privado; `/tmp/irix-domainos-teste` agora aponta para r5 e mantém o papel Xephyr. Nenhuma GUI ou perfil p001532 aberto/instalado na preparação.
- **Instalação corrente lsi r9:** `/tmp/irix-domainos-instalacao-lsi-20261009-r9-popups/RESULTADO.json`, **5/5**, quatro destinos iguais às fontes e oito preferências iguais no intervalo; recibo `a946085d8131442fa8214fc5534541d7`. Apenas o recurso applet foi atualizado; restauração do último recibo atua só sobre destinos alterados. Nenhum widget ou painel ativo substituído.
- **Resumos pessoais anteriores ao portátil r3:** `/tmp/irix-domainos-teste-uid1000-2c96370c8dfd-resumo.json` e `/tmp/irix-domainos-teste-uid1003-f84a11039b85-resumo.json` registram startup11/11 e Pager9/9. Ambos antecedem o manifesto r3; não identificam hashes de fontes nem comprovam a avaliação manual da entrega final. Em lsi, o ENCERRADO acessível confirma hashes preservados/processos próprios encerrados. O conteúdo privado de p001532 não foi acessado; seu resumo público não comprova encerramento ou estado vivo atual.
- `/tmp/irix-domainos-concorrencia-native-r13/COBERTURA-VF20.json`: recorte VF20 180/180, 12 ciclos de mouse/Space/Tab com CPU e notificações reais, relevo/ação no mesmo despacho e geometria constante. O `RESULTADO.json` original permanece failed: limiar extra de atenção antes da expiração não comprovado e exit1 derivado. O modelo SNI e oito sinais totais não provam esse subtotal nem toda a cobertura temporal de VF14.
- `/tmp/irix-domainos-preview-pager-sticky-r2/PAGER-VERIFICACAO.json` e `PAGER-REGRESSAO.json`: 7/7 e 11/11, respectivamente. O defeito de visibilidade reproduzido no Xephyr foi corrigido somente na ferramenta de prévia: painel/referência próprios permanecem nas duas áreas, quatro cliques reais observados e perfis preservados. Não houve alteração do Pager de produção ou do painel real.
- `/tmp/irix-domainos-funcional-r2-20261008/RESULTADO.json` e `SOURCE-COPIES.json` no mesmo diretório: prévia Xephyr final, 10/10 na inicialização e igualdade byte a byte instalado↔repositório↔cópia privada de painel, gr_osview e estilo; esquema instalado também igual. O PNG da referência aprovada não executa ações. A captura da composição inferior utiliza dados/provedores nativos privados.
- `/tmp/irix-domainos-selection-final-sources-20261008-r6.json`: SHA-256 dos arquivos fechados após a correção de ancoragem de escala por este agente.

Os snapshots offline R9 e portátil R5 conservam os quatro recursos do painel,
seus helpers e o wrapper atuais. Seu `components.json` é o catálogo de **30
componentes**, anterior à decoração opcional DomainOS SR10.4; o catálogo atual
tem **31**. A comparação de todas as fontes capturadas encontrou somente essa
diferença, e ambos os manifests de checksum continuam válidos. A decoração
`domainos_sr104` está fora dos quatro destinos do instalador do painel e tem
entrega própria **24/24** em `/tmp/irix-domainos-decoration-entrega-r3/RESULTADO.json`.
A conferência conjunta de leitura passou **20/20**, com caminhos e hashes em
`/tmp/irix-domainos-goal-auditoria-20261009-catalogo/RESULTADO.json`.
Isso não repete nem amplia as provas históricas da suíte completa.

O protocolo `xdg_toplevel` não informa a minimização externa ao `QWidget`. No
ensaio de grupos, minimização é comprovada pelo resultado KWin e pela observação
fresca do TasksModel; restauração também é confirmada pelo foco do cliente próprio.
Não se afirma que `QWidget::isMinimized()` observou essa minimização em lote.

No fechamento documental, todos os PIDs registrados daquela prévia r2, incluindo
Xephyr e supervisor, estavam ausentes. Não há `ENCERRADO.json`; a causa e o caminho
do fechamento não foram estabelecidos. O relatório de inicialização e a captura
são evidências históricas, não uma indicação de prévia ainda aberta nem confirmação
de encerramento pelo supervisor. O ensaio separado de cleanup documentado no
relatório principal conserva seu alcance próprio.

Os 62 checks nativos acrescentam a prova integrada que faltava a F08/F34/F35;
os 30 checks anteriores e as fixtures Qt continuam com seu alcance próprio.
Hardware, áudio, conectividade, dispositivos, contas/agenda pessoais e comandos
sensíveis nas sessões reais não são comprovados por serviços/entradas de teste.

Não resta defeito de alta severidade identificado neste trecho. As limitações acima distinguem implementação de prova em sessão pessoal. O arraste adiado do Pager e integrações de contas não autorizadas não devem gerar novas perguntas ou bloqueios inventados.

## Critérios VF01–VF20 e invariantes D0–D10

Conferência dos critérios dos requisitos e da preservação da base visual.
Os números são contagens por ensaio, não uma soma de cobertura; os valores
numéricos técnicos não são novas decisões atribuídas ao usuário.

## VF01–VF20

| Gate | Estado | Prova concreta e fonte | Limite ou falta real; severidade |
| --- | --- | --- | --- |
| VF01 — emblema/gaveta | comprovado isolado | Aplicativos final 32 conserva catálogo/categorias/pesquisa, contexto e add/remove favorito por mouse/teclado; F29 dirigido 32 prova despachos Kicker reais e categorias sem atividade. Favoritos 28/composição 19 conservam alcance histórico; drawer mantém pins próprios; Sessão é distinta. | Baixa: favoritos KDE compartilham membros por usuário/atividade; não se acessaram bancos pessoais. O ramo de lançamento dos pins no ensaio 32 continua mock de contrato de pedido, sem alegação de janela real desse ramo. |
| VF02 — relógio/data | comprovado isolado | Instrumentos 23/Unidades 34 preservam hora, fusos, localidade e relógio separado. Agenda positiva33 usa holidaysevents, região pública e 2027-01-01 via KConfig próprio: evento/agendaUpdated/delegate nativos e unload ao fechar. Binding loop de ativação corrigido com snapshot de IDs; nenhum evento ou provedor inventado. | Baixa: agenda positiva pública e privada; contas pessoais e Apply por clique não foram autorizados/exercitados. |
| VF03 — rede/medidores | comprovado isolado | Instrumentos finais 23 + ensaio dirigido34 com ksystemstats real. Rx/Tx `network/all/download` e `upload`, unidade200/200; CPU `cpu/all/usage`, unidade1002. Combinação1002/200 fica indisponível, escala/frações nulas e históricos vazios; Graph tem zero delegates de séries, inclusive com histórico antigo injetado explicitamente como defesa. Recuperação Rx/Tx e CPU sem segundo sensor passam. Página Monitor real recusa250→1000 ms; limite nativo efetivo e relógio separado confirmados. | Baixa: sensores de dispositivos específicos podem faltar ou publicar mais lentamente que o limite. Igualdade exige a mesma unidade nativa; não há conversão implícita. Sem curva/escala compartilhada para unidades incompatíveis. |
| VF04 — correio | comprovado isolado | Lançamentos29 executa controlador de produção openMail→helper→launcher KDE para override e default mailto privados distintos: dois Desktop Entries próprios abrem QWidget/marker reais, sem URI compose e com HOME/XDG/display/bus privados. Default privado permanece igual, nenhum MIME real escrito. Unitários12 verificam contrato/IDs/resultados; instrumentos 23 prova despacho separado. | Baixa: prova real de contrato de lançamento, não de Thunderbird ou contas pessoais. Helper registra request-accepted; a observação de janela é do ensaio separado, não completion inventada do cliente. Sem contagem ou estado de mensagens fabricados. |
| VF05 — tarefas/agrupamento | comprovado isolado | TasksModel X11/Wayland30, grupos Wayland62 e Iconbox46: tarefas por IDs nativos, abertas/minimizadas conforme filtros, contagem anterior ao agrupamento, grupos sem limite artificial de7. Pins separados em modelo/configuração próprios. | Baixa: aplicativos restritos podem negar ações; quatro janelas privadas não representam todo o perfil do usuário. |
| VF06 — cliques/seleção | comprovado isolado | Wayland30 prova clique/Ctrl, identidade/PID, minimizar/restaurar/ativar/maximizar/fechar em três janelas próprias; grupos62 prova menu/contexto e cadeia de organização em membros explícitos. Iconbox46 comprova Qt mouse/duplo/relevo imediato; reorder32 usa limiar de arraste do sistema. | Baixa: pedido nativo não equivale a conclusão de aplicação. Grupos não escolhem um membro implícito para fechar/minimizar/mover pelo botão do meio. |
| VF07 — checkboxes entre grupos | comprovado isolado, provas distintas | Iconbox46 é fixture Qt com dois grupos, alvos parciais, acumulação/preservação da seleção e nenhuma ação ao marcar. Grupos Wayland62 tem grupo real de três janelas+avulsa, dois UUIDs escolhidos por cliques reais e reabertura preservada. | Baixa: a troca entre dois grupos foi provada pela fixture Qt; não apresentar esse caso específico como duas aplicações agrupadas reais em Wayland. A prova Wayland cobre seleção parcial e exclusão dos demais pela cadeia de produção. |
| VF08 — mudança da lista | comprovado isolado | Grupos Wayland62 observa fechamento/recontagem sem trocar seleção por outro UUID; Iconbox46 cobre reagrupamento e reorder32 recusa fonte fechada/PID divergente. New Desktop final r7 compara captura A/B com grupo A/B/C: versão anterior criava área/movia C; atual resolve membros/PIDs e capacidade novamente e recusa antes da mutação. Reabrir permite alvo atual exato. | Baixa: QAction programático em X11 privado, com UUIDs KWin, IDs/PIDs/geometrias reais. RAW anterior continua failed; não reter alvo por índice/rótulo/posição nem afirmar navegação física ou Wayland desse caso. |
| VF09 — organização | comprovado isolado, provas distintas | Helpers KWin X11/Wayland55/56 executam colunas/linhas/mosaico para2/3/6 e distinguem maximizar/minimizar/coletar. Grupos Wayland62 liga a UI real→Tasks→WindowOperations→helper para colunas/minimizar somente2 UUIDs, preservando terceiro membro e tarefa avulsa. | Restrição moderada documentada: destino técnico é activeScreen/área útil do KWin. Transiente/modal, pai com dependente ou relação de grupo que a API não isola são recusados antes do lote; não mover dependentes não escolhidos. A prova UI de2 alvos não é uma prova UI de todos os modos para6. |
| VF10 — filtro automático | comprovado isolado | Wayland62 observa N>L, N=L e N<L com janelas reais; N é anterior ao filtro/agrupamento. Filtro não minimiza/fecha; restauro e encerramento reais alteram contagem. L=−1 continua não escolhido. | Baixa: scopes desktop/monitor/atividade dependem da instância; não criar L “aprovado” pelo usuário. |
| VF11 — gaveta | comprovado isolado | Pin-lançamento30: cadeia de produção real até KIO abre janela própria; PID/ID/argv e nova tarefa observados, pin conservado, token/luz reais, nenhum launcher inserido nas tarefas. Apps32 valida catálogo/metadata/lista/ordem e contrato; importação unitária valida IDs XDG, origem explícita só leitura e persistência por instância. | Baixa: prova positiva de API após abrir gaveta, X11 privado; sem clique físico no painel completo ou sessão pessoal. Pedido novo não garante novo processo para apps de instância única. |
| VF12 — Pager | comprovado isolado | Pager103 no KWin privado: UUIDs reais,1/2/várias áreas, CRUD explícito e mínimo1; cartões/setas inferiores e roda só navega por padrão; alternativa ativar foi executada. Regressão da prévia antes9 confirma que seu host Qt.Tool, vinculado à área0, desaparecia ao clicar no segundo tile, mantendo o processo vivo; o Pager ativava corretamente a área1. Wrapper corrigido:7 checks + startup11 e regressão11 comprovam painel/referência próprios sticky, quatro cliques reais2→1→2→1, ambos IsViewable/PID vivo e terminal normal com visibilidade por desktop. | Baixa: correção somente da ferramenta de prévia Xephyr; produção do Pager intacta. Carga/instalação não cria ou renomeia desktops reais. Perfil final pode negar gestão. |
| VF13 — miniaturas | comprovado isolado; arraste adiado | Fontes+Pager103: geometria nativa como mapas, sem captura de conteúdo real; capacidades/estados especiais e limitações documentadas. Nenhum handler de arraste parcialmente habilitado. | Arraste entre miniaturas foi adiado expressamente, sem impedir menus de movimento/organização. Não é falta desta revisão. |
| VF14 — bandeja | comprovado isolado | Bandeja 34 após fix de adoção assíncrona SNI, preferências 13/Discard 18 e concorrência dirigida 197. Seis estados do ID próprio são consumidos no modelo/delegado, com ACK e tempos dentro do intervalo de input; attentionCount=6 até o último release. | Baixa: prova X11 privada com serviços KDE reais e produtor próprio; hardware/contas pessoais não exercitados. R13/R14/R15 failed preservados e suas lacunas explicadas no relatório. |
| VF15 — sessão | parcial por limite autorizado | Comandos23: menu não executa ações, DBus/falha/resultado observados contra ScreenSaver privado; produção envia pedido ao serviço real, sem chamada global ao abrir o menu. | Bloqueio físico, logout, suspensão/desligamento reais não são comprovados por serviço privado e não foram autorizados neste ensaio. Não são motivos para deixar trabalho técnico privado inacabado nem para acioná-los sem autorização. |
| VF16 — ajuda | comprovado isolado | Lançamentos29 executa openXman→helper→/usr/bin/xman instalado, observa janela e pixels das paletas nativas Irixium/DomainOS-SR10.4. Contraste Window/text renderizado11,6655 e4,6337. Menu nativo preserva manual→xman→KDE e não lança ao abrir. PATH privado sem xman devolve erro explícito e apaga atividade. Manual distribuído passa pacote/instalação; unitários recusa injeção e protege contraste. Aparência/ajuda31 observa openKdeHelp→helper→KHelpCenter instalado, PID/argv/janela e manual local do Plasma renderizado. | Baixa: ajuda KDE comprovada pela API do controlador em X11/bus/HOME privados, sem clique no painel completo ou conclusão do programa. Recursos adicionais *Command são enviados, mas Highlight não aparece na face inicial do Xaw; não é exigência de VF16, e cores Window/text efetivamente renderizadas são legíveis. Identificação histórica exata de alguns glifos permanece distinta da adaptação. |
| VF17 — lente | comprovado isolado | Comandos23 histórico conserva tokens/concorrência. F29 final dirigido32/regressão32 liga catálogo, favorito lançável e Desktop Action à Activity, sem atividade de categorias/metadados/inativos. New Desktop r7 atual34 usa Runtime/Activity reais: zero emissão no alvo obsoleto, uma no atual; cauda privada 1500 ms acende/apaga após pedido sem repetir/adiar a ação. Default keepLightAfterCompletion=false. | Baixa: dispatch-returned observa somente retorno; no contexto true solicita fechar o catálogo e false não prova falha da aplicação. request-accepted observa despacho, sem conclusão do compositor/aplicação. Caudas técnicas opt-in 700/1500 ms não são preferências do usuário; sem sessão pessoal ou render da lente inferido. |
| VF18 — preferências | comprovado isolado | Oito categorias ConfigModel reais; preferências32: KConfig por instância, restart e segunda instância, Apply nativo de relógio e API para outros campos. Bandeja13: Configure de produção, títulos de provedores reais, edição/Apply pointer. Discard18: clique nativo Cancel→Discard em página própria, fechamento/reabertura sem salvar e segunda instância101 intacta. Unidades34: página Monitor real rejeita intervalo abaixo do mínimo. | Baixa: não confundir API fixture com clique Apply para todos os campos. Busca global e Restore Defaults por página são sugestões editoriais; não escolhas expressas ausentes. Defaults/ranges técnicos descritos abaixo. |
| VF19 — instalação/restauração | comprovado isolado; ativação pessoal pendente | Suite offline34 e independente52 comprovam recurso próprio, hashes/recibo, idempotência/restauração e recusas de caminhos compartilhados/links/edição posterior. Unidades: package24r4/composição 19r3/offline13r4. Instalação corrente lsi5r9 após as correções dos menus/quadros confirma quatro destinos iguais às fontes e oito preferências iguais no intervalo, painel ativo intocado. Entrega privada22r9 prova instalar/repetir/restaurar os quatro destinos com recursos/manuais e backups exatos; snapshot13r9 contém150 fontes/153 arquivos, portátil20r5 confere recursos e ambos --verificar e corte8 valida o launcher Xephyr. Quadros18/Menu19 cobrem as fontes atuais. R8/r4 e versões anteriores preservam alcance histórico. | Moderada: instalar recursos não valida ativação/substituição do painel em lsi/p001532. Restauração privada passou antes de qualquer proposta de ativação. |
| VF20 — desempenho/teclado | comprovado isolado | Concorrência dirigida r16: 197/197 no relatório original, 12 ciclos mouse/Space/Tab, CPU/notificações/histórico nativos, seis estados SNI consumidos durante pressão e geometria constante dos14 módulos. Máximos press/release mouse 2,956/65,634 ms e Space 4,530/18,299 ms. | Baixa: tempos QTest deste host X11, sem garantia universal ou medida física até a tela. R13 passou 180 do recorte mas manteve failed 182; r14 demonstrou omissão de SNI e r15 timeout do harness, ambos corrigidos com provas distintas. |

## D0–D10 e preservação da base visual

As expressões antigas “apenas desenho/sem função” e dados fixos em D4–D6 são
referência visual, não uma ordem de manter produção fictícia. A precedência R2
autoriza funções reais sem alterar o desenho; a produção usa entidades nativas
e as amostras ilustrativas ficam no ensaio de referência explicitamente identificado.

| Invariante | Estado e prova | Limite concreto |
| --- | --- | --- |
| D0 — Classic independente | comprovado: diff contra base vazio para Plasma Style Classic, Iconbox/Quicklaunch/Systemtray anteriores, defaults look-and-feel Classic e classic_panel/apply_suite/components.py. Comparação semântica de `components.json` confirma profiles.classic e moderno iguais. Independente52 preserva recursos/configs legados. | O perfil Classic continua com IDs IrixClassic, não DomainOS. Configs de usuário podem mudar por uso fora do intervalo do ensaio; não inferir causa a partir de um hash posterior. |
| D1 — recursos próprios | comprovado: metadata org.irixclassic.domainos.panel/IrixClassicDomainOS, esquema DomainOS-SR10.4 e gr_osview instalados offline em XDG privado; independente52/suite34 e unidades package24r4/composição 19r3/offline13r4. Instalação corrente lsi5r9 inclui as correções de menus/quadros e manuais, quatro destinos exatos e oito preferências intactas, sem painel ativo substituído. Entrega privada22r9 prova hashes/recibo/backups e restauração dos quatro destinos; snapshot13r9 e portátil20r5 conservam os quatro recursos, helpers e wrapper atuais, com catálogos anteriores à decoração opcional e preservação de r8/r4 comprovada. Corte8 mantém o launcher Xephyr; a instalação de recursos não comprova ativação pessoal. | Só instalar por usuário autorizado; demais perfis não são visitados. Nenhum layout migrado. |
| D2 — dois andares/chapa | comprovado isolado: referência2437 usa mesmo DomainOSPanel de produção, geometria, molduras, metal26 e ciano2+2 em escala50% conservados. | A prova de referência não finge estado/telemetria reais. Concorrência r13 observa14 módulos e o host sem mudança de geometria durante Notify/sensores reais. |
| D3 — bloco esquerdo/fontes | comprovado isolado: relógio analógico/data/gráfico/correio mantêm artes aprovadas e fonte Courier privada; teste2437 cobre proporção, paletas, AA/configfonts. Instr34 altera somente disponibilidade/curvas, preserva fundo/divisórias/dimensões. | Courier é experimento aprovado; Swiss742 é atribuição histórica provável, não identificação exata comprovada. A produção usa data/hora reais em vez do exemplo fixo. |
| D4 — iconbox/relevos | comprovado visual: referência contém os sete samples na ordem Desk/xterm/winterm/john/Index/Downl/xterm e setas;2437 mede geometria/paletas/press/cancel. Produção reutiliza TaskButton/mesmas molduras e entidades reais. | Sete posições no desenho não são limite de tarefas nem lançadores fixos na produção. |
| D5 — seleção Pager | comprovado visual e funcional: referência2437 compara Work/Procrastination e marcador de seleção nas paletas; Pager103 e Wayland62 distinguem estado nativo da simulação. | Instalar/carregar não impõe nomes Work/Procrastination em desktops existentes. Imagens geométricas não são capturas de conteúdo. |
| D6 — bandeja | comprovado visual: seis símbolos2×3 e setas na referência, molduras conservadas. Bandeja 34 usa provedores reais em produção e vazio/indisponível conforme fonte. | Não tratar símbolo ilustrativo de rede/mensagens/LED como leitura real universal. |
| D7 — rodapé | comprovado isolado:2437 cobre selo GNU/LINUX, quatro sulcos, drawer de três janelas, cinco desenhos e lente com aro/sombra internos, imagem aprovada preservada. | Símbolos mantidos não constituem prova de ação; comandos23 e testes de funções são evidências distintas. |
| D8 — estética/paleta | comprovado isolado:2437 compara oito paletas, incluindo seleção amarela e estados pressionados; filetes ortogonais opacos, sem blur/arredondamento/transições decorativas novas. Widgets usam paleta fornecida. | Contraste do esquema final/escala de cada monitor pessoal merece avaliação autorizada, não aplicação automática. |
| D9 — renderização/press-cancel | comprovado:2437 visual usa componente compartilhado, estados normal/pressionado/cancelado e logs;46 Qt mouse e15 teclado separam input de função;109px/scale0,5 têm popups Window e ancoragem física testados. | O modo de referência continua sem ações; isso não proíbe as funções R2 já aprovadas na produção. |
| D10 — perfis/backup protegidos | comprovado no escopo: namespaces privados, hashes de preferências antes/depois, instaladores não criam/renomeiam desktops ou substituem painel. Backup congelado permanece referência fora do trabalho. | Ativação pessoal exige a autorização específica prevista. Prévia r2 está encerrada: PIDs/Xephyr/supervisor ausentes, sem ENCERRADO.json; causa não estabelecida. Não declarar aberta nem fechamento confirmado pelo supervisor particular. |


## Fechamento técnico 0.2.11 R4 — duas saídas e ConfigView

Este complemento qualifica as provas históricas de F33/VF18 e F34/VF09;
não soma contagens de ensaios diferentes nem reescreve resultados falhos.

- **F34/VF09:** R3 demonstrou a minimização antes do commit cross-output.
  Produção corrigida por sinais, sem atraso de ação: R6 **68/68**, R7
  **41/41** e consolidação **13/13**. Minimização normal/prévia e coleta
  conservam o destino atual nas duas saídas virtuais; colunas no segundo
  monitor têm regressão final. Janelas excluídas, UUID/PID, capacidades e
  desktops originais conferidos. Nove layouts anteriores para 2/3/6 e
  maximização não foram repetidos integralmente no helper final.
  `/tmp/irix-domainos-batch-two-outputs-011-final-20261009.json`, SHA256
  `436904b19e6d65fef0bcc95d6d3ba0de97dbd03e030ef542045a170a9ecc8cac`.
- **F33/VF18:** o erro do PromptDialog é reproduzido somente desabilitando
  cache QML no ensaio isolado do componente instalado. Política normal com
  cache XDG próprio: Aplicar, Cancelar/Descartar, reabrir, reiniciar e segunda
  instância passaram, sem TypeError. Bruto atual **26/27** mantido: a única
  premissa obsoleta é exigir nove linhas totais em vez de nove páginas próprias
  e extensões nativas do calendário. Complemento da causa **15/15**; verificador
  público corrigido **17/17**, com negativos. VisibleRole não foi gravado
  numericamente pelo host; fórmula, seleção vazia e captura têm alcance distinto.
  `/tmp/irix-domainos-configview-cache-native-011-20261009-r2/CAUSA-ANALISE.json`,
  SHA256 `9d20538db74b35ce0e7982f75e752d1e89c0d1f77b87bb143fe366917912b88b`.
- **Pacote R4:** 272 arquivos, 920238 bytes, SHA256
  `a2540fc117bb8c70012d3897bd2f46cdcd153cc0d11483bcf441b9c2c7199306`.
  Auditoria independente **29/29** e **9/9 testes reais extraídos**:
  instalação/repetição/restauração dos quatro destinos, fontes/DSO, sete
  entradas nativas, fechamento de imports e ausência de diretórios pessoais
  em textos/DSO. R3 preservado; sem novas entradas nem recompilação.
  `/tmp/irix-domainos-final-011-r4-independent-audit-20261009/RESULTADO.json`,
  SHA256 `a20b5dd086b37b8a0aa7880dac25f032208c0434b1eb90c20ffd3bd926cc581b`.
- **Prévia pública R4:** 31 componentes e 29451 arquivos lógicos; quatro
  recursos exatos ao ZIP e 27 herdados de snapshots públicos R3, conferidos
  contra a fonte atual. R3 e sua base pública de ícones são dependências
  desses links e permanecem disponíveis. Dois exports antigos R1/R2 foram
  compactados com bytes, modos, UID/GID, mtime e links verificados para liberar
  inodes; seus recibos históricos continuam preservados. Esses caminhos de
  teste não são dependências do instalador publicado.
  `/tmp/irix-tema-completo-recursos-011-r4-verificacao-20261009.json`, SHA256
  `926925e971fe03c63b2c0160998c0ff023f53de99531765b2e0ee58ed33fd771`.
  Aliases futuros `/tmp/irix-tema-completo` e `-011`: **7/7**, sem ação sobre
  as prévias abertas; bytes/modos anteriores conservados para restauração.
- **Nova prévia lsi:** display `:64`, inicialização **14/14** em namespace
  descartável, Qt6/Kvantum e GTK3/4 nativos. Captura e recibo em
  `/tmp/irix-tema-completo-011-lsi-r6-20261009`; resultado SHA256
  `2d4138dcde4b428166adeb037a252ad8b981b8d191eeb9a7244aa07dd8598ead`.
  Supervisores das três prévias anteriores e da nova conferidos no namespace
  do host; nenhum foi encerrado ou recarregado. A presença deles não foi
  inferida da visão de PIDs do sandbox.

F30/aceite pessoal permanece pendente: abrir a prévia atual em p001532 e
confirmar preferências/Aplicar/Descartar e interação da Iconbox nas duas sessões.
O comando é `/tmp/irix-tema-completo` via Alt+F2 na sessão correspondente.
A inicialização da prévia em lsi não substitui esse aceite manual. Não houve
instalação global, commit, push ou publicação nesta rodada; o backup congelado
em Downloads permaneceu intocado. Arraste entre miniaturas continua adiado.

## Comparação com a VM SR10.4 — cores e relevos, 2026-10-10

Esta revisão substitui a limitação histórica de F31/VF20 sobre cores fixas do
GTK/Kvantum no tema DomainOS. A referência foi a VM em execução: Domain/OS
SR10.4, HP VUE 2.01 e manuais instalados do Motif Release 1.1. O nível de patch
do Motif não foi identificado. Não foram usadas referências de SR10.4.1.

A leitura dos oito conjuntos CoralReef e da colormap nativa mostrou que a barra
estava saturada demais. Agora, o relevo da faixa superior usa o conjunto 5
(`#a3d0e6` / `#194b63`) e o da faixa metálica usa o conjunto 3
(`#c4d5ed` / `#3e536e`). As janelas usam o azul primário `#78a0d5`; moldura
ativa coral `#fe8282` e inativa ciano `#7acac5`. São os valores da referência,
reconstruídos a partir dos papéis de cor atuais: trocar o esquema continua
alterando as superfícies, sem uma exceção pelo nome do esquema.

- **Paleta e aplicações abertas:** a prévia descartável R5 passou **40/40**
  verificações no percurso DomainOS → Breeze Dark → Irixium → amarelo de teste
  → DomainOS. Qt6 com `Kvantum::Style`, GTK3 e menu de fixados foram medidos
  renderizados. Não houve reinício dos aplicativos, injeção de paleta ou mudança
  de fonte/geometria; os hashes das configurações do host ficaram iguais.
  A troca usa o script público `tools/apply_kvantum_colors.py` após aplicar o
  esquema KDE, conforme a estratégia aprovada para o Kvantum.
- **Paleta Qt completa:** o leitor KDE registrou os 21 papéis em cada grupo
  Active/Inactive/Disabled. Os oito papéis consultados na QApplication com
  Kvantum coincidiram com os correspondentes do leitor; não se infere disso
  igualdade de pintura de todos os controles.
- **Controles Motif:** a adaptação de GTK/Kvantum passou **160/160** verificações
  nativas dirigidas de face, relevo e indicadores marcados. As setas nativas
  GTK3 passaram **816/816**, com diferença máxima de zero nos 320 recortes
  comparados em quatro esquemas. GTK4 não oferece botões de seta nativos nas
  barras de rolagem; essa diferença de API permanece explícita.
- **Limite histórico:** VUE atribui conjuntos secundários por aplicativo
  (Vuefile 5, Vuehelp 6, Vuestyle 7). O esquema comum do KDE não reproduz essas
  escolhas por cliente. A seleção de listas mantém o papel semântico KDE;
  não foi acrescentada uma política de cores por aplicativo.

Recibos locais de QA, fora do pacote publicado:
`.qa-domainos-sr104-native-colors-preview-r5/FINAL-DOMAINOS-RECEIPT.json`,
`.qa-domainos-motif-relief-r4/NATIVE-COMPARISON.json` e
`.qa-domainos-palette-native-calibration-r1/NATIVE-BEFORE-AFTER.json`.
A captura final DomainOS tem SHA256
`279fe204257021d58d7515f7fdd22c7f6a903dc5906436454cf3cf32c9337bac`.
Esses ensaios não encerram o aceite pessoal nem comprovam a correção dos
pop-ups da Iconbox: essa investigação continua separada.

### Favoritos externos na gaveta — F32

O verificador atual passou **53/53** em um perfil privado. Um segundo cliente
Kicker/KAStats real definiu e reordenou os favoritos; a gaveta seguiu a ordem
desse menu ao reabrir, mesmo com a ordem local diferente. O clique lançou a
entrada desktop correspondente à identidade, não ao índice anterior do
provedor. Preferências permaneceu primeiro e bloqueado, os fixados do painel
na segunda seção e os favoritos na terceira, com separadores. Controles de
ordenação/remoção ficaram até 28 px e o nome conservou ao menos 200 px.

O ensaio também verificou zero alterações de bytes nas estatísticas e nos
metadados do menu externo feitas pela leitura de ordem, e zero mudanças nos
perfis pessoais. Recibo:
`/tmp/irix-domainos-favorites-completion-audit-20261010-r2/RESULTADO.json`, SHA256
`69dc251b674bbb86450585db72d9e2c2671338f00ed1dd488757977ae51c9a90`.
A primeira tentativa, impedida pela restrição do socket D-Bus no sandbox,
permanece registrada separadamente; não foi convertida em resultado positivo.

### Agenda Manaus e flutuação nativa — F03 e X10

O comando público `plasma/tools/testar-domainos-agenda.py --manaus-2026
--validar-unicidade` passou **138/138** com o Runtime atual e o plugin KHolidays
nativo. Os quinze feriados locais de 2026 apareceram uma única vez na fonte e
na agenda visível; nove datas de ponto facultativo não viraram feriados. Os
casos fora de 2026 não receberam eventos locais extrapolados. Abrir, fechar e
descarregar o provedor preservou a sessão e os arquivos pessoais. O alcance
continua sendo Manaus/AM/Brasil em 2026, sem promessa de calendário regional
para outros anos. Recibo:
`/tmp/irix-domainos-manaus2026-regressao-20261010-r5/RESULTADO.json`, SHA256
`702d3dfcf50911bff645e71e7b52783d57328d6cb30568813fa5269a96a79bd7`.
Somente os limites de espera do observador de QA foram ampliados; as asserções,
os dados e os tempos do produto permaneceram iguais. Tentativas anteriores
incompletas continuam registradas como tal.

O comando público `plasma/tools/testar-domainos-fundo.py` passou **44/44** em
KWin/Plasma/Xvfb privados. A margem inferior nativa foi de 8 px com a janela
restaurada, zero ao maximizar e novamente 8 px ao restaurar. O desenho manteve
971 × 109 px e escala 50%, sem recorte, nas cinco situações inspecionadas.
A associação `NoBackground` cedeu ao adicionar outro widget e voltou somente
quando o painel continha apenas DomainOS. A restauração conservou as escolhas
anteriores de fundo, inclusive ao recuperar um painel salvo pela versão antiga.
Não houve erro QML dos nossos applets, mudança das fontes durante o ensaio ou
alteração das configurações pessoais. Os processos próprios foram encerrados.
Recibo: `/tmp/irix-domainos-native-floating-final-20261010-r1/RESULTADO.json`,
SHA256 `2be4ed238d365a763cd35c143d88a7a08701ef18ec74127c833eb49e582f86fc`.

### Iconbox: seleção, foco e operações — revisão R8

A extensão lateral que aparecia ao abrir o seletor vinha do indicador de foco
do painel KDE: seu retângulo acompanhava a largura lógica da Iconbox, antes
da escala do desenho. O receptor de foco agora tem tamanho zero. A Iconbox
continua recebendo teclado sem aumentar o desenho, a máscara do painel ou a
área de entrada. No ensaio X11 R2, os 14 recortes da faixa lateral tiveram
zero pixels diferentes com seletor e menu abertos ou fechados. Esse recibo
pertence à cópia privada que validou a solução; a entrega R8 contém a solução.

Como o painel nativo não aceita foco de janela, a liberação de Ctrl/Shift
também é observada por `KeyboardIndicator.KeyState`, módulo existente no
Plasma. Só os estados desses dois modificadores são consultados. Não há
captura de texto, grab de teclado, temporizador ou alteração do KDE. O
primeiro evento que conclui uma seleção desarma o gesto antes de abrir
Operações, evitando que o evento Qt e o evento global abram duas vezes o menu.
Fechar o seletor também desarma esse gesto, conservando as janelas escolhidas.

- **Qt e ciclo dos pop-ups:** **11/11** testes de regressão, com eventos Qt
  reais e controladores de tarefas deliberadamente substituídos. Cobrem
  transição seletor → Operações, liberação dos modificadores, fechamento,
  descarte de identidades antigas e organização por ponteiro/teclado.
- **Modificadores X11:** o microteste independente passou **42/42** com
  Ctrl/Shift reais, janela sem foco e liberações rápidas nas duas ordens.
  O sinal bruto pode conservar momentaneamente o bit da tecla recém-solta;
  o chamador remove esse bit antes de decidir se resta outro modificador.
  O ensaio comprova esse protocolo X11, sem estender o resultado ao backend
  global de modificadores do Wayland.
- **Painel X11 atual:** o recibo R4 passou **13/13** com entradas nativas
  de ponteiro e teclado. Ctrl selecionou duas identidades Qt/GTK reais e
  abriu Operações uma única vez ao soltar. Com Ctrl+Shift, a primeira
  liberação aguardou a última; liberações duplicadas ou sem gesto não
  reabriram o menu. No seletor de grupo, a conclusão segue o protocolo de
  Continuar seleção/Operações, sem interromper cada marcação. Clicar fora
  com Ctrl pressionado conservou as escolhas e não abriu menu ao soltar.
  Operações apareceu completo na primeira abertura, com 275 × 246 px;
  Colunas organizou os dois PIDs selecionados e conservou as três janelas
  excluídas. Geometria, máscara e `NoBackground` do painel ficaram iguais.
  A faixa lateral teve zero pixels diferentes nos quinze estados de
  pop-ups/gestos. Após Colunas, 98 pixels da margem transparente mudaram
  porque as janelas atrás dela foram movidas; esse resultado bruto foi
  conservado e não foi chamado de erro ou igualdade de desenho.
- **Janelas Wayland:** o comando público `testar-domainos-grupos-wayland.py`
  passou **75/75** com a Iconbox R8 em um KWin privado e o host instalado
  `plasmawindowed`. Restaurar pelo título, acumular/desmarcar checkboxes,
  conservar a seleção ao reabrir, contar antes de agrupar/filtrar, organizar
  em colunas e minimizar em lote atuaram nos UUIDs/PIDs escolhidos.
  As janelas excluídas permaneceram intactas. O ensaio não exercita a
  liberação global de modificadores em um painel Wayland sem foco.

Recibos locais:
`.qa-domainos-popup-native-headless-focus-r2/PROXY-GHOST-RECEIPT.json`,
`.qa-domainos-modifiers-native-microprobe-r1/RESULTADO.json` e
`/tmp/irix-domainos-current-iconbox-wayland-20261010-r1/RESULTADO.json`.
O último tem SHA256
`9564f57c76dee6fcc3d975d513f46763817f1280932ae9a719db80aed49bc38e`.
Todos os processos de teste próprios foram encerrados; os perfis pessoais
e as fontes permaneceram iguais durante os respectivos ensaios.

O recibo X11 atual está em
`.qa-domainos-popup-native-public-r4/NATIVE-R8-QA/FINAL-RECEIPT.json`, SHA256
`9db431470b9b8444fa589fb37cb6d205e95d65544233381d09b962652b5c1d62`.
A fixture agrupou as galerias Python pelo nome do executável porque seu
catálogo KService descartável não resolveu todas as entradas. Duas janelas
foram fixadas temporariamente pela interface para testar seleção direta;
não houve substituição do modelo de tarefas. O timeout inicial por esperar
Operações enquanto o seletor de grupo ainda estava aberto permanece como
tentativa inválida do observador, separado da prova final.

### Identidade das janelas na prévia completa

Xephyr e os aplicativos privados agora compartilham o namespace de PIDs.
Isso permite que XRes autentique o PID real de cada janela e que a ponte
de operações conserve sua verificação de identidade. A prévia mantém HOME,
usuário, mounts, rede, IPC e D-Bus próprios. A versão anterior escondia os
PIDs internos do servidor X e a ponte recusava corretamente as operações.

O encerramento identifica o worker pelo marcador exclusivo da própria prévia
antes de sinalizá-lo; o worker encerra os seus filhos no bloco de limpeza.
Os lançadores desktop das galerias também usam os IDs declarados pelos
aplicativos. Esses ajustes pertencem ao lançador de testes, sem remover
verificações de identidade do produto ou reiniciar a sessão pessoal.

Fechar o display R4 encerrou os dezessete processos registrados/adicionados,
incluindo servidor X, supervisor e worker. Um segundo ensaio de inicialização
**18/18**, R5, conferiu o caminho de SIGTERM no supervisor: todos os processos
registrados e identificados pelo marcador próprio também encerraram.
Os dois recibos conservaram o perfil pessoal. O worker ainda registra o
SIGTERM esperado como `failed/error=0`; esse estado bruto está preservado
ao lado dos recibos de limpeza e não foi renomeado como sucesso de execução.
Recibos: `.qa-domainos-popup-native-public-r4/OWNED-NORMAL-CLOSE-CLEANUP.json`
e `.qa-domainos-popup-native-term-r5/OWNED-SUPERVISOR-TERM-CLEANUP.json`.

### ZIP portátil R8

O ZIP existente, sem reconstrução, passou **4/4** métodos originais de teste
e **18/18** verificações da revisão. Os métodos cobrem payload alterado,
entradas inseguras/duplicadas/links, omissão de runtime obrigatório e
instalação → repetição → restauração dos quatro destinos em perfis
descartáveis. Foram preservados os bytes, modos, backups e configurações
anteriores. O teste de reconstrução determinística e os quatro testes de
inventário de checkout não foram executados nessa validação específica.

O módulo de modificadores, o gate de fechamento do seletor e a dependência
do módulo KDE nos dois instaladores coincidem com as fontes atuais. O ZIP
mantém 275 entradas, 940551 bytes e SHA256
`e7f4a53c788aaa472854094aca23de9cfc6ab3cccad64c9803c519f88b2699f7`.
Recibo: `.qa-domainos-portable-r8-validation-r1/RESULTADO.json`.
Essa prova é de instalação offline do pacote independente de quatro
recursos; GTK, Kvantum, decoração e terceiro tema global pertencem ao
instalador da suíte completa, com validação e entrega próprias.

### Instalação como opção no lsi

O instalador normal da suíte concluiu a atualização de 40 componentes em
52 destinos, incluindo as compatibilidades GTK2/Xcursor, e compilou o
módulo nativo no stage privado com o mesmo SHA256 do pacote R8. Foram
instalados o terceiro tema global `org.magpie.irixclassic.domainos.desktop`,
a decoração `domainos_sr104`, GTK/Kvantum DomainOS e o painel atual. A
atualização incremental modificou 18 destinos; backups, fingerprints e
28 overlays gerenciados foram conferidos pelos seus recibos.

A leitura nativa pós-instalação passou **16/16**. Global Classic, nome do
esquema, Kvantum, grupos efetivos de cores/WM, IDs do painel/desktop/tray,
geometria configurada, 45 preferências e dois desktops ficaram iguais.
Os três registries do Wine também conservaram seus hashes. O GTK permaneceu
na família Classic e passou de `IrixClassic-KDE` para a variante gerenciada
`IrixClassic-KDE-Reload`; fontes, ícones, cursor e demais opções ficaram
iguais. As pontes renovadas estão ativas, com 21 e 11 módulos verificados.
O baseline Classic e o recibo manual do painel foram mantidos; a ponte
não executou transição de painel durante a instalação.

Recibos locais:
`/tmp/irix-domainos-host-suite-r8-postinstall-summary-20261010.json` e
`/tmp/irix-domainos-host-installed-r8-audit-20261010-r2.json`.
A instalação verifica os arquivos no disco. Os módulos que já estavam
carregados no Plasma pessoal não foram reiniciados ou descarregados;
o aceite visual e funcional usa a nova prévia. A instalação em p001532
continua dependendo de execução pelo próprio usuário na sua sessão.

### Lançador portátil com recursos imutáveis

Dois problemas anteriores à abertura foram reproduzidos no export R8 real:
o destino automático diretamente em `/tmp` falhava no guard de propriedade,
e `copytree` preservava as permissões de somente leitura ao normalizar
decorações e gerar paletas GTK privadas. O lançador agora cria um pai
temporário privado com `tempfile` e concede escrita somente ao dono das
cópias de trabalho. O guard de destinos e os recursos publicados mantêm
suas restrições. Os três testes de regressão de
`plasma/tests/test_preview_private_copies.py` passaram, incluindo escrita
real de metadata/CSS na cópia e conservação dos bytes/modos da fonte.

As tentativas recusadas ficaram registradas separadamente em
`.qa-domainos-suite-delivery-r8/PREVIEW-FAILED-ATTEMPTS.json`. Não foram
convertidas em inicializações positivas. O export R8 permanece imutável;
a correção do lançador é distribuída em uma edição R10 própria, conservando
o ZIP e os recursos gráficos validados anteriormente. A tentativa R9 também
reproduziu uma cópia de galeria ainda sem escrita; essa quinta cópia agora
usa o mesmo tratamento privado. O recibo dessa falha anterior à GUI foi
conservado em `.qa-domainos-readonly-export-native-r9/READONLY-GALLERY-FAILURE.json`.


A edição R10 congelada passou **17/17** verificações de integridade e os
**3/3** testes públicos existentes contra o lançador exportado. A abertura
real com destino temporário automático passou **18/18**, seguida de **8/8**
verificações de cores nativas: Qt/Kvantum com os oito papéis ativos do
esquema e GTK3/GTK4 com a família e pixels esperados. O encerramento normal
eliminou os processos próprios, preservou o perfil real e manteve os
31.603 registros e hashes do export. O estado bruto de shutdown esperado
continua registrado separadamente; ele não foi reclassificado.

Recibos: `.qa-domainos-r10-export-validation-r1/RESULTADO.json` e
`.qa-domainos-readonly-export-native-r10/RESULTADO.json`. A derivação nativa
usa Xvfb no lugar do Xephyr e o caminho R10 declarado; o painel, os helpers,
o módulo nativo e as galerias são os recursos publicados. Os três aliases
temporários foram promovidos para R10, com backup dos anteriores e recibo
em `.qa-domainos-suite-delivery-r8/R10-ALIASES.json`. O comando
`/tmp/irix-domainos-completo` inicia diretamente o terceiro perfil DomainOS
numa sessão privada do usuário que o executa. Essa prévia não substitui
a instalação nem o aceite pessoal em p001532.


A prévia visível R10 foi aberta no lsi pelo alias público, sem derivação
Xvfb: display `:67`, perfil DomainOS, decoração `domainos_sr104`, pacote
original e lançador final. As **18/18** verificações de abertura passaram;
os hashes do perfil pessoal continuaram iguais. A janela foi deixada aberta
para aceite manual, sem fechar as cinco prévias anteriores nem a VM.
Recibo: `.qa-domainos-suite-delivery-r8/R10-LSI-VISIBLE.json`. O aceite
visual/funcional do revisor e a execução pela própria sessão p001532
continuam pendentes; essa abertura não conclui a integração inteira.

### Conferência atual da VM e limite de pintura GTK3

Nova consulta somente leitura confirmou Domain/OS SR10.4, CoralReef e os
oito conjuntos da colormap. Os seis arquivos de configuração relidos por
FTP e os conjuntos consultados por Telnet coincidiram com o levantamento
anterior. Os **12/12** papéis medidos do esquema público continuam iguais
à VM, incluindo controles, seleção e molduras ativa/inativa. A captura
atual confirmou também as duas texturas distintas da barra.

O Style Manager e seus diálogos Color/Mouse usam o conjunto secundário 7
(`#768ca1` / rebaixo `#647788`), enquanto a paleta compartilhada KDE usa o
conjunto primário 3. Essa diferença já declarada não indica que a atualização
de cores do Qt/GTK deixou de funcionar.

Há uma diferença pequena de pintura no relevo GTK3 da prévia R10:
`#c4d6ed`, contra `#c4d5ed` na VM, no Qt e no painel, isto é, um nível a mais
no canal verde. Foi observada nas bordas do botão e na linha do grupo.
A fonte e o fator de mistura são iguais; quantização no processamento GTK
é uma hipótese compatível, não uma causa rastreada. Não se afirma igualdade
de todos os pixels. Nenhuma configuração, foco ou entrada da VM foi alterada.
O perfil permanece CPU principal 100%, Ethernet 10%, frameskip 4 e sem throttle.

Recibo local somente de observação:
`/tmp/irix-domainos-reference-20261010/live-observation-r2/CURRENT-COMPARISON-SUMMARY.json`.
A comparação dirigida adicional está em
`.qa-domainos-live-color-review-20261010/COMPARACAO.json`.

### Instalar opções preserva as escolhas existentes

A ponte de GTK/Kvantum agora lê o Tema Global efetivo como estado inicial.
Iniciar ou atualizar a integração não equivale a escolher novamente esse
tema: a primeira reconciliação e mudanças apenas de cores usam o caminho
de paleta, preservando seleções independentes. Uma mudança posterior da
identidade do Tema Global continua selecionando seus companions. Reaplicar
a mesma identidade não constitui uma transição nesse observador; os comandos
explícitos de aplicação/sincronização continuam disponíveis.

O teste usa QFileSystemWatcher e QProcess reais em um perfil descartável;
barramento e worker são fixtures, sem seleção gráfica pessoal. A regressão
da ponte passou **18/18**, seleção de companions **28/28** e restauração da
integração global **4/4**. Recibo:
`.qa-domainos-companion-baseline-20261010/RESULTADO.json`.

### Distribuição portátil dos três temas

A distribuição completa acrescenta o fechamento dos auxiliares públicos ao
catálogo dos **40 componentes**, reutilizando o módulo nativo verificado do
ZIP independente. A instalação continua verificando sua arquitetura e ABI Qt;
não depende do SDK temporário da máquina de desenvolvimento. O ZIP independente
continua contendo quatro componentes, e a prévia R10 continua sendo uma prévia.

O ciclo real da suíte em HOME/XDG/TMPDIR privados passou **13/13** verificações:
instalação, reinstalação e restauração dos 40 recursos, backups úteis,
preferências independentes e bytes/modos da fonte preservados. Compilador,
`moc` e `pkg-config` foram bloqueados no ensaio; nenhum foi chamado. Os
31.286 arquivos/aliases foram verificados sem caminhos de perfis pessoais.
As três regressões novas e os vinte testes pertinentes existentes passaram.
Recibo: `.qa-domainos-suite-package-r1/RESULTADO.json`.

A edição R2 muda somente o lembrete de áudio opcional e seu manifesto; não
acrescenta áudios à distribuição gráfica. Inventário, módulo nativo, seus sete
arquivos de entrada e demais recursos coincidem com R1. Essa equivalência foi
conferida separadamente, sem repetir o ciclo inteiro ou um teste gráfico.
Recibo: `.qa-domainos-suite-package-r1/R2-MESSAGE-DELTA-RESULTADO.json`.

O lançador temporário deste host valida o SHA256 do R2, extrai em pasta própria
e chama o instalador público. Seu `--verificar` real passou em HOME privado,
sem criar configuração, dados ou estado, e sem abrir GUI ou serviço pessoal.
Recibo: `.qa-domainos-suite-bootstrap-r2/RESULTADO.json`. Esse lançador facilita
o teste em p001532 e não integra os caminhos temporários ao produto publicado.
Instalação e aceite na sessão pessoal de p001532 continuam pendentes.

### Distribuição R3 e aplicação sem o módulo opcional de áudio

A revisão dos comandos anunciados encontrou uma falha no aplicador da edição
R2: a aplicação padrão importava um auxiliar de áudio ausente da distribuição
gráfica. Instalar e verificar os recursos não demonstrava esse caminho. O
aplicador agora preserva a escolha de sons quando esse suporte opcional não
está incluído; `--exigir-sons` continua recusando a aplicação antes de efeitos.
Erros internos de um auxiliar presente continuam sendo reportados.

As regressões do aplicador passaram **21/21**. O wrapper real do arquivo R2,
com somente o aplicador corrigido sobreposto, passou **9/9** verificações de
aplicação/restauração em perfil privado. Arquivos, transação e backups são
reais; a chamada de aplicação do KDE é um processo de teste explícito. Esse
ensaio não demonstra uma nova troca gráfica de Tema Global.
Recibo: `.qa-domainos-suite-optional-sounds-r1/RESULTADO.json`.

A distribuição R3 inclui essa correção e um README próprio, correspondente
a `docs/DISTRIBUICAO-SUITE.md`. Seus **40 componentes**, arte e módulo nativo
permanecem iguais. Passaram **8/8** verificações de manifesto, modos, aliases,
fechamento dos imports obrigatórios e presença dos 12 comandos anunciados.
R1 e R2 foram preservados. Não se repetiu o ciclo completo de instalação nem
se contou essa conferência como teste de GUI.
Recibo: `.qa-domainos-suite-package-r3/RESULTADO.json`.

O lançador temporário foi atualizado para o SHA256 do R3. Seu `--verificar`
real passou em HOME/XDG/TMPDIR privados, sem criar configuração, dados ou
estado. Recibo: `.qa-domainos-suite-bootstrap-r3/RESULTADO.json`. A instalação
pessoal anterior no lsi e o aceite pendente dos dois perfis continuam sendo
registros separados dessas provas da distribuição.

### Paginação nativa com as fontes atuais da Iconbox

A paginação atual foi verificada com TaskManager/KWin instalados e **16
janelas reais próprias**, além da janela do instrumento. Cliques Qt nas
duas setas produziram as páginas 0 → 7 → 14 → 7 → 0, sem ativar tarefas.
As dimensões das células e as identidades das janelas permaneceram iguais;
a última página continha os três itens restantes. Passaram **36/36**
verificações nativas. O ensaio separado com tarefas de teste passou **12/12**.

O recibo consolidado registra os hashes das fontes atuais e o encerramento
dos recursos privados observáveis, incluindo o limite de não ter registrado
individualmente todos os PIDs auxiliares. Esse teste não usa janelas pessoais
nem demonstra Wayland ou o painel completo. Recibo:
`.qa-domainos-iconbox-current-navigation-r1/RESULTADO.json`.

Foi corrigido também um falso positivo no runner público: sem recibo nativo
e sem conclusão explícita do cenário, ele deve falhar, mesmo que o perfil
pessoal permaneça preservado. As cinco regressões desse contrato passaram.

### F15/F18: modelos reais e controles nativos preservados

Um ensaio privado abriu, fechou e reabriu os applets originais de rede e
dispositivos pelos slots do adaptador atual. NetworkManager informou estado
70 e conectividade 4; seu modelo nativo apresentou **18 entradas**. O modelo
de DeviceNotifier apresentou **cinco dispositivos**, com contagens de remoção
e montagem fornecidas pelo próprio modelo. As identidades dos applets e das
representações foram preservadas. Recriar o NetworkModel ao reabrir é o
comportamento original do PopupDialog do KDE.

Passaram **17/17** verificações observacionais. A revisão dos delegates
originais confirmou os ramos de estado, disponibilidade e ações explícitas:
Connect/Disconnect continuam no handler de rede; as ações de dispositivos
continuam em `deviceActions`. Esse conjunto comprova a integração e
preservação dos controles previstas em F15/F18. Não demonstra sucesso físico
de conexão, montagem ou ejeção, que não foram executadas neste ensaio.

O barramento do sistema foi exposto somente por getters explicitamente
permitidos no proxy. RequestScan não é permitido; o applet original pode
solicitá-lo ao abrir, portanto não se alega varredura irrestrita. As 54
entradas booleanas observadas não foram mapeadas a capacidades específicas.
Houve duas referências a binding loops e uma a acesso negado, sem atribuição:
os textos brutos dos provedores foram descartados para não guardar dados
pessoais. Não se afirma ausência de avisos nem se atribui o acesso negado a
RequestScan. Os processos próprios foram encerrados. Nenhuma captura ou
identificador de rede/disco foi salvo.

Recibo final: `.qa-domainos-provider-readonly-native-r1/FINAL-RECEIPT.json`;
escopo dos controles e da política:
`.qa-domainos-provider-readonly-native-r1/NATIVE-CONTROL-SOURCE-REVIEW.json` e
`.qa-domainos-provider-readonly-native-r1/POLICY-PROOF.json`.

### Recibos pessoais da instalação como opções

Chegaram os recibos públicos do instalador executado pelos UIDs de lsi e
p001532. Ambos informam **40 componentes instalados como opções**, com o
SHA256 da distribuição R2 conferida. A autoria e o UID declarado coincidem.
Os dois registros mantêm `personal_acceptance: false`.

Esses recibos encerram a pendência de execução do instalador nas duas
sessões; não enumeram hashes atuais de todos os arquivos pessoais nem
comprovam aceite visual/funcional. A correção e distribuição R3 continuam
validadas separadamente; não se alega aplicação pessoal do R3 por esses
recibos R2. Observação somente leitura:
`.qa-domainos-suite-personal-receipts-20261010/RESULTADO.json`.

No lsi, a conferência somente leitura dos dois runtimes pessoais encontrou
**zero diferenças**: 22 arquivos de companions e 11 da ponte DomainOS
coincidem com a fonte e com o R3. Os serviços estão ativos e iniciaram depois
da gravação desses arquivos. A verificação do runtime e a restauração em
modo de consulta passaram, sem instalação, restauração real ou restart.
Não foi necessário atualizar novamente. Recibo:
`.qa-domainos-suite-personal-runtime-20261010/RESULTADO.json`.

### Correção do critério de encerramento

A expressão anterior “aceite manual das prévias nas duas sessões” não é
uma exigência adicional de F30. O requisito exige instalação por usuário,
preservação, substituição autorizada e restauração. A autorização já
concedida não precisa ser solicitada novamente; também não se exige nova
aprovação subjetiva do desenho a cada revisão.

O pedido do usuário “Vamos testar lá no final do goal” mantém uma etapa
concreta de teste funcional em p001532. Os recibos públicos encerram a
pendência de instalação, mas não mostram interação com as preferências,
Aplicar/Descartar e a Iconbox na sessão desse perfil. A prévia e seus
controles continuam disponíveis por `/tmp/irix-domainos-completo` via
Alt+F2. A pendência vigente é essa verificação funcional final, sem criar
outro checklist, refazer instalação ou solicitar novamente aprovação do
desenho. Os ensaios técnicos já registrados continuam com seus escopos;
nenhuma confirmação pessoal é inferida deles.

### Correções solicitadas no reteste: espera e seta GTK3

O reteste do usuário mostrou duas lacunas que os recibos anteriores não
cobriam. O ensaio da lente comprovava pulsos para tokens pendentes, mas os
lançamentos curtos encerravam o token no retorno do auxiliar; isso não
reproduzia a espera do VUE pelo aparecimento do cliente. A comparação GTK
com o próprio asset gerado também aceitava a iluminação invertida da seta
inferior. As classificações desses dois pontos foram reabertas antes da
correção; os demais resultados mantêm seus escopos originais.

O gerador GTK3 agora aplica a iluminação depois de escolher a direção da
silhueta. Assim, a seta inferior mantém luz no alto/esquerda e sombra no
lado direito e na ponta, conforme o controle da referência SR10.4. O teste
de uma tabela GTK3 real passou **540/540** verificações em duas paletas KDE
exportadas e duas identidades adaptativas, incluindo o encontro inferior
direito das barras, pressão/soltura, hover, desativação e limites de rolagem.
As **18/18** regressões do desenho passaram. Os 939 recursos conferidos de
GTK2, CSS comum GTK4 e Kvantum permaneceram byte a byte iguais. Esse ensaio
não exercita transporte de paleta em tempo real nem a nova prévia completa.
Recibo: `.qa-domainos-gtk3-scroll-corner-r1/FINAL-RECEIPT.json`.

As nove prévias Xephyr antigas foram encerradas por seus próprios displays,
com supervisores e workers autenticados. O MAME permaneceu no mesmo
processo. Os recibos de encerramento apresentam os mesmos hashes finais do
perfil do host; comparar uma prévia antiga com seu início também inclui as
alterações pessoais feitas enquanto esteve aberta. A prévia mais recente
preservou seu snapshot inicial. Recibo:
`.qa-domainos-led-gtk-correction-20261010/PREVIAS-ENCERRADAS.json`.

A espera luminosa agora combina os pedidos realmente pendentes com os
registros `IsStartup` do modelo nativo do KDE. O retorno rápido do auxiliar
não encerra um startup ainda observado. O LED alterna a cada 500 ms, como
`waitingBlinkRate` no manual do VUE 2.01; o cursor de espera usa o pacote de
cursores escolhido. Nenhum clique é adiado. A cauda opcional permanece
desligada por padrão e, quando habilitada, começa somente após o último
pedido/startup pendente, sem prolongar o cursor.

Passaram **45/45** verificações de controlador/renderização e **50/50** da
bandeja. O primeiro conjunto inclui concorrência, perda/destruição do
provedor, prioridade do cursor e ausência de repintura ociosa. Os casos de
startup desse ensaio usam um modelo explícito de teste; o lançamento real
do auxiliar usa um processo marcador privado. Portanto, esses resultados
não comprovam por si só a notificação de startup de um aplicativo KDE real.
A primeira tentativa isolada dessa integração expirou em 60 segundos e foi
preservada como inconclusiva, com limpeza dos processos próprios. Recibo:
`.qa-domainos-activity-native-20261010/FINAL-RECEIPT.json`.

Na VM SR10.4, um lançamento válido mostrou alternância do LED e o fim
da espera ao aparecer o cliente, depois de 4,878 segundos emulados. A
ampulheta estava na posição do ponteiro; não se comprovou substituição do
bitmap de cada botão nem iluminação sincronizada de toda a faixa metálica.
A adaptação conserva o amarelo autorizado para o LED e a luz do pager.
A limpeza fechou apenas o diálogo aberto durante a observação, sem aplicar
configurações. O MAME manteve captura solta, frameskip 4 e throttle
desligado. Recibo da limpeza:
`.qa-domainos-led-gtk-correction-20261010/VM-OWN-DIALOG-CANCEL.json`.
