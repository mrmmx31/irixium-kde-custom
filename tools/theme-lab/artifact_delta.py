# SPDX-License-Identifier: GPL-3.0-or-later
"""Content-addressed private file packages, independent of toolkit painting."""
import hashlib
import json
import re
from pathlib import Path, PurePosixPath
from private_publication import private_parents, publish_directory


def digest(data):
    return hashlib.sha256(data).hexdigest()


def relative_path(name):
    if not isinstance(name, str) or not name or '\\' in name:
        raise ValueError('Nome de arquivo inválido no pacote.')
    path = PurePosixPath(name)
    if path.is_absolute() or any(part in ('', '.', '..') for part in name.split('/')):
        raise ValueError('Caminho de arquivo precisa ser relativo e sem . ou ..')
    return path


def read_artifact(root, name, read_file):
    path = Path(root).joinpath(*relative_path(name).parts)
    if any(parent.is_symlink() for parent in (path, *path.parents)):
        raise ValueError('Artefato não pode atravessar links.')
    return read_file(path)


def checked_inventory(root, hashes, read_file):
    if not isinstance(hashes, dict) or len(hashes) > 20000:
        raise ValueError('Inventário de artefatos inválido ou excessivo.')
    files = {}
    for name, expected in hashes.items():
        data = read_artifact(root, name, read_file)
        if digest(data) != expected:
            raise ValueError('Artefato não corresponde ao recibo: ' + name)
        files[name] = data
    return files


def receipt_inventory(folder, receipt, read_file):
    """Only engine inputs certified by the generated toolkit receipt."""
    folder = Path(folder)
    family = receipt.get('family')
    if family == 'gtk3' and receipt.get('status') == 'generated':
        root = Path(receipt['theme_path'])
        if not root.is_absolute() or '..' in root.parts or not root.is_relative_to(folder):
            raise ValueError('Tema fora da geração privada.')
        manifest = json.loads(read_artifact(root, 'MANIFEST.json', read_file))
        files = checked_inventory(root, manifest['files'], read_file)
        files.pop('ORIGEM.json', None)
        return root, files
    if family == 'gtk2' and receipt.get('status') == 'partially_generated':
        rc = Path(receipt['rc'])
        if not rc.is_absolute() or '..' in rc.parts or not rc.is_relative_to(folder):
            raise ValueError('RC fora da geração privada.')
        hashes = dict(receipt['asset_sha256'])
        hashes[rc.name] = receipt['rc_sha256']
        return rc.parent, checked_inventory(rc.parent, hashes, read_file)
    return None, None


def new_destination(destination):
    destination = Path(destination)
    if '..' in destination.parts or any(parent.is_symlink()
            for parent in (destination, *destination.parents)):
        raise ValueError('Destino não pode atravessar links ou ..')
    if destination.exists():
        raise ValueError('Resultado já existe; não substituir.')
    return destination


def package_files(before, after, destination):
    """Store changed bytes only; unchanged files require an exact base."""
    destination = new_destination(destination)
    for name in after:
        relative_path(name)
    for name in before or {}:
        relative_path(name)
    base = before or {}
    changed = {name: data for name, data in after.items()
               if name not in base or base[name] != data}
    reused = {name: digest(data) for name, data in after.items()
              if name in base and base[name] == data}
    manifest = {'schema': 1, 'kind': 'theme_lab_artifact_delta',
                'mode': 'snapshot' if before is None else 'delta',
                'files': {name: digest(data) for name, data in sorted(after.items())},
                'base_files': {name: digest(data) for name, data in sorted(base.items())},
                'payload': {name: digest(data) for name, data in sorted(changed.items())},
                'reuse': reused, 'removed': sorted(set(base) - set(after)),
                'installed': False}
    private_parents(destination.parent)
    destination.mkdir(mode=0o700)
    for name, data in changed.items():
        path = destination / 'payload' / name
        private_parents(path.parent)
        path.write_bytes(data)
    (destination / 'FILES.json').write_text(json.dumps(manifest, indent=2,
                                           ensure_ascii=False) + '\n', encoding='utf-8')
    return manifest


def prepare_files(manifest, package, base, destination, read_file):
    """Validate every input before creating an independent result directory."""
    if (not isinstance(manifest, dict) or type(manifest.get('schema')) is not int or
            manifest['schema'] != 1 or manifest.get('kind') != 'theme_lab_artifact_delta'):
        raise ValueError('Contrato de pacote inválido.')
    if manifest.get('mode') not in ('snapshot', 'delta'):
        raise ValueError('Modo do pacote inválido.')
    for key in ('files', 'payload', 'reuse', 'base_files'):
        inventory = manifest.get(key)
        if not isinstance(inventory, dict) or len(inventory) > 20000:
            raise ValueError('Inventário do pacote inválido: ' + key)
        for name, value in inventory.items():
            relative_path(name)
            if not isinstance(value, str) or not re.fullmatch(r'[a-f0-9]{64}', value):
                raise ValueError('Hash inválido no inventário: ' + key)
    removed = manifest.get('removed')
    if (not isinstance(removed, list) or any(not isinstance(name, str) for name in removed) or
            len(removed) != len(set(removed)) or
            set(removed) != set(manifest['base_files']) - set(manifest['files'])):
        raise ValueError('Lista de remoções inconsistente.')
    paths = {relative_path(name) for name in manifest['files']}
    if any(parent in paths for path in paths for parent in path.parents):
        raise ValueError('Arquivo e pasta ocupam o mesmo caminho.')
    destination = new_destination(destination)
    absolute_destination = destination.absolute()
    for source in (package, base):
        if source is not None and absolute_destination.resolve().is_relative_to(Path(source).resolve()):
            raise ValueError('Destino precisa ficar fora da base e do pacote.')
    files = manifest['files']
    payload, reuse = manifest['payload'], manifest['reuse']
    if not all(isinstance(value, dict) for value in (files, payload, reuse, manifest['base_files'])):
        raise ValueError('Inventários do pacote precisam ser objetos.')
    if manifest['base_files'] and base is None:
        raise ValueError('Este delta exige a base original.')
    if set(payload) & set(reuse) or set(payload) | set(reuse) != set(files):
        raise ValueError('Inventário incompleto ou sobreposto.')
    if manifest['mode'] == 'snapshot' and (manifest['base_files'] or manifest['reuse']):
        raise ValueError('Snapshot não pode depender de uma base.')
    if any(files[name] != value for name, value in {**payload, **reuse}.items()):
        raise ValueError('Hashes de dependências inconsistentes.')
    originals = checked_inventory(base, manifest['base_files'], read_file) if manifest['base_files'] else {}
    changed = checked_inventory(Path(package) / 'payload', payload, read_file)
    if any(name not in originals or digest(originals[name]) != value
           for name, value in reuse.items()):
        raise ValueError('Dependência da base ausente ou divergente.')
    result = {name: changed[name] if name in changed else originals[name] for name in files}
    counts = {'files': len(result), 'payload_files': len(changed), 'reused_files': len(reuse)}
    return result, counts


def write_files(directory, files):
    directory = Path(directory)
    private_parents(directory.parent)
    directory.mkdir(mode=0o700, exist_ok=True)
    for name, data in files.items():
        path = directory / name
        private_parents(path.parent)
        path.write_bytes(data)


def reconstruct_files(manifest, package, base, destination, read_file):
    files, counts = prepare_files(manifest, package, base, destination, read_file)
    publish_directory(destination, lambda stage: write_files(stage, files))
    return counts
