# Uso do painel Irix Classic DomainOS

Este é o manual da composição funcional 0.2.11. O painel utiliza dados e serviços
da sua sessão KDE, preservando o desenho aprovado. A instalação coloca arquivos
no seu perfil; a utilização começa quando você adiciona o widget. Nenhum painel
ativo é substituído pelo instalador. [README.md](README.md) contém os comandos de
instalação e restauração.

## Primeiro uso e cores

Em **Adicionar widgets**, procure **Irix Classic DomainOS**. Pode ser usado no
desktop ou em um painel horizontal com espaço suficiente: 971 × 109 é o tamanho
mínimo solicitado, e 1942 × 218 é a base de desenho. O Plasma determina o espaço
disponível; o widget não reorganiza os demais widgets nem ajusta a altura do painel.

O Style `IrixClassicDomainOS` e **DomainOS SR10.4** são opções independentes nas
configurações de aparência. Escolhê-los é opcional: o painel acompanha os papéis
de cor da paleta atual do KDE, inclusive uma troca de esquema durante a execução.
Os ícones de aplicativos vêm do provedor de tarefas, incluindo QIcons próprios.
A luz e a moldura de seleção do pager conservam o amarelo original; em superfícies
amarelas com pouco contraste, outro tom do mesmo amarelo define a seleção.

Para configurar o applet, abra o menu da placa **GNU/LINUX** e escolha **Configure
panel…**, ou use a ação de configurar widget do Plasma. A janela nativa tem oito
categorias. **Aplicar** salva os valores da página nesta instância; descartar
recarrega os valores salvos. Isso não desfaz comandos já executados, como fechar
uma janela ou criar uma área de trabalho.

### Teclado

Use **Tab** para percorrer os controles. Nos botões do painel, **Espaço** ou
**Enter** mostra a pressão imediatamente e executa a ação ao soltar a tecla.
Perder o foco antes de soltar cancela a ação pendente, como sair do botão com o
mouse. A área já ativa do pager continua elevada também pelo teclado.

Na Iconbox, **Espaço** seleciona a tarefa em foco, **Enter** restaura/ativa,
**Menu** abre o contexto e **Escape** fecha os menus/quadro de seleção.
Os modificadores **Ctrl/Shift** conservam os mesmos papéis de seleção. Os
checkboxes individuais de grupos usam o teclado nativo dos controles Qt.

## Instrumentos à esquerda

| Controle | Clique e dados apresentados |
| --- | --- |
| Relógio | Hora real local; clique abre a consulta dos fusos escolhidos. Não muda o fuso do sistema. |
| Data | Data conforme idioma/formato regional; clique abre calendário. Eventos dependem de provedores instalados e explicitamente escolhidos. |
| Gráfico | Rede, inicialmente recepção e envio simultâneos; clique abre o gr_osview existente. As preferências permitem CPU, memória, disco ou IDs de sensores reais. |
| Correio | Abre o cliente escolhido, sem iniciar uma mensagem. A integração opcional do Thunderbird fornece disponibilidade e total real de não lidas; fonte ausente aparece como indisponível. |

Sensores e relógio indisponíveis são indicados como tal. Ausência de dados não é
substituída por zero. Taxas usam unidades reais e escala baseada nos valores
observados; percentuais usam escala de 100%. O gr_osview permite conferir fontes,
unidades e escala. O componente gr_osview é instalado junto pela suite.

Sem uma escolha local de correio, o botão consulta o cliente configurado para
`mailto`; se não houver, procura Thunderbird instalado. Não abre um URL `mailto:`
nem altera o cliente padrão do KDE. Uma escolha local deve ser um Desktop ID,
como `org.mozilla.thunderbird.desktop`; ela precisa corresponder ao ID realmente
instalado. Se não houver cliente válido, o painel informa a indisponibilidade.

Em **Correio e comandos**, a lista mostra clientes instalados que anunciam suporte
a correio. **Mostrar a contagem real** é opcional e começa desligado. O integrador
do Thunderbird compartilha somente disponibilidade e total de pastas físicas,
sem nomes de contas/pastas ou conteúdo; veja [a instalação separada](../../../integrations/thunderbird-domainos/README.md).
O instalador do painel não instala extensões em perfis do Thunderbird.

