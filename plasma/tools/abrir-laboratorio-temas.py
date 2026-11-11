#!/usr/bin/env python3
# SPDX-License-Identifier: GPL-3.0-or-later
"""Open the Motif Theme Lab in an already owned, private Xephyr session.

The original fixture and theme export remain untouched. A frozen addon gets its
own supervisor and namespaces, while using the existing disposable HOME, bus
and authenticated X socket. Closing Xephyr terminates only the addon processes.
"""
from __future__ import annotations

import argparse
import hashlib
import importlib.util
import json
import os
from pathlib import Path
import re
import signal
import stat
import subprocess
import sys
import time
import uuid

INNER_HOME = Path('/home/domainos-test')
INNER_ROOT = Path('/fixture/theme-lab-root')
SCRIPT = Path(__file__).resolve()
REPO = SCRIPT.parents[2]
ESSENTIAL = ('dbus', 'kwin', 'plasma')
SAMPLE_FILES = {f'preview-events/{kind}-gtk2-{origin}.json': ('gtk2', origin)
                for kind in ('sample', 'runtime') for origin in ('coupled', 'separate')}
RESUME_LIMITS = {'working.json': 4 * 1024 * 1024,
                'scene.json': 4 * 1024 * 1024,
                'editor-journal.json': 8 * 1024 * 1024,
                'project-history.json': 32 * 1024 * 1024,
                **{name: 32 * 1024 * 1024 for name in SAMPLE_FILES}}


def mapped_lab_windows(pid, timeout=2):
    """Read managed top-level windows, without traversing every widget window.

    Motif creates many child windows. Recursive xdotool search can exhaust the
    observer deadline even when X and the actual application are responsive.
    This launcher requires KWin, so EWMH client membership is authoritative.
    Every subprocess shares one bounded observation deadline.
    """
    deadline = time.monotonic() + timeout
    environment = dict(os.environ, LC_ALL='C')

    def query(argv):
        remaining = deadline - time.monotonic()
        if remaining <= 0:
            raise subprocess.TimeoutExpired(argv, timeout)
        result = subprocess.run(argv, capture_output=True, text=True,
                                env=environment, timeout=remaining)
        return result.stdout if result.returncode == 0 else ''

    clients = query(['xprop', '-root', '_NET_CLIENT_LIST'])
    if not clients.startswith('_NET_CLIENT_LIST(WINDOW):'):
        return []
    ids = re.findall(r'0x[0-9a-fA-F]+', clients)
    # Prefer recently managed clients, while never accepting a foreign PID.
    for window in reversed(ids):
        properties = query(['xprop', '-id', window, '_NET_WM_PID', 'WM_CLASS'])
        actual_pid = re.search(r'^_NET_WM_PID\(CARDINAL\) = (\d+)\s*$',
                               properties, re.MULTILINE)
        actual_class = re.search(r'^WM_CLASS\(STRING\) = "[^"\n]*", "ThemeLab"\s*$',
                                 properties, re.MULTILINE)
        if not actual_pid or int(actual_pid.group(1)) != pid or not actual_class:
            continue
        attributes = query(['xwininfo', '-id', window])
        if re.search(r'^\s*Map State: IsViewable\s*$', attributes, re.MULTILINE):
            return [window]
    return []


def validate_sample(name, data, root=REPO):
    if name not in SAMPLE_FILES:
        return
    source = ('preview_runtime_journal.py' if name.startswith('preview-events/runtime-')
              else 'preview_sample_journal.py')
    spec = importlib.util.spec_from_file_location('launcher_sample_journal',
        root / 'tools/theme-lab' / source)
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    module.decode(data, *SAMPLE_FILES[name])

def runtime_python_files(root):
    """Freeze runtime modules beside their entry points, excluding tests.

    Scene and gallery helpers are imported both normally and by filename.
    Copying only the entry point silently leaves a broken private fixture.
    These two flat directories contain shipped runtime modules; development
    tests live in separate subdirectories and are deliberately not collected.
    """
    return [*sorted((root / 'tools/theme-lab').glob('*.py')),
            *sorted((root / 'plasma/tests/galerias-nativas').glob('*.py'))]


def gtk2_press_files(root):
    """Freeze the optional GTK2 bridge with the sources defining its ABI."""
    helper = root / 'tools/theme-lab/build/libtheme-lab-gtk2-press.so'
    if not helper.exists() and not helper.is_symlink():
        return []
    sources = [root / 'tools/theme-lab/native-gtk2' / name
               for name in ('press.c', 'press.h')]
    if not read_bytes(helper, 16 * 1024 * 1024).startswith(b'\x7fELF'):
        raise RuntimeError('Ponte GTK2 presente não é um ELF próprio regular.')
    if any(not source.is_file() or source.is_symlink() for source in sources):
        raise RuntimeError('Fontes da ponte GTK2 ausentes ou inválidas.')
    if any(source.stat().st_mtime_ns > helper.stat().st_mtime_ns for source in sources):
        raise RuntimeError('Ponte GTK2 anterior aos fontes; compile gtk2-pressure.')
    return [helper, *sources]


