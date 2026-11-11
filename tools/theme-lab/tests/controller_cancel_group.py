# SPDX-License-Identifier: GPL-3.0-or-later
"""Real native cancellation/quit with a resistant test-owned descendant."""
import json
import os
from pathlib import Path
import signal
import subprocess
import time


def run(output, observation, click, wait, environment, container, server=None):
    gate = output / 'home/generate-gate'
    scene = output / 'home/lab/scene.json'
    working = output / 'home/lab/working.json'
    handles = []
    sentinel = subprocess.Popen(['sleep', '120'], start_new_session=True)

    def alive(pid):
        try:
            return Path(f'/proc/{pid}/stat').read_text().rsplit(')', 1)[1].split()[0] != 'Z'
        except FileNotFoundError:
            return False

    def arm():
        for suffix in ('.ready', '.descendant-ready'):
            Path(str(gate) + suffix).unlink(missing_ok=True)
        Path(str(gate) + '.spawn-descendant').touch()
        Path(str(gate) + '.arm').touch()
        click('apply')
        wait(lambda: Path(str(gate) + '.ready').exists(), 15)
        leader = int(Path(str(gate) + '.ready').read_text())
        descendant = int(Path(str(gate) + '.descendant-ready').read_text())
        for pid in (leader, descendant):
            assert Path(f'/proc/{pid}').stat().st_uid == os.getuid()
            assert os.getpgid(pid) == leader
            handles.append(os.pidfd_open(pid))
        return leader, descendant

    def edit(value):
        click('controlWidth*fieldValue')
        subprocess.run(['xdotool', 'key', '--clearmodifiers', 'ctrl+a'], env=environment, check=True)
        subprocess.run(['xdotool', 'type', '--clearmodifiers', '--delay', '1', value], env=environment, check=True)
        wait(lambda: observation().get('width_text') == value, 5)
        wait(lambda: json.loads(working.read_text())['recipes']['gtk3']['sizes'][0][0] == int(value), 10)

    try:
        wait(lambda: observation().get('native_push_allocation') == [220, 80], 90)
        (output / 'home/reveal-spin').write_text('width')
        wait(lambda: not (output / 'home/reveal-spin').exists(), 5)
        edit('222'); leader, descendant = arm()
        edit('223')
        if server is not None:
            # The server is the Popen handle created for this disposable test.
            # No DISPLAY lookup or signal to a personal X server is involved.
            files = [output / ('home/lab/' + name) for name in
                     ('working.json', 'scene.json', 'editor-journal.json', 'project-history.json')]
            wait(lambda: all(path.exists() for path in files), 10)
            snapshot = {path.name: path.read_bytes() for path in files}
            started = time.monotonic()
            server.terminate(); server.wait(timeout=5)
            assert container.wait(timeout=10) == 0
            wait(lambda: not alive(leader) and not alive(descendant), 5)
            assert sentinel.poll() is None
            assert {path.name: path.read_bytes() for path in files} == snapshot
            return {'status': 'passed', 'scope': 'Loss of the exact disposable Xvfb server invokes controller X IO handler; owned generation leader and resistant descendant stop; independent sentinel and all four saved project/editor files preserved byte-for-byte. No unsaved-keystroke or historical fidelity claim.',
                    'lost_display_owned_group': [leader, descendant],
                    'exit_seconds': time.monotonic() - started,
                    'independent_process_preserved': True,
                    'saved_files_preserved': list(snapshot)}
        # Loading a project is the controller's explicit cancellation path;
        # Apply queues a refresh and does not cancel a running generation.
        (output / 'home/cancel-reload.json').write_bytes(working.read_bytes())
        applied_before = scene.read_bytes()
        click('load'); wait(lambda: observation().get('file_path'), 10)
        subprocess.run(['xdotool', 'windowfocus', str(observation()['file_window'])], env=environment, check=True)
        click('file_path')
        subprocess.run(['xdotool', 'key', '--clearmodifiers', 'ctrl+a'], env=environment, check=True)
        subprocess.run(['xdotool', 'type', '--clearmodifiers', '--delay', '1', '/home/domainos-test/cancel-reload.json'], env=environment, check=True)
        started = time.monotonic(); click('file_ok')
        wait(lambda: not observation().get('file_path'), 10)
        wait(lambda: not alive(leader) and not alive(descendant), 10)
        elapsed = time.monotonic() - started
        assert elapsed < 8 and sentinel.poll() is None
        assert scene.read_bytes() == applied_before
        click('apply')
        wait(lambda: observation().get('native_push_allocation') == [223, 80], 90)
        assert json.loads(scene.read_text())['recipes']['gtk3']['sizes'][0] == [223, 80]
        # A cancelled old preview remains tracked for group cleanup, but must
        # not prevent a new same-kind preview opening after fast generation.
        edit('224'); click('apply')
        wait(lambda: observation().get('native_push_allocation') == [224, 80], 30)
        assert json.loads(scene.read_text())['recipes']['gtk3']['sizes'][0] == [224, 80]
        leader2, descendant2 = arm()
        applied = scene.read_bytes()
        click('quit'); assert container.wait(timeout=10) == 0
        wait(lambda: not alive(leader2) and not alive(descendant2), 5)
        assert sentinel.poll() is None and scene.read_bytes() == applied
        assert json.loads(working.read_text())['recipes']['gtk3']['sizes'][0] == [224, 80]
        return {'status': 'passed', 'scope': 'Native Motif Load cancels real gated generation leader and resistant descendant; actual GTK3 recovers223x80, then fast Apply updates224x80 while old cancelled preview is tracked; native Quit closes next owned group; independent child stays alive, project and scene preserved. Test-only descendant, no historical fidelity claim.',
                'cancelled_group': [leader, descendant], 'quit_group': [leader2, descendant2],
                'cancellation_seconds': elapsed, 'independent_process_preserved': True}
    finally:
        # pidfds retain exact test identities even after numerical PID reuse.
        for fd in handles:
            try:
                signal.pidfd_send_signal(fd, signal.SIGKILL)
            except ProcessLookupError:
                pass
            finally:
                os.close(fd)
        if sentinel.poll() is None:
            sentinel.terminate()
        sentinel.wait(timeout=5)
