# SPDX-License-Identifier: GPL-3.0-or-later
"""Real GTK4 C-ABI gallery/resource probe on caller-owned Xvfb, no hover claim."""
import json
import os
from pathlib import Path
import selectors
import signal
import subprocess
import tempfile
import time
import argparse

parser=argparse.ArgumentParser();parser.add_argument('--hover',action='store_true')
parser.add_argument('--hover-matrix',action='store_true',
                    help='time native tooltips for mapped hint-bearing controls on both gallery pages')
parser.add_argument('--matrix-timeout-sec',type=int,default=240,
                    help='maximum seconds for the full hover matrix')
parser.add_argument('--reuse-session-bus',action='store_true',
                    help='use the caller session bus instead of starting dbus-run-session')
parser.add_argument('--scrollbar-css',type=Path);parser.add_argument('--scrollbar-class')
parser.add_argument('--capture',type=Path)
args=parser.parse_args()
if args.hover and args.hover_matrix:parser.error('--hover and --hover-matrix are mutually exclusive')
if bool(args.scrollbar_css)!=bool(args.scrollbar_class):parser.error('--scrollbar-css and --scrollbar-class are a pair')
if (args.hover or args.hover_matrix) and (args.capture or args.scrollbar_css):
    parser.error('hover workers cannot be combined with --capture or --scrollbar-css')

