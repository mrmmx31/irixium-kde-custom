#!/usr/bin/env python3
# SPDX-License-Identifier: GPL-3.0-or-later
"""Reconstruct an owned native panel and systray inside a private Plasma shell.

Only read-only snapshots and retained evidence use /tmp. Native profiles, runtime,
cache and D-Bus live in a disposable repository directory to avoid /tmp inode
pressure. No real panel/profile or icon package is copied or configured.
"""
import argparse
import ast
import hashlib
import json
import os
from pathlib import Path
import re
import shutil
import subprocess
import sys
import tempfile
import time

sys.dont_write_bytecode=True
REPO=Path(__file__).resolve().parents[2]
sys.path.insert(0,str(REPO/'tools'))
import panel_layout


def digest(path):
    return hashlib.sha256(path.read_bytes()).hexdigest() if path.is_file() else None


def worker(output):
    if os.environ.get('DOMAINOS_PRIVATE_PANEL_LAYOUT')!='1':raise RuntimeError('Private fixture required')
    processes=[];logs=[];report={};checks={}
    def execute(body):
        result=subprocess.run(['gdbus','call','--session','--dest','org.kde.plasmashell','--object-path','/PlasmaShell','--method','org.kde.PlasmaShell.evaluateScript',panel_layout.script(body)],capture_output=True,text=True,timeout=12,check=True)
        return json.loads(ast.literal_eval(result.stdout)[0])
    def snap(panel_id):
        return execute('print(JSON.stringify(layoutPanelSnapshot(panelById('+str(panel_id)+'))));')
    def stable(panel):
        value=json.loads(json.dumps(panel));value.pop('id',None);value['geometry'].pop('length',None)
        def config(node):
            for key in ('PreloadWeight','UserBackgroundHints','DomainOSLayoutToken','SystrayContainmentId'):node['entries'].pop(key,None)
            for child in node['groups'].values():config(child)
        def widget(item):
            item.pop('id',None);item.pop('geometry',None);config(item['config'])
            if 'tray' in item:
                item['tray'].pop('id',None);config(item['tray']['config']);item['tray']['widgets'].sort(key=lambda child:child['type'])
                for child in item['tray']['widgets']:widget(child)
        config(value['config'])
        for item in value['widgets']:widget(item)
        return value
    try:
        for executable in ('kwin_x11','kactivitymanagerd','plasmashell'):
            path=shutil.which(executable) or '/usr/lib/x86_64-linux-gnu/libexec/'+executable
            log=(output/(executable+'.log')).open('w');logs.append(log)
            processes.append(subprocess.Popen([path,*(['--no-respawn'] if executable=='plasmashell' else [])],stdout=log,stderr=subprocess.STDOUT))
            time.sleep(.2)
        for _ in range(100):
            try:
                baseline=execute('print(JSON.stringify(panels().map(layoutPanelSnapshot)));');break
            except (subprocess.SubprocessError,ValueError):time.sleep(.15)
        else:raise RuntimeError('Private Plasma scripting unavailable')
        # D-Bus becomes ready before default providers finish their own startup
        # migrations. Baseline those independent defaults after settling.
        time.sleep(1.5)
        baseline=execute('print(JSON.stringify(panels().map(layoutPanelSnapshot)));')
        report['unrelatedInitial']=baseline
        source=execute('''var p=new Panel();p.screen=0;p.location="top";p.alignment="center";p.lengthMode="custom";p.minimumLength=500;p.maximumLength=500;p.height=64;p.floating=false;
var launch=p.addWidget("org.kde.plasma.quicklaunch");launch.currentConfigGroup=["General"];launch.writeConfig("launcherUrls",["applications:org.kde.konsole.desktop","applications:io.github.mrmmx31.irixclassic.files.desktop"]);launch.writeConfig("maxSectionCount",1);
p.addWidget("org.kde.plasma.systemtray");print(JSON.stringify({id:p.id}));''')
        source_id=source['id'];time.sleep(1)
        # Customize an actual native child before taking the source snapshot.
        execute('''var p=panelById('''+str(source_id)+''');var w=p.widgets().find(w=>w.type==="org.kde.plasma.systemtray");var t=inner(w);var vol=t.widgets().find(w=>w.type==="org.kde.plasma.volume");if(vol){vol.currentConfigGroup=["General"];vol.writeConfig("volumeStep",7);}print(JSON.stringify({ok:true}));''')
        time.sleep(.3);before=snap(source_id);report['source']=before
        checks['native_source_has_quicklaunch_and_inner_tray']=len(before['widgets'])==2 and any('tray' in widget and widget['tray']['widgets'] for widget in before['widgets'])
        token='c1'*16
        created=execute('print(JSON.stringify(createFromSnapshot('+json.dumps(before)+','+json.dumps(token)+')));')
        report['creation']=created;new_id=created['panelId'];time.sleep(1)
        after=snap(new_id);report['recreated']=after
        checks['native_reconstruction_gets_new_panel_id']=new_id!=source_id
        checks['native_reconstruction_preserves_tree_and_geometry']=stable(before)==stable(after)
        checks['source_panel_stays_intact']=stable(before)==stable(snap(source_id))
        old_ids={widget['id'] for widget in before['widgets']}
        for widget in before['widgets']:
            if 'tray' in widget:old_ids.update(child['id'] for child in widget['tray']['widgets'])
        mapped={int(key):value for key,value in created['widgetIds'].items()}
        checks['every_original_widget_has_new_native_id']=set(mapped)==old_ids and all(old!=new for old,new in mapped.items())
        checks['inner_tray_gets_new_native_id']=bool(created['trayIds']) and all(int(old)!=new for old,new in created['trayIds'].items())
        checks['launcher_urls_preserved']=before['widgets'][0]['config']['groups']['General']['entries']['launcherUrls']==after['widgets'][0]['config']['groups']['General']['entries']['launcherUrls']
        duplicate=execute('try{createFromSnapshot('+json.dumps(before)+','+json.dumps(token)+');print(JSON.stringify({refused:false}));}catch(error){print(JSON.stringify({refused:true,error:String(error)}));}')
        checks['same_transaction_cannot_duplicate_panel']=duplicate['refused']
        conflict=json.loads(json.dumps(after));conflict['geometry']['height']+=1
        refused=execute('try{removePanelChecked('+json.dumps(conflict)+','+json.dumps(token)+');print(JSON.stringify({refused:false}));}catch(error){print(JSON.stringify({refused:true,error:String(error)}));}')
        checks['changed_panel_snapshot_refuses_removal']=refused['refused']
        wrong=execute('try{removePanelChecked('+json.dumps(after)+',"'+'ab'*16+'");print(JSON.stringify({refused:false}));}catch(error){print(JSON.stringify({refused:true,error:String(error)}));}')
        checks['wrong_transaction_marker_refuses_removal']=wrong['refused']
        from PyQt6.QtGui import QGuiApplication
        app=QGuiApplication([]);checks['private_native_capture_saved']=app.primaryScreen().grabWindow(0).save(str(output/'RECREATED-NATIVE-PANEL.png'))
        removed=execute('print(JSON.stringify(removePanelChecked('+json.dumps(snap(new_id))+','+json.dumps(token)+')));');report['removed']=removed
        time.sleep(.4)
        ids=execute('print(JSON.stringify(panels().map(p=>p.id)));')
        checks['checked_removal_removes_only_owned_replacement']=new_id not in ids and source_id in ids
        execute('print(JSON.stringify(removePanelChecked('+json.dumps(snap(source_id))+')));')
        time.sleep(.4);remaining=execute('print(JSON.stringify(panels().map(layoutPanelSnapshot)));');report['unrelatedAfter']=remaining
        checks['all_unrelated_private_panels_preserved']={panel['id']:stable(panel) for panel in baseline}=={panel['id']:stable(panel) for panel in remaining}
    except Exception as error:report['failure']=str(error)
    finally:
        for process in reversed(processes):
            if process.poll() is None:
                process.terminate()
                try:process.wait(3)
                except subprocess.TimeoutExpired:process.kill();process.wait()
        for log in logs:log.close()
    report['checks']=checks;(output/'native.json').write_text(json.dumps(report,indent=2)+'\n')
    return 0 if checks and all(checks.values()) and not report.get('failure') else 1


