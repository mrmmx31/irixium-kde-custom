# SPDX-License-Identifier: GPL-3.0-or-later
"""Owned private journal I/O: bounded bytes, CAS, nonblocking lock and fsync.

Format validation belongs to the caller and completes before publication.
"""
import contextlib
import fcntl
import hashlib
import os
from pathlib import Path
import re
import stat
import tempfile

MAX_BYTES = 32 * 1048576


class PrivateJsonStore:
    def __init__(self, directory, filename):
        if not isinstance(filename, str) or not re.fullmatch(r'[a-z0-9][a-z0-9-]{0,100}\.json', filename):
            raise ValueError('Nome inválido de journal privado.')
        self.directory = Path(directory).absolute()
        if '..' in self.directory.parts or any(p.is_symlink()
                for p in (self.directory, *self.directory.parents)):
            raise ValueError('Journal de amostras não pode atravessar links ou ..')
        # Caller supplies a private existing workspace, never a personal config dir.
        info = self.directory.stat()
        if not stat.S_ISDIR(info.st_mode) or info.st_uid != os.getuid() or info.st_mode & 0o077:
            raise ValueError('Diretório do journal deve ser privado e pertencer ao usuário.')
        self.path = self.directory / filename
        self.lock_path = self.path.with_suffix('.lock')
        self.expected = None
        self.loaded = False
        self.directory_dirty = False

    @contextlib.contextmanager
    def locked(self):
        fd = os.open(self.lock_path, os.O_RDWR | os.O_CREAT | os.O_NOFOLLOW | os.O_NONBLOCK, 0o600)
        try:
            self.check_file(fd)
            fcntl.flock(fd, fcntl.LOCK_EX | fcntl.LOCK_NB)
            yield
        finally:
            os.close(fd)

    @staticmethod
    def check_file(fd):
        info = os.fstat(fd)
        if not stat.S_ISREG(info.st_mode) or info.st_uid != os.getuid() or info.st_mode & 0o077:
            raise ValueError('Arquivo do journal deve ser regular, privado e do usuário.')

    def read(self):
        try:
            fd = os.open(self.path, os.O_RDONLY | os.O_NOFOLLOW | os.O_NONBLOCK)
        except FileNotFoundError:
            return None
        with os.fdopen(fd, 'rb') as stream:
            self.check_file(stream.fileno())
            raw = stream.read(MAX_BYTES + 1)
        if len(raw) > MAX_BYTES:
            raise ValueError('Journal de amostras excede32MiB.')
        return raw

    @staticmethod
    def digest(raw):
        return None if raw is None else hashlib.sha256(raw).hexdigest()

    def read_loaded(self, decoder):
        if self.loaded:
            raise ValueError('Journal já carregado; não substituir histórico vivo.')
        with self.locked():
            raw = self.read()
            histories = {} if raw is None else decoder(raw)
            self.expected, self.loaded = self.digest(raw), True
        return histories

    def write_payload(self, raw):
        if not self.loaded:
            raise ValueError('Carregue o journal antes de gravar.')
        if not isinstance(raw, bytes) or len(raw) > MAX_BYTES:
            raise ValueError('Payload privado inválido ou acima de32MiB.')
        with self.locked():
            current = self.read()
            if self.digest(current) != self.expected:
                raise ValueError('Conflito no journal de amostras; edição externa preservada.')
            if current == raw:
                if self.directory_dirty:
                    self.sync_directory()
                return False
            fd, stage = tempfile.mkstemp(prefix='.' + self.path.name + '-', dir=self.directory)
            try:
                with os.fdopen(fd, 'wb') as stream:
                    stream.write(raw)
                    stream.flush()
                    os.fsync(stream.fileno())
                os.replace(stage, self.path)
                # If directory fsync fails, retain the matching CAS token so a retry
                # can checkpoint again; the caller must still surface the error.
                self.expected = self.digest(raw)
                self.directory_dirty = True
                self.sync_directory()
            finally:
                if os.path.exists(stage):
                    os.unlink(stage)
        return True

    def sync_directory(self):
        directory_fd = os.open(self.directory, os.O_RDONLY | os.O_DIRECTORY | os.O_NOFOLLOW)
        try:
            os.fsync(directory_fd)
            self.directory_dirty = False
        finally:
            os.close(directory_fd)
