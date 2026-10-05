# SPDX-FileCopyrightText: 2026 mrmmx31
# SPDX-License-Identifier: GPL-3.0-or-later
"""One live Qt Quick harness for all three loading paths. No system writes.

The unmodified source file is copied byte-for-byte. The optional input patch is
only applied when mode='temporary_fix'; installed imports follow Qt resolution.
"""
from __future__ import annotations
import hashlib
import importlib
import importlib.util
import json
import os
from pathlib import Path
import shutil
import sys
import tempfile
from arrow_probe_logic import HARNESS_VERSION, judge, summarize, exit_code

ROOT=Path(__file__).resolve().parents[1]
MODES=('installed','file','temporary_fix')


def scene_text(mode):
    if mode not in MODES:raise ValueError('Modo Qt Quick desconhecido.')
    text=(ROOT/'tests/qml/ProbeScrollbars.qml').read_text('utf-8')
    anchor=': ScrollBar { // PROBE_BAR_TYPE'
    if text.count(anchor)!=2:raise ValueError('Cenário deve conter exatamente duas barras registradas.')
    if mode!='installed':text=text.replace(anchor,': ProbeScrollBar { // PROBE_BAR_TYPE')
    return text


def make_private_folder(folder):
    folder=folder.expanduser().absolute()
    for p in (folder,*folder.parents):
        if p.is_symlink():raise ValueError('Saída com link simbólico recusada.')
    if folder.exists() and (not folder.is_dir() or any(folder.iterdir())):
        raise ValueError('Saída deve ser diretório novo ou vazio.')
    folder.mkdir(parents=True,mode=0o700,exist_ok=True)
    return folder


def qimage_digest(image,C):
    if image.isNull():return None
    buf=C.QBuffer();buf.open(C.QIODevice.OpenModeFlag.WriteOnly)
    if not image.save(buf,'PNG'):return None
    return hashlib.sha256(bytes(buf.data())).hexdigest()


