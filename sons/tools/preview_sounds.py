#!/usr/bin/env python3
# SPDX-FileCopyrightText: 2026 mrmmx31
# SPDX-License-Identifier: GPL-3.0-or-later
"""Explicit libcanberra playback. No change to volume, mute, theme or applications."""
from __future__ import annotations
import argparse
import ctypes as C
import ctypes.util
import json
import sys
import threading
from irix_sounds import Failure, THEME, catalog, locations, validate_theme


def play(event: str, direct_file: str | None = None) -> dict:
    name = ctypes.util.find_library('canberra')
    if not name: raise Failure('libcanberra ausente. No Debian/KDE: pacote libcanberra0.')
    lib = C.CDLL(name)
    ptr = C.c_void_p
    lib.ca_context_create.argtypes = [C.POINTER(ptr)]
    lib.ca_context_destroy.argtypes = [ptr]
    lib.ca_context_cancel.argtypes = [ptr, C.c_uint32]
    lib.ca_proplist_create.argtypes = [C.POINTER(ptr)]
    lib.ca_proplist_sets.argtypes = [ptr, C.c_char_p, C.c_char_p]
    lib.ca_proplist_destroy.argtypes = [ptr]
    lib.ca_strerror.argtypes = [C.c_int]; lib.ca_strerror.restype = C.c_char_p
    callback_type = C.CFUNCTYPE(None, ptr, C.c_uint32, C.c_int, ptr)
    lib.ca_context_play_full.argtypes = [ptr, C.c_uint32, ptr, callback_type, ptr]
    context, props = ptr(), ptr()
    done = threading.Event(); completion = []
    @callback_type
    def finished(_context, _id, error, _data):
        completion.append(error); done.set()
    def check(result):
        if result < 0:
            raise Failure('libcanberra: ' + lib.ca_strerror(result).decode('utf-8', 'replace'))
    check(lib.ca_context_create(C.byref(context)))
    try:
        check(lib.ca_proplist_create(C.byref(props)))
        settings = {
            'application.name': 'IrixClassic Sounds Preview',
            'application.id': 'org.mrmmx31.IrixClassicSounds',
            'canberra.cache-control': 'never',
            'media.role': 'event',
        }
        if direct_file:
            settings['media.filename'] = direct_file
        else:
            settings['event.id'] = event
            settings['canberra.xdg-theme.name'] = THEME
        for key, value in settings.items():
            check(lib.ca_proplist_sets(props, key.encode(), value.encode()))
        check(lib.ca_context_play_full(context, 1, props, finished, None))
        if not done.wait(15):
            lib.ca_context_cancel(context, 1); done.wait(2)
            raise Failure('Tempo de reprodução excedido; teste cancelado.')
        check(completion[0])
        return {'event': event, 'mode': 'direct_wav' if direct_file else 'theme_lookup',
                'backend_completed': True,
                'audible_confirmation': 'Confirmar por audição; retorno do backend não comprova volume audível.'}
    finally:
        if props: lib.ca_proplist_destroy(props)
        if context: lib.ca_context_destroy(context)


def main():
    p = argparse.ArgumentParser(description=__doc__)
    p.add_argument('--evento', default='theme-demo')
    p.add_argument('--listar', action='store_true')
    p.add_argument('--direto', action='store_true', help='Toca WAV por caminho, sem lookup do tema.')
    args = p.parse_args()
    c = catalog(); events = {e: s for s in c['sounds'] for e in s['events']}
    if args.listar:
        for e, s in events.items(): print(e + ' <- ' + s['original_filename'])
        return 0
    if args.evento not in events: p.error('Evento não mapeado; use --listar.')
    _, dest, _, _ = locations(); validate_theme(dest, c)
    filename = str(dest / 'stereo' / (args.evento + '.wav')) if args.direto else None
    print(json.dumps(play(args.evento, filename), ensure_ascii=False, indent=2))
    return 0

if __name__ == '__main__':
    try: sys.exit(main())
    except (Failure, OSError, ValueError, KeyError) as e:
        print('ERRO:', e, file=sys.stderr); sys.exit(1)
