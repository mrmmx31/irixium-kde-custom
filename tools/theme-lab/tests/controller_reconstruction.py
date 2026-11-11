# SPDX-License-Identifier: GPL-3.0-or-later
"""Native FILES/directory dialogs and actual reconstruction backend."""
import json
from pathlib import Path
from artifact_delta import package_files, digest

HOME = '/home/domainos-test'


def run(output, exported, observation, click, wait, file_dialog):
    working = output / 'home/lab/working.json'
    scene = output / 'home/lab/scene.json'
    previous_project, previous_scene = working.read_bytes(), scene.read_bytes()
    revisions = output / 'home/lab/generated/reconstructed'

    def folders():
        return set(revisions.glob('revision-*')) if revisions.exists() else set()

    def private_path(path):
        return HOME + '/' + str(path.relative_to(output / 'home'))

    def check_report(before, expected=None):
        wait(lambda: observation().get('export_review_text'))
        text = observation()['export_review_text']
        assert 'Reconstrução de arquivos' in text and 'Nenhum tema foi instalado' in text
        assert 'cores atuais ainda não foram revalidados' in text
        added = folders() - before
        assert len(added) == 1
        folder = added.pop()
        result = json.loads((folder / 'RECONSTRUCTION.json').read_text())
        theme = folder / 'theme'
        files = {str(p.relative_to(theme)): p.read_bytes()
                 for p in theme.rglob('*') if p.is_file()}
        assert {name: digest(data) for name, data in files.items()} == result['file_hashes']
        if expected is not None: assert files == expected
        assert not result['installed'] and not result['palette_revalidated']
        assert working.read_bytes() == previous_project and scene.read_bytes() == previous_scene
        click('export_review_close')
        wait(lambda: not observation().get('export_review_text'))

    file_dialog('reconstruct_files', cancel=True)
    # Reconstruct a real generated GTK3 snapshot, without asking for a base.
    snapshot = exported / 'PACKAGE/gtk3/FILES.json'
    assert json.loads(snapshot.read_text())['mode'] == 'snapshot'
    before = folders()
    file_dialog('reconstruct_files', private_path(snapshot))
    check_report(before)

    base = output / 'home/artifact-base'; base.mkdir()
    initial = {'gtk.css': b'base', 'arrow.svg': b'unchanged'}
    expected = {'gtk.css': b'proposal', 'arrow.svg': b'unchanged'}
    for name, data in initial.items(): (base / name).write_bytes(data)
    package = output / 'home/artifact-package'
    package_files(initial, expected, package)
    path = private_path(package / 'FILES.json')
    before = folders()
    file_dialog('reconstruct_files', path, followed_dialog=True)
    file_dialog(None, cancel=True)
    assert folders() == before
    wrong = output / 'home/wrong-artifact-base'; wrong.mkdir()
    (wrong / 'gtk.css').write_bytes(b'wrong')
    file_dialog('reconstruct_files', path, followed_dialog=True)
    file_dialog(None, private_path(wrong))
    wait(lambda: 'Falha ao reconstruir arquivos' in observation().get('status', ''))
    assert folders() == before
    file_dialog('reconstruct_files', path, followed_dialog=True)
    file_dialog(None, private_path(base))
    check_report(before, expected)
    assert {p.name: p.read_bytes() for p in base.iterdir()} == initial
    assert working.read_bytes() == previous_project and scene.read_bytes() == previous_scene
    return {'native_reconstruction': 'passed: real GTK3 snapshot, delta directory selection, two cancellations, wrong base refusal, exact bytes/report, base/project/scene preserved'}
