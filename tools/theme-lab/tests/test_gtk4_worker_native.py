# SPDX-License-Identifier: GPL-3.0-or-later
"""Fresh private Xvfb/passwd/HOME namespace for the production GTK4 worker."""
import json
import os
from pathlib import Path
import secrets
import shutil
import subprocess
import tempfile
import time
import sys
import argparse
import configparser
ROOT=Path(__file__).resolve().parents[3]


def main():
    parser=argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--coupled',action='store_true')
    parser.add_argument('--toggle-foundation',action='store_true')
    parser.add_argument('--toggle-session',action='store_true')
    parser.add_argument('--toggle-snapshot',action='store_true')
    parser.add_argument('--toggle-worker',action='store_true')
    parser.add_argument('--check-worker',action='store_true')
    parser.add_argument('--toggle-snippet',action='store_true')
    parser.add_argument('--scrollbar-session',action='store_true')
    parser.add_argument('--scrollbar-state',type=int,choices=(0,1,2,3),default=0)
    parser.add_argument('--scrollbar-rerender',action='store_true')
    parser.add_argument('--paint-capture',action='store_true')
    parser.add_argument('--scheme',choices=('DomainOS-SR10.4','BreezeLight','BreezeDark','TestYellow'),default='DomainOS-SR10.4')
    parser.add_argument('--event-reader',type=Path)
    args=parser.parse_args()
    if args.paint_capture and any((args.coupled,args.toggle_foundation,args.toggle_session,
            args.toggle_snapshot,args.toggle_worker,args.check_worker,args.toggle_snippet,
            args.scrollbar_session,args.scrollbar_rerender)):
        parser.error('GTK4 Paint capture uses its own native-only fixture')
    if args.scrollbar_session and any((args.toggle_foundation,args.toggle_session,
            args.toggle_snapshot,args.toggle_worker,args.check_worker,args.toggle_snippet)):
        parser.error('GTK4 scrollbar and button worker probes are separate fixtures')
    if args.check_worker and any((args.toggle_foundation,args.toggle_session,
            args.toggle_snapshot,args.toggle_worker,args.toggle_snippet)):
        parser.error('GTK4 checkbox and other button probes are separate fixtures')
    temp_root=Path.home()/'tempia';temp_root.mkdir(parents=True,exist_ok=True)
    output=Path(tempfile.mkdtemp(prefix='t04-gtk4-worker-',dir=temp_root));print(output,flush=True)
    for name in ('home/.config','home/.local/share','home/.local/state','home/.cache','etc','tmp','run/user/1000'):
        (output/name).mkdir(parents=True,mode=0o700,exist_ok=True)
    (output/'etc/passwd').write_text('domainos-test:x:1000:1000:Preview:/home/domainos-test:/usr/sbin/nologin\n')
    (output/'etc/group').write_text('domainos-test:x:1000:\n')
    (output/'etc/nsswitch.conf').write_text('passwd: files\ngroup: files\nhosts: files\n')
    (output/'etc/domainos-preview').touch()
    for source in ('/etc/fonts','/etc/ld.so.cache','/etc/alternatives'):
        path=Path(source);destination=output/'etc'/path.name
        if path.is_dir():destination.mkdir()
        elif path.exists():destination.touch()
    source=(ROOT/'colors/DomainOS-SR10.4.colors' if args.scheme in ('DomainOS-SR10.4','TestYellow')
            else Path('/usr/share/color-schemes')/(args.scheme+'.colors'))
    target=output/'home/.config/kdeglobals'
    shutil.copyfile(source,target)
    if args.scheme=='TestYellow':
        # Artificial fixture only, matching the existing controller matrix.
        # Product colors continue to come from the native KDE role helper.
        palette=configparser.ConfigParser(interpolation=None);palette.optionxform=str
        palette.read(target)
        palette['General']['Name']='Artificial yellow test'
        for section in ('Colors:Window','Colors:Button','Colors:View'):
            palette[section]['BackgroundNormal']='236,216,112'
            palette[section]['BackgroundAlternate']='216,196,92'
            palette[section]['ForegroundNormal']='32,28,12'
        palette['Colors:Selection']['BackgroundNormal']='88,72,24'
        palette['Colors:Selection']['ForegroundNormal']='255,248,216'
        with target.open('w',encoding='utf-8') as stream:palette.write(stream)
    wrapper=output/'colors-wrapper.py'
    wrapper.write_text('#!/usr/bin/python3\nimport os,sys,time\nfrom pathlib import Path\n'
        'gate=Path(os.environ["T04_NATIVE_COLOR_GATE"])\n'
        'while gate.exists():time.sleep(.02)\n'
        'os.execv("/fixture/colors-real",["/fixture/colors-real"]+sys.argv[1:])\n')
    wrapper.chmod(0o700)
    number=next(n for n in range(500,4096) if not Path(f'/tmp/.X{n}-lock').exists() and not Path(f'/tmp/.X11-unix/X{n}').exists())
    display=':'+str(number);authority=output/'Xauthority';authority.touch(mode=0o600)
    subprocess.run(['xauth','-f',str(authority),'add',display,'.',secrets.token_hex(16)],check=True)
    with (output/'namespace.log').open('w') as log:
        server=subprocess.Popen(['Xvfb',display,'-screen','0','1000x700x24','-nolisten','tcp','-auth',str(authority)],stdout=log,stderr=log)
        try:
            deadline=time.monotonic()+10
            while subprocess.run(['xdpyinfo','-display',display],env=dict(os.environ,XAUTHORITY=str(authority)),stdout=subprocess.DEVNULL,stderr=subprocess.DEVNULL,timeout=2).returncode:
                if server.poll() is not None:raise RuntimeError('Owned Xvfb exited')
                if time.monotonic()>deadline:raise RuntimeError('Owned Xvfb observation deadline')
                time.sleep(.05)
            command=['unshare','--user','--map-root-user','--net','bwrap','--unshare-user','--unshare-ipc','--unshare-uts',
                '--uid','1000','--gid','1000','--clearenv','--ro-bind','/usr','/usr',
                '--symlink','usr/bin','/bin','--symlink','usr/lib','/lib','--symlink','usr/lib64','/lib64',
                '--ro-bind',str(output/'etc'),'/etc','--proc','/proc','--dev','/dev',
                '--bind',str(output/'home'),'/home/domainos-test','--bind',str(output/'run'),'/run',
                '--bind',str(output/'tmp'),'/tmp','--ro-bind',str(ROOT),'/fixture/root',
                '--ro-bind',str(ROOT/'tools/theme-lab/build/theme-lab-colors'),'/fixture/colors-real',
                '--ro-bind',str(wrapper),'/fixture/root/tools/theme-lab/build/theme-lab-colors',
                '--ro-bind',f'/tmp/.X11-unix/X{number}',f'/tmp/.X11-unix/X{number}',
                '--ro-bind',str(authority),'/home/domainos-test/.Xauthority']
            for source in ('/etc/fonts','/etc/ld.so.cache','/etc/alternatives'):
                if Path(source).exists():command+=['--ro-bind',source,source]
            values={'PATH':'/usr/bin:/bin','LC_ALL':'C.UTF-8','HOME':'/home/domainos-test',
                'DISPLAY':display,'XAUTHORITY':'/home/domainos-test/.Xauthority',
                'XDG_CONFIG_HOME':'/home/domainos-test/.config','XDG_DATA_HOME':'/home/domainos-test/.local/share',
                'XDG_STATE_HOME':'/home/domainos-test/.local/state','XDG_CACHE_HOME':'/home/domainos-test/.cache',
                'XDG_RUNTIME_DIR':'/run/user/1000','GDK_BACKEND':'x11','GSK_RENDERER':'cairo','GTK_A11Y':'none',
                'NO_AT_BRIDGE':'1','PRIVATE_XEPHYR':'1','IRIX_DOMAINOS_PRIVATE_NAMESPACE':'bwrap',
                'T04_NATIVE_COLOR_GATE':'/home/domainos-test/color-gate',
                'T04_FIXTURE_SCHEME':args.scheme,
                'T04_TOGGLE_SNAPSHOT':'1' if args.toggle_snapshot else '0',
                'T04_CHECK_WORKER':'1' if args.check_worker else '0',
                'T04_SCROLLBAR_STATE':str(args.scrollbar_state),
                'T04_SCROLLBAR_RERENDER':'1' if args.scrollbar_rerender else '0',
                'T04_PAINT_CAPTURE':'1' if args.paint_capture else '0',
                'T04_WORKER_ORIGIN':'coupled' if args.coupled else 'separate',
                'IRIX_DOMAINOS_PRIVATE_XEPHYR':'1','IRIX_DOMAINOS_SESSION_ROOT':'/home/domainos-test'}
            for key,value in values.items():command+=['--setenv',key,value]
            probe=('probe_gtk4_paint_capture.py' if args.paint_capture else
                   'probe_gtk4_scrollbar_worker.py' if args.scrollbar_session else
                   'probe_gtk4_toggle_snippet.py' if args.toggle_snippet else
                   'probe_gtk4_check_worker.py' if args.check_worker else
                   'probe_gtk4_toggle_worker.py' if args.toggle_worker else
                   'probe_gtk4_toggle_session.py' if args.toggle_session or args.toggle_snapshot else
                   'probe_gtk4_toggle.py' if args.toggle_foundation else 'probe_gtk4_worker.py')
            command+=['--die-with-parent','--chdir','/home/domainos-test','--','dbus-run-session','--',
                'python3','-B','/fixture/root/tools/theme-lab/tests/'+probe]
            result=subprocess.run(command,stdout=log,stderr=log,timeout=100)
            assert result.returncode==0,'Worker probe failed: '+str(output/'namespace.log')
            result_name=('PAINT-CAPTURE-RESULTADO.json' if args.paint_capture else
                         'SCROLLBAR-WORKER-RESULTADO.json' if args.scrollbar_session else
                         'WORKER-RESULTADO.json')
            result_path=output/'home'/result_name
            result_record=json.loads(result_path.read_text())
            if args.event_reader and args.check_worker:
                event_path=Path(result_record['event_directory'])
                event_dir=output/'home'/event_path.relative_to('/home/domainos-test')
                consumed=[]
                action_ids={'select':0,'move':1,'native':2,'metrics':3}
                for event_path in sorted(event_dir.glob('event-*.json')):
                    event=json.loads(event_path.read_text())
                    parsed=json.loads(subprocess.check_output(
                        [str(args.event_reader),'gtk4',event['project_sha256'],str(event_path)],
                        text=True,timeout=5))
                    assert parsed['control']==2 and parsed['action']==action_ids[event['action']],parsed
                    if event['action']=='native':
                        assert parsed['toggle_state_known'] and parsed['toggle_active']==event['state']['active'],parsed
                        assert parsed['toggle_separate']==(event['origin']=='separate'),parsed
                    consumed.append(parsed)
                assert any(item['action']==2 and item['toggle_state_known'] for item in consumed)
                result_record['native_events_consumed_by_c']=consumed
                result_path.write_text(json.dumps(result_record,ensure_ascii=False,indent=2)+'\n')
            print(json.dumps(result_record,ensure_ascii=False,indent=2),flush=True)
        finally:
            if server.poll() is None:
                server.terminate()
                try:server.wait(timeout=3)
                except subprocess.TimeoutExpired:server.kill();server.wait(timeout=3)


if __name__=='__main__':main()
