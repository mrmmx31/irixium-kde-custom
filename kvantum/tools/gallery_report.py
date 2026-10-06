# SPDX-FileCopyrightText: 2026 mrmmx31
# SPDX-License-Identifier: GPL-3.0-or-later
"""Incremental JSON report for synthetic galleries, not application event policy."""
from __future__ import annotations
import json
import os
from pathlib import Path
import tempfile


class GalleryReport:
    def __init__(self, metadata, path=None):
        self.path = Path(path).expanduser().absolute() if path else None
        if self.path:
            if self.path.exists() or self.path.is_symlink():
                raise ValueError('O relatório de saída já existe. Escolha outro nome.')
            for p in (self.path.parent, *self.path.parent.parents):
                if p.is_symlink(): raise ValueError('Diretório de relatório simbólico recusado.')
            self.path.parent.mkdir(parents=True, exist_ok=True)
        self.doc = dict(metadata, status='running', current_stage='initializing',
                        results=[], input_trace=[], errors=[], completed=False)
        self.checkpoint()

    def checkpoint(self):
        if not self.path: return
        data = json.dumps(self.doc, ensure_ascii=False, indent=2)+'\n'
        fd, name = tempfile.mkstemp(prefix='.irix-report-', dir=self.path.parent)
        try:
            with os.fdopen(fd, 'w', encoding='utf-8') as stream:
                stream.write(data); stream.flush(); os.fsync(stream.fileno())
            os.replace(name, self.path)
        finally:
            if os.path.exists(name): os.unlink(name)

    def enter(self, name):
        self.doc['current_stage'] = name
        self.checkpoint()

    def check(self, name, passed):
        self.doc['results'].append({'test': name, 'passed': bool(passed),
                                    'stage': self.doc['current_stage']})
        self.checkpoint()

    def abort(self, exc):
        self.doc['errors'].append({'stage': self.doc['current_stage'],
                                   'type': type(exc).__name__, 'message': str(exc)})
        self.doc['status'] = 'interrupted'
        self.checkpoint()

    def finish(self, completed=True):
        self.doc['completed'] = bool(completed and not self.doc['errors'])
        if not self.doc['completed']:
            self.doc['status'] = 'interrupted'
        else:
            checks = self.doc['results']
            self.doc['status'] = 'passed' if checks and all(r['passed'] for r in checks) else 'failed'
        self.checkpoint()
        return 0 if self.doc['status'] == 'passed' else 1
