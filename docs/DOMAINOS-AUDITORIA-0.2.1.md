# DomainOS 0.2.1 — auditoria do goal

Registro de 9 de outubro de 2026, feito após a instalação da 0.2.1 em **lsi** e
antes da correção dos novos problemas de interface relatados pelo usuário.
Esta auditoria não modifica fontes, pacotes, manuais distribuídos ou o backup
congelado em Downloads. Não declara o goal concluído.

## Autoridade e alcance

A autoridade é o [goal fornecido](/home/lsi/.codex/attachments/6f7375d7-a871-47c6-bbb3-3f05059f3fc7/goal-objective.md),
lido juntamente com [requisitos](DOMAINOS-REQUISITOS.md),
[preferências](DOMAINOS-PREFERENCIAS.md) e
[decisões consolidadas](DOMAINOS-DECISOES-CONSOLIDADAS.md).
Os esclarecimentos posteriores prevalecem: o clique simples abre o seletor,
inclusive para uma janela; o duplo clique individual minimiza a ativa, restaura
a minimizada ou ativa a inativa; a roda navega por padrão. O título de um membro
restaura diretamente enquanto não há seleção por checkbox. O clique no retângulo
geométrico do Pager ativa a janela representada.

**Verificado** abaixo significa implementação e prova no escopo indicado, não
validação de todas as máquinas, contas ou dispositivos pessoais. **Condicional**
significa que a função depende de um provedor real escolhido/disponível e não
pode fabricar estado. **Investigação** conserva as provas anteriores, mas impede
afirmar que a interface corrente está resolvida. Os números pertencem a ensaios
distintos; não devem ser somados como uma única execução da versão final.

## O que impede concluir

- **F27: bloqueio físico da sessão.** O transporte, o resultado e a falha foram
  comprovados contra serviço privado; isso não comprova o bloqueio real de lsi
  ou p001532. Não se executou uma ação sensível pessoal para substituir esse teste.
- **Avaliação manual GTK em lsi**, incluindo a coerência dos controles com o
  esquema escolhido. As provas do painel/Qt não substituem esse checklist.
- **Teste final da 0.2.1 em p001532.** As confirmações e prévias anteriores desse
  perfil não são validação desta entrega.
- **Novos problemas relatados após a entrega:** tamanho/rolagem do seletor de
  grupos, dica instável e faixa atrás da barra. A investigação está em andamento;
  causa, correção e validação da próxima versão não são presumidas aqui.

As antigas lacunas de miniaturas Wayland e de migração/ativação foram resolvidas
pelas provas positivas E01–E04. O arraste entre miniaturas do Pager continua
**adiado por decisão**, sem bloquear esta revisão. Contas de correio/agenda e
operações em hardware não autorizadas não se transformam em integrações obrigatórias
por existir um desenho correspondente.

## Evidências consultadas

Os relatórios recentes foram conferidos por leitura. Os anteriores mantêm apenas
seu alcance documentado, confrontado com os componentes e contratos preservados;
não se afirma uma nova execução nem igualdade integral de hashes com toda a 0.2.1.
As provas e tentativas anteriores permanecem separadas, inclusive resultados falhos.

