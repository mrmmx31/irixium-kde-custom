# DomainOS 0.2.11 — recuperação das travas da bandeja

A atualização reúne a recuperação dos guards da bandeja, portabilidade dos
serviços instalados por usuário e uma rota local da roda nas gavetas.
A limpeza de `refreshing` e `synchronizingVisibility` usa quatro blocos
`try/finally`: `refresh`, `applyVisibility`, inicialização em `attach` e o
sinal nativo `valueChanged`. A pintura, composição, paleta, preferências,
tarefas e Pager conservam seus componentes anteriores. O módulo nativo foi
estendido com o encaminhamento de roda descrito ao fim desta validação.

## Falha e recuperação

O teste público injeta exceções nos limites de `forceLayout`, `itemAtIndex`,
`writeConfig` e setters de configuração. O QML executado é o de produção;
somente os provedores são duplos próprios. Antes da correção, **14/26** critérios
passaram e 12 reproduziram as travas retidas. Depois, **26/26** passaram, incluindo
recuperação por nova chamada/sinal explícito, reentrância e ausência de retry.
As exceções dos sinais continuam no diagnóstico esperado do QML.

Artefatos privados:

- `/tmp/irix-domainos-tray-refresh-failure-before-011-r3/RESULTADO.json`:
  SHA256 `6acdd787eb9a4f0b44374232fae4b06e2e86b7ce50a37eb82a6bfeec97f3ad1f`.
- `/tmp/irix-domainos-tray-refresh-failure-after-011-r1/RESULTADO.json`:
  SHA256 `3c692a038273680ad3dc60fbb953817accfe84617dac44d5d088965bcf06ccc8`.

Falha de gravação pode deixar valores em memória. A prova confirma recuperação
após outra mudança explícita; não afirma rollback, tentativa automática ou
sucesso da gravação recusada. Erros de provedores pessoais e desempenho
universal não são inferidos desse fixture.

## Apresentação e atividade

A fonte corrigida passou novamente **50/50** verificações em Xvfb/DBus privados:
gavetas, segundo clique fechando, recibo de quadro, luz, disponibilidade,
callback falso/exceção e rastreador opcional. A geometria e o único timer da
preferência de luz após a conclusão permanecem iguais.

Artefato: `/tmp/irix-domainos-tray-activity-guard-fix-20261009-r2/RESULTADO.json`,
SHA256 `5a8252fe4510bbaddb5806875501d9e0344c023e302cc8e29a591d3b3ef3bce3`.
A primeira tentativa foi impedida pela restrição de socket do sandbox antes
do ensaio; seu log foi preservado. A execução seguinte usou somente uma
sessão Xvfb/DBus própria, sem recarregar um Xephyr ou Plasma pessoal.

O SHA256 de `DomainOSTray.qml` nos dois ensaios corrigidos é
`64bcf1676be7fad1c50436d153fd30dafbe225e8db4e9d3831fbd680e8630b15`.
A revisão independente confirmou equivalência do caminho de sucesso frente ao
ZIP0.2.10 e ausência de timer, catch, retry ou mudança de desenho.

As provas históricas da [0.2.10](VALIDACAO-DOMAINOS-0.2.10-2026-10-09.md)
mantêm seus limites. Relatórios, observador e perfis privados não entram no
pacote. Esta validação não afirma instalação ou aceite pessoal de lsi/p001532.

## Portabilidade dos instaladores e das prévias

As fontes são localizadas a partir do próprio script; os destinos usam HOME e
XDG do usuário que o executa. O helper do hook opcional Classic agora instala
suas dependências em `XDG_DATA_HOME/irixium/hooks/classic`. O serviço deixa de
depender da pasta extraída. A migração só reconhece comandos legados exatos
daquela origem, preserva serviços personalizados e não habilita nem inicia
serviços. A instalação opcional explícita mantém esse comportamento próprio.
O ZIP DomainOS inclui o helper para resolver os imports compartilhados, mas
instala somente seus quatro recursos e não aciona o hook Classic.

O teste `tests/test_hook_migration.py` passou **13/13**, sem skips: migração,
repetição, quoting, preservação de serviço/configuração, rollback e restauração.
Um checkout extraído com espaços, `%`, `$` e aspas foi apagado antes de executar
duas vezes o `manage.py` instalado. As ferramentas KDE de configuração eram
reais; seleção alternativa e bytes de `kwinrc` permaneceram iguais. Chamadas
systemd foram interceptadas, portanto isso não afirma execução de um serviço
real. A restauração cobre os arquivos, sem alterar o enablement do systemd.

