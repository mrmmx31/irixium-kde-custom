# SPDX-License-Identifier: GPL-3.0-or-later
"""Native catalog categories/member keyboard input and independent families."""
import json
import subprocess


def run(output, observation, click, wait, environment, families_only=False):
    working = output / 'home/lab/working.json'
    wait(lambda: observation().get('catalogControl15'), 30)
    original = json.loads(working.read_text())

    def project():
        return json.loads(working.read_text())

    def recipe(family='gtk3'):
        return project()['recipes'][family]

    def key(*args):
        subprocess.run(['xdotool', 'key', '--clearmodifiers', *args], env=environment, check=True, timeout=5)

    def reveal(command):
        path = output / 'home/reveal-spin'; path.write_text(command)
        written = path.stat().st_mtime_ns
        wait(lambda: not path.exists(), 5)
        wait(lambda: (output / 'home/probe.json').stat().st_mtime_ns > written, 5)

    def tree(kind, index):
        reveal(f'tree {kind} {index}')
        def visible():
            data = observation()
            x, y, width, height = data[f'catalog{kind}{index}']
            cx, cy, cw, ch = data['recipe_clip']
            return cx <= x and cy <= y and x + width <= cx + cw and y + height <= cy + ch
        wait(visible, 5)
        click(f'catalog{kind}{index}')

    base_categories = recipe()['visible_categories']
    base_controls = recipe()['visible_controls']
    if not families_only:
        for category in range(5):
            tree('Expand', category)
            wait(lambda: observation().get(f'catalog_children{category}') is False, 5)
            key('space')
            wait(lambda: observation().get(f'catalog_children{category}') is True, 5)
            tree('CategoryCheck', category)
            wait(lambda: recipe()['visible_categories'] == base_categories & ~(1 << category), 10)
            assert recipe()['visible_controls'] == base_controls
            key('space')
            wait(lambda: recipe()['visible_categories'] == base_categories, 10)
        for control in range(16):
            selected_before = recipe()['selected_control']
            tree('Check', control)
            wait(lambda: recipe()['visible_controls'] == base_controls & ~(1 << control), 10)
            assert recipe()['selected_control'] == selected_before
            key('space'); wait(lambda: recipe()['visible_controls'] == base_controls, 10)
            tree('Control', control)
            wait(lambda: recipe()['selected_control'] == control, 10)
        assert recipe()['positions'] == original['recipes']['gtk3']['positions']
    else:
        tree('Control', 15)
        wait(lambda: recipe()['selected_control'] == 15, 10)
    tree('Check', 15)
    wait(lambda: recipe()['visible_controls'] == base_controls & ~(1 << 15), 10)
    saved_gtk3 = recipe()

    def family(index, name):
        # Exercise the real ComboBox callback deterministically through its
        # internal XmList; popup placement is tested separately by the native
        # pointer flow and is not part of this persistence check.
        reveal(f'family-select {index}')
        wait(lambda: project()['selected_family'] == name, 10)

    family(0, 'motif')
    assert recipe('gtk3') == saved_gtk3
    wait(lambda: json.loads((output / 'home/lab/scene.json').read_text()).get(
        'selected_family') == 'motif', 10)
    applied_after_selection = json.loads((output / 'home/lab/scene.json').read_text())
    assert applied_after_selection['selected_family'] == 'motif'
    assert applied_after_selection['recipes']['gtk3'] == original['recipes']['gtk3']
    assert recipe('motif')['visible_controls'] == original['recipes']['motif']['visible_controls']
    tree('Check', 5)
    wait(lambda: recipe('motif')['visible_controls'] == original['recipes']['motif']['visible_controls'] & ~(1 << 5), 10)
    tree('Control', 4)
    wait(lambda: recipe('motif')['selected_control'] == 4, 10)
    mask_before_return = recipe('motif')['visible_controls']
    reveal('focus-control 5')
    wait(lambda: observation().get('keyboard_focus') == 'catalogControl5', 5)
    assert recipe('motif')['selected_control'] == 4
    key('Return')
    wait(lambda: recipe('motif')['selected_control'] == 5, 10)
    assert recipe('motif')['visible_controls'] == mask_before_return
    saved_motif = recipe('motif')
    family(3, 'gtk3')
    assert recipe() == saved_gtk3 and recipe('motif') == saved_motif
    click('apply')
    wait(lambda: json.loads((output / 'home/lab/scene.json').read_text()).get('selected_family') == 'gtk3', 10)
    assert project()['selected_family'] == 'gtk3'
    family_rows = (
        (1, 'gtk1'), (2, 'gtk2'), (4, 'gtk4'), (5, 'gtk5'),
        (6, 'qt5'), (7, 'qt6'), (8, 'kvantum'), (9, 'plasma'),
    )
    for index, name in family_rows:
        family(index, name)
        click('apply')
        wait(lambda name=name: json.loads(
            (output / 'home/lab/scene.json').read_text()).get('selected_family') == name, 10)
        assert project()['selected_family'] == name
    family(0, 'motif')
    assert recipe('motif') == saved_motif and recipe('gtk3') == saved_gtk3
    for name, before in original['recipes'].items():
        if name not in ('gtk3', 'motif'):
            assert project()['recipes'][name] == before, name
    return {'status': 'passed', 'scope': ('Independent family selection callbacks plus Apply persistence via the native ComboBox XmList and catalog member selection only; ' if families_only else 'Real pointer and Space across five categories/16 checkboxes; ') + 'GTK3→Motif→GTK3→Apply, then GTK1/GTK2/GTK4/GTK5/Qt5/Qt6/Kvantum/Plasma Apply, and return to Motif preserve the selected family and independent masks/selected controls/positions. No adapter or visual fidelity claim.',
            'categories_checked': 0 if families_only else 5, 'members_checked': 0 if families_only else 16, 'keyboard': ['Return'] if families_only else ['Space', 'Return'],
            'family_rows_checked': 10,
            'return_selects_different_member_without_toggling_visibility': True,
            'family_selection_does_not_apply_pending_recipe': True,
            'family_recipes_independent': True, 'positions_preserved': True}