| Ref. | Prova e resultado | Evidência local / alcance |
| --- | --- | --- |
| E01 | Atualização real de lsi, 7/7; conferência posterior, 5/5 | `/tmp/irix-domainos-lsi-021-upgrade.json`; `/tmp/irix-domainos-lsi-021-final.json`. Uma barra, preferências protegidas, recibo e ponte; não comprova avaliação manual. |
| E02 | Ativação nativa 0.2.1, 51/51 | `/tmp/irix-domainos-ativacao-021-native-r2/RESULTADO.json`. Migração de tarefas e configurações completas dos provedores, geometria 971 × 109, flutuação, reinício, restauração, respostas perdidas e retorno pela ponte. Perfil privado; sem barra antiga oculta. |
| E03 | Pager: X11 41/41; Wayland 32/32 | `/tmp/irix-domainos-pager-janelas-native-r6/RESULTADO.json`; `/tmp/irix-domainos-pager-janelas-wayland-r4/RESULTADO.json`. Janelas próprias, identidade/PID, foco/restauração, mouse/teclado, cancelamento e rejeição de alvo obsoleto. X11 também cobre destruição com respostas nativas pendentes. |
| E04 | Miniaturas reais: X11 23/23; Wayland 23/23 | `/tmp/irix-domainos-miniaturas-x11-owned-dicas-r4/RESULTADO.json`; `/tmp/irix-domainos-miniaturas-wayland-real-lsi-r3/RESULTADO.json`. Pixels e atualização de duas janelas próprias; Wayland usa o compositor real de lsi e host autorizado. Desligadas por padrão; dicas textuais/nenhuma dica não mantêm captura. |
| E05 | Recursos/gestos das tarefas, 43/43 | `/tmp/irix-domainos-recursos-tarefas-native-r5/RESULTADO.json`. Iconbox/TasksModel reais, três clientes próprios, seleção, grupo, roda, duplo clique, reordenação e identidades. Precede o novo relato sobre dimensionamento/rolagem. |
| E06 | Unity/SmartLauncher real, 22/22 | `/tmp/irix-domainos-unity-native-r2/RESULTADO.json`. Progresso, contador e urgência via serviço real em barramento privado; não inventa status nem ativa janela ao atualizar. |
| E07 | Áudio real privado, 25/25 | `/tmp/irix-domainos-audio-real-r2/RESULTADO.json`. Dois streams libpulse do PID próprio, provedor KDE real, cliques de mute/unmute, pausa/retomada e remoção; somente null sink, sem hardware ou áudio pessoal. |
| E08 | Preferências/dicas/menu, 48/48; reset das 44 chaves, 31 verificações positivas de 32 | `/tmp/irix-domainos-preferencias-dicas-menu-r1/RESULTADO.json`; `/tmp/irix-domainos-defaults-44-native-r1/RESULTADO.json`. Apply/Discard, persistência e segunda instância. O reset permanece `failed` no gate `qml_errors_zero`: seis TypeErrors do PromptDialog instalado, também reproduzidos sem reset no baseline `/tmp/irix-domainos-padroes-baseline-r7-native-r1/RESULTADO.json` (17/17). Não é 32/32. |
| E09 | Grupos Wayland, 75/75; organização/filtro, 62/62 | `/tmp/irix-domainos-group-title-wayland-r1/RESULTADO.json`; `/tmp/irix-domainos-grupos-wayland-r5/RESULTADO.json`. Seleção de membros, título, alvos exatos, N>L/N=L/N<L e exclusão dos não escolhidos. Provas anteriores ao novo relato de UI. |
| E10 | Organização nativa: X11 55/55; Wayland 56/56 | `/tmp/irix-domainos-janelas-x11-r7-transientes/RESULTADO.json`; `/tmp/irix-domainos-janelas-wayland-r7-transientes/RESULTADO.json`. Colunas/linhas/mosaico para 2/3/6, maximizar/minimizar distintos, capacidade e dependentes recusados antes de mutar. Prova do helper, distinta da UI. |
| E11 | Pager nativo, 103/103 | `/tmp/irix-domainos-pager-native-window-r3/RESULTADO.json`. Uma/duas/várias áreas, IDs, CRUD explícito, limite mínimo, roda e geometria; antecede a ativação de janela acrescentada em E03. |
| E12 | Instrumentos 23/23; unidades/amostragem 34/34; agenda pública 33/33 | `/tmp/irix-domainos-instrumentos-agenda-regressao-final-r1/RESULTADO.json`; `/tmp/irix-domainos-instrumentos-unidades-native-final-r2/RESULTADO.json`; `/tmp/irix-domainos-agenda-publica-native-r4/RESULTADO.json`. Hora/fusos/localidade, RX/TX nativos, ausência diferente de zero, unidades compatíveis, gr_osview existente; provedor real de feriados no perfil privado, descarregado ao fechar. |
| E13 | Correio/xman, 29/29; aparência/ajuda KDE, 31/31 | `/tmp/irix-domainos-lancamentos-mail-xman-native-r2/RESULTADO.json`; `/tmp/irix-domainos-aparencia-ajuda-native-r3/RESULTADO.json`. Clientes próprios abertos pelo KIO, xman instalado e contraste observado, System Settings/Appearance e KHelpCenter reais. Não acessa contas pessoais. |
| E14 | Comandos/atividade, 23/23; catálogo/atividade, 32/32 | `/tmp/irix-domainos-comandos-review-r2-20261008/RESULTADO.json`; `/tmp/irix-domainos-aplicativos-atividade-busca-global-r1/RESULTADO.json`. Tokens concorrentes, início/fim observável, erro explícito e cauda opcional sem adiar ações. O lock desse ensaio é serviço privado. |
| E15 | Aplicativos/busca, 33/33; menu KDE opcional, 23/23; pin lançado, 30/30 | `/tmp/irix-domainos-aplicativos-busca-global-r2/RESULTADO.json`; `/tmp/irix-domainos-application-interface-native-r1/RESULTADO.json`; `/tmp/irix-domainos-pin-lancamento-native-r2/RESULTADO.json`. Catálogo, favoritos e pins distintos, nova tarefa própria pelo KIO; sem prometer nova instância de aplicativo que reutiliza a existente. |
| E16 | Bandeja nativa 34/34; dicas 42/42; ordem 42 verificações comportamentais | `/tmp/irix-domainos-tray-native-window-r2/RESULTADO.json`; `/tmp/irix-domainos-native-tray-hints-r11/RESULTADO.json`; `/tmp/irix-domainos-tray-order-native-r3/RESULTADO.json`. Provedores/SNI reais, excedentes/ocultos, atenção e ordem por instância. Ordem tem 43 gates e mantém o diagnóstico PromptDialog (`qml_runtime_errors_zero=false`), não 43/43. |
| E17 | Textura dos slots ocupados, 28/28; paleta Qt/Kirigami, 7/7 | `/tmp/irix-domainos-tray-texture-native-r2/RESULTADO.json`; `/tmp/irix-domainos-popup-palette-qt-r1.json`. Tecido aprovado nos ocupados, vazios lisos e menus com papéis do esquema. Não diagnostica a faixa recém-relatada atrás da barra. |
| E18 | Onze lançadores, 19/19; concorrência, 197/197 | `/tmp/irix-domainos-toggle-native-r8/RESULTADO.json`; `/tmp/irix-domainos-concorrencia-native-directed-r16/RESULTADO.json`. Abrir/fechar/reabrir, Escape/clique exterior; pressão/teclado com sensores e atenção reais, geometria estável. Tempos pertencem ao host do ensaio, não garantem latência universal. |
| E19 | Referência visual, 2437/2437 | `/tmp/irix-domainos-selecao-20261008-r2-final/RESULTADO.json`. Arte compartilhada, relevos/pressão/cancelamento, oito paletas e contraste amarelo; prova visual histórica, separada da telemetria real. |
| E20 | Alvo de grupo no menu New Desktop | `/tmp/irix-domainos-menu-desktop-membership-r7/RESULTADO.json`: comparação 5/5 e versão atual 34/34 documentadas na prova. Recusa grupo alterado; reabrir captura membros atuais. QAction programática em X11 privado, não clique físico no submenu. |