Artefato: `/tmp/irix-classic-hook-portable-20261009-r1/RESULTADO.json`, SHA256
`4d89720215281dc3b74892d7d997d7ef1bd8e8302a3f93fe27392e96c591228d`.

A ponte opcional de estilos recebeu a mesma distinção de escapes: `$$` em
`ExecStart`, `$` literal em `Environment`. Seus **10/10** testes usaram raízes
XDG com espaços, `%`, `$`, aspas e barra invertida. O runtime instalado executou
`--verificar` depois de apagar o checkout de origem; repetição e restauração dos
arquivos foram conferidas, com chamadas systemd interceptadas.
O parser real do systemd 257 aceitou a unidade com `verify --user --man=no
--generators=no`, sem avisos e sem iniciar serviço. Isso verifica sintaxe e
executável; não afirma execução de um serviço nem restauração de enablement.

Artefatos: `/tmp/irix-domainos-style-bridge-dollar-20261009-r1/RESULTADO.json`
(SHA256 `8bf389f52eae8cfa9ae591fded912774310b959cb5f66713d6da7197fbc0d1dc`)
e `/tmp/irix-domainos-style-bridge-systemd-parser-20261009-r4/RESULTADO.json`
(SHA256 `ba0b04cd7096d4d25180c1b472ad89de73d5c7121d2d4076a7284c54d0e0d22c`).

A busca independente em **2.908 arquivos textuais publicáveis** dos runtimes
e 31 componentes não encontrou os dois nomes pessoais usados no ambiente de
desenvolvimento. Incluiu arquivos Wine UTF-16 e excluiu testes, documentação
histórica e metadados de proveniência. Não é análise de toda dependência
semântica nem de binários. Recibo:
`/tmp/irix-domainos-public-runtime-path-audit-20261009-r1/RESULTADO.json`,
SHA256 `28a40867729683f9083cb50d195fa0b0b3c37468abb6b05fede117a69cbdc912`.

Os guardas da galeria completa também deixaram de citar um usuário específico.
O namespace admite somente seu HOME fictício; a comparação da decoração recebe
a imagem por `--referencia`, sem procurar em Downloads pessoais. Sete casos
dirigidos passaram **49/49** verificações de identidade, namespaces e rejeição
de HOME extra, sem abrir GUI ou serviços. Artefato:
`/tmp/irix-tema-completo-guardas-011-20261009-r1/RESULTADO-r1.json`, SHA256
`6d04ee16615f541070f6525c4b669945481c131f3f97456ff33e34342f5aa1d0`.

## Diagnóstico anterior do Volume em overflow

O primeiro ensaio nativo dirigido de F16 passou **55/57**. O applet Volume instalado,
com PulseAudio/null sink, kded/atalhos e barramento próprios, ajustou o volume
de 50% para 55% e de volta para 50% por XTest no slot. Roda sobre vizinhos SNI
e chapa não alterou o volume. Na gaveta de overflow, as duas direções da roda
não chegaram ao compacto Volume e o volume permaneceu em 50%; no mesmo popup,
o vizinho SNI recebeu seus eventos reais. Naquele ponto, a causa completa de
dispatch não havia sido determinada. Esse ensaio não aprovou F16 no overflow.

Dois candidatos de encaminhamento por célula, MouseArea e WheelHandler, também
falharam e foram revertidos. A fonte então conservou o SHA `64bcf167…`, o mesmo
dos ensaios positivos de recuperação/atividade acima. Não se reteve proxy de
volume ou correção sem prova. Nenhum Xephyr existente, servidor de áudio ou
perfil pessoal foi alterado.

Auditoria: `/tmp/irix-domainos-volume-wheel-011-audit-20261009.json`, SHA256
`4525cea9ac917f3e78328de8760dea4ce1d60e8d3f2c0852ef7390df15b5e644`.

## Roda nativa nas gavetas — prova final de produção

A observação dirigida identificou a rota do Qt 6.8.2/XCB: a gaveta prende a
entrada na janela dona, mas o evento de roda chegava à dona sem ser entregue
à janela do popup. O módulo opcional agora encaminha somente eventos
espontâneos `NoScrollPhase` dessa dona para as duas gavetas explícitas da
bandeja, enquanto abertas e sob o ponteiro. Há guardas de identidade, vida
útil, reentrância, thread e janela superior; não há filtro global, timer,
grab novo, ação de volume ou repetição. A cópia mantém deltas, posições,
dispositivo e timestamp, mas é uma entrega síncrona não espontânea.
As outras versões, plataformas e fases mantêm a rota original.