Em **Relógio e calendário**, escolher **Feriados** torna acessível a página nativa
de regiões. Os provedores escolhidos são ativados ao abrir o calendário e
descarregados ao fechá-lo. Uma fonte sem regiões/eventos informa a ausência;
não exibe uma agenda de exemplo.

## Iconbox: selecionar e operar janelas

A Iconbox mostra janelas abertas e minimizadas dentro do escopo configurado. Sete
posições são visíveis de cada vez; as setas laterais alcançam todas as tarefas.
O número de posições não é um limite de janelas. Inicialmente, o escopo é a área
e a atividade atuais, com janelas de todas as telas, agrupamento por aplicativo
quando o espaço estiver ocupado e ordem manual. São valores técnicos iniciais,
não uma nova decisão do usuário.

- **Clique simples:** seleciona imediatamente e abre o seletor, inclusive quando
  há uma só janela. Ctrl/Shift continuam formando a seleção sem abrir uma lista
  a cada clique. A placa usa a cor de destaque e
  o relevo permanece pressionado enquanto o item estiver selecionado e não
  minimizado. Minimizar levanta os relevos do botão e da placa sem apagar a
  seleção; o destaque continua identificando a seleção para operações em lote.
  Um grupo levanta quando todas as suas janelas estão minimizadas.
- **Duplo clique individual:** minimiza a janela que já está ativa; se estiver
  minimizada, restaura; se estiver inativa, traz para a frente. O duplo clique
  no grupo mantém a lista de membros aberta e não age em todos implicitamente.
- **Ctrl+clique:** acrescenta ou retira uma janela da seleção.
- **Shift+clique:** seleciona um intervalo a partir da âncora; Ctrl+Shift permite
  acumular o intervalo.
- **Grupo:** abre a escolha de janelas individuais por checkboxes. Marcar uma não
  seleciona automaticamente todas nem ativa a janela. Sem checkboxes marcados,
  clicar no título restaura/ativa somente aquela janela e fecha o seletor.
  Depois de iniciar a seleção por checkbox, clicar no título marca/desmarca;
  ao desmarcar todos, o título volta a restaurar. **Continuar seleção** preserva o que foi
  escolhido; **Operações** abre os comandos do conjunto.
- **Pin temporário:** com uma janela marcada, **Operações** oferece fixá-la à
  esquerda, fora do grupo. As próximas seguem a ordem de fixação. O pin identifica
  essa janela, respeita os filtros e desaparece quando ela fecha ou o painel
  reinicia. **Desafixar esta janela da Iconbox** é a primeira opção do menu direito
  desse item. Não cria um fixado permanente na gaveta.
- **Clique direito:** abre o menu nativo de tarefas KDE, com os comandos que o
  provedor oferece àquela janela/grupo e as operações adicionais do DomainOS.
- **Botão do meio:** inicialmente pede nova instância; em Iconbox pode escolher
  nenhuma ação, fechar, nova instância, minimizar/restaurar, agrupamento ou trazer
  para a área atual. As ações de janela sobre um grupo abrem a escolha de membros,
  sem agir implicitamente no primeiro. Nova instância e agrupamento atuam pelo grupo
  nativo, conforme sua capacidade.
- **Roda:** por padrão percorre as páginas de itens como as setas laterais, sem
  ativar nenhuma janela. A página Iconbox oferece a alternativa de alternar/ativar
  janelas, com opção de pular minimizadas. No modo de ativação, a navegação circula
  nas pontas e, sobre um grupo, percorre seus membros.
- **Miniaturas:** desligadas por padrão; habilite na página Iconbox para mostrar
  prévias ao passar o mouse sobre uma janela ou grupo. Usa WindowThumbnail em X11
  e KWin/PipeWire em Wayland, somente enquanto a prévia está visível. Falta de
  composição/provedor ou janela minimizada em X11 é indicada no próprio quadro.
