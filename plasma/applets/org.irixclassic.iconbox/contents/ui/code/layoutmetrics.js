/*
    SPDX-FileCopyrightText: 2012-2013 Eike Hein <hein@kde.org>
    SPDX-FileCopyrightText: 2026 mrmmx31

    SPDX-License-Identifier: GPL-2.0-or-later
*/

.import org.kde.kirigami as Kirigami

const iconMargin = 1;
const labelMargin = Kirigami.Units.smallSpacing;

function horizontalMargins() {
    return taskFrame.margins.left + taskFrame.margins.right;
}

function verticalMargins() {
    return taskFrame.margins.top + taskFrame.margins.bottom;
}

function adjustMargin(height, margin) {
    const available = height - verticalMargins();
    if (available > 0 && available < Kirigami.Units.iconSizes.small) {
        return Math.floor((margin * (Kirigami.Units.iconSizes.small / available)) / 3);
    }
    return margin;
}

function maxStripes() {
    return 1;
}

function optimumCapacity(width, height) {
    const length = tasks.vertical ? height : width;
    const maximum = tasks.vertical ? preferredMaxHeight() : preferredMaxWidth();
    return Math.max(1, Math.floor((length - tasks.frameInset * 2) / maximum));
}

function preferredMinWidth() {
    return 64;
}

function preferredMaxWidth() {
    // Keep the native Narrow/Medium/Wide setting inside compact iconbox bounds.
    const choice = Math.max(0, Math.min(2, tasks.plasmoid.configuration.taskMaxWidth));
    return 64 + choice * 10;
}

function preferredMinHeight() {
    // 28 px icon well + a separate 14 px caption fit below the heading
    // inside the 56 px applet area of a 64 px Plasma panel.
    return 42;
}

function preferredMaxHeight() {
    return 56;
}

function preferredHeightInPopup() {
    // Native group popups keep their icon-and-window-title rows.
    return verticalMargins() + Math.max(Kirigami.Units.iconSizes.sizeForLabels,
                                        Kirigami.Units.iconSizes.medium);
}

function spaceRequiredToShowText() {
    return Math.round(Kirigami.Units.gridUnit * 1.5);
}

function preferredMinLauncherWidth() {
    return preferredMinWidth();
}

function maximumContextMenuTextWidth() {
    return Kirigami.Units.iconSizes.sizeForLabels * 28;
}
