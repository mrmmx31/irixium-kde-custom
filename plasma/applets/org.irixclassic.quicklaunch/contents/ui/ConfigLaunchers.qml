// SPDX-FileCopyrightText: 2026 mrmmx31
// SPDX-License-Identifier: GPL-2.0-or-later

import QtQuick
import QtQuick.Layouts
import QtQuick.Controls as QQC2
import QtCore
import org.kde.kirigami as Kirigami
import org.kde.kcmutils as KCM
import org.kde.plasma.private.quicklaunch

import "launcherurls.js" as LauncherUrls

KCM.SimpleKCM {
    id: editor
    objectName: "classicLauncherConfiguration"

    // Plasma owns loading and saving cfg_* properties. Replace this array on
    // every edit, so Apply detects changes and Cancel leaves the applet intact.
    property var cfg_launcherUrls: []
    property alias selectedIndex: launcherList.currentIndex
    property int revision: 0
    property string selectionMessage: ""

    onCfg_launcherUrlsChanged: revision += 1

    function copiedUrls() {
        const result = [];
        for (let i = 0; i < cfg_launcherUrls.length; ++i) {
            result.push(String(cfg_launcherUrls[i]));
        }
        return result;
    }

    function moveSelected(offset) {
        const urls = copiedUrls();
        const index = selectedIndex;
        const destination = index + offset;
        if ((offset !== -1 && offset !== 1) || index < 0 || index >= urls.length
                || destination < 0 || destination >= urls.length) {
            return false;
        }
        const entry = urls.splice(index, 1)[0];
        urls.splice(destination, 0, entry);
        cfg_launcherUrls = urls;
        selectedIndex = destination;
        selectionMessage = "";
        return true;
    }

    function removeSelected() {
        const urls = copiedUrls();
        const index = selectedIndex;
        if (index < 0 || index >= urls.length) {
            return false;
        }
        urls.splice(index, 1);
        cfg_launcherUrls = urls;
        selectedIndex = Math.min(index, urls.length - 1);
        selectionMessage = "";
        return true;
    }

    function acceptSelection(url, replacementIndex, selectionRevision) {
        const entry = String(url);
        if (!entry.length) {
            return false;
        }
        const urls = copiedUrls();
        if (replacementIndex >= 0) {
            // The native selector is nonmodal. Never replace a different row
            // if the user changed the list while that selector was open.
            if (selectionRevision !== revision || replacementIndex >= urls.length) {
                selectionMessage = i18n("The launcher list changed while choosing an application. Select it again.");
                return false;
            }
            urls[replacementIndex] = entry;
        } else {
            urls.push(entry);
        }
        cfg_launcherUrls = urls;
        selectedIndex = replacementIndex >= 0 ? replacementIndex : urls.length - 1;
        selectionMessage = "";
        return true;
    }

    function requestLauncher(replaceSelected) {
        if (replaceSelected && (selectedIndex < 0 || selectedIndex >= cfg_launcherUrls.length)) {
            return null;
        }
        // Give each native dialog its own callback context; canceling the
        // selector changes no row, and several open selectors cannot share
        // a stale replacement index. QObject callbacks die with this page.
        const selector = selectorComponent.createObject(editor, {
            "replacementIndex": replaceSelected ? selectedIndex : -1,
            "selectionRevision": revision
        });
        selector.addLauncher(false);
        return selector;
    }

    Logic {
        id: metadataLogic
    }

    Component {
        id: selectorComponent
        Logic {
            property int replacementIndex: -1
            property int selectionRevision: 0
            onLauncherAdded: function(url, isPopup) {
                editor.acceptSelection(url, replacementIndex, selectionRevision);
                destroy();
            }
        }
    }

    ColumnLayout {
        spacing: Kirigami.Units.smallSpacing

        QQC2.Label {
            Layout.fillWidth: true
            text: i18n("The launchers appear in this order. Select a row to replace, remove or move it.")
            wrapMode: Text.WordWrap
        }

        QQC2.ScrollView {
            Layout.fillWidth: true
            Layout.minimumWidth: Kirigami.Units.gridUnit * 22
            Layout.preferredHeight: Kirigami.Units.gridUnit * 10

            ListView {
                id: launcherList
                objectName: "classicLauncherConfigurationList"
                clip: true
                model: editor.cfg_launcherUrls
                currentIndex: -1

                delegate: QQC2.ItemDelegate {
                    required property int index
                    required property string modelData
                    readonly property var launcher: metadataLogic.launcherData(
                        LauncherUrls.resolve(modelData, StandardPaths))

                    width: launcherList.width
                    text: launcher.applicationName || modelData
                    icon.name: launcher.iconName || "fork"
                    highlighted: ListView.isCurrentItem
                    onClicked: launcherList.currentIndex = index
                }
            }
        }

        RowLayout {
            QQC2.Button {
                objectName: "classicLauncherAdd"
                text: i18nc("@action:button", "Add…")
                icon.name: "list-add"
                onClicked: editor.requestLauncher(false)
            }
            QQC2.Button {
                objectName: "classicLauncherReplace"
                text: i18nc("@action:button", "Replace…")
                icon.name: "document-edit"
                enabled: editor.selectedIndex >= 0 && editor.selectedIndex < editor.cfg_launcherUrls.length
                onClicked: editor.requestLauncher(true)
            }
            QQC2.Button {
                objectName: "classicLauncherRemove"
                text: i18nc("@action:button", "Remove")
                icon.name: "list-remove"
                enabled: editor.selectedIndex >= 0 && editor.selectedIndex < editor.cfg_launcherUrls.length
                onClicked: editor.removeSelected()
            }
            Item {
                Layout.fillWidth: true
            }
        }
        RowLayout {
            QQC2.Button {
                objectName: "classicLauncherUp"
                text: i18nc("@action:button", "Up")
                icon.name: "go-up"
                enabled: editor.selectedIndex > 0 && editor.selectedIndex < editor.cfg_launcherUrls.length
                onClicked: editor.moveSelected(-1)
            }
            QQC2.Button {
                objectName: "classicLauncherDown"
                text: i18nc("@action:button", "Down")
                icon.name: "go-down"
                enabled: editor.selectedIndex >= 0 && editor.selectedIndex < editor.cfg_launcherUrls.length - 1
                onClicked: editor.moveSelected(1)
            }
            Item {
                Layout.fillWidth: true
            }
        }

        QQC2.Label {
            Layout.fillWidth: true
            visible: editor.cfg_launcherUrls.length === 0
            text: i18n("No launchers. Use Add to choose an installed application.")
            wrapMode: Text.WordWrap
        }

        QQC2.Label {
            Layout.fillWidth: true
            visible: editor.selectionMessage.length > 0
            text: editor.selectionMessage
            wrapMode: Text.WordWrap
        }
    }
}
