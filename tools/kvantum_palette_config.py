# SPDX-License-Identifier: GPL-3.0-or-later
"""Encode native Qt startup colors in a generated Kvantum configuration.

The Kvantum backend unconditionally initializes Base and AlternateBase and
inherits a fixed Shadow unless overridden. Keep the remaining palette roles
native by suppressing explicit color overrides. The backend cannot encode
separate disabled Base/AlternateBase/Shadow values; report those limits.
"""
from __future__ import annotations
import hashlib
import re

_FIELDS = {
    'base.color': ('Active', 'Base'),
    'inactive.base.color': ('Inactive', 'Base'),
    'alt.base.color': ('Active', 'AlternateBase'),
    'inactive.alt.base.color': ('Inactive', 'AlternateBase'),
    'shadow.color': ('Active', 'Shadow'),
}
_COLOR = re.compile(r'#[0-9a-fA-F]{6}\Z')
_ASSIGNMENT = re.compile(r'^(\s*)([^=\r\n]+?)(\s*=\s*)([^\r\n]*)(\r?\n|\r|)$')


def _color(palette, group, role):
    value = palette.get(group, {}).get(role) if isinstance(palette, dict) else None
    if not isinstance(value, str) or not _COLOR.fullmatch(value):
        raise ValueError('Missing or invalid native Qt color: ' + group + '/' + role)
    return value.lower()


def adapt_config(contents: bytes, *, native_qt_palette: dict):
    """Return configuration bytes and an explicit backend capability report.

    ``native_qt_palette`` must be the actual KDE QGuiApplication palette,
    grouped by Active, Inactive and Disabled. This helper does not substitute
    GTK colors for Qt roles or derive AlternateBase/disabled effects itself.
    """
    if not isinstance(contents, bytes) or len(contents) > 1024 * 1024:
        raise ValueError('Invalid Kvantum configuration bytes')
    replacements = {key: _color(native_qt_palette, *role) for key, role in _FIELDS.items()}
    if _color(native_qt_palette, 'Inactive', 'Shadow') != replacements['shadow.color']:
        raise ValueError('Kvantum cannot encode different Active/Inactive Shadow colors')
    limitations = []
    for role, key in (('Base', 'base.color'), ('AlternateBase', 'alt.base.color'), ('Shadow', 'shadow.color')):
        expected = _color(native_qt_palette, 'Disabled', role)
        encoded = replacements[key]
        if expected != encoded:
            limitations.append({'group': 'Disabled', 'role': role,
                'native': expected, 'encoded': encoded,
                'reason': 'Kvantum uses the same configuration field as Active'})

    text = contents.decode('utf-8')
    lines = text.splitlines(keepends=True)
    newline = '\r\n' if '\r\n' in text else '\n'
    section = None
    changed = {}
    output = []
    seen = set()
    general_count = 0
    insert_at = None
    inactiveness = []
    for line in lines:
        stripped = line.strip()
        if stripped.startswith(('#', ';')):
            output.append(line)
            continue
        if stripped.startswith('['):
            if not stripped.endswith(']'):
                raise ValueError('Malformed Kvantum section')
            if section == 'GeneralColors':
                insert_at = len(output)
            section = stripped[1:-1]
            if section == 'GeneralColors':
                general_count += 1
                if general_count > 1:
                    raise ValueError('Duplicate GeneralColors section')
            output.append(line)
            continue
        match = _ASSIGNMENT.match(line)
        if match:
            prefix, raw_key, separator, value, ending = match.groups()
            key = raw_key.strip()
            if section in ('General', '%General') and key == 'no_inactiveness':
                if value.strip() not in ('true', 'false') or inactiveness:
                    raise ValueError('Invalid or duplicate no_inactiveness option')
                inactiveness.append(value.strip())
                output.append(prefix + raw_key + separator + 'false' + ending)
                continue
            if key.endswith('.color'):
                if section != 'GeneralColors' and not key.startswith('text.'):
                    raise ValueError('Unclassified configuration color: ' + str(section) + '/' + key)
                identity = (section, key)
                if identity in seen:
                    raise ValueError('Duplicate Kvantum color field: ' + str(section) + '/' + key)
                seen.add(identity)
                color = replacements.get(key, 'none') if section == 'GeneralColors' else 'none'
                output.append(prefix + raw_key + separator + color + ending)
                changed.setdefault(section, []).append(key)
                continue
        output.append(line)
    if not general_count:
        raise ValueError('GeneralColors section required')
    if section == 'GeneralColors':
        insert_at = len(output)
    if insert_at is None:
        raise ValueError('GeneralColors insertion location missing')
    missing = [key for key in _FIELDS if ('GeneralColors', key) not in seen]
    additions = [key + '=' + replacements[key] + newline for key in missing]
    # Do not merge an inserted key with a last line lacking its newline.
    if additions and insert_at and not output[insert_at - 1].endswith(('\r', '\n')):
        additions.insert(0, newline)
    output[insert_at:insert_at] = additions
    result = ''.join(output).encode('utf-8')
    return result, {'colorCount': sum(map(len, changed.values())),
        'colorsBySection': changed, 'insertedFields': missing,
        'nativeFields': replacements,
        'inactivenessOption': {'source': inactiveness, 'generated': 'false'},
        'backendLimitations': limitations,
        'scope': 'Native Active/Inactive palette startup; disabled Base/AlternateBase/Shadow limitations are explicit',
        'sourceSha256': hashlib.sha256(contents).hexdigest(),
        'outputSha256': hashlib.sha256(result).hexdigest()}
