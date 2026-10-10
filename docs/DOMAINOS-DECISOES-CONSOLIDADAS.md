# Decisões consolidadas e rastreabilidade — DomainOS R2

**Mantenedor:** `mrmmx31`. Consolidação documental, não assinatura digital nem
registro de implementação executada. O JSON original permanece inalterado.

## Atualização de precedência — 2026-10-10

A revisão visual solicitada em 2026-10-10 usa o Trash Can real do SR10.4 e segue
uma família de controles por vez. A [fila de revisão](DOMAINOS-FILA-REVISAO-VISUAL.md)
deve ser consultada a cada retomada: inclui o defeito GTK3 e a seta do System
Settings, sem transformar validação de uma família em conclusão das demais.
O usuário determinou que a regra seja levantada antes do desenho. A
[especificação comum](DOMAINOS-REGRAS-ROLAGEM.md) e seu contrato JSON são a
referência única; cada família traduz e compara essas regras na sua etapa.

Este adendo registra decisões explícitas posteriores à consolidação R2. Elas
prevalecem quando divergirem do corpo histórico, que permanece preservado. Não
altera o JSON recebido, os anexos do goal nem o backup congelado.

| Decisão posterior | Efeito sobre a leitura da R2 |
| --- | --- |
| Favoritos do Applications na gaveta | Ler e acompanhar os favoritos do KDE na mesma ordem, em seção separada. Os pins próprios da barra continuam independentes; importar pins não escreve na origem. |
| Preferências permanentes | Item fixo e não removível no topo da gaveta, seguido dos fixados da barra e depois dos favoritos do KDE, com separadores. |
| Dicas e prévias opcionais | Dicas gerais desligadas; texto da Iconbox ligado por padrão. Miniaturas e realce ao passar o mouse desligados, disponíveis por opção nas preferências. |
| Clique simples | Selecionar imediatamente e abrir a lista, mesmo com uma só janela, sem restaurá-la. Ctrl/Shift continuam compondo seleção acumulativa. |
| Duplo clique individual | Minimizar a ativa, restaurar a minimizada ou ativar a inativa. O grupo mantém a escolha de membros, sem ativação coletiva implícita. |
| Título na lista do grupo | Sem checkbox marcado, restaurar/ativar aquela janela. Durante seleção por checkbox, marcar/desmarcar; desmarcar todos devolve a restauração direta. |
| Roda na Iconbox | Percorrer itens como as setas; ativar janelas pela roda somente como alternativa nas preferências. |

O [manual funcional atual](../plasma/applets/org.irixclassic.domainos.panel/FUNCTIONAL.md)
documenta os contratos atuais; a [matriz de validação](DOMAINOS-MATRIZ-VALIDACAO-R2.md)
discrimina as provas. A entrega da suíte completa em p001532 está em andamento;
este adendo não declara instalação concluída, ativação ou aceite nessa sessão.
O aceite pessoal da prévia no lsi também não é inferido da documentação.

## Fontes e precedência

Base Git consultada: `#irixfiles`, commit
`2f9f6277736ee6c6187cd010d4dd4f4990bb4822`, repositório
`mrmmx31/irixium-kde-custom`. Os dois anexos coincidem com os blobs dessa base:

| Anexo / caminho de origem | Identidade Git blob |
| --- | --- |
| `DOMAINOS-GOAL-ATUAL.txt` / `docs/DOMAINOS-GOAL-ATUAL.txt` | `07913a3159cb5ae526c3b0ca4dd54e5c03d0f23d` |
| `DOMAINOS-REQUISITOS.md` / `docs/DOMAINOS-REQUISITOS.md` | `1b880d60aa0cc98f7ddcaf22254ae019c7f390cd` |

A prancheta é `PCU-VUE-KDE-R1`, revisão 1.0, schema `pcu-review-1`. O arquivo recebido
contém 28 respostas: 17 concordâncias, 9 com ajustes, 2 discordâncias. Justificativas
fazem parte da decisão, inclusive quando o status é “concordo”.

