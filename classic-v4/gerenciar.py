#!/usr/bin/env python3
"""Instala uma decoração de usuário, sem privilégios e sem substituir componentes KDE."""
from __future__ import annotations
import argparse
import datetime as dt
import hashlib
import json
import os
from pathlib import Path
import shutil
import subprocess
import sys
import uuid

ID = 'irixium_irix_classic_v4'
GROUP = 'org.kde.kdecoration2'
LIBRARY = 'org.kde.kwin.aurorae'
BUNDLE = Path(__file__).resolve().parent
SOURCE = BUNDLE / 'kwin' / 'decorations' / ID


def xdg(name: str, fallback: Path) -> Path:
    result = Path(os.environ.get(name) or fallback).expanduser()
    if not result.is_absolute():
        raise RuntimeError(f'{name} precisa ser um caminho absoluto.')
    return result


def locations() -> tuple[Path, Path, Path]:
    home = Path.home()
    return (xdg('XDG_DATA_HOME', home/'.local/share')/'kwin/decorations'/ID,
            xdg('XDG_CONFIG_HOME', home/'.config')/'kwinrc',
            xdg('XDG_STATE_HOME', home/'.local/state')/'irixium-classic-v4')


def run(args: list[str]) -> str:
    proc = subprocess.run(args, text=True, capture_output=True, timeout=20)
    if proc.returncode:
        raise RuntimeError(f'{Path(args[0]).name}: {proc.stderr.strip() or proc.stdout.strip()}')
    return proc.stdout.rstrip('\n')


def get_key(config: Path, key: str) -> str | None:
    marker = '__IRIX_MISSING_' + uuid.uuid4().hex
    value = run(['kreadconfig6', '--file', str(config), '--group', GROUP,
                 '--key', key, '--default', marker])
    return None if value == marker else value


def put_key(config: Path, key: str, value: str | None) -> None:
    args = ['kwriteconfig6', '--file', str(config), '--group', GROUP, '--key', key]
    args += ['--delete'] if value is None else [value]
    run(args)
    if get_key(config, key) != value:
        raise RuntimeError(f'A chave {key} não foi gravada. Verifica permissões/restrições do KDE.')


def hashes(directory: Path) -> dict[str, str]:
    if directory.is_symlink():
        raise RuntimeError(f'Não vou substituir um link simbólico: {directory}')
    result = {}
    for f in sorted(directory.rglob('*')):
        if f.is_symlink():
            raise RuntimeError(f'Link simbólico inesperado: {f}')
        if f.is_file():
            result[f.relative_to(directory).as_posix()] = hashlib.sha256(f.read_bytes()).hexdigest()
    return result


def write_json(path: Path, value: dict) -> None:
    temp = path.with_suffix(path.suffix + '.tmp')
    temp.write_text(json.dumps(value, ensure_ascii=False, indent=2) + '\n', encoding='utf-8')
    temp.replace(path)


def verify() -> None:
    wanted = json.loads((BUNDLE/'MANIFESTO.json').read_text(encoding='utf-8'))
    if hashes(SOURCE) != wanted['theme_files']:
        raise RuntimeError('Os arquivos do pacote diferem do manifesto. Extrai o ZIP novamente.')
    for tool in ['kreadconfig6', 'kwriteconfig6']:
        if not shutil.which(tool):
            raise RuntimeError(f'Não encontrei {tool}; este pacote exige KDE Plasma 6.')
    candidates = [Path('/usr/lib/qt6/qml/org/kde/kwin/decoration/qmldir'),
                  Path('/usr/lib64/qt6/qml/org/kde/kwin/decoration/qmldir')]
    candidates += list(Path('/usr/lib').glob('*/qt6/qml/org/kde/kwin/decoration/qmldir'))
    if not any(p.is_file() for p in candidates):
        raise RuntimeError('Não encontrei o módulo Aurorae/Qt 6 nos diretórios usuais. Não alterei nada.')
    dest, config, state = locations()
    if dest.exists() and not dest.is_dir():
        raise RuntimeError(f'O destino não é uma pasta: {dest}')
    if dest.exists(): hashes(dest)
    print('Arquivos íntegros; ferramentas KDE 6 e módulo Aurorae encontrados.')
    print(f'Destino: {dest}\nTema atual: {get_key(config, "theme")}')
    print('A verificação não executa/renderiza o QML e não altera a sessão.')


def reconfigure() -> None:
    tool = shutil.which('qdbus6')
    if tool:
        try: run([tool, 'org.kde.KWin', '/KWin', 'reconfigure'])
        except (RuntimeError, subprocess.TimeoutExpired):
            print('O recarregamento não respondeu; encerra e reabre a sessão após salvar o trabalho.')


