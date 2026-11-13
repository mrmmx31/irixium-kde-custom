# DomainOS 0.2.0 — liberação para uso em 9 de outubro de 2026

O usuário autorizou o uso da versão e confirmou a substituição completa da barra:
a anterior deve voltar pela opção de Plasma Style, sem continuar como painel oculto.
A liberação foi aplicada somente no perfil lsi. O backup congelado em Downloads
não foi alterado. Não houve publicação remota ou alteração do perfil p001532 nesta etapa.

## Ativação e recuperação

`tools/activate_domainos.py` usa o scripting KDE no barramento pertencente ao usuário.
Antes da mudança, guarda a configuração do painel, widgets, bandeja, launchers,
geometria e cópias de `plasmashellrc`/`plasma-org.kde.plasma.desktop-appletsrc`.
Cria e confere a barra DomainOS antes de remover a anterior. A restauração reconstrói
os widgets e sua configuração com novas identidades nativas, sem sobrescrever os
arquivos inteiros de configuração do shell em execução.

`tools/domainos_style_bridge.py --instalar --iniciar` instala nove módulos e uma
unidade systemd exclusivamente do usuário. QFileSystemWatcher acompanha a escolha
em `plasmarc`: IrixClassic restaura a barra anterior; IrixClassicDomainOS recupera a
DomainOS com suas preferências. Outros estilos não acionam essa troca. A ponte
somente atua depois de uma ativação explicitamente registrada neste perfil.
Atualizações iniciadas recarregam somente essa unidade, usando os módulos copiados.

O applet declara `CanFillArea`. O ativador compensa os gutters horizontais do
containment; o desenho de 971 × 109 não pode ultrapassar a janela do painel.
Não foi introduzido timer ou repaint para o clique dos controles.

## Evidências

| Ensaio | Resultado | Evidência local |
| --- | --- | --- |
| Ativação integral, restauração após reinício, geometria real, preferências, origem no topo e respostas perdidas | 44/44 | `/tmp/irix-domainos-ativacao-native-r4/RESULTADO.json` |
| Reconstrução nativa de painel/bandeja e proteção de painéis não relacionados | 16/16 | `/tmp/irix-panel-layout-reconstruction-native-r2/RESULTADO.json` |
| Ponte por mudanças reais de arquivo, opt-in e isolamento | 7/7 | `tests/test_domainos_style_bridge.py` |
| ZIP determinístico, integridade, instalação/restauração sem checkout em perfil privado | 5/5 | `tests/test_domainos_package.py` |
| Imports obrigatórias e capacidade opcional Wayland | 3/3 | `tests/test_install_domainos_runtime.py` |
| Seleção real dos dois Plasma Styles em lsi, retornando à DomainOS | 5/5 | `/tmp/irix-domainos-lsi-style-roundtrip.json` |

O ensaio nativo final mediu desenho 971 × 109, escala 0,5 e janela 987 × 109,
com todo o desenho dentro da janela. O perfil isolado completo e seus recibos estão
no `PRIVATE-PROFILE.tar.gz` da prova R4. Os testes não instalaram plugins C++ em lsi.
A seleção real restaurou apenas um painel Classic e retornou a apenas um DomainOS;
os fixados Chrome, IRIX Files e Konsole foram preservados.

A primeira tentativa em lsi foi recusada pelo guardião: o campo vazio `launchers`
da Iconbox antiga passou de string vazia a `None` durante a inicialização nativa.
A barra antiga foi preservada integralmente. Depois de conferir essa diferença,
a repetição com o estado estabilizado concluiu a troca. O backup dessa ativação
ficou em `~/.local/state/irixium-domainos-panel/backups/e90a4e997bd3404a8be25e3d6809e866`;
as trocas posteriores de Style têm seus próprios recibos.

## Distribuição

O pacote está em `/home/lsi/Downloads/irixclassic-domainos-0.2.0.zip`, com checksum
externo `.zip.sha256`. Tem 573.519 bytes, 206 arquivos de payload e dois manifestos
internos; o instalador independente mantém exatamente quatro destinos.

SHA256: `daac9f916a1aa33c17bcc6118bed7e2ec20a245c3428bd463bd6148e30c404de`.

A base Classic é incluída como fonte do gerador, não como quinto destino instalado.
O ZIP não inclui configurações pessoais, sons, pacote completo de ícones ou auditor
privado. A suite completa e a decoração paralela continuam no repositório, com
instaladores próprios. Instruções de uso estão em [DomainOS 0.2.0](DOMAINOS-0.2.0.md).

