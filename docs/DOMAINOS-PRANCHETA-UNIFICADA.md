# Prancheta Motif consolidada

Entrega de 2026-10-10, autorizada explicitamente nesta conversa. A aplicação
independente **AI Work Board** substitui as pranchetas anteriores nesta sessão.
O projeto local fica em `Documents/Projetos Open Source/ai-work-board`, no diretório
pessoal. Sua documentação, protocolo e skill são portáveis e não incluem notas
pessoais no projeto destinado à publicação.

## Conteúdo preservado

| Seção | Conteúdo | Itens |
| --- | --- | ---: |
| Fila atual | Prancheta Motif: ferramenta e tema/painel; registros e rascunhos originais | 20 |
| Prancheta | Pedidos PR01–PR08 e instruções inseridas pelo usuário | 8 + inserções |
| Pesquisa de padrões | Motif/Xt, locale e nomenclatura, R01 | 1 |
| Checklists anteriores | Projeto (10), revisão visual (10) e funcionamento da barra (18) | 38 |
| Propostas anteriores | Estabilidade: problema, mecanismo, código, limites, evidências e retorno | 14 |

Os grupos originais continuam disponíveis no filtro da seção. IDs importados
recebem `GTK-`, `FUNC-` ou `PROP-`, evitando colisões com a fila atual.
Os documentos completos, respostas antigas e estruturas originais permanecem
no arquivo privado de migração, além dos campos `legacy_sources` e `legacy`.
Não foram inventadas avaliações para itens sem retorno. Um checkbox antigo
“Funciona” desmarcado e sem explicação continua ambíguo e aparece como pendente.

O menu **Exibir → Distribuir em abas** usa um checkbox: marcado mostra abas;
desmarcado usa **Pranchetas**. Preferência, seção, última seleção, notas e
históricos sobrevivem à navegação e à reabertura. Cada nota continua podendo ser
salva separadamente. Ctrl+Z/Y/Shift+Z/C/V/X/A e menu de edição foram preservados.

## Arquivos ativos

Derivar a pasta do ambiente:

```text
${XDG_STATE_HOME:-$HOME/.local/state}/ai-work-board/
  checklist.json
  respostas.json
  respostas.json.drafts.json
  migration-receipt.json
  legacy-import-20261010/
```

Abrir pelo launcher `open` do projeto independente. Ele prefere o checklist
privado quando disponível; o exemplo público é usado apenas na ausência dele.
O estado antigo em `irixium/work-board` e as respostas GTK em `/tmp` passam a
ser fontes históricas. Não reabrir os frontends antigos para a fila ativa.
O laboratório de temas, a VM, os documentos abertos e a prévia do tema foram
preservados; somente as pranchetas antigas foram encerradas.

## Regra de continuidade

Ler as respostas **salvas** no novo arquivo antes de executar uma tarefa.
A confirmação histórica importada não concede autorização de execução.
Rascunhos, mesmo com checkbox marcado, não são respostas enviadas. A migração
preservou os registros de usuário e IA da fila atual sem alterar revisão,
autorização ou nota. A etapa independente de navegação/importação foi pedida
explicitamente; isso não autoriza implementar outras propostas.

Para mudar critérios futuros, atualizar a definição ativa no checklist privado,
com escopo e evidência delimitados, e usar Recarregar. As definições originais das
revisões GTK são evidência histórica; não representam aprovação de alterações
posteriores. Não marcar conclusão humana a partir de um teste técnico.

## Evidência desta entrega

- 20 testes de modelo/importação: 13 anteriores e sete novos.
- Sete verificações nativas: checkbox, abas, menu, rascunhos independentes,
  desfazer após navegação, recuperação e ausência de autorização automática.
- Verificação após abertura: 72 itens, todos os registros originais da fila
  idênticos e o rascunho preservado. Instâncias antigas encerradas.
- Arquivos de estado privados fora do projeto publicável; cores lidas dos papéis KDE.

O recibo da migração com hashes permanece na pasta de estado. O
[recibo técnico publicável](review/WORK-BOARD-CONSOLIDACAO-20261010.json) usa dados
artificiais e não inclui respostas pessoais. Na versão final foram reexecutados
os oito fluxos nativos e dez cenários de edição, todos aprovados tecnicamente.
Implementação desta etapa entregue; revisão manual da organização permanece aberta.

## Atualização: fila Prancheta e incidente de recarga

