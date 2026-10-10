#!/usr/bin/env python3
# SPDX-FileCopyrightText: 2026 IRIX Classic contributors
# SPDX-License-Identifier: GPL-3.0-or-later
"""Exercise installed KDE menu, global search and permanent drawer preferences.

Runs in a private Plasma/Xvfb/KWin/D-Bus session. The only launched desktop
entry is a /tmp marker fixture; individual desktop preferences remain intact.
"""
import argparse
import hashlib
import importlib.util
import json
import os
from pathlib import Path
import re
import shlex
import shutil
import subprocess
import sys

sys.dont_write_bytecode=True
REPO=Path(__file__).resolve().parents[2]
APPLET=REPO/'plasma/applets/org.irixclassic.domainos.panel'
IDENTIFIER='org.irixclassic.domainos.application.interface.test'


def digest(path):
    return hashlib.sha256(path.read_bytes()).hexdigest() if path.is_file() else None


def worker(output):
    spec=importlib.util.spec_from_file_location('private_applications_session',REPO/'plasma/tools/testar-domainos-aplicativos.py')
    module=importlib.util.module_from_spec(spec);spec.loader.exec_module(module)
    module.IDENTIFIER=IDENTIFIER
    return module.session(output)


def main():
    parser=argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--saida',type=Path,required=True)
    parser.add_argument('--worker',action='store_true',help=argparse.SUPPRESS)
    args=parser.parse_args();output=args.saida.resolve()
    if args.worker:return worker(output)
    if not output.is_relative_to(Path('/tmp')) or output==Path('/tmp') or output.exists():parser.error('Use a new directory under /tmp')
    output.mkdir(mode=0o700)
    environment=os.environ.copy()
    config=Path(environment.get('XDG_CONFIG_HOME',str(Path.home()/'.config')))
    protected=lambda:{str(config/name):digest(config/name) for name in ('kdeglobals','kwinrc','plasmarc','plasma-org.kde.plasma.desktop-appletsrc')}
    before=protected()
    sources={str(path.relative_to(REPO)):digest(path) for path in APPLET.rglob('*') if path.is_file() and path.suffix in ('.qml','.js','.py')}
    native_sources={str(path):digest(path) for path in Path('/usr/share/plasma/plasmoids/org.kde.plasma.kicker/contents/ui').rglob('*') if path.is_file()}
    for key in ('DISPLAY','WAYLAND_DISPLAY','WAYLAND_SOCKET','DBUS_SESSION_BUS_ADDRESS','DBUS_STARTER_ADDRESS','DBUS_STARTER_BUS_TYPE','SESSION_MANAGER','LD_PRELOAD','QML_IMPORT_PATH','QML2_IMPORT_PATH','XAUTHORITY','QT_STYLE_OVERRIDE','QT_QUICK_CONTROLS_STYLE','KDE_FULL_SESSION','KDE_SESSION_VERSION','XDG_SESSION_ID','PULSE_SERVER','PULSE_COOKIE'):
        environment.pop(key,None)
    for key,name in (('HOME','home'),('XDG_CONFIG_HOME','config'),('XDG_DATA_HOME','data'),('XDG_CACHE_HOME','cache'),('XDG_STATE_HOME','state'),('XDG_RUNTIME_DIR','runtime')):
        path=output/name;path.mkdir(mode=0o700);environment[key]=str(path)
    plasmoids=output/'data/plasma/plasmoids'
    shutil.copytree(APPLET,plasmoids/'org.irixclassic.domainos.panel',ignore=shutil.ignore_patterns('__pycache__','*.pyc'))
    for name in ('IrixClassic','IrixClassicDomainOS'):shutil.copytree(REPO/'plasma'/name,output/'data/plasma/desktoptheme'/name)
    fixture=plasmoids/IDENTIFIER;(fixture/'contents/ui').mkdir(parents=True)
    (fixture/'contents/config').mkdir()
    shutil.copy2(APPLET/'contents/config/main.xml',fixture/'contents/config/main.xml')
    (fixture/'metadata.json').write_text(json.dumps({'KPlugin':{'Id':IDENTIFIER,'Name':'DomainOS interface private test','Version':'1.0','License':'GPL-3.0-or-later'},'KPackageStructure':'Plasma/Applet','X-Plasma-API-Minimum-Version':'6.0'}))
    (fixture/'contents/ui/main.qml').write_text('''import QtQuick
import QtQuick.Layouts
import org.kde.plasma.plasmoid
import org.kde.plasma.private.kicker as Kicker
import "../../../org.irixclassic.domainos.panel/contents/ui" as Panel
PlasmoidItem {
    id:host
    preferredRepresentation:fullRepresentation
    fullRepresentation:Item {
        id:fixture;objectName:"domainosApplicationInterfaceFixture"
        Layout.minimumWidth:594;Layout.minimumHeight:150
        Layout.preferredWidth:594;Layout.preferredHeight:150
        property int configureRequests:0
        property int sourceCountBeforeSearch:-1
        property var reports:[]
        function state() {
            let bridge=null
            function visit(item){if(item.objectName==="domainosKdeApplicationMenu")bridge=item;for(const child of item.children || [])visit(child)}
            visit(apps)
            return JSON.stringify({popup:apps.popupVisible,pins:fixtureSettings.pinnedApplications,configureRequests:configureRequests,
                searchResults:apps.filteredModel.count,sourceCountBeforeSearch:sourceCountBeforeSearch,reports:reports,
                kdeRootDistinct:bridge ? bridge.rootModel!==apps.catalogModel : false,kdeRootFlat:bridge ? bridge.rootModel.flat : true})
        }
        function action(name) {
            if(name==="nativeOpen"){fixtureSettings.applicationsMenuStyle="kde";apps.showMenu(anchor);return true}
            if(name==="customSearchOutsideCategory"){
                apps.close();fixtureSettings.applicationsMenuStyle="domainos";apps.showMenu(anchor)
                apps.currentModel=emptyCategory;sourceCountBeforeSearch=emptyCategory.count
                apps.searchText="DomainOS Interface Probe";return true
            }
            if(name==="emptyDrawer"){apps.close();apps.showDrawer(anchor);return true}
            return false
        }
        QtObject { id:fixtureSettings;property var pinnedApplications:[];property string applicationsMenuStyle:"domainos" }
        QtObject {
            id:fixtureCommands
            function openApplication(id){return false}
            function begin(label){return 1}
            function finish(token,result){fixture.reports=fixture.reports.concat([result])}
            function reported(result){fixture.reports=fixture.reports.concat([result])}
        }
        Kicker.FavoritesModel { id:emptyCategory;favorites:[] }
        Panel.DomainOSApplications {
            id:apps;hostItem:host;settings:fixtureSettings;commands:fixtureCommands
            favoritesClient:"org.irixclassic.domainos.private-interface"
            onConfigureRequested:fixture.configureRequests++
            onPinListRequested:pins=>fixtureSettings.pinnedApplications=pins.slice()
        }
        Rectangle { anchors.fill:parent;color:"#7894a7" }
        Item { id:anchor;x:120;y:40;width:100;height:40 }
    }
}
''')
    applications=output/'data/applications';applications.mkdir()
    marker=output/'dispatch.txt';script=output/'owned-marker.py'
    script.write_text('from pathlib import Path\nwith Path('+repr(str(marker))+').open("a") as file:file.write("probe\\n")\n')
    quote=lambda value:'"'+str(value).replace('\\','\\\\').replace('"','\\"')+'"'
    (applications/'irix-domainos-interface-probe.desktop').write_text('[Desktop Entry]\nType=Application\nName=DomainOS Interface Probe\nExec=/usr/bin/python3 '+quote(script)+'\nIcon=utilities-terminal\nTerminal=false\nDBusActivatable=false\nCategories=Utility;\n')
    (output/'config/kwinrc').write_text('[Compositing]\nEnabled=false\n[Desktops]\nNumber=1\nName_1=Private native menu test\n')
    (output/'config/kdeglobals').write_text((REPO/'colors/DomainOS-SR10.4.colors').read_text())
    environment.update(QT_QPA_PLATFORM='xcb',QT_QPA_PLATFORMTHEME='generic',QT_QUICK_BACKEND='software',QML_DISABLE_DISK_CACHE='1',LIBGL_ALWAYS_SOFTWARE='1',KWIN_COMPOSE='N',XDG_SESSION_TYPE='x11',XDG_CURRENT_DESKTOP='NONE',XDG_DATA_DIRS='/usr/local/share:/usr/share',XDG_CONFIG_DIRS='/etc/xdg',LANG='C.UTF-8',LC_ALL='C.UTF-8',GIO_USE_VFS='local',DBUS_SYSTEM_BUS_ADDRESS='unix:path='+str(output/'no-system-bus'),PULSE_SERVER='unix:'+str(output/'no-audio'),IRIX_DOMAINOS_APPLICATIONS_PRIVATE_SESSION='1')
    flags=shlex.split(subprocess.check_output(['pkg-config','--cflags','--libs','Qt6Widgets','Qt6Test'],text=True))
    subprocess.run(['c++','-shared','-fPIC','-std=c++17',str(REPO/'plasma/tests/domainos-application-interface-host.cpp'),'-o',str(output/'applications-host.so'),*flags,'-ldl'],check=True)
    cache=subprocess.run(['kbuildsycoca6','--noincremental'],env=dict(environment,QT_QPA_PLATFORM='offscreen'),capture_output=True,text=True,timeout=20)
    (output/'sycoca.log').write_text(cache.stdout+cache.stderr)
    bus=output/'bus.conf';bus.write_text('<busconfig><type>session</type><listen>unix:tmpdir='+str(output/'runtime')+'</listen><auth>EXTERNAL</auth><policy context="default"><allow send_destination="*"/><allow receive_sender="*"/><allow own="*"/></policy></busconfig>')
    with (output/'runner.log').open('w') as log:
        completed=subprocess.run(['xvfb-run','-a','-s','-screen 0 1200x900x24 -nolisten tcp','dbus-run-session','--config-file',str(bus),'--',sys.executable,str(Path(__file__).resolve()),'--worker','--saida',str(output)],env=environment,stdout=log,stderr=subprocess.STDOUT,timeout=45)
    native=json.loads((output/'native.json').read_text()) if (output/'native.json').is_file() else {}
    checks=native.get('checks',{})
    diagnostics=[line for line in (output/'host.log').read_text().splitlines() if re.search(r'ReferenceError:|TypeError:|SyntaxError:|Cannot assign|Binding loop|is not a type|Type .+ unavailable|module .+ is not installed',line)] if (output/'host.log').is_file() else ['Native host did not save diagnostics']
    checks.update(private_host_exited_cleanly=completed.returncode==0,native_scenario_finished_without_error=not native.get('failure'),qml_runtime_errors_zero=not diagnostics,
        real_profiles_unchanged=before==protected(),production_sources_unchanged=all(digest(REPO/name)==value for name,value in sources.items()),installed_native_menu_sources_unchanged=all(digest(Path(name))==value for name,value in native_sources.items()),
        no_native_menu_source_copied_into_test_package=not any(path.name=='MenuRepresentation.qml' for path in output.rglob('*.qml')))
    report={'status':'passed' if checks and all(checks.values()) else 'failed','checks':checks,'native':native,'qml_diagnostics':diagnostics,'source_sha256':sources,'native_source_sha256':native_sources,'protected_config_sha256':{'before':before,'after':protected()},
        'scope':'Installed KDE menu and native application launch, custom global application search outside the selected catalog source, permanent preferences in an empty drawer. Private KWin/Xvfb/D-Bus/applications only; two launches of the own marker entry, no user application or profile changed.'}
    (output/'RESULTADO.json').write_text(json.dumps(report,indent=2,ensure_ascii=False)+'\n')
    print(json.dumps({'status':report['status'],'checks':len(checks),'result':str(output/'RESULTADO.json'),'failure':native.get('failure')}))
    return 0 if report['status']=='passed' else 1


if __name__=='__main__':raise SystemExit(main())
