# Fila de revisão visual DomainOS SR10.4

A revisão compara os controles do projeto com o Trash Can e outros componentes
nativos do Domain/OS SR10.4 com HP VUE 2.01. A captura apresentada pelo usuário
mostra diferenças tanto no GTK3 quanto no System Settings. O andamento geral
do projeto não representa a conclusão desta revisão visual.

Atualização: 2026-10-10. O levantamento e a
[especificação comum](DOMAINOS-REGRAS-ROLAGEM.md) precedem as adaptações.
A primeira família em revisão é GTK3. O LED já tinha correção em teste final;
esse ensaio funcional não abre outra família visual.

## Regra de execução

Ler o [índice de regras](DOMAINOS-INDICE-REGRAS.md) e a
[política de cores dinâmicas](DOMAINOS-REGRAS-CORES.md). Nenhuma correção desta
fila deve fixar a paleta histórica nos controles. A regra inclui estados
desabilitados e sem foco; as únicas exceções de sinal são LED/Pager com contraste.

Consultar esta fila a cada interação de trabalho DomainOS. Registrar o novo
relato antes de alterar o código. Ler a regra comum, traduzir para o mecanismo
de desenho da família ativa e comparar depois. Trabalhar em uma família por vez, documentando
referência, diferença, correção e comparação final. Manter o relato original e
o resultado dos ensaios que falharam; substituir o estado atual, sem apagar as
evidências anteriores.

Uma etapa passa a concluída quando o controle nativo corrigido foi comparado com
a referência nas duas orientações e nos estados aplicáveis. Uma captura inicial,
um teste que verifica o código ou o número de testes aprovados não encerra a
comparação visual. Avançar tecnicamente não exige uma nova autorização do usuário.

## Referência histórica

- Sistema: Domain/OS **SR10.4**, HP VUE **2.01**, Apollo DN3500 emulado no MAME.
- Referência principal: Trash Can real, com barras horizontal e vertical e o
  encontro no canto inferior direito. A VM existente permanece aberta.
- Registrar separadamente as métricas da área cliente, dos widgets Motif e da
  decoração do vuewm. A faixa de comandos Apollo pertence ao Display Manager.
- Não usar SR10.4.1, SR14.4 ou outra versão para preencher lacunas.
- Fonte Motif é apoio para interpretar iluminação, sombras e interação. A versão
  exata da biblioteca da VM ainda precisa ser confirmada antes de atribuir-lhe
  um código-fonte específico.
- Preservar a paleta escolhida no KDE. As exceções autorizadas são o LED e a luz
  do Pager, com alternativa quando o amarelo perde contraste. Não modificar a
  luz do Pager nesta revisão.

## Sequência e estado

| Ordem | Família ou componente | Estado atual | Escopo da etapa |
| --- | --- | --- | --- |
| 0 | Regras comuns | Contrato documentado; origens explícitas | Recursos reais via FTP e xrdb, medidas do Trash Can e estados observados; não atribuir defaults C ainda desconhecidos. |
| 1 | GTK3 | Revisão visual em andamento | Iluminação, geometria e continuidade de cores nos limites verificadas; moldura principal da tabela preenchida continua pendente. |
| 2 | GTK2 | Na fila | Comparar controles nativos e assets próprios; não herdar a conclusão do GTK3. |
| 3 | GTK4 | Na fila | Comparar barras e limites da API, inclusive disponibilidade de botões de seta; registrar a adaptação possível. |
| 4 | GTK1 | Na fila | Confirmar suporte e presença de aplicativo real antes de afirmar equivalência. |
| 5 | Qt Widgets e Kvantum | Na fila com defeito relatado | Seta inferior, ambas as orientações, botão, relevo e encaixe; verificar tema fixo e variante que segue a paleta. |
| 6 | Qt Quick no KDE | Na fila com defeito relatado | Reproduzir no painel esquerdo e no conteúdo do System Settings; identificar o componente que desenha a seta antes de corrigir. |
| 7 | Plasma Style | Na fila | Verificar os controles reais do Plasma, separando widgets SVG de controles Qt Quick. |
| 8 | Chapa do painel | Relato anterior na fila | Escala, iluminação e borrão junto ao LED e ao ícone de aplicações; comparar pixels nativos e escala efetiva no Xephyr. |
| 9 | Revisão conjunta | Na fila | Abrir a suíte atualizada, trocar esquemas de cores e confirmar que uma correção não regrediu outra família. |

