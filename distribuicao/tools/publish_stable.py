#!/usr/bin/env python3
# SPDX-FileCopyrightText: 2026 mrmmx31
# SPDX-License-Identifier: GPL-3.0-or-later
"""Publish the explicit stable release using the user's Git/GitHub CLI.

--verificar is local and read-only. --publicar creates a lightweight tag,
pushes only that tag, uploads to a draft, verifies downloaded asset bytes,
then publishes a normal release. No commit, branch push, force, clobber, or
system/theme installation. Interrupted uploads remain a draft and can resume.
"""
from __future__ import annotations
import argparse
import json
import os
from pathlib import Path
import shutil
import subprocess
import sys
import tempfile
import build_kvantum as B

REPOSITORY = 'mrmmx31/irixium-kde-custom'
TAG = 'irixclassic-kvantum-v0.7.1'
TITLE = 'IrixClassic Kvantum 0.7.1 — estável'


def run(argv: list[str], cwd: Path, timeout: int = 180) -> str:
    p = subprocess.run(argv, cwd=cwd, text=True, stdout=subprocess.PIPE,
                       stderr=subprocess.PIPE, timeout=timeout, check=False)
    if p.returncode:
        # Never print environment variables, token values, or a credential file.
        raise B.Failure(f'{argv[0]} {argv[1]} retornou {p.returncode}: '+p.stderr.strip()[-1600:])
    return p.stdout


def parse_refs(raw: str) -> dict[str, str]:
    pairs = {}
    for line in raw.splitlines():
        fields = line.split()
        if len(fields) != 2:
            raise B.Failure('Resposta git ls-remote inválida.')
        pairs[fields[1]] = fields[0]
    return pairs


def check_remote_url(url: str) -> None:
    canonical = REPOSITORY
    expected = {f'https://github.com/{canonical}', f'https://github.com/{canonical}.git',
                f'git@github.com:{canonical}', f'git@github.com:{canonical}.git',
                f'ssh://git@github.com/{canonical}', f'ssh://git@github.com/{canonical}.git'}
    if url not in expected:
        raise B.Failure('origin não aponta para o repositório público previsto. Nenhuma publicação.')


def local_plan(repo: Path) -> tuple[dict, dict[str, bytes], dict]:
    outputs, info = B.build_plan(repo)
    notes = B.read_file(repo, 'distribuicao/NOTAS-0.7.1.md').decode('utf-8')
    policy = B.document(B.read_file(repo, 'distribuicao/LANCAMENTO.json'))
    if policy.get('tag') != TAG:
        raise B.Failure('Tag diferente do registro explícito de promoção.')
    plan = {'repository': REPOSITORY, 'tag': TAG, 'title': TITLE,
            'theme_version': B.SUPPORTED_VERSION, 'channel': 'stable',
            'stable_approved': True, 'published': False, 'signed': False,
            'assets': {name: B.digest(data) for name, data in outputs.items()},
            'publication_mode': 'draft -> upload -> download/check -> publish',
            'notice': 'Plano local. Apenas --publicar escreve no GitHub.'}
    return plan, outputs, {'info': info, 'notes': notes}


def source_commit(repo: Path) -> tuple[str, str]:
    top = Path(run(['git', 'rev-parse', '--show-toplevel'], repo).strip())
    if top.resolve() != repo.resolve():
        raise B.Failure('Execute na cópia completa do repositório, não em um pacote extraído.')
    # Refuse tracked edits/staged changes; unrelated untracked files are not uploaded.
    if run(['git', 'status', '--porcelain', '--untracked-files=no'], repo).strip():
        raise B.Failure('Há alterações rastreadas sem commit. Revise e faça commit antes de publicar.')
    branch = run(['git', 'symbolic-ref', '--quiet', '--short', 'HEAD'], repo).strip()
    head = run(['git', 'rev-parse', '--verify', 'HEAD'], repo).strip()
    check_remote_url(run(['git', 'remote', 'get-url', 'origin'], repo).strip())
    spec = B.document(B.read_file(repo, 'distribuicao/ARQUIVOS.json'))
    for rel in spec['source_files']:
        # Binary-safe comparison: git hashes raw bytes, independent of encoding.
        wanted = run(['git', 'hash-object', '--no-filters', rel], repo).strip()
        committed = run(['git', 'rev-parse', '--verify', 'HEAD:'+rel], repo).strip()
        if wanted != committed:
            raise B.Failure('Arquivo de lançamento não corresponde ao commit: '+rel)
    return head, branch


