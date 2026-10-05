#!/usr/bin/env python3
# SPDX-FileCopyrightText: 2026 mrmmx31
# SPDX-License-Identifier: GPL-3.0-or-later
"""Opt-in KDE Qt Quick scrollbar input fix. Does not change any SVG/theme selection.

KDE's arrow MouseArea accepts the press; T.ScrollBar.pressed may stay false.
The old StyleItem binding only follows T.ScrollBar.pressed. Preserve native
handle events and additionally expose a held arrow from that MouseArea.
This correction affects the org.kde.desktop module, not only IrixClassic.
"""
from __future__ import annotations
import argparse
import difflib
import glob
import json
import os
from pathlib import Path
import re
import shutil
import signal
import subprocess
import sys
import tempfile
from theme_transaction import Change, Failure, Transaction, no_links, snapshot, decode

MARKER='IRIXCLASSIC_QTQUICK_ARROW_PRESS_V1'
PREFER_MARKER='# IRIXCLASSIC_QML_FILESYSTEM_V1: load the reviewed local QML, not the embedded qrc copy.'
# These are exact, unique code anchors, not a replacement of the whole KDE file.
REPLACEMENTS=(
('        id: mouseArea\n',
 '        id: mouseArea\n\n'
 '        // '+MARKER+' — input compatibility, no theme artwork.\n'
 '        property string irixPressedArrow: ""\n'),
('        onPressed: mouse => {\n',
 '        onPressed: mouse => {\n'
 '            style.activeControl = style.hitTest(mouse.x, mouse.y);\n'
 '            irixPressedArrow = mouse.button === Qt.LeftButton\n'
 '                && (style.activeControl === "up" || style.activeControl === "down")\n'
 '                ? style.activeControl : "";\n'),
('        onReleased: mouse => {\n',
 '        onReleased: mouse => {\n'
 '            irixPressedArrow = "";\n'),
('        onCanceled: buttonTimer.running = false;\n',
 '        onCanceled: {\n'
 '            irixPressedArrow = "";\n'
 '            buttonTimer.running = false;\n'
 '        }\n'),
('            sunken: controlRoot.pressed\n',
 '            sunken: controlRoot.pressed\n'
 '                || (mouseArea.pressed\n'
 '                    && (mouseArea.pressedButtons & Qt.LeftButton) !== 0\n'
 '                    && mouseArea.irixPressedArrow !== ""\n'
 '                    && activeControl === mouseArea.irixPressedArrow)\n'),
)


def patch_scrollbar(data: bytes) -> bytes:
    if b'\x00' in data or len(data)>100_000: raise Failure('Unexpected ScrollBar.qml.')
    text=data.decode('utf-8')
    if '\r' in text: raise Failure('Formato CRLF não revisado; nenhum arquivo foi alterado.')
    if MARKER in text:
        # Validate our exact patch before treating it as installed/idempotent.
        source=text
        for old,new in reversed(REPLACEMENTS):
            if source.count(new)!=1: raise Failure('Correção local foi editada; revisar antes de atualizar.')
            source=source.replace(new,old,1)
        if patch_scrollbar(source.encode())!=data: raise Failure('Patch local inconsistente.')
        return data
    required=('T.ScrollBar {','id: controlRoot','id: mouseArea','id: style',
              'acceptedButtons: Qt.LeftButton | Qt.MiddleButton','onExited: style.activeControl = "groove";',
              'style.activeControl === "down"','style.activeControl === "up"',
              'buttonTimer.running = true;','elementType: "scrollbar"')
    if not all(t in text for t in required):
        raise Failure('Componente KDE diferente do contrato revisado. Não há opção --force.')
    for old,new in REPLACEMENTS:
        if text.count(old)!=1:
            raise Failure('Âncora Qt Quick ausente/ambígua; o código pode já ter correção upstream. Nenhuma escrita.')
        text=text.replace(old,new,1)
    return text.encode('utf-8')


def patch_qmldir(data: bytes, directory: Path) -> bytes:
    text=data.decode('utf-8')
    if not re.search(r'^module\s+org\.kde\.desktop\s*$',text,re.M):
        raise Failure('O qmldir não é do módulo org.kde.desktop.')
    entries=re.findall(r'^[^\n]*?[ \t]+([^\s]+\.qml)[ \t]*$',text,re.M)
    if 'ScrollBar.qml' not in entries: raise Failure('qmldir não registra ScrollBar.qml.')
    # Removing prefer is safe only when the module's QML sources are installed.
    for name in entries:
        rel=Path(name)
        if rel.is_absolute() or '..' in rel.parts:raise Failure('Fonte QML externa no qmldir.')
        p=directory/rel;no_links(p)
        if not p.is_file():raise Failure('Fonte local ausente; não é seguro retirar prefer: '+name)
    preferences=re.findall(r'^prefer\s+([^\s]+)\s*$',text,re.M)
    if not preferences:return data
    if len(preferences)!=1 or preferences[0] not in (':/qt/qml/org/kde/desktop/','qrc:/qt/qml/org/kde/desktop/'):
        raise Failure('Preferência de carregamento QML não reconhecida.')
    return re.sub(r'^prefer[^\n]*$',PREFER_MARKER,text,flags=re.M).encode()


