# GTK Classic, gr_osview, pager e decorações Moderno

A suíte passou a instalar 26 componentes gráficos, mais as cópias de
compatibilidade em `~/.icons` e `~/.themes`, sempre no perfil de quem executa.
A auditoria local de lsi passou, sem diferenças de arquivos ou seleção.

## GTK

`IrixClassic` cobre GTK 2, 3 e 4 com arte derivada dos mapas Classic locais.
Os 35 arquivos do GTK Irixium anterior foram preservados, apenas reorganizados
em `gtk/Irixium`. Fontes e tamanhos vêm das preferências do usuário.

As galerias nativas passaram em GTK 2.24.33, 3.24.49 e 4.18.6, com Nimbus Sans
10,5 e 12 pt. CSS GTK3/4 sem diagnósticos; pressão, campos, menus, seleção,
checkboxes, radios, barras e estados desabilitados foram renderizados.
Com 12 pt, a pressão mudou 413, 304 e 374 pixels, respectivamente.

A descoberta por nome também foi testada: GTK2 com apenas o caminho XDG
informava o nome configurado, mas não carregava pixmap nem as cores Classic.
Com a cópia completa em `~/.themes`, carregou o engine, os controles e a fonte
de 12 pt; o menu herdou família/tamanho e acrescentou itálico.
Isso corresponde à busca implementada no
[GTK 2.24.33](https://github.com/GNOME/gtk/blob/2.24.33/gtk/gtkrc.c).

Em lsi, o módulo GTK do KDE confirmou `IrixClassic`. Uma aplicação GTK3 nova,
sem `GTK_THEME` forçado ou CssProvider adicional, usou Nimbus Sans 12 e desenhou
os controles Classic. A seleção tem backup próprio e conserva fontes, cursores
e ícones. O IRIX Files instalado pelo `.deb` continua padrão para diretórios.

GTK2 exige o engine pixmap da distribuição. GTK4 não oferece os steppers
antigos; aplicativos libadwaita ou com CSS próprio podem escolher seu estilo.

## Pager e gr_osview

O relatório público executado em p001532 foi conferido com UID nativo 1003.
O pager já era o widget 348 do painel 342. Havia uma área de trabalho; foi
adicionada a segunda, preservando a primeira e todos os widgets/IDs do painel.
O pager nativo só é visível com mais de uma área, conforme o
[PagerModel do KDE 6.3.6](https://github.com/KDE/plasma-desktop/blob/v6.3.6/applets/pager/pagermodel.cpp).

O gr_osview apresenta sete sensores nativos: CPU, memória, swap, leitura e
escrita de disco, recepção e envio de rede. Três amostras no host privado
confirmaram todos os sensores Ready, valores reais e atividade de disco/rede.
Percentuais usam escala 0–100; taxas usam o pico observado de cada barra.
Não há Timer de animação ou repaint de decoração no widget.

Em lsi, o monitor foi adicionado como widget 1883 do desktop 1821, no canto
superior direito. O Plasma alinhou a geometria inicial à grade: x=1632, y=16,
288×224 em uma tela de 1920 pixels de largura. A segunda execução não criou
outro widget, preservou exatamente essa posição e conservou os IDs do painel.
A fixture privada confirmou criação e idempotência; um gesto de arraste nela,
sem gestor de janelas, não forneceu prova de movimento manual. A edição usa
os controles nativos do Plasma, e o helper não reposiciona instâncias existentes.

## Decorações e verificações

As três opções Moderno são instaladas: `irixium_modern`, `irixium_modern_13`
e `irixium_modern_41`. As duas importadas preservam arte, metadados e licenças;
o layout cria menu, minimizar e maximizar/restaurar. Não cria botão fechar.
O Moderno existente permanece como padrão desse perfil.

Passaram 55 verificações de renderização/input das variantes e oito da prévia
nativa KDecoration3 carregando os três `main.qml`, sem avisos QML.
A suíte de integração passou com 764 testes Python e os checks JavaScript da
decoração. Após acrescentar a descoberta GTK2, passaram mais 38 verificações
direcionadas de seleção, restauração e inventário; a auditoria da instalação
final também passou. As transações testam falhas de D-Bus e registro final:
recuperam arquivos independentemente do barramento e removem somente widgets
criados naquela operação. Áreas de trabalho nunca são removidas automaticamente.

As capturas e relatórios estão em
`/home/lsi/Downloads/irix-gtk-grosview-decoracoes-20261008/`.
As imagens mostram galerias/controlos próprios e o host do widget; nenhuma
captura completa de desktop foi necessária. Os diagnósticos temporários e
arquivos de preferências dos usuários não fazem parte do repositório.
