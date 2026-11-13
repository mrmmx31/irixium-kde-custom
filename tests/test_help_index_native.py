#!/usr/bin/env python3
"""Private native startup/screenshot check for the Help Index/Viewer."""
import os,pathlib,re,select,subprocess,tempfile,time
ROOT=pathlib.Path(__file__).resolve().parents[1]
with tempfile.TemporaryDirectory(prefix='help-index-',dir=ROOT/'tmp') as td:
 p=pathlib.Path(td);seed=p/'seed.json';seed.write_text((ROOT/'examples/checklist.json').read_text());state=p/'state.sqlite';exe=p/'board';
 flags=subprocess.check_output(['pkg-config','--cflags','--libs','json-c','libcrypto','sqlite3'],text=True).split()
 objects=sorted(str(ROOT/'build'/f.relative_to(ROOT/'src').with_suffix('.o')) for f in (ROOT/'src').rglob('*.c'))+[str(ROOT/'build/third_party/md4c/md4c.o'),str(ROOT/'build/third_party/md4c/entity.o')]
 subprocess.run(['cc','-std=c99','-Iinclude','-Isrc','-Ithird_party/md4c','tests/native_help_index_probe.c',*objects,'-Wl,--wrap=wb_view_create','-lXm','-lXt','-lX11','-lXext','-lm',*flags,'-o',str(exe)],cwd=ROOT,check=True)
 server=subprocess.Popen(['Xvfb','-displayfd','1','-screen','0','1920x1200x24','-nolisten','tcp'],stdout=subprocess.PIPE,stderr=subprocess.DEVNULL);board=wm=None
 try:
  assert select.select([server.stdout],[],[],5)[0];display=':'+server.stdout.readline().decode().strip();env=dict(os.environ,DISPLAY=display,WB_TEXT_RESOURCES=str(ROOT/'resources'),LC_ALL='C.UTF-8');wm=subprocess.Popen(['openbox'],env=env,stdout=subprocess.DEVNULL,stderr=subprocess.DEVNULL);time.sleep(.25)
  board=subprocess.Popen([str(exe),'--seed',str(seed),'--state',str(state)],cwd=ROOT,env=env,stdout=subprocess.DEVNULL,stderr=subprocess.PIPE)
  end=time.monotonic()+8;tree=''
  while time.monotonic()<end:
   assert board.poll() is None,board.stderr.read().decode()
   tree=subprocess.run(['xwininfo','-root','-tree'],env=env,text=True,capture_output=True).stdout
   if 'helpIndex' in tree or 'Help Viewer' in tree:break
   time.sleep(.1)
  assert board.poll() is None,board.stderr.read().decode()
  assert 'helpIndex' in tree or 'Help Viewer' in tree,tree[-1200:]
  image=p/'help-index.png';subprocess.run(['import','-window','root',str(image)],env=env,check=True)
  info=subprocess.run(['xwininfo','-root','-tree'],env=env,text=True,capture_output=True).stdout
  assert 'helpOpenDocuments' in info and 'helpDocumentList' in info and 'helpFileMenu' in info and 'helpBrowseMenu' in info
  print(f'native help window opened; screenshot: {image}')
 finally:
  if board and board.poll() is None:board.terminate();board.wait(timeout=4)
  if wm:wm.terminate();wm.wait(timeout=4)
  server.terminate();server.wait(timeout=4)
