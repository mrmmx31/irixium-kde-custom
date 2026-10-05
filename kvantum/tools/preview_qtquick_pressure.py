#!/usr/bin/env python3
# SPDX-FileCopyrightText: 2026 mrmmx31
# SPDX-License-Identifier: GPL-3.0-or-later
"""Probe the actual KDE Qt Quick component using a temporary corrected source.

No files in /usr or in the user's theme selection are modified. --testar checks
that the real StyleItem sees sunken while an accepted arrow press is held.
It deliberately loads a local URL, bypassing the installed qmldir prefer.
"""
import argparse
import importlib.util
import json
import os
from pathlib import Path
import shutil
import sys
import tempfile
sys.path.insert(0,str(Path(__file__).resolve().parents[2]/'tools'))
from qtquick_scrollbar_fix import discover,patch_scrollbar,Failure

def main(argv=None):
    p=argparse.ArgumentParser(description=__doc__)
    p.add_argument('--testar',action='store_true');p.add_argument('--original',action='store_true')
    p.add_argument('--qml-file',type=Path);p.add_argument('--capturas',type=Path);a=p.parse_args(argv)
    binding=next((m for m in ('PyQt6','PySide6') if importlib.util.find_spec(m)),None)
    if not binding:print('Qt Quick/Python 6 ausente: ensaio nativo não executado.',file=sys.stderr);return 77
    file=discover(a.qml_file);raw=file.read_bytes();qml=(raw if a.original else patch_scrollbar(raw)).decode()
    # Instrument only the temporary copy, so the probe can read the actual private StyleItem.
    anchor='    id: controlRoot\n'
    if qml.count(anchor)!=1:raise Failure('Componente sem ponto único para instrumentação.')
    qml=qml.replace(anchor,anchor+'    property alias irixProbeStyle: style\n'
        +'    property rect irixProbeUp: { style.width; style.height; return style.subControlRect("up"); }\n',1)
    theme=Path(__file__).resolve().parents[1]/'IrixClassic'
    with tempfile.TemporaryDirectory(prefix='irixclassic-qqc-probe-') as tmp:
        root=Path(tmp);config=root/'config';dest=config/'Kvantum/IrixClassic';dest.mkdir(parents=True)
        for ext in ('svg','kvconfig'):shutil.copyfile(theme/('IrixClassic.'+ext),dest/('IrixClassic.'+ext))
        (config/'Kvantum/kvantum.kvconfig').write_text('[General]\ntheme=IrixClassic\n')
        local=root/'ProbeScrollBar.qml';local.write_text(qml)
        scene=root/'Scene.qml';scene.write_text('''import QtQuick
Rectangle {
    width: 420; height: 340; color: "#c1c1c1"
    Text { x:20; y:15; text:"Pressione e segure a seta superior."; color:"black" }
    Text { x:65; y:80; width:330; wrapMode: Text.Wrap; color:"black"
           text:"Fonte Qt Quick carregada de uma cópia temporária. Nenhuma configuração da sessão muda." }
    ProbeScrollBar { id: bar; objectName:"probeBar"; x:24; y:55; width:18; height:240
                    orientation: Qt.Vertical; size:0.3; position:0.35; active:true }
}''')
        os.environ['XDG_CONFIG_HOME']=str(config);os.environ['QT_STYLE_OVERRIDE']='kvantum'
        if a.testar:os.environ['QT_QPA_PLATFORM']='offscreen';os.environ['QT_QUICK_BACKEND']='software'
        if binding=='PyQt6':from PyQt6 import QtCore as C,QtQuick as Q,QtWidgets as W,QtTest as T
        else:from PySide6 import QtCore as C,QtQuick as Q,QtWidgets as W,QtTest as T
        app=W.QApplication([sys.argv[0]]);style=W.QStyleFactory.create('kvantum')
        if style is None:print('Plugin Kvantum Qt 6 ausente.',file=sys.stderr);return 77
        app.setStyle(style);view=Q.QQuickView();view.setTitle('IRIX Classic — Qt Quick: pressão das setas')
        view.setSource(C.QUrl.fromLocalFile(str(scene)))
        if view.status()==Q.QQuickView.Status.Error:
            print('\n'.join(e.toString() for e in view.errors()),file=sys.stderr)
            errors='\n'.join(e.toString() for e in view.errors())
            if 'is not installed' in errors or 'plugin cannot be loaded' in errors:
                print('Dependência Qt Quick/KDE ausente; ensaio não executado.',file=sys.stderr);return 77
            raise Failure('Erro de carregamento QML: '+errors)
        view.show();app.processEvents();T.QTest.qWait(200)
        rootitem=view.rootObject();bar=rootitem.findChild(C.QObject,'probeBar')
        if bar is None:raise Failure('Controle de teste não carregado.')
        target=bar.property('irixProbeStyle');rect=bar.property('irixProbeUp')
        if target is None or not rect.isValid():raise Failure('StyleItem/retângulo real da seta não exposto.')
        if not a.testar:return app.exec()
        point=C.QPoint(round(bar.property('x')+rect.center().x()),round(bar.property('y')+rect.center().y()))
        folder=a.capturas.expanduser().absolute() if a.capturas else None
        if folder:folder.mkdir(parents=True,exist_ok=True)
        def grab(name):
            if folder and not view.grabWindow().save(str(folder/(name+'.png'))):raise Failure('Falha ao capturar Qt Quick.')
        T.QTest.mouseMove(view,point);app.processEvents();T.QTest.qWait(200);grab('01-repouso')
        left=C.Qt.MouseButton.LeftButton;mods=C.Qt.KeyboardModifier.NoModifier
        T.QTest.mousePress(view,left,mods,point);app.processEvents();T.QTest.qWait(30)
        held=bool(target.property('sunken'));grab('02-pressionado')
        T.QTest.mouseRelease(view,left,mods,point);app.processEvents();T.QTest.qWait(30)
        released=bool(target.property('sunken'));grab('03-solto')
        report={'qt':C.qVersion(),'binding':binding,'source':file.name,'temporary_fix':not a.original,'held_sunken':held,'released_sunken':released}
        print(json.dumps(report,indent=2))
        if folder:(folder/'RESULTADO-QTQUICK.json').write_text(json.dumps(report,indent=2)+'\n')
        if not held or released:raise Failure('Estado nativo não corresponde à pressão/soltura; resultado não aprovado.')
        return 0
if __name__=='__main__':
    try:sys.exit(main())
    except ImportError as exc:print('Dependência Qt ausente:',exc,file=sys.stderr);sys.exit(77)
    except (Failure,OSError,ValueError,RuntimeError) as exc:print('ERRO:',exc,file=sys.stderr);sys.exit(1)
