# DomainOS — revisão de falhas e observação

O usuário esclareceu que a alternância rápida de dicas foi relatada **antes**
da última correção. Não constitui evidência de uma regressão nova. Nesta rodada
separamos a revisão preventiva da correção do destino das preferências.

## Proteções concretas

| Caminho | Problema identificado | Tratamento | Verificação |
| --- | --- | --- | --- |
| `DomainOSTasks.refresh()` | Uma exceção deixava `refreshing=true`, descartando futuras atualizações. | Ler o próximo snapshot antes da publicação; preservar o anterior em falha de leitura; `finally` libera a guarda. Relato fixo uma vez por episódio, sem mensagem privada do provedor. Sem repetição imediata. | `test_domainos_refresh_failure.py`: 5/5; regressão de tarefas: 56/56. |
| `DomainOSIconbox.wheelEvent()` | Subtração repetida pode deixar de alterar um número finito extremo, formando laço infinito. | Calcular passos/resto aritmeticamente; uma navegação ou solicitação de ativação por evento. Padrão continua scroll. | `test_domainos_wheel_failure.py`: 5/5, Qt de produção em workers com timeout externo; entradas extremas e passos parciais. Teste nativo de rolagem: 19/19. |
| Preferências da gaveta | A chave genérica `configure` é compartilhada com o wrapper SystemTray. | Registrar a ação própria `domainos-configure-panel` e acionar diretamente a QAction do painel. Preservar a ação nativa da bandeja. | Rota por sinal: 13/13 verificações positivas, mesmo applet e nove categorias. Status restrito com dois diagnósticos externos do Kirigami; clique físico e Apply não aprovados nesse ensaio. |
| Pedidos de comandos/operações | Exceções ao preparar/conectar/desconectar fontes podiam deixar a indicação de atividade ou o mapa de trabalhos pendente. | Limpeza da propriedade do pedido antes de desconectar; concluir o token; ignorar duplicatas; distinguir pedido não enviado de resultado desconhecido, sem repetir a ação. | `test_domainos_job_failure.py`: 7/7 com QML e Activity de produção, quatro controladores, provedor de falhas e D-Bus privado. Regressão Python de comandos: 12/12; provedor nativo: 23/23. Instalado em lsi na entrega posterior. |

