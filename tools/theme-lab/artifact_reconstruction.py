# SPDX-License-Identifier: GPL-3.0-or-later
"""Private file reconstruction command; does not install themes or apply palettes."""
import json
import os
import stat
from pathlib import Path
import uuid

from artifact_delta import digest, prepare_files, write_files
from private_publication import publish_directory


def inspect_files(file_delta, read_file):
    if file_delta is None:
        raise ValueError('--file-delta obrigatório.')
    manifest = json.loads(read_file(file_delta))
    if (not isinstance(manifest, dict) or type(manifest.get('schema')) is not int or
            manifest['schema'] != 1 or manifest.get('kind') != 'theme_lab_artifact_delta' or
            manifest.get('mode') not in ('snapshot', 'delta') or
            not isinstance(manifest.get('base_files'), dict)):
        raise ValueError('Contrato de arquivos inválido; nenhum arquivo reconstruído.')
    return {'status': 'ok', 'requires_base': bool(manifest['base_files']),
            'mode': manifest['mode'], 'installed': False, 'host_changed': False,
            'reason': 'Inspeção de navegação; hashes e dependências serão validados na reconstrução.'}


def reconstruct(file_delta, base, output, read_file, write_json):
    if file_delta is None or output is None:
        raise ValueError('--file-delta e --output obrigatórios para reconstruir arquivos.')
    source = Path(file_delta)
    # Do not resolve away symlinks before the artifact reader checks them.
    if any(path.is_symlink() for path in (source, *source.parents)):
        raise ValueError('Recibo de arquivos não pode atravessar links.')
    payload = read_file(source)
    manifest = json.loads(payload)
    output = Path(output)
    if not output.is_absolute():
        raise ValueError('Saída de reconstrução precisa ser absoluta.')
    if output.exists():
        info = output.stat()
        if not stat.S_ISDIR(info.st_mode) or info.st_uid != os.getuid() or info.st_mode & 0o077:
            raise ValueError('Saída existente precisa pertencer ao usuário e ter modo 0700.')
    for origin in (source.parent, base):
        if origin is not None and output.resolve().is_relative_to(Path(origin).resolve()):
            raise ValueError('Saída precisa ficar fora da base e do pacote.')
    folder = output / 'reconstructed' / ('revision-' + uuid.uuid4().hex)
    theme = folder / 'theme'
    files, counts = prepare_files(manifest, source.parent, base, theme, read_file)
    result = {'status': 'ok', 'reconstruction_dir': str(folder), 'theme_directory': str(theme),
              'file_delta_sha256': digest(payload), 'mode': manifest['mode'],
              'file_hashes': manifest['files'], **counts,
              'installed': False, 'host_changed': False, 'palette_revalidated': False,
              'reason': 'Arquivos reconstruídos em revisão privada. Não instalado; papéis atuais precisam ser regenerados/conferidos antes de instalar.'}
    result['review_text'] = ('Reconstrução de arquivos\n\nTema privado: ' + str(theme) +
        '\nRecibo: ' + str(folder / 'RECONSTRUCTION.json') +
        '\nOrigem FILES.json: ' + str(source) + '\nSHA-256: ' + digest(payload) +
        '\nModo: ' + manifest['mode'] + '\nArquivos: ' + str(counts['files']) +
        '\nDo payload: ' + str(counts['payload_files']) + '\nReutilizados da base: ' + str(counts['reused_files']) +
        '\n\nNenhum tema foi instalado. Projeto e cena permanecem intactos.\n' +
        'Os papéis de cores atuais ainda não foram revalidados; regenerar/conferir antes de instalar.\n')
    def build(stage):
        write_files(stage / 'theme', files)
        write_json(stage / 'RECONSTRUCTION.json', result)
        return result
    return publish_directory(folder, build)
