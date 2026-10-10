#!/usr/bin/env python3
# SPDX-FileCopyrightText: 2026 IRIX Classic contributors
# SPDX-License-Identifier: GPL-3.0-or-later
"""Prove the drawer's native shared favorites and independent taskbar pins.

Private Plasma/Kicker/Xvfb/KWin/activity daemon/bus; three owned Desktop Entries.
Profiles and caches are temporary in the workspace, only evidence goes under /tmp.
No personal favorite, panel, task, account or compositor is modified.
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
import tarfile
import tempfile

sys.dont_write_bytecode = True
REPO = Path(__file__).resolve().parents[2]
APPLET = REPO/'plasma/applets/org.irixclassic.domainos.panel'
IDENTIFIER = 'org.irixclassic.domainos.drawer.favorites.test'


def digest(path):
    return hashlib.sha256(path.read_bytes()).hexdigest() if path.is_file() else None


def worker(output):
    spec = importlib.util.spec_from_file_location('private_applications_session',
        REPO/'plasma/tools/testar-domainos-aplicativos.py')
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    module.IDENTIFIER = IDENTIFIER
    return module.session(output)


QML = '''import QtQuick
import QtQuick.Layouts
import org.kde.plasma.plasmoid
import org.kde.plasma.private.kicker as Kicker
import org.kde.taskmanager as TaskManager
import "../../../org.irixclassic.domainos.panel/contents/ui" as Panel
PlasmoidItem {
    id:host
    preferredRepresentation:fullRepresentation
    fullRepresentation:Item {
        id:fixture;objectName:"domainosDrawerFavoritesFixture"
        Layout.minimumWidth:600;Layout.minimumHeight:180
        Layout.preferredWidth:600;Layout.preferredHeight:180
        property int configureRequests:0
        property int pinLaunchRequests:0
        property int dispatchBegins:0
        property var dispatchReports:[]
        property string ownRequestedFirst:""
        property string peerRequestedFirst:""
        readonly property var entries:["domainos-favorite-alpha.desktop","domainos-favorite-beta.desktop","domainos-favorite-gamma.desktop"]
        function rows(repeater) {
            let result=[]
            for(let row=0;row<repeater.count;row++) {
                const item=repeater.itemAt(row)
                if(item)result.push({favoriteId:item.favoriteId,title:item.title})
            }
            return result
        }
        function state() {
            let bridge=null
            function visit(item) {if(item.objectName==="domainosKdeApplicationMenu")bridge=item;for(const child of item.children || [])visit(child)}
            visit(apps)
            let drawer=[]
            for(let row=0;row<apps.sharedFavoritesModel.count;row++)drawer.push(apps.favoriteInfo(row))
            return JSON.stringify({popup:apps.popupVisible,pins:fixtureSettings.pinnedApplications.slice(),drawer:drawer,
                orderBusy:apps.favoriteOrderBusy,orderSequence:apps.favoriteOrderSequence,
                orderMessage:apps.favoriteOrderMessage,orderOrigin:apps.favoriteOrderOrigin,overlay:apps.externalFavoriteOrder.slice(),
                native:rows(nativeRows),peer:rows(peerRows),configureRequests:configureRequests,pinLaunchRequests:pinLaunchRequests,
                dispatchBegins:dispatchBegins,dispatchReports:dispatchReports,ownRequestedFirst:ownRequestedFirst,peerRequestedFirst:peerRequestedFirst,
                nativeFavoriteClass:String(apps.sharedFavoritesModel),peerFavoriteClass:String(peer.favoritesModel),
                nativeKdeMenuSameFavorites:bridge ? bridge.globalFavorites===apps.sharedFavoritesModel : false})
        }
        function action(name) {
            if(name==="seed") {for(const id of entries)peer.favoritesModel.addFavorite(id);apps.showDrawer(anchor);return true}
            if(name==="peerRemove") {peer.favoritesModel.removeFavorite(entries[1]);return true}
            if(name==="peerAdd") {peer.favoritesModel.addFavorite(entries[1]);return true}
            if(name==="ownMove") {ownRequestedFirst=String(nativeRows.itemAt(2).favoriteId);apps.sharedFavoritesModel.moveRow(2,0);return true}
            if(name==="peerMove") {
                // Make independent-client order observable: choose a member
                // different from the DomainOS provider's current first row.
                const ownFirst=String(nativeRows.itemAt(0).favoriteId)
                for(let row=1;row<peerRows.count;row++) {
                    const id=String(peerRows.itemAt(row).favoriteId)
                    if(id!==ownFirst) {peerRequestedFirst=id;peer.favoritesModel.moveRow(row,0);return true}
                }
                return false
            }
            if(name==="drawer") {apps.close();apps.showDrawer(anchor);return true}
            if(name==="coalesced") {
                for(let count=0;count<4;count++){apps.close();apps.showDrawer(anchor)}
                return true
            }
            if(name==="protocolFailures") {
                const saved=JSON.stringify(apps.externalFavoriteOrder),savedMessage=apps.favoriteOrderMessage
                let checks={}
                apps.favoriteOrderCommand="fixture-response";apps.favoriteOrderToken="expected"
                apps.pendingFavoriteOrderGeneration=apps.favoriteOrderGeneration
                apps.pendingFavoriteOrderActivity=fixtureActivity.currentActivity
                apps.handleFavoriteOrderResult("foreign-response",{stdout:"{}"})
                checks.foreign_response_does_not_release_owned_request=apps.favoriteOrderBusy
                apps.handleFavoriteOrderResult("fixture-response",{stdout:JSON.stringify({ok:true,token:"wrong",order:["bad.desktop"]})})
                checks.wrong_token_does_not_replace_order=!apps.favoriteOrderBusy && JSON.stringify(apps.externalFavoriteOrder)===saved
                apps.favoriteOrderCommand="fixture-stale";apps.favoriteOrderToken="expected"
                apps.pendingFavoriteOrderGeneration=apps.favoriteOrderGeneration-1
                apps.handleFavoriteOrderResult("fixture-stale",{stdout:JSON.stringify({ok:true,token:"expected",order:["bad.desktop"]})})
                checks.stale_opening_does_not_replace_order=!apps.favoriteOrderBusy && JSON.stringify(apps.externalFavoriteOrder)===saved
                apps.favoriteOrderCommand="fixture-failed";apps.favoriteOrderToken="expected"
                apps.pendingFavoriteOrderGeneration=apps.favoriteOrderGeneration
                apps.pendingFavoriteOrderActivity=fixtureActivity.currentActivity
                apps.handleFavoriteOrderResult("fixture-failed",{stdout:"malformed JSON"})
                checks.malformed_result_releases_request_and_preserves_members=!apps.favoriteOrderBusy && JSON.stringify(apps.externalFavoriteOrder)===saved
                apps.handleFavoriteOrderResult("fixture-failed",{stdout:JSON.stringify({ok:true,token:"expected",order:["bad.desktop"]})})
                checks.duplicate_result_does_not_replace_order=JSON.stringify(apps.externalFavoriteOrder)===saved
                apps.favoriteOrderCommand="fixture-activity";apps.favoriteOrderToken="expected"
                apps.pendingFavoriteOrderGeneration=apps.favoriteOrderGeneration
                apps.pendingFavoriteOrderActivity="another-activity"
                apps.handleFavoriteOrderResult("fixture-activity",{stdout:JSON.stringify({ok:true,token:"expected",order:["bad.desktop"]})})
                checks.old_activity_result_does_not_replace_order=!apps.favoriteOrderBusy && JSON.stringify(apps.externalFavoriteOrder)===saved
                let many=[]
                for(let row=0;row<32;++row)many.push({favoriteId:"unknown-"+row,providerRow:row})
                const sorted=apps.orderFavoriteRows(many,["unknown-31","unknown-2"])
                let expected=[31,2]
                for(let row=0;row<31;++row)if(row!==2)expected.push(row)
                checks.thirty_two_unranked_members_preserve_native_order=JSON.stringify(sorted.map(row=>row.providerRow))===JSON.stringify(expected)
                apps.favoriteOrderMessage=savedMessage
                return JSON.stringify(checks)
            }
            if(name==="kde") {fixtureSettings.applicationsMenuStyle="kde";apps.showDrawer(anchor);return true}
            return false
        }
        TaskManager.ActivityInfo { id:fixtureActivity }
        QtObject {
            id:fixtureSettings
            property var pinnedApplications:["domainos-favorite-gamma.desktop","domainos-favorite-alpha.desktop"]
            property string applicationsMenuStyle:"domainos"
        }
        QtObject {
            id:fixtureCommands
            function openApplication(id){fixture.pinLaunchRequests++;return false}
            function begin(label){fixture.dispatchBegins++;return fixture.dispatchBegins}
            function finish(token,result){fixture.dispatchReports=fixture.dispatchReports.concat([result])}
            function reported(result){fixture.dispatchReports=fixture.dispatchReports.concat([result])}
        }
        Panel.DomainOSApplications {
            id:apps;hostItem:host;settings:fixtureSettings;commands:fixtureCommands
            onConfigureRequested:fixture.configureRequests++
            onPinListRequested:pins=>fixtureSettings.pinnedApplications=pins.slice()
        }
        Kicker.RootModel {
            id:peer;appletInterface:host;flat:true;showAllApps:true;showPowerSession:false
            Component.onCompleted:favoritesModel.initForClient("org.kde.plasma.kicker.favorites.instance-42")
        }
        Repeater {
            id:nativeRows;model:apps.sharedFavoritesModel
            delegate:Item {required property var model;readonly property string favoriteId:String(model.favoriteId || "");readonly property string title:String(model.display || "");visible:false}
        }
        Repeater {
            id:peerRows;model:peer.favoritesModel
            delegate:Item {required property var model;readonly property string favoriteId:String(model.favoriteId || "");readonly property string title:String(model.display || "");visible:false}
        }
        Rectangle {anchors.fill:parent;color:"#7894a7"}
        Item {id:anchor;x:120;y:40;width:100;height:40}
    }
}
'''


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--saida', type=Path, required=True)
    parser.add_argument('--worker', action='store_true', help=argparse.SUPPRESS)
    args = parser.parse_args()
    output = args.saida.absolute()
    if args.worker:
        return worker(output)
    if output.exists() or not output.is_relative_to(Path('/tmp')) or output == Path('/tmp') \
            or any(p.is_symlink() for p in output.parents):
        parser.error('Use a new directory under /tmp, without links')
    output.mkdir(mode=0o700)
    report_output=output
    evidence_workspace=tempfile.TemporaryDirectory(prefix='.domainos-fav-evidence-',dir=REPO)
    output=Path(evidence_workspace.name)
    config = Path(os.environ.get('XDG_CONFIG_HOME', str(Path.home()/'.config')))
    protected = lambda: {str(config/name):digest(config/name) for name in
        ('kdeglobals','kwinrc','plasmarc','plasma-org.kde.plasma.desktop-appletsrc')}
    before = protected()
    # Other agents can still edit unrelated Iconbox/Pager components. Hash the
    # drawer and its direct shared dependencies, never imply full-release freeze.
    dependencies=('ui/DomainOSApplications.qml','ui/DomainOSApplicationMenu.qml',
        'ui/DomainOSKdeApplicationMenu.qml','ui/DomainOSControlPalette.qml',
        'ui/DomainOSPopupToggle.qml','ui/DomainOSPalette.qml','code/ApplicationActions.js',
        'code/favorite_order.py','code/pin_import.py')
    sources = {str((APPLET/'contents'/name).relative_to(REPO)):digest(APPLET/'contents'/name)
        for name in dependencies}
    with tempfile.TemporaryDirectory(prefix='.domainos-fav-',dir=REPO) as private, \
            tempfile.TemporaryDirectory(prefix='.ird-fav-',dir=REPO) as runtime:
        fixture = Path(private)
        environment = dict(os.environ)
        for key in ('DISPLAY','WAYLAND_DISPLAY','WAYLAND_SOCKET','DBUS_SESSION_BUS_ADDRESS',
                'DBUS_STARTER_ADDRESS','DBUS_STARTER_BUS_TYPE','SESSION_MANAGER','LD_PRELOAD',
                'QML_IMPORT_PATH','QML2_IMPORT_PATH','XAUTHORITY','QT_STYLE_OVERRIDE',
                'QT_QUICK_CONTROLS_STYLE','KDE_FULL_SESSION','KDE_SESSION_VERSION',
                'XDG_SESSION_ID','PULSE_SERVER','PULSE_COOKIE','PIPEWIRE_REMOTE'):
            environment.pop(key,None)
        for key,name in (('HOME','home'),('XDG_CONFIG_HOME','config'),('XDG_DATA_HOME','data'),
                ('XDG_CACHE_HOME','cache'),('XDG_STATE_HOME','state')):
            path=fixture/name;path.mkdir(mode=0o700);environment[key]=str(path)
        environment['XDG_RUNTIME_DIR']=runtime
        plasmoids=fixture/'data/plasma/plasmoids'
        shutil.copytree(APPLET,plasmoids/'org.irixclassic.domainos.panel',
            ignore=shutil.ignore_patterns('__pycache__','*.pyc'))
        own=plasmoids/IDENTIFIER
        (own/'contents/ui').mkdir(parents=True)
        (own/'contents/config').mkdir()
        shutil.copy2(APPLET/'contents/config/main.xml',own/'contents/config/main.xml')
        (own/'metadata.json').write_text(json.dumps({'KPlugin':{'Id':IDENTIFIER,
            'Name':'Private DomainOS drawer favorites proof','Version':'1.0',
            'License':'GPL-3.0-or-later'},'KPackageStructure':'Plasma/Applet',
            'X-Plasma-API-Minimum-Version':'6.0'}))
        (own/'contents/ui/main.qml').write_text(QML)
        apps=fixture/'data/applications';apps.mkdir()
        marker=output/'dispatch.txt';launch=fixture/'owned-marker.py'
        launch.write_text('from pathlib import Path\nimport sys\nwith Path('+repr(str(marker))
            +').open("a") as f:f.write(sys.argv[1]+"\\n")\n')
        quote=lambda value:'"'+str(value).replace('\\','\\\\').replace('"','\\"')+'"'
        for name in ('alpha','beta','gamma'):
            desktop='domainos-favorite-'+name+'.desktop'
            (apps/desktop).write_text('[Desktop Entry]\nType=Application\nName=DomainOS Favorite '
                +name.title()+'\nExec=/usr/bin/python3 '+quote(launch)+' '+desktop
                +'\nIcon=utilities-terminal\nTerminal=false\nDBusActivatable=false\nCategories=Utility;\n')
        (fixture/'config/kwinrc').write_text('[Compositing]\nEnabled=false\n[Desktops]\nNumber=1\nName_1=Private drawer proof\n')
        (fixture/'config/plasma-org.kde.plasma.desktop-appletsrc').write_text('[Containments][77][Applets][42]\nplugin=org.kde.plasma.kicker\n')
        (fixture/'config/kdeglobals').write_text((REPO/'colors/DomainOS-SR10.4.colors').read_text())
        environment.update(QT_QPA_PLATFORM='xcb',QT_QPA_PLATFORMTHEME='generic',
            QT_QUICK_BACKEND='software',QML_DISABLE_DISK_CACHE='1',LIBGL_ALWAYS_SOFTWARE='1',
            KWIN_COMPOSE='N',XDG_SESSION_TYPE='x11',XDG_CURRENT_DESKTOP='NONE',
            XDG_DATA_DIRS='/usr/local/share:/usr/share',XDG_CONFIG_DIRS='/etc/xdg',
            LANG='C.UTF-8',LC_ALL='C.UTF-8',GIO_USE_VFS='local',
            DBUS_SYSTEM_BUS_ADDRESS='unix:path='+str(fixture/'no-system-bus'),
            PULSE_SERVER='unix:'+str(fixture/'no-audio'),IRIX_DOMAINOS_APPLICATIONS_PRIVATE_SESSION='1')
        flags=shlex.split(subprocess.check_output(['pkg-config','--cflags','--libs','Qt6Widgets','Qt6Test'],text=True))
        compiler=fixture/'compiler';compiler.mkdir(mode=0o700)
        environment['TMPDIR']=str(compiler)
        subprocess.run(['c++','-shared','-fPIC','-std=c++17',
            str(REPO/'plasma/tests/domainos-drawer-favorites-host.cpp'),
            '-o',str(output/'applications-host.so'),*flags,'-ldl'],check=True,
            env=dict(os.environ,TMPDIR=str(compiler)),timeout=30)
        cache=subprocess.run(['kbuildsycoca6','--noincremental'],
            env=dict(environment,QT_QPA_PLATFORM='offscreen'),capture_output=True,text=True,timeout=20)
        (output/'sycoca.log').write_text(cache.stdout+cache.stderr)
        bus=fixture/'bus.conf'
        bus.write_text('<busconfig><type>session</type><listen>unix:tmpdir='+runtime
            +'</listen><auth>EXTERNAL</auth><policy context="default"><allow send_destination="*"/>'
            +'<allow receive_sender="*"/><allow own="*"/></policy></busconfig>')
        with (output/'runner.log').open('w') as log:
            completed=subprocess.run(['xvfb-run','-a','-s','-screen 0 1200x900x24 -nolisten tcp',
                'dbus-run-session','--config-file',str(bus),'--',sys.executable,
                str(Path(__file__).resolve()),'--worker','--saida',str(output)],
                env=environment,stdout=log,stderr=subprocess.STDOUT,timeout=50)
        with tarfile.open(report_output/'EVIDENCIAS.tar.gz','w:gz') as archive:
            archive.add(fixture,arcname='private')
            for artifact in output.iterdir():
                if artifact.is_file() and artifact.suffix in ('.json','.log','.png'):
                    archive.add(artifact,arcname='evidence/'+artifact.name)
    native=json.loads((output/'native.json').read_text()) if (output/'native.json').is_file() else {}
    checks=native.get('checks',{})
    diagnostics=[line for line in (output/'host.log').read_text().splitlines()
        if re.search(r'ReferenceError:|TypeError:|SyntaxError:|Cannot assign|Binding loop|is not a type|Type .+ unavailable|module .+ is not installed',line)] if (output/'host.log').is_file() else ['Native host did not save diagnostics']
    cleanup=json.loads((output/'cleanup.json').read_text()) if (output/'cleanup.json').is_file() else {}
    checks.update(private_host_exited_cleanly=completed.returncode==0,
        native_scenario_finished_without_error=not native.get('failure'),
        qml_runtime_errors_zero=not diagnostics,real_profiles_unchanged=before==protected(),
        production_sources_unchanged=all(digest(REPO/name)==value for name,value in sources.items()),
        own_daemons_stopped=cleanup.get('own_daemons_exited') is True)
    report={'status':'passed' if checks and all(checks.values()) else 'failed',
        'checks':checks,'native':native,'qml_diagnostics':diagnostics,'source_sha256':sources,
        'protected_config_sha256':{'before':before,'after':protected()},
        'scope':'Production drawer read-only order overlay and genuine external KAStats/Kicker client 42 in private Plasma/KWin/Xvfb/activity service/bus. Private appletsrc identifies that external menu. Three owned Desktop Entries and two independent taskbar pins. Real pointers, peer move then drawer reopen, identity launch and unchanged stats/appsrc across reads; explicit injected malformed/stale replies only for protocol defenses. No personal favorites/profile/window/compositor changed.'}
    (report_output/'RESULTADO.json').write_text(json.dumps(report,indent=2,ensure_ascii=False)+'\n')
    evidence_workspace.cleanup()
    print(json.dumps({'status':report['status'],'checks':len(checks),
        'result':str(report_output/'RESULTADO.json'),'failure':native.get('failure')}))
    return 0 if report['status']=='passed' else 1


if __name__=='__main__':
    raise SystemExit(main())