assert os.environ.get('T07_PRIVATE_PROBE')=='1'
assert os.environ['DISPLAY'].startswith(':')
root=Path(__file__).resolve().parents[3]
with tempfile.TemporaryDirectory(prefix='t07-gtk4-') as directory:
    base=Path(directory)
    env=os.environ.copy()
    for name in ('WAYLAND_DISPLAY','GTK_THEME'):
        env.pop(name,None)
    if not args.reuse_session_bus:
        env.pop('DBUS_SESSION_BUS_ADDRESS',None)
    env.update(IRIX_DOMAINOS_PRIVATE_XEPHYR='1',IRIX_DOMAINOS_SESSION_ROOT=directory,
               HOME=directory,GDK_BACKEND='x11',NO_AT_BRIDGE='1')
    for name,relative in {'XDG_CONFIG_HOME':'config','XDG_DATA_HOME':'data',
                          'XDG_STATE_HOME':'state','XDG_CACHE_HOME':'cache',
                          'XDG_RUNTIME_DIR':'run'}.items():
        path=base/relative;path.mkdir(mode=0o700);env[name]=str(path)
    script=root/('tools/theme-lab/tests/gtk4_hint_matrix_worker.py' if args.hover_matrix else
                 'tools/theme-lab/tests/gtk4_hover_worker.py' if args.hover else
                 'plasma/tests/galerias-nativas/gtk4_demo.py')
    command=['/usr/bin/python3','-B',str(script)]
    if not args.reuse_session_bus:
        command=['dbus-run-session','--',*command]
    if args.scrollbar_css:
        command+=['--theme-lab-scrollbar-css',str(args.scrollbar_css),
                  '--theme-lab-scrollbar-class',args.scrollbar_class]
    child=subprocess.Popen(command,
                           env=env,text=True,stdout=subprocess.PIPE,
                           stderr=subprocess.PIPE,start_new_session=True)
    selector=None
    try:
        if args.hover or args.hover_matrix:
            stdout,stderr=child.communicate(timeout=args.matrix_timeout_sec if args.hover_matrix else 45)
            assert child.returncode==0,(
                'GTK4 hover worker failed; stdout=' + stdout + '; stderr=' + stderr)
            reports=[json.loads(line) for line in stdout.splitlines() if line.startswith('{')]
            gallery=next((row for row in reports if row.get('toolkit')=='GTK4 C ABI'),None)
            assert gallery is not None,'GTK4 gallery did not report its mapped native window'
            assert gallery['display']==env['DISPLAY'],'wrong display'
            assert gallery['window']['mapped'] and not gallery['window']['allocation_wait_timed_out']
            assert min(gallery['window']['allocated_px'])>0
            if args.hover_matrix:
                result=next((row for row in reports if 'hover_matrix' in row),None)
                assert result is not None,'hover worker did not report a matrix result'
                matrix=result['hover_matrix']
                assert matrix['status'] in ('passed','partial')
                assert matrix['passed_targets']>0,matrix
                assert (matrix['passed_targets']+matrix['failed_targets']==
                        matrix['mapped_targets_first_page']+matrix['mapped_targets_second_page'])
                output={'status':matrix['status'],'native_gallery':gallery,'hover_matrix':matrix,
                        'scope':'real GTK4 mapped-control hover matrix; no color-pixel or historical comparison'}
            else:
                result=next((row for row in reports if 'hover_proof' in row),None)
                assert result is not None,'hover worker did not report a tooltip result'
                hover=result['hover_proof']
                assert hover['status']=='passed'
                output={'status':'passed','native_gallery':gallery,'hover_proof':hover,
                        'scope':'real production GTK4 push/menu hover; no other layouts/paint/later-creation proof'}
            print(json.dumps(output))
        else:
            selector=selectors.DefaultSelector();selector.register(child.stdout,selectors.EVENT_READ)
            deadline=time.monotonic()+15;proof=None
            while time.monotonic()<deadline and child.poll() is None:
                if not selector.select(.2):continue
                line=child.stdout.readline()
                if line.startswith('{'):
                    proof=json.loads(line);break
            assert proof is not None,'gallery did not report native controls'
            assert proof['display']==env['DISPLAY'],'wrong display'
            assert proof['hintCoverage']['controls']>=25
            assert proof['hintCoverage']['utf8_resources_verified']
            assert proof['hintCoverage']['internal']['scrollbars']>=4
            contract=proof['hintCoverage']['internal']['scrollbar_contract']
            assert contract['observed_widget_type']=='GtkScrollbar'
            assert contract['widget_css_name']=='scrollbar'
            assert all(value is False for value in contract['arrow_stepper_properties'].values())
            assert proof['hintCoverage']['internal']['menu_rows']>=7
            if args.scrollbar_css:
                styled=proof['scrollbar_css_proof']
                assert styled['provider_loaded'] and not styled['parse_errors']
                assert styled['styled_count']>=4 and styled['css_selector_applied']
                assert all(row['style_class_applied'] for row in styled['allocations'])
                nonzero=[row for row in styled['allocations'] if row['width']>0 and row['height']>0]
                assert any(row['orientation']=='vertical' and row['width']==15 for row in nonzero),nonzero
                assert any(row['orientation']=='horizontal' and row['height']==15 for row in nonzero),nonzero
            if args.capture:
                args.capture.parent.mkdir(parents=True,exist_ok=True,mode=0o700)
                capture=subprocess.run(['xwd','-silent','-root','-out',str(args.capture)],
                                       env=env,capture_output=True,text=True,timeout=10)
                assert capture.returncode==0,capture.stderr
            elif not args.scrollbar_css:
                assert proof['custom_css'] is False
            capture_info=None
            if args.capture:
                import hashlib
                capture_info={'path':str(args.capture),'sha256':hashlib.sha256(args.capture.read_bytes()).hexdigest(),
                              'format':'XWD root capture of caller-owned private Xvfb'}
            print(json.dumps({'status':'passed','native_gallery':proof,'capture':capture_info,
                              'scope':'real GTK4 logical controls; custom scrollbar mode also proves CSS parsing, class application and native allocation; no pixel-diff or historical comparison'}))
    finally:
        if selector is not None:selector.close()
        if child.poll() is None:os.killpg(child.pid,signal.SIGTERM)
        _,stderr=child.communicate(timeout=5)
        if stderr:print(stderr,file=__import__('sys').stderr)
