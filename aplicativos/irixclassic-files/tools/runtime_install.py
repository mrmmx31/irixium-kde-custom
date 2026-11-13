#!/usr/bin/env python3
# SPDX-FileCopyrightText: 2026 mrmmx31
# SPDX-License-Identifier: GPL-2.0-or-later
"""Install the private bundle and register it as a directory handler."""
from pathlib import Path, PurePosixPath
import argparse, hashlib, json, os, shlex, shutil, stat, sys, tempfile
VERSION='0.1.0-alpha2'
ID='io.github.mrmmx31.irixclassic.files'
class Failure(RuntimeError):pass

def no_links(path):
    for p in (path,*path.parents):
        if p.is_symlink():raise Failure('Symlink refused: '+str(p))
def hash_file(p):return hashlib.sha256(p.read_bytes()).hexdigest()
def verify(root):
    no_links(root)
    meta=json.loads((root/'BUILD-RESULT.json').read_text())
    if meta.get('version')!=VERSION or not meta.get('native_tests_passed'):raise Failure('This is not a tested build of the expected version')
    expected=set(meta['files'])|{'BUILD-RESULT.json'}
    actual={p.relative_to(root).as_posix() for p in root.rglob('*') if p.is_file() or p.is_symlink()}
    if actual!=expected:raise Failure('Bundle contains missing or unrecognized files')
    for rel,record in meta['files'].items():
        r=PurePosixPath(rel)
        if r.is_absolute() or '..' in r.parts:raise Failure('Invalid manifest path')
        p=root/rel
        if 'symlink' in record:
            target=record['symlink']
            if '/' in target or target.startswith('.') or not p.is_symlink() or os.readlink(p)!=target:raise Failure('Invalid library link')
            if not p.resolve().is_relative_to(root.resolve()):raise Failure('External library link')
        elif p.is_symlink() or not p.is_file() or hash_file(p)!=record['sha256'] or stat.S_IMODE(p.stat().st_mode)!=record['mode']:raise Failure('Changed bundle file or permissions: '+rel)
    return meta

def main():
    parser=argparse.ArgumentParser(description=__doc__);parser.add_argument('--verificar',action='store_true');parser.add_argument('--remover',action='store_true')
    a=parser.parse_args()
    if os.geteuid()==0:raise Failure('Run as an ordinary user, without sudo')
    source=Path(__file__).resolve().parent;verify(source)
    home=Path.home();base=home/'.local/lib/irixclassic-files';dest=base/VERSION
    bindir=home/'.local/bin';applications=Path(os.environ.get('XDG_DATA_HOME',home/'.local/share'))/'applications'
    launcher=bindir/'irixclassic-files';desktop=applications/(ID+'.desktop')
    if not applications.is_absolute():raise Failure('XDG_DATA_HOME must be absolute')
    for p in (dest,launcher,desktop):no_links(p)
    command=dest/'bin/irixclassic-files'
    shell='#!/bin/sh\nexec '+shlex.quote(str(command))+' "$@"\n'
    # Desktop Exec quoting is not shell quoting. Percent must be escaped separately.
    escaped=str(command).replace('\\','\\\\').replace('"','\\"').replace('`','\\`').replace('$','\\$').replace('%','%%')
    entry='[Desktop Entry]\nType=Application\nName=IrixClassic Files (experimental)\nComment=Classic file manager based on Dolphin\nExec="'+escaped+'" %U\nIcon=system-file-manager\nTerminal=false\nCategories=System;FileManager;\nMimeType=inode/directory;application/x-directory;\nStartupNotify=true\n'
    if a.remover:
        if not dest.exists():raise Failure('Private version is not installed')
        verify(dest)
        if launcher.exists() and launcher.read_text()!=shell:raise Failure('Launcher changed; refusing to remove')
        if desktop.exists() and desktop.read_text()!=entry:raise Failure('Desktop entry changed; refusing to remove')
        if a.verificar:print('Would remove only:',dest,launcher,desktop);return 0
        launcher.unlink(missing_ok=True);desktop.unlink(missing_ok=True);shutil.rmtree(dest)
        print('Removed private application. Shelf and user preferences were preserved.');return 0
    for p,content in ((launcher,shell),(desktop,entry)):
        if p.exists() and (not p.is_file() or p.read_text()!=content):raise Failure('Existing launcher/entry is not ours: '+str(p))
    if dest.exists():
        verify(dest)
        if (dest/'BUILD-RESULT.json').read_bytes()!=(source/'BUILD-RESULT.json').read_bytes():raise Failure('Different build under the same experimental version; remove it first')
    if a.verificar:print('Would install in:',dest,'\nRegisters directory MIME types; the user default is unchanged.');return 0
    base.mkdir(parents=True,exist_ok=True);bindir.mkdir(parents=True,exist_ok=True);applications.mkdir(parents=True,exist_ok=True)
    created=[]
    try:
        if not dest.exists():
            with tempfile.TemporaryDirectory(prefix='.install-',dir=base) as temp:
                stage=Path(temp)/'bundle';shutil.copytree(source,stage,symlinks=True);verify(stage);stage.rename(dest);created.append(dest)
        for p,data,mode in ((launcher,shell,0o755),(desktop,entry,0o644)):
            if p.exists():continue
            # Exclusive creation refuses races rather than replacing another file.
            fd=os.open(p,os.O_WRONLY|os.O_CREAT|os.O_EXCL,mode);created.append(p)
            with os.fdopen(fd,'w') as out:out.write(data);out.flush();os.fsync(out.fileno())
    except Exception:
        for p in reversed(created):
            if p.is_dir():shutil.rmtree(p)
            else:p.unlink(missing_ok=True)
        raise
    print('Installed:',command,'\nLaunch with:',launcher,'\nDirectory MIME types are registered; the user default was not changed.');return 0
if __name__=='__main__':
    try:sys.exit(main())
    except (Failure,OSError,ValueError,KeyError) as e:print('ERRO:',e,file=sys.stderr);sys.exit(1)
