#!/usr/bin/env python3
# SPDX-FileCopyrightText: 2026 mrmmx31
# SPDX-License-Identifier: GPL-3.0-or-later
"""IRIX sounds importer. No network, Dolphin hook, daemon, global config or
system writes.

The public package contains no SGI audio and never downloads it. Source bytes
are checked against pinned Git blob identities before FFmpeg runs. Playback
and selecting the theme are separate explicit user operations.
"""
from __future__ import annotations
import argparse
import configparser
import hashlib
import html
import io
import json
import os
from pathlib import Path
import re
import shutil
import signal
import struct
import subprocess
import sys
import tempfile
import wave
from sound_transaction import (Change, Failure, Transaction, no_links,
                               snapshot, sha)

ROOT = Path(__file__).resolve().parents[1]
VERSION = '0.1.0'
THEME = 'IrixClassic'
MANIFEST = 'MANIFEST-SOUNDS.json'
MAX_SOURCE = 256 * 1024
MAX_WAV = 4 * 1024 * 1024


def read_json(path: Path):
    no_links(path)
    if not path.is_file() or path.stat().st_size > 4 * 1024 * 1024:
        raise Failure('JSON ausente ou excessivo: ' + str(path))
    return json.loads(path.read_text('utf-8'))


def catalog():
    c = read_json(ROOT / 'data/catalogo.json')
    if c['version'] != VERSION or c['theme_id'] != THEME or len(c['sounds']) != 19:
        raise Failure('Catálogo de sons incompatível.')
    seen = set()
    for s in c['sounds']:
        if not re.fullmatch(r'[a-z0-9.-]+\.(aifc|aiff)', s['original_filename']):
            raise Failure('Nome de fonte inválido.')
        if not re.fullmatch(r'[0-9a-f]{40}', s['git_blob_sha1']):
            raise Failure('Identificador da fonte inválido.')
        if not 12 <= s['source_size'] <= MAX_SOURCE:
            raise Failure('Tamanho de fonte fora do limite.')
        for event in s['events']:
            if not re.fullmatch(r'[a-z][a-z0-9-]+', event) or event in seen:
                raise Failure('Evento inválido ou repetido.')
            seen.add(event)
    if any(e in seen or not re.fullmatch(r'[a-z][a-z0-9-]+', e) for e in c['disabled_events']):
        raise Failure('Evento desabilitado inválido ou conflitante.')
    return c


def xdg(name: str, fallback: str) -> Path:
    p = Path(os.environ.get(name) or str(Path.home() / fallback)).expanduser()
    no_links(p)
    return p


def locations():
    cache = xdg('XDG_CACHE_HOME', '.cache') / 'irixclassic-sounds' / VERSION
    data = xdg('XDG_DATA_HOME', '.local/share')
    state = xdg('XDG_STATE_HOME', '.local/state') / 'irixclassic-sounds'
    config = xdg('XDG_CONFIG_HOME', '.config')
    for p in (cache, data, state, config):
        no_links(p)
    return cache, data / 'sounds' / THEME, state, config


def user_only():
    if os.geteuid() == 0:
        raise Failure('Execute como usuário normal, sem sudo. Este pacote não escreve no sistema.')


def git_blob(data: bytes) -> str:
    return hashlib.sha1(b'blob ' + str(len(data)).encode() + b'\0' + data).hexdigest()


def check_source(data: bytes, s: dict) -> None:
    if len(data) != s['source_size'] or git_blob(data) != s['git_blob_sha1']:
        raise Failure('Bytes diferentes da fonte fixada: ' + s['original_filename'])
    if data[:4] != b'FORM' or data[8:12] not in (b'AIFF', b'AIFC'):
        raise Failure('O arquivo não é AIFF/AIFC: ' + s['original_filename'])
    size = struct.unpack('>I', data[4:8])[0]
    if size + 8 > len(data):
        raise Failure('Arquivo AIFF/AIFC truncado.')


