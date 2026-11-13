// SPDX-FileCopyrightText: 2013 Aurélien Gâteau <agateau@kde.org>
// SPDX-FileCopyrightText: 2013-2015 Eike Hein <hein@kde.org>
// SPDX-FileCopyrightText: 2017 Ivan Cukic <ivan.cukic@kde.org>
// SPDX-FileCopyrightText: 2021 Mikel Johnson <mikel5764@gmail.com>
// SPDX-FileCopyrightText: 2021 Noah Davis <noahadvs@gmail.com>
// SPDX-FileCopyrightText: 2024 ivan tkachenko <me@ratijas.tk>
// SPDX-FileCopyrightText: 2026 IRIX Classic contributors
// SPDX-License-Identifier: GPL-2.0-or-later
// Instance-owned adaptation of the existing Kickoff ActionMenu.
import QtQuick
import org.kde.plasma.extras as PlasmaExtras

Item {
    id: root
    property var actionList: []
    property var sourceModel
    property int sourceRow: -1
    required property var dispatchHandler
    signal launchRequested()
    readonly property alias menu: contextMenu
    visible: false

    PlasmaExtras.Menu {
        id: contextMenu
        visualParent: null
        placement: PlasmaExtras.Menu.BottomPosedLeftAlignedPopup
    }
    Instantiator {
        model: root.actionList
        delegate: menuItemComponent
        onObjectAdded: (index, object) => contextMenu.addMenuItem(object)
        onObjectRemoved: (index, object) => contextMenu.removeMenuItem(object)
    }
    Component { id: menuComponent; PlasmaExtras.Menu {} }
    Component {
        id: menuItemComponent
        PlasmaExtras.MenuItem {
            id: menuItem
            required property var modelData
            readonly property PlasmaExtras.Menu subMenu: modelData.subActions
                ? menuComponent.createObject(this, {visualParent: action}) : null
            text: modelData.text ?? ""
            enabled: modelData.type !== "title" && (modelData.enabled ?? true)
            separator: modelData.type === "separator"
            section: modelData.type === "title"
            icon: modelData.icon ?? null
            checkable: modelData.checkable ?? false
            checked: modelData.checked ?? false
            readonly property Instantiator subItems: Instantiator {
                active: menuItem.subMenu !== null
                model: menuItem.modelData.subActions ?? []
                delegate: menuItemComponent
                onObjectAdded: (index, object) => menuItem.subMenu.addMenuItem(object)
                onObjectRemoved: (index, object) => menuItem.subMenu.removeMenuItem(object)
            }
            onClicked: {
                if (!enabled || separator || section || modelData.subActions) return
                if (root.dispatchHandler(root.sourceModel, root.sourceRow,
                        modelData.actionId, modelData.actionArgument)) root.launchRequested()
            }
        }
    }
}
