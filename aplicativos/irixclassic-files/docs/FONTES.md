# Fontes e distinções

- Fonte base: https://packages.debian.org/trixie/dolphin
- Fonte upstream examinada: https://github.com/KDE/dolphin/tree/v25.04.3
- DolphinMainWindow e ações: src/dolphinmainwindow.cpp, src/dolphinui.rc.
- Backend e seleção: src/views/dolphinview.h e src/dolphinviewcontainer.h.
- Persistência a isolar: src/views/viewproperties.cpp e src/dolphinbookmarkhandler.cpp.
- Linkagem: src/CMakeLists.txt. Bibliotecas private/VCS são recompiladas em conjunto.
- Referência histórica: https://techpubs.jurassic.nl/library/manuals/1000/007-1342-170/sgi_html/ch13.html
- Content Viewer: https://techpubs.jurassic.nl/library/manuals/1000/007-1342-180/sgi_html/ch04.html
- Qt: https://doc.qt.io/qt-6.8/qimagereader.html e https://doc.qt.io/qt-6.8/qprocess.html
- Publicação: https://cli.github.com/manual/gh_release_create

Cores de referência da captura fornecida: vista #729C9C, Shelf #5680AB,
preview #5F5F5F, campo de caminho #B98E8E. Elas não definem uma paleta universal
histórica. Não foi embutida a captura nem reutilizado um desenho SGI sem licença.

Estudo anterior (2026-10-06) previa identidade em paralelo e primeira versão
com texto/imagens. Nesta implementação, o código novo é uma composição ao redor
da janela Dolphin real. O controle de zoom é QSlider, e o menu histórico é uma
adaptação. Não há equivalência total dos widgets ViewKit/Motif.
