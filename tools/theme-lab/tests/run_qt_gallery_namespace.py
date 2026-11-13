# SPDX-License-Identifier: GPL-3.0-or-later
"""Run complete Qt gallery hint probes in bwrap on a caller-owned Xvfb."""
import argparse
import configparser
import json
import os
from pathlib import Path
import re
import shutil
import subprocess
import signal

assert os.environ.get('T07_PRIVATE_PROBE')=='1'
parser=argparse.ArgumentParser(description=__doc__)
parser.add_argument('--output',type=Path,required=True)
parser.add_argument('--major',type=int,choices=(5,6),required=True)
parser.add_argument('--quick',action='store_true')
parser.add_argument('--quick-baseline',action='store_true')
args=parser.parse_args()
assert not args.quick_baseline or args.quick
root=Path(__file__).resolve().parents[3]
out=args.output.absolute();out.mkdir(mode=0o700,parents=True,exist_ok=False)
home='/home/domainos-test'
for directory in ('home','etc','run/user/1000','tmp','home/.config','home/.local/share',
                  'home/.local/state','home/.cache'):
    (out/directory).mkdir(mode=0o700,parents=True,exist_ok=True)
(out/'etc/passwd').write_text('domainos-test:x:1000:1000:Preview:'+home+':/usr/sbin/nologin\n')
(out/'etc/group').write_text('domainos-test:x:1000:\n')
(out/'etc/nsswitch.conf').write_text('passwd: files\ngroup: files\nhosts: files\n')
(out/'etc/domainos-preview').touch()
for source in ('/etc/fonts','/etc/ld.so.cache','/etc/alternatives'):
    path=Path(source)
    target=out/'etc'/path.name
    if path.is_dir():target.mkdir()
    elif path.exists():target.touch()
palette=configparser.ConfigParser(interpolation=None,strict=False);palette.optionxform=str
palette.read(root/'colors/DomainOS-SR10.4.colors')
palette['General']['ColorScheme']='DomainOS-SR10.4'
palette['KDE']={'LookAndFeelPackage':'org.magpie.irixclassic.domainos.desktop'}
with (out/'home/.config/kdeglobals').open('w') as f:palette.write(f)
directory=out/'home/.local/share/color-schemes';directory.mkdir()
shutil.copy2(root/'colors/DomainOS-SR10.4.colors',directory/'DomainOS-SR10.4.colors')
display=os.environ['DISPLAY'];authority=Path(os.environ['XAUTHORITY']).resolve(strict=True)
assert re.fullmatch(r':\d+',display)
socket='/tmp/.X11-unix/X'+display[1:]
command=['unshare','--user','--map-root-user','--net','bwrap','--unshare-user','--unshare-ipc',
    '--unshare-uts','--unshare-pid','--uid','1000','--gid','1000','--clearenv','--ro-bind','/usr','/usr',
    '--symlink','usr/bin','/bin','--symlink','usr/lib','/lib','--symlink','usr/lib64','/lib64',
    '--ro-bind',str(out/'etc'),'/etc','--proc','/proc','--dev','/dev','--bind',str(out/'run'),'/run',
    '--bind',str(out/'tmp'),'/tmp','--bind',str(out/'home'),home,
    '--ro-bind',str(root),'/fixture/root','--ro-bind',socket,socket,
    '--ro-bind',str(authority),home+'/.Xauthority']
for source in ('/etc/fonts','/etc/ld.so.cache','/etc/alternatives'):
    if Path(source).exists():command+=['--ro-bind',source,source]
environment={'PATH':'/usr/bin:/bin','LC_ALL':'C.UTF-8','HOME':home,'DISPLAY':display,
    'XAUTHORITY':home+'/.Xauthority','XDG_RUNTIME_DIR':'/run/user/1000','QT_QPA_PLATFORM':'xcb',
    'PRIVATE_XEPHYR':'1','IRIX_DOMAINOS_PRIVATE_NAMESPACE':'bwrap','NO_AT_BRIDGE':'1',
    'XDG_CONFIG_HOME':home+'/.config','XDG_DATA_HOME':home+'/.local/share',
    'XDG_STATE_HOME':home+'/.local/state','XDG_CACHE_HOME':home+'/.cache'}
