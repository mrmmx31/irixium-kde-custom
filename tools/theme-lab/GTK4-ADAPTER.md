# Adaptador GTK4 — I168

## Contrato de capacidade

GTK4 fornece `GtkScrollbar` com a árvore CSS `scrollbar → range → trough →
slider`. A API verificada não oferece as quatro propriedades de steppers
presentes em GTK3 (`has-backward-stepper`, `has-forward-stepper`,
`has-secondary-backward-stepper` e `has-secondary-forward-stepper`). A adaptação
preserva o ajuste e a entrada nativos e não inventa setas nem interações para
substituí-las.

Referências de API, não de aparência histórica:
[GtkScrollbar GTK4](https://docs.gtk.org/gtk4/class.Scrollbar.html) e
[GtkRange GTK3](https://docs.gtk.org/gtk3/class.Range.html). A referência visual
continua sendo exclusivamente Domain/OS SR10.4 com HP VUE 2.01 e o contrato
medido em [`domainos_scrollbar_rules.json`](../../tools/domainos_scrollbar_rules.json).

## Tradução aplicada

`gtk4_scrollbars.py` gera a receita do trilho e do thumb a partir dos papéis
KDE atuais. Mantém a geometria medida em 15 px de espessura, borda de relevo de
2 px e face transversal do thumb de 11 px. O comprimento continua sob controle
do `GtkAdjustment`; não é copiado do Trash Can vazio. As máscaras de relevo são
geradas como assets de nove fatias e a orientação não depende de cores finais
fixas.

`gtk4_scrollbar_session.py` monta `GtkScrollbar` reais nas orientações
horizontal e vertical, preserva o ajuste/roda, aplica estado e fornece métricas.
O ciclo de vida mantém referências próprias aos `GtkAdjustment` para desconectar
os sinais com segurança no fechamento. Ao substituir a cena, agenda layout e
redesenho da janela e dos controles. A rota do backend, o worker separado e o
host Motif acoplado selecionam a sessão de barra somente para essa cena; cenas
mistas ainda são recusadas antes de gerar arquivos.

## Evidência técnica de I168

GTK 4.18.6 foi exercitado por ABI C em sessões privadas, sem alterar perfil KDE,
configurações pessoais, Xephyr ou VM. A matriz final tem nove sessões: estados
normal, pressionado, desabilitado e backdrop em DomainOS; paletas Breeze clara,
Breeze escura e amarela sintética no estado normal; e sessões adicionais
separada/acoplada para normal e pressionado. As barras mediram 280×15 e 15×180
em escala 1:1, com pedido mínimo/natural GTK4 de 15×15. Roda do mouse mudou o
`GtkAdjustment` e gravou evento nativo. Recarga de projeto percorreu os quatro
estados nas duas prévias.

Em cada captura, pixels do trilho fora do thumb e pixels do thumb coincidiram
exatamente com os assets produzidos pela receita e pela paleta efetiva (zero
diferenças nas regiões comparadas). A matriz sintética amarela confirma apenas
que os papéis selecionados continuam dinâmicos; não é um esquema instalado.
Os workers encerraram com código 0. Recibo e PNGs:
[`I168-GTK4-SCROLLBAR-MATRIX-20261014.json`](../../docs/review/I168-GTK4-SCROLLBAR-MATRIX-20261014.json)
e arquivos privados indicados por ele no diretório temporário local do ensaio
(armazenado sob `~/tempia`; o caminho da máquina de desenvolvimento não faz
parte do adaptador nem da distribuição).

## Limites

Esta evidência fecha a tradução GTK4 e sua aplicação nas duas origens de
prévia. Ela compara a saída real do GTK4 com a receita gerada, não compara o
GTK4 a pixels de uma seta Motif: GTK4 não tem setas nativas. Isso não é
aprovação visual humana nem afirma fidelidade histórica integral. A avaliação
de todas as famílias e estados nativos permanece na fila visual.
