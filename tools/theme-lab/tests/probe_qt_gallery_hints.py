#!/usr/bin/python3
# SPDX-License-Identifier: GPL-3.0-or-later
"""Qt hint helper on real widgets, owned Xvfb and a disposable HOME.

This does not bypass or invoke the complete gallery's bwrap guard.
"""
import argparse
import json
import os
from pathlib import Path
import sys
import tempfile

assert os.environ.get('T07_PRIVATE_PROBE')=='1'
parser=argparse.ArgumentParser(description=__doc__)
parser.add_argument('--major',type=int,choices=(5,6),required=True)
args=parser.parse_args()
root=Path(__file__).resolve().parents[3]
sys.path.insert(0,str(root/'plasma/tests/galerias-nativas'))
with tempfile.TemporaryDirectory(prefix='t07-qt-hints-') as private:
    os.environ.update(HOME=private,QT_QPA_PLATFORM='xcb',DBUS_SESSION_BUS_ADDRESS='unix:path='+private+'/absent-bus')
    os.environ.pop('WAYLAND_DISPLAY',None)
    for key,sub in [('XDG_CONFIG_HOME','config'),('XDG_DATA_HOME','data'),('XDG_CACHE_HOME','cache'),
                    ('XDG_STATE_HOME','state'),('XDG_RUNTIME_DIR','runtime')]:
        path=Path(private)/sub;path.mkdir(mode=0o700);os.environ[key]=str(path)
    if args.major==6:
        from PyQt6 import QtWidgets as W
        from PyQt6.QtGui import QAction
    else:
        from PyQt5 import QtWidgets as W
        from PyQt5.QtWidgets import QAction
    from qt_widget_hints import add_gallery_hints
    app=W.QApplication([])
    assert app.platformName()=='xcb'
    window=W.QMainWindow()
    central=W.QWidget();layout=W.QVBoxLayout(central);window.setCentralWidget(central)
    controls=[W.QPushButton('Press'),W.QCheckBox('Check'),W.QRadioButton('Radio'),W.QToolButton(),
              W.QComboBox(),W.QSpinBox(),W.QDoubleSpinBox(),W.QLineEdit('Private text'),
              W.QTextEdit('Private paragraphs'),W.QSlider(),W.QProgressBar(),W.QTableWidget(3,2),
              W.QTabWidget(),W.QScrollArea()]
    controls[4].addItems(['A','B']);controls[5].setRange(-99,999);controls[5].setSingleStep(3)
    controls[6].setRange(-2.5,12.5);controls[6].setSingleStep(.25)
    controls[12].addTab(W.QWidget(),'First')
    controls[0].setToolTip('Explicação existente preservada')
    menu=window.menuBar().addMenu('File');action=QAction('Open',window);menu.addAction(action)
    action.setToolTip('Ação já documentada')
    generic=QAction('&Other',window);menu.addAction(generic)
    hits=[];controls[0].clicked.connect(lambda:hits.append(True))
    for widget in controls:layout.addWidget(widget)
    before=[widget.text() for widget in (controls[7],)]
    text_before=controls[8].toPlainText()
    palette_before=app.palette()
    report=add_gallery_hints(window,W.QWidget,QAction)
    window.show();app.processEvents()
    assert all(widget.toolTip() for widget in controls)
    assert '-99' in controls[5].toolTip() and '999' in controls[5].toolTip() and 'passo 3' in controls[5].toolTip()
    assert '0.25' in controls[6].toolTip()
    assert controls[0].toolTip()=='Explicação existente preservada'
    assert action.toolTip()=='Ação já documentada' and 'Ação do menu' in generic.toolTip()
    assert menu.toolTipsVisible()
    assert 'Cabeçalho' in controls[11].horizontalHeader().toolTip()
    assert [controls[7].text()]==before and controls[8].toPlainText()==text_before
    assert app.palette()==palette_before
    controls[0].click();assert hits==[True]
    window.close();app.processEvents()
    print(json.dumps({'status':'passed','qt_major':args.major,'coverage':report,
        'scope':'real widget helper, menus enabled, dynamic limits, existing tips/text/palette/actions preserved; full guarded gallery and hover not certified'}))
