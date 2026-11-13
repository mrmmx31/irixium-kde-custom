
## Retomada da fila e proposta de limpeza (2026-10-12)

A comparação I220 foi repetida na sessão Apollo existente. O estado inicial do
gancho era `captured=false`; usei sua recaptura normal e confirmei `captured=true`,
mas movimento do host não alterou os contadores Apollo. Um clique esquerdo no
File do Help Viewer e F10 pela fila de teclado existente também não mostraram
mudança de menu. Como o snapshot nativo não confirmou o alvo do cursor, parei sem
movimento relativo estimado. Depois restaurei o gancho ao estado liberado inicial;
nenhum botão/callback ficou ativo e a fila de teclas está vazia. Frameskip4,
sem throttle e pausa; ponte sem pendências. Foco do host voltou à Xephyr `:301`.
Pressionado/solto e paleta continuam sem evidência. Recibo privado:
`/home/lsi/tempia/board/tmp/i220-native-receipt-20261012.json`.

I188 foi revalidada com 43/43 hashes de origem e arquivo iguais. Adoção da área
de Tema/Laboratório depende da responsável desse trabalho; estado atualizado para
espera, sem fechamento técnico integral.

O Q102 pediu uma proposta de limpeza com preservação das versões recentes e uma
demanda para autorização. A auditoria atual rechecando as 43 árvores de I186
confirmou igualdade com o arquivo histórico. Das 18 árvores de fontes/versões,
a proposta preserva as três mais recentes e enumera 15 mais antigas; os demais
25 artefatos ficam fora. Isso representa 5.671 entradas e 45.767.188 bytes
lógicos, sem afirmar recuperação equivalente de espaço. Não foi feita exclusão.
A leitura de descritores de processo teve 257 lacunas de permissão e, apesar de
zero referências observadas nos alvos, nenhuma ausência de uso é comprovada até
que uma checagem completa possa ser feita. I266 foi inserida após Q102, com
escopo integral, hash de manifesto
`f428221b2b3fc713127a6d57b3241490efceb599300926f63dc134e26d91ee7d`, e sem
autorização salva. Mesmo após autorização, qualquer lacuna futura bloqueará
remoção. Artefatos privados em `/home/lsi/tempia/board/cleanup-authorization-20261012/`.

Para permitir esse escopo explícito no modelo, o CLI agora cria demandas por
arquivo JSON UTF-8 `{title, body}`; `body` define o escopo e a nova demanda
continua sem autorização. Rejeição de estrutura inválida conserva o estado.
`make build/work-board`, 19 testes de persistência e `make check` passaram.
Build atual SHA-256 `7f815af890076c3bdf49b6ca6537a47103ed54fb7ce940a57d74c818a4177055`;
recibo `docs/VALIDACAO-CLI-INSERCAO-DEMANDA.json`. O preview Xephyr segue ativo
com dados sintéticos e a janela pessoal permanece fechada.


## Prancheta produção — atualização 2026-10-12

A versão de produção do AI Work Board foi recompilada, executada e reaberta após
um SIGSEGV no processamento de uma pressão de botão em menu Motif. O primeiro
core termina em `_XmMenuPopDown` e não identifica o menu, o botão ou o alvo; a
causa funcional permanece em Q279. SQLite `integrity_check` passou; estado e
journal foram preservados em cópias privadas. `make check` e `make check-editing`
passaram em testes privados. A GUI voltou aberta no PID 418554; o recibo de
produção está em `docs/VALIDACAO-I269.json` no repositório ai-work-board.

Q102r155 esclareceu que “Desconsidere” foi engano e que devo manter o foco; Q102
é o bate-papo. Q300 foi encerrada como esclarecida. A ideia de orientação lógica
para casos simples foi registrada em Q301, sem implementação. O pedido de
operador NOT em I299 aguarda Q302; o fluxo de checklist documental distinto de
I298 está separado em I303, sem autorização.

I217 permanece sem comparação pressionado/solto: Four segue sem alvo de cursor
guest estável; nenhuma entrada nova foi enviada à VM nesta retomada. I218 aguarda
Q290/Q291; I270 aguarda Q279; I280 aguarda Q285; o título local I247 aguarda
Q282. I240 e I253 mantêm suas dependências e autorizações próprias. Não interagi
com a Xephyr :61 nem com T04 da outra IA. Marco compilação/abertura da produção:
100%, baseado em build, hashes, PID e captura privada; estabilidade do menu e
conclusão da fila permanecem abertas. Nenhuma porcentagem é atribuída à
fidelidade visual.


## Prancheta produção — atualização I270 2026-10-12

Q102r159 foi respondida na aplicação. I270 permanece autorizada e em
andamento. A correção do popup esquerdo e dos menus Motif passou o teste
privado de clique direito dentro/fora, cascatas, checkbox, Fechar explícito e
clique esquerdo fora. `make all`, `make check` e `make check-editing` passaram.
Produção reaberta no PID 436724 (SHA-256
`c0736b94e674072fd9a899049438a691d39e438ff3ed2480789d10ca595c476f`); a
janela e o rascunho recuperado estão visíveis. SQLite `integrity_check=ok`;
backup privado em `/home/lsi/tempia/board/i270-left-popup-20261012/production-before-final-install/`.

Próximo: tratar/verificar o comportamento de arraste ao lado do X em Visualizar
e revisar os outros menus na produção sem tocar no rascunho atual. Build e
abertura da produção concluídos por hash, PID e janela visível; I270 continua
aberto, sem percentual de fidelidade visual.

Q304 pergunta na produção qual é a barra junto ao X que deve atuar como alça
de arraste; aguarda resposta antes de mexer nesse controle. Q102r161 localizou
I222 como a implementação da busca (I219 só entregou o menu). I222 já está
autorizada em r1 e ficou na fila atrás de I270, com escopo de Q213r1: títulos,
notas e respostas das demandas da prancheta atual. O checkpoint mais recente
do banco/rascunhos está em
`/home/lsi/tempia/board/i270-left-popup-20261012/production-current/`.
Q102r162 confirmou manter essa ordem. A captura atual mostra I270 destacado na
lista e I305 no painel de detalhes; deixei ambos e o rascunho sem alteração e
avisei a pessoa para conferir.


## 2026-10-13 — Q323, Xephyr e I316

Q323r1 foi reconhecida e encerrada após a pessoa pedir uma demanda separada para
avaliar uma forma temporária e reversível de configurar a regra da TAP. I325 foi
criada depois de Q323 como proposta sem autorização; o escopo exige inventário
de um método já disponível, rollback e verificação, sem instalação ou mudança
de firewall. I287/I253 permanecem aguardando esse método; não houve listener,
Vuewm nem alteração de rede. T04 e Xephyr :61 da outra IA continuam intocadas.

I217: a recaptura controlada e um passo relativo adicional não confirmaram o
ponteiro guest sobre Four. Nenhum clique foi enviado. Capture/mouse voltaram ao
estado liberado, VM despausada em frameskip 4 sem throttle, bridge e teclado sem
pendências. Recibo `ai-work-board/docs/VALIDACAO-I217-PAGER-RECHECK-20261013.json`;
capturas privadas em `/home/lsi/tempia/board/i217-current/`.

I316: Q318r1 autorizou prosseguir com o desligamento. A combinação documentada
Ctrl+Shift+F11 não retornou ao DM, mesmo com o MAME focado; setas do teclado
virtual foram recebidas, mas a combinação específica não teve efeito. Parei sem
`shut`, sem fechar MAME e sem copiar disco. A VM continua no VUE; o perfil e a
entrada estão limpos. Recibo `ai-work-board/docs/VALIDACAO-I316-SHUTDOWN-20261013.json`;
evidências privadas em `/home/lsi/tempia/board/i316-backup-base-20261013/`.
Próximo: avançar para a próxima demanda autorizada independente, mantendo I217,
I287 e I316 em espera até surgir método observável ou resposta própria.

## 2026-10-13 — validação I124 e coordenação Q165

A validação offline dos alvos já existentes do Theme Lab passou: modelo, armazenamento,
sessão transacional e prova do controlador (`check-project-history`,
`check-project-history-store`, `check-project-session`,
`check-project-history-controller`). O recibo I119 confirma histórico do projeto
separado do journal textual e dos dados da Work Board. Q165 está encerrada na
revisão 2; inventários conjuntos, script de migração e cálculo de transferência
foram destinados a proposta futura após o limite de 200 itens. A produção atual
não contém I124/Q165 como tarefas; Q102 continua o canal ativo. Nenhum rascunho,
resposta, interface :61 ou autorização foi alterado. Recibo da validação:
`docs/VALIDACAO-I124-20261013.json` no repositório do tema. Progresso técnico
estimado de I124: 100%, baseado nos testes específicos e no recibo I119; avaliação
humana permanece separada. Próximo: aguardar novas mensagens por Q102 e seguir a
fila de trabalho ativa sem misturar os históricos.

## 2026-10-13 — I297 e recompilação da produção

I297r1 foi expandida no catálogo offline `~/tempia/domainos-vue-study/catalog/`: registra hashes/proveniência dos três recortes push-buttons existentes, estado observado e lacunas pendentes; notas por família/recorte ficam em localStorage, preservam a marcação legada e podem ser exportadas manualmente. A edição foi validada em Xephyr :62 com texto UTF-8 multilinha, seleção/substituição, Undo/Redo, atalhos Ctrl+Z/Y/Shift+Z e Ctrl+C/V/X/A, menu Editar, salvar, alternar alvo, recarregar e export JSON schema 2. Recibo: `~/tempia/domainos-vue-study/receipts/i297-catalog-editor-xephyr-20261013.json`. Não houve envio automático ou alteração do armazenamento pessoal do navegador. Outras famílias/estados continuam pendentes e não foram inferidos dos recortes estáticos.

A versão de produção do AI Work Board foi recompilada com `make -B build/work-board` (SHA-256 `f98ee4429607bd678b819d6223ce3baadc82ff77ba6f0e55162ba58c466e124f`, igual ao executável anterior). `check-draft-review`, `check-draft-review-native`, `check-editing`, cobertura de recursos de texto e `check-i308` passaram. A instância antiga fechou por WM_DELETE normal e a nova foi iniciada sobre o mesmo SQLite, PID 1056630, na sessão :1; `PRAGMA integrity_check=ok`. A interface mostra I273 e mantém o controle Recuperar rascunhos; nenhum texto de rascunho foi lido ou alterado. Q102 seq.64 informa que a pessoa já pode responder às perguntas pela aplicação. I297 fica tecnicamente concluída; avaliação humana continua separada.
## 2026-10-13 — I217 rechecagem de cursor e limite do perfil

A nova captura nativa ainda mostra Three selecionado e Four visível, sem cursor guest
confirmado sobre Four. Nenhum clique, movimento ou mudança de foco foi enviado nesta
tentativa; o estado permaneceu `captured=false`, sem fila pendente, e a VM observada
está despausada em frameskip 4 e sem throttle. Contudo, os argumentos do processo
MAME existente incluem `-frameskip 10`, divergindo do estado medido e do perfil
registrado. Preservei a VM e parei antes de intervenção gráfica. I268 não foi
executada porque sua condição de clique único exige o alvo visível confirmado.
Recibo complementar `ai-work-board/docs/VALIDACAO-I217-PAGER-RECHECK-20261013B.json`;
captura privada em `/home/lsi/tempia/board/i217-current/cli-recheck-20261013T1840Z/`.
Próximo: aguardar método de posicionamento guest verificável e resolver a divergência
de perfil por fluxo autorizado antes de novas entradas gráficas. Progresso técnico
de I217: 0% da comparação pressionado/solto, com base na ausência de alvo confirmado;
nenhuma fidelidade visual foi inferida.


## 2026-10-14 — I295 Pager estático e interrupção I217/I268

I295 recebeu três recortes estáticos do Pager (grade One–Six, Three realçado
visualmente e face de Four), todos em escala 1:1 com coordenadas, dimensões,
hashes, fonte e recibo. A captura nativa prévia mostra `captured=false`, sem pausa,
sem throttle e frameskip 4. A imagem não prova seleção/foco nem transições; nenhum
clique foi enviado. O catálogo HTML agora apresenta os recortes de botões e Pager,
preservando IDs e formato de notas; JavaScript passou `node --check`, HTML passou
parser e os três PNG retornaram HTTP 200. A seção Three/Four foi inspecionada em
Chrome de perfil isolado no Xephyr :62. Evidência e recibos em
`/home/lsi/tempia/domainos-vue-study/controls/tabs-pager/README.md`,
`receipts/i295-pager-static-20261014.json` e
`receipts/i297-update-i295-recuts-20261014.json`. I295 segue aberta para estados
interativos e outras famílias.

Na tentativa de I217/I268, a movimentação do ponteiro do host foi interrompida
antes de haver retorno da captura nativa correlacionada (`f2127393cf7642a4896dceae1977ea71`). Não houve clique/tecla. O arquivo de comando pendente foi preservado, sem reenvio ou edição; após a atualização da sessão, MAME e janela de produção já não existem e o XID salvo expirou. O ponteiro host foi restaurado à coordenada salva; não reiniciei a VM nem acessei :61/T04. Recibo `ai-work-board/docs/VALIDACAO-I217-PAGER-INTERRUPT-20261013.json`. I217/I268 ficam pendentes até sessão e resposta observável disponíveis.

A build de produção I273/I308 foi compilada e executada antes da sessão ser
atualizada; seu hash é `5c51fff5b42cb7961e9c9fd0d35b1f34e1cd6583f34733a8a6caebb567c8b834`.
Os testes de revisão de rascunho, edição, I308, notificações e navegação passaram;
SQLite `quick_check=ok`. O journal pessoal permaneceu com o hash
`fd526eeb37db294cb4fb41d049dfc35cfffbb499357a60c21f6acd059d2596ed`; seu conteúdo
não foi lido ou alterado. A instância de produção não foi reaberta; a GUI sintética
foi mantida separada. Recibo `VALIDACAO-CONTINUIDADE-I273-I308-20261014.json` no
projeto AI Work Board. Q327 tem resposta “2” reconhecida; Q328/Q329 continuam sem
resposta. Próximo: continuar tarefas autorizadas sem VM, e retomar prova nativa
somente quando a sessão original estiver disponível e segura.

## 2026-10-13 — produção aberta para respostas; teste nativo GTK2 inconclusivo

A build de produção AI Work Board foi revalidada pelo hash
`5c51fff5b42cb7961e9c9fd0d35b1f34e1cd6583f34733a8a6caebb567c8b834` e está
visível em :1 (PID 1279760). Q102 recebeu atualização na sequência 73, indicando
que Q328–Q330 estão disponíveis para resposta. Após abrir a aplicação, o hash do
journal de rascunhos passou a `2483b6ecd8184386282b1d24f5dd405e42933f0f7792562992bd5b6a372b0288`;
não li seu conteúdo nem acionei recarga, para preservar possível digitação.
Q328, Q329 e Q330 ainda estavam sem resposta na última leitura.

No laboratório, `make build/theme-lab` passou. O teste de rota GTK2 e testes
puros relacionados passaram na sessão anterior, mas a nova prova pública
`test_gtk2_public_native.py` não concluiu: a janela não foi encontrada por
`xdotool`; o log do namespace registra limite de inotify (“Too many open files”).
Não considero a comparação nativa repetida aprovada. Xephyr :62 segue viva e
sem janelas; T04/:61 não foi acessada. I217 e I316 continuam dependentes da VM
original, I295 não pode avançar para recortes interativos sem a captura nativa,
e I240 continua sem método administrativo disponível. Próximo passo: aguardar
respostas na produção sem tocar no journal e retomar somente o item independente
que permaneça autorizado e executável.

## 2026-10-14 — rascunho recuperado em Xephyr :62

Na build de produção aberta em Xephyr :62 com `examples/checklist.json` e estado
privado sintético, colei texto UTF-8 de dois parágrafos. O autosave mostrou
proteção em disco; Ctrl+Z e Ctrl+Y removeram/restauraram o texto; trocar T01→T02→T01
preservou o rascunho. Fechamento normal via WM_DELETE e nova abertura recuperaram
o valor, sem alterar resposta salva, revisão ou autorização. Clipboard confirmou
o texto reconstruído; a captura posterior à reabertura mostra o conteúdo completo
sem interação. Um primeiro quadro vazio não se repetiu após recriar :62 e está
registrado como ocorrência transitória, sem correção de código inferida. Nenhum
dado pessoal foi usado, e a produção em :1 permaneceu aberta e intocada.
Recibo com hashes e capturas: `/home/lsi/tempia/board/work-board-xephyr-synthetic-20261014/receipt.json`;
captura final `draft-reopen-unfocused.png` SHA-256
`2cad607d6d366c9567038f0c4bf1cec08ef7d966feff06803985dd9e9e40d3d8`.
I298 permanece tecnicamente coberta por esta prova sintética; avaliação humana
continua pendente. Próximo: continuar monitorando Q102 e manter a revisão de VM
parada até a sessão MAME estar disponível.

## 2026-10-13 — recompilação de produção para respostas Q102

Após o pedido para liberar respostas somente com a produção compilada e aberta,
`make -B --jobs=4 build/work-board build/kde-colors` terminou sem erro no projeto
AI Work Board. O binário gerado e o processo de produção PID 1346206 em :1 têm
SHA-256 idêntico `5c51fff5b42cb7961e9c9fd0d35b1f34e1cd6583f34733a8a6caebb567c8b834`;
a janela foi confirmada visível. Mantive essa instância aberta para não
interromper digitação. A atualização foi enviada ao canal Q102 na sequência 81;
Q328/Q329 continuam disponíveis para respostas. Não li nem alterei o journal
pessoal. A prova de edição/rascunhos sintéticos previamente registrada continua
com seu escopo e hash originais; este marco comprova a recompilação e execução,
não acrescenta nova prova de entrada de texto. Próximo: seguir as tarefas
autorizadas independentes e aguardar respostas pelo Q102. Avanço deste requisito
de disponibilidade: 100%, baseado na build concluída, hash do processo ativo e
janela visível; não representa porcentagem de fidelidade visual.

## 2026-10-13 — rascunhos confirmados em Xephyr :62

A prova manual sintética foi refeita após corrigir a preparação do clipboard:
com o proprietário ativo, os dois parágrafos UTF-8 foram colados e protegidos
em disco; Undo/Redo, troca T01→T02→T01 e reabertura normal recuperaram o mesmo
rascunho. A resposta salva continuou vazia, revisão 0 e sem autorização. A primeira
Xephyr :62 deixou de responder a consultas X11; copiei o estado sintético,
reiniciei apenas :62 e concluí a prova. Nenhum dado pessoal foi lido/alterado,
nem produção, VM, T04 ou :61 foram reiniciados. `make --jobs=4
check-draft-review check-draft-review-native check-editing` passou, incluindo
12 invariantes. Recibo completo:
`/home/lsi/tempia/board/work-board-drafts-recheck-20261013/receipt-manual-verification.json`.
Nenhuma alteração de código ou demanda duplicada foi necessária; I298 já é
tecnicamente coberta. A produção segue ativa com hash `5c51fff5…67c8b834`.
Q102 recebeu o resultado na sequência 82; não havia resposta da pessoa depois
dessa sequência na última leitura. Próximo: acompanhar Q102; I217,
I295 e I316 aguardam uma sessão MAME; I240/I253 aguardam método de rede e
privilégio; I266 espera o retorno do scanner; Q328/Q329/Q327 mantêm as decisões
pendentes. T04 e a seção de trabalho da outra IA permanecem fora do escopo.

Revalidei em 2026-10-13: :62 responde a consultas X11 e mantém a janela
sintética; produção :1 segue no hash esperado. Não há processo MAME. O processo
atual não tem CAP_NET_ADMIN efetivo, `sudo -n -l` exige senha e os CLIs de
firewall/captura seguem ausentes. Q102 não tinha resposta após seq.82; enviei a
constatação na seq.83. As demandas autorizadas restantes continuam em espera
pelos gates listados acima; não há outra tarefa `section=board` executável sem
resposta ou mudança externa. Próximo: acompanhar Q102, preservando :62 e a
produção abertas para as próximas interações.

## 2026-10-13 — produção aberta e I273 disponível para avaliação

Revalidei a execução solicitada: produção PID 1386952 em :1, janela mapeada
1920×951, executável SHA-256
`5c51fff5b42cb7961e9c9fd0d35b1f34e1cd6583f34733a8a6caebb567c8b834`. Q102
está na sequência 84; ainda não há resposta nova da Pessoa. Atualizei somente
`assistant.reply` de I273 revisão 2 para indicar que o painel está disponível
na janela, preservando nota, avaliação e autorização. Recibo da execução:
`docs/VALIDACAO-I273-PRODUCTION-RUN-20261013.json`; provas funcionais e de
edição permanecem no recibo de integração original, com seu escopo próprio.

A fila autorizada continua sem outra demanda executável: I217/I295/I316 precisam
de sessão MAME; I240/I253 e subetapas precisam de método de rede/privilégio;
I266 aguarda o resumo do scanner; I305/I296/I303/I324 aguardam Q328/Q329/Q327;
I188 depende da responsabilidade compartilhada; I212 aguarda avaliação. Xephyr
:62 e produção :1 permanecem abertas. Avanço de disponibilidade para respostas:
100%, baseado em hash, processo e janela visível; não mede aceite nem fidelidade
visual. Próximo: acompanhar Q102 e executar a primeira demanda liberada por uma
resposta salva ou por retorno de dependência externa.

## 2026-10-13 — produção aberta e I273 disponível para avaliação

Revalidei a execução solicitada: produção PID 1386952 em :1, janela mapeada
1920×951, executável SHA-256
`5c51fff5b42cb7961e9c9fd0d35b1f34e1cd6583f34733a8a6caebb567c8b834`. Q102
está na sequência 84; ainda não há resposta nova da Pessoa. Atualizei somente
`assistant.reply` de I273 revisão 2 para indicar que o painel está disponível
na janela, preservando nota, avaliação e autorização. Recibo da execução:
`docs/VALIDACAO-I273-PRODUCTION-RUN-20261013.json`; provas funcionais e de
edição permanecem no recibo de integração original, com seu escopo próprio.

A fila autorizada continua sem outra demanda executável: I217/I295/I316 precisam
de sessão MAME; I240/I253 e subetapas precisam de método de rede/privilégio;
I266 aguarda o resumo do scanner; I305/I296/I303/I324 aguardam Q328/Q329/Q327;
I188 depende da responsabilidade compartilhada; I212 aguarda avaliação. Xephyr
:62 e produção :1 permanecem abertas. Avanço de disponibilidade para respostas:
100%, baseado em hash, processo e janela visível; não mede aceite nem fidelidade
visual. Próximo: acompanhar Q102 e executar a primeira demanda liberada por uma
resposta salva ou por retorno de dependência externa.

## 2026-10-13 — I316 aguarda confirmação do desligamento

I316r3 continua autorizada para produzir o ZIP-base, e Q318r1 autorizou o
procedimento de desligamento. A resposta anterior, porém, registra que o retorno
ao DM falhou e que `shut` não foi enviado enquanto o MAME ainda estava no VUE.
Agora não há processo MAME e `fuser` não apontou dono aberto para o disco ativo;
a ausência de processo não comprova desligamento limpo. Como o manual 10.2 exige
confirmação de `shut` antes do backup consistente e a skill de controle cobre
somente uma sessão existente, não reiniciei a VM e não criei o ZIP. Q331 foi
criada após I316, sem autorização própria, para confirmar desligamento posterior
ou pedir autorização específica para relançar e encerrar pelo procedimento.
Recibo: `docs/VALIDACAO-I316-BACKUP-GATE-20261013.json`. Próximo: aguardar Q331;
I217/I295 também aguardam sessão MAME. Nenhum backup histórico foi alterado.

## 2026-10-14 — pedido MAME de I217 ainda sem resposta

O status somente-leitura de `mame_control.py` confirmou que o pedido
`f2127393cf7642a4896dceae1977ea71`, já registrado como pendente por I217/I268,
continua sem resposta e sem ack. Não sobrescrevi `command.lua`, não repeti a
entrada e não reutilizei resultado antigo. Nenhum processo MAME está ativo;
I217/I268 não têm prova nativa correlacionada e I295 segue sem captura dinâmica.
Recibo: `docs/VALIDACAO-I217-MAME-PENDING-20261014.json`. Q102 sequência 87
registra o gate; Q331 trata separadamente a confirmação de desligamento para o
backup I316. Próximo: aguardar resposta/retorno do canal pendente e Q331.

Clarificação em Q331: a opção de relançamento não libera reutilizar, repetir ou
sobrescrever o comando pendente de I217. Se o `shut` exigir outro canal de
controle, esse método será verificado em demanda/pergunta própria antes de
qualquer entrada no guest.

## 2026-10-14 — rechecagem após Q102 seq.88

Q331 continua sem resposta (revisão 0, autorização false); I316r3 permanece
aguardando confirmação de desligamento ou autorização específica de relançamento.
O pedido MAME f212 de I217/I268 segue sem reply/ack; não existe processo MAME.
Produção PID 1386952 e Xephyr :62 continuam ativos. I266 aguarda o resumo do
scanner; I305/I296/I303/I324 aguardam Q328/Q329/Q327; I212/I273 aguardam
avaliação; I188 permanece parcial pela responsabilidade compartilhada.
Não encontrei tarefa autorizada independente pronta para executar. O próximo
avanço depende dessas respostas ou de uma sessão MAME válida. Avanço verificável
desta rodada: disponibilidade de produção comprovada e I273 oferecida para
avaliação; nenhum progresso visual é inferido desses estados.

## 2026-10-14 — I295: boot retomado, FrontPanel ausente

A sessão MAME privada :68 alcançou o login de Domain/OS SR10.4. O salvage
terminou com sucesso e relatou três flags VTOC em logs/temporários e cinco
objetos sem catálogo; não fiz reparos nem limpeza. O login documentado `user`
chegou a um Pad com linha Command, mas a captura atual não contém FrontPanel,
Help Viewer ou scrollbar VUE para observar estados dinâmicos. O helper de teclado
terminou com fila vazia e nenhuma tecla pressionada. Não alterei configurações
nem paleta. Iniciar `vuewm` em Xephyr permanece bloqueado por I287: a regra TCP
restrita da TAP exige privilégio administrativo que não está disponível. I325
registra um método candidato e rollback, sem autorizar a aplicação da regra.
I295 fica parcial, aguardando um método de X/FrontPanel autorizado e executável.
Recibo e hashes: `~/tempia/board/i295-live-20261014T0150Z/receipt-login-block.json`.
Nenhuma fidelidade visual dinâmica é estimada a partir desta captura.

## 2026-10-14 — rascunhos e I316

Reproduzi em fixture sintética a perda de uma edição confirmada no widget
quando o processo terminava antes do timeout de 200 ms. O checkpoint agora é
síncrono no evento de edição; a candidata preserva a tecla após SIGKILL e os
12 fluxos nativos de edição passaram. A fonte oficial foi atualizada, mas não
substituí a produção, que está visível para respostas. Colagem UTF-8 de 3.648
caracteres manteve ~40 ms; burst artificial de 96 teclas levou ~106 ms a mais.
Recibo: `ai-work-board/docs/VALIDACAO-DRAFT-DURABILITY-20261014.json`.

Na sessão MAME :68, o segundo `shut` foi digitado na linha Command visível e
submetido uma vez. As capturas ficaram pretas sem mostrar `SHUTDOWN SUCCESSFUL`;
MAME continua ativo com o disco aberto. Não repeti a mutação nem criei o ZIP.
Q332 segue pendente. Recibo: `domainos-mame-lab/docs/VALIDACAO-I316-SHUT-20261014.json`.


## 2026-10-14 — I316, backup e retorno à fila

A captura passiva da ponte, conferida visualmente, mostra `BEGINNING SHUTDOWN
SEQUENCE...` e `SHUTDOWN SUCCESSFUL`; hash `c340d205423e80c5cc55f2c7830eb58670eec87c7becd905c46177ca366d9f80`.
A ponte estava sem pendências e a máquina sem pausa; fechei a janela por WM_DELETE,
confirmei processo encerrado e disco liberado. ZIP novo em Downloads:
`DomainOS-SR10.4-backup-base-20261014.zip`, 16 arquivos, `unzip -t` aprovado;
SHA-256 `fa79d20bf59c8dc28d7a9893186085411dca29c0650ea7dbea4739c0ea54206c`.
Restauração ainda não testada. Recibo no domainos-mame-lab.

I295 continua parcial: a sessão mostrou Pad/linha Command, sem FrontPanel nem família
VUE disponível. I287 segue bloqueada pela regra temporária da TAP sem privilégio;
nenhuma alteração de rede foi aplicada. Próximo item autorizado executável passa a
ser I167 (GTK2), uma família por vez; T04 e :61 permanecem alheias a este trabalho.


## 2026-10-14 — Prancheta de produção reaberta

Atendendo à condição para responder às perguntas, fechei a instância anterior por
WM_DELETE, compilei a fonte corrigida (`make -B --jobs=4 build/work-board
build/kde-colors`) e reabri a versão de produção, PID 1491642, com os mesmos
arquivos e preferências. Hash do binário
`101ab92339b0185b7824ecc61845706c4f11bb4413b9072ba7bd206f005402f2`; banco
SQLite íntegro. `make check-editing` e `tests/test_draft_durability.py` passaram;
rascunho fixture confirmado em 6–10 ms, persistido antes de SIGKILL e recuperado.
Nenhum conteúdo do journal pessoal foi inspecionado. Captura da interface e perguntas
visíveis: `~/tempia/board/production-20261014/work-board-production.png`, SHA-256
`e217c52bf059e961f59b201053a755b4f954445eb4b9fbd2bb41fd7bebefeac0`. Q102 foi
atualizado com este estado. A fila seguinte da Prancheta aguarda retorno: I217/Q268
precisa de decisão sobre o Pager; I303/I324 esperam Q327, I305 espera Q328 e I296
espera Q329. I295 é parcial, bloqueada por privilégio da TAP; I240/I253 também
aguardam decisão/acesso. Não há outra implementação de prancheta autorizada e
independente executável neste momento. T04 e :61 não foram acessadas.

## 2026-10-14 — produção pronta para resposta; I295 no FrontPanel

A versão oficial foi recompilada com `make -B --jobs=4 all kde-colors` e abriu
pela raiz de `ai-work-board`. Janela visível “AI Work Board — Prancheta de
projetos”, PID 1510609; SHA-256 de `build/work-board`:
`101ab92339b0185b7824ecc61845706c4f11bb4413b9072ba7bd206f005402f2`.
Q102 revisão 191 foi atualizada com esse estado; Q333 continua aguardando a
resposta da pessoa sobre o menu de Preferências. Não inspecionei o conteúdo do
journal pessoal.

I295 retomou em MAME :68, PID 1496409. O VUE terminou de abrir sozinho e agora
há File Manager, Terminal e FrontPanel visíveis. Recorte ao vivo do Pager
Four–Six, 1:1, `[351,739,678,768]`, corresponde exatamente à fonte. Fonte
1024×844 inclui 44 px de artwork; a tela Apollo medida é 1024×800. Fonte e
recorte estão em `~/tempia/domainos-vue-study/captures/2026-10-14/` e
`controls/tabs-pager/`; recibo
`~/tempia/domainos-vue-study/receipts/i295-live-frontpanel-20261014.json`.
Existem recortes estáticos das oito famílias no acervo, mas isso não comprova
os estados transitórios.

I295 avançou por teclado Apollo: Alt+V abriu a cascata View; uma seta para baixo
deixou visível o realce em Select All, sem ativá-lo; Escape fechou o menu. As
capturas completas (aberta, realçada e fechada) e o recorte 1:1 estão em
`~/tempia/domainos-vue-study/captures/2026-10-14/` e `controls/menus/`; recibo
`~/tempia/domainos-vue-study/receipts/i295-live-frontpanel-20261014.json`.
O eixo vertical do mouse continua sem resposta visível, embora o movimento
horizontal tenha funcionado; uma nova sequência de cinco incrementos de Y, um
a cada dez quadros MAME, também não moveu o cursor na imagem. Uma seta para baixo
com View fechado não selecionou um ícone visivelmente; nenhum Enter foi enviado.
O clique do host não recapturou pelo gancho. No fim, a fila Apollo e as quatro
máscaras do teclado estavam zeradas; botão do mouse solto, callback concluído e
sem pedido MAME pendente. Não alterei opção nem paleta. Estimativa do escopo:
oito famílias têm espécimes estáticos e uma cascata VUE tem captura aberta,
destaque visível e dispensa; I295 permanece parcial porque outros estados
transitórios não foram provados. Isto não é uma porcentagem de fidelidade visual.
Próximo: continuar a coleta de estados com a fila Apollo e investigar a
navegação do mouse separadamente. T04 e Xephyr :61 continuam intocados.

## 2026-10-14 — I295: Help e primeira tentativa de rolagem ao vivo

Complemento ao recibo anterior, sem alteração da configuração da VM. Na tela
SR10.4/HP VUE 2.01, a cascata Help do File Manager mostra On Item, On
Application, On Help, On Keys e On Version. Após uma entrada Ctrl+K pela fila
Apollo, Help Viewer ficou em primeiro plano na página File Manager Keys,
“Lines 1 to 15 of 165”. Com o alvo visível, uma tecla Apollo Roll Down foi
emitida uma vez. O texto e a barra não mudaram visivelmente; os recortes da
barra antes/depois são pixel a pixel idênticos (diferença por canal 0). Isso
registra somente esta tentativa, sem determinar causa ou comportamento de
outras entradas. Recibo: `~/tempia/domainos-vue-study/receipts/i295-live-help-scrollbar-20261014.json`.
Fontes e recortes estão no acervo em `captures/2026-10-14/`, `controls/menus/`
e `controls/scrollbars/`; catálogo e READMEs foram atualizados.

A fila Apollo encerrou o callback após 40 quadros, sem erro; ao conferir,
queue=0, active=false, quatro máscaras de teclado zeradas, botão do mouse solto,
MAME sem pausa e ponte sem pendência. I295 continua parcial: foco semântico,
pressão/soltura, arraste e movimento de rolagem continuam sem comprovação, assim
como estados transitórios de outras famílias. Q102 foi atualizado com este
avanço; Q333 foi posta em espera depois da compilação/abertura inicial da
produção (PID 1510609; a reabertura atual está registrada abaixo). Estimativa do
escopo I295: oito famílias possuem ao menos
espécimes estáticos e a família de menus tem cascata aberta, realce visível e
dispensa; a primeira tentativa registrada de rolagem não mudou pixels. Esta
estimativa mede cobertura de estados e famílias, não fidelidade visual.
Próximo: continuar a captura de estados da scrollbar e depois avançar uma
família autorizada por vez. T04 e Xephyr :61 continuam intocados.

