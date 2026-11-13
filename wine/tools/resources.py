# SPDX-FileCopyrightText: 2026 mrmmx31
# SPDX-License-Identifier: GPL-3.0-or-later
"""Deterministic, resource-only PE32 container for Wine .msstyles.

No executable code, imports, compiler or third-party theme is needed.
Resource-only styles can be read by either 32-bit or 64-bit Wine.
"""
import struct


def aligned(value, alignment):
    return (value + alignment - 1) // alignment * alignment


def theme_pe(resources):
    tree = {}
    for kind, name, data in resources:
        if name in tree.setdefault(kind, {}):
            raise ValueError('Duplicate resource')
        tree[kind][name] = {0x409: bytes(data)}
    buffer = bytearray()
    leaves = []

    def reserve(length, alignment=4):
        buffer.extend(b'\0' * (aligned(len(buffer), alignment) - len(buffer)))
        start = len(buffer)
        buffer.extend(b'\0' * length)
        return start

    def directory(node):
        names = sorted(k for k in node if isinstance(k, str))
        numbers = sorted(k for k in node if isinstance(k, int))
        keys = names + numbers
        offset = reserve(16 + 8 * len(keys))
        struct.pack_into('<IIHHHH', buffer, offset, 0, 0, 0, 0, len(names), len(numbers))
        for index, key in enumerate(keys):
            if isinstance(key, str):
                encoded = key.encode('utf-16le')
                name_offset = reserve(2 + len(encoded), 2)
                struct.pack_into('<H', buffer, name_offset, len(encoded) // 2)
                buffer[name_offset+2:name_offset+2+len(encoded)] = encoded
                name_id = name_offset | 0x80000000
            else:
                name_id = key
            value = node[key]
            if isinstance(value, dict):
                target = directory(value) | 0x80000000
            else:
                target = reserve(16)
                leaves.append((target, value))
            struct.pack_into('<II', buffer, offset + 16 + index * 8, name_id, target)
        return offset

    if directory(tree) != 0:
        raise ValueError('Unexpected root offset')
    for entry, data in leaves:
        offset = reserve(len(data))
        buffer[offset:offset+len(data)] = data
        struct.pack_into('<IIII', buffer, entry, 0x1000 + offset, len(data), 0, 0)
    size = len(buffer)
    raw_size = aligned(size, 0x200)
    buffer.extend(b'\0' * (raw_size - size))
    header = bytearray(0x200)
    header[:2] = b'MZ'
    struct.pack_into('<I', header, 0x3c, 0x80)
    header[0x80:0x84] = b'PE\0\0'
    struct.pack_into('<HHIIIHH', header, 0x84, 0x14c, 1, 0, 0, 0, 224, 0x2102)
    opt = 0x98
    struct.pack_into('<H', header, opt, 0x10b)
    struct.pack_into('<I', header, opt+8, raw_size)
    struct.pack_into('<IIIIII', header, opt+16, 0, 0, 0x1000, 0x10000000, 0x1000, 0x200)
    struct.pack_into('<HHHHHH', header, opt+40, 4, 0, 0, 0, 4, 0)
    struct.pack_into('<II', header, opt+56, aligned(0x1000+size, 0x1000), 0x200)
    struct.pack_into('<HH', header, opt+68, 2, 0)
    struct.pack_into('<IIIII', header, opt+72, 0x100000, 0x1000, 0x100000, 0x1000, 0)
    struct.pack_into('<I', header, opt+92, 16)
    struct.pack_into('<II', header, opt+96+2*8, 0x1000, size)
    section = opt + 224
    header[section:section+8] = b'.rsrc\0\0\0'
    struct.pack_into('<IIII', header, section+8, size, 0x1000, raw_size, 0x200)
    struct.pack_into('<I', header, section+36, 0x40000040)
    return bytes(header + buffer)
