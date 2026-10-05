#!/usr/bin/env python3
"""Atualiza uma única IRIX Classic no perfil do usuário; backup e reversão verificáveis."""
from __future__ import annotations
import argparse
import ast
from contextlib import contextmanager
from datetime import datetime, timezone
import fcntl
import hashlib
import json
import os
from pathlib import Path
import re
import shutil
import subprocess
import sys
import uuid

BUNDLE = Path(__file__).resolve().parent.parent
IDS = ('irix_classic', 'irixium_irix_classic_v4', 'irixium_irix_classic_v5')
GROUP = 'org.kde.kdecoration2'
LIBRARY = 'org.kde.kwin.aurorae'
VERSION = '1.0.0-rc1'
KEYS = ('library','theme')


def no_links(path: Path) -> None:
    for part in (path, *path.parents):
        if part.is_symlink():
            raise RuntimeError(f'Link simbólico não será substituído/seguido: {part}')


def tree_hashes(path: Path) -> dict[str,str]:
    no_links(path)
    if not path.is_dir():
        raise RuntimeError(f'Pasta ausente: {path}')
    result = {}
    for item in sorted(path.rglob('*')):
        if item.is_symlink():
            raise RuntimeError(f'Link simbólico dentro do tema: {item}')
        if item.is_file():
            result[item.relative_to(path).as_posix()] = hashlib.sha256(item.read_bytes()).hexdigest()
        elif not item.is_dir():
            raise RuntimeError(f'Arquivo especial recusado: {item}')
    return result


def atomic_json(path: Path, value: dict) -> None:
    no_links(path)
    temp = path.with_name(path.name + '.tmp-' + uuid.uuid4().hex)
    try:
        with temp.open('x',encoding='utf-8') as stream:
            json.dump(value,stream,ensure_ascii=False,indent=2)
            stream.write('\n'); stream.flush(); os.fsync(stream.fileno())
        os.replace(temp,path)
    finally:
        if temp.exists(): temp.unlink()


def read_json(path: Path) -> dict:
    no_links(path)
    return json.loads(path.read_text(encoding='utf-8'))


def command(args: list[str]) -> str:
    p = subprocess.run(args,capture_output=True,text=True,timeout=20)
    if p.returncode:
        raise RuntimeError(f'{Path(args[0]).name}: {p.stderr.strip() or p.stdout.strip()}')
    return p.stdout.rstrip('\n')


class KDEConfig:
    def __init__(self,path: Path): self.path = path
    def get(self,key: str) -> str | None:
        marker = '__IRIX_ABSENT_' + uuid.uuid4().hex
        value = command(['kreadconfig6','--file',str(self.path),'--group',GROUP,
                         '--key',key,'--default',marker])
        return None if value == marker else value
    def put(self,key: str,value: str | None) -> None:
        args = ['kwriteconfig6','--file',str(self.path),'--group',GROUP,'--key',key]
        args += ['--delete'] if value is None else [value]
        command(args)
        if self.get(key) != value:
            raise RuntimeError(f'Não foi possível verificar a gravação da chave {key}.')
    def values(self) -> dict[str,str | None]: return {k:self.get(k) for k in KEYS}


def xdg(key: str, fallback: Path) -> Path:
    value = Path(os.environ.get(key) or fallback).expanduser()
    if not value.is_absolute(): raise RuntimeError(f'{key} deve ser absoluto.')
    return value


def configuration() -> tuple[Path,Path,Path]:
    home = Path.home()
    return (xdg('XDG_DATA_HOME',home/'.local/share')/'kwin/decorations',
            xdg('XDG_CONFIG_HOME',home/'.config')/'kwinrc',
            xdg('XDG_STATE_HOME',home/'.local/state')/'irix-classic')