Correção operacional após a validação final (2026-10-14 03:40 UTC): a instância
que havia sido registrada em 1510609 já não estava ativa. Reabri pela raiz de
`ai-work-board/open`; agora o PID confirmado é 1536650 e a janela está visível
em :1. Q102r191 foi atualizado com o PID atual. A compilação/hash
permanece o mesmo; Q333 segue sem resposta.

Pergunta de abordagem Q334 foi criada após I295, ack_revision=0, status
`waiting_user`: escolher se faço uma tentativa isolada com Cursor Down no Help
Viewer visível, se deixo a rolagem pendente e sigo para outro estado autorizado,
ou se indicas outra interação documentada. Nenhuma resposta foi inferida. A
produção está ativa em :1, PID 1536650; Q102r191 foi atualizada com esse PID e
os dois questionamentos pendentes. Responder pela interface; eventual recarga
preserva os rascunhos conforme o protocolo.

Atualização posterior: a produção continua ativa e o executável em memória
corresponde ao build (`101ab92339b0185b7824ecc61845706c4f11bb4413b9072ba7bd206f005402f2`).
`make check-editing` passou 12 invariantes e a recuperação sintética após
SIGKILL (28,4 ms até o checkpoint, resposta salva intacta). `make check-chat`
passou em repetição completa; uma tentativa anterior falhou ao ler uma seleção
X11 transitória. Journal pessoal não lido. I295 acrescentou espécime estático
1:1 dos botões Next View/Previous View; a face mais clara não foi chamada de
desabilitada. Recibo em `/home/lsi/tempia/domainos-vue-study/receipts/`.
Captura passiva adicional: botão Snapshot em recorte 60×60, SHA-256
`c6b34fbddbf3ef175d64f23ef1a6a96de292de530dd32a52b704d44245d4f90c`.
O catálogo passou `node --check` e o recibo passou validação JSON.
I295 segue parcial e Q334 segue aguardando resposta; sem nova entrada na VM.

I217/I268 tiveram uma tentativa revalidada na sessão :68: o alvo Four estava
visível, mas a movimentação XTest não deixou o cursor confirmável sobre ele.
Parei sem clicar, restaurei a coordenada X salva e conferi botões/modificadores
soltos, MAME sem pausa e fila vazia. Pressionado/solto continua sem prova.
Recibo `ai-work-board/docs/VALIDACAO-I217-I268-RECHECK-20261014.json`.
Auditoria estática do acervo I295: 29 entradas e 58 imagens passaram SHA-256,
assinatura PNG, dimensões e geometria 1:1. Isso valida os arquivos, não a
fidelidade histórica ou os estados dinâmicos. Recibo em
`/home/lsi/tempia/domainos-vue-study/receipts/i295-catalog-integrity-20261014.json`.

## 2026-10-14 — I124: persistência de progresso validada novamente

I124r2 autorizada. Recompilei os alvos em diretório privado de `/home/lsi/tempia`
com warnings como erro e repeti `check-project-history`,
`check-project-history-store`, `check-project-session` e
`check-project-history-controller`; os quatro passaram. O controlador Motif real
foi exercitado em Xvfb/bwrap com projeto sintético: Undo/Redo, checkpoint,
recuperação, atalhos separados do editor textual, conflito CAS e falha de escrita
preservaram a proposta; a cena permaneceu igual até Aplicar. Resultado/captura
privados: `/home/lsi/tempia/board/i124-controller-test-20261014/`.
Recibo com hashes atuais: `docs/VALIDACAO-I124-20261014.json`.

I124 está tecnicamente concluída para seu escopo de recuperação separada; isso
não encerra a avaliação humana. Q165r2 continua esclarecida: inventário/script
conjunto e cálculo de transferência são proposta futura própria; I166 não foi
alterada. A VM :68 e Xephyr :61 não foram usadas. Próxima ação segue a fila
atual, sem assumir itens T04 atribuídos à outra IA.

## 2026-10-14 — P02: relógio, fusos e feriados revalidados

P02r1 estava autorizada e o hash da definição coincidiu. A composição privada
atual passou `testar-domainos-instrumentos.py`: 23/23. A captura nativa do relógio
mostra hora local com `America/Manaus (-04)` e linha UTC explícita; a data segue o
locale; o quadro do relógio é separado do calendário. Sem fonte escolhida, o
calendário informa que não há agenda configurada.

A prova do calendário KHolidays Manaus 2026 passou 138/138: descoberta da região
pública no XDG privado, exatamente uma linha nativa para cada um dos 15 feriados,
nove pontos facultativos ausentes e datas fora de 2026 excluídas. A captura mostra
`Aniversário de Manaus`; nenhuma agenda/conta pessoal ou evento sintético foi
usado. Cinco preferências pessoais permaneceram inalteradas, as fontes conferidas
não mudaram e os daemons próprios encerraram. Capturas e relatórios completos:
`/home/lsi/tempia/board/domainos-p02-20261014/`. Recibo com hashes:
`docs/VALIDACAO-P02-20261014.json`.

P02 está tecnicamente concluída nos critérios salvos; a avaliação humana continua
pendente. Não alterei altura da barra, ícones, preferências nem outras famílias.
Próxima tarefa autorizada em estado `queued`: P03 (rede, gr_osview e correio),
sem sobrepor a responsabilidade T04 da outra IA.

## 2026-10-14 — P03: rede, gr_osview e correio conferidos

P03r1 autorizada. Reutilizei o recibo atual de instrumentos (hash coincidente
com o componente): Rx/Tx nativos têm amostras reais e o clique do gráfico carrega
o `gr_osview` existente no quadro suspenso. Não repeti esse ensaio inalterado.
Para o correio, a configuração da instância seleciona `thunderbird.desktop` e
`mailCountsEnabled=true`; o padrão mailto também é Thunderbird. Registro do host
nativo e XPI preparado estão presentes, mas não havia processo host conectado.
Não consultei perfil, conta ou mensagens pessoais; portanto a instalação/ativação
da extensão no perfil não foi afirmada.

No ensaio privado do painel, os 18 checks de estado da contagem passaram: valores
conhecidos, indisponibilidade como traço, EOF/crash sem badge obsoleto e recuperação.
Os checks de lançamento de correio explícito e padrão também passaram. O runner
ampliado terminou `failed` por oito checks auxiliares de `xman`/paleta fora do
escopo P03; as janelas foram observadas, mas o teste não confirmou processos e
pixels esperados. Isso fica registrado e não foi convertido em evidência positiva.
Recibo detalhado e artefatos: `/home/lsi/tempia/board/domainos-p03-20261014/`
(`VALIDACAO-P03-20261014.json`).

P03 está tecnicamente conferida para seus dois critérios; avaliação manual pendente.
Próxima tarefa autorizada: P05 (seleção, Operações e pin temporário). I295 segue
parcial: o mesmo pedido de leitura `4260854bc6024f04a92238d48a3cd4c7` ainda não
tem resposta correlacionada; uma captura passiva confirma o Help Viewer atual,
sem entrada enviada. I253 continua dependendo do método privilegiado da I287;
I296 espera Q329. T04 e Xephyr :61 permanecem com a outra IA.

## 2026-10-14 — P05: seleção, Operações, pin e Unpin revalidados

P05r1 autorizada. Como a Iconbox mudou desde os recibos anteriores, usei a prova
Wayland privada atual com hashes da fonte correspondente. Os 65 checks passaram:
checkbox em grupo e janela individual, acumulação/reabertura da seleção, abertura
de Operações, ações no conjunto, pin na ordem escolhida, menu contextual direito
com Unpin como primeira ação e retorno da janela ao grupo exato. As janelas não
selecionadas e seus estados permaneceram intactos; os hashes das preferências
pessoais guardadas foram iguais antes/depois. Nenhum perfil ou janela pessoal foi
usado. Artefatos em `/home/lsi/tempia/board/domainos-p05-20261014/`; recibo
`docs/VALIDACAO-P05-20261014.json`.

P05 tecnicamente concluída; a nota da pessoa reserva a verificação no perfil
pessoal para quando ela estiver presente. Próxima autorizada: P06 (Pager e áreas
de trabalho). A avaliação de P05 continua pendente e não bloqueia essa tarefa.

## 2026-10-14 — P06: Pager e áreas de trabalho revalidados parcialmente

P06r1 autorizada e reconhecida. A prova focada de nomes/quantidade passou 93/93;
a ativação geométrica em KWin/X11 privado passou 41/41, incluindo janela inativa,
restauração, troca de área, foco e rejeição de identidade obsoleta. O ensaio
completo passou 87 verificações; a única falha substantiva foi o popup de
renomeação medir 82 px frente a 82,8 px implícitos num host artificial de 109 px.
As flags de conclusão do runner também ficaram falsas em consequência da asserção.
Sem ajuste de código: esse delta fracionário permanece registrado para eventual
avaliação autorizada. O recibo e hashes estão em
`docs/VALIDACAO-P06-20261014.json`; relatórios e capturas privados em
`/home/lsi/tempia/board/domainos-p06-20261014/`.

A nota salva em P06 torna P08 requisito para concluir o critério da luz do Pager;
nenhuma aprovação manual foi inferida e as provas de luz deste ensaio não fecham
essa dependência. Próxima etapa autorizada independente: P07 (bandeja, excedentes
e notificações). Registrar a captura manual quando a pessoa voltar à produção.

## 2026-10-14 — P07: bandeja e provedores revalidados parcialmente

P07r1 continua autorizada. A repetição independente do ensaio da bandeja nativa
passou 42/42; a primeira execução teve três falhas de inicialização de SNI/ocultos
que não se repetiram. Textura ocupada/vazia e retorno do slot passaram 28/28;
popups nativos de status/excedentes passaram 18/18. A prova de roda 121/121 foi
reutilizada porque os hashes de `DomainOSTray.qml`, `DomainOSPopupWheel.qml` e do
encaminhador nativo coincidem. Escopo XCB/Qt 6.8.2 e áudio simulado, sem prova de
Wayland ou dispositivos/contas pessoais.

A lista de ordem permanece defeituosa: 14/43 gates falharam; 13 comportamentais
decorrem da lista vazia no ConfigView, cuja instância ID4 não tem o
`internalAction` do applet proprietário ID3. O teste também registra erro do
`Kirigami PromptDialog` instalado. O perfil pessoal confirma somente bateria em
`trayVisibleItems`; Volume existe em `extraItems`, mas não está selecionado como
visível. Nada foi escrito na configuração pessoal. A nota sobre um menu que só
aparece no Xephyr não identifica qual menu/contexto; perguntas próprias foram
abertas na aplicação. Captura do Xephyr foi passiva; Q334 permanece sem resposta
correlacionada e nenhum comando foi enviado ao convidado.

Recibo `docs/VALIDACAO-P07-20261014.json`; artefatos privados em
`/tmp/domainos-p07-20261014-*`. P07 fica parcial/aguardando as respostas e a
correção do transporte do catálogo. Q335 pergunta sobre a visibilidade do Volume;
Q336 pede identificar o menu/contexto relatado fora do Xephyr. Próximo item
autorizado: P08 (rodapé, ajuda e LED de espera). A avaliação manual de P07
continua separada.

## P08 — defeito de geometria registrado antes do ajuste

A nota autorizada P08 informa que o borrão já sumiu e que o símbolo de
Applications ainda sobra na chapa metálica. A captura isolada atual
`/tmp/domainos-p08-20261014-before/LENS-OFF.png` (971×109, renderização do
componente QML, não sessão Plasma) mostra o desenho de 32×24 exibido em uma
caixa de 64×48 dentro do botão de 118×52. O relevo usa quatro unidades por lado;
em escala 1:2, o ícone ocupa toda a face interna e toca os limites do relevo.
O relato do borrão não será reaberto: a pessoa já confirmou que desapareceu.

Antes de alterar o código, a prova de atividade/LED atual passou 45/45 em Xvfb
privado, incluindo requests síncronos, pisca durante operação, fim da operação,
cursor, paleta e lançamento de um marcador sintético. Isso não cobre startup
notification/abertura de janela real após três segundos nem o clique de menus de
Sessão/Ajuda. Próximo passo desta mesma tarefa: reduzir o desenho somente o
suficiente para margem visível na face e verificar a geometria/captura; depois
buscar evidências ou testes próprios para os dois critérios ainda sem prova.

## 2026-10-14 — P08 parcial, geometria do Applications corrigida

O ícone do botão Applications foi reduzido de 64×48 para 54×40 unidades lógicas;
preserva a proporção 4:3 e a paleta por papéis. O novo gate exige que a imagem
fique dentro da face interna do relevo. A regressão antes da correção falhou
somente nesse gate (45/46); após a correção passou 46/46 em Xvfb e 46/46 numa
sessão Xephyr privada :69. As capturas são da cena QML isolada, não de uma sessão
Plasma completa.

A verificação dos menus nativos de Ajuda e Sessão confirma ordem do menu e nenhum
lançamento ao apenas abri-los. O ensaio de comandos terminou 20/23: três gates de
subprocessos de fixture/helper falharam (`real_helper_launch_result`, ausência de
alegação de conclusão e três processos distintos). Nenhum menu de energia foi
acionado. A tela da VM foi apenas observada; Q334 continua pendente, portanto não
enviei entrada ao MAME.

Recibo `docs/VALIDACAO-P08-20261014.json`; evidências em
`/tmp/domainos-p08-20261014-{before,after,commands,xephyr}`. P08 permanece parcial
até revisão manual e prova segura de startup/lançamento real. Segue P09, cuja
autorização r1 já está salva; não há necessidade de repetir evidências de P09
enquanto seus hashes e escopo permanecerem iguais.

## 2026-10-14 — P09: preferências aprovadas; prévia nativa pendente

P09 r1 já traz aprovação manual explícita: “Isso já fiz. E deu tudo certo.”
Reaproveitei essa avaliação separadamente dos testes e repeti apenas as provas
afetadas por mudanças posteriores nas fontes. A central nativa em perfil privado
passou 48/48: categorias, preparação temporária, Aplicar/Descartar, recarga e
independência entre instâncias; `real_profiles_modified=false` e zero diagnósticos
QML. A lista do teste registra avisos de escopo de propriedades do fixture, sem
falha nos gates.

`plasma/tests/test_domainos_thumbnails.py` passou 16/16 na fonte atual. A cena
isolada em Plasma real sob Xephyr capturou a dica de grupo e os títulos completos,
mas o gate de prévia nativa não avançou: `contentsLoader` e provedores não chegaram
a abrir. A mesma falha ocorreu em Xvfb; o cenário usa janelas próprias, compositor
privado, e os arquivos registram apenas llvmpipe. Não prova defeito no perfil real,
mas também não permite aprovar a prévia atual. Não alterei produção. Q338 pede uma
conferência manual objetiva da opção de miniaturas após uma nova passagem do
ponteiro, na versão corrente.

Recibo `docs/VALIDACAO-P09-20261014.json`; capturas privadas em
`/tmp/domainos-p09-20261014-*`. P09 fica aguardando Q338. Próximo item autorizado
e independente: P10, respeitando a regra de uma família visual por vez.

## 2026-10-14 — P10 parcial: fila visual e bloqueios explícitos

P10r1 foi lida e confirmada pela revisão exata; continua autorizada. GTK3 ainda
tem estados/encaixe pendentes e depende de Q334 para nova observação da VM; não
enviei entrada. Avancei conforme a instrução do usuário: GTK2/GTK4 não foram
tocados por sobreposição com T04 da outra IA; GTK1 não tem runtime de teste no
ambiente. Q339 pergunta se há um aplicativo GTK1 específico que deva receber
cobertura. A verificação foi somente leitura; nenhum pacote, perfil ou fonte foi
alterado. Recibo `docs/VALIDACAO-P10-20261014.json`. P10 segue parcial; resposta
de Q339 e liberação do escopo T04 determinam os próximos ramos independentes.


## 2026-10-14 — I337: seção Rui concluída e conferida após reabertura

I337 revisão 2 foi concluída tecnicamente; a resposta da IA reconhece a revisão
exata e permanece separada do aceite humano. A seção Documentos `Rui` está no
estado persistido e na interface reaberta, vazia (0 demandas); nenhuma demanda
foi criada ou transferida. A liberação temporária autorizada foi usada para
fechar a janela anterior normalmente e reabri-la uma vez (PID atual 1669615).
O hash do journal de rascunhos foi idêntico antes e depois da reabertura e a
composição voltou a aparecer, sem edição. A permissão de uso único foi
consumida; nenhuma nova reabertura foi feita. Recibo: `ai-work-board/docs/VALIDACAO-I337-20261014.json`.

## 2026-10-14 — I340: canal fixo Rui criado

I340 revisão 2 autorizada/hash atual: criei o registro I341 como canal fixo
`Rui`. O botão apareceu na janela ativa ao lado dos canais existentes e do
Canal — Conjunto. A autorização I340 foi preservada, sem reutilizar histórico.
O modelo de filtro da GUI exclui canais (probe sintético `[[]]`), mas
`--command queue` inclui seus registros; Q343 pergunta qual contrato CLI deve
valer, sem autorização de código. `make check-channels` não passou: falha de
link SQLite e janela Xvfb não localizada pelo harness. Recibo em
`ai-work-board/docs/VALIDACAO-I340-20261014.json`; aceite humano segue separado.


## 2026-10-14 — P10/V06 parcial em Xephyr; próxima Qt Quick

V06 foi avançada em Qt 6.8.2/Kvantum no Xephyr isolado: extent corrigido para
15 px e as quatro células normais de seta tiveram diferença de 0 pixels ante a
referência VUE 2.01 em 1:1. A variante usa paleta KDE dinâmica, mantém geometria
em 1.868 grupos, e seis testes focados passaram. Estado técnico segue parcial;
pressionado/desabilitado, thumb comparável, encaixe/canto de 4 px e avaliação
manual ainda faltam. Não alterei configurações pessoais, a VM, a T04, nem a
produção da prancheta. Próximo item independente: V07 Qt Quick em Xephyr,
identificar o scrollbar efetivamente mostrado pelo System Settings antes de
qualquer ajuste. V02 aguarda Q334, V03/V04 seguem sobrepostas à T04 e V05 aguarda
Q339. Recibo: `docs/VALIDACAO-V06-QT-20261014.json`.

V07 avançou para identificação em System Settings 6.3.4 no Xephyr, com XDG
isolado e paleta DomainOS. A barra lateral é Qt Quick `org.kde.desktop/ScrollBar.qml`
e delega a pintura para `StylePrivate.StyleItem`; o plugin Kvantum estava
carregado. Ainda não foi provado o caminho exato de pintura do glyph inferior,
logo não houve correção. Próximo V08: tentar consumidor real de Plasma Style em
Xephyr; se indisponível, registrar o bloqueio e avançar a V09. Recibo:
`docs/VALIDACAO-V07-QTQUICK-20261014.json`.

## 2026-10-14 — P10/V08 parcial: Plasma Components ScrollBar em Xephyr

A barra Plasma foi renderizada pelo componente QML real `org.kde.plasma.components.ScrollBar`
com KSvg. A captura inicial mediu 20 px no eixo transversal vertical, 16 px
horizontal e thumb de 12 px. Ajustei no gerador DomainOS o hint e as margens
transversais para 15/11 px; a captura final confirma 15 px nas duas orientações
e thumb de 11 px, com hover atingido. Builder e seis testes de procedência
passaram; verificador nativo KSvg passou 207 checagens nos quatro esquemas
(current, escuro, amarelo e papéis distintos). A comparação registrou os oito
IDs cuja caixa mudou deliberadamente e preservou os demais 1.875 limites por
caso. V08 permanece parcial por comprimento/estados/canto e revisão humana.
Próximo V09: chapa, LED e ícone no consumidor isolado. Recibo:
`docs/VALIDACAO-V08-PLASMA-20261014.json`.

## 2026-10-14 — P10/V09 parcial: applet do painel em Xephyr

Carreguei o applet `org.irixclassic.domainos.panel` em `plasmawindowed` no Xephyr
privado e copiei a dependência `org.irixclassic.grosview` apenas para o XDG
temporário. A captura válida mostra a chapa e o ícone Applications, mas o Pager
fica em “Áreas indisponíveis”. A tentativa com KWin resultou em imagem preta; a
referência VUE disponível tem a faixa inferior parcialmente coberta. Esses dados
não permitem registrar escala ou atribuir o borrão a um elemento; não fiz ajuste
visual. R13 comprova a espera do LED como comportamento, sem avaliar sua
aparência. V09 permanece parcial até haver painel integrado funcional e faixa
VUE desobstruída. V10 continua na fila, dependente das comparações registradas e
estados visuais pendentes. Recibo: `docs/VALIDACAO-V09-PANEL-20261014.json`.

## 2026-10-14 — P10/V10 parcial: decoração atual revalidada

Os recibos anteriores da decoração pertenciam ao pacote 0.1.0; a fonte atual é
0.1.1, por isso reexecutei os ensaios contra os hashes presentes. A comparação
de 12 regiões da moldura ativa/inativa com a referência SR10.4 teve zero pixels
diferentes; 85 verificações do renderer passaram. KWin privado passou 39/39,
incluindo diálogo fixo 6/6/25/6 e pressão/soltura do título; a prévia KDecoration3
passou 9/9. Sem mudança de código ou configuração pessoal. V10 fica parcial:
V02-V09 ainda têm etapas abertas e falta a matriz integrada dos esquemas neutro,
escuro e amarelo. Não é aceite visual do usuário. Próximo trabalho: retomar V07
para identificar o pintor Qt Quick ou V09 quando houver consumidor integrado e
captura VUE desobstruída. Recibo: `docs/VALIDACAO-V10-DECORATION-20261014.json`.


## 2026-10-14 — build de produção e recuperação de rascunhos

A versão de produção do AI Work Board foi recompilada com `make --always-make
build/work-board` (`-Werror`) e terminou sem erro. O hash novo e o processo
visível em :1, PID 1737873, coincidem (`101ab92339b0185b7824ecc61845706c4f11bb4413b9072ba7bd206f005402f2`);
a janela permaneceu aberta porque já executava exatamente o mesmo executável.
Q102 recebeu aviso na sequência 103; Q335/Q336/Q338/Q339 estão disponíveis para
resposta pela aplicação. Nenhum rascunho pessoal foi lido ou alterado.

A revalidação da edição/rascunhos está em
`ai-work-board/docs/VALIDACAO-DRAFT-DURABILITY-RECHECK-20261014.json`: 12
invariantes de edição, journal persistido antes de SIGKILL e restauração do
texto artificial, revisão de rascunhos e teste nativo Motif passaram. O estado
salvo pessoal ficou inalterado. Recibo da compilação/runtime:
`ai-work-board/docs/VALIDACAO-PRODUCAO-COMPILACAO-20261014.json`.

## 2026-10-14 — confirmação de produção e V07 corrigida no teste isolado

A versão de produção da AI Work Board foi forçada a compilar e terminou sem
falhas (`-Werror`). Build e processo da janela aberta em :1 (PID 1737873) usam
SHA-256 `101ab92339b0185b7824ecc61845706c4f11bb4413b9072ba7bd206f005402f2`.
Q102 seq.103 confirmou a disponibilidade das perguntas; seq.104/105 comunicaram
a inspeção V07. A revalidação de rascunhos/edição está em
`ai-work-board/docs/VALIDACAO-DRAFT-DURABILITY-RECHECK-20261014.json`; nenhuma
resposta, autorização ou journal pessoal foi lido ou alterado.

Em V07, o glyph pequeno era fallback do ensaio: o tema Kvantum estava no nível
errado da árvore XDG temporária. Com a pasta `<tema>/<tema>`, `StyleItem` informa
`kvantum::`, usa extent 15 px, e as células inferiores normal e superior
insensível coincidem pixel a pixel com seus indicadores SVG. Nenhuma fonte
visual foi modificada. V07 continua parcial para spacing/canto, thumb, paletas e
revisão humana. Recibo `docs/VALIDACAO-V07-QTQUICK-20261014.json`.


## 2026-10-14 — produção reaberta e continuação V07

A compilação de produção já registrada foi executada de novo na sessão normal:
PID 1768706, janela “AI Work Board — Prancheta de projetos” visível em :1 a
1920×951, SHA-256 do executável igual ao build
`101ab92339b0185b7824ecc61845706c4f11bb4413b9072ba7bd206f005402f2`. O journal
pessoal não foi consultado nem alterado. Q102 foi verificado até seq.105 e recebeu
a confirmação de execução em seq.106.

V07: barra de conteúdo System Settings medida em 15×468 px; seta inferior normal
coincide com o SVG ativo em 0/225 pixels. Thumb mede 42,18 px nesta página, sem
referência de conteúdo equivalente. Fundo/moldura invisível e ausência de barra
horizontal impedem medir os 4 px de moldura e o canto. Sem mudança de produto;
V07 permanece parcial. Próximo: encontrar consumidor Qt Quick com moldura e ambas
as barras para comparação com conteúdo/viewport equivalente. Evidência em
`docs/VALIDACAO-V07-QTQUICK-20261014.json`.


V07 — KInfoCenter 6.3.6 (`kcm_kwinsupportinfo`) é um consumidor real Qt Quick/Kirigami
com barras simultâneas. Em Xephyr, barras 15 px, canto 15×15 e quatro setas do estado
normal/limite coincidem com os grupos SVG esperados em 0/225 pixels; canto é
`View.BackgroundNormal`. O fundo do ScrollView está invisível, portanto espaçamento
de 4 px sem medida. Q345 foi aberta no Q102 após GTK-V07 pedindo uma app real com
moldura visível. Sem mudança no produto. Evidência:
`docs/VALIDACAO-V07-QTQUICK-20261014.json`.


2026-10-14 Q102 atualizado até seq.108: KInfoCenter real confirmou barras 15 px,
canto 15×15 e quatro setas de endpoint/normais idênticas aos SVGs ativos. Q345
pergunta por app Qt Quick com moldura visível. Uma tentativa de pressão moveu a
página, mas a captura não correspondeu à variante pressionada; esse estado fica
pendente. A versão de produção segue PID 1768706 em :1, SHA-256
`101ab92339b0185b7824ecc61845706c4f11bb4413b9072ba7bd206f005402f2`.


V07 press/release: no KInfoCenter isolado, seta inferior e seta direita pressionadas
coincidem com os SVGs pressed em 0/225 px; as solturas retornam aos grupos normal
em 0/225. A primeira sonda separada foi inconclusiva e preservada sem usar como
prova. Etapas restantes: Q345 para widget com moldura, thumb com conteúdo equivalente
e paletas.


Q102 consultado após a atualização V07: seq.109 é a mensagem mais recente; não
há resposta nova do usuário em Q102 nem nas perguntas Q335/Q336/Q338/Q339/Q345.
A produção permanece aberta em :1, PID 1768706, executável SHA-256 igual ao build.


2026-10-14 — produção e bloqueio V09: confirmei a versão de produção aberta em :1,
PID 1768706, SHA-256 `101ab92339b0185b7824ecc61845706c4f11bb4413b9072ba7bd206f005402f2`;
Q102 recebeu aviso seq.113 para Q335/Q336/Q338/Q339/Q345. Não alterei respostas,
autorizações nem journal de rascunhos. Em Xephyr :69, a retentativa privada com
KWin 6.3.6, quatro desktops e `KWIN_COMPOSE=N` disponibilizou o serviço e reportou
4 áreas, mas produziu captura preta; a tentativa OpenGL anterior também falhou
visualmente. O código aberto do KWin documenta esse valor como desativação de
composição. V09 permanece bloqueada, sem mudança no produto.

O bridge MAME foi consultado com `status`: há uma requisição antiga sem resposta
desde 2026-10-13. Não a removi nem publiquei outra; a VM continua viva. Assim, não
enviei comandos de interface nem consegui liberar a faixa VUE parcialmente
encoberta. Recibo atualizado `docs/VALIDACAO-V09-PANEL-20261014.json`; provas
anteriores preservadas. Próximo: conferir autorização e fila atuais para seguir
ao próximo item independente; V10 permanece parcial porque V02–V09 não fecharam.


## 2026-10-14 — V07 alternativa sem moldura e V08 interação no Plasma Components

V07: testei o Plasma System Monitor já instalado na Xephyr :69, com XDG isolado. A página Processes abriu sem conteúdo/rolagem e não mostrou moldura; `BaseTableView.qml` usa `ScrollView` com `Rectangle` de fundo sem borda. A tentativa inicial com overlay gerou erro `ScrollablePage` e foi excluída. Q345 permanece sem resposta. Recibo `docs/VALIDACAO-V07-SYSTEMMONITOR-20261014.json`.

V08: em fixture isolada do componente Plasma real, capturei normal/hover/pressionado/solto. Hover revela o trilho; pressionar o thumb e soltar em hover não muda seus pixels; ao afastar o cursor retorna exatamente ao normal. A rota de eventos e a geometria não mostram deslocamento. Não interpreto isso como prova de aparência histórica do thumb pressionado, que a VM não cobre. V08 segue parcial e a sequência vai para V09 conforme P10. Recibo atualizado `docs/VALIDACAO-V08-PLASMA-20261014.json`.

## 2026-10-14 — recompilação de produção, I342 e rascunhos

Após a pessoa dizer que só poderia responder com a aplicação de produção aberta,
executei `make --always-make build/work-board` com `-Werror` e reabri a interface
normal em :1. Build e processo ativo têm SHA-256
`101ab92339b0185b7824ecc61845706c4f11bb4413b9072ba7bd206f005402f2`; PID
1929120, janela visível. Q102 seq.115 avisa que Q335, Q336, Q338, Q339, Q345 e
Q351 podem ser respondidas na aplicação. Nenhuma resposta/autorização foi
alterada nem o journal privado consultado.

I342: `help_viewr_rev/README.md` e o relatório da etapa agora descrevem os
resultados Ghidra, sem chamar pseudocódigo de fonte compilável. O índice escolhido
para o Help Viewer registra 178/178; sete bibliotecas/runtime, 5.208/5.248; total
5.386/5.426. As 40 falhas estão discriminadas; a causa das 21 falhas de criação
em libc não foi inferida. Novo manifesto em
`analysis/decompiler/ghidra/EXPORT-MANIFEST-20261014.json` cobre 1.421 artefatos;
validação: 0 divergências em seus hashes e 0 referências de assembly ausentes.
`SHA256SUMS` voltou a passar após atualizar os hashes do README/relatório. Ainda
não há C reconstruído, compilação ou execução do candidato na VM. Não anexei DDE
nem alterei VM, perfil ou ftpd. Estimativa técnica I342: cerca de 33%, baseada em
uma de três etapas planejadas (captura/inventário e mapa estático); reconstrução
e validação no toolchain Apollo continuam pendentes.

O recheck de rascunhos (`VALIDACAO-DRAFT-DURABILITY-RECHECK-20261014.json`)
prova os invariantes em dados sintéticos, não reproduz a falha específica relatada
pela pessoa. I298 já entregou revisão reversível dos rascunhos. Para não adivinhar
nem abrir o journal pessoal, criei I352 sem autorização: proposta para colher os
passos sem conteúdo, reproduzir com fixture sintética e corrigir a menor camada
se houver defeito. Q353 pede descrição do item/campo, ação, resultado esperado e
observado, sem texto privado. Responder à Q353 não autoriza I352.

V09 permanece parcial/bloqueada: a nova tentativa integrada KWin em Xephyr
continuou preta/corrompida e a faixa VUE está parcialmente coberta; não obtive
comparação visual válida. V10 também permanece parcial e a revisão conjunta não
pode ser fechada. O MAME tem requisição de bridge pendente sem resposta; preservei
o arquivo e não enviei entrada nova. Não toquei na T04 da outra IA. Próximos
passos: aguardar Q353 e as respostas parciais pela produção aberta; em paralelo,
continuar I342 dentro da autorização salva e manter V09 em espera até obter captura
integrada válida e referência desobstruída.

### I342 aguarda disponibilidade do guest — 2026-10-14

Consulta Telnet somente leitura não conectou: `No route to host`. No host, não há
processo MAME; `tap-mess-1000-0` está DOWN/NO-CARRIER. A bridge ainda registra a
requisição antiga `f2127393cf7642a4896dceae1977ea71` sem resposta. Não reenviei nem
substituí arquivo de comando, não iniciei MAME e não alterei a rede. Como reiniciar
poderia descartar estado volátil, I342 recebeu status `waiting_user` para a parte
Apollo e Q354 pergunta qual caminho seguir; a autorização de I342 continua salva.
Q102 seq.119 informa que a produção da prancheta permanece aberta. Q353 também
segue aberta para detalhar o sintoma do rascunho sem revelar conteúdo pessoal.

## 2026-10-14 — V08 disabled revalidado; captura V09 identificada

Retomei V08 em Xephyr :70, 1024×844, DPR 1, usando o componente real
`org.kde.plasma.components.ScrollBar` e KSvg, com diretório XDG de teste isolado.
Vertical e horizontal permaneceram visíveis com `enabled=false` e conservaram
espessura de 15 px. Contra a captura habilitada no mesmo fixture, 814/7202 pixels
mudaram na ROI vertical e 990/7840 na horizontal; as diferenças ficaram nas
regiões dos thumbs. A QML instalada declara opacidade 0,5 para o handle
desabilitado. Isso não prova como um thumb Xt insensível deveria aparecer no
SR10.4, portanto V08 segue parcial; faltam thumb com conteúdo equivalente,
canto/acabamento e avaliação manual. Recibo e hashes em
`docs/VALIDACAO-V08-PLASMA-20261014.json`; capturas privadas em
`/home/lsi/tempia/domainos-v08-plasma-20261014/disabled-20261014/`.

Na reauditoria V09, o arquivo `xdg-retry3/state/panel.png` com hash
`d8a8e40e…34d23a8` mostra Cores do System Settings, não uma tela preta nem
captura de painel integrado. O screenshot realmente preto do applet é
`panel-applet-kwin.png` (`b3bf314b…edd9794`). Corrigi a descrição da evidência.
Também localizei no acervo a captura completa de 2026-10-12, 1024×844, com toda
a faixa inferior VUE desobstruída; seu recorte 1:1 `[43,707,990,800]` (947×93)
foi catalogado em I295. Isso libera a comparação estática da moldura, mas não
substitui uma captura integrada atual do applet nem prova estados transitórios.
V09 permanece parcial por falta dessa captura integrada e revisão de LED/Pager.
Não houve alteração de tema, perfil pessoal, VM ou T04. A captura passiva I295
em 966×796 foi excluída do acervo 1:1 (guest: 1024×800); Q334 segue sem resposta
e nenhuma entrada Apollo foi enviada.

V09: comparei também os escopos de dimensão antes de inferir um ajuste. O
desenho canônico do projeto é 1942×218 (971×109 a 50%); o painel VUE observado
no recorte mede 947×93. Mantive ambas as medidas em seus contextos, sem alterar
o applet para caber na captura VUE. Em uma tentativa nova de re-render, o applet
atual foi copiado para XDG isolado em Xephyr :70; os hashes de `metadata.json` e
`main.qml` coincidem com a árvore atual do projeto. `plasmawindowed` criou janelas
mas o root ficou preto uniforme (SHA-256
`79a9fce6…03ef118ba`) e o host registrou pacote `empty` ausente e falta do
serviço KWin. A causa do quadro preto não foi determinada; não serve de prova
visual. Recibo V09 atualizado.

