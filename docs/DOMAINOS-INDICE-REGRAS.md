# Índice de regras e continuidade DomainOS

Consultar ao iniciar ou retomar trabalho. A referência histórica é exclusivamente
Domain/OS SR10.4 com HP VUE 2.01. Ler a regra antes de alterar o desenho.

| Assunto | Fonte que deve orientar a implementação |
| --- | --- |
| Cores dinâmicas e exceções | [Regra de cores](DOMAINOS-REGRAS-CORES.md): todas as famílias seguem a paleta KDE; somente LED/Pager têm exceção com contraste. |
| Geometria, iluminação e rolagem | [Especificação](DOMAINOS-REGRAS-ROLAGEM.md) e [contrato único](../tools/domainos_scrollbar_rules.json). |
| Preferências já decididas | [Decisões consolidadas](DOMAINOS-DECISOES-CONSOLIDADAS.md) e [preferências](DOMAINOS-PREFERENCIAS.md). |
| Etapa ativa e defeitos pendentes | [Fila visual](DOMAINOS-FILA-REVISAO-VISUAL.md). Uma família por vez; GTK3 permanece ativo. |
| Evidências e limites técnicos | [Matriz](DOMAINOS-MATRIZ-VALIDACAO-R2.md), [comparação GTK3](DOMAINOS-COMPARACAO-ROLAGEM-GTK3.md) e [cores das setas](DOMAINOS-CORES-SETAS-REVISAO.md). |
| Retorno do usuário | [Pranchetas](DOMAINOS-CHECKLISTS-REVISAO.md): dez grupos do projeto e dez da revisão visual, com respostas em JSON. |
| Protocolos reutilizáveis por outras IAs | [Índice de skills](../skills/INDEX.md), com revisão visual e controle da sessão MAME existente. |
| Distribuição atual das regras | [Recibo R2](review/DISTRIBUICAO-REGRAS-R2.json): índice, política de cores e skills no pacote; scripts preservados e pacote R1 intacto. |

A regra de cores nos limites da rolagem GTK3 foi aplicada e conferida em quatro
paletas. A etapa ativa é o laboratório de ajuste manual solicitado pelo usuário. A moldura
principal da tabela GTK3 preenchida permanece como o próximo ajuste visual.
Documentação distribuída não equivale a auditoria concluída das demais famílias
ou aprovação visual do usuário.

## Laboratório de temas — nova etapa

A ferramenta Motif C99/MVC passa a integrar o goal em 2026-10-10.
[Escopo e arquitetura](DOMAINOS-LABORATORIO-TEMAS.md). O usuário conduz os
ajustes; receitas, medidas e evidências permanecem separadas. GTK3 é o primeiro
tradutor; a existência de uma prévia não comprova um adaptador concluído.
