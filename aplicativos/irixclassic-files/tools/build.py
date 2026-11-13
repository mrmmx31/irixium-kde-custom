#!/usr/bin/env python3
# SPDX-FileCopyrightText: 2026 mrmmx31
# SPDX-License-Identifier: GPL-2.0-or-later
"""Build the pinned Debian-based fork. No sudo, cmake install or git writes."""
from __future__ import annotations
import argparse, hashlib, json, os, platform, shutil, subprocess, sys, tarfile
from pathlib import Path
from prepare_source import ROOT, VERSION, DEBIAN_VERSION, Failure, prepare

def run(cmd,cwd,log,env=None):
    with log.open('ab') as f:
        f.write(('\n$ '+repr(cmd)+'\n').encode());f.flush()
        p=subprocess.Popen(cmd,cwd=cwd,env=env,stdout=subprocess.PIPE,stderr=subprocess.STDOUT)
        for line in iter(p.stdout.readline,b''):
            f.write(line);f.flush();sys.stdout.buffer.write(line);sys.stdout.buffer.flush()
        if p.wait():raise Failure('Command failed; see '+str(log))

def digest(p):return hashlib.sha256(p.read_bytes()).hexdigest()
def inventory(root):
    result={}
    for p in sorted(root.rglob('*')):
        if p.is_symlink():
            target=os.readlink(p)
            if '/' in target or target.startswith('.'):raise Failure('Unsafe library symlink')
            result[p.relative_to(root).as_posix()]={'symlink':target}
        elif p.is_file():result[p.relative_to(root).as_posix()]={'sha256':digest(p),'mode':p.stat().st_mode&0o777}
    return result

def archive(source,output,arcname):
    # Corresponding-source archive must never contain font binaries or VCS credentials.
    for p in source.rglob('*'):
        if '.git' in p.relative_to(source).parts:raise Failure('Unexpected .git in release input')
        if p.suffix.lower() in ('.ttf','.otf','.woff','.woff2'):raise Failure('Font binary excluded from distribution')
    with tarfile.open(output,'w:gz',format=tarfile.PAX_FORMAT) as t:
        def normalize(info):
            info.uid=info.gid=0;info.uname=info.gname='';info.mtime=1791244800
            return info
        t.add(source,arcname=arcname,filter=normalize)