def gtk4_host_files(root):
    """Freeze the X11 host bridge and its exact C ABI source pair."""
    helper=root/'tools/theme-lab/build/libtheme-lab-gtk4-host.so'
    if not helper.exists() and not helper.is_symlink():return []
    sources=[root/'tools/theme-lab/native-gtk4'/name for name in ('host.c','host.h')]
    if not read_bytes(helper,16*1024*1024).startswith(b'\x7fELF'):
        raise RuntimeError('Ponte GTK4 presente não é um ELF próprio regular.')
    if any(not source.is_file() or source.is_symlink() for source in sources):
        raise RuntimeError('Fontes da ponte GTK4 ausentes ou inválidas.')
    if any(source.stat().st_mtime_ns>helper.stat().st_mtime_ns for source in sources):
        raise RuntimeError('Ponte GTK4 anterior aos fontes; compile gtk4-host.')
    return [helper,*sources]


def write_json(path, data):
    temporary = path.with_name(path.name + '.tmp')
    fd = os.open(temporary, os.O_WRONLY | os.O_CREAT | os.O_TRUNC | os.O_NOFOLLOW, 0o600)
    with os.fdopen(fd, 'w', encoding='utf-8') as stream:
        json.dump(data, stream, ensure_ascii=False, indent=2)
        stream.write('\n')
    temporary.replace(path)


def read_bytes(path, limit=4 * 1024 * 1024, owned=True):
    fd = os.open(path, os.O_RDONLY | os.O_NOFOLLOW | os.O_NONBLOCK)
    with os.fdopen(fd, 'rb') as stream:
        info = os.fstat(stream.fileno())
        if (not stat.S_ISREG(info.st_mode) or info.st_size > limit or
                (owned and info.st_uid != os.getuid())):
            raise RuntimeError('Arquivo não regular, de outro usuário ou fora do limite: ' + str(path))
        data = stream.read(limit + 1)
        if len(data) > limit:
            raise RuntimeError('Arquivo cresceu durante a leitura: ' + str(path))
        return data


def read_json(path):
    return json.loads(read_bytes(path))


def digest(path):
    return hashlib.sha256(read_bytes(path, 64 * 1024 * 1024)).hexdigest()


def private_directory(path):
    info = path.lstat()
    if (not stat.S_ISDIR(info.st_mode) or info.st_uid != os.getuid() or
            stat.S_IMODE(info.st_mode) & 0o077):
        raise RuntimeError('Diretório privado 0700 do próprio usuário exigido: ' + str(path))


def namespace_ids(pid):
    return {key: os.stat(f'/proc/{pid}/ns/{key}').st_ino
            for key in ('mnt', 'net', 'pid', 'user')}


def process_identity(pid, token=None, lab_id=None):
    if type(pid) is not int or pid <= 1:
        raise RuntimeError('PID inválido na sessão privada')
    proc = Path('/proc') / str(pid)
    if proc.stat().st_uid != os.getuid():
        raise RuntimeError('O processo não pertence ao usuário atual')
    status = (proc / 'status').read_text()
    uid = re.search(r'^Uid:\s+(\d+)\s+(\d+)', status, re.MULTILINE)
    if uid is None or any(int(value) != os.getuid() for value in uid.groups()):
        raise RuntimeError('UID real/efetivo do processo não corresponde à sessão')
    command = (proc / 'cmdline').read_bytes().split(b'\0')
    argv = [part.decode('utf-8', 'surrogateescape') for part in command if part]
    environment = ((proc / 'environ').read_bytes().split(b'\0')
                   if token is not None or lab_id is not None else [])
    for name, value in (('IRIX_DOMAINOS_PREVIEW_ID', token), ('IRIX_DOMAINOS_LAB_ID', lab_id)):
        if value is not None and (name + '=' + value).encode() not in environment:
            raise RuntimeError('O processo não tem o marcador privado esperado: ' + name)
    fields = (proc / 'stat').read_text().rsplit(')', 1)[1].split()
    if not argv or fields[0] == 'Z':
        raise RuntimeError('O processo privado encerrou')
    return {'pid': pid, 'starttime': int(fields[19]), 'argv': argv,
            'namespace': namespace_ids(pid)}


def identity_alive(identity, token=None, lab_id=None):
    try:
        current = process_identity(identity['pid'], token, lab_id)
        return (current['starttime'] == identity['starttime'] and
                current['argv'] == identity['argv'] and
                current['namespace'] == identity['namespace'])
    except (OSError, RuntimeError, ValueError):
        return False


def started_process_identity(process, token, lab_id, timeout=2):
    """Observe this exact child until its exec environment is readable."""
    deadline = time.monotonic() + timeout
    last_error = None
    while time.monotonic() < deadline:
        if process.poll() is not None:
            raise RuntimeError('A aplicação encerrou antes da identificação: ' + str(process.returncode))
        try:
            return process_identity(process.pid, token, lab_id)
        except (OSError, RuntimeError, ValueError) as error:
            last_error = error
            time.sleep(.02)
    raise RuntimeError('Identidade privada da aplicação não confirmada: ' + str(last_error))


def own_signal(identity, token, lab_id, number):
    """A pidfd retains the proved process identity even if a PID gets reused."""
    descriptor = os.pidfd_open(identity['pid'])
    try:
        if not identity_alive(identity, token, lab_id):
            return False
        signal.pidfd_send_signal(descriptor, number)
        return True
    finally:
        os.close(descriptor)


def xephyr_identity(session, display):
    matches = []
    # Read only owned Xephyr command lines, then verify the precise auth file.
    for proc in Path('/proc').iterdir():
        if not proc.name.isdigit():
            continue
        try:
            if proc.stat().st_uid != os.getuid() or (proc / 'comm').read_text().strip() != 'Xephyr':
                continue
            identity = process_identity(int(proc.name))
            argv = identity['argv']
            if (len(argv) > 1 and Path(argv[0]).name == 'Xephyr' and argv[1] == display and
                    '-auth' in argv and argv[argv.index('-auth') + 1] == str(session / 'Xauthority')):
                matches.append(identity)
        except (OSError, ValueError, IndexError, RuntimeError):
            continue
    if len(matches) != 1:
        raise RuntimeError('Não foi encontrada uma única Xephyr própria com o display e Xauthority da sessão')
    return matches[0]


