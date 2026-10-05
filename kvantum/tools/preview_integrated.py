#!/usr/bin/env python3
# SPDX-FileCopyrightText: 2026 mrmmx31
# SPDX-License-Identifier: GPL-3.0-or-later
"""One real Qt Widgets gallery for integrated appearance review.

Same layout for IrixClassic and Irixium; temporary theme selection. The screen
and font settings of the desktop are never changed. Optional captures include
only this artificial gallery. No backend override is made implicitly.
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
from arrow_runtime import make_private_folder
ROOT=Path(__file__).resolve().parents[1]


def main(argv=None):
    p=argparse.ArgumentParser(description=__doc__)
    p.add_argument('--tema',choices=('IrixClassic','Irixium'),default='IrixClassic')
    p.add_argument('--fonte-px',type=int,default=14);p.add_argument('--testar',action='store_true')
    p.add_argument('--capturas',type=Path);p.add_argument('--offscreen',action='store_true');a=p.parse_args(argv)
    if not 10<=a.fonte_px<=28:p.error('Fonte entre 10 e 28 pixels.')
    binding=next((b for b in ('PyQt6','PySide6') if importlib.util.find_spec(b)),None)
    if not binding:print('SKIP: bindings Qt 6 ausentes. Galeria nativa não executada.',file=sys.stderr);return 77
    source=ROOT/a.tema
    if not all((source/(a.tema+'.'+ext)).is_file() for ext in ('svg','kvconfig')):
        raise ValueError('Tema não encontrado no checkout: '+a.tema)
    folder=make_private_folder(a.capturas) if a.capturas else None
    with tempfile.TemporaryDirectory(prefix='irix-integrated-gallery-') as temp:
        config=Path(temp);dest=config/'Kvantum'/a.tema;dest.mkdir(parents=True)
        for ext in ('svg','kvconfig'):shutil.copyfile(source/(a.tema+'.'+ext),dest/(a.tema+'.'+ext))
        (config/'Kvantum/kvantum.kvconfig').write_text('[General]\ntheme='+a.tema+'\n',encoding='utf-8')
        (config/'kdeglobals').write_text('[KDE]\nwidgetStyle=kvantum\n',encoding='utf-8')
        os.environ['XDG_CONFIG_HOME']=str(config);os.environ['QT_STYLE_OVERRIDE']='kvantum'
        if a.offscreen:os.environ['QT_QPA_PLATFORM']='offscreen'
        C=importlib.import_module(binding+'.QtCore');G=importlib.import_module(binding+'.QtGui')
        W=importlib.import_module(binding+'.QtWidgets');T=importlib.import_module(binding+'.QtTest')
        app=W.QApplication(['irix-integrated-gallery']);style=W.QStyleFactory.create('kvantum')
        if style is None:print('SKIP: plugin Kvantum Qt 6 ausente; sem substituir por Fusion.',file=sys.stderr);return 77
        app.setStyle(style);font=G.QFont('Nimbus Sans');font.setPixelSize(a.fonte_px);app.setFont(font)
        win=W.QMainWindow();win.setWindowTitle(a.tema+' — revisão integrada / dados artificiais')
        menu=win.menuBar().addMenu('&Arquivo');action=menu.addAction('&Novo');menu.addAction('Ação indisponível').setEnabled(False)
        menu.addSeparator();submenu=menu.addMenu('Su&bmenu');submenu.addAction('Exemplo')
        opts=win.menuBar().addMenu('&Opções');toggle=opts.addAction('Marcação');toggle.setCheckable(True);toggle.setChecked(True)
        toolbar=win.addToolBar('Ferramentas');toolbar.addAction('Novo');toolbar.addSeparator();toolbar.addAction('Abrir')
        central=W.QWidget();win.setCentralWidget(central);main=W.QVBoxLayout(central)
        explanation=W.QLabel('Mesma galeria nos dois temas. Compare o conjunto, não só as primitivas SVG.\n'
            'Tab/Espaço: teclado. Rolagem Qt Quick continua sendo ensaio separado.');explanation.setWordWrap(True);main.addWidget(explanation)
        top=W.QHBoxLayout();main.addLayout(top)
        buttons=W.QGroupBox('Botões');bl=W.QVBoxLayout(buttons);top.addWidget(buttons)
        normal=W.QPushButton('Aplicar');bl.addWidget(normal)
        default=W.QPushButton('Padrão');default.setDefault(True);bl.addWidget(default)
        latched=W.QPushButton('Selecionado');latched.setCheckable(True);latched.setChecked(True);bl.addWidget(latched)
        inactive=W.QPushButton('Indisponível');inactive.setEnabled(False);bl.addWidget(inactive)
        fields=W.QGroupBox('Campos');fl=W.QFormLayout(fields);top.addWidget(fields,2)
        entry=W.QLineEdit('Texto editável');fl.addRow('Nome:',entry)
        readonly=W.QLineEdit('Selecionável, mas somente leitura');readonly.setReadOnly(True);fl.addRow('Leitura:',readonly)
        combo=W.QComboBox();combo.addItems(['Primeira opção','Segunda opção','Terceira opção']);fl.addRow('Escolha:',combo)
        spin=W.QSpinBox();spin.setRange(-5,5);fl.addRow('Número:',spin)
        choices=W.QGroupBox('Seleção');cl=W.QVBoxLayout(choices);top.addWidget(choices)
        check=W.QCheckBox('Marca independente');cl.addWidget(check)
        partial=W.QCheckBox('Estado parcial');partial.setTristate(True);partial.setCheckState(C.Qt.CheckState.PartiallyChecked);cl.addWidget(partial)
        radio1=W.QRadioButton('Alternativa A');radio2=W.QRadioButton('Alternativa B');radio1.setChecked(True)
        group=W.QButtonGroup(win);group.addButton(radio1);group.addButton(radio2);cl.addWidget(radio1);cl.addWidget(radio2)
        unavailable=W.QCheckBox('Indisponível marcado');unavailable.setChecked(True);unavailable.setEnabled(False);cl.addWidget(unavailable)
        tabs=W.QTabWidget();tabs.setTabsClosable(True);main.addWidget(tabs,1)
        split=W.QSplitter(C.Qt.Orientation.Horizontal)
        tree=W.QTreeWidget();tree.setHeaderLabels(['Recurso','Estado']);tree.setSortingEnabled(True)
        for i in range(40):
            node=W.QTreeWidgetItem(tree,[f'Item {i:02}','Disponível'])
            if i<5:W.QTreeWidgetItem(node,['Subitem','Detalhes'])
        tree.expandToDepth(0);tree.setMinimumWidth(280)
        text=W.QTextEdit();text.setPlainText(('Conteúdo artificial para rolar e selecionar.\n'+'Linha longa. '*18+'\n')*30)
        text.setLineWrapMode(W.QTextEdit.LineWrapMode.NoWrap)
        split.addWidget(tree);split.addWidget(text);tabs.addTab(split,'Listas, árvores e rolagem')
        tabs.addTab(W.QLabel('Página de referência para mudar a aba pelo teclado.'),'Segunda página')
        tabs.addTab(W.QLabel('Indisponível'),'Aba indisponível');tabs.setTabEnabled(2,False)
        tabs.tabCloseRequested.connect(lambda i:tabs.removeTab(i) if tabs.count()>1 else None)
        intervals=W.QGroupBox('Intervalos');row=W.QHBoxLayout(intervals);main.addWidget(intervals)
        slider=W.QSlider(C.Qt.Orientation.Horizontal);slider.setRange(0,100);slider.setValue(40)
        slider.setTickPosition(W.QSlider.TickPosition.TicksBelow);slider.setTickInterval(10);row.addWidget(slider,2)
        progress=W.QProgressBar();progress.setValue(40);row.addWidget(progress,2);slider.valueChanged.connect(progress.setValue)
        dial=W.QDial();dial.setRange(0,100);dial.setValue(40);dial.setFixedSize(62,62);dial.setNotchesVisible(True);row.addWidget(dial)
        rtl=W.QCheckBox('RTL');row.addWidget(rtl)
        rtl.toggled.connect(lambda yes:win.setLayoutDirection(C.Qt.LayoutDirection.RightToLeft if yes else C.Qt.LayoutDirection.LeftToRight))
        win.statusBar().showMessage('Nenhum documento pessoal ou configuração global é utilizado.')
        win.resize(1080,760);win.show();app.processEvents();T.QTest.qWait(200)
        resolved=G.QFontInfo(font)
        report={'theme':a.tema,'binding':binding,'qt':C.qVersion(),'platform':app.platformName(),
            'style_class':style.metaObject().className(),'font_family_resolved':resolved.family(),
            'font_pixel_size':resolved.pixelSize(),'device_pixel_ratio':win.devicePixelRatioF(),
            'metrics':{'button_size':[normal.sizeHint().width(),normal.sizeHint().height()],
                'entry_height':entry.sizeHint().height(),'menubar_height':win.menuBar().height(),
                'tabbar_height':tabs.tabBar().height(),
                'scrollbar_extent':style.pixelMetric(W.QStyle.PixelMetric.PM_ScrollBarExtent),
                'splitter_extent':style.pixelMetric(W.QStyle.PixelMetric.PM_SplitterWidth)},'checks':[]}
        def capture(name):
            if folder:
                path=folder/(name+'.png')
                if not win.grab().save(str(path),'PNG'):raise RuntimeError('Falha na captura da galeria.')
                path.chmod(0o600)
        capture('01-conjunto')
        def require(test,label):
            report['checks'].append({'name':label,'passed':bool(test)})
        def click(widget):
            T.QTest.mouseClick(widget,C.Qt.MouseButton.LeftButton);app.processEvents()
        if a.testar:
            T.QTest.mousePress(normal,C.Qt.MouseButton.LeftButton);require(normal.isDown(),'Pressão do botão de comando')
            capture('02-pressionado');T.QTest.mouseRelease(normal,C.Qt.MouseButton.LeftButton);require(not normal.isDown(),'Soltura do botão')
            entry.setFocus();entry.selectAll();T.QTest.keyClicks(entry,'IRIX');require(entry.text()=='IRIX','Campo editável')
            original=readonly.text();readonly.selectAll();T.QTest.keyClicks(readonly,'X');require(readonly.text()==original,'Somente leitura preserva conteúdo')
            readonly.selectAll();require(readonly.selectedText()==original,'Somente leitura permite seleção')
            click(check);require(check.isChecked(),'Marcação do checkbox')
            click(radio2);require(radio2.isChecked() and not radio1.isChecked(),'Exclusividade dos radios')
            require(unavailable.isChecked() and not unavailable.isEnabled(),'Indisponibilidade sem perder a seleção')
            combo.setFocus();T.QTest.keyClick(combo,C.Qt.Key.Key_Down);require(combo.currentIndex()==1,'Combo pelo teclado')
            spin.setValue(5);spin.stepUp();require(spin.value()==5,'Limite da entrada numérica')
            tabs.setCurrentIndex(1);require(tabs.currentIndex()==1,'Mudança de página')
            require(not tabs.isTabEnabled(2),'Aba desativada');tabs.setCurrentIndex(0)
            slider.setFocus();T.QTest.keyClick(slider,C.Qt.Key.Key_Right)
            require(slider.value()==41 and progress.value()==41,'Slider e progresso integrados')
            before=toggle.isChecked();toggle.trigger();require(toggle.isChecked()!=before,'Ação de menu com seleção persistente')
            capture('03-interacao');click(rtl);require(win.layoutDirection()==C.Qt.LayoutDirection.RightToLeft,'Layout RTL');capture('04-rtl')
        if folder:
            path=folder/'METRICAS-INTEGRACAO.json';path.write_text(json.dumps(report,indent=2,ensure_ascii=False)+'\n',encoding='utf-8');path.chmod(0o600)
        print(json.dumps(report,indent=2,ensure_ascii=False))
        if a.testar or folder:
            win.close();return 0 if all(c['passed'] for c in report['checks']) else 1
        return app.exec()

if __name__=='__main__':
    try:sys.exit(main())
    except ImportError as exc:print('SKIP: dependência Qt ausente:',exc,file=sys.stderr);sys.exit(77)
    except (OSError,ValueError,RuntimeError) as exc:print('ERRO:',exc,file=sys.stderr);sys.exit(1)
