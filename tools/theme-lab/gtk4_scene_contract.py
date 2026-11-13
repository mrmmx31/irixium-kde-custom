# SPDX-License-Identifier: GPL-3.0-or-later
"""GTK4 layout validation, limited to the implemented push renderer."""
from scene_contract import scene
from gtk2_buttons import geometry


def push_records(model):
    records = [record for record in scene(model, 'gtk4') if record['id'] == 'push']
    geometry(model['recipes']['gtk4'])
    return records
