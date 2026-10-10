# SPDX-License-Identifier: GPL-3.0-or-later
"""Recover simplified closed outlines from the preserved two-colour artwork.

Render outlines at the requested resolution; never blur an enlarged bitmap.
The source font recreation is still the reference, not an original SGI dump.
"""
from PIL import Image, ImageDraw


def simplify(points, tolerance=0.6):
    """Ramer-Douglas-Peucker, split closed loops at their furthest vertex."""
    def segment(points):
        if len(points) <= 2:
            return points
        a, b = points[0], points[-1]
        dx, dy = b[0]-a[0], b[1]-a[1]
        length = dx*dx+dy*dy
        def distance(p):
            t = max(0, min(1, ((p[0]-a[0])*dx+(p[1]-a[1])*dy)/length)) if length else 0
            return ((p[0]-a[0]-t*dx)**2+(p[1]-a[1]-t*dy)**2)**0.5
        index = max(range(1, len(points)-1), key=lambda i: distance(points[i]))
        if distance(points[index]) <= tolerance:
            return [a, b]
        return segment(points[:index+1])[:-1]+segment(points[index:])
    split = max(range(1, len(points)), key=lambda i: (points[i][0]-points[0][0])**2+(points[i][1]-points[0][1])**2)
    result = segment(points[:split+1])[:-1]+segment(points[split:]+[points[0]])[:-1]
    return result if len(result) >= 3 else points


def outlines(mask):
    """Trace oriented exposed pixel edges, keeping holes and disconnected dots."""
    pixels = set(mask)
    edges = set()
    for x, y in pixels:
        for neighbour, a, b in (
            ((x,y-1),(x,y),(x+1,y)), ((x+1,y),(x+1,y),(x+1,y+1)),
            ((x,y+1),(x+1,y+1),(x,y+1)), ((x-1,y),(x,y+1),(x,y))):
            if neighbour not in pixels:
                edges.add((a,b))
    loops = []
    while edges:
        start, following = min(edges)
        points = [start]
        edges.remove((start,following))
        previous, current = start, following
        while current != start:
            points.append(current)
            candidates = [b for a,b in edges if a == current]
            # At diagonally touching pixels turn right to retain separate islands.
            dx,dy = current[0]-previous[0],current[1]-previous[1]
            directions = [(dx,dy),(-dy,dx),(-dx,-dy),(dy,-dx)]
            order = {directions[1]:0,directions[0]:1,directions[3]:2,directions[2]:3}
            following = min(candidates, key=lambda b: order[(b[0]-current[0],b[1]-current[1])])
            edges.remove((current,following))
            previous,current = current,following
        area = sum(a[0]*b[1]-b[0]*a[1] for a,b in zip(points,points[1:]+points[:1]))/2
        loops.append((area, simplify(points) if abs(area)>4 else points))
    return sorted(loops, key=lambda item: -abs(item[0]))


def render(source, size, smooth=False):
    # Discard faint compression fringe pixels in the old files, and recover
    # straight colours from their premultiplied channels before tracing.
    source = source.copy()
    source.putdata([(*(255 if c*255/a>=128 else 0 for c in (r,g,b)),255)
                    if a>=128 else (0,0,0,0) for r,g,b,a in source.getdata()])
    factor = size/32
    dimensions = tuple(round(v*factor) for v in source.size)
    sample = 4
    scale = factor*sample
    result = Image.new('RGBA', tuple(v*sample for v in dimensions))
    values = source.load()
    # White silhouette beneath the coloured regions avoids seams between fills.
    colours = sorted({p[:3] for p in source.getdata() if p[3]}, reverse=True)
    for colour in colours:
        mask = [(x,y) for y in range(source.height) for x in range(source.width)
                if values[x,y][3] and (colour == (255,255,255) or values[x,y][:3] == colour)]
        layer = Image.new('RGBA', result.size)
        drawing = ImageDraw.Draw(layer)
        for area, points in outlines(mask):
            drawing.polygon([(round(x*scale),round(y*scale)) for x,y in points],
                            fill=(*colour,255) if area>0 else (0,0,0,0))
        result.alpha_composite(layer)
    result = result.resize(dimensions, Image.Resampling.LANCZOS if smooth else Image.Resampling.BOX)
    if not smooth:
        result.putdata([(*min(colours, key=lambda c: sum((c[i]-p[i])**2 for i in range(3))),255)
                        if p[3]>=128 else (0,0,0,0) for p in result.getdata()])
    return result


def premultiply(image):
    """Xcursor pixels are premultiplied ARGB, unlike Pillow's straight RGBA."""
    result = image.copy()
    result.putdata([(round(r*a/255),round(g*a/255),round(b*a/255),a)
                    for r,g,b,a in image.getdata()])
    return result
