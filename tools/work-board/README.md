> Histórico: este frontend foi substituído pela aplicação independente AI Work Board.
> Consulte [a prancheta ativa](../../docs/DOMAINOS-PRANCHETA-UNIFICADA.md) antes de abrir ou alterar a fila.

# Prancheta de trabalho Motif

Interface C99/Motif com MVC. A prancheta organiza a fila e as decisões; não
executa notas como comandos e não altera o tema, o laboratório ou a VM.

```sh
make -C tools/work-board
tools/work-board/open
```

Dependências: compilador C, make, libmotif-dev, libjson-c-dev e libssl-dev.
O leitor existente `tools/theme-lab/build/theme-lab-colors` fornece os papéis
KDE. Consulte a compilação desse leitor no README do laboratório. Sem ele,
a UI conserva os recursos nativos Motif. Recarregar também relê a paleta; o
leitor assíncrono acompanha mudanças a cada cinco segundos. Uma paleta igual
não reconstrói os widgets nem suas dicas. Não há RGB final estático no código.

O launcher deriva os diretórios do repositório, HOME/XDG e não tem caminho de
usuário fixo. O estado persistente fica em
`${XDG_STATE_HOME:-$HOME/.local/state}/irixium/work-board/respostas.json`.
`--state /outra/pasta/respostas.json` permite usar uma pasta existente diferente.

## Uso

Selecione a atividade e um item à esquerda. Seu texto e a resposta da IA ficam
em campos separados. **Salvar item** grava apenas o item aberto: não é preciso
responder o restante. Trocar de item mantém rascunhos, marcados com `*`, e seu histórico de edição.
Recarregar mantém esses rascunhos e busca as respostas da IA. Se outra janela
alterou a mesma resposta, o salvamento antigo é recusado; compare o arquivo e
use Voltar ao salvo para retornar ao texto salvo (Ctrl+Z recupera o texto anterior). Fechar avisa sobre rascunhos
pendentes; não os descarta silenciosamente.

**Autorizar execução** e **avaliação** são separados. Aprovar a aparência não
autoriza automaticamente uma mudança. Uma resposta nova é calculada por
`user.revision > assistant.ack_revision`. Ao ler a revisão exata, a IA desmarca
esse aviso, preservando seu texto, horário, avaliação e autorização.

Marque o checkbox entre linhas para escolher um intervalo. Escreva o título e
use Inserir no intervalo. Complete os detalhes no campo de resposta do item
criado e salve. Instruções têm autorização própria, inicialmente desmarcada.
O modo Pergunta não permite autorização; sua resposta não libera tarefas.
As instruções também aparecem junto à tarefa de origem no filtro Todos ou
na atividade correspondente.

Nível de explicação: novice pede contexto e passos; intermediate concentra a
explicação na dúvida; expert pede confirmação técnica concisa. O aplicativo
registra o nível; a IA escreve a explicação, sem simular respostas automáticas.
Horários são ISO 8601 UTC, com milissegundos. Estado técnico, escopo e critérios
ficam separados da avaliação do usuário.

## Protocolo para a IA

1. Sincronizar o dataset e ler o estado. Conferir itens novos, autorização salva,
   escopo, nota e revisão atual; processar respostas parciais sem esperar todas.
2. Executar apenas o item autorizado, com o limite descrito; não inferir
   autorização das perguntas, de uma aprovação visual ou de ausência de resposta.
3. Registrar leitura/resposta pela revisão exata, preservando o texto do usuário.
   Se chegar uma nova revisão, reler; nunca limpar o aviso de uma resposta antiga.
4. Responder no nível escolhido e atualizar fila/evidência. Perguntas e propostas
   novas entram em itens separados, com posição `after`. Não repetir provas válidas.

Exemplo (a pasta e a revisão devem vir do estado atual):

```sh
tools/work-board/open --command sync
tools/work-board/open --command read
tools/work-board/open --command ack --id T01 --revision 1
tools/work-board/open --command reply --id T01 --revision 1 --input "$HOME/tempia/resposta-ia.json"
```

Arquivo de resposta da IA: `{"reply":"Explicação…","status":"waiting_user"}`.
Estados usuais: queued, running, waiting_user, done. running/done exigem
autorização do escopo atual. O CLI preserva os demais itens e usa bloqueio
não bloqueante, escrita atômica, histórico antes da troca e comparação de revisão.
Um critério/escopo alterado retira a autorização anterior e preserva o texto.
O dataset mantém IDs estáveis; não eliminar/reutilizar IDs que têm respostas.

## Organização MVC e validação

- `model.c`: JSON, revisão, autorização, bloqueio, histórico e persistência.
- `view.c`: widgets Motif, textos, dicas e layout. UTF-8 usa FontSet.
- `controller.c`: rascunhos, ações, atualização da UI e leitor KDE assíncrono.
- `main.c`: argumentos de GUI/CLI, ambos usando o mesmo modelo.

`make -C tools/work-board check` verifica persistência parcial, concorrência,
revisões antigas, autorização por escopo, perguntas, arquivos inválidos e lock
ocupado. A prova nativa usa dados artificiais em Xvfb; não aprova o tema.
O leitor de cores tem limite de cinco segundos e não bloqueia a interface.

A prancheta não é um daemon autônomo: a IA consulta o arquivo durante o trabalho
ou na próxima interação. Salvar comunica a decisão; não inicia um agente sozinho.

## Edição e recuperação obrigatórias

Ctrl+Z desfaz; Ctrl+Y ou Ctrl+Shift+Z refaz. Ctrl+C/V/X/A copiam, colam,
recortam e selecionam tudo. Botão direito, tecla Menu e Shift+F10 oferecem
menu de edição. Os campos de resposta e título têm histórico independente;
os campos de leitura permitem selecionar/copiar. Não confiar nas traduções
default Motif: caracteres de controle invisíveis são recusados.

O histórico preserva até 128 edições e 1 MiB por campo (sempre os dois últimos
valores). Não é um histórico ilimitado. Salvar, Recarregar, trocar de item e
Voltar ao salvo preservam esse histórico. Há botões Desfazer/Refazer para a
resposta. Voltar ao salvo também arquiva o último rascunho substituído.

O journal privado `respostas.json.drafts.json` preserva rascunhos, título e
histórico em disco a cada 200 ms enquanto se digita, com escrita atômica,
fsync e permissão 0600. O pequeno intervalo entre entrada e checkpoint não é
uma garantia contra qualquer perda de energia. Ações de substituição/fechamento
pela barra exigem checkpoint bem-sucedido. Falha de gravação mantém o texto
em memória e apresenta aviso; não descarta para retornar ao salvo. Apenas uma
GUI pode editar esse journal por vez. JSON inválido é preservado e impede a
abertura; não é substituído por um arquivo vazio. O journal tem limite de
32 MiB. Rascunhos não alteram as respostas/autorização salvas: **Salvar item**
ainda é necessário para enviar uma resposta. Reabrir recupera o que foi
protegido; autorização em rascunho não permite execução pela IA.

`make -C tools/work-board check-editing` verifica edição nativa com vários
parágrafos UTF-8, substituição, histórico, recarga, troca de item, menu,
crash/reabertura e falha de gravação. A prancheta original foi entregue sem
undo/redo validado; a conclusão anterior não cobria a segurança da edição.
