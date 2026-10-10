# DomainOS — ajustes da avaliação funcional de 9 de outubro de 2026

Este registro complementa a validação das dicas e a revisão de resiliência.
Os testes usam componentes de produção e perfis privados; seu resultado não
substitui a avaliação da sessão do usuário. O backup aprovado permanece congelado.

## Prancheta respondida pelo mantenedor

O JSON salvo pelo mantenedor em `/tmp/irix-domainos-checklist-20261009-uid1000.json`
registra 18 respostas às 14:07:34, no fuso UTC−4. Dezesseis comportamentos foram
confirmados: flutuação, roda, seleção de grupos e de uma janela, três estados do
duplo clique, ativação pelo Pager, fechamento dos quadros, dicas e alternância
de Plasma Style. A lista de uma janela conserva as opções atuais de selecionar
ou ativar. O JSON pessoal não integra a distribuição.
Uma cópia da primeira resposta permanece em
`/tmp/irix-domainos-checklist-primeira-resposta-20261009-uid1000.json`, permitindo
atualizar a prancheta sem perder as falhas relatadas nesta avaliação.

Duas falhas ficaram confirmadas: dicas e outros quadros ainda azuis fora do
esquema selecionado; miniaturas sem cartão utilizável enquanto a imagem não
chega, com conteúdo residual ao retornar às dicas textuais. A correção e sua
validação são registradas separadamente, sem converter estas respostas em sucesso.

## Clique do meio e identidade das tarefas

