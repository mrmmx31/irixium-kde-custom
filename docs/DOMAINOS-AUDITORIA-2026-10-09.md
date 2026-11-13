# DomainOS — revisão dos gates em 9 de outubro de 2026

Este registro atualiza a leitura de F01–F35, D0–D10 e VF01–VF20. Os relatórios
anteriores, inclusive os que falharam, permanecem preservados. Uma aprovação de
contrato ou um ensaio privado não significa teste de todas as aplicações pessoais.
As respostas posteriores do mantenedor prevalecem sobre a tabela documental R2:
clique simples abre o seletor inclusive para uma janela; duplo clique individual
minimiza a ativa, restaura a minimizada ou ativa a inativa; roda só navega por
padrão; destaque pelo compositor é uma preferência independente, desligada.

## Provas novas após a avaliação da prancheta

| Área | Resultado | Alcance e limite |
| --- | --- | --- |
| Clique do meio | 37/37 nativo e 6 testes QML | Grupo e janela individual com Desktop Action e flag genérica falsa. Janelas próprias X11; não é prova de instância única do VS Code pessoal. |
| Seletor de membros | 165/165 | Superfície nativa, listas 3/15/16, alterações de altura durante abertura e depois. Rodapé e janela dentro da tela. |
| Proprietário das dicas e cartões sem imagem | 71/71 nativo, 11/11 títulos, 16/16 ciclo de vida e 4/4 orçamento na 0.2.6 | Posição fora do seletor, entrada/saída QPA completa, ativação única por UUID/PID, título/checkbox/Operações e clique externo. Os 59/59 históricos e a captura Wayland permanecem provas distintas. |
| Dois grupos reais, lotes e popups atuais | 87/87 e 88/88 com Kvantum | Checkbox distinto da seleção comum, título restaura, grupo fecha antes de Operações, UUIDs/PIDs exatos, três exclusões e menu nativo completo na primeira abertura; Wayland privado. |
| Imagem real Wayland na fonte atual | 24/24 | Duas fontes do próprio PID, pintura confirmada na fonte e no frame, descarga, nenhum frame de janela pessoal. |
| Horas, fusos, instrumentos | 23/23 | Hora nativa, UTC/localidade, rede Rx/Tx, ausência de sensor e gr_osview real. |
| Agenda | 33/33 | Plugin nativo de feriados públicos e evento real em configuração privada; sem conta pessoal. |
| Unidades e amostragem | 34/34 | Unidades compatíveis/incompatíveis, ausência/recuperação, limite do sensor e relógio independente. |
| Preferências por instância | 26/27 | Clique no item permanente, Aplicar/Descartar/reabrir/reiniciar; outra instância intacta. Gate de diagnóstico geral falha pelo PromptDialog Kirigami instalado. |
| Reset dirigido e geral atuais | 42/43 | Cinco categorias restantes e 44 entradas gerais; Aplicar/Descartar/reiniciar, outras categorias/instância intactas. Mesmo diagnóstico Kirigami; relatório permanece `failed`, saída 1. |
| Roda do Pager | 10 testes nativos | Eventos comuns, fracionários, extremos, não finitos e MouseArea real; KWin/PagerModel X11 privados. Um destino e no máximo um despacho por evento. |
| Ordem externa dos favoritos | 53/53 nativo e 9/9 helper | A gaveta acompanha a ordem alterada pelo outro menu KDE ao reabrir; lançamento pela identidade atual, pins separados e arquivos de origem intactos. |
| Falhas da importação | 8 critérios QML | Exceções de conexão/desconexão, respostas inválidas e recuperação usando as funções reais da página. Ensaio dirigido; não substitui a prova de persistência do ConfigView. |
| Papéis de cor de SVGs funcionais | 198/198 gates, 5/5 testes | Quatro paletas, mudança no mesmo motor QML, PlasmoidHeading/Controls/KSvg reais; 1.883 IDs/bounds preservados por esquema. Não lê notificações pessoais. |

Os 59 critérios de cartões deliberadamente sem IDs não provam captura. A prova
Wayland atual de 24 critérios é separada e possui os hashes atuais dos nove componentes
relevantes. Sua captura foi conferida, incluindo a cor alterada da primeira fonte.
O monitor do lsi continua observador externo, sem reinício automático.

Os seis erros `Success`/`None` do reset são idênticos à baseline instalada,
reproduzida sem nossa função de reset. As operações de reset funcionaram, mas o
gate de ausência total de erros não passou; os resultados não foram renomeados
como aprovação integral. Não houve alteração do SDK instalado.

## Cobertura funcional e limites

