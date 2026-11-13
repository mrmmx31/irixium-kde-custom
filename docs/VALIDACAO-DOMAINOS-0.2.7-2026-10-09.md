# Validação DomainOS 0.2.7 — 2026-10-09

Esta revisão corrige seleção acumulada, pins temporários de janelas, posição e
destinos do menu nativo, dica da legenda da miniatura e apresentação da lente.
Acrescenta configuração nativa de fontes de calendário e integração opcional
de contagem com Thunderbird. Instalação de recursos, ativação do painel e
instalação da extensão do cliente continuam etapas distintas, por usuário.

## Provas dirigidas

| Comportamento | Resultado e alcance |
| --- | --- |
| Pins temporários e seleção | 14 unitários, 6 regressões de clique do meio, 66 verificações nativas e 26 verificações dirigidas de destino. Janelas próprias identificadas por ID/PID; seleção acumulada, ordem de fixação, retirada do grupo, primeira ação Desafixar e fechamento. O ensaio nativo usa entrada QPA na sessão privada, sem alegar uso físico na sessão pessoal. |
| Grupo remanescente | 13 contratos QML do adaptador nativo com modelos explícitos, incluindo capacidades dos membros restantes e proteção de criar área de trabalho. Launch/drop alcança o primeiro membro remanescente, sem lançar por uma janela retirada do grupo. O teste de destinos nativos observa o índice real; execução de launch/drop com URLs diferentes é prova de contrato separada. |
| Menu direito na escala do painel | Comparação X11/KWin/Xvfb com grupo próprio e menu KDE real: 15 verificações na versão atual, em escalas de 50% e 100%. A 0.2.6 reproduz a sobreposição da âncora em 50%; o menu corrigido fica acima, com todas as 13 ações dentro da tela na primeira abertura. Cinco gates de comparação/isolamento passaram, com fontes e perfis protegidos intactos. |
| Dica da legenda | 11 contratos QML, incluindo o caminho real `previews=true`, `hints=false`. Legenda abreviada recebe dica; modo desligado e fechamento do pai cancelam a apresentação. Não equivale a ensaio físico de ponteiro. |
| Preferências de agenda/correio | 34 verificações de controles da página nativa, rascunho, descarte e escrita/releitura em KConfig privado; página Feriados visível somente quando escolhida. Mais 17 verificações de opt-in da contagem. Aplicar/Descartar nesse ensaio tem chamada explícita da fixture; não é uma nova comprovação do botão Aplicar de todo o framework Plasma. |
| Agenda nativa | 39 verificações com eventos públicos em perfil privado. Mais 44 com a região brasileira instalada: 12/10/2026 tem evento; 24/10/2026 não está coberto pela região original. A definição final Manaus 2026 passa 138 verificações: descoberta nativa no XDG, cada um dos 15 feriados com exatamente um evento/uma linha visível, 9 pontos facultativos ausentes, datas fora de 2026 ausentes e descarregamento. Não houve acesso a agenda pessoal. |
| Thunderbird real | 9 verificações com Thunderbird 140 ESR, XPI e host nativo em perfil descartável: três eventos reais de pastas, contagem 1→2→3, zero conhecido ao marcar como lida e perda da fonte ao encerrar. Não utiliza contas ou mensagens pessoais. |
| Contagem até o desenho do botão | 18 verificações com Runtime, Instruments, SmartLauncher, serviço D-Bus e botão reais. Valores 0/3/2 e indisponibilidade aparecem na legenda; EOF, encerramento abrupto e frame excessivo retiram disponibilidade sem reapresentar badge antigo. Entrada é framing nativo sintético; a prova de Thunderbird é a linha anterior. |
| Cliente padrão e falhas da ponte | 13 contratos de atualização dos metadados no clique explícito, sem polling nem espera antes do lançamento; 5 verificações de framing, extensão e instalação. Respostas repetidas e falhas de conexão/desconexão são descartadas/liberadas. |
| Lente amarela | 24 verificações em renderização OpenGL com thread: operação imediata concluída mantém apenas a apresentação até `frameSwapped`; apresentação e execução têm recibos distintos. Paletas clara, escura e amarela têm capturas; proteção de contraste da lente não altera a seleção do Pager. Não é benchmark de CPU nem prova de evento físico na sessão lsi. |
| Padrões e restauração | 7 contratos de defaults, incluindo a nova opção de contagem. Seis contratos do configurador regional preservam outras regiões/chaves, bytes e modos; reinstalação idêntica mantém o backup, edição posterior impede restauração destrutiva e o modo de conferência não cria journal. |

