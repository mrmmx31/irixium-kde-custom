// SPDX-FileCopyrightText: 2026 IRIX Classic contributors
// SPDX-License-Identifier: GPL-3.0-or-later
import QtQuick
import org.kde.plasma.components as PlasmaComponents
import org.kde.kirigami as Kirigami

// Keep Qt Dialog's standardButtons and action roles. Its native footer wiring
// forwards accepted/rejected; only this panel's button rendering changes.
PlasmaComponents.DialogButtonBox {
    id: box
    visible: count > 0

    delegate: DomainOSButton {
        // Match PlasmaComponents' own delegate sizing, including its spacing
        // and padding. The local button keeps its normal implicit minimum.
        width: Math.min(implicitWidth,
            box.width / box.count - box.rightPadding - box.spacing * (box.count - 1))
        Kirigami.MnemonicData.controlType: Kirigami.MnemonicData.DialogButton
    }
}
