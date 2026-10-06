#!/usr/bin/env python3
# SPDX-FileCopyrightText: 2026 mrmmx31
# SPDX-License-Identifier: GPL-3.0-or-later
"""Close the candidate's review, without publishing, installing globally or approving it.

One collection includes static suites, real Qt gallery tests, same-layout
captures, package integrity and a temporary-HOME installation/restore exercise.
Visual acceptance is recorded separately by a person and bound to the report.
This tool never upgrades the version, creates tags or reinstalls the KDE patch.
"""
from __future__ import annotations
import argparse
import datetime
import hashlib
import html
import importlib.util
import json
import os
from pathlib import Path
import re
import stat
import subprocess
import sys
import tempfile
import zipfile
sys.dont_write_bytecode = True
import build_kvantum as B
import smoke_package

ROOT = Path(__file__).absolute().parents[2]
CANDIDATE_VERSION = '0.7.1-rc1'
MANUAL = {
    'toolbar': 'Separadores finos, centrados e sem blocos esticados nas duas orientações.',
    'spinbox': 'Símbolos legíveis, pressão/soltura e limites visíveis; sem confundir com a scrollbar.',
    'conjunto_e_limites': 'Conjunto sem cortes ou regressões; diferenças documentadas (readonly/Qt Quick/históricas) revisadas.'
}
EXPECTED_NATIVE = {
    'classic-selection': ('results', 'IrixClassic', False),
    'classic-menus': ('results', 'IrixClassic', True),
    'modern-selection': ('results', 'Irixium', False),
    'modern-menus': ('results', 'Irixium', True),
    'finishing': ('results', 'IrixClassic', True),
    'classic-integrated': ('checks', 'IrixClassic', False),
    'modern-integrated': ('checks', 'Irixium', False),
}
EXPECTED_COUNTS = {'classic-selection':11,'modern-selection':11,'classic-menus':17,
                   'modern-menus':11,'finishing':7,'classic-integrated':15,'modern-integrated':15}
LIMITS = [
    'No universal readonly-only SVG state; editable and read-only fields may share a surface.',
    'Not every Qt Quick or custom application control is drawn by Kvantum.',
    'Some IRIX-specific behaviors require application/engine support; adaptations are documented.',
    'Screenshots are this gallery only. No historical pixel-identity certification is issued.',
    'The separate KDE arrow repair is not reapplied or retested automatically.'
]


def dump(value): return (json.dumps(value, indent=2, ensure_ascii=False, sort_keys=True)+'\n').encode()
def sha(data): return hashlib.sha256(data).hexdigest()


def atomic(path, data):
    B.no_links(path)
    fd, tmp = tempfile.mkstemp(prefix='.irix-final-', dir=path.parent)
    try:
        with os.fdopen(fd, 'wb') as stream:
            stream.write(data); stream.flush(); os.fsync(stream.fileno())
        os.replace(tmp, path)
    finally:
        if os.path.exists(tmp): os.unlink(tmp)


def new_output(path, repo=ROOT):
    path = path.expanduser().absolute(); B.no_links(path)
    if path == repo or repo in path.parents: raise B.Failure('Saída deve ficar fora do clone.')
    if not path.parent.is_dir(): raise B.Failure('Diretório pai da saída não existe.')
    path.mkdir(mode=0o700, exist_ok=False)
    return path


def sources(repo):
    result = {}
    for part in ('kvantum', 'tools', 'tests', 'distribuicao', 'moderno'):
        root = repo/part
        if root.is_dir():
            for p in sorted(root.rglob('*')):
                if '.git' in p.parts or '__pycache__' in p.parts: continue
                if p.is_symlink(): raise B.Failure('Link em insumo da revisão: '+str(p.relative_to(repo)))
                if p.is_file(): result[p.relative_to(repo).as_posix()] = sha(p.read_bytes())
    return result


def extract_json(text):
    decoder = json.JSONDecoder(); values = []
    for m in re.finditer(r'^\s*\{', text, re.M):
        try:
            value, _ = decoder.raw_decode(text[m.end()-1:])
            if isinstance(value, dict): values.append(value)
        except ValueError: pass
    return next((v for v in reversed(values) if any(k in v for k in ('results','checks'))), None)