O ZIP 0.2.1 e sua aplicação em lsi permanecem registros de entrega verdadeiros,
conforme [liberação](VALIDACAO-DOMAINOS-LIBERACAO-2026-10-09.md). A integridade
byte a byte e os quatro destinos são distintos da aprovação funcional completa.
Os relatórios de [integração](VALIDACAO-DOMAINOS-INTEGRACAO-2026-10-08.md) e
[interação](VALIDACAO-DOMAINOS-INTERACAO-2026-10-09.md) conservam os limites das
provas antigas. Suas frases históricas sobre Wayland sem frame e ativação pessoal
pendente foram superadas por E01–E04, não por uma reexecução fictícia desses relatórios.

## Matriz F01–F35

| Item | Estado nesta auditoria | Cobertura / limite |
| --- | --- | --- |
| F01 — GNU/LINUX / aplicativos | Verificado | E14–E15; menu geral, busca, categorias/favoritos; gaveta separada. |
| F02 — relógio e fusos | Verificado | E12; hora real, quadro próprio, sem calendário duplicado. |
| F03 — data / calendário / agenda | Verificado; agenda condicional | E12; variante regional e fonte pública real escolhida; nenhuma conta inferida. |
| F04 — RX/TX / gr_osview | Verificado | E12; rede dupla por padrão, métricas, unidades e indisponibilidade explícita. |
| F05 — cliente de correio | Verificado; estado condicional | E13; default/override reais privados; sem contagem sem fonte autorizada. |
| F06 — tarefas abertas/minimizadas | Verificado | E05–E07/E09; TasksModel nativo, filtros/agrupamento, pins separados. |
| F07 — seleção / duplo clique | Verificado nos ensaios; investigação de UI | E05/E09; protocolo atualizado; tamanho/rolagem do seletor ainda em investigação. |
| F08 — contexto / organização | Verificado nos ensaios; investigação de UI | E09–E10/E20; identidades/capacidades, força separada de Fechar; nova UI não declarada concluída. |
| F09 — navegação esquerda | Verificado | E05/E18; navegação e limite, sem limite artificial de tarefas. |
| F10 — navegação direita | Verificado | E05; páginas sem ativar por padrão, alternativa configurável. |
| F11 — primeiro desktop | Verificado | E03/E11; UUID nativo e marcador, sem renomear implicitamente. |
| F12 — segundo desktop | Verificado | E03/E11; área existente; clique no mapa ativa janela própria correta. |
| F13 — CRUD / quantidade de áreas | Verificado | E11; mínimo uma, uma preenche, duas lado a lado, várias navegáveis. |
| F14 — geometria / roda | Verificado; arraste adiado | E03/E11; mapas sem conteúdo capturado, roda navega; arraste fora desta revisão. |
| F15 — rede na bandeja | Verificado no contrato nativo | E16/E18; abrir não conecta/desconecta; conectividade pessoal não alterada. |
| F16 — volume na bandeja | Verificado no contrato nativo | E16; ações do provedor preservadas. E07 comprova áudio real da Iconbox em servidor privado, não hardware pessoal. |
| F17 — mensagens / correio na bandeja | Condicional | E16; somente provedor real configurado; sem envelope/contador fictício. |
| F18 — dispositivos / armazenamento | Verificado no contrato nativo | E16/E18; ações explícitas, navegação não ejeta; hardware pessoal não exercitado. |
| F19 — monitor escolhido na bandeja | Condicional | E16; provedor e alvo reais, disponibilidade depende da escolha local. |
| F20 — sexta posição real | Verificado no contrato nativo | E16/E18; estado de atenção real, sem LED permanentemente normal fabricado. |
| F21 — continuação dos visíveis | Verificado | E16; excedentes, paginação/fallback e ocultos opcionais. |
| F22 — status / notificações | Verificado no contrato nativo | E16/E18; ocultos acessíveis; abrir não limpa histórico nem muda DND. |
| F23 — seis slots / ordem / visibilidade | Verificado | E16–E17; 2 × 3, ordem por instância, Apply/Discard e textura ocupada. |
| F24 — terminal | Verificado | E14; usuário normal, resolução segura e argumentos literais. |
| F25 — Appearance & Style | Verificado | E13; System Settings instalado, separado das preferências próprias. |
| F26 — sessão / energia | Verificado no escopo autorizado | E14/E18; capacidades e menu sem ação ao abrir. Não afirma suspensão/hibernação/logout físicos. |
| F27 — bloqueio real | **Pendente** | E14 prova apenas serviço privado; falta bloqueio físico da sessão pessoal. |
| F28 — ajuda local / xman / KDE | Verificado | E13/E18; ordem, manual distribuído, janela real, contraste e erro quando ausente. |
| F29 — lente / ciclo de atividade | Verificado | E14/E20; começo/fim observável; cauda desligada por padrão e só retarda apagar. Retorno do pedido não é fim da aplicação. |
| F30 — instalar / migrar / restaurar | Verificado em perfil privado e lsi; p001532 pendente | E01–E02; uma barra, recibos/reconstrução, preferências de tarefas e provedores transferidas. |
| F31 — estilos independentes / esquema | Verificado; avaliação pessoal pendente | E01–E02/E17/E19; Classic recuperável pela escolha de Style; GTK lsi e p001532 final ainda faltam. |
| F32 — gaveta de fixados | Verificado | E02/E15; lista própria, importação opcional, pins preservados, pedido de nova janela. |
| F33 — preferências próprias | Verificado funcionalmente; diagnóstico SDK e investigação de dica | E08; categorias/defaults/alternativas, 44 chaves, escopo da instância, Apply/Discard; não afirma gate de logs limpo. |
| F34 — checkbox / operações em lote | Verificado nos ensaios; investigação de UI | E09–E10/E20; membros exatos, seleção preservada e destino atual; novo seletor requer correção/validação. |
| F35 — filtro automático | Verificado | E09; N contado antes de filtro/agrupamento, N>L/N≤L, sem minimizar janelas; limiar não inventado como escolha do usuário. |