- **Dicas do Iconbox:** títulos e lista numerada do grupo são o padrão ao passar
  o mouse. Títulos individuais completos não repetem uma dica; um grupo conserva
  sua relação ordenada de títulos. No seletor, nomes abreviados aguardam o intervalo
  de tooltip do sistema. As miniaturas ficam fora da lista, preferencialmente acima
  dela; sair lateralmente fecha a apresentação. A legenda da própria miniatura só
  oferece o nome completo quando estiver abreviada, após o mesmo intervalo e dentro
  da área da imagem. A página Iconbox permite substituir essas dicas por miniaturas ou
  desligar ambas. Os outros botões e a bandeja têm sua opção própria de dicas,
  desligada por padrão em Interação e atividade.
- **Ordem Manual:** arraste uma tarefa sobre outra para reordenar a lista nativa.
  O gesto usa a distância de arraste do sistema; somente ao soltar sobre uma tarefa
  atual é solicitado `TasksModel.move`. Não move, minimiza, fecha ou ativa janelas,
  nem altera pins. Um alvo que desapareceu/mudou de identidade ou outro modo de
  ordenação recusa a reordenação. Não há mudança das molduras ou tamanhos dos botões.
  Ctrl+Shift+Esquerda/Direita também reordena a tarefa com foco.

Soltar ambos Ctrl e Shift após uma seleção de duas ou mais janelas abre uma vez
o menu do conjunto. A escolha individual de um grupo não é interrompida por essa
liberação. Sair do botão antes de soltar cancela o clique. O painel confere a
identidade e o PID novamente antes de agir; uma janela que fechou ou mudou de
processo não vira outra tarefa por reutilização de seu identificador.

Os botões que abrem menus, gavetas e quadros alternam a abertura: clicar outra vez
no mesmo botão fecha o conteúdo; o próximo clique abre novamente. Isso inclui
Ajuda, Sessão, GNU/Linux, fixados, relógio, calendário, gr_osview, grupos e as duas
gavetas da bandeja. A troca de estado ocorre no clique, sem timer de interação.

No comando nativo **New Desktop** de um grupo, a composição do grupo também é
conferida novamente. Se alguma janela entrou ou saiu desde que o menu foi aberto,
o painel pede para reabrir o menu antes de criar a área ou mover janelas. Assim,
uma janela recém-chegada não entra inadvertidamente na operação do menu anterior.

**Columns/Rows/Mosaic** organizam ao menos duas janelas selecionadas. **Collect**
reúne o conjunto; maximizar/minimizar em lote também reúne as janelas antes da
operação. O destino é a área de trabalho corrente e o **monitor ativo do KWin
(`activeScreen`)**, usando sua área útil. Isso pode diferir do monitor onde o
widget está desenhado. O helper confirma o destino e as geometrias/estados reais;
restrições de tamanho dos aplicativos podem impedir o arranjo exato. Nesse caso,
o resultado relata a limitação em vez de anunciar sucesso completo.

Organização de conjuntos recusa janelas transientes/modais e seus pais quando há
um diálogo dependente, mesmo escolhendo ambos. O KWin pode propagar a mudança de
desktop/monitor para janelas dependentes não selecionadas; sua API de scripts não
expõe toda a relação `mainWindows/transients`. Um transiente de grupo sem pai exposto
também impede a operação enquanto estiver presente. Essa restrição é informada antes
de alterar qualquer alvo. Fechar normalmente continua usando o fluxo do aplicativo.

Os comandos nativos de uma janela continuam disponíveis conforme suas capacidades:
minimizar/maximizar, mover/redimensionar interativamente, fechar, áreas/atividades
e outros recursos do menu instalado do KDE. Organização de conjuntos fica
indisponível sem a ponte KWin necessária; o painel não simula um arranjo movendo
apenas seus próprios ícones. Aplicativos podem aceitar um lançamento e reaproveitar
a janela existente, conforme seu comportamento de instância única.

**Forçar encerramento** fica em submenu separado do fechamento normal. A operação
verifica novamente janela, PID e todas as janelas conhecidas do mesmo processo,
inclusive fora do filtro atual. É recusada quando atingiria uma janela do processo
que não foi selecionada. Só envia o sinal a um processo do próprio usuário,
mantendo um `pidfd` contra reutilização do PID. A confirmação de envio do sinal
não significa que o painel observou a saída do processo.

