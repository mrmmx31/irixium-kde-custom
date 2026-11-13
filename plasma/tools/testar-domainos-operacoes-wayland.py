#!/usr/bin/env python3
# SPDX-License-Identifier: GPL-3.0-or-later
"""Owned virtual KWin + legitimate plasmawindowed. Model windows are doubles.
Checks mapped operations geometry, not physical seat input or real batch jobs.
"""
import json
import os
from pathlib import Path
import subprocess
import sys
import tempfile
import time

REPO=Path(__file__).resolve().parents[2]
ID='org.irixclassic.domainos.operations.private'

def worker(out):
    compositor=host=None
    with (out/'SESSION.log').open('w') as log:
        try:
            compositor=subprocess.Popen(['kwin_wayland','--virtual','--width','1200','--height','900','--socket','p04-own-wayland','--no-lockscreen','--no-global-shortcuts','--no-kactivities'],env=dict(os.environ,QT_QPA_PLATFORM='offscreen',KWIN_COMPOSE='Q'),stdout=log,stderr=subprocess.STDOUT)
            for _ in range(100):
                if compositor.poll() is not None: raise RuntimeError('Own KWin exited')
                if (out/'runtime/p04-own-wayland').is_socket(): break
                time.sleep(.05)
            else: raise RuntimeError('Own Wayland socket not ready')
            with (out/'HOST.log').open('w') as hostlog:
                host=subprocess.Popen(['/usr/bin/plasmawindowed',ID],env=dict(os.environ,QT_QPA_PLATFORM='wayland',WAYLAND_DISPLAY='p04-own-wayland'),stdout=hostlog,stderr=subprocess.STDOUT)
                for _ in range(100):
                    if host.poll() is not None: break
                    if 'P04_REPORT ' in (out/'HOST.log').read_text(): break
                    time.sleep(.1)
                else: raise RuntimeError('Native host report timeout')
                host.terminate();host.wait(timeout=5)
            lines=(out/'HOST.log').read_text().splitlines()
            reports=[json.loads(line.split('P04_REPORT ',1)[1]) for line in lines if 'P04_REPORT ' in line]
            if not reports: raise RuntimeError('Native host supplied no report')
            report=reports[0]
            report['host_exit_code']=host.returncode
            report['scope']='legitimate plasmawindowed in own KWin virtual/profile/bus; QML-invoked lifecycle with model doubles, no seat-input or real-job claim'
            (out/'RESULTADO.json').write_text(json.dumps(report,indent=2)+'\n')
            return 0 if report['visible'] and report['above'] and report['bounded'] and report['count']==11 and host.returncode in (0,-15) else 1
        finally:
            for process in (host,compositor):
                if process and process.poll() is None:
                    process.terminate()
                    try: process.wait(timeout=5)
                    except subprocess.TimeoutExpired:process.kill();process.wait()

def main():
    if len(sys.argv)>1 and sys.argv[1]=='--worker': return worker(Path(sys.argv[2]))
    temp_root=Path.home()/'tempia/domainos-theme-work'
    temp_root.mkdir(mode=0o700,parents=True,exist_ok=True)
    out=Path(tempfile.mkdtemp(prefix='domainos-p04-wayland-',dir=temp_root))
    env=dict(os.environ)
    for key in ('DISPLAY','WAYLAND_DISPLAY','LD_PRELOAD','SESSION_MANAGER','XAUTHORITY'):env.pop(key,None)
    for key,name in [('HOME','home'),('XDG_CONFIG_HOME','config'),('XDG_DATA_HOME','data'),('XDG_CACHE_HOME','cache'),('XDG_STATE_HOME','state'),('XDG_RUNTIME_DIR','runtime'),('TMPDIR','tmp')]:
        path=out/name;path.mkdir(mode=0o700);env[key]=str(path)
    (out/'config/kwinrc').write_text('[org.kde.kdecoration2]\nlibrary=org.kde.breeze\n')
    env.update(XDG_CONFIG_DIRS='/etc/xdg',DBUS_SYSTEM_BUS_ADDRESS='unix:path='+str(out/'no-system'),PULSE_SERVER='unix:'+str(out/'no-audio'),QT_LOGGING_RULES='kwin_core.debug=true')
    applet=out/'data/plasma/plasmoids'/ID;(applet/'contents/ui').mkdir(parents=True)
    (applet/'metadata.json').write_text(json.dumps({'KPlugin':{'Id':ID,'Name':'P04 owned Wayland fixture','Version':'1.0','License':'GPL-3.0-or-later'},'KPackageStructure':'Plasma/Applet','X-Plasma-API-Minimum-Version':'6.0'}))
    qml='''import QtQuick
import org.kde.plasma.plasmoid
import "TESTS" as Fixtures
PlasmoidItem {
 preferredRepresentation:fullRepresentation
 fullRepresentation:Item { implicitWidth:100;implicitHeight:50 }
 property var fixture: Fixtures.DomainOSIconboxPreview { title:"P04 owned reference window" }
 property int phase:0
 Timer {
  interval:800;running:true;repeat:true
  onTriggered:{
   if(parent.phase===0) {
    parent.fixture.resetUi();parent.fixture.addGeometryBackend()
   } else if(parent.phase===1) {
    const c=parent.fixture.controller
    c.setMemberSelected("window:1",true);c.setMemberSelected("window:3",true)
    parent.fixture.iconbox.openOperations(c.selectedWindows(),Qt.rect(500,750,100,30))
   } else {
    const m=parent.fixture.iconbox.batchContextMenu,r=m.invocationRect
    console.log("P04_REPORT "+JSON.stringify({visible:m.visible,count:m.count,
      x:m.x,y:m.y,width:m.width,height:m.height,anchor:{x:r.x,y:r.y,width:r.width,height:r.height},
      above:m.y+m.height<=r.y && r.y-m.y-m.height<=8,
      bounded:m.x>=0 && m.y>=0 && m.x+m.width<=1200 && m.y+m.height<=900,
      opened:parent.fixture.iconbox.operationsOpened,error:parent.fixture.iconbox.lastError}))
    running=false;parent.fixture.closeMenus();parent.fixture.close()
   }
   parent.phase++
  }
 }
}
'''.replace('TESTS',(REPO/'plasma/tests').as_uri())
    (applet/'contents/ui/main.qml').write_text(qml)
    bus=out/'bus.conf';bus.write_text('<busconfig><type>session</type><listen>unix:tmpdir='+str(out/'runtime')+'</listen><auth>EXTERNAL</auth><policy context="default"><allow send_destination="*"/><allow receive_sender="*"/><allow own="*"/></policy></busconfig>')
    process=subprocess.run(['dbus-run-session','--config-file',str(bus),'--',sys.executable,__file__,'--worker',str(out)],env=env,timeout=40)
    print(json.dumps({'exit_code':process.returncode,'evidence':str(out)}))
    return process.returncode

if __name__=='__main__': raise SystemExit(main())