def main():
    parser=argparse.ArgumentParser(description=__doc__);parser.add_argument('--saida',type=Path,required=True);parser.add_argument('--worker',action='store_true',help=argparse.SUPPRESS)
    args=parser.parse_args();output=args.saida.resolve()
    if args.worker:return worker(output)
    if not output.is_relative_to(Path('/tmp')) or output.exists():parser.error('Use a new owned /tmp evidence directory')
    output.mkdir(mode=0o700);env=os.environ.copy();config=Path(env.get('XDG_CONFIG_HOME',str(Path.home()/'.config')))
    protected=lambda:{name:digest(config/name) for name in ('kdeglobals','kwinrc','plasmarc','plasmashellrc','plasma-org.kde.plasma.desktop-appletsrc')}
    before=protected();source=digest(REPO/'tools/panel_layout.py')
    for key in ('DISPLAY','WAYLAND_DISPLAY','WAYLAND_SOCKET','DBUS_SESSION_BUS_ADDRESS','DBUS_STARTER_ADDRESS','DBUS_STARTER_BUS_TYPE','SESSION_MANAGER','LD_PRELOAD','XAUTHORITY','QML_IMPORT_PATH','QML2_IMPORT_PATH','QT_STYLE_OVERRIDE','QT_QUICK_CONTROLS_STYLE','KDE_FULL_SESSION','KDE_SESSION_VERSION','XDG_SESSION_ID'):env.pop(key,None)
    with tempfile.TemporaryDirectory(prefix='.qa-panel-layout-',dir=REPO) as temporary:
        root=Path(temporary)
        for key,name in (('HOME','home'),('XDG_CONFIG_HOME','config'),('XDG_DATA_HOME','data'),('XDG_CACHE_HOME','cache'),('XDG_STATE_HOME','state'),('XDG_RUNTIME_DIR','runtime')):
            folder=root/name;folder.mkdir(mode=0o700);env[key]=str(folder)
        (root/'config/kwinrc').write_text('[Desktops]\nNumber=1\n[Compositing]\nEnabled=false\n')
        bus=root/'bus.conf';bus.write_text('<busconfig><type>session</type><listen>unix:tmpdir='+str(root/'runtime')+'</listen><auth>EXTERNAL</auth><policy context="default"><allow send_destination="*"/><allow receive_sender="*"/><allow own="*"/></policy></busconfig>')
        env.update(QT_QPA_PLATFORM='xcb',QT_QPA_PLATFORMTHEME='generic',QT_QUICK_BACKEND='software',QML_DISABLE_DISK_CACHE='1',QT_SCALE_FACTOR='1',XDG_SESSION_TYPE='x11',XDG_CURRENT_DESKTOP='NONE',XDG_DATA_DIRS='/usr/local/share:/usr/share',XDG_CONFIG_DIRS='/etc/xdg',LANG='C.UTF-8',LC_ALL='C.UTF-8',DBUS_SYSTEM_BUS_ADDRESS='unix:path='+str(root/'no-system-bus'),PULSE_SERVER='unix:'+str(root/'no-audio'),KWIN_COMPOSE='N',LIBGL_ALWAYS_SOFTWARE='1',DOMAINOS_PRIVATE_PANEL_LAYOUT='1')
        result=subprocess.run(['xvfb-run','--auto-servernum','--server-args=-screen 0 1100x750x24','dbus-run-session','--config-file',str(bus),'--',sys.executable,str(Path(__file__).resolve()),'--worker','--saida',str(output)],env=env,capture_output=True,text=True,timeout=45)
        (output/'runner.log').write_text(result.stdout+result.stderr)
    native=json.loads((output/'native.json').read_text()) if (output/'native.json').is_file() else {}
    checks=native.get('checks',{});checks.update(private_host_completed=result.returncode==0 and not native.get('failure'),real_profiles_unchanged=before==protected(),helper_source_unchanged=source==digest(REPO/'tools/panel_layout.py'))
    diagnostics=[line for line in (output/'plasmashell.log').read_text().splitlines() if re.search(r'ReferenceError:|TypeError:|SyntaxError:|Cannot assign|Binding loop|is not a type',line)] if (output/'plasmashell.log').is_file() else []
    report={'status':'passed' if checks and all(checks.values()) else 'failed','checks':checks,'native':native,'qml_diagnostics_retained':diagnostics,'protected_config_sha256':{'before':before,'after':protected()},'scope':'Native helper reconstruction and checked removal on own disposable Plasma/KWin/Xvfb/D-Bus. Old panel, ordered launcher IDs and inner systray provider settings preserved; all recreated IDs are fresh. Personal profiles untouched; workspace cache/runtime removed after daemon termination.'}
    (output/'RESULTADO.json').write_text(json.dumps(report,indent=2,ensure_ascii=False)+'\n');print(json.dumps({'status':report['status'],'checks':len(checks),'failed':[name for name,value in checks.items() if not value],'result':str(output/'RESULTADO.json')}))
    return 0 if report['status']=='passed' else 1


if __name__=='__main__':raise SystemExit(main())
