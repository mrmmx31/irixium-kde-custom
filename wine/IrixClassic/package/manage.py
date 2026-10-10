#!/usr/bin/env python3
# SPDX-FileCopyrightText: 2026 mrmmx31
# SPDX-License-Identifier: GPL-3.0-or-later
"""Apply/restore Classic in one explicitly selected, initialized Wine prefix."""
import argparse
import base64
import contextlib
import fcntl
import hashlib
import json
import os
from pathlib import Path
import re
import subprocess
import tempfile
import uuid

PACKAGE = Path(__file__).resolve().parent
SCOPES = ('HKEY_CURRENT_USER\\Control Panel\\Colors',
          'HKEY_CURRENT_USER\\Control Panel\\Desktop',
          'HKEY_CURRENT_USER\\Software\\Microsoft\\Windows\\CurrentVersion\\ThemeManager')
TARGET = Path('drive_c/windows/resources/themes/IrixClassic/IrixClassic.msstyles')


def safe(path):
    if not path.is_absolute() or '..' in path.parts:
        raise RuntimeError('Caminho absoluto sem .. necessário.')
    for p in (path, *path.parents):
        if p.is_symlink(): raise RuntimeError('Link simbólico recusado: '+str(p))
        if p.exists() and p not in (Path('/'), Path('/home'), Path('/tmp')) and p.stat().st_uid != os.getuid():
            raise RuntimeError('O caminho não pertence ao usuário: '+str(p))
    if any(p == path or p in path.parents for p in map(Path, ('/usr','/etc','/opt','/var'))):
        raise RuntimeError('Destino compartilhado recusado.')


def atomic(path, data, mode=0o600):
    safe(path); path.parent.mkdir(parents=True, exist_ok=True)
    fd, tmp = tempfile.mkstemp(prefix='.irix-write-', dir=path.parent)
    try:
        with os.fdopen(fd, 'wb') as stream:
            stream.write(data); stream.flush(); os.fsync(stream.fileno())
        os.chmod(tmp, mode); os.replace(tmp, path)
        fd = os.open(path.parent, os.O_RDONLY | os.O_DIRECTORY)
        try: os.fsync(fd)
        finally: os.close(fd)
    finally:
        if os.path.exists(tmp): os.unlink(tmp)


def save(path, doc): atomic(path, (json.dumps(doc, indent=2)+'\n').encode())
def digest(data): return hashlib.sha256(data).hexdigest()


def parse_reg(data):
    """Keep reg.exe's native value syntax; normalize hex continuation lines."""
    text = data.decode('utf-16') if data.startswith(b'\xff\xfe') else data.decode('utf-8-sig')
    text = re.sub(r'\\\r?\n\s*', '', text)
    result = {}; key = None
    for raw in text.splitlines():
        line = raw.strip()
        if not line or line.startswith(';') or line.startswith('Windows Registry'): continue
        if line.startswith('[') and line.endswith(']'):
            key = line[1:-1].lower()
            if not any(key == s.lower() or key.startswith(s.lower()+'\\') for s in SCOPES):
                raise RuntimeError('Chave fora da aparência recusada.')
        elif key and (line.startswith('"') or line.startswith('@=')):
            match = re.fullmatch(r'("(?:[^"\\]|\\.)*"|@)=(.*)', line)
            if not match: raise RuntimeError('Valor de registro inválido.')
            name, value = match.groups()
            if value.startswith(('hex', 'dword')): value = re.sub(r'\s+', '', value).lower()
            result[key+'\n'+name.lower()] = [key, name, value]
        else: raise RuntimeError('Formato de registro inesperado.')
    return result


def reg_patch(current, desired):
    groups = {}
    for ident in sorted(current.keys() | desired.keys()):
        if current.get(ident) == desired.get(ident): continue
        key, name, _ = desired.get(ident, current.get(ident))
        if not any(key == s.lower() or key.startswith(s.lower()+'\\') for s in SCOPES):
            raise RuntimeError('Chave fora da aparência recusada.')
        groups.setdefault(key, []).append(name+'='+(desired[ident][2] if ident in desired else '-'))
    text = 'Windows Registry Editor Version 5.00\r\n\r\n'
    for key, values in groups.items(): text += '['+key+']\r\n'+'\r\n'.join(values)+'\r\n\r\n'
    return b'\xff\xfe'+text.encode('utf-16le')


def merged_restore(current, before, after):
    desired = dict(current)
    for ident in before.keys() | after.keys():
        if before.get(ident) == after.get(ident): continue
        if current.get(ident) != after.get(ident):
            raise RuntimeError('A aparência foi alterada depois da instalação: '+ident.replace('\n',' / '))
        if ident in before: desired[ident] = before[ident]
        else: desired.pop(ident, None)
    return desired


