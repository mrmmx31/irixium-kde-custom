// SPDX-FileCopyrightText: 2026 IRIX Classic contributors
// SPDX-License-Identifier: GPL-3.0-or-later
import QtQuick
import org.kde.plasma.private.keyboardindicator as KeyboardIndicator

// The standard Plasma dock does not accept keyboard focus. Its own modifier
// backend observes these two states without taking focus or grabbing keys.
QtObject {
    id: modifiers
    property bool ready: false
    readonly property int pressedModifiers: (control.pressed ? Qt.ControlModifier : 0)
        | (shift.pressed ? Qt.ShiftModifier : 0)
    signal released(int remainingModifiers, int key)
    property QtObject control: KeyboardIndicator.KeyState {
        key: Qt.Key_Control
        onPressedChanged: if (modifiers.ready && !pressed)
            modifiers.released(modifiers.pressedModifiers, Qt.Key_Control)
    }
    property QtObject shift: KeyboardIndicator.KeyState {
        key: Qt.Key_Shift
        onPressedChanged: if (modifiers.ready && !pressed)
            modifiers.released(modifiers.pressedModifiers, Qt.Key_Shift)
    }
    Component.onCompleted: ready = true
}
