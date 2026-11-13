# Preferências DomainOS — contrato da revisão R2

As oito categorias de ferramentas e a página **Padrões do painel**, em
`contents/config/config.qml`, usam a janela de configuração
nativa do Plasma. Cada página é um `KCM.SimpleKCM`; a navegação, Aplicar, Cancelar e
o aviso de mudanças pertencem ao diálogo do Plasma. Os controles não alteram o
desenho aprovado da barra. A página de relógio permite pesquisar os fusos; não há
uma busca geral própria de preferências nesta implementação.

O esquema `contents/config/main.xml` usa `<kcfgfile name=""/>` e o grupo `General`.
Assim, `Plasmoid.configuration` é o `KConfigPropertyMap` da instância do applet,
armazenado pelo Plasma no perfil do usuário. Não há arquivo global novo, alteração
de MIME padrão, sincronização com outro painel, nem armazenamento paralelo em JSON.

## Edição e alcance

As páginas editam somente suas propriedades `cfg_*`. Aplicar copia as propriedades
pertencentes à página para o mapa nativo e chama `writeConfig()`. Descartar uma edição
recarrega os valores salvos. Não existe gravação de configurações a cada clique,
movimento do mouse ou amostra de telemetria. Comandos de janelas já executados fora
da configuração não são revertidos por Descartar.

Cada página de ferramenta declara somente as chaves que possui. Isso evita que salvar uma página
reescreva valores antigos de páginas diferentes. O diálogo Plasma 6.3.5 observado
injeta todas as chaves do applet, inclusive acompanhantes `*Default`, em cada página
e registra avisos sobre propriedades que não pertencem àquela página. O carregamento
e o botão Aplicar funcionam; esses avisos do mecanismo nativo não justificam declarar
propriedades alheias e ampliar o escopo da gravação. Os relatórios distinguem esses
avisos de erros de tipo, referência e loops de binding.

As áreas de trabalho são objetos reais da sessão KDE: criar, remover e renomear são
comandos explícitos no Pager, não preferências acionadas por Aplicar. A central não
impõe os nomes Work/Procrastination às áreas existentes. A página de sessão e ajuda
explica os comandos disponíveis; não oferece opções de hibernação, correio ou arraste
que o backend não tenha confirmado.

## Restaurar padrões

Cada uma das oito categorias tem **Restaurar esta categoria** no rodapé. O botão
prepara somente as preferências daquela página e fica desabilitado quando já estão
nos padrões. A página **Padrões do painel** contém **Restaurar todos os padrões**,
que prepara as preferências de todas as categorias desta instância, incluindo
fixados e comandos personalizados. A gaveta mantém seu acesso permanente às
preferências mesmo quando a lista de fixados volta a ficar vazia.

Os dois controles editam somente o rascunho: **Aplicar** salva; **Descartar** conserva
os valores anteriores. Os valores vêm dos campos nativos `<chave>Default` do mesmo
`KConfigPropertyMap`, sem uma segunda tabela de valores iniciais. As listas são
copiadas e todos os defaults são validados antes de alterar a página. A página de
reset geral declara deliberadamente todas as chaves do schema; as categorias de
ferramentas continuam com seus escopos separados.

Restaurar preferências não recria desktops, não reorganiza janelas e não redefine
outras instâncias. Os comandos e a lista de aplicativos próprios desta instância
voltam aos valores iniciais somente quando a restauração é aplicada.

## Esquema e valores iniciais

Valores numéricos, escopos e enums herdados dos controladores são padrões técnicos
para uma nova instância. Não são apresentados como decisões numéricas do usuário.
Preferências já salvas na mesma instância prevalecem sobre estes valores.

