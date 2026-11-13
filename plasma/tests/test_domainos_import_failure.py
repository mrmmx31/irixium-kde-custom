#!/usr/bin/env python3
# SPDX-License-Identifier: GPL-3.0-or-later
"""Production preferences import boundaries, with a failing recording source.

Loads the actual ConfigApplications.qml once in a private offscreen namespace.
No helper/source is executed and no ConfigView Apply or desktop API is used.
"""
import json
import os
from pathlib import Path
import signal
import subprocess
import sys
import tempfile
import unittest

sys.dont_write_bytecode=True
ROOT=Path(__file__).resolve().parents[2]
UI=ROOT/'plasma/applets/org.irixclassic.domainos.panel/contents/ui'


def worker():
    if os.environ.get('DOMAINOS_PRIVATE_IMPORT_TEST')!='1':raise RuntimeError('Private test worker required')
    from PyQt6.QtCore import Q_ARG,QMetaObject,QUrl,Qt
    from PyQt6.QtWidgets import QApplication
    from PyQt6.QtQml import QQmlComponent,QQmlEngine,qmlRegisterSingletonType
    app=QApplication([sys.argv[0]]);engine=QQmlEngine();component=QQmlComponent(engine)
    # ConfigView registers this module in C++; a plain offscreen engine does
    # not. Supply only its read-only configuration context for the reset footer.
    # It has no applet, persistence, methods, provider or desktop-session access.
    context_path=Path(os.environ['TMPDIR'])/'PrivatePlasmoidContext.qml'
    context_path.write_text('pragma Singleton\nimport QtQuick\nQtObject { property var configuration: ({}) }\n')
    qmlRegisterSingletonType(QUrl.fromLocalFile(str(context_path)),'org.kde.plasma.plasmoid',1,0,'Plasmoid')
    fixture_path=Path(os.environ['TMPDIR'])/'import-failure.qml'
    fixture_path.write_text('''import QtQuick
import "'''+UI.as_uri()+'''" as Production
Item {
    id:fixture
    property var lastSnapshot
    property var lastReturn
    QtObject {
        id:source
        property bool throwConnect:false
        property bool throwDisconnect:false
        property bool inlineComplete:false
        property var connected:[]
        property var disconnected:[]
        function connectSource(command) {
            connected=connected.concat([command])
            if (inlineComplete) page.handleImportResult(command,{stdout:JSON.stringify({ok:true,token:page.pendingToken,origins:[{id:"7/4",label:"Native test source"}]})})
            if (throwConnect) throw new Error("private connect details")
        }
        function disconnectSource(command) {
            disconnected=disconnected.concat([command])
            if (throwDisconnect) throw new Error("private disconnect details")
        }
    }
    Production.ConfigApplications { id:page;importSource:source }
    function setup(connectFailure,disconnectFailure,inlineResult) {
        source.throwConnect=connectFailure;source.throwDisconnect=disconnectFailure;source.inlineComplete=inlineResult
    }
    function request(action) {lastReturn=page.requestImport(action,action==="source" ? "7/4" : "")}
    function result(kind) {
        const command=page.pendingCommand,token=page.pendingToken
        let result={ok:true,token:token,origins:[{id:"7/4",label:"Native test source"}],desktopIds:["org.kde.kate.desktop"]}
        if (kind==="wrong") result.token="other-token"
        if (kind==="malformed") lastReturn=page.handleImportResult(command,{stdout:"malformed JSON"})
        else if (kind==="null") lastReturn=page.handleImportResult(command,null)
        else if (kind==="foreign") lastReturn=page.handleImportResult("other-source",{stdout:JSON.stringify(result)})
        else lastReturn=page.handleImportResult(command,{stdout:JSON.stringify(result)})
    }
    function snapshot() {lastSnapshot={busy:page.importBusy,command:page.pendingCommand,token:page.pendingToken,action:page.pendingAction,
        origins:page.importOrigins,pins:page.cfg_pinnedApplications,message:page.importMessage,connected:source.connected.length,disconnected:source.disconnected.length}}
}''')
    component.loadUrl(QUrl.fromLocalFile(str(fixture_path)));fixture=component.create()
    assert fixture is not None,'\n'.join(error.toString() for error in component.errors())
    def variant(v):return v.toVariant() if hasattr(v,'toVariant') else v
    def invoke(name,*values):
        QMetaObject.invokeMethod(fixture,name,Qt.ConnectionType.DirectConnection,*(Q_ARG('QVariant',value) for value in values))
        app.processEvents();return variant(fixture.property('lastReturn'))
    def state():invoke('snapshot');return variant(fixture.property('lastSnapshot'))
    def settled():
        current=state();assert not current['busy'] and current['command']==current['token']==current['action']=='',current;return current
    checks={}
    invoke('setup',True,True,False);assert invoke('request','origins') is False
    current=settled();assert current['connected']==current['disconnected']==1 and not current['pins']
    checks['connect_and_cleanup_exceptions_release_busy_without_retry']=True
    invoke('setup',False,True,False);assert invoke('request','origins') is True
    assert state()['busy'];invoke('result','valid');current=settled();assert current['origins'][0]['id']=='7/4'
    checks['disconnect_exception_preserves_valid_reply_and_releases_busy']=True
    invoke('setup',False,False,False);invoke('request','source');before=state();assert invoke('result','foreign') is False
    assert state()['busy'] and state()['disconnected']==before['disconnected'];invoke('result','wrong');current=settled();assert not current['pins']
    checks['foreign_reply_does_not_consume_owned_request']=True;checks['wrong_token_does_not_import']=True
    for kind in ('malformed','null'):
        invoke('request','source');invoke('result',kind);assert not settled()['pins'];checks[kind+'_reply_releases_busy']=True
    invoke('request','source');invoke('result','valid');current=settled();assert current['pins']==['org.kde.kate.desktop']
    checks['recovery_imports_only_after_new_explicit_request']=True
    invoke('setup',True,False,True);invoke('request','origins');current=settled();assert current['origins'][0]['id']=='7/4'
    checks['inline_completion_survives_subsequent_connect_exception']=True
    print(json.dumps({'status':'passed','checks':checks,'scope':'Actual production preferences page functions with recording/failing provider and an explicit empty Plasmoid configuration context for the footer; no ConfigView, executable connections or native persistence'}))
    fixture.deleteLater();app.processEvents()


