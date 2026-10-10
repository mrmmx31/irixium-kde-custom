# DomainOS 0.2.3 — dicas e destaque de janelas

## Relato e evidência

O travamento ocorreu ao mostrar o título dentro da lista de um grupo, conforme
identificação do usuário. No processo afetado, o D-Bus não respondeu e foram
medidos 6,01 segundos de CPU em 6,01 segundos. As duas amostras de pilha passaram
por geometria/transient parent de `PopupPlasmaWindow` e máscara `FrameSvg`.
Esses dados localizam a investigação; não demonstram uma causa única no KDE.

A recuperação inicial desligou temporariamente o ToolTipArea na cópia instalada
em lsi. Isso foi substituído pela correção abaixo, com as dicas reativadas.
O original e os backups de instalação continuam em `/tmp`; o ZIP 0.2.2 e o
backup aprovado em Downloads não foram sobrescritos.

## Correção

- Os títulos dentro do seletor usam `Controls.ToolTip` com `Popup.Item`, na
  janela já aberta da lista. Não instanciam outra janela `PlasmaQuick::ToolTipDialog`.
- O texto faz parte do `contentItem` da dica; não é reparentado para a linha da
  lista. Conserva caracteres literais, quebra de linha e o título atual/PID.
- As dicas das células continuam nativas e são ocultadas enquanto a lista está
  aberta. Miniaturas permanecem opcionais; o conteúdo e os provedores são
  compartilhados entre as apresentações, sem captura no modo de títulos.
- `highlightWindows` fica **false** no schema, na página de preferências e nos
  fallbacks do painel. O usuário esclareceu que o destaque deve exigir opção
  expressa. A preferência é independente das dicas e das miniaturas.
- Quando habilitado, o destaque acompanha o hover da célula ou do título de um
  membro. A identificação do membro não exige uma linha de tarefa de topo:
  janelas agrupadas são validadas por chave/PID e usam seus IDs nativos atuais.
- Dicas de texto são transparentes ao ponteiro: não interceptam o hover do
  título seguinte quando se sobrepõem à lista. Só as miniaturas opcionais
  mantêm interação. O observador de destaque nas células fica desativado
  junto com a preferência; reutilizar uma célula cancela o alvo antigo.
- Sair do item, fechar a lista, ocultar o painel, perder o alvo ou desligar a
  preferência cancela o destaque. A saída atrasada do item anterior não cancela
  o novo. Não foi introduzido timer de pintura, clique ou atualização do painel.

## Verificação e limites

| Prova | Resultado / alcance |
| --- | --- |
| `/tmp/irix-domainos-group-hint-highlight-native-r1/RESULTADO.json` | **108/108**. Xvfb, KWin e D-Bus privados, estilo Qt KDE, janelas reais do processo de teste. Grupos de 3/15/16, rolagem, reabertura, vinte movimentos de ponteiro, dez mudanças reais de título, permanência dos objetos/dica, pintura no tooltip, destaque desligado por padrão, membro agrupado aceito pelo backend, troca/saída e desativação. Composição desligada nesse ensaio: confirma o encaminhamento nativo e a propriedade de destaque, não o efeito visual final do compositor. |
| `/tmp/irix-domainos-highlight-physical-r5/RESULTADO.json` | **111/111** na fonte final. Acrescenta movimento físico entre dois títulos e saída da lista, verificando o proprietário do destaque. A tentativa r4 registrou falha ao passar pelo texto sobreposto; a dica textual foi tornada não interativa. Mesma limitação: compositor desligado. |
| `/tmp/irix-domainos-highlight-native-clicks-r1/RESULTADO.json` | **17/17**. Clique simples, menu KDE e duplo clique real com xdotool em clientes próprios; perfis pessoais preservados. |
| `plasma/tests/test_domainos_member_hint.py` | **4/4**. Hover Qt dentro de `Popup.Window`, vinte atualizações do título, posição visual do texto, preferência desligada, miniatura opcional/descarregada e remoção do alvo. Backend offscreen: não comprova captura real. |
| `plasma/tests/test_domainos_window_highlight.py` | **5/5**. Provedor espião, padrão sem pedidos positivos, troca com saída atrasada, saída atual, preferência desligada e PID/alvo inválido. Não é uma prova do compositor. |
| `plasma/tests/test_domainos_thumbnails.py` | **11/11** após extrair o conteúdo compartilhado. Ciclo de carga/descarga, títulos ordenados/literais, ausência de captura no modo textual e indisponibilidade explícita. |
| `tests/test_domainos_defaults_schema.py` | **2/2**. As páginas de reset acompanham os valores do schema. |
| `/tmp/irix-domainos-destaque-final-lsi-20261009.json` | Instalação somente em lsi, backup, uma instância, opção de destaque false conforme o pedido e comparação das demais preferências. |

