/*
    SPDX-FileCopyrightText: 2013 Eike Hein <hein@kde.org>
    SPDX-FileCopyrightText: 2026 mrmmx31

    SPDX-License-Identifier: GPL-2.0-or-later
*/

import QtQuick
import QtQuick.Controls as QQC2
import QtQuick.Layouts

import org.kde.kcmutils as KCMUtils
import org.kde.kirigami as Kirigami
import org.kde.plasma.core as PlasmaCore
import org.kde.plasma.plasmoid

KCMUtils.SimpleKCM {
    readonly property bool plasmaPaAvailable: Qt.createComponent("PulseAudio.qml").status === Component.Ready
    readonly property bool plasmoidVertical: Plasmoid.formFactor === PlasmaCore.Types.Vertical
    readonly property bool iconOnly: Plasmoid.pluginName === "org.kde.plasma.icontasks"

    property alias cfg_showToolTips: showToolTips.checked
    property alias cfg_highlightWindows: highlightWindows.checked
    property bool cfg_interactiveMute
    property alias cfg_fill: fill.checked
    property int cfg_maxStripes: 1
    property bool cfg_forceStripes: false
    property alias cfg_taskMaxWidth: taskMaxWidth.currentIndex
    property int cfg_iconSpacing: 0

    Kirigami.FormLayout {
        QQC2.CheckBox {
            id: showToolTips
            Kirigami.FormData.label: i18nc("@label for several checkboxes", "General:")
            text: i18nc("@option:check section General", "Show small window previews when hovering over tasks")
        }

        QQC2.CheckBox {
            id: highlightWindows
            text: i18nc("@option:check section General", "Hide other windows when hovering over previews")
        }

        QQC2.CheckBox {
            id: interactiveMute
            text: i18nc("@option:check section General", "Use audio indicators to mute tasks")
            checked: cfg_interactiveMute && plasmaPaAvailable
            onToggled: cfg_interactiveMute = checked
            enabled: plasmaPaAvailable
        }

        QQC2.CheckBox {
            id: fill
            text: i18nc("@option:check section General", "Fill free space on panel")
        }

        Item {
            Kirigami.FormData.isSection: true
            visible: !iconOnly
        }

        QQC2.ComboBox {
            id: taskMaxWidth
            visible: !iconOnly && !plasmoidVertical

            Kirigami.FormData.label: i18nc("@label:listbox", "Maximum task width:")

            model: [
                i18nc("@item:inlistbox how wide a task item should be", "Narrow"),
                i18nc("@item:inlistbox how wide a task item should be", "Medium"),
                i18nc("@item:inlistbox how wide a task item should be", "Wide")
            ]
        }

        Item {
            Kirigami.FormData.isSection: true
        }

        QQC2.Label {
            Kirigami.FormData.label: i18nc("@label for task arrangement", "Arrangement:")
            text: plasmoidVertical
                ? i18nc("@info task arrangement", "One column of icons with captions")
                : i18nc("@info task arrangement", "One row of icons with captions")
        }

        Item {
            Kirigami.FormData.isSection: true
        }

        QQC2.ComboBox {
            visible: iconOnly
            Kirigami.FormData.label: i18nc("@label:listbox", "Spacing between icons:")

            model: [
                {
                    "label": i18nc("@item:inlistbox Icon spacing", "Small"),
                    "spacing": 0
                },
                {
                    "label": i18nc("@item:inlistbox Icon spacing", "Normal"),
                    "spacing": 1
                },
                {
                    "label": i18nc("@item:inlistbox Icon spacing", "Large"),
                    "spacing": 3
                },
            ]

            textRole: "label"
            enabled: !Kirigami.Settings.tabletMode

            currentIndex: {
                if (Kirigami.Settings.tabletMode) {
                    return 2; // Large
                }

                switch (cfg_iconSpacing) {
                    case 0: return 0; // Small
                    case 1: return 1; // Normal
                    case 3: return 2; // Large
                }
            }
            onActivated: index => {
                cfg_iconSpacing = model[currentIndex]["spacing"];
            }
        }

        QQC2.Label {
            visible: Kirigami.Settings.tabletMode
            text: i18nc("@info:usagetip under a set of radio buttons when Touch Mode is on", "Automatically set to Large when in Touch mode")
            font: Kirigami.Theme.smallFont
        }
    }
}