Outro problema era independente: itens nativos estacionados com `opacity:0`
ainda habilitados recebiam a roda atrás do item visível. O estacionamento
agora está desabilitado para entrada. Os provedores conservam seu `enabled`
explícito, e a adoção/restauração de pai visual conserva seu funcionamento.

O stage final, sem filtro experimental no host, passou **121/121** critérios
com Volume instalado, XTest e PulseAudio/null sink privados. Oito gestos de
Volume — slot, gaveta, reabertura e reparentamento, em ambas as direções —
produziram exatamente um despacho nativo e a variação esperada de 5% cada.
Os quatro gestos SNI chegaram somente ao item apontado; vizinho, chapa e
borda não alteraram volume. Abrir a representação completa, menu nativo e
silenciar/restaurar também passaram. O detach restaurou a identidade de pai
original capturada, inclusive `null`, nove itens e o mesmo compacto nativo.
Houve zero erros QML e nenhum arquivo de configuração ou fonte alterado.

`ScrollUpdate` e `ScrollMomentum` foram injetados pelo QPA somente na janela
própria: os guardas não copiaram eventos nem acionaram Volume. Isso prova a
fronteira do adaptador; não é teste físico de touchpad nem aprovação dessas
fases na gaveta. Wayland, outras versões Qt, hardware e perfis pessoais ficam
fora deste ensaio.

Artefatos privados:

- `/tmp/irix-domainos-popup-wheel-final-011-20261009.json`: SHA256
  `5ee185abbf3aecba7f48bae61c199187b89e2b9325e8918a47f445d82319af27`.
- `/tmp/irix-domainos-volume-wheel-011-r18/RESULTADO.json`: SHA256
  `6d6f4d5909fdea36764f5cc297df240f4003e1ad007324aedc51fd0e4cf004ce`.
- `/tmp/irix-domainos-tray-refresh-wheel-fallback-20261009-r2/RESULTADO.json`:
  recuperação sem o módulo carregado, **26/26**, SHA256
  `df68ce11aa206568c174dc795d9b57e1ba94671dd32b35f06dcf65cfbb2465e2`.

O módulo final tem SHA256
`60734648f19cf08d790eb94d97069c1e9373942383e4391ed5d1a51365542c21`;
o manifesto confere suas sete fontes e ABI. Os resultados intermediários
94/95 e 107/108 foram preservados: o primeiro revelou o item estacionado;
o segundo exigia equivocadamente pai original não nulo no fixture. A prova
final captura a origem antes da adoção, sem reclassificar esses brutos.