| Gates | Situação nesta revisão |
| --- | --- |
| F01–F05 / VF01–VF04 | Aplicativos, relógio/calendário, monitor e lançamento de correio implementados. Os três ensaios atuais de instrumentos fecham a diferença de fonte dos relatórios anteriores. Correio foi lançado por Desktop Entries próprias; contas e contadores pessoais não foram consultados. |
| F06–F10 / VF05–VF10 | Modelo nativo, seleção explícita, grupos, cliques e navegação presentes. Os relatórios de grupo/organização têm escopos distintos; a prova nativa antiga tem um grupo e uma tarefa avulsa, não dois grupos reais. A prova atual de popups passou 87/87 e 88/88 com Kvantum entre dois grupos reais. |
| F11–F14 / VF12–VF13 | Pager por UUID, CRUD explícito, mapas geométricos e foco por retângulo. Roda recebeu limite aritmético. Arrastar entre miniaturas continua adiado por decisão. |
| F15–F23 / VF14 | Delegados, serviços, atenção, seis posições, continuação, ocultos e ordem próprios da bandeja conservados. Provas usam serviços/SNI privados; não equivalem a conectividade, hardware, ejeção ou contas pessoais. |
| F24–F26 / VF15 | Terminal e Appearance & Style foram lançados em sessões privadas; menu de sessão consulta capacidades e não executa ao abrir. Não se acionaram suspensão, hibernação ou logout pessoais. |
| F27 / VF15 | Contrato Lock/GetActive e falhas comprovados contra serviço privado. Bloqueio físico de uma sessão pessoal permanece para teste coordenado; não será acionado durante esta auditoria. |
| F28–F29 / VF16–VF17 | Ajuda local/xman/KDE, contraste e tokens de atividade comprovados em ensaios próprios. Despacho aceito não é conclusão inventada da aplicação; cauda de luz permanece opcional. |
| F30–F31 / VF19 | Instalação/restauração transacionais dos quatro recursos comprovadas; entrega 0.2.3 no lsi preservou IDs/General e seis arquivos de configuração. A remoção de `colors` não bastava: a 0.2.5 adapta os SVGs funcionais, inclusive cabeçalhos/rodapés nativos, aos papéis do KDE. Classic anterior preservado. Avaliação visual pessoal posterior continua distinta. |
| F32 / VF11 | Pins e favoritos são seções diferentes, com Preferências permanentes primeiro. A nova prova 53/53 acompanha a ordem de outro cliente KDE e lança o ID correto mesmo quando o índice nativo é diferente. A ordem é consultada ao abrir/reabrir e ao trocar Activity; não há observação contínua de reordenação entre clientes. Adições/remoções seguem o modelo nativo. Ordens conflitantes são informadas; a importação libera os controles quando falha. |
| F33 / VF18 | Nove categorias, rota própria e Aplicar/Descartar/persistência por instância comprovados. Reset geral das 44 entradas e cinco categorias restantes exercitados na fonte atual. Diagnóstico geral conserva falha do SDK. |
| F34–F35 / VF07–VF10 | Identidade/PID, capacidades, lotes explícitos e contagem anterior a filtros/grupos presentes. Provas históricas continuam válidas dentro de seu alcance; testes atuais de dois grupos passaram 87/87 e 88/88 com Kvantum e complementam a cadeia UI–helper. |

D0/D1/D10 preservam os namespaces independentes e a recuperação por usuário.
D2–D9 mantêm o desenho aprovado, relevos e proporções; a verificação anterior do
artwork passou 30/30. A nova prova de cores passa 198/198 gates e também compara
a árvore Classic em bytes. A captura de referência
2437 é histórica, não um teste de funções inexistentes naquele protótipo.

## Evidências e próxima entrega

Os relatórios atuais são:

- `/tmp/irix-domainos-middle-native-r3-20261009/RESULTADO.json`
- `/tmp/irix-domainos-group-natural-height-position-r4/RESULTADO.json`
- `/tmp/irix-domainos-two-real-groups-wayland-r2/RESULTADO.json`
- `/tmp/irix-domainos-thumbnail-lifecycle-native-r7/RESULTADO.json`
- `/tmp/irix-domainos-miniaturas-wayland-real-lsi-current-r1-20261009/RESULTADO.json`
- `/tmp/irix-domainos-instrumentos-fonte-atual-smoke-20261009-r2/RESULTADO.json`
- `/tmp/irix-domainos-agenda-fonte-atual-smoke-20261009-r2/RESULTADO.json`
- `/tmp/irix-domainos-unidades-fonte-atual-smoke-20261009-r2/RESULTADO.json`
- `/tmp/irix-domainos-pref-ui-apply-discard-restart-isolacao-r5/RESULTADO.json`
- `/tmp/irix-domainos-defaults-current-five-categories-r2/RESULTADO.json`
- `/tmp/irix-domainos-pager-wheel-20261009.json`
- `/tmp/irix-domainos-gaveta-ordem-externa-native-20261009-r1/RESULTADO.json`

As primeiras tentativas de instrumentos/agenda/reset desta rodada pararam no
socket privado negado pelo sandbox, antes de carregar QML. Permanecem como falhas
de infraestrutura; a repetição liberada usou somente sessões próprias.

O ZIP 0.2.3 final e o backup aprovado em Downloads não são atualizados nem
eliminados. As correções do Pager, favoritos e importação compõem a entrega 0.2.4.
Após essa entrega, o journal do lsi registrou uma saída fatal de protocolo
Wayland; o ZIP não é substituído nem tratado como integralmente estável. As
correções posteriores de SVGs, menus, checkboxes e orçamento de miniaturas
compõem a entrega 0.2.5; seu
[registro de validação](VALIDACAO-DOMAINOS-0.2.5-2026-10-09.md) distingue a falha
observada, as provas privadas sem reprodução e a avaliação pessoal pendente.
A [entrega atual 0.2.6](DOMAINOS-0.2.6.md) corrige posição, intervalo, redundância
e saída das dicas. Seu [registro](VALIDACAO-DOMAINOS-0.2.6-2026-10-09.md) distingue
a r15 falha dos 71 critérios finais e as limitações do input dirigido e da captura.
A validação pessoal de p001532 ocorrerá apenas no final, conforme combinado,
com um lançador simples de janela independente. Nenhum teste desta revisão mudou
configuração global ou perfil de outro usuário. Não se declara o goal concluído
enquanto essa avaliação final estiver pendente.
