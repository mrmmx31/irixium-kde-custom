# DomainOS 0.2.10 — gavetas e luz de atividade

A mudança funcional desta versão está em `DomainOSTray.qml` e na ligação ao
tracker de `DomainOSPanel.qml`. O helper de apresentação usa begin/finish com
limpeza em finally, conserva as guardas de disponibilidade e reporta retorno
falso ou exceção como falha. Não altera handlers dos provedores, geometria,
cores, repetição nativa, menus das tarefas ou a seleção do Pager.

## Ensaio dirigido da bandeja

**50/50 verificações**, sem erros QML, em Xvfb, perfil e D-Bus privados. O
ensaio usa o loader do painel e o tracker de produção, recibo de quadro
apresentado, Popup.Window e clique físico no botão Status. Cobre abertura e
segundo clique fechando, disponibilidade ausente, callback falso, exceção e
recuperação, tracker opcional ausente e a preferência de manter a luz depois
do retorno. O único timer é o da preferência já existente, desligada por padrão.

Artefato local: `/tmp/irix-domainos-tray-activity-010-r4/RESULTADO.json`.
Seu SHA256 é `d9bf41d33bb53ef604180319bbb53588c90d963b3001e0bfd3a5b0fa62d5d6d5`.
Os provedores do fixture são duplos declarados; esse ensaio não comprova a
conclusão de uma operação SNI, hardware pessoal ou desempenho universal.

## Cores e desenho

Os componentes de paleta, pintura, scrollbars e módulo nativo conservam os
bytes validados pela [0.2.9](VALIDACAO-DOMAINOS-0.2.9-2026-10-09.md). As provas
nativas de aplicação de cinco esquemas no mesmo engine e pintura da arte
mantêm seu alcance. As gavetas utilizam esses mesmos papéis dinâmicos; o tempo
da luz não governa a troca do esquema. O desenho aprovado e o backup congelado
de Downloads não foram modificados.

Resultados históricos não são apresentados como uma execução integral nova.
O aceite visual das sessões pessoais e integrações condicionais permanece
separado dos ensaios privados.

## Reset das preferências atuais

Ensaio dirigido com duas instâncias nativas, as 45 preferências do esquema
atual, ConfigView, botões Aplicar/Descartar e reabertura/reinício: **26/27**.
Os contratos funcionais passaram: defaults exatos dos 45 campos, inclusive
`mailCountsEnabled=false`, persistência após reinício, reset da categoria
Correio e preservação integral da segunda instância.

O resultado bruto continua `failed`: a verificação de zero diagnóstico falha
pelos seis TypeErrors de `PromptDialog.qml` do Kirigami instalado, referentes
a `None` e `Success`. Esses diagnósticos não foram suprimidos nem corrigidos
por alteração do SDK global. A análise distingue esse limite dos contratos
funcionais, sem converter o resultado bruto em aprovação integral.

Artefatos: `/tmp/irix-domainos-reset-geral-45-009-20261009-r3/RESULTADO.json`
e `RESULTADO-ANALISADO.json`. SHA256 do bruto:
`34216d2ec8a0646e13144227e48ec17c74b5dc124cdf102ab802e06b7057daab`.
A produção das páginas/esquema permanece idêntica nesta atualização. O driver
teve seu prazo de teste corrigido para permitir concluir suas etapas; não
foi introduzido tempo de espera em nenhum controle do painel. Tentativas
anteriores interrompidas pelo prazo/socket permanecem preservadas.

## Diálogos do Pager

**93/93 verificações** com o Pager atual, KWin/Xvfb e áreas de trabalho
privados. Os botões padrão receberam cliques XTest reais; o injetor respeitou
o intervalo de duplo clique do Qt para conferir ações simples distintas.
Criar, renomear e remover confirmaram IDs, nomes e quantidade no KWin.
Cancelar não executou operações; confirmar executou exatamente uma por
pedido. A tentativa de remover a última área foi recusada, preservando seu
UUID. Não houve erros QML nem leitura de configurações pessoais.

Artefato: `/tmp/irix-domainos-pager-crud-dialogs-010-r5/RESULTADO.json`, SHA256
`61004dcd0326b4e07e2b24a6f33708038da4351f47d91d4c2cbc04c69f037ab8`.
O fixture restrito não instala o style Classic e registra os avisos de sua
ausência; isso não é uma prova de pintura desse style. O ensaio não repete
os testes anteriores de navegação, roda, geometria ou composição integral.
