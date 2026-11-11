# SPDX-License-Identifier: GPL-3.0-or-later
"""Native tree clicks preserve recipe masks/positions through save and load."""
import json
import subprocess


def run(output, observation, click, wait, environment):
    working = output / 'home/lab/working.json'
    wait(lambda: observation().get('catalogControl2'), 30)
    initial = json.loads(working.read_text())['recipes']['gtk3']
    positions = initial['positions']; controls = initial['visible_controls']
    categories = initial['visible_categories']

    def recipe():
        return json.loads(working.read_text())['recipes']['gtk3']

    def tree(kind, index):
        command = output / 'home/reveal-spin'
        command.write_text(f'tree {kind} {index}')
        wait(lambda: not command.exists(), 5)
        click(f'catalog{kind}{index}')

    def key(*args):
        subprocess.run(['xdotool', 'key', '--clearmodifiers', *args], env=environment, check=True, timeout=5)

    def file_dialog(action, path):
        click(action); wait(lambda: observation().get('file_path'), 10)
        subprocess.run(['xdotool', 'windowfocus', str(observation()['file_window'])], env=environment, check=True)
        click('file_path'); key('ctrl+a')
        subprocess.run(['xdotool', 'type', '--clearmodifiers', '--delay', '1', path], env=environment, check=True)
        click('file_ok'); wait(lambda: not observation().get('file_path'), 10)

    tree('Expand', 0); wait(lambda: observation().get('catalog_children0') is False, 5)
    assert recipe()['visible_controls'] == controls and recipe()['visible_categories'] == categories
    tree('CategoryCheck', 0); wait(lambda: recipe()['visible_categories'] == categories & ~1, 10)
    assert recipe()['visible_controls'] == controls
    tree('Expand', 0); wait(lambda: observation().get('catalog_children0') is True, 5)
    tree('Control', 2); wait(lambda: recipe()['selected_control'] == 2, 10)
    tree('Check', 2); wait(lambda: recipe()['visible_controls'] == controls & ~4, 10)
    assert recipe()['selected_control'] == 2
    tree('CategoryCheck', 0); wait(lambda: recipe()['visible_categories'] == categories, 10)
    assert recipe()['visible_controls'] == controls & ~4 and recipe()['positions'] == positions
    file_dialog('save', '/home/domainos-test/catalog-saved.json')
    saved = json.loads((output / 'home/catalog-saved.json').read_text())['recipes']['gtk3']
    assert saved['visible_controls'] == controls & ~4 and saved['selected_control'] == 2
    tree('Check', 2); wait(lambda: recipe()['visible_controls'] == controls, 10)
    file_dialog('load', '/home/domainos-test/catalog-saved.json')
    wait(lambda: recipe()['visible_controls'] == controls & ~4, 10)
    assert recipe()['selected_control'] == 2 and recipe()['positions'] == positions
    assert recipe()['visible_categories'] == categories
    return {'status': 'passed', 'scope': 'Actual Motif pointer clicks collapse/expand category, toggle category visibility without losing member choices, select by label, toggle member checkbox without changing selection, preserve all positions and restore masks/selection through native Save/Load. Expansion is current view state, not project data. No toolkit fidelity claim.',
            'selected_control': 2, 'positions_preserved': True, 'saved_visibility_restored': True}
