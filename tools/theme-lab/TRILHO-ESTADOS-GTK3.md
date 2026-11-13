# Estados da moldura contínua GTK3 — I118

Esta peça do laboratório é o encaixe externo contínuo que envolve setas e
trilho. A máscara fica no nó `scrollbar contents`; não é a superfície interna
`trough`. Sua geometria segue o contrato DomainOS e a receita da peça. Receitas
de relevo são propostas de ajuste, sem constituir novos defaults históricos.

Antes de desenhar: no GTK 3.24.49, `update_trough_state` copia as flags do range,
remove PRELIGHT/ACTIVE e aplica esse estado ao `contents`. Somente depois aplica
hover/pressão ao `trough` interno. [Fonte primária GTK](https://raw.githubusercontent.com/GNOME/gtk/3.24.49/gtk/gtkrange.c).

| Estado da receita | Tradução da moldura externa |
| --- | --- |
| Normal | Máscara própria com contexto Button ativo, inclusive durante interação interna. |
| Desabilitado | Máscara própria com contexto Button desabilitado; combina com backdrop. |
| Sem foco / backdrop | Máscara própria para barra sensível em contexto Button inativo. |
| Pressionado, Hover | Indisponíveis para essa moldura: o GTK remove essas flags do nó. Não ampliar para todos os elementos internos como aproximação. |
| Foco | Indisponível na barra padrão, que não aceita foco; não forçar essa capacidade. |

Cada máscara conserva espessura, corte e posição. Elevado/rebaixado usam os
mesmos tokens semânticos com luz/sombra trocadas; plano usa face no relevo. A
superfície vazia continua recebendo o papel de trilho, não a face do botão.
Os estados desabilitados prevalecem sobre o backdrop sensível. Retirar um
estado volta ao encaixe nativo rebaixado somente naquele contexto.

Todas as cores vêm dos papéis atuais KDE e das regras de mistura existentes.
As máscaras originais, viewport, cursor e setas ficam preservados. Nenhuma
entrada de RGB da pipeta vira cor final de um controle.

Aparência histórica de hover/desabilitado da VM continua sem prova. O contraste,
os estados de entrada e a pintura GTK3 devem ser testados nativamente em quatro
paletas; parser CSS não comprova pixels. O resultado e as limitações ficam na
fila visual e no recibo I118. A documentação não constitui aprovação humana.
