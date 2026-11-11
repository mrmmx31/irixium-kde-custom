# SPDX-License-Identifier: GPL-3.0-or-later
import contextlib
import io
from pathlib import Path
import sys
import unittest
from unittest.mock import patch

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
import preview_gtk2


class EntryGuardTest(unittest.TestCase):
    def test_guard_failure_precedes_project_output_and_gi_import(self):
        self.assertNotIn('gi', sys.modules)
        with patch.object(preview_gtk2.backend, 'private_namespace',
                          side_effect=ValueError('private guard rejected')), \
             patch.object(preview_gtk2.backend, 'project') as project, \
             patch.object(preview_gtk2, 'EventWriter') as writer, \
             contextlib.redirect_stderr(io.StringIO()) as error:
            status = preview_gtk2.main(['--project', '/not-read.json', '--rc', '/not-read.rc',
                                       '--events-dir', '/not-created'])
        self.assertEqual(status, 2)
        self.assertIn('private guard rejected', error.getvalue())
        project.assert_not_called()
        writer.assert_not_called()
        self.assertNotIn('gi', sys.modules)


if __name__ == '__main__': unittest.main()
