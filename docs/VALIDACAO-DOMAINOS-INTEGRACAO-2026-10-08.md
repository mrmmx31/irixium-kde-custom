# Validação da integração DomainOS — 2026-10-08

## Instalação e restauração por usuário

A composição funcional 0.2.0 e sua ajuda foram instaladas e restauradas pelo
`tools/install_suite.py`, como usuário normal (UID 1000), exclusivamente em
diretórios novos sob `/tmp/irix-domainos-instalacao-20261008-r4`.
**34/34 verificações passaram nas fontes daquele ensaio**, antes da correção
posterior de unidades/amostragem dos instrumentos descrita abaixo. O ensaio r2 passou 37/37;
seus três checks adicionais eram a restauração/reinstalação condicionais porque
uma fonte mudou durante a cópia. Nenhuma fonte mudou no ensaio final. As execuções
anteriores são históricas e não são somadas ao resultado final. A rodada r3,
anterior à última correção das âncoras dos popups, também passou 34/34; ela não
é a prova da árvore final.

O ambiente forneceu HOME, XDG_DATA_HOME, XDG_CONFIG_HOME, XDG_STATE_HOME,
XDG_CACHE_HOME e XDG_RUNTIME_DIR privados, com permissões 0700. As raízes de
compatibilidade de cursores/GTK também foram privadas. DISPLAY, WAYLAND_DISPLAY
e DBUS_SESSION_BUS_ADDRESS não foram herdados. Todas as chamadas utilizaram
`--sem-cache`, `--cursor-compat-root` e `--gtk-compat-root`; não houve aplicação de
perfil, criação de painel nem acesso a uma sessão gráfica ativa.

| Etapa | Evidência verificada |
| --- | --- |
| `--verificar` | Dependências e fontes verificadas; recursos, preferências e ausência de recibo preservados. |
| Instalar | 35 destinos: 30 componentes do catálogo e cinco cópias de compatibilidade. Todos os destinos coincidiram com os hashes pós-instalação do recibo; todos os backups coincidiram com os hashes anteriores. |
| Repetir instalação | Nenhuma mudança de conteúdo, novo backup ou alteração de recibo: instalação idempotente. |
| `--restaurar --verificar` | Recursos e recibo instalado permaneceram intactos. |
| `--restaurar` | Recibo final marcado `restored`; quatro árvores anteriores recuperadas, recursos novos removidos e todos os arquivos de dados/configuração/compatibilidade iguais ao estado inicial. Sem restos `.stage-`, `.old-` ou `.restore-` nos destinos. |

As quatro árvores anteriores foram o applet DomainOS, o Style DomainOS e as cópias
de compatibilidade de SGI-Classic/GTK IrixClassic. Um arquivo do usuário fora do
catálogo também permaneceu intacto. A restauração pode deixar diretórios pais vazios;
o ensaio compara o conteúdo de arquivos/links, não seus mtimes ou diretórios vazios.

O pacote instalado coincidiu byte a byte com a árvore fonte daquele ensaio, incluindo
`README.md`, `FUNCTIONAL.md`, configuração, helpers, QML e a referência visual
`DomainOSPanel.qml`. `main.qml` carregava `DomainOSFunctionalPanel`, metadata
anunciava versão 0.2.0 e foram instalados gr_osview, IrixClassicDomainOS e
DomainOS SR10.4. A conferência final após a restauração não encontrou diferenças
entre os hashes de fonte registrados e o checkout naquele momento.

Oito preferências privadas e seus oito equivalentes reais de lsi mantiveram hashes
idênticos: `kdeglobals`, `kwinrc`, `plasmarc`,
`plasma-org.kde.plasma.desktop-appletsrc`, `Kvantum/kvantum.kvconfig`,
`gtk-3.0/settings.ini`, `gtk-4.0/settings.ini` e `mimeapps.list`.
O ensaio não instala em lsi/p001532, não acessa Downloads e não substitui o painel
ativo. Os hashes são evidência de preservação, sem copiar conteúdo desses perfis.

Artefatos locais:

- Resultado final: `/tmp/irix-domainos-instalacao-20261008-r4/RESULTADO.json`.
- Script do ensaio: `/tmp/irix-domainos-install-proof-r4.py`; cópia do r2 com saída nova.
- Logs das cinco chamadas em `01-verificar.log` até `05-restaurar.log`.
- Recibo final restaurado:
  `/tmp/irix-domainos-instalacao-20261008-r4/state/irixium-suite/backups/ecdec1b5f36b4576a3e61612fef03936/receipt.json`.

Hashes SHA-256 do pacote daquele ensaio:

| Arquivo | SHA-256 |
| --- | --- |
| `tools/install_suite.py` | `f07303b53fbc5389519465552a9e3e2bf71fef7f19c4648acbe976b9dc1312bd` |
| `metadata.json` | `b96c23c67420a172bac6d25ca5ab9a128dacd93b56b59d7f88c88e6851419a41` |
| `contents/ui/main.qml` | `cd2403e39f5ae5ac59d2433d287a586607aa227417999ae70f9fc3ad23590c2c` |
| `contents/ui/DomainOSRuntime.qml` | `89b8631189dcc08b8cfba432feccb2a1548e24409ae74916f5e01c0c0d08733e` |
| `README.md` | `042137767a45f857ea79f84c2d8d2cf1787b0b0cda46e74d705e8234117644c9` |
| `FUNCTIONAL.md` | `ce39380ea22c911ab0eacfb504e76ea4b8de8840ef2ddedc56ffc78ed955cef1` |

O resultado contém a lista completa de hashes do KPackage, os recibos e os estados
anteriores/posteriores. Este ensaio valida distribuição, idempotência e recuperação.
Não exercita atualização de caches/sinais da sessão, recarga de QML em memória nem
todos os provedores/aplicativos do perfil real. Esses efeitos não são inferidos da
instalação sem sessão. A guarda contra edições posteriores é documentada pelo
instalador; não foi provocada neste ensaio de ida/volta.

## Instalador independente DomainOS

`tools/install_domainos.py` foi exercitado separadamente, exclusivamente em
`/tmp/irix-domainos-independente-20261008-r3`, com **52/52 verificações aprovadas**
nas fontes daquele ensaio. Após corrigir unidades/amostragem, o mesmo contrato
passou novamente **52/52** em `/tmp/irix-domainos-independente-20261008-r4-unidades`.
Seu recibo final restaurado é
`state/irixium-domainos/backups/d5044738a47d4efc8b569b24f5d9781a/receipt.json`.
Uma linha de `FUNCTIONAL.md` foi corrigida depois dessa rodada; runtime, instalador
e catálogo não mudaram. A entrega final abaixo verifica também esse manual corrigido.
As execuções anteriores r1/r2 também passaram 52/52 e são históricas.
O resultado e os logs estão em `RESULTADO.json` e arquivos numerados no mesmo
diretório; o script do ensaio é `/tmp/irix-domainos-independente-proof.py` e exige
uma saída nova. Não houve instalação em lsi nem p001532.

O recibo de `irixium-domainos` registrou somente os quatro destinos permitidos:
applet DomainOS, gr_osview, Plasma Style IrixClassicDomainOS e cores DomainOS SR10.4.
Cada destino instalado conferiu com a fonte e com seu hash no recibo; os quatro
componentes anteriores conferiram com os backups. A repetição não criou backup
ou alterou recibos. A restauração recuperou todos os bytes anteriores. Um segundo
perfil, inicialmente sem nenhum dos quatro recursos, confirmou a criação e a
remoção dos quatro pela restauração.

O ensaio também provocou uma edição posterior no QML instalado e outra no backup,
somente nas cópias privadas: cada restauração foi recusada antes de qualquer
substituição e preservou integralmente esses arquivos. As verificações sem escrita
e a restauração em modo de verificação mantiveram recursos e recibos intactos.
Foram recusados destinos de sistema, raiz pertencente a outro usuário, caminho
relativo e link simbólico. A guarda root foi testada com UID simulado, sem executar
o instalador como administrador. Dependência nativa ausente produziu erro explícito.

Qt 6.7.3 e uma versão inválida foram recusados; 6.8.0, 6.8.2 e 6.9.1 foram aceitos
pela guarda de versão, com respostas simuladas de `qtpaths6`. A instalação real do
ensaio verificou o runtime Qt 6.8.2 e os módulos/recursos KDE da distribuição.
Essa guarda é compartilhada com o instalador completo, pois o DomainOS usa janelas
separadas de Popup disponíveis desde Qt 6.8. Não foram baixados ou instalados pacotes
de sistema.

O instalador independente testado tem SHA-256
`8812a239415032691ef435bb9476c9fb779fa794b8f77f63bc818ee62e28dc68`.
O JSON registra os hashes completos das quatro fontes instaladas. O recibo final
restaurado está em
`/tmp/irix-domainos-independente-20261008-r3/state/irixium-domainos/backups/191d05abbef446dfa48c1ca9a288346f/receipt.json`.

HOME, XDG_CONFIG_HOME, cache e runtime privados mantiveram todos os seus arquivos.
Recursos Classic, GTK/cursores legados, um prefixo Wine privado e um hook privado
pré-existente permaneceram idênticos. Nenhum estado da suite completa foi criado.
Oito hashes das preferências reais lsi permaneceram iguais, sem copiar seu conteúdo.
O ambiente não tinha display nem barramento da sessão; esse ensaio não valida
recarga do QML em memória, inclusão do widget ou interação no painel ativo.

Antes do fechamento de entrega, a correção do launcher passou também pela
instalação pública, repetição e restauração dos quatro destinos privados:
**22/22** em `/tmp/irix-domainos-entrega-20261008-r5-launcher/RESULTADO.json`.
Os destinos preexistentes foram recuperados byte a byte, a repetição não criou
novo backup e as oito preferências reais mantiveram hashes iguais no intervalo.
O recibo final é
`/tmp/irix-domainos-entrega-20261008-r5-launcher/state/irixium-domainos/backups/1df02c4d626140779ca94e71281c74bd/receipt.json`,
com estado `restored`. Esse ensaio dirigido verifica os bytes atuais e não repete
nem substitui as guardas transacionais anteriores de 52 verificações.

## TaskManager em host nativo Wayland