| Página | Chaves | Valor técnico inicial / contrato |
| --- | --- | --- |
| Relógio e calendário | `timeZones` | `Local,UTC`; consulta, sem alterar fuso do sistema |
| Relógio e calendário | `calendarPlugins` | Lista vazia; só provedores explicitamente escolhidos |
| Monitor e gr_osview | `instrumentMetric` | `network`; alternativas `cpu`, `memory`, `disk`, `custom` |
| Monitor e gr_osview | `networkInterface` | `all`; Rx/Tx simultâneos para a interface escolhida |
| Monitor e gr_osview | `customSensorId`, `customSecondarySensorId` | Vazios; IDs reais do KSystemStats, segundo opcional |
| Monitor e gr_osview | `instrumentSampleInterval` | 1000 ms; faixa técnica da UI e do controlador: 1000–60000 ms |
| Monitor e gr_osview | `instrumentHistoryLength` | 60 amostras; faixa técnica da UI: 10–1000 |
| Correio e comandos | `mailClient` | Vazio: resolver cliente configurado para mailto; Thunderbird se não houver cliente |
| Correio e comandos | `mailCountsEnabled` | `false`; contagem real opcional, exige integrador do cliente disponível |
| Correio e comandos | `terminalCommand` | Vazio: terminal preferido do KDE; Konsole se ausente |
| Iconbox | `tasksOnlyCurrentDesktop`, `tasksOnlyCurrentScreen`, `tasksOnlyCurrentActivity` | `true`, `false`, `true` |
| Iconbox | `tasksGroupingMode` | 1: por aplicativo; 0: sem agrupamento |
| Iconbox | `tasksOnlyGroupWhenFull` | `true` |
| Iconbox | `tasksSortMode` | 1: manual; enums nativos 0: nenhuma, 2: alfabética, 3: desktop, 4: atividade, 5: última ativação |
| Iconbox | `middleClickAction` | 2: nova instância; enum anterior 0: nenhuma, 1: fechar, 3: minimizar/restaurar, 4: agrupamento, 5: trazer para área atual |
| Iconbox | `wheelEnabled`, `iconboxWheelActivates`, `wheelSkipMinimized` | `true`, `false`, `true`: navegar pelos itens; ativação pela roda é opcional, e só nesse modo se aplica pular minimizadas |
| Iconbox | `interactiveMute`, `unhideOnAttention` | `true`: silenciar pelo indicador e mostrar painel oculto quando há atenção; configuráveis por instância |
| Iconbox | `highlightWindows` | `false`: destaque do compositor opcional ao passar o mouse nos ícones e nos títulos individuais de um grupo; sair do item cancela o destaque |
| Iconbox | `iconboxWindowThumbnails` | `false`; prévias nativas ao passar o mouse, carregadas sob demanda |
| Iconbox | `iconboxHintsEnabled` | `true`; título da janela ou lista numerada do grupo, sem captura |
| Iconbox | `tasksFilterMode` | `normal`; alternativas `minimized`, `automatic` |
| Iconbox | `tasksAutomaticThreshold` | **−1: não escolhido**; modo automático indisponível até escolher L ≥ 0 |
| Iconbox | `tasksGroupingAppIdBlacklist`, `tasksGroupingLauncherUrlBlacklist` | Listas vazias; exclusões próprias de agrupamento |
| Aplicativos fixados | `pinnedApplications` | Lista vazia; Desktop IDs próprios, independente dos favoritos do menu |
| Aplicativos fixados | `applicationsMenuStyle` | `domainos`; alternativa `kde` utiliza a interface nativa instalada do Menu de aplicativos |
| Compatibilidade do menu KDE | `showIconsRootLevel`, `alignResultsToBottom` | `true`, `false`; valores consumidos pela representação nativa do KDE |
| Pager | `pagerWheelActivates`, `pagerCurrentScreen` | `false`, `false`; navegar sem ativar por padrão |
| Bandeja | `trayVisibleItems`, `trayHiddenItems`, `trayOrder` | Listas vazias: preservar política nativa da bandeja desta instância |
| Bandeja | `trayIncludeHiddenInOverflow` | `false`; ▶ contém os visíveis excedentes |
| Bandeja | `trayOverflowMode` | `continuation`; paginar se não couber; `pagination` é alternativa explícita |
| Interação e atividade | `keepActivityLight` | `false` |
| Interação e atividade | `barHintsEnabled` | `false`; dicas nos botões e itens da bandeja desta barra |
| Interação e atividade | `activityLightMilliseconds` | 1000 ms; só eficaz com a opção acima; faixa técnica: 0–60000 ms |
| Interna | `configurationSchemaVersion` | 1; identifica o esquema atual, sem converter outro perfil |

