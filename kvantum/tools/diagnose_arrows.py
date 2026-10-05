#!/usr/bin/env python3
# SPDX-FileCopyrightText: 2026 mrmmx31
# SPDX-License-Identifier: GPL-3.0-or-later
"""Read-only system inventory + isolated cross-style input probes.

No package installation, system patch, global theme selection or mouse remapping.
Qt test events target only synthetic test windows. Reports never contain desktop
screenshots, clipboard contents or the full environment. No --testar means only
read-only inventory. A missing native dependency is not reported as a pass.
"""
from __future__ import annotations
import argparse
import hashlib
import importlib.util
import json
import os
from pathlib import Path
import re
import shutil
import subprocess
import sys
import tempfile

ROOT = Path(__file__).resolve().parents[1]
STYLES = ('Fusion', 'Breeze', 'kvantum')


def clean(text):
    return str(text).replace(str(Path.home()), '~')


def run_info(args):
    try:
        p = subprocess.run(args, text=True, capture_output=True, timeout=8)
        return {'code': p.returncode, 'text': clean((p.stdout+p.stderr).strip())}
    except (OSError, subprocess.TimeoutExpired) as exc:
        return {'unavailable': clean(exc)}


def inspect_qml(text):
    return {
        'sha256': hashlib.sha256(text.encode()).hexdigest(),
        'previous_optional_patch_marker': 'IRIXCLASSIC_QTQUICK_ARROW_PRESS_V1' in text,
        'native_pressed_only': bool(re.search(r'sunken:\s*controlRoot\.pressed\s*\n\s*(?://|minimum:)', text)),
        'sunken_bindings': [x.strip() for x in text.splitlines() if 'sunken:' in x],
        'press_handler_present': 'onPressed:' in text,
        'click_hit_test_present': 'style.activeControl = style.hitTest(mouse.x, mouse.y);' in text,
        'left_button_enabled': 'Qt.LeftButton' in text,
    }


def inventory():
    config = Path(os.environ.get('XDG_CONFIG_HOME', str(Path.home()/'.config')))
    selected = config/'Kvantum/kvantum.kvconfig'
    info = {'kind': 'read_only_inventory', 'session': os.getenv('XDG_SESSION_TYPE',''),
        'environment': {k:clean(os.getenv(k)) for k in (
            'QT_STYLE_OVERRIDE', 'QT_QUICK_CONTROLS_STYLE', 'QML_IMPORT_PATH',
            'QML2_IMPORT_PATH', 'QT_QPA_PLATFORM', 'QT_SCALE_FACTOR') if k in os.environ},
        'packages':run_info(['dpkg-query','-W','-f=${binary:Package} ${Version}\\n',
            'qml6-module-org-kde-desktop','libqt6widgets6','libqt6quick6',
            'qt-style-kvantum','python3-pyqt6','python3-pyside6.qtwidgets']),
        'modules':[], 'qt_binding':next((m for m in ('PyQt6','PySide6') if importlib.util.find_spec(m)),None)}
    if selected.is_file():
        # Only the theme key, not per-app lists or unrelated user configuration.
        match = re.search(r'^theme\s*=\s*(.+)$', selected.read_text(errors='replace'), re.M)
        info['selected_kvantum_theme'] = match.group(1).strip() if match else None
    for base in (Path('/usr/lib'), Path('/usr/lib64')):
        if not base.is_dir(): continue
        for mask in ('qt6/qml/org/kde/desktop/ScrollBar.qml','*/qt6/qml/org/kde/desktop/ScrollBar.qml'):
            for file in base.glob(mask):
                if file.stat().st_size > 200000: continue
                row = {'path':str(file), **inspect_qml(file.read_text(errors='replace'))}
                qmldir = file.parent/'qmldir'
                row['prefer'] = [s for s in qmldir.read_text(errors='replace').splitlines()
                                 if s.startswith('prefer ')] if qmldir.is_file() else []
                row['owner'] = run_info(['dpkg-query','-S',str(file)])
                info['modules'].append(row)
    info['notes'] = ['Identifies on-disk modules; does not prove which copy an already running app loaded.',
        'Failure across styles points to a shared layer; lack of motion and lack of bevel are different observations.']
    return info


def classify(before, during, after, expected_sign):
    delta = during-before
    moved = delta*expected_sign > 0
    return {'motion': 'ok' if moved else 'failed', 'before':before, 'held':during,
            'after_release':after, 'delta':delta}


def qimage_hash(image):
    # Serialize without a binding-specific raw pointer API.
    from importlib import import_module
    binding=next(m for m in ('PyQt6','PySide6') if m+'.QtCore' in sys.modules)
    C=import_module(binding+'.QtCore')
    buf=C.QBuffer();buf.open(C.QIODevice.OpenModeFlag.WriteOnly)
    image.save(buf,'PNG');return hashlib.sha256(bytes(buf.data())).hexdigest()


