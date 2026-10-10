# Pranchetas de avaliação DomainOS

Atualização: 2026-10-10. São duas listas de dez grupos. Na abertura, todos
começaram **Não avaliado**; evidência técnica existente não equivale à sua aprovação.
Cada grupo permite Confirmado, Falha, Dúvida ou Não testei, com o botão Explicar.
O [retorno parcial salvo](review/RETORNO-20261010-PARCIAL.md) confirma V01 e V02
no escopo observado. Os outros 18 grupos continuam sem resposta.

## Projeto — dez grupos

Fonte: [checklist do projeto](review/project-checklist.json), requisitos F01–F35
e decisões consolidadas. As ressalvas de cada evidência aparecem na prancheta.

| ID | Grupo | Estado técnico |
| --- | --- | --- |
| P01 | Applications e gaveta de fixados | Evidências existentes |
| P02 | Relógio, calendário e feriados | Evidências existentes |
| P03 | Rede, gr_osview e correio | Evidências existentes |
| P04 | Iconbox: cliques, grupos e rolagem | Evidências existentes |
| P05 | Seleção, Operações e pin temporário | Evidências existentes |
| P06 | Pager e áreas de trabalho | Evidências existentes |
| P07 | Bandeja, excedentes e notificações | Evidências existentes |
| P08 | Rodapé, ajuda e LED de espera | Evidências existentes; LED em X11 |
| P09 | Preferências, dicas e miniaturas | Evidências existentes |
| P10 | Temas, cores, decorações e suíte | Parcial; revisão visual e teste final em p001532 abertos |

## Revisão visual — dez grupos

Fonte: [checklist visual](review/visual-checklist.json) e
[fila de execução](DOMAINOS-FILA-REVISAO-VISUAL.md). Esta lista delimita a revisão;
não solicita repetir ensaios aprovados de cada componente.

| ID | Grupo | Avaliação humana | Estado técnico |
| --- | --- | --- | --- |
| V01 | Cores e harmonia das setas | Confirmado nas barras GTK observadas; sinal + do spin diferente de − relatado | Parcial; novo defeito do spin pendente e estado inteiramente insensível sem regra histórica confirmada |
| V02 | GTK3: barras, relevo e encaixe | Confirmado; usar como exemplo para as demais versões GTK | Parcial; moldura principal da tabela preenchida pendente |
| V03 | GTK2 | Sem resposta | Na fila |
| V04 | GTK4 e limites da API | Sem resposta | Na fila |
| V05 | GTK1 e suporte disponível | Sem resposta | Na fila; cobertura DomainOS não comprovada |
| V06 | Qt Widgets e Kvantum | Sem resposta | Na fila; seta inferior relatada |
| V07 | Qt Quick e System Settings | Sem resposta | Na fila; seta inferior relatada |
| V08 | Controles próprios do Plasma Style | Sem resposta | Na fila |
| V09 | Chapa metálica e desenho do LED | Sem resposta | Na fila; borrão e escala relatados |
| V10 | Conjunto, decorações e esquemas | Sem resposta | Após as etapas individuais |

O retorno avalia a prévia R13. A correção posterior r2 das cores nos limites
GTK3 ainda não foi apresentada nessa Xephyr; sua prova técnica não foi
convertida em aprovação humana. Os datasets 1.0 permanecem preservados.

## Abrir e responder

O comando do projeto é `python3 -B tools/review_domainos.py`. Ele abre as duas
pranchetas e grava em uma pasta privada em `/tmp`, identificada pelo UID do
usuário, sem alterar seu tema. `--output` permite escolher outra pasta existente.

O frontend está na skill portável
[retro-ui-review](../skills/retro-ui-review/SKILL.md). A execução genérica não
depende de nome de usuário, Downloads ou instalação do projeto:

```bash
review_dir=$(mktemp -d /tmp/domainos-review.XXXXXX)
python3 -B skills/retro-ui-review/scripts/review_board.py \
  --data docs/review/project-checklist.json \
  --data docs/review/visual-checklist.json \
  --output "$review_dir/respostas.json" \
  --title 'DomainOS — pranchetas de avaliação'
```

Execute a partir da raiz do repositório, em uma sessão com GTK3/PyGObject.
Salvar respostas mantém a janela aberta. Salvar e fechar grava e encerra.
Fechar com alterações grava um rascunho. Ao reabrir com o mesmo caminho, as
respostas são recuperadas; mudanças de critério preservam a resposta anterior
e reabrem somente o item alterado. Cada nova gravação mantém um histórico.

Ao retomar o projeto, ler as respostas salvas, registrar falhas/dúvidas na fila
e consultar a evidência que já cobre cada grupo. Repetir uma prova somente por
entrada alterada, falha ou dúvida ainda não coberta. A avaliação do usuário não
bloqueia trabalho independente e as notas não são comandos executáveis.

O protocolo de controle da VM também está preservado como skill portável:
[mame-live-control](../skills/mame-live-control/SKILL.md). Ele usa a sessão
existente e não requer reiniciar a VM para consultar seu canal atual.

## Conferência desta entrega

| Verificação | Resultado e limite |
| --- | --- |
| Organização dos requisitos | Duas listas de dez grupos; F01–F35 aparecem uma vez na lista do projeto. Nenhuma aprovação preenchida pela IA. |
| Prancheta GTK | Janela real observada no KWin/Wayland, aberta e não minimizada. Uma falha inicial de escopo da variável de título foi corrigida; o registro bruto foi preservado. |
| Respostas | Persistência conferida offline. Retorno manual parcial salvo: V01 e V02 confirmados no escopo observado; outros 18 grupos sem resposta. JSON e janela preservados. |
| Skills portáveis | Metadados válidos, cópias instaladas idênticas e ZIP com hashes conferidos. |
| Scripts MAME | 19 testes offline com Lua 5.4 e serviços simulados; nenhum comando na VM nesta entrega. Isso não comprova movimento/foco em outro emulador. |

O [recibo com hashes](review/PREPARACAO-SKILLS.json) permite reutilizar essas
provas enquanto os arquivos e critérios permanecerem iguais. Os testes do tema
já registrados não foram repetidos para preparar estas pranchetas.

A distribuição R2 acrescenta a regra explícita de cores dinâmicas e os índices;
seu [recibo próprio](review/DISTRIBUICAO-REGRAS-R2.json) identifica os hashes novos.
Os scripts, datasets e a prancheta aberta foram preservados. A entrada central
passa a ser o [índice de regras](DOMAINOS-INDICE-REGRAS.md).