A causa foi conferida nas fontes oficiais do
[PopupWindow do Qt 6.8.2](https://raw.githubusercontent.com/qt/qtdeclarative/v6.8.2/src/quicktemplates/qquickpopupwindow.cpp),
[processamento de roda](https://raw.githubusercontent.com/qt/qtbase/v6.8.2/src/gui/kernel/qguiapplication.cpp)
e [DeliveryAgent](https://raw.githubusercontent.com/qt/qtdeclarative/v6.8.2/src/quick/util/qquickdeliveryagent.cpp).
As prévias existentes não foram recarregadas; esta é prova do stage privado.

## Operações em lote em duas saídas Wayland

O ensaio identificou um defeito real no helper anterior: minimizar uma janela
antes de confirmar sua transferência de saída podia impedir o commit Wayland.
O resultado correto daquele pedido foi `partial-request`, confirmado por uma
observação independente do KWin. O bruto R3 permanece preservado.

O helper corrigido registra a emissão por alvo e aplica a minimização somente
quando desktop e saída atuais são confirmados. Uma janela previamente minimizada
em outra saída é restaurada para permitir o commit e então minimizada novamente.
Não há timer de ação, repetição ou alteração de alvos não selecionados. A guarda
de reentrância e o `finally` protegem os sinais síncronos; exceções assíncronas
continuam sendo reportadas. A operação não é uma transação visual atômica.
O mecanismo utiliza a [API pública do KWin](https://develop.kde.org/docs/plasma/kwin/api/).

Provas de produção em KWin privado, com duas saídas virtuais reais:

- R6, **68/68**: minimização normal para Virtual-0, janelas já minimizadas
  para Virtual-1 e coleta conservando estados minimizados. IDs/PIDs, capacidades,
  destino, exclusões, restauração dos desktops originais e encerramento conferidos.
- R7, **41/41**: regressão dirigida de colunas de três janelas para Virtual-1,
  incluindo duas previamente minimizadas; geometrias e commits confirmados.
- Ambos os stages conferem byte a byte com as seis fontes atuais dessa cadeia.
  Os nove layouts para 2/3/6 janelas e a maximização têm provas anteriores
  qualificadas; não foram repetidos nem atribuídos integralmente à revisão final.

Relatório consolidado: `/tmp/irix-domainos-batch-two-outputs-011-final-20261009.json`,
SHA256 `436904b19e6d65fef0bcc95d6d3ba0de97dbd03e030ef542045a170a9ecc8cac`.
R6: SHA256 `b7a59af192364c5128262547f893eb7f17397836de54ad8b8eee9971e67f7b61`.
R7: SHA256 `487dbeb0a817e5bda5099d1a7a813b16777541ca0b0d746382ac4379079539ca`.
Helper final: SHA256 `3b942297616dac0b32c3ed18241c75611f426782002abb37fb9db9abaa2ba728`.
Seleção usa a API real de checkboxes do controlador; cliques físicos têm prova
separada. Monitores físicos, perfis pessoais e Xephyr existentes não foram alterados.

## ConfigView e política de cache dos ensaios

O diálogo instalado do Kirigami reproduz os erros `None/Success` sem o painel
quando `QML_DISABLE_DISK_CACHE=1`. Com a política normal e cache XDG novo e
privado, o ciclo de preferências atual ficou sem esses erros: Aplicar,
Cancelar/Descartar, reabrir, reiniciar e preservar a segunda instância passaram.
Os dois runners públicos conservam esse isolamento e removem somente a variável
que desabilitava o cache. Nenhuma biblioteca ou configuração global foi modificada.

O bruto do novo ciclo permanece **26/27**: seu único gate falho esperava nove
linhas totais no ConfigModel. A fonte atual tem nove páginas próprias e acrescenta
as UIs nativas de feriados/eventos, com visibilidade condicionada à seleção do
provedor. O verificador agora exige cada página própria exatamente uma vez e
aceita somente arquivos existentes de configuração de plugins nativos de calendário.
Não reclassifica a execução antiga nem afirma uma nova medição de VisibleRole.

O complemento do verificador passou **17/17**, usando o mesmo bruto e incluindo
recusas de páginas ausentes, duplicadas, arquivo estranho e plugin inexistente:
`/tmp/irix-domainos-configview-public-verifier-011-20261009-r1.json`, SHA256
`26d3cfe64560dc971209515831b7fded3ec9d47d1dbaf82aad56522fef440e03`.
O ciclo nativo preservado está em
`/tmp/irix-domainos-configview-cache-native-011-20261009-r2/RESULTADO.json`.

## Tema global, padrões do KDE e GTK

A regressão relatada na prévia completa foi reproduzida: o KDE escreve os
padrões do tema global em `kdedefaults` e remove as chaves explícitas da seleção.
O launcher descartável usava apenas `/etc/xdg` como fallback, omitindo a pasta
de padrões do próprio perfil. Isso deixava o Qt e a decoração em Breeze mesmo
quando os padrões gravados apontavam para Classic. O launcher agora usa a mesma
precedência do startplasma, sem forçar estilo, paleta ou layout. A ponte opcional
de estilos também observa esses padrões, respeitando overrides explícitos,
inclusive uma chave vazia. Instalação não inicia essa ponte.

O ensaio nativo de KSharedConfig, QApplication e Plasma::Theme passou **27/27**,
com CLI real Breeze → Classic e Breeze → Irixium. As cores, a seleção do QStyle
e as chaves da decoração foram observadas em HOME/XDG privados. O teste da
ponte passou **16/16**, incluindo mudanças só no fallback, substituições
atômicas, precedência, chave vazia e recusa de arquivos inválidos.

Na nova sessão Xephyr, os cinco pedidos nativos Breeze → Classic → Breeze →
Irixium → Classic passaram; os cinco pares de pixels medidos acompanharam as
cores esperadas. O bruto R2 ficou **10/11**: seu último critério procurava o
plugin no arquivo de configuração ainda não serializado, embora a barra
continuasse visível. A consulta posterior ao modelo real do Plasma confirmou
o mesmo painel 1/applet 2. Esse complemento não altera o bruto. A revisão
visual conferiu as decorações e os controles Qt nas três variantes. Não prova
seleção automática de subtema Kvantum ou recoloração de GTK.

As primeiras capturas imediatas incluíram quadros pretos ou ainda com a paleta
anterior; permanecem preservadas e não foram contadas como prova visual. O
ensaio R2 aguardou pixels da pintura real apenas na instrumentação de captura.
O primeiro lançamento corrigido também encontrou um timeout de prontidão do
D-Bus; sua falha foi preservada. O lançamento seguinte passou **14/14** barreiras
de isolamento/prontidão, com aplicativos Qt6, GTK3 e GTK4 reais abertos.

GTK2 **2.24.33**, GTK3 **3.24.49**, GTK4 **4.18.6** e GTK Config **6.3.4** foram
conferidos. A seleção completa existente não exige reinstalação a cada troca;
ela seleciona explicitamente GTK/Kvantum. A aplicação nativa de aparência do
tema global não executa scripts arbitrários desses pacotes. O exportador KDE
publica papéis `*_breeze` para GTK3/4, mas o CSS e os bitmaps atuais do Classic
ainda contêm cores fixas. O sufixo não obriga o desenho Breeze.

O teste GTK privado passou **59/59 critérios de reprodução do defeito**: os
papéis azul, amarelo e escuro chegaram aos providers reais GTK3/4 em prioridade
de usuário, mas a janela continuou `#c1c1c1` e o botão `#999999`, inclusive com
widgets novos e processo GTK4 novo. Não é aprovação de integração de cores nem
ensaio do daemon KDE: nesse teste, a fixture forneceu as definições de papéis.
Uma auditoria complementar **6/6** confirmou fontes exatas e carregamento do
Classic, descartando fallback Adwaita. GTK2 exige adaptação própria; GTK4 não
tem a garantia de recarga ao vivo do módulo GTK3. Esses limites permanecem
abertos e estão descritos em `gtk/README.md` na suíte completa.

Outro defeito foi corrigido nos seletores da suíte: o getter nativo lê apenas
a seleção GTK3. Agora sucesso exige confirmar os nomes armazenados em GTK2,
GTK3 e GTK4. Os recibos novos também incluem `gtk.css` e `colors.css` das duas
versões; recibos antigos conservam seu escopo original de cinco arquivos.
Passaram **27/27** testes do seletor e **13/13** da suíte, incluindo escrita
parcial, rollback de bytes/modos, edição posterior e recuperação de Kvantum.
São testes transacionais com doubles de provider; não comprovam recarga de
aplicativos, cancelamento de escrita assíncrona KDE já agendada ou restauração
dos assets CSD que o KDE pode gerar ao selecionar Breeze.

Relatórios privados:

- `/tmp/irix-domainos-kdedefaults-native-011-r3/RESULTADO.json`.
- `/tmp/irix-domainos-style-bridge-kdedefaults-20261009.json`.
- `/tmp/irix-domainos-theme-roundtrip-full-011-20261009-r2/RESULTADO.json` e
  `/tmp/irix-domainos-theme-roundtrip-review-011-20261009.json`.
- `/tmp/irixclassic-gtk-color-roles-native-011-r1/RESULTADO.json` e
  `SOURCE-AND-BASELINE-AUDIT.json` no mesmo diretório.
- `/tmp/irix-gtk-selection-transaction-20261009.json`.

Quatro prévias antigas de lsi foram encerradas após autorização expressa,
somente por PID/UID/argv do próprio supervisor. A prévia atual permaneceu
aberta. Não houve instalação pessoal, alteração de outro perfil ou do backup
congelado em Downloads. O aceite anterior em lsi/p001532 foi reaberto pelo
relato de regressão; estas provas privadas não substituem esse aceite.

A precedência foi conferida no [startplasma 6.3.6](https://raw.githubusercontent.com/KDE/plasma-workspace/v6.3.6/startkde/startplasma.cpp)
e no [gerenciador de temas globais 6.3.6](https://raw.githubusercontent.com/KDE/plasma-workspace/v6.3.6/kcms/lookandfeel/lookandfeelmanager.cpp).
O mecanismo GTK foi conferido na [fonte GTK Config 6.3.4](https://deb.debian.org/debian/pool/main/k/kde-gtk-config/kde-gtk-config_6.3.4.orig.tar.xz)
e na [inicialização GTK4 4.18.6](https://raw.githubusercontent.com/GNOME/gtk/4.18.6/gtk/gtksettings.c).