## Matriz VF01–VF20

| Critério | Estado / evidência | Limite que permanece |
| --- | --- | --- |
| VF01 — emblema e gaveta distintos | Verificado, E14–E15/E19 | Favoritos KDE e pins próprios têm alcances distintos. |
| VF02 — hora/data/agenda | Verificado, E12 | Contas pessoais não acessadas; agenda só com fonte autorizada. |
| VF03 — medidores reais | Verificado, E12 | Unidade/fonte ausente não gera zero ou curva fictícia. |
| VF04 — correio | Verificado, E13 | Lançamento real de clientes próprios, sem comprovar contas/Thunderbird pessoal. |
| VF05 — tarefas / agrupamento | Verificado, E05/E09 | Sem limite de sete; compatibilidade de aplicativos depende da API nativa. |
| VF06 — cliques / menus | Provas positivas E05/E09/E18; investigação | Novo dimensionamento/rolagem do seletor impede fechamento da UI. |
| VF07 — seleção entre grupos | Provas positivas E09; investigação | Acumulação entre grupos também tem fixture Qt separada; não atribuir todos os casos ao mesmo ensaio Wayland. |
| VF08 — mudança da lista / identidade | Verificado, E05/E09/E20 | Alvo fechado/PID divergente/grupo alterado recusado; reabrir captura alvo atual. |
| VF09 — organização do conjunto | Verificado, E09–E10 | UI de dois membros e helper para 2/3/6 são provas distintas; dependentes não isoláveis recusados. |
| VF10 — filtro N>L/N≤L | Verificado, E09 | Não altera estado das janelas; limiar continua escolha da instância. |
| VF11 — fixados | Verificado, E02/E15 | Importação opcional; pedido novo não garante segunda instância em aplicativo de instância única. |
| VF12 — Pager / quantidade / roda | Verificado, E03/E11 | Preserva IDs/nomes; criar/renomear exige ação explícita. |
| VF13 — mapas e miniaturas | Verificado, E03–E04/E11 | Pager geométrico; captura opcional só na Iconbox. Arraste do Pager adiado. |
| VF14 — bandeja / atenção / ocultos | Verificado no contrato, E16–E18 | Provedores e serviços reais próprios; não presume hardware/contas pessoais. |
| VF15 — sessão e bloqueio | **Parcial**, E14/E18 | Falta F27 físico; menu não executa energia ao abrir. |
| VF16 — ajuda / contraste / distribuição | Verificado, E13 | xman exige X11/XWayland; recursos extras do Xaw não foram todos observados na face inicial. |
| VF17 — lente / responsividade | Verificado, E14/E18/E20 | Pedido aceito/retorno é o evento observável, não conclusão inventada do aplicativo. |
| VF18 — preferências / padrões | Verificado funcionalmente, E08 | 31/32 no reset por diagnóstico SDK reproduzido em baseline; dica recém-relatada em investigação. |
| VF19 — instalar / recuperar / perfis | Verificado E01–E02; final p001532 pendente | Instalação e ativação têm provas distintas; avaliação GTK lsi ainda falta. |
| VF20 — teclado / carga / desenho | Provas positivas E03/E05/E18–E19; investigação visual | Tempos do ensaio não são garantia universal; faixa atrás da barra recém-relatada sem diagnóstico final. |

