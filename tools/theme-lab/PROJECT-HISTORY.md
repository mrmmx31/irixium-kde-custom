# I119 — recuperação do projeto

Histórico do projeto separado de editor-journal.json e respostas da prancheta.
Snapshots canônicos usam a mesma validação/serialização do projeto, sem o horário
exported_at. Preservam números, estados, peças, layout, famílias, papéis KDE,
notas e proveniência. Não salvam widgets nem estado interno dos processos.

Undo/Redo altera a proposta; Aplicar permanece a ação que muda a cena nativa.
O ponto salvo de comparação é independente do cursor do histórico. Restaurar o
ponto e resetar a peça são novas alterações recuperáveis. Reset remove só os
overrides esparsos da peça selecionada, retomando a herança da família.

Até128 snapshots, com limite explícito. Ao criar alteração depois de Undo,
substitui-se só o ramo Redo; navegar ou salvar sem alteração não duplica entradas.
A persistência deve escrever candidato validado antes de substituir o estado
em memória, com lock, escrita atômica e proteção de concorrência. Erro conserva
proposta, histórico anterior e texto; nunca descarta silenciosamente.

I124 já registra o pedido posterior de salvar progresso em arquivo. Sua
persistência integra esta recuperação, sem misturar respostas da prancheta.
Etapas: modelo/codec; armazenamento e falhas; controlador; interface e atalhos
sem interceptar Undo dos textos; prova nativa; entrega coordenada.

## Armazenamento implementado (ainda sem integração ao controlador)

`project_history_store.h` e `src/persistence/project_history_store.c` usam
arquivo separado, UTF-8, limite de 32 MiB, arquivo regular e permissão 0600
na gravação nova. Recuperam todas as entradas, cursor e ponto de comparação.
O lock exclusivo não bloqueante é compartilhado pelos escritores que usam
esta API. Antes de substituir o arquivo, a revisão lida é comparada sob lock;
uma instância desatualizada recebe conflito, sem substituir o estado vigente.

A gravação valida o candidato, escreve temporário no mesmo diretório, faz
fsync e rename atômico. Fsync do diretório confirma a persistência do nome.
O retorno distingue erro anterior ao commit (-1), sucesso durável (0) e
commit com durabilidade do diretório incerta (1). O controlador deve adotar
o candidato também no retorno 1 e mostrar o aviso, evitando divergência
entre memória e arquivo. O arquivo corrompido não é substituído silenciosamente.

Limites: escritores externos que ignoram o lock não são coordenados;
leitura/gravação síncronas ainda precisam ser integradas ao controlador sem
bloquear a interface. Não houve ensaio de queda de energia real nem de falha
de fsync do diretório. Históricos maiores exigirão outra política explícita.
Não altera JSON da interface, recursos de locale ou respostas da prancheta.

## Sessão transacional

`src/controller/project_session.c` possui o histórico, caminho e revisão CAS.
Prepara uma cópia candidata e aplica push/Undo/Redo/ponto/restore/reset nela;
somente adota a cópia após commit. Falha mantém modelo, cursor e ponto anteriores.
A API ainda não está ligada aos callbacks do controlador Motif. Próximo: migrar
as mutações de leitura, seleção, importação, pipeta e eventos antes de atualizar
a cena; a gravação derivada de working.json não será a fonte de recuperação.

## Integração Motif em andamento

O controlador usa a sessão antes de adotar números, seleção, estados, layout,
importação e amostras da pipeta. Digitação contínua agrupa alterações após
300 ms; o journal textual continua independente. Ações explícitas capturam
imediatamente os campos válidos antes de atuar. Dados inválidos mantêm o texto
para correção e impedem aplicar uma proposta inválida.

A faixa própria oferece Desfazer projeto, Refazer projeto, Guardar ponto,
Voltar ao ponto e Resetar peça. Ctrl+Alt+Z, Ctrl+Alt+Y e Ctrl+Alt+Shift+Z nos
widgets Motif da janela principal acionam o histórico do projeto. Ctrl+Z/Y e
Ctrl+Shift+Z conservam os comandos do editor textual. Os atalhos do projeto
não são instalados dentro da aplicação GTK acoplada ou dos diálogos criados
posteriormente. Nesses casos use os botões principais.

Undo/Redo, retorno ao ponto e reset da peça atualizam a proposta/código;
Atualizar aplica à cena. O comando antigo Restaurar família permanece próprio,
agora recuperável por Undo. O histórico é fonte de recuperação na reabertura;
working.json continua um arquivo derivado para o backend. --project explícito
é uma importação registrada no histórico, enquanto a retomada sem --project
recupera o cursor salvo. O launcher transporta project-history.json separado
do journal de texto, sem copiar cenas/saídas antigas.