“GTK” é o conjunto de versões acima, não um resultado adicional presumido.
Qt, Qt Quick, Kvantum e Plasma Style não são tratados como um único desenho.
LED e espera do painel: correção funcional verificada na prévia R13 X11, independente da
sequência de famílias de rolagem acima.

## Comparação obrigatória de cada família

| Parte | O que medir e observar |
| --- | --- |
| Seta | Contorno, orientação, centralidade, área ocupada, luz e sombra com a iluminação do original. |
| Botão de seta | Largura e altura, afastamento do trilho, normal, pressionado, solto e desabilitado. |
| Trilho | Largura, cor do fundo, bordas e recessão; não confundir relevo do trilho com o do thumb. |
| Thumb | Comprimento, largura útil, afastamento das bordas, iluminação e reação ao arraste. |
| Encaixe | Borda entre a barra e o conteúdo, continuidade dos cantos e do relevo da área rolável. |
| Canto entre barras | Espaço reservado, borda e ausência de corte ou sobreposição da seta inferior e da seta direita. |
| Escala | Comparação em pixels nativos e escala proporcional documentada; não julgar uma imagem interpolada como original. |
| Cores | Paleta DomainOS, paleta clara neutra e paleta escura; sem prender a geometria a cores azuis estáticas. |
| Interação | Clique, manter pressionado, soltar, arrastar e atingir os limites; referência histórica separada do comportamento de KDE. |

## Resultados e pendências registradas

### LED e espera

O QML acompanha os pedidos em andamento e os registros nativos de inicialização
do gerenciador de tarefas. A alternância é de 500 ms por fase. O cursor usa a
forma de espera do pacote de cursores escolhido. O tempo extra após o fim fica
desligado por padrão e não atrasa comandos.

O helper dos quatro lançamentos diretos passou a publicar um pedido KIO por um
Desktop Entry temporário, preservando argumentos e diretório atual. Os testes
unitários passaram 17/17 e o teste nativo do helper passou 17/17. O clique real
no Terminal da prévia R13 passou 12/12: token QML, helper, inicialização nativa
do TaskManager, alternância da luz e cursor de espera até a janela mapear.
O semiperíodo observado teve mediana de 516 ms; o temporizador configurado é
500 ms. Luz e cursor retornaram ao normal sem cauda. O comando Terminal privado
foi restaurado para `/usr/bin/xterm`, e o cliente temporário encerrou sozinho.

Limites: a aceitação de um lançamento não comprova que a aplicação terminou de
abrir. O modelo do KDE pode omitir inicialização correspondente a uma janela já
aberta. Não há heurística de título/PID nem tempo fictício para encobrir essa
limitação. A prova nativa obtida é X11; Wayland não foi validado nesta etapa.

### GTK3

A seta inferior usava a rotação de uma imagem já sombreada. A correção orienta
primeiro o contorno e depois aplica a iluminação para cada direção. Após a
revisão de geometria, os ensaios nativos GTK3 passaram 620/620 e os de desenho
e integridade, 18/18. Esses ensaios cobrem funcionamento e os estados GTK;
não encerram a comparação de todo o conjunto com o Trash Can.

A revisão do botão, trilho, thumb, encaixe e canto continua aberta. Os recursos
GTK2, GTK4 e Kvantum não foram considerados corrigidos por esses resultados.

A [captura nativa do Trash Can](referencias/domainos-sr104/trash-can-normal.png)
e suas [métricas](referencias/domainos-sr104/TRASH-CAN-METRICAS.json) mostram barras
de 15 pixels, setas e thumb de 11 pixels, relevo de 2 pixels e intervalo de
4 pixels até a moldura do conteúdo. O GTK3 tinha barras de 16 pixels, setas de
12 pixels, espaçamento zero e continuidade diferente do relevo junto às setas. Essa
diferença reabre a geometria do conjunto mesmo depois da correção da iluminação.

O original também tem relevos separados no trilho e no thumb. A análise inicial
os interpretou como camadas adicionais no GTK3; a comparação ampliada corrigiu
essa interpretação. O ajuste considera largura, alinhamento e continuidade,
sem eliminar um relevo que existe no original.

