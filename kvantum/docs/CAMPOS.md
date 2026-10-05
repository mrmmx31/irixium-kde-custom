# Bloco 3 — campos e entradas (0.3.0-rc1)

Manutenção: `mrmmx31`. Esta revisão não é a decoração da janela.

## Implementado

Campos simples e os campos de toolbar usam um contorno rebaixado de três
unidades, conteúdo neutro `#B6B6AA` e contorno externo preto ao receber foco de
teclado. No Kvantum, `LineEdit-focused` representa foco de teclado, não hover.
Botões de opção (combo não editável) têm face elevada e um pequeno marcador
horizontal com relevo; o combo editável mantém área de texto rebaixada.
Spinboxes têm recursos próprios para seus botões e setas, com pressão e
indisponibilidade; os limites, repetição, precisão e edição continuam com o Qt.
Painéis genéricos recebem contorno rebaixado, sem preencher o conteúdo.

São mantidos os tamanhos mínimos e margens de campo/spin da candidata anterior,
sem alterar fonte global, esquema KDE ou a área clicável das barras de rolagem.
O marcador de opção e seus estados são uma adaptação Motif/IRIX, não uma medida
pixel a pixel certificada. A posição dos botões de spin continua a da base.

## Limites explícitos

O manual SGI diferencia campo **somente leitura** (pode selecionar/copiar) de
campo indisponível. O Kvantum 1.1.4 não seleciona um recurso SVG `readonly` para
LineEdit: usa `normal`/`focused` e compõe o indisponível com opacidade. Esta revisão
preserva a semântica nativa, mas **não promete cor própria para readonly em todos
os aplicativos**. Essa diferenciação exige cooperação da aplicação ou mudança
no motor. A galeria não força uma cor artificial para fingir que o tema a suporta.

Os campos podem ter cor especial imposta pelo aplicativo. O campo de caminho
rosado visto no File Finder não implica que todo campo IRIX tenha essa cor;
a variante adota a superfície neutra das referências. Seleção, caret, máscara
de senha, validação e mensagens de erro continuam sob controle do aplicativo.
Um widget desenhado por QML, CSS ou pelo próprio aplicativo pode não usar todos
os recursos de QStyle/Kvantum. Não há alegação de cobertura de todos os apps.

## Validação local

```sh
bash kvantum/testar-campos.sh
bash kvantum/prever-campos.sh
bash kvantum/prever-campos.sh --testar --capturas /caminho/temporario/campos
```

A galeria usa configuração temporária, exige Qt 6 Python e Kvantum, e retorna
77 quando uma dependência não está presente; não instala nada. Testar Tab,
seleção/cópia em readonly, campo desativado, combo aberto e fechado, combo
editável, spin nos limites e em RTL. Conferir com fonte de 14 e 16 pixels.
A fonte de teste afeta somente o processo da galeria.

## Referências

- SGI, Indigo Magic User Interface Guidelines, capítulo 9, Text Fields / Option
  Buttons: https://techpubs.jurassic.nl/library/manuals/2000/007-2167-003/sgi_html/ch09.html
- Kvantum 1.1.4, PE_PanelLineEdit / drawComboLineEdit e CC_ComboBox:
  https://github.com/tsujan/Kvantum/blob/V1.1.4/Kvantum/style/Kvantum.cpp
- Capturas IRIX fornecidas: File Finder, Help Viewer e Confidence Tests; cores
  de superfícies/relevo. Nenhuma fonte tipográfica ou binário SGI é distribuído.