Antes da modularização, o conteúdo ativo tinha 80 itens em cinco seções. PR01–PR07 e R01 foram registrados
com critérios, fontes e prioridade posterior à etapa atual. A proposta de três
arquivos e textos externos está documentada no projeto independente; a separação
completa ainda não foi implementada. O combobox de atividade permanece estático,
com opções dinâmicas por grupo da seção aberta. Notas e interações não viram
estrutura/código da UI. O locale da aplicação atual é C.UTF-8; não impor latin-1.

O pedido direto seguinte para corrigir título e recarga foi tratado como incidente,
sem liberar a fila futura. A janela publica nome UTF-8 e fallback ICCCM. Recarregar
combina seções por ID, preserva itens e valida o resultado antes de gravar; arquivos
parciais não eliminam a navegação anterior. A Form não solicita encolhimento ao
reconstruir filhos. Filtro/seleção acompanham o item. Provas com dados artificiais:
22 verificações de modelo/importação, cinco de recarga, sete de navegação e dez de
edição segura. Revisão humana da correção permanece pendente.

## Atualização: arquitetura modular PR08

Em 2026-10-10, o pedido direto de modularização foi aplicado ao projeto
independente e à prancheta aberta no lsi. `src/` contém `app`, `common`, `model`,
`persistence`, `controller`, `view`, `editor` e `platform`; interfaces públicas
ficam em `include/work_board`, e detalhes privados nos headers dos módulos.
São 36 arquivos C; o maior tem 144 linhas. O mapa de manutenção está em
`ai-work-board/docs/MANUTENCAO.md` no projeto independente. A biblioteca do modelo
compila e funciona sem Motif, X11 ou Qt. O build gera objetos/dependências por
arquivo, e os 53 checks de modelo/importação/API e fluxos nativos passaram.

A substituição da instância preservou registros de usuário, rascunhos, seleção
e históricos de undo. Cinco seções e 82 itens estavam presentes nesse momento;
inserções futuras continuam dinâmicas. Na Fila atual, **Todos** é o filtro geral;
os dois grupos são **Ferramenta** e **Tema/painel**. Grupos das demais seções
aparecem ao selecionar suas abas/menu. Filtros por autorização/falha ainda não
existiam naquela entrega: I082 ainda não tinha autorização salva.

As respostas T01/P01/P04 revisão 1 foram reconhecidas, sem alterar notas ou
autorizações. Métricas de controles, ordenação da gaveta e menu Operações
continuam como etapas próprias. PR08 está implementado/testado; aceite humano
permanece pendente. [Recibo técnico](review/WORK-BOARD-MODULARIZACAO-20261010.json).

## Acompanhamento na prancheta — I085

Revisão 3 autorizada e entregue: a coluna esquerda contém lista e andamento,
separados por divisória ajustável. O último aviso da IA substitui o anterior,
com estado/horário UTC e limite de 1.600 bytes UTF-8. A leitura do estado ocorre
a cada dois segundos e atualiza somente esse painel; os detalhes/editor continuam
com recarga explícita para preservar a edição. Não é telemetria nem histórico
cumulativo. A falha de leitura conserva o último aviso válido. A IA deve registrar
etapas relevantes pelo CLI, com a revisão atual, para permitir o acompanhamento.

Provas: nove fluxos Motif, modelo sem GUI e cinco verificações de recarga/abas.
Reabertura lsi preservou decisões, rascunhos, navegação e undo por comparação.
[Recibo](review/WORK-BOARD-ACOMPANHAMENTO-20261010.json). Aceite manual pendente.
I086/I088 foram lidos/respondidos; entrada pelo corpo e expansão dentro da coluna
continuam sem autorização e não foram implementados como extensão deste item.

## Filtros por estado — I082

Revisão 2 autorizada: implementados e instalados no projeto independente.
O novo seletor combina estado, seção e categoria; distingue falha reportada,
consentimento salvo válido e conclusão técnica/avaliação humana. Uma lista vazia
permanece vazia e conserva seção/estado ao reabrir. Rascunhos e undo sobrevivem
à troca de filtros; salvar continua necessário para enviar uma resposta.
Dez fluxos Motif, dez de edição e cinco de recarga passaram, além do cliente
do modelo sem GUI. A reabertura normal está coordenada com o usuário.

Novas respostas lidas: I085 revisão 4 confirma o acompanhamento; I083 revisão 2
autoriza histórico somente leitura em etapa própria. I089 revisão 1 pede um
visualizador de diferenças por item, motivo/caminhos e realce; não tem autorização.
Não foi implementado junto aos filtros. O registro de respostas I083/I085 foi
recusado pela revisão automática por escopo; seus campos permanecem intactos.