### Filtro opcional da Iconbox

Em **Iconbox**, escolha todas as janelas no escopo, apenas minimizadas ou o modo
automático. O automático só fica disponível quando você escolhe um limiar **L ≥ 0**;
o valor inicial **−1** significa **não escolhido**. **N** conta as janelas reais
do escopo antes de filtrar minimização e agrupar: **N > L** apresenta minimizadas;
**N ≤ L** volta ao normal. A indicação do filtro aparece na Iconbox.

Aplicar o filtro não minimiza, fecha ou limita janelas. Alterar agrupamento também
não executa operações nas janelas. As exceções de agrupamento usam App IDs/URLs
de lançadores, não nomes traduzidos; a ação explícita no menu nativo salva as
exceções nesta instância.

## Pager: áreas reais e mapas

O pager usa as áreas, nomes e IDs reais da sessão. Uma área ocupa o módulo; duas
ficam lado a lado; com mais áreas, setas e roda permitem navegar pelos cartões.
Por padrão, navegar com a roda não muda a área ativa. A preferência **A roda também
ativa a área de trabalho percorrida** altera esse comportamento explicitamente.

Clique numa área para ativá-la. A área ainda não selecionada afunda somente
durante a pressão e sobe ao soltar; a luz e a moldura amarela permanecem na área
ativa. Clicar de novo na área ativa não afunda nem desloca seu conteúdo. Arrastar
para fora antes de soltar cancela o clique.

As miniaturas são mapas da geometria das janelas, sem captura de seu conteúdo.
A preferência de mostrar somente janelas desta tela afeta esses mapas. O menu
de contexto oferece criar, remover e renomear áreas, sujeito ao serviço e às
autorizações KDE; sempre preserva pelo menos uma área. São comandos sobre a
sessão real, não consequências de abrir/aplicar preferências. O painel não cria
Work/Procrastination por padrão. **Arrastar janelas entre miniaturas está adiado.**

## Bandeja, status e notificações

A bandeja utiliza os provedores da bandeja nativa desta instância. Seis posições
em duas linhas de três mostram os itens visíveis. Os eventos e menus de Wi-Fi,
Bluetooth, áudio e demais itens continuam pertencendo aos respectivos provedores.
O painel não substitui os serviços por desenhos de exemplo.

**▶** abre a continuação dos excedentes; se não couberem, pagina. Há uma opção
explícita para usar paginação e outra para incluir os ocultos. **▲** abre status,
notificações e acesso aos ocultos. Abrir o quadro não limpa notificações nem
altera Não perturbe. Cada item pode oferecer ações próprias de seu provedor.

As listas de visibilidade e ordem pertencem à bandeja deste applet. Na configuração,
escolha entre política nativa, visível e oculto para cada provedor, ou informe IDs
nativos. Um ID não pode estar ao mesmo tempo nas listas visível e oculta. Listas
vazias conservam a política nativa desta instância, incluindo escolhas existentes.

## Placa GNU/LINUX, gaveta e faixa metálica

A placa **GNU/LINUX** abre o catálogo de aplicativos nativo do KDE, com pesquisa
global de aplicativos, navegação, favoritos e recentes conforme o provedor. **Configure
panel…** abre as preferências do applet. A gaveta apresenta os favoritos pelo
mesmo modelo nativo e na mesma ordem desse menu, incluindo a interface KDE
opcional. A lista própria de fixados continua em armazenamento independente.

O botão das janelas sobrepostas na faixa metálica abre a **gaveta de aplicativos
fixados**. Use **Pin** no catálogo ou a ação de fixar no menu da Iconbox para
acrescentar um Desktop ID à lista própria. Na gaveta, use as setas para ordenar
e o botão compacto de remoção para retirar. A gaveta organiza três seções:
preferências permanentes no topo, fixados pela barra de tarefas e favoritos do
KDE, com separadores. Os botões de operação medem 28 × 28 px para deixar espaço
aos nomes. Retirar um pin não altera nem fecha a tarefa aberta na Iconbox.
Ativar um pin solicita o lançamento do aplicativo, que pode reutilizar uma
instância existente. Um pin ausente permanece removível e não anuncia lançamento.