def main():
    parser=argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--trabalho',type=Path,required=True)
    source=parser.add_mutually_exclusive_group(required=True)
    source.add_argument('--baixar',action='store_true');source.add_argument('--origem',type=Path)
    parser.add_argument('--jobs',type=int,default=2)
    a=parser.parse_args()
    if os.geteuid()==0:raise Failure('Run as an ordinary user. Install build dependencies separately with apt.')
    if not 1<=a.jobs<=64:raise Failure('--jobs must be between 1 and 64')
    for tool in ('cmake','ninja','g++','dpkg-source','dbus-run-session'):
        if not shutil.which(tool):raise Failure('Missing build dependency: '+tool)
    work=a.trabalho.expanduser().absolute()
    if work.exists():raise Failure('Build directory exists. Choose a NEW directory; old logs are preserved.')
    if ROOT==work or ROOT in work.parents:raise Failure('Keep builds outside the integration checkout')
    work.mkdir(parents=True);log=work/'BUILD.log'
    try:
        integration={p.relative_to(ROOT).as_posix():digest(p) for p in ROOT.rglob('*') if p.is_file() and '__pycache__' not in p.parts and p.suffix!='.pyc'}
        originals={}
        if a.baixar:
            downloads=work/'debian-source';downloads.mkdir()
            # apt validates the download against its signed Sources index.
            run(['apt-get','source','--download-only','dolphin='+DEBIAN_VERSION],downloads,log)
            dsc=list(downloads.glob('*.dsc'))
            if len(dsc)!=1:raise Failure('Expected one Debian source control file')
            originals={p.name:digest(p) for p in downloads.iterdir() if p.is_file()}
            upstream=work/'debian-unmodified'
            run(['dpkg-source','-x',str(dsc[0]),str(upstream)],work,log)
        else:upstream=a.origem.expanduser().absolute()
        prepared=work/'source';prepare(upstream,prepared)
        (prepared/'IRIXCLASSIC-SOURCE-ARCHIVES.json').write_text(json.dumps(originals,indent=2)+'\n')
        build=work/'build'
        # No telemetry build, no original Dolphin executable or plugin target.
        run(['cmake','-S',str(prepared),'-B',str(build),'-G','Ninja',
             '-DCMAKE_BUILD_TYPE=RelWithDebInfo','-DBUILD_TESTING=OFF','-DIRIXCLASSIC_BUILD_TESTS=ON',
             '-DCMAKE_DISABLE_FIND_PACKAGE_KF6UserFeedback=TRUE','-DCMAKE_BUILD_RPATH_USE_ORIGIN=TRUE'],work,log)
        run(['cmake','--build',str(build),'--target','irixclassic-bundle','irixclassic-tests','--parallel',str(a.jobs)],work,log)
        env=os.environ.copy();env['QT_QPA_PLATFORM']='offscreen'
        # The test executable itself uses a temporary HOME and XDG directories.
        run(['dbus-run-session','--','ctest','--test-dir',str(build),'-R','^irixclassic-',
             '--no-tests=error','--output-on-failure','--output-junit',str(work/'TESTS.xml')],work,log,env)
        built=build/'irixclassic-bundle'
        binary_root=work/('IrixClassic-Files-'+VERSION);(binary_root/'bin').mkdir(parents=True);(binary_root/'lib').mkdir()
        for name in ('irixclassic-files','irixclassic-preview-worker'):
            p=built/'bin'/name
            if not p.is_file() or not os.access(p,os.X_OK):raise Failure('Missing executable '+name)
            shutil.copy2(p,binary_root/'bin'/name)
        for prefix in ('libirixclassic-files-private.so','libirixclassic-files-vcs.so'):
            found=list((built/'lib').glob(prefix+'*'))
            if not found:raise Failure('Private library missing: '+prefix)
            for p in found:
                if p.is_symlink():os.symlink(os.readlink(p),binary_root/'lib'/p.name)
                else:shutil.copy2(p,binary_root/'lib'/p.name)
        shutil.copy2(ROOT/'LICENSE',binary_root/'LICENSE')
        shutil.copy2(ROOT/'README.md',binary_root/'README.md')
        shutil.copy2(ROOT/'tools/runtime_install.py',binary_root/'instalar.py')
        meta={'version':VERSION,'channel':'experimental','debian_source':DEBIAN_VERSION,
              'architecture':platform.machine(),'native_tests_passed':True,
              'source_archives':originals,'files':inventory(binary_root),
              'limits':'Tests use Qt offscreen. Wayland interaction and full file-operation regression still require local acceptance.'}
        (binary_root/'BUILD-RESULT.json').write_text(json.dumps(meta,indent=2)+'\n')
        # Verify the relocatable loader paths; ldd is only run on our just-built code.
        result=subprocess.run(['ldd',str(binary_root/'bin/irixclassic-files')],capture_output=True,text=True,check=True)
        (work/'LDD.txt').write_text(result.stdout)
        if 'not found' in result.stdout or str(build) in result.stdout:raise Failure('Bundle still depends on the build directory, or a library is missing')
        packages=work/'pacotes';packages.mkdir()
        binary=packages/f'IrixClassic-Files-{VERSION}-linux-{platform.machine()}.tar.gz'
        archive(binary_root,binary,binary_root.name)
        source_bundle=work/('IrixClassic-Files-'+VERSION+'-source');source_bundle.mkdir()
        shutil.copytree(prepared,source_bundle/'dolphin-debian')
        shutil.copytree(ROOT,source_bundle/'integration-kit',ignore=shutil.ignore_patterns('__pycache__','*.pyc'))
        src=packages/f'IrixClassic-Files-{VERSION}-source.tar.gz';archive(source_bundle,src,source_bundle.name)
        (packages/'SHA256SUMS').write_text(''.join(digest(p)+'  '+p.name+'\n' for p in (binary,src)))
        (work/'RESULTADO-BUILD.json').write_text(json.dumps({'status':'built_and_tested','version':VERSION,
             'packages':{p.name:digest(p) for p in (binary,src)},'integration_sha256':integration,'native_tests':'passed','published':False},indent=2)+'\n')
        print('\nPacotes de teste gerados em:',packages)
        print('Não houve instalação no sistema, troca de gerenciador padrão ou publicação.')
        return 0
    except Exception as e:
        (work/'RESULTADO-BUILD.json').write_text(json.dumps({'status':'blocked','version':VERSION,'error':str(e),'published':False},indent=2)+'\n')
        raise
if __name__=='__main__':
    try:sys.exit(main())
    except (Failure,OSError,subprocess.SubprocessError) as e:print('ERRO:',e,file=sys.stderr);sys.exit(1)
