# Amostra de grupo de opções GTK2 — I195

O controle `radio` da montagem representa um grupo de duas `GtkRadioButton`
reais, dentro de um `GtkVBox` homogêneo. Os textos Opção A/B vêm do contrato
existente de amostras. O GTK mantém exclusividade; o laboratório não reproduz
essa lógica com checkboxes ou cores.

Largura e altura solicitadas são do conjunto. Cada opção tem alocação e pedido
natural próprios, registrados em `group_members`; o pedido natural do conjunto
fica separado. O membro selecionado é `selected_member` (0 ou 1), estado de
execução, não preferência salva do projeto. O espaçamento zero e as duas opções
são composição da amostra, não medidas históricas do DomainOS.

Cliques normais operam opções. Ctrl+arraste em um membro move o conjunto sem
alterar seleção. A substituição transacional da cena mantém a seleção. A
preservação ao reiniciar processos por Aplicar usa um cache efêmero por origem,
com membro inteiro 0/1 e origem validados no IPC. Importar projeto limpa o cache.

A geração OPTION reutiliza os ativos dependentes dos papéis KDE. Foco, estado
inconsistente, RTL e backdrop automático continuam fora da prova atual. Uma
métrica do grupo não deve ser apresentada como dimensão de um botão individual.