for k,v in environment.items():command+=['--setenv',k,v]
command+=['--die-with-parent','--new-session','--chdir',home,'dbus-run-session','--',
    '/usr/bin/python3','-B','/fixture/root/tools/theme-lab/tests/'+('probe_qtquick_baseline.py' if args.quick_baseline else ('probe_qtquick_gallery_hints.py' if args.quick else 'probe_qt_full_gallery_hints.py')),
    '--major',str(args.major)]
stdout_path=out/'probe.stdout.tmp';stderr_path=out/'probe.stderr.tmp'
timed_out=False
with stdout_path.open('w') as stdout_file, stderr_path.open('w') as stderr_file:
    child=subprocess.Popen(command,text=True,stdout=stdout_file,stderr=stderr_file,
                           start_new_session=True)
    try:
        child.wait(timeout=90)
    except subprocess.TimeoutExpired:
        timed_out=True
        # Kill the private process group without waiting for orphaned helpers
        # that may have inherited the gallery's standard streams.
        os.killpg(child.pid,signal.SIGTERM)
        try:
            child.wait(timeout=2)
        except subprocess.TimeoutExpired:
            os.killpg(child.pid,signal.SIGKILL)
            child.wait()
    stdout_file.flush();stderr_file.flush()
stdout=stdout_path.read_text();stderr=stderr_path.read_text()
stdout_path.unlink();stderr_path.unlink()
if child.returncode is None:
    raise RuntimeError(f'Qt gallery process did not terminate; diagnostics saved in {out}')
if timed_out:
    (out/'stdout.log').write_text(stdout);(out/'stderr.log').write_text(stderr)
    raise RuntimeError(f'Qt gallery probe exceeded 90 seconds; diagnostics saved in {out}')
if child.returncode:
    (out/'stdout.log').write_text(stdout);(out/'stderr.log').write_text(stderr)
    raise RuntimeError(stderr or f'Qt gallery exited with {child.returncode}')
(out/'stdout.log').write_text(stdout);(out/'stderr.log').write_text(stderr)
proof=out/'home'/(f'qtquick{args.major}-proof' if args.quick else ('qtwidgets-proof' if args.major==6 else 'qt5widgets-proof'))
qa=json.loads((proof/'HINTS-QA.json').read_text())
native=json.loads((proof/'RESULTADO.json').read_text())
assert qa['status']=='passed' and native['guards']['verified']
if args.quick:
    if args.quick_baseline:assert not native['nativeHints'] and qa['baseline']
    else:assert len(native['nativeHints'])>=20
    assert any(a['action']=='button' and a['detail']=='clicked' for a in native['actions'])
    assert any(a['action']=='menu' and a['detail']=='activated' for a in native['actions'])
else:
    assert native['hintCoverage']['widgets']>=40
    assert qa['menu_action_hover']['rows_tested'] == sum(
        not action['text'].strip() == '' for action in qa['typed_hint_coverage']['menu_actions']
    ) - 2, 'hover probe did not cover every visible menu row'
    assert qa['menu_action_hover']['all_rows_passed']
assert native['platform']=='xcb'
print(json.dumps({'status':'passed','qt_major':args.major,'qa':qa,'coverage':native.get('hintCoverage',len(native.get('nativeHints',[]))),
    'guarded_main':True,'scope':('pre-hint QML baseline and menu action, same private guards/runtime/palette; not hover'
                                if args.quick_baseline else 'native QtQuick KDE Controls resources, one push hover and menu action; not all layouts or Plasma SVG'
                                if args.quick else 'native production gallery resources and one push hover, private HOME/passwd/bus/X11; not all controls/layouts or fidelity')}))
