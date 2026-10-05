# Bloco 5 — menus do Kvantum IrixClassic

Revisão **0.5.0-rc1**. Manutenção: `mrmmx31`.

## Escopo

São novos recursos exclusivos de menu: painel opaco, barra, item armado por
mouse/teclado, item pressionado, setas de submenu, separador e faixa de destaque
para menus destacáveis (tear-off) quando o aplicativo os habilita. O tema não cria ações,
não muda atalhos, não reposiciona Ajuda à direita e não reorganiza o aplicativo.

As seções alteradas são `Menu`, `MenuBar`, `MenuItem`, `MenuBarItem` e dois
parâmetros globais específicos de menu. `menu_separator_height=6` mantém duas
linhas no centro da faixa de separação; `spread_menuitems=false` deixa os itens
dentro do contorno. `submenu_delay=250` e `submenu_overlap=1` são preservados.
Não são valores certificados como temporização exata do IRIX.

A fonte global não muda. Os rótulos de menu usam a indicação de itálico do
estilo, em coerência com ObliqueLabelFont do esquema SGI. O sublinhado estilizado
oblíquo do IRIX não é reproduzido pelo SVG: o Qt desenha os mnemônicos. A política
`alt_mnemonic` anterior permanece intacta para não afetar os outros controles.

## Referências e limites

O perfil em repouso foi medido na barra de menus da captura IRIX Confidence
Tests fornecida: altura da amostra 24 pixels, duas linhas `#ECECEC` no topo,
face `#C1C1C1`, uma linha `#919191` e uma `#606060` na base. O perfil central
foi refeito em `menu_art.surface('menustrip')`. Isso comprova somente o trecho
medido, não a fonte, os cantos, a largura de cada item nem todos os popups.

A documentação SGI recomenda navegação mouse/teclado, mnemônicos, itens
indisponíveis e cancelamento sem destruir a seleção. A integração mantém as
ações nativas do Qt; o tema não implementa novamente essa máquina de eventos.
Os popups e estados que não aparecem nas referências recebidas são adaptações
explícitas da mesma linguagem de relevos, sem alegação de equivalência exata.

Fontes primárias consultadas:

- SGI, Indigo Magic User Interface Guidelines, apêndice A, Menu Traversal and
  Activation / Pull-Down Menus / Popup Menus:
  https://techpubs.jurassic.nl/library/manuals/2000/007-2167-003/sgi_html/apa.html
- SGI, Using Schemes, ObliqueLabelFont:
  https://techpubs.jurassic.nl/library/manuals/2000/007-2006-080/sgi_html/ch03.html
- Kvantum 1.1.4, CE_MenuItem / CE_MenuBarItem / CE_MenuTearoff:
  https://github.com/tsujan/Kvantum/blob/V1.1.4/Kvantum/style/Kvantum.cpp
- Kvantum, configuração:
  https://github.com/tsujan/Kvantum/blob/V1.1.4/Kvantum/doc/Theme-Config

O capítulo 8 completo da cópia web do manual SGI estava indisponível nesta
consulta. Não se atribuem novas medidas/estados a figuras desse capítulo que
não foram inspecionadas; o apêndice e as capturas fornecidas são a base usada.

## Estado visual e estado funcional não são iguais

| Estado do motor | Desenho | Observação |
|---|---|---|
| normal | Sem painel individual | O painel do menu já fornece o fundo. |
| focused | Face clara elevada | Pode representar hover, não necessariamente foco de teclado. |
| toggled | Mesmo item armado | Em CE_MenuItem, State_Selected escolhe toggled; NÃO significa checkbox marcado. |
| pressed | Bisel invertido / face discretamente mais escura | Só aparece quando o componente envia State_Sunken. |
| disabled | Sem destaque de item | Qt/Kvantum controla o texto e a opacidade do indicador. |

Os checkboxes vermelhos e radios azuis continuam usando os recursos do bloco 4.
O estado marcado não depende do fundo do item. Seus 52 mapas estão preservados.
O Kvantum compõe os indicadores indisponíveis com opacidade 0.7; o texto usa
a paleta desativada do Qt, não um SVG de letras.
Atalhos recebem o tratamento de texto próprio do Kvantum, inclusive redução de
opacidade; não se promete preto idêntico a uma captura do IRIX em todo app.

Qt Quick pode fornecer estados, métricas e desenho de texto por outra camada.
A galeria Qt Quick usa o módulo `org.kde.desktop` instalado, sem sobrescrevê-lo.
O reparo opcional de pressão da scrollbar continua independente destes menus.

## Preservação da herança

Toolbar, TabBarFrame, DockTitle, TitleBar, Tooltip, Slider, Progressbar, Splitter
e as outras seções fora do bloco têm as configurações efetivas antigas. Quando
necessário, a herança de recurso do Menu/MenuBar recebeu override explícito.
Nenhum recurso SVG preexistente foi removido, alterado ou reposicionado.
Os recursos de menu são acrescentados ao atlas; apenas as rotas de menu apontam
para eles. Não alterar os valores antigos dos JSONs de baseline para encobrir
regressões: os testes cumulativos checam separadamente cada bloco.

## Testar (raiz do clone)

```sh
bash kvantum/testar-menus.sh
bash kvantum/prever-menus.sh
bash kvantum/prever-menus.sh --testar --capturas /pasta/nova/menus
bash kvantum/prever-menus.sh --tema Irixium
bash kvantum/prever-menus.sh --qtquick
```

O modo automático é Qt Widgets. A galeria Qt Quick desta revisão é manual;
`--qtquick --testar` é recusado para não anunciar uma cobertura inexistente.
As duas galerias usam configuração temporária e não executam comandos de arquivo,
clipboard ou rede. Dependências ausentes retornam 77, não sucesso.

Conferir: clique simples, menu aberto, item indisponível, setas de navegação,
Enter, Escape, checkbox, radios exclusivos, submenu, RTL, textos longos, menu
rolável e menu destacável. A política de clique-fora é do Qt/app; não há filtro
global para tentar impor o comportamento histórico. Conferir em 100% de escala.

## Instalar / voltar

```sh
bash kvantum/instalar-classic.sh --verificar
bash kvantum/instalar-classic.sh
# retorno independente do reparo opcional Qt Quick:
bash kvantum/restaurar-classic.sh
```

Sem sudo. Reabrir aplicativos. O instalador não seleciona outro estilo e não
modifica fontes, GTK ou decorações de janela. O nome continua IrixClassic.
