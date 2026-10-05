# Bloco 6 — abas do IrixClassic 0.6.0-rc1

Manutenção: `mrmmx31`. Escopo: Kvantum / Qt Widgets e sua integração com o desktop.
Não altera a decoração de janela, GTK, fonte global ou os controles dos blocos 1–5.

## Referência e adaptação

A documentação SGI do **VkTabPanel**, no capítulo 14 do ViewKit, descreve abas
sobrepostas em linha ou coluna, com a selecionada desenhada à frente. Também
explica texto/ícones e altura dependente da fonte. Isso confirma uma referência
histórica de abas, além dos prints anteriores que não mostravam esse controle.

Esta revisão não é uma cópia pixel a pixel das figuras do manual. As laterais
inclinadas, as cores, a largura das peças laterais e o recobrimento de **4 unidades**
são adaptações explícitas. Não foi obtida uma figura histórica sem redimensionamento
que permita certificar todas essas medidas. A moldura usa a linguagem de relevo
já existente no IrixClassic, sem importar bibliotecas, código ou fontes da SGI.

**Limite funcional importante:** no VkTabPanel, abas excedentes se colapsam nas
extremidades e abrem um menu de todas as abas. Um tema QStyle não acrescenta esse
comportamento a um QTabBar. O pacote mantém a navegação, rolagem, menus e fechamento
que o aplicativo Qt oferece. Não se mascara uma seta nativa como se ela abrisse
um menu histórico inexistente.

## Recursos e medidas

| Parte | Implementação |
|---|---|
| Aba normal | Face cinza mais escura e laterais inclinadas. |
| Ponteiro | Clareamento discreto, sem marcar a aba como selecionada. |
| Selecionada | Face alinhada ao painel e passagem sem linha fechada no encontro com a página. |
| Documentos | Família `floating-ic-notebook` com acabamento próprio; não exige página pintada atrás. |
| Moldura da página | Cortes próprios para as quatro orientações e junções de 6×3 ou 3×6. |
| Fechar | Grade 12×12; máscara escura estável; realce de pressão sem mover o símbolo. |
| Transbordamento | Indicador de borda próprio; função continua nativa do Qt. |

Em `[Tab]`, as peças laterais passam de 2 para 6 unidades, mas as margens de texto
laterais passam de 6 para 2. Assim, a reserva por lado continua **8 unidades**.
Top/bottom permanecem 2, com margem vertical de texto 1; o mínimo nominal continua
22. Não se promete altura final fixa: fonte, ícone e aplicativo participam do cálculo.
`frame.expansion=0` permanece; `active_tab_overlap=4` é a única mudança global além
do comentário de versão. O espaçamento entre abas nativas é definido pelo Kvantum.

## Estados que o motor realmente usa

Kvantum 1.1.4 usa `normal`, `focused` e `toggled` para o corpo da aba e ignora
`State_Sunken` e o desenho disabled nesse caminho. O texto indisponível e o bloqueio
de ativação continuam nativos; não há promessa de um SVG pressionado de aba que
nunca seria consultado. Foco de teclado usa os recursos de foco já existentes.

O botão de fechar tem um contrato diferente: `normal`, `focused`, `pressed`,
`disabled` e, na aba selecionada, `toggled`, `toggledFocused` e `toggledPressed`.
A grafia camelCase desses dois últimos é intencional. **`toggled` não é pressão**:
o fechar de uma aba ativa mantém a aparência de repouso. Só `pressed` ou
`toggledPressed` acrescentam o realce inferior/direito.

Janela inativa não muda essa paleta. As variantes `-inactive` repetem seus mapas.
`TabBarFrame` não força uma moldura sobre a área útil do aplicativo.

## Verificação local

Na raiz do clone:

```sh
bash kvantum/testar-abas.sh
bash kvantum/prever-abas.sh
bash kvantum/prever-abas.sh --testar
bash kvantum/prever-abas.sh --qtquick
```

A galeria Widgets contém quatro orientações, documento, nomes longos, aba
indisponível, foco de teclado, fechar e layout RTL. `--testar` usa QTest nas próprias
janelas e o plugin verdadeiro. A galeria **Qt Quick é manual**, porque o componente
KDE pode impor outra disposição. Ausência de bindings/plugin retorna 77, não aprovação.
`--capturas /pasta/nova` é opcional e captura apenas os widgets da galeria.
Não são feitas capturas gerais da tela nem alterações na seleção global do Kvantum.

A prancha `PREVIA-ABAS.png` é uma composição dos mapas/fatias do SVG, não um screenshot
Qt. As transformações de orientação nela servem à inspeção da geometria; as fontes
e o encaixe real precisam ser conferidos na galeria nativa.

Critérios locais: seleção visível; texto não invade as laterais; encontro sem
fresta no painel; foco pelo teclado; aba indisponível não ativa; fechamento afeta
somente a aba solicitada; transbordamento conserva os controles oferecidos pelo
aplicativo; nenhuma regressão dos campos, menus ou botões já revisados.

## Instalação e retorno

```sh
bash kvantum/instalar-classic.sh --verificar
bash kvantum/instalar-classic.sh
# Reabra os aplicativos; sem sudo e sem alterar a decoração.
bash kvantum/restaurar-classic.sh
```

Instalar o tema **não aplica** o reparo Qt Quick opcional das setas. Esse problema
continua pendente de comprovação no componente efetivamente carregado.

## Fontes técnicas

- SGI ViewKit, capítulo 14, Tab Panel Component:
  https://techpubs.jurassic.nl/library/manuals/2000/007-2124-005/sgi_html/ch14.html
- SGI VkTabPanel(3x):
  https://techpubs.jurassic.nl/manpages_0530/cat3/Vk/VkTabPanel.html
- Kvantum 1.1.4, configuração de Tab/TabFrame/TabBarFrame e active_tab_overlap:
  https://github.com/tsujan/Kvantum/blob/V1.1.4/Kvantum/doc/Theme-Config
- Kvantum 1.1.4, CE_TabBarTabShape e PE_IndicatorTabClose:
  https://github.com/tsujan/Kvantum/blob/V1.1.4/Kvantum/style/Kvantum.cpp
- Kvantum 1.1.4, junções de renderFrame:
  https://github.com/tsujan/Kvantum/blob/V1.1.4/Kvantum/style/rendering.cpp
