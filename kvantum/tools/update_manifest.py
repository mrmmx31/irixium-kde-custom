#!/usr/bin/env python3
# SPDX-License-Identifier: GPL-3.0-or-later
from pathlib import Path
import hashlib
import json
root=Path(__file__).resolve().parent.parent/'IrixClassic'
files=['IrixClassic.kvconfig','IrixClassic.svg','LICENSE','ORIGEM.json','README.md']
manifest={'version':'0.1.0-rc1','files':{name:hashlib.sha256((root/name).read_bytes()).hexdigest() for name in files}}
(root/'MANIFEST.json').write_text(json.dumps(manifest,indent=2)+'\n',encoding='utf-8')