A captura inicial é do estado normal de um Trash Can vazio. O ensaio separado
de manter a seta inferior pressionada confirmou a inversão de luz/sombra em
53 pixels e o retorno ao desenho normal ao soltar. As quatro setas normais e
o triângulo inferior pressionado coincidem com os recortes nativos. Arraste,
desabilitado e outras direções pressionadas ainda não foram confirmados na VM.

As barras GTK3 usam 15 pixels, setas e thumb de 11, relevo de 2, intervalo
seta/thumb de 1 e afastamento do conteúdo de 4. GTK2, GTK4 e Kvantum foram
preservados nesta etapa. A moldura principal de GtkTreeView preenchida continua
pendente: esse widget não pinta o frame principal pelo CSS usado. A tentativa
de sombra global pintou também as células e foi descartada. Não declarar a
família concluída nem avançar para GTK2 antes de resolver ou delimitar essa
adaptação.
O [relatório GTK3](DOMAINOS-COMPARACAO-ROLAGEM-GTK3.md) registra antes/depois,
provas e essa pendência.

### KDE e Qt

O usuário apontou a seta inferior do System Settings nesta interação. O defeito
está registrado para reprodução nativa e identificação do componente responsável.
Não atribuir automaticamente a seta ao Kvantum: o System Settings pode apresentar
controles de famílias diferentes na mesma janela.

## Arquivos de partida das etapas seguintes

Este mapa localiza as implementações sem declarar sua aparência validada.

| Etapa | Arquivos a consultar |
| --- | --- |
| GTK2 | `gtk/DomainOS-SR10-4*/gtk-2.0/gtkrc`, `tools/domainos_motif_art.py`, `tools/gtk2_domainos_palette.py`. |
| GTK4 | `gtk/DomainOS-SR10-4*/gtk-4.0/gtk.css`, CSS comum dos mesmos temas, `tools/gtk4_palette_runtime.py`. |
| GTK1 | `gtk/Irixium/gtk-1.2/gtkrc`; não há variante DomainOS completa demonstrada. |
| Qt Widgets e Kvantum | `kvantum/DomainOS-SR10-4/`, `tools/kvantum_domainos_palette.py`, `tools/kvantum_palette_runtime.py`. |
| Qt Quick no KDE | Aplicativo System Settings e estilo carregado em sua sessão; identificar o QML e os papéis de cores efetivos. |
| Plasma Style | `plasma/IrixClassicDomainOS/widgets/scrollbar.svg` e o gerador de desenho do tema. |

## Evidências e continuidade

A [matriz de validação](DOMAINOS-MATRIZ-VALIDACAO-R2.md) conserva o histórico dos
ensaios. As [decisões consolidadas](DOMAINOS-DECISOES-CONSOLIDADAS.md) definem as
preferências e exceções autorizadas. Os recibos privados preservam os detalhes
de processos e da sessão de teste; os documentos públicos não dependem de um
diretório pessoal para executar o instalador.

O gerador GTK3 já consome o contrato único. A conexão preservou 759 arquivos
de desenho/CSS e passou quatro testes focados. A prévia R13 abriu com 18/18
verificações iniciais e permanece disponível para teste; os atalhos temporários
apontam para essa revisão. O snapshot foi congelado antes dos resultados finais
registrados neste documento; não foi reescrito para alterar o histórico do ensaio.

### Cores das setas e pranchetas — revisão de 2026-10-10

O [diagnóstico de cores](DOMAINOS-CORES-SETAS-REVISAO.md) reutilizou a captura
R13. Baixo/direita GTK3 coincidem com a paleta normal da VM; cima/esquerda
coincidem com os papéis desabilitados do KDE, que diferem da referência normal.
A geometria confirmada não encerra a regra de cores desse estado. O estado
realmente insensível no Motif SR10.4 ainda precisa de referência ou de uma
política explícita de adaptação. Esse achado não explica por si todos os relatos
do usuário nem reabre as provas normais que permanecem válidas.

As [duas pranchetas](DOMAINOS-CHECKLISTS-REVISAO.md) agrupam o projeto e esta
revisão em dez itens cada. Ler suas respostas salvas ao retomar; manter prova
técnica e aprovação manual separadas. Repetir um ensaio somente por entrada
alterada, falha ou dúvida ainda não coberta.

### Continuidade de cores nos limites GTK3 — aplicada

