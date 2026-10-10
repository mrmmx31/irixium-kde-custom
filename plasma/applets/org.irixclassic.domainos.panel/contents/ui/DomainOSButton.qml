// SPDX-FileCopyrightText: 2026 IRIX Classic contributors
// SPDX-License-Identifier: GPL-3.0-or-later
import QtQuick
import org.kde.plasma.components as PlasmaComponents

// Use KDE's native SVG control and its public Qt button actions. The popup
// layout keeps the desktop style's text-button minimum; explicit compact sizes
// still take precedence. The main panel artwork is a separate component.
PlasmaComponents.Button {
    id: button
    implicitWidth: Math.max(text && display !== PlasmaComponents.AbstractButton.IconOnly ? 80 : 0,
                            implicitBackgroundWidth + leftInset + rightInset,
                            implicitContentWidth + leftPadding + rightPadding)
    DomainOSControlPalette { target: button }
}
