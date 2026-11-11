# SPDX-License-Identifier: GPL-3.0-or-later
"""GTK2 lifecycle bridge for independent runtime sample journals."""
from preview_sample_journal import SampleJournal
from preview_runtime_journal import RuntimeJournal
import gtk2_runtime_state as runtime

CONTROL_IDS = {4: 'entry', 6: 'spin', 7: 'text'}


class SampleState:
    def __init__(self, directory, origin):
        self.journal = SampleJournal(directory, 'gtk2', origin)
        self.runtime_journal = RuntimeJournal(directory, 'gtk2', origin)
        self.runtime_states = self.runtime_journal.load()
        self.histories = {index: history for name, history in self.journal.load().items()
                          for index, control in CONTROL_IDS.items() if control == name}

    def seed_runtime(self, scene, toggle=None, check=None, radio=None):
        # Controller cache is a fallback only. A completed journal checkpoint
        # must win even if a preceding native event was not yet consumed by C.
        for value in (toggle, check, radio):
            if value is not None and (type(value) is not int or value not in (0, 1)):
                raise ValueError('Cache inicial GTK2 inválido.')
        for index, name, value in ((1, 'toggle', toggle), (2, 'check', check)):
            if value is not None and name not in self.runtime_states and index in scene.widgets:
                scene.widgets[index].set_active(bool(value))
        if radio is not None and 'radio' not in self.runtime_states and 3 in scene.radio_groups:
            scene.radio_groups[3].select(radio)

    def restore_runtime(self, scene):
        runtime.restore(scene, self.runtime_states)

    def checkpoint(self, scene, capture=True):
        # Selection changes do not emit changed; capture them before publication.
        # After native destruction only the already flushed history is accessed.
        if capture:
            for editor in scene.text_editors.values():
                editor.flush()
                editor.history.remember_selection(editor.read())
        if capture:
            self.runtime_states = runtime.capture(scene, self.runtime_states)
        self.histories = scene.text_histories
        text_changed = self.journal.save({CONTROL_IDS[index]: history
                                  for index, history in self.histories.items()})
        runtime_changed = self.runtime_journal.save(self.runtime_states)
        return text_changed or runtime_changed
