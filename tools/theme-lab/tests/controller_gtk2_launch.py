# SPDX-License-Identifier: GPL-3.0-or-later
"""GTK2 assertions shared with the existing real bwrap controller harness."""
import json


def run(output, observation, click, wait, move_separate):
    def bars(width, separate=False):
        rows = observation().get('native_bars', [])
        expected = 4 if separate else 2
        if len(rows) != expected:
            return None
        for row in rows:
            if row['control'] == 10 and (row['width'], row['height']) != (width, 15):
                return None
            if row['control'] == 11 and (row['width'], row['height']) != (15, 180):
                return None
        return rows
    wait(lambda: observation().get('window'))
    initial = wait(lambda: bars(220))
    click('separatePreview')
    both = wait(lambda: bars(220, True))
    move_separate()
    (output / 'home/reveal-spin').write_text('set-width 280')
    wait(lambda: observation().get('width_text') == '280')
    click('apply')
    changed = wait(lambda: bars(280, True))
    assert "GTK2 acoplado" in observation().get("metrics", "")
    assert "GTK2 separado" in observation().get("metrics", "")
    assert "GTK3 acoplado" not in observation().get("metrics", "")
    move_separate()
    project = json.loads((output / 'home/lab/working.json').read_text())
    assert project['recipes']['gtk2']['sizes'][10][0] == 280
    assert project['recipes']['gtk3']['sizes'][10][0] == 220
    generation = json.loads((output / 'home/lab/generated/latest.json').read_text())
    local = output / 'home' / generation['generation_dir'].removeprefix('/home/domainos-test/')
    receipt = json.loads((local / 'RESULTADO.json').read_text())
    assert receipt['status'] == 'partially_generated'
    assert receipt['families']['gtk2']['translated_controls'] == ['push', 'toggle', 'scroll_h', 'scroll_v']
    assert not receipt['families']['gtk2']['recipe_applied']
    click('separatePreview')
    # Check the controller toggle; earlier measurements do not prove process closure.
    wait(lambda: not observation().get('separate_preview_checked', True), 5)
    return {'status': 'passed', 'scope': 'Real Motif controller GTK2 startup, detached toggle and Apply in bwrap',
            'initial': initial, 'both': both, 'changed': changed,
            'gtk3_recipe_unchanged': True, 'partial_recipe_not_claimed_complete': True}