O intervalo do monitor vale para telemetria. Relógio e consulta de fusos conservam
a fonte temporal de 1000 ms, mesmo que a amostragem dos sensores seja mais lenta.
Valores antigos abaixo de 1000 ms são limitados a 1000 ms pelo controlador;
o diagnóstico distingue intervalo pedido e efetivo.

O limite superior de L na UI é técnico (1000000), não capacidade máxima de tarefas.
N é contado pelo controlador antes de filtrar minimização e agrupamento. `N > L`
habilita a apresentação de minimizadas; `N ≤ L` volta ao normal. Nenhuma janela é
minimizada ao aplicar a preferência. Se um perfil externo contiver `automatic` e L
ainda indefinido, o controlador relata a escolha pendente e usa a apresentação normal.

Cliente de correio é um Desktop ID como `org.mozilla.thunderbird.desktop`, não comando.
Entradas inválidas não substituem o valor válido em edição. O terminal recebe executável
e argumentos sem shell; pipes/redirecionamentos não são interpretados. Ambos valem
somente para os botões desta instância, sem escrever em `kdeglobals` ou MIME global.

## Agenda, sensores e bandeja

Abrir a página de calendário enumera apenas metadados de provedores instalados. Seu
`EventPluginsManager` mantém `enabledPlugins: []`. Escolher um checkbox edita a lista
local; os provedores selecionados só são ativados pelo calendário funcional depois de
Aplicar e ao abrir esse calendário. A página não cria contas nem lê eventos por dedução.

Cada provedor selecionado com configuração própria acrescenta sua página nativa
à navegação. **Feriados** permite escolher regiões oferecidas pelo KHolidays;
fontes PIM continuam opcionais e separadas. As regiões são configurações do
provedor no perfil do usuário; não pertencem ao grupo `General` do painel.
Restaurar os padrões do painel limpa sua lista de provedores, preservando a
seleção de regiões do provedor.

A lista de clientes de correio usa metadados dos Desktop Entries instalados.
Escolher um cliente não muda o padrão do KDE. A contagem começa desligada; quando
habilitada, ausência do integrador ou cliente sem fonte aparece como indisponível.
Zero só aparece quando uma fonte disponível informa zero. A integração opcional
do Thunderbird tem instalador separado e não modifica perfis/contas existentes.

Sensores customizados exigem IDs reais. Um ID inexistente é indisponibilidade, não zero.
A amostragem é limitada pela assinatura nativa; não introduz timer de clique/repaint.
O gráfico continua abrindo o componente gr_osview existente.

IDs de bandeja são `pluginName` para plasmoids e `Id` para StatusNotifierItems.
Títulos traduzidos não são identidades. A composição fornece seu snapshot real
`availableItems: [{id,title,type,hidden,status}]` pela ação interna somente de leitura
`domainos-tray-items`. A propriedade string `itemsJson` atravessa os dois motores
QML do applet e do ConfigView sem compartilhar objetos da bandeja. A página mostra
os títulos reais para escolher a política individual; não instancia outro provedor.
Essa mesma lista permite mover os itens para cima ou para baixo pelo nome. A ordem
fica no rascunho até Aplicar, quando os seis primeiros itens visíveis ocupam a
bandeja e os excedentes continuam na mesma sequência na ▶. Descartar conserva a
ordem salva. Um item temporariamente indisponível continua na lista de organização
e conserva sua posição para quando retornar. Mover itens não altera sua política
de visibilidade nem a ordem de outra instância.