Em **Aplicativos fixados**, também é possível fornecer IDs manualmente ou escolher
uma fonte de importação. **Escolher fonte para importar…** lista fontes compatíveis
do seu próprio perfil; **Importar fonte selecionada** lê somente a fonte escolhida.
Aplicar salva a gaveta, sem escrever na origem nem sincronizar favoritos alheios.

Os cinco atalhos da faixa, na ordem do desenho, são:

| Atalho | Comportamento |
| --- | --- |
| Terminal | Abre uma sessão normal do terminal escolhido; vazio segue o preferido do KDE ou Konsole. |
| Aparência | Abre Appearance & Style no System Settings. Abrir não muda o esquema. |
| Sessão | Abre o menu de sair/suspender/hibernar conforme o suporte. Sair apresenta o diálogo do KDE; abrir o menu não executa uma ação. |
| Cadeado | Solicita o bloqueio real da sessão e consulta confirmação quando o serviço a oferece. |
| Ajuda | Oferece este manual, o navegador de manuais Unix xman e a ajuda KDE, nessa ordem. |

O comando de terminal aceita executável e argumentos separados sem shell:
`konsole --new-tab` é um exemplo, enquanto `|`, `>` e `&&` não são interpretados.
O xman utiliza cores derivadas da paleta atual; exige xman instalado e um display
X11/XWayland disponível. Correio, terminal e xman ausentes são erros explícitos.
Terminal, Aparência, xman e Ajuda KDE anunciam o lançamento pelo KIO usando um
Desktop Entry executável temporário, com `StartupNotify=true`. O arquivo fica
num diretório privado de cada pedido, conserva os argumentos literais e o
diretório de trabalho e é eliminado após a resposta ou erro. Não é instalado
no catálogo de aplicativos do usuário. A resposta confirma somente a aceitação
do pedido, sem devolver o PID do launcher como se fosse o da aplicação.
Se KIO não estiver instalado, esses comandos usam a criação direta do processo
e informam que não solicitaram uma notificação de inicialização. Se KIO já
recebeu o pedido e não responder a tempo, o estado da solicitação é desconhecido:
a aplicação pode ter iniciado, e o painel não repete o comando automaticamente.

A lente inferior acompanha pedidos em andamento e seus resultados observáveis.
Durante a espera, pisca com 500 ms acesa e 500 ms apagada, como o recurso
`waitingBlinkRate` do HP VUE 2.01. O painel mostra o cursor de espera do tema de
cursores selecionado, sem bloquear botões ou atrasar comandos. O cursor não
permanece durante o tempo adicional opcional da lente.
Ao acender, usa amarelo com proteção de contraste se a superfície conflita com
essa cor. O sinal de um pedido imediato fica pendente de apresentação até um
quadro efetivamente apresentado; a ação e seu resultado não aguardam esse quadro.
Um launcher/TaskManager pode confirmar apenas a aceitação do pedido, sem confirmar
que uma janela apareceu ou que a aplicação terminou. A lente não fabrica essa
conclusão. Em paralelo, observa os registros reais `IsStartup` que o TaskManager
do KDE publica, inclusive para lançamentos externos. Essa espera continua depois
da resposta do launcher enquanto o KDE mantiver o registro, sem atribuí-lo a
uma janela ou declarar sucesso quando ele desaparecer. O caminho KIO desses
quatro atalhos foi verificado em X11 com inicialização lenta e argumentos
preservados. Em Wayland, a notificação depende também do token de ativação e
do contexto da sessão; essa espera não foi comprovada pelo ensaio X11.
O fallback por `Popen`, aplicativos sem notificação de inicialização e instâncias
já abertas podem não publicar `IsStartup`: nesses casos, a adaptação confirma
apenas o pedido observado.
O modelo unificado `TasksModel` também pode omitir registros de inicialização
quando já há uma janela correspondente aberta. Portanto, a ausência de
`IsStartup` não comprova que uma janela está pronta nem que o lançamento falhou.
No catálogo, nos favoritos e nas ações contextuais de aplicativos, o retorno do
provedor nativo encerra o pedido; navegar por categorias ou editar favoritos
não acende a lente por si só. **Manter a luz acesa depois da conclusão** é opcional e desligado
inicialmente; seu tempo adicional só posterga apagar a luz. Não atrasa o clique,
o comando ou o relevo pressionado. Com operações simultâneas, o tempo adicional
começa somente depois do último pedido ou registro de inicialização observado.

