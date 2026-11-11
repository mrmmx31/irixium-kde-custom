# SPDX-License-Identifier: GPL-3.0-or-later
"""Owned generation child: polling never blocks the GTK4 event loop."""
import os
from pathlib import Path
import signal
import subprocess
import sys
import uuid
import backend


class SnapshotJob:
    def __init__(self, root, base, model, digest, kdeglobals, *,
                 allow_toggle=False, allow_scrollbar=False, allow_check=False):
        if any(type(value) is not bool for value in (allow_toggle, allow_scrollbar, allow_check)):
            raise ValueError('GTK4 generation capability must be boolean')
        if allow_scrollbar and (allow_toggle or allow_check):
            raise ValueError('GTK4 scrollbar and button generation capabilities are mutually exclusive')
        self.allow_toggle, self.allow_scrollbar, self.allow_check = allow_toggle, allow_scrollbar, allow_check
        self.folder=backend.private_output(base/('snapshot-'+uuid.uuid4().hex),root)
        self.model,self.digest=model,digest
        self.input=self.folder/'INPUT.json'
        backend.write_json(self.input,model)
        self.log=(self.folder/'generation.log').open('w')
        command=[sys.executable,'-B',str(root/'tools/theme-lab/gtk4_generation.py'),
                 '--root',str(root),'--project',str(self.input),
                 '--digest',digest,'--output',str(self.folder/'generated')]
        if kdeglobals:command+=['--kdeglobals',str(kdeglobals)]
        if allow_toggle:command+=['--private-toggle-session']
        if allow_scrollbar:command+=['--private-scrollbar-session']
        if allow_check:command+=['--private-check-session']
        try:
            self.process=subprocess.Popen(command,stdout=self.log,stderr=subprocess.STDOUT,
                                          start_new_session=True)
        except BaseException:
            self.log.close();raise

    def poll(self):return self.process.poll()

    def close(self):
        try:
            if self.process.poll() is None:
                try:os.killpg(self.process.pid,signal.SIGTERM)
                except ProcessLookupError:pass
                try:self.process.wait(timeout=2)
                except subprocess.TimeoutExpired:
                    try:os.killpg(self.process.pid,signal.SIGKILL)
                    except ProcessLookupError:pass
                    self.process.wait(timeout=2)
        finally:self.log.close()