I082 foi reaberto após a pausa expressamente liberada: janela normal única e
maximizada, filtro visível e paleta atual. Decisões, rascunhos, undo e navegação
foram preservados por comparação exata. [Recibo](review/WORK-BOARD-FILTROS-20261010.json).
Entrega técnica: 100%; avaliação humana pendente. O reconhecimento isolado de
I083 revisão 2 foi aceito após inspeção do CLI e da autorização salva, sem
reescrever a orientação da pessoa. O histórico é a próxima etapa independente.

I082 revisão 3 foi confirmado pelo usuário e reconhecido pelo CLI. I083 revisão 2
foi implementado/testado/instalado sem fechar a janela de avaliação. Histórico
somente leitura, paginação, editor preservado e leitor cancelável foram provados.
[Recibo](review/WORK-BOARD-HISTORICO-20261010.json). Falta reabertura coordenada
e verificação lsi; pergunta de pausa enviada com a entrega preparada. I090
revisão 2 está autorizado para a próxima etapa separada. I089 continua sem
autorização. Nenhum aceite humano foi preenchido pela IA.

I083 entregue e verificado na janela real lsi: Histórico está visível à direita
dos seletores depois de separar o consentimento em sua linha. Escopo permanece
visível; decisões, rascunhos, undo e navegação foram idênticos na reabertura.
[Recibo atualizado](review/WORK-BOARD-HISTORICO-20261010.json). Avanço da entrega
técnica I083: 100%; aceite humano pendente. A prioridade salva Q091 revisão 1
substitui a ordem anterior: etapa ativa I084 revisão 2 autorizada, aviso/filtro
de novas respostas da IA. I092/I090/T01 aguardam etapas próprias; sem alterações
no laboratório, tema ou VM durante este trabalho.

I084 revisão 2 está implementado, testado e instalado: aviso no canto superior
direito, pulsação com papel de atenção KDE e filtro global reversível Novas
respostas. Registro privado de leitura não muda avaliação, autorização ou
rascunho. Provas nativas verificam chegada de respostas durante digitação,
inclusive no filtro ativo, menu/abas, recuperação, paletas e preservação do
editor. [Recibo](review/WORK-BOARD-NOVAS-RESPOSTAS-20261010.json). Reabertura foi
coordenada após concluir a entrega concreta. Avanço técnico antes da conferência
lsi: 80%; avaliação humana separada.

I083 revisão 4 foi reconhecido e continua na fila autorizada para o novo modo
bate-papo e a ordem de seletores/checkboxes. A entrega anterior de histórico
somente leitura cobre revisão 2, não essa ampliação. I092/I090/T01 aguardam suas
etapas; laboratório, tema e VM não foram alterados.

I084 entregue e conferido no lsi após a pausa liberada: aviso/filtro visíveis,
pulsação real observada e preservação exata de respostas, rascunhos, Undo e
navegação. [Recibo final](review/WORK-BOARD-NOVAS-RESPOSTAS-20261010.json).
Avanço técnico da etapa: 100%; aceite humano permanece pendente. Próxima etapa
autorizada: I083 revisão 4 (bate-papo/layout); ainda não implementada.

I083 revisão 5 conserva o mesmo escopo da revisão 4. Bate-papo, compositor e
Undo independentes, referência somente leitura e seletores acima dos checkboxes
estão implementados/testados/instalados. Dezessete fluxos próprios e regressões
relevantes passaram; quatro esquemas KDE acompanham os papéis atuais.
[Recibo](review/WORK-BOARD-BATE-PAPO-20261010.json). Avanço técnico: 80%; falta
pausa coordenada para reabrir e conferir a janela lsi. A prancheta em uso foi
preservada. I093 (liberar reabertura) e I094 (prioridade) foram registrados e
aguardam suas etapas; os demais itens mantêm seu estado. Aceite humano separado.

I083 entregue no lsi pela liberação salva revisão 6: janela única aberta, hash
da compilação confirmado e comparação exata de respostas/rascunhos/Undo/journal.
Seletores acima dos checkboxes e Histórico/escopo visíveis; modo Bate-papo
permanece opcional e não foi imposto à navegação da pessoa. [Recibo final](review/WORK-BOARD-BATE-PAPO-20261010.json).
Avanço técnico desta etapa: 100%; avaliação humana separada e goal amplo ativo.

## Entrega I090 e retorno reaberto