2026-10-14 — V09: capturei o applet dentro de um painel do `plasmashell` real em
Xephyr :69, com KWin 6.3.6 privado e XDG descartável. A árvore do pacote copiado
coincide com a fonte atual. O KWin expõe quatro desktops e a composição do painel
tem 971×109 px, comprovados por `xwininfo`; o recorte 1:1 do screenshot mede a
mesma dimensão e tem SHA-256 `bf761e3a7a4961e5c5508b1d6e68d8a7d747a6fa87bcb22c3e8125126bace5de`.
O screenshot root 1600×1200 mede `3f7d2821c25b849fb80b38e3a063efd8a0899b6f82570f332ced21b2c4e95f0d`.
O Pager mostra dois desktops de cada vez e navegação; o fonte confirma limite de
dois, enquanto a imagem VUE estática tem seis células. Registrei essa diferença e
criei Q355 para escolha, sem alterar o desenho. VUE 947×93 e painel 971×109 são
medidas independentes, sem reescala. O LED dinâmico continua bloqueado pela VM
inativa/bridge antiga. Não toquei em T04, configuração pessoal ou entrada Apollo.


## 2026-10-14 — matriz V09 e diagnóstico de rascunhos

V09 continuou no Xephyr :69 com o applet real dentro de Plasma/KWin. A captura
integrada 971×109 a 1:1 já cobria o Pager conectado. Completei a matriz do
appet sob `DomainOS-SR10-4`, `BreezeClassic`, `BreezeDark` e fixture amarelo
privado; os recortes mudam sob os esquemas de teste. Restaurei o XDG privado para
DomainOS e confirmei que `~/.config/kdeglobals` permanece no hash anterior
`a782395a…138de17`. A árvore de fonte do applet e configurações pessoais não
mudaram. O primeiro recorte amarelo saiu preto durante a reconstrução; foi
descartado e substituído por captura estável. Recibos:
`docs/VALIDACAO-V09-PALETAS-20261014.json`,
`docs/VALIDACAO-V09-PANEL-20261014.json`. V09 segue parcial: Q355 aguarda a preferência do Pager e Q356 pergunta pela faixa
de títulos de janelas entre Mail e Pager; LED dinâmico Apollo depende de guest/bridge acessível.

Rascunhos: o defeito conhecido de fechamento antes do checkpoint assíncrono de
200 ms já foi reproduzido e corrigido em I261. A fonte atual de
`src/controller/actions.c` e a prova `tests/test_draft_durability.py` coincidem
com os hashes do recheck; o binário ativo de produção também é o SHA
`101ab923…005402f2`. O teste sintético registrou edição no widget, checkpoint
antes de SIGKILL e recuperação sem mudar a resposta/autorização salva. Isso não
identifica a nova ocorrência sem passos. I352 permanece sem autorização e não foi
executada; Q353 pede campo/item, última ação, esperado/ocorrido e aviso de
checkpoint, sem incluir texto pessoal. Em 2026-10-14, confirmei que a produção
estava fechada, preservei o binário anterior em
`/home/lsi/tempia/board/work-board-before-rebuild-20261014-0937`, forcei a
recompilação (`-Werror`) e reabri pelo lançador oficial. A janela ficou visível
na sessão :1 e o executável ativo corresponde ao build SHA
`101ab92339b0185b7824ecc61845706c4f11bb4413b9072ba7bd206f005402f2`. Enviei o
estado e a prontidão para respostas no Q102 (seq. 140); Q355/Q356 continuam sem
resposta salva neste registro. Não examinei nem alterei rascunhos pessoais.


Comparação estática adicional V09: no recorte VUE, as seis células do Pager vêm
logo após os quatro controles à esquerda; no applet integrado há uma faixa larga
de títulos entre Mail e Pager, além do Pager atual de dois cartões/navegação. São
observações de composição, não prova de que a faixa deva ser removida. Abri Q356
após Q355 para pedir a preferência; não alterei a fonte. A captura e os limites
foram acrescentados a `VALIDACAO-V09-PANEL-20261014.json`.


## 2026-10-14 — V06 Qt estados, spacing sem controle Kvantum, Q357

Retomada conforme regras DomainOS, contrato único e recibos atuais. No fixture
privado Qt 6.8.2/Kvantum em Xephyr, QTest moveu o valor 0→1 ao segurar a seta
inferior; o glyph mudou 53 pixels e a soltura restaurou a base. Após mascarar
nove pixels do cursor sobre a referência HP VUE, os crops normal/held/released
coincidem em 0 pixels diferentes. O fixture sintético tem 165 linhas e estima
15 visíveis; viewport 536×289, barra 15 px, range 0..151, pageStep 14, thumb
22 px. A captura nativa correspondente estima 21 px, mas fonte/moldura não são
pareadas o bastante para ajuste. A barra dual-axis reserva canto 15×15, sem
comparação nativa de sua face; estado disabled foi capturado somente no Qt.

O espaçamento viewport/barra foi medido em 0 px contra os 4 px do contrato
SR10.4. A opção `scrollbar_in_view=true` no XDG descartável não mudou a
geometria; Kvantum não expõe ajuste para `PM_ScrollView_ScrollBarSpacing`, e
`layout_spacing` não altera esse intervalo. Nenhuma correção foi feita para
simular spacing. Abri Q357 depois de Q356 para perguntar se a limitação deve
ser documentada ou se a pessoa deseja uma demanda própria para adaptador Qt
com autorização separada. Evidência em
`docs/VALIDACAO-V06-ESTADOS-20261014.json`; recibo original em
`docs/VALIDACAO-V06-QT-20261014.json`. Checklist e fila visual atualizados.

Produção AI Work Board segue compilada com `-Werror`, aberta pelo launcher
oficial e visível na sessão :1 (PID 2224516, SHA ativo
`101ab92339b0185b7824ecc61845706c4f11bb4413b9072ba7bd206f005402f2`), pronta
para respostas. Q102 foi lido até seq.144; seq.141–144 são atualizações da
outra tarefa, sem resposta sua nova após a seq.140. Q355 e Q356 continuam
aguardando sua preferência. Não toquei na T04, na configuração KDE pessoal,
na VM ou em rascunhos pessoais. MAME segue ausente e a TAP indisponível; mantive
a requisição I295 pendente sem reenviar. Próximo trabalho visual independente:
V08, no Xephyr existente :69, depois de registrar resposta a Q357 se chegar.


## 2026-10-14 — V08: canto pertence ao host ScrollView

Mantive o tema e o XDG pessoal intactos. Em Xephyr :69 com Qt 6.8.2, executei
uma fixture privada usando `org.kde.plasma.components.ScrollView` e as barras
Plasma/KSvg reais, conteúdo 700×600 num viewport nominal 350×270. Com duas
barras visíveis, o ScrollView reservou interseção 15×15; horizontal 335×15 e
vertical 15×255. Na referência HP VUE, o canto nativo aparece preenchido com a
face do conteúdo. Na fixture, como não foi definido background no ScrollView,
a interseção mostra o Window background, enquanto o conteúdo usa `palette.base`.
Isso localiza o preenchimento na composição/host da aplicação; não prova defeito
no asset de ScrollBar nem uma regra universal para todas as aplicações. O QML
emitiu aviso de binding loop `visible` nos ScrollBars anexados, embora tenha
produzido as medidas/captura. Registrei isso como limitação do fixture. Recibo e
hashes em `docs/VALIDACAO-V08-PLASMA-20261014.json`; fila e checklist visual
atualizados. V08 segue parcial por falta de consumidor real com papéis de fundo
conhecidos, thumb histórico pareado e revisão humana. Estimativa ~75% dos marcos
de evidência V08, não de fidelidade. Próximo: continuar P10 em escopo V08 quando
houver um consumidor ou evidência apropriados; Q355/Q356/Q357 seguem aguardando
a pessoa.


Complemento V08: aninhei a mesma ScrollView Plasma sob uma `PC.Page` real.
`Kirigami.Theme.backgroundColor` e `SystemPalette.window` reportaram #78a0d5;
`SystemPalette.base` reportou #6688b5. A PC.Page permaneceu sem preenchimento
na interseção do screenshot, consistente com seu fonte e com
`PlasmaExtras.Representation.qml`, que estende PC.Page e só ajusta margens. O
fonte instalado de Vault usa essa Representation com PC.ScrollView e também não
define background no ScrollView. Isso deixa o fundo final a cargo do host externo
do popup. Não abri um applet com dados do usuário; a aparência do popup real
permanece sem prova. Hashes e fontes locais adicionados ao recibo V08; nenhuma
alteração em produto/configuração pessoal.


## 2026-10-14 — V09: diferença das proporções externas, Q358

Comparei lado a lado as capturas sem reescala. O recorte estático HP VUE mede
947×93 px; o containment atual mede 971×109 px a 1:1 e corresponde ao canvas
de design 1942×218 renderizado em escala 0,5. A diferença externa é +24×+16 px
e as proporções são distintas. A captura VUE não resolve se a composição atual
maior/mais alta é intencional. Registrei Q358 para a pessoa escolher preservar
o canvas/aspecto atual ou aproximar a proporção externa da captura VUE. Nenhum
asset, escala ou dimensão foi alterado. Q355 e Q356 permanecem separados e
aguardam a decisão do Pager e da faixa de títulos. Recibo atualizado:
`docs/VALIDACAO-V09-PANEL-20261014.json`.


Leitura final do Q102 nesta rodada: seq.152. A seq.151 é a atualização V09
acima; a seq.152 pertence à análise I342 do outro contexto. Nenhuma resposta
humana nova chegou às Q355/Q356/Q357/Q358 após a atualização. A produção
permanece aberta para receber respostas parciais.

## 2026-10-14 — produção recompilada e Q102 disponível

Executei `make -B build/work-board` no AI Work Board com `-Werror`; a compilação
completa terminou sem erro. O build resultante manteve SHA-256
`101ab92339b0185b7824ecc61845706c4f11bb4413b9072ba7bd206f005402f2`, idêntico
ao executável do processo ativo. Confirmei a janela visível da produção na
sessão :1 (1650×606); ela continua aberta sobre o estado oficial, sem segunda
GUI e sem leitura ou alteração de rascunhos pessoais. A atualização foi enviada
ao canal Q102 na sequência 155. Q355/Q356/Q357/Q358 seguem aguardando respostas
pela interface. Próximo: processar respostas parciais depois que forem salvas;
T04 permanece com a outra IA. Nenhuma mudança de código do tema ou da VM.


## 2026-10-14 — produção com rascunhos duráveis e V08 host registrado

A reprodução sintética confirmou que conversas individual e conjunta agendavam
checkpoint 200 ms depois da edição; ambos agora confirmam o journal antes de
retornar ao loop de eventos, e atualizações programáticas do campo não
ressuscitam rascunhos descartados. `make check-editing` passou os 12 cenários de
edição, a recuperação após SIGKILL e a suíte adicional dos dois compositores;
`check-conversation-hub` também passou com descarte/Undo sem ressurreição. O
candidato foi compilado, verificado no Xephyr e instalado na raiz do projeto de
produção com backup SHA-256 `101ab923…005402f2`; executável ativo
`f2d87697…3b96307d`. A interface oficial está aberta em :1. Não examinei texto
de rascunhos pessoais nem alterei respostas/autorização. Q102 recebeu o aviso na
sequência 158. I352 continua aguardando Q353 para distinguir o relato novo; a
correção da corrida conhecida não é apresentada como reprodução daquele evento.

V08 ganhou captura de um containment real de painel Plasma em Xephyr :69: a
interseção 15×15 usa a superfície externa do painel, com papéis window/base/text
registrados. Não é captura do popup do applet; V08 permanece parcial, sem mudança
de asset ou configuração pessoal. Recibo e hashes em
`docs/VALIDACAO-V08-PLASMA-20261014.json`. V09 aguarda respostas Q355/Q356/Q358;
V06 aguarda Q357. I295/Q334 seguem sem guest visível, GTK2/GTK4 continuam
retidos por T04 da outra IA, e T04 não foi tocada. Próximo: receber respostas
parciais pelo Q102/prancheta e continuar a evidência independente de V08.


## 2026-10-14 — V08 popup real e fila reavaliada

Correção de escopo: `root-tall.png` era containment de painel, não popup. Em
Xephyr :69 criei uma fixture sintética com `PlasmoidItem.expanded`, cliquei na
representação compacta e confirmei a fullRepresentation num popup `IsViewable`
do plasmashell. As barras reais Plasma ficaram ao redor de 24 linhas sintéticas.
Janela 778×558 em captura 1600×1200 a 1:1. No ROI 15×15 da interseção, 169/225
pixels iguais ao fundo adjacente `#78a0d5`; linhas usam base dinâmica. Captura e
hashes no recibo V08. Removi o painel/applet e restaurei o layout isolado.

O host agora foi provado no fixture, no painel e no popup. A referência SR10.4
continua sendo o Trash Can vazio, portanto comprimento pareado do thumb não pode
ser medido; não alterei asset. V08 permanece parcial e segue para revisão manual
quando a pessoa quiser. Estimativa ~85% dos marcos de evidência V08 (geometria,
paletas, estados e host), não de fidelidade. P10 continua ativo; V09 aguarda
Q355/Q356/Q358 e V06 aguarda Q357. Leitura Q102 nesta retomada: sequência 158,
sem resposta humana nova; produção corrigida segue aberta na :1. I352/Q353 também
aguarda descrição do evento para verificar se havia outra falha além da corrida
conhecida. Próxima: avançar somente outra demanda independente com autorização
salva; I167/T04 continua com a outra IA.


## 2026-10-14 — I178 GTK3: limitação confirmada, aguarda escopo

I178r1 autorizada e reconhecida. Reproduzi em Xephyr :69 com GtkTreeView real: borda transparente não pinta; borda opaca e sombra inset desenham contornos em cada linha/célula (44.054 pixels alterados na comparação da mesma paleta), sem resolver apenas o quadro principal. Tentei a tabela vazia e a preenchida; não mexi no tema. Recibo `docs/review/I178-GTK3-TREEVIEW-FRAME-20261014.json` e capturas privadas em `/home/lsi/tempia/domainos-i178-20261014/evidence/`. I178 fica aguardando Q359 sobre manter a limitação CSS ou abrir uma demanda separada de integração de aplicação. V02 continua parcial. Próximo trabalho visual depende de resposta ou de outra demanda autorizada e independente; GTK2/GTK4 continuam com T04 da outra IA.


## 2026-10-14 — Q102 159 lido; próximas demandas aguardam escolha

Confirmei no estado atual que I179 já foi entregue com recibo; não repeti a entrega. I167–I173 continuam vinculadas ao T04 da outra IA e I174–I177 seguem depois do P10. I178 permanece aguardando Q359; Q345/Q353/Q355/Q356/Q357/Q358 também não têm resposta nova. A última leitura do Q102 foi a sequência 159. Não encontrei outra demanda visual independente pronta sem autorização ou preferência pendente. A produção AI Work Board continua viva na :1 com o executável compilado/instalado; a Xephyr :69 e o perfil pessoal permanecem intactos.


## 2026-10-14 — I169 conferida contra T04

Correção operacional: I169 é explicitamente a frente Qt5 da T04 no documento de arquitetura do laboratório. Apesar da autorização salva, o usuário atribuiu T04 à outra IA. A leitura inicial ocorreu, mas nenhum artefato Qt5 foi modificado; o item voltou a `waiting_user` com motivo registrado e aviso no Q102. A fila volta a aguardar Q359/Q345/Q353/Q355/Q356/Q357/Q358; não há próximo item independente livre identificado.


## 2026-10-14 — I342: solicitação de capacidade do ftpd

O pedido de usar Telnet para elevar conexões simultâneas do ftpd Apollo foi
registrado como I361, depois de Q354, sem autorização salva. A verificação local
read-only encontrou nenhuma instância MAME, TAP `tap-mess-1000-0` em
`DOWN/NO-CARRIER`, nenhuma porta Telnet local aberta e conexão a
`192.168.240.2:23` indisponível. A ponte MAME ainda mantém a solicitação
`f2127393cf7642a4896dceae1977ea71` sem resposta; não foi reenviada nem editada.
Não houve conexão à VM, alteração de configuração ou reinício. Q354 segue
aguardando a escolha entre manter a sessão em espera ou pedir avaliação de uma
partida controlada; qualquer ajuste do ftpd também depende de autorização salva
em I361. Próximo: aguardar Q354 e autorização de I361 pelo Q102/prancheta.


## 2026-10-14 — I342: r24 e estado de retorno

Com I342r3 autorizado, recuperei suplemento estático para `PrintComplexState`:
quatro hooks A5 tipados preservam os argumentos/retornos longword conferidos
contra a assembly; duas importações Ghidra 12.1.4 limpas deram output idêntico.
O índice-base permanece inalterado: 19/20 falhas têm agora suplemento aceito;
`_XtLookupModifier` permanece pendente, com C manual host testado mas pseudo-C
Ghidra ainda rejeitado. Recibo r24 e 7 artefatos registrados no manifesto;
3.678 artefatos base, 133 suplementos, 31 reconstruções manuais e 1.868 hashes
foram auditados. Verificadores r22/r24 e teste C89 host de XtLookupModifier
passaram. A VM continua ausente (TAP DOWN/NO-CARRIER; Telnet indisponível), Q354
aguarda decisão, e I361 (ftpd) segue sem autorização. Próximo: tratar a falha
restante em análise estática e aguardar autorização necessária antes de iniciar
ou alterar a VM.

Complemento da retomada I342: r25/r26/r28 testaram três modelos para a pilha do
callback de `_XtLookupModifier` (stdcall/RTD, referência de chamada e A1 fixado
no call site); os três reproduziram a mesma divergência e foram preservados
como rejeitados, sem alterar a contagem aceita. Manifesto revisado com 142
suplementos e 3.678 itens base, sem erro de hash; `SHA256SUMS` passou 1.877
itens. Próximo continua sendo atacar a recuperação estática restante enquanto
Q354 e I361 aguardam respostas no Q102.


## 2026-10-14 — I342: auditoria semântica de `PrintComplexState`

Ao comparar o modelo C host com a assembly SR10.4 e o suplemento r24, corrigi
três divergências que os testes anteriores não detectavam: o seletor de evento
fica em +2 e o de tradução em +4; o sinalizador de ramo usa o bit 30 do
longword (máscara `0x40000000`); a contagem usa comparação signed positiva.
Os testes agora verificam seletores distintos por callbacks separados, o bit 30
versus bit 31 isolado e contagem negativa. C89 estrito, ASan/UBSan, verificadores
r22/r24, manifesto (3.678 artefatos base, 11 funções manuais) e 1.880 hashes
passaram. I342 e Q102 foram atualizadas pela CLI SQLite com as revisões salvas
I342r3/Q102r191; a autorização do usuário ficou intacta. Continua faltando
compilar e executar na Apollo; não migrei código para o projeto Linux. Avanço
estimado do objetivo integral: cerca de 10%, baseado no inventário e na análise
estática acumulada e em apenas 11 modelos C manuais parciais; isso não representa
percentual de código recuperado nem de validação. Próximo: continuar reconstrução
estática incremental; a compilação/execução Apollo espera uma sessão acessível.
Q354 continua sem resposta e I361 segue sem autorização; nenhuma mudança na VM,
rede, ftpd ou disco ocorreu.

Complemento I342 (14-10): além das correções de `PrintComplexState`, modelei
`LookAheadForCycleOrMulticlick` a partir dos 408 bytes de assembly e do
pseudocódigo ativo, com callbacks explícitos para tabelas A5 e testes de cadeias,
branch, pares de tipos, registro não mapeado e incompatibilidades. Ambos os
helpers passaram C89 estrito e ASan/UBSan; r22/r24 e auditorias de bytes,
manifesto e hashes também passaram. O manifesto agora contém 12 entradas
manuais: 11 modelos C semânticos parciais e um stub; 37 artefatos manuais e
3.678 artefatos base. I342r3 e Q102r191 foram atualizados via CLI SQLite. Isso
avança reconstrução estática no host, sem cumprir ainda a compilação/execução
Apollo. A estimativa do objetivo integral segue perto de 10%, baseada no
inventário e nesses modelos parciais, sem inferir cobertura funcional.

Complemento I342 (14-10): reconstruí também o helper `LookAheadForCycleOrMulticlick`
(408 bytes) em C semântico host, com lookup A5 injetado, contagem por seletores,
flag bit-30, pares de tipos 4/5 e 2/3 e comparações de dados. O teste de
`PrintComplexState` agora chama esse helper e valida a sequência repetição +
branch até o adaptador de texto. Os testes C89/ASan/UBSan de ambos passaram; os
verificadores r22/r24, hash do intervalo machine-code, auditoria do manifesto
(3.678 artefatos base, 12 entradas manuais) e 1.883 hashes também. I342r3 e
Q102r191 receberam atualização por CLI; nenhuma resposta/autorização da pessoa
foi modificada. A validação Apollo e a migração continuam pendentes. Avanço
estimado total permanece ~10%: há progresso na análise estática e modelos host,
mas o requisito central de compilar/executar no guest ainda não foi cumprido.

Complemento I342 (14-10): reconstruí `PrintActions` (368 bytes), com iteração
nos registros, resolução A5 de prefixo/nome, chamada injetada a `PrintParams`,
redimensionamento e cursor. O teste `PrintComplexState` agora integra os modelos
host de `LookAheadForCycleOrMulticlick` e `PrintActions`; C89 estrito e
ASan/UBSan passaram para as três rotinas, assim como os verificadores r22/r24,
auditoria de hashes de bytes, manifesto e 1.886 hashes. Totais auditados:
3.678 artefatos base, 12 modelos C semânticos parciais e um stub (13 entradas,
40 artefatos manuais). I342 e Q102 foram atualizadas no canal SQLite. A
estimativa global permanece ~10%: inventário/estática avançaram, porém compilar
e executar na Apollo ainda não aconteceu. Sem alteração de VM, rede, ftpd ou
disco; próximo: seguir nas dependências estáticas enquanto aguarda acesso ao
guest para cumprir a validação solicitada.

Complemento I342 (14-10): modelei também `PrintParams` (218 bytes), que percorre
tokens, faz quoting/separação e aplica a condição de buffer observada. O teste
de `PrintActions` agora chama este modelo; o teste de `PrintComplexState`
integra `LookAheadForCycleOrMulticlick` e `PrintActions`. Quatro suítes C89
estritas e ASan/UBSan, verificadores Ghidra r22/r24, hashes dos três intervalos,
auditoria do manifesto e 1.889 hashes passaram. Estado auditado: 3.678
artefatos base, 13 modelos semânticos host parciais e um stub (14 entradas,
43 artefatos manuais). I342/Q102 foram atualizadas pela CLI SQLite preservando
campos da pessoa. O avanço continua estimado em ~10% porque a validação
Apollo ainda não começou; os testes host não substituem essa etapa. VM/rede/
ftpd/disco permanecem sem alterações.

Complemento I342 (14-10): modelei `PrintEvent` (210 bytes) com despacho por
tipo e adapters para os formatadores irmãos. A suíte de `PrintComplexState`
agora integra esse helper, o lookahead e `PrintActions`; a suíte de ações
integra `PrintParams`. Cinco suítes relacionadas passaram C89 estrito e
ASan/UBSan, além dos verificadores Ghidra r22/r24, hashes dos quatro intervalos,
auditoria do manifesto e 1.892 hashes. Totais: 3.678 artefatos base, 14 modelos
C host parciais e um stub (15 entradas manuais, 46 artefatos). I342/Q102 foram
atualizadas por CLI SQLite sem mudar dados da pessoa. A validação Apollo ainda
falta; estimativa global continua ~10% pelo escopo amplo e ausência do build/run
guest. Sem alteração na VM, rede, ftpd ou disco.

Complemento I342 (14-10): reconstruí `PrintLateModifiers` (186 bytes), com
registros de seis bytes, comparação de capacidade signed observada na assembly,
crescimento, truncamento e salto da entrada seguinte. A suíte de `PrintEvent`
agora chama o helper host real. As seis suítes TMprint passaram C89 estrito e
ASan/UBSan; r22/r24 e auditoria do manifesto passaram. Totais: 3.678 artefatos
base, 15 modelos C host semânticos + um stub (16 entradas manuais), 49 artefatos
manuais e 1.895 hashes válidos. I342r3 e Q102r191 foram atualizadas pela CLI
após revalidar as revisões, preservando os campos da pessoa. Compilação, link e execução Apollo continuam
pendentes; avanço estimado do objetivo integral permanece ~10% pelo inventário,
análise estática e modelos parciais, sem equivalência entre número de testes e
código recuperado. I361 permanece sem autorização; nenhuma alteração na VM,
rede, ftpd ou disco.

Para o pedido de ampliar conexões do ftpd, consultei o estado salvo: I361 está
queued, revisão 0 e `user.authorized=false`. Não usei Telnet nem alterei a VM.
Criei Q362 depois de I361 solicitando autorização pelo escopo já descrito; a
pergunta foi respondida pela CLI e aguarda a pessoa. Q102r191 também recebeu o
aviso e seguirá como canal de comunicação.

Complemento I342 (14-10): reconstruí também `PrintEventType` (452 bytes), com
offsets da tabela A5 para eventos 2–33 e -1, fallback para outros valores,
comparação signed da capacidade, crescimento e avanço do cursor. O teste de
`PrintEvent` agora executa este modelo nos caminhos conhecido e desconhecido.
Sete suítes TMprint passaram C89 estrito e ASan/UBSan; verificadores r22/r24,
hash de intervalo, manifesto e todos os 1.898 hashes passaram. Totais: 3.678
artefatos base, 16 modelos C host semânticos + um stub (17 entradas), 52
artefatos manuais. Ainda sem validação Apollo. Confirmei o estado ao vivo antes
de prosseguir: não há processo MAME ativo; o bridge tem uma solicitação de
13-10 sem resposta e não foi substituída; a interface TAP da VM está DOWN,
Telnet expira e FTP retorna “sem rota”. Não reiniciei MAME nem alterei guest,
rede ou disco. Avanço integral segue perto de 10%, com base no inventário e
análise estática parcial, sem inferir cobertura pelo número de testes.

Complemento I342 (14-10): reconstruí `PrintCode` (160 bytes), com crescimento
antecipado do buffer, caminho sem formatação para código zero, formato normal
em A5+0x180 e sentinela -1 em A5+0x18c. A integração de `PrintEvent` agora
encadeia os modelos reais de `PrintEventType` e `PrintCode`. Oito suítes TMprint
passaram C89 estrito e ASan/UBSan; r22/r24, hash de intervalo, manifesto e
1.901 hashes passaram. Totais: 3.678 artefatos base, 17 modelos C host
semânticos e um stub (18 entradas manuais), 55 artefatos. A validação Apollo
continua indisponível: nenhum processo MAME ativo, bridge antigo pendente sem
resposta, TAP DOWN e guest sem resposta. Nenhuma mudança em VM/rede/disco; o
avanço integral segue ~10% pelo escopo amplo e ausência de build/run guest.

Complemento I342 (14-10): reconstruí `PrintKeysym` (158 bytes) e seu caminho
`PrintCode(-1, keysym)` para keysym sem nome. `PrintEvent` integra agora os
modelos de `PrintEventType`, `PrintKeysym` e `PrintCode`; testes verificam nome
conhecido e fallback, além dos ramos diretos. Nove suítes TMprint passaram C89
estrito e ASan/UBSan; r22/r24, manifesto, intervalo machine-code e 1.904 hashes
passaram. Totais: 3.678 artefatos base, 18 modelos semânticos + um stub (19
entradas), 58 artefatos manuais. O helper privado de cópia recebe token nulo no
fallback; esse comportamento Apollo ainda não foi comprovado. A VM continua
sem processo MAME e TAP acessível, portanto build/link/run guest pendente e
estimativa integral ~10%.

Complemento I342 (14-10): reconstruí `PrintAtom` (178 bytes), incluindo
consulta dependente do display, fallback `PrintCode(-1, atom)` e crescimento
de buffer calculado com comprimento da string. `PrintEvent` integra agora os
modelos de `PrintEventType`, `PrintKeysym`, `PrintAtom` e `PrintCode`; testes
cobrem nome e fallback em cada caminho. Dez suítes TMprint passaram C89 estrito
e ASan/UBSan; r22/r24, hash de intervalo, manifesto e 1.907 hashes passaram.
Totais: 3.678 artefatos base, 19 modelos semânticos + um stub (20 entradas) e
61 artefatos manuais. Sem validação Apollo. O efeito dos helpers privados de
cópia/medição com token nulo continua desconhecido e está registrado, sem
assumir equivalência ao host. A VM segue sem MAME/TAP disponíveis.

Complemento I342 (14-10): reconstruí `PrintModifiers` (1.186 bytes), com ordem
dos 13 bits e offsets A5, regras de `~`/espaço e o caso AnyModifier (`!`). O
teste de `PrintEvent` chama este modelo; a suíte isolada valida todos os offsets,
ordem e crescimento. Onze suítes TMprint passaram C89 estrito e ASan/UBSan;
r22/r24, hash de intervalo, manifesto e 1.910 hashes passaram. Totais: 3.678
artefatos base, 20 modelos C host semânticos + um stub (21 entradas) e 64
artefatos manuais. Strings reais de modifiers seguem privadas/injetadas; ainda
sem build/link/execução Apollo. O bloqueio do guest permanece, sem alteração de
VM, rede ou disco.

Complemento (14-10): a solicitação de elevar conexões simultâneas do ftpd foi
conferida novamente no estado autoritativo da prancheta. I361 permanece com
`user.authorized=false`; Q362 já pede a autorização salva para esse escopo.
Conforme a regra de execução por item, a mensagem recebida nesta conversa não
substitui esse campo. Não usei Telnet e não alterei serviço, VM, rede ou disco.
Q102r191 foi atualizado pela CLI, preservando a mensagem e a autorização do
usuário; o próximo passo é a pessoa autorizar I361 na aplicação.

Complemento I342 (14-10): reconstruí mais três funções do caminho de tradução
Xt: `FindNextMatch` (212 bytes), `ProcessStateTree` (202) e
`ProcessLaterMatches` (284), com offsets e intervalos conferidos no assembly
capturado e em callers diretos. Os modelos host usam memória big-endian e
callbacks privados explícitos; não são fonte original nem ABI Apollo. A suíte
atual de 22 testes passou C89 estrito e ASan/UBSan; os verificadores Ghidra
r22/r24, hashes dos três intervalos, 3.687 artefatos do manifesto, 73 manuais e
1.919 entradas SHA256SUMS também conferem. A Apollo continua indisponível:
nenhum processo MAME, TAP sem carrier e solicitação antiga do bridge ainda sem
resposta. Q354 segue sem autorização para retomar a VM; não reiniciei MAME nem
alterei guest, rede, disco ou ftpd. Estimativa do objetivo integral permanece
~10%, baseada no escopo amplo e na falta de compilação/link/execução Apollo;
contagem de testes não é medida de código recuperado.

I342 — refinamento da prova (14-10): `test_xtlib_ProcessStateTree.c` agora
encadeia os modelos reais `ProcessStateTree` → `ProcessLaterMatches` →
`FindNextMatch`; não usa um mock no helper lateral. Reexecutei as 22 suítes
C89 estritas e ASan/UBSan após essa integração. Os hashes e os dois inventários
(3.687 artefatos base, 73 manuais, 1.919 checksums) foram recalculados e
validados; nenhuma alteração no guest.

Complemento I342 (14-10): modelei também `PrintState` (326 bytes), recuperando
os seis slots de argumento pelos pushes de `_XtPrintXlations`, que o pseudo-C
base omitia. O modelo cobre os ramos especial/comum, lookup das tabelas A5 com
strides 16/14, buffer +100/relocação, registro de ações temporário e roteamento
para `PrintComplexState`. As 23 suítes passaram C89 estrito e ASan/UBSan;
r22/r24 e hash do intervalo passaram. Manifesto: 3.690 artefatos base e 76
manuais; SHA256SUMS: 1.922 entradas verificadas. I342 continua parcial: sem
processo MAME, TAP DOWN/NO-CARRIER, solicitação antiga da bridge sem resposta e
Q354 sem autorização para retomar a VM. Não reiniciei MAME nem alterei guest,
rede, disco ou ftpd. Estimativa integral continua ~10%, pelo volume de
binários/dependências ainda sem fonte reconstruída e pela ausência de
compilação/link/execução Apollo; número de testes não mede cobertura do produto.

## 2026-10-14 — I342 `_XtPrintXlations` e pedido de capacidade do ftpd

A I342 rev3 segue autorizada e parcial. Foi acrescentado o modelo semântico host
`_XtPrintXlations` (314 bytes, `0x5c6b8..0x5c7f2`), com hash do trecho executável
confirmado diretamente na imagem. Os callers confirmam os offsets das árvores e
os seis argumentos de `PrintState`. Os testes exercitam árvore nula, dois pares,
argumentos, relocação do buffer de saída e os limites de 250/251 registros. Os
24 testes standalone passaram C89 estrito e ASan/UBSan; verificações Ghidra r22 e
r24, 3.693 artefatos do manifesto e 1.925 checksums passaram. Recibo em
`/home/lsi/Documents/Projetos/help_viewr_rev/analysis/reconstruction-c/xtlib-XtPrintXlations.evidence.json`.
Esses resultados validam modelos no host; não provam fontes originais, ABI,
compilação, link ou execução na Apollo. Progresso estimado de I342: ~10%, baseado
no grande escopo de aplicação/dependências e na ausência de validação guest, não
na contagem de testes.

O pedido de aumentar conexões do ftpd está registrado em I361; `user.authorized`
continua falso e Q362 pede autorização salva antes de usar Telnet. Q354 também
continua sem resposta: não há autorização para retomar/iniciar MAME. Não usei
Telnet, não alterei o serviço, a VM ou a rede. Próximo: aguardar as autorizações
próprias de I361/Q354; até lá, prosseguir somente com reconstrução host que não
dependa do guest. Q102r191 recebeu a atualização e o relato de deslocamento do
menu de preferências permaneceu intacto.

## 2026-10-14 — I342 wrappers de saída Xt

Avancei os dois callers de 72 bytes de `_XtPrintXlations`:
`_XtDisplayTranslations` lê a árvore em `widget+0x2c` e usa destino A5+`0x1a0`;
`_XtDisplayAccelerators` lê `widget+0x3c` e usa A5+`0x1a4`. Ambos chamam o
renderer com prefixo 0 e modo 1, exibem a saída e a liberam. Os intervalos foram
hasheados diretamente da imagem. Modelos, testes e recibo estão em
`/home/lsi/Documents/Projetos/help_viewr_rev/analysis/reconstruction-c/`.
Todos os 25 testes standalone passaram C89 estrito e ASan/UBSan; verificações
Ghidra r22/r24, manifesto (3.696 artefatos; 82 manuais) e checksums (1.928)
passaram. Isso é evidência host e estática, sem build ou runtime Apollo.
Progresso total I342 estimado em ~10%, pelo escopo da aplicação/dependências e
pela validação no guest ainda ausente.