## Relatórios privados

Os relatórios e capturas ficam fora do repositório. Cada prova preserva seus
hashes, processos próprios e limites; não há soma desses números apresentada
como uma única execução final da interface.

- `/tmp/irix-domainos-temporary-window-pins-final-007.json`
- `/tmp/irix-domainos-native-menu-projection-unit-r3/RESULTADO.json` e
  `/tmp/irix-domainos-native-menu-projected-desktop-unit-007-r1/RESULTADO.json`
- `/tmp/irix-domainos-native-menu-scale-x11-007-r2/RESULTADO.json`
- `/tmp/irix-domainos-caption-hints-007-r1/RESULTADO.json`
- `/tmp/irix-domainos-agenda-correio-preferencias-r2/RESULTADO.json`
- `/tmp/irix-domainos-correio-optin-preferencias-r3/RESULTADO.json`
- `/tmp/irix-domainos-agenda-publica-007-r5/RESULTADO.json`
- `/tmp/irix-domainos-agenda-brasil-007-r1/RESULTADO.json`
- `/tmp/irix-domainos-agenda-manaus-2026-final-007-r5/RESULTADO.json`
- `/tmp/irix-domainos-feriados-configurador-007-r1/RESULTADO.json`
- `/tmp/irix-domainos-thunderbird-007-ready/RESULTADO-READY.json`
- `/tmp/irix-domainos-thunderbird-native-007-r3/RESULTADO.json`
- `/tmp/irix-domainos-thunderbird-panel-007-r3/RESULTADO.json`
- `/tmp/irix-domainos-activity-light-007-r5-threaded/RESULTADO.json`

## Regressões e limites preservados

O primeiro ensaio Manaus confirmou presença/ausência de datas, mas não exigiu
unicidade. A revisão seguinte encontrou duplicação visível em janeiro/dezembro:
o parser nativo reprocessa datas absolutas quando a grade abrange dois anos.
A definição final guarda o dia pelo ano de parsing, mantendo o ano explícito
2026. A prova final exige uma única linha nas datas positivas e zero nas negativas;
as tentativas anteriores, inclusive erros dos asserts da fixture, permanecem
preservadas. Nenhuma deduplicação genérica foi aplicada a agendas pessoais.

A prova positiva de pixels de miniaturas em X11 é complementar à entrega
0.2.6: 26/26 com Xvfb/KWin e Mesa softpipe, janelas próprias e pixels reais que
mudam de vermelho para azul. O teste anterior com llvmpipe não ofereceu o
provedor necessário; seu resultado negativo permanece preservado. A prova
Wayland verifica estados, cancelamento e cartão acionável quando a captura do
provedor não está disponível; não comprova pixels PipeWire naquele ambiente.

As tentativas iniciais de geometria em Wayland usavam posição global não
exposta pelo cliente. Não validam distância até a âncora; a comparação X11
posterior usa coordenadas globais reais. A primeira comparação X11 observou
mudança externa do arquivo de applets e falhou o guard de perfil; o resultado
não foi reescrito. A repetição com prova de namespaces privados passou.

A renderização nativa QWidget depende do estilo de aplicação. Um controle
privado com Breeze acompanha os dois esquemas KDE; com Kvantum IrixClassic,
o QMenu conserva a paleta e a arte definidas nesse tema. Isso não comprova
adaptação universal do menu nativo ao esquema. A investigação está em
`/tmp/irix-domainos-native-qmenu-palette-007-r2/RESULTADO.json`; não houve
mudança global de estilo para mascarar esse limite. Os menus QML próprios,
dicas e arte do painel usam os papéis de cor do esquema atual.

O gate independente de pacote produz um recibo externo com inventário,
integridade e instalação/reinstalação/restauração em raízes descartáveis,
incluindo sentinelas de perfil Thunderbird preservadas. O recibo final de
distribuição identifica o ZIP exato e a entrega por usuário; não são
reescritos dentro de um ZIP já congelado.

Continuam pendentes as verificações manuais finais de lsi/p001532 combinadas
com o usuário. A instalação do host de correio não instala o XPI no perfil
pessoal: essa etapa usa o gerenciador de extensões do Thunderbird. O arraste
entre miniaturas do Pager continua adiado, conforme a revisão R2.
