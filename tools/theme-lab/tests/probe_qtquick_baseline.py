# SPDX-License-Identifier: GPL-3.0-or-later
"""Exact pre-hint QML fixture; same guarded main, runtime, palette and menu action."""
import argparse
import hashlib
import json
from pathlib import Path
import sys
sys.path.insert(0,str(Path(__file__).resolve().parents[3]/'plasma/tests/galerias-nativas'))
import qtquick_demo as gallery
gallery.private_guards()
parser=argparse.ArgumentParser();parser.add_argument('--major',type=int,choices=(5,6),required=True)
args=parser.parse_args()
fixture=Path(__file__).parent/'fixtures/qtquick-before-hints.qml'
source=fixture.read_text();assert 'ToolTip' not in source
# Diagnostics only, to satisfy the current proof writer. No visual changes.
gallery.QML_SOURCE=source.replace('property int selectedRow: -1',
                                 'property int selectedRow: -1\n readonly property string nativeHints: "[]"')
from importlib import import_module
W=import_module(f'PyQt{args.major}.QtWidgets');Core=import_module(f'PyQt{args.major}.QtCore')
QTest=import_module(f'PyQt{args.major}.QtTest').QTest
native_exec=W.QApplication.exec

def inspect_exec(app):
    QTest.qWait(400)
    window=next(w for w in app.allWindows() if w.objectName()==f'privateQtQuick{args.major}Window')
    assert app.platformName()=='xcb'
    button=window.findChild(Core.QObject,f'qtquick{args.major}_pressButton')
    point=button.mapToScene(Core.QPointF(button.width()/2,button.height()/2)).toPoint()
    QTest.mouseClick(window,Core.Qt.MouseButton.LeftButton,Core.Qt.KeyboardModifier.NoModifier,point)
    menu=next(o for o in window.findChildren(Core.QObject)
              if o.inherits('QQuickMenu') and o.property('title')=='Native menu')
    Core.QMetaObject.invokeMethod(menu,'open');QTest.qWait(400)
    assert menu.property('visible')
    first=next(o for o in menu.findChildren(Core.QObject)
               if o.inherits('QQuickMenuItem') and o.property('text')=='Record activation')
    point=first.mapToScene(Core.QPointF(first.width()/2,first.height()/2)).toPoint()
    QTest.mouseClick(first.window(),Core.Qt.MouseButton.LeftButton,Core.Qt.KeyboardModifier.NoModifier,point)
    QTest.qWait(400);assert not menu.property('visible')
    output=Path('/home/domainos-test')/f'qtquick{args.major}-proof'
    (output/'HINTS-QA.json').write_text(json.dumps({'status':'passed','baseline':True,
        'fixture_commit':'9a67cc83d763e1e5a910a891dbfc77979fc562d8',
        'fixture_sha256':hashlib.sha256(fixture.read_bytes()).hexdigest(),
        'scope':'historical pre-hint QML, same native production main/guards/menu action; diagnostic nativeHints stub only'}))
    Core.QTimer.singleShot(1100,app.quit)
    return native_exec()

W.QApplication.exec=inspect_exec
raise SystemExit(gallery.main(['--qt-major',str(args.major)]))
