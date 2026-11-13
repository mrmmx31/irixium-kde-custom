#!/usr/bin/env python3
# SPDX-FileCopyrightText: 2026 IRIX Classic contributors
# SPDX-License-Identifier: GPL-3.0-or-later
"""Measure production DomainOS input/geometry while native data/events update.

The installed Plasma host loads the exact final main.qml and native providers.
KDED's actual SNI watcher, KDE's natural notification server and ksystemstats
remain real. Only the producer applications and their notifications are owned
test stimuli. Every process/display/bus/profile is private; no persistent
preview, real desktop, frozen Downloads backup or production edit is used.
"""
import argparse
import hashlib
import json
import os
from pathlib import Path
import re
import shlex
import shutil
import signal
import subprocess
import sys
import time

sys.dont_write_bytecode=True
REPO=Path(__file__).resolve().parents[2]


def digest(path):return hashlib.sha256(path.read_bytes()).hexdigest() if path.is_file() else None


def worker(output):
    if os.environ.get('IRIX_DOMAINOS_VF20_PRIVATE')!='1':raise RuntimeError('Private session required')
    from PyQt6.QtCore import QObject,QMetaType,QTimer,pyqtClassInfo,pyqtProperty,pyqtSignal,pyqtSlot
    from PyQt6.QtDBus import QDBusArgument,QDBusConnection,QDBusMessage,QDBusObjectPath,QDBusPendingReply
    from PyQt6.QtWidgets import QApplication
    app=QApplication([]);bus=QDBusConnection.sessionBus()
    processes=[];logs=[];host=None;report={};native_events=[];notify_ids=[];server_info={};provider_calls=[];notification_enabled=[True];registration_calls=[];sni_service='org.kde.StatusNotifierItem-'+str(os.getpid())+'-1';registration_evidence={}
    def call(service,path,interface,method,arguments=()):
        message=QDBusMessage.createMethodCall(service,path,interface,method);message.setArguments(list(arguments))
        reply=bus.call(message,timeout=3000)
        if reply.type()==QDBusMessage.MessageType.ErrorMessage:raise RuntimeError(reply.errorMessage())
        return reply.arguments()
    def owner(service):
        value=call('org.freedesktop.DBus','/org/freedesktop/DBus','org.freedesktop.DBus','GetNameOwner',[service])[0]
        pid=call('org.freedesktop.DBus','/org/freedesktop/DBus','org.freedesktop.DBus','GetConnectionUnixProcessID',[value])[0]
        return {'owner':value,'pid':int(pid)}
    @pyqtClassInfo('D-Bus Interface','org.kde.StatusNotifierItem')
    class AttentionItem(QObject):
        NewStatus=pyqtSignal(str);NewIcon=pyqtSignal();NewAttentionIcon=pyqtSignal();NewOverlayIcon=pyqtSignal();NewToolTip=pyqtSignal();NewTitle=pyqtSignal()
        status='Active';serial=0
        @pyqtProperty(str)
        def Category(self):return 'ApplicationStatus'
        @pyqtProperty(str)
        def Id(self):return 'domainos-vf20-native-sni'
        @pyqtProperty(str)
        def Title(self):return 'DomainOS VF20 attention '+str(self.serial)
        @pyqtProperty(str)
        def Status(self):return self.status
        @pyqtProperty(str)
        def IconName(self):return 'utilities-terminal'
        @pyqtProperty(str)
        def AttentionIconName(self):return 'dialog-warning'
        @pyqtProperty(str)
        def OverlayIconName(self):return ''
        @pyqtProperty(str)
        def IconThemePath(self):return ''
        @pyqtProperty('uint')
        def WindowId(self):return 0
        @pyqtProperty(bool)
        def ItemIsMenu(self):return False
        @pyqtProperty(QDBusObjectPath)
        def Menu(self):return QDBusObjectPath('/NO_DBUSMENU')
        @pyqtSlot(int,int)
        def Activate(self,x,y):provider_calls.append({'action':'Activate','x':x,'y':y})
        @pyqtSlot(int,int)
        def SecondaryActivate(self,x,y):provider_calls.append({'action':'SecondaryActivate','x':x,'y':y})
        @pyqtSlot(int,int)
        def ContextMenu(self,x,y):provider_calls.append({'action':'ContextMenu','x':x,'y':y})
        @pyqtSlot(int,str)
        def Scroll(self,value,orientation):provider_calls.append({'action':'Scroll','value':value})
        @pyqtSlot(str)
        def ProvideXdgActivationToken(self,token):pass
    directed=os.environ.get('IRIX_DOMAINOS_DIRECTED_ATTENTION')=='1'
    item=AttentionItem();event_timer=QTimer();event_timer.setInterval(80)
    def set_attention(status,sequence):
        if status not in ('Active','NeedsAttention'):raise RuntimeError('Invalid owned attention status')
        item.status=status;item.NewStatus.emit(status)
        native_events.append({'kind':'SNI','id':item.Id,'sequence':sequence,'status':status,'monotonic_ns':time.monotonic_ns(),'directed':True})
    def start_events():
        # The native host may be synchronously waiting for BeginEvents' void
        # reply. Inspect its real notification service only after returning
        # that reply; otherwise the two legitimate clients would deadlock.
        try:
            server_info.update(owner('org.freedesktop.Notifications'))
            server_info['information']=call('org.freedesktop.Notifications','/org/freedesktop/Notifications','org.freedesktop.Notifications','GetServerInformation')
            server_info['native']=server_info['pid']==host.pid
        except RuntimeError as error:server_info.update(native=False,error=str(error))
        event_timer.start();pulse()
    @pyqtClassInfo('D-Bus Interface','org.irixclassic.DomainOSVf20.Events')
    class Events(QObject):
        @pyqtSlot()
        def RegisterAttention(self):
            registration=QDBusMessage.createMethodCall('org.kde.StatusNotifierWatcher','/StatusNotifierWatcher','org.kde.StatusNotifierWatcher','RegisterStatusNotifierItem')
            registration.setArguments([sni_service]);registration_calls.append(QDBusPendingReply(bus.asyncCall(registration)))
            registration_evidence.update(service=sni_service,registered_after_native_host=True)
        @pyqtSlot()
        def BeginEvents(self):QTimer.singleShot(0,start_events)
        @pyqtSlot(str,int)
        def SetOwnedAttention(self,status,sequence):
            # Return the test control reply before emitting the actual SNI
            # signal. The producer then holds the state until the native host
            # has observed it and explicitly requests the next state.
            QTimer.singleShot(0,lambda:set_attention(status,sequence))
        @pyqtSlot()
        def StopNotificationReplacements(self):notification_enabled[0]=False
        @pyqtSlot()
        def StopEvents(self):
            event_timer.stop()
            for identifier in set(notify_ids):
                message=QDBusMessage.createMethodCall('org.freedesktop.Notifications','/org/freedesktop/Notifications','org.freedesktop.Notifications','CloseNotification')
                message.setArguments([QDBusArgument(identifier,QMetaType.Type.UInt.value)]);bus.asyncCall(message)
            bus.unregisterService(sni_service)
    events=Events()
    def pulse():
        item.serial+=1
        if not directed:
            item.status='NeedsAttention' if item.serial%2 else 'Active'
            item.NewStatus.emit(item.status);item.NewTitle.emit();item.NewIcon.emit()
            native_events.append({'kind':'SNI','id':item.Id,'serial':item.serial,'status':item.status,'monotonic_ns':time.monotonic_ns()})
        if item.serial%4==1 and server_info.get('native') and notification_enabled[0]:
            summary='DomainOS VF20 '+str(item.serial)
            replace=notify_ids[0] if len(notify_ids)>=2 else 0
            arguments=['DomainOS VF20 private producer',QDBusArgument(replace,QMetaType.Type.UInt.value),'utilities-terminal',summary,'Private native notification concurrent with input',QDBusArgument([],QMetaType.Type.QStringList.value),{'suppress-sound':True,'desktop-entry':'org.irixclassic.DomainOSVf20','transient':False,'urgency':1},2500]
            try:
                identifier=call('org.freedesktop.Notifications','/org/freedesktop/Notifications','org.freedesktop.Notifications','Notify',arguments)[0]
                notify_ids.append(int(identifier));native_events.append({'kind':'Notify','summary':summary,'id':int(identifier),'monotonic_ns':time.monotonic_ns()})
            except RuntimeError as error:native_events.append({'kind':'NotifyError','error':str(error),'monotonic_ns':time.monotonic_ns()})
    event_timer.timeout.connect(pulse)
    try:
        for executable in ('kwin_x11','kactivitymanagerd','ksystemstats','kded6'):
            path=shutil.which(executable) or ('/usr/lib/x86_64-linux-gnu/libexec/kactivitymanagerd' if executable=='kactivitymanagerd' else executable)
            log=(output/(executable+'.log')).open('w');logs.append(log)
            processes.append(subprocess.Popen([path,*(['--remain'] if executable=='ksystemstats' else [])],stdout=log,stderr=subprocess.STDOUT))
        readiness_errors=[]
        for _ in range(100):
            app.processEvents()
            try:
                watcher=owner('org.kde.StatusNotifierWatcher')
                watcher['initial_properties']=str(call('org.kde.StatusNotifierWatcher','/StatusNotifierWatcher','org.freedesktop.DBus.Properties','GetAll',['org.kde.StatusNotifierWatcher']))
                if subprocess.run(['qdbus6','org.kde.KWin','/VirtualDesktopManager'],capture_output=True,timeout=2).returncode==0:break
            except RuntimeError as error:readiness_errors.append(str(error))
            time.sleep(.05)
        else:
            registration_evidence['readiness_errors']=readiness_errors[-3:]
            paths=subprocess.run(['qdbus6','org.kde.StatusNotifierWatcher'],capture_output=True,text=True,timeout=3)
            registration_evidence['watcher_paths']=paths.stdout+paths.stderr
            raise RuntimeError('Native KWin/KDED StatusNotifierWatcher object did not become ready')
        if watcher['pid']!=processes[3].pid:raise RuntimeError('SNI watcher owner is not this native KDED process')
        assert bus.registerService(sni_service)
        assert bus.registerObject('/StatusNotifierItem',item,QDBusConnection.RegisterOption.ExportAllSlots|QDBusConnection.RegisterOption.ExportAllProperties|QDBusConnection.RegisterOption.ExportAllSignals)
        assert bus.registerService('org.irixclassic.DomainOSVf20.Control')
        assert bus.registerObject('/Events',events,QDBusConnection.RegisterOption.ExportAllSlots)
        monitor_log=(output/'private-bus-events.log').open('w');logs.append(monitor_log)
        processes.append(subprocess.Popen(['dbus-monitor',"interface='org.kde.StatusNotifierWatcher'","path='/StatusNotifierItem'","sender='"+bus.baseService()+"'"],stdout=monitor_log,stderr=subprocess.STDOUT))
        environment=dict(os.environ,LD_PRELOAD=str(output/'concurrency-host.so'),IRIX_DOMAINOS_CONCURRENT_DIR=str(output),IRIX_DOMAINOS_CONCURRENT_REPORT=str(output/'HOST.json'))
        with (output/'host.log').open('w') as log:
            host=subprocess.Popen(['/usr/bin/plasmawindowed','org.irixclassic.domainos.panel'],env=environment,stdout=log,stderr=subprocess.STDOUT)
            deadline=time.monotonic()+38
            while host.poll() is None and time.monotonic()<deadline:app.processEvents();time.sleep(.005)
            if host.poll() is None:raise RuntimeError('Native host observation deadline exceeded')
        registration_evidence['registration_errors']=[pending.error().message() for pending in registration_calls if pending.isError()]
        state=json.loads((output/'HOST.json').read_text()) if (output/'HOST.json').is_file() else {}
        errors=[line for line in (output/'host.log').read_text().splitlines() if re.search(r'ReferenceError:|TypeError:|SyntaxError:|Cannot assign|Binding loop|is not a type|Type .+ unavailable|module .+ is not installed',line)]
        checks=state.get('checks',{})
        checks.update(native_host_exited_cleanly=host.returncode==0,native_sni_watcher_owned_by_private_kded=watcher['pid']==processes[3].pid,native_notification_server_owned_by_legitimate_host=server_info.get('native') is True,real_notify_requests_accepted=sum(event['kind']=='Notify' for event in native_events)>=4,no_sni_window_action_from_telemetry_or_notifications=not provider_calls,qml_runtime_errors_zero=not errors,host_self_reports_private_namespace=state.get('host_namespace',{}).get('HOME')==str(output/'home') and state.get('host_namespace',{}).get('XDG_CONFIG_HOME')==str(output/'config') and state.get('host_namespace',{}).get('DBUS_SESSION_BUS_ADDRESS')==os.environ['DBUS_SESSION_BUS_ADDRESS'])
        if directed:
            witnesses=state.get('directed_attention_witnesses',[])
            emitted={event['sequence']:event for event in native_events if event.get('kind')=='SNI' and event.get('directed')}
            interval=state.get('input_interval',{})
            checks['six_owned_attention_states_consumed_within_input_interval']=len(witnesses)==6 and all(
                witness.get('sequence') in emitted and emitted[witness['sequence']]['id']==witness.get('id')=='domainos-vf20-native-sni'
                and emitted[witness['sequence']]['status']==witness.get('requested_status')
                and interval.get('start_monotonic_ns',0)<=emitted[witness['sequence']]['monotonic_ns']<=witness.get('observed_monotonic_ns',0)<=interval.get('end_monotonic_ns',0)
                and witness.get('model_and_delegate_confirmed') and witness.get('pointer_still_pressed')
                for witness in witnesses)
            delivered={(event['id'],event['summary']) for event in native_events if event['kind']=='Notify'}
            history=state.get('history_test_notifications',[])
            checks['native_history_ids_match_real_notify_replies_during_input']=bool(history) and all(
                (entry.get('notification_id'),entry.get('summary')) in delivered and entry.get('desktop_entry')=='org.irixclassic.DomainOSVf20'
                and interval.get('start_monotonic_ns',0)<=entry.get('observed_monotonic_ns',0)<=interval.get('end_monotonic_ns',0)
                for entry in history)
        values={name:[sample[name] for sample in state.get('measurements',[]) if name in sample] for name in ('pointer_press_us','pointer_release_us','keyboard_press_us','keyboard_release_us')}
        latency={name:{'samples':len(samples),'minimum_us':min(samples) if samples else None,'maximum_us':max(samples) if samples else None} for name,samples in values.items()}
        report.update(checks=checks,native=state,watcher=watcher,registration=registration_evidence,notification_server=server_info,event_log=native_events,provider_calls=provider_calls,qml_diagnostics=errors,latency=latency)
    except Exception as error:report.update(error=str(error),checks={'native_scenario_completed':False},event_log=native_events,notification_server=server_info,registration=registration_evidence)
    finally:
        events.StopEvents()
        for process in ([host] if host else [])+list(reversed(processes)):
            if process.poll() is None:
                process.terminate()
                try:process.wait(5)
                except subprocess.TimeoutExpired:process.kill();process.wait()
        for log in logs:log.close()
        report.setdefault('checks',{})['owned_processes_exited']=all(process.poll() is not None for process in processes+([host] if host else []))
    report['status']='passed' if all(report['checks'].values()) else 'failed'
    (output/'NATIVO.json').write_text(json.dumps(report,indent=2,ensure_ascii=False)+'\n')
    return 0 if report['status']=='passed' else 1


