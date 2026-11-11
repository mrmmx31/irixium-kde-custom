# SPDX-License-Identifier: GPL-3.0-or-later
import io
import os
from types import SimpleNamespace
import unittest
from unittest.mock import patch,MagicMock
from gtk4_worker import (Worker, capture_capabilities, capture_scrollbar_probe,
                         configure_display_backend, publish_pending_x11_state,
                         validate_preview_renderer, wait_window_xid)
from gtk4_snapshot_job import SnapshotJob
from test_backend import model


class WorkerRecoveryTests(unittest.TestCase):
    def test_manual_capture_derives_exact_native_renderer(self):
        self.assertEqual(capture_capabilities(0), {
            'renderer':'buttons', 'allow_toggle':False,
            'allow_check':False, 'allow_scrollbar':False})
        self.assertEqual(capture_capabilities(1)['allow_toggle'], True)
        self.assertEqual(capture_capabilities(2)['allow_check'], True)
        for control in (10, 11):
            capability = capture_capabilities(control)
            self.assertEqual(capability['renderer'], 'scrollbar')
            self.assertTrue(capability['allow_scrollbar'])
            self.assertFalse(capability['allow_toggle'])
            self.assertFalse(capability['allow_check'])

    def test_manual_capture_rejects_untranslated_control(self):
        with self.assertRaisesRegex(ValueError, 'not translated'):
            capture_capabilities(3)

    def test_scrollbar_probe_maps_private_dimensions_and_range(self):
        horizontal = capture_scrollbar_probe(SimpleNamespace(
            capture_length=320, capture_thickness=19, capture_value=10,
            capture_page_size=40, capture_part='whole',
            capture_direction='auto'), 10)
        vertical = capture_scrollbar_probe(SimpleNamespace(
            capture_length=240, capture_thickness=17, capture_value=50,
            capture_page_size=25, capture_part='whole',
            capture_direction='auto'), 11)
        self.assertEqual(horizontal, {
            'size':[320,19], 'value':10, 'page_size':40,
            'part':'whole', 'direction':'auto'})
        self.assertEqual(vertical['size'], [17,240])
        self.assertEqual(vertical['value'], 50)

    def test_scrollbar_probe_refuses_unimplemented_part_or_direction(self):
        for part, direction in (('thumb','auto'), ('whole','right'),
                                ('arrow','left')):
            with self.subTest(part=part, direction=direction), \
                 self.assertRaisesRegex(ValueError, 'only whole/auto'):
                capture_scrollbar_probe(SimpleNamespace(
                    capture_length=200, capture_thickness=15, capture_value=25,
                    capture_page_size=25, capture_part=part,
                    capture_direction=direction), 10)

    def test_worker_route_covers_five_and_refuses_other_eleven(self):
        project = model()
        recipe = project['recipes']['gtk4']
        recipe['visible_categories'] = 31
        recipe['visible_controls'] = (1 << 16) - 1
        for control in range(16):
            recipe['selected_control'] = control
            with self.subTest(control=control):
                if control <= 2:
                    self.assertEqual(validate_preview_renderer(
                        project, True, True, False), 'buttons')
                elif control in (10, 11):
                    self.assertEqual(validate_preview_renderer(
                        project, False, False, True), 'scrollbar')
                else:
                    with self.assertRaisesRegex(
                            ValueError, 'sem tradutor DomainOS'):
                        validate_preview_renderer(project, False, False, False)

    def test_worker_rejects_old_three_button_fallback_flags(self):
        project = model()
        recipe = project['recipes']['gtk4']
        recipe['visible_categories'] = 31
        recipe['visible_controls'] = (1 << 16) - 1
        recipe['selected_control'] = 0
        with self.assertRaisesRegex(ValueError, 'capability mismatch'):
            validate_preview_renderer(project, False, False, False)

    def test_runtime_reload_preserves_scene_for_unsupported_selection(self):
        project = model()
        recipe = project['recipes']['gtk4']
        recipe['visible_categories'] = 31
        recipe['visible_controls'] = (1 << 16) - 1
        recipe['selected_control'] = 12
        worker = Worker.__new__(Worker)
        worker.stop_requested = False
        worker.bridge = None
        worker.args = SimpleNamespace(project='fixture.json')
        worker.palette_stamp = lambda: ()
        worker.job = None
        worker.failed_signature = None
        worker.digest = 'a' * 64
        worker.receipt = {'palette_inputs':[]}
        worker.allow_toggle = worker.allow_check = worker.allow_scrollbar = False
        worker.report = MagicMock()
        worker.checkpoint = MagicMock()
        with patch('gtk4_worker.backend.project',
                   return_value=(project, 'b' * 64)):
            self.assertEqual(worker.tick(None), 1)
        worker.report.assert_called_once()
        self.assertIn('sem tradutor DomainOS',
                      str(worker.report.call_args.args[0]))

    def test_embedded_preview_forces_x11_before_gtk_initialization(self):
        with patch.dict(os.environ,{'GDK_BACKEND':'wayland'}):
            configure_display_backend(0x1234)
            self.assertEqual(os.environ['GDK_BACKEND'],'x11')

    def test_separate_preview_preserves_selected_backend(self):
        with patch.dict(os.environ,{'GDK_BACKEND':'wayland'}):
            configure_display_backend(None)
            self.assertEqual(os.environ['GDK_BACKEND'],'wayland')

    def test_x11_publication_dispatches_pending_work_then_flushes(self):
        calls=[]
        pending=iter((1,1,0))
        publish_pending_x11_state(
            lambda context,blocking:calls.append(('iterate',context,blocking)) or next(pending),
            lambda display:calls.append(('flush',display)),17)
        self.assertEqual(calls,[('iterate',None,0),('iterate',None,0),
                                ('iterate',None,0),('flush',17)])

    def test_window_xid_waits_for_surface_publication(self):
        surfaces=iter((None,17))
        times=iter((0.0,0.1,0.2,0.3))
        iterations=[]
        self.assertEqual(wait_window_xid(
            9,lambda _window:next(surfaces),lambda _surface:0x1234,
            lambda context,blocking:iterations.append((context,blocking)) or 0,
            clock=lambda:next(times),sleeper=lambda _delay:None),0x1234)
        self.assertEqual(iterations,[(None,0)])

    def test_window_xid_timeout_is_bounded(self):
        times=iter((0.0,1.0))
        with self.assertRaisesRegex(RuntimeError,'did not become ready'):
            wait_window_xid(9,lambda _window:None,lambda _surface:0,
                            lambda _context,_blocking:0,timeout=0.5,
                            clock=lambda:next(times),sleeper=lambda _delay:None)

    def test_toggle_terminal_checkpoint_after_scene_closed(self):
        worker=SimpleNamespace(status='closed',window_id=1,digest='a'*64,
            writer=SimpleNamespace(instance_id='b'*32),last_error=None,event_error=None,
            bridge=None,renderer_requested='cairo',job=None,allow_toggle=True,
            session=SimpleNamespace(scene=None))
        self.assertEqual(Worker.state(worker)['toggle_selection'],{})

    def test_native_toggle_event_records_selected_value(self):
        worker=Worker.__new__(Worker);worker.allow_toggle=True
        worker.session=SimpleNamespace(scene=SimpleNamespace(records={1:{'id':'toggle'}},widgets={1:77}))
        worker.api=SimpleNamespace(toggle_active=lambda widget:widget==77)
        worker.bridge=None
        worker.writer=MagicMock();worker.digest='a'*64
        worker.clicked(1)
        worker.writer.emit.assert_called_once_with('native',1,'a'*64,
            state={'clicked':True,'selected':True,'active':True},origin='separate')

    def test_invalid_project_preserves_accepted_digest_and_scene(self):
        worker=Worker.__new__(Worker)
        worker.stop_requested=False;worker.bridge=None
        worker.args=SimpleNamespace(project='fixture.json')
        worker.digest='a'*64;worker.model={'accepted':True}
        worker.session=object();old=worker.session
        worker.last_error=None;worker.window=1
        worker.title=MagicMock();worker.checkpoint=MagicMock()
        with patch('gtk4_worker.backend.project',side_effect=ValueError('Invalid project')):
            self.assertEqual(worker.tick(None),1)
        self.assertIs(worker.session,old)
        self.assertEqual(worker.digest,'a'*64)
        self.assertIn('Invalid project',worker.last_error)

    def test_event_storage_failure_is_reported_without_losing_click_handler(self):
        worker=Worker.__new__(Worker)
        worker.writer=MagicMock();worker.writer.emit.side_effect=OSError('disk failure')
        worker.digest='a'*64;worker.window=1;worker.title=MagicMock()
        worker.session=SimpleNamespace(scene=SimpleNamespace(
            records={0:{'id':'push'}},widgets={}))
        worker.allow_toggle=False;worker.allow_check=False;worker.bridge=None
        worker.clicked(0)
        self.assertEqual(worker.event_error,'disk failure')
        worker.writer.emit.side_effect=None;worker.clicked(0)
        self.assertIsNone(worker.event_error)

    def test_generation_close_handles_exit_race_and_closes_log(self):
        job=SnapshotJob.__new__(SnapshotJob)
        job.process=MagicMock();job.process.pid=99999;job.process.poll.return_value=None
        job.log=io.StringIO()
        with patch('gtk4_snapshot_job.os.killpg',side_effect=ProcessLookupError):
            job.close()
        job.process.wait.assert_called_once_with(timeout=2)
        self.assertTrue(job.log.closed)


if __name__=='__main__':unittest.main()