def verify_session(session):
    private_directory(session)
    if any((session / name).exists() for name in ('ENCERRADO.json', 'ERRO.json')):
        raise RuntimeError('A prévia já encerrou ou registrou erro')
    manifest = read_json(session / 'MANIFESTO.json')
    report = read_json(session / 'RESULTADO.json')
    if manifest.get('uid') != os.getuid() or report.get('status') != 'open':
        raise RuntimeError('Prévia aberta do próprio usuário exigida')
    environment = manifest.get('environment', {})
    display = manifest.get('display', '')
    token = environment.get('IRIX_DOMAINOS_PREVIEW_ID', '')
    required = {'HOME': str(INNER_HOME), 'USER': 'domainos-test', 'LOGNAME': 'domainos-test',
                'DISPLAY': display, 'XAUTHORITY': str(INNER_HOME / '.Xauthority'),
                'DBUS_SESSION_BUS_ADDRESS': 'unix:path=/run/user/1000/bus',
                'XDG_RUNTIME_DIR': '/run/user/1000', 'PRIVATE_XEPHYR': '1',
                'IRIX_DOMAINOS_PRIVATE_NAMESPACE': 'bwrap'}
    if (not re.fullmatch(r':\d+', display) or not re.fullmatch(r'[0-9a-f]{32}', token) or
            any(environment.get(key) != value for key, value in required.items())):
        raise RuntimeError('O ambiente da sessão não atende às barreiras privadas')
    for key in ('XDG_CONFIG_HOME', 'XDG_DATA_HOME', 'XDG_CACHE_HOME', 'XDG_STATE_HOME'):
        if not Path(environment.get(key, '')).is_relative_to(INNER_HOME):
            raise RuntimeError('O ambiente XDG escaparia do HOME privado')
    own_namespaces = namespace_ids('self')
    if manifest.get('parent_namespaces', {}).get('pid') != own_namespaces['pid']:
        raise RuntimeError('A sessão exige o mesmo namespace de PID para autenticação XRes')
    worker = process_identity(report.get('worker_pid'), token)
    if (worker['namespace'] != report.get('namespace') or
            worker['namespace']['pid'] != own_namespaces['pid'] or
            any(worker['namespace'][key] == own_namespaces[key] for key in ('mnt', 'net', 'user')) or
            '/fixture/prever-tema-completo.py' not in worker['argv'] or '--worker' not in worker['argv']):
        raise RuntimeError('O worker da prévia não tem a identidade/isolamento esperados')
    worker_environment = Path(f"/proc/{worker['pid']}/environ").read_bytes().split(b'\0')
    if any((key + '=' + value).encode() not in worker_environment
           for key, value in environment.items() if isinstance(key, str) and isinstance(value, str)):
        raise RuntimeError('O ambiente publicado difere do worker existente')
    if any(not isinstance(key, str) or not isinstance(value, str) for key, value in environment.items()):
        raise RuntimeError('Ambiente publicado inválido')
    processes = {'worker': worker}
    for name in ESSENTIAL:
        entry = report.get('processes', {}).get(name, {})
        current = process_identity(entry.get('pid'), token)
        expected = entry.get('argv', [])
        if (current['namespace'] != worker['namespace'] or not expected or
                Path(current['argv'][0]).name != Path(expected[0]).name or current['argv'][1:] != expected[1:]):
            raise RuntimeError('Um processo essencial não corresponde ao recibo: ' + name)
        processes[name] = current
    processes['xephyr'] = xephyr_identity(session, display)
    if processes['xephyr']['namespace']['pid'] != own_namespaces['pid']:
        raise RuntimeError('Xephyr não compartilha o namespace de PID')
    for name in ('etc', 'run', 'tmp', 'home', 'fixture', 'applications'):
        if not (session / name).is_dir() or (session / name).is_symlink():
            raise RuntimeError('Montagem da sessão ausente ou ligada: ' + name)
    for resource in manifest.get('resources', []):
        mount = Path(resource.get('mount', ''))
        if not mount.is_relative_to(INNER_HOME) or mount == INNER_HOME or not Path(resource.get('source', '')).exists():
            raise RuntimeError('Recurso somente leitura da sessão é inválido')
    return manifest, processes


def frozen_copy(source, target):
    before = source.stat()
    payload = read_bytes(source, 64 * 1024 * 1024)
    after = source.stat()
    if (before.st_ino, before.st_size, before.st_mtime_ns) != (after.st_ino, after.st_size, after.st_mtime_ns):
        raise RuntimeError('Fonte mudou enquanto o addon era congelado: ' + str(source))
    target.parent.mkdir(parents=True, exist_ok=True)
    target.write_bytes(payload)
    target.chmod(0o555 if before.st_mode & 0o111 else 0o444)
    return hashlib.sha256(payload).hexdigest()


