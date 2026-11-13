#!/usr/bin/env python3
# SPDX-FileCopyrightText: 2026 IRIX Classic contributors
# SPDX-License-Identifier: GPL-3.0-or-later
"""Directed native tray texture, empty slots, actual click and tooltip proof.

Every SNI, display, D-Bus and writable path is private. Production components
and completed fixture themes are read-only; no package/icon tree is copied.
"""
import argparse
import hashlib
import importlib.util
import json
import os
from pathlib import Path
import re
import shlex
import subprocess
import sys

sys.dont_write_bytecode=True
REPO=Path(__file__).resolve().parents[2]
APPLET='org.irixclassic.domainos.tray.texture.test'
UI=REPO/'plasma/applets/org.irixclassic.domainos.panel/contents/ui'


def digest(path):
    return hashlib.sha256(path.read_bytes()).hexdigest() if path.is_file() else None


def worker(output):
    spec=importlib.util.spec_from_file_location('domainos_owned_texture_sni',REPO/'plasma/tools/testar-domainos-bandeja.py')
    fixture=importlib.util.module_from_spec(spec);spec.loader.exec_module(fixture);fixture.IDENTIFIER=APPLET
    return fixture.worker(output)


def main():
    parser=argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--saida',type=Path,required=True)
    parser.add_argument('--recursos-encerrados',type=Path,required=True)
    parser.add_argument('--adaptor-encerrado',type=Path,required=True)
    parser.add_argument('--worker',action='store_true',help=argparse.SUPPRESS)
    args=parser.parse_args();output=args.saida.resolve();resources=args.recursos_encerrados.resolve();adaptor=args.adaptor_encerrado.resolve()
    if args.worker:return worker(output)
    if not output.is_relative_to(Path('/tmp')) or output.exists():parser.error('Use a new owned /tmp output')
    for path in (resources,adaptor):
        if not path.is_relative_to(Path('/tmp')) or path.stat().st_uid!=os.getuid():parser.error('Reuse only completed owned private fixtures')
    if json.loads((resources/'RESULTADO.json').read_text()).get('checks',{}).get('native_host_exited') is not True:parser.error('Resource host must have exited')
    if json.loads((adaptor/'worker-exit.json').read_text()).get('returncode')!=0:parser.error('Adaptor host must have exited')
    output.mkdir(mode=0o700);env=os.environ.copy();real_config=Path(env.get('XDG_CONFIG_HOME',str(Path.home()/'.config')))
    protected=lambda:{name:digest(real_config/name) for name in ('kdeglobals','kwinrc','plasmarc','plasma-org.kde.plasma.desktop-appletsrc')}
    before=protected();sources={name:digest(UI/name) for name in ('DomainOSTray.qml','Bevel.qml','PanelButton.qml','PaletteImage.qml','DomainOSPalette.qml')}
    for key in ('DISPLAY','WAYLAND_DISPLAY','WAYLAND_SOCKET','DBUS_SESSION_BUS_ADDRESS','DBUS_STARTER_ADDRESS','DBUS_STARTER_BUS_TYPE','SESSION_MANAGER','LD_PRELOAD','XAUTHORITY','QML_IMPORT_PATH','QML2_IMPORT_PATH','QT_STYLE_OVERRIDE','QT_QUICK_CONTROLS_STYLE','KDE_FULL_SESSION','KDE_SESSION_VERSION','XDG_SESSION_ID'):
        env.pop(key,None)
    for key,name in (('HOME','home'),('XDG_CONFIG_HOME','config'),('XDG_DATA_HOME','data'),('XDG_CACHE_HOME','cache'),('XDG_STATE_HOME','state'),('XDG_RUNTIME_DIR','runtime')):
        path=output/name;path.mkdir(mode=0o700);env[key]=str(path)
    fixture=output/'data/plasma/plasmoids'/APPLET;(fixture/'contents/ui').mkdir(parents=True)
    (fixture/'metadata.json').write_text(json.dumps({'KPlugin':{'Id':APPLET,'Name':'DomainOS native tray texture private proof','Version':'1.0','License':'GPL-3.0-or-later'},'KPackageStructure':'Plasma/Applet','X-Plasma-API-Minimum-Version':'6.0','X-Plasma-RootPath':'org.kde.plasma.systemtray'}))
    (fixture/'contents/ui/main.qml').write_text('''import QtQuick
import QtQuick.Layouts
import org.kde.plasma.plasmoid
import "'''+UI.as_uri()+'''" as Panel
PlasmoidItem {
    id:host;preferredRepresentation:fullRepresentation
    property ContainmentItem internalSystray
    readonly property var fixtureHiddenProviders:["org.kde.plasma.networkmanagement","org.kde.plasma.volume","org.kde.plasma.bluetooth","org.kde.plasma.notifications","org.kde.plasma.vault","org.kde.plasma.devicenotifier","org.kde.kscreen","org.kde.kdeconnect","org.kde.plasma.printmanager"]
    function hiddenIds(includeChosen){return fixtureHiddenProviders.concat(Array.from({length:9},(_,i)=>"domainos-fixture-sni-"+i).filter(id=>includeChosen || id!=="domainos-fixture-sni-1"));}
    function attach(){internalSystray=Plasmoid.internalSystray;if(internalSystray){const cfg=internalSystray.plasmoid.configuration;cfg.shownItems=["domainos-fixture-sni-1"];cfg.hiddenItems=hiddenIds(false);cfg.extraItems=["org.kde.plasma.networkmanagement","org.kde.plasma.volume","org.kde.plasma.bluetooth","org.kde.plasma.notifications"];}}
    Component.onCompleted:attach()
    Connections{target:Plasmoid;function onInternalSystrayChanged(){host.attach()}}
    fullRepresentation:Item {
        id:fixture;objectName:"domainosTrayTextureFixture"
        implicitWidth:460;implicitHeight:180
        Layout.minimumWidth:460;Layout.minimumHeight:180
        readonly property real domainosRenderScale:0.5
        readonly property QtObject domainosPalette:colors
        readonly property Item hoverSni:tray.entries.find(entry=>entry.id==="domainos-fixture-sni-1")?.item || null
        property int scenario:0
        function find(item,name){if(!item)return null;if(item.objectName===name)return item;for(const child of item.children){const result=find(child,name);if(result)return result;}return null;}
        property string snapshotJson:JSON.stringify(Object.assign(tray.snapshot(),{
            slots:Array.from({length:6},(_,i)=>{const frame=find(tray,"domainosTraySlot_"+i+"Relief");return {id:tray.visibleEntries[i]?.id || "",texture:frame?.texture.toString() || "",face:frame?.face.toString() || "",sunken:frame?.sunken || false};}),
            hover:hoverSni ? ({active:hoverSni.active,containsMouse:hoverSni.containsMouse,iconScale:hoverSni.iconContainer?.scale ?? 1}) : null
        }))
        QtObject{id:settings;property var trayVisibleItems:["domainos-fixture-sni-1"];property var trayHiddenItems:host.hiddenIds(false);property var trayOrder:["domainos-fixture-sni-1"];property bool trayIncludeHiddenInOverflow:false;property string trayOverflowMode:"continuation";property bool barHintsEnabled:false;}
        Panel.DomainOSPalette{id:colors;followSystem:false}
        Text{x:10;y:10;text:"Nativo: ocupado / vazio";color:colors.text}
        Panel.DomainOSTray{id:tray;x:10;y:50;width:326;height:150;scale:0.5;transformOrigin:Item.TopLeft;nativeTray:host.internalSystray;settings:settings;colorPalette:colors;screenGeometry:Qt.rect(0,0,1000,700)}
        Text{x:230;y:10;text:"Face aprovada";color:colors.text}
        Panel.PanelButton{objectName:"domainosApprovedTrayReference";x:230;y:62;width:50;height:48;scale:0.5;transformOrigin:Item.TopLeft;face:colors.recessed;imageSource:Qt.resolvedUrl("'''+(UI.parent/'images/speaker.svg').as_uri()+'''");imageWidth:32;label:"Referência gráfica"}
        onScenarioChanged:{if(scenario===1){settings.trayVisibleItems=[];settings.trayHiddenItems=host.hiddenIds(true);}else if(scenario===2){settings.trayHiddenItems=host.hiddenIds(false);settings.trayVisibleItems=["domainos-fixture-sni-1"];settings.barHintsEnabled=true;}else if(scenario===3)settings.barHintsEnabled=false;}
    }
}
''')
    (output/'config/kdeglobals').write_text((REPO/'colors/DomainOS-SR10.4.colors').read_text())
    (output/'config/plasmarc').write_text('[Theme]\nname=IrixClassicDomainOS\n')
    os.link(adaptor/'native-tooltip-type.so',output/'native-tooltip-type.so')
    env.update(QT_QPA_PLATFORM='xcb',QT_QPA_PLATFORMTHEME='generic',QT_QUICK_BACKEND='software',QML_DISABLE_DISK_CACHE='1',QT_SCALE_FACTOR='1',XDG_SESSION_TYPE='x11',XDG_CURRENT_DESKTOP='NONE',XDG_DATA_DIRS=str(resources/'data')+':/usr/local/share:/usr/share',XDG_CONFIG_DIRS='/etc/xdg',LANG='C.UTF-8',LC_ALL='C.UTF-8',DBUS_SYSTEM_BUS_ADDRESS='unix:path='+str(output/'no-system-bus'),PULSE_SERVER='unix:'+str(output/'no-audio'),IRIX_DOMAINOS_TRAY_PRIVATE_SESSION='1')
    flags=shlex.split(subprocess.check_output(['pkg-config','--cflags','--libs','Qt6Widgets','Qt6DBus'],text=True))
    subprocess.run(['c++','-std=c++17','-shared','-fPIC',str(REPO/'plasma/tests/domainos-tray-texture-host.cpp'),'-o',str(output/'tray-host.so'),*flags,'-ldl'],check=True)
    bus=output/'bus.conf';bus.write_text('<busconfig><type>session</type><listen>unix:tmpdir='+str(output/'runtime')+'</listen><auth>EXTERNAL</auth><policy context="default"><allow send_destination="*"/><allow receive_sender="*"/><allow own="*"/></policy></busconfig>')
    result=subprocess.run(['xvfb-run','--auto-servernum','--server-args=-screen 0 1000x700x24','dbus-run-session','--config-file',str(bus),'--',sys.executable,str(Path(__file__).resolve()),'--worker','--saida',str(output),'--recursos-encerrados',str(resources),'--adaptor-encerrado',str(adaptor)],env=env,capture_output=True,text=True,timeout=35)
    (output/'runner.log').write_text(result.stdout+result.stderr)
    native=json.loads((output/'native.json').read_text()) if (output/'native.json').is_file() else {}
    calls=json.loads((output/'provider-calls.json').read_text()) if (output/'provider-calls.json').is_file() else {}
    log=(output/'host.log').read_text() if (output/'host.log').is_file() else result.stderr
    diagnostics=[line for line in log.splitlines() if re.search(r'ReferenceError:|TypeError:|SyntaxError:|Cannot assign|Binding loop|is not a type|Type .+ unavailable',line)]
    checks=native.get('checks',{});checks.update(native_host_exited_cleanly=result.returncode==0 and not native.get('failure'),actual_native_activate_callback=any(call.get('action')=='Activate' for call in calls.get('domainos-fixture-sni-1',[])),qml_runtime_errors_zero=not diagnostics,real_profiles_unchanged=before==protected(),production_sources_unchanged=all(digest(UI/name)==value for name,value in sources.items()))
    report={'status':'passed' if checks and all(checks.values()) else 'failed','checks':checks,'native':native,'provider_calls':calls,'qml_diagnostics':diagnostics,'source_sha256':sources,'protected_config_sha256':{'before':before,'after':protected()},'scope':'Directed native SNI occupied/vacant/reappearing slot, pixel comparison with existing approved PanelButton face, physical native press/release/callback and restored tooltip binding. Private Xvfb/D-Bus; no personal profile, existing preview or package/icon copy.'}
    (output/'RESULTADO.json').write_text(json.dumps(report,indent=2,ensure_ascii=False)+'\n');print(json.dumps({'status':report['status'],'checks':len(checks),'failed':[key for key,value in checks.items() if not value],'result':str(output/'RESULTADO.json')}))
    return 0 if report['status']=='passed' else 1


if __name__=='__main__':raise SystemExit(main())
