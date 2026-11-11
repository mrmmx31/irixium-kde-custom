# SPDX-License-Identifier: GPL-3.0-or-later
"""Bounded private event persistence shared by native GTK2/GTK3/GTK4 scenes."""
import datetime as dt
import json
import os
from pathlib import Path
import re
import tempfile
import time
import uuid

class EventWriter:
    """Owned 0700 directory, unique 0600 atomic events; no project writes."""
    def __init__(self, directory, root, family='gtk3', backend_api=None, instance_id=None):
        if family not in ('gtk2', 'gtk3', 'gtk4'):
            raise ValueError('Família de evento não suportada.')
        if backend_api is None:
            import backend as backend_api
        if instance_id is not None and (not isinstance(instance_id, str) or
                not re.fullmatch(r'[0-9a-f]{32}', instance_id)):
            raise ValueError('Identidade da prévia inválida.')
        self.instance_id = instance_id
        self.backend, self.family = backend_api, family
        self.directory = self.backend.private_output(directory, root)

    def emit(self, action, control, project_hash, **fields):
        if type(control) is not int or not 0 <= control < len(self.backend.CONTROLS):
            raise ValueError('Índice de controle inválido.')
        if not isinstance(project_hash, str) or not re.fullmatch(r'[0-9a-f]{64}', project_hash):
            raise ValueError('Hash da proposta inválido.')
        reserved = {'schema_version','kind','event_id','family','action','control_id','control_index','project_sha256','emitted_at','preview_instance'}
        if reserved.intersection(fields):
            raise ValueError('Campo reservado de evento não pode ser substituído.')
        if action not in ('select','move','native','metrics'):
            raise ValueError('Ação de evento inválida.')
        event = {'schema_version': 1, 'kind': 'theme_lab_preview_event',
                 'event_id': uuid.uuid4().hex, 'family': self.family, 'action': action,
                 'control_id': self.backend.CONTROLS[control], 'control_index': control,
                 'project_sha256': project_hash,
                 'emitted_at': dt.datetime.now(dt.timezone.utc).isoformat(), **fields}
        if self.instance_id is not None:
            event['preview_instance'] = self.instance_id
        payload = (json.dumps(event, ensure_ascii=False, allow_nan=False) + '\n').encode('utf-8')
        if len(payload) > 16384:
            raise ValueError('Evento excede 16 KiB.')
        target = self.directory / f'event-{time.monotonic_ns():020d}-{event["event_id"]}.json'
        fd, temporary = tempfile.mkstemp(prefix='.preview-event-', dir=self.directory)
        try:
            with os.fdopen(fd, 'wb') as stream:
                os.fchmod(stream.fileno(), 0o600)
                stream.write(payload)
                stream.flush()
                os.fsync(stream.fileno())
            os.replace(temporary, target)
        finally:
            Path(temporary).unlink(missing_ok=True)


