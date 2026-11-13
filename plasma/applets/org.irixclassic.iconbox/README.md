# IRIX Classic Iconbox

Barra de janelas compacta para Plasma 6: uma fileira de ícones com o nome do
aplicativo abaixo, molduras em relevo e fundo próprio recuado. Em um painel
vertical, a mesma organização usa uma coluna. O identificador é
`org.irixclassic.iconbox`; o gerenciador de tarefas padrão do KDE permanece
disponível separadamente.

O desenho usa o Plasma Style selecionado: `widgets/background` para a caixa
e `widgets/tasks` para as células. As larguras estreita, média e larga são
64, 74 e 84 pixels lógicos. Uma célula tem altura prevista de 48–56 pixels;
o contorno externo acrescenta três pixels por lado. Ícones são apresentados
em 16, 24 ou 32 pixels conforme o espaço, e a legenda ocupa uma linha.
Janelas continuam identificadas pelo título completo nas dicas e nos grupos.

Ao pressionar, a moldura consulta imediatamente o SVG do estado pressionado;
ícone e legenda recuam um pixel. A ação nativa continua no soltar do botão,
sem espera ou temporizador acrescentado ao clique. O Style Classic oferece
os estados `normal-pressed`, `focus-pressed`, `minimized-pressed` e
`attention-pressed`. Em outros estilos, a busca recua ao prefixo `pressed`
ou à aparência do estado correspondente.

## Funções preservadas

A base é o gerenciador de tarefas completo do KDE Plasma Desktop 6.3.6,
do pacote Debian `plasma-desktop` versão `4:6.3.6-1`. Foram preservados os
modelos nativos de janelas, as ações de ativar/minimizar/abrir/fechar, os menus
de contexto, agrupamento, lançamento fixado, arrastar e soltar, ordenação,
filtros por tela/atividade/desktop, prévias, indicadores de áudio/progresso,
atalhos, navegação por teclado e acessibilidade. A legenda resumida altera
a apresentação da barra; o popup de grupos conserva as linhas de título.

Não há lançadores fixados inicialmente: os quatro atalhos do painel Classic
ficam em seu grupo próprio. É possível fixar aplicativos pelo menu de contexto.
A configuração de aparência mantém as três larguras, prévias, indicadores de
áudio e preenchimento; a barra usa sempre uma única fileira.

Este é um plasmoid QML com `PlasmoidItem`, não uma biblioteca C++ nova. Ele
usa os módulos de execução do Plasma, inclusive
`org.kde.plasma.private.taskmanager.Backend`; não altera esses módulos.
Os temporizadores de geometria, arraste e prévias já existentes no código do
KDE foram preservados. Nenhum timer, loop ou pedido explícito de repaint foi
acrescentado à resposta visual do clique.

## Fonte e licença

Todos os arquivos de `contents/` e a configuração da base foram incluídos;
os avisos SPDX e os créditos originais permanecem nos arquivos. A adaptação
tem licença GPL-2.0-or-later. O wrapper de texto herdado conserva seu aviso
LGPL-2.0-or-later. `LICENSE` contém a GPL versão 2.

`ORIGEM.json` registra a versão, o endereço da
[fonte KDE](https://invent.kde.org/plasma/plasma-desktop/-/tree/v6.3.6/applets/taskmanager)
e os hashes SHA-256 de cada arquivo instalado que serviu de base. A identidade
visual é uma adaptação do projeto, inspirada em ferramentas de estações de
trabalho; não declara ser um componente original da SGI.