Se o snapshot estiver indisponível, conserva os campos explícitos de IDs. Listas visível/oculta não
aceitam o mesmo item simultaneamente. Aplicar encaminha a política apenas ao
containment da bandeja pertencente a esta instância; não altera provedores globais.

## Importação explícita de pins

`ConfigApplications.qml` não consulta listas de outro painel ao ser criada.
“Escolher fonte para importar…” chama `contents/code/pin_import.py` com `origins`,
apresentando plugin e identificação containment/applet do próprio perfil. “Importar
fonte selecionada” chama `source` somente para uma origem dessa listagem. O helper
lê o perfil, não o escreve. Desktop IDs válidos são acrescentados, sem duplicados,
à edição da gaveta; Aplicar salva a gaveta e Descartar mantém a lista anterior.

É possível fornecer uma lista manual de Desktop IDs, ordenar e retirar pins. Metadados
de título vêm do `Kicker.FavoritesModel` em memória, sem usar o armazenamento de favoritos
do menu. Um aplicativo ausente continua removível; não vira uma operação fictícia.

## Wiring da composição

“Preferências do painel…” é um item permanente no início da gaveta. Não integra
`pinnedApplications`, portanto limpar, importar, remover ou ordenar os pins nunca
o elimina. Abaixo ficam os pins próprios; uma seção separada acompanha os
favoritos e a ordem do menu Applications nativo. Essa apresentação sincronizada
não transforma os favoritos em `pinnedApplications` nem os remove ao resetar
essa chave. Seu comando abre a central da própria instância. A interface do menu
é escolhida na página Aplicativos fixados; a busca do menu DomainOS usa o provedor
nativo de aplicativos do KRunner e abrange todas as categorias, mesmo depois de
navegar em uma categoria.

Na página Iconbox, “Títulos e lista do grupo” é o padrão. “Miniaturas de janelas”
substitui a dica de texto por prévias nativas; “Nenhuma dica” desliga ambas.
São duas chaves booleanas: miniaturas têm prioridade se um perfil externo ativar
as duas. As dicas dos demais botões e da bandeja ficam em Interação e atividade,
desligadas por padrão e independentes da escolha do Iconbox.

O título textual individual só aparece quando a legenda está abreviada; um grupo
mantém a lista ordenada dos títulos que a célula não mostra. No seletor de membros,
nomes completos não repetem dicas. Nomes cortados aguardam o intervalo de tooltip
do sistema. As prévias ficam fora da lista, preferencialmente acima dela, e fecham
ao sair lateralmente. A legenda da própria prévia só acrescenta uma dica quando
estiver cortada, depois do mesmo intervalo, dentro da área da imagem.

O root do applet passa `Plasmoid.configuration` ao `DomainOSRuntime.settings` e usa
a ação própria `domainos-configure-panel` para pedir
`containment.configureRequested(Plasmoid)`. O item permanente da gaveta aciona
diretamente essa QAction, sem consultar a chave genérica `configure`.
O wrapper SystemTray nativo encaminhava sua ação ao containment interno da bandeja,
cujo esquema não é o do DomainOS. Este pedido abre a central para a instância correta;
a ação Configure do containment interno permanece intacta. O acesso permanente
à central fica na gaveta de fixados, sem abrir preferências ao ativar o painel.
As páginas não instanciam uma
segunda composição funcional só para editar preferências.

