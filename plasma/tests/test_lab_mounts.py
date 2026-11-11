#!/usr/bin/env python3
"""Contrato do addon privado: worker verificado, socket único e caminhos internos."""
import importlib.util
import os
from pathlib import Path
import stat
import tempfile
from types import SimpleNamespace
import unittest
from unittest.mock import patch

spec = importlib.util.spec_from_file_location('launcher', Path(__file__).resolve().parents[1] / 'tools/abrir-laboratorio-temas.py')
lab = importlib.util.module_from_spec(spec)
spec.loader.exec_module(lab)


class MountsTests(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory(prefix='lab-mounts-')
        self.session = Path(self.temp.name)
        (self.session / 'fixture').mkdir()
        (self.session / 'fixture/probe.py').touch()
        self.output = self.session / 'lab-addon/run-example'
        self.original = {'display': ':61', 'resources': [{'source': '/host/personal-resource', 'mount': '/home/domainos-test/readonly-assets'}]}
        self.manifest = {'original_processes': {'worker': {'pid': 12345}}, 'preview_id': 'a' * 32,
                         'environment': {'DISPLAY': ':61'}}
        self.xdir = Path('/proc/12345/root/tmp/.X11-unix')
        self.xsocket = self.xdir / 'X61'

    def tearDown(self):
        self.temp.cleanup()

    def command(self, alive=True, entries=None, socket_mode=stat.S_IFSOCK):
        real_stat, real_iter = Path.stat, Path.iterdir
        def info(path, *args, **kwargs):
            return SimpleNamespace(st_mode=socket_mode, st_uid=os.getuid()) if path == self.xsocket else real_stat(path, *args, **kwargs)
        def listing(path):
            return iter(entries if entries is not None else [self.xsocket]) if path == self.xdir else real_iter(path)
        with patch.object(lab, 'identity_alive', return_value=alive), patch.object(Path, 'stat', info), patch.object(Path, 'iterdir', listing):
            return lab.container_command(self.session, self.output, self.original, self.manifest)

    def test_existing_private_mount_then_independent_namespace(self):
        argv = self.command()
        self.assertEqual(argv[:9], ['nsenter', '--target', '12345', '--user', '--mount', '--net', '--preserve-credentials', 'bwrap', '--unshare-user'])
        self.assertIn('--unshare-net', argv)
        self.assertNotIn('--unshare-pid', argv)
        self.assertFalse(any(str(self.session) in value for value in argv))
        triples = [argv[i:i+3] for i in range(len(argv)-2)]
        self.assertIn(['--ro-bind', '/tmp/.X11-unix', '/tmp/.X11-unix'], triples)
        self.assertIn(['--ro-bind', '/out/lab-addon/run-example/root', '/fixture/theme-lab-root'], triples)
        self.assertIn(['--ro-bind', '/home/domainos-test/readonly-assets', '/home/domainos-test/readonly-assets'], triples)
        self.assertNotIn('/host/personal-resource', argv)

    def test_changed_worker_refused(self):
        with self.assertRaises(RuntimeError): self.command(alive=False)

    def test_extra_socket_refused(self):
        with self.assertRaises(RuntimeError): self.command(entries=[self.xsocket, self.xdir / 'X1'])

    def test_non_socket_refused(self):
        with self.assertRaises(RuntimeError): self.command(socket_mode=stat.S_IFREG)


if __name__ == '__main__':
    unittest.main()
