# Bloco 1 — barras de rolagem, 0.1.0-rc2

## Escopo

Apenas IrixClassic Kvantum. Largura 18, extensão mínima 34, setas persistentes e
nome do tema preservados. Nenhuma mudança na seleção global, fontes, escala,
decoração da janela, tema Irixium ou GTK. `PLANO-IRIXCLASSIC.md` mantém o roteiro
completo; esta revisão NÃO encerra os outros seis blocos.

## Reconstrução

| Parte | rc1 | rc2 |
|---|---|---|
| Símbolo ↑ | 7×4, achatado | 8×9, mapa da amostra IRIX fornecida |
| Célula da seta | 18×18 | 18×18, mesmos alvos nativos |
| Ranhuras | Escuro/claro, passo 2 | Claro `#E1E1E1` e preto `#000000`, passo 4 |
| Puxador | Face genérica do botão | Perfil próprio: cinza `#999999`, faixas claras/escuras amostradas |
| Ranhuras versus borda | Indicador com margem, restrito ao interior | Indicador cobre largura total de 18 e atravessa faixas laterais |
| Trilho | Herdado do menu | Recursos exclusivos; não altera sliders ou progresso |
| Hover | Igual ao repouso | Igual ao repouso; sem animação ou brilho novo |
| Pressão | Genérica | Relevo invertido sem mover seta nem ranhuras; adaptação declarada |
| Indisponível | Mapa genérico | Seta em baixo contraste/baixo-relevo; ação continua bloqueada pelo Qt |

A referência é *Confidence Tests*, imagem 1024×768 fornecida no projeto. O
triângulo ↑ veio da caixa `(625,587)-(633,596)`; o perfil lateral do puxador de
`(620,620)-(638,621)`; a faixa das ranhuras de `(620,654)-(638,664)`.
Coordenadas usam limite superior exclusivo. SHA-256 do PNG:
`7fbdbd84aadd1b6ddf337dcf21d8fde7e094a3711ae91704374de74c59eea1f9`.
O original completo não é distribuído; não há screenshot embutido no SVG.

O triângulo ↓ usa o espelhamento do ↑, e ←/→ usam a transposição. É uma adaptação
simétrica, não a afirmação de identidade de todo pixel de toda seta histórica.
A célula quadrada foi normalizada para a métrica Qt de 18; a amostra apresenta
algumas diferenças de rasterização entre orientações/controles. Pressão e estado
indisponível não estão documentados pelas capturas em repouso.

## Contrato com o Kvantum 1.1.4

- `CE_ScrollBarAddLine/SubLine` escolhe `up/down` e o estado `disabled` quando o
  valor atinge a extremidade correspondente. A orientação horizontal é desenhada
  por transformação do pintor; não depende de o Qt pedir arquivos `left/right`.
- `CE_ScrollBarSlider` pinta `ic-scroll-thumb-*` e depois `ic-scroll-grip-*`.
  `frame.left/right=0` permite atravessar as laterais; elas são desenhadas dentro
  do interior. As tampas superior/inferior têm 2/3 pixels. `indicator.size=10`
  controla o comprimento das três ranhuras; `center_scrollbar_indicator=false`
  faz a largura acompanhar o puxador inteiro. Isso evita esticar um indicador
  quadrado 10×10 para tentar reproduzir uma faixa 18×10.
- Desativado: o engine utiliza o fundo normal do puxador com opacidade 0,7 e
  escolhe o estado disabled para o indicador. Um `thumb-disabled` no SVG, sozinho,
  não prova que será desenhado. O teste local mostra o resultado real desse caminho.
- `Slider`, `SliderCursor` e `Progressbar` conservam as propriedades efetivas da
  rc1. Seus recursos `ic-groove`, `ic-thumb`, `ic-grip` não foram redesenhados.
- Não alterar globalmente a largura para corrigir um caso imposto pelo aplicativo.
  Este perfil é calibrado para 18 unidades e escala 100%. Outras larguras/escala
  fracionária podem reamostrar as faixas laterais; precisam de teste separado.

Código primário conferido:
https://github.com/tsujan/Kvantum/blob/V1.1.4/Kvantum/style/Kvantum.cpp
(seções `CE_ScrollBarAddLine`, `CE_ScrollBarSubLine`, `CE_ScrollBarSlider`).

https://github.com/tsujan/Kvantum/blob/V1.1.4/Kvantum/doc/Theme-Config
(chaves `scroll_width`, `scroll_min_extent`, `center_scrollbar_indicator`).

## Limites históricos e funcionais

O manual SGI, capítulo 9, seção Scrollbars, descreve impressão da posição inicial
durante arraste, cancelamento por Escape e desaparecimento só do puxador quando
não há conteúdo oculto. Essas funcionalidades não são acrescentadas pelo SVG.
A implementação conserva o QScrollBar nativo; não intercepta o desktop inteiro.
`range=0`, wheel, teclas, page step e repetição de clique seguem Qt e aplicativo.
Não se deve anunciar uma implementação completa do comportamento Motif.

https://techpubs.jurassic.nl/library/manuals/2000/007-2167-003/sgi_html/ch09.html
https://doc.qt.io/qt-6.8/qscrollbar.html

## Teste local e captura real

Na raiz do checkout, sem instalação:

```sh
bash kvantum/testar-rolagem.sh
bash kvantum/prever-rolagem.sh
bash kvantum/prever-rolagem.sh --tema Irixium
```

A galeria usa uma configuração temporária, tem as duas orientações, RTL,
limites, sem intervalo e desativado. Exige PyQt6 ou PySide6 e Kvantum Qt 6.
Ausência é código 77 (não é aprovação), sem instalar dependências.

Para testes nativos e PNGs reais offscreen:

```sh
bash kvantum/prever-rolagem.sh --testar --capturas /tmp/irixclassic-rolagem-qt
```

São verificados cliques de incremento/decremento, arraste vertical, operação
bloqueada, incremento horizontal LTR/RTL e teclado. Os PNGs e METRICAS.json ficam
no diretório indicado. Não são equivalentes a testar todos os aplicativos no KWin.
`PREVIA-ROLAGEM.png` e `ESTADOS-ROLAGEM.png` deste pacote são composições de SVG/
mapas, não capturas de execução do plugin.

Aceitação: escala 100%; setas proporcionais; três ranhuras separadas; encaixe
lateral contínuo; ausência de efeito no hover; relevo na pressão; extremos sem
incremento indevido; arraste e wheel normais; controles restantes sem regressão.
Registrar as capturas e atualizar o estado do bloco no plano mestre.

## Instalação e retorno

```sh
bash kvantum/instalar-classic.sh --verificar
bash kvantum/instalar-classic.sh
```

O instalador aceita a revisão nova, guarda backup e não troca a seleção sem
`--ativar`. Se IrixClassic já está selecionado, basta reabrir os aplicativos.
Não executar `update-irixium.sh` para testar este bloco. Retorno:

```sh
bash kvantum/restaurar-classic.sh --verificar
bash kvantum/restaurar-classic.sh
```

Depois, reabrir os aplicativos. Sem logout obrigatório: nenhum QML de decoração
foi alterado nesta entrega.