def native_verdict(name, code, doc):
    if code == 77: return 'unavailable'
    if code != 0: return 'failed'
    if not isinstance(doc, dict): return 'inconclusive'
    key, theme, require_completed = EXPECTED_NATIVE[name]
    checks = doc.get(key)
    if not isinstance(checks, list) or len(checks) < EXPECTED_COUNTS[name]: return 'inconclusive'
    if any(not isinstance(c, dict) or c.get('passed') is not True for c in checks): return 'failed'
    if require_completed and (doc.get('completed') is not True or doc.get('status') != 'passed'): return 'inconclusive'
    if doc.get('theme') != theme: return 'inconclusive'
    style = doc.get('style_class', doc.get('style', ''))
    if style != 'Kvantum::Style': return 'inconclusive'
    if not isinstance(doc.get('platform'), str) or not doc['platform']: return 'inconclusive'
    return 'passed'


def counts(text):
    matches = list(re.finditer(r'^Ran (\d+) tests? in .+$', text, re.M))
    if not matches: return None
    m = matches[-1]; tail = text[m.end():]; skipped = re.search(r'skipped=(\d+)', tail)
    n = int(m.group(1)); skip = int(skipped.group(1)) if skipped else 0
    ok = bool(re.search(r'^OK(?: \([^\n]*\))?\s*$', tail, re.M))
    return {'run':n, 'skipped':skip, 'passed':n-skip if ok else None}


def tasks(native=True):
    jobs = []
    for name, path in (('static-theme','kvantum/tests'),('static-install','tests'),('static-distribution','distribuicao/tests')):
        jobs.append((name, [sys.executable,'-B','-m','unittest','discover','-s',path,'-p','test_*.py','-v'], 'static', 300))
    if native:
        for theme, short in (('IrixClassic','classic'), ('Irixium','modern')):
            for kind, script in (('selection','preview_selection.py'),('menus','preview_menus.py')):
                jobs.append((short+'-'+kind,[sys.executable,'-B','kvantum/tools/'+script,'--testar','--tema',theme], 'native', 90))
        jobs.append(('finishing',[sys.executable,'-B','kvantum/tools/preview_finish.py','--testar'], 'native', 90))
        for theme, short in (('IrixClassic','classic'),('Irixium','modern')):
            jobs.append((short+'-integrated',[sys.executable,'-B','kvantum/tools/preview_integrated.py','--testar','--tema',theme,'--fonte-px','14'], 'native', 90))
    return jobs


def run_task(job, repo, output):
    name, argv, category, timeout = job
    args = list(argv)
    if name in ('finishing','classic-integrated','modern-integrated'):
        args += ['--capturas', str(output/'capturas'/name)]
    env = dict(os.environ, PYTHONDONTWRITEBYTECODE='1')
    try:
        p = subprocess.run(args, cwd=repo, env=env, capture_output=True, text=True, timeout=timeout)
        code, stdout, stderr = p.returncode, p.stdout, p.stderr
    except subprocess.TimeoutExpired as exc:
        code = 124
        stdout = exc.stdout.decode(errors='replace') if isinstance(exc.stdout, bytes) else (exc.stdout or '')
        stderr = 'Tempo limite; ensaio não concluído.'
    except OSError as exc: code, stdout, stderr = 127, '', str(exc)
    raw = stdout+'\n'+stderr
    sanitized = raw.replace(str(repo), '<clone>').replace(str(Path.home()), '<home>').replace(str(output), '<coleta>')
    atomic(output/'logs'/(name+'.log'), sanitized.encode())
    doc = extract_json(stdout)
    row = {'name':name, 'category':category, 'returncode':code, 'log':'logs/'+name+'.log'}
    if category == 'native':
        row['status'] = native_verdict(name,code,doc)
        row['platform'] = doc.get('platform') if doc else None
        if doc:
            safe_doc = json.loads(json.dumps(doc).replace(str(repo),'<clone>').replace(str(Path.home()),'<home>').replace(str(output),'<coleta>'))
            atomic(output/'resultados'/(name+'.json'), dump(safe_doc))
            row['result'] = 'resultados/'+name+'.json'
            key = EXPECTED_NATIVE[name][0]; row['checks'] = len(doc.get(key,[]))
        # Offscreen/minimal do not establish acceptance in the user's desktop.
        row['desktop_evidence'] = row['status']=='passed' and row['platform'] in ('wayland','xcb')
    else:
        c = counts(raw); row['test_counts'] = c
        row['status'] = 'failed' if code != 0 else 'inconclusive' if not c or not c['run'] or c['passed'] is None else 'passed_with_skips' if c['skipped'] else 'passed'
    return row


