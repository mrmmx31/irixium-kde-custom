# IrixClassic GTK

Tema de controles GTK inspirado na reconstrução Classic deste repositório.
É uma tradução para widgets nativos GTK, não uma certificação histórica do IRIX.
Manutenção: mrmmx31. GPL-3.0-or-later; veja [LICENSE](LICENSE).

O fundo `#c1c1c1`, os botões `#999999`, a seleção `#9ebfbf` e os relevos de três
bandas seguem `kvantum/IrixClassic`. Os PNGs são mapas inteiros gerados das mesmas
fontes Classic. Família e tamanho do texto são herdados de `gtk-font-name` do
perfil individual; o tema não substitui esse valor. Fontes não são distribuídas.
Títulos de menus usam a itálica da referência local sem fixar família ou tamanho.

Botões, menus, campos, combos/dropdowns, spinboxes, abas, cabeçalhos, listas,
sidebar, progresso, sliders, barras de rolagem, divisores e tooltips recebem o
acabamento Classic. Checkboxes usam marca vermelha; radios usam losango e marca
triangular azul. Switches GTK3/4 têm trilho e cursor quadrados. Controles
desativados mantêm sua geometria com texto e marcas cinza. A pressão inverte as
bandas internas sem deslocar rótulos nem o contorno externo; não há transições,
gradientes ou animações no CSS. GTK continua responsável pelas ações, seleção,
teclado, grabs e temporização funcional de menus.

Copie esta pasta inteira, incluindo `common/`, para o diretório de temas XDG
usado pela suíte e selecione `IrixClassic`. A cópia dos arquivos não ativa o tema.
O instalador e o helper de seleção da suíte tratam integração e restauração.

| Runtime validado | Resultado e limite |
|---|---|
| GTK2 2.24.33 | Galeria nativa e pressão verificadas com engine **pixmap** externo |
| GTK3 3.24.49 | CSS sem diagnósticos, galeria/menu nativos, nome IrixClassic e Nimbus Sans confirmados |
| GTK4 4.18.6 | Mesmos ensaios em host C ABI via ctypes; não havia typelib GTK4 instalado |

GTK2 precisa do módulo `libpixmap.so` fornecido pelo ambiente GTK2. O tema não
embute nem instala esse motor; sua ausência impede os mapas de controles. GTK2
não possui `GtkSwitch`. GTK3 mostra steppers quando o toolkit permite; GTK4 não
oferece essa API, portanto conserva o trilho largo com grip e pressão do cursor.
Aplicativos libadwaita podem usar seu próprio stylesheet e não seguir um tema
GTK externo. Não se aplica override global de libadwaita. Widgets desenhados
pelo aplicativo e escalas fracionárias não têm promessa de identidade pixel a
pixel. Campos somente leitura podem conservar o fundo dos campos editáveis.

As provas de 08/10/2026 foram feitas em Xvfb privado, escala 1, com conteúdo
artificial e fixture Nimbus Sans 10,5 pt, configurada somente no processo de
ensaio. Uma segunda rodada com Nimbus Sans 12 pt verifica a herança de tamanho.
Capturas incluem somente a janela da galeria, controles individuais
e seu próprio popup; nenhuma captura de desktop. A pressão nativa alterou 387,
284 e 349 pixels do botão GTK2/3/4, respectivamente, sem mover o contorno externo.
Isso verifica a tradução e os estados no host, sem homologar todo aplicativo
real ou a integração XSettings/KDED de uma sessão existente.

Para repetir, a partir da raiz do repositório:

```sh
python3 -m unittest discover -s gtk/tests -p 'test_*.py'
xvfb-run -a --server-args='-screen 0 1100x800x24 -nolisten tcp' \
  /usr/bin/python3 gtk/tools/preview_gtk2.py --output-dir /tmp/irixclassic-gtk-proof
xvfb-run -a --server-args='-screen 0 1100x800x24 -nolisten tcp' \
  /usr/bin/python3 gtk/tools/preview_classic.py --output-dir /tmp/irixclassic-gtk-proof
xvfb-run -a --server-args='-screen 0 1100x800x24 -nolisten tcp' \
  /usr/bin/python3 gtk/tools/preview_gtk4.py --output-dir /tmp/irixclassic-gtk-proof
```

GTK2/3 hosts precisam de GI da versão correspondente; GTK4 usa `libgtk-4` e
ctypes. Os hosts também usam xdotool e Pillow; GTK2/4 usam o comando `import` do
ImageMagick para capturar apenas o XID próprio. Eles gravam PNG e JSON sob `/tmp`,
configuram somente o processo de ensaio e removem seus diretórios XDG temporários.
O relógio de captura pertence ao ensaio e não implementa feedback visual no tema.
O argumento opcional `--font 'Nimbus Sans 12'` troca somente a fonte da galeria.

`gtk/tools/build_classic.py` recria PNGs e gtkrc usando Pillow e as fontes locais
Kvantum. O tema instalado não depende de Python ou Kvantum. A semântica de
overlays do motor GTK2 foi conferida no [tutorial GNOME do Pixmap Engine](https://wiki.gnome.org/Attic/GnomeArt/Tutorials/GtkEngines/PixmapEngine).
