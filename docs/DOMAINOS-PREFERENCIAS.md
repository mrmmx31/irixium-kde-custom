# Irix Classic DomainOS — preferências por ferramenta

**Revisão funcional R2 · mantenedor `mrmmx31`.** Este documento especifica a central
solicitada; não contém código, nem afirma que essa central já existe no protótipo.
Ler com [requisitos](DOMAINOS-REQUISITOS.md) e
[rastreamento das decisões](DOMAINOS-DECISOES-CONSOLIDADAS.md).

## 1. Diretriz aprovada e limites

O usuário pediu preferências amplas **organizadas por ferramenta**, com navegação
semelhante ao System Settings do KDE. A estética clássica não é motivo para eliminar
funções modernas úteis. Um comportamento padrão não impede uma alternativa explicitamente
solicitada; uma preferência também não autoriza alterar o desenho e a posição dos
controles aprovados.

A organização descrita a seguir é a tradução documental dessa diretriz. Nomes de
páginas, agrupamento de campos e convenções de edição são **proposta de organização**,
não captura de uma interface pronta nem lista de novos módulos do KDE já existentes.
A escolha técnica entre janela própria, configuração de applet ou outra integração
não está fechada por esse pedido.

Manter separados três acessos:

| Acesso | Destino |
| --- | --- |
| Placa GNU/LINUX | Menu geral de aplicativos |
| Paleta/preferências já desenhada no rodapé | System Settings, área Appearance & Style, como aprovado em RESP-E02 |
| Configuração do painel | Central de preferências próprias, organizada pelas ferramentas abaixo |

**Acesso proposto para a central:** item “Configurar Painel Irix Classic DomainOS…”
no menu de contexto do painel; acesso contextual de uma ferramenta pode abrir sua
página diretamente. Isso não cria outro botão na chapa nem muda o atalho de aparência.
Esse caminho de entrada é uma sugestão de usabilidade, não uma decisão adicional
já respondida sobre um ícone.

## 2. Estrutura de navegação proposta

Categorias à esquerda; controles e explicações da categoria à direita. Usar títulos
que indiquem a ferramenta, não uma única página enorme chamada “Avançado”. A página
pode ter subseções quando a ferramenta justificar. A tabela define organização, não
uma árvore obrigatória de arquivos ou componentes.

| Categoria | Páginas/subseções | Requisitos associados |
| --- | --- | --- |
| Painel geral | Identidade, instância/monitor, apresentação, teclado e diagnóstico | F01, F30, F31, F33 |
| Instrumentos | Relógio; data e calendário; gráfico/telemetria; correio | F02–F05 |
| Menu de aplicativos | Provedor existente, apresentação e recursos úteis já disponíveis | F01 |
| Iconbox | Conteúdo e filtros; filtro automático; agrupamento/ordem; seleção e gestos; organização em lote | F06–F10, F34, F35 |
| Aplicativos fixados | Lista própria; importação; abertura de aplicativos | F32 |
| Pager | Desktops e nomes; cartões e navegação; representação geométrica | F11–F14 |
| Bandeja e notificações | Visibilidade/ordem; excedentes; ocultos/status; ações de itens | F15–F23 |
| Comandos do rodapé | Terminal; aparência; sessão; bloqueio; ajuda | F24–F28 |
| Interação e atividade | Resposta dos controles; animações opcionais; lente e tempo adicional | F29, F33 |
| Instalação e diagnóstico | Recursos, estado da integração, perfis, restauração | F30, F31, F33 |

**Convenções propostas:** busca de preferências por rótulo/descrição, subseções
progressivas, navegação por teclado, indicação de mudanças não aplicadas e comandos
Aplicar/Descartar/Restaurar padrões da página. “Restaurar padrões” deve indicar seu
escopo e não zerar outros módulos silenciosamente. Essas convenções são sugestões
para ensaio; não alegam reproduzir cada comportamento do System Settings instalado.

## 3. Como ler os padrões

- **Confirmado:** definido na prancheta ou nos esclarecimentos posteriores.
- **Preservar:** não foi pedido que a consolidação alterasse a configuração atual.
- **Não quantificado:** a opção foi pedida, mas não há valor numérico escolhido.
- **Proposta:** detalhe do redator para implementar/testar sem atribuí-lo ao usuário.

Uma opção desabilitada por padrão não é um recurso descartado. Uma opção cujos
valores dependem do sistema não pode apresentar uma fonte de dados indisponível
como configurada e funcional. A capacidade deve ser conferida e explicada.