SHA-256 do JSON recebido:
`0e67e1ebdcb7e6d5be044bc7dcc20ab351eb123a6e2bc06fda04351fedcbe40c`.
Hash declarado do questionário original:
`2e26948b92665d2f7476d5df14a27678634541fc2b597e16decb0b9ec36ffe6a`.
Esses hashes não são assinatura digital. Campos cadastrais em branco não foram
inventados ou preenchidos: o foco é o conteúdo das decisões.

A ordem de precedência é: esclarecimento explícito mais recente; justificativas e
respostas da prancheta; propostas originais apenas onde foram aceitas e não alteradas;
goal e requisitos anteriores como base/histórico. Frases da proposta que entram em
conflito com a resposta não permanecem obrigação de implementação.

Os fatos extraídos do protótipo descrevem seu estado, não decisões do usuário: dados
fixos e seleção simulada não provam integração real. A documentação R2 converge esses
materiais sem mudar a imagem, o código ou o histórico das respostas.

## Mapa das 28 respostas

Prefixo `RESP-` identifica a prancheta; `REQ-` identifica o memorial. Não confundir
RESP-F01 (interação) com REQ-F01 (emblema).

| Resposta | Status original | Requisito(s) | Resultado consolidado |
| --- | --- | --- | --- |
| RESP-A01 | discordo | REQ-F01 | A placa abre menu geral de aplicativos; o selo puramente estático foi recusado. |
| RESP-A02 | concordo | REQ-F02 | Relógio abre hora/fusos como quadro suspenso. Calendário continua no botão próprio. |
| RESP-A03 | concordo | REQ-F03 | Data/localidade do sistema e calendário suspenso; agenda quando houver fonte configurada. |
| RESP-A04 | ajustes | REQ-F04 | Rede e clique abre gr_osview existente. Rodada Q7 fecha recepção e envio simultâneos e métrica configurável. |
| RESP-A05 | concordo | REQ-F05, REQ-F17 | Cliente configurado, Thunderbird como preferência; contagens dependem de integração autorizada. |
| RESP-B01 | ajustes | REQ-F06, REQ-F32, REQ-F35 | Fixados em gaveta própria já localizada. Rodada Q1 muda o padrão para todas as tarefas do escopo e adiciona filtro opcional. |
| RESP-B02 | ajustes | REQ-F07, REQ-F08, REQ-F34 | Duplo clique restaura; simples seleciona; Ctrl/Shift, menu e organização em lote. Seleção parcial de grupos por checkboxes fechada na última resposta. |
| RESP-B03 | concordo | REQ-F09, REQ-F10 | Setas percorrem conjuntos/páginas; sem conteúdo extra ficam indisponíveis. |
| RESP-B04 | concordo | REQ-F06, REQ-F33 | Agrupamento configurável preservado, acessível nas preferências do painel; padrão não significa proibição de alternativas. |
| RESP-B05 | ajustes | REQ-F08 | Menu mantém Fechar normal; encerramento forçado em submenu, não na posição de ação casual. |
| RESP-C01 | discordo | REQ-F11, REQ-F12, REQ-F13, REQ-F14 | Não fixar dois desktops globais. Uma/duas/várias áreas adaptam cartões no mesmo módulo; gerir nomes/quantidade explicitamente. |
| RESP-C02 | concordo | REQ-F11, REQ-F12 | Clique ativa desktop; repetir no atual não executa outro comando. |
| RESP-C03 | concordo | REQ-F14 | Miniaturas geométricas aceitas; confirmação histórica de funcionamento IRIX continua solicitada, não realizada por esta consolidação. |
| RESP-C04 | concordo | REQ-F14 | Arraste entre miniaturas adiado para próxima versão; menus de mover e organização em lote não entram nesse adiamento. |
| RESP-D01 | concordo | REQ-F15–F20, REQ-F23 | Seis posições visíveis 2×3, itens reais e configuráveis; os exemplos não fixam seis serviços universais. |
| RESP-D02 | ajustes | REQ-F21, REQ-F23 | Visíveis excedentes em continuação deslocada; paginação como alternativa quando necessário. |
| RESP-D03 | concordo | REQ-F21 | ▶ para excedentes visíveis; rodada Q6 permite incluir ocultos como preferência alternativa. |
| RESP-D04 | concordo | REQ-F22 | ▲ para status/notificações e acesso aos ocultos; não limpar avisos por abrir. |
| RESP-D05 | concordo | REQ-F15–F20 | Preservar ações/menus nativos dos itens, sem interpretações fictícias de estados. |
| RESP-E01 | concordo | REQ-F24 | Terminal preferido, nova sessão normal, sem comando administrativo implícito. |
| RESP-E02 | concordo | REQ-F25 | Abrir System Settings em Appearance & Style; a central própria por ferramenta não substitui esse botão. |
| RESP-E03 | ajustes | REQ-F26 | Sessão inclui suspensão/hibernação conforme suporte, em escolha explícita, não execução ao abrir. |
| RESP-E04 | concordo | REQ-F27 | Bloqueio real; informar falha, sem simular proteção. |
| RESP-E05 | ajustes | REQ-F28 | Ajuda em ordem painel/xman/KDE, documentação distribuída e xman com esquema/contraste atuais, não hexadecimais fixos do exemplo. |
| RESP-E06 | ajustes | REQ-F29 | Lente acompanha atividade. Esclarecimento Q8 substitui “simulação de espera” por tempo adicional de luz, desligado por padrão. |
| RESP-F01 | ajustes | REQ-F07, REQ-F08, REQ-F29, REQ-F33 | Sem espera de interação; animação de apresentação opcional. Exceção específica do duplo clique da Iconbox e lente conforme esclarecimentos. |
| RESP-F02 | concordo | REQ-F30, REQ-F31, REQ-F33 | Estrutura estável, perfis/monitores e capacidades reais preservados, sem mudanças globais silenciosas. |
| RESP-F03 | concordo | REQ-F30, REQ-F31, REQ-F32 | Desenho e posições preservados; a célula em branco específica tornou-se gaveta, não todos os espaços vazios viraram comandos. |

