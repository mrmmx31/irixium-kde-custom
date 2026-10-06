# SPDX-FileCopyrightText: 2026 mrmmx31
# SPDX-License-Identifier: GPL-3.0-or-later
"""Check release authority and appearance equivalence; never change candidate evidence."""
from __future__ import annotations
import configparser
import hashlib
import json
from pathlib import Path
import xml.etree.ElementTree as ET


def digest(data: bytes) -> str:
    return hashlib.sha256(data).hexdigest()


def config_digest(raw: bytes) -> str:
    c = configparser.ConfigParser(interpolation=None, strict=True)
    c.optionxform = str
    c.read_string(raw.decode('utf-8'))
    data = {s: dict(c[s]) for s in c.sections()}
    data['%General'].pop('comment', None)  # descriptive release metadata, not style behavior
    return digest((json.dumps(data, indent=2, ensure_ascii=False, sort_keys=True)+'\n').encode())


def svg_digest(raw: bytes) -> str:
    if b'<!DOCTYPE' in raw.upper() or b'<!ENTITY' in raw.upper():
        raise ValueError('External SVG entities are not allowed.')
    def canonical(e):
        return [e.tag, sorted(e.attrib.items()), (e.text or '').strip(),
                [canonical(c) for c in e if c.tag.rsplit('}', 1)[-1] != 'title']]
    return digest(json.dumps(canonical(ET.fromstring(raw)), ensure_ascii=False,
                             separators=(',', ':')).encode())


def validate(repo: Path, policy: dict) -> dict:
    # Delayed import avoids a cycle with build_kvantum.py.
    import build_kvantum as B
    if (policy.get('theme') != 'IrixClassic' or policy.get('theme_version') != '0.7.1'
            or policy.get('channel') != 'stable' or policy.get('stable_approved') is not True
            or policy.get('pending_acceptance') != []):
        raise B.Failure('Registro estável inconsistente.')
    name = policy.get('promotion_file')
    if name != 'distribuicao/promocoes/0.7.1.json':
        raise B.Failure('Registro de promoção desconhecido.')
    raw = B.read_file(repo, name)
    if digest(raw) != policy.get('promotion_sha256'):
        raise B.Failure('O registro de promoção mudou.')
    p = B.document(raw)
    if (p.get('from_version') != '0.7.1-rc1' or p.get('to_version') != '0.7.1'
            or p.get('authorized_by') != 'mrmmx31' or p.get('authorization_date') != '2026-10-06'
            or p.get('channel') != 'stable' or p.get('stable_approved') is not True
            or p.get('candidate_acceptance', {}).get('status') != 'candidate_accepted_locally'
            or p['candidate_acceptance'].get('report_sha256') !=
            'ab4c16c5b74a9141a0119180f48c1d31081a8e261453b2f068a5d6fe56b1abd1'):
        raise B.Failure('Falta a promoção explícita da candidata aceita.')
    eq = p['equivalence']
    svg = B.read_file(repo, 'kvantum/IrixClassic/IrixClassic.svg')
    cfg = B.read_file(repo, 'kvantum/IrixClassic/IrixClassic.kvconfig')
    if svg_digest(svg) != eq.get('svg_without_title_sha256'):
        raise B.Failure('O desenho mudou desde o aceite. Publique mudanças em outra versão.')
    if config_digest(cfg) != eq.get('kvconfig_without_comment_sha256'):
        raise B.Failure('Uma configuração funcional mudou desde o aceite.')
    for rel, expected in eq['preserved_files'].items():
        if digest(B.read_file(repo, rel)) != expected:
            raise B.Failure('Arquivo aprovado modificado: '+rel)
    return {'stable_approved': True, 'appearance_equivalent': True,
            'candidate_report_sha256': p['candidate_acceptance']['report_sha256']}