def allowed(path: Path, phase=1):
    return phase==1 and re.fullmatch(
        r'/usr/lib(?:64)?(?:/[A-Za-z0-9_-]+)?/qt6/qml/org/kde/desktop/(ScrollBar\.qml|qmldir)',str(path)) is not None


def discover(explicit=None):
    if explicit:
        files=[Path(explicit).expanduser().absolute()]
    else:
        files=[]
        for mask in ('/usr/lib/*/qt6/qml/org/kde/desktop/ScrollBar.qml',
                     '/usr/lib/qt6/qml/org/kde/desktop/ScrollBar.qml',
                     '/usr/lib64/qt6/qml/org/kde/desktop/ScrollBar.qml'):
            files.extend(Path(x) for x in glob.glob(mask))
        files=list(dict.fromkeys(files))
    if len(files)!=1:raise Failure('Nenhum módulo Qt Quick único encontrado. Use --qml-file com um caminho Qt 6 listado pelo sistema.')
    file=files[0];no_links(file)
    if not allowed(file) or file.name!='ScrollBar.qml' or not file.is_file():raise Failure('Caminho Qt Quick recusado.')
    return file


def make_plan(file: Path):
    info=snapshot(file);patched=patch_scrollbar(decode(info))
    qmldir=file.parent/'qmldir';qinfo=snapshot(qmldir)
    if not qinfo['exists']:raise Failure('qmldir ausente; não é possível confirmar o carregamento.')
    directory=patch_qmldir(decode(qinfo),file.parent)
    return [Change(file,patched,1,info['mode'],info), Change(qmldir,directory,1,qinfo['mode'],qinfo)]


def system_writer(entries):
    launcher=shutil.which('pkexec') or shutil.which('sudo')
    python=shutil.which('python3')
    if not launcher or not python:raise Failure('Necessários pkexec ou sudo e Python 3 para este reparo opcional.')
    here=Path(__file__).resolve().parent
    with tempfile.TemporaryDirectory(prefix='irixclassic-qtquick-') as tmp:
        root=Path(tmp)
        for name in ('qtquick_scrollbar_fix.py','theme_transaction.py','system_theme_writer.py'):
            shutil.copyfile(here/name,root/name)
        payload=root/'operation.json';payload.write_text(json.dumps(entries))
        result=subprocess.run([launcher,python,str(root/'qtquick_scrollbar_fix.py'),
                               '--system-json',str(payload)],check=False)
        if result.returncode:raise Failure('Autorização/cópia Qt Quick falhou: '+str(result.returncode))


def system_main(file):
    if os.geteuid()!=0:raise Failure('Auxiliar administrativo exige autorização.')
    from system_theme_writer import apply
    import fcntl
    no_links(file)
    entries=json.loads(file.read_text())
    if len(entries)>2:raise Failure('Lote deve conter apenas ScrollBar.qml e qmldir.')
    for e in entries:
        if not e['before'].get('exists') or not e['after'].get('exists'):
            raise Failure('Não é permitido criar/apagar fontes KDE.')
        if len(decode(e['after']))>100_000:raise Failure('Arquivo QML excessivo.')
    lock=Path('/run/lock/irixclassic-qtquick.lock');no_links(lock)
    with lock.open('a+b') as stream:
        fcntl.flock(stream,fcntl.LOCK_EX)
        apply(entries,validator=allowed)
    return 0


def main(argv=None):
    parser=argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--verificar',action='store_true');parser.add_argument('--diff',action='store_true')
    parser.add_argument('--restaurar',action='store_true');parser.add_argument('--recuperar',action='store_true')
    parser.add_argument('--qml-file',type=Path);parser.add_argument('--system-json',type=Path,help=argparse.SUPPRESS)
    a=parser.parse_args(argv)
    if a.system_json:return system_main(a.system_json)
    if a.diff:a.verificar=True  # A diff never writes system files.
    if os.geteuid()==0:raise Failure('Execute como usuário normal, sem sudo; a autorização ocorre somente na cópia.')
    if a.recuperar and not a.restaurar:raise Failure('--recuperar exige --restaurar.')
    state=Path(os.environ.get('XDG_STATE_HOME',str(Path.home()/'.local/state'))).expanduser()
    no_links(state)
    tx=Transaction(state/'irixclassic-qtquick-press',system_writer,allowed)
    print('Escopo: integração org.kde.desktop/Qt Quick. Afeta os temas que usam esse componente; não altera SVGs.')
    def run():
        if a.restaurar:tx.restore(a.recuperar,a.verificar);return
        file=discover(a.qml_file);changes=make_plan(file)
        if a.diff:
            for c in changes:
                old=decode(c.expected).decode();new=c.data.decode()
                print(''.join(difflib.unified_diff(old.splitlines(True),new.splitlines(True),
                      fromfile=str(c.path),tofile=str(c.path))),end='')
        tx.install(changes,a.verificar)
        if not a.verificar:print('Reabra os aplicativos Qt Quick; saia e entre na sessão para recarregar componentes residentes. Nenhum processo foi reiniciado.')
    if a.verificar:run()
    else:
        with tx.locked():run()
    return 0

if __name__=='__main__':
    def stop(*_):raise KeyboardInterrupt()
    signal.signal(signal.SIGTERM,stop)
    try:sys.exit(main())
    except (Failure,OSError,ValueError,KeyError,TypeError) as exc:
        print('ERRO:',exc,file=sys.stderr);sys.exit(1)
    except KeyboardInterrupt:sys.exit(130)