def merge_settings(before: Path, staged: Path) -> list[str]:
    """Import ONLY literal known appearance values, never execute an old QML file."""
    allowed = {'pixelScale':int,'titlePixels':int,'titleFamily':str,
               'titleItalic':bool,'titleBold':bool,'menuOpensOnPress':bool}
    values = {}
    ui = before/'contents/ui'
    old_files = [ui/'Settings.qml'] if (ui/'Settings.qml').is_file() else [
        ui/'Appearance.qml',ui/'InteractionSettings.qml']
    for file in old_files:
        if not file.is_file(): continue
        for key,kind in allowed.items():
            match = re.search(r'^\s*property\s+(?:int|bool|string)\s+'+key+r'\s*:\s*(.*?)\s*$',
                              file.read_text(encoding='utf-8'),re.M)
            if not match: continue
            raw = match[1].rstrip(';').strip()
            try:
                value = {'true':True,'false':False}[raw] if kind is bool else ast.literal_eval(raw)
            except (ValueError,SyntaxError,KeyError) as exc:
                raise RuntimeError(f'Ajuste {key} em {file} não é literal. Revise-o antes de atualizar.') from exc
            if type(value) is not kind: raise RuntimeError(f'Tipo inválido para {key} em {file}.')
            if key=='pixelScale' and value not in (1,2,3): raise RuntimeError('pixelScale deve ser 1, 2 ou 3.')
            if key=='titlePixels' and not 10<=value<=18: raise RuntimeError('titlePixels deve estar entre 10 e 18.')
            if kind is str and (not value or len(value)>120 or '\n' in value): raise RuntimeError('Nome de fonte inválido.')
            values[key] = value
    target = staged/'contents/ui/Settings.qml'
    content = target.read_text(encoding='utf-8')
    for key,value in values.items():
        encoded = json.dumps(value,ensure_ascii=False)
        content,count = re.subn(r'(property\s+(?:int|bool|string)\s+'+key+r'\s*:\s*)[^\n]+',
                               lambda m:m[1]+encoded,content)
        if count!=1: raise RuntimeError(f'Contrato de configuração inválido: {key}.')
    target.write_text(content,encoding='utf-8')
    return sorted(values)