## Esclarecimentos posteriores que modificam a leitura original

| Rodada/tema | Confirmação do usuário |
| --- | --- |
| Localização da gaveta | Usar a célula antes vazia, já desenhada como `domainosApplicationsDrawer`, antes do terminal; não ocupar outro atalho |
| Q1 — universo de tarefas | Manter padrão atual de abertas/minimizadas; só minimizadas como opção; filtro automático opcional pelo número de janelas, não limite do total |
| Q2 — sequência de gestos | Simples seleciona, duplo restaura, Ctrl/Shift compõem seleção; direito mantém menu e adiciona organização |
| Q3 — destino da organização | Reunir selecionadas no desktop/monitor atuais |
| Q4 — pins | Lista própria, importação opcional, acionar solicita nova janela/instância; tarefa fica na Iconbox e não substitui o pin |
| Q5 — roda no Pager | Navegar cartões por padrão, ativar área pela roda só como alternativa; arraste entre miniaturas adiado |
| Q6 — bandeja | ▶ tem visíveis excedentes; ocultos podem ser incluídos por preferência. ▲ permanece status/notificações |
| Q7 — instrumento | Recepção e envio simultâneos; troca de métrica nas preferências |
| Q8 — indicador | Luz acompanha início/fim; checkbox com tempo mantém luz depois de concluir, sem atrasar ação |
| Última resposta 1 — grupos | Abrir menu com checkboxes para selecionar membros e depois continuar em outros grupos; não selecionar grupo inteiro automaticamente |
| Última resposta 2 — filtro | Aprovar N antes de filtro/agrupamento, N>L liga e N≤L retorna; preferências organizadas por ferramenta, semelhantes ao System Settings |

## O que a consulta ao protótipo esclareceu

