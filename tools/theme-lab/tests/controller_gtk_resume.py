# SPDX-License-Identifier: GPL-3.0-or-later
"""Applied GTK3 scene resumes independently from pending project/selection."""
import copy
import json
import subprocess

HOME = '/home/domainos-test'


def run(output, observation, click, wait, environment, restart):
    working = output / 'home/lab/working.json'
    scene = output / 'home/lab/scene.json'
    wait(lambda: observation().get('native_push_allocation') == [220, 80], 90)
    applied = scene.read_bytes()
    baseline = json.loads(working.read_text())
    proposal = copy.deepcopy(baseline)
    proposal['name'] = 'Proposta GTK3 ainda nao aplicada'
    proposal['recipes']['gtk3']['sizes'][0] = [330, 110]
    source = output / 'home/pending.json'

    def data(value):
        result = copy.deepcopy(value); result.pop('exported_at', None)
        return result

    def load(value):
        source.write_text(json.dumps(value))
        click('load'); wait(lambda: observation().get('file_path'))
        subprocess.run(['xdotool', 'windowfocus', str(observation()['file_window'])],
                       env=environment, check=True, timeout=5)
        click('file_path')
        subprocess.run(['xdotool', 'key', '--clearmodifiers', 'ctrl+a'],
                       env=environment, check=True, timeout=5)
        subprocess.run(['xdotool', 'type', '--clearmodifiers', '--delay', '1', HOME + '/pending.json'],
                       env=environment, check=True, timeout=10)
        click('file_ok')
        wait(lambda: json.loads(working.read_text()).get('name') == value['name'])
        assert data(json.loads(working.read_text())) == data(value)
        assert scene.read_bytes() == applied

    load(proposal)
    restart()
    wait(lambda: observation().get('native_push_allocation') == [220, 80], 90)
    assert scene.read_bytes() == applied, 'GTK restart rewrote the unchanged applied scene'
    assert data(json.loads(working.read_text())) == data(proposal)
    assert observation()['width_text'] == '330'

    other = copy.deepcopy(proposal)
    other['name'] = 'Proposta Qt6 com cena GTK3 preservada'
    other['selected_family'] = 'qt6'
    other['recipes']['qt6']['sizes'][0] = [410, 140]
    load(other)
    restart()
    wait(lambda: observation().get('native_push_allocation') == [220, 80], 90)
    assert scene.read_bytes() == applied
    assert data(json.loads(working.read_text())) == data(other)
    assert observation()['width_text'] == '410'
    # Select the real GTK3 scene while another recipe is in the editor.
    # This must preserve the Qt6 proposal and expose the selected scene recipe.
    x, y, _width, _height = observation()['canvas']
    subprocess.run(['xdotool', 'mousemove', str(x + 70), str(y + 90),
                    'keydown', 'Control_L', 'click', '1', 'keyup', 'Control_L'],
                   env=environment, check=True, timeout=5)
    wait(lambda: json.loads(working.read_text())['selected_family'] == 'gtk3', 10)
    selected = json.loads(working.read_text())
    assert selected['recipes'] == other['recipes'], 'Scene selection changed a pending recipe'
    assert scene.read_bytes() == applied, 'Selection applied a pending proposal'
    wait(lambda: observation().get('width_text') == '330', 5)
    origin = selected['recipes']['gtk3']['positions'][0]
    subprocess.run(['xdotool', 'mousemove', str(x + 70), str(y + 90),
                    'keydown', 'Control_L', 'mousedown', '1', 'sleep', '0.15',
                    'mousemove', str(x + 110), str(y + 110), 'sleep', '0.15',
                    'mouseup', '1', 'keyup', 'Control_L'],
                   env=environment, check=True, timeout=5)
    destination = [origin[0] + 40, origin[1] + 20]
    wait(lambda: json.loads(working.read_text())['recipes']['gtk3']['positions'][0] == destination, 15)
    moved = json.loads(working.read_text())
    expected = copy.deepcopy(selected)
    expected['recipes']['gtk3']['positions'][0] = destination
    assert data(moved) == data(expected), 'Drag changed another pending setting'
    wait(lambda: json.loads(scene.read_text())['recipes']['gtk3']['positions'][0] == destination, 15)
    moved_scene = json.loads(scene.read_text())
    expected_scene = json.loads(applied)
    expected_scene['recipes']['gtk3']['positions'][0] = destination
    assert data(moved_scene) == data(expected_scene), 'Drag applied a pending size or other recipe'
    wait(lambda: observation().get('native_push_allocation') == [220, 80], 90)
    return {'status': 'passed', 'scope': 'Native GTK3 startup, two resumes with different pending dimensions and then Qt6 editor selection; original GTK3 scene bytes/hash and actual allocation preserved; proposal fields/history independent; no Qt6 painting claim',
            'applied_allocation': [220, 80], 'gtk3_pending': [330, 110],
            'qt6_pending': [410, 140], 'scene_bytes_preserved': True, 'cross_family_native_selection_preserved_recipes': True, 'native_drag_changed_only_gtk3_position': True}