def releases(repo: Path) -> list[dict]:
    rows = []
    for page in range(1, 101):
        batch = json.loads(run(['gh','api',f'repos/{REPOSITORY}/releases?per_page=100&page={page}'], repo))
        if not isinstance(batch, list):
            raise B.Failure('Resposta de releases inválida.')
        rows.extend(batch)
        if len(batch) < 100:
            return rows
    raise B.Failure('Lista de releases excessiva; nenhuma escrita.')


def find_release(repo: Path) -> dict | None:
    found = [r for r in releases(repo) if r.get('tag_name') == TAG]
    if len(found) > 1:
        raise B.Failure('Tag com múltiplas releases; revisar manualmente.')
    return found[0] if found else None


def check_release_identity(release: dict, notes: str, outputs: dict[str, bytes]) -> None:
    if release.get('tag_name') != TAG or release.get('name') != TITLE:
        raise B.Failure('Release existente não corresponde a este lançamento.')
    if (release.get('body') or '').strip() != notes.strip():
        raise B.Failure('Notas existentes diferem; não serão sobrescritas.')
    names = [a.get('name') for a in release.get('assets', [])]
    if len(names) != len(set(names)) or set(names) - set(outputs):
        raise B.Failure('Assets existentes inesperados; não serão apagados/substituídos.')
    if not release.get('draft') and release.get('prerelease'):
        raise B.Failure('Já existe prerelease publicada com esta tag. Não será modificada.')


def downloaded(repo: Path, outputs: dict[str, bytes], names: set[str]) -> None:
    if not names:
        return
    with tempfile.TemporaryDirectory(prefix='irix-verify-release-') as tmp:
        run(['gh','release','download',TAG,'--repo',REPOSITORY,'--dir',tmp], repo)
        folder=Path(tmp)
        existing={p.name for p in folder.iterdir()}
        if existing != names:
            raise B.Failure('Download contém assets diferentes dos listados.')
        for name in names:
            p=folder/name
            if p.is_symlink() or not p.is_file() or p.read_bytes() != outputs[name]:
                raise B.Failure('Asset remoto divergente: '+name+'. Nenhum overwrite foi solicitado.')