def native_probe(mode, stylename, manual=False):
    binding = next((m for m in ('PyQt6','PySide6') if importlib.util.find_spec(m)),None)
    if not binding: return {'status':'skipped','reason':'PyQt6/PySide6 missing'},77
    from importlib import import_module
    C=import_module(binding+'.QtCore');W=import_module(binding+'.QtWidgets')
    T=import_module(binding+'.QtTest');G=import_module(binding+'.QtGui')
    # Only this process sees this temporary theme selection.
    with tempfile.TemporaryDirectory(prefix='irix-style-probe-') as tmp:
        config=Path(tmp);dest=config/'Kvantum/IrixClassic';dest.mkdir(parents=True)
        for ext in ('svg','kvconfig'):
            shutil.copyfile(ROOT/'IrixClassic'/('IrixClassic.'+ext),dest/('IrixClassic.'+ext))
        (config/'Kvantum/kvantum.kvconfig').write_text('[General]\ntheme=IrixClassic\n')
        os.environ['XDG_CONFIG_HOME']=str(config)
        os.environ['QT_STYLE_OVERRIDE']=stylename
        os.environ['QT_QUICK_CONTROLS_STYLE']='org.kde.desktop'
        app=W.QApplication(['irix-style-probe']);style=W.QStyleFactory.create(stylename)
        if style is None: return {'status':'skipped','reason':stylename+' style not installed',
                                  'available':W.QStyleFactory.keys()},77
        app.setStyle(style)
        report={'mode':mode,'requested_style':stylename,'style_class':style.metaObject().className(),
                'qt':C.qVersion(),'binding':binding,'platform':app.platformName(),
                'checks':[], 'theme_source':'checkout (temporary selection)',
                'input':'QTest synthetic events in own test windows'}
        if mode=='widgets':
            win=W.QWidget();win.setWindowTitle('Diagnóstico Qt Widgets — '+stylename)
            layout=W.QVBoxLayout(win);label=W.QLabel('Clique nas setas; compare o número e o relevo.');layout.addWidget(label)
            bars={}
            for name,ori in (('vertical',C.Qt.Orientation.Vertical),('horizontal',C.Qt.Orientation.Horizontal)):
                b=W.QScrollBar(ori);b.setRange(0,100);b.setPageStep(15);b.setValue(50)
                b.setObjectName(name)
                if name=='vertical': b.setFixedHeight(250)
                else: b.setMinimumWidth(430)
                b.valueChanged.connect(lambda v, n=name:label.setText(n+': '+str(v)))
                layout.addWidget(b);bars[name]=b
            win.show();app.processEvents();T.QTest.qWait(150)
            if manual:return {'status':'manual_closed','mode':mode},app.exec()
            for name,b in bars.items():
                for direction,sub,sign in (
                    ('subtract',W.QStyle.SubControl.SC_ScrollBarSubLine,-1),
                    ('add',W.QStyle.SubControl.SC_ScrollBarAddLine,1)):
                    b.setValue(50);app.processEvents();opt=W.QStyleOptionSlider();b.initStyleOption(opt)
                    cell=style.subControlRect(W.QStyle.ComplexControl.CC_ScrollBar,opt,sub,b)
                    row={'orientation':name,'direction':direction}
                    if not cell.isValid() or style.hitTestComplexControl(W.QStyle.ComplexControl.CC_ScrollBar,opt,cell.center(),b)!=sub:
                        report['checks'].append({**row,'motion':'not_available','reason':'style has no matching arrow'});continue
                    T.QTest.mouseMove(b,cell.center());T.QTest.qWait(220)
                    a=b.grab().toImage().copy(cell);before=b.value()
                    T.QTest.mousePress(b,C.Qt.MouseButton.LeftButton,C.Qt.KeyboardModifier.NoModifier,cell.center())
                    app.processEvents();T.QTest.qWait(40)
                    during=b.value();pressed=b.grab().toImage().copy(cell)
                    T.QTest.mouseRelease(b,C.Qt.MouseButton.LeftButton,C.Qt.KeyboardModifier.NoModifier,cell.center())
                    app.processEvents()
                    row.update(classify(before,during,b.value(),sign));row['arrow_pixels_changed']=qimage_hash(a)!=qimage_hash(pressed)
                    report['checks'].append(row)
        else:
            Q=import_module(binding+'.QtQml')
            engine=Q.QQmlApplicationEngine();errors=[]
            engine.warnings.connect(lambda e: errors.extend(str(x.toString()) for x in e))
            engine.load(C.QUrl.fromLocalFile(str(ROOT/'tests/qml/ProbeScrollbars.qml')))
            if not engine.rootObjects():
                return {**report,'status':'skipped','reason':'installed org.kde.desktop QML failed to load',
                        'errors':[clean(s) for s in errors]},77
            win=engine.rootObjects()[0];app.processEvents();T.QTest.qWait(350)
            report['qml_import_paths']=[clean(s) for s in engine.importPathList()]
            if manual:return {'status':'manual_closed','mode':mode},app.exec()
            tick=0
            def snapshot(name):
                nonlocal tick
                tick+=1;win.setProperty('probeName',name);win.setProperty('sampleTick',tick);app.processEvents()
                return json.loads(win.property('diagnostic'))
            for name in ('vertical','horizontal'):
                for direction,key,sign in (('subtract','up',-1),('add','down',1)):
                    C.QMetaObject.invokeMethod(win,'resetProbe',C.Qt.ConnectionType.DirectConnection)
                    app.processEvents();T.QTest.qWait(50);s=snapshot(name);cell=s.get(key)
                    row={'orientation':name,'direction':direction}
                    if not cell or cell['width']<=0 or cell['height']<=0:
                        report['checks'].append({**row,'motion':'not_available','reason':'no arrow rectangle/StyleItem'});continue
                    pt=C.QPoint(round(s['x']+cell['x']+cell['width']/2),round(s['y']+cell['y']+cell['height']/2))
                    T.QTest.mouseMove(win,pt);T.QTest.qWait(220);s=snapshot(name)
                    T.QTest.mousePress(win,C.Qt.MouseButton.LeftButton,C.Qt.KeyboardModifier.NoModifier,pt)
                    app.processEvents();T.QTest.qWait(40);held=snapshot(name)
                    T.QTest.mouseRelease(win,C.Qt.MouseButton.LeftButton,C.Qt.KeyboardModifier.NoModifier,pt)
                    app.processEvents();released=snapshot(name)
                    row.update(classify(s['value'],held['value'],released['value'],sign))
                    row.update({'held_states':held,'released_states':released})
                    report['checks'].append(row)
            report['warnings']=[clean(s) for s in errors]
        win.close();app.processEvents()
        tested=[r for r in report['checks'] if r['motion']!='not_available']
        failed=[r for r in tested if r['motion']=='failed']
        # A bevel difference is an observation, not proof of input success/failure.
        report['status']='failed_motion' if failed else 'motion_ok' if tested else 'skipped'
        return report,1 if failed else 0 if tested else 77


