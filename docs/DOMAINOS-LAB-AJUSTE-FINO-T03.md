# T03 — proposta de ajuste por peça

Origem: resposta parcial T03, revisão 1, na prancheta. Este documento organiza
propostas; não declara implementação nem autorização. A execução começa somente
no item escolhido e autorizado pela pessoa. GTK3 continua a primeira tradução;
outros adaptadores recebem sua própria etapa e prova nativa.

## Estado atual — I120

I115–I119 possuem entregas técnicas registradas; suas avaliações humanas
continuam separadas. I120 está autorizado na revisão 1 e em investigação.
OpenFont no servidor da VM confirmou Swiss 742 Bold e Prestige Medium de
16 pixels, com ascendente 12 e descendente 4. A primeira é proporcional;
a segunda tem avanço de 8 pixels. As fontes usam HP-Roman8 e declaram
direitos Bitstream; uma licença de redistribuição não foi identificada.
Não foi aplicada uma substituição ao tema.

[Identificação e limites](referencias/domainos-sr104/I120-FONTES-IDENTIFICADAS.json)
e [medidas atuais Pango](referencias/domainos-sr104/I120-ALTERNATIVAS-PANGO.json)
separam referência, fontes configuradas, resolução pelo servidor e alternativas.
Ainda faltam comparação de glyphs/textos e equivalências por toolkit.

## Registro anterior — I115

As seis propostas I115–I120 foram autorizadas em revisões salvas; T03 está na
revisão 2. A execução está no I115, uma peça por vez. Base de receitas e
persistência concluída; primeira edição/tradução da seta GTK3 comprovada em
prévia nativa privada. O botão isolado GTK3 também ganhou receita própria
para moldura e espaço interno; isso não altera os nós internos de GtkRange.
O trilho GTK3 já tem campos ligados à tradução e medidas nativas comprovadas
nas duas orientações e pixels/estados atuais conferidos em quatro paletas.
Essa prova não estabelece os defaults históricos insensíveis/backdrop da VM. O cursor GTK3 também tem edição/tradução de três parâmetros e provas nativas
de pixels/estados. O encaixe agora tem tradução independente e prova de pixels em quatro paletas;
os dois campos já passaram o percurso nativo de edição e geração pela GUI.
A entrega pessoal continua pendente. I124 registra o pedido adicional de salvar progresso.
O planejamento abaixo permanece como contrato, não como declaração de conclusão.

## Base atual verificada

`TLRecipe` guarda posições e tamanhos por controle, porém geometria/relevo/fonte
continuam compartilhados pela receita da família. `TLNativeMetrics` distingue
alocação, mínimo, natural e escala; isso não é um default histórico da VM.
Undo/Redo do editor de texto não comprova reversão de mudanças numéricas do
projeto. A nova proposta não altera essa distinção.

## Seis etapas propostas

| Etapa | O que será ajustado | Critério para concluir |
| --- | --- | --- |
| 1. Peças independentes | Separar seta, botão da seta, trilho, cursor e encaixe nas receitas. | Mudar uma peça não altera as outras; limites do toolkit aparecem, sem desenhar uma imitação quando não houver API nativa. |
| 2. Eixos e proporções | Comprimento e espessura separados; trava de espessura/orientação. | Barra vertical varia só no comprimento, horizontal só no comprimento horizontal; outra peça permanece intacta. Mostrar pedido, mínimo e tamanho efetivo quando o toolkit impuser limites. |
| 3. Comparação pareada | Mesma peça/estado/posição lógica entre Motif e a família ativa. | Mostrar dimensões naturais/mínimas/alocadas, escala e fonte efetivas dos dois controles reais. Diferenciar posição dentro da prévia de posição global da janela. Não afirmar igualdade de pixels sem medir. |
| 4. Estados e relevo | Normal, pressionado, desabilitado, hover e foco por peça. | Prévia nativa interativa e estado editável somente quando a API permitir; mostrar limitações. Cores sempre seguem papéis KDE, sem RGB final fixo. |
| 5. Recuperação do ajuste | Histórico do projeto, ponto de comparação salvo e reset da peça. | Undo/Redo de várias alterações numéricas/estados/layout, restaurar ponto salvo e reset somente da peça com retorno recuperável. Provar recarga/reabertura e falha de escrita sem perder o projeto. Não substituir o histórico de texto. |
| 6. Fonte histórica, por último | Investigar fonte exata na VM SR10.4/VUE2.01 e equivalências. | Separar identificação comprovada, substituição e medidas atuais. Não tratar a fonte Motif instalada como prova da VM. Preservar licença/proveniência e suporte disponível por família. |

## Método de trabalho proposto

Escolher uma peça e uma família. Salvar um ponto de comparação. Medir a referência
Motif e a amostra nativa no mesmo estado. Alterar um parâmetro, observar o tamanho
real e o resultado visual; manter ou voltar ao ponto salvo. Só depois passar à
próxima peça. Sem comparar simultaneamente todas as famílias nem repetir provas
cuja entrada permaneceu igual.

Exemplo: numa barra vertical, aumentar o comprimento não deve engrossar a barra
nem aumentar a seta. Se o GTK exigir um mínimo maior que o pedido, mostrar ambos
os números. A ferramenta não deve ocultar essa restrição ou inventar a medida.

## Limites e organização

As seis etapas cabem no grupo Ferramenta/T03; não criam seis implementações
paralelas. A pessoa escolhe a próxima. Definição da UI, interações da prancheta,
projeto de tema e journals permanecem separados. Nenhuma demanda de manutenção
da própria Prancheta é assumida pelo contexto de tema/laboratório.

## Continuidade I117 — 2026-10-11

I115 e I116 entregues tecnicamente, com avaliação humana separada. I117 em
execução autorizada: comparação de posições locais e tamanhos físicos começa
por Motif/GTK3. Fonte efetiva da amostra será medida nesta etapa; investigação
da fonte principal histórica permanece no I120, por último. Receita Motif
independente não será sobrescrita para esconder diferenças. Consulte recibo
I117-BASE-COMPARACAO-20261011.json antes de repetir provas desta camada.

## Continuidade I118 — base por estado

I117 entregue; I118 autorizado e em execução. O módulo model/part_states.c mantém overrides esparsos normal/pressed/disabled/backdrop/hover/focus, com relevo flat/raised/sunken. Salvar/carregar preserva geometria e peças independentes; limpar retorna à herança. Não há RGB final nesta camada. Tradução gráfica e GUI ainda pendentes, e a geração rejeita explicitamente overrides não traduzidos. Receita não afirma suporte nativo para forçar estado de subpeça GtkRange. Provas: 947 verificações do modelo, 25 testes backend e teste isolado de estados; recibo I118-CONTRATO-ESTADOS-20261011.json. Próxima peça: seta GTK3.

### I118 — seta normal/pressionada e editor

Primeira tradução simbólica da seta comprovada em pixels reais: quatro direções/paletas e flat/raised/sunken em normal/pressed, incluindo restauração após interação. Editor Motif modular criado com estado de receita independente do estado nativo, hints e bloqueios explícitos. Teste de callbacks passou; percurso integrado e entrada real ainda pendentes. Receita dos outros estados e peças permanece preservada, sem geração silenciosa. Recibo I118-SETA-PIXELS-EDITOR-20261011.json.
