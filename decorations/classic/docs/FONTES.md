# Fontes e procedência

## Materiais do usuário preservados

Base recebida: pacote `irixium-classic-v5.zip` da conversa; mapas gráficos da v4
usados sem alteração de bytes. Referências de pixels: os dois PNGs IRIX de
1280×1024 e 1024×768. Fonte tipográfica e conteúdo dos aplicativos não integram
os mapas de teste. Os PNGs completos do usuário não são redistribuídos no pacote.

## API primária consultada nesta revisão

- Qt Quick 6.8, MouseArea:
  https://doc.qt.io/qt-6.8/qml-qtquick-mousearea.html
  Pressão, soltura, cancelamento, eventos compostos e supressão do segundo clique
  quando doubleClicked é aceito; indisponibilidade torna MouseArea transparente,
  razão para consumir separadamente o clique no controle indisponível.
- KDE KWin, ramo Plasma/6.3, Aurorae:
  https://raw.githubusercontent.com/KDE/kwin/Plasma/6.3/src/plugins/kdecorations/aurorae/src/aurorae.cpp
  Descoberta pelo ID do pacote, caminho kwin/decorations, cache de componentes,
  contexto decoration/decorationSettings e installTitleItem.
- KDE KDecoration, ramo Plasma/6.3:
  https://raw.githubusercontent.com/KDE/kdecoration/Plasma/6.3/src/decoration.h
  requestShowWindowMenu(QRect), requestMinimize, requestToggleMaximization e
  requestClose. Não foi pressuposto um sinal de fechamento do menu nativo.
- CDE, manual dtwm:
  https://cdesktopenv.sourceforge.io/man1/dtwm.html
  Referência da mecânica histórica do menu e da linhagem Motif.

## Código histórico já examinado na conversa

- CDE/dtwm: cde/programs/dtwm/WmCDecor.c, DepressGadget/PushGadgetIn/PopGadgetOut.
  https://github.com/cdesktopenv/cde/blob/master/cde/programs/dtwm/WmCDecor.c
- CDE/dtwm: cde/programs/dtwm/WmCEvent.c, pressão/soltura dos controles.
  https://github.com/cdesktopenv/cde/blob/master/cde/programs/dtwm/WmCEvent.c
- Manual 4Dwm preservado:
  https://techpubs.jurassic.nl/manpages_0530/cat1/Xm/4Dwm.html

O comportamento foi reimplementado em QML/JavaScript a partir dos princípios;
não há cópia de uma suposta árvore privada do 4Dwm nem alegação de acesso a ela.
As distinções entre referência IRIX, base CDE e adaptação estão em CONTRATO.md.

## Verificações específicas da rc2

- KWin/Aurorae, MenuButton.qml, ramo Plasma/6.3:
  https://raw.githubusercontent.com/KDE/kwin/Plasma/6.3/src/plugins/kdecorations/aurorae/src/qml/MenuButton.qml
  O próprio comentário do componente identifica que publicar o popup pode consumir
  o segundo clique. A rc2 implementa sua própria espera após a soltura; não copia
  o temporizador de pressão do componente SVG.
- KWin, configurações de decoração:
  https://raw.githubusercontent.com/KDE/kwin/Plasma/6.3/src/decorations/settings.cpp
  `CloseOnDoubleClickOnMenu` é lido com padrão false. A rc2 adota uma política
  local explícita, sem regravar essa chave compartilhada.
- Qt 6.8, QStyleHints:
  https://doc.qt.io/qt-6.8/qstylehints.html#mouseDoubleClickInterval-prop
  Intervalo de reconhecimento usado para aguardar o clique simples.
- Qt 6.8, Qt.styleHints:
  https://doc.qt.io/qt-6.8/qml-qtqml-qt.html#styleHints-prop
  Acesso ao intervalo nativo em QML.
- KWin, encaminhamento para a superfície Qt Quick:
  https://raw.githubusercontent.com/KDE/kwin/Plasma/6.3/src/effect/offscreenquickview.cpp
  `forwardMouseEvent()` encaminha a pressão e pode gerar MouseButtonDblClick.
  A máquina de estados aceita a segunda pressão antes desse evento.
- Qt 6.8, QtTest TestCase:
  https://doc.qt.io/qt-6.8/qml-qttest-testcase.html#mouseDoubleClickSequence-method
  Sequência completa de teste: Press-Release-Press-DoubleClick-Release.