def main():
    parser=argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--saida',type=Path,required=True);parser.add_argument('--worker',action='store_true',help=argparse.SUPPRESS)
    parser.add_argument('--atencao-dirigida',action='store_true',help='Hold six owned SNI states until native model/delegate observations during held input')
    args=parser.parse_args();output=args.saida.resolve()
    if args.worker:return worker(output)
    if not output.is_relative_to(Path('/tmp')) or output==Path('/tmp') or output.exists():parser.error('Use a new directory under /tmp')
    output.mkdir(mode=0o700);environment=os.environ.copy()
    if args.atencao_dirigida:environment['IRIX_DOMAINOS_DIRECTED_ATTENTION']='1'
    config=Path(environment.get('XDG_CONFIG_HOME',str(Path.home()/'.config')))
    protected=lambda:{str(config/name):digest(config/name) for name in ('kdeglobals','kwinrc','plasmarc','plasma-org.kde.plasma.desktop-appletsrc')}
    before=protected();sources={str(path.relative_to(REPO)):digest(path) for path in (REPO/'plasma/applets/org.irixclassic.domainos.panel').rglob('*') if path.is_file() and path.suffix not in ('.md','.pyc')};documents={str(path.relative_to(REPO)):digest(path) for path in (REPO/'plasma/applets/org.irixclassic.domainos.panel').rglob('*.md')}
    for key in ('DISPLAY','WAYLAND_DISPLAY','WAYLAND_SOCKET','DBUS_SESSION_BUS_ADDRESS','DBUS_STARTER_ADDRESS','DBUS_STARTER_BUS_TYPE','SESSION_MANAGER','LD_PRELOAD','QML_IMPORT_PATH','QML2_IMPORT_PATH','XAUTHORITY','QT_STYLE_OVERRIDE','QT_QUICK_CONTROLS_STYLE','KDE_FULL_SESSION','KDE_SESSION_VERSION','XDG_SESSION_ID','PULSE_SERVER','PULSE_COOKIE','KWIN_WAYLAND_NO_PERMISSION_CHECKS'):
        environment.pop(key,None)
    for key,name in (('HOME','home'),('XDG_CONFIG_HOME','config'),('XDG_DATA_HOME','data'),('XDG_CACHE_HOME','cache'),('XDG_STATE_HOME','state'),('XDG_RUNTIME_DIR','runtime')):
        path=output/name;path.mkdir(mode=0o700);environment[key]=str(path)
    plasmoids=output/'data/plasma/plasmoids'
    for name in ('org.irixclassic.domainos.panel','org.irixclassic.grosview'):shutil.copytree(REPO/'plasma/applets'/name,plasmoids/name,ignore=shutil.ignore_patterns('__pycache__','*.pyc'))
    for name in ('IrixClassic','IrixClassicDomainOS'):shutil.copytree(REPO/'plasma'/name,output/'data/plasma/desktoptheme'/name)
    applications=output/'data/applications';applications.mkdir(parents=True,exist_ok=True)
    (applications/'org.irixclassic.DomainOSVf20.desktop').write_text('[Desktop Entry]\nType=Application\nName=DomainOS VF20 private producer\nExec=false\nIcon=utilities-terminal\nNoDisplay=true\n')
    (output/'config/kwinrc').write_text('[Desktops]\nNumber=1\nName_1=Private concurrent native test\n[Compositing]\nEnabled=false\n')
    (output/'config/kdeglobals').write_text((REPO/'colors/DomainOS-SR10.4.colors').read_text())
    (output/'config/plasmarc').write_text('[Theme]\nname=IrixClassicDomainOS\n')
    modules=Path('/usr/lib/x86_64-linux-gnu/qt6/plugins/kf6/kded')
    (output/'config/kded6rc').write_text('\n'.join('[Module-'+path.stem+']\nautoload='+('true' if path.stem=='statusnotifierwatcher' else 'false')+'\n' for path in modules.glob('*.so')))
    flags=shlex.split(subprocess.check_output(['pkg-config','--cflags','--libs','Qt6Widgets','Qt6Test','Qt6DBus'],text=True))
    subprocess.run(['c++','-std=c++17','-shared','-fPIC',str(REPO/'plasma/tests/domainos-concurrency-host.cpp'),'-o',str(output/'concurrency-host.so'),*flags,'-ldl'],check=True)
    environment.update(XDG_DATA_DIRS='/usr/local/share:/usr/share',XDG_CONFIG_DIRS='/etc/xdg',QT_QPA_PLATFORM='xcb',QT_QPA_PLATFORMTHEME='kde',QT_QUICK_BACKEND='software',KWIN_COMPOSE='N',XDG_SESSION_TYPE='x11',XDG_CURRENT_DESKTOP='KDE',KDE_FULL_SESSION='true',KDE_SESSION_VERSION='6',QT_SCALE_FACTOR='1',DBUS_SYSTEM_BUS_ADDRESS='unix:path='+str(output/'no-system-bus'),PULSE_SERVER='unix:'+str(output/'no-audio'),IRIX_DOMAINOS_VF20_PRIVATE='1')
    bus=output/'bus.conf';bus.write_text('<busconfig><type>session</type><listen>unix:tmpdir='+str(output/'runtime')+'</listen><auth>EXTERNAL</auth><policy context="default"><allow send_destination="*" eavesdrop="true"/><allow receive_sender="*" eavesdrop="true"/><allow own="*"/></policy></busconfig>')
    with (output/'runner.log').open('w') as log:
        runner=subprocess.Popen(['xvfb-run','--auto-servernum','--server-args=-screen 0 1200x700x24 -nolisten tcp','dbus-run-session','--config-file',str(bus),'--',sys.executable,str(Path(__file__).resolve()),'--worker','--saida',str(output)],env=environment,stdout=log,stderr=subprocess.STDOUT,start_new_session=True)
        try:runner.wait(55)
        except subprocess.TimeoutExpired:
            os.killpg(runner.pid,signal.SIGTERM)
            try:runner.wait(5)
            except subprocess.TimeoutExpired:os.killpg(runner.pid,signal.SIGKILL);runner.wait()
    report=json.loads((output/'NATIVO.json').read_text()) if (output/'NATIVO.json').is_file() else {'checks':{'native_report_saved':False},'error':(output/'runner.log').read_text()}
    report['checks'].update(private_worker_exited_cleanly=runner.returncode==0,real_profiles_unchanged=before==protected(),production_source_hashes_unchanged=all(digest(REPO/name)==value for name,value in sources.items()))
    report['documentation_changes_during_test']=[name for name,value in documents.items() if digest(REPO/name)!=value]
    report.update(protected_config_sha256={'before':before,'after':protected()},source_sha256=sources,scope='Directed native X11 production-main trial during genuine ksystemstats/time updates and test-owned SNI/Notify events through real KDE servers. Same-dispatch relief/action/focus state and observed elapsed times are measured here, not guaranteed for every computer or all input/accessibility devices. No synthetic sensor histories or substituted providers/models are used.')
    report['status']='passed' if all(report['checks'].values()) else 'failed'
    (output/'RESULTADO.json').write_text(json.dumps(report,indent=2,ensure_ascii=False)+'\n')
    print(json.dumps({'status':report['status'],'checks':len(report['checks']),'result':str(output/'RESULTADO.json')}))
    return 0 if report['status']=='passed' else 1


if __name__=='__main__':raise SystemExit(main())
