#!/usr/bin/env python3
# SPDX-FileCopyrightText: 2026 mrmmx31
# SPDX-License-Identifier: GPL-3.0-or-later
"""Real Qt Widgets gallery, isolated from the user's Kvantum configuration."""
from __future__ import annotations
import argparse
import importlib.util
import json
import os
from pathlib import Path
import shutil
import sys
import tempfile


def main():
    p=argparse.ArgumentParser(description=__doc__)
    p.add_argument('--tema',choices=('IrixClassic','Irixium'),default='IrixClassic')
    p.add_argument('--fonte-px',type=int,choices=range(10,21),default=14)
    p.add_argument('--captura',help='PNG da janela real; usa o backend offscreen')
    args=p.parse_args()
    if importlib.util.find_spec('PyQt6') is None and importlib.util.find_spec('PySide6') is None:
        print('Executor ausente: é necessário PyQt6 ou PySide6 para esta galeria opcional. Nenhum pacote foi instalado.',file=sys.stderr)
        return 77
    source=Path(__file__).resolve().parent.parent/args.tema
    if not (source/(args.tema+'.svg')).is_file():
        print('Tema não encontrado no checkout: '+args.tema,file=sys.stderr);return 1
    with tempfile.TemporaryDirectory(prefix='irix-kvantum-preview-') as tmp:
        config=Path(tmp)
        dest=config/'Kvantum'/args.tema
        dest.mkdir(parents=True)
        for ext in ('svg','kvconfig'):
            shutil.copyfile(source/(args.tema+'.'+ext),dest/(args.tema+'.'+ext))
        (config/'Kvantum/kvantum.kvconfig').write_text('[General]\ntheme='+args.tema+'\n')
        # Child process only; no setting is written in the real configuration.
        os.environ['XDG_CONFIG_HOME']=str(config)
        os.environ['QT_STYLE_OVERRIDE']='kvantum'
        if args.captura: os.environ['QT_QPA_PLATFORM']='offscreen'
        if importlib.util.find_spec('PyQt6'):
            from PyQt6 import QtWidgets as W, QtGui as G, QtCore as C
        else:
            from PySide6 import QtWidgets as W, QtGui as G, QtCore as C
        app=W.QApplication([sys.argv[0]])
        app.setApplicationName('IrixClassicPreview')
        style=W.QStyleFactory.create('kvantum')
        if style is None:
            print('O plugin Kvantum para Qt 6 não carregou; não será exibido Fusion como se fosse Kvantum.',file=sys.stderr)
            return 77
        app.setStyle(style)
        font=G.QFont('Nimbus Sans'); font.setPixelSize(args.fonte_px); app.setFont(font)
        window=W.QMainWindow(); window.setWindowTitle(args.tema+' — galeria Qt Widgets isolada')
        menu=window.menuBar().addMenu('&Arquivo')
        menu.addAction('&Novo'); disabled=menu.addAction('Ação indisponível');disabled.setEnabled(False)
        menu.addSeparator(); menu.addAction('&Sair',window.close)
        settings=window.menuBar().addMenu('&Opções'); act=settings.addAction('Selecionado');act.setCheckable(True);act.setChecked(True)
        toolbar=window.addToolBar('Ferramentas');toolbar.setMovable(True)
        toolbar.addAction('Novo');toolbar.addAction('Abrir');toolbar.addSeparator()
        toggle=toolbar.addAction('Fixar');toggle.setCheckable(True)
        central=W.QWidget();window.setCentralWidget(central);layout=W.QVBoxLayout(central)
        info=W.QLabel('Repouso, pressão, foco, selecionado e indisponível. Tab navega entre os controles.');layout.addWidget(info)
        row=W.QHBoxLayout();layout.addLayout(row)
        normal=W.QPushButton('Aplicar');row.addWidget(normal)
        default=W.QPushButton('Padrão');default.setDefault(True);row.addWidget(default)
        checked=W.QPushButton('Selecionado');checked.setCheckable(True);checked.setChecked(True);row.addWidget(checked)
        off=W.QPushButton('Indisponível');off.setEnabled(False);row.addWidget(off)
        form=W.QFormLayout();layout.addLayout(form)
        entry=W.QLineEdit('Entrada de texto');form.addRow('Nome:',entry)
        combo=W.QComboBox();combo.addItems(['Primeira opção','Segunda opção','Terceira opção']);form.addRow('Opção:',combo)
        spin=W.QSpinBox();spin.setValue(42);form.addRow('Quantidade:',spin)
        options=W.QHBoxLayout();layout.addLayout(options)
        for text,state in [('Desmarcado',0),('Marcado',2),('Parcial',1)]:
            box=W.QCheckBox(text);box.setTristate(True);box.setCheckState(C.Qt.CheckState(state));options.addWidget(box)
        disabledcheck=W.QCheckBox('Desativado');disabledcheck.setChecked(True);disabledcheck.setEnabled(False);options.addWidget(disabledcheck)
        radios=W.QHBoxLayout();layout.addLayout(radios)
        for i in range(3):
            radio=W.QRadioButton('Alternativa '+str(i+1));radio.setChecked(i==0);radio.setEnabled(i!=2);radios.addWidget(radio)
        tabs=W.QTabWidget();layout.addWidget(tabs)
        split=W.QSplitter();tree=W.QTreeWidget();tree.setHeaderLabels(['Recurso','Estado'])
        for i in range(25):
            item=W.QTreeWidgetItem(tree,['Item '+str(i+1),'Disponível'])
            if i<4: W.QTreeWidgetItem(item,['Subitem','Detalhes'])
        tree.expandToDepth(0)
        text=W.QTextEdit();text.setPlainText(('Área de visualização\n\nTexto longo para testar rolagem e seleção.\n')*30)
        split.addWidget(tree);split.addWidget(text);tabs.addTab(split,'Controles')
        tabs.addTab(W.QLabel('As abas retangulares são uma adaptação declarada.'),'Segunda aba')
        slider=W.QSlider(C.Qt.Orientation.Horizontal);slider.setValue(42);layout.addWidget(slider)
        progress=W.QProgressBar();progress.setValue(42);layout.addWidget(progress)
        slider.valueChanged.connect(progress.setValue)
        window.resize(820,660);window.show();app.processEvents()
        infofont=G.QFontInfo(font)
        metrics={'qt':C.qVersion(),'style':app.style().metaObject().className(),'theme':args.tema,
                 'font_family_resolved':infofont.family(),'font_pixels':infofont.pixelSize(),
                 'button_height':normal.sizeHint().height(),'menubar_height':window.menuBar().sizeHint().height(),
                 'toolbar_height':toolbar.sizeHint().height(),'tabs_height':tabs.tabBar().sizeHint().height(),
                 'scrollbar_extent':style.pixelMetric(W.QStyle.PixelMetric.PM_ScrollBarExtent)}
        print(json.dumps(metrics,ensure_ascii=False,indent=2))
        if args.captura:
            out=Path(args.captura).expanduser().absolute();out.parent.mkdir(parents=True,exist_ok=True)
            if not window.grab().save(str(out),'PNG'): return 1
            print('Captura real gravada:',out);return 0
        return app.exec()

if __name__=='__main__': sys.exit(main())