O contrato distingue a seta bloqueada pelo limite de um scrollbar inteiramente
insensível. A primeira acompanha os papéis KDE atuais do pai; o clique permanece
bloqueado. A segunda conserva os papéis insensíveis. Essa política de adaptação
foi definida antes da alteração do gerador, a partir da continuidade das quatro
setas normais do Trash Can; não substitui a pesquisa do verdadeiro estado
`XtSensitive=False` da VM.

O ensaio focado em GTK3 real passou 468/468 verificações nas paletas azul, cinza,
escura e amarela, com limites, falta de foco, contêiner insensível e 64 cliques
bloqueados. As oito células azuis dos dois limites coincidem com os recortes
normais da VM. Os snapshots de papéis KDE têm proveniência e hashes conferidos;
a prova não cobre atualização da paleta ao vivo. As três identidades têm CSS
idêntico; 757 arquivos não afetados permaneceram iguais.

O [resultado de cores](DOMAINOS-CORES-SETAS-REVISAO.md) preserva antes/depois e
os limites da prova. A R13 permanece congelada; a moldura principal de
GtkTreeView preenchida é o próximo item da mesma família. A comparação de
Qt/System Settings e a chapa continuam na fila. Nenhuma família foi declarada
concluída por este resultado, e nenhuma resposta manual foi preenchida pela IA.

### Laboratório Motif solicitado pelo usuário — etapa ativa

O usuário passa a regular o desenho em uma ferramenta reutilizável C99/MVC.
A [especificação do laboratório](DOMAINOS-LABORATORIO-TEMAS.md) integra o goal.
O contrato e as provas históricas existentes permanecem preservados; não
traduzir automaticamente receitas novas para todos os temas canônicos.

| Grupo de entrega | Situação desta etapa |
| --- | --- |
| Modelo e projetos | Importação validada, receitas independentes e salvamento atômico; 689 verificações offline. |
| Interface Motif | V1 preservada; V2 aberta no lsi, com ferramentas, montagem e código em três painéis. |
| Plataformas | Catálogo registra disponibilidade real; GTK1/GTK5 ausentes, demais galerias nativas identificadas. |
| Cores do preview | Seleção isolada; leitor KColorScheme reproduz a política de estados do GTKConfig, sem escrever no KDE. |
| Montagem GTK3 | 16 widgets nativos mantidos após atualizações; XEmbed, foco e prévia separada conferidos. |
| Estados e gestos | Quatro estados e deslocamento exato 24 × 18 comprovados; estados forçados não são prova histórica. |
| Atualização | Cena aplicada separada dos rascunhos; manual ou automático com intervalo configurável. |
| Código e exportação | Trecho por controle/estado; GTK3 traduzido, demais adaptadores explicitamente pendentes. |
| Referência e pipeta | PNG 1:1; medição X11 com origem e teste anterior preservado no seu escopo. |
| Avaliação e continuidade | Respostas parciais preservadas; avaliação do usuário e próxima família permanecem pendentes. |

Não inferir aprovação dos 18 itens sem resposta. Não reabrir os ensaios de cores
das setas normais já válidos. A prioridade seguinte, após a ferramenta funcionar,
é o ajuste manual GTK3 pelo usuário, incluindo a moldura da tabela preenchida.

#### Achados da integração nativa do laboratório

- Rótulos Motif: tag de locale incorreta retornava `XmString` nulo. Corrigido
  com a regra documentada do Motif; textos reais aparecem no ensaio privado.
- XEmbed: evento de propriedade não chegava ao handler Xt, deixando o GTK3
  sem mapear e em 1 × 1. Corrigido; canvas e Plug em 740 × 410, clique e
  digitação nativos comprovados. Pedidos de tamanho recebem confirmação.
- Edição: Ctrl+seleção preserva rascunhos sem aplicar a geometria pendente.
  O arraste alterava só metade do deslocamento porque usava coordenadas do
  próprio widget móvel. A implementação agora usa coordenadas root lógicas
  estáveis e cancela ao mudar a escala; delta nativo de 24 × 18 comprovado.
  O formulário Motif oculto também deixou de participar da navegação no
  canvas GTK3; retorno de foco por Shift+Tab comprovado em ensaio nativo.
