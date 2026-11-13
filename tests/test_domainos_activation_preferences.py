#!/usr/bin/python3
# SPDX-License-Identifier: GPL-3.0-or-later
"""Guard loss of customized task/tray preferences during full replacement."""
import copy
from pathlib import Path
import sys
import unittest

sys.dont_write_bytecode = True
sys.path.insert(0, str(Path(__file__).resolve().parents[1] / 'tools'))
import activate_domainos as activation
from theme_transaction import Failure


def widget(kind, entries, **extra):
    return {'type': kind, 'config': {'entries': {}, 'groups': {'General': {'entries': entries, 'groups': {}}}}, **extra}


class PreferenceMigrationTests(unittest.TestCase):
    def test_customized_filters_gestures_grouping_and_native_values(self):
        before = {'widgets': [widget('org.irixclassic.iconbox', {
            'showOnlyCurrentDesktop': 'false', 'showOnlyCurrentScreen': 'true',
            'showOnlyCurrentActivity': 'false', 'showOnlyMinimized': 'true',
            'onlyGroupWhenFull': 'false', 'groupingStrategy': '0', 'sortingStrategy': '4',
            'groupingAppIdBlacklist': r'foo.desktop,bar\,baz.desktop',
            'groupingLauncherUrlBlacklist': ['applications:foo.desktop'],
            'middleClickAction': '1', 'wheelEnabled': 'false', 'wheelSkipMinimized': 'false',
            'showToolTips': 'false', 'interactiveMute': 'false', 'highlightWindows': 'false',
            'unhideOnAttention': 'false', 'groupedTaskVisualization': '2', 'maxStripes': '4',
        })]}
        snapshot = copy.deepcopy(before)
        settings, tray = activation.seed_preferences(before)
        self.assertEqual(settings, {
            'tasksOnlyCurrentDesktop': False, 'tasksOnlyCurrentScreen': True,
            'tasksOnlyCurrentActivity': False, 'tasksFilterMode': 'minimized',
            'tasksOnlyGroupWhenFull': False, 'tasksGroupingMode': 0, 'tasksSortMode': 4,
            'tasksGroupingAppIdBlacklist': ['foo.desktop', 'bar,baz.desktop'],
            'tasksGroupingLauncherUrlBlacklist': ['applications:foo.desktop'],
            'middleClickAction': 1, 'wheelEnabled': False, 'wheelSkipMinimized': False,
            'iconboxHintsEnabled': False, 'interactiveMute': False, 'highlightWindows': False,
            'unhideOnAttention': False,
        })
        self.assertIsNone(tray)
        self.assertEqual(before, snapshot)
        self.assertNotIn('iconboxWheelActivates', settings)  # New approved default: browse.
        self.assertNotIn('iconboxWindowThumbnails', settings)  # New default: titles.

    def test_tray_source_retains_complete_children_and_visibility(self):
        tray = {'id': 42, 'config': {'groups': {'General': {'entries': {
            'shownItems': 'org.kde.plasma.volume', 'hiddenItems': 'test.application',
            'extraItems': 'org.kde.plasma.volume', 'showAllItems': 'false',
        }}}}, 'widgets': [widget('org.kde.plasma.volume', {'raiseMaximumVolume': 'true'}, shortcut='Meta+V')]}
        before = {'widgets': [widget('org.irixclassic.systemtray', {}, tray=tray)]}
        untouched = copy.deepcopy(before)
        settings, saved = activation.seed_preferences(before)
        self.assertEqual(settings, {'trayVisibleItems': ['org.kde.plasma.volume'], 'trayHiddenItems': ['test.application']})
        self.assertEqual(saved, untouched['widgets'][0]['tray'])
        self.assertNotIn('trayOrder', settings)  # Numeric applet IDs are not visual item IDs.
        self.assertEqual(before, untouched)

    def test_no_source_manager_preserves_new_approved_defaults(self):
        self.assertEqual(activation.seed_preferences({'widgets': [widget('org.kde.plasma.pager', {})]}), ({}, None))

    def test_native_task_variants_and_typed_values(self):
        for kind in ('org.kde.plasma.taskmanager', 'org.kde.plasma.icontasks'):
            settings, _ = activation.seed_preferences({'widgets': [widget(kind, {
                'showOnlyCurrentDesktop': False, 'groupingStrategy': 1, 'sortingStrategy': 5,
                'showOnlyMinimized': False, 'groupingAppIdBlacklist': ['x', 'x', 'y'],
            })]})
            self.assertEqual(settings['tasksFilterMode'], 'normal')
            self.assertEqual(settings['tasksGroupingAppIdBlacklist'], ['x', 'y'])
            self.assertEqual(settings['tasksSortMode'], 5)

    def test_refuses_ambiguous_source_before_any_mutation(self):
        for kind in ('org.irixclassic.iconbox', 'org.kde.plasma.systemtray'):
            with self.assertRaisesRegex(Failure, 'múltiplos'):
                activation.seed_preferences({'widgets': [widget(kind, {}), widget(kind, {})]})

    def test_refuses_invalid_explicit_choices_and_missing_tray(self):
        for key, value in (('showOnlyMinimized', 'yes'), ('groupingStrategy', '9'),
                           ('sortingStrategy', '-1'), ('middleClickAction', True),
                           ('groupingAppIdBlacklist', [4])):
            with self.assertRaises(Failure):
                activation.seed_preferences({'widgets': [widget('org.irixclassic.iconbox', {key: value})]})
        with self.assertRaisesRegex(Failure, 'Snapshot'):
            activation.seed_preferences({'widgets': [widget('org.irixclassic.systemtray', {})]})

    def test_destructive_commit_requires_matching_independent_native_choices(self):
        original_tray = {'id': 7, 'config': {'entries': {}, 'groups': {}}, 'widgets': [
            {'id': 8, **widget('org.kde.plasma.volume', {'volumeStep': '3'}, shortcut='', background='StandardBackground')}]}
        replacement = copy.deepcopy(original_tray)
        replacement['id'] = 70
        replacement['widgets'][0]['id'] = 80
        settings = {'tasksOnlyCurrentDesktop': False, 'tasksFilterMode': 'minimized', 'trayHiddenItems': ['some.service']}
        created = {'widgets': [widget(activation.PLUGIN, {
            'tasksOnlyCurrentDesktop': 'false', 'tasksFilterMode': 'minimized', 'trayHiddenItems': 'some.service',
        }, tray=replacement)]}
        self.assertTrue(activation.verify_seed(created, settings, original_tray))
        for mutate in (
            lambda value: value['widgets'][0]['config']['groups']['General']['entries'].update(tasksOnlyCurrentDesktop='true'),
            lambda value: value['widgets'][0]['tray'].update(id=7),
            lambda value: value['widgets'][0]['tray']['widgets'][0].update(id=8),
            lambda value: value['widgets'][0]['tray']['widgets'][0]['config']['groups']['General']['entries'].update(volumeStep='5'),
            lambda value: value['widgets'][0]['tray']['widgets'].clear(),
        ):
            changed = copy.deepcopy(created)
            mutate(changed)
            self.assertFalse(activation.verify_seed(changed, settings, original_tray))


if __name__ == '__main__':
    unittest.main()