A VM continua sem processo MAME, TAP `NO-CARRIER`; o bridge mantém o pedido
antigo sem resposta. Q354 continua sem resposta e não iniciei nem reiniciei a VM.
I361 segue com `user.authorized=false`; Q362 continua pedindo autorização salva
antes do uso de Telnet. Nenhuma alteração no guest, serviço ftpd, disco ou rede.
Próximo trabalho independente: reconstruir o caminho seguinte em `TMprint.c` e
continuar o inventário sem inferir autorização para o ftpd ou para retomar MAME.

## 2026-10-14 — I342 `_XtDisplayInstalledAccelerators`

Reconstruí o caminho Xt de 390 bytes que resolve e apresenta aceleradores
instalados. O hash direto da faixa `0x5c882..0x5ca08` confere com o recibo.
O modelo representa explicitamente os hooks A5, testa o sinalizador da lista,
filtra as branches pelo widget correspondente, seleciona vetor local/dinâmico,
chama os modelos `ProcessStateTree`/`PrintState` por adapters e preserva a ordem
de liberação/exibição vista na assembly. Cinco casos dedicados passaram C89
estrito e ASan/UBSan. A suíte toda passou com 26 testes em cada perfil; r22/r24,
manifesto (3.699 artefatos, 85 manuais/29 entradas de função) e 1.931 checksums
passaram. Recibo:
`/home/lsi/Documents/Projetos/help_viewr_rev/analysis/reconstruction-c/xtlib-XtDisplayInstalledAccelerators.evidence.json`.

Essas provas são estáticas/host; os callbacks A5, ABI, compilação/link e runtime
Apollo seguem pendentes. A estimativa total I342 continua ~10% diante do escopo
completo e do bloqueio de acesso guest. A sessão MAME não está ativa, TAP está
sem carrier e o pedido anterior do bridge segue pendente. Q354 permanece sem
resposta; I361 sem autorização salva e Q362 aguardando. Nenhum comando Telnet,
reinício, alteração de rede, disco ou ftpd foi realizado. Próximo passo: seguir
reconstruindo os símbolos de `TMprint.c` no host, preservando as incertezas dos
layouts privados, enquanto aguardamos acesso/autorização do guest.

## 2026-10-14 — I342 wrappers `_XtPrintActions` e `_XtPrintState`

Modelei os wrappers de 72/80 bytes do `TMprint.c`. A assembly confirma que ambos
alocam e inicializam buffer de 1000 bytes e retornam a base atual após os helpers.
`_XtPrintActions` passa os dois argumentos e prefixo zero; `_XtPrintState` passa
branch/registro, modo 1 e prefixo/contexto zero. Os testes verificam esses
argumentos e a base relocada. A suíte inteira passou com 27 testes standalone
em C89 estrito e ASan/UBSan; r22/r24 também passaram. Manifesto agora tem 3.702
artefatos (88 manuais/31 entradas de função) e SHA256SUMS tem 1.934 caminhos;
checksums conferidos. Recibo:
`/home/lsi/Documents/Projetos/help_viewr_rev/analysis/reconstruction-c/xtlib-XtPrintWrappers.evidence.json`.

A validação continua somente no host: hooks A5, ABI e build/runtime Apollo ainda
não foram demonstrados. A estimativa integral I342 permanece ~10%, pelo escopo
completo e falta de execução guest. A sessão guest segue fora de alcance sem a
decisão de Q354; não toquei em VM, rede ou ftpd. I361 continua sem autorização
salva. Próximo símbolo em TMprint é `_XtPrintEventSeq` (334 bytes), cujo fluxo de
até 100 registros exige reconstrução cuidadosa antes dos testes.

## 2026-10-14 — coordenação/revisão de `_XtPrintEventSeq`

Durante esta revisão, os arquivos `xtlib-XtPrintEventSeq.c` e
`test_xtlib_XtPrintEventSeq.c` mudaram enquanto os builds estavam em andamento.
O teste alternou entre compilar a fonte como unidade separada e incluí-la no
próprio teste; uma compilação intercalada recebeu definições duplicadas. Parei de
editar esse par. No snapshot estável mais recente, o teste standalone passou em
C89 estrito e ASan/UBSan; hash do código-fonte executável em
`0x5caa0..0x5cbf0`: `1d2d5636a89c2124699b09ae9537c0880fce7a771ea73d3507abcb259243b48e`.
A revisão encontrou um caso a corrigir/decidir: para sequência vazia a assembly
aloca e retorna sem resolver as tabelas privadas, mas o modelo atualmente exige
as tabelas antes de retornar. O teste vazio usa tabelas válidas e não cobre essa
condição. Não registrei ainda esse código como artefato estável no manifesto.

Abri Q363, depois de I342, perguntando se devo continuar apenas auditando enquanto
a outra IA edita esse símbolo ou assumir a edição exclusiva dele; Q102 foi
atualizada e preserva o relato original de menu deslocado. A resposta da pessoa
é necessária para evitar sobrescrever o trabalho concorrente. I342 continua
parcial e a validação Apollo segue ausente. Nenhum guest/VM/rede/ftpd foi tocado.

### Revalidação de suíte durante Q363

Após a pergunta de coordenação, o par atual de arquivos ficou estável durante a
execução completa. Rodei cada um dos 28 testes standalone, incluindo
`test_xtlib_XtPrintEventSeq.c`, em C89 estrito e em ASan/UBSan; ambos os perfis
passaram. O recibo `analysis/reconstruction-c/host-suite-validation-20261014.json`
foi atualizado para 28 e registra que a análise do caso vazio permanece aberta.
Q102 foi respondida na revisão 191, sem alteração da nota do usuário; Q363 segue
aguardando decisão sobre quem edita o símbolo. O código ainda não foi adicionado
ao manifesto/checksums enquanto a revisão semântica e a coordenação estão abertas.

### I342 — modelo independente do Help Viewer (14-10-2026)

Acrescentei um modelo host de `vuehelp:StartDisplayFileBMS`, função SR10.4 de
388 bytes, em `help_viewr_rev/analysis/reconstruction-c/`. O recibo registra o
hash direto da faixa de assembly, os caminhos de erro/sucesso e os limites dos
adaptadores A5. O teste dedicado passou C89 estrito e ASan/UBSan. Reexecutei a
suíte: 29 testes standalone passaram nos dois perfis; `test_apollo_layout.c` é
uma asserção incluída por outro teste, não um executável independente. O
resultado foi salvo em `host-suite-validation-20261014-r6.json`.

Q363 permanece sem resposta, então não alterei `_XtPrintEventSeq`, cujo
caminho de lista vazia ainda difere da assembly. MAME continua ausente, TAP sem
carrier e bridge com pedido sem resposta; não reenviei comando nem toquei na VM.
I361 segue com autorização falsa: nenhum Telnet ou ajuste do ftpd foi feito. A
I342 permanece parcial (~10%, estimativa pelo escopo amplo e falta de build e
execução Apollo), e este trabalho host não substitui a validação no guest.

Continuação: também modelei `vuehelp:StartDbUpdateBMS` (170 bytes,
`0x41d38..0x41de2`), com o encadeamento de estado, os helpers do banco, a
atribuição do recurso primário e o percurso das entradas de 32 bytes. O teste
dedicado passou C89 estrito e ASan/UBSan. A suíte completa agora tem 30 testes,
aprovados nos dois perfis. O manifesto r8 registra 3.716 artefatos, 34 modelos
manuais e 99 artefatos manuais; os 1.942 caminhos de SHA256SUMS passaram.
Q363 e o bloqueio de acesso Apollo continuam sem resposta; I361 continua sem
autorização, então Telnet/ftpd permanecem intocados.

Mais uma unidade host da I342: `vuehelp:MessageSetup`, função de 176 bytes em
`0x41de2..0x41e92`. O modelo preserva o gate condicional, argumentos e ordem das
duas inscrições de mensagem, hooks do banco, instalação dos callbacks e escrita
final da flag. O teste dedicado e a suíte completa passaram C89 estrito e
ASan/UBSan: 31 testes standalone em cada perfil. Manifesto r9: 3.720 artefatos,
35 modelos manuais e 103 artefatos manuais; SHA256SUMS validado com 1.946
caminhos. A sessão Apollo e as autorizações pendentes não mudaram.

### I342 — `vuehelp:ManageTopicWindow` (14-10-2026)

Modelei a rotina de 304 bytes em `0x41e92..0x41fc2`: busca/validação do tópico,
tratamento opcional do erro, criação de janela ou atualização e ativação da
existente. Os testes cobrem o estado novo/aberto e os dois layouts selecionados
por bit de classe. A suíte passou com 32 testes standalone em C89 estrito e
ASan/UBSan. O manifesto r10 contém 3.724 artefatos, 36 modelos manuais e 107
artefatos manuais; os 1.950 caminhos de SHA256SUMS passaram. Continua faltando
validação Apollo; Q354/Q363 seguem sem resposta e I361 sem autorização salva.

### I342 — `vuehelp:StartTopicsListBMS` (14-10-2026)

Reconstruí em modelo C host a função de 152 bytes `0x419ae..0x41a46`. O modelo
encaminha os argumentos ao construtor da lista, trata o objeto global de erro,
seleciona o tópico pelas duas variantes do registro e preserva a codificação do
status de notificação. O teste dedicado e a suíte completa passaram C89 estrito
e ASan/UBSan, com 33 testes standalone. Manifesto r11: 3.728 artefatos, 37
modelos manuais e 111 artefatos manuais; os 1.954 checksums passaram. A
validação Apollo e as respostas pendentes continuam necessárias.

### I342 — `vuehelp:StartTopLevelBMS` (14-10-2026)

Acrescentei modelo host para a função de 144 bytes `0x41a46..0x41ad6`, com
ponteiros do estado, builder, gate de erro, escolha dos dois layouts e palavra de
status derivada do endereço de retorno. O teste individual e os 35 testes
standalone passaram em C89 estrito e ASan/UBSan. A primeira execução da suíte
colidiu com um binário temporário de nome compartilhado; a repetição com nomes
únicos passou e os hashes dos arquivos do outro modelo Xt ficaram estáveis.
Manifesto r12: 3.732 artefatos, 38 modelos manuais, 115 artefatos manuais e
1.958 checksums, todos validados. Apollo continua sem execução.

### I342 — `vuehelp:StartManualPagesBMS` (14-10-2026)

Modelei a rotina de 86 bytes `0x41ad6..0x41b2c`: builder, chamada de comparação
com retorno descartado e despacho na ordem da assembly. A suíte passou com 36
testes standalone em C89 estrito e ASan/UBSan. Os hashes das fontes dos testes
ficaram iguais antes/depois; usei executáveis temporários únicos. Manifesto r13:
3.736 artefatos, 39 modelos manuais, 119 artefatos manuais; 1.962 checksums
validados. A validação Apollo ainda falta.

### I342 — `vuehelp:ErrorHandler` (14-10-2026)

Modelei a rotina de 88 bytes `0x415f0..0x41648`: buffer local de 1.032 bytes,
formatação e preservação do retorno, busca do catálogo `(4, 0x1f, A5+0xdb0)` e
exibição em modo 2. O teste individual passou; a suíte completa passou com 37
testes standalone em C89 estrito e ASan/UBSan, com hashes das fontes estáveis.
Manifesto r14: 3.740 artefatos, 40 modelos manuais, 123 artefatos manuais e
1.966 checksums validados. Ainda sem compilação/execução Apollo.

### I342 — `vuehelp:usage` (14-10-2026)

Modelei a rotina de 176 bytes `0x416f4..0x417a4`: quatro consultas ao catálogo
e append na mesma posição, seguidas da solicitação de saída com status 1. O
modelo não presume a semântica do helper privado de append. A suíte passou com
38 testes standalone em C89 estrito e ASan/UBSan, fontes estáveis durante a
execução. Manifesto r15: 3.744 artefatos, 41 modelos manuais, 127 artefatos
manuais e 1.970 checksums validados. Falta validação Apollo.

### I342 — `vuehelp` signal handlers (14-10-2026)

Registrei um modelo host de `HandleDeath`, `HandleXvStopDeath`, `HandleChildDeath` e `HandleBrokenPipe` baseado nas faixas assembly de SR10.4. O teste comprova ordem e argumentos dos callbacks injetados, incluindo o evento `0x01000000`; passou em C89 estrito e ASan/UBSan como parte da suíte completa 39/39. Artefatos e limites estão no projeto `help_viewr_rev`, em `analysis/reconstruction-c/vuehelp-SignalHandlers.{c,evidence.json}` e no recibo r16. Hashes do manifesto e `SHA256SUMS` foram validados. A evidência é do host e não comprova ABI, build ou execução Apollo. Q354/Q363 ainda sem resposta; I361 permanece não autorizada, sem Telnet ou mudança de ftpd. Próximo passo I342: recuperar acesso autorizado ao guest para compilar/executar; até lá, continuar apenas reconstrução host com evidência suficiente e sem tocar no símbolo `_XtPrintEventSeq` pendente.

### I342 — `vuehelp:StripWMHints` e revalidação de acesso (14-10-2026)

A rotina `StripWMHints` (172 bytes, `0x41648`) foi modelada como adapter host; cobre gate `0x15`, seleção de hint pelos dois layouts de classe, alterações do registro e releitura do bit antes de anexá-lo. Testes dedicados passaram e a suíte completa agora passa 40/40 C89 estrito e 40/40 ASan/UBSan. Manifesto r17 contém 3.752 artefatos; hashes internos e SHA256SUMS conferidos. Acesso Apollo testado novamente em modo somente leitura: rota aponta à TAP, mas TCP/23 expira e TCP/21 dá “No route to host”; não há processo MAME e a TAP está DOWN/NO-CARRIER. Nenhum guest, ftpd ou limite global foi alterado. I346 está autorizada, mas Q351 ainda pede o alvo e autorização para limites globais caso necessários; Q354 segue sem resposta para retomada do MAME. Próximo avanço I342: aguardar uma rota/sessão Apollo disponível, sem reiniciar; reconstrução host continua parcial e não substitui compilação/link/execução guest.

Complemento de I342 na mesma sessão: modelei também `vuehelp:StartTopLevel` (50 bytes, `0x422e2`), que cria buffer local de 50 bytes e despacha a raiz de estado desreferenciada, a mensagem e zero. Teste dedicado passou; suíte atual 42/42 C89 estrito e ASan/UBSan. Manifesto r18: 3.756 artefatos, 47 modelos C semânticos host e 139 artefatos manuais; hashes completos válidos. Isso continua sendo reconstrução host, sem prova de ABI nem build Apollo. A VM permanece indisponível, sem rota Telnet/FTP; não reiniciei MAME. I346 está autorizada, mas rede guest falha; Q351 pede target/escopo de limite global se for preciso exceder as sessões já observadas. Q354 aguarda decisão sobre retomar MAME.

Complemento I342: modelei `vuehelp:StartAtIndex` (288 bytes, `0x42316`) com separação do nome/diretório pelo último `/`, mutação do argumento original, fallback ao diretório padrão, buffer de saída e mensagem/exit em erro. Casos relativos, absolutos, raiz e erro passaram na suíte completa: 43/43 C89 estrito e 43/43 ASan/UBSan. Manifesto r19 lista 3.760 artefatos (48 modelos host e 143 itens manuais); verificações de hashes passam. Revalidação de acesso ao guest continua igual: Telnet sem resposta, FTP sem rota, TAP sem carrier e MAME ausente; nenhuma tentativa de iniciar/reiniciar foi feita. Q354 ainda sem resposta. Próximo passo guest continua condicionado à restauração/autorização correspondente.

Complemento I342: acrescentei modelo de `InstallMsgServerCallbacks` (240 bytes, `0x41804`), preservando seis registros na ordem do binário, seus endereços A5, handlers opacos, masks `3,3,1,2,1,2` e argumentos zero. O teste confere cada argumento. Suíte: 44/44 C89 estrito e 44/44 ASan/UBSan; manifesto r20: 3.764 artefatos, 49 modelos semânticos host, todos os hashes internos e SHA256SUMS conferidos. O guest segue indisponível (TAP DOWN/NO-CARRIER, sem MAME) e Q354 aguarda resposta; sem build/link/execução Apollo. Nenhum guest reiniciado ou alterado.

I342 — `RestoreSession` (338 bytes, `0x43f9a`) foi reconstruída como adapter host baseada na assembly, cobrindo seleção de widget, seletor/abertura da sessão, três rotinas de restauração ordenadas, alertas e limpeza. Um caso incomum da condição final de fechamento permanece explicitamente registrado e aguarda checagem no guest. Também registrei `history_stack_int` (40 bytes) que já estava no workspace: os quatro clears e o valor imediato/retorno `0x19` conferem com a assembly. Suíte combinada passou 46/46 em C89 estrito e ASan/UBSan; manifesto r21 contém 3.771 artefatos e 51 modelos host; hashes internos/SHA256SUMS conferidos. A Apollo continua inacessível (TAP DOWN/NO-CARRIER, nenhum MAME); Q354 sem resposta. Nenhuma reinicialização ou alteração do guest.

Complemento I342: `CreateTopLevels` (242 bytes, `0x420ea`) agora está modelada com os dois pares de criação, valores de argumentos, armazenamento dos handles e atualização de recurso `0x3e` nos dois widgets. Teste verifica todos os parâmetros; suíte atual passou 47/47 em C89 estrito e ASan/UBSan. Manifesto r22 lista 3.775 artefatos e 52 modelos host; tamanhos e hashes internos e SHA256SUMS conferidos. Guest segue inacessível, sem MAME e TAP DOWN/NO-CARRIER; Q354 sem resposta. Sem build/execução Apollo, sem mudança ou reinício do guest.

Complemento I342: `CreateViewStruct` (262 bytes, `0x421dc`) agora integra o modelo `CreateTopLevels` à sequência de inicialização, seleção de window pelo bit de classe, consulta de atributos e escrita de recursos. O teste integrado verifica ambas as classes e retorno da consulta; 48/48 testes passaram em C89 estrito e ASan/UBSan. Manifesto r23: 3.779 artefatos, 53 modelos host; verificações completas de tamanho/hash passaram. A Apollo segue sem MAME e TAP DOWN/NO-CARRIER; Q354 sem resposta. Build/execução no guest ainda necessários; nenhuma ação de reinicialização ou alteração.


## 2026-10-14 — I346: nova tentativa de acesso Telnet ao Apollo

O usuário reiterou que deseja ampliar as conexões do ftpd por Telnet. A autorização salva de I346 (revisão 1) foi conferida. A inspeção atual encontrou `tap-mess-1000-0` `UP/NO-CARRIER` e `DOWN`, nenhum processo MAME do guest; conexão TCP/23 e TCP/21 a `192.168.240.2` retornou `No route to host`. Nenhuma sessão Telnet foi aberta nem configuração alterada. I346 permanece aguardando a sessão. Q354 ainda não recebeu resposta sobre a retomada controlada do MAME; não iniciei o emulador. Q351 também permanece sem decisão sobre alvo e possível alteração de limites globais; nenhum limite global foi tocado. Próximo passo: aguardar resposta salva a Q354; com a sessão acessível, medir primeiro a capacidade corrente e seguir apenas o escopo autorizado de I346.


## 2026-10-14 — I342: despacho de inicialização de `main` (r25)

Reconstruí como adapter host o bloco de 66 bytes `0x44498..0x444da`, que despacha `RestoreSession`, `StartAtIndex`, `StartUnMapped` ou `StartTopLevel` por prioridade dos slots de argumento. Evidência, hash binário, teste e limites estão em `help_viewr_rev/analysis/reconstruction-c/vuehelp-DispatchStartup.{c,evidence.json}`. A suíte passou 49/49 em C89 estrito e ASan/UBSan. Manifesto r25 contém 3.787 artefatos, 55 modelos C host e 170 registros manuais; tamanhos e hashes dos artefatos e 2.023 entradas de `SHA256SUMS` foram conferidos. Isso modela somente o bloco de despacho, não `main` inteiro nem ABI/build/link/runtime Apollo. Nova medição da VM: sem processo MAME, TAP `DOWN/NO-CARRIER`, TCP/23 expira; não houve reinício. Q354 continua sem resposta e `_XtPrintEventSeq` ficou intocado com Q363 pendente. Próximo: continuar reconstrução host de partes centrais/dependências de I342 e aguardar Q354 antes de qualquer inicialização da VM. Estimativa integral segue ~10%, baseada no volume ainda por reconstruir e na ausência de compilação/execução Apollo; o número de testes não mede fidelidade.


## 2026-10-14 — I342: bloco de contexto de `main` (r26)

Reconstruí em C host os primeiros 270 bytes de `main` (`0x44214..0x44322`): catálogo, basename de `argv[0]`, `GlobalInit`, criação do contexto, seleção do handle de janela pelo bit `0x04`, attach, hooks A5 opacos, registro de callbacks e gate de `usage`. O teste valida sequência, tokens encaminhados, duas classes e `argc` alterado pelo hook; modelo/evidência ficam em `help_viewr_rev/analysis/reconstruction-c/vuehelp-MainContextSetup.{c,evidence.json}`. Junto ao adapter anterior do despacho em `0x44498..0x444da`, existem modelos para 336 dos 756 bytes de `main`, em blocos separados; o miolo e o cleanup continuam sem integração. Suíte host: 50/50 C89 estrito e 50/50 ASan/UBSan. Manifesto r26: 3.791 artefatos, 56 modelos C, 174 registros manuais; hashes/tamanhos do manifesto e 2.028 entradas SHA256SUMS passaram. Isso não valida o `main` inteiro nem ABI/build/link/runtime Apollo. Estado da VM conferido nesta sessão: sem MAME, TAP `DOWN/NO-CARRIER`, TCP/23 expira; não reiniciei nem alterei o guest. Q354 e Q363 continuam pendentes. Próximo: modelar o trecho de inicialização de mensagens, banco e janelas com os hooks realmente identificáveis, depois auditar o startup inteiro; aguardar Q354 antes de iniciar Apollo. Estimativa integral permanece ~10%, pelo escopo amplo de dependências e falta de compilação/execução guest, não pela contagem de testes.


## 2026-10-14 — I342: cobertura assembly completa de `main` em adapters (r27)

Acrescentei adapters host para o intervalo de mensagens/banco/janelas (`0x44322..0x44498`, 374 bytes) e para a notificação/limpeza final (`0x444da..0x44508`, 46 bytes). Com os blocos anteriores, os intervalos `0x44214..0x44322` (270), `0x44322..0x44498` (374), `0x44498..0x444da` (66) e `0x444da..0x44508` (46) cobrem sem lacuna os 756 bytes de `main`. Cada bloco tem adapter, evidência de assembly/hash e teste independente; ainda falta a integração host conjunta, e hooks/layouts/ABI Apollo permanecem abstraídos. Casos cobrem sucesso/falha do banco, callback/dialog/exit, duas classes de janela, recursos, eventos/ações e gate de limpeza. Suíte: 52/52 C89 estrito e 52/52 ASan/UBSan. Manifesto r27: 3.798 artefatos, 58 modelos semânticos C e 181 registros manuais; hashes/tamanhos validados e 2.036 linhas SHA256SUMS passaram. Apollo continua sem MAME, TAP `DOWN/NO-CARRIER`, TCP/23 em timeout; sem reinício ou alteração. Q354 e Q363 ainda sem resposta. Próximo: integrar os quatro adapters em uma prova host do fluxo completo, depois continuar a auditoria das dependências e aguardar a autorização para retomar a VM. Estimativa integral permanece ~10%: o escopo de dependências não tem denominador finito estabelecido e a prova de compilação/execução Apollo ainda falta; contagem de testes não representa fidelidade.


## 2026-10-14 — I342: `main` conectado em fluxo host integrado (r28)

`VueHelpMainFlowHost` agora encadeia os quatro adapters que cobrem `0x44214..0x44508` (756 bytes), propagando a janela inicial e o token do widget raiz. A prova end-to-end cobre startup no topo e falha de abertura da base com hook de exit simulado que retorna, seguida de restauração de sessão e cleanup. Ela valida contratos host e ordem dos hooks, não a ABI Apollo nem o comportamento real do `exit`. Suíte r28: 53/53 C89 estrito e 53/53 ASan/UBSan. Manifesto: 3.805 registros de artefato, 59 modelos/fluxos C host e 188 registros manuais; tamanhos e hashes de todos os artefatos e 2.041 entradas SHA256SUMS passaram. Q354 permanece sem resposta; nova leitura mostra sem MAME, TAP `DOWN/NO-CARRIER` e TCP/23 em timeout; não reiniciei ou alterei a VM. Próximo passo: continuar identificação/reconstrução dos serviços externos necessários ao build e aguardar Q354 antes do guest. Estimativa integral ~10%, baseada no escopo ainda aberto de dependências e na falta de compilação/execução Apollo; testes host não medem fidelidade.


## 2026-10-14 — I342: `GlobalInit` e fluxo `main` conectado (r29)

Modelei o `GlobalInit` de 2.580 bytes (`0x40bdc`) em C host: vinte chaves de catálogo condicionais, cópia com alocação `length+1`, doze ponteiros estáticos A5-relativos e flag final zerada. Um verificador compara as 20 linhas e 12 destinos com o pseudo-C Ghidra e hash da faixa COFF; correspondência confirmada. O teste cobre entradas ausentes e alocação retornando zero; o harness host integrado de `main` agora chama o adapter real, não um stub para GlobalInit. Suíte r29: 54/54 C89 estrito e 54/54 ASan/UBSan. Manifesto r29: 3.810 artefatos, 60 modelos e 193 registros manuais; todos os tamanhos/hashes verificados e 2.047 entradas SHA256SUMS passaram. Serviços A5, ABI e dependências externas continuam sem validação guest. Apollo foi rechecado: sem processo MAME, TAP `DOWN/NO-CARRIER`, TCP/23 em timeout; Q354 sem resposta. Não reiniciei nem alterei a VM. Próximo: seguir os serviços externos/C runtime necessários ao build e aguardar Q354 para a compilação Apollo. Estimativa integral ~10%, dado o escopo geral de dependências e ausência de build/runtime; a contagem de testes não mede fidelidade.

## 2026-10-14 — I342: `DisplayTopCB` e pedido de conexões ftpd

Reconstruí `vuehelp:DisplayTopCB` como adapter C host para os 48 bytes em
`0x403ae..0x403de`. A evidência liga a implementação ao assembly e ao
pseudocódigo extraídos; o teste verifica ordem dos hooks, limite de 50 bytes,
`call_data` encaminhado e status zero. A suíte r30 passou 55/55 C89 estrito e
55/55 ASan/UBSan. Manifesto r30: 3.814 registros de artefatos, 61 adapters e
2.052 linhas de SHA256SUMS; inventário, tamanhos e hashes foram conferidos.
Essas provas são do host e não cobrem fonte original, ABI, dependências,
compilação/link/execução Apollo. Estimativa integral de I342 permanece ~10%,
com base no escopo de aplicação/dependências ainda aberto e ausência de build e
runtime guest; contagem de testes não mede fidelidade.

A pessoa pediu agora aumentar conexões simultâneas do ftpd por Telnet. O escopo
existe em I361, porém o estado SQLite consultado ainda tem
`user.authorized=false`; Q362 também está pendente. Portanto não usei Telnet nem
alterei ftpd, rede ou guest. I342 continua autorizada rev3. Q354 (retomada da
VM) e Q363 (propriedade de `_XtPrintEventSeq`) continuam sem resposta; não
iniciei MAME nem editei o símbolo concorrente. Q102r191 recebeu este avanço e a
indicação de que I361 precisa de autorização salva antes de operar o guest.
Próximo: prosseguir com dependências Apollo reconstruíveis no host e aguardar as
decisões necessárias antes de qualquer ação na VM.

## 2026-10-14 — I342: `PointerSelectTopicCB` (r31)

Acrescentei adapter host para os 174 bytes de `vuehelp:PointerSelectTopicCB`
(`0x40300..0x403ae`). Ele modela o cálculo da linha por coordenada, limites da
lista, guarda temporal de clique repetido e sequência dos hooks, distinguindo
as duas chamadas de redesenho que têm aridades diferentes na assembly. Teste
isolado cobre seleção, repetição, linha inválida e guardas host. Suíte r31:
56/56 C89 estrito e 56/56 ASan/UBSan. Manifesto: 3.818 artefatos e 62 adapters;
tamanhos e hashes validados, 2.057 checksums listados. Tipos/layouts originais,
hooks privados e comportamento de falhas do guest não são comprovados. A
estimativa integral de I342 permanece ~10%; não representa cobertura de testes,
pois continuam em aberto recuperação das dependências e compilação/link/execução
na Apollo.

Q354 ainda não foi respondida e não iniciei MAME; Q363 segue sem decisão e não
editei `_XtPrintEventSeq`. O pedido anterior de aumentar conexões do ftpd está
em I361, cujo `user.authorized` segue falso; não usei Telnet nem alterei o guest.
Q102r191 recebeu o avanço r31 e o estado desses gates. Próximo: reconstruir mais
funções do Help Viewer e auditar dependências com artefatos de assembly e hashes,
sem apresentar adapters host como build histórico validado.

## 2026-10-14 — I342: `ManageIndexSearchCB` (r32)

Reconstruí como adapter host `vuehelp:ManageIndexSearchCB`, intervalo de 532
bytes `0x403f8..0x4060c`. O modelo cobre os ramos de busca à frente/para trás,
lookup e combinação da lista de ações, liberação temporária, leitura e ajuste
da posição, atribuição de recursos e manage/unmanage/toggle. O teste confirma
ramos, argumentos, ordem, vida da lista temporária e controles. Suíte r32:
57/57 C89 estrito e 57/57 ASan/UBSan. Manifesto: 3.822 artefatos e 63 adapters;
2.062 checksums e hashes/tamanhos do inventário validados. A5, layout Xt, ABI e
comportamento em guest não foram provados. Progresso total de I342 permanece
estimado em ~10% pelo escopo amplo e falta da compilação/execução Apollo; os
testes host não representam fidelidade.

A leitura atual da prancheta mantém I342 autorizada rev3; Q354 e Q363 estão sem
resposta. Não iniciei MAME. I361 ainda tem `user.authorized=false`, portanto não
usei Telnet nem alterei ftpd. Q102r191 será atualizado com esta evidência.

## 2026-10-14 — I342: `SizeIndexDialog` (r33)

Modelei `vuehelp:SizeIndexDialog` (1.160 bytes, `0x4060c..0x40a94`) como
adapter C host. A função consulta métricas e medidas, forma totais de 16 bits,
calcula percentuais/gaps inteiros, emite os argumentos de layout e escolhe a
dimensão do dialog shell pelo ramo observado. O teste cobre ordem dos callbacks,
valores derivados e ambos os ramos. Suíte r33: 58/58 C89 estrito e 58/58
ASan/UBSan. Manifesto: 3.826 artefatos, 64 adapters e 2.067 checksums; hashes e
tamanhos conferidos. Isso não valida os recursos A5 reais, layouts Xt, ABI ou
tratamento de fault Apollo. I342 segue estimada em ~10% pelo escopo amplo e pela
ausência de build/runtime no guest; testes host não medem fidelidade histórica.

I342 continua autorizada rev3. Q354/Q363 continuam sem resposta; MAME segue sem
ser iniciado. I361 continua sem autorização salva; não houve Telnet nem mudança
do ftpd. Q102r191 receberá o resultado r33.

### I342 — correção de integridade e `MakeIndex` (r34)

Na revisão seguinte à entrada r33, detectei que
`vuehelp-SizeIndexDialog.evidence.json` foi substituído por outro recibo cujos
hashes internos correspondem aos fontes/testes atuais, mas divergem do manifesto
r33. Preservei o estado concorrente e abri Q367 para definir autoria antes de
reconciliar o manifesto e `SHA256SUMS`; portanto os checksums/inventário r33 não
devem ser tratados como íntegros após essa mudança posterior. Recompilei e rodei
os 58 testes atuais nos dois perfis, todos passaram.

Em trilha separada, reconstruí `MakeIndex` (328 bytes, `0x40a94..0x40bdc`) como
adapter host, com teste para presença/ausência do título de catálogo, alocação,
criação, callback de sizing injetado, recursos e quatro callbacks registrados.
Preserva a chamada de cópia mesmo no caso de alocação nula observado no
pseudocódigo. Suíte ampliada r34 passou 59/59 em C89 estrito e 59/59 em
ASan/UBSan; evidências locais: `host-suite-validation-20261014-r34.json` e
`vuehelp-MakeIndex.evidence.json`. O adapter de `MakeIndex` ainda não foi
incorporado ao manifesto compartilhado. Q102r191 recebeu o estado e Q367 aguarda
resposta. A estimativa integral I342 continua ~10%, diante do escopo amplo e da
falta de validação Apollo; não representa cobertura de testes.

### I342 — `MakeIndex` e callbacks da navegação (r35)

Em unidades distintas da edição concorrente de `SizeIndexDialog`, modelei
`MakeIndex` (328 bytes, `0x40a94..0x40bdc`) e quatro callbacks de 28 bytes:
`BrowseNextCB`, `BrowsePreviousCB`, `MapIndexCB` e `MapTopicViewerCB`. Os recibos
`vuehelp-MakeIndex.evidence.json` e `vuehelp-IndexNavCallbacks.evidence.json`
registram ranges/hash, hooks injetados e limites; o dimensionamento chamado por
`MakeIndex` ainda está como hook para evitar acoplar a função à edição em
conciliação. Suíte r35: 60/60 C89 estrito e 60/60 ASan/UBSan; o ledger r35 guarda
hashes dos 60 testes. Esses novos arquivos continuam fora do manifesto e da
SHA256SUMS até resolver Q367: a substituição concorrente de
`SizeIndexDialog.evidence.json` ainda deixa o manifesto r33 divergente, e não
sobrescrevi esse conjunto. Q102 recebeu o estado. A build/execução Apollo segue
pendente; Q354 sem resposta, sem reinício do MAME.

### I342 — `StartQMarkBMS` (r36)

Modelei `StartQMarkBMS` (186 bytes, `0x418f4..0x419ae`) como adapter host em
`help_viewr_rev/analysis/reconstruction-c/vuehelp-StartQMarkBMS.c`. O teste
cobre criação da marca com os três campos do tópico, estado ativo/inativo,
seleção de recurso pelos dois lados do bit `0x04` no estilo, ordem da gravação
da marca e instalação do evento `<EnterWindow>`. O recibo registra SHA-256 do
trecho binário `dae3ee3800a03cc27223126df8c7bcda5b62fabfab4b551b1a5b8029b700d5dd`.
O teste isolado passou em C89 estrito e ASan/UBSan. Estes três artefatos novos
estão fora do manifesto/checksum compartilhados enquanto Q367 aguarda resolução;
não alterei `SizeIndexDialog` nem os índices comuns.