## 4. Instrumentos e menu de aplicativos

| Preferência | Definição funcional | Padrão/origem |
| --- | --- | --- |
| Hora e fusos | Fonte temporal da sessão; consulta suspensa pelo relógio | Confirmado; calendário permanece no botão próprio |
| Idioma/região da data | Seguir configuração de idioma e variante regional, incluindo diferenças entre variantes de inglês | Confirmado; não fixar o exemplo “Feb 27 / Thu” |
| Agenda | Exibir eventos somente quando houver fonte configurada | Confirmado; sem criar/acessar contas por dedução |
| Métrica da face gráfica | Recepção e envio de rede simultâneos; permitir trocar o objeto medido | Confirmado; rede é o padrão |
| Origem/unidade/escala do medidor | Identificar o sensor, direção, unidade e escala usada | Requisito de interpretação; escolhas numéricas não quantificadas |
| Abertura do medidor | Mostrar o gr_osview existente como quadro suspenso | Confirmado; não lançar monitor diferente no lugar sem decisão |
| Cliente de correio | Cliente escolhido; Thunderbird foi informado como preferência do usuário | Confirmado; não sobrescrever silenciosamente o padrão global |
| Estado do correio | Contagem/atenção somente por integração autorizada | Confirmado; fonte ausente é indisponibilidade |
| Menu geral de aplicativos | Reaproveitar os recursos úteis do menu existente | Confirmado em intenção; preservar busca/categorias/favoritos disponíveis, sem confundi-los com pins |

Os segundos do relógio e detalhes adicionais de escala/amostragem não receberam
valores novos nesta consolidação. Preservar a apresentação aprovada; não adicionar
outro ponteiro ou subdivisão por iniciativa da implementação. Ajustes necessários
devem ser classificados como técnicos ou visuais antes de mudar a referência.

## 5. Iconbox

### 5.1 Conteúdo, filtros e contagem

| Preferência | Definição funcional | Padrão/origem |
| --- | --- | --- |
| Conteúdo normal | Mostrar janelas abertas e minimizadas conforme o escopo do perfil | Confirmado: manter o funcionamento atual |
| Apenas minimizadas | Filtro manual de apresentação | Alternativa confirmada, não padrão obrigatório |
| Automatizar apenas minimizadas | Acionar o filtro pela quantidade de janelas | Alternativa confirmada; não ativar sem escolha |
| Limiar de entrada | N>L ativa o filtro; N≤L volta ao normal | Regra confirmada; L não quantificado |
| Escopo de monitores/desktops/atividades | Respeitar as preferências da instância designada | Preservar; não ampliar/reduzir escopo global por esta revisão |
| Número de tarefas | Sem limite de quantidade derivado da arte; percorrer pelas setas | Confirmado; limiar de filtro não é capacidade de tarefas |

N conta janelas antes do filtro de minimização e antes do agrupamento. Nenhuma
janela é minimizada pela preferência automática. Se o usuário quiser só minimizadas
permanentemente, não é a mesma escolha que o modo automático que volta ao normal.

**Apresentação proposta dos controles:** escolha de modo “normal”, “apenas
minimizadas” ou “automático conforme quantidade”, com campo do limiar habilitado só
no último modo. Essa apresentação evita combinar opções conflitantes; o uso de
radio buttons ou de lista de seleção ainda é uma escolha de implementação.

Não selecionar um valor inicial de L em nome do usuário. A implementação deve
registrar a escolha inicial e permitir ajustá-la. Exemplos de teste podem usar
valores arbitrários, desde que não sejam publicados como padrão aprovado.

### 5.2 Ordem, agrupamento e seleção

| Preferência/contrato | Definição funcional | Padrão/origem |
| --- | --- | --- |
| Agrupamento por aplicativo | Manter recurso configurável e visível nas preferências do painel | Confirmado; não impor GroupDisabled |
| Ordem e rótulos | Preservar ordenação configurável; rótulo da janela e detalhes acessíveis | RESP-B04 + recurso existente; não atribuir valor novo sem necessidade |
| Clique simples em janela | Seleciona sem restaurar/ativar | Confirmado |
| Duplo clique em janela | Restaura/ativa | Confirmado; sem esperar para mostrar seleção no primeiro clique |
| Ctrl e Shift | Acrescentar/retirar membros e selecionar intervalo | Confirmado |
| Grupo selecionável | Lista das janelas com checkboxes; seleção acumulada entre grupos | Confirmado pelo último esclarecimento |
| Título no seletor do grupo | Sem checkbox marcado, restaura/ativa; durante seleção por checkbox, marca/desmarca | Pedido de 2026-10-09; esvaziar a seleção recupera restauração direta |
| Miniaturas de janelas ao passar o mouse | Prévia nativa opcional, por instância | Pedido de 2026-10-09; desligada por padrão |
| Botão direito | Menu atual acrescido de organização | Confirmado |
| Menu de operações após seleção | Soltar Ctrl/Shift após duas ou mais janelas | Confirmado, com detalhe de integração ao seletor de grupos proposto nos requisitos |
| Botão do meio, roda na Iconbox e demais ações herdadas | Preservar recursos existentes que não contradigam as escolhas explícitas | Não redefinidos individualmente nesta rodada; mapear o estado da instância antes de importar |

