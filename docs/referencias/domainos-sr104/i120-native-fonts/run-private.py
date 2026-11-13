import os,sys,json,time,subprocess,configparser,pathlib,hashlib
root=pathlib.Path(__file__).resolve().parent;out=root/'result';out.mkdir(exist_ok=True)
config=pathlib.Path(os.environ.get('XDG_CONFIG_HOME',str(pathlib.Path.home()/'.config')))/'kdeglobals';p=configparser.ConfigParser(interpolation=None,strict=False);p.optionxform=str;p.read(config)
def color(key):
 rgb=tuple(int(v) for v in p['Colors:Window'][key].split(','));assert len(rgb)==3 and all(0<=v<=255 for v in rgb);return '#%02x%02x%02x'%rgb
face=color('BackgroundNormal');text=color('ForegroundNormal');(out/'palette.json').write_text(json.dumps({'source':str(config),'sha256':hashlib.sha256(config.read_bytes()).hexdigest(),'roles':['Colors:Window/BackgroundNormal','Colors:Window/ForegroundNormal'],'effective':[face,text],'personal_config_changed':False},indent=2))
env=dict(os.environ,LC_ALL='C.UTF-8',XDG_CONFIG_HOME=str(out/'config'),XDG_DATA_HOME=str(out/'data'),XDG_CACHE_HOME=str(out/'cache'),GDK_BACKEND='x11',GDK_SCALE='1',GDK_DPI_SCALE='1',NO_AT_BRIDGE='1')
env.pop('WAYLAND_DISPLAY',None)
env.pop('DBUS_SESSION_BUS_ADDRESS',None)
for name,command in [('motif',[str(root/'motif-font-probe'),face,text]),('gtk',['/usr/bin/python3',str(root/'gtk-font-probe.py'),str(out),face,text])]:
 if len(sys.argv)>1 and name!=sys.argv[1]:continue
 log=out/(name+'.log')
 with log.open('w') as f:
  process=subprocess.Popen(command,stdout=f,stderr=subprocess.STDOUT,env=env)
  try:
   end=time.monotonic()+10;wid=None
   while time.monotonic()<end:
    if process.poll() is not None:raise RuntimeError(name+' exited before window')
    lines=log.read_text().splitlines();windows=[l.split()[1] for l in lines if l.startswith('WINDOW ')]
    if windows:wid=windows[-1];break
    time.sleep(.05)
   if not wid:raise RuntimeError(name+' missing window')
   time.sleep(.4);subprocess.run(['import','-window',wid,str(out/(name+'.png'))],check=True,env=env)
   status=process.wait(timeout=20);assert status==0;print(name,'captured/terminal0',flush=True)
  finally:
   if process.poll() is None:process.terminate();process.wait(timeout=5)