O `DomainOSPanel.qml` separa `domainosIdentity`, `domainosApplicationsDrawer` e os
cinco atalhos, incluindo `domainosShortcut_drawer`. O primeiro é a placa, o segundo
é o botão próprio de fixados e o terceiro é o desenho do atalho de Sessão. Seus
nomes internos não determinam automaticamente sua função final.

O componente `Grosview.qml` existente contém métricas de CPU, memória, swap, disco
e recepção/envio de rede. O lançador existente tem modelos de aplicativos e
favoritos; a Iconbox tem filtros e agrupamento. Esses recursos devem ser considerados
para reaproveitamento. O painel DomainOS ainda usa referências ilustrativas e
seleção simulada, sem handlers que comprovem as funções agora escolhidas.

As referências de código da consulta anterior pertencem à mesma revisão Git
reconfirmada nesta consolidação. Não se afirma que os applets foram executados
novamente nem que seus provedores foram integrados ao novo painel.

## Pendências antigas que deixaram de existir

Não manter “aguardar documento do usuário” para a gaveta, “selo sem função definida”,
“somente minimizadas obrigatório”, “todos os F01–F32 pendentes”, “agrupamento
obrigatoriamente desabilitado” ou “proibição absoluta de qualquer temporização”.
O objetivo permanece sem atraso de comandos; a única temporização adicional
especificada é o apagamento opcional da lente depois de a operação já ter terminado.
Atualização temporal de relógios/sensores é outra finalidade, não espera de clique.

O objetivo antigo de citar o mesmo significado do gráfico HP e do comportamento
IRIX não foi convertido em certeza histórica. A escolha de rede é válida como
adaptação, independentemente dessa comprovação.

## Detalhes propostos pelo redator, não decisões expressas

Para tornar as decisões executáveis, os requisitos/preferências distinguem como
**proposta**: manter popup de checkboxes aberto durante marcação; indicação de seleção
parcial; coordenar o fechamento do seletor com o menu de operações; lidar com janelas
que surgem/desaparecem por identidade; regra da lente com ações simultâneas; acesso à
central própria por menu contextual; busca e comandos Aplicar/Descartar/Padrões;
organização dos modos manual/automático para evitar conflito.

O usuário não escolheu números iniciais de limiar, duração extra, escalas ou taxas
de atualização nesta rodada. Nenhum valor ilustrativo é padrão aprovado. Gestos
sobre o resumo de um grupo, instante de conclusão do seletor e identificação do
monitor “atual” devem ser expostos no ensaio se alterarem o comportamento percebido.
Esses pontos não autorizam ignorar seleção individual, filtro automático ou destino
solicitado. Não reabrir decisões resolvidas sob o pretexto de detalhar APIs.

## O que permanece para a próxima versão ou para evidência

**Próxima versão:** arrastar janelas entre miniaturas do Pager. Os menus de movimento,
seleção múltipla e organização em lote continuam nesta etapa. A gaveta de pins já
não está adiada.

**Evidência histórica:** a caixa de confirmação histórica de RESP-C03 foi marcada e
não recebeu nova pesquisa nesta consolidação. Manter a distinção entre intenção da
adaptação e equivalência histórica comprovada.

**Trabalho técnico restante:** implementação, disponibilidade de APIs na sessão,
preferências funcionais, medições, testes reais e instalação/restauração. Nenhum
arquivo desta entrega transforma “aprovado” em “executado” ou “testado”.

## Leitura recomendada para a IA implementadora

Começar pelo goal; localizar requisitos pelos IDs REQ-F; consultar a central de
preferências e este mapa quando a proposta antiga divergir das respostas. Respeitar
suas fronteiras: arte existente, funções aprovadas, propostas de detalhamento e
verificações ainda pendentes. Não exigir outra assinatura das mesmas 28 questões.
A evidência final deve dizer o que realmente funcionou, o que foi adiado pelo usuário
e o que está bloqueado tecnicamente, sem preencher lacunas com resultado inventado.