- Visibilidade: a reposição sequencial de itens em `XmEXTENDED_SELECT`
  mantinha apenas o último item. O primeiro Atualizar podia trocar a máscara
  65535 por 32768 e esconder 15 controles. A seleção em lote foi corrigida;
  lista inicial, Ctrl+seleção, Atualizar e arraste preservam os 16 itens.
- Reinício XEmbed: inscrições repetidas de um mesmo drawable no Xt sobreviviam
  ao DestroyNotify e rejeitavam o cliente substituto com XID reutilizado.
  Fonte do libXt e trace nativo confirmaram a causa. O registro agora ocorre
  uma vez; a limpeza remove somente inscrições do nosso canvas. Quatro
  notificações de embedding sucessivas e limpeza Xt comprovadas nativamente.
- Seta isolada: o widget de desenho foi substituído por botão GTK3 nativo
  compacto, com máscara sem escala e papéis da receita. CSS apenas privado;
  clique e quatro estados comprovados no ensaio nativo. Botão independente e
  stepper da barra têm contextos de paleta distintos, explicitados no trecho.

As falhas iniciais e as provas seguintes ficam preservadas por snapshot. Não
alterar a janela V1 que o usuário está avaliando para reproduzir esses achados.

#### Entrega da montagem V2

O [recibo do laboratório](review/theme-lab-v2/RESULTADO.json) reúne 14 verificações
nativas resolvidas em dois snapshots do mesmo binário. Inclui a correlação do
papel Button do Breeze Dark; o primeiro oracle usava Window por engano e o
relatório bruto foi preservado. O ensaio não declara fidelidade histórica nem
tradução das outras famílias. Oito configurações pessoais permaneceram iguais.

A V2 foi aberta na Xephyr já existente, em um diretório de projetos próprio.
A [captura da janela aberta](review/theme-lab-v2/V2-OPEN.png) foi passiva, sem
enviar cliques ou teclas. A montagem conserva pixels nativos; áreas menores
usam rolagem. A V1, a VM, o backup e as respostas parciais não foram alterados.
Próximo item: avaliação manual da ferramenta e ajuste da moldura GTK3 pelo
usuário; ampliar o catálogo e implementar os demais tradutores em etapas.

#### Reabertura solicitada pelo usuário

Em 2026-10-10, o usuário autorizou fechar as Xephyr anteriores e pediu uma nova
com a ferramenta. A sessão antiga foi encerrada por identidade conferida;
três arquivos de projeto permaneceram com os mesmos hashes. Uma sessão nova
abriu com 22/22 verificações iniciais, seguida pelo laboratório em GTK3, com
montagem de 16 controles e diretório próprio. Os perfis pessoais permaneceram
iguais na abertura. O binário da ferramenta é o mesmo da entrega V2 validada;
esta reabertura não declara uma revisão funcional nova.

#### Etapa ativa: referência Motif interativa

O usuário pediu substituir o bloco da imagem original por uma referência Motif.
Usar controles reais do Motif instalado, com receita independente e esquema de
teste dinâmico. Cliques na referência exercitam os controles; não editam a
receita GTK3. A imagem histórica deve continuar acessível separadamente.
Comparar interação, isolamento das receitas e troca de esquema antes de abrir
a revisão. Esta referência não comprova a versão da biblioteca da VM SR10.4.
Depois, retomar os parâmetros específicos dos controles GTK3 (direção da seta
e valores de faixas/indicadores), ainda não implementados.

Pedido seguinte do usuário: substituir os campos numéricos por controles de
incremento/decremento, acrescentar tamanho por componente e fazer a alteração
aparecer também na prévia separada. Implementar após concluir a referência;
preservar projetos anteriores e verificar com controles nativos nas duas prévias.

### Publicação beta e revisão da ferramenta — prioridade atual

Pedido do usuário: publicar a versão corrente para uso diário e aplicar em lsi.
Distribuição 1.1.0-beta.1, painel 0.2.12-beta.1. Não condicionar a publicação à
fidelidade integral das famílias ainda na fila. A aprovação da referência Motif
foi relatada pelo usuário, com fonte explicitamente fora da etapa atual.

Referência interativa: [recibo](review/theme-lab-motif-reference/RESULTADO.json)
com interação nativa e quatro paletas. As provas referem-se ao snapshot indicado
no recibo, anterior aos novos campos de tamanho e spin.