def instance_work(manifest):
    lab_id = manifest.get('lab_id', '')
    new_instance = manifest.get('new_instance', False)
    if not re.fullmatch(r'[0-9a-f]{32}', lab_id) or type(new_instance) is not bool:
        raise RuntimeError('Identidade da instância do laboratório inválida')
    relative = 'theme-lab-' + lab_id[:12] if new_instance else 'theme-lab'
    if manifest.get('work_directory_relative', relative) != relative:
        raise RuntimeError('Diretório de trabalho não corresponde à instância privada')
    return INNER_HOME / relative


def recovered_editor_snapshot(session, path):
    """Accept an explicit, owned rescue snapshot, never a foreign profile."""
    path = path.absolute()
    if path.parent != session / 'home' or path.is_symlink():
        raise RuntimeError('Journal recuperado exige arquivo direto no HOME privado desta sessão')
    private_directory(path.parent)
    if path.stat().st_mode & 0o077:
        raise RuntimeError('Journal recuperado exige permissões privadas')
    data = read_bytes(path, 8 * 1024 * 1024)
    root = json.loads(data)
    if not isinstance(root, dict) or root.get('schema_version') != 1:
        raise RuntimeError('Schema do journal recuperado inválido')
    histories = root.get('histories')
    if not isinstance(histories, dict):
        raise RuntimeError('Históricos recuperados inválidos')
    for key, row in histories.items():
        if (not isinstance(key, str) or not key or '\0' in key or
                len(key.encode('utf-8')) >= 1024 or not isinstance(row, dict)):
            raise RuntimeError('Contexto recuperado inválido')
        entries, position = row.get('entries'), row.get('position')
        if (not isinstance(entries, list) or not 1 <= len(entries) <= 128 or
                type(position) is not int or not 0 <= position < len(entries)):
            raise RuntimeError('Undo/Redo recuperado inválido')
        if any(not isinstance(s, str) or '\0' in s or len(s.encode('utf-8')) > 65536
               for s in entries) or sum(len(s.encode('utf-8')) for s in entries) > 1024 * 1024:
            raise RuntimeError('Texto recuperado inválido ou fora do limite')
    return data, {'source_snapshot': str(path), 'sha256': hashlib.sha256(data).hexdigest(),
                  'histories': len(histories), 'source_snapshot_untouched': True}


def resume_files_to_verify(resume):
    saved = resume['saved_files_sha256']
    delivered = resume.get('delivered_files_sha256', saved)
    recovery = resume.get('editor_recovery')
    if not isinstance(saved, dict) or not isinstance(delivered, dict):
        raise RuntimeError('Hashes da retomada inválidos')
    if recovery:
        if delivered.get('editor-journal.json') != recovery.get('sha256'):
            raise RuntimeError('Hash do journal recuperado divergente')
        if {k:v for k,v in saved.items() if k != 'editor-journal.json'} != {
                k:v for k,v in delivered.items() if k != 'editor-journal.json'}:
            raise RuntimeError('Recuperação não pode substituir outros arquivos')
    elif delivered != saved:
        raise RuntimeError('Retomada sem recuperação deve conservar os hashes salvos')
    return delivered


def resume_snapshot(session, source_manifest, destination, editor_recovery=None):
    """Copy saved proposal, applied scene and histories; never reuse generated outputs."""
    source_manifest = source_manifest.absolute()
    base = session / 'lab-addon'
    if (source_manifest.name != 'MANIFESTO.json' or source_manifest.is_symlink() or
            source_manifest.parent.parent != base or source_manifest.parent.is_symlink()):
        raise RuntimeError('Retomada exige manifesto de addon desta mesma sessão')
    private_directory(source_manifest.parent)
    old = read_json(source_manifest)
    original = read_json(session / 'MANIFESTO.json')
    if (old.get('uid') != os.getuid() or old.get('session') != str(session) or
            old.get('preview_id') != original['environment']['IRIX_DOMAINOS_PREVIEW_ID']):
        raise RuntimeError('A origem da retomada não pertence à sessão')
    source = session / 'home' / instance_work(old).name
    private_directory(source)
    if destination.exists() or destination.is_symlink():
        raise RuntimeError('Retomada nunca sobrescreve um diretório existente')
    payloads = {}
    limits = RESUME_LIMITS
    for name, limit in limits.items():
        path = source / name
        if name in SAMPLE_FILES and path.parent.exists():
            private_directory(path.parent)
        if name in SAMPLE_FILES and path.parent.is_symlink():
            raise RuntimeError('Journal de amostras não pode atravessar link')
        if name != 'working.json' and not path.exists() and not path.is_symlink():
            continue
        before = path.lstat()
        data = read_bytes(path, limit)
        after = path.lstat()
        if ((before.st_ino, before.st_size, before.st_mtime_ns) !=
                (after.st_ino, after.st_size, after.st_mtime_ns)):
            raise RuntimeError('A origem mudou durante a retomada: ' + name)
        if stat.S_IMODE(after.st_mode) & 0o077 or not isinstance(json.loads(data), dict):
            raise RuntimeError('Retomada exige JSON privado com objeto raiz: ' + name)
        validate_sample(name, data)
        payloads[name] = data
    # Recheck the whole set, so a concurrent checkpoint cannot mix generations.
    for name, data in payloads.items():
        if read_bytes(source / name, limits[name]) != data:
            raise RuntimeError('Edição concorrente na origem; repetir após pausa')
    delivered = dict(payloads)
    recovery = None
    if editor_recovery:
        recovered, recovery = recovered_editor_snapshot(session, editor_recovery)
        baseline = json.loads(payloads.get('editor-journal.json', b'{"histories":{}}'))
        if not set(baseline.get('histories', {})).issubset(json.loads(recovered)['histories']):
            raise RuntimeError('Recuperação não pode remover contextos já salvos')
        delivered['editor-journal.json'] = recovered
        if read_bytes(editor_recovery, 8 * 1024 * 1024) != recovered:
            raise RuntimeError('Snapshot de recuperação mudou durante a retomada')
        for name, data in payloads.items():
            if read_bytes(source / name, limits[name]) != data:
                raise RuntimeError('Edição concorrente durante recuperação; repetir após pausa')
    destination.mkdir(mode=0o700)
    for name, data in delivered.items():
        (destination / name).parent.mkdir(mode=0o700, parents=True, exist_ok=True)
        descriptor = os.open(destination / name,
                             os.O_WRONLY | os.O_CREAT | os.O_EXCL | os.O_NOFOLLOW, 0o600)
        with os.fdopen(descriptor, 'wb') as stream:
            stream.write(data)
            stream.flush()
            os.fsync(stream.fileno())
    return {'source_manifest': str(source_manifest),
            'source_manifest_sha256': digest(source_manifest),
            'saved_files_sha256': {name: hashlib.sha256(data).hexdigest()
                                   for name, data in payloads.items()},
            'delivered_files_sha256': {name: hashlib.sha256(data).hexdigest()
                                       for name, data in delivered.items()},
            'editor_recovery': recovery,
            'source_untouched': True, 'unsaved_widget_text_imported': False,
            'runtime_outputs_imported': False,
            'sample_histories_imported': [name for name in payloads if name in SAMPLE_FILES],
            'applied_scene_imported': 'scene.json' in payloads}