class Wine:
    def __init__(self, prefix):
        self.prefix = Path(prefix).expanduser().absolute()
        if os.getuid() == 0: raise RuntimeError('Execute como o dono do prefixo, sem sudo.')
        safe(self.prefix); safe(self.prefix/TARGET)
        for file in ('user.reg','system.reg','drive_c'):
            safe(self.prefix/file)
            if not (self.prefix/file).exists(): raise RuntimeError('Prefixo Wine já inicializado necessário: '+str(self.prefix))
        if '#arch=win64' not in (self.prefix/'system.reg').read_text(errors='replace')[:1024]:
            raise RuntimeError('Este assistente requer prefixo win64; use winecfg para instalar o msstyles em win32.')
        self.env = dict(os.environ, WINEPREFIX=str(self.prefix), WINEDEBUG='-all')
        self.env.pop('WINEARCH', None)
        self.state = self.prefix/'.irixclassic-theme'; safe(self.state)

    def run(self, args):
        # Wine can leave service processes holding inherited pipe handles after
        # the requested executable exits. Regular temporary files avoid waiting
        # for unrelated services to close stdout/stderr.
        with tempfile.TemporaryFile() as stdout, tempfile.TemporaryFile() as stderr:
            result = subprocess.run(args, env=self.env, stdout=stdout, stderr=stderr, timeout=90)
            stdout.seek(0); stderr.seek(0)
            if result.returncode: raise RuntimeError('Falha em '+args[0]+': '+stderr.read().decode(errors='replace')[-1000:])
            return stdout.read()

    def windows(self, path): return self.run(['winepath','-w',str(path)]).decode().strip()

    def theme(self, *args):
        return json.loads(self.run(['wine',str(PACKAGE/'irix-theme.exe'),*args]))

    def registry(self):
        result = {}
        with tempfile.TemporaryDirectory(prefix='irix-reg-') as folder:
            for i, scope in enumerate(SCOPES):
                path = Path(folder)/(str(i)+'.reg')
                # All three keys exist in supported initialized Wine prefixes.
                self.run(['wine','reg.exe','export',scope,self.windows(path),'/y'])
                result.update(parse_reg(path.read_bytes()))
        return result

    def restore_registry(self, desired):
        current = self.registry()
        if current == desired: return
        with tempfile.TemporaryDirectory(prefix='irix-reg-') as folder:
            path = Path(folder)/'restore.reg'; path.write_bytes(reg_patch(current, desired)); os.chmod(path,0o600)
            self.run(['wine','reg.exe','import',self.windows(path)])
        if self.registry() != desired: raise RuntimeError('Falha na conferência da restauração de aparência.')

    def set_theme(self, theme):
        if theme['active']: return self.theme('apply',theme['path'],theme['color'],theme['size'])
        return self.theme('clear')

    @contextlib.contextmanager
    def lock(self):
        self.state.mkdir(mode=0o700, exist_ok=True)
        path = self.state/'lock'; safe(path)
        with path.open('a') as stream:
            fcntl.flock(stream, fcntl.LOCK_EX | fcntl.LOCK_NB)
            yield


def install(wine):
    target = wine.prefix/TARGET
    theme = wine.theme('inspect'); before = wine.registry()
    data = (PACKAGE/'IrixClassic.msstyles').read_bytes()
    if theme['active'] and theme['path'].lower() == wine.windows(target).lower() and target.is_file() and target.read_bytes() == data:
        return {'status':'already_applied', 'prefix':str(wine.prefix), 'theme':theme}
    ident = uuid.uuid4().hex; backup = wine.state/'backups'/ident
    backup.mkdir(parents=True, mode=0o700)
    old = target.read_bytes() if target.exists() else None
    receipt = {'format':1,'prefix':str(wine.prefix),'status':'prepared','theme_before':theme,
               'registry_before':before,'file_before':base64.b64encode(old).decode() if old is not None else None,
               'file_mode':(target.stat().st_mode & 0o777) if old is not None else 0o644,
               'file_after_sha256':digest(data)}
    save(backup/'receipt.json', receipt)
    try:
        atomic(target,data,0o644)
        applied = wine.theme('apply',wine.windows(target),'Classic','NormalSize')
        if not applied['active'] or applied['color'] != 'Classic' or applied['path'].lower() != wine.windows(target).lower():
            raise RuntimeError('O Wine não confirmou o tema Classic.')
        after = wine.registry()
        # Wine's ApplyTheme can normalize point-height LOGFONT values to pixel
        # heights even when the style declares no fonts. Keep the exact user's
        # font settings; changing the theme must not rewrite those preferences.
        desired = dict(after)
        for key in before.keys() | after.keys():
            if key.startswith(SCOPES[1].lower()+'\\') and 'font' in key.split('\n')[-1]:
                if key in before: desired[key] = before[key]
                else: desired.pop(key,None)
        wine.restore_registry(desired)
        receipt.update(status='applied',theme_after=applied,registry_after=wine.registry())
        save(backup/'receipt.json',receipt); atomic(wine.state/'latest',ident.encode())
    except BaseException:
        errors = []
        for recover in (lambda: atomic(target,old,receipt['file_mode']) if old is not None else target.unlink(missing_ok=True),
                        lambda: wine.set_theme(theme), lambda: wine.restore_registry(before)):
            try: recover()
            except BaseException as error: errors.append(str(error))
        receipt.update(status='recovery_needed' if errors else 'rolled_back', recovery_errors=errors)
        try: save(backup/'receipt.json',receipt)
        except OSError: pass
        if errors: raise RuntimeError('Restauração incompleta; backup: '+str(backup)+'; '+'; '.join(errors))
        raise
    return {'status':'applied','prefix':str(wine.prefix),'backup':str(backup),'theme':applied}


