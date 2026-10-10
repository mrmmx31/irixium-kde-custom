#!/usr/bin/python3
# SPDX-FileCopyrightText: 2026 mrmmx31
# SPDX-License-Identifier: GPL-3.0-or-later
"""Verify the configured agenda path using KDE's installed public-holiday provider.

Loads the production DomainOS composition in private Xvfb/KWin/D-Bus/HOME paths.
The historical default selects the public US holiday region and 2027-01-01.
The directed Brazil mode checks 2026-10-12 and the installed provider's lack of
local Manaus/Amazonas coverage on 2026-10-24. No personal calendar, account
source or live desktop is read or configured; no holiday is fabricated.
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
import time

sys.dont_write_bytecode = True
REPO = Path(__file__).resolve().parents[2]
APPLET = REPO / 'plasma/applets/org.irixclassic.domainos.panel'

def digest(path):
    return hashlib.sha256(path.read_bytes()).hexdigest() if path.is_file() else None

def worker(output):
    if os.environ.get('IRIX_DOMAINOS_AGENDA_PRIVATE_SESSION') != '1':
        raise RuntimeError('Private agenda session required')
    processes, logs = [], []
    try:
        for executable in ('kwin_x11','kactivitymanagerd','ksystemstats'):
            path = shutil.which(executable) or '/usr/lib/x86_64-linux-gnu/libexec/' + executable
            log = (output / (executable + '.log')).open('w'); logs.append(log)
            processes.append(subprocess.Popen([path,*(['--remain'] if executable == 'ksystemstats' else [])],stdout=log,stderr=subprocess.STDOUT))
        for _ in range(80):
            if subprocess.run(['qdbus6','org.kde.KWin','/VirtualDesktopManager'],capture_output=True,timeout=2).returncode == 0: break
            time.sleep(.05)
        else: raise RuntimeError('Private KWin did not become ready')
        environment = dict(os.environ,LD_PRELOAD=str(output/'agenda-host.so'),
            IRIX_DOMAINOS_AGENDA_REPORT=str(output/'NATIVO.json'),IRIX_DOMAINOS_AGENDA_DIR=str(output))
        host = subprocess.run(['/usr/bin/plasmawindowed','org.irixclassic.domainos.panel'],env=environment,
            capture_output=True,text=True,timeout=29)
        (output/'host.log').write_text(host.stdout+host.stderr)
        (output/'HOST-EXIT.json').write_text(json.dumps({'returncode':host.returncode})+'\n')
        return host.returncode
    finally:
        for process in reversed(processes):
            if process.poll() is None:
                process.terminate()
                try: process.wait(3)
                except subprocess.TimeoutExpired: process.kill(); process.wait()
        (output/'LIMPEZA.json').write_text(json.dumps({'own_daemons_exited':all(p.poll() is not None for p in processes),
            'daemon_pids':[p.pid for p in processes]},indent=2)+'\n')
        for log in logs: log.close()

def main():
    parser=argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--saida',type=Path,required=True,help='New private directory under /tmp')
    region_mode=parser.add_mutually_exclusive_group()
    region_mode.add_argument('--brasil',action='store_true',help='Use installed br_pt-br region, 2026-10-12 positive and 2026-10-24 negative')
    region_mode.add_argument('--manaus-2026',action='store_true',help='Use only official Manaus/Brazil 2026 region in private XDG paths')
    parser.add_argument('--inspecionar-identidade',action='store_true',help='Inspect native UIDs/visible rows for four suspected duplicate holiday dates only')
    parser.add_argument('--validar-unicidade',action='store_true',help='Require exactly one native event/visible row on all fifteen Manaus holiday dates')
    parser.add_argument('--worker',action='store_true',help=argparse.SUPPRESS)
    args=parser.parse_args(); output=args.saida.resolve()
    if args.worker: return worker(output)
    if (args.inspecionar_identidade or args.validar_unicidade) and not args.manaus_2026: parser.error('Identity/uniqueness modes require --manaus-2026')
    if not output.is_relative_to(Path('/tmp')) or output.exists(): parser.error('Use a new directory under /tmp')
    output.mkdir(mode=0o700)
    report_output=output
    # Profiles/caches/build products are disposable and repository-local. Keep
    # only a small evidence set in /tmp, without retaining a copied user tree.
    workspace=tempfile.TemporaryDirectory(prefix='.domainos-agenda-',dir=REPO)
    output=Path(workspace.name)
    sources = [APPLET/'contents/ui'/name for name in ('main.qml','DomainOSFunctionalPanel.qml','DomainOSRuntime.qml','DomainOSInstruments.qml')]
    sources.append(APPLET/'contents/config/main.xml')
    regional_file=APPLET/'contents/code/holidays/holiday_br-am-manaus-2026_pt-br'
    if args.manaus_2026: sources.append(regional_file)
    source_before = {str(path):digest(path) for path in sources}
    protected = [Path.home()/'.config'/name for name in ('kdeglobals','plasmarc','kwinrc','plasma-org.kde.plasma.desktop-appletsrc','plasma_calendar_holiday_regions')]
    protected_before = {str(path):digest(path) for path in protected}
    environment=os.environ.copy()
    for key in ('DISPLAY','WAYLAND_DISPLAY','DBUS_SESSION_BUS_ADDRESS','DBUS_STARTER_ADDRESS','DBUS_STARTER_BUS_TYPE','SESSION_MANAGER','QML_IMPORT_PATH','QML2_IMPORT_PATH','QT_STYLE_OVERRIDE','QT_QUICK_CONTROLS_STYLE','LD_PRELOAD','XAUTHORITY','XDG_SESSION_ID','KDE_FULL_SESSION','KDE_SESSION_VERSION','SSH_AUTH_SOCK'):
        environment.pop(key,None)
    for key,name in (('HOME','home'),('XDG_CONFIG_HOME','config'),('XDG_DATA_HOME','data'),('XDG_CACHE_HOME','cache'),('XDG_STATE_HOME','state'),('XDG_RUNTIME_DIR','runtime')):
        (output/name).mkdir(mode=0o700); environment[key]=str(output/name)
    for name in ('org.irixclassic.domainos.panel','org.irixclassic.grosview'):
        shutil.copytree(REPO/'plasma/applets'/name,output/'data/plasma/plasmoids'/name,ignore=shutil.ignore_patterns('__pycache__','*.pyc'))
    for name in ('IrixClassic','IrixClassicDomainOS'):
        shutil.copytree(REPO/'plasma'/name,output/'data/plasma/desktoptheme'/name)
    (output/'config/kdeglobals').write_text((REPO/'colors/DomainOS-SR10.4.colors').read_text())
    (output/'config/plasmarc').write_text('[Theme]\nname=IrixClassicDomainOS\n')
    (output/'config/kwinrc').write_text('[Desktops]\nNumber=1\nName_1=Private public-holiday test\n[Compositing]\nEnabled=false\n')
    # KDE's own holiday plugin/config helper share this native file/key. The
    # installed provider supplies all event data; no synthetic event is added.
    public_region='br-am-manaus-2026_pt-br' if args.manaus_2026 else ('br_pt-br' if args.brasil else 'us_en-us')
    selected_date='2026-01-01' if args.manaus_2026 else ('2026-10-12' if args.brasil else '2027-01-01')
    absent_date='2026-10-24' if args.brasil else ''
    regional_probes=[]
    if args.manaus_2026:
        regional_dir=output/'data/kf5/libkholidays/plan2';regional_dir.mkdir(parents=True)
        shutil.copyfile(regional_file,regional_dir/regional_file.name)
        regional_probes=[{'date':'2026-'+date,'event':True} for date in
            ('02-17','04-03','04-21','05-01','06-04','09-05','09-07','10-12','10-24','11-02','11-15','11-20','12-08','12-25')]
        regional_probes += [{'date':'2026-'+date,'event':False} for date in
            ('02-16','02-18','04-02','04-20','06-05','10-28','12-07','12-24','12-31')]
        regional_probes += [{'date':date,'event':False} for date in ('2025-10-24','2027-10-24')]
        if args.inspecionar_identidade:
            regional_probes=[{'date':date,'event':True} for date in ('2026-10-12','2026-12-08','2026-12-25')]
    native_region_config='[General]\nselectedRegions='+public_region+'\n'
    (output/'config/plasma_calendar_holiday_regions').write_text(native_region_config)
    flags=shlex.split(subprocess.check_output(['pkg-config','--cflags','--libs','Qt6Widgets','Qt6Test'],text=True))
    compiler_tmp=output/'compiler'; compiler_tmp.mkdir(mode=0o700)
    subprocess.run(['c++','-std=c++17','-shared','-fPIC',str(REPO/'plasma/tests/domainos-agenda-host.cpp'),'-o',str(output/'agenda-host.so'),*flags,'-ldl'],check=True,
        env=dict(os.environ,TMPDIR=str(compiler_tmp)),timeout=30)
    bus=output/'private-bus.conf'
    bus.write_text('<busconfig><type>session</type><listen>unix:tmpdir=/tmp</listen><auth>EXTERNAL</auth><policy context="default"><allow send_destination="*"/><allow receive_sender="*"/><allow own="*"/></policy></busconfig>')
    environment.update(TMPDIR=str(compiler_tmp),XDG_DATA_DIRS='/usr/local/share:/usr/share',XDG_CONFIG_DIRS='/etc/xdg',XDG_CURRENT_DESKTOP='NONE',
        XDG_SESSION_TYPE='x11',QT_QPA_PLATFORM='xcb',QT_QPA_PLATFORMTHEME='kde',QT_QUICK_BACKEND='software',KWIN_COMPOSE='N',
        LIBGL_ALWAYS_SOFTWARE='1',DBUS_SYSTEM_BUS_ADDRESS='unix:path='+str(output/'no-system-bus'),
        PULSE_SERVER='unix:'+str(output/'no-audio-server'),LANG='en_US.UTF-8',LC_ALL='en_US.UTF-8',TZ='UTC',
        IRIX_DOMAINOS_AGENDA_PRIVATE_SESSION='1',IRIX_DOMAINOS_AGENDA_PUBLIC_REGION=public_region,
        IRIX_DOMAINOS_AGENDA_PUBLIC_DATE=selected_date,IRIX_DOMAINOS_AGENDA_ABSENT_DATE=absent_date,
        IRIX_DOMAINOS_AGENDA_REGIONAL_PROBES=json.dumps(regional_probes),
        IRIX_DOMAINOS_AGENDA_INSPECT_IDENTITY='1' if args.inspecionar_identidade or args.validar_unicidade else '0')
    if args.manaus_2026:
        subprocess.run([sys.executable,str(REPO/'plasma/tests/domainos-holiday-region-metadata.py'),
            '--region',public_region,'--saida',str(output/'REGIAO-NATIVA.json')],
            env=dict(environment,QT_QPA_PLATFORM='offscreen'),check=True,timeout=10,capture_output=True,text=True)
    result=subprocess.run(['xvfb-run','--auto-servernum','--server-args=-screen 0 1300x950x24','dbus-run-session','--config-file='+str(bus),'--',sys.executable,str(Path(__file__).resolve()),'--saida',str(output),'--worker'],
        env=environment,capture_output=True,text=True,timeout=40)
    (output/'session.log').write_text(result.stdout+result.stderr)
    native=json.loads((output/'NATIVO.json').read_text()) if (output/'NATIVO.json').is_file() else {}
    log=(output/'host.log').read_text() if (output/'host.log').is_file() else result.stderr
    errors=[line for line in log.splitlines() if re.search(r'ReferenceError:|TypeError:|SyntaxError:|Cannot assign|Binding loop|is not a type|error when loading applet',line)]
    cleanup=json.loads((output/'LIMPEZA.json').read_text()) if (output/'LIMPEZA.json').is_file() else {}
    checks=dict(native.get('checks',{}))
    metadata=json.loads((output/'REGIAO-NATIVA.json').read_text()) if args.manaus_2026 else None
    if metadata:
        checks.update({'regional_metadata_'+name:ok for name,ok in metadata['checks'].items()})
        checks['selected_regional_file_matches_source_bytes']=(output/'data/kf5/libkholidays/plan2'/regional_file.name).read_bytes()==regional_file.read_bytes()
    checks.update(native_host_exited_cleanly=result.returncode==0 and not native.get('failure'),
        native_events_for_date_invocation_succeeded=native.get('events_for_date_invoked') is True,
        qml_runtime_errors_zero=not errors,
        production_calendar_sources_unchanged=source_before=={str(path):digest(path) for path in sources},
        five_personal_preferences_unchanged=protected_before=={str(path):digest(path) for path in protected},
        own_daemons_exited=cleanup.get('own_daemons_exited') is True,
        host_is_absent_after_test=native.get('host_pid') is not None and not Path('/proc',str(native['host_pid'])).exists(),
        native_host_used_private_home=native.get('private_namespace',{}).get('HOME')==str(output/'home'),
        only_public_region_written_in_private_profile=(output/'config/plasma_calendar_holiday_regions').read_text()==native_region_config)
    report={'status':'passed' if all(checks.values()) else 'failed','checks':checks,'native':native,'qml_diagnostics':errors,
        'source_hashes':source_before,'protected_preferences':{'before':protected_before,'after':{str(path):digest(path) for path in protected}},
        'scope':'Production main/KConfig/calendar/DaysModel/agenda delegates with installed KDE public-holiday provider chosen only in disposable HOME. No personal account/agenda/device/session action; no synthetic event source.',
        'chosen_public_region':public_region,'chosen_date':selected_date,'negative_coverage_date':absent_date or None,
        'regional_metadata':metadata,'regional_probe_cases':regional_probes,
        'native_uid_and_agenda_uniqueness_inspection':args.inspecionar_identidade,
        'all_fifteen_native_and_visible_events_unique':args.validar_unicidade,
        'cleanup':cleanup,'original_instrument23_rerun':False}
    (report_output/'RESULTADO.json').write_text(json.dumps(report,indent=2,ensure_ascii=False)+'\n')
    for artifact in output.iterdir():
        if artifact.is_file() and artifact.suffix in ('.json','.log','.png'):
            shutil.copy2(artifact,report_output/artifact.name)
    workspace.cleanup()
    print(json.dumps({'status':report['status'],'checks':len(checks),'failed':[name for name,ok in checks.items() if not ok],
        'failure':native.get('failure'),'report':str(report_output/'RESULTADO.json')},ensure_ascii=False))
    return 0 if report['status']=='passed' else 1

if __name__=='__main__':raise SystemExit(main())