O print `GROUP-HINT.png` do ensaio nativo mostra o título completo legível na
dica. Não se capturou conteúdo de aplicativos pessoais para substituir esse teste.
A amostra posterior à primeira instalação confirmou resposta do D-Bus e CPU
sem saturação naquele intervalo; isso não equivale à validação manual do hover.

As tentativas Wayland com QQuickView e Plasma privado conservaram os perfis
pessoais, mas **não reproduziram de forma confiável a sequência completa de
hover e travamento**. Algumas tiveram medição dependente de delegate destruído,
outros enviaram eventos à janela proprietária em vez do popup, e a entrega de
ponteiro do QtTest não confirmou o hover pretendido. Resultados falhos continuam
separados. Não são provas positivas do funcionamento da versão final em Wayland.
A confirmação na sessão real de lsi ainda precisa completar esse alcance.

O dimensionamento teve falhas intermitentes ao reabrir 15 membros: altura 178
apesar do tamanho preferido 610, em `fix-r4-final`, `highlight-native-r3-final`
e `highlight-physical-r4`. A execução r5 passou sem explicar a corrida; esses
relatórios continuam preservados. A revisão posterior encontrou o tamanho
explícito retido pelo popup nativo. O seletor agora usa `implicitHeight` e
redefine a altura explícita uma vez ao abrir ou mudar o número de membros,
sem alterações por hover, timer ou pintura.

`/tmp/irix-domainos-group-natural-height-position-r4/RESULTADO.json` passou
**165/165**: alturas finais já em `aboutToShow`/`opened`, sete reaberturas de
3/15/16 membros, crescimento/redução ao vivo e medição da posição/tamanho da
superfície nativa. Os rodapés ficaram inteiramente dentro da tela. Uma primeira
tentativa apenas com altura natural falhou e permanece em
`/tmp/irix-domainos-group-natural-height-r1/RESULTADO.json`; os ensaios
intermediários também foram mantidos. Isso verifica a corrida em X11 privado,
sem declarar cobertura de todos os backends ou substituição da prova manual.

O roteiro Qt offscreen de 85 critérios parou após 34 positivos, no envio de
duplo clique (`iconbox-highlight-disabled-r3`). Um ensaio instrumentado com
pressão explícita passou 85, mas não substitui o roteiro original nem prova
o mesmo gesto. O duplo clique físico passou no ensaio nativo de 17 critérios;
a divergência do roteiro offscreen fica registrada, sem atribuir causa não
comprovada nem reclassificar a tentativa falha.

## Entrega e pendências do goal

A fonte identifica a correção como 0.2.3. O pacote 0.2.2 distribuído não contém
esta correção e permanece congelado. A configuração de p001532 e instalações
globais não foram modificadas nesta rodada.

O usuário salvou o checklist GTK de lsi em
`/tmp/irix-domainos-checklist-20261009-uid1000.json`, em 9 de outubro às
14:07 (UTC−4). **16/18 itens aprovados**: flutuação, rolagem, seleção de grupos,
seletor individual, os três estados do duplo clique, ações geométricas do Pager,
fechamento pelo mesmo botão, dicas e retorno por Plasma Style. O seletor de
uma janela deve continuar com as opções de selecionar e ativar que já apresenta.

Dois itens foram reprovados: dicas/quadros ainda azulados fora do esquema atual;
miniaturas que não apresentam o cartão clicável enquanto a captura carrega, e
artefatos nos ícones ao retornar ao modo textual. São falhas atuais em análise,
e não aprovação de captura ou da troca de modos na fonte final. O JSON pessoal
permanece provisório e não é incluído no pacote ou versionado.

Continuam separados da correção: confirmação dos efeitos opcionais na sessão
real, fechamento desses dois itens reprovados, teste final em p001532 e bloqueio
físico de sessão (F27).
O arraste entre miniaturas do Pager permanece adiado por decisão anterior.
Não se declara o goal completo por esses testes privados.