def run_quick(mode,stylename='kvantum',manual=False,qml_file=None,offscreen=False,captures=None):
    binding=next((b for b in ('PyQt6','PySide6') if importlib.util.find_spec(b)),None)
    if not binding:return {'status':'skipped','reason':'PyQt6/PySide6 missing','harness_version':HARNESS_VERSION},77
    C=importlib.import_module(binding+'.QtCore');W=importlib.import_module(binding+'.QtWidgets')
    Q=importlib.import_module(binding+'.QtQuick');T=importlib.import_module(binding+'.QtTest')
    text=scene_text(mode);raw=None;file=None;patched=False
    if mode!='installed':
        sys.path.insert(0,str(ROOT.parent/'tools'))
        from qtquick_scrollbar_fix import discover,patch_scrollbar,MARKER
        file=discover(qml_file);raw=file.read_bytes();patched=MARKER.encode() in raw
    folder=make_private_folder(captures) if captures else None
    with tempfile.TemporaryDirectory(prefix='irix-arrow-runtime-') as tmp:
        root=Path(tmp);config=root/'config';dest=config/'Kvantum/IrixClassic';dest.mkdir(parents=True)
        for ext in ('svg','kvconfig'):shutil.copyfile(ROOT/'IrixClassic'/('IrixClassic.'+ext),dest/('IrixClassic.'+ext))
        (config/'Kvantum/kvantum.kvconfig').write_text('[General]\ntheme=IrixClassic\n',encoding='utf-8')
        (config/'kdeglobals').write_text('[KDE]\nwidgetStyle='+stylename+'\n',encoding='utf-8')
        os.environ['XDG_CONFIG_HOME']=str(config);os.environ['QT_STYLE_OVERRIDE']=stylename
        os.environ['QT_QUICK_CONTROLS_STYLE']='org.kde.desktop'
        if offscreen:
            os.environ['QT_QPA_PLATFORM']='offscreen';os.environ['QT_QUICK_BACKEND']='software'
        source=raw if mode=='file' else patch_scrollbar(raw) if mode=='temporary_fix' else None
        if source is not None:(root/'ProbeScrollBar.qml').write_bytes(source)
        shutil.copyfile(ROOT/'tests/qml/ArrowProbe.js',root/'ArrowProbe.js')
        scene=root/'Scene.qml';scene.write_text(text,encoding='utf-8')
        app=W.QApplication(['irix-arrow-runtime']);style=W.QStyleFactory.create(stylename)
        if style is None:return {'status':'skipped','reason':stylename+' style not installed'},77
        app.setStyle(style);view=Q.QQuickView();warnings=[]
        view.engine().warnings.connect(lambda e:warnings.extend(x.toString() for x in e))
        view.setTitle('Setas — '+stylename+' / '+mode);view.setSource(C.QUrl.fromLocalFile(str(scene)))
        if view.status()==Q.QQuickView.Status.Error:
            errors=[x.toString() for x in view.errors()]
            absent=any('is not installed' in x or 'plugin cannot be loaded' in x for x in errors)
            return {'status':'skipped' if absent else 'qml_error','errors':errors},77 if absent else 1
        view.show();app.processEvents()
        exposed=T.QTest.qWaitForWindowExposed(view,3000)
        if not exposed and not offscreen:
            view.close();return {'status':'inconclusive','reason':'test window not exposed'},2
        T.QTest.qWait(400);obj=view.rootObject()
        if manual:
            code=app.exec();return {'status':'manual_closed','mode':mode},code
        tick=0;checks=[]
        def invoke(name):
            C.QMetaObject.invokeMethod(obj,name,C.Qt.ConnectionType.DirectConnection)
        def sample(name,key):
            nonlocal tick
            obj.setProperty('probeName',name);obj.setProperty('probeArrow',key)
            tick+=1;obj.setProperty('sampleTick',tick)
            app.processEvents()
            return json.loads(obj.property('diagnostic'))
        def pixels(bounds):
            image=view.grabWindow()
            if image.isNull():return None
            sx,sy=image.width()/view.width(),image.height()/view.height()
            crop=C.QRect(round(bounds['x']*sx),round(bounds['y']*sy),
                         max(1,round(bounds['width']*sx)),max(1,round(bounds['height']*sy)))
            return qimage_digest(image.copy(crop),C)
        left=C.Qt.MouseButton.LeftButton;mods=C.Qt.KeyboardModifier.NoModifier
        for name in ('vertical','horizontal'):
            for key in ('up','down'):
                invoke('resetProbe');app.processEvents();T.QTest.qWait(100)
                obj.setProperty('queryX',-1);obj.setProperty('queryY',-1)
                before=sample(name,key);point=None;geometry=[]
                # The scan is executed anew on every sample, after layout and hover.
                for attempt in range(3):
                    target=before.get('target')
                    if not target:break
                    point=C.QPoint(int(target['x']),int(target['y']))
                    obj.setProperty('queryX',point.x());obj.setProperty('queryY',point.y())
                    T.QTest.mouseMove(view,point);T.QTest.qWait(220)
                    before=sample(name,key);fresh=before.get('target') or {}
                    geometry.append(fresh)
                    if fresh.get('hit')==key and fresh.get('clear') and \
                       fresh.get('x')==point.x() and fresh.get('y')==point.y():break
                    obj.setProperty('queryX',-1);obj.setProperty('queryY',-1)
                    before=sample(name,key)
                target=before.get('target') or {}
                if not target:
                    checks.append({'orientation':name,'arrow':key,'status':'not_available',
                        'reason':'no arrow found by the live native hitTest'});continue
                if not point or target.get('hit')!=key or not target.get('clear') or \
                   target.get('x')!=point.x() or target.get('y')!=point.y():
                    checks.append({'orientation':name,'arrow':key,'status':'invalid_target',
                        'valid_target':False,'passed':None,'invalid_reasons':['preflight_not_stable'],
                        'geometry_samples':geometry,'before':before});continue
                unpressed=pixels(target['bounds']);held=None
                try:
                    T.QTest.mousePress(view,left,mods,point);app.processEvents();T.QTest.qWait(40)
                    held=sample(name,key);pressed=pixels(target['bounds'])
                    if folder:
                        path=folder/(mode+'-'+name+'-'+key+'-held.png')
                        if not view.grabWindow().save(str(path)):raise RuntimeError('Falha ao salvar captura da janela de teste.')
                        path.chmod(0o600)
                finally:
                    T.QTest.mouseRelease(view,left,mods,point);app.processEvents()
                T.QTest.qWait(40);released=sample(name,key)
                row=judge(before,held,released,name,key)
                row.update({'geometry_samples':geometry,'arrow_pixel_before_sha256':unpressed,
                    'arrow_pixel_held_sha256':pressed,
                    'arrow_pixels_changed':unpressed!=pressed if unpressed and pressed else None})
                checks.append(row)
        summary=summarize(checks)
        report={'harness_version':HARNESS_VERSION,'qt':C.qVersion(),'binding':binding,
            'platform':app.platformName(),'style':stylename,'style_class':style.metaObject().className(),
            'mode':mode,'source':file.name if file else 'installed org.kde.desktop import',
            'on_disk_already_patched':patched if file else None,'temporary_fix':mode=='temporary_fix',
            'source_sha256':hashlib.sha256(raw).hexdigest() if raw is not None else None,
            'loaded_file_sha256':hashlib.sha256(source).hexdigest() if source is not None else None,
            'checks':checks,'assessment':summary,'status':summary['verdict'],
            'warnings':[s.replace(str(root),'<temporary>').replace(str(Path.home()),'~') for s in warnings],
            'note':'No system file or installed theme changed. Only test-window pixels are hashed; input is synthetic QTest.'}
        if folder:
            path=folder/'RESULTADO-QTQUICK.json';path.write_text(json.dumps(report,ensure_ascii=False,indent=2)+'\n',encoding='utf-8');path.chmod(0o600)
        view.close();app.processEvents()
        return report,exit_code(summary)