class ImportFailure(unittest.TestCase):
    def test_production_import_boundary_and_recovery(self):
        with tempfile.TemporaryDirectory(prefix='.qa-domainos-import-',dir=ROOT) as private:
            base=Path(private);env=dict(os.environ)
            for name in ('HOME','XDG_CONFIG_HOME','XDG_DATA_HOME','XDG_CACHE_HOME','XDG_STATE_HOME','XDG_RUNTIME_DIR','TMPDIR'):
                path=base/name.lower();path.mkdir(mode=0o700);env[name]=str(path)
            for name in ('DISPLAY','WAYLAND_DISPLAY','DBUS_SESSION_BUS_ADDRESS','DBUS_STARTER_ADDRESS','LD_PRELOAD','QML_IMPORT_PATH','QML2_IMPORT_PATH','QT_STYLE_OVERRIDE'):
                env.pop(name,None)
            env.update(QT_QPA_PLATFORM='offscreen',QT_QPA_PLATFORMTHEME='generic',QT_QUICK_BACKEND='software',QT_QUICK_CONTROLS_STYLE='Basic',
                QML_DISABLE_DISK_CACHE='1',XDG_CURRENT_DESKTOP='NONE',DBUS_SYSTEM_BUS_ADDRESS='unix:path='+str(base/'disabled-system-bus'),DOMAINOS_PRIVATE_IMPORT_TEST='1')
            bus=base/'bus.conf';bus.write_text('<busconfig><type>session</type><listen>unix:path='+str(base/'bus.socket')+'</listen><auth>EXTERNAL</auth><policy context="default"><allow own="*"/><allow send_destination="*"/><allow receive_sender="*"/></policy></busconfig>')
            process=subprocess.Popen(['dbus-run-session','--config-file',str(bus),'--',sys.executable,'-B',str(Path(__file__).resolve()),'--worker'],
                env=env,stdout=subprocess.PIPE,stderr=subprocess.PIPE,text=True,start_new_session=True)
            try:stdout,stderr=process.communicate(timeout=15)
            except subprocess.TimeoutExpired:
                os.killpg(process.pid,signal.SIGKILL);process.communicate();self.fail('Private import fixture exceeded 15 seconds')
            self.assertEqual(process.returncode,0,stdout+stderr)
            report=json.loads(stdout.strip().splitlines()[-1]);self.assertEqual(len(report['checks']),8);self.assertTrue(all(report['checks'].values()))
            print(stdout.strip())


if __name__=='__main__':
    if len(sys.argv)==2 and sys.argv[1]=='--worker':worker()
    else:unittest.main()