| Destino | Mapeamento |
| --- | --- |
| `DomainOSInstruments` | `timeZones`, `calendarPlugins`, `metric ← instrumentMetric`, `networkInterface`, sensores custom; `sampleInterval ← instrumentSampleInterval`, `historyLength ← instrumentHistoryLength` |
| `DomainOSCommands` | `settings.mailClient`, `settings.terminalCommand` |
| `DomainOSTasks` | `onlyCurrentDesktop/Screen/Activity`, `groupingMode`, `onlyGroupWhenFull`, `sortMode`, `filterMode`, `automaticThreshold`, blacklists ← respectivas chaves `tasks*` |
| `DomainOSIconbox` | `middleClickAction`, `wheelEnabled`, `iconboxWheelActivates`, `wheelSkipMinimized`, `interactiveMute`, `highlightWindows`, `thumbnailsEnabled ← iconboxWindowThumbnails`; arraste manual usa a ordenação do TasksModel, sem alterar geometrias de janelas |
| `DomainOSApplications` | `settings.pinnedApplications`, `settings.applicationsMenuStyle`; pedidos de pin atualizam somente a lista; a alternativa KDE lê os dois valores de compatibilidade |
| `DomainOSPager` | `wheelActivatesDesktop ← pagerWheelActivates`; `showOnlyCurrentScreen ← pagerCurrentScreen` |
| Adaptador da bandeja | As cinco chaves `tray*` acima; snapshot nativo pela QAction desta instância |
| `DomainOSActivity` | `keepLightAfterCompletion ← keepActivityLight`; `extraLightMilliseconds ← activityLightMilliseconds` |

## Verificação reproduzível

```sh
python3 plasma/tools/testar-domainos-preferencias.py --saida /tmp/irix-domainos-preferencias-ensaio
python3 plasma/tools/testar-domainos-preferencias-bandeja.py --saida /tmp/irix-domainos-preferencias-bandeja-ensaio
```

O ensaio usa Plasma/Xvfb, D-Bus e diretórios HOME/XDG privados. Carrega as oito páginas,
confere edição/descartar/aplicar pelo mapa KConfig real, faz importação com cliques de
ponteiro reais e cria outro applet nativo do mesmo plugin com ID distinto. Abre também
o `ConfigView` nativo pela ação de configurar, verifica suas oito categorias e clica
no checkbox de Manaus e no Aplicar do diálogo real antes de reiniciar o host para
conferir persistência. O teste de Descartar usa recarga pela API e não afirma um
clique nativo nesse comando; os demais cenários de aplicar mapeiam `cfg_*` e chamam
o KConfig nativo, além do cenário separado de Aplicar com o botão real.

O plasmawindowed restaura seu layout de containments ao reiniciar. Depois do teste
com duas instâncias, o ensaio retira somente esse layout descartável do host de
teste para evitar que ele restaure a instância sem uma janela. As preferências em
`plasmawindowedrc` permanecem intactas e são a fonte da prova de persistência.

O segundo ensaio carrega a composição de produção e seus provedores reais. Confere
que Configure abre o applet DomainOS, que a lista e os títulos chegam ao ConfigView,
seleciona a política de volume pelo controle real, clica no Aplicar nativo e verifica
que somente depois desse clique a bandeja pertencente à instância recebe a política.

Esses ensaios anteriores abrangiam oito categorias. A revisão do reset acrescenta
a nona página, **Padrões do painel**, e um ensaio próprio:

```sh
python3 plasma/tools/testar-domainos-padroes.py --saida /tmp/irix-domainos-padroes-ensaio
```

Esse ensaio usa cliques reais em reset, Aplicar e Descartar, verifica as 40 entradas
do schema e restaura duas instâncias com suas identidades após reiniciar o host.
As 31 verificações funcionais passaram. A verificação de ausência de erros QML
registra separadamente os TypeErrors do `PromptDialog.qml` instalado, reproduzidos
também nas páginas antigas R7 sem reset. O relatório de interação em
`docs/VALIDACAO-DOMAINOS-INTERACAO-2026-10-09.md` contém a prova de baseline; os logs
não são filtrados nem o SDK global modificado.

Os números 3 e 1750 ms nos cenários são dados de teste, não padrões escolhidos pelo
usuário. O relatório e capturas ficam na saída solicitada em `/tmp`. Hashes comprovam
que fontes da produção, preferências reais e a origem de launchers permanecem intactas.
O ensaio não substitui validar todos os efeitos na composição funcional integrada.
