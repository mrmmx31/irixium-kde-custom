#!/usr/bin/env python3
# SPDX-License-Identifier: GPL-3.0-or-later
"""Real Qt pointer/key input; isolated models exercise inherited task contracts.

This is a UI/contract proof, not a native PulseAudio/SmartLauncher/compositor
claim. Its HOME, config and cache are disposable workspace directories.
"""
import argparse
import hashlib
import json
import os
from pathlib import Path
import sys
import tempfile

sys.dont_write_bytecode=True
REPO=Path(__file__).resolve().parents[2]

def main():
    parser=argparse.ArgumentParser(description=__doc__);parser.add_argument('--saida',type=Path,required=True)
    output=parser.parse_args().saida.resolve()
    if output.exists():parser.error('Use a new evidence directory')
    output.mkdir(mode=0o700);config=Path(os.environ.get('XDG_CONFIG_HOME',str(Path.home()/'.config')))
    def hashes():return {name:hashlib.sha256((config/name).read_bytes()).hexdigest() if (config/name).is_file() else None for name in ('kdeglobals','kwinrc','plasmarc','plasma-org.kde.plasma.desktop-appletsrc')}
    before=hashes();checks={};errors=[];failure=None
    with tempfile.TemporaryDirectory(prefix='.qa-task-resources-',dir=REPO) as folder:
        root=Path(folder)
        for key,name in (('HOME','home'),('XDG_CONFIG_HOME','config'),('XDG_DATA_HOME','data'),('XDG_CACHE_HOME','cache'),('XDG_RUNTIME_DIR','runtime')):
            p=root/name;p.mkdir(mode=0o700);os.environ[key]=str(p)
        for key in ('DISPLAY','WAYLAND_DISPLAY','LD_PRELOAD','QT_STYLE_OVERRIDE','QML_IMPORT_PATH','QML2_IMPORT_PATH'):os.environ.pop(key,None)
        os.environ.update(QT_QPA_PLATFORM='offscreen',QT_QUICK_BACKEND='software',QT_QPA_PLATFORMTHEME='generic',QT_QUICK_CONTROLS_STYLE='Basic',QML_DISABLE_DISK_CACHE='1',XDG_CURRENT_DESKTOP='NONE',XDG_DATA_DIRS='/usr/share:/usr/local/share',DBUS_SESSION_BUS_ADDRESS='unix:path='+str(root/'disabled-session'),DBUS_SYSTEM_BUS_ADDRESS='unix:path='+str(root/'disabled-system'))
        from PyQt6 import sip
        from PyQt6.QtCore import QObject,Qt,QUrl,QPointF,QPoint,QMetaObject,Q_ARG,Q_RETURN_ARG
        from PyQt6.QtGui import QGuiApplication,QWheelEvent
        from PyQt6.QtQml import QQmlApplicationEngine
        from PyQt6.QtQuick import QQuickWindow
        from PyQt6.QtTest import QTest
        app=QGuiApplication([]);engine=QQmlApplicationEngine();engine.warnings.connect(lambda messages:errors.extend(message.toString() for message in messages))
        engine.load(QUrl.fromLocalFile(str(REPO/'plasma/tests/DomainOSTaskResourcesPreview.qml')))
        def gate(name,value):
            checks[name]=bool(value)
            if not value:raise AssertionError(name)
        try:
            gate('production_resources_fixture_loads',bool(engine.rootObjects()))
            window=sip.cast(engine.rootObjects()[0],QQuickWindow)
            def settle():app.processEvents();QTest.qWait(30);app.processEvents()
            def call(name,*args):
                r=QMetaObject.invokeMethod(window,name,Qt.ConnectionType.DirectConnection,Q_RETURN_ARG('QVariant'),*(Q_ARG('QVariant',arg) for arg in args));settle();return r
            def state():return json.loads(call('snapshot'))
            def descendants(item):
                yield item
                for child in item.childItems():yield from descendants(child)
            def find(name):
                item=next((item for item in descendants(window.contentItem()) if item.objectName()==name),None)
                if not item:raise AssertionError('Missing '+name)
                return item
            def point(item):return item.mapToScene(QPointF(item.width()/2,item.height()/2)).toPoint()
            def wheel(name,angle):
                item=find(name);p=point(item);event=QWheelEvent(QPointF(p),QPointF(window.mapToGlobal(p)),QPoint(),QPoint(0,angle),Qt.MouseButton.NoButton,Qt.KeyboardModifier.NoModifier,Qt.ScrollPhase.NoScrollPhase,False)
                app.sendEvent(window,event);settle()
            def requests():return state()['requests']
            call('prepare',False);settle()
            wheel('domainosLiveTask_window:1',-60)
            gate('half_wheel_step_neither_pages_nor_activates',state()['firstVisible']==0 and not requests())
            wheel('domainosLiveTask_window:1',-60)
            gate('default_wheel_pages_without_activating',state()['firstVisible']==7 and not requests())
            wheel('domainosLiveTask_window:8',120)
            gate('default_wheel_returns_previous_page_without_window_action',state()['firstVisible']==0 and not requests())
            call('setWheelActivation',True)
            call('seedNoActive')
            wheel('domainosLiveTask_window:1',-120)
            gate('activation_without_active_window_chooses_first',requests()[-1]['ids']==[1])
            call('mutate',1,'active',False);call('mutate',9,'active',True)
            wheel('domainosLiveTask_window:1',-120)
            gate('activation_wheel_wraps_last_to_first',requests()[-1]['ids']==[1])
            call('mutate',9,'active',False);call('mutate',1,'active',True)
            wheel('domainosLiveTask_window:1',120)
            gate('activation_wheel_wraps_first_to_last',requests()[-1]['ids']==[9])
            call('prepare',True);call('setWheelActivation',True)
            wheel('domainosLiveTask_group:terminal',-120)
            gate('group_wheel_restricts_members_and_skips_minimized',requests()[-1]['ids']==[3])
            call('prepare',False)
            item=find('domainosLiveTask_window:1');item.forceActiveFocus()
            QTest.keyClick(window,Qt.Key.Key_Right,Qt.KeyboardModifier.ControlModifier|Qt.KeyboardModifier.ShiftModifier);settle()
            gate('control_shift_right_reorders_without_window_action',state()['rows'][1]['key']=='window:1' and requests()[-1]['action']=='reorder' and all(r['action']=='reorder' for r in requests()))
            item=find('domainosLiveTask_window:1');item.forceActiveFocus()
            QTest.keyClick(window,Qt.Key.Key_Left,Qt.KeyboardModifier.ControlModifier|Qt.KeyboardModifier.ShiftModifier);settle()
            gate('control_shift_left_restores_order',state()['rows'][0]['key']=='window:1')
            call('prepare',False);call('mutate',6,'demandsAttention',True)
            gate('native_attention_role_reaches_controller',state()['attention'] and find('domainosLiveTask_window:6').property('demandsAttention'))
            call('setStatuses','window:6')
            item=find('domainosLiveTask_window:6')
            gate('smart_launcher_progress_and_count_use_existing_icon',find(item.objectName()+'Progress').isVisible() and find(item.objectName()+'Count').isVisible() and item.width()==66 and item.height()==98)
            audio=find(item.objectName()+'Audio');QTest.mouseClick(window,Qt.MouseButton.LeftButton,Qt.KeyboardModifier.NoModifier,point(audio));settle()
            gate('audio_click_mutes_all_streams_without_selecting_task',item.property('muted') and not state()['selected'])
            QTest.mouseClick(window,Qt.MouseButton.LeftButton,Qt.KeyboardModifier.NoModifier,point(audio));settle()
            gate('audio_click_unmutes_every_stream',not item.property('muted'))
            gate('status_capture_saved',window.grabWindow().save(str(output/'TASK-STATUS.png')))
            call('prepare',False)
            for key,active,minimized,expected in ((1,True,False,'toggleMinimized'),(2,False,True,'activate'),(6,False,False,'activate')):
                call('mutate',key,'active',active);call('mutate',key,'minimized',minimized)
                item=find('domainosLiveTask_window:'+str(key));QTest.mouseDClick(window,Qt.MouseButton.LeftButton,Qt.KeyboardModifier.NoModifier,point(item));settle()
                gate('double_click_state_'+str(key),requests()[-1]['action']==expected and requests()[-1]['ids']==[key])
            gate('qml_diagnostics_zero',not errors)
        except Exception as error:failure=str(error)
        finally:
            # Destroy Qt providers while their private profile still exists;
            # deferred destruction after TemporaryDirectory can recreate cache.
            sip.delete(engine)
            sip.delete(app)
    checks['real_profiles_unchanged']=before==hashes()
    report={'status':'passed' if not failure and all(checks.values()) else 'failed','checks':checks,'failure':failure,'qml_diagnostics':errors,'scope':__doc__,'protected_config_sha256':{'before':before,'after':hashes()}}
    (output/'RESULTADO.json').write_text(json.dumps(report,indent=2,ensure_ascii=False)+'\n');print(json.dumps({'status':report['status'],'checks':len(checks),'failure':failure,'report':str(output/'RESULTADO.json')}))
    return 0 if report['status']=='passed' else 1

if __name__=='__main__':raise SystemExit(main())
