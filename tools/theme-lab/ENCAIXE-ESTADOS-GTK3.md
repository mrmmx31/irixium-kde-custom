# Encaixe de conteúdo GTK3 — I118

A peça atual é o GtkViewport inserido pelo GtkScrolledWindow para conteúdo
sem rolagem própria. Sua moldura não é a moldura externa do GtkScrolledWindow
nem o contents da barra. GtkTextView/GtkTreeView não usam este mesmo viewport.

Fonte algorítmica GTK3.24.49: https://raw.githubusercontent.com/GNOME/gtk/3.24.49/gtk/gtkviewport.c
O viewport possui um nó CSS, gadget próprio e nenhuma implementação de
pressionar/hover/foco de botão. Validar capacidade também na amostra nativa;
não transformar ausência de handler em prova histórica da VM.

Traduzir Normal, Desabilitado e Backdrop com papéis View/KDE. Pressão, Hover e
Foco ficam indisponíveis nesta moldura não interativa. Os filhos podem ser
interativos sem alterar a capacidade da moldura. Normal não cobre os estados
herdados. Retirar um ajuste devolve o encaixe rebaixado nativo nesse estado.
Máscaras mudam apenas luz/sombra; distância da barra, inset e outras peças
mantêm suas receitas. Habilitar editor somente após prova nativa de pintura.
