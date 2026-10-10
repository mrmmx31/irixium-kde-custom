#!/usr/bin/python3
# SPDX-FileCopyrightText: 2026 mrmmx31
# SPDX-License-Identifier: GPL-3.0-or-later
"""Directed real-page input, edit/Discard/Apply and restart in a private Plasma host.

Only public desktop metadata and public calendar provider IDs are used. No mail
application, PIM account, personal calendar or user session is launched/read.
Fixture Apply maps production cfg_* buffers to native Plasma KConfig; this does
not claim to test the stock AppletConfiguration dialog's framework Apply button.
"""
import argparse
import hashlib
import json
import os
from pathlib import Path
import re
import shlex
import shutil
import subprocess
import sys
import tempfile

sys.dont_write_bytecode = True
REPO = Path(__file__).resolve().parents[2]
APPLET = REPO / 'plasma/applets/org.irixclassic.domainos.panel'
IDENTIFIER = 'org.irixclassic.domainos.calendar.mail.preferences.test'
PAGES = ('ConfigCommands.qml', 'ConfigInstruments.qml', 'ConfigIconbox.qml')


def digest(path):
    return hashlib.sha256(path.read_bytes()).hexdigest() if path.is_file() else None


def fixture_qml():
    keys = {name: re.findall(r'property\s+(?:alias|var|string|bool|int)\s+cfg_(\w+)\s*:',
        (APPLET / 'contents/ui' / name).read_text()) for name in PAGES}
    return '''import QtQuick
import QtQuick.Controls as QQC
import QtQuick.Layouts
import org.kde.plasma.plasmoid
import org.kde.plasma.core as PlasmaCore
PlasmoidItem {
    id: host
    preferredRepresentation: fullRepresentation
    Plasmoid.backgroundHints: PlasmaCore.Types.NoBackground
    fullRepresentation: Item {
        id: fixture
        objectName: "domainosCalendarMailPreferenceFixture"
        implicitWidth: 860; implicitHeight: 1100
        Layout.minimumWidth: 860; Layout.minimumHeight: 1100
        property string activePage: "ConfigCommands.qml"
        readonly property var page: loader.item
        readonly property var pageKeys: '''+json.dumps(keys)+'''
        readonly property string savedJson: {
            const values = {};
            for (const key of Plasmoid.configuration.keys()) values[key] = Plasmoid.configuration[key];
            return JSON.stringify(values);
        }
        readonly property string mailChoicesJson: activePage === "ConfigCommands.qml" && loader.item
            ? JSON.stringify(loader.item.mailClientChoices) : "[]"
        function showPage(name) {
            activePage = name;
            const values = {};
            for (const key of pageKeys[name]) values["cfg_"+key] = Plasmoid.configuration[key];
            loader.setSource("", {});
            loader.setSource(name, values);
        }
        function apply() {
            for (const key of pageKeys[activePage]) Plasmoid.configuration[key] = loader.item["cfg_"+key];
            Plasmoid.configuration.writeConfig();
        }
        Loader { id: loader; anchors { left: parent.left; right: parent.right; top: parent.top; bottom: buttons.top; margins: 12 } }
        Row {
            id: buttons
            anchors { bottom: parent.bottom; right: parent.right; margins: 12 }
            spacing: 12
            QQC.Button { objectName: "domainosDirectedDiscard"; text: "Descartar"; onClicked: fixture.showPage(fixture.activePage) }
            QQC.Button { objectName: "domainosDirectedApply"; text: "Aplicar"; onClicked: fixture.apply() }
            QQC.Button { objectName: "domainosDirectedConfigure"; text: "Fontes nativas"; onClicked: Plasmoid.internalAction("configure").trigger() }
        }
        Component.onCompleted: {
            showPage("ConfigCommands.qml");
        }
    }
}
'''