`try/catch` trata exceções JavaScript nas fronteiras com provedores. Não
interrompe um laço infinito nem um bloqueio de geometria dentro do Qt/C++.
Esses casos exigem evitar ciclos e limitar trabalho antes da execução. A
[documentação de QJSEngine](https://doc.qt.io/qt-6/qjsengine.html) descreve o
tratamento de exceções do ambiente JavaScript.

## Observador externo

`tools/monitor_domainos.py` observa somente o Plasma do usuário que o executa.
Não instala serviço, modifica preferências, reinicia o Plasma ou fecha programas.

```sh
python3 tools/monitor_domainos.py --samples 3 --saida /tmp/domainos-observacao.json
python3 tools/monitor_domainos.py --follow --saida /tmp/domainos-observacao.json
```

O padrão consulta a cada 15 segundos, com prazo de dois segundos por comando.
Três faltas de resposta consecutivas são registradas como `sem_resposta`;
isso é evidência sobre a interface D-Bus, não uma identificação da causa ou
de qual widget falhou. CPU alta isolada não declara travamento. Erro imediato
da interface é `sonda_indisponivel`. Suspensão ou pausa longa de agendamento
reinicia a contagem. PID e início do processo distinguem instâncias.

O arquivo tem permissão 0600, substituição atômica e histórico limitado às
últimas 120 observações. Não contém títulos de janelas, credenciais nem
conteúdo dos aplicativos. Os oito testes cobrem os prazos, classificação,
recuperação, reutilização de PID, suspensão, pausas e gravação.

O serviço KDE instalado já usa `Restart=on-failure`, com limite de partidas.
Isso trata saída do processo; não declara watchdog de responsividade. A
[unidade oficial do KDE](https://raw.githubusercontent.com/KDE/plasma-workspace/master/shell/plasma-plasmashell.service.in)
confirma essa política. `WatchdogSec` exige notificações periódicas enviadas
pelo serviço, conforme a [documentação do systemd](https://github.com/systemd/systemd/blob/main/man/systemd.service.xml).
Não alteramos a unidade do KDE nem habilitamos recuperação automática.

## Propostas separadas da implementação

- Um proprietário de dica por seletor, com saída validada por identidade e
  suspensão somente do recurso opcional se uma tempestade for comprovada.
- Miniaturas carregadas somente para cartões visíveis. O Repeater atual
  instancia provedores inclusive para cartões fora da área de rolagem.
- Limpeza de menus parcialmente criados, com falha explícita e alternativa
  básica; não reconstruir continuamente um provedor que falha. Os mapas de
  trabalhos de Commands/WindowOperations já receberam o tratamento testado
  acima; não há timeout/repetição automático novo no applet.
- Relatos consolidados em vez de abrir repetidamente a janela de erro do Runtime.
- Recuperação automática apenas como escolha futura expressa, com limite de
  tentativas. O observador desta rodada não implementa essa política.

As revisões de alternância atuais em Fusion e no estilo KDE não reproduziram
oscilação: cem trocas rápidas, no máximo uma dica e seletor mantido aberto.
Esses ensaios offscreen não validam o compositor Wayland. Os relatórios são
`/tmp/domainos-hint-switch-review-Fusion.json` e
`/tmp/domainos-hint-switch-review-org-kde-desktop.json`.

## Prancheta provisória e alcance

A ferramenta de avaliação fica em `/tmp/irix-domainos-prancheta-estabilidade.py`,
fora do repositório. Os exemplos nela são explicativos e não executáveis pela
interface. Cada solução distingue implementação testada, proposta e mecanismo
existente. As avaliações e notas ficam em
`/tmp/irix-domainos-estabilidade-respostas-1000.json` na sessão lsi.

As fontes e o observador acompanham o próximo pacote independente. Os ZIPs
publicados e o backup aprovado em Downloads permanecem congelados. A revisão
não constitui liberação de uma nova versão, commit ou validação completa do goal.
Nenhuma instalação global ou alteração de p001532 faz parte desta rodada.

## Instalação e evidência desta rodada

Instalados apenas em lsi: `main.qml`, `DomainOSTasks.qml` e
`DomainOSIconbox.qml`. O relatório
`/tmp/irix-domainos-resiliencia-lsi-20261009.json` registra hashes exatos,
backup, uma instância do painel, resposta D-Bus e igualdade de todas as
preferências General antes/depois. O backup está em
`/tmp/irix-domainos-resiliencia-backup-lsi-20261009`.

O ensaio final da rota de preferências está em
`/tmp/irix-domainos-preferencias-rota-sinal-estavel-20261009/RESULTADO.json`.
Não é aprovação geral: os dois TypeError do PromptDialog Kirigami instalado
(`Success`/`None` indefinidos) continuam no relatório e o ensaio retorna 2.
A confirmação do clique da gaveta no lsi continua pendente. Tentativas de
clique físico e Apply falhas não foram apagadas. Uma tentativa concorrente
registrou mudança no perfil enquanto o root fazia a instalação autorizada;
o ensaio posterior com baseline estável verificou os hashes iguais.

A prova posterior
`/tmp/irix-domainos-pref-ui-fisico-runtime-curto-r2/RESULTADO.json` verificou o
clique físico no item permanente da gaveta: **14/14 controles positivos**, mesmo
applet e nove categorias. O runtime curto do teste eliminou um erro de socket
KIO que havia encoberto a janela em tentativas anteriores. Os dois TypeError
do SDK continuam registrados, com status restrito e saída 2. O ensaio comprova
a abertura correta. Em
`/tmp/irix-domainos-pref-ui-apply-restart-isolacao-r3/RESULTADO.json`, 21/22
controles foram positivos: clique físico até Iconbox, edição, Aplicar, envio da
preferência ao TaskManager, persistência após reiniciar o host privado e
configuração completa de uma segunda instância preservada. O único gate falso
foi ausência de todos os erros QML, pelos mesmos diagnósticos do Kirigami; erros
DomainOS foram zero. A prova posterior
`/tmp/irix-domainos-pref-ui-apply-discard-restart-isolacao-r5/RESULTADO.json`
acrescentou Cancelar/Descartar por clique físico e reabertura sem salvar a segunda
edição: **26/27** critérios positivos. Conserva os diagnósticos do SDK e a saída 2.

A regressão dos comandos com o provedor executável nativo está em
`/tmp/irix-domainos-command-job-regression-r2-20261009/RESULTADO.json`, **23/23**.
Usa Xvfb/D-Bus privados, quatro terminais próprios e um serviço ScreenSaver
de teste: não bloqueia a sessão real. Confirma resultados dos helpers,
atividade, falha explícita e pedidos concorrentes. A primeira tentativa foi
impedida pelo sandbox ao criar o socket e seu log foi conservado.

As provas de regressão são
`/tmp/irix-domainos-tasks-resilience-regression-20261009/RESULTADO.json`
e `/tmp/irix-domainos-wheel-resilience-native-20261009/RESULTADO.json`.
Os cinco testes de empacotamento passaram com o observador/documentação
incluídos no escopo de suporte; não foi gerado nem publicado um novo ZIP.

O observador está ativo em modo de registro, sem autostart, com saída
`/tmp/irix-domainos-monitor-lsi-20261009.json`. Este relatório é limitado e
continua sendo atualizado. O estado `respondendo` comprova apenas a sonda
naquele instante; não substitui os testes dos gestos e destinos das ações.

## Entrega posterior

O [registro de ajustes](VALIDACAO-DOMAINOS-AJUSTES-2026-10-09.md) documenta a
prancheta respondida, clique do meio 37/37, dicas/cartões/paleta 59/59 e pacote
9/9. A atualização completa dos recursos do applet e do style foi instalada
em lsi, incluindo a limpeza de pedidos de Commands/WindowOperations. O relatório
`/tmp/irix-domainos-ajustes-lsi-20261009.json` confirma fonte instalada, IDs e
preferências preservadas, retirada do colors que fixava azul e seis configurações
protegidas iguais. A validação visual do usuário e o ensaio final em p001532
continuam separados. Não se instalou recuperação automática ou patch do SDK.
