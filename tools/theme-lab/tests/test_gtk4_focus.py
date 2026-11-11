# SPDX-License-Identifier: GPL-3.0-or-later
import unittest
from gtk4_focus import FocusKeys, traversal_direction


class FocusPolicyTests(unittest.TestCase):
    def test_boundary_keys_and_application_shortcuts(self):
        self.assertIs(traversal_direction(0xff09,0),False)
        self.assertIs(traversal_direction(0xff09,1),True)
        self.assertIs(traversal_direction(0xfe20,0),True)
        for key, modifiers in ((0xff09,4),(0xff09,8),(0xff09,1<<26),(0x20,0),(0x7a,4)):
            self.assertIsNone(traversal_direction(key,modifiers))

    def test_failed_callback_does_not_swallow_native_key_or_claim_success(self):
        class Bridge:
            def traverse(self, backward):
                raise OSError('temporary observation failure')
        keys=FocusKeys.__new__(FocusKeys)
        keys.bridge=Bridge();keys.requests=[];keys.last_error=None
        self.assertEqual(keys.key_pressed(None,0xff09,0,0,None),0)
        self.assertEqual(keys.requests,[])
        self.assertIn('temporary',keys.last_error)

    def test_request_history_is_bounded(self):
        class Bridge:
            def traverse(self, backward):pass
        keys=FocusKeys.__new__(FocusKeys)
        keys.bridge=Bridge();keys.requests=[];keys.last_error='old'
        for _ in range(80):self.assertEqual(keys.key_pressed(None,0xff09,0,0,None),1)
        self.assertEqual(len(keys.requests),32)
        self.assertIsNone(keys.last_error)


if __name__=='__main__':unittest.main()