class Manager:
    def __init__(self,base: Path,config, state: Path,source: Path=BUNDLE/'package'):
        self.base,self.cfg,self.state,self.source = base,config,state,source
    def choose(self,requested: str | None=None) -> str:
        if requested:
            if requested not in IDS: raise RuntimeError('Identificador não permitido.')
            return requested
        selected = self.cfg.get('theme')
        if selected in IDS: return selected
        found = [i for i in IDS if (self.base/i).exists()]
        if len(found)==1: return found[0]
        if len(found)>1:
            raise RuntimeError('Há mais de uma Classic instalada e nenhuma selecionada. '
                               'Selecione a que usa no KDE ou informe --destino '+ ' / '.join(found))
        return IDS[0]
    def verify(self,target_id: str | None=None) -> str:
        theme_id = self.choose(target_id)
        for path in (self.base,self.state,self.cfg.path): no_links(path)
        expected = read_json(BUNDLE/'MANIFEST.json')['package']
        if tree_hashes(self.source)!=expected:
            raise RuntimeError('O pacote difere do manifesto. Extraia o ZIP novamente.')
        dest = self.base/theme_id
        if dest.exists():
            tree_hashes(dest)
            metadata = read_json(dest/'metadata.json')
            if metadata.get('KPackageStructure')!='KWin/Decoration' or metadata.get('KPlugin',{}).get('Id')!=theme_id:
                raise RuntimeError('O destino não corresponde à decoração esperada. Nada foi sobrescrito.')
        print(f'Destino: {dest}\nNome: IRIX Classic\nRevisão: {VERSION}')
        print('Atualizará a Classic existente.' if dest.exists() else 'Será a primeira instalação neste destino.')
        return theme_id
    @contextmanager
    def locked(self):
        no_links(self.state)
        self.state.mkdir(parents=True,exist_ok=True,mode=0o700)
        lock = self.state/'manage.lock'; no_links(lock)
        with lock.open('a') as stream:
            try: fcntl.flock(stream,fcntl.LOCK_EX|fcntl.LOCK_NB)
            except BlockingIOError as exc: raise RuntimeError('Já há outra instalação/restauração em execução.') from exc
            yield
    def install(self,theme_id: str,activate: bool=False) -> Path:
        if os.geteuid()==0: raise RuntimeError('Execute como usuário normal, sem sudo.')
        if theme_id not in IDS: raise RuntimeError('Identificador não permitido.')
        with self.locked():
            if (self.state/'pending.json').exists():
                raise RuntimeError('Há uma instalação interrompida. Execute restaurar.sh --recuperar.')
            self.verify(theme_id)
            dest = self.base/theme_id
            previous = self.cfg.values()
            stamp = datetime.now(timezone.utc).strftime('%Y%m%dT%H%M%SZ')+'-'+uuid.uuid4().hex[:8]
            backup = self.state/'backups'/stamp
            no_links(backup); backup.mkdir(parents=True,mode=0o700); os.chmod(backup,0o700)
            before = tree_hashes(dest) if dest.exists() else None
            if before is not None:
                shutil.copytree(dest,backup/'before')
                if tree_hashes(backup/'before')!=before or tree_hashes(dest)!=before:
                    raise RuntimeError('O tema mudou durante o backup; instalação cancelada.')
            self.base.mkdir(parents=True,exist_ok=True)
            token=uuid.uuid4().hex
            stage=self.base/(theme_id+'.stage-'+token)
            old=self.base/(theme_id+'.old-'+token)
            prior_latest=read_json(self.state/'latest.json') if (self.state/'latest.json').exists() else None
            receipt={'format':1,'id':theme_id,'version':VERSION,'config':str(self.cfg.path),
                     'destination':str(dest),'before':before,'previous':previous,'activate':activate,
                     'stage':stage.name,'old':old.name,'status':'prepared','prior_latest':prior_latest}
            renamed=False; installed=False; touched=[]
            try:
                shutil.copytree(self.source,stage)
                meta=read_json(stage/'metadata.json'); meta['KPlugin']['Id']=theme_id
                atomic_json(stage/'metadata.json',meta)
                if before is not None:
                    receipt['preserved_settings']=merge_settings(dest,stage)
                receipt['installed']=tree_hashes(stage)
                atomic_json(backup/'receipt.json',receipt)
                atomic_json(self.state/'pending.json',{'backup':stamp})
                if dest.exists(): os.replace(dest,old); renamed=True
                os.replace(stage,dest); installed=True
                if activate:
                    if self.cfg.values()!=previous:
                        raise RuntimeError('A seleção do KDE mudou durante a instalação; cancelando ativação.')
                    for key,value in [('library',LIBRARY),('theme',theme_id)]:
                        touched.append(key); self.cfg.put(key,value)
                receipt['status']='installed'; atomic_json(backup/'receipt.json',receipt)
                atomic_json(self.state/'latest.json',{'backup':stamp})
                (self.state/'pending.json').unlink()
            except Exception:
                rollback_ok=True
                for key in reversed(touched):
                    try:
                        if self.cfg.get(key)==({'library':LIBRARY,'theme':theme_id}[key]):
                            self.cfg.put(key,previous[key])
                    except Exception as exc:
                        rollback_ok=False; print(f'ATENÇÃO: restauração de {key}: {exc}',file=sys.stderr)
                try:
                    if installed and dest.exists(): shutil.rmtree(dest)
                    if renamed and old.exists(): os.replace(old,dest)
                except OSError as exc:
                    rollback_ok=False; print(f'ATENÇÃO: restauração de pasta: {exc}',file=sys.stderr)
                receipt['status']='failed' if rollback_ok else 'prepared'
                atomic_json(backup/'receipt.json',receipt)
                if rollback_ok:
                    if prior_latest: atomic_json(self.state/'latest.json',prior_latest)
                    elif (self.state/'latest.json').exists(): (self.state/'latest.json').unlink()
                    if (self.state/'pending.json').exists(): (self.state/'pending.json').unlink()
                raise
            finally:
                if stage.exists(): shutil.rmtree(stage)
            if old.exists():
                try: shutil.rmtree(old)
                except OSError: print(f'Instalação concluída; cópia temporária preservada: {old}')
            print(f'Instalado no MESMO identificador: {theme_id}\nBackup: {backup}')
            if activate: reconfigure()
            print('Salve o trabalho e entre novamente na sessão se estiver atualizando a decoração selecionada.')
            return backup
    def restore(self,recover: bool=False) -> None:
        if os.geteuid()==0: raise RuntimeError('Execute como usuário normal, sem sudo.')
        with self.locked():
            no_links(self.cfg.path); no_links(self.base)
            index=self.state/('pending.json' if recover else 'latest.json')
            record=read_json(index); name=record['backup']
            if not re.fullmatch(r'\d{8}T\d{6}Z-[0-9a-f]{8}',name): raise RuntimeError('Nome de backup inválido.')
            backup=self.state/'backups'/name; r=read_json(backup/'receipt.json')
            theme_id=r['id']; dest=self.base/theme_id
            if theme_id not in IDS or r['format']!=1 or r['destination']!=str(dest) or r['config']!=str(self.cfg.path):
                raise RuntimeError('Backup de outro destino/usuário ou formato inválido.')
            if not re.fullmatch(re.escape(theme_id)+r'\.old-[0-9a-f]{32}',r['old']):
                raise RuntimeError('Nome de cópia transitória inválido no recibo.')
            if r['status'] not in (('prepared','installed') if recover else ('installed',)):
                raise RuntimeError(f'Backup não restaurável neste modo: {r["status"]}.')
            if r['before'] is not None and tree_hashes(backup/'before')!=r['before']:
                raise RuntimeError('O backup foi alterado. Não restaurarei conteúdo diferente do registrado.')
            current=tree_hashes(dest) if dest.exists() else None
            valid=[r['installed']]
            if recover: valid += [None,r['before']]
            if current not in valid:
                raise RuntimeError('Há edições locais após instalar. Nada foi apagado; preserve-as antes de restaurar.')
            # Prepare the replacement before taking the active directory out of place.
            token=uuid.uuid4().hex
            staged=self.base/(theme_id+'.restore-'+token)
            parked=self.base/(theme_id+'.park-'+token)
            if r['before'] is not None: shutil.copytree(backup/'before',staged)
            selected=self.cfg.values()=={'library':LIBRARY,'theme':theme_id}
            current_config=self.cfg.values(); changed=[]; moved=False; replacement=False
            try:
                if dest.exists(): os.replace(dest,parked); moved=True
                if staged.exists(): os.replace(staged,dest); replacement=True
                if selected:
                    for key in KEYS:
                        changed.append(key); self.cfg.put(key,r['previous'][key])
                r['status']='restored'; atomic_json(backup/'receipt.json',r)
                if recover:
                    index.unlink()
                    latest=self.state/'latest.json'
                    if latest.exists() and read_json(latest).get('backup')==name:
                        if r.get('prior_latest'): atomic_json(latest,r['prior_latest'])
                        else: latest.unlink()
                elif r.get('prior_latest'):
                    atomic_json(index,r['prior_latest'])
                else:
                    index.unlink()
            except Exception:
                for key in changed:
                    try: self.cfg.put(key,current_config[key])
                    except Exception as exc: print(f'ATENÇÃO: {exc}',file=sys.stderr)
                if replacement and dest.exists(): shutil.rmtree(dest)
                if moved and parked.exists(): os.replace(parked,dest)
                raise
            finally:
                if staged.exists(): shutil.rmtree(staged)
            if parked.exists(): shutil.rmtree(parked)
            # Remove an interrupted old tree only when it is the exact saved copy.
            old=self.base/r['old']
            if old.exists() and tree_hashes(old)==r['before']:
                shutil.rmtree(old)
            if re.fullmatch(re.escape(theme_id)+r'\.stage-[0-9a-f]{32}',r['stage']):
                stale=self.base/r['stage']
                if stale.exists() and tree_hashes(stale)==r['installed']: shutil.rmtree(stale)
            if selected: reconfigure()
            print('Estado anterior restaurado. Outras decorações e preferências foram preservadas.')
            print('Salve o trabalho e entre novamente na sessão para descartar o QML em cache.')