A propriedade nativa `CanLaunchNewInstance` pode ser falsa quando o aplicativo
possui uma Desktop Action para nova janela. Ela determina a apresentação do
comando genérico no menu. O gerenciador de tarefas do KDE ainda solicita
`requestNewInstance` no gesto do botão do meio. O DomainOS passa a seguir esse
comportamento, após conferir novamente a tarefa e sua identidade/PID.
As referências primárias são o
[helper do TaskManager](https://raw.githubusercontent.com/KDE/plasma-workspace/master/libtaskmanager/tasktools.cpp)
e o [encaminhamento de grupos](https://raw.githubusercontent.com/KDE/plasma-workspace/master/libtaskmanager/taskgroupingproxymodel.cpp),
conferidos também com `Task.qml` do gerenciador de tarefas instalado.

O ensaio de interação passou 6/6 verificações: grupo e janela individual,
preferência desabilitada, seleção preservada e identidade antiga recusada. O
ensaio nativo X11 passou 37/37: TaskManager::TasksModel real, Desktop Entries
privadas com `Actions=new-empty-window` e `CanLaunchNewInstance=false`, clique
físico no grupo e na janela individual. Cada clique criou exatamente uma nova
janela/PID; a seleção e as janelas existentes permaneceram intactas. Os cinco
clientes próprios e o KWin privado foram encerrados. Evidência:
`/tmp/irix-domainos-middle-native-r3-20261009/RESULTADO.json` e três PNGs na mesma
pasta. O ensaio não executa o VS Code do usuário nem comprova seu comportamento
de instância única; tampouco cobre este gesto em Wayland.

## Preferências da própria instância

O item permanente da gaveta aciona `domainos-configure-panel`, pertencente ao
painel. O comando genérico `configure` continua disponível para a bandeja
nativa incorporada. A janela própria apresenta as categorias DomainOS.

O ensaio físico verificou abertura, edição de Iconbox, Aplicar, segunda edição
sem salvar, Cancelar/Descartar, reabertura e reinício do host privado. A chave
escolhida foi salva e chegou ao TasksModel; a segunda instância permaneceu
intacta, assim como quatro arquivos reais de configuração protegidos.
Evidência: `/tmp/irix-domainos-pref-ui-apply-discard-restart-isolacao-r5/RESULTADO.json`.
Passaram 26/27 critérios. O critério de ausência total de diagnósticos falhou por
erros `Success`/`None` do PromptDialog Kirigami instalado. Não houve erro QML do
DomainOS. O relatório conserva esse limite e o código de saída 2.

## Tamanho do seletor e limites de falha

A abertura do seletor agora deixa o Qt calcular a altura natural antes de
exibir a superfície. O ensaio nativo verificou 165/165 critérios, incluindo
listas de 3, 15 e 16 membros, tamanho no sinal de abertura, alteração ao vivo e
posição real da janela dentro da tela. Evidência:
`/tmp/irix-domainos-group-natural-height-position-r4/RESULTADO.json`.
As tentativas anteriores que falharam continuam registradas.

Comandos e operações de janelas limpam o pedido pertencente à instância antes
de interpretar seu resultado. Exceções de preparação, conexão e desconexão
produzem estado conhecido ou indeterminado, sem repetir uma ação que possa já
ter sido enviada. Resultados estranhos, duplicados e de outra instância são
ignorados. Foram aprovados 7 testes QML de falha e recuperação, 12 testes do
helper e 23 critérios com DataSource nativo em sessão privada. Evidência nativa:
`/tmp/irix-domainos-command-job-regression-r2-20261009/RESULTADO.json`.
Esses tratamentos não permitem capturar um travamento do processo inteiro.
O observador do lsi permanece somente de leitura e não reinicia a sessão.

## Entrega

O conteúdo da dica possui um item estável por célula; somente o proprietário
da janela nativa visível apresenta seu conteúdo. Preparação e visibilidade
determinam a carga, sem depender de um hover antigo. Os cartões têm geometria,
título e ação antes de existir imagem. Retornar ao modo textual libera os
cartões e os provedores.

O Plasma Style DomainOS deixa de distribuir um arquivo `colors` que fixava
azul. Os relevos opacos de dicas e diálogos usam papéis ColorScheme; o esquema
DomainOS SR10.4 continua disponível como opção separada. A árvore Classic e a
composição aprovada do painel permanecem intactas.

O ensaio nativo passou **59/59**, com três janelas próprias, TasksModel e
plasmawindowed instalados: cartões sem imagem medidos e clicáveis; 12 trocas de
proprietário, 8 trocas de modo, ausência de conteúdo residual; moldura cinza no
esquema Irixium privado, zero diagnósticos QML e quatro configurações reais
preservadas. Evidência:
`/tmp/irix-domainos-thumbnail-lifecycle-native-r7/RESULTADO.json`, com
`EMPTY-CARDS.png`, `IRIXIUM-HINT-FRAME.png` e `RESTORED-TITLES.png`.
O teste retira deliberadamente IDs dos provedores para representar imagem
ausente. Não demonstra uma nova captura de pixels da janela; os ensaios de
captura anteriores têm escopo próprio. As tentativas falhas permanecem
registradas: compilação/filter do fixture e posição do cursor que diferia do
evento QTest. O teste final usa a posição global real do cursor e a política
nativa de hover, sem acrescentar temporizador à produção.

Os **9/9** testes de pacote passaram. A extração e instalação privadas
confirmaram os quatro destinos, retirada do `colors` antigo, reinstalação sem
novo backup, verificação de restauração sem mudança e restauração exata dos
bytes/modos. Quatro configurações permaneceram iguais após cada um dos cinco
comandos. Evidências em
`/tmp/irix-domainos-package-tests-20261009-ajustes-r1/RESULTADO.json` e
`EXTRACAO-INSTALACAO-RESTAURACAO.json` na mesma pasta. Arquivos removidos do
checkout são excluídos pelo inventário Git; suporte obrigatório ausente continua
bloqueando o pacote. Caches e arquivos privados continuam fora do escopo.

A atualização foi aplicada somente em lsi, com substituição transacional dos
recursos e recarga de seu Plasma. Mudaram o applet e o Plasma Style; os outros
dois destinos já correspondiam às fontes. IDs e preferências General de todos
os widgets do painel permaneceram iguais. Os hashes de `kdeglobals`, `kwinrc`,
`plasmarc`, Kvantum e configurações GTK 3/4 também permaneceram iguais.
Relatório: `/tmp/irix-domainos-ajustes-lsi-20261009.json`. Backup recuperável:
`~/.local/state/irixium-domainos/backups/794c4bab44fc41d5bf71cf03bd472b11/receipt.json`.
O processo recarregado respondeu à sonda; seu início não apresentou diagnóstico
de erro identificado como DomainOS. Isso não é uma garantia sobre falhas futuras.

A primeira tentativa de entrega parou na leitura do snapshot, antes de qualquer
instalação: ordenar a sequência nativa `configKeys` tentou modificar uma
propriedade somente de leitura. A enumeração foi corrigida, mantendo comparação
independente da ordem. Registro preservado:
`/tmp/irix-domainos-ajustes-lsi-snapshot-falha-r1-20261009.json`.

A confirmação visual destas correções na sessão Wayland do mantenedor continua
separada das provas privadas. A validação final em p001532 fica para o fim da
etapa, conforme solicitado. Não foi acionado bloqueio real da tela para testar
o cadeado, nem alterado outro perfil. Os arquivos anteriores distribuídos e o
backup aprovado em Downloads continuam congelados.