def publish(repo: Path, folder: Path) -> dict:
    if hasattr(os, 'geteuid') and os.geteuid() == 0:
        raise B.Failure('Publique como usuário normal; não use sudo.')
    for tool in ('git','gh'):
        if not shutil.which(tool):
            raise B.Failure('Programa necessário não encontrado: '+tool)
    plan, outputs, context = local_plan(repo)
    head, branch = source_commit(repo)
    run(['gh','auth','status','--hostname','github.com'], repo)
    branch_ref='refs/heads/'+branch
    remote=parse_refs(run(['git','ls-remote','--heads','origin',branch_ref], repo))
    if remote.get(branch_ref) != head:
        raise B.Failure('O commit atual ainda não é a ponta dessa branch no origin. Faça push da branch revisada.')
    tag_ref='refs/tags/'+TAG
    refs=parse_refs(run(['git','ls-remote','--tags','origin',tag_ref,tag_ref+'^{}'], repo))
    tag_target=refs.get(tag_ref+'^{}',refs.get(tag_ref))
    if tag_target is not None and tag_target != head:
        raise B.Failure('Tag remota já existe em outro commit. Não será movida.')
    existing=find_release(repo)
    if existing:
        check_release_identity(existing,context['notes'],outputs)
        if tag_target != head:
            raise B.Failure('Release existente sem tag correspondente.')
    B.no_links(folder)
    if folder.exists():
        for name, data in outputs.items():
            p=folder/name;B.no_links(p)
            if not p.is_file() or p.read_bytes()!=data:
                raise B.Failure('Pasta de assets existente diverge. Use pasta nova ou os mesmos arquivos.')
    else:
        B.write_outputs(folder, outputs, repo)
    if tag_target is None:
        # Lightweight tag: no additional tagger identity/email is recorded.
        listed=run(['git','tag','--list',TAG],repo).strip()
        if listed:
            local=run(['git','rev-parse',TAG+'^{commit}'],repo).strip()
            if local!=head:raise B.Failure('Tag local aponta para outro commit.')
        else:
            run(['git','tag',TAG,head],repo)
        run(['git','push','origin',tag_ref+':'+tag_ref],repo)
    if existing is None:
        run(['gh','release','create',TAG,'--repo',REPOSITORY,'--verify-tag','--draft',
             '--title',TITLE,'--notes-file',str(repo/'distribuicao/NOTAS-0.7.1.md'),
             '--target',head],repo)
        existing=find_release(repo)
        if existing is None:raise B.Failure('Rascunho não encontrado depois da criação.')
    check_release_identity(existing,context['notes'],outputs)
    names={a['name'] for a in existing.get('assets',[])}
    downloaded(repo,outputs,names)
    if not existing.get('draft'):
        if names!=set(outputs):raise B.Failure('Release publicada sem todos os assets; não será sobrescrita.')
        status='already_published_verified'
    else:
        missing=sorted(set(outputs)-names)
        if missing:
            run(['gh','release','upload',TAG,'--repo',REPOSITORY,*[str(folder/n) for n in missing]],repo)
        fresh=find_release(repo)
        if fresh is None:raise B.Failure('Rascunho desapareceu.')
        check_release_identity(fresh,context['notes'],outputs)
        names={a['name'] for a in fresh.get('assets',[])}
        if names!=set(outputs):raise B.Failure('Upload incompleto; o lançamento permanece rascunho.')
        downloaded(repo,outputs,names)
        run(['gh','release','edit',TAG,'--repo',REPOSITORY,'--draft=false','--prerelease=false','--latest'],repo)
        status='published_verified'
    final=find_release(repo)
    if final is None or final.get('draft') or final.get('prerelease'):
        raise B.Failure('Não foi possível confirmar a publicação estável.')
    check_release_identity(final,context['notes'],outputs)
    receipt={**plan,'status':status,'published':True,'commit':head,'url':final['html_url'],
             'release_id':final['id'],'published_at':final.get('published_at')}
    out=folder/'PUBLICACAO.json';B.no_links(out)
    out.write_bytes(B.json_bytes(receipt))
    return receipt


def main(argv=None) -> int:
    p=argparse.ArgumentParser(description=__doc__)
    mode=p.add_mutually_exclusive_group(required=True)
    mode.add_argument('--verificar',action='store_true')
    mode.add_argument('--publicar',action='store_true')
    p.add_argument('--saida',type=Path)
    a=p.parse_args(argv)
    if a.verificar:
        print(json.dumps(local_plan(B.REPO)[0],indent=2,ensure_ascii=False));return 0
    folder=(a.saida or (Path.home()/'Downloads/IrixClassic-0.7.1-publicacao')).expanduser().absolute()
    print(json.dumps(publish(B.REPO,folder),indent=2,ensure_ascii=False));return 0


if __name__=='__main__':
    try:sys.exit(main())
    except (B.Failure,OSError,ValueError,subprocess.SubprocessError) as exc:
        print('ERRO:',exc,file=sys.stderr)
        print('Não use force/clobber. Se um upload começou, a release pode estar em rascunho; repita o comando com a mesma base.',file=sys.stderr)
        sys.exit(1)