def reconfigure() -> None:
    tool=shutil.which('qdbus6')
    if tool:
        try: command([tool,'org.kde.KWin','/KWin','reconfigure'])
        except (RuntimeError,subprocess.SubprocessError): print('D-Bus não respondeu; entre novamente na sessão.')


def check_environment() -> None:
    for tool in ('kreadconfig6','kwriteconfig6'):
        if not shutil.which(tool): raise RuntimeError(f'Ferramenta necessária ausente: {tool}.')
    candidates=list(Path('/usr/lib').glob('*/qt6/qml/org/kde/kwin/decoration/qmldir'))
    candidates += [Path(p) for p in ('/usr/lib/qt6/qml/org/kde/kwin/decoration/qmldir',
                                    '/usr/lib64/qt6/qml/org/kde/kwin/decoration/qmldir')]
    if not any(p.is_file() for p in candidates):
        raise RuntimeError('Módulo Aurorae/Qt 6 não localizado. Não instalei nem alterei dependências.')


def main() -> int:
    p=argparse.ArgumentParser(description=__doc__)
    g=p.add_mutually_exclusive_group()
    g.add_argument('--verificar',action='store_true')
    g.add_argument('--ativar',action='store_true')
    g.add_argument('--restaurar',action='store_true')
    g.add_argument('--recuperar',action='store_true')
    p.add_argument('--destino',choices=IDS,help='somente para resolver múltiplas Classic não selecionadas')
    a=p.parse_args()
    try:
        if os.geteuid()==0: raise RuntimeError('Execute como usuário normal, sem sudo.')
        base,cfg,state=configuration(); m=Manager(base,KDEConfig(cfg),state)
        if a.restaurar or a.recuperar:
            m.restore(a.recuperar)
        else:
            check_environment(); target=m.verify(a.destino)
            if a.verificar:
                print('Somente leitura. Isto verifica arquivos/ambiente, não renderiza Qt Quick/KWin.')
            else: m.install(target,a.ativar)
        return 0
    except (OSError,ValueError,KeyError,RuntimeError,subprocess.SubprocessError) as exc:
        print(f'ERRO: {exc}',file=sys.stderr); return 1


if __name__=='__main__': raise SystemExit(main())