def prepare(args):
    if os.getuid() == 0 or os.geteuid() != os.getuid():
        raise RuntimeError('Execute como usuário da prévia, sem sudo')
    session = args.sessao.absolute()
    if session.is_symlink():
        raise RuntimeError('A sessão não pode ser um link')
    session = session.resolve()
    manifest, processes = verify_session(session)
    if args.retomar_manifesto and not args.nova_instancia:
        raise RuntimeError('--retomar-manifesto exige --nova-instancia')
    if args.recuperar_journal and not args.retomar_manifesto:
        raise RuntimeError('--recuperar-journal exige --retomar-manifesto')
    root = args.raiz.resolve()
    binary = root / 'tools/theme-lab/build/theme-lab'
    if not binary.is_file() or not os.access(binary, os.X_OK) or not read_bytes(binary, 64 * 1024 * 1024).startswith(b'\x7fELF'):
        raise RuntimeError('Compile primeiro tools/theme-lab/build/theme-lab (make -C tools/theme-lab)')
    sources = [*sorted((root / 'tools/theme-lab/src').rglob('*.c')),
               *sorted((root / 'tools/theme-lab/src').rglob('*.h')),
               *sorted((root / 'tools/theme-lab/include').glob('*.h')), root / 'tools/theme-lab/Makefile',
               root / 'tools/theme-lab/sample_controls.json', root / 'tools/theme-lab/sample_contract.py']
    sources += [*sorted((root/'tools/theme-lab/native-gtk4').glob('*.c')),
                *sorted((root/'tools/theme-lab/native-gtk4').glob('*.h'))]
    if any(source.stat().st_mtime_ns > binary.stat().st_mtime_ns for source in sources):
        raise RuntimeError('O binário é anterior às fontes: execute make -C tools/theme-lab antes de abrir')
    native_sources = [*sorted((root / 'tools/theme-lab/src').glob('*.cpp')),
                      root / 'tools/theme-lab/native-build/CMakeLists.txt']
    native_helper = root / 'tools/theme-lab/build/theme-lab-colors'
    helper_files = gtk2_press_files(root)+gtk4_host_files(root)
    if native_helper.exists() or native_helper.is_symlink():
        if (not os.access(native_helper, os.X_OK) or
                not read_bytes(native_helper, 64 * 1024 * 1024).startswith(b'\x7fELF')):
            raise RuntimeError('O helper theme-lab-colors presente não é um ELF próprio executável')
        if any(source.stat().st_mtime_ns > native_helper.stat().st_mtime_ns for source in native_sources):
            raise RuntimeError('O helper theme-lab-colors é anterior às suas fontes C++/CMake: recompile-o antes de abrir')
        helper_files.append(native_helper)
    base = session / 'lab-addon'
    base.mkdir(mode=0o700, exist_ok=True)
    private_directory(base)
    if not args.nova_instancia:
        for existing in base.glob('*/MANIFESTO.json'):
            old = read_json(existing)
            result = existing.with_name('RESULTADO.json')
            if result.is_file() and read_json(result).get('status') in ('starting', 'open'):
                identity = old.get('supervisor')
                if identity and identity_alive(identity, old['preview_id'], old['lab_id']):
                    raise RuntimeError('Este laboratório já tem um addon aberto: ' + str(existing.parent) +
                                       '; use --nova-instancia para outro diretório de trabalho')
    lab_id = uuid.uuid4().hex
    output = base / ('run-' + lab_id)
    output.mkdir(mode=0o700)
    fixture = output / 'root'
    fixture.mkdir(mode=0o700)
    files = [binary, *runtime_python_files(root), root / 'tools/theme-lab/sample_controls.json',
             *helper_files, *native_sources, root / 'tools/domainos_scrollbar_rules.json',
             root / 'gtk/tools/build_kde_domainos.py', root / 'gtk/tools/adaptive_assets.py',
             root / 'colors/DomainOS-SR10.4.colors', root / 'decorations/domainos/LICENSE',
             root / 'docs/referencias/domainos-sr104/trash-can-normal.png',
             *sorted((root / 'tools').glob('*.py')),
             *sources]
    hashes = {}
    for source in dict.fromkeys(files):
        target = fixture / ('reference.png' if source.name == 'trash-can-normal.png' else source.relative_to(root))
        hashes[str(target.relative_to(fixture))] = frozen_copy(source, target)
    launcher = output / SCRIPT.name
    launcher_sha = frozen_copy(SCRIPT, launcher)
    for directory in sorted((path for path in fixture.rglob('*') if path.is_dir()), reverse=True):
        directory.chmod(0o555)
    fixture.chmod(0o555)
    payload = {'schema_version': 1, 'uid': os.getuid(), 'session': str(session),
               'lab_id': lab_id, 'preview_id': manifest['environment']['IRIX_DOMAINOS_PREVIEW_ID'],
               'new_instance': args.nova_instancia,
               'work_directory_relative': 'theme-lab-' + lab_id[:12] if args.nova_instancia else 'theme-lab',
               'native_colors_helper_frozen': bool(helper_files),
               'original_manifest_sha256': digest(session / 'MANIFESTO.json'),
               'original_processes': processes, 'fixture_sha256': hashes,
               'launcher_sha256': launcher_sha,
               'environment': dict(manifest['environment'], IRIX_DOMAINOS_LAB_ID=lab_id),
               'scope': 'Addon namespace only; original fixture/export unchanged; shares disposable HOME/bus/Xephyr.'}
    payload['work_directory'] = str(instance_work(payload))
    if args.retomar_manifesto:
        payload['resume'] = resume_snapshot(session, args.retomar_manifesto,
                                           session / 'home' / instance_work(payload).name,
                                           args.recuperar_journal)
    path = output / 'MANIFESTO.json'
    write_json(path, payload)
    write_json(output / 'RESULTADO.json', {'status': 'starting', 'gui_started': False,
               'new_instance': payload['new_instance'], 'work_directory': payload['work_directory'],
               'work_directory_relative': payload['work_directory_relative']})
    environment = {'PATH': '/usr/bin:/bin', 'LC_ALL': 'C.UTF-8',
                   'IRIX_DOMAINOS_PREVIEW_ID': payload['preview_id'], 'IRIX_DOMAINOS_LAB_ID': lab_id}
    with (output / 'supervisor.log').open('w') as log:
        supervisor_process = subprocess.Popen([sys.executable, '-B', str(launcher), '--supervisor', str(path)],
             stdout=log, stderr=subprocess.STDOUT, start_new_session=True, env=environment)
    payload['supervisor'] = process_identity(supervisor_process.pid, payload['preview_id'], lab_id)
    write_json(path, payload)
    deadline = time.monotonic() + 20
    while time.monotonic() < deadline:
        report = read_json(output / 'RESULTADO.json')
        if report.get('status') == 'open':
            print(json.dumps({'status': 'open', 'display': manifest['display'], 'pid': report['app']['pid'],
                  'windows': report.get('windows', []), 'report': str(output / 'RESULTADO.json'),
                  'manifest': str(path), 'work_directory': payload['work_directory'],
                  'work_directory_relative': payload['work_directory_relative']}, ensure_ascii=False))
            return 0
        if report.get('status') in ('failed', 'closed') or supervisor_process.poll() is not None:
            raise RuntimeError(report.get('error', 'Supervisor do laboratório encerrou; veja ' + str(output / 'supervisor.log')))
        time.sleep(.1)
    raise RuntimeError('A janela ainda não foi confirmada; o addon permanece monitorado. Consulte ' + str(output / 'RESULTADO.json'))