def restore(wine):
    ident = (wine.state/'latest').read_text().strip()
    if not re.fullmatch('[0-9a-f]{32}',ident): raise RuntimeError('Identificador de backup inválido.')
    backup = wine.state/'backups'/ident; safe(backup/'receipt.json')
    receipt = json.loads((backup/'receipt.json').read_text())
    if receipt.get('format') != 1 or receipt['prefix'] != str(wine.prefix): raise RuntimeError('Backup de outro prefixo.')
    if receipt['status'] == 'restored': return {'status':'already_restored','backup':str(backup)}
    if receipt['status'] != 'applied': raise RuntimeError('Backup não aplicado; consulte o receipt.json.')
    target = wine.prefix/TARGET
    if not target.is_file() or digest(target.read_bytes()) != receipt['file_after_sha256']:
        raise RuntimeError('Arquivo do tema modificado depois da instalação.')
    current_theme = wine.theme('inspect')
    for key in ('active','path','color','size'):
        if current_theme[key] != receipt['theme_after'][key]: raise RuntimeError('Outro tema foi selecionado depois da instalação.')
    current = wine.registry()
    desired = merged_restore(current,receipt['registry_before'],receipt['registry_after'])
    # The old theme may reset metrics. Reapply the merged snapshot afterwards,
    # retaining later settings that were never changed by our installation.
    old = base64.b64decode(receipt['file_before'],validate=True) if receipt['file_before'] is not None else None
    installed = target.read_bytes()
    try:
        if old is not None: atomic(target,old,receipt['file_mode'])
        wine.set_theme(receipt['theme_before']); wine.restore_registry(desired)
        if old is None: target.unlink()
        receipt['status'] = 'restored'; save(backup/'receipt.json',receipt)
    except BaseException:
        errors=[]
        for recover in (lambda: atomic(target,installed,0o644),
                        lambda: wine.set_theme(current_theme), lambda: wine.restore_registry(current)):
            try: recover()
            except BaseException as error: errors.append(str(error))
        receipt.update(status='recovery_needed' if errors else 'applied',recovery_errors=errors)
        try: save(backup/'receipt.json',receipt)
        except OSError: pass
        if errors: raise RuntimeError('Restauração incompleta; backup: '+str(backup)+'; '+'; '.join(errors))
        raise
    return {'status':'restored','prefix':str(wine.prefix),'backup':str(backup),'theme':wine.theme('inspect')}


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--prefix',required=True,help='Prefixo existente, pertencente ao usuário.')
    group = parser.add_mutually_exclusive_group()
    group.add_argument('--restaurar',action='store_true'); group.add_argument('--verificar',action='store_true')
    group.add_argument('--exibir',action='store_true',help='Abrir a galeria de controles nativos, sem aplicar tema.')
    args = parser.parse_args()
    try:
        wine = Wine(args.prefix)
        if args.verificar: result = {'prefix':str(wine.prefix),'theme':wine.theme('inspect')}
        elif args.exibir:
            subprocess.run(['wine',str(PACKAGE/'irix-preview.exe')],env=wine.env,check=True); return
        else:
            with wine.lock(): result = restore(wine) if args.restaurar else install(wine)
        print(json.dumps(result,indent=2))
    except (RuntimeError,OSError,ValueError,subprocess.SubprocessError) as error:
        parser.exit(1,str(error)+'\n')


if __name__ == '__main__': main()