O ensaio de cliente Qt/Python autônomo em Wayland criou suas janelas, mas não recebeu
o modelo de tarefas: `/tmp/irix-domainos-tarefas-wayland-20261008-r1/RESULTADO.json`
registra a falha anterior às ações. Esse resultado não comprova tarefas funcionais
em Wayland. O KWin restringe `org_kde_plasma_window_management` e consulta as
interfaces declaradas para o caminho real do executável. Essa regra está no
[código oficial do KWin](https://github.com/KDE/kwin/blob/Plasma/6.3/src/wayland_server.cpp#L117).

O ensaio foi corrigido para carregar `DomainOSTasks.qml` de produção num applet de
teste dentro do **`/usr/bin/plasmawindowed` real**, conforme o uso documentado de
[plasmawindowed para testar widgets](https://develop.kde.org/docs/plasma/widget/testing/).
O Desktop Entry instalado `/usr/share/applications/org.kde.plasmawindowed.desktop`
já declara a interface necessária. Não foram criados Desktop Entries para autorizar
Python, alteradas identidades nem desativadas verificações de permissão. O log KWin
registra a autorização de PlasmaWindowManagement para `/usr/bin/plasmawindowed` e
continua negando as interfaces não declaradas fake-input/lockscreen-overlay.

**30/30 verificações passaram** em
`/tmp/irix-domainos-tarefas-wayland-host-20261008-r2/RESULTADO.json`. O host usa três
QWidget próprios, adicionados por um driver C++ exclusivamente de teste. A composição
da fixture usa a Iconbox e o controlador de produção, com escopo sem filtros e
agrupamento desativado para identificar os alvos individualmente. Os registros
incluem o caminho real de `/proc/self/exe`, PID do host, UUIDs das janelas e snapshots
antes/depois de cada operação.

| Comportamento | Confirmação real |
| --- | --- |
| Identidade | Três UUIDs distintos e PID igual ao processo que criou as janelas; chaves `window:<UUID>`. |
| Seleção | Clique Qt seleciona imediatamente; Ctrl+clique acumula dois IDs. |
| Minimizar | Pedido nativo aceito e estado minimizado recebido do compositor; os dois demais alvos permanecem não minimizados. |
| Restaurar/ativar | Estado nativo não minimizado/ativo e foco confirmado pelo QWidget destinatário. |
| Maximizar | Estado nativo maximizado e configure confirmado pelo QWidget; os dois demais alvos permanecem não maximizados. |
| Fechar | Somente a terceira tarefa sai do modelo e seu QWidget deixa de estar visível; as duas janelas selecionadas e sua seleção permanecem. |
| Isolamento | HOME/XDG, barramento e compositor Wayland privados em `/tmp`; quatro configurações reais e as duas fontes do controlador com hashes intactos. |
| Imagem e diagnóstico | `NATIVE-WAYLAND.png` captura somente a própria Iconbox; nenhum erro de execução QML. Avisos ambientais do host/compositor ficam integralmente nos logs. |

O C++ de teste não é um plugin instalado pelo produto e não substitui métodos do
TaskManager. Ele entrega cliques Qt ao próprio host, chama o contrato do controlador
e observa estados. Não utiliza fake-input, captura global da sessão nem uma API
alternativa para executar os comandos de janela.

Reprodução em saída nova:

```sh
python3 plasma/tools/testar-domainos-tarefas-nativas.py --backend wayland --saida /tmp/domainos-wayland-tasks-novo
python3 plasma/tools/testar-domainos-tarefas-nativas.py --backend x11 --saida /tmp/domainos-x11-tasks-novo
```

A regressão X11 do mesmo script passou **19/19** em
`/tmp/irix-domainos-tarefas-x11-final-host-20261008-r1/RESULTADO.json`, usando
Xvfb/Openbox e IDs X11. O ensaio Wayland acima exercita tarefas individuais e
seleção acumulada; não comprova, sozinho, grupos com checkboxes, filtro N>L,
menu nativo completo ou toda a composição funcional em Wayland. Esses contratos
têm evidências separadas de lógica/UI ou outros hosts. Organização via script KWin
é outro backend e suas verificações não são usadas como substituto dessa prova.

## Grupos e filtro automático no Wayland

A lacuna entre seleção de grupo e operação em lote foi verificada separadamente:
**62/62** em `/tmp/irix-domainos-grupos-wayland-r5/RESULTADO.json`.
Três janelas próprias formam um grupo nativo e uma quarta pertence a outro processo.
Cliques reais abrem o seletor, marcam dois checkboxes e acionam colunas/minimização.
A cadeia de produção Iconbox → Tasks → WindowOperations → helper temporário KWin
confirma somente os dois UUIDs escolhidos. A terceira janela do grupo e a avulsa
mantêm seus estados e geometrias. A seleção persiste ao reabrir o grupo e após as ações.

O contador registra N=4 antes de agrupar ou filtrar. Com L=3, mostra somente as
minimizadas; na igualdade e abaixo do limiar, volta à apresentação normal.
Restaurar uma janela pelo TaskManager atualiza a apresentação sem recontagem circular.
Fechar explicitamente a terceira janela reconta N=3 e restaura o modo normal.
Essas transições não enviam minimização, organização ou fechamento automaticamente.

Minimização externa não gera um estado `minimized` no protocolo `xdg_toplevel`
observável pelo QWidget. A prova usa a confirmação do helper KWin e um snapshot
novo do TasksModel; a restauração também confirma foco no cliente próprio.
Não se apresenta `QWidget::isMinimized()` como evidência de minimização externa.
O ensaio abrange colunas e minimização em grupo; linhas, mosaico e demais operações
continuam com a prova separada do backend descrita abaixo.

HOME/XDG/barramento foram registrados nos filhos imediatamente antes de `exec`,
mantendo PID e ambiente, e confirmados pelo próprio host após `exec`.
Os três processos privados encerraram; fontes de produção, executável/desktop entry
do host e quatro configurações reais preservaram seus hashes no intervalo final.
A primeira tentativa r1 registrou uma variação do `appletsrc` real; sua causa não
foi estabelecida. Esse resultado foi mantido e não conta como preservação comprovada.
Os ensaios finais r3/r5 preservaram seus respectivos estados anteriores.

Reprodução em saída nova:

```sh
python3 plasma/tools/testar-domainos-grupos-wayland.py --saida /tmp/domainos-grupos-wayland-novo
```


## Organização e janelas relacionadas

A ponte temporária de produção foi exercitada em KWin X11 e Wayland, com
**55/55** e **56/56** verificações, respectivamente. Os resultados estão em
`/tmp/irix-domainos-janelas-x11-r7-transientes/RESULTADO.json` e
`/tmp/irix-domainos-janelas-wayland-r7-transientes/RESULTADO.json`.

O ensaio cria seis janelas próprias e compara as geometrias nativas para colunas,
linhas e mosaico com 2, 3 e 6 alvos; verifica maximização, minimização e reunião.
Os alvos começam também em outra área e, no Wayland, em outro dos dois monitores
virtuais. PID obsoleto, desktop alterado e cliente com tamanho fixo são recusados
antes de qualquer mutação. O encerramento forçado é testado somente num processo
filho próprio: um irmão não selecionado impede o comando; ambos escolhidos permitem
o sinal, e o teste observa a saída do filho com −9 sem atingir o processo principal.
O produto descreve esse retorno como envio do sinal, sem inventar confirmação de saída.

Foi acrescentada uma guarda para relações de diálogos. O
[código oficial de Window::setDesktops/sendToOutput](https://github.com/KDE/kwin/blob/Plasma/6.3/src/window.cpp)
propaga mudanças a descendentes transientes e, no caso modal, a janelas principais.
O [header da API](https://github.com/KDE/kwin/blob/Plasma/6.3/src/window.h)
expõe `transient`, `transientFor` e `modal`, mas não a relação completa de
`mainWindows()/transients()` ao script. Por isso, organização em lote recusa alvos
com relações de diálogos, inclusive quando pai e filho estão escolhidos. Um diálogo
de grupo com pai não resolvido também impede a operação: não é seguro inferir seu
alcance apenas pelo PID. O menu nativo de ações individuais permanece disponível.

O teste verifica um QDialog não modal e depois modal, confirma a relação no próprio
KWin e compara snapshots antes/depois. Reunião, colunas, maximização e minimização
do pai não alteram o filho não selecionado; selecionar só o filho também não move
o pai. A recusa é explícita e ocorre antes de alterar qualquer alvo. Não se afirma
suporte a disposição independente de janelas com relações que a API não permite isolar.

## Instrumentos, aplicativos, comandos e bandeja

Os resultados abaixo são contratos separados; seus totais não representam uma única
sequência de interação nem devem ser somados como cobertura de todos os aplicativos.
São usados HOME/XDG, D-Bus e displays privados. Provedores de teste são identificados
nos próprios relatórios e não são apresentados como hardware do computador real.

| Contrato | Resultado local | O que foi observado |
| --- | --- | --- |
| Aplicativos e pins (histórico) | 23/23 em `/tmp/irix-domainos-aplicativos-20261008-v7/RESULTADO.json` | Catálogo Kicker, lista independente, pedido de lançamento e remoção sem fechar tarefa; regressão final 32/32 de F29 descrita abaixo. |
| Instrumentos | 23/23 em `/tmp/irix-domainos-instrumentos-20261008-final/RESULTADO.json` | Relógio/calendário separados, sensores reais e fontes ausentes, histórico e gr_osview. |
| Comandos/atividade | 23/23 em `/tmp/irix-domainos-comandos-review-r2-20261008/RESULTADO.json` | Resolução segura dos comandos, pedidos nativos, bloqueio/falha observados em serviço privado e lente sem atrasar ação. |
| Pager | 103/103 em `/tmp/irix-domainos-pager-native-window-r3/RESULTADO.json` | IDs, uma/duas/várias áreas, CRUD explícito, roda alternativa, troca rápida confirmada por D-Bus, mapas geométricos e cancelamento. |
| Bandeja | 34/34 em `/tmp/irix-domainos-tray-native-window-r2/RESULTADO.json` | Delegates Plasma/SNI nativos, menus/Activate/ContextMenu, popups, excedentes/ocultos, atenção e preferências próprias. |
| Configuração da bandeja | 13/13 em `/tmp/irix-domainos-preferencias-bandeja-20261008-final/RESULTADO.json` | O Configure de produção abre as páginas do applet correto; nomes reais de provedores e mudança aplicada pelo controle nativo. |
| Teclado | 15/15 em `/tmp/irix-domainos-teclado-20261008-r2-final/RESULTADO.json` | Pressão imediata, ação ao soltar, cancelamento ao perder foco, seleção/ativação e menu pelo teclado. |

Áudio, Wi-Fi, Bluetooth, energia e notificações do perfil real não foram modificados.
No ensaio da bandeja, NetworkManager/BlueZ e itens SNI de teste pertencem somente ao
barramento privado; os popups são os provedores Plasma instalados. Abrir esses
quadros não é prova de conexão a hardware real. Suspender, hibernar, desligar e
encerrar sessão não foram executados no computador do usuário.

Os pedidos de TaskManager e dos helpers de comandos que observam somente o
despacho são registrados como `request-accepted`. O catálogo/contexto Kicker
registra `dispatch-returned`: seu retorno não comprova aceitação nem conclusão
da aplicação. No contexto, o booleano controla a solicitação de fechamento do
popup do catálogo; `false` não significa falha da aplicação. As provas finais de F29 abaixo
distinguem esses contratos. A lente representa operações observáveis, sem
prolongar a execução para fabricar atividade. A opção de permanência após a conclusão apenas
adia apagar a luz; fica desligada inicialmente. Ausência de sensor não é zero e
contagens de correio não são fabricadas. Provedores de agenda são selecionados
explicitamente, sem ler contas do usuário.

## Correção dos instrumentos na auditoria final

A revisão de VF03 encontrou uma escala enganosa: dois sensores personalizados
com unidades diferentes podiam alimentar o mesmo gráfico. O runtime agora exige
a mesma unidade nativa, explica a recusa e mantém escala/frações indisponíveis.
Os valores individuais formatados continuam reais; não há conversão implícita.
Perda da fonte, troca de unidade ou incompatibilidade limpa histórico/pico, e o
gráfico não desenha curvas antigas por cima do indicador de indisponibilidade.

**34/34** passaram em
`/tmp/irix-domainos-instrumentos-unidades-native-final-r2/RESULTADO.json`.
Os sensores reais `cpu/all/usage` e `network/all/download` forneceram unidades
1002 (%) e 200 (B/s), respectivamente: o conjunto foi recusado, sem escala ou
frações fabricadas. Rx/Tx com unidades 200/200 recuperou as duas séries; CPU sem
secundário também funcionou. A injeção explícita de um histórico antigo é uma
fixture de defesa visual, não dados apresentados como medição real.
O contrato original dos instrumentos passou novamente **23/23** em
`/tmp/irix-domainos-instrumentos-contrato-final-r2/RESULTADO.json`.

UI/XML agora oferecem o mínimo efetivo de 1000 ms. Um pedido legado de 250 ms
permanece registrado só para diagnóstico e resulta em limite real de 1000 ms.
O relógio usa sua atualização própria de 1000 ms; selecionar telemetria de
60000 ms não atrasa hora/fusos. O teste observou a hora avançar enquanto as duas
assinaturas de sensores usavam o limite de 60000 ms. Esses são limites técnicos,
não valores escolhidos pelo usuário. Nenhum temporizador de clique foi acrescentado.

```sh
python3 plasma/tools/testar-domainos-instrumentos.py --unidades --saida /tmp/domainos-unidades-novo
```

## Lançamento de correio e ajuda nativa

O ensaio dirigido encontrou dois defeitos no launcher compartilhado: a URI
`applications:ID` não resolvia o Desktop Entry e a captura por pipes podia esperar
pela saída do aplicativo, mesmo depois do retorno do KIO. `commands.py` agora passa
o arquivo XDG previamente resolvido como argumento literal do KIO e usa stdin/stdout
em DEVNULL, com stderr em arquivo temporário e leitura de erro limitada a 8192 bytes.
O timeout de 20 segundos continua limitado ao launcher. O fallback GTK conserva
o Desktop ID; nenhuma configuração MIME é escrita pelo helper. O resultado segue
`request-accepted`, sem prometer conclusão ou janela aberta.

**29/29** passaram em
`/tmp/irix-domainos-lancamentos-mail-xman-native-r2/RESULTADO.json`.
Os caminhos reais `openMail` → helper → KIO abriram duas janelas Qt próprias,
uma para o cliente escolhido na instância e outra para o default MIME privado.
PIDs, argumentos sem URI de composição e namespaces foram observados; o default
privado permaneceu intacto. Não se abriu Thunderbird nem se acessou uma conta pessoal.
O despacho do botão gráfico tem sua prova separada no ensaio de instrumentos.

O mesmo teste abriu o `/usr/bin/xman` verdadeiro com duas paletas nativas.
As cores de fundo/texto foram observadas nos pixels, com contrastes de 11,67:1
(Irixium) e 4,63:1 (DomainOS SR10.4). A ordem ajuda local/xman/KDE foi observada
no menu, e um PATH privado sem xman produziu falha explícita e apagou a lente.
Os recursos adicionais `Command` foram enviados, mas suas cores de seleção não
apareceram na face inicial do Xaw; não se afirma que essa face reproduza Highlight.
Não houve mudança nas cores do xman para retirar essa limitação do relatório.

O ensaio original dos comandos passou novamente **23/23** em
`/tmp/irix-domainos-comandos-contrato-final-launch-r3/RESULTADO.json`;
os **12** unitários dirigidos também passaram. A tentativa r1 e o diagnóstico
`/tmp/irix-domainos-launch-diagnostic-r1/native.log` permanecem históricos.
O r1 incluía dois critérios extras de Highlight que não constam de VF16;
o r2 verifica o contraste efetivamente renderizado e registra os recursos extras.
O helper final tem SHA-256
`546ce36fafb9140e5aa6ea7c0205bd835dd168e91b29848eb113a772eeeb5927`.

```sh
python3 plasma/tools/testar-domainos-comandos.py --lancamentos --saida /tmp/domainos-lancamentos-novo
```

### Aparência e ajuda KDE observadas nas aplicações instaladas

A auditoria encontrou uma lacuna de evidência em F25: a fonte encaminhava para
`systemsettings kcm_lookandfeel`, mas a prova anterior não observava essa janela.
O ensaio dirigido passou **31/31** em
`/tmp/irix-domainos-aparencia-ajuda-native-r3/RESULTADO.json`, sem alterar produção.
O controlador QML real chamou o helper e abriu `/usr/bin/systemsettings`; PID,
argumentos, janela Global Theme visível, objetos da categoria de aparência e
`kcm_lookandfeel.so` mapeado foram observados na aplicação instalada.

O segundo caminho abriu `/usr/bin/khelpcenter` com `help:/plasma-desktop`. O
`KHC::View` real em `help:/plasma-desktop/index.html` renderizou The Plasma Handbook
e seu índice, em vez de uma página de boas-vindas ou erro. Capturas:
`/tmp/irix-domainos-aparencia-ajuda-native-r3/SYSTEMSETTINGS.png` e
`/tmp/irix-domainos-aparencia-ajuda-native-r3/KHELPCENTER.png`.

HOME/XDG, Xvfb e barramento eram privados, sem diretórios de ativação D-Bus nem
acesso ao barramento de sistema. As oito preferências reais e as quatro fontes
efetivamente usadas conservaram os hashes; zero processos privados restaram.
As tentativas r1/r2 conservam falhas de compilação/asserção da sonda, não defeitos
do produto. Alcance: invocação da API do controlador → helper → GUI nativa, sem
clicar no painel completo ou validar uma sessão pessoal. Não substitui a prova
anterior de xman, nem representa bloqueio/suspensão/logout físicos.

Reprodução em saída nova:

```sh
python3 plasma/tools/testar-domainos-aparencia-ajuda.py --saida /tmp/domainos-aparencia-ajuda-novo
```

## Arte e pesquisa histórica

A regressão da referência passou **2437/2437** em
`/tmp/irix-domainos-selecao-20261008-r2-final/RESULTADO.json`: desenho, relevos,
seleção, fontes e contraste foram comparados em oito paletas, incluindo quatro
amarelas. Esses são ensaios visuais/fixtures, não confirmação de comandos KDE.
A fonte e os SVGs aprovados permanecem no componente compartilhado.

A confirmação histórica solicitada para o Pager foi registrada em
[DOMAINOS-PAGER-REFERENCIA-IRIX.md](DOMAINOS-PAGER-REFERENCIA-IRIX.md), com manuais SGI
primários. A adaptação é descrita separadamente do comportamento histórico;
mapas geométricos não capturam conteúdo de janelas. O significado original do gráfico
HP não é usado como prova da métrica escolhida. O backup congelado em Downloads
não foi usado como área de trabalho, atualizado ou removido.

A substituição do painel ativo e a validação nas sessões lsi/p001532 continuam
pendentes de autorização específica de cada sessão. Os ensaios privados não
substituem essa avaliação. O arraste entre miniaturas do Pager permanece adiado.


## Pacote e composição finais

O KPackage de produção passou **24/24** em
`/tmp/irix-domainos-package-20261008-r4-unidades-final/RESULTADO.json`; a integração
com KWin, relógio/sensores, tarefas e bandeja passou **19/19** em
`/tmp/irix-domainos-integracao-20261008-r3-unidades-final/RESULTADO.json`.
Ambos usam `main.qml` efetivo, sem substituir os componentes por uma imagem ou
seus dados por exemplos. A composição confirma ausência de comandos ao carregar,
fusos/data e rede reais, um desktop existente sem criar outros, catálogo e menu
de tarefas, fonte Courier aprovada, paleta nativa, imagens recoloridas e bandeja.
As rodadas anteriores `r2-anchor-final` comprovaram o estado anterior à correção
de instrumentos. A primeira tentativa atual do pacote `r3-unidades-final` foi
interrompida antes do host pelo sandbox, que recusou o socket D-Bus privado;
essa falha ambiental está preservada. O r4 executou o mesmo teste no barramento
privado permitido, sem acessar uma sessão KDE real.

Essas duas rodadas antecedem a alteração posterior apenas em `commands.py`.
Esse launcher tem prova nativa dirigida 29/29 e contrato 23/23 descritos acima;
a instalação atual confere os bytes das quatro árvores, incluindo o helper corrigido.

Qt Quick Controls anteriores a 6.8 só permitem pop-ups dentro da cena da janela.
Um painel de 109 px cortava quadros maiores. Agora grupos, status, excedentes,
menus e diálogos usam janelas separadas; o instalador exige **Qt ≥ 6.8**.
Os controles próprios não herdam transições de opacidade do estilo. A posição de
quadros ancorados compensa a escala do painel sem mudar seu tamanho nativo.
A ajuda local e a mensagem de falha abrem integralmente fora do painel; menus
compactos também têm janelas próprias, mesmo quando sua altura cabe nos 109 px.
A API utilizada está na [documentação oficial de Popup](https://doc.qt.io/qt-6.8/qml-qtquick-controls-popup.html#popup-type).

A Iconbox passou **46/46** em
`/tmp/irix-domainos-iconbox-20261008-scaled-ancestor-final-r6/RESULTADO.json`:
checkboxes acumulativos, modos de clique central sem membro implícito, grupo/menu
em janelas separadas e posição com ancestral realmente escalado a 50%. O topo da
Iconbox foi 645 px e a borda inferior do seletor 640 px. A pressão e o desenho
continuam no componente compartilhado. A reordenação manual pelo TasksModel real
passou **32/32** em
`/tmp/irix-domainos-reorder-native-final-window-r4/RESULTADO.json`, com validação de
PID/identidade, limiar de arraste do sistema, rejeição em outros modos e conservação
dos estados/pins. Arrastar tarefas não implementa o arraste de miniaturas do Pager.

As três preferências anteriores de clique central/roda persistem por instância,
com os mesmos defaults técnicos da Iconbox anterior. A configuração passou
**32/32** em `/tmp/irix-domainos-preferencias-20261008-mouse-final/RESULTADO.json`.
Esse ensaio utiliza a API nativa para parte das mudanças; não representa cliques
reais em todos os controles. Apply clicado e visibilidade de provedores reais
continuam com sua prova separada de 13 verificações. Nesse ensaio de 32 checks,
o descarte foi verificado por recarregamento das propriedades.

A lacuna do descarte por clique foi fechada num ensaio dirigido separado,
**18/18** em
`/tmp/irix-domainos-preferencias-descarte-native-final-r1/RESULTADO.json`.
Após editar a política de um provedor, cliques reais em Cancelar e na confirmação
Descartar fecham o ConfigView nativo. Reabrir recupera o valor salvo anterior,
sem Apply. O KConfig da instância, a visibilidade nativa do provedor e uma segunda
instância de ID 101 permanecem intactos. Não houve mudança nas fontes de produção
ou nas configurações reais, nem erro QML. Isso não representa cliques em todos os
campos das oito páginas.

```sh
python3 plasma/tools/testar-domainos-preferencias-bandeja.py --descartar --saida /tmp/domainos-descarte-novo
```

## Cliques durante telemetria e notificações — VF20

A composição de produção foi ensaiada no `/usr/bin/plasmawindowed` com KWin,
ksystemstats, watcher SNI do KDED e servidor de notificações Plasma/KDE 6.3.6
próprios. As únicas fontes de estímulos foram um aplicativo SNI e notificações
pertencentes ao teste. Não houve substituição dos modelos/servidores nativos,
histórico de sensores fabricado ou uso dos serviços da sessão real.

Em `/tmp/irix-domainos-concorrencia-native-r13/COBERTURA-VF20.json`, **180/180**
verificações do recorte VF20 passaram: 12 ciclos de pressão/liberação por mouse
e Space, Tab/foco, relevo/ação no mesmo despacho e geometria constante dos
14 módulos e da janela. O sensor CPU emitiu nove sinais; o servidor real emitiu
dois eventos de inclusão e 27 de reposição. Resumos próprios foram observados
no histórico durante os gestos; a expiração natural terminou com duas não lidas.
As fontes de produção e quatro configurações reais mantiveram hashes iguais.
Os processos próprios registrados foram encerrados, sem interferir nas prévias.

O `RESULTADO.json` original do mesmo diretório permanece **failed**: das 182
verificações, faltou provar um limiar extra de seis mudanças de atenção antes
da expiração, e o worker retornou 1 por essa asserção. O modelo SNI real mostrou
NeedsAttention e o adaptador emitiu oito sinais no total, mas não se registrou
o subtotal no instante do corte. Esse limiar não consta de VF20; a cobertura
separada não converte a falha original em sucesso nem comprova todo o timing VF14.
Não se alterou a produção para satisfazer uma asserção adicional do fixture.

| Entrega do evento QTest | Mínimo observado | Máximo observado |
| --- | --- | --- |
| Pressionar mouse | 0,677 ms | 9,426 ms |
| Liberar mouse | 6,861 ms | 31,228 ms |
| Pressionar Space | 0,222 ms | 19,663 ms |
| Liberar Space | 0,452 ms | 38,847 ms |

Esses tempos medem as chamadas QTest e seu processamento nativo nesse host X11
com renderização por software. Não são latência física até a tela nem garantia
universal; rodadas diagnósticas anteriores variaram. Capturas BEFORE, PRESSED e
AFTER estão no mesmo diretório. Esses números pertencem à rodada r13; o ensaio
dirigido posterior abaixo fecha a lacuna temporal de atenção.

### Adoção e atenção de itens SNI carregados depois

O ensaio dirigido r14 mostrou um defeito de produção: o StatusNotifierModel e
o delegado nativo recebiam NeedsAttention do item próprio, mas a lista adotada
por `DomainOSTray` não o incluía. O primeiro scan podia acontecer antes de o
Loader terminar; observar apenas count/children e os loaders já capturados
não cobria todas as alterações dos modelos nativos.

O adaptador agora observa inserções, remoções, reset, layout e dados dos modelos
visible/hidden, além da disponibilidade/status dos loaders e itens. Usa o
`Qt.callLater(refresh)` já existente, sem timer ou troca de provedor. A regressão
`/tmp/irix-domainos-bandeja-native-attention-refresh-r15/RESULTADO.json` passou
**34/34**. SHA-256 de `DomainOSTray.qml`:
`1dfa60fb9560a16fb0be011d9b46705082adfbcf758aeae2d82e8d0207c46d64`.

`/tmp/irix-domainos-concorrencia-native-directed-r16/RESULTADO.json` passou
**197/197 no relatório original**, sem recorte de falhas. Mantém o critério
anterior de pelo menos seis mudanças de atenção e acrescenta seis testemunhos
de ID/estado no modelo e delegado adotado durante mouse pressionado. Os estados
NeedsAttention/Active são estímulos SNI próprios, mantidos até consumo nativo;
não são estados injetados no adaptador. ACKs reais e os tempos monotônicos
confirmam atençãoCount=6 até o último release. CPU, notificações, teclado/foco e
geometria dos 14 módulos continuam reais; 12 identidades do histórico foram
cruzadas com os IDs retornados por Notify. Perfis e fontes se mantiveram iguais
durante o ensaio e os processos próprios foram encerrados.

Máximos observados nesta rodada: mouse pressionar/liberar **2,956/65,634 ms**;
Space pressionar/liberar **4,530/18,299 ms**. São tempos QTest neste host, não
limites universais ou latência até a tela. Capturas BEFORE/PRESSED/AFTER estão
no diretório r16. Os resultados failed r13/r14/r15 foram preservados: r15 já
adotava o item, mas o controle síncrono do harness podia disputar o Notify e
estourar seu timeout. O controle virou assíncrono com ACK obrigatório; não se
removeu a asserção nem se alterou a produção para contornar esse timeout.

### Favoritos administráveis e alcance do provedor

O catálogo mostrava favoritos, mas sua UI não permitia acrescentar ou retirar
entradas. `DomainOSApplicationMenu` recupera o menu contextual nativo do Kicker,
incluindo ações da aplicação e favoritos, com botão direito, tecla Menu e
Shift+F10. A gaveta continua com pins próprios. Licença e avisos de autoria dos
helpers derivados do lançador existente foram mantidos.

`/tmp/irix-domainos-aplicativos-favoritos-native-r3/RESULTADO.json` passou
**28/28 nas fontes daquela rodada**, antes da correção posterior de F29: adicionar/retirar/recolocar favorito pelo contexto nativo, abertura
por teclado, lista/catálogo reais, pins e tarefas intactos, nenhum lançamento
extra e quatro preferências pessoais preservadas. Dois clientes privados
observam os mesmos membros de favoritos. Isso é o contrato do KAStats: o client
ID distingue ordenação, enquanto os membros pertencem ao usuário/atividade.
O menu e a dica do botão explicam esse alcance, sem importar ou editar favoritos
ao abrir. [Código oficial KDE](https://github.com/KDE/plasma-workspace/blob/Plasma/6.3/applets/kicker/plugin/kastatsfavoritesmodel.cpp).

A tentativa r1 preservada falhou na hipótese incorreta de membros isolados por
client ID; r2 falhou porque o observador escolheu o título desabilitado do menu.
r3 clica somente ações habilitadas. `FINAL-SOURCES.json` registra as cópias
testadas; `COPYRIGHT-NOTICES.json` documenta a reposição posterior de duas linhas
SPDX de autoria, com código QML idêntico fora desses comentários. Não se afirma
que bancos/favoritos pessoais foram usados no ensaio.

### F29 final: atividade do catálogo e das ações de contexto

A auditoria encontrou um caminho que ignorava a lente: catálogo, favoritos
lançáveis e Desktop Actions chamavam o provedor Kicker diretamente. O dispatcher
final usa `commands.begin/finish` síncronos ao redor do pedido nativo; não acrescenta
espera para lançar, pressionar ou pintar. Categorias, edição de favoritos,
títulos, separadores, submenus e controles desabilitados não geram atividade.
A gaveta continua com seus pins próprios e seu caminho de comando existente.

O resultado é **`dispatch-returned`**, com `closeRequested` separado: ele observa
que a chamada do dispatcher retornou, sem afirmar aceitação, janela aberta,
vida ou conclusão da aplicação. No menu contextual, retorno verdadeiro solicita
fechar o popup do catálogo; retorno `false` não é falha da aplicação. O catálogo conserva seu
fechamento preexistente ao acionar uma folha. Exceções encerram o token com falha
explícita. O retorno e a exceção foram exercitados com **modelos duplos declarados**;
os três despachos positivos abaixo usam o Kicker e Desktop Entries próprios reais.

As **provas finais de F29** são distintas e não têm suas contagens somadas:

- **32/32** em
  `/tmp/irix-domainos-aplicativos-atividade-runtime-curto-final-r3/RESULTADO.json`:
  categoria sem atividade, catálogo/favorito/ação de contexto nativos e marcadores
  exatos `first`, `first`, `context-first`. `DomainOSActivity` de produção observa
  `pending=1/lit=true` no início; o finish padrão é síncrono, sem cauda. A cauda
  opcional de **700 ms é escolha técnica do fixture privado**, começa só após o
  retorno e apaga sem esperar a conclusão da aplicação. Edição de favoritos e
  controles inativos não geram token. Os tokens do início/fim correspondem.
- **32/32** em
  `/tmp/irix-domainos-aplicativos-regressao-atividade-runtime-curto-final-r10/RESULTADO.json`:
  conserva as 28 verificações anteriores de catálogo, pins, metadados/ícones,
  tarefa/launchers, Configure da instância e favoritos nativos compartilhados
  pelo KDE. Acrescenta visibilidade temporal do popup/alvo, ausência de modal
  impeditivo e limpeza dos processos/runtime. O ramo `openApplication` dos pins
  permanece **mock de contrato de pedido**, sem alegação de lançamento real por
  esse ramo; o marcador `first` é o despacho nativo do catálogo.

As entradas foram pressão → `processEvents` → 50 ms → soltura em controles Qt
reais, com popup, owner e alvo preservados e janela ativa. Os contextos ficaram
visíveis durante o gesto. HOME/XDG, KWin, Xvfb e D-Bus eram privados; preferências
pessoais/fontes ficaram intactas, daemons próprios encerraram e o runtime foi
removido. Os testes não abriram sessões reais de lsi ou p001532.

As tentativas históricas r1–r8 da regressão permanecem preservadas. R8 tinha menu
X11 `IsViewable`, exposto, geometria 316,0,448,438 e itens habilitados, mas um
`QDialog Error` **modal e visível** bloqueava o input. O log registra falha de
`QLocalServer::listen` e de socket KIO para o protocolo `tags`. O runtime tinha
73 caracteres; no final, um runtime próprio `/tmp/ird-app-*` de 21 caracteres
removeu o erro/modal e os controles responderam ao gesto completo. A hipótese
inicial de perda de popup entre press/release foi refutada; acrescentar KWin ou
usar XTest com runtime longo não eliminou o modal. R9, runtime curto/XTest,
confirmou o primeiro despacho, mas o observador bloqueou após o contexto e
atingiu seu deadline; também foi preservado. R10 é a regressão final com gesto
QtTest separado, KWin e ausência de modal diretamente observada.

Não se capturou o caminho completo do socket falho. O formato UTF-16
`XXXXXX.%1.kioworker.socket` foi observado na biblioteca KIO instalada; substituir
`%1` por `plasmawindowed` resultaria em 110 caracteres no r8, mas isso é **inferência**,
sem caminho efetivamente capturado. Não há evidência desse erro na prévia de
p001532. Esta prova não alterou o wrapper nem valida sua próxima revisão.

SHAs finais: `DomainOSApplications.qml`
`e3860664e973622dd227155999c74d5640a883e2b481e93dbc463b409989d800`;
`DomainOSApplicationMenu.qml`
`aac426503e57bb2eac2e15a2b588b3ca82790c0731f5307559576763c8a41b03`.
O resumo da prova está em `/tmp/irix-domainos-aplicativos-atividade-F29-final.md`.
Os resultados de favoritos 28 e catálogo/pins 23 anteriores são históricos,
com seu alcance próprio, e não substituem estes ensaios finais de atividade.

### New Desktop final: identidade do grupo e atividade do Runtime

O menu nativo conservava o índice do grupo capturado. Na versão anterior,
`New Desktop` podia atingir um membro que entrou depois de abrir o menu: a captura
continha A/B, C ingressava no grupo e o QAction criava outra área e movia A/B/C.
Isso foi reproduzido com o `TasksModel`, o `ContextMenu.qml` instalado e o KWin
reais, em X11 privado. O RAW anterior mantém **`failed`**, exatamente nos gates
`stale_action_creates_no_desktop` e `stale_action_moves_no_member`; os outros
**18/20** checks passaram. Os UUIDs reais do KWin, IDs numéricos X11, PIDs,
associações aos desktops e geometrias estão nos snapshots.

A proteção final resolve novamente a linha pelo conjunto exato de membros e
PIDs capturados, revalida capacidade nativa e recusa o alvo alterado antes de
criar a área. O menu obsoleto mostra erro para reabrir; não cria desktop, move
janela ou emite pedido/atividade. Reabrir o menu capturando A/B/C permite criar
exatamente uma área e mover somente esses três membros, preservando PIDs e
geometrias. Depois do método nativo retornar, uma única emissão
`operationRequested({state:"requested", action:"newVirtualDesktop", key:...})`
encaminha a atividade ao Runtime existente.

A **prova final r7** passou **5/5 na comparação** e **34/34 na versão atual**, em
`/tmp/irix-domainos-menu-desktop-membership-r7/RESULTADO.json`. `DomainOSRuntime`
e `DomainOSActivity` reais observam zero pedido/token/relatório no alvo obsoleto;
no alvo atual, exatamente um pedido com a identidade do grupo e um relatório
**`request-accepted`**. Esse relatório confirma somente o despacho, sem atribuir
conclusão ao compositor. A observação separada dos desktops/janelas comprova o
efeito no KWin privado, sem mudar o contrato do relatório de atividade.

A cauda opt-in de **1500 ms é configuração técnica privada do teste**, sem mudança
de padrão ou preferência pessoal. Foi observada acesa após o pedido e apagada
depois, com `pendingCount=0`, sequência 1 e sem repetir ou postergar o comando:
os desktops/janelas já tinham mudado enquanto a cauda estava acesa. O teste não
acrescenta timer à operação ou altera Runtime/Activity. Fonte final de
`DomainOSNativeTaskMenu.qml`:
`a8dc72d1d9ab0080c46d0477a06b6c95c563fc9571210bba7c4870e7ceebbd3b`.

O gesto desta prova é **QAction instalado acionado programaticamente**; a fixture
abre o menu pela função `openContext` de produção. Não se afirma navegação física
no submenu, Wayland, renderização da lente ou avaliação em sessão pessoal.
A/B pertencem ao host e C a processo Qt filho próprio, com AppId correspondente
e PID distinto. Remove-se atenção somente dessas janelas via EWMH no display
privado para obter o agrupamento normal, sem modelo duplo ou override do provedor.
Os screenshots mostram só a Iconbox. Processos próprios encerraram; quatro
preferências pessoais e a fonte de produção ficaram intactas.

R1–r5 preservam o bloqueio de socket ou ajustes do observador; não demonstraram
mutação de produção. R6, **5/5 e 26/26**, conserva a reprodução/proteção de identidade
antes da emissão de atividade acrescentada depois; é histórico para F29.
`TEST-SOURCES.json`, `test-sources/`, `before/RAW.json` e `after/RAW.json` da rodada
r7 preservam fontes, hashes, limites e o relatório anterior com falha, sem
converter uma falha histórica em aprovação.

### Agenda positiva com feriados públicos

`/tmp/irix-domainos-agenda-publica-native-r4/RESULTADO.json` passou **33/33** na
composição de produção, KConfig da própria instância, KWin e D-Bus privados.
O teste escolhe somente `holidaysevents` instalado/região `us_en-us` e a data
2027-01-01; o DaysModel fornece New Year's Day (all-day), `agendaUpdated` é
observado e o delegate apresenta o título. O botão Data abre/fecha o calendário;
o provedor só carrega com o quadro aberto e a preferência volta à lista vazia.
Cinco preferências pessoais permanecem iguais e os processos próprios encerram.
Não houve conta pessoal, evento fabricado ou Apply nativo alegado.

O cenário positivo revelou um binding loop antes não exercitado: model e
enabledPlugins do EventPluginsManager compartilham `pluginsChanged`. O binding
de enumeração retroalimentava a lista habilitada. A correção guarda somente IDs
de metadados e atualiza o snapshot quando o conteúdo realmente muda, sem outra
instância de provedor, timer ou alteração de arte. O contrato de instrumentos
também passou **23/23** em
`/tmp/irix-domainos-instrumentos-agenda-regressao-final-r1/RESULTADO.json`.
SHA de `DomainOSInstruments.qml`:
`410c1f286175f4f4c1ca3e799ce589cbc79e9280a261b093452a0214452a795d`.
As tentativas r1/r2 preservam falhas do observador; r3 preserva o binding loop
real antes da correção. A captura final `AGENDA-FERIADO-NATIVO.png` é a janela
real do calendário, 708×428, separada do painel.

```sh
python3 plasma/tools/testar-domainos-agenda.py --saida /tmp/domainos-agenda-novo
```

## Instalação final em lsi e avaliação

### Regressão da janela Xephyr ao trocar de área

O relato de lsi foi reproduzido numa prévia totalmente privada. A janela do
painel e a referência eram clientes Qt Tool vinculados à primeira área: clicar
no segundo cartão alterava somente a área do KWin privado e deixava ambos
`IsUnmapped`, com o processo do painel ainda vivo. Não era encerramento do Plasma.
Resultado anterior: `/tmp/irix-domainos-preview-pager-antes-r1/PAGER-REGRESSAO.json`.

`plasma/tools/prever-domainos-funcional.py` agora confirma os PIDs dos dois
clientes próprios e solicita `_NET_WM_DESKTOP=4294967295` apenas nesses IDs,
no display e barramento privados. O applet/Pager de produção não foi alterado.
A inicialização faz quatro cliques reais 2→1→2→1 e confirma ativação, visibilidade,
PIDs e capturas; o painel e a referência permanecem acessíveis. Um terminal comum
do teste continua vinculado à primeira área e reaparece ao retornar a ela.

Provas em `/tmp/irix-domainos-preview-pager-sticky-r2`: inicialização **11/11**,
`PAGER-VERIFICACAO.json` **7/7** e `PAGER-REGRESSAO.json` **11/11**.
`ENCERRADO.json` confirma limpeza dos processos próprios e quatro preferências
reais com hashes iguais. O wrapper daquela rodada tem SHA-256
`09413d950267f55a50ff88df3b849b7ee5b8159d596117f17de5f0de61b0e5f4`.

Uma captura podia ainda mostrar um terminal durante a atualização assíncrona do
filtro. Isso não era a própria prévia entrando na Iconbox: os IDs do painel e da
referência foram conferidos e estão ausentes dos TasksModel/ScopeModel nativos.
A ferramenta passou a aguardar o UUID e o filtro observados antes de capturar,
sem polling ou timer permanente no host. A primeira área contém os três xterms
próprios; a segunda tem lista vazia em ambas as idas. Não se aplicaram flags SKIP
adicionais nem se alterou o filtro do applet.

Prova em `/tmp/irix-domainos-preview-pager-modelo-r3/PAGER-VERIFICACAO.json`:
**9/9**, com inicialização e regressão **11/11** cada. O wrapper final tem SHA-256
`9a8fd1d142b8ae13288571737d1558c41999e3e36f983323e5892dda37b1ac4c`.

### Comando portátil para avaliação por usuário

O assistente `plasma/tools/testar-domainos-sessao.py` abre essa prévia sem instalar
arquivos no perfil. Verifica recursos, integridade quando empacotado e Qt >=6.8,
recusa root e usa a sessão gráfica do próprio usuário apenas para a janela externa.
O conteúdo tem HOME/KWin/D-Bus próprios, com serviços de hardware/áudio reais fora
do teste. Naquela rodada foi preparado `/tmp/irix-domainos-teste-pacote-r2`, legível
por outros usuários, com cópias dos recursos necessários e referência PNG. O pacote
r1 foi preservado e as provas gráficas abaixo conservam o alcance daquela rodada.

Em lsi ou p001532, na sessão KDE correspondente, Alt+F2:

```sh
/tmp/irix-domainos-teste
```

Esse comando abre uma nova janela Xephyr. Para conferir dependências/recursos sem
abri-la, execute `/tmp/irix-domainos-teste --verificar` no terminal gráfico.
Um resumo legível por outros usuários em `/tmp/irix-domainos-teste-uid*-resumo.json`
contém apenas UID, caminhos e booleans das verificações iniciais; não copia
configurações, contas, endereços de barramento ou capturas do perfil privado.
Ele registra a inicialização, sem prometer que a janela permanece aberta depois.
O roteiro daquela rodada está em `/tmp/irix-domainos-teste-pacote-r2/README-TESTE.txt`;
a versão atual é r3, descrita no fechamento da entrega abaixo.
Fechar a janela externa encerra apenas os processos dessa prévia; não instala
no usuário p001532, substitui painel ou muda as áreas da sessão real.

O comando portátil completo passou pela mesma regressão em displays inteiramente
privados: `/tmp/irix-domainos-publico-modelo-r2/PAGER-REGRESSAO.json` **11/11** e
`PAGER-VERIFICACAO.json` **9/9**. O resumo público foi conferido, com booleans
iniciais aprovados e modo 0644; `ENCERRADO.json` confirmou processos próprios
encerrados e configurações reais preservadas. Isso comprova o lançador entregue,
sem afirmar que p001532 já o executou.

A atualização portátil r2 inclui os ajustes finais de favoritos, bandeja e agenda,
com os recursos auxiliares, fontes e licenças. **20/20** verificações passaram em
`/tmp/irix-domainos-teste-pacote-r2-verificacao/RESULTADO.json`: fontes exatas,
referência aprovada intacta e somente leitura, links internos válidos, permissões,
licenças e ambos os comandos públicos `--verificar` aprovados em HOME/XDG privados.
As oito preferências reais ficaram iguais e a árvore inteira de r1 foi preservada.
Somente depois dessas conferências, `/tmp/irix-domainos-teste` passou a apontar
atomicamente para r2. A verificação dessa atualização não abriu uma sessão gráfica;
não deve ser apresentada como avaliação pessoal de lsi ou p001532.

### Instalação e histórico das prévias

Depois da prova de restauração privada, os **quatro** componentes independentes
foram instalados em lsi pelo instalador público, sem aplicar tema, sinalizar cache,
criar áreas ou substituir o painel. O resultado final está em
`/tmp/irix-domainos-instalacao-lsi-20261008-r2/RESULTADO.json`: sucesso da instalação,
cópias iguais às fontes daquela rodada, recibo próprio e oito preferências reais com hashes iguais.
A primeira instalação e a atualização final têm backups separados; o comando de
restauração recupera a instalação independente mais recente, como documentado.

Após corrigir os instrumentos e seu manual, o instalador público atualizou
novamente somente os quatro componentes disponíveis em lsi. **5/5** conferências
passaram em `/tmp/irix-domainos-instalacao-lsi-20261008-r3-unidades/RESULTADO.json`:
sucesso, oito preferências intactas no intervalo, quatro destinos iguais ao checkout,
recibo independente e fontes preservadas. O recibo daquela instalação é
`/home/lsi/.local/state/irixium-domainos/backups/9d7feebfa9ac47429bc4604c4499b7c2/receipt.json`.
Não houve aplicação de esquema/Style ou inserção/substituição do painel ativo.

A correção posterior do launcher foi instalada pelo mesmo comando público:
**5/5** em `/tmp/irix-domainos-instalacao-lsi-20261008-r4-launcher/RESULTADO.json`.
Os quatro destinos coincidiam com as fontes daquela rodada e as oito preferências ficaram
iguais antes/depois dessa atualização. O recibo daquela atualização é
`/home/lsi/.local/state/irixium-domainos/backups/0ea0c493c3754a2d9211ae3db3a74eb7/receipt.json`.
Só o applet precisava de substituição; os outros três destinos já coincidiam.
Essa operação também não ativou o widget nem alterou o painel.

Após os ajustes de favoritos, adoção/atenção SNI e calendário positivo, os quatro
recursos atuais foram instalados novamente pelo instalador público somente em
lsi. **5/5** em
`/tmp/irix-domainos-instalacao-lsi-20261008-r5-native-final/RESULTADO.json`:
quatro destinos exatos, oito preferências iguais antes/depois, recibo independente
e fontes preservadas. O recibo daquela instalação é
`/home/lsi/.local/state/irixium-domainos/backups/b82a0b4a995143adb4b8b4f7b7b7094a/receipt.json`.
Esse resultado inclui os novos arquivos de contexto/ações e os manuais atuais;
não ativa o applet, seleciona Style/esquema ou substitui qualquer painel.

A prévia **“DomainOS R2 — funções e preferências finais”** foi aberta em
Xephyr, com fonte de produção, três terminais próprios e duas áreas privadas.
A imagem aprovada é a referência superior, sem comandos. Resultado/captura em
`/tmp/irix-domainos-funcional-r2-20261008/RESULTADO.json` e
`/tmp/irix-domainos-funcional-r2-20261008/PREVIA-FUNCIONAL.png`.
Fechar a janela externa encerra somente os processos dessa prévia. Sua limpeza
foi comprovada num segundo host em
`/tmp/irix-domainos-funcional-cleanup-r2-20261008/TESTE-ENCERRAMENTO.json`.
Na conferência posterior, o Xephyr, o supervisor e todos os PIDs registrados da
prévia final já estavam ausentes. O resultado de inicialização conserva seu estado
histórico `open`; não surgiu `ENCERRADO.json` nessa instância e a causa do encerramento
não foi estabelecida. A imagem continua disponível para comparação, mas não se
afirma que essa janela esteja aberta ou que seu supervisor tenha registrado a limpeza.

O ambiente verificado é Plasma/KWin **6.3.6**, Qt **6.8.2** e PyQt6 da distribuição.
A validação final de lsi/p001532 e a substituição de qualquer painel ativo ainda
exigem a autorização prevista no goal. Não há instalação global nem instalação
em p001532 nesta etapa. Não se executaram comandos de encerramento/suspensão ou
acesso a contas pessoais para ampliar artificialmente a cobertura.

Foi preparado um pacote offline histórico em `/tmp/irix-domainos-validacao-sessoes-r5`
para facilitar a avaliação futura por outro usuário sem acessar `/home/lsi`.
Contém somente as quatro fontes independentes, `components.json`, cinco módulos
do instalador e instruções/manifests. Os 147 arquivos fonte conferem com o checkout;
bytecode é excluído explicitamente. Arquivos 0644 e diretórios 0755 permitem leitura
por p001532, sem escrita por usuários diferentes do proprietário.
**13/13** verificações passaram em
`/tmp/irix-domainos-validacao-sessoes-r5-verificacao/RESULTADO.json`.
O comando público `--verificar` foi executado em HOME/XDG privados, sem display
ou barramento, e não escreveu nenhum arquivo. Preparar esse pacote não instalou
em p001532 nem abriu qualquer sessão real. Seu README mantém a exigência de
autorização antes de instalar e abrir a janela de avaliação daquele usuário.
Os snapshots r2/r3/r4 foram preservados como históricos. O r4 incorpora a correção
textual de `FUNCTIONAL.md` posterior ao ensaio transacional r4-unidades;
o r5 difere dele apenas pelo helper `commands.py` corrigido e registra essa
diferença temporal no manifesto. Seus hashes foram conferidos diretamente
com `sha256sum --quiet --check MANIFEST.sha256`.

A entrega final com os ajustes de favoritos, bandeja e calendário passou **22/22**
em `/tmp/irix-domainos-entrega-20261008-r6-native-final/RESULTADO.json`. O instalador
público instalou, repetiu e restaurou exatamente os quatro destinos num perfil
descartável, incluindo todos os manuais e arquivos novos. O recibo
`71af8245db2b46cb8be985a417cf339e` registra a restauração dos quatro componentes
anteriores; preferências reais e fontes ficaram intactas durante o ensaio.
Essa prova dirigida não repete nem substitui a matriz de 52 guardas anterior.

O snapshot offline daquela rodada é `/tmp/irix-domainos-validacao-sessoes-r6`, com **149**
fontes exatas e **152** arquivos no total. **13/13** verificações passaram em
`/tmp/irix-domainos-validacao-sessoes-r6-verificacao/RESULTADO.json`; manifesto,
permissões e `--verificar` em HOME/XDG privados foram conferidos sem display ou
barramento. O manifesto registra sete diferenças para r5, incluindo os dois novos
arquivos de ações/contexto de aplicativos. Os snapshots anteriores permanecem
históricos. Preparação e conferência não instalaram em p001532 nem abriram sessões
reais; a ativação pessoal continua com a autorização prevista no goal.

A [matriz F01–F35](DOMAINOS-MATRIZ-VALIDACAO-R2.md) reúne o alcance e as limitações
das provas por requisito, incluindo a validação pessoal ainda pendente.

Na auditoria posterior de entrega, `sha256sum --quiet --check` voltou a aprovar
o `SHA256SUMS` da cópia congelada (107 arquivos) e o manifesto do pacote offline.
O backup mantém arquivos 0444 e diretórios 0555. Os quatro destinos instalados
em lsi ainda coincidem com as fontes correntes; a ajuda acompanha o applet.
Sete preferências reais continuam iguais ao snapshot histórico anterior; o `appletsrc`
difere posteriormente. Essa variação não tem causa estabelecida e não foi revertida.
A igualdade das oito preferências no intervalo de instalação é uma evidência
histórica; não significa que elas permaneceram congeladas durante o uso posterior.

### Prévia final: runtime curto e caminho de saída longo

O teste de aplicativos encontrou um diálogo modal de erro do KIO com runtime
longo. A prévia também construía `XDG_RUNTIME_DIR` a partir de `--saida`, que
aceita caminhos longos. Agora os relatórios e recursos permanecem na saída
escolhida, e os sockets usam um diretório temporário curto, próprio do UID, 0700.
O manifesto registra sua identidade; nonce, UID, modo e ausência de symlink são
conferidos antes do uso e da remoção. Supervisor/guard removem somente esse
runtime, após encerrarem os processos próprios confirmados.

**26/26** verificações passaram em
`/tmp/irix-domainos-runtime-preview-longo-r2/RESULTADO.json`. A saída tem 199
caracteres; o runtime efetivo tem 23. O teste usa o entry point real da prévia,
Xvfb externo próprio, Xephyr/KWin/barramento internos próprios e QML de produção.
Um observador C++ descartável acrescenta somente coordenadas/estado de modal.
Cliques XTest com pressão, observação e soltura abrem GNU/LINUX, All Applications,
busca e entrada; um Desktop Entry privado lança o marcador pelo Kicker real.
Nenhum modal ou erro de socket KIO/QML foi observado. Não se afirma que esse erro
tenha ocorrido em p001532, nem que o caminho completo do socket falho tenha sido
capturado no ensaio anterior.

O resultado inclui **11/11** de inicialização e **9/9** do Pager: quatro trocas
2→1→2→1, UUIDs e filtros nativos estabilizados antes das capturas. Painel e
referência próprios permanecem visíveis em ambas as áreas e fora do TasksModel;
os três terminais pertencem à primeira área. `ENCERRADO.json` confirma processos
próprios encerrados, hashes preservados e runtime removido. As nove guardas de
UID/nonce/root/symlink/limpeza são ensaios de API, não testes em outro perfil.
A tentativa r1, que falhou por include ausente no observador antes de alocar o
runtime da prévia, permanece preservada.

Captura conferida: `/tmp/irix-domainos-runtime-preview-longo-r2/NATIVE-CATALOG-AFTER.png`.
Reprodução: `python3 plasma/tools/testar-domainos-runtime-preview.py --saida /tmp/novo-diretorio`.
SHA-256 final de `prever-domainos-funcional.py`:
`380a74e443e2c4282f2242919f1ffd20f0c859a14718244d172da5a35d4aca70`.

### Entrega corrente após F29, New Desktop e runtime

As provas anteriores de entrega r6 e portátil r2 foram preservadas e precedem
estes últimos deltas. A entrega corrente está nos seguintes resultados:

| Resultado | Escopo observado |
| --- | --- |
| `/tmp/irix-domainos-entrega-20261008-r7-native-final/RESULTADO.json` — **22/22** | Instalador público em HOME/XDG privados: quatro destinos finais exatos, backups, repetição idempotente e restauração byte a byte. Recibo `c85245c2d7d547d99c0377be95a3bd99` restaurado; oito preferências reais intactas. |
| `/tmp/irix-domainos-validacao-sessoes-r7-verificacao/RESULTADO.json` — **13/13** | Snapshot offline r7, 149 fontes/152 arquivos totais, manifesto e permissões conferidos; `--verificar` privado sem escrita, display ou bus. Seis diferenças para r6: três QML e três manuais do applet. |
| `/tmp/irix-domainos-teste-pacote-r3-verificacao/RESULTADO.json` — **20/20** | Portátil r3 com 28.510 fontes, 28.514 arquivos e 2.096 links internos resolvíveis. Ambos `--verificar` passaram sem alterar raízes privadas; r2 preservado. Inclui o wrapper de runtime curto com SHA final. |
| `/tmp/irix-domainos-instalacao-lsi-20261008-r7-current-manuals-final/RESULTADO.json` — **5/5** | Instalação pública somente em lsi: quatro destinos coincidem com as fontes correntes, oito preferências iguais no intervalo, recibo independente. Nenhum widget/painel ativado ou substituído. |

Recibo corrente de lsi:
`/home/lsi/.local/state/irixium-domainos/backups/d77376e664f848b39feb42b8cf563a36/receipt.json`.
Esta atualização alterou somente o applet; os outros três destinos já coincidiam.
A atualização r6, anterior à última correção textual do manual, conserva seu
resultado 5/5 e recibo `be3ba1953c2e434ba8600152323d741f` como histórico.
Restaurar o último recibo recupera somente os destinos que aquela execução mudou;
não desfaz automaticamente instalações mais antigas dos componentes intactos.

Após os dois preflights, `/tmp/irix-domainos-teste` foi atualizado atomicamente
para `/tmp/irix-domainos-teste-pacote-r3/plasma/tools/testar-domainos-sessao.py`.
O roteiro atual é `/tmp/irix-domainos-teste-pacote-r3/README-TESTE.txt`. Arquivos
0644, diretórios/launcher 0755 e PNG aprovado 0444 permitem leitura por p001532,
sem escrita por outro usuário. O PNG conserva SHA-256
`f3541fd49c928f829832e437b9193cd84ff08f6e9e819664fdacce43fdae4266`.

O preflight usa `DISPLAY=:65535` somente como marcador não vazio, sem conexão
gráfica. Preparar estas entregas não abriu sessão real nem instalou em p001532.
Para avaliar, o próprio usuário executa `/tmp/irix-domainos-teste` pelo Alt+F2 da
sua sessão KDE e fecha a janela externa ao terminar. A avaliação pessoal e a
substituição do painel ativo continuam pendentes da autorização prevista no goal.

### Gaveta: lançamento positivo pela cadeia de produção

A auditoria distinguiu os ensaios de aplicativos 23/32, cujo `openApplication`
dos pins era um duplo de contrato, da prova positiva do helper compartilhado no
ensaio de correio29. Esses resultados anteriores não comprovavam, juntos, um
lançamento observado pela cadeia completa da gaveta.

O ensaio dirigido passou **30/30** em
`/tmp/irix-domainos-pin-lancamento-native-r2/RESULTADO.json`:
`DomainOSApplications.launchPin` → `DomainOSRuntime/DomainOSCommands` →
`commands.py` intacto → KIO instalado (`/usr/bin/kioclient`). Após abrir a gaveta
real, a API do controlador lançou um Desktop Entry privado, com argumentos
literais conferidos no processo. A janela X11 **8388615**, PID **2510306**, surgiu
no TasksModel com os mesmos IDs do marcador; nenhuma entrada de launcher foi
acrescentada às tarefas, e o pin permaneceu disponível na gaveta.

O helper retorna **`request-accepted`**, token 1. O Runtime/Activity reais
passaram de `pending=1/lit=true` imediatamente após o pedido para
`pending=0/lit=false` com a janela ainda aberta. Isso comprova a conclusão do
pedido observado, sem atribuir conclusão à aplicação. O efeito real do
lançamento é comprovado separadamente por PID, janela, metadados e argumentos.

O teste usa Xvfb/KWin/barramento/HOME/XDG privados, runtime curto, oito hashes de
preferências reais e fontes de produção preservadas. Processo próprio encerrado
com pidfd após verificar seu script/ambiente; daemons próprios encerrados e
runtime removido. É prova de API após abertura da gaveta, sem clique físico na
barra inteira, sem sessão pessoal/Wayland e sem rastreamento strace. As capturas
auxiliares da gaveta e janela Qt não são comparação da arte do painel completo.

A tentativa r1 `failed` permanece preservada: o interceptor do observador do
teste foi herdado pelo programa próprio. A r2 remove somente `LD_PRELOAD` do
`Exec` privado e protege o observador para executar apenas no host identificado;
nenhuma correção de produção foi necessária. Fontes/hashes/limites estão em
`TEST-SOURCES.json` e `F32-PROVA-FINAL.md` no diretório do resultado.
Reprodução: `python3 plasma/tools/testar-domainos-pin-lancamento.py --saida /tmp/novo-diretorio`.
Este novo instrumento está fora dos quatro componentes distribuídos; o payload
instalado em lsi e os snapshots r7/r3 permanecem com os mesmos bytes conferidos.

### Resumos pessoais recebidos e limite da avaliação final

Na conferência posterior foram encontrados os resumos públicos
`/tmp/irix-domainos-teste-uid1000-2c96370c8dfd-resumo.json` e
`/tmp/irix-domainos-teste-uid1003-f84a11039b85-resumo.json`. Cada um registra
**11/11** verificações de inicialização e **9/9** de Pager. Os timestamps dos
resumos antecedem o manifesto do portátil r3; eles não incluem hashes de fontes.
São evidência do escopo da prévia daquela rodada, sem comprovar a avaliação manual
com as correções finais de F29/New Desktop/runtime.

O ENCERRADO acessível de lsi confirma hashes preservados, processos próprios
encerrados e lista restante vazia. O resultado privado de p001532 permanece
protegido; não se tentou contornar suas permissões. O resumo público registra o
estado de inicialização, não confirma sua limpeza nem que a prévia continue viva.
A consulta ao namespace de processos disponível não encontrou handle atual para
uma prévia; não permite concluir o estado dos processos protegidos de outro usuário.

A auditoria documental/funcional final não encontrou outra lacuna material que
justifique repetir os ensaios isolados. Corrigiu-se VF16, que ainda negava a abertura
real do KHelpCenter já comprovada por aparência/ajuda31. Permanecem pendentes a
autorização/avaliação das sessões e ações reais previstas; o arraste do Pager
permanece adiado, e integrações de contas não escolhidas não viraram novo requisito.

### 2026-10-09 — menus cortados na borda da prévia

Os prints recebidos revelaram um defeito adicional de posicionamento. A prova
anterior não conferia todos os rótulos dentro da janela e da tela. A reprodução
`/tmp/irix-domainos-menus-baseline-r6/RESULTADO.json` registra **10/10** gates de
reprodução: Ajuda/Sessão aparecem em y=802 com 98 pixels de altura numa tela de
850 pixels; as últimas opções ficam fora da tela. Esse resultado positivo
significa que o defeito antigo foi reproduzido, não que os menus antigos passaram.

`DomainOSPopupPlacement.qml` mede todos os itens/separadores antes de abrir,
escolhe acima/abaixo conforme o espaço e limita a posição ao monitor do botão.
Usa o pai não escalado da janela para manter o tamanho físico do menu. A medição
do ListView sozinho ainda retornava a primeira linha na abertura inicial; por
isso a altura/largura vêm dos tamanhos naturais dos itens. Nenhum timer, atraso
ou repaint adicional foi colocado no painel. Ajuda, Sessão, operações/fallback
da Iconbox e contexto do Pager compartilham essa regra. A âncora original do
botão de Ajuda é guardada separadamente para o diálogo local.

No [posicionador oficial Qt 6.8.2](https://raw.githubusercontent.com/qt/qtdeclarative/v6.8.2/src/quicktemplates/qquickpopuppositioner.cpp),
o caminho de Popup.Window retorna antes das regras de margens/inversão de
Popup.Item. Somente acrescentar `margins: 0` não resolveria esse caso.

`/tmp/irix-domainos-menus-native-r3/RESULTADO.json`: **12/12**, vinte aberturas
com produção real em Xvfb → Xephyr/KWin/D-Bus próprios. Ajuda/Sessão/Pager usam
cliques físicos; operações e fallback usam APIs do controlador com as três
janelas próprias. Quatro posições: inferior, superior, esquerda e direita.
Todos os rótulos e janelas ficam dentro da tela desde a primeira abertura;
os menus de três itens mantêm altura nativa de 98 pixels na barra em escala 0,5.
Sem despacho de comandos ao abrir, sem erros QML, processos/runtime próprios
encerrados e hashes das preferências reais preservados. Capturas
`bottom-help.png` e `bottom-session.png` conferidas visualmente.
`/tmp/irix-domainos-comandos-menus-r3/RESULTADO.json`: contrato **23/23** após
a correção; bloqueio somente contra serviço privado do teste.

A prévia também passa a ler os dois temas públicos de ícones por links no seu
diretório privado, evitando cerca de 28 mil novos arquivos a cada execução.
Configurações e caches continuam privados. Para recuperar inodes de /tmp, somente
os ícones de duas provas próprias já encerradas, `irix-domainos-runtime-preview-longo-r2`
e `irix-domainos-preview-pager-sticky-r2`, foram arquivados. Cada
`ICONES-RECURSOS-ENCERRADOS.tar.gz` contém 28.419 entradas verificadas
por hashes/tipos/links antes de retirar as cópias. Relatórios, logs e capturas
permanecem; nenhum pacote anterior ou backup aprovado em Downloads foi alterado.

A prova final estendida `/tmp/irix-domainos-menus-native-r6/RESULTADO.json`
passou **19/19**: vinte posições dos cinco menus, mais clique real na ajuda
local e hover real no submenu Processo junto à borda direita. O observador
confirma `commands.helpAnchor` e `localHelp.parent` como
`domainosShortcut_help`. A janela de ajuda foi capturada após pintura completa;
o submenu termina em x=1598 numa tela de 1600 pixels. Ambas as capturas foram
conferidas visualmente. Dois links de ícones apontam aos recursos públicos
esperados; hashes dos dois `index.theme` permanecem iguais. Esse último gate
não é um hash recursivo de todos os ícones. Preferências reais preservadas,
processos próprios encerrados e runtime removido. As tentativas anteriores
permanecem, incluindo a falha r4 na inicialização privada antes dos menus
(modelo de tarefas observou duas das três janelas próprias), superada nas
provas r5/r6; não se apresenta essa tentativa como teste positivo.

A entrega dirigida r8 `/tmp/irix-domainos-entrega-20261009-r8-menus/RESULTADO.json`
passou **22/22** em raízes privadas: instalar, repetir e restaurar os quatro
destinos, agora com o novo QML de posicionamento. A instalação lsi r8
`/tmp/irix-domainos-instalacao-lsi-20261009-r8-menus/RESULTADO.json` passou
**5/5**, quatro destinos exatos e oito preferências iguais; recibo
`2a456685fb4c48d2a6b1cd701a53e474`. Nenhum painel foi ativado/substituído.
O offline r8 `/tmp/irix-domainos-validacao-sessoes-r8-menus-verificacao/RESULTADO.json`
passou **13/13**, 150 fontes/153 arquivos, verificação seca sem sessão gráfica.

O portátil `/tmp/irix-domainos-teste-pacote-r4-menus` passou **20/20**:
28.511 fontes/28.515 arquivos e 2.096 links internos. R3 preservado por
bytes/links/modos/UID; fontes mudadas têm cópias independentes. Recursos públicos
idênticos compartilham arquivos regulares, cujos conteúdos/modos não são escritos.
O tmpfs também contabiliza entradas de hard links no limite de inodes; a primeira
preparação não coube. Somente sua cópia R4 incompleta foi retirada, com registro
em `/tmp/irix-domainos-preview-r4-falha.txt`. Após o arquivamento reversível das
cópias de testes encerrados, a segunda preparação passou integralmente.

`/tmp/irix-domainos-teste-pacote-r4-menus-verificacao/CORTE-LAUNCHER.json`:
**8/8**, troca atômica do launcher próprio `/tmp/irix-domainos-teste` para r4;
o launcher real com `--verificar` saiu zero em HOME/XDG privados sem GUI.
O PNG aprovado mantém SHA f3541fd49c928f829832e437b9193cd84ff08f6e9e819664fdacce43fdae4266.
Nenhuma sessão pessoal ou instalação em p001532 foi executada nesta rodada.
Para carregar o novo snapshot, fechar a prévia antiga e reabrir o mesmo comando;
isso não exige reiniciar a sessão nem substituir o painel de uso diário.

Após reabrir pelo comando de teste, chegou o resumo público de p001532
`/tmp/irix-domainos-teste-uid1003-c071964c36c7-resumo.json`: inicialização
**11/11** e Pager **9/9**, sem erros QML. Seu timestamp é posterior ao corte r4.
O resumo não inclui hashes das fontes nem aberturas dos menus, portanto não
comprova sozinho a versão exata carregada ou a avaliação visual de Ajuda/Sessão.
Não se acessou o resultado privado protegido desse usuário. Em seguida, o usuário
confirmou que Ajuda e Sessão mostram todas as opções, inclusive a última, dentro
da tela da prévia reaberta. Essa confirmação visual fecha a queixa de corte dos
menus; permanece distinta dos vinte gates automáticos e não representa aprovação
para substituir painéis ou executar ações reais de sessão.

### 2026-10-09 — quadros nas quatro bordas, após o aceite dos menus

A auditoria encontrou posições fixas acima da barra em outros `Popup.Window`.
O ensaio dirigido `plasma/tools/testar-domainos-quadros.py` abre e cancela sete
quadros nas quatro bordas: aviso de falha, ajuda local, seletor de grupo,
continuação da bandeja, status, nome de área e confirmação de remoção.
Não confirma CRUD nem aciona serviços, janelas, áudio, dispositivos ou sessão.
Os quadros de instrumentos continuam usando `PlasmaCore.Dialog`; não receberam
esta mudança de posicionamento.

Baseline congelado `/tmp/irix-domainos-quadros-baseline-r7/RESULTADO.json`:
**18/18 verificações e 28 amostras**, com o gate positivo exigindo reproduzir
o defeito anterior. Três quadros cortaram no alto da tela: grupo
`x=650,y=-172,w=400,h=172`, continuação `x=1118,y=-146,w=136,h=144` e status
`x=881,y=-282,w=400,h=270`. Os quatro diálogos restantes couberam sob o KWin X11
deste ensaio; não se afirma que estavam quebrados.

Fonte corrigida `/tmp/irix-domainos-quadros-native-r1/RESULTADO.json`:
**18/18 e 28 amostras**, todos os quadros e rótulos dentro da tela. As três
capturas `top-group.png`, `top-overflow.png` e `top-status.png` foram conferidas
visualmente. `DomainOSPopupPlacement` limita a moldura ao monitor e escolhe
espaço acima/abaixo, convertendo a posição pela âncora real. Diálogos de áreas
conservam a centralização no host, com limites do monitor. Reposicionamento usa
os sinais de abertura/tamanho, sem Timer, espera ou ciclo de repaint na produção.
A ajuda conserva seu botão original como parent; desenhos, dimensões e ações
do painel permanecem os mesmos.

O observador usa bootstrap próprio para estes quadros, sem repetir a troca de
áreas do autoensaio Pager. Seu bootstrap reduzido tem seis verificações e não
é apresentado como o startup11 original. As tentativas r1–r6 continuam salvas:
nenhuma era prova aprovada dos 28 quadros; r6 materializou vinte amostras dos
cinco quadros principais antes da falha de prontidão do watcher. O teste final
usa dois xterms próprios agrupados pelo TasksModel real, desabilitando o limiar
de agrupamento apenas no controlador descartável, sem gravar essa preferência.
O watcher nativo tem PID igual ao kded6 próprio, com autoload somente do módulo
statusnotifierwatcher no KConfig privado; oito serviços SNI próprios produzem
o overflow real. Seus registros de ações permanecem vazios. Nomes/UUIDs das
áreas, comandos, hashes das fontes e quatro preferências reais foram preservados;
processos próprios encerrados e runtime removido.

A regressão `/tmp/irix-domainos-menus-native-r7-quadros/RESULTADO.json` passou
**19/19**, vinte posições dos cinco menus, ajuda local por clique e submenu
Processo por hover. Não soma suas amostras às dos sete quadros. A instalação,
repetição e restauração privadas R9 passaram **22/22** em
`/tmp/irix-domainos-entrega-20261009-r9-popups/RESULTADO.json`; recibo
`6cd0a6f77af14f7693f1c5560c771ccb`, fontes exatas e oito preferências intactas.

A instalação própria lsi R9 passou **5/5** em
`/tmp/irix-domainos-instalacao-lsi-20261009-r9-popups/RESULTADO.json`, recibo
`a946085d8131442fa8214fc5534541d7`: quatro destinos exatos e oito preferências
iguais, sem ativação de painel. O offline R9 passou **13/13**, 150 fontes e
153 arquivos, em `/tmp/irix-domainos-validacao-sessoes-r9-popups-verificacao/RESULTADO.json`.
O R8 foi preservado por bytes/modos/UID.

O portátil R5 `/tmp/irix-domainos-teste-pacote-r5-popups` passou **20/20**:
28.511 fontes, 28.515 arquivos e 2.096 links internos. Cinco QMLs mudados têm
cópias independentes; o R4 continua igual por bytes/links/modos/UID.
`/tmp/irix-domainos-teste-pacote-r5-popups-verificacao/CORTE-LAUNCHER.json` passou
**8/8**: o comando `/tmp/irix-domainos-teste` agora aponta ao R5, preservando seu
papel de prévia Xephyr privada. A verificação do launcher saiu zero em raízes
privadas, sem GUI. O PNG aprovado permanece igual. Para obter mais inodes,
somente os recursos duplicados de ícones do ensaio automático já encerrado
`/tmp/irix-domainos-funcional-cleanup-r2-20261008` foram arquivados/verificados e
retirados: 28.420 entradas com nomes, tipos, bytes, links, modos e UID/GID iguais
no tar; os dez PIDs registrados estavam ausentes e seus relatórios ficaram intactos.
O ensaio menus-native-r1 tinha somente três entradas de links/diretório e também
conserva seu arquivo de recursos e verificação, sem alterar os alvos públicos.
Nenhum resultado privado de usuário ou backup em Downloads foi usado nessa limpeza.

Para a avaliação pessoal restante foi preparado `/tmp/irix-domainos-teste-real`,
legível/executável como cada usuário. Ele confere o manifesto offline R9 e
dependências, instala apenas os quatro componentes no próprio XDG e abre
`plasmawindowed org.irixclassic.domainos.panel` numa janela independente. Não
aplica esquema/Style ou insere painel. `--verificar` apenas confere recursos;
essa rota passou **6/6** em
`/tmp/irix-domainos-teste-real-verificacao-r9/RESULTADO.json`, com HOME/XDG privados,
sem display/bus de sessão, raízes e oito preferências reais intactas. A rota de
instalação/GUI deste comando ainda não foi executada nas sessões pessoais.

O goal R2 exige autorização de cada sessão para essa validação. Não exige
substituir a barra atual nem executar logout/suspensão/hibernação. Restam uma
avaliação curta da janela real em lsi/p001532 — cores, fonte, relevo, quadros,
provedores da bandeja e categorias de preferências próprias — e uma confirmação
autorizada do cadeado real após desbloquear. O transporte privado do ScreenSaver
não comprova esse último gate. Contas ou itens de mensagens não configurados
continuam condicionais/indisponíveis; nenhuma integração pessoal será inventada.

### 2026-10-09 — alcance dos snapshots após a decoração opcional

A inclusão posterior de **DomainOS SR10.4** como opção de decoração acrescentou
um componente ao catálogo do repositório: agora são **31**. Os snapshots offline
R9 e portátil R5 permanecem preservados com o catálogo de **30 componentes**
capturado antes dessa inclusão. A comparação de todas as fontes registradas
nos dois manifests encontrou somente `components.json` diferente do repositório
atual. Os quatro recursos do painel, helpers e wrapper continuam iguais;
`MANIFEST.sha256` do R9 e `PREVIEW.sha256` do R5 ainda conferem integralmente.
Os quatro destinos instalados no lsi também permanecem iguais às fontes atuais.

A decoração `domainos_sr104` tem instalador, estado e prova de restauração
independentes: `/tmp/irix-domainos-decoration-entrega-r3/RESULTADO.json`, **24/24**.
Ela não é dependência nem um dos quatro destinos de `tools/install_domainos.py`;
sua ausência nesses snapshots não altera o teste do painel. A conferência
conjunta de leitura passou **20/20** e registra caminhos e hashes em
`/tmp/irix-domainos-goal-auditoria-20261009-catalogo/RESULTADO.json`.

Não se executou novamente a suíte completa nesta auditoria. A prova inicial
de 35 destinos — 30 componentes e cinco cópias de compatibilidade — conserva
seu alcance histórico; não comprova uma instalação completa atual de 36 destinos.
Nenhum snapshot anterior, preferência pessoal ou backup congelado foi alterado.
