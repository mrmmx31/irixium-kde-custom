#!/usr/bin/env python3
# SPDX-FileCopyrightText: 2026 mrmmx31
# SPDX-License-Identifier: GPL-3.0-or-later
"""Real Kvantum menus with temporary configuration; no system/theme writes.

Qt Widgets: interactive gallery and --testar event/renderer checks.
--qtquick: manual gallery of the installed org.kde.desktop menu components.
Captures include only this process's windows; no desktop or personal data.
"""
from __future__ import annotations
import argparse
import importlib
import importlib.util
import json
import os
from pathlib import Path
import shutil
import sys
import tempfile
ROOT=Path(__file__).resolve().parents[1]


def main(argv=None):
    p=argparse.ArgumentParser(description=__doc__)
    p.add_argument('--testar',action='store_true');p.add_argument('--qtquick',action='store_true')
    p.add_argument('--tema',choices=('IrixClassic','Irixium'),default='IrixClassic')
    p.add_argument('--fonte-px',type=int,default=14);p.add_argument('--capturas',type=Path)
    a=p.parse_args(argv)
    if not 10<=a.fonte_px<=28:p.error('--fonte-px deve estar entre 10 e 28.')
    if a.qtquick and a.testar:p.error('--qtquick é galeria manual; os testes automatizados são de Qt Widgets.')
    binding=next((m for m in ('PyQt6','PySide6') if importlib.util.find_spec(m)),None)
    if not binding:
        print('SKIP: PyQt6/PySide6 ausente; galeria não executada.',file=sys.stderr);return 77
    C=importlib.import_module(binding+'.QtCore');G=importlib.import_module(binding+'.QtGui')
    W=importlib.import_module(binding+'.QtWidgets');T=importlib.import_module(binding+'.QtTest')
    captures=a.capturas.expanduser().absolute() if a.capturas else None
    if captures:
        if captures.exists() and (not captures.is_dir() or any(captures.iterdir())):
            raise ValueError('Use pasta de capturas nova ou vazia.')
        captures.mkdir(parents=True,exist_ok=True)
    with tempfile.TemporaryDirectory(prefix='irix-menu-gallery-') as tmp:
        config=Path(tmp);dest=config/'Kvantum'/a.tema;dest.mkdir(parents=True)
        for ext in ('svg','kvconfig'):
            shutil.copyfile(ROOT/a.tema/(a.tema+'.'+ext),dest/(a.tema+'.'+ext))
        (config/'Kvantum/kvantum.kvconfig').write_text('[General]\ntheme='+a.tema+'\n')
        (config/'kdeglobals').write_text('[KDE]\nwidgetStyle=kvantum\n')
        os.environ['XDG_CONFIG_HOME']=str(config);os.environ['QT_STYLE_OVERRIDE']='kvantum'
        os.environ['QT_QUICK_CONTROLS_STYLE']='org.kde.desktop'
        app=W.QApplication(['irix-menu-gallery']);style=W.QStyleFactory.create('kvantum')
        if style is None:
            print('SKIP: plugin Kvantum ausente para este Qt.',file=sys.stderr);return 77
        app.setStyle(style);font=G.QFont('Nimbus Sans');font.setPixelSize(a.fonte_px);app.setFont(font)
        if a.qtquick:
            Q=importlib.import_module(binding+'.QtQml');engine=Q.QQmlApplicationEngine()
            errors=[];engine.warnings.connect(lambda es:errors.extend(e.toString() for e in es))
            engine.load(C.QUrl.fromLocalFile(str(ROOT/'tests/qml/PreviewMenus.qml')))
            if not engine.rootObjects():
                text='\n'.join(errors)
                if 'is not installed' in text or 'plugin cannot be loaded' in text:
                    print('SKIP: dependência KDE/Qt Quick ausente:\n'+text,file=sys.stderr);return 77
                raise RuntimeError('Falha de carregamento QML:\n'+text)
            return app.exec()
        win=W.QMainWindow();win.setWindowTitle('IrixClassic — menus / '+a.tema)
        win.menuBar().setNativeMenuBar(False)
        central=W.QWidget();win.setCentralWidget(central);layout=W.QVBoxLayout(central)
        title=W.QLabel('Menus reais do Qt Widgets, com o plugin Kvantum.\n'
                       'Compare seleção, submenus, atalhos, exclusividade e cancelamento com Esc.')
        title.setWordWrap(True);layout.addWidget(title)
        feedback=W.QLabel('Nenhuma ação executada.');feedback.setWordWrap(True);layout.addWidget(feedback)
        log=[]
        def record(name):
            log.append(name);feedback.setText('Última ação de demonstração: '+name)
        menu=win.menuBar().addMenu('&Arquivo')
        first=menu.addAction('&Abrir...');first.setShortcut(G.QKeySequence('Ctrl+O'))
        first.setIcon(style.standardIcon(W.QStyle.StandardPixmap.SP_DirOpenIcon))
        disabled=menu.addAction('&Salvar indisponível');disabled.setEnabled(False)
        second=menu.addAction('Duplicar &exemplo');second.setShortcut(G.QKeySequence('Ctrl+D'))
        menu.addSeparator()
        toggle=menu.addAction('Exibir &detalhes');toggle.setCheckable(True);toggle.setChecked(True)
        submenu=menu.addMenu('&Formato');subGroup=G.QActionGroup(win);subGroup.setExclusive(True)
        radio=[]
        for i,text in enumerate(('&Texto','&Imagem')):
            act=submenu.addAction(text);act.setCheckable(True);act.setChecked(i==0)
            subGroup.addAction(act);radio.append(act)
        deep=submenu.addMenu('&Mais opções');deep.addAction('Exemplo sem efeito externo')
        menu.addSeparator();last=menu.addAction('&Fechar galeria')
        menu.setTearOffEnabled(True)
        for act in (first,disabled,second,toggle,*radio):
            act.triggered.connect(lambda checked=False,t=act.text():record(t))
        last.triggered.connect(win.close)
        edit=win.menuBar().addMenu('&Editar');edit.addAction('Exemplo de ação')
        viewMenu=win.menuBar().addMenu('&Visualizar')
        rtl=viewMenu.addAction('Direita para esquerda');rtl.setCheckable(True)
        rtl.toggled.connect(lambda on:win.setLayoutDirection(C.Qt.LayoutDirection.RightToLeft if on else C.Qt.LayoutDirection.LeftToRight))
        longmenu=viewMenu.addMenu('Menu &longo')
        for i in range(60):longmenu.addAction('Item de demonstração '+str(i+1))
        helpMenu=win.menuBar().addMenu('A&juda');helpMenu.addAction('Sobre esta galeria')
        button=W.QPushButton('Abrir menu contextual');layout.addWidget(button)
        def popup():menu.popup(button.mapToGlobal(C.QPoint(0,button.height())))
        button.clicked.connect(popup)
        central.setContextMenuPolicy(C.Qt.ContextMenuPolicy.CustomContextMenu)
        central.customContextMenuRequested.connect(lambda pt:menu.popup(central.mapToGlobal(pt)))
        shortcut=G.QShortcut(G.QKeySequence('Shift+F10'),win);shortcut.activated.connect(popup)
        layout.addWidget(W.QLabel('Clique direito na área vazia ou use Shift+F10.\n'
                                 'Os comandos desta galeria não leem arquivos nem alteram a área de transferência.'))
        layout.addStretch();win.resize(640,340);win.show();win.activateWindow()
        app.processEvents();T.QTest.qWait(150)
        if not a.testar:return app.exec()
        results=[]
        def check(name,ok):results.append({'test':name,'passed':bool(ok)})
        def show(m):
            m.popup(win.mapToGlobal(C.QPoint(40,80)));app.processEvents();T.QTest.qWait(100)
        def click(m,act):
            pt=m.actionGeometry(act).center()
            T.QTest.mouseMove(m,pt);T.QTest.mouseClick(m,C.Qt.MouseButton.LeftButton,C.Qt.KeyboardModifier.NoModifier,pt)
            app.processEvents()
        show(menu);check('popup visible',menu.isVisible())
        if captures:menu.grab().save(str(captures/'01-popup.png'))
        n=len(log);click(menu,disabled);check('disabled action not triggered',len(log)==n)
        menu.close();show(menu);click(menu,first);check('mouse triggers action',log and log[-1]==first.text())
        check('action dismisses popup',not menu.isVisible())
        show(menu);n=len(log);T.QTest.keyClick(menu,C.Qt.Key.Key_Escape);app.processEvents()
        check('Escape dismisses without action',not menu.isVisible() and len(log)==n)
        show(menu);menu.setActiveAction(first);T.QTest.keyClick(menu,C.Qt.Key.Key_Down);app.processEvents()
        check('keyboard skips disabled action',menu.activeAction()==second)
        T.QTest.keyClick(menu,C.Qt.Key.Key_Return);app.processEvents()
        check('Return triggers selected action',log and log[-1]==second.text())
        show(menu);before=toggle.isChecked();click(menu,toggle)
        check('checkable item toggles',toggle.isChecked()!=before)
        show(submenu);click(submenu,radio[1]);check('radio menu exclusive',radio[1].isChecked() and not radio[0].isChecked())
        # Open a cascade with keyboard, letting QMenu own the full event policy.
        show(menu);menu.setActiveAction(submenu.menuAction());T.QTest.keyClick(menu,C.Qt.Key.Key_Right)
        app.processEvents();T.QTest.qWait(300);check('keyboard opens submenu',submenu.isVisible())
        submenu.close();menu.close()
        # Actual renderer: isolate the panel from text, symbols and icons.
        if a.tema=='IrixClassic':
            flag=W.QStyle.StateFlag
            for state,flags,corner,face in (
                ('selected',flag.State_Enabled|flag.State_Active|flag.State_Selected,'#ececec','#dfdfdf'),
                ('pressed',flag.State_Enabled|flag.State_Active|flag.State_Sunken,'#606060','#b3b3b3'),
                ('disabled',flag.State_Active|flag.State_Selected,'#c1c1c1','#c1c1c1')):
                opt=W.QStyleOptionMenuItem();opt.initFrom(menu);opt.rect=C.QRect(0,0,150,24)
                opt.text='';opt.menuItemType=W.QStyleOptionMenuItem.MenuItemType.Normal
                opt.checkType=W.QStyleOptionMenuItem.CheckType.NotCheckable;opt.menuHasCheckableItems=False
                opt.maxIconWidth=0;opt.state=flags;opt.font=font
                im=G.QImage(150,24,G.QImage.Format.Format_ARGB32);im.fill(G.QColor('#c1c1c1'))
                painter=G.QPainter(im)
                try:style.drawControl(W.QStyle.ControlElement.CE_MenuItem,opt,painter,menu)
                finally:painter.end()
                check(state+' panel corner',im.pixelColor(0,0).name()==corner)
                check(state+' panel face',im.pixelColor(70,12).name()==face)
                if captures:im.save(str(captures/('menurow-'+state+'.png')))
        win.setLayoutDirection(C.Qt.LayoutDirection.RightToLeft);show(menu)
        check('RTL popup usable',menu.isVisible() and menu.actionGeometry(first).isValid())
        menu.close();win.close();app.processEvents()
        report={'qt':C.qVersion(),'binding':binding,'platform':app.platformName(),
                'theme':a.tema,'style':style.metaObject().className(),'results':results,
                'note':'Native Qt Widgets behavior/pixels, not historical equivalence certification.'}
        print(json.dumps(report,ensure_ascii=False,indent=2))
        if captures:(captures/'RESULTADO-MENUS.json').write_text(json.dumps(report,indent=2)+'\n')
        return 0 if all(r['passed'] for r in results) else 1

if __name__=='__main__':
    try:sys.exit(main())
    except ImportError as e:print('SKIP: dependência Qt ausente:',e,file=sys.stderr);sys.exit(77)
    except (OSError,ValueError,RuntimeError) as e:print('ERRO:',e,file=sys.stderr);sys.exit(1)