def decision(doc, manual=None):
    rows = doc.get('tasks', [])
    failed = [r['name'] for r in rows if r.get('status') == 'failed']
    if doc.get('preserved') is not True: failed.append('source_integrity')
    for k in ('packages_verified','packages_reproducible'):
        if doc.get(k) is not True: failed.append(k)
    smoke = doc.get('installation',{})
    if smoke.get('status') == 'failed': failed.append('package_install_restore')
    if failed: return 'blocked', 1, sorted(set(failed))
    names = {r['name'] for r in rows}
    pending = [r['name'] for r in rows if r.get('status') not in ('passed',)]
    pending += sorted((set(EXPECTED_NATIVE)|{'static-theme','static-install','static-distribution'})-names)
    for rel in ('capturas/finishing/01-acabamento.png','capturas/finishing/02-toolbar-horizontal.png',
                'capturas/finishing/03-toolbar-vertical.png',
                'capturas/classic-integrated/01-conjunto.png','capturas/modern-integrated/01-conjunto.png'):
        if rel not in doc.get('evidence',{}): pending.append(rel)
    for r in rows:
        if r.get('category')=='native' and not r.get('desktop_evidence'): pending.append(r['name']+':desktop')
    if smoke.get('status') != 'passed': pending.append('package_install_restore')
    if pending: return 'evidence_incomplete', 77, sorted(set(pending))
    if manual is None: return 'awaiting_visual_acceptance', 2, list(MANUAL)
    states = manual.get('items', {})
    if set(states) != set(MANUAL): raise B.Failure('Matriz de aceite incompleta ou desconhecida.')
    statuses = [states[k].get('status') if isinstance(states[k],dict) else None for k in MANUAL]
    if any(s not in ('pendente','aprovado','reprovado') for s in statuses): raise B.Failure('Status de aceite inválido.')
    if 'reprovado' in statuses: return 'visual_changes_requested', 2, [k for k in MANUAL if states[k]['status']=='reprovado']
    if statuses != ['aprovado']*len(MANUAL): return 'awaiting_visual_acceptance', 2, [k for k in MANUAL if states[k]['status']!='aprovado']
    if manual.get('responsible') != 'mrmmx31' or not isinstance(manual.get('date'),str) or not re.fullmatch(r'\d{4}-\d{2}-\d{2}',manual['date']):
        raise B.Failure('Informe nick e data do aceite, sem nome civil ou e-mail.')
    datetime.date.fromisoformat(manual['date'])
    return 'candidate_accepted_locally', 0, []


def evidence_hashes(folder):
    result = {}
    for root_name in ('logs','resultados','capturas','pacotes'):
        root = folder/root_name
        if not root.exists(): continue
        for p in sorted(root.rglob('*')):
            B.no_links(p)
            if p.is_file():
                if p.stat().st_size > 16*1024*1024: raise B.Failure('Evidência excessiva.')
                result[p.relative_to(folder).as_posix()] = sha(p.read_bytes())
    return result


