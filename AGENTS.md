# Continuidade do trabalho DomainOS

Entrada central: [índice de regras](docs/DOMAINOS-INDICE-REGRAS.md).
Regra obrigatória: todas as adaptações acompanham os papéis atuais do esquema
KDE; não inserir cores finais estáticas. Somente o LED e a luz do Pager têm
exceção de cor de sinal, com proteção de contraste. Consulte a
[regra de cores](docs/DOMAINOS-REGRAS-CORES.md) antes de qualquer correção visual.

Ao iniciar ou retomar trabalho no tema DomainOS, leia
[as regras comuns](docs/DOMAINOS-REGRAS-ROLAGEM.md),
[a fila de revisão](docs/DOMAINOS-FILA-REVISAO-VISUAL.md), o estado da etapa ativa
e o registro mais recente de evidências. Consulte também as decisões consolidadas
quando houver dúvida sobre uma preferência já definida pelo usuário.
Consulte também [as pranchetas e o protocolo de retorno](docs/DOMAINOS-CHECKLISTS-REVISAO.md).
Leia o JSON de respostas mais recente antes de repetir verificações. Agrupe o
projeto em dez itens relacionados e mantenha outra lista curta para a revisão
visual. Não preencha a aprovação do usuário a partir de um teste técnico.

O usuário pediu execução por etapas: somente uma família de controles recebe
correções visuais por vez. Registre novos defeitos na fila antes de mudar de tarefa.
Leia a regra antes de desenhar; traduza o contrato único
`tools/domainos_scrollbar_rules.json` para a implementação ativa e depois compare.
Distinga recursos configurados, defaults C comprovados e medidas da VM.
Conclua a etapa ativa com comparação visual nativa e registre seu resultado;
testes de integridade não comprovam fidelidade histórica de outra família.
Reutilize evidências válidas com seu escopo e hashes. Repita apenas o que tiver
entrada alterada, falha ou uma dúvida que a prova anterior não cobre. A falta
de avaliação manual não impede trabalho independente já autorizado.

Use exclusivamente Domain/OS SR10.4 com HP VUE 2.01 como referência histórica.
Fontes Motif de outra versão podem explicar algoritmos, mas não substituem a VM
ou comprovam métricas e aparência do SR10.4.

Preserve a VM e seu perfil de desempenho, as configurações pessoais dos usuários
e o backup aprovado em Downloads. As comparações e intervenções gráficas devem
usar os ambientes já autorizados. Não acrescente outra confirmação para ações
que o usuário já autorizou.

Atualize a fila antes de encerrar a interação: evidências obtidas, diferenças
restantes e próximo item. Informe ao usuário o avanço estimado e sua base,
sem transformar contagens de testes em porcentagem de fidelidade visual.

## Laboratório de temas

Toda ação, botão, combobox, campo numérico e controle de ajuste deve ter uma
dica que explique sua finalidade e unidade. Medidas nativas, mínimos do toolkit
e dimensões personalizadas devem ser distinguíveis. As comparações mantêm
coordenadas correspondentes e escala 1:1. Não apresentar uma aproximação
desenhada como renderização nativa de GTK, Qt ou Plasma. A ferramenta pode
abrir na sessão normal do usuário; testes que alterem o desktop permanecem
isolados. O usuário define quando usar Xephyr.
