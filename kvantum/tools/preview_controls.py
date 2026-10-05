#!/usr/bin/env python3
# SPDX-FileCopyrightText: 2026 mrmmx31
# SPDX-License-Identifier: GPL-3.0-or-later
"""Block 7 native gallery. No system writes, proxy style, or simulated rendering.

--testar uses Qt's controls/events and separately checks QStyle-rendered images.
Only the gallery's own content is saved with --capturas. Missing native runtime
returns 77, never a successful result.
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
    p.add_argument('--testar',action='store_true')
    p.add_argument('--qtquick',action='store_true')
    p.add_argument('--tema',choices=('IrixClassic','Irixium'),default='IrixClassic')
    p.add_argument('--fonte-px',type=int,default=14)
    p.add_argument('--capturas',type=Path)
    a=p.parse_args(argv)
    if not 10<=a.fonte_px<=28:p.error('--fonte-px: 10 a 28.')
    if a.qtquick and (a.testar or a.capturas):p.error('--qtquick é galeria manual; --testar e --capturas são de Widgets.')
    binding=next((m for m in ('PyQt6','PySide6') if importlib.util.find_spec(m)),None)
    if not binding:
        print('SKIP: PyQt6/PySide6 ausente. Nenhum teste nativo executado.',file=sys.stderr);return 77
    source=ROOT/a.tema
    if not all((source/(a.tema+'.'+ext)).is_file() for ext in ('svg','kvconfig')):
        raise ValueError('Tema não encontrado: '+a.tema)
    folder=a.capturas.expanduser().absolute() if a.capturas else None
    if folder:
        if any(x.is_symlink() for x in (folder,*folder.parents)) or (folder.exists() and (not folder.is_dir() or any(folder.iterdir()))):
            raise ValueError('Use pasta nova ou vazia, sem links simbólicos.')
        folder.mkdir(parents=True,mode=0o700,exist_ok=True)
    with tempfile.TemporaryDirectory(prefix='irix-controls-gallery-') as tmp:
        config=Path(tmp);dest=config/'Kvantum'/a.tema;dest.mkdir(parents=True)
        for ext in ('svg','kvconfig'):shutil.copyfile(source/(a.tema+'.'+ext),dest/(a.tema+'.'+ext))
        (config/'Kvantum/kvantum.kvconfig').write_text('[General]\ntheme='+a.tema+'\n')
        (config/'kdeglobals').write_text('[KDE]\nwidgetStyle=kvantum\n')
        os.environ['XDG_CONFIG_HOME']=str(config);os.environ['QT_STYLE_OVERRIDE']='kvantum'
        os.environ['QT_QUICK_CONTROLS_STYLE']='org.kde.desktop'
        C=importlib.import_module(binding+'.QtCore');G=importlib.import_module(binding+'.QtGui')
        W=importlib.import_module(binding+'.QtWidgets');T=importlib.import_module(binding+'.QtTest')
        app=W.QApplication(['irixclassic-controls-gallery']);style=W.QStyleFactory.create('kvantum')
        if style is None:
            print('SKIP: plugin Kvantum indisponível para este Qt.',file=sys.stderr);return 77
        app.setStyle(style);font=G.QFont('Nimbus Sans');font.setPixelSize(a.fonte_px);app.setFont(font)
        if a.qtquick:
            Q=importlib.import_module(binding+'.QtQml');engine=Q.QQmlApplicationEngine();errors=[]
            engine.warnings.connect(lambda es:errors.extend(e.toString() for e in es))
            engine.load(C.QUrl.fromLocalFile(str(ROOT/'tests/qml/PreviewControls.qml')))
            if not engine.rootObjects():
                text='\n'.join(errors)
                if 'is not installed' in text or 'plugin cannot be loaded' in text:
                    print('SKIP: módulo Qt/KDE ausente:\n'+text,file=sys.stderr);return 77
                raise RuntimeError('Erro QML:\n'+text)
            return app.exec()

        class Slider(W.QSlider):
            def option(self):
                o=W.QStyleOptionSlider();self.initStyleOption(o);return o
        win=W.QMainWindow();win.setWindowTitle('IrixClassic — bloco 7 / '+a.tema)
        root=W.QWidget();lay=W.QVBoxLayout(root);win.setCentralWidget(root)
        title=W.QLabel('Qt Widgets reais: intervalos, seleção, foco, arraste e indisponibilidade.\n'
                        'Dial, MDI e Toolbox são adaptações do Qt, não réplicas de aplicativos SGI.')
        title.setWordWrap(True);lay.addWidget(title)
        rtl=W.QCheckBox('Direita para esquerda (RTL)');lay.addWidget(rtl)
        rtl.toggled.connect(lambda on:win.setLayoutDirection(C.Qt.LayoutDirection.RightToLeft if on else C.Qt.LayoutDirection.LeftToRight))
        tabs=W.QTabWidget();lay.addWidget(tabs)
        ranges=W.QWidget();gl=W.QGridLayout(ranges);tabs.addTab(ranges,'Intervalos')
        sliders=[]
        for k,ori in enumerate((C.Qt.Orientation.Horizontal,C.Qt.Orientation.Vertical)):
            group=W.QGroupBox('Horizontal' if k==0 else 'Vertical');box=W.QVBoxLayout(group)
            label=W.QLabel('Valor: 40');box.addWidget(label)
            slider=Slider(ori);slider.setRange(0,100);slider.setValue(40);slider.setSingleStep(1);slider.setPageStep(10)
            slider.setTickInterval(10);slider.setTickPosition(W.QSlider.TickPosition.TicksBothSides)
            slider.valueChanged.connect(lambda v,l=label:l.setText('Valor: '+str(v)))
            if k==1:slider.setMinimumHeight(140)
            box.addWidget(slider);sliders.append(slider)
            inactive=Slider(ori);inactive.setRange(0,100);inactive.setValue(65);inactive.setEnabled(False)
            box.addWidget(inactive);gl.addWidget(group,0,k)
        for i,value in enumerate((0,1,50,99,100)):
            bar=W.QProgressBar();bar.setRange(0,100);bar.setValue(value);bar.setFormat('%p%')
            gl.addWidget(bar,i+1,0,1,2)
        busy=W.QProgressBar();busy.setRange(0,0);gl.addWidget(busy,6,0,1,2)
        muted=W.QProgressBar();muted.setValue(55);muted.setEnabled(False);gl.addWidget(muted,7,0,1,2)
        vertical=W.QProgressBar();vertical.setOrientation(C.Qt.Orientation.Vertical);vertical.setValue(50)
        gl.addWidget(vertical,0,2,7,1)
        label=W.QLabel('0/1/50/99/100%, indeterminado e desativado; percentual é informação do aplicativo.')
        label.setWordWrap(True);gl.addWidget(label,8,0,1,3)

        data=W.QWidget();dl=W.QVBoxLayout(data);tabs.addTab(data,'Listas, árvores e tabelas')
        split=W.QSplitter(C.Qt.Orientation.Horizontal);dl.addWidget(split)
        lists=W.QListWidget();lists.addItems(['Sistema','Rede','Áudio','Vídeo','Indisponível'])
        lists.setSelectionMode(W.QAbstractItemView.SelectionMode.ExtendedSelection)
        lists.item(4).setFlags(lists.item(4).flags() & ~C.Qt.ItemFlag.ItemIsEnabled)
        split.addWidget(lists)
        tree=W.QTreeWidget();tree.setHeaderLabels(['Nome','Tipo'])
        branch=W.QTreeWidgetItem(tree,['Sistema','Grupo']);W.QTreeWidgetItem(branch,['Dispositivos','Pasta'])
        W.QTreeWidgetItem(branch,['Terminal','Aplicativo']);branch.setExpanded(True)
        checkitem=W.QTreeWidgetItem(tree,['Confirmado','Seleção']);checkitem.setCheckState(0,C.Qt.CheckState.Checked)
        split.addWidget(tree)
        table=W.QTableWidget(6,3);table.setHorizontalHeaderLabels(['Nome','Valor','Estado'])
        table.setAlternatingRowColors(True);table.setSelectionBehavior(W.QAbstractItemView.SelectionBehavior.SelectRows)
        for y in range(6):
            for x,text in enumerate((f'Recurso {y+1}',str(60-y*7),'Pronto')):table.setItem(y,x,W.QTableWidgetItem(text))
        table.setSortingEnabled(True);dl.addWidget(table)
        splitter_vertical=W.QSplitter(C.Qt.Orientation.Vertical)
        splitter_vertical.addWidget(W.QLabel('Divisor horizontal — arraste o relevo.'))
        edit=W.QTextEdit();edit.setPlainText('Conteúdo de exemplo.\n'+('Área rolável com os desenhos aprovados.\n'*12))
        splitter_vertical.addWidget(edit);dl.addWidget(splitter_vertical)

        misc=W.QWidget();ml=W.QHBoxLayout(misc);tabs.addTab(misc,'Painéis, dial e MDI')
        tools=W.QToolBox()
        for i in range(3):
            page=W.QWidget();pl=W.QVBoxLayout(page);pl.addWidget(W.QLabel('Forma do Toolbox: nativa do motor.'))
            pl.addWidget(W.QLineEdit('Conteúdo preservado'));tools.addItem(page,'Grupo '+str(i+1))
        tools.setItemEnabled(2,False);ml.addWidget(tools)
        dialbox=W.QGroupBox('Dial — adaptação Qt');dbo=W.QVBoxLayout(dialbox)
        dial=W.QDial();dial.setRange(0,100);dial.setValue(40);dial.setNotchesVisible(True);dial.setFixedSize(96,96)
        dbo.addWidget(dial);dialvalue=W.QLabel('40');dbo.addWidget(dialvalue)
        dial.valueChanged.connect(lambda v:dialvalue.setText(str(v)))
        muted_dial=W.QDial();muted_dial.setValue(60);muted_dial.setEnabled(False);dbo.addWidget(muted_dial)
        tip=W.QPushButton('Mostrar tooltip');tip.setToolTip('Dica opaca com relevo IrixClassic.');dbo.addWidget(tip)
        ml.addWidget(dialbox)
        mdi=W.QMdiArea();mdi.setMinimumSize(270,230);sub=mdi.addSubWindow(W.QTextEdit('Subjanela interna.\nNão é uma decoração do KWin.'))
        sub.setWindowTitle('Documento');sub.resize(240,190);sub.show();ml.addWidget(mdi)
        dock=W.QDockWidget('Painel acoplável',win);dock.setWidget(W.QLabel('Título do dock e divisor; os ícones continuam nativos.'))
        win.addDockWidget(C.Qt.DockWidgetArea.BottomDockWidgetArea,dock)
        win.statusBar().showMessage('Configuração temporária — nenhuma instalação executada.');win.statusBar().setSizeGripEnabled(True)
        win.resize(1020,770);win.show();win.activateWindow();app.processEvents();T.QTest.qWait(250)
        if not a.testar:
            return app.exec()
        results=[]
        def check(name,value):results.append({'test':name,'passed':bool(value)})
        def save(name,widget):
            if folder and not widget.grab().save(str(folder/(name+'.png'))):raise RuntimeError('Falha ao gravar imagem.')
        tabs.setCurrentIndex(0);app.processEvents()
        for i,s in enumerate(sliders):
            s.setValue(40);s.setFocus();app.processEvents()
            T.QTest.keyClick(s,C.Qt.Key.Key_Right if i==0 else C.Qt.Key.Key_Up);app.processEvents()
            check(f'slider {i}: keyboard step',s.value()==41)
            T.QTest.keyClick(s,C.Qt.Key.Key_End);app.processEvents();check(f'slider {i}: maximum',s.value()==100)
            T.QTest.keyClick(s,C.Qt.Key.Key_Home);app.processEvents();check(f'slider {i}: minimum',s.value()==0)
            s.setValue(40);opt=s.option();r=style.subControlRect(W.QStyle.ComplexControl.CC_Slider,opt,W.QStyle.SubControl.SC_SliderHandle,s)
            pt=r.center();T.QTest.mousePress(s,C.Qt.MouseButton.LeftButton,C.Qt.KeyboardModifier.NoModifier,pt)
            app.processEvents();check(f'slider {i}: drag starts',s.isSliderDown())
            end=pt+C.QPoint(16,0) if i==0 else pt+C.QPoint(0,-16)
            T.QTest.mouseMove(s,end,20);T.QTest.mouseRelease(s,C.Qt.MouseButton.LeftButton,C.Qt.KeyboardModifier.NoModifier,end)
            app.processEvents();check(f'slider {i}: drag releases',not s.isSliderDown());check(f'slider {i}: range respected',0<=s.value()<=100)
            check(f'slider {i}: pointer changes value',s.value()!=40)
        save('intervalos',ranges)
        tabs.setCurrentIndex(1);app.processEvents();T.QTest.qWait(100)
        for row_index,mods in ((0,C.Qt.KeyboardModifier.NoModifier),(2,C.Qt.KeyboardModifier.ControlModifier)):
            pt=lists.visualItemRect(lists.item(row_index)).center()
            T.QTest.mouseClick(lists.viewport(),C.Qt.MouseButton.LeftButton,mods,pt)
        app.processEvents();check('list: native multiple selection',len(lists.selectedItems())==2)
        pt=lists.visualItemRect(lists.item(4)).center()
        T.QTest.mouseClick(lists.viewport(),C.Qt.MouseButton.LeftButton,C.Qt.KeyboardModifier.ControlModifier,pt)
        app.processEvents();check('list: unavailable item not selected',not lists.item(4).isSelected())
        tree.setCurrentItem(branch);tree.setFocus();branch.setExpanded(True);app.processEvents()
        T.QTest.keyClick(tree,C.Qt.Key.Key_Left);app.processEvents();check('tree: collapse by keyboard',not branch.isExpanded())
        T.QTest.keyClick(tree,C.Qt.Key.Key_Right);app.processEvents();check('tree: expand by keyboard',branch.isExpanded())
        header=table.horizontalHeader();x=header.sectionViewportPosition(1)+header.sectionSize(1)//2
        T.QTest.mouseClick(header.viewport(),C.Qt.MouseButton.LeftButton,C.Qt.KeyboardModifier.NoModifier,C.QPoint(x,header.height()//2))
        app.processEvents();check('header: sorting requested',header.sortIndicatorSection()==1)
        split.setSizes([150,350]);sizes=split.sizes();handle=split.handle(1);pt=handle.rect().center()
        T.QTest.mousePress(handle,C.Qt.MouseButton.LeftButton,C.Qt.KeyboardModifier.NoModifier,pt)
        T.QTest.mouseMove(handle,pt+C.QPoint(24,0),20)
        T.QTest.mouseRelease(handle,C.Qt.MouseButton.LeftButton,C.Qt.KeyboardModifier.NoModifier,pt+C.QPoint(24,0));app.processEvents()
        check('splitter: panes remain valid',all(x>0 for x in split.sizes()))
        check('splitter: pointer changes divider position',split.sizes()!=sizes)
        save('dados',data)
        tabs.setCurrentIndex(2);app.processEvents();dial.setFocus();value=dial.value()
        T.QTest.keyClick(dial,C.Qt.Key.Key_Right);app.processEvents();check('dial: native value changes',dial.value()!=value)
        check('toolbox: disabled page remains unavailable',not tools.isItemEnabled(2))
        check('MDI: subwindow present',sub in mdi.subWindowList());save('paineis',misc)
        # Image comparison uses QStyle paths, not our Python map renderer.
        flags=W.QStyle.StateFlag
        def draw(kind,state):
            im=G.QImage(24,220,G.QImage.Format.Format_ARGB32);im.fill(G.QColor('#c1c1c1'))
            painter=G.QPainter(im)
            try:
                if kind=='slider':
                    o=sliders[1].option();o.rect=C.QRect(0,0,24,220);o.state=state
                    o.subControls=W.QStyle.SubControl.SC_SliderHandle|W.QStyle.SubControl.SC_SliderGroove
                    o.activeSubControls=W.QStyle.SubControl.SC_SliderHandle
                    o.orientation=C.Qt.Orientation.Vertical;o.minimum=0;o.maximum=100;o.sliderPosition=50;o.sliderValue=50
                    style.drawComplexControl(W.QStyle.ComplexControl.CC_Slider,o,painter,sliders[1])
                else:
                    o=W.QStyleOptionHeader();o.rect=C.QRect(0,0,24,24);o.state=state
                    o.position=W.QStyleOptionHeader.SectionPosition.OnlyOneSection
                    style.drawControl(W.QStyle.ControlElement.CE_HeaderSection,o,painter,None)
            finally:painter.end()
            return im
        if a.tema=='IrixClassic':
            for kind in ('slider','header'):
                normal=draw(kind,flags.State_Enabled|flags.State_Active)
                pressed=draw(kind,flags.State_Enabled|flags.State_Active|flags.State_Sunken)
                check(kind+': QStyle draws a distinct pressed bevel',normal!=pressed)
                if folder:normal.save(str(folder/(kind+'-normal.png')));pressed.save(str(folder/(kind+'-pressed.png')))
        rtl.setChecked(True);app.processEvents();check('RTL retained',win.layoutDirection()==C.Qt.LayoutDirection.RightToLeft)
        report={'qt':C.qVersion(),'binding':binding,'platform':app.platformName(),'theme':a.tema,
                'style':style.metaObject().className(),'results':results,
                'scope':'Qt Widgets gallery, not target-app or Qt Quick acceptance.'}
        print(json.dumps(report,indent=2,ensure_ascii=False))
        if folder:(folder/'RESULTADO-CONTROLES.json').write_text(json.dumps(report,indent=2,ensure_ascii=False)+'\n')
        win.close();app.processEvents()
        return 0 if all(x['passed'] for x in results) else 1

if __name__=='__main__':
    try:sys.exit(main())
    except ImportError as exc:print('SKIP: dependência Qt ausente:',exc,file=sys.stderr);sys.exit(77)
    except (OSError,ValueError,RuntimeError) as exc:print('ERRO:',exc,file=sys.stderr);sys.exit(1)