def worker(output):
    if os.environ.get('IRIX_DOMAINOS_PREFS_PRIVATE_SESSION') != '1':
        raise RuntimeError('Private session required')
    outcomes = []
    for mode in ('edit', 'reload'):
        env = dict(os.environ, LD_PRELOAD=str(output / 'preferences-host.so'),
            IRIX_DOMAINOS_PREFS_MODE=mode, IRIX_DOMAINOS_PREFS_REPORT=str(output / (mode+'.json')),
            IRIX_DOMAINOS_PREFS_DIR=str(output))
        result = subprocess.run(['dbus-run-session', '--config-file='+str(output/'private-bus.conf'),
            '--', '/usr/bin/plasmawindowed', IDENTIFIER], env=env, capture_output=True, text=True, timeout=30)
        (output/(mode+'.log')).write_text(result.stdout+result.stderr)
        (output/(mode+'-exit.json')).write_text(json.dumps({'returncode':result.returncode})+'\n')
        outcomes.append(result.returncode)
        if result.returncode:
            break
    return 0 if outcomes == [0, 0] else 1


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--saida', type=Path, required=True)
    parser.add_argument('--worker', action='store_true', help=argparse.SUPPRESS)
    parser.add_argument('--somente-contagem', action='store_true', help='Only the new count opt-in checkbox, Discard/Apply and restart')
    args = parser.parse_args()
    if args.worker:
        return worker(args.saida)
    destination = args.saida.absolute()
    if not destination.is_relative_to(Path('/tmp')) or destination.exists():
        parser.error('Use a new output directory below /tmp')
    destination.mkdir(mode=0o700)
    sources = [APPLET/'contents/ui'/name for name in (*PAGES, 'ConfigUtils.js', 'DomainOSCategoryDefaults.qml')]
    sources += [APPLET/'contents/config/main.xml', APPLET/'contents/config/config.qml', APPLET/'contents/code/commands.py']
    source_before = {str(path):digest(path) for path in sources}
    protected = [Path.home()/'.config'/name for name in ('kdeglobals', 'plasmarc', 'kwinrc',
        'plasma-org.kde.plasma.desktop-appletsrc', 'plasma_calendar_holiday_regions', 'mimeapps.list')]
    protected_before = {str(path):digest(path) for path in protected}
    with tempfile.TemporaryDirectory(prefix='.qa-calendar-mail-', dir=REPO) as temporary:
        output = Path(temporary)
        env = os.environ.copy()
        for name in ('DISPLAY','WAYLAND_DISPLAY','DBUS_SESSION_BUS_ADDRESS','DBUS_STARTER_ADDRESS','DBUS_STARTER_BUS_TYPE',
            'SESSION_MANAGER','QML_IMPORT_PATH','QML2_IMPORT_PATH','QT_STYLE_OVERRIDE','QT_QUICK_CONTROLS_STYLE',
            'LD_PRELOAD','XAUTHORITY','XDG_SESSION_ID','KDE_FULL_SESSION','KDE_SESSION_VERSION','SSH_AUTH_SOCK'):
            env.pop(name,None)
        for key,name in (('HOME','home'),('XDG_CONFIG_HOME','config'),('XDG_DATA_HOME','data'),
            ('XDG_CACHE_HOME','cache'),('XDG_STATE_HOME','state'),('XDG_RUNTIME_DIR','runtime')):
            (output/name).mkdir(mode=0o700);env[key]=str(output/name)
        compiler = output/'compiler';compiler.mkdir(mode=0o700)
        package = output/'data/plasma/plasmoids'/IDENTIFIER
        shutil.copytree(APPLET,package,ignore=shutil.ignore_patterns('__pycache__','*.pyc'))
        (package/'metadata.json').write_text(json.dumps({'KPlugin':{'Id':IDENTIFIER,'Name':'Calendar/mail private preferences',
            'Version':'1.0','License':'GPL-3.0-or-later'},'KPackageStructure':'Plasma/Applet','X-Plasma-API-Minimum-Version':'6.0'}))
        (package/'contents/ui/main.qml').write_text(fixture_qml())
        apps=output/'data/applications';apps.mkdir()
        for label in ('alpha','beta'):
            (apps/('domainos-qa-'+label+'.desktop')).write_text('[Desktop Entry]\nType=Application\nName=DomainOS QA '+label.title()+
                '\nExec=/usr/bin/false\nIcon=mail-client\nTerminal=false\nMimeType=x-scheme-handler/mailto;\n')
        mime=output/'config/mimeapps.list'
        mime.write_text('[Default Applications]\nx-scheme-handler/mailto=domainos-qa-alpha.desktop;\n')
        mime_before=digest(mime)
        # The actual provider is selected, but this test does not load a personal
        # PIM calendar or account. Region data remains private and public.
        (output/'config/plasma_calendar_holiday_regions').write_text('[General]\nselectedRegions=us_en-us\n')
        flags=shlex.split(subprocess.check_output(['pkg-config','--cflags','--libs','Qt6Widgets','Qt6Test'],text=True))
        subprocess.run(['c++','-std=c++17','-shared','-fPIC',str(REPO/'plasma/tests/domainos-calendar-mail-preferences-host.cpp'),
            '-o',str(output/'preferences-host.so'),*flags,'-ldl'],check=True,env=dict(os.environ,TMPDIR=str(compiler)),timeout=30)
        (output/'private-bus.conf').write_text('<busconfig><type>session</type><listen>unix:tmpdir=/tmp</listen><auth>EXTERNAL</auth>'
            '<policy context="default"><allow send_destination="*"/><allow receive_sender="*"/><allow own="*"/></policy></busconfig>')
        env.update(TMPDIR=str(compiler),XDG_DATA_DIRS='/usr/local/share:/usr/share',XDG_CONFIG_DIRS='/etc/xdg',
            XDG_CURRENT_DESKTOP='NONE',XDG_SESSION_TYPE='x11',QT_QPA_PLATFORM='xcb',QT_QPA_PLATFORMTHEME='generic',
            QT_QUICK_BACKEND='software',QT_SCALE_FACTOR='1',LIBGL_ALWAYS_SOFTWARE='1',
            DBUS_SYSTEM_BUS_ADDRESS='unix:path='+str(output/'no-system-bus'),PULSE_SERVER='unix:'+str(output/'no-audio-server'),
            LANG='en_US.UTF-8',LC_ALL='en_US.UTF-8',IRIX_DOMAINOS_PREFS_PRIVATE_SESSION='1')
        if args.somente_contagem:
            env['IRIX_DOMAINOS_PREFS_SCENARIO']='counts'
        sycoca=subprocess.run(['kbuildsycoca6','--noincremental'],env=dict(env,QT_QPA_PLATFORM='offscreen'),capture_output=True,text=True,timeout=20)
        (output/'sycoca.log').write_text(sycoca.stdout+sycoca.stderr)
        result=subprocess.run(['xvfb-run','--auto-servernum','--server-args=-screen 0 1300x1250x24',sys.executable,
            str(Path(__file__).resolve()),'--saida',str(output),'--worker'],env=env,capture_output=True,text=True,timeout=65)
        (output/'session.log').write_text(result.stdout+result.stderr)
        natives={mode:json.loads((output/(mode+'.json')).read_text()) if (output/(mode+'.json')).exists() else {} for mode in ('edit','reload')}
        checks={mode+'_'+name:value for mode,native in natives.items() for name,value in native.get('checks',{}).items()}
        logs='\n'.join(path.read_text() for path in output.glob('*.log'))
        errors=[line for line in logs.splitlines() if re.search(r'ReferenceError:|TypeError:|SyntaxError:|Cannot assign|Binding loop|is not a type|error when loading applet',line)]
        checks.update(private_host_edit_and_restart_completed=result.returncode==0 and all(natives.values()) and not any(n.get('failure') for n in natives.values()),
            qml_runtime_errors_zero=not errors,production_sources_unchanged=source_before=={str(path):digest(path) for path in sources},
            six_personal_preferences_unchanged=protected_before=={str(path):digest(path) for path in protected},
            private_mailto_preference_unchanged=digest(mime)==mime_before,
            own_hosts_exited=all(n.get('host_pid') and not Path('/proc',str(n['host_pid'])).exists() for n in natives.values()))
        report={'status':'passed' if all(checks.values()) else 'failed','checks':checks,'native':natives,
            'scenario':'counts-only' if args.somente_contagem else 'calendar-client-thumbnails',
            'scope':__doc__,'source_hashes':source_before,'protected_preferences':{'before':protected_before,'after':{str(path):digest(path) for path in protected}},
            'qml_diagnostics':errors,'returncode':result.returncode}
        (destination/'RESULTADO.json').write_text(json.dumps(report,indent=2,ensure_ascii=False)+'\n')
        for path in output.iterdir():
            if path.is_file() and path.suffix in ('.json','.log','.png'):
                shutil.copy2(path,destination/path.name)
        if (output/'config/plasmawindowed-appletsrc').exists():
            shutil.copy2(output/'config/plasmawindowed-appletsrc',destination/'PRIVATE-KCONFIG.ini')
    print(json.dumps({'status':report['status'],'checks':len(checks),'failed':[name for name,ok in checks.items() if not ok],
        'failures':{mode:n.get('failure') for mode,n in natives.items()},'report':str(destination/'RESULTADO.json')},ensure_ascii=False))
    return 0 if report['status']=='passed' else 1


if __name__=='__main__':raise SystemExit(main())