def install(activate: bool = False) -> Path:
    dest, config, state = locations()
    if os.geteuid() == 0:
        raise RuntimeError('Executa como teu usuário normal, sem sudo.')
    previous = {key: get_key(config, key) for key in ('library', 'theme')}
    stamp = dt.datetime.now(dt.timezone.utc).strftime('%Y%m%dT%H%M%SZ')+'-'+uuid.uuid4().hex[:8]
    backup = state/'backups'/stamp
    backup.mkdir(parents=True, mode=0o700)
    os.chmod(backup, 0o700)
    existed = dest.exists()
    if existed:
        hashes(dest)  # refuse symlinks before touching the existing tree
        shutil.copytree(dest, backup/'theme-before')
    receipt = {'id': ID, 'version': 4, 'destination': str(dest), 'config': str(config),
               'previous': previous, 'had_theme': existed, 'status': 'prepared',
               'installed_hashes': hashes(SOURCE)}
    write_json(backup/'receipt.json', receipt)
    dest.parent.mkdir(parents=True, exist_ok=True)
    staged = dest.parent/(ID+'.staging-'+uuid.uuid4().hex)
    changed_keys: list[str] = []
    replaced = False
    try:
        shutil.copytree(SOURCE, staged)
        replaced = True
        if dest.exists(): shutil.rmtree(dest)
        staged.replace(dest)
        if activate:
            for key, value in [('library', LIBRARY), ('theme', ID)]:
                changed_keys.append(key)
                put_key(config, key, value)
        receipt['status'] = 'installed'
        write_json(backup/'receipt.json', receipt)
        write_json(state/'latest.json', {'backup': stamp})
    except Exception:
        for key in reversed(changed_keys):
            try: put_key(config, key, previous[key])
            except Exception as exc: print(f'ATENÇÃO: restauração de {key}: {exc}', file=sys.stderr)
        if replaced:
            if dest.exists(): shutil.rmtree(dest)
            if existed: shutil.copytree(backup/'theme-before', dest)
        receipt['status'] = 'failed'
        write_json(backup/'receipt.json', receipt)
        raise
    finally:
        if staged.exists(): shutil.rmtree(staged)
    print(f'Instalado. Backup: {backup}')
    if activate:
        reconfigure()
        print('Tema selecionado. Se necessário, salva o trabalho e entra novamente na sessão.')
    else:
        print('O tema atual NÃO foi trocado. Abre Decorações de janelas e seleciona')
        print('  Irixium — IRIX Classic (v4)')
        print('Confere a miniatura antes de clicar em Aplicar.')
    return backup


def restore() -> None:
    if os.geteuid() == 0:
        raise RuntimeError('Executa como teu usuário normal, sem sudo.')
    dest, config, state = locations()
    latest = json.loads((state/'latest.json').read_text(encoding='utf-8'))
    name = latest['backup']
    if Path(name).name != name or name in ('.', '..'):
        raise RuntimeError('Referência de backup inválida.')
    backup = state/'backups'/name
    receipt = json.loads((backup/'receipt.json').read_text(encoding='utf-8'))
    if receipt['destination'] != str(dest) or receipt['config'] != str(config) or receipt['id'] != ID:
        raise RuntimeError('O backup pertence a outro destino/configuração.')
    if receipt['status'] != 'installed':
        raise RuntimeError(f'Backup não está em estado instalado: {receipt["status"]}.')
    if dest.exists() and hashes(dest) != receipt['installed_hashes']:
        raise RuntimeError('A decoração foi editada após instalar. Preservarei as edições; '
                           'seleciona o tema anterior na interface. Nenhum arquivo foi apagado.')
    # Do not overwrite a different theme the user selected since installation.
    selected = get_key(config, 'theme') == ID
    if selected:
        current_library = get_key(config, 'library')
        put_key(config, 'theme', receipt['previous']['theme'])
        if current_library == LIBRARY:
            put_key(config, 'library', receipt['previous']['library'])
    if dest.exists(): shutil.rmtree(dest)
    if receipt['had_theme']: shutil.copytree(backup/'theme-before', dest)
    receipt['status'] = 'restored'
    write_json(backup/'receipt.json', receipt)
    if selected: reconfigure()
    print('Restauração concluída. Os componentes das versões v1/v2/v3 não foram alterados.')
    print('Se necessário, salva o trabalho e entra novamente na sessão.')


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    g = parser.add_mutually_exclusive_group()
    g.add_argument('--verificar', action='store_true', help='somente leitura; não instala')
    g.add_argument('--ativar', action='store_true', help='instala e seleciona o novo tema')
    g.add_argument('--restaurar', action='store_true', help='restaura a última instalação')
    args = parser.parse_args()
    try:
        if args.restaurar: restore()
        else:
            verify()
            if not args.verificar: install(args.ativar)
        return 0
    except (OSError, ValueError, KeyError, RuntimeError, subprocess.SubprocessError) as exc:
        print(f'ERRO: {exc}', file=sys.stderr)
        return 1

if __name__ == '__main__':
    raise SystemExit(main())
