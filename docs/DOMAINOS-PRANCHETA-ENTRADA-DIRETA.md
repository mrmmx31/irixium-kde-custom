# I086 — entrada direta pelo corpo

Contrato antes dos widgets. Toggle Título/Texto; modo Texto permite vários
parágrafos e Inserir cria título genérico Instrução <ID> / Pergunta <ID> com
corpo em user.note. A ação explícita salva revisão 1 e horário; autosave
continua rascunho. Item novo sempre começa pending e authorized=false.
Limite 64000 bytes UTF-8; não truncar. Lock/fsync/history em transação única.
Título tradicional preserva o contrato anterior. Falha preserva entrada/Undo.
Inserção limpa de forma reversível; modos têm rascunhos/históricos separados
no journal auxiliar. Ausência de preferência mantém Título, sem migração.

UI Motif nativa, cores por papéis KDE, menu e atalhos de edição completos.
Provar UTF-8, limites, seleção/substituição, inserção, troca de modo, recarga,
reabertura e checkpoint falho antes de instalar.

Título solicitado para I086: Comunicação pela prancheta entrada. Renomear
por transação explícita na entrega, preservando nota/revisão/histórico. Não
reatribuir autorização antiga a novo hash; coordenar a janela antes dessa
renomeação pelo escopo autorizado atual.

O corpo inicial também define o escopo da nova proposta e entra no hash da
definição. O título genérico não substitui esse escopo. Respostas posteriores
continuam como interações; não reescrever o escopo ao editar a orientação.

Estado atual: contrato, modelo, frontend e journal privados implementados.
Treze fluxos Motif nativos, treze regressões de título e dez de edição passaram.
A reabertura conserva o journal completo; a primeira prova detectou a inserção
indevida de vazio no histórico e a correção passou a prova repetida. Quatro
paletas usam papéis KDE. Renomeação, instalação e handoff ainda pendentes.
