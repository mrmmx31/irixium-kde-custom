#!/usr/bin/env python3
"""Retomada de dados salvos, sem abrir aplicações nem acessar perfis pessoais."""
import importlib.util
import json
import os
from pathlib import Path
import tempfile
import unittest
from unittest.mock import patch, Mock

SCRIPT = Path(__file__).resolve().parents[1] / 'tools/abrir-laboratorio-temas.py'
spec = importlib.util.spec_from_file_location('lab_launcher', SCRIPT)
lab = importlib.util.module_from_spec(spec)
spec.loader.exec_module(lab)


class ResumeTests(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory(prefix='lab-resume-')
        self.session = Path(self.temp.name)
        self.home = self.session / 'home'
        self.home.mkdir(mode=0o700)
        self.addon = self.session / 'lab-addon/run-test'
        self.addon.mkdir(parents=True, mode=0o700)
        self.manifest = self.addon / 'MANIFESTO.json'
        self.token = 'a' * 32
        lab.write_json(self.session / 'MANIFESTO.json',
                       {'environment': {'IRIX_DOMAINOS_PREVIEW_ID': self.token}})
        self.old = {'lab_id': 'b' * 32, 'new_instance': True, 'uid': os.getuid(),
                    'session': str(self.session), 'preview_id': self.token}
        lab.write_json(self.manifest, self.old)
        self.source = self.home / lab.instance_work(self.old).name
        self.source.mkdir(mode=0o700)
        lab.write_json(self.source / 'working.json', {'note': 'ação — café', 'family': 'motif'})
        lab.write_json(self.source / 'scene.json', {'old_output': True})
        self.destination = self.home / 'theme-lab-new'

    def tearDown(self):
        self.temp.cleanup()

    def run_snapshot(self):
        return lab.resume_snapshot(self.session, self.manifest, self.destination)

    def sample_files(self):
        folder = self.source / 'preview-events'; folder.mkdir(mode=0o700)
        snapshot = {'states': [['ação🙂', 4, 0, None], ['novo', 4, 4, None]],
                    'position': 0, 'limit': 128, 'byte_limit': 1048576}
        for name, (family, origin) in lab.SAMPLE_FILES.items():
            value = {'schema_version': 1, 'family': family, 'origin': origin}
            if name.startswith('preview-events/runtime-'):
                value.update(kind='theme_lab_sample_runtime_state', states={'toggle': True,
                    'list': {'rows': ['ação🙂'], 'selected': ['0'], 'horizontal': 0, 'vertical': 0}})
            else:
                value.update(kind='theme_lab_sample_text_history', histories={'entry': snapshot})
            lab.write_json(self.source / name, value)
        lab.write_json(folder / 'event-ignore.json', {'not': 'history'})
        (folder / 'sample-gtk2-coupled.lock').write_text('not copied')

    def test_sample_histories_are_exact_separate_and_validated(self):
        self.sample_files()
        receipt = self.run_snapshot()
        self.assertEqual(set(receipt['sample_histories_imported']), set(lab.SAMPLE_FILES))
        for name in lab.SAMPLE_FILES:
            self.assertEqual((self.destination / name).read_bytes(), (self.source / name).read_bytes())
            self.assertIn(name, receipt['saved_files_sha256'])
            self.assertEqual((self.destination / name).stat().st_mode & 0o777, 0o600)
        self.assertEqual((self.destination / 'preview-events').stat().st_mode & 0o777, 0o700)
        self.assertFalse((self.destination / 'preview-events/event-ignore.json').exists())
        self.assertFalse((self.destination / 'preview-events/sample-gtk2-coupled.lock').exists())

    def test_invalid_sample_preserved_without_destination(self):
        self.sample_files()
        path = self.source / next(iter(lab.SAMPLE_FILES))
        data = json.loads(path.read_bytes()); data['histories']['entry']['position'] = 100
        lab.write_json(path, data); original = path.read_bytes()
        with self.assertRaises(ValueError): self.run_snapshot()
        self.assertEqual(path.read_bytes(), original)
        self.assertFalse(self.destination.exists())

    def test_invalid_runtime_sample_preserved_without_destination(self):
        self.sample_files()
        path = self.source / 'preview-events/runtime-gtk2-coupled.json'
        data = json.loads(path.read_bytes()); data['states']['list']['selected'] = ['2']
        lab.write_json(path, data); original = path.read_bytes()
        with self.assertRaises(ValueError): self.run_snapshot()
        self.assertEqual(path.read_bytes(), original)
        self.assertFalse(self.destination.exists())

    def test_sample_parent_link_refused_without_destination(self):
        self.sample_files()
        parent = self.source / 'preview-events'; parent.rename(self.source / 'other-events')
        parent.symlink_to('other-events')
        with self.assertRaises(RuntimeError): self.run_snapshot()
        self.assertFalse(self.destination.exists())

    def test_sample_concurrent_checkpoint_refused_without_destination(self):
        self.sample_files()
        original = lab.read_bytes; counter = 0
        def changed(path, *args, **kwargs):
            nonlocal counter
            data = original(path, *args, **kwargs)
            if path.name == 'sample-gtk2-coupled.json':
                counter += 1
                if counter == 2: return data + b' '
            return data
        lab.read_bytes = changed
        try:
            with self.assertRaises(RuntimeError): self.run_snapshot()
            self.assertFalse(self.destination.exists())
        finally: lab.read_bytes = original

    def test_saved_project_exact_without_runtime_outputs(self):
        before = (self.source / 'working.json').read_bytes()
        receipt = self.run_snapshot()
        self.assertEqual((self.destination / 'working.json').read_bytes(), before)
        self.assertEqual((self.source / 'working.json').read_bytes(), before)
        self.assertEqual((self.destination / 'scene.json').read_bytes(),
                         (self.source / 'scene.json').read_bytes())
        self.assertTrue(receipt['applied_scene_imported'])
        self.assertFalse((self.destination / 'generated').exists())
        self.assertFalse(receipt['unsaved_widget_text_imported'])
        self.assertEqual((self.destination / 'working.json').stat().st_mode & 0o777, 0o600)

    def test_missing_scene_is_explicit(self):
        (self.source / 'scene.json').unlink()
        receipt = self.run_snapshot()
        self.assertFalse(receipt['applied_scene_imported'])
        self.assertFalse((self.destination / 'scene.json').exists())

    def test_invalid_scene_rejected_without_destination(self):
        path = self.source / 'scene.json'; path.write_bytes(b'{broken')
        with self.assertRaises(ValueError): self.run_snapshot()
        self.assertEqual(path.read_bytes(), b'{broken')
        self.assertFalse(self.destination.exists())

    def test_symlink_scene_rejected(self):
        path = self.source / 'scene.json'; path.rename(self.source / 'other-scene.json')
        path.symlink_to('other-scene.json')
        with self.assertRaises(OSError): self.run_snapshot()
        self.assertFalse(self.destination.exists())

    def test_scene_concurrent_checkpoint_rejected(self):
        original = lab.read_bytes
        counter = 0
        def changed(path, *args, **kwargs):
            nonlocal counter
            data = original(path, *args, **kwargs)
            if path.name == 'scene.json':
                counter += 1
                if counter == 2: return data + b' '
            return data
        lab.read_bytes = changed
        try:
            with self.assertRaises(RuntimeError): self.run_snapshot()
            self.assertFalse(self.destination.exists())
        finally: lab.read_bytes = original

    def test_large_project_history_uses_same_limit_on_recheck(self):
        lab.write_json(self.source / 'project-history.json', {'text': 'x' * (9 * 1024 * 1024)})
        self.run_snapshot()
        self.assertEqual((self.destination / 'project-history.json').read_bytes(),
                         (self.source / 'project-history.json').read_bytes())

    def test_history_exact(self):
        lab.write_json(self.source / 'editor-journal.json', {'histories': {'notes': ['ação', 'ação!']}})
        self.run_snapshot()
        self.assertEqual((self.destination / 'editor-journal.json').read_bytes(),
                         (self.source / 'editor-journal.json').read_bytes())

    def test_project_history_is_separate_and_exact(self):
        lab.write_json(self.source / 'project-history.json',
                       {'kind': 'theme_lab_project_history', 'position': 1,
                        'entries': [{'note': 'início'}, {'note': 'ação'}],
                        'point': {'note': 'início'}})
        lab.write_json(self.source / 'editor-journal.json', {'histories': {'notes': ['texto']}})
        receipt = self.run_snapshot()
        for name in ('working.json', 'editor-journal.json', 'project-history.json'):
            self.assertEqual((self.destination / name).read_bytes(), (self.source / name).read_bytes())
            self.assertIn(name, receipt['saved_files_sha256'])

    def test_existing_destination_preserved(self):
        self.destination.mkdir(mode=0o700)
        marker = self.destination / 'keep'; marker.write_text('keep')
        with self.assertRaises(RuntimeError): self.run_snapshot()
        self.assertEqual(marker.read_text(), 'keep')

    def test_other_session_rejected(self):
        self.old['preview_id'] = 'c' * 32; lab.write_json(self.manifest, self.old)
        with self.assertRaises(RuntimeError): self.run_snapshot()
        self.assertFalse(self.destination.exists())

    def test_symlink_project_rejected(self):
        path = self.source / 'working.json'; path.rename(self.source / 'other.json')
        path.symlink_to('other.json')
        with self.assertRaises(OSError): self.run_snapshot()
        self.assertFalse(self.destination.exists())

    def test_invalid_json_preserved(self):
        path = self.source / 'working.json'; path.write_bytes(b'{broken')
        with self.assertRaises(ValueError): self.run_snapshot()
        self.assertEqual(path.read_bytes(), b'{broken')
        self.assertFalse(self.destination.exists())

    def test_non_private_project_rejected(self):
        (self.source / 'working.json').chmod(0o644)
        with self.assertRaises(RuntimeError): self.run_snapshot()
        self.assertFalse(self.destination.exists())

    def test_concurrent_source_rejected(self):
        original = lab.read_bytes
        counter = 0
        def changed(path, *args, **kwargs):
            nonlocal counter
            data = original(path, *args, **kwargs)
            if path.name == 'working.json':
                counter += 1
                if counter == 2: return data + b' '
            return data
        lab.read_bytes = changed
        try:
            with self.assertRaises(RuntimeError): self.run_snapshot()
            self.assertFalse(self.destination.exists())
        finally: lab.read_bytes = original


    def test_explicit_recovery_preserves_source_and_all_histories(self):
        path=self.home/'rescued.json'
        rows={f'context/{i}':{'entries':['','ação — rascunho'], 'position':1} for i in range(310)}
        lab.write_json(path,{'schema_version':1,'histories':rows})
        lab.write_json(self.source/'editor-journal.json',{'schema_version':1,'histories':dict(list(rows.items())[:254])})
        original=(self.source/'editor-journal.json').read_bytes()
        snapshot=path.read_bytes()
        result=lab.resume_snapshot(self.session,self.manifest,self.destination,path)
        self.assertEqual((self.source/'editor-journal.json').read_bytes(),original)
        self.assertEqual(path.read_bytes(),snapshot)
        self.assertEqual((self.destination/'editor-journal.json').read_bytes(),snapshot)
        self.assertEqual(result['editor_recovery']['histories'],310)
        self.assertEqual(lab.resume_files_to_verify(result),result['delivered_files_sha256'])
        self.assertNotEqual(result['saved_files_sha256']['editor-journal.json'],result['delivered_files_sha256']['editor-journal.json'])

    def test_recovery_rejects_invalid_or_removed_history(self):
        row={'entries':['saved'],'position':0}
        lab.write_json(self.source/'editor-journal.json',{'schema_version':1,'histories':{'existing':row}})
        for data in ({'schema_version':1,'histories':{}},
                     {'schema_version':1,'histories':{'existing':{'entries':['x'],'position':2}}},
                     {'schema_version':1,'histories':{'existing':{'entries':['bad\0text'],'position':0}}}):
            path=self.home/'rescued.json';lab.write_json(path,data)
            with self.assertRaises(RuntimeError):
                lab.resume_snapshot(self.session,self.manifest,self.destination,path)
            self.assertFalse(self.destination.exists())

    def test_recovery_rejects_foreign_or_public_snapshot(self):
        path=self.session/'outside.json';lab.write_json(path,{'schema_version':1,'histories':{}})
        with self.assertRaises(RuntimeError):lab.recovered_editor_snapshot(self.session,path)
        local=self.home/'rescued.json';lab.write_json(local,{'schema_version':1,'histories':{}})
        local.chmod(0o644)
        with self.assertRaises(RuntimeError):lab.recovered_editor_snapshot(self.session,local)
        link=self.home/'link.json';link.symlink_to(path)
        with self.assertRaises(RuntimeError):lab.recovered_editor_snapshot(self.session,link)


    def test_worker_hash_selection_rejects_unrelated_override(self):
        resume={'saved_files_sha256':{'working.json':'old','editor-journal.json':'disk'},
                'delivered_files_sha256':{'working.json':'altered','editor-journal.json':'memory'},
                'editor_recovery':{'sha256':'memory'}}
        with self.assertRaises(RuntimeError):lab.resume_files_to_verify(resume)
        resume['delivered_files_sha256']['working.json']='old'
        resume['editor_recovery']['sha256']='wrong'
        with self.assertRaises(RuntimeError):lab.resume_files_to_verify(resume)
        resume['editor_recovery']=None
        with self.assertRaises(RuntimeError):lab.resume_files_to_verify(resume)

    def test_worker_accepts_legacy_resume(self):
        resume={'saved_files_sha256':{'working.json':'original'}}
        self.assertEqual(lab.resume_files_to_verify(resume),resume['saved_files_sha256'])


    def test_start_identity_reobserves_same_child_after_transient_read(self):
        child=Mock(pid=123,returncode=None);child.poll.return_value=None
        with patch.object(lab,'process_identity',side_effect=[RuntimeError('not ready'),{'pid':123}]) as query:
            self.assertEqual(lab.started_process_identity(child,'token','lab'),{'pid':123})
            self.assertEqual(query.call_count,2)
            query.assert_called_with(123,'token','lab')

    def test_start_identity_stops_on_terminal_child(self):
        child=Mock(pid=123,returncode=2);child.poll.return_value=2
        with patch.object(lab,'process_identity') as query:
            with self.assertRaisesRegex(RuntimeError,'encerrou'):
                lab.started_process_identity(child,'token','lab')
            query.assert_not_called()

    def test_start_identity_never_accepts_missing_marker(self):
        child=Mock(pid=123,returncode=None);child.poll.return_value=None
        with patch.object(lab,'process_identity',side_effect=RuntimeError('wrong marker')):
            with self.assertRaisesRegex(RuntimeError,'não confirmada'):
                lab.started_process_identity(child,'token','lab',timeout=.03)


if __name__ == '__main__':
    unittest.main()