A VM SR10.4 confirmou LED alternando, ampulheta no painel e fim da espera quando
o novo cliente apareceu. O contorno coral observado era foco do painel; não há
evidência de todos os botões metálicos piscando juntos. O cursor SGI Classic
reutilizado no KDE tem seu próprio desenho de espera; não redistribuímos o cursor
Apollo nem substituímos o bitmap dos botões. A lente mantém o amarelo aprovado
pelo usuário, com proteção de contraste, e a luz do pager permanece independente.

## Preferências e valores técnicos iniciais

| Categoria | Opções desta instância |
| --- | --- |
| Relógio e calendário | Fusos consultados, inicialmente Local/UTC; provedores de eventos inicialmente não selecionados. |
| Monitor e gr_osview | Métrica, interface (`all` inicialmente), IDs de sensores, intervalo e histórico. Valores técnicos: 1000 ms e 60 amostras; a faixa oferecida acompanha o mínimo efetivo de 1000 ms. O relógio mantém atualização própria de 1000 ms. Duas séries exigem a mesma unidade nativa. |
| Correio e comandos | Cliente instalado ou preferido do KDE; contagem real opcional; executável/argumentos do terminal. Vazio segue a resolução do perfil descrita acima. |
| Iconbox | Área/tela/atividade, filtro e L, agrupamento, apenas quando cheio, ordem, exceções, ação do meio e roda/pular minimizadas. |
| Aplicativos fixados | Lista própria, ordem, remoção, adição manual e importação escolhida. Inicialmente vazia. |
| Pager | Roda ativa ou apenas navega; mapas somente desta tela ou de todas. Ambas opções inicialmente desligadas. |
| Bandeja e notificações | Visíveis, ocultos, ordem, continuação/paginação e inclusão dos ocultos. |
| Interação e atividade | Permanência adicional da lente, inicialmente desligada; 1000 ms é seu valor técnico inicial. |

Os valores numéricos e enums iniciais são escolhas técnicas da implementação.
Preferências já salvas nesta instância prevalecem. As páginas usam o KConfig nativo
do applet no perfil; não escrevem seleção global de tema, MIME padrão, configurações
de outros widgets ou de outros usuários. [PREFERENCES.md](PREFERENCES.md) contém o
mapeamento técnico das chaves.

## X11, Wayland e limites práticos

TaskManager, pager, bandeja e comandos de sessão usam os serviços nativos KDE.
Organização de janelas foi exercitada isoladamente em KWin X11 e Wayland. O helper
abre um script KWin temporário no barramento da mesma sessão, confere identidades,
capacidades e destino, observa o resultado e descarrega o script. Exige os bindings
Qt da distribuição e o serviço de scripting acessível; falha/indisponibilidade é
reportada, sem promessa de sucesso quando o compositor a recusa.

No X11, janelas usam seu WId; no Wayland, o ID interno conhecido pelo KWin. Forçar
encerramento depende também de `pidfd` no Linux. No X11, o PID precisa ser autenticado
pelo servidor com XRes 1.2 e libXRes/libX11; `_NET_WM_PID` sozinho não basta. No
Wayland nativo, a verificação usa o PID da conexão conhecido pelo KWin. Clientes X11
remotos sem PID local autenticado não têm encerramento forçado disponível.

Aplicativos podem recusar fechamento, alteração de tamanho ou outras operações.
As confirmações do backend descrevem o que ele observou; comandos nativos sem retorno
de conclusão são descritos como pedidos aceitos. Menus, áudio, atividades, recentes,
provedores de agenda e bandeja dependem dos recursos presentes na sessão. Os testes
privados não cobrem todos os provedores/aplicativos existentes.

O instalador de recursos e a ativação são etapas separadas, descritas no manual
de distribuição. A integração de arraste de janelas no Pager permanece adiada.
O desenho de referência e o backup congelado continuam disponíveis para comparar
a composição funcional.
