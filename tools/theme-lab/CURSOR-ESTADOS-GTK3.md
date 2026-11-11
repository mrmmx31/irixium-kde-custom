# Cursor móvel GTK3 — estados de relevo I118

Referência algorítmica: GTK3.24.49, `update_slider_state` em
[gtkrange.c](https://raw.githubusercontent.com/GNOME/gtk/3.24.49/gtk/gtkrange.c).
O nó slider recebe hover quando o ponteiro está no seu gadget e pressão quando
está capturado. Sensibilidade/backdrop vêm do range. A barra padrão não aceita
foco. Isso explica capacidades GTK3; não prova estados históricos da VM.

A receita thumb oferece Normal, Pressionado, Desabilitado, Sem foco/backdrop e
Hover. Foco permanece indisponível nessa amostra. Pressão prevalece sobre hover;
desabilitado prevalece sobre interação. Backdrop escolhe a paleta inativa junto
com estados de interação. O override Normal não cobre os outros estados.

Cada ajuste troca só a máscara semântica do relevo da peça. Plano usa face nas
bordas; elevado/rebaixado orientam luz e sombra pelo canto superior esquerdo.
As cores são papéis Button/KDE e as misturas atuais da receita. Tamanho mínimo,
comprimento proporcional ao conteúdo, posição, margem, setas, trilho e área de
conteúdo continuam com suas regras existentes. Retirar um estado devolve apenas
nesse contexto a máscara elevada nativa.

Antes de habilitar edição: conferir parser, máscaras e pintura/entrada nativas
nas duas orientações, quatro paletas, pressão e restauração, sensibilidade e
backdrop. Editor integrado e entrega pessoal têm provas separadas. Não converter
este contrato em aprovação humana ou equivalência histórica.
