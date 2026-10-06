#!/usr/bin/env python3
"""Atualiza o manifesto após uma edição intencional do código-fonte do pacote."""
import hashlib
import json
from pathlib import Path
root=Path(__file__).resolve().parent.parent
package=root/'package'
paths=sorted(package.rglob('*'))
if any(p.is_symlink() for p in paths):raise SystemExit('Links simbólicos não são aceitos no pacote.')
version=json.loads((package/'metadata.json').read_text())['KPlugin']['Version']
data={'version':version,'package':{p.relative_to(package).as_posix():hashlib.sha256(p.read_bytes()).hexdigest()
                                for p in paths if p.is_file()}}
(root/'MANIFEST.json').write_text(json.dumps(data,ensure_ascii=False,indent=2)+'\n',encoding='utf-8')
print('Manifesto atualizado. Execute os testes antes de distribuir a edição.')