def frozen_verify(output, manifest):
    private_directory(output)
    if manifest['uid'] != os.getuid() or digest(output / SCRIPT.name) != manifest['launcher_sha256']:
        raise RuntimeError('Supervisor addon alterado ou de outro usuário')
    for relative, expected in manifest['fixture_sha256'].items():
        path = Path(relative)
        if path.is_absolute() or '..' in path.parts or digest(output / 'root' / path) != expected:
            raise RuntimeError('Fonte congelada do laboratório mudou: ' + relative)


def container_command(session, output, original, manifest):
    worker_identity = manifest['original_processes']['worker']
    if not identity_alive(worker_identity, manifest['preview_id']):
        raise RuntimeError('O worker original mudou antes da montagem X')
    directory = Path(f"/proc/{worker_identity['pid']}/root/tmp/.X11-unix")
    socket = directory / ('X' + original['display'].lstrip(':'))
    info = socket.stat()
    if (not stat.S_ISSOCK(info.st_mode) or info.st_uid != os.getuid() or
            list(directory.iterdir()) != [socket]):
        raise RuntimeError('Diretório X privado não contém somente o socket próprio esperado')
    # Enter the proved private mount first, then create an independent addon
    # namespace. Recursive directory bind retains an unlinked socket mount.
    command = ['nsenter', '--target', str(worker_identity['pid']), '--user', '--mount', '--net',
        '--preserve-credentials', 'bwrap', '--unshare-user', '--unshare-net',
        '--unshare-ipc', '--unshare-uts', '--uid', '1000', '--gid', '1000', '--clearenv',
        '--ro-bind', '/usr', '/usr', '--symlink', 'usr/bin', '/bin', '--symlink', 'usr/lib', '/lib',
        '--symlink', 'usr/lib64', '/lib64', '--ro-bind', str(session / 'etc'), '/etc',
        '--proc', '/proc', '--dev', '/dev', '--bind', str(session / 'run'), '/run',
        '--bind', str(session / 'tmp'), '/tmp', '--bind', str(session / 'home'), str(INNER_HOME),
        '--bind', str(session), '/out', '--tmpfs', '/fixture']
    # Separate read-only mounts preserve every original /fixture entry while
    # allowing a new mountpoint without creating anything in the frozen tree.
    for entry in sorted((session / 'fixture').iterdir()):
        if entry.name == 'theme-lab-root':
            raise RuntimeError('A fixture original já usa o nome reservado do laboratório')
        command.extend(['--ro-bind', str(entry), '/fixture/' + entry.name])
    command.extend(['--ro-bind', str(output / 'root'), str(INNER_ROOT),
        '--remount-ro', '/fixture', '--ro-bind', '/tmp/.X11-unix', '/tmp/.X11-unix',
        '--ro-bind', str(session / 'Xauthority'), str(INNER_HOME / '.Xauthority'),
        '--ro-bind', str(session / 'applications'), '/usr/share/applications'])
    for resource in original['resources']:
        command.extend(['--ro-bind', resource['mount'], resource['mount']])
    for key, value in manifest['environment'].items():
        command.extend(['--setenv', key, value])
    inner_output = Path('/out') / output.relative_to(session)
    command.extend(['--die-with-parent', '--new-session', '--chdir', str(INNER_HOME),
        '/usr/bin/python3', '-B', str(inner_output / SCRIPT.name), '--worker',
        str(inner_output / 'MANIFESTO.json')])
    prefix = str(session)
    return ['/out' + value[len(prefix):] if value == prefix or
            value.startswith(prefix + '/') else value for value in command]


