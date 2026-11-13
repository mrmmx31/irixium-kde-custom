#!/usr/bin/env python3
# SPDX-License-Identifier: GPL-3.0-or-later
"""Check cursor aliases, all frames, sizes, hotspots and the committed manifest."""
import hashlib
import json
from pathlib import Path
from xcursor import read

REQUIRED = ('default up-arrow crosshair wait text vertical-text pointer help progress '
            'context-menu cell all-scroll grab grabbing copy alias move no-drop not-allowed '
            'ns-resize ew-resize nesw-resize nwse-resize n-resize s-resize e-resize w-resize '
            'ne-resize nw-resize se-resize sw-resize col-resize row-resize zoom-in zoom-out').split()
SIZES = {24, 32, 48, 64, 96}


def audit_theme(folder):
    folder = Path(folder)
    errors, animations, checked = [], [], 0
    payload = folder/'cursors'
    if not (folder/'index.theme').is_file() or not payload.is_dir():
        return {'theme': folder.name, 'errors': [str(folder)+': tema ausente'], 'entries': 0}
    for name in REQUIRED:
        if not (payload/name).is_file():
            errors.append(folder.name+': cursor ausente '+name)
    for p in sorted(payload.iterdir()):
        try:
            if not p.resolve(strict=True).is_relative_to(payload.resolve()):
                raise ValueError('alias externo')
            frames = read(p)
            if {f['size'] for f in frames} != SIZES:
                raise ValueError('tamanhos incompletos')
            if p.is_symlink():
                continue
            checked += 1
            groups = [[f for f in frames if f['size']==s] for s in sorted(SIZES)]
            if any(len(g)>1 for g in groups):
                if any(len(g)!=8 or any(f['delay']!=125 for f in g) for g in groups):
                    raise ValueError('animação incoerente')
                animations.append(p.name)
        except (OSError, ValueError) as exc:
            errors.append(folder.name+'/'+p.name+': '+str(exc))
    if (payload/'wait').is_file() and (payload/'progress').is_file():
        if (payload/'wait').read_bytes() == (payload/'progress').read_bytes():
            errors.append(folder.name+': espera e progresso idênticos')
    manifest = folder/'MANIFEST.json'
    if manifest.is_file():
        expected = json.loads(manifest.read_text())['cursors']
        actual = {p.name: ('link:'+p.readlink().as_posix() if p.is_symlink()
                          else hashlib.sha256(p.read_bytes()).hexdigest()) for p in payload.iterdir()}
        if expected != actual:
            errors.append(folder.name+': manifesto divergente')
    else:
        errors.append(folder.name+': manifesto ausente')
    return {'theme': folder.name, 'entries': len(list(payload.iterdir())), 'artworks': checked,
            'sizes': sorted(SIZES), 'animated': animations, 'errors': errors}


if __name__ == '__main__':
    root = Path(__file__).resolve().parents[1]
    reports = [audit_theme(root/name) for name in ('sgi', 'SGI-Classic', 'SGI-Irixium')]
    print(json.dumps(reports, ensure_ascii=False, indent=2))
    raise SystemExit(any(r['errors'] for r in reports))
