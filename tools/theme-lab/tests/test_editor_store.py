#!/usr/bin/python3
# SPDX-License-Identifier: GPL-3.0-or-later
"""Owned fixtures only: recovery accepts Unicode and rejects invalid journals."""
import copy
import hashlib
import json
import os
from pathlib import Path
import subprocess
import sys
import tempfile

binary=Path(sys.argv[1]).resolve(strict=True)
directory=Path(tempfile.mkdtemp(prefix='theme-lab-editor-store-',dir=tempfile.gettempdir()))
valid={'schema_version':1,'histories':{'recipe/gtk3/notes':{'entries':['','ação\nCafé — revisão.'],'position':1}}}
count=0

def check(data,accepted,mode=0o600):
    global count
    path=directory/f'case-{count}.json'
    path.write_bytes(data if isinstance(data,bytes) else json.dumps(data,ensure_ascii=False).encode())
    path.chmod(mode)
    before=hashlib.sha256(path.read_bytes()).hexdigest()
    result=subprocess.run([str(binary),str(path)],stdout=subprocess.PIPE,stderr=subprocess.PIPE)
    assert (result.returncode==0)==accepted,(result.returncode,result.stderr)
    assert hashlib.sha256(path.read_bytes()).hexdigest()==before
    count+=1
    return path

check(valid,True)
check({'schema_version':1,'histories':{'':{'entries':['sample'],'position':0}}},False)
for replacement in (-1,2,1.5,'1'):
    data=copy.deepcopy(valid);data['histories']['recipe/gtk3/notes']['position']=replacement;check(data,False)
data=copy.deepcopy(valid);data['histories']['recipe/gtk3/notes']['entries']=['bad\0text'];data['histories']['recipe/gtk3/notes']['position']=0;check(data,False)
check(b'{"schema_version":1,"histories":{"x":{"entries":["\xff"],"position":0}}}',False)
check(json.dumps(valid).encode()+b' trailing',False)
check(valid,False,0o644)
data=copy.deepcopy(valid);data['histories']['recipe/gtk3/notes']['entries']=['x']*129;check(data,False)
data=copy.deepcopy(valid);data['histories']['recipe/gtk3/notes']['entries']=['x'*65537];data['histories']['recipe/gtk3/notes']['position']=0;check(data,False)
# Visiting additional families must not turn existing Undo history unsavable.
for fields in (256, 258, 4097):
    data={'schema_version':1,'histories':{
        f'recipe/family/control/{i}/notes':{'entries':['','ação — rascunho\n'], 'position':1}
        for i in range(fields)}}
    path=check(data,True)
    result=subprocess.run([str(binary),str(path),'--checkpoint'],capture_output=True)
    assert result.returncode==0,result.stderr
    assert json.loads(path.read_text())==data, 'Checkpoint must preserve every history and position'
    assert path.stat().st_mode & 0o777 == 0o600
    count+=1
# A directory-sync failure after atomic rename is reported and remains dirty;
# the installed journal stays valid and no temporary file is orphaned.
failure=directory/'directory-sync-failure.json'
failure.write_text(json.dumps(valid,ensure_ascii=False),encoding='utf-8')
failure.chmod(0o600)
before=json.loads(failure.read_text(encoding='utf-8'))
result=subprocess.run([str(binary),str(failure),'--fail-directory-sync'],stdout=subprocess.PIPE,stderr=subprocess.PIPE)
assert result.returncode==1,result.stderr
assert json.loads(failure.read_text(encoding='utf-8'))==before
assert not list(directory.glob('directory-sync-failure.json.*'))
count+=1
# The byte bound still protects loading; rejected input remains unchanged.
check(b' '*(8*1024*1024+1),False)
target=check(valid,True);link=directory/'link.json';link.symlink_to(target)
assert subprocess.run([str(binary),str(link)],stdout=subprocess.PIPE,stderr=subprocess.PIPE).returncode==1
assert link.is_symlink()
print(f'Editor store: {count+1} checks; UTF-8 accepted, invalid files preserved.')
