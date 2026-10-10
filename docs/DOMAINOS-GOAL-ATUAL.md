# Goal — conectar o Irix Classic DomainOS às funções do KDE

**Branch de trabalho:** `#irixfiles` · **Mantenedor:** `mrmmx31`\
**Revisão documental:** R2 — decisões da prancheta e esclarecimentos consolidados.

## Objetivo e autoridade das decisões

Continuar o protótipo existente no repositório `mrmmx31/irixium-kde-custom`.
A revisão consultada é `2f9f6277736ee6c6187cd010d4dd4f4990bb4822`. Não recomeçar
pela imagem nem reconstruir o painel em outra arquitetura sem necessidade demonstrada.
O desenho aprovado recebe funções reais; aprovação documental não comprova implementação.

A proposta é adaptar a linguagem visual Domain/OS SR10.4 / HP VUE ao KDE, e não
substituir o KDE ou eliminar recursos modernos úteis. Preservar composição,
proporções, relevos, faixa metálica, identidade GNU/LINUX, iconografia e a tipografia
privada aprovadas. As preferências funcionais não autorizam redistribuir os botões.

Ler conjuntamente:

- `DOMAINOS-REQUISITOS.md`: requisitos F01–F35 e critérios de verificação.
- `DOMAINOS-PREFERENCIAS.md`: organização por ferramenta, padrões e alternativas.
- `DOMAINOS-DECISOES-CONSOLIDADAS.md`: correspondência com as 28 respostas e com
  os esclarecimentos posteriores; distinção entre decisão e detalhamento proposto.

As respostas do revisor e os esclarecimentos posteriores prevalecem sobre propostas
antigas da prancheta. Não manter todos os itens como “aguardando confirmação”: as
funções abaixo estão decididas. Solicitar esclarecimento somente diante de uma
lacuna que altere o comportamento, de conflito novo ou de mudança de escopo; não
pedir novamente autorização para o que já foi respondido. Não registrar novos
detalhes sugeridos pelo redator como escolhas expressas do usuário.

## Instrumentação e identidade

A placa Tux + GNU/LINUX abre o menu geral de aplicativos, preservando sua aparência.
A gaveta de fixados é outro botão: `domainosApplicationsDrawer`, antes do terminal.
O botão de ajuda é independente do emblema.

O relógio consulta hora e fusos em um quadro suspenso; a data abre calendário e,
quando houver fonte configurada, agenda. Respeitar idioma, variante regional e
configuração temporal do sistema. Não duplicar o calendário no botão do relógio.

O gráfico pequeno mede recepção e envio de rede simultaneamente por padrão, com
preferência para trocar a métrica. Seu clique abre o `gr_osview` existente como
quadro suspenso. Não substituir uma medição ausente por zero ou inventar histórico.
O botão de correio abre o cliente configurado, com Thunderbird como preferência
de uso informada. Contagens e estados reais exigem fonte autorizada; não ler contas
ou inventar uma integração só porque existe um envelope desenhado.

## Iconbox, seleção e organização

Preservar o gerenciador de tarefas e seus recursos atuais, dentro da composição
aprovada. O padrão inclui janelas abertas e minimizadas conforme os filtros do
perfil; “somente minimizadas” é opcional. Não limitar o total de tarefas à quantidade
de células da imagem. Os lançadores fixados vão para sua gaveta, não substituem as
tarefas abertas. Agrupamento e filtros ficam nas preferências por ferramenta.

Clique simples seleciona imediatamente. Duplo clique restaura/ativa uma janela.
Ctrl acrescenta/retira itens; Shift seleciona intervalo. Uma seleção de duas ou mais
janelas permite operações em lote. A liberação de Ctrl/Shift após formar essa seleção
abre o menu de organização, respeitando o tratamento específico do seletor de grupo.
O botão direito preserva o menu existente e acrescenta as operações de organização.
Não acrescentar espera para dar resposta visual ao primeiro clique.

Ao selecionar um grupo, abrir uma relação das janelas com checkboxes. O usuário
escolhe membros individualmente, conserva a seleção e segue para outro grupo ou
item. Selecionar um grupo não seleciona automaticamente todos os seus membros.
Marcar uma caixa não restaura, organiza nem fecha a janela. O protocolo de conclusão
da seleção deve permitir esse percurso sem o menu de operações interromper cada
marcação; o detalhamento sugerido está nos requisitos, separado da decisão aprovada.

Oferecer comandos distintos de organização lado a lado/colunas, linhas/mosaico,
maximização em massa e minimização em massa. Para organizar o conjunto, reuni-lo no
desktop/monitor atuais. Atuar nas janelas efetivamente selecionadas, com identidade
atual e capacidades verificadas. Fechar normalmente continua visível; encerramento
forçado fica em submenu, nunca se confunde com Fechar. Conflitos de capacidade
X11/Wayland precisam de evidência e tratamento explícito, não de sucesso simulado.

