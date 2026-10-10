#!/usr/bin/env python3
# SPDX-FileCopyrightText: 2026 mrmmx31
# SPDX-License-Identifier: GPL-2.0-or-later
"""Explicit publication of a built/tested experimental prerelease. Never stable."""
from pathlib import Path
import argparse,hashlib,json,subprocess,sys,tempfile
ROOT=Path(__file__).resolve().parents[1]
VERSION='0.1.0-alpha2';TAG='irixclassic-files-v'+VERSION
REPO='mrmmx31/irixium-kde-custom'
class Failure(RuntimeError):pass

def call(args,cwd=ROOT):return subprocess.check_output(args,cwd=cwd,text=True).strip()
def sha(p):return hashlib.sha256(p.read_bytes()).hexdigest()
def main():
    p=argparse.ArgumentParser(description=__doc__);p.add_argument('--trabalho',type=Path,required=True);p.add_argument('--publicar',action='store_true');a=p.parse_args()
    work=a.trabalho.expanduser().resolve();report=json.loads((work/'RESULTADO-BUILD.json').read_text())
    if report.get('status')!='built_and_tested' or report.get('version')!=VERSION or report.get('native_tests')!='passed':raise Failure('A successful native build/test receipt is required')
    expected=report.get('integration_sha256',{})
    current={q.relative_to(ROOT).as_posix():sha(q) for q in ROOT.rglob('*') if q.is_file() and '__pycache__' not in q.parts and q.suffix!='.pyc'}
    if not expected or expected!=current:raise Failure('Integration source changed after the native build. Rebuild before publication.')
    files=[]
    for name,digest in report['packages'].items():
        if Path(name).name!=name:raise Failure('Unsafe artifact name')
        f=work/'pacotes'/name
        if not f.is_file() or sha(f)!=digest:raise Failure('Artifact hash mismatch: '+name)
        files.append(f)
    checks=work/'pacotes/SHA256SUMS';files.append(checks)
    checkout=Path(call(['git','rev-parse','--show-toplevel']));commit=call(['git','rev-parse','HEAD'])
    if call(['git','status','--porcelain'],checkout):raise Failure('Commit/review all pending changes before publishing the branch')
    origin=call(['git','remote','get-url','origin'],checkout)
    if origin not in (f'https://github.com/{REPO}.git',f'https://github.com/{REPO}',f'git@github.com:{REPO}.git'):raise Failure('Unexpected origin repository')
    if not a.publicar:
        print(json.dumps({'ready_for_explicit_publication':True,'tag':TAG,'commit':commit,'prerelease':True,'published':False},indent=2));return 0
    # Read first: the commit must exist remotely, and no tag/release is replaced.
    call(['gh','api',f'repos/{REPO}/commits/{commit}','--jq','.sha'])
    if call(['git','ls-remote','--tags','origin','refs/tags/'+TAG],checkout):raise Failure('Tag exists. Do not overwrite it; inspect an interrupted draft or use a new version.')
    cmd=['gh','release','create',TAG,*map(str,files),'--repo',REPO,'--target',commit,'--prerelease','--draft',
         '--title','IrixClassic Files '+VERSION,'--notes-file',str(ROOT/'docs/RELEASE-NOTES.md')]
    call(cmd,checkout)
    with tempfile.TemporaryDirectory(prefix='irix-release-check-') as tmp:
        call(['gh','release','download',TAG,'--repo',REPO,'--dir',tmp],checkout)
        for f in files:
            if sha(Path(tmp)/f.name)!=sha(f):raise Failure('Downloaded release asset differs; draft was NOT published')
    call(['gh','release','edit',TAG,'--repo',REPO,'--draft=false','--prerelease'],checkout)
    url=call(['gh','release','view',TAG,'--repo',REPO,'--json','url','--jq','.url'],checkout)
    receipt={'status':'published','channel':'experimental','tag':TAG,'commit':commit,'url':url,'signed':False}
    (work/'PUBLICACAO.json').write_text(json.dumps(receipt,indent=2)+'\n');print(json.dumps(receipt,indent=2));return 0
if __name__=='__main__':
    try:sys.exit(main())
    except (Failure,OSError,ValueError,KeyError,subprocess.SubprocessError) as e:print('ERRO:',e,file=sys.stderr);sys.exit(1)