def main(argv=None):
    p=argparse.ArgumentParser(description=__doc__)
    p.add_argument('--testar',action='store_true');p.add_argument('--saida',type=Path)
    p.add_argument('--probe',choices=('widgets','quick'));p.add_argument('--style',choices=STYLES,default='Fusion')
    p.add_argument('--manual',action='store_true');a=p.parse_args(argv)
    if a.probe:
        try:result,code=native_probe(a.probe,a.style,a.manual)
        except ImportError as exc:result,code={'status':'skipped','reason':str(exc)},77
        except Exception as exc:result,code={'status':'probe_error','reason':clean(exc)},1
        print(json.dumps(result,ensure_ascii=False,indent=2));return code
    result=inventory();folder=None
    if a.saida:
        folder=a.saida.expanduser().absolute()
        if folder.is_symlink() or (folder.exists() and (not folder.is_dir() or any(folder.iterdir()))):
            p.error('--saida deve ser diretório novo ou vazio; não sobrescrevemos relatórios.')
        folder.mkdir(parents=True,mode=0o700,exist_ok=True)
    if a.testar:
        result['tests']=[]
        for style in STYLES:
            for mode in ('widgets','quick'):
                try:
                    child=subprocess.run([sys.executable,__file__,'--probe',mode,'--style',style],capture_output=True,text=True,timeout=45)
                    try:data=json.loads(child.stdout)
                    except json.JSONDecodeError:data={'status':'probe_error','stdout':clean(child.stdout)}
                    result['tests'].append({'style':style,'mode':mode,'returncode':child.returncode,
                                           'result':data,'stderr':clean(child.stderr)})
                except subprocess.TimeoutExpired:
                    result['tests'].append({'style':style,'mode':mode,'returncode':124,'result':{'status':'timeout'}})
    text=json.dumps(result,indent=2,ensure_ascii=False)+'\n';print(text,end='')
    if folder:
        (folder/'DIAGNOSTICO-SETAS.json').write_text(text)
        (folder/'DIAGNOSTICO-SETAS.json').chmod(0o600)
        print('Relatório:',clean(folder/'DIAGNOSTICO-SETAS.json'),file=sys.stderr)
    if a.testar:
        codes=[r['returncode'] for r in result['tests']]
        return 1 if any(c not in (0,77) for c in codes) else 77 if not any(c==0 for c in codes) else 0
    return 0

if __name__=='__main__':
    try:sys.exit(main())
    except (OSError,ValueError) as exc:print('ERRO:',clean(exc),file=sys.stderr);sys.exit(1)
