# SPDX-FileCopyrightText: 2026 mrmmx31
# SPDX-License-Identifier: GPL-3.0-or-later
"""Recolor only the original DomainOS Motif reconstruction, preserving geometry.

Canonical source bytes must match the deterministic public generator. New or
edited SVGs are rejected before the caller touches a user theme. Native Qt
startup colors use the same explicit backend limits as the other two families.
"""
from __future__ import annotations
from functools import lru_cache
import hashlib
import json
import xml.etree.ElementTree as ET
from pathlib import Path

import domainos_motif_art as art
from kvantum_palette_config import adapt_config


@lru_cache(maxsize=1)
def scrollbar_recipe():
    """Read and validate the shared SR10.4 metric contract beside this helper."""
    path = Path(__file__).with_name('domainos_scrollbar_rules.json')
    rules = json.loads(path.read_text(encoding='utf-8'))
    geometry = rules.get('geometry', {})
    keys = ('bar_px', 'shadow_px', 'arrow_px', 'thumb_cross_px')
    if (rules.get('schema_version') != 1 or geometry.get('unit') != 'native_pixel' or
            geometry.get('origin') != 'measurement_vm' or
            any(type(geometry.get(key)) is not int for key in keys) or
            geometry['bar_px'] != geometry['arrow_px'] + 2 * geometry['shadow_px'] or
            geometry['thumb_cross_px'] != geometry['arrow_px']):
        raise ValueError('DomainOS scrollbar metric contract is invalid')
    for direction in ('up', 'down', 'left', 'right'):
        for state in art.STATES:
            cell = art.kvantum_scrollbar_stepper(
                state, direction, **{key: geometry[key] for key in ('bar_px', 'shadow_px', 'arrow_px')})
            glyph = art.kvantum_scrollbar_triangle(state, direction)
            if ((len(cell), len(cell[0])) != (geometry['bar_px'], geometry['bar_px']) or
                    (len(glyph), len(glyph[0])) != (geometry['arrow_px'], geometry['arrow_px'])):
                raise ValueError('Kvantum artwork does not match the shared metric contract')
    return {key: geometry[key] for key in ('bar_px', 'shadow_px', 'arrow_px')}, hashlib.sha256(path.read_bytes()).hexdigest()


@lru_cache(maxsize=1)
def sources():
    geometry, _ = scrollbar_recipe()
    return art.svg(scrollbar_geometry=geometry), art.kvconfig(
        geometry['bar_px'], geometry['shadow_px'])


def render(svg: bytes, kvconfig: bytes, palette: dict, *, native_qt_palette: dict):
    expected_svg, expected_config = sources()
    if svg != expected_svg or kvconfig != expected_config:
        raise ValueError('DomainOS canonical source changed; recoloring refused')
    if not isinstance(palette, dict): raise ValueError('Native GTK color export required')
    # The semantic drawing declares every native role it consumes. Missing
    # inactive/disabled inputs are never silently replaced by Active colors.
    for names in art.ROLES.values():
        for name in names: art._rgb(palette.get(name))
    geometry, contract_hash = scrollbar_recipe()
    output = art.svg(palette, scrollbar_geometry=geometry)
    before, after = art.geometry_sha(svg), art.geometry_sha(output)
    if before != after: raise ValueError('Motif geometry changed during recoloring')
    settings, config_report = adapt_config(kvconfig, native_qt_palette=native_qt_palette)
    elements = ET.fromstring(output)
    groups = elements.findall('{*}g')
    rectangles = elements.findall('.//{*}rect')
    bounds = sum(node.get('fill-opacity') == '0' for node in rectangles)
    return output, settings, {
        'groups': len(groups), 'opaqueRects': len(rectangles)-bounds,
        'transparentBoundsPreserved': bounds, 'geometryUnchanged': True,
        'geometrySha256': after, 'roles': sorted({name for names in art.ROLES.values() for name in names}),
        'scrollbarGeometry': geometry,
        'scrollbarContractSha256': contract_hash,
        'sourceSvgSha256': hashlib.sha256(svg).hexdigest(), 'svgSha256': hashlib.sha256(output).hexdigest(),
        'config': config_report, 'artwork': 'Original SR10.4 Motif control reconstruction; no HP assets',
        'limits': ['KDE has one application palette rather than eight per-client VUE color sets',
                   'Kvantum disabled push buttons may use normal artwork with native opacity',
                   'Disabled Base/AlternateBase/Shadow startup limits are reported in config'],
    }
