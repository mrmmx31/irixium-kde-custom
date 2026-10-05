#!/usr/bin/env python3
# SPDX-FileCopyrightText: 2026 mrmmx31
# SPDX-License-Identifier: GPL-3.0-or-later
"""Run an integrated review with explicit static/native/manual result categories.

No installation, privilege escalation, global settings, or automatic system fix.
Logs are written only to a new/empty directory. Missing native dependencies are
reported as unavailable, never counted as passed. Visual acceptance remains manual.
"""
from __future__ import annotations
import argparse
import hashlib
import html
import json
import os
import re
from pathlib import Path
import subprocess
import sys
sys.dont_write_bytecode=True
from arrow_runtime import make_private_folder
ROOT=Path(__file__).resolve().parents[2]
BLOCKS=(('1','Rolagem','preview_scrollbars.py'),('2','Botões','preview_buttons.py'),
        ('3','Campos','preview_entries.py'),('4','Seleção','preview_selection.py'),
        ('5','Menus','preview_menus.py'),('6','Abas','preview_tabs.py'),
        ('7','Demais controles','preview_controls.py'))


def digest(data):return hashlib.sha256(data).hexdigest()

def fingerprints(root):
    paths=[]
    for part in ('kvantum/IrixClassic','kvantum/Irixium','aurorae','classic-rewrite-rc1','moderno','gtk'):
        directory=root/part
        if directory.is_dir():paths.extend(p for p in directory.rglob('*') if p.is_file() and '__pycache__' not in p.parts)
    return {str(p.relative_to(root)):digest(p.read_bytes()) for p in sorted(paths)}


def integrity(root):
    source=root/'kvantum/IrixClassic'
    doc=json.loads((source/'MANIFEST.json').read_text('utf-8'))
    failures=[]
    if not {'IrixClassic.svg','IrixClassic.kvconfig','LICENSE'} <= doc['files'].keys():
        failures.append('manifest_required_files')
    for name,expected in doc['files'].items():
        if Path(name).name!=name or not(source/name).is_file() or digest((source/name).read_bytes())!=expected:
            failures.append(name)
    return {'version':doc.get('version'),'passed':not failures,'failures':failures,
        'svg_sha256':digest((source/'IrixClassic.svg').read_bytes()),
        'config_sha256':digest((source/'IrixClassic.kvconfig').read_bytes())}


def tasks(native):
    out=[('static-theme',[sys.executable,'-m','unittest','discover','-s','kvantum/tests','-p','test_*.py','-v'],'static',300),
         ('static-install',[sys.executable,'-m','unittest','discover','-s','tests','-p','test_*.py','-v'],'static',120)]
    if native:
        for number,label,script in BLOCKS:
            # Three legacy block galleries explicitly use offscreen; this is not
            # evidence of Wayland compositor/input behavior. Keep the label honest.
            mode='qt-widgets-offscreen' if number in ('1','2','3') else 'qt-widgets-session'
            out.append(('native-block-'+number,[sys.executable,'kvantum/tools/'+script,'--testar'],mode,90))
        out.append(('native-integrated',[sys.executable,'kvantum/tools/preview_integrated.py','--testar'],'qt-widgets-session',90))
    return out


def unittest_counts(text):
    """Describe unittest's own summary, including skipped tests explicitly."""
    matches=list(re.finditer(r"^Ran (\d+) tests? in .+$",text,re.M))
    if not matches:return None
    tail=text[matches[-1].end():]
    total=int(matches[-1].group(1))
    skipped_match=re.search(r"skipped=(\d+)",tail)
    skipped=int(skipped_match.group(1)) if skipped_match else 0
    ok=bool(re.search(r"^OK(?: \(skipped=\d+\))?\s*$",tail,re.M))
    return {'run':total,'skipped':skipped,'passed':total-skipped if ok else None}


