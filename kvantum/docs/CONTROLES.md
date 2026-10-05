# Bloco 7 — intervalos, progresso e organização de dados

**IrixClassic 0.7.0-rc1 · manutenção: `mrmmx31`.**

Esta revisão implementa os controles restantes do roteiro como candidata de
Application Style. Não certifica fidelidade integral ao IRIX nem aprovação de
execução em KDE. Os sete blocos precisam de uma revisão integrada na sessão real.

## Desenho e medidas

| Família | Recursos e comportamento visual | Medidas preservadas |
|---|---|---|
| Sliders / scales | Trilho rebaixado; porção preenchida azul-esverdeada; cursor cinza com ranhuras; relevo invertido durante o estado de pressão recebido do Qt; marcas de escala separadas | Trilho 14, cursor 16 × 26, tamanho do indicador anterior |
| Progresso | Trilho rebaixado e preenchimento azul-esverdeado dentro da moldura; desenho para indisponibilidade, intervalos conhecidos e animação indeterminada nativa | Espessura nominal 18; `spread_progressbar=false` mantém o preenchimento dentro do trilho |
| Divisores | Perfil próprio e ranhuras; desenho mestre vertical, transformado pelo Kvantum quando horizontal | Área total 7; borda passa de 2 para 1, deixando 5 unidades para o indicador, sem estreitar a área de arraste |
| Cabeçalhos | Faixa elevada, realce ao apontar, bisel invertido quando o motor recebe pressão; separador e indicadores de ordenação próprios | Relevo 3; margens e mínimos anteriores |
| Listas, tabelas e árvores | Fundo normal pertence à vista; apontado, seleção com foco e seleção sem foco recebem superfícies diferentes; contorno de foco já existente é preservado | Margens e mínimos anteriores; expansor 9 |
| Agrupamentos | Contorno gravado com centro transparente; sem cobrir o título nem a área do aplicativo | Relevo reservado 3; geometria de títulos nativa |
| Tooltips | Superfície opaca e borda retangular; sem sombra externa moderna adicionada | Margens e atraso anteriores |
| Docks, MDI e size grip | Título de dock próprio; paleta e pequenos símbolos de subjanela MDI; cantoneira de redimensionamento | Dimensões anteriores; MDI e size grip usam os tamanhos já configurados |
| Dial Qt | Disco, indicador e foco próprios para evitar mistura com o tema de fallback | Tamanho e ângulo continuam sendo do widget |

As medidas são lógicas. A altura efetiva depende também das fontes e das
restrições do aplicativo. Não foram modificados fontes, escala, cores globais,
checkboxes, menus, abas, campos, botões ou recursos de scrollbar dos blocos 1–6.

A cor de preenchimento `#719e9e` e a paleta cinza são escolhas coerentes com as
referências disponíveis. **Não foram medidas neste bloco em uma figura histórica
renderizada de cada controle.** Os desenhos exatos do slider, progresso, cabeçalho,
divisor, dial e MDI são adaptações documentadas, não cópias pixel a pixel.

## Estados realmente consumidos pelo Kvantum 1.1.4

- **Slider:** a parte vazia/preenchida do trilho usa normal/toggled; o cursor
  utiliza os estados fornecidos pelo `QStyleOptionSlider`. O indicador decorativo
  é independente do preenchimento. Horizontal e vertical usam transformações do
  mesmo mestre. O Qt decide valores, inversão, passos, limite e teclado.
- **Progresso:** o percentual é calculado/desenhado pelo aplicativo e pelo motor.
  O intervalo 0–0 solicita progresso indeterminado; nenhum temporizador foi
  acrescentado ao tema. Cores de texto existentes foram mantidas para contraste.
- **ItemView:** `pressed` representa, neste caminho, seleção com foco; não uma
  ordem para executar a ação de um item. `toggled` representa seleção sem foco.
  O tema não transforma seleção em ativação. Fundo em repouso não é pintado pelo
  motor; mantemos o mapa normal transparente e a paleta da vista intacta.
- **HeaderSection:** inativo/desativado pode ser produzido pelo motor a partir de
  normal e opacidade. A pressão recebida usa `State_Sunken`. A separação usa o nome fixo `header-separator`, diferente
  dos prefixos configuráveis dos indicadores de ordenação.
- **Splitter:** o motor tem sua própria escolha de estados e pode não fornecer
  pressão separada; não prometemos uma transição que o aplicativo não solicita.
