#!/usr/bin/python3
# SPDX-License-Identifier: GPL-3.0-or-later
"""Check continuity in existing native button captures without repeating input.

The fixture test_arrow_button_states_native places a 2px-bordered button at
(30,30). Expected KDE colours are independently checked at edge midpoints by
that test. Here both straight strips must agree along their length. CSS corner
joins and glyphs are deliberately excluded; this is not a historical proof.
"""
import json
from pathlib import Path
import sys
from PIL import Image


def verify(root):
    rows=[]
    for case in sorted(root.glob('*/NATIVE.json')):
        data=json.loads(case.read_text())
        for phase,detail in data['details'].items():
            image=Image.open(case.parent/(phase+'.png')).convert('RGB')
            width,height=detail['allocation'];x=y=30
            differences=[];count=0
            for offset in (0,1):
                edges=[[(x+i,y+offset) for i in range(2,width-2)],
                       [(x+width-1-offset,y+i) for i in range(2,height-2)],
                       [(x+i,y+height-1-offset) for i in range(2,width-2)],
                       [(x+offset,y+i) for i in range(2,height-2)]]
                for edge in edges:
                    if not edge:raise ValueError('Fixture border has no straight segment')
                    reference=image.getpixel(edge[len(edge)//2])
                    for point in edge:
                        count+=1
                        if max(abs(a-b) for a,b in zip(reference,image.getpixel(point)))>1:
                            differences.append(point)
            rows.append({'case':case.parent.name,'phase':phase,
                         'pixels':count,'differences':differences})
    if not rows:raise ValueError('No native fixture captures')
    return {'passed':all(not r['differences'] for r in rows),
            'scope':'Continuity of both straight border strips; CSS joins/corners and glyph excluded',
            'phases':len(rows),'pixels':sum(r['pixels'] for r in rows),
            'failures':[r for r in rows if r['differences']]}


if __name__=='__main__':
    result=verify(Path(sys.argv[1]))
    print(json.dumps(result,indent=2))
    raise SystemExit(int(not result['passed']))