I090 revisão 2 foi instalado e reaberto na sessão lsi com journal/respostas/Undo
idênticos: campo Título expandido, Limpar reversível, limpeza após inserção e
placeholder separado. [Recibo](review/WORK-BOARD-INSERCAO-20261010.json).
Entrega técnica 100% desta etapa; avaliação humana pendente. I083 revisão 7
confirma o bate-papo entregue. I084 revisão 6 reabre o posicionamento inicial
das conversas na última mensagem; é a próxima etapa autorizada, sem alteração
do verdict durante I090. O pedido de reset específico após nova correção está
na política RETORNO-AVALIACAO.md do projeto independente, com implementação
segura pendente. Etiquetas I092 permanecem uma etapa distinta.

## I084: nova rodada entregue

Conversa, referência e resposta simples iniciam na última mensagem; atualizações
preservam a leitura anterior. A operação `review` apresenta Não avaliado e
Aguardando retorno, mantendo o registro humano e os rascunhos anteriores.
[Recibo](review/WORK-BOARD-NOVA-RODADA-20261010.json): onze fluxos focados,
modelo e regressões de edição/histórico/compositor passaram. Instalação e
reabertura lsi conferidas com respostas e journal idênticos. Entrega técnica
I084: 100%; retorno humano pendente, sem conclusão do goal amplo.

Revisões 2 de I086/I088/I089 autorizam respectivamente entrada pelo corpo,
expansão dentro da coluna e visualizador de diferenças. I093 revisão 2 conserva
o pedido de liberação temporária de reabertura. São tarefas próprias na fila;
I092 continua a próxima etapa registrada, salvo nova orientação de prioridade.
Q087 revisão 2 mantém a falha real de Operações e sua proposta de popup próprio,
sem autorizar pela pergunta alterações nos demais menus.

## I092: etiquetas entregues

CONCLUÍDO apresenta `done` registrado pela IA; EM ESPERA apresenta `waiting_user`.
O observador atualiza só as etiquetas de execução dos botões existentes, sem
recarregar o editor. Onze fluxos focados, edição (10), avisos (15) e navegação
maximizada a 1920 px (7) passaram. A correção também preserva a seção lembrada
e suas seleções ao reabrir o filtro global Novas respostas.
[Recibo e handoff](review/WORK-BOARD-ETIQUETAS-20261010.json): revisão 2 atual,
janela lsi reaberta e todos os campos atuais do journal/respostas idênticos.
Entrega técnica I092: 100%; decisões humanas não foram preenchidas pela IA.

I095 registra separadamente recorte do menu Pranchetas a 1650 px sem abas,
com captura/geometria verificadas e autorização desmarcada. Não interpretar
o teste maximizado como prova de todas as resoluções. Próxima etapa: I093,
sujeita à orientação mais recente; o goal amplo continua ativo.

## I093: liberação temporária entregue

Pedido específico e revogável, separado das respostas e do journal; botão
oculto ao começar/fechar, aplicação e motivo explícitos, ajuda permanente e
contorno pelo papel KDE de atenção com fallback de contraste. As dicas Motif
continuam visíveis e não capturam os cliques sobre controles. [Recibo](review/WORK-BOARD-REABERTURA-20261010.json):
quinze fluxos próprios, API sem GUI e regressões relevantes. Instalação/reabertura
lsi conferidas: respostas e journal inteiro idênticos, inclusive Undo/Redo.
Entrega técnica I093: 100%; goal amplo ativo, sem preencher aceite humano.
Próxima etapa conforme resposta parcial I094 revisão 2: prioridade. I096 revisão
2 registra fechamento manual urgente e permanece na sequência.

## I094 — prioridade instalada

Contrato `docs/PRIORIDADES.md` no projeto AI Work Board: prioridade salva por pessoa, independente de consentimento; fila comum GUI/CLI e compatibilidade com documentos antigos. [Recibo](review/WORK-BOARD-PRIORIDADES-20261010.json): oito provas do modelo, treze fluxos nativos e regressões pertinentes passaram. Instalação guardada de 29 caminhos; pausa para reabrir lsi solicitada pelo botão I093, ainda sem liberação. Entrega técnica 90%; falta handoff da janela. Próximo I096 urgente.

I094 revisão 3: primeira reabertura preservou todos os dados, mas expôs achatamento no filtro vazio maximizado. Corrigido com base em XmRowColumn(3); cinco provas geométricas e regressões passaram. Correção instalada, segunda pausa solicitada via I093. A nova nota foi preservada/reconhecida. Entrega técnica 90%; I096 urgente permanece seguinte.

I094 entregue: correção final reaberta por liberação específica da pessoa, binário/captura conferidos e todos os dados/journal/Undo iguais. Entrega técnica 100%; aceite humano separado. I084 revisão 9 foi confirmado pela pessoa e sua rodada encerrada sem apagar texto. Próximo I096 urgente; objetivo amplo ativo.