def stop_child(process):
    if process is None or process.poll() is not None:
        return
    process.terminate()
    try:
        process.wait(5)
    except subprocess.TimeoutExpired:
        process.kill()
        process.wait(3)


def worker(path):
    output = path.parent
    manifest = read_json(path)
    work = instance_work(manifest)
    # Guards run before the native app or any gallery can initialize X/Qt/GTK.
    sys.path.insert(0, str(INNER_ROOT / 'plasma/tests/galerias-nativas'))
    from qt6_demo import private_guards
    from demo_env import require_private_session
    checks = private_guards()
    require_private_session()
    if (os.environ.get('IRIX_DOMAINOS_PREVIEW_ID') != manifest['preview_id'] or
            os.environ.get('IRIX_DOMAINOS_LAB_ID') != manifest['lab_id']):
        raise RuntimeError('Marcador addon diferente do manifesto')
    original = read_json(Path('/out/MANIFESTO.json'))
    namespaces = namespace_ids('self')
    if (namespaces['pid'] != original['parent_namespaces']['pid'] or
            any(namespaces[key] == original['parent_namespaces'][key] for key in ('mnt', 'net', 'user')) or
            list(Path('/tmp/.X11-unix').iterdir()) != [Path('/tmp/.X11-unix/X' + original['display'].lstrip(':'))]):
        raise RuntimeError('Namespace ou socket X do addon não é o esperado')
    report = {'status': 'starting', 'checks': checks, 'namespace': namespaces,
              'worker': process_identity(os.getpid(), manifest['preview_id'], manifest['lab_id']),
              'new_instance': manifest.get('new_instance', False), 'work_directory': str(work),
              'work_directory_relative': work.name,
              'gui_started': False}
    write_json(output / 'RESULTADO.json', report)
    process = None

    def terminate(_number, _frame):
        raise SystemExit(0)
    signal.signal(signal.SIGTERM, terminate)
    signal.signal(signal.SIGINT, terminate)
    try:
        work.mkdir(mode=0o700, exist_ok=True)
        private_directory(work)
        if manifest.get('resume'):
            expected = resume_files_to_verify(manifest['resume'])
            if (not isinstance(expected, dict) or 'working.json' not in expected or
                    any(name not in RESUME_LIMITS or
                        digest(work / name) != value for name, value in expected.items())):
                raise RuntimeError('Os dados de retomada mudaram antes da abertura')
            for name in expected:
                validate_sample(name, read_bytes(work / name, RESUME_LIMITS[name]), INNER_ROOT)
        argv = [str(INNER_ROOT / 'tools/theme-lab/build/theme-lab'), '--root', str(INNER_ROOT),
                '--work-dir', str(work)]
        if not manifest.get('resume'):
            argv.extend(['--reference', str(INNER_ROOT / 'reference.png')])
        if manifest.get('new_instance') and not manifest.get('resume'):
            argv.extend(['--family', 'gtk3'])
        with (output / 'motif.log').open('w') as log:
            process = subprocess.Popen(argv, stdout=log, stderr=subprocess.STDOUT, start_new_session=True)
            report['app'] = started_process_identity(process, manifest['preview_id'], manifest['lab_id'])
            report['argv'] = argv; report['gui_started'] = True
            write_json(output / 'RESULTADO.json', report)
            deadline = time.monotonic() + 15
            while process.poll() is None and time.monotonic() < deadline:
                try:
                    windows = mapped_lab_windows(process.pid)
                except subprocess.TimeoutExpired:
                    # An observer timeout says nothing about the app's state.
                    # Keep observing this exact child until the startup deadline.
                    report['window_observation_timeouts'] = report.get('window_observation_timeouts', 0) + 1
                    write_json(output / 'RESULTADO.json', report)
                    continue
                if windows:
                    # The controller publishes _NET_WM_PID. Matching both PID
                    # and native class prevents V1 from satisfying V2 readiness.
                    # This observes mapping only; no window input is sent.
                    report.update(status='open', windows=windows, window_map_observed=True,
                                  window_input_sent=False)
                    write_json(output / 'RESULTADO.json', report)
                    break
                time.sleep(.1)
            if report['status'] != 'open':
                raise RuntimeError('Motif não mapeou a janela no prazo; consulte motif.log')
            while process.poll() is None:
                time.sleep(.3)
            report.update(status='closed', exit_code=process.returncode, reason='Motif window closed')
    except BaseException as error:
        if isinstance(error, SystemExit):
            report.update(status='closed', reason='Addon supervisor requested own cleanup')
        else:
            report.update(status='failed', error=str(error))
        write_json(output / 'RESULTADO.json', report)
        if not isinstance(error, SystemExit):
            raise
    finally:
        signal.signal(signal.SIGTERM, signal.SIG_IGN)
        signal.signal(signal.SIGINT, signal.SIG_IGN)
        stop_child(process)
        report['own_app_stopped'] = process is None or process.poll() is not None
        write_json(output / 'RESULTADO.json', report)


