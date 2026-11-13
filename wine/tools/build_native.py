#!/usr/bin/env python3
# SPDX-FileCopyrightText: 2026 mrmmx31
# SPDX-License-Identifier: GPL-3.0-or-later
"""Build the original small Wine utility with Clang and LLVM/binutils.

Prebuilt utilities are shipped; these are optional maintainer dependencies.
No downloaded SDK or compiler binary is used.
"""
import argparse
import hashlib
import json
from pathlib import Path
import shutil
import subprocess
import tempfile

ROOT=Path(__file__).resolve().parents[2]
DLLS={
    'kernel32':['GetStdHandle','WriteFile','ExitProcess','GetCommandLineW','LoadLibraryW','GetProcAddress','GetLastError','GetModuleHandleW'],
    'shell32':['CommandLineToArgvW'],
    'uxtheme':['IsThemeActive','GetCurrentThemeName','OpenThemeData','IsThemePartDefined','CloseThemeData','GetThemeFilename'],
    'user32':['GetSysColor','RegisterClassW','CreateWindowExW','DefWindowProcW','ShowWindow',
              'UpdateWindow','GetMessageW','TranslateMessage','DispatchMessageW','PostQuitMessage',
              'DestroyWindow','SendMessageW','EnableWindow','LoadCursorW','GetSysColorBrush',
              'SetWindowTextW','SetProcessDPIAware','BeginPaint','EndPaint','GetWindowRect'],
    'gdi32':['CreateFontW','TextOutW','SetTextColor','SetBkMode'],
    'comctl32':['InitCommonControlsEx'],
}


def build(source=None, destination=None):
    source=source or ROOT/'wine/native/theme.c'
    destination=destination or ROOT/'wine/IrixClassic/package/irix-theme.exe'
    programs=['clang','llvm-dlltool-19','ld']
    for name in programs:
        if not shutil.which(name):raise RuntimeError('Optional build dependency missing: '+name)
    with tempfile.TemporaryDirectory(prefix='irix-wine-build-') as folder:
        tmp=Path(folder)
        libs=[]
        for name,exports in DLLS.items():
            definition=tmp/(name+'.def')
            definition.write_text('LIBRARY '+name+'.dll\nEXPORTS\n'+'\n'.join(exports)+'\n')
            library=tmp/(name+'.a')
            subprocess.run(['llvm-dlltool-19','-m','i386:x86-64','-d',str(definition),'-l',str(library)],check=True)
            libs.append(str(library))
        obj=tmp/'theme.obj'
        subprocess.run(['clang','--target=x86_64-pc-windows-msvc','-Os','-fno-stack-protector',
                        '-ffreestanding','-c',str(source),'-o',str(obj)],check=True)
        destination.parent.mkdir(parents=True,exist_ok=True)
        resources=[]
        if source.name=='preview.c':
            manifest=tmp/'preview.manifest'
            manifest.write_text('<?xml version="1.0" encoding="UTF-8" standalone="yes"?>'
                '<assembly xmlns="urn:schemas-microsoft-com:asm.v1" manifestVersion="1.0">'
                '<assemblyIdentity version="1.0.0.0" processorArchitecture="amd64" name="IRIXClassic.Preview" type="win32"/>'
                '<dependency><dependentAssembly><assemblyIdentity type="win32" '
                'name="Microsoft.Windows.Common-Controls" version="6.0.0.0" processorArchitecture="amd64" '
                'publicKeyToken="6595b64144ccf1df" language="*"/></dependentAssembly></dependency></assembly>')
            rc=tmp/'preview.rc';rc.write_text('1 24 "'+str(manifest)+'"\n')
            res=tmp/'preview.res';resobj=tmp/'preview-resource.obj'
            subprocess.run(['llvm-rc-19','/fo',str(res),str(rc)],check=True)
            subprocess.run(['llvm-cvtres-19','/machine:x64','/out:'+str(resobj),str(res)],check=True)
            resources=[str(resobj)]
        subprocess.run(['ld','-mi386pep','--no-insert-timestamp','--entry=mainCRTStartup',
                        '--subsystem=console','--image-base=0x140000000','--stack=1048576',
                        '-o',str(destination),str(obj),*resources,*libs],check=True)
    print(destination)


if __name__=='__main__':
    build()
    build(ROOT/'wine/native/preview.c',ROOT/'wine/IrixClassic/package/irix-preview.exe')
    origin=ROOT/'wine/IrixClassic/package/ORIGEM.json'
    if origin.exists():
        doc=json.loads(origin.read_text())
        doc['native_utilities']={}
        for file in ('theme.c','preview.c'):
            doc['native_utilities']['wine/native/'+file]=hashlib.sha256((ROOT/'wine/native'/file).read_bytes()).hexdigest()
        for file in ('irix-theme.exe','irix-preview.exe'):
            doc['native_utilities'][file]=hashlib.sha256((ROOT/'wine/IrixClassic/package'/file).read_bytes()).hexdigest()
        origin.write_text(json.dumps(doc,indent=2)+'\n')
        package=origin.parent
        manifest={'package':{p.relative_to(package).as_posix():hashlib.sha256(p.read_bytes()).hexdigest()
            for p in sorted(package.rglob('*')) if p.is_file() and '__pycache__' not in p.parts}}
        (package.parent/'MANIFEST.json').write_text(json.dumps(manifest,indent=2)+'\n')
