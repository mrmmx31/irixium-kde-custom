---
name: retro-ui-review
description: "Review a visual software adaptation against an exact historical reference using a shared design rule, scoped evidence and an editable GTK checklist. Use for iterative theme or interface fidelity reviews and reviewer feedback; not for ordinary code changes without a visual review."
---

# Revisão visual com pranchetas

Mantenha uma regra documentada por controle e uma fila persistente por família
de implementação. Consulte o estado ativo e as respostas salvas a cada retomada.
O projeto pode escolher outra organização; não imponha Motif, KDE ou uma versão
histórica quando isso não fizer parte do pedido.
Em uma adaptação que acompanha esquemas de cores, os controles devem usar a
paleta atual da plataforma. Não inserir cores finais estáticas do original.
Leia [a política de cores](references/color-policy.md), incluindo estados,
contraste e exceções explicitamente autorizadas pelo projeto.

## Fluxo de revisão

1. Identifique a versão exata de referência. Levante recursos de configuração,
   defaults de fonte comprovados e medidas da imagem separadamente. Registre
   origem, paleta, escala e estado; não preencha uma lacuna com outra versão.
2. Defina o contrato de desenho antes de alterar assets. Traduza-o para a
   família ativa e compare a saída real, incluindo composição e cores. Igualdade
   de um glyph isolado não prova o controle inteiro nem os estados disabled.
3. Antes de repetir um teste, consulte seu recibo e hashes. Reuse uma prova
   quando fonte, contexto e critério forem os mesmos. Repita somente o escopo
   invalidado por mudança, falha ou relato novo; diga o que a nova prova resolve.
4. Agrupe o projeto em cerca de dez itens, ou na quantidade pedida, e mantenha
   outro checklist para a fila visual. Separe conclusão técnica de confirmação
   humana. Nada vem pré-aprovado pelo revisor.
5. Abra a prancheta em paralelo ao trabalho autorizado. O revisor pode marcar
   confirmado, falha, dúvida ou não testado, acrescentar uma nota e salvar JSON.
   Leia o arquivo salvo na próxima retomada, registre correções e mantenha as
   avaliações anteriores quando o critério mudar.

Use [o formato dos checklists](references/checklist-format.md) para criar os
dados. Execute `scripts/review_board.py --data <checklist.json> --data
<fila.json> --output <respostas.json>`; `--data` pode ser repetido. A interface
usa GTK3/PyGObject do sistema, sem CSS de cor próprio e sem instalar pacotes.
`--validate` confere os dados sem abrir uma janela. `--self-test` verifica
persistência, revisão de critérios e recusa de links, sem avaliar o produto.

## Conclusões e continuidade

Registre estado técnico e evidência curta para cada grupo. Teste automático,
medição visual e avaliação humana são provas diferentes. Não converta contagem
de testes em porcentagem de fidelidade. Se o usuário pedir progresso, informe
uma estimativa com escopo claro e os grupos ainda abertos.

Uma resposta só muda os itens que ela avalia. Não trate silêncio, campo vazio,
rascunho ou “não testei” como aprovação. A prancheta orienta o trabalho; não cria
uma confirmação obrigatória para cada mudança já autorizada. Preserve a sessão
real, o backup de referência e as janelas que o usuário pediu para manter.