def supervisor(path):
    output = path.parent
    manifest = read_json(path)
    frozen_verify(output, manifest)
    session = Path(manifest['session'])
    original, current = verify_session(session)
    if digest(session / 'MANIFESTO.json') != manifest['original_manifest_sha256'] or current != manifest['original_processes']:
        raise RuntimeError('A prévia mudou desde a preparação do laboratório')
    container = None

    def terminate(_number, _frame):
        raise SystemExit(0)
    signal.signal(signal.SIGTERM, terminate)
    signal.signal(signal.SIGINT, terminate)
    try:
        command = container_command(session, output, original, manifest)
        write_json(output / 'MONTAGENS.json', {'argv': command, 'original_fixture_untouched': True,
                   'shared_pid_namespace_for_xres': True, 'no_new_xephyr': True})
        with (output / 'namespace.log').open('w') as log:
            container = subprocess.Popen(command, stdout=log, stderr=subprocess.STDOUT,
                        start_new_session=True,
                        env={'PATH': '/usr/bin:/bin', 'LC_ALL': 'C.UTF-8'})
            while container.poll() is None:
                if not all(identity_alive(identity, manifest['preview_id'] if name != 'xephyr' else None)
                           for name, identity in manifest['original_processes'].items()):
                    write_json(output / 'ENCERRADO.json', {'reason': 'Original owned preview process closed',
                                                          'only_addon_stopped': True})
                    break
                time.sleep(.3)
    except BaseException as error:
        if not isinstance(error, SystemExit):
            report = read_json(output / 'RESULTADO.json')
            report.update(status='failed', error=str(error))
            write_json(output / 'RESULTADO.json', report)
            raise
    finally:
        signal.signal(signal.SIGTERM, signal.SIG_IGN)
        signal.signal(signal.SIGINT, signal.SIG_IGN)
        try:
            report = read_json(output / 'RESULTADO.json')
            identity = report.get('worker')
            if identity and own_signal(identity, manifest['preview_id'], manifest['lab_id'], signal.SIGTERM):
                deadline = time.monotonic() + 6
                while identity_alive(identity, manifest['preview_id'], manifest['lab_id']) and time.monotonic() < deadline:
                    time.sleep(.1)
        except (OSError, RuntimeError, ValueError):
            pass
        stop_child(container)
        # The native controller owns/kills its backend process groups on Quit,
        # SIGTERM and XIO. Only the recorded addon app is a fallback target;
        # never scan or signal processes of the original preview.
        try:
            report = read_json(output / 'RESULTADO.json')
            identity = report.get('app')
            if identity:
                own_signal(identity, manifest['preview_id'], manifest['lab_id'], signal.SIGTERM)
        except (OSError, RuntimeError, ValueError):
            pass
        write_json(output / 'SUPERVISOR-ENCERRADO.json', {'only_addon_processes_targeted': True,
                   'original_fixture_untouched': True, 'new_xephyr_started': False})


def main(argv=None):
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--sessao', type=Path, help='Diretório 0700 da prévia Xephyr já aberta')
    parser.add_argument('--raiz', type=Path, default=REPO, help='Repositório com laboratório compilado')
    parser.add_argument('--nova-instancia', action='store_true',
                        help='Abrir outra instância na mesma Xephyr com diretório de trabalho próprio')
    parser.add_argument('--retomar-manifesto', type=Path,
                        help='Copiar projeto salvo e journal do addon indicado, sem alterar a origem')
    parser.add_argument('--recuperar-journal', type=Path,
                        help='Retomar cópia privada resgatada do journal; preservar o arquivo original')
    parser.add_argument('--supervisor', type=Path, help=argparse.SUPPRESS)
    parser.add_argument('--worker', type=Path, help=argparse.SUPPRESS)
    args = parser.parse_args(argv)
    os.umask(0o077)
    if args.worker:
        worker(args.worker)
    elif args.supervisor:
        supervisor(args.supervisor)
    elif args.sessao:
        return prepare(args)
    else:
        parser.error('Informe --sessao com a prévia existente')
    return 0


if __name__ == '__main__':
    try:
        raise SystemExit(main())
    except (OSError, RuntimeError, ValueError, subprocess.SubprocessError) as error:
        print('Laboratório não aberto: ' + str(error), file=sys.stderr)
        raise SystemExit(2)