A captura de miniaturas foi validada em X11; Wayland permanece sem frame validado
na sessão virtual e as miniaturas começam desligadas. Os diagnósticos SDK já
reproduzidos em baseline continuam documentados nas provas de interação e de
reconstrução. A liberação para uso não afirma validação de todas as distribuições.

## Atualização posterior: 0.2.1

O registro acima conserva a evidência histórica da 0.2.0. A versão corrente desta
rodada é **0.2.1**, aplicada somente em lsi e sem alterações globais ou em p001532.
O checklist GTK temporário fica fora do repositório. A avaliação manual do usuário
permanece distinta dos testes automatizados.

Foram corrigidos a ancoragem do seletor após reordenar/reagrupar tarefas, o clique
simples para abrir a lista inclusive com uma janela, o duplo clique individual
ativa/inativa/minimizada e a roda que navega por padrão. A alternativa de ativar
janelas pela roda continua nas preferências. O retângulo geométrico do Pager ativa
a janela representada, e os menus próprios recebem a paleta de controles do KDE.
A flutuação usa o containment nativo, com o afastamento padrão de 8 px medido no
ensaio privado. Não foi acrescentado temporizador de ações aos controles.

A primeira ativação transfere as preferências compatíveis do gerenciador de
tarefas e as configurações completas dos provedores da bandeja antes de remover
a barra original. Retornos posteriores reutilizam as preferências próprias do
DomainOS. A restauração continua guardada em recibos, sem uma segunda barra oculta.

| Ensaio da atualização | Resultado | Evidência local |
| --- | --- | --- |
| Atualização real de lsi; atalhos/preferências, esquema e demais configurações preservados | 7/7 | `/tmp/irix-domainos-lsi-021-upgrade.json` |
| Conferência posterior: uma barra, um widget, flutuação, recibo e ponte ativos | 5/5 | `/tmp/irix-domainos-lsi-021-final.json` |
| Ativação nativa completa, migração, geometria, reinício, restauração e respostas perdidas | 51/51 | `/tmp/irix-domainos-ativacao-021-native-r2/RESULTADO.json` |
| Interação física com tarefas, grupos, roda e teclado | 43/43 | `/tmp/irix-domainos-recursos-tarefas-native-r5/RESULTADO.json` |
| Ativação de janelas pelo Pager, X11 / Wayland | 41/41 / 32/32 | `/tmp/irix-domainos-pager-janelas-native-r6/RESULTADO.json`; `/tmp/irix-domainos-pager-janelas-wayland-r4/RESULTADO.json` |
| Miniaturas com pixels reais e atualização em Wayland | 23/23 | `/tmp/irix-domainos-miniaturas-wayland-real-lsi-r3/RESULTADO.json` |
| Progresso, contador e urgência pelo serviço Unity/SmartLauncher real privado | 22/22 | `/tmp/irix-domainos-unity-native-r2/RESULTADO.json` |
| Áudio real privado: dois streams, mute/unmute, pausa/retomada e remoção | 25/25 | `/tmp/irix-domainos-audio-real-r2/RESULTADO.json` |
| Paleta de controles Qt/Kirigami, menus/submenus e troca de esquema | 7/7 | `/tmp/irix-domainos-popup-palette-qt-r1.json` |

A prova de reset das **44** preferências confirmou 31 verificações comportamentais
e conservou o resultado geral `failed`: a verificação adicional de ausência de
diagnósticos encontra o erro de PromptDialog do SDK também observado no baseline.
O registro é `/tmp/irix-domainos-defaults-44-native-r1/RESULTADO.json`; não constitui
32/32 nem um diagnóstico novo atribuído ao reset.

O pacote corrente foi conferido byte a byte contra as 208 fontes/inventários do
plano de distribuição e os quatro destinos instalados. Contém 210 arquivos no ZIP,
585.306 bytes. Está em `/home/lsi/Downloads/irixclassic-domainos-0.2.1.zip`, com seu
`.zip.sha256`. SHA256:
`0b54b45f8dc26f50c4cf3b03b25d889c567670362425ee0046bfe20b188d6637`.
Instruções: [DomainOS 0.2.1](DOMAINOS-0.2.1.md).

O recibo corrente de lsi é
`~/.local/state/irixium-domainos-panel/backups/25a843873c2a4a199a31eb188d80f31a/receipt.json`.
A avaliação manual corrente em lsi, o teste final desta versão em p001532 e a
verificação do bloqueio físico da sessão ainda são pendências da conclusão do
goal completo. Não se executou bloqueio, logout ou desligamento pessoal para
substituir essa avaliação.
