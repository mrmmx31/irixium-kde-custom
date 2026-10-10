# SPDX-License-Identifier: GPL-3.0-or-later
"""Read and write Xcursor images without installing a theme or using X11."""
import struct
from pathlib import Path

IMAGE = 0xfffd0002


def read(path):
    data = Path(path).read_bytes()
    if len(data) < 16:
        raise ValueError('Xcursor truncado')
    magic, header, version, count = struct.unpack_from('<4I', data)
    if magic != 0x72756358 or header < 16 or header + count * 12 > len(data):
        raise ValueError('Cabeçalho Xcursor inválido')
    frames = []
    for i in range(count):
        kind, size, pos = struct.unpack_from('<3I', data, header + i * 12)
        if kind != IMAGE:
            continue
        if pos + 36 > len(data):
            raise ValueError('Imagem Xcursor truncada')
        h, t, subtype, v, w, height, x, y, delay = struct.unpack_from('<9I', data, pos)
        if h < 36 or t != IMAGE or subtype != size or not (0 < w <= 512 and 0 < height <= 512):
            raise ValueError('Dimensões Xcursor inválidas')
        if x >= w or y >= height or pos + h + w * height * 4 > len(data):
            raise ValueError('Hotspot ou pixels Xcursor inválidos')
        frames.append({'size': size, 'width': w, 'height': height,
                       'hotspot': (x, y), 'delay': delay,
                       'pixels': data[pos + h:pos + h + w * height * 4]})
    if not frames:
        raise ValueError('Xcursor sem imagens')
    return frames


def write(path, frames):
    pos = 16 + len(frames) * 12
    toc, chunks = [], []
    for f in frames:
        w, h = f['width'], f['height']
        x, y = f['hotspot']
        if len(f['pixels']) != w * h * 4 or not (0 <= x < w and 0 <= y < h):
            raise ValueError('Imagem ou hotspot inválido')
        toc.append(struct.pack('<3I', IMAGE, f['size'], pos))
        chunk = struct.pack('<9I', 36, IMAGE, f['size'], 1, w, h, x, y, f['delay']) + f['pixels']
        chunks.append(chunk)
        pos += len(chunk)
    Path(path).write_bytes(struct.pack('<4I', 0x72756358, 16, 0x10000, len(frames)) + b''.join(toc + chunks))