Acrescentar um filtro automático opcional, com limiar definido nas preferências:
contar as janelas do escopo atual antes do filtro de minimização e independentemente
do agrupamento. Se a quantidade for maior que o limiar, apresentar somente as
minimizadas; ao voltar ao limiar ou ficar abaixo, restaurar a apresentação normal.
Isso não minimiza nenhuma janela e não limita quantas tarefas podem existir.

## Gaveta de aplicativos fixados

Conectar o botão já desenhado à lista própria de fixados do painel DomainOS.
Oferecer importação opcional dos fixados existentes, sem sincronização compulsória
com outra instância e sem confundir fixados com favoritos do menu de aplicativos.
Acionar um fixado solicita nova janela/instância. A tarefa criada é representada
na Iconbox; o fixado continua lançador. Aplicativos de instância única podem decidir
como responder à solicitação; não prometer uma segunda janela inexistente.

A gaveta deixou de estar adiada “até receber o documento”. Sua função foi aprovada
na prancheta e concluída pelos esclarecimentos desta revisão. Não ocupar outro
atalho, deslocar terminal/preferências/sessão/cadeado/ajuda ou alterar a faixa metálica.

## Pager e bandeja

O Pager mantém seu módulo: uma área usa o espaço disponível, duas aparecem lado a
lado e mais áreas ficam acessíveis por navegação. As setas adicionais ficam abaixo
e só são necessárias quando há mais de duas áreas. Por padrão, a roda percorre
cartões sem ativar outra área; troca imediata pela roda é alternativa nas preferências.
Clique no cartão ativa a área. Criar/remover/renomear exige ação explícita, preservando
IDs e a configuração existente. Work/Procrastination são nomes de referência/padrão
para configuração autorizada, nunca renomeação automática de desktops existentes.

O arraste de janelas entre miniaturas fica para a próxima versão. Movimentação por
menu e organização em lote não estão adiadas por causa disso. Miniaturas geométricas
continuam sem capturas do conteúdo; a confirmação histórica pedida para esse ponto
permanece registro de pesquisa, não uma equivalência já comprovada.

A bandeja usa seis posições, em duas linhas de três, com itens e ações reais.
▶ abre a continuação dos itens visíveis excedentes; se não for acomodável, usa
paginação. Uma preferência permite incluir também os ocultos. ▲ abre status e
notificações, mantendo acesso aos ocultos sem misturá-los compulsoriamente ao padrão
da ▶. Preservar menus e ações nativas, estados de atenção e escolhas individuais.
Não acrescentar chaves fictícias de configuração ou ícones estáticos simulando serviço.

## Rodapé e indicador

Terminal abre sessão normal do usuário. Preferências/paleta abre o System Settings
na área Appearance & Style; não redirecionar esse botão para outra função.
Sessão abre opções incluindo suspender/hibernar quando disponíveis, sem executá-las
só por abrir o menu. Cadeado solicita bloqueio real e informa falha.
Ajuda abre, nesta ordem, ajuda local do painel, xman e ajuda do KDE. O xman deve
acompanhar o esquema selecionado com contraste adequado; não fixar as cores do
exemplo de comando da prancheta. Documentação acompanha a distribuição, em pacote
principal ou documental conforme o empacotamento efetivamente adotado.

A lente acompanha o início e o fim da operação observável, sem inventar duração.
Preferência desabilitada por padrão: “Manter luz acesa após a conclusão”, com
checkbox e campo numérico de tempo. Somente o apagamento é postergado. A ação real,
o clique, o resultado e a pintura não esperam esse tempo. Não chamar esse recurso
de “simulação de execução”; se só há confirmação de envio, informar esse limite.
Animações opcionais de apresentação não podem bloquear a operação nem redesenhar o painel.

## Preferências e conclusão

Organizar as preferências por ferramenta, em central inspirada no System Settings:
categorias navegáveis, páginas específicas e separação entre padrão e alternativa.
A especificação da central é funcional, não exige criar um módulo global do KDE.
Os controles, fontes de configuração e propostas de usabilidade constam do documento
próprio. Não inventar valores numéricos aprovados para limiares ou durações.

Implementar, testar e instalar por usuário como opção independente do Irix Classic
existente. Instalar arquivos não autoriza substituir o painel ativo, criar desktops
ou alterar outros perfis. Ensaios iniciais usam dados e sessões isolados. Validação
nos perfis lsi e p001532 continua dependente de autorização de cada sessão.
Preservar o backup congelado indicado nos requisitos; não usá-lo como área de trabalho.

Concluir a etapa quando as funções de seu escopo e as preferências forem verificadas,
com instalação/restauração documentadas. Registrar bloqueios reais e o arraste entre
miniaturas adiado, sem declarar toda a integração concluída por uma captura ou teste
estático. Esta revisão entrega documentação; não contém implementação, testes nativos
novos, commit, push ou publicação de software.
