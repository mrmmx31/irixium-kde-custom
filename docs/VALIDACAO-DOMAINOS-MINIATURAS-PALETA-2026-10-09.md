# Dicas, miniaturas sem imagem e paleta — 2026-10-09

O checklist real de lsi aprovou 16 itens e recusou dois: hints ainda azuis fora
do esquema escolhido, e miniaturas sem cartões clicáveis antes de haver imagem.
Também informou conteúdo branco/ilegível nas células ao voltar às dicas textuais.
As mudanças abaixo tratam esses dois relatos; a confirmação visual final em lsi
continua sendo uma verificação separada.

## Mudanças

`DomainOSWindowThumbnails.qml` mantém um único item próprio por célula para a
janela nativa compartilhada de dicas. A visibilidade pertence à célula somente
quando sua janela é visível e contém esse item como `mainItem`. O preparo ocorre
em `aboutToShow`, com tamanho implícito definido antes de carregar uma imagem;
ao perder a janela, o conteúdo e os provedores são descarregados. O hover antigo
não mantém mais um Loader preparado. Dicas textuais são passivas; somente as
miniaturas explicitamente habilitadas são interativas.

`DomainOSWindowPreviewContents.qml` dá dimensão e superfície opaca a cada cartão,
independentemente da disponibilidade do provedor. O título, o aviso de imagem
indisponível e o alvo de ativação existem desde o início. As cores de texto têm
fallback para a paleta do controle. `DomainOSGroupMemberHint.qml` aplica a mesma
paleta local ao controle e ao seu fundo.

O arquivo `plasma/IrixClassicDomainOS/colors` foi removido: ele fixava a paleta
nativa do Plasma Style em azul. Os dois SVGs de tooltip/dialog usam agora
`ColorScheme-Background`, mantendo a geometria dos nove segmentos, as quatro
bandas de um pixel e a superfície final opaca. Luz e sombra são derivadas do
fundo escolhido. O gerador e a verificação reproduzem esse contrato.
O esquema independente `colors/DomainOS-SR10.4.colors`, o Classic anterior e a
arte aprovada do painel permanecem disponíveis e intactos.