def arrow_paths(arrow_doc):
    """Keep installed and temporary results separate; collection is not repair."""
    paths={}
    for name,probe in arrow_doc.get('probes',{}).items():
        result=probe.get('result') or {}
        checks=result.get('checks') or []
        paths[name]={'returncode':probe.get('returncode'),
            'assessment':result.get('assessment'),
            'reported_status':result.get('status',probe.get('status')),
            'check_count':len(checks),
            'pixel_changes':sum(c.get('arrow_pixels_changed') is True for c in checks),
            'temporary_fix':bool(result.get('temporary_fix',False))}
    return paths


def run_task(name,args,category,timeout,root,folder):
    env=dict(os.environ,PYTHONDONTWRITEBYTECODE='1')
    try:
        p=subprocess.run(args,cwd=root,env=env,capture_output=True,text=True,timeout=timeout)
        code=p.returncode;stdout=p.stdout;stderr=p.stderr
    except subprocess.TimeoutExpired:
        code=124;stdout='';stderr='Tempo limite atingido; tarefa não aprovada.'
    except OSError as exc:
        code=127;stdout='';stderr=str(exc)
    status='passed' if code==0 else 'unavailable' if code==77 else 'failed'
    # Preserve useful errors, but avoid putting an absolute home path in the log.
    text=(stdout+'\n'+stderr).replace(str(Path.home()),'~')
    (folder/(name+'.log')).write_text(text,encoding='utf-8');(folder/(name+'.log')).chmod(0o600)
    row={'name':name,'category':category,'returncode':code,'status':status,'log':name+'.log'}
    counts=unittest_counts(text) if category=='static' else None
    if counts:
        row['test_counts']=counts
        if code==0 and counts['skipped']:
            row['status']='passed_with_skips'
    return row


def overall(rows,native_requested,preserved,ok):
    if not preserved or not ok or any(r['status']=='failed' for r in rows):return 'falhas_detectadas'
    if native_requested and any(r['status']=='unavailable' for r in rows):return 'nativo_incompleto'
    return 'aguarda_aceitacao_visual' if native_requested else 'estaticos_concluidos_nativo_pendente'


def write_reports(folder,doc):
    path=folder/'REVISAO-INTEGRADA.json'
    path.write_text(json.dumps(doc,ensure_ascii=False,indent=2)+'\n',encoding='utf-8');path.chmod(0o600)
    rows=''.join('<tr><td>'+html.escape(r['name'])+'</td><td>'+html.escape(r['category'])+
        '</td><td>'+html.escape(r['status'])+'</td><td>'+str(r['returncode'])+'</td><td>'+html.escape(str(r.get('test_counts','—')))+'</td></tr>' for r in doc['tasks'])
    arrow_rows=''
    for name,info in doc.get('arrow_paths',{}).items():
        verdict=(info.get('assessment') or {}).get('verdict',info.get('reported_status'))
        arrow_rows+='<tr><td>'+html.escape(name)+'</td><td>'+html.escape(str(verdict))+'</td><td>'+str(info.get('pixel_changes',0))+'/'+str(info.get('check_count',0))+'</td></tr>'
    arrow_html='<h2>Setas: instalado não é temporário</h2><table><tr><th>Caminho</th><th>Resultado</th><th>Mudança de pixels</th></tr>'+arrow_rows+'</table><p>Uma aprovação na cópia temporária não instala a correção no KDE.</p>' if arrow_rows else ''
    page='''<!doctype html><html lang="pt-BR"><meta charset="utf-8"><title>Revisão integrada — IrixClassic</title>
<style>body{font:16px sans-serif;max-width:1000px;margin:40px auto;line-height:1.5}table{border-collapse:collapse;width:100%}th,td{border:1px solid #aaa;padding:8px;text-align:left}code{background:#eee;padding:2px}h1{line-height:1.2}</style>
<h1>Revisão integrada — IrixClassic</h1><p><b>''' +html.escape(doc['status'])+'''</b></p><p>Execução de teste não equivale a identidade histórica nem aceitação visual. Os resultados Qt Widgets não certificam Qt Quick.</p>
<table><tr><th>Tarefa</th><th>Categoria</th><th>Estado</th><th>Código</th><th>Contagem unittest</th></tr>'''+rows+'''</table>'''+arrow_html+'''
<h2>Próxima conferência manual</h2><p>Abra <code>prever-integracao.sh</code>. Compare os mesmos controles, tamanhos e estados com as referências; preencha a lista abaixo em arquivo separado, sem sobrescrever este registro.</p><ul>'''+''.join('<li>'+html.escape(b['name'])+' — '+html.escape(b['status'])+'</li>' for b in doc['acceptance'])+'''</ul><p>O teste de setas usa um relatório próprio: COMPARACAO-SETAS.json. Este painel não o transforma automaticamente em aprovação.</p></html>'''
    path=folder/'REVISAO-INTEGRADA.html';path.write_text(page,encoding='utf-8');path.chmod(0o600)


