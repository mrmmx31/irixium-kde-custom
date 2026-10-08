#!/usr/bin/env python3
# SPDX-FileCopyrightText: 2026 IRIX Classic contributors
# SPDX-License-Identifier: GPL-3.0-or-later
"""Load the unchanged DomainOS KPackage in private plasmawindowed/Xvfb.

Optional native test tools: Qt 6 headers, C++, pkg-config, Xvfb,
dbus-run-session, kpackagetool6 and plasmawindowed. No user theme, desktop,
workspace, application, device or button action is changed or exercised.
"""
import sys

sys.dont_write_bytecode = True

import argparse
import hashlib
import json
import os
from pathlib import Path
import re
import shlex
import shutil
import subprocess
import tempfile

REPO=Path(__file__).resolve().parents[2]
IDENTIFIER='org.irixclassic.domainos.panel'


def sha256(path):return hashlib.sha256(path.read_bytes()).hexdigest()


def hashes(root):
    return {str(p.relative_to(root)):sha256(p) for p in sorted(root.rglob('*')) if p.is_file() and '__pycache__' not in p.parts}


def main():
    parser=argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--saida',type=Path,help='New/empty output directory; default a new /tmp directory')
    args=parser.parse_args()
    for tool in ('c++','pkg-config','xvfb-run','dbus-run-session','kpackagetool6','plasmawindowed'):
        if not shutil.which(tool):parser.error('Missing optional native test tool: '+tool)
    output=args.saida.resolve() if args.saida else Path(tempfile.mkdtemp(prefix='irix-domainos-package-'))
    if output.exists() and any(output.iterdir()):parser.error('Output directory must be new or empty')
    output.mkdir(parents=True,exist_ok=True)
    source=REPO/'plasma/applets'/IDENTIFIER
    source_before=hashes(source)
    fixture=output/'fixture';fixture.mkdir()
    paths={name:fixture/name for name in ('home','data','config','cache','state','runtime')}
    for path in paths.values():path.mkdir(mode=0o700)
    applet=paths['data']/'plasma/plasmoids'/IDENTIFIER
    shutil.copytree(source,applet,ignore=shutil.ignore_patterns('__pycache__','*.pyc'))
    copied=hashes(applet);assert copied==source_before,'Production package copy changed bytes'
    style_inventories={}
    for name in ('IrixClassic','IrixClassicDomainOS'):
        style=REPO/'plasma'/name;target=paths['data']/'plasma/desktoptheme'/name
        shutil.copytree(style,target,ignore=shutil.ignore_patterns('__pycache__','*.pyc'))
        style_inventories[name]={'source_sha256':hashes(style),'staged_matches_source':hashes(style)==hashes(target)}
    (paths['config']/'plasmarc').write_text('[Theme]\nname=IrixClassicDomainOS\n')
    (paths['config']/'kdeglobals').write_text((REPO/'plasma/IrixClassicDomainOS/colors').read_text())
    # No service directories: this isolated session bus cannot activate daemons.
    bus=fixture/'private-bus.conf'
    bus.write_text('<!DOCTYPE busconfig PUBLIC "-//freedesktop//DTD D-Bus Bus Configuration 1.0//EN"\n"http://www.freedesktop.org/standards/dbus/1.0/busconfig.dtd">\n<busconfig><type>session</type><listen>unix:tmpdir=/tmp</listen><auth>EXTERNAL</auth><policy context="default"><allow send_destination="*"/><allow receive_sender="*"/><allow own="*"/></policy></busconfig>\n')
    env=os.environ.copy()
    for name in ('DISPLAY','WAYLAND_DISPLAY','DBUS_SESSION_BUS_ADDRESS','DBUS_STARTER_ADDRESS','DBUS_STARTER_BUS_TYPE','SESSION_MANAGER','LD_PRELOAD','QML_IMPORT_PATH','QML2_IMPORT_PATH','QT_STYLE_OVERRIDE','QT_QUICK_CONTROLS_STYLE','XDG_SESSION_ID','KDE_FULL_SESSION','KDE_SESSION_VERSION'):env.pop(name,None)
    env.update(HOME=str(paths['home']),XDG_DATA_HOME=str(paths['data']),XDG_CONFIG_HOME=str(paths['config']),XDG_CACHE_HOME=str(paths['cache']),XDG_STATE_HOME=str(paths['state']),XDG_RUNTIME_DIR=str(paths['runtime']),XDG_DATA_DIRS='/usr/local/share:/usr/share',XDG_CONFIG_DIRS='/etc/xdg',XDG_CURRENT_DESKTOP='NONE',XDG_SESSION_TYPE='x11',QT_QPA_PLATFORM='xcb',QT_QPA_PLATFORMTHEME='generic',QT_ACCESSIBILITY='0',QT_QUICK_BACKEND='software',LIBGL_ALWAYS_SOFTWARE='1',DBUS_SYSTEM_BUS_ADDRESS='unix:path='+str(paths['runtime']/'no-system-bus'))
    helper_source=REPO/'plasma/tests/domainos-package-host.cpp';helper=output/'domainos-package-host.so'
    flags=shlex.split(subprocess.check_output(['pkg-config','--cflags','--libs','Qt6Widgets'],text=True))
    subprocess.run(['c++','-std=c++17','-shared','-fPIC',str(helper_source),'-o',str(helper),*flags,'-ldl'],check=True)
    discovery_env=dict(env,QT_QPA_PLATFORM='offscreen')
    discovered=subprocess.run(['kpackagetool6','--type','Plasma/Applet','--list'],env=discovery_env,text=True,stdout=subprocess.PIPE,stderr=subprocess.STDOUT,timeout=15)
    (output/'package-list.log').write_text(discovered.stdout)
    capture=output/'DomainOS-production-package.png';native_file=output/'native-host.json'
    command=['xvfb-run','--auto-servernum','--server-args=-screen 0 2200x850x24','dbus-run-session','--config-file',str(bus),'--','env','LD_PRELOAD='+str(helper),'IRIX_DOMAINOS_CAPTURE='+str(capture),'IRIX_DOMAINOS_REPORT='+str(native_file),'plasmawindowed',IDENTIFIER]
    result=subprocess.run(command,env=env,text=True,stdout=subprocess.PIPE,stderr=subprocess.STDOUT,timeout=30)
    (output/'native-host.log').write_text(result.stdout)
    native=json.loads(native_file.read_text()) if native_file.is_file() else {}
    qml_errors=[line for line in result.stdout.splitlines() if re.search(r'(?:ReferenceError:|TypeError:|SyntaxError:|module .+ is not installed|Type .+ unavailable|is not a type|Cannot assign|Error loading QML|Failed to load QML|QML (?:Image|Item|Rectangle|Text):|Image: Cannot open)',line)]
    images=native.get('images',[]); loaded={Path(record['source']).name for record in images if record.get('status')==1}
    expected_png={'desk.png','xterm.png','winterm.png','john.png','index.png','downl.png'}
    expected_svg={'metal-weave.svg','metal-lines.svg','clock-face.svg','graph-reference.svg','mail.svg'}
    names=set(native.get('object_names',[]))
    checks={'kpackage_metadata_discovered':discovered.returncode==0 and IDENTIFIER in discovered.stdout,
            'production_source_copy_byte_identical':source_before==copied,
            'production_sources_unchanged':source_before==hashes(source),
            'two_independent_styles_staged':all(v['staged_matches_source'] for v in style_inventories.values()),
            'native_process_exit_zero':result.returncode==0,
            'production_full_representation_loaded':native.get('production_panel_loaded') is True,
            'production_full_representation_visible':native.get('production_panel_visible') is True,
            'production_class_is_domainos_panel':native.get('panel_class','').startswith('DomainOSPanel_QMLTYPE'),
            'public_qt_quick_abi_checked':native.get('public_quick_symbols') is True,
            'preferred_size_rendered':native.get('drawing_scale',0)>=.95,
            'native_capture_saved':native.get('captured') is True and capture.is_file(),
            'all_production_images_ready':native.get('all_production_images_ready') is True,
            'all_six_unique_sgi_bitmaps_decoded':expected_png<=loaded,
            'all_seven_iconbox_instances_present':native.get('sgi_iconbox_image_items')==7,
            'native_textures_clock_graph_mail_decoded':expected_svg<=loaded,
            'requested_fonts_resolve_without_family_fallback':bool(native.get('rendered_fonts')) and all(record['resolved']==record['requested'] or record['resolved'].startswith(record['requested']+' [') for record in native.get('rendered_fonts',[])),
            'fixed_modules_present':{'domainosInstitutional','domainosIconbox','domainosPager','domainosTray','domainosTrayNavigation','domainosLowerRail'}<=names,
            'two_workspace_design_blocks':native.get('workspace_count')==2,
            'two_by_three_tray_design_grid':native.get('tray_rows')==2 and native.get('tray_columns')==3,
            'actions_await_confirmation':native.get('phase')=='design-awaiting-button-confirmations' and native.get('actions_exercised') is False,
            'qml_errors_zero':not qml_errors}
    report={'format':1,'status':'passed' if all(checks.values()) else 'failed','checks':checks,'native':native,'qml_errors':qml_errors,'styles':style_inventories,'production_source_sha256':source_before,'helper_sha256':sha256(helper_source),'qt_compiled':subprocess.check_output(['pkg-config','--modversion','Qt6Widgets'],text=True).strip(),'commands':{'native_host':command,'package_discovery':['kpackagetool6','--type','Plasma/Applet','--list']},'capture':str(capture),'logs':{'host':str(output/'native-host.log'),'package_discovery':str(output/'package-list.log')},'scope':'Real plasmawindowed KPackage fullRepresentation; production sources unchanged. Only the design and asset decoding are verified; button actions, live windows, workspaces and devices are deliberately not activated.','desktop_modified':False,'button_actions_exercised':False,'fixture_scope':str(fixture)}
    (output/'RESULTADO.json').write_text(json.dumps(report,ensure_ascii=False,indent=2)+'\n')
    print(json.dumps({'status':report['status'],'checks':checks,'report':str(output/'RESULTADO.json')},indent=2),flush=True)
    return 0 if report['status']=='passed' else 1


if __name__=='__main__':sys.exit(main())