## Matriz D0–D10

Os nomes/janelas/ícones ilustrados em D4–D6 pertencem à arte de referência,
não são ordem para limitar tarefas, renomear áreas ou fabricar serviços.

| Invariante | Estado / evidência | Distinção necessária |
| --- | --- | --- |
| D0 — Classic permanece opção | Verificado, E01–E02 | Retorno reconstrói a barra anterior; nenhuma segunda barra oculta. |
| D1 — recursos DomainOS próprios | Verificado, E01–E02 | Quatro destinos per-user, IDs próprios; instalação separada da ativação. |
| D2 — composição / dois andares / chapa | Provas positivas E02/E19; investigação visual | 971 × 109, escala 0,5 e chassis dentro do painel; faixa recém-relatada ainda não explicada. |
| D3 — bloco esquerdo / fontes | Verificado na referência, E12/E19 | Courier é a escolha aprovada; atribuição histórica provável de outra fonte não é identificação exata. |
| D4 — Iconbox / setas / relevos | Arte preservada, E05/E19; investigação de seletor | Sete samples não limitam tarefas; prova da arte não sana rolagem/tamanho do popup. |
| D5 — Pager / luz de seleção | Verificado, E03/E11/E19 | Pressiona durante o gesto, depois conserva luz; nomes de exemplo não são impostos. |
| D6 — bandeja 2 × 3 | Verificado, E16–E17/E19 | Slots ocupados com tecido, vazios lisos; símbolos ilustrativos não viram status fictício. |
| D7 — GNU/LINUX / sulcos / ícones / lente | Verificado na referência, E14/E19 | Arte e ações são provas distintas; nenhuma troca dos atalhos do rodapé. |
| D8 — aparência UNIX / paleta | Verificado no painel, E17/E19; avaliação GTK pendente | Filetes opacos/ortogonais, contraste amarelo e esquema; não declara aprovação GTK pessoal. |
| D9 — pressão / cancelamento / render | Provas positivas E03/E05/E18–E19; investigação visual | Feedback imediato sem timer de ação/repaint acrescentado; referência estática não finge execução. |
| D10 — perfis / backup protegido | Verificado no escopo, E01–E02 e relatórios privados | Sem modificação global ou de p001532 nesta entrega; backup congelado não tocado. |

## Encerramento da auditoria

A 0.2.1 foi entregue e instalada de forma recuperável em lsi. Isso é diferente
de concluir o goal. Seu encerramento depende das validações pessoais acima e da
resolução dos novos relatos de interface. A próxima correção/entrega deve trazer
suas próprias provas; este documento não as antecipa nem reclassifica tentativas
falhas como aprovação.

## Continuação na versão 0.2.2

As investigações de rolagem/clique, dimensionamento do seletor, estabilidade das
dicas, fundo duplicado e gaveta de favoritos receberam correções e novas provas
na entrega 0.2.2. Consulte a
[validação de 0.2.2](VALIDACAO-DOMAINOS-0.2.2-2026-10-09.md), que distingue os
resultados atuais dos históricos desta auditoria. A 0.2.2 já está aplicada em lsi;
a avaliação pessoal, o teste final em p001532 e F27 físico seguem pendentes.