Atualização de 2026-10-09: o clique simples conserva a seleção e abre a lista,
inclusive para uma janela individual; Ctrl/Shift continuam a seleção acumulativa.
O duplo clique minimiza a janela ativa, restaura a minimizada ou ativa a inativa.
A roda navega pelas páginas por padrão, sem trocar de janela. Ativar janelas pela
roda é uma alternativa nas preferências. O pedido distingue o título dentro do seletor
do grupo: ele restaura diretamente enquanto nenhuma seleção por checkbox está em andamento.
O fato de haver muitas preferências não dispensa um comportamento padrão coerente.

### 5.3 Operações em lote

Reunir as janelas efetivamente escolhidas no desktop/monitor atuais para a organização.
Os comandos de disposição em linhas/colunas/mosaico, maximização em massa e minimização
em massa são distintos. Preferências de organização não substituem a escolha explícita
da operação no menu, nem atuam assim que uma caixa é marcada.

O menu com checkboxes deve permitir continuar a seleção de outros grupos. Estado
parcial do grupo, “x de y selecionadas” e manutenção do popup durante a marcação são
**detalhes propostos** para evitar erros. A integração com a liberação de Ctrl/Shift
precisa ser testada, não completada com atraso artificial.

“Encerrar à força” permanece em submenu. Confirmações, reconhecimento de alvos e
tratamento de processos que possuem várias janelas são salvaguardas a verificar,
não autorização para finalizar tudo que compartilha o mesmo nome de aplicativo.

## 6. Gaveta de aplicativos fixados

| Preferência | Definição funcional | Padrão/origem |
| --- | --- | --- |
| Lista de fixados | Própria da instância/painel DomainOS | Confirmado; independente de favoritos do menu |
| Importar fixados existentes | Importação opcional com identificação da origem | Confirmado; não sincronizar compulsoriamente |
| Acionamento de um pin | Solicitar nova janela/instância | Confirmado; aplicação define a capacidade real |
| Relação com tarefas | Janela aberta aparece na Iconbox; pin continua lançador | Confirmado |
| Ordenação/retirada de pins | Administração da lista própria, sem fechar janelas ou desinstalar programas | Consequência funcional da lista de lançadores; detalhes de edição propostos |

Não oferecer “trazer a janela existente por padrão” como se tivesse sido a escolha
do usuário. Não reutilizar a lista de um Task Manager arbitrário. A origem de uma
importação deve ser identificada; a importação não altera o gerenciador de origem.

## 7. Pager

| Preferência | Definição funcional | Padrão/origem |
| --- | --- | --- |
| Desktops reais | Criar/remover/renomear por comando explícito; mínimo um | Confirmado; preservar configuração existente ao instalar |
| Cartões visíveis | Um usa o módulo; dois lado a lado; demais por navegação | Confirmado; não reduzir a quantidade global a dois |
| Nomes | Work/Procrastination como referência/padrão de configuração nova autorizada | Confirmado; não impor a nomes existentes |
| Roda do mouse | Percorrer cartões sem ativar área | Confirmado como padrão |
| Roda troca área | Alternativa nas preferências | Confirmado, desabilitado no comportamento padrão |
| Setas adicionais | Abaixo dos cartões, para mais de duas áreas | Confirmado; sem ocupar lateral da miniatura ou mudar a chapa |
| Miniaturas | Geometria das janelas, não captura de conteúdo | Confirmado; referência histórica detalhada ainda a pesquisar |
| Arraste entre miniaturas | Adiado para próxima versão | Não mostrar como configuração funcional nesta entrega |

## 8. Bandeja e notificações