def obtain_source(c: dict, s: dict, cache: Path, origin: Path | None) -> tuple[bytes, str]:
    # A user-provided source is never silently replaced by an online file.
    if origin:
        p = origin / s['original_filename']; no_links(p)
        if not p.is_file() or p.stat().st_size > MAX_SOURCE:
            raise Failure('Fonte local ausente ou excessiva: ' + str(p))
        data = p.read_bytes(); check_source(data, s)
        return data, 'local-pinned-source'
    p = cache / 'originais' / s['original_filename']; no_links(p)
    if p.exists():
        if p.stat().st_size > MAX_SOURCE:
            raise Failure('Cache excessivo: ' + str(p))
        data = p.read_bytes(); check_source(data, s)
        return data, 'verified-cache'
    raise Failure('Fonte ausente. Organize os arquivos originais e use '
                  '--origem DIRETORIO: ' + s['original_filename'])


def wav_info(path: Path) -> dict:
    no_links(path)
    if path.stat().st_size > MAX_WAV:
        raise Failure('Áudio convertido excedeu o limite.')
    with wave.open(str(path), 'rb') as w:
        channels, rate, width, frames = (w.getnchannels(), w.getframerate(),
                                       w.getsampwidth(), w.getnframes())
        if (w.getcomptype() != 'NONE' or channels not in (1, 2) or width != 2
                or not 8000 <= rate <= 48000 or not 0 < frames <= rate * 10):
            raise Failure('Formato/duração WAV fora do perfil permitido.')
        data = w.readframes(frames + 1)
        if len(data) != frames * channels * width:
            raise Failure('WAV truncado.')
    values = [v[0] for v in struct.iter_unpack('<h', data)]
    peak = max(abs(v) for v in values)
    if peak == 0:
        raise Failure('Áudio totalmente silencioso: não será usado como substituto do original.')
    return {'channels': channels, 'rate': rate, 'sample_width': width, 'frames': frames,
            'duration_seconds': frames / rate, 'peak': peak,
            'pcm_sha256': sha(data), 'sha256': sha(path.read_bytes())}


def convert(source: Path, target: Path) -> dict:
    ffmpeg = shutil.which('ffmpeg'); ffprobe = shutil.which('ffprobe')
    if not ffmpeg or not ffprobe:
        raise Failure('FFmpeg/ffprobe ausentes. No Debian: sudo apt install ffmpeg')
    no_links(source); no_links(target)
    probe = subprocess.run([ffprobe, '-v', 'error', '-select_streams', 'a:0',
                            '-show_entries', 'stream=sample_rate,channels', '-of', 'json', str(source)],
                           capture_output=True, text=True, timeout=25, check=False)
    if probe.returncode:
        raise Failure('FFprobe recusou a fonte: ' + probe.stderr[:500])
    streams = json.loads(probe.stdout).get('streams', [])
    if len(streams) != 1:
        raise Failure('Fonte sem uma primeira faixa de áudio válida.')
    rate, channels = int(streams[0]['sample_rate']), int(streams[0]['channels'])
    if channels not in (1, 2) or not 8000 <= rate <= 48000:
        raise Failure('Fonte exigiria remistura/resampling; operação automática recusada.')
    cmd = [ffmpeg, '-nostdin', '-hide_banner', '-loglevel', 'error', '-y', '-i', str(source),
           '-map', '0:a:0', '-vn', '-map_metadata', '-1', '-c:a', 'pcm_s16le',
           '-ar', str(rate), '-ac', str(channels), '-threads', '1', '-bitexact', str(target)]
    r = subprocess.run(cmd, capture_output=True, text=True, timeout=30, check=False)
    if r.returncode:
        raise Failure('Conversão de áudio falhou: ' + r.stderr[:500])
    info = wav_info(target)
    if info['channels'] != channels or info['rate'] != rate:
        raise Failure('A conversão mudou os canais ou a taxa de amostragem.')
    return info


def tree_files(root: Path) -> dict[str, str]:
    no_links(root)
    out = {}
    if not root.exists():
        return out
    if not root.is_dir():
        raise Failure('Diretório esperado: ' + str(root))
    for f in sorted(root.rglob('*')):
        no_links(f)
        if f.is_file():
            if f.stat().st_size > MAX_WAV:
                raise Failure('Arquivo inesperadamente grande: ' + str(f))
            out[f.relative_to(root).as_posix()] = sha(f.read_bytes())
        elif not f.is_dir():
            raise Failure('Arquivo especial recusado: ' + str(f))
    return out


def safe_relative(name: str) -> bool:
    p = Path(name)
    return bool(name) and not p.is_absolute() and '..' not in p.parts and '\\' not in name


