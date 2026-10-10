# Menu de aplicativos e gaveta — contrato R2

`DomainOSApplications.qml` mantém dois conjuntos distintos: o catálogo e
favoritos nativos do Kicker e a lista `settings.pinnedApplications` da instância
DomainOS. Adicionar, retirar ou reordenar um pin emite `pinListRequested` com uma
nova lista; o controlador não escreve a configuração global nem altera tarefas,
janelas ou favoritos do menu.

O catálogo fornece categorias, aplicativos, favoritos e itens recentes pelos
provedores nativos. A busca usa `Kicker.RunnerModel` com o provedor nativo
`krunner_services`, como o menu do KDE: encontra aplicativos por nomes,
descrições e palavras-chave em todas as categorias. Navegar em uma categoria
não restringe a busca. Esvaziar o campo recupera a navegação anterior.
O clique de um resultado converte o índice filtrado para o modelo de origem
antes de chamar `trigger`, preservando o aplicativo correto. Itens com filhos
entram na categoria; o botão Voltar restaura o nível anterior. Ausência de
resultados e favoritos tem mensagem explícita.

O menu contextual de uma entrada preserva as ações fornecidas pelo Kicker e
permite adicionar/retirar favoritos. Também abre pela tecla Menu ou Shift+F10.
O menu identifica esses favoritos como favoritos KDE do usuário. A gaveta mostra
esses favoritos pelo mesmo modelo nativo, com a mesma ordem do menu Applications
DomainOS e de sua interface KDE opcional. Adições, remoções e reordenação desse
modelo aparecem na gaveta sem copiar a lista para `pinnedApplications`. Os pins
próprios continuam com sua importação explícita e suas próprias operações.

No menu DomainOS padrão, o lançamento pelo catálogo, pelos favoritos ou por uma ação contextual nativa
passa por `dispatchNative`: a lente acompanha a chamada ao provedor e seu retorno,
sem acrescentar espera ao clique. O resultado `dispatch-returned` comprova esse
retorno; não comprova que a aplicação aceitou o pedido, abriu uma janela ou terminou.
No contexto, o booleano nativo controla o fechamento do menu: `false` não significa
falha do aplicativo. Categorias e edição de favoritos não acionam a lente.

O cliente recebido em `favoritesClient` identifica a ordenação da instância.
Os membros dos favoritos nativos são compartilhados pelos menus de aplicativos
do mesmo usuário, conforme o modelo KAStats instalado; um client ID diferente
não cria uma lista privada. O contexto e a dica do botão Favoritos informam esse
alcance. Abrir o menu não acrescenta, remove ou importa favoritos.
[Implementação KDE de KAStatsFavoritesModel](https://github.com/KDE/plasma-workspace/blob/Plasma/6.3/applets/kicker/plugin/kastatsfavoritesmodel.cpp).

Os pins usam `Kicker.FavoritesModel` como resolvedor de metadados em memória
(classe nativa `SimpleFavoritesModel`). Os IDs são os IDs de armazenamento dos
serviços, como `org.kde.kate.desktop`. Acrescentar `applications:` nesse modelo
geraria uma entrada URL genérica, sem o título e ícone do serviço. O controlador
normaliza entradas recebidas para IDs e rejeita conteúdo inválido e duplicados.

`pinInfo(index)` retorna título, ícone e disponibilidade fornecidos pelo modelo.
Um serviço ausente continua na lista com indicação de indisponibilidade e pode
ser retirado, mas não pode ser lançado como se estivesse disponível. Os comandos
de ordem e remoção verificam os limites antes de solicitar a lista nova.

`launchPin(index)` solicita `commands.openApplication(desktopId)` para o serviço
selecionado. É uma solicitação de lançamento; a capacidade de criar outra janela
ou instância pertence à aplicação. Retirar o pin não fecha uma janela.

`showMenu(anchor)` e `showDrawer(anchor)` alternam entre os dois conteúdos.
Repetir o clique no mesmo botão fecha o conteúdo; um novo clique reabre.
`configureRequested` encaminha a configuração
para a instância que abriu o menu, sem escolher outro painel.

“Preferências do painel…” é o primeiro item permanente na gaveta. Não faz parte
da lista editável e não tem comandos para remover ou ordenar. Também aparece
quando nenhum aplicativo está fixado. Um separador antecede os pins da barra de
tarefas, que têm a segunda prioridade; outro separa os favoritos do KDE, na
terceira seção. Os comandos de remover/subir/descer dos pins medem 28 × 28 px,
reservando a maior parte da linha ao nome. Os favoritos não recebem esses
comandos locais: sua fonte e sua ordem são as do menu. O lançamento de um
favorito resolve novamente sua identidade no modelo antes do despacho nativo. A página Aplicativos fixados permite
escolher `applicationsMenuStyle`: `domainos` é o padrão, e `kde` carrega a
representação do Menu de aplicativos instalada pelo Plasma, sem copiar seu
desenho para o repositório. A gaveta e as preferências continuam sendo da instância
DomainOS nas duas opções.
Essa interface opcional conserva os despachos do KDE; eles não são interceptados
pela lente de atividade do menu DomainOS.

## Verificação isolada

`python3 plasma/tools/testar-domainos-aplicativos.py --saida /tmp/novo-diretorio`
executa Plasma/Kicker em Xvfb, HOME/XDG e D-Bus privados. Um
`kactivitymanagerd` descartável permite conferir favoritos reais sem tocar o
banco do usuário. Dois Desktop Entries locais representam aplicativos de teste;
o único lançamento escreve um marcador em `/tmp` e termina.

O ensaio verifica o catálogo nativo, um clique QtTest real num resultado
filtrado, títulos/ícones dos pins, ordem/remoção/limites, pin ausente, pedido de
lançamento correto, configuração da instância e botão Favoritos. Favoritos são
adicionados/retirados por cliques no menu contextual nativo, inclusive aberto
pelo teclado. Dois clientes nativos privados observam a mesma mudança, como
prevê o KDE, enquanto os pins permanecem iguais. O favorito do perfil descartável
permanece independente da lista de pins; o modelo nativo de tarefas e
seus lançadores permanecem iguais. Os hashes das preferências reais são
comparados antes e depois. A abertura de aplicações reais e a importação de
fixados existentes são verificações separadas da integração.

Acrescente `--atividade` para verificar a lente de produção com os lançamentos
nativos do catálogo, de um favorito e de uma Desktop Action. O ensaio observa
início/fim síncronos e a permanência adicional opcional após o retorno. Os casos
de exceção e retorno `false` usam modelos duplos declarados; os lançamentos positivos
usam Kicker e Desktop Entries privados reais. Os dois modos usam KWin e um runtime
temporário curto, removido ao encerrar, para não ultrapassar os limites de sockets
locais do KIO.