def write_reports(folder, doc):
    atomic(folder/'FECHAMENTO.json',dump(doc))
    rows = ''.join('<tr><td>'+html.escape(r['name'])+'</td><td>'+html.escape(r['status'])+'</td><td>'+html.escape(str(r.get('test_counts',r.get('checks','—'))))+'</td></tr>' for r in doc['tasks'])
    imgs = ''.join('<h3>'+html.escape(rel)+'</h3><img style="max-width:100%;image-rendering:pixelated" src="'+html.escape(rel,quote=True)+'">'
                   for rel in doc.get('evidence',{}) if rel.startswith('capturas/') and rel.endswith('.png'))
    body = '<!doctype html><html lang="pt-BR"><meta charset="utf-8"><title>Fechamento IrixClassic</title><style>body{font:16px sans-serif;max-width:1150px;margin:36px auto;line-height:1.5}td,th{border:1px solid #999;padding:7px}table{border-collapse:collapse}</style><h1>IrixClassic '+CANDIDATE_VERSION+'</h1><p><b>'+html.escape(doc['status'])+'</b></p><p>Aceite visual não é inferido dos testes. A versão continua candidata; sem publicação, tag ou instalação global.</p><table><tr><th>Ensaio</th><th>Estado</th><th>Contagem</th></tr>'+rows+'</table><h2>Instalação isolada</h2><p>'+html.escape(doc['installation']['status'])+'</p><h2>Conferência visual</h2>'+imgs+'<h2>Limitações</h2><ul>'+''.join('<li>'+html.escape(s)+'</li>' for s in LIMITS)+'</ul><p>Reveja ACEITE-VISUAL.json e depois execute --avaliar. Hashes não são assinaturas digitais.</p></html>'
    atomic(folder/'FECHAMENTO.html',body.encode())


def export_evidence(folder):
    """Export only known report/log/gallery files; never the user's whole folder."""
    known = ['FECHAMENTO.json','FECHAMENTO.html','ACEITE-VISUAL.json','PARECER-FINAL.json']
    doc = B.document((folder/'FECHAMENTO.json').read_bytes())
    known += [n for n in doc.get('evidence',{}) if not n.startswith('pacotes/')]
    target = folder/'EVIDENCIAS-PARA-REVISAO.zip'
    stream = tempfile.NamedTemporaryFile(prefix='.irix-evidence-', dir=folder,delete=False); temp=Path(stream.name);stream.close()
    try:
        total = 0
        with zipfile.ZipFile(temp,'w',compression=zipfile.ZIP_DEFLATED) as z:
            for rel in sorted(set(known)):
                if not B.safe_name(rel): raise B.Failure('Nome inválido de evidência.')
                p=folder/rel;B.no_links(p)
                if not p.exists():continue
                if not p.is_file():raise B.Failure('Evidência não regular.')
                b=p.read_bytes();total+=len(b)
                if total>64*1024*1024:raise B.Failure('Coleta excede limite de exportação.')
                zi=zipfile.ZipInfo('irixclassic-fechamento/'+rel,B.DATE);zi.external_attr=(stat.S_IFREG|0o600)<<16;zi.compress_type=zipfile.ZIP_DEFLATED
                z.writestr(zi,b)
        os.replace(temp,target)
    finally:temp.unlink(missing_ok=True)


def collect(repo, folder, native=True):
    before=sources(repo); outputs,package_info=B.build_plan(repo)
    for d in ('logs','resultados','capturas'): (folder/d).mkdir(mode=0o700)
    B.write_outputs(folder/'pacotes',outputs,repo)
    second,_=B.build_plan(repo)
    doc={'format':1,'revision':'fechamento-r1','theme_version':CANDIDATE_VERSION,
         'channel':'candidate','stable_approved':False,'native_requested':native,'tasks':[],
         'sources_sha256':sha(dump(before)), 'source_files':before,
         'packages_verified':True,'packages_reproducible':outputs==second,
         'theme_svg_sha256':before['kvantum/IrixClassic/IrixClassic.svg'],
         'theme_config_sha256':before['kvantum/IrixClassic/IrixClassic.kvconfig'],
         'installation':{'status':'pending'},'preserved':False,'status':'running','known_limits':LIMITS}
    write_reports(folder,doc)
    try:
        for job in tasks(native):
            print('Executando:',job[0],flush=True)
            doc['tasks'].append(run_task(job,repo,folder));write_reports(folder,doc)
        try: doc['installation']=smoke_package.run(repo)
        except (B.Failure,OSError,ValueError,subprocess.SubprocessError) as exc:
            doc['installation']={'status':'failed','error':str(exc)}
    except KeyboardInterrupt:
        doc['tasks'].append({'name':'interrupted','status':'failed','category':'collection'})
    finally:
        doc['preserved']=before==sources(repo)
        doc['evidence']=evidence_hashes(folder)
        doc['status'], code, doc['pending']=decision(doc)
        write_reports(folder,doc)
    manual={'format':1,'report_sha256':sha((folder/'FECHAMENTO.json').read_bytes()),
            'theme_version':CANDIDATE_VERSION,'responsible':'mrmmx31','date':'',
            'items':{k:{'status':'pendente','criterion':v,'notes':''} for k,v in MANUAL.items()},
            'notice':'Preencher após inspeção humana. Este modelo não é um aceite; hashes não são assinaturas.'}
    atomic(folder/'ACEITE-VISUAL.json',dump(manual));export_evidence(folder)
    print('Resultado:',doc['status']);print('Relatório:',folder/'FECHAMENTO.html')
    print('Arquivo para revisão:',folder/'EVIDENCIAS-PARA-REVISAO.zip')
    return code