def validate_theme(root: Path, c: dict) -> dict:
    m = read_json(root / MANIFEST)
    if m.get('package') != 'IrixClassic Sounds' or m.get('version') != VERSION:
        raise Failure('Tema existente sem manifesto compatível; não será sobrescrito.')
    expected = m.get('files', {})
    if not expected or not all(safe_relative(n) for n in expected):
        raise Failure('Manifesto do tema inválido.')
    names = {'index.theme', 'CREDITS.md', 'MAPEAMENTO.json', 'OUVIR.html'}
    for item in c['sounds']:
        for event in item['events']:
            names.update({'stereo/' + event + '.wav', 'stereo/' + event + '.sound'})
    names.update('stereo/' + event + '.disabled' for event in c['disabled_events'])
    if set(expected) != names:
        raise Failure('Conjunto de arquivos não corresponde ao esquema publicado.')
    actual = tree_files(root); actual.pop(MANIFEST, None)
    if actual != expected:
        raise Failure('Tema alterado, incompleto ou com arquivos extras. Preserve suas alterações.')
    ids = {s['id'] for s in c['sounds'] if s['events']}
    if set(m.get('sources', {})) != ids:
        raise Failure('Manifesto sem todas as fontes requeridas.')
    for s in c['sounds']:
        if not s['events']: continue
        record = m['sources'][s['id']]
        if record['git_blob_sha1'] != s['git_blob_sha1'] or record['source_size'] != s['source_size']:
            raise Failure('Identidade de origem divergente.')
        for event in s['events']:
            path = root / 'stereo' / (event + '.wav')
            if ('stereo/' + event + '.wav') not in expected:
                raise Failure('Evento não registrado: ' + event)
            info = wav_info(path)
            if info['pcm_sha256'] != record['converted']['pcm_sha256']:
                raise Failure('PCM do alias difere da fonte convertida: ' + event)
    for event in c['disabled_events']:
        p = root / 'stereo' / (event + '.disabled')
        if p.read_bytes() != b'':
            raise Failure('Arquivo .disabled deve ser vazio.')
    cfg = configparser.ConfigParser(interpolation=None)
    cfg.read(root / 'index.theme', encoding='utf-8')
    if (cfg['Sound Theme']['Directories'] != 'stereo'
            or cfg['Sound Theme']['Example'] != 'theme-demo'
            or cfg['stereo']['OutputProfile'] != 'stereo'):
        raise Failure('index.theme inválido.')
    return m


def render_gallery(c: dict, records: dict) -> bytes:
    rows = []
    for s in c['sounds']:
        if not s['events']: continue
        event = s['events'][0]
        info = records[s['id']]['converted']
        rows.append('<tr><td>' + html.escape(s['label_pt']) + '</td><td><code>'
                    + html.escape(s['original_filename']) + '</code></td><td>'
                    + f'{info["duration_seconds"]:.3f} s'
                    + '</td><td><audio controls preload="none" src="stereo/' + event + '.wav"></audio></td></tr>')
    return ('''<!doctype html><html lang="pt-BR"><meta charset="utf-8">
<title>IrixClassic Sounds — audição local</title>
<style>body{font:16px system-ui;margin:2rem;max-width:1100px}td,th{padding:.7rem;text-align:left;border-bottom:1px solid #aaa}table{border-collapse:collapse}audio{width:290px}</style>
<h1>IrixClassic Sounds 0.1.0</h1><p>IRIX desktop sounds courtesy the SGI desktop.
Esquema: R. C. Underwood; colaboração de Roger Powell e sons de Jeff Essex.
Integração KDE: mrmmx31.</p><p>Reprodução direta dos WAVs locais: não comprova a entrega de eventos nas aplicações.
Não altera volume ou seleção do KDE. Ajuste o volume antes de ouvir.</p>
<table><tr><th>Função original</th><th>Fonte</th><th>Duração</th><th>Ouvir</th></tr>'''
            + ''.join(rows) + '</table><p>Veja CREDITS.md e MAPEAMENTO.json para a procedência e as adaptações.</p></html>').encode()