- **Dial:** `dial`, `dial-handle`, `dial-notches`, `dial-focus` são nomes fixos
  usados pelo motor. Não existe um conjunto universal de estados pressed/hover
  para esse caminho. As pequenas ranhuras são **decorativas**, não uma escala
  numérica calibrada: o Qt determina o ângulo real do indicador.
- **Toolbox:** o Kvantum desenha sua forma diretamente com QPainter e cores de
  paleta; não consome um SVG de moldura `ToolboxTab` para substituir essa forma.
  O desenho nativo foi preservado, e a galeria o expõe para revisão.
- **MDI:** afeta somente subjanela interna de `QMdiArea`. Controles maximizado/
  integrado ao menu, ícone de sistema e títulos especiais ainda podem usar os
  ícones padrão do Qt. Não altera a decoração KWin nem move/remove comandos.

Recursos de fallback e seus limites estão em `COBERTURA-IRIXCLASSIC.md`.

## Galerias e testes

Na raiz do clone:

```sh
bash kvantum/testar-controles.sh
bash kvantum/prever-controles.sh
bash kvantum/prever-controles.sh --testar
bash kvantum/prever-controles.sh --qtquick
```

Os primeiros testes são de arquivos, contratos, mapas e recuperação. A galeria
é de controles **Qt Widgets reais**, sem `QProxyStyle`, folhas de estilo locais
ou uma implementação substituta de eventos. `--qtquick` abre uma galeria manual
com controles nativos do KDE, quando os respectivos módulos estão instalados.

Para salvar somente as imagens da galeria e o resultado do teste:

```sh
bash kvantum/prever-controles.sh --testar --capturas "$HOME/Downloads/irix-controles-07"
```

A pasta deve ser nova ou vazia. Não há captura de outras janelas ou do desktop.
PyQt6 ou PySide6 e Kvantum para o mesmo Qt são necessários. Dependências ausentes
retornam 77: isso significa **não executado**, não aprovado. Nada é instalado por
esses comandos. As configurações são temporárias e locais ao processo.

Aceitação manual: testar sliders por arraste e teclado nas duas orientações;
progresso em 0/1/50/99/100%, desativado e indeterminado; seleção simples, Ctrl e
Shift; perda/retorno de foco; ordenação e redimensionamento de colunas; expansão
de árvore; divisores nas duas orientações; layouts RTL; campos dentro de grupos;
subjanelas MDI; tooltip legível; aplicativos com paletas próprias.

## A pendência das setas não foi ocultada

Os desenhos e o reparo opcional anterior estão idênticos à 0.6.0-rc1. O último
inventário recebido apontava QML sem o marcador do reparo e preferência por qrc,
mas isso não comprova o estado atual após outras tentativas. Sem o resultado de
interação não é possível concluir se o problema é carregamento, hit-test, ação,
sinal de pressão ou um componente diferente daquele ensaiado.

O diagnóstico já existente continua disponível, sem reinstalação do sistema:

```sh
bash kvantum/comparar-setas.sh --saida "$HOME/Downloads/setas-quatro-caminhos-07"
```

O `COMPARACAO-SETAS.json` distingue Widgets, importação KDE instalada, arquivo
QML direto e cópia temporária com o reparo. Coletar o relatório não corrige a
aplicação aberta. Não se afirma que as setas foram resolvidas nesta revisão.

## Referências e limites históricos

SGI, *Indigo Magic User Interface Guidelines*, capítulo 9, Controls — descreve
lists, scales e componentes especiais; é referência de organização/semântica,
não fonte de código nem uma prova de equivalência geométrica desta revisão:
https://techpubs.jurassic.nl/library/manuals/2000/007-2167-003/sgi_html/ch09.html

Kvantum 1.1.4, contrato de configuração:
https://github.com/tsujan/Kvantum/blob/V1.1.4/Kvantum/doc/Theme-Config

Kvantum 1.1.4, caminhos efetivos de renderização, incluindo CE_HeaderSection,
CE_Splitter, CE_ProgressBar*, CC_Slider, CC_Dial, CE_ToolBoxTabShape e CC_TitleBar:
https://github.com/tsujan/Kvantum/blob/V1.1.4/Kvantum/style/Kvantum.cpp

Qt, propriedade de controle e semântica de intervalo:
https://doc.qt.io/qt-6.8/qabstractslider.html
https://doc.qt.io/qt-6.8/qprogressbar.html
