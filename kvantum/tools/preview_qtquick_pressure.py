#!/usr/bin/env python3
# SPDX-FileCopyrightText: 2026 mrmmx31
# SPDX-License-Identifier: GPL-3.0-or-later
"""Test the real KDE StyleItem on a temporary on-disk or corrected ScrollBar.

No system writes. --original means use the file currently on disk without
patching, not necessarily upstream if a system repair was already applied.
The session platform is retained unless --offscreen is explicitly requested.
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
sys.path.insert(0,str(Path(__file__).resolve().parents[2]/'tools'))
from qtquick_scrollbar_fix import discover,patch_scrollbar,Failure,MARKER

# KQuickStyleItem 6.13 supports hitTest("up"/"down" result), but does NOT
# support subControlRect("up"/"down") for a scrollbar. Never guess its metrics.
INSTRUMENT = '''
    property int irixProbeTick: 0
    property string irixProbeJSON: {
        irixProbeTick;
        return JSON.stringify({position:position, pressed:pressed,
            sunken:style.sunken, mousePressed:mouseArea.pressed,
            activeControl:style.activeControl});
    }
    property string irixProbeGeometry: {
        width; height; style.width; style.height;
        const vertical = orientation === Qt.Vertical;
        const length = Math.min(2048, Math.floor(vertical ? height : width));
        const cross = Math.floor((vertical ? width : height) / 2);
        function point(target) {
            let first=-1, last=-1;
            for (let i=0; i<length; ++i) {
                const hit = vertical ? style.hitTest(cross,i) : style.hitTest(i,cross);
                if (hit === target) { if (first<0) first=i; last=i; }
                else if (first>=0) break;
            }
            if (first<0) return null;
            const c = Math.floor((first+last)/2);
            return {x:vertical ? cross : c, y:vertical ? c : cross};
        }
        return JSON.stringify({up:point("up"), down:point("down")});
    }
'''
SCENE = '''import QtQuick
Rectangle {
    width: 560; height: 360; color: "#c1c1c1"
    Text { x:20; y:15; text:"Setas: pressione e segure; compare posição e relevo."; color:"black" }
    Text { x:65; y:95; width:450; wrapMode: Text.Wrap; color:"black"
           text:"Módulo KDE real; fonte temporária. Nenhuma configuração global é alterada." }
    ProbeScrollBar { objectName:"vertical"; x:24; y:55; width:18; height:230
                    orientation: Qt.Vertical; size:0.3; position:0.35; active:true }
    ProbeScrollBar { objectName:"horizontal"; x:65; y:285; width:445; height:18
                    orientation: Qt.Horizontal; size:0.3; position:0.35; active:true }
}'''


def instrument(qml: str) -> str:
    anchor='    id: controlRoot\n'
    if qml.count(anchor)!=1:
        raise Failure('Componente sem ponto único para instrumentação.')
    return qml.replace(anchor,anchor+INSTRUMENT,1)


def main(argv=None):
    p=argparse.ArgumentParser(description=__doc__)
    p.add_argument('--testar',action='store_true')
    p.add_argument('--original',action='store_true')
    p.add_argument('--estilo',choices=('Fusion','Breeze','kvantum'),default='kvantum')
    p.add_argument('--offscreen',action='store_true')
    p.add_argument('--qml-file',type=Path)
    p.add_argument('--capturas',type=Path)
    a=p.parse_args(argv)
    binding=next((m for m in ('PyQt6','PySide6') if importlib.util.find_spec(m)),None)
    if not binding:
        print('SKIP: Qt Quick/Python 6 ausente. Ensaio nativo não executado.',file=sys.stderr);return 77
    file=discover(a.qml_file);raw=file.read_bytes()
    qml=instrument((raw if a.original else patch_scrollbar(raw)).decode('utf-8'))
    theme=Path(__file__).resolve().parents[1]/'IrixClassic'
    folder=a.capturas.expanduser().absolute() if a.capturas else None
    if folder:
        if folder.exists() and (not folder.is_dir() or any(folder.iterdir())):
            raise Failure('Escolha uma pasta de capturas nova ou vazia.')
        folder.mkdir(parents=True,exist_ok=True)
    with tempfile.TemporaryDirectory(prefix='irixclassic-qqc-probe-') as tmp:
        root=Path(tmp);config=root/'config';dest=config/'Kvantum/IrixClassic';dest.mkdir(parents=True)
        for ext in ('svg','kvconfig'):
            shutil.copyfile(theme/('IrixClassic.'+ext),dest/('IrixClassic.'+ext))
        (config/'Kvantum/kvantum.kvconfig').write_text('[General]\ntheme=IrixClassic\n')
        (config/'kdeglobals').write_text('[KDE]\nwidgetStyle='+a.estilo+'\n')
        (root/'ProbeScrollBar.qml').write_text(qml)
        scene=root/'Scene.qml';scene.write_text(SCENE)
        os.environ['XDG_CONFIG_HOME']=str(config)
        os.environ['QT_STYLE_OVERRIDE']=a.estilo
        if a.offscreen:
            os.environ['QT_QPA_PLATFORM']='offscreen'
            os.environ['QT_QUICK_BACKEND']='software'
        C=importlib.import_module(binding+'.QtCore');Q=importlib.import_module(binding+'.QtQuick')
        W=importlib.import_module(binding+'.QtWidgets');T=importlib.import_module(binding+'.QtTest')
        app=W.QApplication(['irixclassic-qqc-probe']);style=W.QStyleFactory.create(a.estilo)
        if style is None:
            print('SKIP: estilo '+a.estilo+' ausente para este Qt.',file=sys.stderr);return 77
        app.setStyle(style);view=Q.QQuickView()
        view.setTitle('Qt Quick — '+a.estilo+(' / fonte do disco' if a.original else ' / reparo temporário'))
        view.setSource(C.QUrl.fromLocalFile(str(scene)))
        if view.status()==Q.QQuickView.Status.Error:
            errors='\n'.join(e.toString() for e in view.errors())
            if 'is not installed' in errors or 'plugin cannot be loaded' in errors:
                print('SKIP: dependência KDE/Qt Quick ausente:\n'+errors,file=sys.stderr);return 77
            raise Failure('Erro QML: '+errors)
        view.show();app.processEvents();T.QTest.qWait(200)
        if not a.testar:return app.exec()
        checks=[];tick=0
        for name in ('vertical','horizontal'):
            bar=view.rootObject().findChild(C.QObject,name)
            if bar is None:raise Failure('Controle de ensaio não carregado.')
            geometry=json.loads(bar.property('irixProbeGeometry'))
            def sample():
                nonlocal tick
                tick+=1;bar.setProperty('irixProbeTick',tick);app.processEvents()
                return json.loads(bar.property('irixProbeJSON'))
            for key,sign in (('up',-1),('down',1)):
                pt=geometry.get(key)
                if pt is None:
                    checks.append({'orientation':name,'arrow':key,'status':'not_available'});continue
                bar.setProperty('position',0.35);app.processEvents()
                point=C.QPoint(round(bar.property('x')+pt['x']),round(bar.property('y')+pt['y']))
                T.QTest.mouseMove(view,point);T.QTest.qWait(250);before=sample()
                left=C.Qt.MouseButton.LeftButton;mods=C.Qt.KeyboardModifier.NoModifier
                try:
                    T.QTest.mousePress(view,left,mods,point);app.processEvents();T.QTest.qWait(40)
                    held=sample()
                    if folder and not view.grabWindow().save(str(folder/(name+'-'+key+'-pressionado.png'))):
                        raise Failure('Falha ao capturar janela de ensaio.')
                finally:
                    T.QTest.mouseRelease(view,left,mods,point);app.processEvents()
                T.QTest.qWait(40);released=sample()
                check={'orientation':name,'arrow':key,'before':before,'held':held,'released':released,
                       'motion_ok':sign*(held['position']-before['position'])>0,
                       'held_sunken':bool(held['sunken']),'released_sunken':bool(released['sunken'])}
                check['passed']=check['motion_ok'] and check['held_sunken'] and not check['released_sunken']
                checks.append(check)
        report={'qt':C.qVersion(),'binding':binding,'platform':app.platformName(),'style':a.estilo,
                'source':file.name,'on_disk_already_patched':MARKER.encode() in raw,
                'temporary_fix':not a.original,'checks':checks,
                'note':'Tests local URL loading, not resolution of installed qmldir/prefer.'}
        print(json.dumps(report,indent=2,ensure_ascii=False))
        if folder:(folder/'RESULTADO-QTQUICK.json').write_text(json.dumps(report,indent=2)+'\n')
        view.close();app.processEvents()
        available=[c for c in checks if 'passed' in c]
        return 77 if not available else 0 if all(c['passed'] for c in available) else 1

if __name__=='__main__':
    try:sys.exit(main())
    except ImportError as exc:
        print('SKIP: dependência Qt ausente:',exc,file=sys.stderr);sys.exit(77)
    except (Failure,OSError,ValueError,RuntimeError) as exc:
        print('ERRO:',exc,file=sys.stderr);sys.exit(1)
