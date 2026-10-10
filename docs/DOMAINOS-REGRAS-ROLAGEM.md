# Regras comuns de rolagem — DomainOS SR10.4

Esta especificação vem antes da adaptação de cada toolkit. O contrato único está
em [domainos_scrollbar_rules.json](../tools/domainos_scrollbar_rules.json).
GTK3 é o primeiro consumidor; GTK2, GTK4, GTK1, Qt/Kvantum, Qt Quick e Plasma
seguem a [fila de revisão](DOMAINOS-FILA-REVISAO-VISUAL.md). A existência do
contrato não declara essas implementações concluídas.

## Origem das regras

A referência é o Trash Can da VM **Domain/OS SR10.4, HP VUE 2.01**. As medidas
abaixo são dos controles efetivamente desenhados, em pixels nativos. Não são
apresentadas como defaults universais de Motif nem valores encontrados em um
arquivo quando não o foram.

Em 2026-10-10, o FTP ativo à raiz do convidado permitiu reler os recursos
`Vue`, `Vuewm`, `Vuefile`, `Vuestyle`, `Vuehelp`, `XTerm`, `Mwm`, `sys.Xdefaults`
e as paletas CoralReef e da sessão. Foram lidos 10 arquivos e listados 12
diretórios, sem escrita no convidado. Outra leitura limitada examinou 30
diretórios de fontes e exemplos. A pasta `/sys/source` contém exemplos Pascal
e Fortran; os diretórios examinados não forneceram os fontes C de XmScrollBar
e XmScrolledWindow. Isso descreve a busca feita, não prova ausência em todo
o sistema ou em mídias de desenvolvimento.
Os [arquivos verificados](referencias/domainos-sr104/CONFIGURACOES-VERIFICADAS.json)
ficam identificados por caminho no convidado e SHA-256. Esses caminhos são
fontes de evidência; o instalador não depende da VM nem de diretórios pessoais.

| Evidência | Resultado e consequência |
| --- | --- |
| `/usr/X11/lib/app-defaults/Vuefile` | Linha 1: conjunto secundário 5. Os demais recursos são de XmpIcon. Não há medida de barra de rolagem neste arquivo. SHA-256 `052b89bee515c80096011eeb1744173dc42979fddabcbeccec71cc9adf4e66e0`. |
| Recursos `Vuewm` | Conjuntos de cores do painel e recursos `wsButtonBorder`/`wsButtonSpacing`. Esses nomes referem-se aos botões de áreas de trabalho, não à distância entre barra de rolagem e conteúdo. |
| `sys.Xdefaults` | Muitas linhas são exemplos comentados. Os recursos `mwm_bw` descrevem uma configuração específica; não definem o Trash Can CoralReef atual. |
| `xrdb -query` da sessão VUE | Fontes Swiss 742/Prestige, fundo `#7848A075D500`, texto branco e `xterm*scrollBar: True`. Não declara as medidas XmScrollBar desta captura. |
| `/lib/xmlib1.1` | Biblioteca instalada com nomes de recursos e caminhos `sr10.4_beta3/lib/Xm/{ScrollBar,ScrolledW,ArrowBI}.c`. Caminhos de debug não são o conteúdo C. A revisão exata ainda não foi confirmada. |
| Trash Can real | Fornece dimensões e cores do estado normal; o ensaio separado de pressionar/soltar confirma a seta inferior. |

As configurações X podem sobrescrever recursos; a biblioteca e o código da
aplicação também estabelecem padrões. Por isso, um recurso ausente do arquivo
não será preenchido por suposição. Fontes de outro Motif podem explicar uma
operação, mas não substituem os dados do SR10.4.

