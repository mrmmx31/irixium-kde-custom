#!/usr/bin/env python3
# SPDX-FileCopyrightText: 2026 mrmmx31
# SPDX-License-Identifier: GPL-3.0-or-later
"""Native Qt tab gallery. Isolated configuration; no global theme writes."""
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
    p.add_argument('--testar',action='store_true')
    p.add_argument('--qtquick',action='store_true')
    p.add_argument('--tema',choices=('IrixClassic','Irixium'),default='IrixClassic')
    p.add_argument('--fonte-px',type=int,default=14)
    p.add_argument('--capturas',type=Path)
    a=p.parse_args(argv)
    if not 10<=a.fonte_px<=28:p.error('--fonte-px: 10 a 28.')
    if a.qtquick and a.testar:p.error('--qtquick é galeria manual; --testar exercita Qt Widgets.')
    binding=next((m for m in ('PyQt6','PySide6') if importlib.util.find_spec(m)),None)
    if not binding:
        print('SKIP: PyQt6/PySide6 ausente; testes nativos não executados.',file=sys.stderr);return 77
    source=ROOT/a.tema
    if not all((source/(a.tema+'.'+ext)).is_file() for ext in ('svg','kvconfig')):
        raise ValueError('Tema não encontrado no checkout: '+a.tema)
    folder=a.capturas.expanduser().absolute() if a.capturas else None
    if folder:
        if folder.is_symlink() or (folder.exists() and (not folder.is_dir() or any(folder.iterdir()))):
            raise ValueError('Use uma pasta de capturas nova ou vazia.')
        folder.mkdir(parents=True,mode=0o700,exist_ok=True)
    with tempfile.TemporaryDirectory(prefix='irix-tabs-gallery-') as tmp:
        config=Path(tmp);dest=config/'Kvantum'/a.tema;dest.mkdir(parents=True)
        for ext in ('svg','kvconfig'):shutil.copyfile(source/(a.tema+'.'+ext),dest/(a.tema+'.'+ext))
        (config/'Kvantum/kvantum.kvconfig').write_text('[General]\ntheme='+a.tema+'\n')
        (config/'kdeglobals').write_text('[KDE]\nwidgetStyle=kvantum\n')
        os.environ['XDG_CONFIG_HOME']=str(config)
        os.environ['QT_STYLE_OVERRIDE']='kvantum'
        os.environ['QT_QUICK_CONTROLS_STYLE']='org.kde.desktop'
        C=importlib.import_module(binding+'.QtCore');G=importlib.import_module(binding+'.QtGui')
        W=importlib.import_module(binding+'.QtWidgets');T=importlib.import_module(binding+'.QtTest')
        app=W.QApplication(['irixclassic-tabs-gallery']);style=W.QStyleFactory.create('kvantum')
        if style is None:
            print('SKIP: plugin Kvantum não disponível para este Qt.',file=sys.stderr);return 77
        app.setStyle(style);font=G.QFont('Nimbus Sans');font.setPixelSize(a.fonte_px);app.setFont(font)
        if a.qtquick:
            Q=importlib.import_module(binding+'.QtQml');engine=Q.QQmlApplicationEngine();errors=[]
            engine.warnings.connect(lambda es:errors.extend(e.toString() for e in es))
            engine.load(C.QUrl.fromLocalFile(str(ROOT/'tests/qml/PreviewTabs.qml')))
            if not engine.rootObjects():
                text='\n'.join(errors)
                if 'is not installed' in text or 'plugin cannot be loaded' in text:
                    print('SKIP: dependência KDE/Qt Quick ausente:\n'+text,file=sys.stderr);return 77
                raise RuntimeError('Erro QML:\n'+text)
            return app.exec()

        class ProbeTabBar(W.QTabBar):
            def option(self,index):
                opt=W.QStyleOptionTab();self.initStyleOption(opt,index);return opt
        class ProbeTabWidget(W.QTabWidget):
            def __init__(self):
                super().__init__();self.setTabBar(ProbeTabBar())
        win=W.QWidget();win.setWindowTitle('IrixClassic — abas / '+a.tema)
        layout=W.QVBoxLayout(win)
        title=W.QLabel('Abas reais do Qt Widgets: clique, teclado, foco, indisponível e fechar.\n'
                       'O transbordamento usa os controles do Qt, não o popup de abas colapsadas do ViewKit.')
        title.setWordWrap(True);layout.addWidget(title)
        rtl=W.QCheckBox('Direita para esquerda');layout.addWidget(rtl)
        rtl.toggled.connect(lambda on:win.setLayoutDirection(C.Qt.LayoutDirection.RightToLeft if on else C.Qt.LayoutDirection.LeftToRight))
        grid=W.QGridLayout();layout.addLayout(grid);tabs=[]
        positions=(W.QTabWidget.TabPosition.North,W.QTabWidget.TabPosition.South,
                   W.QTabWidget.TabPosition.West,W.QTabWidget.TabPosition.East)
        for k,pos in enumerate(positions):
            group=W.QGroupBox(('Superior — painel','Inferior — documentos','Esquerda','Direita')[k])
            gl=W.QVBoxLayout(group);tw=ProbeTabWidget();tw.setTabPosition(pos);tw.setDocumentMode(k==1)
            tw.setTabsClosable(True);tw.setMovable(True);tw.tabBar().setExpanding(False);tw.setUsesScrollButtons(True)
            for i,text in enumerate(('Geral','Detalhes','Indisponível','Avançado','Nome de aba bastante longo','Outros')):
                page=W.QWidget();pl=W.QVBoxLayout(page)
                pl.addWidget(W.QLabel('Página '+str(i+1)+' — conteúdo do aplicativo preservado.'))
                pl.addWidget(W.QLineEdit('Campo de demonstração'))
                pl.addStretch();tw.addTab(page,text)
            tw.setTabEnabled(2,False)
            tw.tabCloseRequested.connect(lambda i,w=tw:w.removeTab(i))
            gl.addWidget(tw);grid.addWidget(group,k//2,k%2);tabs.append(tw)
        status=W.QLabel('Nenhuma alteração na seleção global do Kvantum.');layout.addWidget(status)
        win.resize(940,690);win.show();win.activateWindow();app.processEvents();T.QTest.qWait(200)
        if not a.testar:return app.exec()
        results=[]
        def check(name,value):results.append({'test':name,'passed':bool(value)})
        for k,tw in enumerate(tabs):
            bar=tw.tabBar();bar.setCurrentIndex(0);app.processEvents()
            # Select tab 1, not its close button. The left label inset is stable.
            r=bar.tabRect(1);pt=r.center()
            T.QTest.mouseClick(bar,C.Qt.MouseButton.LeftButton,C.Qt.KeyboardModifier.NoModifier,pt)
            app.processEvents();check(f'{k}: mouse selects page',tw.currentIndex()==1)
            old=tw.currentIndex();r=bar.tabRect(2)
            T.QTest.mouseClick(bar,C.Qt.MouseButton.LeftButton,C.Qt.KeyboardModifier.NoModifier,r.center())
            app.processEvents();check(f'{k}: disabled tab does not activate',tw.currentIndex()==old)
            check(f'{k}: labels have valid geometry',all(bar.tabRect(i).isValid() for i in range(bar.count())))
            if folder:
                if not tw.grab().save(str(folder/(f'orientacao-{k}.png'))):raise RuntimeError('Falha ao salvar captura.')
        tw=tabs[0];bar=tw.tabBar();bar.setCurrentIndex(0);bar.setFocus();app.processEvents()
        T.QTest.keyClick(bar,C.Qt.Key.Key_Right);app.processEvents()
        check('keyboard selects next tab',bar.currentIndex()==1)
        T.QTest.keyClick(bar,C.Qt.Key.Key_Right);app.processEvents()
        check('keyboard skips disabled tab',bar.currentIndex()==3)
        check('keyboard focus remains on tabbar',bar.hasFocus())
        # Request the close of a synthetic page only; application signal owns it.
        before=tw.count();index=tw.currentIndex()
        button=bar.tabButton(index,W.QTabBar.ButtonPosition.RightSide) or bar.tabButton(index,W.QTabBar.ButtonPosition.LeftSide)
        if button:
            T.QTest.mouseClick(button,C.Qt.MouseButton.LeftButton);app.processEvents()
            check('close emits application request',tw.count()==before-1)
        else:check('close control present',False)
        # Rendering checks use the actual style, not a replacement painter/style.
        if a.tema=='IrixClassic':
            f=W.QStyle.StateFlag
            images={}
            for state,flags in (('normal',f.State_Enabled|f.State_Active),
                                ('focused',f.State_Enabled|f.State_Active|f.State_MouseOver),
                                ('selected',f.State_Enabled|f.State_Active|f.State_Selected),
                                ('pressed',f.State_Enabled|f.State_Active|f.State_Sunken)):
                opt=bar.option(0);opt.rect=C.QRect(0,0,140,28);opt.state=flags
                im=G.QImage(140,28,G.QImage.Format.Format_ARGB32);im.fill(G.QColor('#c1c1c1'))
                painter=G.QPainter(im)
                try:style.drawControl(W.QStyle.ControlElement.CE_TabBarTabShape,opt,painter,bar)
                finally:painter.end()
                images[state]=im
                if folder:im.save(str(folder/(state+'.png')))
            check('selection has distinct face',images['normal']!=images['selected'])
            check('hover has distinct face',images['normal']!=images['focused'])
            check('tab press has no invented sunken state',images['normal']==images['pressed'])
        win.setLayoutDirection(C.Qt.LayoutDirection.RightToLeft);app.processEvents()
        check('RTL layout retained',bar.layoutDirection()==C.Qt.LayoutDirection.RightToLeft)
        report={'qt':C.qVersion(),'binding':binding,'platform':app.platformName(),'theme':a.tema,
                'style':style.metaObject().className(),'results':results,
                'note':'Qt Widgets native execution only; not historical pixel equivalence or Qt Quick acceptance.'}
        print(json.dumps(report,indent=2,ensure_ascii=False))
        if folder:(folder/'RESULTADO-ABAS.json').write_text(json.dumps(report,indent=2)+'\n')
        win.close();app.processEvents()
        return 0 if all(r['passed'] for r in results) else 1

if __name__=='__main__':
    try:sys.exit(main())
    except ImportError as e:print('SKIP: dependência Qt ausente:',e,file=sys.stderr);sys.exit(77)
    except (OSError,ValueError,RuntimeError) as e:print('ERRO:',e,file=sys.stderr);sys.exit(1)