A demanda I342 segue autorizada, mas o JSON de estado instalado em
`~/.local/state/irixium/work-board` contém apenas T01–T10 e não é o canal Motif
atual; não encontrei interface SQLite/CLI ativa neste workspace para gravar
Q102/I342 com segurança nesta rodada. A fila do repositório registra o avanço,
mas falta sincronizá-lo no canal da aplicação. Q354/Q363 seguem pendentes; não
iniciei MAME, não acessei Telnet e não alterei ftpd. Estimativa global de I342
permanece ~10%, pelo escopo total ainda não reconstruído e ausência de
compilação/execução Apollo; a contagem de testes não mede conclusão histórica.

### I342 — conflito no `StartTopicsListBMS` (r38)

Ao avançar para o próximo inicializador, a auditoria dos inventários encontrou
que o r35 já continha `test_vuehelp_StartTopicsListBMS.c` com 5.752 bytes e hash
`981291a52eb36d729dc19c4cca2512be5fda9bb1c59932f6377060d4f6172416`. Durante a
minha tentativa de criar um adapter desse mesmo símbolo, o arquivo atual passou
a divergir desse recibo. Não consigo atribuir com segurança a versão atual nem
recuperar o conteúdo anterior apenas do hash; suspendi novas edições no símbolo
e abri Q368. O teste isolado da versão que criei passou C89/ASan/UBSan, mas isso
não substitui a integridade nem a prova anterior. A suíte r36 (61/61 em cada
perfil) foi executada antes de detectar a divergência; não a trato como recibo
da árvore atual. Corrigi I342 e o canal Q102 (sequência 203) com esse limite.

O adapter separado `StartQMarkBMS` permanece registrado; o conjunto compartilhado
segue sem reconciliação enquanto Q367 e agora Q368 aguardam resposta. I342 rev3
continua autorizada. A sessão Apollo permanece indisponível, Q354/Q363 sem
resposta; I361/Q362 sem autorização salva. Não iniciei MAME, não usei Telnet e
não alterei ftpd. Estimativa integral permanece ~10% por escopo amplo e ausência
de compilação/execução Apollo.

### I342 — suíte host ampliada e Q102 sincronizado (r37)

Revalidei I342 rev3 no SQLite atual do AI Work Board: autorização permanece
verdadeira e vinculada ao hash da definição. Q354, Q363 e Q367 continuam sem
resposta; I361 segue sem autorização. Os hashes dos 60 testes listados no recibo
r35 conferem com os arquivos atuais. Rodei esses testes mais
`test_vuehelp_StartQMarkBMS.c`: 61/61 passaram em C89 estrito e 61/61 em
ASan/UBSan. O ledger é
`help_viewr_rev/analysis/reconstruction-c/host-suite-validation-20261014-r36.json`;
atualizei o recibo exclusivo de `StartQMarkBMS` para apontá-lo. I342 e a
mensagem do canal compartilhado Q102 foram atualizadas pela CLI; confirmação da
mensagem: sequência 199. O conjunto continua host-only, sem build/link/runtime
Apollo. O guest segue sem MAME observável e TAP DOWN/NO-CARRIER. Não usei
Telnet nem alterei ftpd: a solicitação foi registrada em I361/Q362 e ainda não
tem autorização salva; não iniciei MAME, mantendo Q354 pendente. Estimativa de
I342 segue ~10% pelo escopo amplo não reconstruído e falta da prova Apollo.

### I342 — extensão da divergência ao conjunto inventariado (r39)

Correção de integridade: o manifesto r33 mostra que divergiram os três artefatos
`StartTopicsListBMS`, não apenas o teste. Manifesto→árvore atual: teste
5752/`981291a5…` → 3294/`f18d0ff8…`; fonte 4751/`38c99dee…` →
3392/`4e9beac6…`; evidência 2472/`efd3164a…` → 2020/`f6d81b1e…`. Procurei
cópias em Downloads, tempia e Projetos e não encontrei os conteúdos anteriores.
Não atualizei manifesto, README nem SHA256SUMS. Q369 complementa Q368 para
coordenar a autoria e recuperar a versão válida. Os arquivos atuais têm prova
host isolada, mas isso não substitui os artefatos antes inventariados. A suíte
r36 vale para o instante em que foi executada; ela não atesta essa árvore após a
divergência. I342 e Q102 foram corrigidas (mensagem Q102 seq. 204). Próximo:
aguardar Q368/Q369 e resolver a recuperação sem sobrescrever trabalho alheio;
retomar símbolos independentes quando seguro. I342 permanece ~10%; compilação e
execução Apollo pendentes; Q354/Q363 sem resposta, I361 sem autorização, sem
mudanças na VM/Telnet/ftpd.

### I342 — `StartHelpHelpBMS` e regressão sem o símbolo conflitante (r40)

Acrescentei adapter independente para `StartHelpHelpBMS` (136 bytes,
`0x41b2c..0x41bb4`), com teste de estado ativo/inativo, dois ramos do bit `0x04`,
escolha do recurso, forwarding e ordem do callback final. O teste dedicado
passou em C89 estrito e ASan/UBSan. Para uma verificação mais ampla, rodei os
59 testes do r35 cujos hashes continuam iguais, mais `StartQMarkBMS` e
`StartHelpHelpBMS`: 61/61 em ambos os perfis. Recibo
`host-suite-validation-20261014-r38.json` exclui explicitamente o teste
`StartTopicsListBMS` conflitante; assim o r38 é válido para essa seleção de
arquivos, sem declarar a suíte agregada completa íntegra. Atualizei os recibos
independentes de StartQMark e StartHelp. I342 e Q102 foram atualizadas pela CLI
(mensagem Q102 seq.209). Continuam pendentes a recuperação do conjunto
StartTopicsListBMS em Q368/Q369 e a reconciliação de Q367. Não alterei manifesto,
README ou SHA256SUMS. Apollo ainda sem MAME/guest acessível; Q354/Q363 pendentes.
I361 não autorizada: nenhum Telnet/ftpd. Estimativa de I342 ~10% pelo volume
amplo ainda não reconstruído e falta de compilação/execução Apollo.

### I342 — sessões Telnet antigas ainda estabelecidas (r41)

Rechecagem host em 2026-10-14: não há processo MAME, e
`tap-mess-1000-0` continua DOWN/NO-CARRIER, mas `ss -tnp` mostra dois sockets
TCP estabelecidos de Telnet para `192.168.240.2:23`. PIDs 167977/pts16 iniciado
12 out e 1117587/pts11 iniciado 10 out. Inspecionei apenas metadados de processo,
TTY e sockets; não li/escrevi nos terminais nem enviei comandos. Eles podem ser
de outra IA ou execução anterior, então Q370 pergunta autoria e autorização para
inspeção de leitura no guest. Atualizei Q354 para refletir a nova evidência e
Q102 seq.211. Não trato sockets como prova de sessão Apollo correta ou consentida.
I361/Q362 seguem separados e sem autorização salva: nenhuma ação ftpd. Próximo:
aguardar Q370 para classificar essas sessões; depois, se autorizada, verificar a
sessão Apollo sem reiniciá-la. I342 continua parcial e sem prova de build/link/
execução guest; estimativa total ~10%.

### I342 — `SaveSessionCB` e validação host atual (r42)

Modelei `SaveSessionCB` (490 bytes, `0x42f5c..0x43146`) como adapter host em
`help_viewr_rev/analysis/reconstruction-c/vuehelp-SaveSessionCB.c`. O teste
dedicado cobre retorno do resolver, falha do open/flag `0x1b0`, limpeza, seleção
do widget de sessão por bit `0x20`, ordem de salvamento Topic/Index/Torn,
write/close, tamanho do buffer (`len(base)+len(session)+0x0b`) e título por
bit `0x04`. C89 estrito e ASan/UBSan passaram. A seleção r39 passou 62/62 em
ambos os perfis: 61 fontes de teste do r38 com hashes válidos mais
`test_vuehelp_SaveSessionCB.c`. Ela exclui explicitamente o símbolo conflitado
`StartTopicsListBMS`; não é a suíte completa e não prova Apollo. Recibo
`host-suite-validation-20261014-r39.json`; I342 e canal Q102 atualizados (seq.216).
Q368/Q369 e Q370 seguem sem resposta; Q354 segue aguardando decisão. Os dois
sockets Telnet antigos continuam estabelecidos; não usei terminais nem enviei
comandos. MAME ausente, TAP down. I361 sem autorização salva, nenhum ajuste ao
ftpd. Estimativa de I342 ~10% por escopo amplo restante e validação guest ausente.

### I342 — `SaveIndexWindow` no caminho de persistência (r43)

Modelei `SaveIndexWindow` (578 bytes, `0x42a3c..0x42c7e`) em adapter host
separado. O teste cobre título e geometria, flag de janela nested igual a 1,
bit de estilo `0x04` para a escolha do recurso, query inicial sucesso/falha,
query final e condição exata `status==0 && geometry_present && kind==3` para
selecionar `0x10d0` em vez de `0x10d8`, além de ordem e liberação da lista.
Dependências Xt, expansão de strings e `BuildGeoString` seguem injetadas. Teste
dedicado passou em C89 estrito e ASan/UBSan. A seleção r40 passou 63/63 em ambos
os perfis, incluindo 62 hashes do r39 e o teste novo; exclui explicitamente
`StartTopicsListBMS` enquanto Q368/Q369 aguardam reconciliação. Recibo
`help_viewr_rev/analysis/reconstruction-c/host-suite-validation-20261014-r40.json`.
I342/Q102 atualizados pela CLI (seq.220). Li também o aviso Q102 seq.219 de
`TitleExposeCB`; não alterei esse símbolo. Guest sem MAME, TAP down; Q354/Q370
pendentes e os Telnet antigos não foram usados. I361 sem autorização salva,
ftpd intacto. Estimativa total ~10%, sem prova Apollo.

### I342 — `SaveTopicWindow` e suíte host r41 (2026-10-14)

Adicionei adapter host independente para `SaveTopicWindow` (734 bytes,
`0x42c7e..0x42f5c`) e teste dedicado. A modelagem cobre títulos, geometria,
seleção de recurso por bit `0x04`, mapeamento dos tipos de view e fallback,
consulta condicional, predicate final de `status`, geometria e `kind==3`, além
da liberação e ordem das escritas. O teste dedicado passou em C89 estrito e
ASan/UBSan. A seleção r41 passou 64/64 nos dois perfis: 63 testes herdados do
r40 cujos hashes conferem, mais `SaveTopicWindow`. `StartTopicsListBMS` continua
excluído por Q368/Q369; o recibo não representa a suíte completa nem valida
ABI, build ou execução Apollo. Evidências:
`help_viewr_rev/analysis/reconstruction-c/vuehelp-SaveTopicWindow.evidence.json`
e `host-suite-validation-20261014-r41.json` (SHA-256
`6fe5960566b94420385ba01b14c3919a1c3b6dc267e2beebdac734801d429d7d`). A
atualização I342/Q102 foi confirmada no canal Q102, sequência 224; a leitura
não mostrou resposta humana nova. I342 rev3 permanece autorizada e running.
Q354, Q367–Q370 seguem sem resposta; I361 permanece sem autorização salva,
portanto não usei Telnet e não alterei o ftpd. A divergência de
`StartTopicsListBMS` ainda impede integrar/publicar a suíte agregada. Estimativa
de I342: ~10%, baseada no escopo amplo ainda não reconstruído e na ausência de
build/link/execução no guest, não na contagem de testes.

### I361 / Q362 — novo pedido de ajuste do ftpd (2026-10-14)

O usuário reiterou no chat que deseja usar Telnet para ampliar o limite de
conexões simultâneas. A leitura autoritativa via CLI confirma que I361 rev0
continua `user.authorized=false`; a regra de AGENTS.md exige autorização salva
no próprio item antes da execução. Q370 também não recebeu resposta, e há duas
sessões Telnet preexistentes cuja autoria não foi identificada. Não enviei
comandos, não acessei os TTYs e não alterei o ftpd. Atualizei a resposta de Q362
pedindo a autorização salva em I361 e a resolução de Q370; publiquei a situação
no Q102, sequência 225. Qualquer reinício ou interrupção continua sujeito a
pergunta prévia como previsto no escopo I361. Próximo: aguardar autorização e
identificação das sessões; então verificar o limite e determinar se um aumento
mínimo pode ser aplicado sem reiniciar ou interromper conexões.

### I342 — `history_update_item` e suíte host r42 (2026-10-14)

Reconstruí como adapter host a rotina `history_update_item` (74 bytes,
`0x509aa..0x509f4`). Ela lê o índice ativo no word `+0x18`, usa esse índice
para obter seis words brutos de 32 bits nos offsets observados e encaminha o
registro, esses seis valores e um zero fixo ao callback localizado relativamente
em A5. `history_prev_item` e `history_next_item` confirmam o uso depois de
carregar a localização. Teste dedicado e regressão passaram 65/65 em C89
estrito e ASan/UBSan; todas as 64 fontes da seleção r41 tiveram hash conferido
antes da execução. Recibo r42:
`help_viewr_rev/analysis/reconstruction-c/host-suite-validation-20261014-r42.json`
(SHA-256 `310d8326a1fe59756216cbbc8605925df438efd2f7c56e7084e65b6b7026c98b`);
evidência individual em `vuehelp-HistoryUpdateItem.evidence.json`. Q102/I342
atualizada pela CLI (mensagem Q102 seq.227). `StartTopicsListBMS` continua fora
da seleção por Q368/Q369; não alterei esse bloco. Detectei também trabalho em
`ViewExposeCB` e deixei seus artefatos intocados. Esta prova é somente modelo e
testes no host; callback, tipos e ABI Apollo permanecem incertos, sem build/link/
runtime do guest. I361 permanece sem autorização e Q370 sem resposta; nenhum
Telnet/ftpd foi usado. A estimativa de I342 segue ~10%, com base no escopo amplo
ainda faltante e na ausência de validação Apollo.

### I342 — navegação de histórico e `AllocateStructures` (r44–r46, 2026-10-14)

Modelei três funções adicionais de `util.c`. `history_prev_item` salva o índice
antes de `history_update_line`, decrementa e faz wrap para `count-1`, carrega os
words indexados, chama `history_load_locn` e atualiza o item. `history_next_item`
avança/wrapa os índices, ajusta os recursos +0x3c/+0x40 nos dois views na ordem
do assembly, persiste o estado e atualiza o item. `AllocateStructures` verifica
+4 <= +8, cresce +4 em dez e chama o hook A5 duas vezes com tamanho atualizado
vezes quatro, guardando os retornos nos ponteiros associados a A5-0x24/-0x28.
Os testes dedicados passaram e os recibos r44, r45 e r46 registraram
respectivamente 67/67, 68/68 e 69/69 testes nos perfis C89 estrito e ASan/UBSan.
Cada seleção partiu da anterior com todos os hashes conferidos e exclui
`StartTopicsListBMS` por Q368/Q369. Evidências em
`vuehelp-HistoryPrevItem.evidence.json`, `vuehelp-HistoryNextItem.evidence.json`,
`vuehelp-AllocateStructures.evidence.json` e os recibos de suíte r44–r46.
Q102/I342 atualizados pela CLI (seq.232); li as atualizações concorrentes
seq.230–231 sobre `CreateSeparator` e `MakeTornWindow` e não toquei nesses
símbolos. I361 ainda sem autorização salva, Q370 sem resposta; sem Telnet/ftpd.
Sem prova de compilação/link/runtime Apollo. A estimativa de I342 fica em ~10%
pelo escopo histórico integral e dependências não reconstruídas, não pelo número
de testes.

### I342 — `AllocData` e suíte host r47 (2026-10-14)

Reconstruí `AllocData` (44 bytes, `0x50b6c..0x50b98`) como adapter host: lê o
ponteiro antigo da célula recebida, calcula bytes por `units << 5`, chama o hook
A5 e grava o retorno na mesma célula. Callers em `util.c` confirmam seu uso
com buffers, mas o alocador privado permanece sem identificação. Teste dedicado
e suíte r47 passaram 70/70 em C89 estrito e 70/70 em ASan/UBSan; os 69 testes
r46 foram validados por hash antes de repetir. Recibo
`help_viewr_rev/analysis/reconstruction-c/host-suite-validation-20261014-r47.json`
(SHA-256 `69ce4cbd6873817725a62f78acf2bf0e0ec01ef54643ef2be7bd683cb7942808`)
e evidência `vuehelp-AllocData.evidence.json`. Q102/I342 atualizado (seq.234).
`StartTopicsListBMS` continua excluído por Q368/Q369. Q102 não tinha resposta
humana quando foi lido até seq.232; I361 segue sem autorização e Q370 pendente,
sem Telnet/ftpd. Sem compilação, link ou execução Apollo. A estimativa I342
continua ~10% pelo escopo integral restante e pelas dependências, não pela
contagem de testes.

### I342 — `part_of_string` e suíte host r48 (2026-10-14)

Modelei `part_of_string` (82 bytes, `0x50b98..0x50bea`) sem dar nomes
presumidos às funções privadas: chama dois hooks de comprimento em ordem,
retorna nulo quando o segundo texto é menor, e então compara o segundo com o
primeiro pelo tamanho deste. Só comparação igual retorna o ponteiro do segundo
texto. O teste isolado e a regressão r48 passaram 71/71 em C89 estrito e
ASan/UBSan; os 70 testes r47 tiveram hashes conferidos antes da execução. Recibo
`help_viewr_rev/analysis/reconstruction-c/host-suite-validation-20261014-r48.json`
(SHA-256 `10731a5caa1db12e569ba4c256bae396ad7b3219183dd2123af4041da57b9b24`)
e evidência `vuehelp-PartOfString.evidence.json`. Q102/I342 atualizado (seq.236).
Li a atualização seq.235 sobre `MakeIndexWindow`; não editei o símbolo da outra
IA. `StartTopicsListBMS` segue excluído por Q368/Q369. Sem prova Apollo. I361
sem autorização salva, Q370 pendente; nenhum Telnet/ftpd. Estimativa I342 ~10%
pelo escopo completo pendente, não pela quantidade de testes.

### I342 — `findHost` e suíte host r49 (2026-10-14)

Modelei `findHost` (60 bytes, `0x51af4..0x51b30`) como busca linear nos
registros de stride `0x14`, comparando a word big-endian no deslocamento +8 e
retornando o primeiro índice ou −1. Teste isolado e seleção r49 passaram
72/72 em C89 estrito e 72/72 em ASan/UBSan; hashes dos 71 testes r48 conferidos
antes da execução. Recibo
`help_viewr_rev/analysis/reconstruction-c/host-suite-validation-20261014-r49.json`
(SHA-256 `fc5be79b880def0939d7f9525299e1d03fec89ec9fdbcae8ff827b529ddc7c5a`)
e evidência `vuehelp-FindHost.evidence.json`. Q102/I342 atualizado (seq.237).
`StartTopicsListBMS` permanece excluído em Q368/Q369. Q102 estava sem resposta
humana até seq.236; I361 continua sem autorização salva, Q370 pendente, sem
Telnet/ftpd. Sem compilação/link/runtime Apollo; avanço estimado segue ~10% pelo
escopo integral e validação de guest que faltam.

### I342 — `GetHostByPath` e suíte host r50 (2026-10-14)

Modelei `GetHostByPath` (94 bytes, `0x51a96..0x51af4`) como varredura de
registros stride `0x14`: lê o handle de caminho em +4, resolve o texto, mede o
comprimento, chama o comparador privado e retorna o primeiro índice cujo
resultado é zero; sem correspondência retorna −1. Hooks de resolução,
comprimento e comparação permanecem injetados. Teste isolado e r50 passaram
73/73 em C89 estrito e ASan/UBSan; os 72 testes r49 foram validados por hash
antes da repetição. Recibo
`help_viewr_rev/analysis/reconstruction-c/host-suite-validation-20261014-r50.json`
(SHA-256 `b390814b8b8a51b78962e08235fe83119e30f47ce540e96090a207dcb8784df9`)
e evidência `vuehelp-GetHostByPath.evidence.json`. Q102/I342 atualizado
(seq.238). `StartTopicsListBMS` segue excluído em Q368/Q369. Q102 sem resposta
humana; I361 sem autorização salva, Q370 sem resposta, sem Telnet/ftpd. Sem
validação Apollo; estimativa geral I342 continua ~10% pelo escopo ainda amplo.

### I342 — `MakeFileItem` e suíte host r51 (2026-10-14)

Modelei `MakeFileItem` (82 bytes, `0x50cf4..0x50d46`): duplica os argumentos
2 e 3 pelo mesmo hook privado em ordem, grava os resultados nos words +0/+4,
copia argumento 4 em +8, preenche +0x0c/+0x10/+0x14 com `0xffffffff` e limpa
+0x18/+0x1c. Teste isolado e r51 passaram 74/74 em C89 estrito e ASan/UBSan;
os 73 testes r50 passaram verificação de hash antes da execução. Recibo
`help_viewr_rev/analysis/reconstruction-c/host-suite-validation-20261014-r51.json`
(SHA-256 `0039882b3e1718e8e42677f295e64248bcac151143027651f1fbad7fbc6397eb`)
e evidência `vuehelp-MakeFileItem.evidence.json`. Q102/I342 atualizado (seq.239).
`StartTopicsListBMS` continua excluído por Q368/Q369. Q102 ainda sem resposta
humana; I361 sem autorização salva, Q370 sem resposta, sem Telnet/ftpd. Sem
validação Apollo; estimativa I342 ~10% pelo escopo integral pendente.

### I342 — wrappers `CmpLine`/`CmpFileLabel` e suíte host r52 (2026-10-14)

Os dois wrappers de `nlsio.c` têm intervalos distintos de 50 bytes, mas
assembly equivalente. Cada um carrega as words apontadas por dois argumentos,
invoca uma vez o hook A5 com elas nessa ordem e descarta o retorno. O modelo e o
teste compartilhados passaram junto à regressão r52: 75/75 C89 estrito e
75/75 ASan/UBSan, com hash dos 74 testes r51 conferidos antes. Evidências
individuais `vuehelp-CmpLine.evidence.json` e
`vuehelp-CmpFileLabel.evidence.json`; recibo
`help_viewr_rev/analysis/reconstruction-c/host-suite-validation-20261014-r52.json`
(SHA-256 `4d5924ed40b3cac3dde4a6caf8a58d4a54c7d22658bf8f874556a7286948332f`).
Q102/I342 atualizado (seq.241); li também P10/V06 seq.240, sem resposta humana
sobre I342. `StartTopicsListBMS` excluído por Q368/Q369. I361 sem autorização,
Q370 sem resposta; sem Telnet/ftpd. Ainda não há build/link/runtime Apollo;
estimativa global ~10%, baseada no amplo escopo faltante.

### I342 — `MakeManDir` e suíte host r53 (2026-10-14)

Modelei `MakeManDir` (82 bytes, `0x5155a..0x515ac`): limpa as duas entradas
indexadas antes da validação; para seletor válido chama `ScanManDir` com o
caminho da tabela e índice; retorna zero em todos os casos. Teste isolado e
r53 passaram 76/76 em C89 estrito e ASan/UBSan; os 75 testes r52 passaram
checagem de hashes antes da execução. Recibo
`help_viewr_rev/analysis/reconstruction-c/host-suite-validation-20261014-r53.json`
(SHA-256 `4696e78bdc418ed3c44cf0cf47a8009f34acc8dd17792e17bec96df4f375cab8`)
e evidência `vuehelp-MakeManDir.evidence.json`. Q102/I342 atualizado (seq.242).
`StartTopicsListBMS` segue excluído em Q368/Q369. I361 sem autorização salva,
Q370 sem resposta; sem Telnet/ftpd. Sem validação Apollo; estimativa total I342
~10%, com base no trabalho de reconstrução e validação guest ainda necessários.

### I342 — `StripSpaces` e suíte host r54 (2026-10-14)

Modelei `StripSpaces` (158 bytes, `0x5286c..0x5290a`) preservando a classificação
via tabela locale pelo bit `0x08`, com índice de byte signed observado, cópia do
primeiro não-espaço, medição e remoção de sufixo. O caso NULL retorna sem hooks;
a classificação/cópia/comprimento seguem injetados. Teste dedicado e seleção r54
passaram 77/77 em C89 estrito e 77/77 em ASan/UBSan; todos os 76 hashes r53
foram validados antes de repetir. Recibo
`help_viewr_rev/analysis/reconstruction-c/host-suite-validation-20261014-r54.json`
(SHA-256 `bdea6a9fff3f4ea42042e9cdff51285e916e01ea00f552e01f9633cf34dcaa82`)
e evidência `vuehelp-StripSpaces.evidence.json`. Q102/I342 atualizado (seq.244).
Li seq.243: Xephyr está vazio, MAME ausente e TAP down, sem resolução das
perguntas Apollo. `StartTopicsListBMS` segue excluído em Q368/Q369; I361 sem
autorização e Q370 pendente, sem Telnet/ftpd. Sem build/link/runtime Apollo;
estimativa geral ~10% pelo escopo integral ainda não reconstruído/validado.

### I342 — `processError` e suíte host r55 (2026-10-14)

Modelei `processError` (158 bytes, `0x4c042..0x4c0e0`) pelos ramos do assembly:
0x14/2 seleciona mensagem 1 e A5+0; 0x0d seleciona mensagem 2/A5+0x30; 4
seleciona mensagem 3/A5+0x50; demais códigos, mensagem 4/A5+0x80. O hook de
mensagem recebe domínio 9; os callbacks regulares ou default recebem os
argumentos 3, 0, mensagem e argumento original. Teste isolado e r55 passaram
78/78 em C89 estrito e ASan/UBSan; os 77 hashes r54 foram verificados. Recibo
`help_viewr_rev/analysis/reconstruction-c/host-suite-validation-20261014-r55.json`
(SHA-256 `6d6514a12ee4c754327836fe1cb7820532a39d1e58a852b362ceb248eaae0b85`)
e evidência `vuehelp-ProcessError.evidence.json`. Q102/I342 atualizado (seq.245).
Hooks de mensagem/exibição seguem sem identidade confirmada. `StartTopicsListBMS`
excluído por Q368/Q369; I361 sem autorização salva e Q370 pendente, sem
Telnet/ftpd. Sem build/link/runtime Apollo. Estimativa I342 ~10% pelo escopo
amplo ainda em falta.

### Pedido ftpd via Telnet — aguardando autorização e identificação (2026-10-14)

O usuário reiterou que quer ampliar as conexões simultâneas do ftpd via Telnet.
Conferi o estado do banco da prancheta: I361 continua `user.authorized=false`;
Q362 pede essa autorização e Q370 ainda aguarda identificar/reconhecer os dois
clientes Telnet já estabelecidos. Conforme AGENTS.md, não acessei a VM nem
alterei o ftpd. Registrei a situação e os passos pendentes no canal Q102 da
Prancheta (revisão 191, resposta IA `waiting_user`). Retomar somente depois da
autorização salva em I361 e da resposta a Q370. Se o método exigir reinício ou
interrupção de sessões, parar e abrir pergunta conforme o escopo de I361.

### I342 — `make_index` de `nlsio.c` e seleção r56 (2026-10-14)

Criei `vuehelp-MakeIndexNlsio.c` e teste separado para `make_index`
(`0x4c0e0..0x4c1de`, 254 bytes), preservando o `MakeIndex` de `index.c` já
existente. O adapter registra os caminhos de open failure (retorno 2), texto
vazio/comparação igual (fecha, reporta erro 4), parse com word zero (fecha,
retorno 8) e sucesso (escreve saída big-endian, incluindo o word desalinhado
+6, fecha e retorna 0). Read/compare/parse/error/close continuam hooks privados;
o array de diretórios é representação host. Teste dedicado passou em C89 estrito
e ASan/UBSan.

A regressão r56 passou 78/78 na seleção C89 estrito e 78/78 ASan/UBSan. Antes
da suíte, os hashes dos testes r55 foram comparados: `test_vuehelp_MakeIndex.c`
divergiu (esperado `4ae63d69eb9f6de84e7997f1fccbdb8bb2d75c43cc19cc8f02ec1bfd4c1c5ce7`,
atual `7c60b9cc1250c19d4d7ef37f39b9a06e79bd4a11c444c7a39e35136fc8dba3d1`),
foi preservado e excluído; Q371 pergunta quem é responsável e qual versão deve
prevalecer. `StartTopicsListBMS` também permanece excluído por Q368/Q369. Evidência
`help_viewr_rev/analysis/reconstruction-c/vuehelp-MakeIndexNlsio.evidence.json`
(SHA-256 `490f66a758b80c012f5e1993598adfad5ebe9d84c312d4bb07a517a787c37b03`) e
recibo `host-suite-validation-20261014-r56.json` (SHA-256
`32c3aee4e124b85fdcab805e699ca7a07c13699c59050bdda6107e621c5f8a38`). Atualizei
I342 e Q102 na CLI; sem respostas novas no canal ao último estado lido. Sem
build/link/runtime Apollo; estimativa I342 ~10% baseada no escopo restante e na
validação guest ainda ausente. I361 ainda não autorizada, Q370 sem resposta:
nenhum comando Telnet nem ajuste ftpd.

### I342 — `RootIndex` de `nlsio.c` e seleção r57 (2026-10-14)

Modelei `RootIndex` (`0x4c302..0x4c358`, 86 bytes) em adapter host isolado.
Ele lê da linha stride 20 os campos +8 e +0x0c, chama o hook `RootIndex2`
com índice e ambos os valores, ignora o retorno do hook, relê o índice corrente
e devolve o word big-endian em +0x10. O teste verifica também a mudança do
índice durante o callback. O teste isolado passou C89 estrito e ASan/UBSan; a
seleção r57 passou 79/79 em cada perfil após conferir os hashes da seleção r56.
Recibo `help_viewr_rev/analysis/reconstruction-c/host-suite-validation-20261014-r57.json`
(SHA-256 `3efc7945ce77093671c120fcbb503c09a73e46e8ee36dde7dd95b160ed3a0b09`)
e evidência `vuehelp-RootIndexNlsio.evidence.json` (SHA-256
`c79f1496bb26dd5413d4298882484309746dc9a173e8f168687ad034004c2e6c`). `MakeIndex.c`
continua excluído em Q371; `StartTopicsListBMS` continua excluído em Q368/Q369.
Atualizei I342 e Q102; sem resposta humana nova até a leitura do canal. Ainda
sem ABI/build/link/runtime Apollo. Estimativa I342 ~10% pelo amplo restante e
validação guest ausente. I361 sem autorização salva e Q370 pendente; sem Telnet
ou alteração do ftpd.

### I342 — `RootIndex2` de `nlsio.c` e seleção r58 (2026-10-14)

Modelei `RootIndex2` (`0x4c1de..0x4c302`, 292 bytes) em adapter host
separado. Ele preserva o retorno imediato quando o campo +0x10 da linha stride
20 já está preenchido; para item diferente de -1 abre o caminho e lê o índice;
texto vazio ou comparação igual seleciona título default e sinaliza 4; substitui
o título salvo (liberando apenas se não nulo), fecha e chama a montagem de lista.
Falha de abertura reporta o código do hook de erro, mas ainda monta a lista. O
retorno é resultado da lista OR sinalizador local. Teste cobre cache, item -1,
open failure, texto vazio e igual, liberação/duplicação e montagem; passou em
C89 estrito e ASan/UBSan. Seleção r58 passou 80/80 em cada perfil, com hashes
r57 conferidos. Evidência
`help_viewr_rev/analysis/reconstruction-c/vuehelp-RootIndex2Nlsio.evidence.json`
(SHA-256 `551a6ca9936db48782f964314511732972e6c3b6f3757f211fc39671560014ab`) e
recibo `host-suite-validation-20261014-r58.json` (SHA-256
`a33b8451029c414f14007e88939684a39e226930b52d7915cd9a51762217a5c3`). Caminhos,
filesystem, duplicação/liberação e construção de listas continuam hooks; sem
prova de ABI/build/link/runtime Apollo. `test_vuehelp_MakeIndex.c` segue fora em
Q371 e `StartTopicsListBMS` em Q368/Q369. I342 e Q102 atualizados. Sem respostas
humanas novas no estado lido. Estimativa I342 ~10% pelo escopo amplo e validação
guest ainda pendentes.

### I342 — `clear_related` de `nlsio.c` e seleção r59 (2026-10-14)

Modelei `clear_related` (`0x4d412..0x4d464`, 82 bytes). Com estado relacionado
zero, não chama o hook; com estado não zero, passa dois pares recurso/valor
`[resource1,0,resource2,0]` à atualização do widget com contagem 2 e limpa o
estado somente após o callback. Teste isolado passou C89 estrito e ASan/UBSan;
a seleção r59 passou 81/81 em cada perfil com hashes r58 conferidos. Evidência
`help_viewr_rev/analysis/reconstruction-c/vuehelp-ClearRelatedNlsio.evidence.json`
(SHA-256 `e8f779338262dd4786c829e82db7991cde5e5218c257b7edc5d0552f4eaab079`) e
recibo `host-suite-validation-20261014-r59.json` (SHA-256
`6284f4d3b9e64facecfdcd15bf855cfa7d2e142ff62e628d806b21cd6eec4c11`). Handle do
widget e células A5 seguem abstraídos no host; sem ABI/build/link/runtime Apollo.
`MakeIndex.c` aguarda Q371 e `StartTopicsListBMS` Q368/Q369; ainda sem resposta
humana nas perguntas lidas. I342/Q102 atualizados; estimativa geral segue ~10%
pelo escopo amplo e validação Apollo pendentes.

### I342 — `ProcessHelp` de `nlsio.c` e seleção r60 (2026-10-14)

Modelei o wrapper `ProcessHelp` (`0x4ed46..0x4ed74`, 46 bytes): encaminha a
mensagem, A5+0x4a0, o word de `root_record+0x14` e o word da célula de help para
`ProcessTopic`, nessa ordem, sem usar seu retorno. Teste isolado passou em C89
estrito e ASan/UBSan; r60 passou 82/82 em cada perfil, após validar hashes r59.
Evidência `help_viewr_rev/analysis/reconstruction-c/vuehelp-ProcessHelpNlsio.evidence.json`
(SHA-256 `50649881c27b46d7385c4b00d872940644d44de173b4b4719e743e0d742c570f`) e
recibo `host-suite-validation-20261014-r60.json` (SHA-256
`7ad3c7c71e033b4b587b10d7dae7ed4f0308456f6cd0fe889bdfb7491e1979eb`). Ponteiros
A5 são buffers/células resolvidos no host; `ProcessTopic` continua hook. Sem
ABI/build/link/runtime Apollo. Q371 e Q368/Q369 seguem sem resposta. I342/Q102
atualizados, sem nova mensagem humana no estado lido; estimativa global ~10%
pelo escopo restante e validação guest ausente.