def evaluate(folder, repo=ROOT):
    B.no_links(folder)
    doc=B.document(B.read_file(folder,'FECHAMENTO.json'));manual=B.document(B.read_file(folder,'ACEITE-VISUAL.json'))
    if doc.get('format')!=1 or doc.get('theme_version')!=CANDIDATE_VERSION or doc.get('revision')!='fechamento-r1':raise B.Failure('Relatório não reconhecido.')
    if manual.get('format')!=1 or manual.get('theme_version')!=CANDIDATE_VERSION or manual.get('report_sha256')!=sha((folder/'FECHAMENTO.json').read_bytes()):
        raise B.Failure('O aceite não pertence a este relatório.')
    if sources(repo)!=doc.get('source_files'):raise B.Failure('Fontes mudaram desde a coleta; gere evidência atualizada.')
    if evidence_hashes(folder)!=doc.get('evidence'):raise B.Failure('Evidência mudou, desapareceu ou foi acrescentada desde a coleta.')
    status, code, pending=decision(doc,manual)
    verdict={'status':status,'pending':pending,'report_sha256':manual['report_sha256'],
             'theme_version':CANDIDATE_VERSION,'channel':'candidate','stable_approved':False,
             'published':False,'signed':False,'notice':'Este parecer não altera versões nem publica pacotes.'}
    atomic(folder/'PARECER-FINAL.json',dump(verdict));export_evidence(folder)
    print(json.dumps(verdict,indent=2,ensure_ascii=False));return code


def main(argv=None):
    p=argparse.ArgumentParser(description=__doc__)
    group=p.add_mutually_exclusive_group(required=True)
    group.add_argument('--verificar',action='store_true')
    group.add_argument('--saida',type=Path)
    group.add_argument('--avaliar',type=Path)
    p.add_argument('--sem-nativos',action='store_true',help='Somente desenvolvimento; nunca conclui o aceite de desktop.')
    a=p.parse_args(argv)
    if a.sem_nativos and not a.saida:p.error('--sem-nativos exige --saida.')
    if a.saida and '-' not in B.SUPPORTED_VERSION:
        raise B.Failure('Versão estável: o aceite da candidata já está encerrado. Use gerar-kvantum.sh e publicar-estavel.sh.')
    if a.verificar:
        _, info=B.build_plan(ROOT)
        print(json.dumps({'version':CANDIDATE_VERSION,'tasks':[j[0] for j in tasks()],
                          'packages':list(info['packages']),'writes':False},indent=2));return 0
    if hasattr(os,'geteuid') and os.geteuid()==0:raise B.Failure('Execute como usuário normal, sem sudo.')
    if a.avaliar:return evaluate(a.avaliar.expanduser().absolute())
    return collect(ROOT,new_output(a.saida),not a.sem_nativos)


if __name__=='__main__':
    try:sys.exit(main())
    except (B.Failure,OSError,ValueError,TypeError,KeyError) as exc:
        print('ERRO:',exc,file=sys.stderr);sys.exit(1)
