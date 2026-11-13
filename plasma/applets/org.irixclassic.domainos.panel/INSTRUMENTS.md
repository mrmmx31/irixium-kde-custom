# Instrumentos nativos — contrato R2

`contents/ui/DomainOSInstruments.qml` fornece dados e quadros suspensos para os
quatro botões já desenhados. Não cria outro painel nem modifica o desenho aprovado.
O componente fica inativo no protótipo visual; a integração funcional o carrega
explicitamente. O backup em Downloads não é usado como diretório de trabalho.

## Ligação ao painel

| Propriedade ou chamada | Uso |
| --- | --- |
| `monitoringEnabled` | Habilita as assinaturas; desabilitar fecha os quadros e impede dados de parecerem disponíveis |
| `domainosPalette`, `popupLocation` | Paleta e posição recebidas da instância |
| `clockHour`, `clockMinute`, `clockSecond`, `currentDateTime` | Fonte `Local` do mecanismo temporal do Plasma |
| `timeAvailable`, `dateText`, `fullDateText`, `timeText`, `localeName` | Disponibilidade e formatação da localidade da sessão |
| `timeZones` | Fontes temporais adicionais; `Local` permanece incluída |
| `calendarPlugins` | IDs selecionados explicitamente; nenhum habilitado automaticamente |
| `metric`, `networkInterface` | `network`, `cpu`, `memory`, `disk` ou `custom`; interface `all` usa o agregado nativo |
| `customSensorId`, `customSecondarySensorId` | IDs nativos para uma seleção personalizada |
| `primaryAvailable`, `secondaryAvailable`, `metricAvailable`, `unitsCompatible` | Valores individuais podem estar disponíveis; o gráfico só aceita um conjunto com a mesma unidade nativa, distinto de um valor real igual a zero |
| `primaryValue`, `secondaryValue`, `primaryText`, `secondaryText` | Valores reais e unidades formatadas pelo KSysGuard |
| `primaryHistory`, `secondaryHistory`, `primarySampleTimes`, `secondarySampleTimes` | Amostras e horários efetivamente recebidos |
| `primaryFraction`, `secondaryFraction`, `scaleMaximum`, `scaleText` | CPU e memória usam escala 100; outras métricas usam o pico observado. Conjunto indisponível não tem escala/frações compartilhadas (`null` / `—`) |
| `showClock(anchor)` | Consulta de hora/fusos, sem calendário |
| `showCalendar(anchor)` | Calendário nativo; agenda apenas com provedor configurado e instalado |
| `showMonitor(anchor)` | Carrega sob demanda o `Grosview.qml` existente do pacote irmão |
| `requestMail()` / `mailRequested` | Encaminha ao serviço de comandos da instância; não lê contas nem inventa contagem |

O intervalo técnico inicial é 1.000 ms e o histórico inicial tem até 60 amostras
por direção. A central oferece 1.000–60.000 ms e 10–1.000 amostras; esses limites
e valores iniciais não foram escolhidos pelo usuário na consolidação R2. Um
valor antigo abaixo de 1.000 ms também é limitado pelo controlador a 1.000 ms.
`sensorSnapshot().samplingLimitMilliseconds` indica esse intervalo efetivo;
`requestedSamplingLimitMilliseconds` conserva o valor pedido apenas para diagnóstico.
O limite de assinatura não força um sensor nativo mais lento a publicar mais
rápido. A fonte temporal permanece em 1.000 ms, independente desse limite:
alterar o monitor não desacelera relógio e consulta de fusos. O monitor detalhado indica o intervalo efetivo, a escala com unidade
e o escopo. Nenhum temporizador de repintura ou espera artificial de ação foi
adicionado. O mecanismo de hora e as assinaturas de sensores fornecem sinais.

O cliente de correio é resolvido por `DomainOSCommands.openMail()` no painel,
com cliente configurado e Thunderbird como fallback quando apropriado. Este
componente apenas emite a solicitação. Não utiliza `mailto:` para abrir uma
composição, não altera associações MIME e mantém `mailStateAvailable=false`.

## Dados ausentes e transições

