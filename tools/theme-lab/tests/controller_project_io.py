# SPDX-License-Identifier: GPL-3.0-or-later
"""Project IO with native file dialogs in the existing disposable namespace."""
import copy
import json
import subprocess
import sys
from pathlib import Path

HOME = '/home/domainos-test'


def run(output, observation, click, wait, environment, restart):
    working = output / 'home/lab/working.json'
    scene = output / 'home/lab/scene.json'
    wait(lambda: working.is_file() and scene.is_file() and observation().get('load'))
    base = json.loads(working.read_text())
    scene_bytes = scene.read_bytes()
    incoming = copy.deepcopy(base)
    incoming['schema_version'] = 2
    for recipe in incoming['recipes'].values():
        recipe.setdefault('length_anchor', [0] * 16)
        recipe.setdefault('scrollbar_parts', {})
    incoming['name'] = 'Projeto importado — ação e São Paulo'
    incoming['recipes']['gtk5']['notes'] = 'Receita sem runtime preservada — revisão'
    incoming['recipes']['gtk5']['scrollbar_parts'] = {'arrow': {'glyph_px': 12}}
    incoming['recipes']['qt6']['positions'][0] = [73, 94]
    incoming['recipes']['qt6']['sizes'][0] = [120, 50]
    source = output / 'home/incoming.json'
    source.write_text(json.dumps(incoming, ensure_ascii=False), encoding='utf-8')

    def read_project():
        try: return json.loads(working.read_text())
        except (OSError, ValueError): return {}

    def project_data(value):
        # File serialization stamps exported_at; it is not editable project data.
        result = copy.deepcopy(value)
        result.pop('exported_at', None)
        return result

    def assert_project(actual, expected):
        assert project_data(actual) == project_data(expected), \
            'Project IO changed recipes, geometry, positions or evidence'

    def key(value):
        subprocess.run(['xdotool', 'key', '--clearmodifiers', value],
                       env=environment, check=True, timeout=5)

    def file_dialog(action, path=None, cancel=False, followed_dialog=False):
        if action: click(action)
        wait(lambda: observation().get('file_path'))
        window = observation()['file_window']
        subprocess.run(['xdotool', 'windowfocus', str(window)],
                       env=environment, check=True, timeout=5)
        if cancel:
            click('file_cancel')
        else:
            click('file_path'); key('ctrl+a')
            subprocess.run(['xdotool', 'type', '--clearmodifiers', '--delay', '1', path],
                           env=environment, check=True, timeout=10)
            click('file_ok')
        if followed_dialog:
            wait(lambda: observation().get('file_path') and observation().get('file_window') != window)
        else:
            wait(lambda: not observation().get('file_path'))

    file_dialog('load', HOME + '/incoming.json')
    wait(lambda: read_project().get('name') == incoming['name'])
    imported = read_project()
    assert_project(imported, incoming)
    assert scene.read_bytes() == scene_bytes, 'Import applied the proposal implicitly'
    assert 'proposta' in observation().get('status', ''), observation()

    # Resume the actual controller without --project. Pending inactive recipes
    # and history must survive, and startup must not silently apply the proposal.
    restart()
    assert_project(read_project(), incoming)
    assert scene.read_bytes() == scene_bytes, 'Restart silently applied the proposal'

    click('projectUndo'); wait(lambda: read_project().get('name') == base['name'])
    assert_project(read_project(), base)
    assert scene.read_bytes() == scene_bytes
    click('projectRedo'); wait(lambda: read_project().get('name') == incoming['name'])
    assert_project(read_project(), incoming)

    assert scene.read_bytes() == scene_bytes

    saved = output / 'home/saved.json'
    file_dialog('save', HOME + '/saved.json')
    wait(saved.is_file)
    assert_project(json.loads(saved.read_text()), incoming)
    assert source.read_bytes() == json.dumps(incoming, ensure_ascii=False).encode('utf-8')
    file_dialog('load', cancel=True)
    assert_project(read_project(), incoming)
    invalid = output / 'home/invalid.json'; invalid.write_text('{invalid')
    file_dialog('load', HOME + '/invalid.json')
    wait(lambda: 'JSON' in observation().get('status', ''))
    assert_project(read_project(), incoming)
    assert scene.read_bytes() == scene_bytes

    click('export')
    wait(lambda: observation().get('export_review_text'), 90)
    report = observation()['export_review_text']
    assert 'Nenhum tema foi instalado' in report
    assert 'recipes/gtk5/notes' in report
    index = output / 'home/lab/generated/exports/latest.json'
    wait(index.is_file)
    exported = json.loads(index.read_text())
    folder = output / 'home' / Path(exported['generation_dir']).relative_to(HOME)
    result = json.loads((folder / 'RESULTADO.json').read_text())
    assert result['comparison']['scene_snapshot_sha256']
    assert (folder / 'PACKAGE/DELTA.json').is_file()
    assert json.loads((folder / 'PROJECT.json').read_text())['recipes']['gtk5']['notes'] == incoming['recipes']['gtk5']['notes']
    assert scene.read_bytes() == scene_bytes
    click('export_review_close')
    wait(lambda: not observation().get('export_review_text'))
    click('apply')
    wait(lambda: json.loads(scene.read_text()).get('name') == incoming['name'])
    assert_project(json.loads(scene.read_text()), incoming)
    applied_bytes = scene.read_bytes()
    restart()
    assert_project(read_project(), incoming)
    assert scene.read_bytes() == applied_bytes
    click('projectUndo'); wait(lambda: read_project().get('name') == base['name'])
    assert_project(read_project(), base)
    assert scene.read_bytes() == applied_bytes
    click('projectRedo'); wait(lambda: read_project().get('name') == incoming['name'])
    assert_project(read_project(), incoming)

    sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
    import backend
    from proposal_export import differences, model_digest
    delta_base, _ = backend.project(source)
    delta_proposal = copy.deepcopy(delta_base)
    delta_proposal['name'] = 'Proposta delta — revisão independente'
    delta_proposal['recipes']['qt6']['positions'][0] = [83, 104]
    delta_proposal['recipes']['gtk5']['notes'] = 'Importada pelo botão — sem suporte simulado'
    delta_file = output / 'home/delta.json'
    delta_file.write_text(json.dumps({'schema': 1, 'kind': 'theme_lab_project_delta',
        'base_model_sha256': model_digest(delta_base),
        'proposal_model_sha256': model_digest(delta_proposal),
        'changes': differences(delta_base, delta_proposal)}, ensure_ascii=False))
    file_dialog('import_delta', cancel=True)
    assert_project(read_project(), incoming)
    file_dialog('import_delta', HOME + '/incoming.json', followed_dialog=True)
    file_dialog(None, cancel=True)
    assert_project(read_project(), incoming)
    wrong_base = output / 'home/wrong-base.json'
    wrong = copy.deepcopy(delta_base); wrong['name'] = 'Wrong base'
    wrong_base.write_text(json.dumps(wrong))
    file_dialog('import_delta', HOME + '/wrong-base.json', followed_dialog=True)
    file_dialog(None, HOME + '/delta.json')
    wait(lambda: 'Falha ao importar delta' in observation().get('status', ''))
    assert_project(read_project(), incoming)
    assert scene.read_bytes() == applied_bytes
    source_bytes = source.read_bytes()
    gate = output / 'home/import-gate'
    Path(str(gate) + '.arm').touch()
    file_dialog('import_delta', HOME + '/incoming.json', followed_dialog=True)
    file_dialog(None, HOME + '/delta.json')
    wait(lambda: Path(str(gate) + '.ready').is_file())
    (output / 'home/reveal-spin').write_text('notes')
    wait(lambda: not (output / 'home/reveal-spin').exists())
    wait(lambda: 0 < observation()['notes'][1] + observation()['notes'][3] / 2 < 760)
    click('notes'); key('ctrl+a')
    concurrent_note = 'Edicao concorrente preservada durante importacao'
    subprocess.run(['xdotool', 'type', '--clearmodifiers', '--delay', '1', concurrent_note],
                   env=environment, check=True, timeout=10)
    wait(lambda: read_project().get('recipes', {}).get('motif', {}).get('notes') == concurrent_note)
    Path(str(gate) + '.release').touch()
    wait(lambda: 'Projeto editado durante a importação' in observation().get('status', ''))
    concurrent = copy.deepcopy(incoming)
    concurrent['recipes']['motif']['notes'] = concurrent_note
    assert_project(read_project(), concurrent)
    assert observation().get('notes_text') == concurrent_note
    assert scene.read_bytes() == applied_bytes
    click('projectUndo')
    wait(lambda: read_project().get('recipes', {}).get('motif', {}).get('notes') == incoming['recipes']['motif']['notes'])
    assert_project(read_project(), incoming)
    file_dialog('import_delta', HOME + '/incoming.json', followed_dialog=True)
    file_dialog(None, HOME + '/delta.json')
    wait(lambda: read_project().get('name') == delta_proposal['name'])
    assert_project(read_project(), delta_proposal)
    assert scene.read_bytes() == applied_bytes
    assert source.read_bytes() == source_bytes
    assert list((output / 'home/lab/generated/imports').glob('revision-*/IMPORT.json'))
    click('projectUndo'); wait(lambda: read_project().get('name') == incoming['name'])
    assert_project(read_project(), incoming)
    click('projectRedo'); wait(lambda: read_project().get('name') == delta_proposal['name'])
    assert_project(read_project(), delta_proposal)

    # Broken persisted scene must be reported, not replaced with a proposal.
    from controller_reconstruction import run as reconstruct
    reconstruction = reconstruct(output, folder, observation, click, wait, file_dialog)
    scene.write_bytes(b'{broken persisted scene')
    preserved_working = working.read_bytes()
    restart(expected_exit=1)
    assert scene.read_bytes() == b'{broken persisted scene'
    assert working.read_bytes() == preserved_working
    assert 'Cena salva inválida; arquivo preservado' in (output / 'namespace.log').read_text()
    return {'status': 'passed', 'scope': 'Native controller file load/save/cancel/invalid input, pending inactive recipes, positions, Unicode, project Undo/Redo, explicit Apply, real backend Export and comparison; private Motif and selected-scheme generators, not historical painting',
            'imported_recipes_preserved': True, 'scene_changed_only_on_apply': True,
            'native_restart_preserved_pending_project_scene_and_undo': True,
            'invalid_persisted_scene_rejected_without_overwrite': True,
            'native_delta_import_cancel_wrong_base_success_and_undo': True,
            'native_edit_during_real_import_preserved_model_widget_scene_and_undo': True,
            **reconstruction,
            'export_package': str(folder / 'PACKAGE'), 'export_families': result['affected_families']}
