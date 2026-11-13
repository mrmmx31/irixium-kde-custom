// SPDX-FileCopyrightText: 2026 IRIX Classic contributors
// SPDX-License-Identifier: GPL-3.0-or-later
import QtQuick
import org.kde.plasma.components as PlasmaComponents

// Native Plasma SVG painting follows the KDE scheme without Kvantum's static
// QStyle brush. Keep the previous popup field's minimum width and padding.
PlasmaComponents.TextField {
    id: field
    topPadding: 6
    bottomPadding: 6
    leftPadding: 6
    rightPadding: 6
    implicitWidth: Math.max(200, implicitBackgroundWidth + leftInset + rightInset,
                            contentWidth + leftPadding + rightPadding,
                            placeholderMetrics.width + leftPadding + rightPadding)
    implicitHeight: Math.max(30, implicitBackgroundHeight + topInset + bottomInset,
                             fontMetrics.height + topPadding + bottomPadding)
    FontMetrics { id: fontMetrics; font: field.font }
    TextMetrics { id: placeholderMetrics; font: field.font; text: field.placeholderText }
    DomainOSControlPalette { target: field }
}