| Preferência | Definição funcional | Padrão/origem |
| --- | --- | --- |
| Posições à vista | Seis, duas linhas de três | Confirmado; quantidade não é limite do total de provedores |
| Ordem/visibilidade | Seleção individual preservada/configurável | Confirmado; não esconder automaticamente tudo considerado “não crítico” |
| Conteúdo da ▶ | Somente visíveis excedentes | Confirmado como padrão |
| Incluir ocultos na ▶ | Alternativa explícita | Confirmado, fora do padrão |
| Apresentação dos excedentes | Continuação deslocada; paginação quando não for acomodável | Prioridade confirmada, não dois comportamentos sem ordem |
| ▲ | Status/notificações e acesso aos ocultos | Confirmado; não repetir apenas a paginação |
| Ações dos ícones | Preservar gestos e menus do provedor real | Confirmado |
| Atenção/ausência de itens | Mostrar estado verdadeiro, preservar acesso a quem pede atenção | Confirmado; sem LED normal fixo |

A preferência de visibilidade não apaga provedores. O quadro de notificações não
limpa histórico nem altera “Não perturbe” por ser aberto. Controle de volume, redes
e dispositivos permanece onde a ação é explicitamente solicitada.

## 9. Rodapé, ajuda e atividade

| Preferência/contrato | Definição funcional | Padrão/origem |
| --- | --- | --- |
| Terminal | Terminal preferido, nova sessão normal | Confirmado; sem elevar privilégio |
| Aparência | Encaminhar a Appearance & Style | Confirmado; não usar esse botão para a nova central própria |
| Sessão | Ações de sessão incluindo suspensão/hibernação conforme suporte | Confirmado; abrir opções não executa ação |
| Bloqueio | Bloqueio real da sessão com relato de falha | Confirmado |
| Ajuda | Painel → xman → KDE | Ordem confirmada; documentação local disponível |
| xman e cores | Acompanhar esquema atual e contraste | Confirmado; os hexadecimais do exemplo não são constantes da paleta |
| Animações de apresentação | Podem ser opcionais, sem bloquear comandos | Opção confirmada em geral; efeitos específicos não enumerados |
| Lente padrão | Acompanha início/fim observáveis | Confirmado |
| Manter luz após conclusão | Checkbox habilita permanência adicional | Confirmado; desabilitado por padrão |
| Tempo adicional da lente | Campo numérico com setas e unidade explícita | Confirmado como controle; valor/range não quantificados |

A duração extra não é delay do comando nem simulação de execução. O tempo começa
na conclusão observável e só posterga apagar a lente. Checkbox desligado torna o
valor inoperante. Operações simultâneas e sem notificação de término precisam de
tratamento honesto, especificado e ensaiado; não declarar conclusão usando apenas
uma duração artificial.

## 10. Aplicação, persistência e integração com preferências existentes

**Propostas de engenharia para avaliar durante a implementação:**

1. Separar preferências do painel de ações globais do KDE. Alterações de desktops,
   cliente padrão ou aparência global devem indicar o alcance e depender de ação
   explícita. Não reconfigurar outros usuários, instâncias ou a opção Irix Classic.
2. Manter uma fonte de verdade por propriedade: valor próprio do painel ou valor
   ligado ao provedor KDE, com origem visível. Não criar duas telas que se sobrescrevam
   silenciosamente. Agrupamento ligado ao KDE também deve estar acessível na página
   da Iconbox, conforme RESP-B04.
3. Não salvar a cada passagem do mouse ou usar timer para processar um clique.
   Aplicar deve comunicar falhas; descartar não deve desfazer operações de janelas
   já executadas fora da configuração.
4. Explicar indisponibilidade de uma capacidade sem mostrar checkbox funcional
   fictício. Configuração não substitui implementação.
5. Preservar preferências por migração versionada e oferecer restauração documentada.
   Essa é orientação de implementação, não um algoritmo de migração já validado.

Números e políticas não escolhidos pelo usuário devem constar do registro de
implementação como proposta/teste. Não abrir novamente as 28 decisões para perguntar
os mesmos padrões; consultar somente diferenças que alterariam a intenção aprovada.

## 11. Aceite da central

A central estará funcional quando cada opção documentada tiver destino claro,
padrão/alternativa identificáveis, persistência conferida e efeito limitado ao
escopo anunciado. Validar busca/navegação e Apply/Discard se a organização proposta
for adotada. Verificar que o limiar da Iconbox não limita tarefas, que a roda do
Pager não muda desktops no padrão e que a lente prolongada não atrasa comandos.
Não declarar a central implementada apenas por entregar este catálogo de preferências.