### I342 — `clear_glossary` de `nlsio.c` e seleção r61 (2026-10-14)

Modelei `clear_glossary` (`0x4d81e..0x4d87e`, 96 bytes). A rotina encaminha o
valor corrente, os words do registro +0x8c e +0xba (word desalinhado) a
`set_glossaryText`; depois lê o widget +0x88 e aplica dois pares
recurso/valor terminados em zero. O teste verifica valores e a ordem das chamadas.
Passou C89 estrito e ASan/UBSan; a seleção r61 passou 83/83 nos dois perfis após
conferir os hashes r60. Evidência
`help_viewr_rev/analysis/reconstruction-c/vuehelp-ClearGlossaryNlsio.evidence.json`
(SHA-256 `26d2a62a82dd5190fdb879bc47deb5c5b4014ff3775f0416d769ee0cf4c1d4c0`) e
recibo `host-suite-validation-20261014-r61.json` (SHA-256
`c9a49486764a59e6a780ab5ffb5e3271f10371fee801633de125b3f4379e77cc`). Cadeias A5
e funções privadas são abstraídas em valores/hooks host; sem ABI/build/link/runtime
Apollo. Q371 e Q368/Q369 sem resposta; I342/Q102 atualizados, sem mensagem humana
nova no estado consultado. Estimativa ~10% pelo escopo amplo e validação guest.

### I342 — `HistoryPrevious` de `nlsio.c` e seleção r62 (2026-10-14)

Modelei o wrapper `HistoryPrevious` (`0x4ef6e..0x4ef88`, 26 bytes) como um
único dispatch do argumento original para o hook privado A5−0x430; não inferi
a semântica do callback. Teste isolado passou C89 estrito e ASan/UBSan; r62
passou 84/84 em cada perfil após validar hashes r61. Evidência
`help_viewr_rev/analysis/reconstruction-c/vuehelp-HistoryPreviousNlsio.evidence.json`
(SHA-256 `9d11da9a0bd31e087915529e98da277f1e48443f3c2af83e1bbaa1b8aa618857`) e
recibo `host-suite-validation-20261014-r62.json` (SHA-256
`ec6d33214eac6c3034c9184f03764c2506b8bb78b1056194bad26d41ecad08fe`). Sem
ABI/build/link/runtime Apollo. Q371 e Q368/Q369 sem resposta no estado lido.
I342/Q102 atualizados; estimativa ~10% pelo escopo integral e validação guest
pendentes.

### I342 — `RelatedTopic` de `nlsio.c` e seleção r63 (2026-10-14)

Modelei `RelatedTopic` (`0x4ee02..0x4ee62`, 96 bytes): índice menos um, seleção
de registro stride 8, passagem do high word/halfword/word e constantes
`0,0,1,0xffffffff` ao hook `display_info`, callback final com o parâmetro
original e retorno do resultado de exibição. O teste isolado passou C89 estrito
e ASan/UBSan; r63 passou 85/85 em cada perfil após validar hashes r62. Evidência
`help_viewr_rev/analysis/reconstruction-c/vuehelp-RelatedTopicNlsio.evidence.json`
(SHA-256 `a1c3b39a9b6d4bc7275358632292b4927066aba593839bebaf44575fcef3ad0a`) e
recibo `host-suite-validation-20261014-r63.json` (SHA-256
`43c94ac386594af0a682e54e949ff4ad14db77c120d3e1a0af898b264b1c2dc2`). O adapter
requer índice positivo válido; exibição permanece hook. Sem ABI/build/link/runtime
Apollo. Atualizei I342/Q102; Q371 e Q368/Q369 seguem pendentes, sem resposta
humana no estado lido. Estimativa ~10% por amplo escopo e validação guest.

### I342 — `ShowGlossary` de `nlsio.c` e seleção r64 (2026-10-14)

Modelei `ShowGlossary` (`0x4ee62..0x4eee0`, 126 bytes): limpa A5+0x1d4; chama
em ordem os dois hooks de preparo para `param[0]` e `param[1]`; lê o seletor
`param[6]` e passa `param[seletor+8]`/`param[seletor+0x21]` ao hook construtor;
executa os dois hooks finais e retorna o resultado do construtor. Teste isolado
passou C89 estrito e ASan/UBSan; r64 passou 86/86 em ambos os perfis após hashes
r63 conferidos. Evidência
`help_viewr_rev/analysis/reconstruction-c/vuehelp-ShowGlossaryNlsio.evidence.json`
(SHA-256 `253b6910a5a8b40996e0d6f101d0bb61dc33a5980b855b875385391f0c2153a1`) e
recibo `host-suite-validation-20261014-r64.json` (SHA-256
`75df71af4aac38dc6f39ef96b6d67104c9252b33b281aab0f2ad3aa80963af4f`). Callbacks
e marcador A5 continuam abstraídos; sem ABI/build/link/runtime Apollo. Q371 e
Q368/Q369 seguem sem resposta no estado consultado; I342/Q102 atualizados.
Estimativa ~10% pelo escopo integral restante e validação guest ausente.

### I342 — `GlossaryTopic` de `nlsio.c` e seleção r65 (2026-10-14)

Modelei `GlossaryTopic` (`0x4eee0..0x4ef54`, 116 bytes): índice menos um, leitura
de registro stride 8, callbacks de preparo para param[0]/param[1], chamada de
`display_gloss` com high word/halfword/word, callbacks finais e retorno zero.
Teste isolado passou C89 estrito e ASan/UBSan; r65 passou 87/87 em cada perfil
após conferir hashes r64. Evidência
`help_viewr_rev/analysis/reconstruction-c/vuehelp-GlossaryTopicNlsio.evidence.json`
(SHA-256 `8fee0f4e347204279bf7d8e91f2cb3739cfe8610892208cc7d20d87380304547`) e
recibo `host-suite-validation-20261014-r65.json` (SHA-256
`f1d09951e51b9ae7b5405c934e4336a78d96fac8d51a8d746b8fdb8faa6cc724`). Exige
índice positivo e armazenamento válido; callbacks privados permanecem hooks.
Sem ABI/build/link/runtime Apollo. Q371 e Q368/Q369 sem resposta no estado
consultado. Atualizei I342/Q102; estimativa ~10% pelo escopo amplo e validação
guest ausente.

### I342 — `HistoryNext` de `nlsio.c` e seleção r66 (2026-10-14)

Modelei `HistoryNext` (`0x4ef54..0x4ef6e`, 26 bytes), distinto de
`history_next_item`: despacha uma vez o argumento original ao hook privado
A5−0x42c. Teste isolado passou em C89 estrito e ASan/UBSan; r66 passou 88/88
nos dois perfis após validar hashes r65. Evidência
`help_viewr_rev/analysis/reconstruction-c/vuehelp-HistoryNextNlsio.evidence.json`
(SHA-256 `c3ae94aa97ba99366aff995b21db37b56212967887317446602b64981a552560`) e
recibo `host-suite-validation-20261014-r66.json` (SHA-256
`be36e6ca72a416e924115aecda113b1881fc1008c394d1552f663cbe73a74d7d`). Hook
permanece opaco; sem ABI/build/link/runtime Apollo. I342/Q102 atualizados.
Q371 e Q368/Q369 seguem pendentes, sem resposta humana no estado consultado.
Estimativa ~10% pelo escopo integral e validação guest ausente.

### I342 — `PopLevel` de `nlsio.c` e seleção r67 (2026-10-14)

Modelei `PopLevel` (`0x4ef88..0x4f01e`, 150 bytes): campos indexados por nível,
registros stride 32, redirecionamento por igualdade do contexto em +0x18 e por
flag `0x80` ausente, chamada de `display_info` e callback final. A revisão do
ramo com índice -1 corrigiu a ordem para somente calcular o endereço da linha
após o teste de sentinela, como no assembly. Teste isolado passou C89 estrito e
ASan/UBSan; r67 passou 89/89 nos dois perfis após validar hashes r66. Evidência
`help_viewr_rev/analysis/reconstruction-c/vuehelp-PopLevelNlsio.evidence.json`
(SHA-256 `1dc5a93cf5ad3cbfa19284beb33e364168f00f06164a4d600171a89dfa275fb3`) e
recibo `host-suite-validation-20261014-r67.json` (SHA-256
`bbfcfd3cd8fb669641ca9c1b57ceb7a4ab4308f85bf8d2f07a1d858e2ff5bddd`). Dados
precisam ser índices/registros válidos; display/finalização seguem hooks. Sem
ABI/build/link/runtime Apollo. Q371 e Q368/Q369 seguem pendentes. I342/Q102
atualizados; estimativa ~10% pelo escopo amplo e validação guest ausente.

### I342 — `ProcessTopLevel` de `nlsio.c` e seleção r68 (2026-10-14)

Modelei `ProcessTopLevel` (`0x4ea08..0x4ead8`, 208 bytes): resultado negativo
de lookup busca mensagem de domínio 9/código 0x13 e exibe erro; sucesso lê os
campos +8/+0x0c da linha stride 20, chama `display_toplevel`, aplica callback
condicional em ordem determinada por `param3` e bit 0x2000, chama callback
sempre e passa flags sem 0x2000 a `get_error`. Teste cobre not-found e os fluxos
de flags/callbacks; passou C89 estrito e ASan/UBSan. r68 passou 90/90 em cada
perfil após conferir hashes r67. Evidência
`help_viewr_rev/analysis/reconstruction-c/vuehelp-ProcessTopLevelNlsio.evidence.json`
(SHA-256 `7b234c53fc1aae6c197ce34ef70393b698df9b00ffc7dd0fecea703f11daf61d`) e
recibo `host-suite-validation-20261014-r68.json` (SHA-256
`780f3682aca14c765adc62575774e69bb2edae3fa23fd233133fe9449bfb8f9f`). Busca,
mensagem, exibição, callbacks e erro continuam hooks; sem ABI/build/link/runtime
Apollo. I342/Q102 atualizados; Q371 e Q368/Q369 seguem sem resposta no estado
consultado. Estimativa ~10% pelo escopo integral e validação guest ausente.

### I342 — `SearchForFile` de `nlsio.c` e seleção r69 (2026-10-14)

Modelei `SearchForFile` (`0x4c5ea..0x4c6ce`, 228 bytes): busca direta por path
handle em registros stride 32; depois percorre diretórios com flag 0x10, cria
filho ausente pelo hook `build_dir`, limpa somente bit 0x10 quando a criação
falha e propaga grupo/arquivo de busca recursiva bem-sucedida. Teste isolado
passou C89 estrito e ASan/UBSan; r69 passou 91/91 nos dois perfis após conferir
hashes r68. Evidência
`help_viewr_rev/analysis/reconstruction-c/vuehelp-SearchForFileNlsio.evidence.json`
(SHA-256 `748df8140512b1a9338c99ccf60ecf33d3193df565b619e72d3e51bc95b90c2a`) e
recibo `host-suite-validation-20261014-r69.json` (SHA-256
`2191dbbf541e22fc8db226889cdd1087706700be149dc503326a3061edf53997`). Entradas,
contagens e callbacks privados são representados por arrays/hooks; preservada a
recursão sem detecção nova de ciclos. Sem ABI/build/link/runtime Apollo. I342/Q102
atualizados; Q371 e Q368/Q369 sem resposta no estado consultado. Estimativa ~10%
pelo escopo integral e validação guest ausente.

### I342 — `FindHlp` de `nlsio.c` e seleção r70 (2026-10-14)

Modelei `FindHlp` (`0x4c6ce..0x4c7c4`, 246 bytes): exige flag 0x40, mantém
cache +0x1c, reporta erro 0x80 quando falta flag/cache, aloca tamanho+6, copia
e aplica locale, chama parser com buffer duplicado e outputs de dois words,
retorna 0x100 em falha de parse ou decodifica o segundo word em sucesso e sempre
libera o buffer. Teste isolado passou C89 estrito e ASan/UBSan; r70 passou 92/92
em cada perfil com hashes r69 conferidos. Evidência
`help_viewr_rev/analysis/reconstruction-c/vuehelp-FindHlpNlsio.evidence.json`
(SHA-256 `5d3f611861a4ff0f9af06001b56adfc390cb6b8ef20c5a92bac60e9fb155d953`) e
recibo `host-suite-validation-20261014-r70.json` (SHA-256
`020dabbb4695fff94e9159718ff3536fea6c79f51cae845a21bb2850dc99b0cd`). Parser,
alocação, locale e serviços privados continuam hooks; sem ABI/build/link/runtime
Apollo. I342/Q102 atualizados; Q371 e Q368/Q369 sem resposta no estado lido.
Estimativa ~10% pelo escopo integral e validação guest ausente.

### I342 — `ProcessIndex` de `nlsio.c` e seleção r71 (2026-10-14)

Modelei `ProcessIndex` (`0x4ed74..0x4ee02`, 142 bytes): lê índice em +0xd6,
registro stride 14 e campos +6/+8/+0xA, chama `display_info` com constantes,
executa cleanup sempre e cleanup adicional se bit 0x2000 estiver ativo; chama
`get_error` com esse bit removido. Teste isolado passou C89 estrito e ASan/UBSan;
r71 passou 93/93 nos dois perfis após hash-check da r70. Evidência
`help_viewr_rev/analysis/reconstruction-c/vuehelp-ProcessIndexNlsio.evidence.json`
(SHA-256 `e099ac3070beca5e734f1d363d4a9a9e2d7d98d9d6811ed588bc141331308563`) e
recibo `host-suite-validation-20261014-r71.json` (SHA-256
`d2e41ffc947f9169c8e437a884c8baa39b91234360a2921c0c9c5b05fd92d086`). Callbacks
A5 e resolução de dados continuam abstraídos; sem ABI/build/link/runtime Apollo.
I342/Q102 atualizados. Q371 e Q368/Q369 sem resposta no estado consultado.
Estimativa ~10% pelo escopo restante e validação guest ausente.

### I342 — `FindDir` de `nlsio.c` e seleção r72 (2026-10-14)

Modelei `FindDir` (`0x4c3a0..0x4c4b6`, 278 bytes) em adapter host. A rotina
percorre registros stride 32, verifica o flag 0x10 e o limite de prefixo,
desce pelos grupos filhos, constrói diretório ausente pelo hook e limpa somente
o bit 0x10 quando a construção falha. A auditoria corrigiu a escrita do índice
passado por ponteiro: só ocorre ao achar o diretório exato, não durante descida;
falha em descendente preserva o índice original. Testes dedicados passaram em
C89 estrito e ASan/UBSan. r72 passou 94/94 nos dois perfis, usando testes r71
com hashes intactos e adicionando FindDir; exclusões herdadas seguem registradas.
Evidência `vuehelp-FindDirNlsio.evidence.json` (SHA-256
`062729c93924a4d046129ef51388fcafa9c8ca1ddaae5db02be354c35965d6db`) e recibo
`host-suite-validation-20261014-r72.json` (SHA-256
`6ef62fff0f977f2f40f2c233bb337bbcc0eec72b74a5edf0b7de82e8c4e7f307`).
Sem ABI/build/link/runtime Apollo; estimativa I342 ~10% pelo escopo integral
e validação guest ausente. O pedido direto para elevar conexões ftpd foi
registrado no Q102, mas I361 continua sem autorização salva e Q370 sem resposta;
nenhum Telnet nem alteração de guest/ftpd foi feito. Próximo: seguir I342 em
função host independente e aguardar liberação/identificação na prancheta para
qualquer acesso ao serviço.

### I342 — `FindFile` de `nlsio.c` e seleção r73 (2026-10-14)

Modelei `FindFile` (`0x4c4b6..0x4c5ea`, 308 bytes) em adapter host. Ele verifica
igualdade exata do caminho em qualquer linha antes de procurar diretórios pelo
flag 0x10; respeita fronteira NUL/barra, constrói grupo filho ausente por hook,
limpa somente o bit 0x10 em falha e grava os índices de saída apenas no sucesso.
O contador de grupo e os índices usam sinal conforme a assembly, inclusive o
retorno imediato com contagem negativa. Teste dedicado passou em C89 estrito e
ASan/UBSan. r73 passou 95/95 nos dois perfis: fontes r72 com hashes preservados
mais FindFile. Foram carregadas explicitamente as exclusões herdadas de Q371 e
Q368/Q369. Evidência `vuehelp-FindFileNlsio.evidence.json` (SHA-256
`79ded34880c97fc7f9be7f443b8a596e817f4ac7e34b244244e5c55b9e500ad6`) e recibo
`host-suite-validation-20261014-r73.json` (SHA-256
`4f9c607f4d8041b0fbab8b1ecf05be2d956487b88146e201229e2c0ca4d70359`). Continua
sem ABI/build/link/runtime Apollo; progresso integral I342 estimado em ~10% pelo
escopo amplo e validação guest ausente. Próximo: seguir para outra função host
independente enquanto as questões de autoria seguem pendentes.

### I342 — `build_list_from_dir` de `nlsio.c` e seleção r75 (2026-10-14)

Modelei `build_list_from_dir` (`0x4c7c4..0x4c908`, 324 bytes) em adapter host.
A rotina lida com grupo vazio, alocação, filtragem de uma linha, montagem dos
registros stride 14, status acumulado, ordenação, terminador e redução do buffer.
Falha inicial de alocação retorna o valor de falha com bit 8 sem mostrar erro;
falha no shrink mantém o valor de falha, soma bit 8 e chama catálogo/exibição.
Falha de todas as linhas libera o buffer e devolve o valor sentinela. Teste cobre
caminhos vazios, falhas, filtro, sort, shrink e buffer sem redução; passou em C89
estrito e ASan/UBSan. r75 passou 96/96 nos dois perfis com hashes r74 revalidados,
mais o teste atualizado; exclusões de Q371 e Q368/Q369 seguem listadas.
Evidência `vuehelp-BuildListFromDirNlsio.evidence.json` (SHA-256
`82361ce58e789d59b43c320c334a358d014d5c5307939dfc6e350c11748cac80`) e recibo
`host-suite-validation-20261014-r75.json` (SHA-256
`3cd8164bc2e82318d7c43c7369d7f71e7ec7d219ac1f043b549f9f4ad03612aa`). Continua
sem ABI/build/link/runtime Apollo; I342 estimada em ~10% pela amplitude total e
validação guest ausente. I361 sem autorização salva, Q370 e Q354 sem resposta;
nenhum acesso Telnet nem reinício MAME. Próximo: avançar para montagem de listas
por arquivo, independente das perguntas pendentes.

### I342 — `build_list_from_file` de `nlsio.c` e seleção r76 (2026-10-14)

Modelei `build_list_from_file` (`0x4c908..0x4cbb8`, 688 bytes) em adapter host. A rotina valida grupo/linha, aloca lista em blocos de
128 registros stride 14, abre a pasta, ignora índices iniciais 0/1, interrompe
no nome vazio ou charset, elimina nomes iguais consecutivos, registra handle,
comprimento de 16 bits, grupo/linha e índice original, ordena, termina e reduz a
lista. Teste cobre pasta vazia, duplicatas, limites de crescimento, abertura,
alocação inicial, falha de nome e resize. Preserva os retornos antecipados de
falha de abertura/crescimento observados na assembly, inclusive falta de close/
free nesses ramos; o harness recupera buffers simulados após provar a saída.
Teste dedicado e r76 passaram 97/97 em C89 estrito e ASan/UBSan. Exclusões de
Q371 e Q368/Q369 continuam herdadas. Evidência
`vuehelp-BuildListFromFileNlsio.evidence.json` (SHA-256
`75aef75f5954d96948e178be03f5cb96201835bad9e89aeae127d3b8d838f2df`) e recibo
`host-suite-validation-20261014-r76.json` (SHA-256
`4d810c6bcc1a48dbc8eb7acbd090722f1b997d8d45dc1c929ea3ebe1d2ab5ef0`). Sem ABI,
build, link ou runtime Apollo; estimativa integral I342 ~10%. I361 não
autorizada e Q354/Q370 pendentes; nenhum acesso Telnet nem retomada da VM.
Próximo: continuar em função host independente de `nlsio.c`.

### I342 — `processTabs` de `nlsio.c` e seleção r77 (2026-10-14)

Modelei `processTabs` (`0x4cbb8..0x4cc3c`, 132 bytes): cópia até 8.192 bytes,
expansão de tab para a próxima coluna múltipla de oito, NUL final e chamada de
duplicação cujo retorno é ignorado. O hook de preenchimento recebe o recurso de
espaços do programa e a largura calculada. Teste cobre texto simples, tab no
início, larguras 8/7 e limite de saída em fronteira de tab e texto longo; passou
C89 estrito e ASan/UBSan. r77 passou 98/98 nos dois perfis; hashes r76 estáveis,
com exclusões Q371 e Q368/Q369 mantidas. Evidência
`vuehelp-ProcessTabsNlsio.evidence.json` (SHA-256
`2c8d2a5d4ba5ad0950f2d05cb544191cc34cd0100979cc1f78bbe1800ad6e077`) e recibo `host-suite-validation-20261014-r77.json` (SHA-256
`855a2fa711d5d13af50ad85753824476f02ce0fa3c18a79d4dbd05770538ca2d`). Sem
ABI/build/link/runtime Apollo; estimativa I342 ~10%. I361 segue sem autorização;
Q354/Q370 pendentes, sem Telnet/ftpd e sem reinício MAME. Próximo: analisar
`make_msg` ou outra função host independente de `nlsio.c`.

### I342 — `make_msg` de `nlsio.c` e seleção r78 (2026-10-14)

Modelei `make_msg` (`0x4cc3c..0x4cde6`, 426 bytes): parser opcional `@`, leitura
de mensagem type 1, liberação de diretório substituto, fallback por erro/vazio/
sentinela, divisão em linhas, chamada do processamento de tabs, registros stride
14 e terminador. A capacidade cresce em 128 e preserva a sequência de duas
chamadas resize do binário; a falha retorna -1 sem publicar o ponteiro local. O
caminho final pode aumentar capacidade em um. Teste cobre parse/fallback, liberação,
linhas, metadata, expansão dupla e falhas. Dado que a assembly avança após NUL na
última linha, o adapter host encerra com segurança após processar essa linha; os
bytes de saída para string NUL-terminada são equivalentes. Teste dedicado e r78
passaram 99/99 em C89 estrito e ASan/UBSan; exclusões Q371 e Q368/Q369 mantidas.
Evidência `vuehelp-MakeMsgNlsio.evidence.json` (SHA-256
`19860422081f67b7acbbe901aec5f18e5c18e03f97b7ae3a6da11cfcaddfe3b8`) e recibo `host-suite-validation-20261014-r78.json`
(SHA-256 `72a896e31de44030fe9fc20fd234c3ab6b7307ceec2600ad293a54da4c77c682`).
Host-only, sem ABI/build/link/runtime Apollo; estimativa total I342 ~10%. I361
segue sem autorização e Q354/Q370 sem resposta. Próximo: continuar em outra
rotina independente de `nlsio.c`.

### I342 — `build_msg_list` de `nlsio.c` e seleção r79 (2026-10-14)

Modelei `build_msg_list` (`0x4cde6..0x4cf92`, 428 bytes): preparação condicional,
validação de índices, abertura/leitura de entrada type 1, limpeza dos nomes da
lista anterior, duplicação separada do buffer da mensagem, divisão por linhas e
despacho a `make_msg`. Os caminhos abrem/fecham e reportam erro na ordem da
assembly; no sucesso retorna a primeira word da lista, e erro de montagem retorna
o sentinela. Teste cobre preparação, open failure, texto vazio/sentinela, limpeza,
linhas e falha parcial. O adapter encerra com segurança após a última linha sem
newline, sem avançar além do NUL. Teste dedicado e r79 passaram 100/100 em C89
estrito e ASan/UBSan, mantendo Q371 e Q368/Q369 como exclusões. Evidência
`vuehelp-BuildMsgListNlsio.evidence.json` (SHA-256
`10f1998842bf51cc44f131799ab2898f7635f9a9d2c6b75e8aae61c6ffe43cb2`) e recibo `host-suite-validation-20261014-r79.json`
(SHA-256 `c49a9fb48ad03ee50199490690c006faa1f76e0a8dde06dd1277fe9840b88371`).
Host-only, sem ABI/build/link/runtime Apollo; I342 ~10%. I361 sem autorização e
Q354/Q370 sem resposta; nenhuma ação Telnet/VM. Próximo: continuar em rotina
independente de `nlsio.c`.

### I342 — `build_dir` de `nlsio.c` e seleção r80 (2026-10-14)

Modelei `build_dir` (`0x4cf92..0x4d058`, 198 bytes): preparação, cópia do caminho
e corte dos quatro caracteres finais, criação do grupo no slot do próximo ID,
atualização do contador e dos parent pointers nas linhas filhas. Sucesso também
salva o child group e zera a lista de mensagens da linha pai; falha retorna -1
sem alterar contador nem linha pai. Teste dedicado passou e r80 passou 101/101 em
C89 estrito e ASan/UBSan, preservando exclusões Q371/Q368/Q369. Evidência
`vuehelp-BuildDirNlsio.evidence.json` (SHA-256
`793aa965d650b49b724e9ad7b52bc5d1bccb3f8a4544b3f1bb43cf84646d9937`) e recibo `host-suite-validation-20261014-r80.json`
(SHA-256 `91770f52ef88e4bb77460ae9f1ce0f160c0aee4789cdd1229fb9f9ebf17b81f2`).
Host-only, sem ABI/build/link/runtime Apollo; I342 ~10%. I361 sem autorização
salva e Q354/Q370 sem resposta, sem Telnet ou retomada da VM. Próximo: reconstruir
outra rotina host de `nlsio.c`.

## 2026-10-14 17:05 UTC — V08 pareado e revalidação Xephyr

P10 revisão 1 continua autorizada e em andamento. A captura 1:1 de Help Viewer
SR10.4/HP VUE 2.01 pareia “Lines 1 to 15 of 165” com o consumidor real Plasma
PC.ScrollBar+KSvg numa fixture: trilho 15×228 px em ambos; thumb nativo 11×21
em y=1 e Plasma 11×20 em y=2. A diferença completa do trilho inclui o fundo
Plasma oculto em repouso. A prova privada de inset 1 px não corrigiu o
comprimento vertical e alargou o eixo horizontal para 13 px. Registrei hashes,
limites e a variação privada em `docs/VALIDACAO-V08-PLASMA-20261014.json`,
checklist e fila visual; nenhum SVG/QML de produto mudou. Q372 revisão 0 foi
reconhecida e aguarda a escolha entre documentar o limite ou abrir uma demanda
QML autônoma. Produção aberta no PID 3339378; canal Q102 seq.256.

Revalidação de I217/I295: Xephyr :68 PID 1442542 permanece viva, mas a raiz X
está sem janelas filhas; MAME não está ativo e TAP `tap-mess-1000-0` está
DOWN/NO-CARRIER. `mame_control.py status` no diretório explícito I295 devolveu
request `4260854bc6024f04a92238d48a3cd4c7` sem reply/ack. Não houve novo input,
tentativa, alteração na bridge ou reinício. Atualizei somente os campos da IA
de P10, I217 e I295 pela CLI, conservando os registros humanos; Q334/Q354 e as
escolhas visuais continuam aguardando resposta. I342 segue em progresso no
registro de outra IA; I167/T04 permanece com a responsável anterior. Itens já
entregues à avaliação não foram repetidos. Não encontrei demanda independente,
autorizada e executável agora que não cruze o gate da VM, o limite de uma família
visual ou o trabalho da outra IA.

## 2026-10-14 — I342 `build_man` de `nlsio.c` e seleção r81

Modelei `build_man` (`0x4d08a`, 288 bytes) como adapter host e corrigi a
publicação do grupo filho para ocorrer somente após `make_man` retornar sucesso,
conforme o pseudocódigo. O teste dedicado cobre falha sem modificar contador ou
registro pai, ordenação, vínculos pai e marcação de rótulos duplicados. Seleção
r81 passou 102/102 em C89 estrito e 102/102 em ASan/UBSan; hashes dos testes
selecionados conferidos contra r80. Evidência `vuehelp-BuildManNlsio.evidence.json`
(SHA-256 `3d8db8bcc1d6753515b63bd55010781bf8a7bd3a29c14fb412c0d4b30be21f82`)
e recibo `host-suite-validation-20261014-r81.json` (SHA-256
`238fef487d575b96fbdab2dfd23b91929f5967f2ce40ea82a628d683b733abd4`). Host-only;
sem build, link ou execução Apollo. I361 continua sem autorização e Q354/Q370
aguardam resposta; não usei Telnet nem retomei a VM. Progresso integral I342
estimado em ~10%, pelo amplo escopo restante e ausência de validação guest.
Próximo: continuar na próxima rotina independente de `nlsio.c`, preservando as
exclusões registradas até receber respostas.


## 2026-10-14 17:10 UTC — P07: transporte do catálogo ao ConfigView

Conferi o recibo e os hashes atuais: `ConfigTray.qml` e `DomainOSTray.qml`
seguem iguais aos ensaiados. A reprodução preservada mostra o applet proprietário
ID 3 com catálogo de 18 provedores e ConfigView ID 4 sem `internalAction`,
`availableItems=[]`; 14/43 gates comportamentais da ordenação falham. Não
alterei outra bandeja/configuração ao abrir preferências. Abri e reconheci Q373
(rev0), após P07, pedindo a escolha entre uma ponte transitória somente leitura
e manter os campos avançados por IDs com limitação explícita. P07 segue parcial;
Q335 (Volume) e Q336 (menu/contexto) ficam separadas. Nenhum código ou perfil
pessoal foi alterado.

## 2026-10-14 — I342 `build_man_list` de `nlsio.c` e seleção r82

Modelei `build_man_list` (`0x4d1aa`, 616 bytes) com hooks host para diretório,
comparação, resolução de nomes e alocação. O adapter preserva o cursor de
entradas entre comparações ordenadas, ignora os registros com bit `0x4`, monta
os caminhos conforme a ordem dos `strcpy`/`strcat` no assembly, usa o rótulo
original quando não há correspondência ou a alocação de caminho falha, e grava
um terminador nulo na lista. Teste dedicado cobre ordenação, correspondência,
entrada marcada e falha ao abrir diretório. R82 passou 103/103 em C89 estrito e
103/103 em ASan/UBSan; hashes da seleção herdada r81 conferidos. Evidência
`vuehelp-BuildManListNlsio.evidence.json` (SHA-256
`c26b9f847f3008fb764521105711ce718b9e142a95f6c9e2b6cf164d499f17ea`) e recibo
`host-suite-validation-20261014-r82.json` (SHA-256
`a793385f60adb223297ceb3938306bc4150540f94d13ffb3a4129c24a3ce233d`). O registro
resultante do adapter é uma estrutura host; não comprova o layout de 14 bytes,
ponteiros ou ABI Apollo. Sem build/link/runtime Apollo. I361 não autorizada e
Q354/Q370 pendentes; sem Telnet ou reinício MAME. Estimativa integral I342 ~10%
pelo amplo escopo restante e ausência de validação guest. Próximo: continuar
reconstrução estática de uma rotina independente de `nlsio.c`.

Nota de integridade I342 r81–r82: atualizei `help_viewr_rev/README.md` e
acrescentei os dois adapters, testes, evidências e recibos r81/r82 em
`help_viewr_rev/SHA256SUMS`; os novos registros conferem. A verificação integral
continua apontando quatro entradas preexistentes divergentes: os três arquivos
StartTopicsListBMS pendentes de Q368/Q369 e `vuehelp-SizeIndexDialog.evidence.json`.
Preservei os arquivos e não alterei essas entradas.

I342r3 continua autorizada/running no estado verificado; Q102 segue revision 191,
sem resposta humana nova, e recebeu a atualização de integridade na sequência
260. I361 permanece `authorized=false`; Q354 e Q370 continuam aguardando. Não
houve acesso Telnet nem operação na VM nesta etapa.


## 2026-10-14 — P08: margem lateral de Applications

P08 r1 autoriza o defeito descrito. A releitura da implementação mostrou que
`PanelButton` centraliza uma caixa 54×40 dentro da face interna de 44×44; o gate
anterior só verificava a altura e deixava passar a sobra lateral. Corrigi a caixa
para 36×36, mantendo o SVG 4:3 com `PreserveAspectFit`, os papéis dinâmicos de cor
e margem geométrica mínima de quatro unidades em todos os lados. O gate confere
agora os quatro limites. Xvfb software passou 49/49 e OpenGL threaded passou 49/49;
a captura 971×109 é da cena QML isolada, não do Plasma completo. Xephyr :74
excedeu 60 s sem gerar resultado; não conto esse ensaio como aprovação.

A verificação seca do instalador oficial falhou porque falta `Qt6Qml.pc`; nenhum
pacote foi instalado, nenhuma preferência pessoal foi alterada e o plasmashell
não foi reiniciado. O recibo do Plasma completo existente representa 54×40 e está
obsoleto para a nova geometria. Próximo: quando houver SDK Qt6Qml válido, preparar
o beta por fluxo oficial reversível e então coletar captura integral 1:1 para
revisão. Q334 e revisão visual ainda aguardam; o cálculo 97% é avanço técnico,
não percentual de fidelidade.

## 2026-10-14 — I342 `set_glossaryText` de `nlsio.c` e seleção r83

Modelei `set_glossaryText` (`0x4d776`, 168 bytes) sem nomear os hooks privados:
duas chamadas de conversão encadeadas; atualização inicial com o primeiro token
de recurso e o valor recebido; segunda chamada indireta com saída para um handle
opaco; e atualização final desse handle com três pares, usando os tokens A5
observados e `position`, `2*position`. O teste confere argumentos, saída opaca e
ordem. R83 passou 104/104 em C89 estrito e 104/104 em ASan/UBSan, com hashes da
seleção r82 conferidos. Evidência
`vuehelp-SetGlossaryTextNlsio.evidence.json` SHA-256
`c83b89ebcc81351bfad2bdda5be67a1b4b82ed95c865876ff88044cc43e9e15f`; recibo
`host-suite-validation-20261014-r83.json` SHA-256
`fa0805597ea39dee1ecc4cb5e87029fa7336048a74925108f50051a6b2d835cd`. README e
SHA256SUMS do help_viewr_rev incluem o adapter, teste, evidência e recibo. A
checagem integral mantém as quatro divergências anteriores, sem modificá-las.
Hooks A5, tipos Xt, ABI e guest continuam sem prova; sem build/link/runtime
Apollo. I361 não autorizada; Q354/Q370 pendentes; sem Telnet ou alteração na VM.
I342 estimada em ~10% pelo amplo escopo restante e ausência de validação guest.
Próximo: continuar na próxima rotina estática independente e manter as perguntas
pendentes preservadas.