Na busca externa, os dois acervos de fontes OSF/1 examinados identificam sua
biblioteca como **Motif 1.2.2** no próprio `Xm.h`; foram descartados como prova
dos defaults desta VM: [acervo calmsacibis995, revisão fixada](https://github.com/calmsacibis995/osf1-10-src/blob/52dcefc059eda40b725df2ede0b0178a2534f648/usr/opt/OSCX200/src/motif/lib/Xm/Xm.h#L31)
e [acervo Arquivotheca, revisão fixada](https://github.com/Arquivotheca/OSF1/blob/7d4874fa6985af6ff9400b42d358a19084f1f7aa/src/motif/lib/Xm/Xm.h#L76).

## Geometria comum

| Parte | Regra em pixels nativos | Origem |
| --- | --- | --- |
| Barra completa | 15 de espessura | Medida na VM, horizontal e vertical. |
| Relevo externo do trilho | 2 em cada borda, encaixe rebaixado contínuo | Medida na VM. |
| Campo da seta | 11 × 11; triângulo inteiro com ponta central de um pixel | Medida na VM, quatro direções. |
| Thumb transversal | 11; relevo elevado distinto do trilho | Medida na VM. |
| Distância seta–thumb | 1 | Medida na VM. |
| Distância moldura do conteúdo–barra | 4 | Medida na VM, duas orientações. |
| Moldura do conteúdo | 2, rebaixada | Medida na VM. |
| Canto entre as barras | Face de fundo; reservar a área das duas setas | Observação da VM. |

A relação de largura é `15 = 11 + 2 × 2`. A distância de quatro pixels fica
fora desse conjunto: não engrossar a barra para imitar o afastamento.
O [registro de métricas](referencias/domainos-sr104/TRASH-CAN-METRICAS.json)
contém coordenadas e hashes da [referência normal](referencias/domainos-sr104/trash-can-normal.png).

O comprimento do thumb depende da quantidade de conteúdo e do intervalo de
rolagem. O Trash Can vazio tem um thumb quase integral; copiar esse comprimento
para todas as aplicações seria uma regra incorreta. O mínimo C original ainda
não foi estabelecido.

## Iluminação e interação

Luz e sombra permanecem orientadas pelo canto superior esquerdo. Primeiro se
orienta a silhueta, depois se desenha o relevo; girar um bitmap já sombreado
mudaria a direção da iluminação. O trilho e o thumb têm relevos próprios.
Não acrescentar um botão retangular elevado ao redor de cada triângulo.

Na VM, a seta inferior troca luz e sombra **somente enquanto pressionada**.
No ensaio, 53 pixels trocaram entre `#c4d5ed` e `#3e536e`; a soltura restaurou
o triângulo sem diferença de pixels. O corpo não deslocou porque o Trash Can
estava vazio. Essa prova não demonstra arraste de thumb, limite de conteúdo,
estado desabilitado ou todas as outras direções pressionadas. Esses estados
continuam registrados como pendentes.
O [registro do ciclo](referencias/domainos-sr104/SETA-INFERIOR-ESTADOS.json)
preserva os hashes, as linhas de pixels e a distinção entre triângulo e cursor.

## Cores e escala na adaptação

A [regra de cores para todas as famílias](DOMAINOS-REGRAS-CORES.md) é obrigatória;
esta seção traduz a mesma política para barras de rolagem.

Os RGB originais ficam no contrato como amostras de comparação. O desenho
do produto usa os papéis atuais do KDE: face, texto, luz, sombra e trilho.
Não inserir cores azuis constantes para corrigir um arredondamento. As únicas
exceções autorizadas no projeto continuam sendo o LED e a seleção do Pager,
com proteção de contraste; esta etapa não altera o Pager.

No limite da rolagem, uma seta GTK3 pode ficar desabilitada enquanto a barra
permanece sensível. O contrato agora distingue esse caso: a seta usa os papéis
do scrollbar pai, incluindo seu estado sem foco, e conserva o bloqueio de input.
Não troca sozinha a face, a luz, a sombra e o fundo para outra paleta.
É uma política de adaptação baseada nas quatro setas normais do Trash Can vazio
e no ciclo nativo de pressionar/soltar. Não afirma que a biblioteca SR10.4
desabilita a seta da mesma maneira que GTK3.

Um controle inteiro insensível é outro caso. Seus papéis KDE desabilitados
permanecem separados; a aparência histórica de `XtSensitive=False` ainda não foi
comprovada. A tradução desta nova regra está limitada à família GTK3 ativa.

Comparar primeiro em escala nativa, sem interpolação. Em outra escala, todas
as medidas pertencentes ao mesmo controle seguem o mesmo fator e uma política
de arredondamento documentada. Registrar o fator efetivo do toolkit antes de
atribuir ao original um borrão produzido pela renderização atual.

## Tradução e verificação

| Implementação | Tradução prevista e limite a verificar |
| --- | --- |
| GTK3 | CSS de GtkScrolledWindow, masks inteiras do trilho/thumb e glyphs de direção. O espaçamento usa `scrollbar-spacing`. GtkViewport aceita a moldura; GtkTreeView preenchida não desenha uma moldura principal equivalente por esse CSS. |
| GTK2 | Pixmap engine e recursos GTK2 próprios; consumir as mesmas medidas sem concluir por analogia com GTK3. |
| GTK4 | CSS e papéis de cores próprios; a API não fornece os mesmos botões de seta nativos. Documentar a diferença antes de propor outra implementação. |
| GTK1 | Confirmar aplicação e engine reais. A variante legada Irixium não prova cobertura DomainOS. |
| Qt Widgets/Kvantum | Gerador SVG, métricas Kvantum e variantes de paleta. Validar barras dos widgets reais e as duas setas finais. |
| Qt Quick/System Settings | Identificar o estilo e o controle carregados. Corrigir nessa implementação, sem presumir que a seta pertence ao Kvantum. |
| Plasma Style | SVG e geometria efetiva do controle Plasma, com comparação própria. |

Para cada família: ler a regra, identificar o mecanismo de desenho, implementar
a tradução, comparar a captura nativa e registrar diferenças. Testar normal,
pressionado, solto, desabilitado, cantos e paletas. Falta de suporte deve aparecer
como limitação ou tarefa em aberto; não ser escondida com um efeito que prejudique
outras partes do widget. Em particular, a tentativa de sombra global em TreeView
pintou as células e foi descartada.

A etapa GTK3 permanece parcial pela moldura principal da tabela preenchida.
Os testes de geometria, glyphs e estados GTK passaram; não comprovam que todas
as famílias ou todos os estados históricos estão equivalentes.

A tradução GTK3 da política de cores no limite da rolagem passou o ensaio focado
em quatro paletas, incluindo falta de foco e contêiner insensível. O bloqueio
de clique permaneceu efetivo. O [resultado](review/arrow-boundary-color-result.json)
registra pixels, fontes e limites; o estado histórico realmente insensível
permanece sem comparação nativa comprovada.