Próximos itens da ferramenta: validar spin/tamanhos e checkbox de prévia;
hints em todos os controles; medidas e posições comparáveis; busca no código;
execução nativa na sessão do usuário. A limitação do papel personalizado de
face de botões GTK3 continua pendente no recibo. Nenhuma resposta da prancheta
foi preenchida automaticamente.

Beta: pacote íntegro, auditoria de 40 componentes aprovada; instalação e
seleção em lsi inicialmente conferidas. KWin confirmou `domainos_sr104`, GTK2/3/4 e
Kvantum selecionados. Painel recarregado pelo serviço da própria sessão.
[Recibo](review/RELEASE-1.1.0-beta.1.json). Próximo item: revisão da ferramenta.

### Retorno sobre a beta — correção ativa

O usuário relatou cores e barra sem atualização. A seleção do tema e o restart
foram conferidos antes, mas não os RGB efetivos. Diagnóstico: o KDE recusou
reaplicar um esquema com o mesmo ID e conservou grupos antigos; a ponte GTK2
validou um journal já restaurado contra arquivos atualizados pelo instalador.
Corrigir a aplicação explícita e a retomada após restauração; conferir papéis
reais KDE/GTK/Qt e o painel carregado antes de anunciar esta correção.
A ferramenta fica temporariamente atrás desta falha de aplicação.

Correção R2 aplicada em lsi: papéis Window/Button/View e WM conferidos contra
o arquivo instalado; Qt/Kvantum e Plasma retornaram as mesmas cores efetivas;
GTK3 confirmou janela/botão/conteúdo nativos. O painel foi recarregado e manteve
os IDs 2268/2269 e altura 109; serviços ativos. A recarga recuperável passou a
incluir DomainOS e aguardar o KWin. A captura privada confirmou título inativo
ciano e ativo coral; o usuário respondeu “Sim, agora correspondem”.
[Recibo R2](review/PALETA-APLICACAO-20261010-R2.json). A confirmação se refere
às decorações nesta sessão, não à fidelidade das demais famílias.

Distribuição corretiva: suíte 1.1.0-beta.2; painel 0.2.12-beta.1 preservado,
com auxiliares de aplicação e superfície de texto GTK3 corrigidos. Reutilizar as provas dos
recursos inalterados da beta.1. p001532 não foi reaplicado nesta correção.
Próximo item: retomar spin/tamanhos, hints, medidas comparáveis, busca e execução
nativa do laboratório. O pipeline de eventos de métricas está em rascunho;
a view e o emissor nativo ainda precisam ser concluídos antes de compilar.

### Retorno Mousepad — contraste da área de texto GTK3

O usuário relatou texto branco sobre fundo quase branco no Mousepad aberto.
Etapa ativa: superfície de texto GTK3, incluindo o nó `text` do GtkTextView e
o GtkSourceView usado pelo editor. A prova R2 consultou o contexto do controle
externo; ela não comprovou o fundo efetivamente desenhado nesse nó interno.
Reproduzir com texto artificial, corrigir pelos papéis View/Text do KDE e
conferir os pixels em quatro esquemas antes da beta.2. Preservar o documento
aberto; não trocar sua preferência de realce de sintaxe nem reiniciar o editor.

Causa reproduzida com texto artificial: Mousepad 0.6.3 mapeia “none” para
GtkSourceView Classic, que define o fundo externo a partir do estilo dos números
de linha. O nó `text` transparente combinava esse fundo claro com o texto branco.
O tema agora define explicitamente o par View/Text nesse nó e Selection na
seleção. O contexto externo pode continuar indicando a cor do esquema do editor;
a prova válida é a superfície pintada. Ensaio nativo: 48 casos em quatro snapshots
KDE, dois controles e seis estados, todos com os pixels dos papéis esperados.
Escopo: texto GTK3; não comprova realce de sintaxe, fonte histórica ou outra família.
Aplicação em lsi concluída pela atualização recuperável da suíte e recarga nativa
GTK, com o Mousepad e seu documento abertos. O usuário confirmou “Sim, consigo
ler”. [Recibo R3](review/GTK3-TEXTO-20261010-R3.json). A beta.2 incorpora essa
correção; p001532 não foi alterado. Próximo item: melhorias já solicitadas do
laboratório, preservando as revisões das outras famílias na fila.
