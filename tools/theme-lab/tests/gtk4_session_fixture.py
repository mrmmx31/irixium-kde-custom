# SPDX-License-Identifier: GPL-3.0-or-later
"""Real GTK4 session replacement/rollback checks in a private test window."""
import copy
import ctypes as C
import io
import subprocess
from PIL import Image, ImageChops
from gtk4_push_api import PushAPI
from gtk4_push_session import PushSession
from test_backend import backend, model


def verify_session(window, window_id, builder, palette, output, drain, bind, gtk):
    api = PushAPI()
    project = model()
    recipe = project['recipes']['gtk4']
    recipe.update(visible_controls=1, selected_control=0, edit_state=0,
                  sizes=[[160, 60]] + [[0, 0] for _ in range(15)],
                  positions=[[32, 32]] + [[0, 0] for _ in range(15)])
    activated = []
    session = PushSession(api, window, builder, activated.append)
    allocated_width = bind(gtk, 'gtk_widget_get_allocated_width', C.c_int, C.c_void_p)
    allocated_height = bind(gtk, 'gtk_widget_get_allocated_height', C.c_int, C.c_void_p)
    flags = bind(gtk, 'gtk_widget_get_state_flags', C.c_uint, C.c_void_p)
    tooltip = bind(gtk, 'gtk_widget_get_tooltip_text', C.c_char_p, C.c_void_p)
    grab_focus = bind(gtk, 'gtk_widget_grab_focus', C.c_int, C.c_void_p)
    rows = []

    def screen():
        raw = subprocess.check_output(['import', '-window', hex(window_id), 'png:-'], timeout=5)
        return Image.open(io.BytesIO(raw)).convert('RGB')

    def check(state, record, name):
        button = session.scene.widgets[0]
        assert tooltip(button).decode('utf-8').startswith('GTK4 nativo.')
        assert [allocated_width(button), allocated_height(button)] == record['size']
        actual = screen()
        actual.save(output / (name + '.png'))
        canvas_flags = flags(session.scene.fixed)
        canvas_index = 2 if canvas_flags & 8 else 1 if canvas_flags & 64 else 0
        canvas_color = builder.art._rgb(palette[builder.art.ROLES['window'][canvas_index]])
        assert actual.getpixel((2, 2)) == canvas_color
        x, y = record['position']; width, height = record['size']
        effective = dict(palette)
        index = 2 if state == 2 else 1 if state == 3 else 0
        for role in ('button', 'button-fg'):
            effective[builder.art.ROLES[role][0]] = palette[builder.art.ROLES[role][index]]
        shadow = recipe['geometry']['shadow_px']
        with backend.recipe_rules(builder, recipe['palette']):
            expected = Image.open(io.BytesIO(builder.png(
                builder.art.bevel(builder.art.blank(width, height, 'face'),
                                  thickness=shadow, down=state == 1),
                'button', effective))).convert('RGB')
        image = actual.crop((x, y, x + width, y + height))
        edge = [(a, b) for b in range(height) for a in range(width)
                if min(a, b, width-1-a, height-1-b) < shadow]
        differences = sum(image.getpixel(p) != expected.getpixel(p) for p in edge)
        assert differences == 0, (name, differences)
        rows.append({'capture': name, 'edge_pixels': len(edge),
                     'edge_differences': differences, 'canvas_role_verified': True,
                     'flags': flags(button), **record})
        return actual

    try:
        previous = None
        for state in range(4):
            recipe['edit_state'] = state
            session.replace(project, palette, output / ('session-state-' + str(state)))
            drain()
            if previous:
                assert not previous.handlers and previous.fixed is None
            previous = session.scene
            check(state, {'position': [32, 32], 'size': [160, 60]}, 'session-state-' + str(state))
        assert not activated
        recipe['edit_state'] = 0
        recipe['positions'][0] = [20, 20]
        recipe['sizes'][0] = [180, 64]
        session.replace(project, palette, output / 'session-resized')
        drain()
        accepted = session.scene
        baseline = check(0, {'position': [20, 20], 'size': [180, 64]}, 'session-resized')
        bad_css = output / 'invalid.css'
        bad_css.write_text('button { color: ; }', encoding='utf-8')
        try:
            api.css_provider(bad_css)
            raise AssertionError('Malformed CSS accepted')
        except ValueError as error:
            assert 'GTK4 CSS:' in str(error)
        assert session.scene is accepted
        invalid = copy.deepcopy(project)
        invalid['recipes']['gtk4']['visible_controls'] = 3
        invalid_dir = output / 'session-invalid'
        try:
            session.replace(invalid, palette, invalid_dir)
            raise AssertionError('Unsupported control accepted')
        except ValueError as error:
            assert 'renderers pending' in str(error)
        assert not invalid_dir.exists() and session.scene is accepted
        failed = []

        def fail_after_transfer(candidate):
            failed.append(candidate)
            raise RuntimeError('Injected transfer failure')

        try:
            session.replace(project, palette, output / 'session-rollback', fail_after_transfer)
            raise AssertionError('Injected failure ignored')
        except RuntimeError as error:
            assert 'Injected transfer failure' in str(error)
        drain()
        assert session.scene is accepted
        assert not failed[0].handlers and failed[0].fixed is None
        restored = screen(); restored.save(output / 'session-restored.png')
        assert ImageChops.difference(baseline, restored).getbbox() is None
        subprocess.run(['xdotool', 'mousemove', '--window', str(window_id),
                        '100', '50', 'click', '1'], check=True, timeout=5)
        drain()
        assert activated == [0], activated
        assert grab_focus(session.scene.widgets[0])
        subprocess.run(['xdotool', 'windowfocus', '--sync', str(window_id),
                        'key', 'space'], check=True, timeout=5)
        drain()
        assert activated == [0, 0], activated
        return {'rows': rows, 'rollback_image_equal': True,
                'malformed_css_rejected': True,
                'unsupported_refused_before_output': True,
                'failed_candidate_closed': True, 'old_handlers_disconnected': True,
                'artificial_clicks': 0, 'physical_clicks_after_rollback': 1,
                'keyboard_space_activations': 1,
                'persistent_native_window': window_id}
    finally:
        session.close()