A prancheta confirma I342r3 autorizada/running. Q102 recebeu esta atualização na
sequência 261; não havia resposta humana nova. I361 segue sem autorização, Q354 e
Q370 aguardam respostas, e nenhuma sessão Telnet ou VM foi tocada.

## 2026-10-14 — I342 `get_title` de `nlsio.c` e seleção r84

Modelei `get_title` (`0x4dc1c`, 138 bytes): carrega o token de caminho em +4,
abre com modo zero; em falha obtém o erro corrente, chama `processError(error,
path)` e retorna o título fallback; em sucesso consulta o campo 2 no índice
recebido e fecha o handle. Teste dedicado cobre sucesso e falha, incluindo a
ordem. R84 passou 105/105 em C89 estrito e 105/105 em ASan/UBSan, com os hashes
da seleção r83 conferidos. Evidência `vuehelp-GetTitleNlsio.evidence.json`
(SHA-256 `7d2c53e88574101c9b27e68c55db70d0c5046a1d5ad709658a4ddc3ea0adf5de`) e
recibo `host-suite-validation-20261014-r84.json` (SHA-256
`700c7c96a72e378678c164faa6a3d471c1dc0751bc436f700c79f1c89bf948ca`). README e
SHA256SUMS do help_viewr_rev incluem os artefatos desta função; a checagem global
mantém as quatro divergências conhecidas. Sem build/link/runtime Apollo. I361
não autorizada, Q354/Q370 pendentes; nenhuma ação Telnet ou MAME. Estimativa
integral I342 ~10% pelo grande volume restante e validação guest ausente.
Próximo: continuar reconstrução host de rotina independente de `nlsio.c`.

Estado após r84: I342 rev3 segue autorizada/running; Q102 recebeu o avanço na
sequência 262, sem resposta humana nova. I361 continua sem autorização e Q354/
Q370 aguardam decisão. Nenhuma interação com a VM ocorreu.

## 2026-10-14 — I342 `display_toplevel` de `nlsio.c` e seleção r85

Modelei `display_toplevel` (`0x4dca6`, 410 bytes) como adapter de orquestração
host. Mantive hooks privados separados para operações de widget, `RootIndex2`,
listas de mensagem/tópicos e glossário; o teste verifica sua ordem, valores e
ramos. O adapter também modela os campos +2, +0xc4 e +0xf2 dos widgets, incluindo
a condição `widget[3]+0x102 == 4`, o valor de grupo especial e o índice de linha
negativo. R85 passou 106/106 C89 estrito e 106/106 ASan/UBSan; hashes da seleção
r84 conferidos. Evidência `vuehelp-DisplayToplevelNlsio.evidence.json` (SHA-256
`6b53701d8e259cf5039d7a1837c90e7f4627734bc035f41c249e1b79d387bbc8`) e recibo
`host-suite-validation-20261014-r85.json` (SHA-256
`c7c9d772cfb89d6b8dc6e9402d3d3e107d7a36127c8767d591d57c936e082893`). README e
SHA256SUMS do help_viewr_rev incluem os artefatos desta função. As quatro
divergências globais de hash persistem sem alteração. O modelo não prova
layout Apollo, ponteiros, ABI ou comportamento Xt e não foi compilado/ligado/
executado na VM. I361 não autorizada; Q354/Q370 aguardam. Próximo: continuar
reconstrução de rotina independente, sem inferir execução guest.

I342 rev3 permanece autorizada/running. O CLI da prancheta passou a exigir
`--ai-context board` para escritas desta área; após identificar o contrato e
repetir com o contexto correto, o reply e Q102 foram aceitos. Q102 está na
sequência 263, sem resposta humana nova. I361 segue não autorizada; Q354/Q370
continuam pendentes. Nenhuma ação na VM.

## 2026-10-14 — I342 `display_gloss` de `nlsio.c` e seleção r86

Modelei `display_gloss` (`0x4e326`, 506 bytes) com hooks para leitura, erro,
`make_msg`, armazenamento de lista, conversão e atualização de glossário. O
adapter cobre a abertura do caminho, o caso vazio/default, a separação de texto
em linhas, acumulação de mensagens, concatenação com separador, liberação dos
recursos e os caminhos de erro. O teste exercita sucesso com duas linhas, campo
default e falha de abertura. R86 passou 107/107 em C89 estrito e 107/107 em
ASan/UBSan; hashes r85 conferidos. Evidência
`vuehelp-DisplayGlossNlsio.evidence.json` SHA-256
`4cf8b8c2eb5a38286cd6a3fe6f2600e6a40391281a4202ed3b4186abb5ceb85f`; recibo
`host-suite-validation-20261014-r86.json` SHA-256
`ea7fa8b13f1d8fc31b98fc80acd5604401286fd0b80d33323c6ecc7a601bdb7d`. README e
SHA256SUMS atualizados; as quatro divergências anteriores permanecem. A
representação da lista `make_msg`, o separador e os efeitos Xt permanecem hooks;
o layout e ABI Apollo não foram provados e não houve build/link/runtime guest.
I361 não autorizada, Q354/Q370 pendentes, sem Telnet ou operação MAME. Estimativa
integral I342 ~10% pelo amplo restante e pela validação guest ausente.

I342 rev3 permanece autorizada/running. Q102 recebeu r86 na sequência 264, sem
resposta humana nova. I361 segue sem autorização e Q354/Q370 aguardam; não houve
acesso ao guest.

## 2026-10-14 — I342 `ProcessTopic` em `nlsio.c` (r87)

Reconstruí `ProcessTopic` (`0x4e7cc`, 572 bytes) como adapter semântico host em
`/home/lsi/Documents/Projetos/help_viewr_rev/analysis/reconstruction-c/`. O
fluxo cobre stride 20 da tabela e campos observados +0/+4/+8, validação
curto-circuitada, fallback do tópico, montagem de caminho, erros 15–18, busca,
`display_info`, limpeza e máscara do status. A revisão do assembly corrigiu a
passagem do índice mutável: `FindDir` e `SearchForFile` recebem o mesmo endereço,
e o índice resultante é encaminhado a `display_info`; o teste comprova a cadeia.
Os helpers A5/Xt e o layout/ABI
permanecem abstraídos. Teste e seleção completa r87 passaram 108/108 em C89
estrito e 108/108 em ASan/UBSan; a lista r86 foi preservada e seus hashes não
mudaram antes da seleção. As três exclusões herdadas foram mantidas. Evidência
`vuehelp-ProcessTopicNlsio.evidence.json` SHA-256
`d8fc09a96d703855a6c760183ef3595b2ee6aa799e18d96d226880ae50f3dfac`; recibo r87
SHA-256 `c807c6dc7e5bb501959f2731db19019e549a9907bdc6c93a11d0b9cb5e381969`.
README e SHA256SUMS do projeto foram atualizados; as quatro divergências
históricas globais continuam preservadas. Nenhum build/link/runtime Apollo:
I342 continua parcial, estimativa integral ~10% pelo escopo de aplicação e
bibliotecas ainda aberto e pela falta de validação guest. I361 não autorizada;
Q354/Q370 sem resposta. Não usei Telnet/MAME nem alterei VM, rede ou ftpd.
Próximo: reconstruir outra rotina NLSIO ainda não modelada com fluxo assembly
suficientemente determinado. Q102 recebeu a atualização inicial na sequência 266;
as correções de contrato foram informadas nas sequências 268 e 269. I342
revisão 3 segue autorizada e `running`. I361 revisão 0 continua sem autorização
salva.

## 2026-10-14 — I342 `ProcessManualPage` em `nlsio.c` (r88)

Modelei `ProcessManualPage` (`0x4ead8`, 622 bytes) como adapter semântico host
em `/home/lsi/Documents/Projetos/help_viewr_rev/analysis/reconstruction-c/`.
O fluxo cobre salvamento e validação do caminho, ordem dos hooks de controle,
extração e liberação dos dados, lookup de página/título, comparação com a entrada
raiz, seleção de recursos, escritas nos widgets e resets de rolagem. Testes
verificam raiz correspondente e alternativa, caminho nulo/default e manual
inexistente. R88 passou 109 testes únicos em C89 estrito e 109 em ASan/UBSan;
os 108 testes herdados de r87 foram deduplicados por caminho/hash e as três
exclusões conhecidas foram preservadas. Evidência
`vuehelp-ProcessManualPageNlsio.evidence.json` SHA-256
`cc27eb867509fb40c7f972dbc63946c152ffdf6bd30d405b7070fdcce997f146`; recibo r88
SHA-256 `e8f29290a9c8b24faa6ff8d37d0ee5198ddc420afa49d8a8540753634a35923e`.
README e SHA256SUMS atualizados. Os hooks A5/Xt, estruturas privadas, ABI e
execução Apollo continuam sem prova. I342 segue parcial (~10% pelo escopo total
restante e falta de validação guest). I361 segue sem autorização; Q354/Q370
aguardam. Nenhuma ação Telnet/MAME ou mudança de VM/rede/ftpd. Q102 recebeu
este avanço na sequência 270; I342 revisão 3 permanece autorizada e `running`.

## 2026-10-14 — I342 `build_related_topics` em `nlsio.c` (r89)

Modelei `build_related_topics` (`0x4d464`, 786 bytes) como adapter semântico
host em `/home/lsi/Documents/Projetos/help_viewr_rev/analysis/reconstruction-c/`.
O fluxo cobre limpeza inicial, erros de leitura, campo sentinel, parsing por
linha, passagem de handle mutável, fecho dos handles filhos conforme os ramos
assembly, crescimento dos registros persistentes, identidade grupo/linha/índice,
entrega dos itens ao widget e liberação. R89 passou 110 testes únicos em C89
estrito e 110 em ASan/UBSan; os 109 herdados de r88 foram deduplicados por
caminho/hash e as três exclusões conhecidas foram preservadas. Evidência
`vuehelp-BuildRelatedTopicsNlsio.evidence.json` SHA-256
`0faed55d4b30058bdb115492e5f48fbeddb2a5909bc842816ec42d0bf5e4b8d6`; recibo r89
SHA-256 `d7d5d06d31805fff4bf1e35344d8038f91c91cd926d0a907fa1c1bcbec52ae5a`.
README e SHA256SUMS atualizados. Hooks A5/Xt, estruturas, ABI e execução Apollo
permanecem sem prova. I342 segue parcial (~10% pelo escopo restante e falta de
validação guest). I361 sem autorização, Q354/Q370 aguardam. Sem Telnet/MAME ou
mudança na VM/rede/ftpd.
Q102 recebeu este avanço na sequência 272; não havia resposta humana nova. I342
revisão 3 permanece autorizada e `running`.

## 2026-10-14 — pedido de ampliar conexões do ftpd

O usuário reiterou o pedido para usar Telnet e aumentar a capacidade de conexões
do ftpd. A releitura pela CLI confirma I361 `authorized=false`; Q370 segue sem
resposta sobre as sessões Telnet existentes e Q354 permanece `waiting_user`.
Como as regras da prancheta exigem autorização salva por item e os gates de
acesso ao guest ainda não foram resolvidos, não abri Telnet nem alterei o ftpd.
Q102 foi atualizado na sequência 273 com o estado e os passos para destravar.
I342r3 continua autorizada; o próximo trabalho host é `build_glossary` em
`nlsio.c` (0x4d87e, 926 bytes), sem depender desses gates.

## 2026-10-14 — coordenação concorrente de `build_glossary`

Ao iniciar r90, a versão compartilhada de `vuehelp-BuildGlossaryNlsio.c` mudou
durante a preparação de seu teste, em duas gravações observadas às 14:01:24 e
14:02:16 -04. A implementação deixou de corresponder ao teste, e o recibo r90
não inclui essa rotina. Para não sobrescrever trabalho de outra IA, não alterei
novamente os arquivos após detectar a segunda mudança. Registrei Q377 após I342
para decidir autoria/ordem; Q377 revisão 0 foi reconhecida, sem resposta humana
até a leitura atual. Q102 recebeu o aviso na sequência 274. I342r3 permanece
autorizada e `running`; a rotina não foi validada e sua conclusão está em espera
de coordenação. A ação do `ftpd` continua sem Telnet ou alteração do guest.

Atualização de verificação: o teste e adapter compartilhados ficaram estáveis
durante uma execução r91. A suíte completa passou 112/112 em C89 estrito e
112/112 em ASan/UBSan, com hashes dos 112 testes e do adapter conferidos antes e
depois. Recibo `host-suite-validation-20261014-r91.json` SHA-256
`4975f6fb75b93c7769b586f0e6ac6da669f7b7acd644d5bc10b5032dc96ffd93`; adapter
SHA-256 `0c93813389e56cea670156e0cfcc2417521be3943285a7a7af42fbc4c4370ed8`;
teste SHA-256 `6bb45d96934d9bcf25cf6b6da7a3b9c1ab4949172df71d73c095fa1e635acb8f`.
Uma execução sanitizada iniciada durante as gravações concorrentes falhou com
`stack-use-after-return`; a repetição após estabilização passou. A causa da
primeira falha não foi isolada. Leitura comparativa ainda pede verificar que o
índice inicial de `FindFile` venha do campo `group-record +8` observado no
assembly, distinto do índice de grupo usado para obter diretório. Sem
`build_glossary.evidence.json`, README/SHA256SUMS ou prova Apollo por decisão de
não disputar os arquivos até a resposta Q377. Q102 atualizado na sequência 275.

Releitura posterior (Q102 seq.277): o estado compartilhado já contém
`vuehelp-BuildGlossaryNlsio.evidence.json`, README e SHA256SUMS para o adapter.
Os hashes de modelo/teste conferem; r91 foi regravado no projeto compartilhado
após a primeira criação, então o recibo atual substitui o hash histórico acima:
`3cb662a868aefc5e0d27f31d51a2952ff941f4835a923bbc14b575b7e9aa24f4`.
A auditoria direta do pseudocódigo (0x4d9bc) e assembly encontrou que o índice
inicial para `FindFile` deve vir do campo +8 do registro de grupo, não do índice
resolvido usado para localizar o diretório. Em 0x4d9a0, `set_glossaryText` também
recebe dois valores nos offsets +0x8c/+0xba além do widget; o adapter não os
representa. Essas diferenças foram comunicadas no Q102 seq.277. Não editei
adapter/teste durante a coordenação pendente Q377; `build_glossary` continua sem
conclusão de fidelidade e sem validação Apollo.

Inventário independente do TSV de funções NLSIO versus adapters disponíveis:
42 rotinas totais, 35 com adapter host e 7 ainda sem fonte de modelo:
`CmpLine`, `get_error`, `processError`, `RootMsg`, `CmpFileLabel`, `display_info`
e `RestoreTorn`. O próximo alvo estrutural depois da coordenação é
`display_info` (0x4de40, 1.254 bytes); `RestoreTorn` mede 844 bytes. A conta é
limitada a `nlsio.c` e não representa a cobertura do Help Viewer/dependências.
Q102 seq.278 recebeu essa base; I342r3 segue autorizada/running.

## 2026-10-14 — I342 `display_info` e `RestoreTorn` (r94–r95)

Retomei trabalho host autorizado sem acessar a VM. Reproduzi a seleção r93:
113/113 fixtures em C89 estrito e 113/113 em ASan/UBSan; os hashes dos fixtures
foram conferidos antes/depois. Recibo r94 SHA-256
`f0bb03f7b4d34a2f94b004529c78c4df8d7d641b155877f4e2272b990c1a3ec7`; README e
SHA256SUMS agora incluem `display_info` e sua evidência atualizada.

Modelei `RestoreTorn` (`nlsio.c`, `0x4f01e`, 844 bytes) em
`/home/lsi/Documents/Projetos/help_viewr_rev/analysis/reconstruction-c/`, com
rotas de tópico/diretório/manual, duas leituras, parsing de linhas, mensagens e
limpeza por hooks explícitos. R95 passou 114/114 em C89 estrito e 114/114 em
ASan/UBSan; os 113 fixtures herdados permaneceram hash-idênticos. Recibo SHA-256
`d9344a36be87697ad0209ae185d630303c720d73ab3c1c2392f18d2e58a1d3ad`; adapter
`7a9d890f2854737a2cf5cd5dd20885dc21edda4fe79e37d97bfdfcc7df482349`; teste
`5aff4a57be74b71a0d4076f0de5bd2a931e2c5ec443c89c37ca6d0fa3ab53aab`; evidência
`16b39d5aa3f18a6b610c71ffb440540397be7cc8876b910a58d159ca96808232`.

Correção do inventário anterior: as 42 funções DST de `nlsio.c` agora têm modelo
host; `CmpLine`/`CmpFileLabel` são cobertos por `CmpWrappers`, e `RestoreTorn`
completou a única função antes sem adapter. Isto mede apenas os anchors NLSIO,
não a reconstrução do Help Viewer/dependências, nem prova C original, ABI ou
execução Apollo. O limite de caminho de 1.026 bytes no adapter RestoreTorn é uma
divergência de segurança explícita frente à concatenação do target. Próximo:
continuar o inventário/análise fora de NLSIO e consolidar as pendências sem tocar
no `build_glossary`/`get_title` em coordenação concorrente. Q377 permanece sem
resposta; I361 continua sem autorização e Q354/Q370 sem resposta, portanto não
houve Telnet, MAME ou mudança de ftpd/VM. Q102 estava na seq.281 antes do novo
registro desta etapa; I342r3 segue autorizada/running, goal incompleto.

## 2026-10-14 — I342 Xt r4 `XtAppGetSelectionTimeout` (r96)

Avancei a primeira função de dependência fora de NLSIO: `Selection.c`
(`0x50628`, 24 bytes) retorna a palavra de 32 bits no offset `+0x3c` do
application record. Adapter host e fixture dedicado verificam o offset e três
valores. R96 passou 115/115 fixtures em C89 estrito e 115/115 em ASan/UBSan;
os 114 herdados ficaram com hashes idênticos antes/depois. Recibo SHA-256
`aeda4b707ab571b5535ca8284e4c67225e81e12ed6f04a337f2667130a1079aa`; modelo
`10d3dea91416d9d7bb80027bbbc185e152e54203733fa3d6dcf0309ffc7e64fa`; fixture
`e4ab84a0a4045b4cf785404b50920a6acbd49ae974c1681583808622b361a257`; evidência
`eb9d30f5b75aabfd4586769b7cbc76dcdee660e75cbdc4032c91d88a1162c582`. README e
manifesto passaram verificação dirigida de SHA-256.

Escopo remanescente objetivamente maior: as sete imagens de dependência exportadas
contêm 5.248 anchors DST (bmslib 542, xvlib 368, x11lib_r4 577, libc 620,
xmlib1_1 2.332, xtlib_r4 714, libsoftlib 95). Isso não prova que todos sejam
referências executadas pelo Help Viewer, mas mostra que cobrir NLSIO não conclui
as bibliotecas. O adapter usa palavra host de 32 bits; não prova layout/ABI Xt
Apollo ou runtime. Próximo passo é continuar o inventário por dependência e
selecionar outra função independente com assembly/pseudocódigo exportados.
Nenhuma validação Apollo, compilação/link na VM ou ação Telnet foi feita. Q102
recebeu r95 na seq.282; esta nova etapa ainda será enviada. I361 e Q354/Q370
seguem nos estados anteriormente registrados.

## 2026-10-14 — I342 Xt r4 `XtWindow` (r97)

Modelei a leitura de `XtWindow` (`Intrinsic.c`, `0x4b108`, 24 bytes): palavra no
offset `+0x5c` do widget. Fixture de layout/valores e adapter host passaram;
a suíte r97 passou 116/116 C89 estrito e 116/116 ASan/UBSan, com os 115 hashes
herdados intactos. Recibo SHA-256
`dc24995ee4bdcedee3d65faa0e9314fee7c7ac9222082ae8822bfc1ba857241b`; modelo
`bdaf368a4212385fc9466bdbb4c514472d47c55a26b4ad05ef2fdf5fba29504e`; teste
`39b6a9511e6bc0d716e3d3e800658c8d73275ee51c6e1af8169ab6648bcf3da2`; evidência
`4b10e42a4b2ee36327df66cd7d3c1fcceb320b5a278e6780bed600355f2a0139`. README e
SHA256SUMS conferidos. O host usa unsigned int de 32 bits; isso não certifica
layout/ABI Apollo ou Xt em execução. Base do avanço: 42/42 anchors NLSIO têm modelo
host e dois accessors Xt têm adapters/fixtures integrados; 5.248 anchors ainda
aparecem nas sete bibliotecas exportadas, sem cobertura integral. Não apresento
percentual global até reconciliar todos os símbolos e build/runtime Apollo.
Próximo: seguir inventário Xt/Xlib e escolher função não modelada com limites
claros. Nenhuma ação guest/Telnet. Q102 seq.283 tinha r96; esta atualização ainda
será enviada. I342 revisão 3 continua autorizada/running.

## 2026-10-14 — I342 Xt `XtIsManaged` / `XtIsSensitive` (r98)

Modelei dois predicados de estado de `Intrinsic.c` a partir de pseudocódigo e
assembly: `XtIsManaged` exige o bit `0x02` em class flags e retorna o byte managed
sem normalizar; `XtIsSensitive` exige esse bit, o byte `+0x25` e normaliza o byte
`+0x26` para booleano. R98 passou 117/117 fixtures em C89 estrito e 117/117 em
ASan/UBSan; os 116 fixtures herdados permaneceram com os mesmos hashes.
Recibo SHA-256 `bc2e8edfebad055cf5dbba713d4f346769deba75349ef137248b69f4b471fed1`;
adapter `b74895de36614fb0860281ee100c257542f60342dcb81bc7d721e0bc0a1eb2e3`;
teste `fc1b8f72f1e4359df55e58940dedb629ce655312b7b0e9ed437db472d5a1203e`;
evidência `7a1dae18c553e227ea3b083686d15b271cb56d761a01270f63ea373bef6dd84f`.
README/SHA256SUMS dirigidos conferidos. O adapter recebe bytes dos campos sem
impor estrutura/pointer layout; Apollo ABI e runtime Xt seguem sem prova. A
cobertura host inclui agora quatro funções Xt específicas em três adapters e os
42 anchors NLSIO; 5.248 anchors de dependências ainda requerem reconciliação.
Próximo: escolher serviço Xt de tamanho/risco adequado fora desses accessors.
Q102 recebeu este avanço na seq.285. Sem atividade na VM.

## 2026-10-14 — I342 Xt `XtClass` / `XtSuperclass` (r99)

Modelei o acesso à classe e à superclasse em `Intrinsic.c` (0x4b142, 26 bytes;
0x4b120, 34 bytes). Os adapters host usam ponteiros nativos para preservar a
identidade da cadeia, sem afirmar o layout/pointer ABI Apollo. R99 passou 118/118
em C89 estrito e 118/118 em ASan/UBSan; os 117 herdados ficaram hash-idênticos.
Recibo SHA-256 `b9da1dd6ff62f601d42d8ea40e42692c47f9d15114ec18affe463988c64ef502`;
adapter `43f2c8473825b8f9aa141e3a43166ad801c2836083c4a2b08ead492a2b89c460`;
teste `93726f226c46a2fc71158c122f3371101b2b9a990a45fc73e0e32e5971516681`;
evidência `6e23d9c0f78467dd527f2c85da4989c664ff4f80e632ddc67e4e45d77b17f9e0`.
README/SHA256SUMS conferidos. Seis funções Xt têm agora adapters/fixtures host
em quatro módulos; isso segue estreito frente às 714 funções DST de Xt r4 e às
5.248 âncoras das sete dependências. Próximo: continuar nos caminhos Xt realmente
chamados pelo Help Viewer; nenhuma validação Apollo ou mudança na VM. Q102 seq.285
tinha r98; este r99 ainda será enviado. I342 permanece parcial/autorizada.

## 2026-10-14 — I342 Xt `_XtWindowedAncestor` (r100)

Modelei a travessia de pais (`Intrinsic.c`, `0x4b1e2`, 122 bytes): começa no pai,
pula classes sem bit `0x04`, retorna o primeiro ancestral windowed e, se nenhum
existir, chama o hook de aviso com o nome do widget original. R100 passou 119/119
em C89 estrito e 119/119 em ASan/UBSan; os 118 fixtures anteriores conservaram
seus hashes. Recibo SHA-256
`0dab932798d54d6b6584d8b3a81f5ea4b8ca2cbb81c143ec1fb67428cb4114b5`; adapter
`bce8641f43a32a4f59e831a0a1faff4e19cc6648f2f792e28c9e8663d83d2763`; teste
`eac5e7721107abab5fe0140b93641f1e9709a570d4c847da839aa21ed8e19126`; evidência
`75a91a627f1c4fcd8043a0a98d958e0686452f90f0a8f198c7b14b253fe696ff`. README e
manifesto conferidos. O inventário host cobre sete funções Xt específicas em
cinco adapters, contra 714 anchors Xt r4; a auditoria deve priorizar chamadas
relevantes e continuar cobrindo as demais bibliotecas. XtName, warning real,
layout/ABI Apollo e runtime seguem sem prova. Próximo: mapear consumidores Xt
no Help Viewer antes de escolher o próximo adapter; nenhum uso da VM foi feito.
Q102 ainda precisa registrar r99/r100; I342r3 autorizada e incompleta.

## 2026-10-14 — I342 Xt `XtWindowOfObject` (r101)

O assembly confirma chamada direta de `_XtWindowedAncestor` (`Intrinsic.c`,
0x4b0cc, 60 bytes). Modelei a seleção: retorna o campo +0x5c do widget se sua
classe tem bit `0x04`; caso contrário percorre os pais e lê do ancestral encontrado.
Sem ancestral, o target chama aviso e depois tenta ler +0x5c do endereço nulo; o
adapter deixa essa leitura em hook para evitar UB host e não inventa o resultado
do Apollo. R101 passou 120/120 em C89 estrito e 120/120 em ASan/UBSan; os 119
fixtures herdados ficaram hash-idênticos. Recibo SHA-256
`c985c10e40e5743fe628259376f3794ba04c2484ac34e0c14d85d523b06c6ea6`; adapter
`eb27c6a6b3411e25666a34c4fcb3888dad4e44fe6e2d714d34b5bf34dbd11d9c`; teste
`67bb02c94bd095d9e12d35a1acd16dc4ea87df76a9ef8f15d5f95b8572ba1f88`; evidência
`c666554ccb1b3175b285d319336ff6fd3cd3608cbc8f65617f9b19225447bbca`. README e
SHA256SUMS passaram conferência dirigida. A trilha mostra chamada Xt interna e
alimenta o mapa de prioridade; ABI, mapping baixo e runtime Apollo permanecem
sem prova. Cobertura host em Xt: oito funções específicas em seis adapters;
714 anchors Xt r4 seguem no inventário. Próximo: rastrear mais chamadas da app e
outras bibliotecas. Q102 receberá r101 depois da releitura; sem VM/Telnet.

## 2026-10-14 — I342 Xt `XtParent` / `XtScreen` (r102)

Modelei dois accessors de `Intrinsic.c`: `XtParent` lê o word em `+0x08` e
`XtScreen` lê em `+0x54`. Fixture/adapter host passaram 121/121 C89 estrito e
121/121 ASan/UBSan; os 120 hashes anteriores foram estáveis. Recibo SHA-256
`08d7bc410883cc0e5c5e13a36dc31b1017e3fac6159800d256b043c976eb18f7`; modelo
`32c53ba4bb6ed22b58fa8577322a264e7319cecce5889c1c42534bc3091ae976`; teste
`24dbf05b8210ed6824883714ff42a26e30abd8bffe9167373bb2426d954fc340`; evidência
`ccf3adc6edfe359ce795d4cb8c26cdc9221d917c09917e44b12a08a6a916deda`. README/
SHA256SUMS conferidos. Cobertura Xt em adapter host: dez funções específicas em
sete módulos, sobre 714 anchors DST; Xt representa só uma de sete imagens de
dependência. ABI Apollo e VM continuam sem validação. Próximo: rastrear chamadas
relevantes em consumidores e outras bibliotecas. Q102 seq.289 tinha r101; r102
será enviado após releitura. Sem MAME/Telnet.

## 2026-10-14 — I342 Xt `XtIsRealized` (r103)

Modelei `XtIsRealized` (`Intrinsic.c`, `0x4b188`, 32 bytes), que chama
`XtWindowOfObject` e normaliza a janela não-zero para verdadeiro. R103 passou
122/122 em C89 estrito e 122/122 em ASan/UBSan, com os 121 fixtures herdados
hash-idênticos. Recibo SHA-256
`840a602969625b0cc7bf112f8bec0f8abbafc28a4c44796fc66381715166a695`; adapter
`960c7639ab065bbbdff83f74cff6da7ba23a293a07a30b9a79d6fdfd08ae21ca`; teste
`8851a2871f5a4c0a473a420370e81d18e888e8dff99281ea106957bb9ee86553`; evidência
`423dd5a250fa8fcd1fe3e6411761658d213d46324d5cb8d6b1f4d58a6ed29c43`. README/
SHA256SUMS verificados. A trilha agora cobre onze funções Xt, incluindo a cadeia
observada `XtIsRealized -> XtWindowOfObject -> _XtWindowedAncestor`; o resultado
de carregar de endereço baixo permanece no hook. Isso não cobre as 714 funções
Xt r4 ou outras seis bibliotecas; ABI Apollo/guest seguem sem validação. Próximo:
continuar callgraph e priorizar APIs do Help Viewer. Q102 seq.290 recebeu r102;
r103 será enviado após releitura. I342 incompleta, sem uso de MAME/Telnet.


## 2026-10-14 — Pedido de aumento do limite do ftpd (I361)

O usuário reiterou que deseja usar Telnet para aumentar a capacidade de conexões
simultâneas do ftpd. A leitura atual da prancheta confirma I361 com
`user.authorized=false`; Q362 pede autorização salva. Q370 ainda aguarda identificar
as duas sessões Telnet já conectadas e Q354 aguarda decisão sobre retomar a VM.
Nenhum Telnet foi usado e nenhum comando ou alteração foi feito no guest. Próximo:
aguardar respostas nos itens já abertos e só então avaliar o procedimento mínimo,
respeitando os limites de reinício/parada descritos em I361.

## 2026-10-14 — I342 Xt event loop (r104)

A trilha COFF confirma `XtMainLoop` como import externo do Help Viewer,
resolvido pelo inventário capturado para Xt r4. Modelei em adapter host
`XtMainLoop` e `XtAppMainLoop`: leitura do application context, buffer local de
96 bytes, serviço indireto de obtenção de evento e despacho repetido por
`XtDispatchEvent`. O fixture interrompe o laço infinito via `longjmp`, verifica
três iterações, contexto, bytes e reuso do buffer. R104 passou 123/123 C89 estrito
e 123/123 ASan/UBSan; os 122 fixtures herdados mantiveram os hashes. Recibo
`2e18472994e0d9f6e3d4cc5b3dc4bb9c5563e13dd9dd60bb602dff1bddb61f96`; evidência
`7f2512c7ee39411fb1634519da3ae21985e5d9899ec49ee288e681a14779b395`. Isto é
host-only: slot A5, ABI/layout Apollo e guest continuam sem validação. Cobertura
contabilizada: 42/42 anchors de NLSIO têm adapter host e 13/714 anchors Xt r4 têm
modelo/fixture host; as outras seis imagens de dependência, build/link/runtime
Apollo seguem pendentes. I361 continua sem autorização salva; Q354/Q370/Q377
sem resposta. Próximo: seguir APIs chamadas pelo fluxo do Help Viewer e avançar a
reconstrução host enquanto a liberação/estado da VM seguem pendentes.

## 2026-10-14 — I342 Xt despacho de eventos (r105)

Completei mais uma rotina chamada diretamente pelo laço r104: `XtDispatchEvent`
(Event.c, `0x4783a`, 116 bytes). O adapter modela leitura do display em evento
+0x0c, obtenção do contexto, profundidade aninhada +0xce, chamada de
`DecideToDispatch`, comparação assinada do nível sync +0xca, hook de sincronização
e os gates de processamento/flush na saída externa. O fixture faz despacho
recursivo e confere retorno, níveis e ordem dos callbacks. R105 passou 124/124 em
C89 estrito e 124/124 ASan/UBSan; os 123 fixtures herdados conservaram hashes.
Recibo SHA-256 `259f332e543af082db8516bad393dbe41d6871289ca7babfff12e70941d1d75c`;
adapter `0aace0046a240ef6f74ed9ea7c2864c143c2bee50586feb0a490c81985891604`;
fixture `10b190145128fc3fe564d9571e208878cb11271d301b3079dc73e2553a25c45a`;
evidência `fa82d4658a317d50765955e8bc421706bd08c1074d1ada99591acec9838b7515`.
`DecideToDispatch` ainda é hook; slots A5/ABI Apollo e runtime não foram provados.
Cobertura host contabilizada: NLSIO 42/42 e Xt r4 14/714 anchors. Faltam as seis
imagens de dependência restantes e build/link/runtime Apollo. Q102 recebeu r104
na seq.293; Q354, I361/Q362, Q370 e Q377 seguem sem resposta/autorização conforme
o estado salvo da prancheta. Próximo: seguir o callgraph de eventos e as APIs
chamadas pelo Help Viewer, depois voltar à validação Apollo quando for possível.

## 2026-10-14 — I342 Xt `ConvertTypeToMask` (r107)

`DecideToDispatch` consulta `ConvertTypeToMask` para mapear o tipo do evento.
Modelei os sete bits baixos como índice da tabela de 128 entradas e a leitura dos
words em +0xc8/+0xcc, stride 8. Fixture cobre tipo normal, bit alto ignorado e
índice 0x7f. R107 passou 126/126 em C89 estrito e 126/126 ASan/UBSan; os 125
hashes herdados ficaram iguais. Recibo SHA-256
`912ba53f566dfbd890b417da89d989c3b4fb872de862b857b00b2902a06a2a44`;
adapter `926c84f804f5cf866362904d007f316b1a833b8d657388b533e9da14f8dd9ad3`;
fixture `fc0f4cdd8687ad14cd5fdecd5ac87301d22c28254971df3406b1134cd3a23bd5`;
evidência `af9e97223be95dd583413cfb3422b639000ad1c5ece22698ce163737788b6781`.
Os 128 valores da tabela continuam injetados; não validei dados A5 Apollo.

Correção de contagem para notas r104–r106: os números 13/714, 14/714 e 15/714
contavam apenas os alvos recém-modelados naquele subgrupo e não o total Xt. Uma
varredura atual dos recibos JSON de Xt identifica 47 nomes únicos de anchors com
registro de evidência entre 711 anchors do `vuehelp.dst-functions.tsv`; isso
mede presença de evidência, não completude semântica nem ABI. NLSIO continua
42/42 anchors com adapter host. O restante das seis imagens de dependência e
build/link/runtime Apollo seguem abertos. Q102 recebeu r106 na seq.295; Q354 e
Q370 sem resposta, I361 sem autorização, Q377 aguardando coordenação. Próximo:
integrar `DecideToDispatch` com esses helpers e continuar o callgraph; Apollo só
retoma quando a sessão e os gates necessários estiverem resolvidos.

