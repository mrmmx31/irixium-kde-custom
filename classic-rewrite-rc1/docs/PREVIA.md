# IRIX Classic — fundo da miniatura

## Causa e escopo

Na integração Aurorae do Plasma 6.3.6, `Decoration::init()` identifica a prévia
pela propriedade C++ `visualParent`. O item QML recebe o `PreviewItem` como pai
visual e o Aurorae grava `drawBackground=false` nesse pai. Assim, a cor que o
KCM normalmente desenharia na área cliente deixa de ser aplicada.

A IRIX Classic rc2 desenha somente a moldura e deixa a área cliente transparente.
Isso está correto para uma janela real, mas na miniatura permite enxergar a
moldura da janela de trás através do corpo da frente. O SVG do Irixium moderno
preenche seu centro; copiar o bege desse SVG não seria uma boa correção, pois
cor de título e cor de fundo do corpo têm funções diferentes.

## Correção rc3

`PreviewSupport.js` reconhece o contrato observado no `PreviewItem`:
`drawBackground` booleano, `windowColor` presente e `decoration` exatamente igual
à decoração em uso. Um pai desconhecido nunca habilita o preenchimento.
Não há identificação por legenda, nome de aplicativo, tamanho, resolução ou
nome de classe presumido.

`PreviewBackground.qml` cria um retângulo **somente** quando esse contrato está
presente e o pai não está desenhando o fundo. O retângulo usa `windowColor` do
KCM, com alpha 1. Usa a geometria compartilhada de `Surface` para ocupar apenas
a área cliente; não recobre barra, botões, divisórias nem moldura. A instância
é desenhada antes de `Surface`, não recebe entrada de mouse e desaparece em
janelas recolhidas ou sem área cliente positiva. Se o hospedeiro passar a
pintar seu próprio fundo, o preenchimento adicional é desativado.

O novo componente não escreve propriedades no pai nativo. Em uma janela real,
o pai é a superfície offscreen do Aurorae, não o PreviewItem; o Loader fica
inativo e **nenhum retângulo de preenchimento é criado**. `alpha: true` e o
Canvas original permanecem intocados. Transparência configurada no aplicativo,
conteúdo, entrada, duplo clique e capacidades dos controles não são alterados.

A miniatura mostra a cor de janela fornecida pelo KCM. Ela não renderiza o
Application Style Kvantum nem prevê a cor particular de cada aplicativo. Uma
cor igual àquela atrás da miniatura não é transparência: o teste relevante é
que o corpo da frente oculte a moldura de trás.

## Atualização e teste

Esta revisão usa o instalador e identificador existentes. Não cria outra entrada
IRIX Classic e não instala o tema Kvantum nem o Irixium moderno.

1. Aplicar o patch ao clone e executar `bash classic-rewrite-rc1/testar.sh`.
2. Fechar completamente Configurações do Sistema (o processo guarda componentes
   QML carregados; apenas mudar de página pode reutilizar a prévia antiga).
3. Executar, sem sudo, `bash classic-rewrite-rc1/instalar.sh --verificar` e depois
   `bash classic-rewrite-rc1/instalar.sh`.
4. Reabrir Configurações do Sistema em Decorações de janelas. A miniatura da
   frente deve ocultar a moldura de trás, mantendo a cor de corpo separada da
   cor do título. Não é necessário mudar o Application Style para isso.
5. Para o KWin da sessão também recarregar o código atualizado, salvar o trabalho,
   encerrar a sessão e entrar novamente. Não usar `kwin --replace`.

Retorno à cópia instalada anterior: `bash classic-rewrite-rc1/restaurar.sh`.
O roteiro completo está em `ACEITACAO.md`.

## Testes e limite

Há testes Node do JavaScript de detecção/geometria usado em produção, testes
estáticos de integração e preservação, e 12 testes QtTest novos que usam um
hospedeiro QML simulado. Executar estes últimos com `bash testar.sh --qml`.
Mesmo quando aprovados, os testes do hospedeiro simulado não substituem o KCM
nativo. Neste ambiente o executor Qt 6 não está disponível e a execução QtTest
retornou 77; não foi homologada uma sessão real KWin.

O contrato é de integração privada do Plasma 6.3.6. Se ele mudar em outra versão,
o comportamento seguro é não preencher, e não tentar reconhecer janelas reais
por heurísticas. Os arquivos fontes primários consultados estão abaixo.

## Fontes primárias

- Aurorae, `init()`, atribuição do pai visual e supressão de `drawBackground`:
  https://github.com/KDE/kwin/blob/v6.3.6/src/plugins/kdecorations/aurorae/src/aurorae.cpp
- Contrato do PreviewItem e sinais de notificação das propriedades:
  https://github.com/KDE/kwin/blob/v6.3.6/src/kcms/decoration/declarative-plugin/previewitem.h
- Cor inicial de janela a partir de QPalette e desenho do fundo da área cliente:
  https://github.com/KDE/kwin/blob/v6.3.6/src/kcms/decoration/declarative-plugin/previewitem.cpp
- Montagem das duas miniaturas sobrepostas:
  https://github.com/KDE/kwin/blob/v6.3.6/src/kcms/decoration/ui/Themes.qml

A implementação é restrita ao pacote; não modifica esses arquivos de sistema.