Valor ausente é `null` / `—`, nunca um zero fictício. Na troca de sensor, o
KSysGuard conserva internamente o valor anterior e encaminha mudanças de estado
como `valueChanged`. O controlador exige um sinal de valor com estado já estável
para impedir que uma taxa de rede entre no histórico de CPU. A mudança de ID
limpa as amostras e o pico anteriores. Mudanças de unidade e perda de disponibilidade
também limpam os dois históricos e seus horários. Duas séries com unidades
nativas diferentes são recusadas sem conversão implícita: a mensagem explica
que é preciso selecionar a mesma unidade ou remover o segundo sensor. As
leituras individuais mantêm suas unidades, mas não produzem frações comparáveis.
O gráfico não instancia curvas para um conjunto indisponível, mesmo se receber
um histórico antigo; o fundo e as divisórias aprovados permanecem iguais.

Hora em outro fuso é calculada com o deslocamento fornecido pelo mecanismo do
Plasma. A abreviação também vem dessa fonte; o fuso local do processo não é
impresso como se fosse o fuso consultado. O formato compacto mantém a ordem e os
separadores regionais; a consulta mostra a data completa.

O modelo de calendário enumera metadados de provedores instalados. IDs ausentes
são filtrados e geram uma mensagem de indisponibilidade. Provedores selecionados
só são ativados com o calendário aberto. Lista vazia não apresenta agenda.
Os IDs disponíveis ficam num snapshot atualizado apenas quando seu conteúdo
muda: no gerenciador nativo, modelo e lista habilitada compartilham o mesmo
notify. Isso evita que carregar um plugin retroalimente o próprio binding.
Quando houver provedor, os eventos vêm de `MonthView.daysModel.eventsForDate`,
sem dados ilustrativos. Nenhuma conta ou fonte particular é descoberta por este
componente.

## Verificação isolada

`python3 plasma/tools/testar-domainos-instrumentos.py --saida /tmp/novo-diretorio`
abre um plasmoid de teste em Xvfb com HOME/XDG e D-Bus descartáveis e um daemon
privado `ksystemstats`. Verifica hora local real, UTC, variações regionais,
recepção/envio, transição para CPU, sensor inexistente, quadros separados,
gr_osview real, ausência de agenda implícita e despacho de correio sem abrir
aplicativos. Também compara hashes das preferências reais antes e depois.

`python3 plasma/tools/testar-domainos-instrumentos.py --unidades --saida /tmp/novo-diretorio`
faz apenas o ensaio dirigido de unidades: observa CPU em porcentagem e recepção
de rede em bytes por segundo, recusa a escala comum e confirma histórico vazio.
Depois recupera recepção/envio compatíveis, testa uma fonte ausente e CPU sem
segundo sensor. Uma injeção de histórico antiga, identificada no relatório como
fixture, verifica separadamente que curvas indisponíveis não reaparecem. O
ensaio também pede 250 ms no controlador privado e na página real de configuração
para verificar a guarda de 1.000 ms e os limites efetivos das fontes nativas.
Em seguida pede 60.000 ms para sensores e verifica que a fonte temporal continua
em 1.000 ms e a hora avança, sem criar outro temporizador.

O ensaio deliberadamente não acessa uma agenda pessoal nem uma conta de correio.
O caminho dos eventos está implementado com os modelos nativos, mas o conteúdo
de uma fonte particular depende da seleção e configuração autorizadas pelo
usuário. O serviço de correio e sua abertura real são verificados na integração
do painel, separadamente deste controlador.

`python3 plasma/tools/testar-domainos-agenda.py --saida /tmp/novo-diretorio`
verifica a agenda positiva na composição de produção. Escolhe explicitamente
somente o plugin instalado de feriados públicos, região US e 1 de janeiro de
2027, em HOME/KConfig/KWin/D-Bus privados. Observa evento, signal e delegate
nativos, o clique do botão Data, descarregamento ao fechar e volta à lista vazia.
Não lê contas ou calendários pessoais e não alega Apply por clique no diálogo.

Referências de implementação: [sensor nativo do KSysGuard](https://github.com/KDE/libksysguard/blob/master/sensors/Sensor.cpp)
e [gerenciador de eventos do Plasma](https://github.com/KDE/plasma-workspace/blob/master/components/calendar/eventpluginsmanager.cpp).