## 2026-10-14 — Rechecagem de disponibilidade Apollo para I342

Às 14:58 local, `pgrep -x mame` não encontrou processo MAME; `tap-mess-1000-0`
continuou DOWN/NO-CARRIER. `ss` mostrou duas conexões TCP estabelecidas de
`192.168.240.1` a `192.168.240.2:23`; não consultei o conteúdo nem interagi com
as sessões. A validação Apollo de I342 continua sem sessão acessível. Q354 segue
aguardando decisão sobre retomada da VM e Q370 sobre as duas sessões Telnet;
I361 permanece sem autorização. Nenhum comando guest ou mudança de VM/rede/ftpd.
Próximo: seguir a reconstrução host independente e aguardar resolução desses
itens antes de qualquer uso da VM.

## 2026-10-14 — I342 `DecideToDispatch` (r108)

Modelei a roteirização do `DecideToDispatch` a partir do pseudocódigo e assembly
Xt r4, compondo os adapters de `XtWindowToWidget` e `ConvertTypeToMask`. O
fixture percorre despacho direto, gate de grab + sensibilidade, roteamento de
popup, reconciliação, fallback spring-loaded e o caso sem widget. R108 passou
127/127 C89 estrito e 127/127 ASan/UBSan; os 126 fixtures herdados mantiveram
hashes. Recibo SHA-256
`8b9cbed453d1c7c1a6c8eb4dd5745044bf5d8e01c04b0835db72bab648b65e4e`;
adapter `4a375a23c5d6fb12fcbebbba3f522dd37d284ceeb7b23e234a83e6ae84c83a62`;
fixture `2690590b0a73fcab16205f279c2575b5e4948903269faa5b1d72fc62764cfc18`;
evidência `981f8ebaa4f8b97c008e8490f0f08b9327f90c6d8456e36641d95cd7e1201e74`.
O roteamento por display, `_XtOnGrabList`, `LookupSpringLoaded`, `DispatchEvent`
e serviços popup ainda são hooks, então o teste não comprova o dispatcher completo
nem o ABI Apollo. A varredura atual encontra 48 anchors Xt com registro de
evidência entre 711 nomes exportados; NLSIO tem 42/42 adapters host. Isso não é
percentual de conclusão. Seis imagens de dependência e build/link/runtime Apollo
continuam pendentes. Rechecagem às 15:04: MAME ausente, TAP DOWN/NO-CARRIER, duas
sessões Telnet estabelecidas sem interação. Q354/Q370 aguardam; I361 sem
autorização; Q377 aguarda coordenação. Q102 recebeu r107 na seq.296; r108 será
enviado. Próximo: aprofundar `DispatchEvent` e implementar helper/service calls
restantes antes de retestar o fluxo host.

Correção de protocolo: a mensagem r108 foi recebida no Q102 na sequência 298;
substitui a anotação acima de que ainda seria enviada. A próxima rotina no
callgraph é `DispatchEvent` (802 bytes), imediatamente chamada pelos ramos de
`DecideToDispatch`; seu pseudocódigo indica lista de ações, crescimento em blocos
de 100 e caminhos especiais de compressão de eventos, ainda sem adapter aqui.

## 2026-10-14 — I342 `DispatchEvent` (r109) e pedido de Telnet

Modelei `DispatchEvent` do Xt r4 (`Event.c`, 0x46fbc, 802 bytes): seleção e
ordem dos callbacks de tradução, crescimento em blocos de 100, flag de parada,
compressão de expose, filtros leave/motion e estado de foco. Os serviços A5 de
fila e `CompressExposures` seguem como hooks explícitos; registros do adapter são
semânticos host, não layouts Apollo. A suíte herdada mais o novo fixture passou
128/128 em C89 estrito e 128/128 ASan/UBSan; 127 hashes anteriores foram
conferidos estáveis antes/depois. Recibo
`host-suite-validation-20261014-r109.json` SHA-256
`e8746586914878e1bd1cb221385b23efe91361d784b45ddb8d0f076015959091`;
evidência `xtlib-DispatchEvent.evidence.json` SHA-256
`ffce5bd4904ec20ac7775aa35ffb7421630a442d956920a584f2acbe793b5de6`. README e
manifesto SHA256SUMS atualizados; os quatro arquivos de r109 conferidos.
Compilação/link/runtime Apollo continuam pendentes.

O pedido reiterado para aumentar conexões do ftpd foi reconhecido como I361
revisão 0, sem alterar a autorização salva (`false`). Q102 recebeu o estado na
sequência 299. Não usei Telnet nem alterei serviço/guest; Q362 ainda solicita a
autorização de I361 e Q370 aguarda resolver a propriedade das sessões Telnet
existentes. O novo pedido não supera os gates gravados na prancheta. Próximo:
seguir a cadeia host do Xt com fixtures estáveis; retomar o guest somente depois
de autorização salva e resolução da sessão.

Correção de validação r109: após atualizar a soma do README, a verificação global
`sha256sum -c SHA256SUMS` acusa quatro entradas fora dos artefatos r109:
`test_vuehelp_StartTopicsListBMS.c`, `vuehelp-StartTopicsListBMS.c`,
`vuehelp-StartTopicsListBMS.evidence.json` e `vuehelp-SizeIndexDialog.evidence.json`.
Não editei nem regenerei esses arquivos; o manifesto e os quatro artefatos r109
passam isoladamente. Q102 recebeu o avanço r109 na sequência 300.

## 2026-10-14 — I342 `XtAddExposureToRegion` (r110)

Modelei `XtAddExposureToRegion` (Xt r4 `Event.c`, 0x47aea, 78 bytes): apenas
os tipos 12/13 chamam o hook de união de regiões, recebendo quatro valores
brutos de 16 bits dos offsets +0x16/+0x1a/+0x1e/+0x22 e o ponteiro da região.
R110 passou 129/129 C89 estrito e 129/129 ASan/UBSan; os 128 fixtures herdados
ficaram hash-idênticos. Recibo SHA-256
`1d4715f787e12736b00ee2b95e3cc3141b06d85a607318f826fce7f15c7587d1`; evidência
SHA-256 `f79cd1c6a9fb1b24cc8968f4be1ba1057410f24f9ede753dd04db0f6b11ae5ee`.
Não inferi nomes de campos nem ABI Apollo; a operação de região é hook. Q102
recebeu r110 na sequência 301. Próximo host: rastrear `CompressExposures` e os
serviços XCheckIfEvent/XPutBackEvent usando seus próprios anchors antes de compor.
Build/link/runtime Apollo e I361 ftpd continuam pendentes dos gates da prancheta.

## 2026-10-14 — I342 `CheckExposureEvent` (r111)

Rastreei o predicado passado a `XCheckIfEvent` em `CompressExposures` e modelei
`CheckExposureEvent` (Xt r4 `Event.c`, 0x474ae, 76 bytes). Ele compara o tipo com
um dos dois valores recebidos; tipo diferente liga a flag mutável. Para tipo
compatível, a janela é comparada ao alvo, salvo o gate que recusa após tipo
anterior diferente. R111 passou 130/130 C89 estrito e 130/130 ASan/UBSan; 129
fixtures herdados ficaram hash-idênticos. Recibo SHA-256
`e2875672e98a7d25fc38656c10fe8e88d5ce75a2746d0dc3020a4eb388fccc8c`; evidência
SHA-256 `3bf8040c7de86e5d46641169d08deedb228efcac12847a37106f0ca6bca700bc`.
Sem integração Apollo ou declaração de structs/ABI. Próximo: mapear os anchors
X11 de `XCheckIfEvent` e `XPutBackEvent` antes de compor `CompressExposures`.

## 2026-10-14 — I342 X11 `XCheckIfEvent` (r112)

Modelei `XCheckIfEvent` da imagem X11 r4 (`XChkIfEv.c`, 0x41940, 212 bytes).
A rotina percorre os nós atuais com o predicado e closure recebidos, mantém o
último nó examinado entre as passagens, chama dois serviços indiretos após fila
esgotada nas duas primeiras fases e retorna falso após a terceira sem match. Ao
encontrar match, copia 96 bytes, retira o nó, coloca-o na lista livre e decrementa
o contador. R112 passou 131/131 C89 estrito e 131/131 ASan/UBSan; os 130 fixtures
herdados ficaram hash-idênticos. Recibo SHA-256
`b29cc3c622bec18358c565aec19c43ab3a48add7da7b9e1aaee3c6ca4b64fec1`; evidência
SHA-256 `f926056ae88eaf358862f0a136ca9fb323c45c684bb85988034a300afd4609e2`.
Os serviços e o ABI Apollo permanecem hooks/pendências. Próximo: modelar
`XPutBackEvent`, depois compor `CompressExposures` com os helpers já verificados.

## 2026-10-14 — I342 X11 `XPutBackEvent` (r113)

Modelei `XPutBackEvent` da imagem X11 r4 (`XPutBEvent.c`, 0x4ea7c, 118 bytes):
reusa a lista livre ou solicita 100 bytes ao hook alocador; alocação nula retorna
sem alterar fila; caso contrário copia 96 bytes do evento, encadeia o nó antes da
cabeça, atualiza cauda se necessário e incrementa a contagem. R113 passou 132/132
C89 estrito e 132/132 ASan/UBSan; os 131 fixtures herdados ficaram hash-idênticos.
Recibo SHA-256 `99e2efc500e404d904ef67f5333a065e41889f8bbe004b342bc85353a0940693`;
evidência SHA-256 `8ed232ed1eab892f93ec9f5463918205168922f7549d05f630fb935092962bd4`.
A fila e o nó host são semânticos, não ABI Apollo. Próximo: compor os helpers
`DispatchEvent`, `XtAddExposureToRegion`, `CheckExposureEvent`, `XCheckIfEvent` e
`XPutBackEvent` em `CompressExposures`, mantendo os serviços A5 ainda desconhecidos
como hooks. Build/link/runtime Apollo segue sem prova.

Correção do próximo helper: as notas r110/r112/r113 associaram prematuramente
`XPutBackEvent` à composição de `CompressExposures`. A inspeção dos quatro
argumentos no assembly identifica esse segundo serviço como `XIfEvent`; a API
`XPutBackEvent` r113 é independente neste caminho. A correção foi publicada no
Q102 seq.305 antes da continuação.

## 2026-10-14 — I342 X11 `XIfEvent` (r114)

Modelei `XIfEvent` (X11 r4 `XIfEvent.c`, 0x48948, 158 bytes): busca a partir da
cabeça ou do último nó examinado, chama o serviço A5 de espera sem match e repete
até achar evento; ao encontrar, copia 96 bytes, remove o nó, atualiza a fila livre
/head/tail e decrementa a contagem. O serviço continua hook não identificado.
R114 passou 133/133 C89 estrito e 133/133 ASan/UBSan; 132 fixtures herdados
mantiveram hashes. Recibo SHA-256
`2c427e67085a259568983c9110ff6e3e7aba774944de70608e6e94a60072036f`; evidência
SHA-256 `b4251f0a7db2cc535a255f2f0930d38824662c9e7526457296a6dda503baf45c`.
Próximo: modelar o controle de `CompressExposures` compondo `XCheckIfEvent`,
`XIfEvent`, `CheckExposureEvent` e `XtAddExposureToRegion`; deixar a emissão e
serviços desconhecidos como hooks explícitos.

## 2026-10-14 — I342 `CompressExposures` (r115)

Compus o controle de `CompressExposures` (Xt r4 `Event.c`, 0x472de, 338 bytes)
com os adapters já verificados de região, predicado, `XCheckIfEvent` e `XIfEvent`.
O evento de entrada é adicionado à região; contador +0x24 não zero retorna cedo,
sem emissão. Com contador zero, o adapter aplica os gates de classe/tela, prepara
o predicado e drena eventos correspondentes, esperando via `XIfEvent` se o contador
anterior indicar continuação. União de região, gate/tela, serviços de fila e envio
final continuam hooks explícitos. R115 passou 134/134 C89 estrito e 134/134
ASan/UBSan; os 133 fixtures herdados ficaram hash-idênticos. Recibo SHA-256
`dbfb9a9a7ee4d54a1aa3be22746752fbf3a73bcf35d3f0d1b7177699a2f9a7fc`; evidência
SHA-256 `2f9d312f8ab154964aa9bcc506c536031543afe83ad2638b64a3a50a724dcf89`.
Q102 atualizará este avanço. Próximo: reconstruir a rotina interna `SendExposureEvent`
e seus serviços antes de substituir o hook final; build/link/runtime Apollo segue aberto.

## 2026-10-14 — I342 `SendExposureEvent` (r116)

Modelei a rotina Xt r4 `SendExposureEvent` (`Event.c`, 0x47430, 126 bytes):
consulta o retângulo do hook consistente com `XClipBox`, escreve x/y sign-extended
e width/height zero-extended no evento, chama o callback da classe e encaminha
a região global e a região fornecida duas vezes ao hook final. A forma do último
serviço coincide com `XIntersectRegion` importado, mas o slot A5 não foi resolvido,
portanto mantenho-o genérico. R116 passou 135/135 C89 estrito e 135/135 ASan/UBSan;
134 fixtures herdados mantiveram hashes. Recibo SHA-256
`6aa2a164df0e83713380c1ac090050f6fd3f1f3a7cd253fd5955dec4c3bf6bee`; evidência
SHA-256 `ebce43523daec5cefc186bb6db1983bec1ffceb60fa0a990d51703ca93695b0c`.
Próximo: ligar o adapter de `SendExposureEvent` ao controle `CompressExposures`
por um thunk de callback, mantendo desconhecido o serviço final de região.

## 2026-10-14 — I342 composição `SendExposureEvent` no envio de exposição (r117)

O adapter host de `CompressExposures` agora encaminha o hook de emissão, por
thunk, ao adapter de `SendExposureEvent`. O fixture verifica a união inicial,
o ramo de contador zero, a atualização de x/y e largura/altura, o callback da
classe e a ordem dos hooks. A suíte selecionada passou 136/136 em C89 estrito
e 136/136 em ASan/UBSan; os 135 fixtures herdados permaneceram com hashes
idênticos. Recibo `analysis/reconstruction-c/host-suite-validation-20261014-r117.json`;
evidência `analysis/reconstruction-c/xtlib-CompressExposuresSendExposure.evidence.json`.
O serviço final de três regiões permanece não identificado; ABI, X11 real,
build/link e runtime Apollo continuam sem prova. Q102 lido no seq.308 antes do
envio deste resultado. I342r3 segue autorizada e parcial. Próximo: identificar
as rotinas de região e resolver os gates de sessão Apollo; não acessar Telnet nem
alterar o ftpd sem autorização específica salva para o item correspondente.

## 2026-10-14 — I342 X11 r4 `XClipBox` e resolução dos slots Xt (r118)

Reconstruí `XClipBox` (`x11lib.r4` `XRegion.c`, 0x5137e, 58 bytes): copia a
origem assinada e calcula largura/altura por subtração word de 16 bits, com
resultado armazenado como unsigned. O fixture cobre extremos dos endpoints.
A suíte passou 137/137 C89 estrito e 137/137 ASan/UBSan; 136 fixtures herdados
permaneceram hash-idênticos. Recibo `analysis/reconstruction-c/host-suite-validation-20261014-r118.json`;
evidências `analysis/reconstruction-c/x11lib-XClipBox.evidence.json` e
`analysis/reconstruction-c/xtlib-RegionImportSlots.evidence.json`.
A associação dos slots Xt agora é sustentada pelos imports `XUnionRectWithRegion`,
`XClipBox`, `XIntersectRegion` e pelas aridades/formas dos argumentos em três
callsites. Como `.text` não preserva relocation, descrevo isso como resolução
estática callsite/import, não como registro de relocation do loader. A nota r116
que dizia slot não provado foi refinada por esta evidência posterior. ABI/build/
link/runtime Apollo continuam sem prova. Q102 estava no seq.309 antes do envio.
Próximo: reconstruir `XIntersectRegion` e dependências internas da imagem X11;
I342r3 permanece autorizada/running. Q354, Q370 e Q377 aguardam resposta; I361
continua sem autorização salva. Sem uso de Telnet/VM e sem alteração de ftpd.

## 2026-10-14 — I342 X11 r4 `XIntersectRegion` e `miSetExtents` (r119)

Modelei o controle de `XIntersectRegion` e reconstruí `miSetExtents`. Limites
assinados com interseção estrita; regiões vazias ou bordas em contato limpam a
contagem de destino; caminho sobreposto encaminha os seis argumentos vistos no
assembly ao hook `miRegionOp`. O helper atualiza os extents vazios ou varre os
retângulos não vazios. A suíte passou 138/138 C89 estrito e 138/138 ASan/UBSan;
os 137 fixtures herdados mantiveram hashes. Recibo
`analysis/reconstruction-c/host-suite-validation-20261014-r119.json`; evidência
`analysis/reconstruction-c/x11lib-XIntersectRegion.evidence.json`. `miRegionOp`
(872 bytes), suas alocações e o contexto A5 seguem pendentes; este adapter não
reproduz ainda a operação real dos retângulos intersectados. Q102 foi lido no
seq.310 antes do envio. I342r3 continua autorizada/running. Próximo: reconstruir
`miRegionOp` e helpers, sem acessar VM/Telnet enquanto sessões/gates permanecem
sem resolução; I361 segue não autorizada.

## 2026-10-14 — correção do callback `miIntersectO` em I342 (r120)

Revisão do call contract de `miRegionOp` mostrou que a leitura r119 estava
incorreta: A5-0xc0 é o quarto argumento, callback de operação por sobreposição,
não um contexto. Os argumentos 5 e 6 são callbacks nulos. A assinatura e o fluxo
apontam para `miIntersectO` (XRegion.c, 0x51766) no caminho de interseção; o
valor efetivo da tabela A5 ainda não foi observado diretamente. Corrigi o adapter
e fixture para transmitir um ponteiro de função. Suíte: 138/138 C89 estrito e
138/138 ASan/UBSan; 137 fixtures herdados estáveis. R120 substitui a interpretação
r119; recibo `analysis/reconstruction-c/host-suite-validation-20261014-r120.json`,
evidência `analysis/reconstruction-c/x11lib-XIntersectRegion.evidence.json`.
Próximo: reconstruir o callback `miIntersectO` e depois o sweep `miRegionOp`;
sem build/link/runtime Apollo até a sessão e os gates Q354/Q370 serem resolvidos.

## 2026-10-14 — I342 X11 r4 `miIntersectO` (r121)

Reconstruí o callback por banda `miIntersectO` e integrei-o ao fluxo host de
`XIntersectRegion`: calcula max(x1)/min(x2), emite overlap de largura positiva,
avança intervalos pelo menor x2, grava y1/y2 do band e segue a condição de
crescimento/realloc observada. O fixture cobre duas interseções em uma banda,
ambos os crescimentos (16 e 32 bytes), caso vazio e falha de realocação. Suíte
138/138 C89 estrito e 138/138 ASan/UBSan; 137 fixtures herdados estáveis. Recibo
`analysis/reconstruction-c/host-suite-validation-20261014-r121.json`; evidência
`analysis/reconstruction-c/x11lib-miIntersectO.evidence.json`. `miRegionOp` ainda
é hook; o allocator A5-0xac é adapter e não tem valor de runtime provado. Q102
foi relido em seq.312 antes do próximo envio. Próximo: implementar o sweep de
`miRegionOp` e `miCoalesce`; VM/build Apollo continua condicionada aos gates de
sessão Q354/Q370, sem reinício ou Telnet.

## 2026-10-14 — I342 X11 r4 `miRegionOp` interseção (r122)

O adaptador host agora executa a alocação inicial, o sweep das bandas verticais,
a chamada de `miIntersectO` para a sobreposição, ajuste de capacidade e a
coalescência dos casos adjacentes cobertos. O escopo é só interseção:
`XIntersectRegion` passa callbacks left/right nulos. A comparação de `miCoalesce`
mostrou que o host ainda simplifica o índice/avanço do original; r122 registra essa
limitação e não afirma equivalência completa. Suíte: 138/138 C89 estrito e
138/138 ASan/UBSan, 137 fixtures herdados com hashes estáveis. Recibo
`analysis/reconstruction-c/host-suite-validation-20261014-r122.json`; evidência
`analysis/reconstruction-c/x11lib-XIntersectRegion.evidence.json`. Sem ABI/build/
link/runtime Apollo. Próximo: completar e testar a semântica de `miCoalesce`,
examinar alocadores e continuar as dependências X11 do Help Viewer. I342 permanece
autorizada/running. Q102 será relido antes do retorno. Nenhuma ação Telnet/ftpd.

## 2026-10-14 — I342 `miCoalesce` no caminho de interseção (r123)

Refinei o índice da coalescência em X11 r4: após uma callback `miIntersectO`,
o helper leva o início da faixa anterior, compara contagem, continuidade y e
intervalos x, estende y2/remove duplicatas ao mesclar e devolve o índice para a
próxima chamada. O fixture cobre mescla, recusa por x divergente e nova mescla
após essa recusa. O escopo continua exatamente o call shape de `XIntersectRegion`,
com callbacks left/right nulos; não é a reconstrução geral de união/subtração.
Suíte: 138/138 C89 estrito e 138/138 ASan/UBSan; 137 fixtures estáveis. Recibo
`analysis/reconstruction-c/host-suite-validation-20261014-r123.json`, evidência
`analysis/reconstruction-c/x11lib-XIntersectRegion.evidence.json`; manifesto
SHA256SUMS integral validado. Próximo: mapear a próxima dependência X11 do Help
Viewer e seguir a reconstrução. Ainda faltam ABI/build/link/runtime Apollo; as
sessões Telnet continuam sem autorização para uso, portanto nada foi enviado.
I342 segue autorizada/running; I361 continua não autorizada.

## 2026-10-14 — I342 X11 r4 `XParseGeometry` (r124)

A tabela de imports COFF confirma que `vuehelp` importa `XParseGeometry` de
`x11lib_r4`. Reconstruí `ReadInteger` (0x4d534, 104 bytes) e `XParseGeometry`
(0x4d59c, 414 bytes), incluindo máscaras de width/height/x/y/sinal, dimensões e
offsets parciais, rejeição de string incompleta sem escrever saídas, e wrap de
32 bits no adapter host. R124 passou 139/139 C89 estrito e 139/139 ASan/UBSan;
138 fixtures anteriores permaneceram com hashes idênticos. Recibo
`analysis/reconstruction-c/host-suite-validation-20261014-r124.json`;
evidência `analysis/reconstruction-c/x11lib-XParseGeometry.evidence.json`.
Manifesto SHA256SUMS integral validado. Isso ainda não prova ABI, build, link ou
execução Apollo. Próximo: seguir as APIs X11 importadas pelo Help Viewer e suas
dependências; estágio host cumulativo continua separado da validação guest.
I342 permanece autorizada/running. Nenhum Telnet/ftpd foi tocado.

## 2026-10-14 — imports X11 diretos do Help Viewer (r125–r126)

R125 cobre `XSetClipRectangles`/`_XSetClipRectangles`: pedido opcode 0x3b, tamanho,
GC e dirty flags, reserva do header, append ou envio externo e flush de extensão;
flush/data/send continuam hooks sem identidades A5 provadas. R126 cobre
`XDefaultScreen` e `XScreenOfDisplay`, com stride Screen observado de 0x50
(80 bytes), sem declarar ABI Display/Screen completo. São APIs encontradas como
imports de `vuehelp` em `import-resolution.tsv`. Suítes cumulativas: 140/140 e
141/141 em C89 estrito/ASan/UBSan; 139 e 140 fixtures herdados estáveis. Recibos
r125/r126 e evidências por função no projeto help_viewr_rev; manifesto será
conferido depois do próximo lote. I342 continua autorizada/running, sem prova de
build/link/runtime Apollo. Nenhuma interação com Telnet/ftpd.

## 2026-10-14 — I342 X11 r4 `XGetFontProperty` (r127)

Import direto confirmado: `vuehelp` usa `XGetFontProperty` de x11lib_r4.
Reconstruí a busca linear pelo nome da propriedade no vetor da fonte, que retorna
o primeiro valor coincidente e preserva o ponteiro de saída em caso de ausência.
Teste cobre primeira correspondência, não encontrado e vetor vazio. R127 passou
142/142 C89 estrito e ASan/UBSan, 141 fixtures herdados hash-idênticos; manifesto
SHA256SUMS integral validado. Recibo
`analysis/reconstruction-c/host-suite-validation-20261014-r127.json` e evidência
`analysis/reconstruction-c/x11lib-XGetFontProperty.evidence.json`. O layout
Font/FontProp não foi declarado como ABI Apollo. I342 segue autorizada/running,
sem build/link/runtime guest. Não houve interação com Telnet/ftpd.

## 2026-10-14 — I342 X11 r4 `XGetSizeHints` (r129)

`XGetNormalHints` é importada diretamente por vuehelp e encaminha para
`XGetSizeHints`. Reconstruí essa helper e `XGetZoomHints`: query do property
com offset 0/length 15/type 41, validação de type/formato 32/ao menos 15 items,
cópia do flags low-byte e 14 palavras restantes, liberação nos ramos observados,
e atoms 40/42 nos wrappers. A falha do query preserva o ramo original sem free.
Suíte 144/144 C89 estrito e 144/144 ASan/UBSan, 143 fixtures herdados estáveis;
manifesto SHA256SUMS integral validado. Recibo
`analysis/reconstruction-c/host-suite-validation-20261014-r129.json`, evidência
`analysis/reconstruction-c/x11lib-XGetSizeHints.evidence.json`. Query/free e
layout XSizeHints continuam hooks/views, sem ABI Apollo. I342 segue em execução;
nenhum acesso Telnet/ftpd.

## 2026-10-14 — I342 X11 r4 `XSetSizeHints` (r130)

`XSetNormalHints` aparece como import direto do Help Viewer e delega para
`XSetSizeHints`. O adapter copia flags do low-byte e os outros 14 words de 32
bits para a chamada change-property, type 41, format 32, mode Replace; os wrappers
Normal/Zoom encaminham atoms 40/42. O serviço A5 permanece hook e sem identidade
em runtime. R130 passou 145/145 C89 estrito e 145/145 ASan/UBSan, 144 fixtures
herdados estáveis; SHA256SUMS integral passou. Recibo
`analysis/reconstruction-c/host-suite-validation-20261014-r130.json`, evidência
`analysis/reconstruction-c/x11lib-XSetSizeHints.evidence.json`. Sem ABI/build/
link/runtime Apollo. I342 continua autorizada/running.

## 2026-10-14 — I342 X11 r4 `XMapWindow`/`XRaiseWindow` (r131)

Ambas são imports diretos de vuehelp. Reconstruí o request Map (tipo 8, 2
words) e Raise (tipo 12, 4 words, mask 0x40), representando buffer e flush como
hooks host. Suíte 146/146 C89 estrito e ASan/UBSan; 145 fixtures herdados
estáveis; SHA256SUMS integral validado. Recibo/evidência em
`analysis/reconstruction-c`. ABI Display, padding/endian, slots A5 e runtime
Apollo continuam sem prova; faltam APIs/dependências e build/link/run no guest.
I342 segue autorizada/running. I361 `ftpd` continua `user.authorized=false`;
nenhum Telnet ou comando guest executado.

### Revisão da evidência r131 (buffer de requests)

A revisão técnica identificou omissão de efeitos do buffer em `XMapWindow` e
`XRaiseWindow`. O modelo foi aprofundado: gravação big-endian, `last_request`,
avanço do cursor, contagem, callback de crescimento se o espaço faltar e flush
condicional. Testes cobrem request bytes, campos, counters, buffer suficiente e
crescimento. Suíte refeita sobre fixtures únicos: 147/147 C89 estrito e
147/147 ASan/UBSan; 146 herdados estáveis. Isso reforça semântica, mas não prova
ABI/slots A5 Apollo. A primeira saída 148/148 foi descartada por duplicação na
lista; só 147/147 é válida.

## 2026-10-14 — I342 X11 r4 `XDeleteProperty` (r133)

Import direto do Help Viewer. Request tipo 19/3 words; dois argumentos de 32
bits, gravação big-endian, buffer/last_request/cursor/contador e expansão por
hook. Testes passaram 147/147 C89 estrito e ASan/UBSan, 146 fixtures herdados
estáveis; SHA256SUMS será validado após adicionar os recibos. ABI Display e slot
A5 sem prova, sem build/link/runtime Apollo. I342 continua autorizada/running.

## 2026-10-14 — I342 X11 r4 `XClearArea` (r134)

Import direto de vuehelp. Pedido tipo 61/4 words, exposures, window e quatro
campos de 16 bits; buffer big-endian, cursor/contador, crescimento e flush
opcional. Suíte passou 148/148 C89 estrito e ASan/UBSan, 147 fixtures herdados
estáveis; recibo/evidência em `analysis/reconstruction-c`. ABI Display/A5 e
runtime Apollo continuam sem prova; compile/link/run guest pendentes. I342 ativa.

## 2026-10-14 — I342 X11 r4 `XCopyArea` (r135)

Import direto de vuehelp. Pedido tipo 62/7 words; ordem observada source,
destination, ID GC, src x/y, dst x/y e width/height. Inclui GC validation gate,
expansão de buffer, cursor, contador e flush opcional. Suíte 149/149 C89 estrito
e ASan/UBSan, 148 herdados estáveis; evidência/recibo em
`analysis/reconstruction-c`. Hooks/ABI Display e runtime Apollo não provados;
I342 continua ativa.

## 2026-10-14 — I342 X11 r4 `XFillRectangle` (r136)

Import direto de vuehelp. Reconstruída criação e coalescência condicional dos
retângulos do mesmo drawable/GC, gated por capacidade e max request size;
validação GC, crescimento, campos geométricos e flush. Suíte 150/150 C89
estrito e ASan/UBSan, 149 herdados estáveis; recibo/evidência em
`analysis/reconstruction-c`. Threshold/ABI/A5 continuam views host e sem prova
Apollo; etapa I342 segue ativa.

## 2026-10-14 — I342 X11 r4 `XDrawString` (r137)

Import direto do Help Viewer. Reconstruído PolyText8 com chunks de até 254
bytes, prefixos/delta, length e padding em 4 bytes, no-op para tamanho <=0,
validação condicional GC, expansão e flush. Suíte 151/151 C89 estrito e
ASan/UBSan, 150 herdados estáveis; evidência/recibo em
`analysis/reconstruction-c`. ABI/A5/runtime Apollo permanecem sem prova; etapa
I342 continua ativa.

## 2026-10-14 — I342 X11 r4 `XGetAtomName` (r138)

Import direto de vuehelp. Reconstruídos request tipo 17/2 words, reply
síncrono, allocate length+1, read e NUL; em OOM, eat com alinhamento de 4 bytes;
flush nos ramos observados. Suíte 152/152 C89 estrito e ASan/UBSan, 151
fixtures herdados estáveis. Recibo/evidência em `analysis/reconstruction-c`.
Reply ABI, hooks A5 e runtime Apollo pendentes; I342 ativa.

## 2026-10-14 — I342 X11 r4 `XChangeProperty` (r139)

Import direto de vuehelp. Requests tipo 18/6 words; formatos 8/16/32, contagem
e padding próprios, teto de 65535 words, cópia buffered ou envio separado se
faltar espaço; formato inválido/overflow sem payload. Suíte 153/153 C89 estrito
e ASan/UBSan, 152 herdados estáveis; recibo/evidência em
`analysis/reconstruction-c`. Dados opacos e slots/ABI A5 sem runtime Apollo;
I342 permanece ativa.

## 2026-10-14 — I342 X11 r4 `XSetWMHints` (r140)

Import direto de vuehelp. Converte nove campos para WM_HINTS; flag `input`
canônica para 1 somente quando valor original é 1. Property/type 35, format
32, Replace e 9 elementos. Suíte 154/154 C89 estrito e ASan/UBSan, 153 herdados
estáveis; recibo/evidência em `analysis/reconstruction-c`. Layout/slot A5 e
runtime Apollo sem prova; I342 ativa.

## 2026-10-14 — I342 X11 r4 `XGetWMHints` (r141)

Import direto de vuehelp. Query property 35/length9; valida type/formato/count,
aloca resultado 36 bytes semântico, normaliza flag e copia campos, zera o nono
quando ausente. Query error mantém ramo sem free; validação/OOM/sucesso liberam
conforme evidência. Suíte 155/155 C89 estrito e ASan/UBSan, 154 herdados
estáveis. Recibo/evidência em `analysis/reconstruction-c`; ABI/A5/runtime sem
prova e I342 continua ativa.

## 2026-10-14 — I342 X11 r4 `XGetWindowProperty` (r142)

Import direto. Request 20/6 words; reply failure=status 1; zero itens=sucesso
sem payload; formatos 8/16 usam reader byte e 32 usa reader distinto, NUL ao
final. Formato inválido emite BadValue/eat0/status11; OOM eat(payload)/11.
Suíte 156/156 C89 estrito e ASan/UBSan, 155 herdados estáveis. Recibo/evidência
em `analysis/reconstruction-c`; reply ABI, leituras/A5 e execução Apollo não
provados; I342 ativa.

## 2026-10-14 — I342 X11 r4 `XTranslateCoordinates` (r143)

Import direto de vuehelp. Request tipo 40/4 words; falha do reply preserva as
saídas; sucesso escreve child/x/y e retorna `same_screen` separadamente.
Suíte 157/157 C89 estrito e ASan/UBSan, 156 fixtures herdados. Recibo e
evidência em `analysis/reconstruction-c`; layout de reply, ABI/A5 e runtime
Apollo sem prova; I342 continua ativa.

## 2026-10-14 — I342 X11 r4 `XTextWidth` (r144)

Import direto de vuehelp, função 0x547de/348 bytes. Reconstituí seleção de
métrica default 1D/2D, métricas por byte, fallback de métrica vazia e soma de
larguras; endereço, pseudocódigo, assembly e bytes da imagem COFF foram
cruzados. Suíte 158/158 C89 estrito e ASan/UBSan, 157 fixtures herdados
estáveis. Recibo/evidência em `analysis/reconstruction-c`; layout ABI, overflow
e runtime Apollo não comprovados; I342 continua ativa.

## 2026-10-14 — I342 X11 r4 `XDrawImageString` (r145)

Import direto de vuehelp; função 0x49a20/400 bytes. Reconstruí ImageText8
opcode76, blocos até 255 bytes, tamanho/padding, buffer ou envio separado,
consulta/medida/liberação de fonte entre blocos e flush de GC/display. Bytes da
imagem COFF e fontes Ghidra foram cruzados. Suíte 159/159 C89 estrito e
ASan/UBSan, 158 fixtures herdados estáveis. Recibo/evidência em
`analysis/reconstruction-c`; ABI/hooks e runtime Apollo não provados; I342
continua ativa.