def prepare(c: dict, cache: Path, origin: Path | None) -> Path:
    ready = cache / THEME
    if ready.exists():
        validate_theme(ready, c)
        print('Importação já preparada e íntegra:', ready)
        return ready
    needed = [s for s in c['sounds'] if s['events']]
    if not shutil.which('ffmpeg') or not shutil.which('ffprobe'):
        raise Failure('Instale ffmpeg antes de importar os sons.')
    cache.mkdir(mode=0o700, parents=True, exist_ok=True)
    with tempfile.TemporaryDirectory(prefix='.prepare-', dir=cache) as tmp:
        root = Path(tmp); work = root / 'originais'; work.mkdir()
        theme = root / THEME; (theme / 'stereo').mkdir(parents=True)
        records = {}
        for i, s in enumerate(needed, 1):
            print(f'[{i}/{len(needed)}] {s["original_filename"]}', flush=True)
            data, origin_label = obtain_source(c, s, cache, origin)
            p = work / s['original_filename']; p.write_bytes(data)
            wav = root / (s['id'] + '.wav'); info = convert(p, wav)
            records[s['id']] = {'original_filename': s['original_filename'],
                'source_size': len(data), 'source_sha256': sha(data),
                'git_blob_sha1': git_blob(data), 'source': origin_label, 'converted': info}
            for event in s['events']:
                shutil.copyfile(wav, theme / 'stereo' / (event + '.wav'))
                text = '[Sound Data]\nDisplayName=' + s['label_pt'] + '\nX-IrixClassic-Original=' + s['original_filename'] + '\n'
                (theme / 'stereo' / (event + '.sound')).write_text(text, encoding='utf-8')
        for event in c['disabled_events']:
            (theme / 'stereo' / (event + '.disabled')).write_bytes(b'')
        shutil.copyfile(ROOT / 'modelo/index.theme', theme / 'index.theme')
        shutil.copyfile(ROOT / 'docs/CREDITOS-E-AUDIOS.md', theme / 'CREDITS.md')
        (theme / 'MAPEAMENTO.json').write_text(json.dumps(c, ensure_ascii=False, indent=2)+'\n', encoding='utf-8')
        (theme / 'OUVIR.html').write_bytes(render_gallery(c, records))
        m = {'package': 'IrixClassic Sounds', 'version': VERSION, 'theme': THEME,
             'sources': records, 'files': tree_files(theme),
             'conversion': 'WAV PCM s16le; original channels/rate; no gain, trim or remix',
             'authenticity': 'Pinned mirror Git blob identity; not an SGI digital signature.'}
        (theme / MANIFEST).write_text(json.dumps(m, ensure_ascii=False, indent=2)+'\n', encoding='utf-8')
        validate_theme(theme, c)
        # Public audio assets are never written into the Git checkout.
        os.replace(theme, ready)
    return ready


def transaction(destination: Path, state: Path) -> Transaction:
    def allowed(path: Path, phase: int):
        try:
            rel = path.relative_to(destination)
        except ValueError:
            return False
        return bool(rel.parts) and '..' not in rel.parts and (phase == 0 or
            (phase == 2 and rel.as_posix() in ('index.theme', MANIFEST)))
    def no_system(_):
        raise Failure('Escrita administrativa não pertence a este pacote.')
    return Transaction(state, no_system, allowed)


def installed_selection(config: Path):
    # Read only; KCM is the authoritative writer and notifies running apps.
    f = config / 'kdeglobals'; no_links(f)
    if not f.exists(): return {'Theme': '(padrão do KDE)', 'Enable': '(padrão do KDE)'}
    text = f.read_text('utf-8'); group = ''; result = {}
    for raw in text.splitlines():
        line = raw.strip()
        if line.startswith('['): group = line
        elif group == '[Sounds]' and '=' in line and not line.startswith(('#', ';')):
            k, v = line.split('=', 1)
            if k.strip() in ('Theme', 'Enable'): result[k.strip()] = v.strip()
    return result


