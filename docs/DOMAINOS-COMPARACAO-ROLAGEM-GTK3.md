# Comparação das barras GTK3 com o Trash Can SR10.4

Etapa de 2026-10-10, ainda **parcial**. A
[regra comum](DOMAINOS-REGRAS-ROLAGEM.md) distingue recursos do convidado,
medidas e adaptações. A [fila](DOMAINOS-FILA-REVISAO-VISUAL.md) continua
com GTK3 ativo; não encerra Qt/System Settings, GTK2, GTK4 ou Plasma.

| Parte | Antes da revisão | Resultado atual |
| --- | --- | --- |
| Espessura | 16 pixels | 15, incluindo duas bordas de 2. |
| Setas e thumb transversal | 12 pixels | 11, com intervalo seta–thumb de 1. |
| Distância do conteúdo | Zero | 4, nas duas orientações. |
| Seta inferior | Rotação também mudava a iluminação | Silhueta orientada antes do relevo; quatro direções normais coincidem com os recortes nativos. |
| Trilho e thumb | Continuidade diferente junto às setas | Masks inteiras preservam seus relevos separados, sem junções suavizadas pelo miter CSS. |
| Pressionar/soltar seta inferior | Referência histórica não registrada | Ciclo real na VM: 53 pixels trocam luz/sombra; soltura restaura o triângulo. Desenho GTK3 coincide dentro da silhueta. |
| Moldura de GtkViewport | Encaixe diferente | Moldura rebaixada de 2 pixels disponível. |
| Moldura principal de GtkTreeView preenchida | Diferente do Trash Can | **Pendente.** O widget não pinta esse frame principal pelo CSS utilizado. A sombra global afetava também as células e foi descartada. |

O gerador GTK3 consome `tools/domainos_scrollbar_rules.json`; não mantém uma
segunda lista de medidas. O refactor preservou 759 arquivos de desenho/CSS.
A proveniência de cada um dos três temas GTK registra o caminho relativo e
o hash do contrato.

Os ensaios GTK3 nativos passaram 620/620, os de desenho/integridade 18/18 e
os quatro testes focados do refactor passaram. Foram preservados 376 arquivos
protegidos de GTK2, GTK4 e Kvantum. Esses números verificam o escopo ensaiado;
não medem porcentagem de fidelidade nem confirmam estados históricos ainda
sem captura, como desabilitado, outras direções pressionadas e arraste de thumb.

Os recortes normais coincidem nos quatro triângulos. O ensaio pressionado
mantém nove pixels de cursor fora da silhueta no contexto da imagem. Nenhum
pixel foi removido do bruto para afirmar uma igualdade da região inteira.

O [diagnóstico posterior de cores](DOMAINOS-CORES-SETAS-REVISAO.md) encontrou
uma diferença no estado desabilitado da captura R13: cima/esquerda usam a paleta
insensível do KDE; baixo/direita usam a normal e coincidem com a VM. A prova
anterior dos triângulos normais não abrangia a regra histórica de cores desse
estado. Não generalizar sua igualdade a todos os estados ou toolkits.

Próxima pendência GTK3: confirmar a regra de cores desabilitadas e resolver ou
delimitar a moldura principal da tabela,
comparando uma solução que preserve também as células, a seleção e a rolagem.
Depois verificar os estados históricos restantes antes de encerrar a família.
