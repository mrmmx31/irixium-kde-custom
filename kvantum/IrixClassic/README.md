# IrixClassic — Kvantum

**0.1.0-rc2. Maintainer: `mrmmx31`.** Estilo de **Qt Widgets**, separado da
decoração IRIX Classic e do Irixium moderno. Primeira candidata para ensaio local;
não é uma reprodução certificada de todos os controles do IRIX.

## Bloco 1 revisado nesta entrega

Setas verticais 8×9 na célula 18×18; três ranhuras claro/preto com passo 4;
trilho e puxador exclusivos; faixas laterais atravessadas pelo indicador de
largura total. Pressão sem deslocar o símbolo; hover igual ao repouso. Os demais
recursos gráficos e suas configurações efetivas foram preservados.

Roteiro completo: `../PLANO-IRIXCLASSIC.md`. Detalhes, limites históricos e teste
local: `../docs/ROLAGEM.md`. O bloco está implementado para ensaio, **não aprovado
em Qt/KDE nesta entrega**. A função nativa do Qt continua responsável pelo gesto.

```sh
bash kvantum/testar-rolagem.sh
bash kvantum/prever-rolagem.sh
```

Os comandos acima partem da raiz do checkout. `PREVIA-ROLAGEM.png` compara os
mapas da referência, da rc1 e da rc2; `ESTADOS-ROLAGEM.png` mostra as composições
verticais/horizontais. Não são capturas de execução do plugin.

## Desenho desta revisão

O `.kvconfig` parte da organização da base Irixium de Mark Whittaker/Phob1an;
o SVG é uma construção nova, com retângulos inteiros, sem gradientes, sombras
externas, transparência de janelas ou animações de transição. O moderno em
`../Irixium/` permanece intacto.

As referências de IRIX mostram fundo de barras `#C1C1C1`, botões de comando
`#999999`, campos/painéis neutros `#B6B6AA` e visualização clara `#EFEFEF`.
O relevo dos botões utiliza as faixas `#4C4C4C`, `#E1E1E1`, `#CCCCCC`,
`#737373` e `#252525` observadas nos recortes. A paleta do interior não é
limitada às quatro cores da moldura externa.

| Controle | Proposta |
|---|---|
| Botões de comando | Relevo de 3 px; margens verticais de texto de 2 px; altura mínima nominal 22. |
| Ferramentas | Moldura de 2 px; margens verticais de 1 px; ícones 16. |
| Menus | Relevo compacto e indicação de item selecionado; não eliminamos a navegação visual. |
| Abas | Retangulares; sem sobreposição de 12 px nem expansão de moldura de 20 px da base. |
| Campos | Moldura rebaixada de 3 px; conteúdo e caret continuam sob controle do Qt. |
| Barras de rolagem | 18 px, setas persistentes e puxador com ranhuras; sem desaparecimento automático. |
| Divisores | 7 px; ranhuras de arraste. |
| Check/radio | 15 px; marcação, parcial e indisponível distintos; rádio em losango. |
| Foco/default | Contorno pontilhado de teclado e indicação de botão padrão preservados. |

**Medidas são limites/margens lógicas, não alturas finais garantidas.** O Qt soma
métricas de fonte, ícones e espaço exigido pelo aplicativo. A fonte global de
12 pontos pode manter controles maiores que capturas antigas. Não a alteramos.

**Comprovado nas imagens:** cores amostradas e princípio visual dos relevos de
menus, botões e áreas roláveis. **Adaptações:** abas, check/radio, cores de seleção,
estados não mostrados e seus encaixes no Qt. Não afirmar identidade pixel a pixel
para estes elementos nem confundir essa variante com código original da SGI.

## Efeitos

Botões comuns não ganham brilho de hover; a pressão inverte o relevo sem mover
seu conteúdo. Toggled é persistente e não se confunde com hover. Itens de menu
continuam tendo realce para navegação, e o teclado conserva uma indicação de foco.
O Qt/Kvantum continua responsável por entrada, indisponibilidade e ativação.
Isso não transfere a política da barra de título a todos os widgets.

## Teste sem instalar nem alterar a seleção atual

Na raiz do checkout:

```sh
bash kvantum/prever-classic.sh
bash kvantum/prever-classic.sh --tema Irixium
bash kvantum/prever-classic.sh --fonte-px 16
```

A galeria usa uma configuração Kvantum temporária, somente no processo de teste.
Exige **PyQt6 ou PySide6** e o plugin **Kvantum Qt 6**. Se faltar um deles, retorna
77; não instala dependências e não mostra Fusion fingindo ser Kvantum. A fonte de
14 pixels é local à galeria. O aplicativo não contém fontes embutidas.

Para gerar uma captura **real** onde houver essas dependências:

```sh
bash kvantum/prever-classic.sh --captura /tmp/irixclassic-qt.png
```

Os tamanhos efetivos e o plugin carregado são impressos. Captura offscreen ainda
não testa Wayland/KWin, menus externos ou o comportamento de todos os aplicativos.

## Instalação independente e reversível

```sh
bash kvantum/instalar-classic.sh --verificar
bash kvantum/instalar-classic.sh
```

Use o usuário normal, **sem sudo**. Instala em
`${XDG_CONFIG_HOME:-$HOME/.config}/Kvantum/IrixClassic/`, mas **não seleciona** o
tema. Selecione IrixClassic no Kvantum Manager. O Application Style deve continuar
em **kvantum**. Ou selecione explicitamente no mesmo comando:

```sh
bash kvantum/instalar-classic.sh --ativar
```

Essa opção altera somente `[General] theme` em `Kvantum/kvantum.kvconfig`; mantém
exceções em `[Applications]`. Elas podem fazer um aplicativo continuar usando
outro tema. Reabra os aplicativos para testar. Não é necessário reiniciar o KWin.

Não altera `kwinrc`, fontes globais, esquema de cores do Plasma, Irixium moderno,
GTK, conteúdo do terminal nem a decoração de janela. Não instala o plugin Kvantum.
Qt Quick e controles desenhados pelo próprio aplicativo não são integralmente
controlados por este tema. Dials, ícones internos de janelas MDI e outros controles
menos comuns ainda não foram comparados; podem usar fallbacks do Qt/Kvantum.

Restauração da última instalação:

```sh
bash kvantum/restaurar-classic.sh --verificar
bash kvantum/restaurar-classic.sh
```

Em caso de interrupção, use `--recuperar`. Recibos e cópias privadas:
`${XDG_STATE_HOME:-$HOME/.local/state}/irixclassic-kvantum/backups/`.
Alterações posteriores desconhecidas são recusadas, não sobrescritas. Pastas vazias
criadas na instalação podem permanecer após a restauração.

## Fontes técnicas e desenvolvimento

- Kvantum 1.1.4, `Kvantum/doc/Theme-Config` e `Kvantum/style/rendering.cpp`:
  https://github.com/tsujan/Kvantum/tree/V1.1.4/Kvantum
- Estados e dimensionamento do Qt:
  https://doc.qt.io/qt-6.8/qstyle.html
- Base de configuração: `../Irixium/`; proveniência em `ORIGEM.json`.

`python3 kvantum/tools/build_classic.py` regenera o SVG deterministicamente.
Após editar o tema, execute `python3 kvantum/tools/update_manifest.py`.
O manifesto detecta alteração de bytes, não é assinatura de origem.
`PREVIA.png` conserva o catálogo inicial da rc1 para referência. Para a rolagem
na rc2, use `PREVIA-ROLAGEM.png` e `ESTADOS-ROLAGEM.png`; são composições
técnicas, **não execução do Kvantum**.