def main(argv=None):
    p=argparse.ArgumentParser(description=__doc__);p.add_argument('--saida',type=Path,required=True)
    p.add_argument('--nativos',action='store_true');p.add_argument('--comparar-setas',action='store_true')
    a=p.parse_args(argv);folder=make_private_folder(a.saida)
    first=fingerprints(ROOT);info=integrity(ROOT)
    doc={'review_version':'r2','theme':info,'tasks':[],'native_requested':a.nativos,
        'status':'em_execucao','acceptance':[{'block':n,'name':label,'status':'pendente nesta revisão'} for n,label,_ in BLOCKS],
        'notes':['No system patch installed. No global theme or font changed.',
                 'Block 1/2 artwork was approved in prior feedback; this record does not invent new acceptance.']}
    write_reports(folder,doc)
    if not info['passed']:print('Integridade do tema divergente. Execução interrompida.',file=sys.stderr);return 1
    try:
        for task in tasks(a.nativos):
            print('Executando:',task[0],flush=True)
            doc['tasks'].append(run_task(*task,ROOT,folder));write_reports(folder,doc)
        if a.comparar_setas:
            doc['tasks'].append(run_task('arrow-collection',[sys.executable,'kvantum/tools/compare_arrows.py',
                '--estilo','kvantum','--saida',str(folder/'setas')],'native-evidence-collection',270,ROOT,folder))
            # Collector exit 0 means saved observations, not that each path passed.
            if doc['tasks'][-1]['status']=='passed':doc['tasks'][-1]['status']='collected_not_certified'
            arrow_file=folder/'setas/COMPARACAO-SETAS.json'
            if arrow_file.is_file():
                arrow_doc=json.loads(arrow_file.read_text('utf-8'))
                doc['arrow_paths']=arrow_paths(arrow_doc)
                doc['arrows']=arrow_doc.get('probes',{}).get('quick_installed',{}).get('result',{}).get('assessment',
                    {'all_passed':False,'verdict':'no_complete_native_assessment'})
    except KeyboardInterrupt:
        doc['status']='interrompido';doc['preserved']=fingerprints(ROOT)==first;write_reports(folder,doc);return 130
    doc['preserved']=fingerprints(ROOT)==first
    doc['status']=overall(doc['tasks'],a.nativos,doc['preserved'],info['passed'])
    if doc['status'] not in ('falhas_detectadas','nativo_incompleto') and a.comparar_setas and not doc.get('arrows',{}).get('all_passed'):
        doc['status']='pendencia_setas_qtquick'
    write_reports(folder,doc)
    print('Relatório:',folder/'REVISAO-INTEGRADA.html')
    print('Estado:',doc['status']);print('Aceitação visual e histórico IRIX permanecem separados dos testes automatizados.')
    return 1 if doc['status']=='falhas_detectadas' else 77 if doc['status']=='nativo_incompleto' else 2 if doc['status']=='pendencia_setas_qtquick' else 0

if __name__=='__main__':
    try:sys.exit(main())
    except (OSError,ValueError,KeyError,TypeError) as exc:print('ERRO:',exc,file=sys.stderr);sys.exit(1)