def verify(c, cache, destination, config) -> dict:
    needed = [s for s in c['sounds'] if s['events']]
    sources = []
    for s in needed:
        p = cache / 'originais' / s['original_filename']; no_links(p)
        ok = False
        if p.exists():
            if p.stat().st_size > MAX_SOURCE: raise Failure('Cache excessivo.')
            check_source(p.read_bytes(), s); ok = True
        sources.append({'file': s['original_filename'], 'cached': ok})
    generated = (cache / THEME).exists()
    if generated: validate_theme(cache / THEME, c)
    installed = destination.exists() and bool(tree_files(destination))
    if installed: validate_theme(destination, c)
    return {'version': VERSION, 'theme_id': THEME,
            'event_aliases': sum(len(s['events']) for s in needed),
            'source_count': len(needed), 'source_bytes': sum(s['source_size'] for s in needed),
            'ffmpeg': bool(shutil.which('ffmpeg')), 'ffprobe': bool(shutil.which('ffprobe')),
            'sources': sources, 'prepared': generated, 'installed': installed,
            'destination': str(destination), 'kde_sound_selection': installed_selection(config),
            'network_used': False, 'dolphin_integration': False}


def install(ready: Path, destination: Path, state: Path, c: dict, dry=False):
    m = validate_theme(ready, c)
    old = tree_files(destination)
    if old: validate_theme(destination, c)
    tx = transaction(destination, state)
    paths = sorted(m['files']) + [MANIFEST]
    changes = [Change(destination / n, (ready / n).read_bytes(),
                      phase=2 if n in ('index.theme', MANIFEST) else 0,
                      expected=snapshot(destination / n)) for n in paths]
    tx.install(changes, dry)
    if not dry:
        validate_theme(destination, c)
        os.utime(destination, None)  # libcanberra theme-cache invalidation
        print('\nTema instalado. Selecione IrixClassic Sounds em Sons do sistema e clique em Aplicar.')
        print('Abrir o painel: kcmshell6 kcm_soundtheme')
        print('Audição local:', destination / 'OUVIR.html')
        print('Seleção, volume, Não perturbe e regras de notificações não foram alterados.')


def main(argv=None):
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('action', choices=('install', 'prepare', 'restore', 'verify'))
    parser.add_argument('--origem', type=Path, help='Pasta com os originais fixados; alternativa sem rede.')
    parser.add_argument('--verificar', action='store_true', help='Somente leitura; não baixa nem escreve.')
    parser.add_argument('--recuperar', action='store_true', help='Recupera restauração/instalação interrompida.')
    args = parser.parse_args(argv)
    if args.recuperar and args.action != 'restore': parser.error('--recuperar exige restore.')
    if args.action not in ('install', 'prepare') and args.origem:
        parser.error('A importação só pertence a install/prepare.')
    c = catalog(); cache, dest, state, config = locations()
    origin = args.origem.expanduser().absolute() if args.origem else None
    if origin: no_links(origin)
    if args.action == 'verify' or (args.verificar and args.action != 'restore'):
        report = verify(c, cache, dest, config)
        if args.action in ('install', 'prepare'):
            report['plan_only'] = True
            report['warning'] = 'Fontes ausentes devem ser fornecidas com --origem DIRETORIO.'
        print(json.dumps(report, indent=2, ensure_ascii=False))
        return 0
    user_only()
    tx = transaction(dest, state)
    if args.action == 'restore':
        # Removing a selected theme would silently change playback via fallback.
        prior = tx.latest()
        if not prior: raise Failure('Não existe instalação registrada por este pacote.')
        removes_index = any(Path(e['path']).name == 'index.theme' and not e['before']['exists']
                            for e in prior[1]['entries'])
        if removes_index and installed_selection(config).get('Theme') == THEME:
            raise Failure('Selecione primeiro outro tema em Sons do sistema; depois restaure.')
        if args.verificar:
            tx.restore(args.recuperar, True)
        else:
            with tx.locked(): tx.restore(args.recuperar, False)
            if dest.exists(): os.utime(dest, None)
        return 0
    with tx.locked():
        tx.assert_ready()
        ready = prepare(c, cache, origin)
        if args.action == 'install': install(ready, dest, state, c)
        else: print('Pronto para instalar:', ready)
    return 0


if __name__ == '__main__':
    def stop(*_): raise KeyboardInterrupt()
    signal.signal(signal.SIGTERM, stop)
    try: sys.exit(main())
    except (Failure, OSError, ValueError, KeyError, TypeError, wave.Error,
            subprocess.TimeoutExpired) as e:
        print('ERRO:', e, file=sys.stderr); sys.exit(1)
    except KeyboardInterrupt:
        print('Interrompido. Se houve escrita, confira o recibo e use restaurar.sh --recuperar.', file=sys.stderr)
        sys.exit(130)