O contrato de cores é documentado pelo [KDE](https://develop.kde.org/docs/plasma/theme/quickstart/#theme-colors).
A implementação nativa explica a [janela compartilhada e a troca de conteúdo](https://raw.githubusercontent.com/KDE/libplasma/master/src/declarativeimports/core/tooltiparea.cpp)
e seu [reparenting e dimensionamento](https://raw.githubusercontent.com/KDE/libplasma/master/src/plasmaquick/plasmawindow.cpp).
O comportamento também foi verificado com a biblioteca instalada libplasma 6.3.5
e Qt 6.8.2; a consulta ao código upstream complementa a prova instalada.

## Evidências finais

| Prova | Resultado | Escopo |
| --- | --- | --- |
| `/tmp/irix-domainos-thumbnail-lifecycle-native-r7/RESULTADO.json` | 59/59 | `plasmawindowed` instalado, Xvfb/KWin/D-Bus e perfil Irixium privados, três janelas próprias |
| `/tmp/domainos-thumbnail-lifecycle-final.log` | 15/15 | Fonte final, ToolTipDialog real offscreen, propriedade de duas células, cartas vazias clicáveis, retorno a títulos, paleta privada dourada |
| `/tmp/domainos-member-hint-palette-final.log` | 4/4 | Dicas dentro do seletor Qt Popup, texto atualizado, opção de miniatura e descarga |
| `/tmp/domainos-style-kde-palette-r1/verification.json` | 30/30 | SVG/KSvg nativos; geometria, opacidade, bandas, trama e Classic byte idêntico |

A prova nativa usou movimento do cursor real, respeitando o intervalo padrão
das dicas. Exercitou 12 trocas entre células e oito mudanças de modo; em todas
houve um proprietário visível correto e descarga do conteúdo anterior. Os três
cartões sem imagem tinham dimensões completas; clicar num deles ativou a janela
própria correspondente pelo TasksModel real. Os hashes das quatro configurações
reais protegidas permaneceram iguais, e não houve diagnóstico QML de erro.

Capturas finais na pasta `r7`: `EMPTY-CARDS.png`, `IRIXIUM-HINT-FRAME.png` e
`RESTORED-TITLES.png`. A prévia offscreen da paleta dourada está em
`/tmp/domainos-native-tooltip-palette-lifecycle.png`.

O backend sem identificação foi exercitado de propósito; esta prova demonstra
cartões e ativação sem imagem. A captura positiva de texturas X11/PipeWire
pertence à suíte separada `testar-domainos-miniaturas.py`. Não se atribui à
prova `r7` uma validação de imagem ao vivo ou de Wayland.

## Falhas preservadas e correções do ensaio

As pastas `irix-domainos-thumbnail-lifecycle-native-r1` a `r6` não foram apagadas.
`r1` parou na compilação do fixture por ausência do pacote de desenvolvimento
Qt Quick; o fixture foi adaptado aos símbolos já carregados pelo host, sem
instalar dependências. `r2` incluiu por engano a janela do próprio host junto às
três fontes do mesmo PID; o filtro passou a exigir também o título próprio.

`r3`/`r4` revelaram conteúdo preparado por `containsMouse` antigo, apesar de
invisível; a ativação dos Loaders foi desvinculada desse hover. A investigação de
`r5`/`r6` também encontrou uma falha do ensaio: `QTest::mouseMove(QWindow*)`
injeta o evento Qt, mas não desloca o cursor nativo. O cursor real ficava dentro
da miniatura grande e gerava um Leave atrasado ao trocar para texto, ocultando
a janela compartilhada. `r7` usa `QCursor::setPos` nas coordenadas globais
medidas, posiciona o fixture junto à borda inferior como o painel real e deixa
o hover nativo abrir a dica. Os estados de ambas as células, o cursor e a
geometria das janelas constam do relatório.

Nenhum timer de ação, repaint periódico, alteração global ou reinício automático
de Plasma foi inserido nos componentes de dica/miniatura.


## Captura Wayland na fonte atual

Depois da alteração do ciclo de vida, uma prova separada passou **23/23**:
`/tmp/irix-domainos-miniaturas-wayland-real-lsi-current-r1-20261009/RESULTADO.json`.
Usou o compositor e PipeWire existentes em lsi, com HOME/XDG e D-Bus privados.
O TasksModel leu somente AppPid nas linhas alheias; títulos e UUIDs foram obtidos
apenas depois de confirmar o PID do próprio processo. As duas fontes eram
QWidgets desse processo; nenhuma janela pessoal ou tela inteira foi capturada.

`NATIVE-THUMBNAILS.png` contém pixels das duas fontes próprias; após mudar e
repintar uma fonte, `NATIVE-THUMBNAILS-UPDATED.png` mostra a nova cor. Os critérios
comparam os pixels, o backend Wayland e PID/UUID atuais, além da descarga ao
ocultar/desabilitar. Dicas textuais e modo sem dicas não criam provedores de
captura. Os nove hashes de componentes e quatro configurações reais protegidas
permaneceram iguais; o host era `/usr/bin/plasmawindowed` instalado, com zero
diagnósticos QML.
O processo próprio e suas janelas foram encerrados ao fim.

A reprodução no checkout usa o mesmo cenário, dentro da própria sessão Wayland:

```sh
python3 plasma/tools/testar-domainos-miniaturas-wayland.py --saida /tmp/domainos-miniaturas-prova-nova
```

O tool não instala nem recarrega o painel, substitui o compositor ou desativa
verificações de protocolos privilegiados. Perfis e arquivos de compilação ficam
em pasta temporária do checkout; resultados e capturas próprias ficam no caminho
escolhido. Esta prova de pixels complementa o lifecycle X11 `r7`; não demonstra
os cliques de todas as aplicações pessoais ou a aprovação visual em p001532.
