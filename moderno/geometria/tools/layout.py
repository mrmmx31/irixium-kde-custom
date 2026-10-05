# SPDX-FileCopyrightText: 2026 mrmmx31
# SPDX-License-Identifier: GPL-3.0-or-later
"""Only the [Layout] geometry is changed. Preserve all other bytes and keys."""
from __future__ import annotations
import re

VALUES = {
    'TitleHeight': '26',
    'ButtonSpacing': '6',
    'ButtonMarginTop': '2',
    'ButtonMarginTopMaximized': '2',
    'TitleEdgeTop': '7',
    'TitleEdgeBottom': '1',
    'TitleEdgeLeft': '9',
    'TitleEdgeRight': '9',
    'TitleEdgeTopMaximized': '4',
    'TitleEdgeBottomMaximized': '4',
    'TitleEdgeLeftMaximized': '6',
    'TitleEdgeRightMaximized': '6',
    'TitleBorderLeft': '12',
    'TitleBorderRight': '12',
}


def update_layout(data: bytes) -> bytes:
    text = data.decode('utf-8')
    eol = '\r\n' if '\r\n' in text else '\n'
    lines = text.splitlines(keepends=True)
    starts = [i for i, line in enumerate(lines) if line.strip() == '[Layout]']
    if len(starts) != 1:
        raise ValueError('É necessária exatamente uma seção [Layout] no Irixiumrc.')
    start = starts[0] + 1
    end = next((i for i in range(start, len(lines)) if re.match(r'^\s*\[', lines[i])), len(lines))
    found = {}
    for i in range(start, end):
        m = re.match(r'^\s*([A-Za-z][A-Za-z0-9]*)\s*=\s*([^\r\n]*?)(?:\r?\n)?$', lines[i])
        if m:
            key = m.group(1)
            if key in found:
                raise ValueError('Chave duplicada em [Layout]: ' + key)
            found[key] = (i, m.group(2).strip())
    for key in ('ButtonWidth', 'ButtonHeight'):
        if key not in found or found[key][1] != '22':
            raise ValueError('Este perfil preserva botões 22×22. Dimensão local diferente em ' + key
                             + '; nenhuma alteração foi aplicada.')
    for key, (_, value) in found.items():
        if key.startswith('ButtonWidth') and value != '22':
            raise ValueError('Largura específica diferente do perfil 22×22: ' + key)
    if found.get('TitleHeight', (None, None))[1] not in ('34', '26'):
        raise ValueError('Altura de título personalizada; revise o perfil antes de aplicar.')
    for key, value in VALUES.items():
        if key in found:
            i, old = found[key]
            if old == value:
                continue
            m = re.match(r'^(\s*' + key + r'\s*=\s*)', lines[i])
            lines[i] = m.group(1) + value + eol
    missing = [key for key in VALUES if key not in found]
    if missing:
        if end and not lines[end - 1].endswith(('\n', '\r')):
            lines[end - 1] += eol
        lines[end:end] = [f'{key}={VALUES[key]}{eol}' for key in missing]
    return ''.join(lines).encode('utf-8')
