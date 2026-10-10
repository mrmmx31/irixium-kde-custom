// SPDX-FileCopyrightText: 2026 mrmmx31
// SPDX-License-Identifier: GPL-3.0-or-later
import QtQuick
import QtQuick.Controls as QQC
import QtQuick.Layouts
import org.kde.kirigami as Kirigami
import org.kde.kcmutils as KCM
import org.kde.plasma.plasmoid
import "ConfigUtils.js" as ConfigUtils

KCM.SimpleKCM {
    id: page
    objectName: "domainosTrayConfigPage"
    property var cfg_trayVisibleItems: []
    property var cfg_trayHiddenItems: []
    property var cfg_trayOrder: []
    property alias cfg_trayIncludeHiddenInOverflow: hiddenOverflow.checked
    property string cfg_trayOverflowMode: "continuation"
    // The host may provide native IDs/titles from its own tray. No provider is
    // instantiated, reparented or configured merely by opening this page.
    // ConfigView has its own QQmlEngine. The owning applet publishes JSON through
    // an internal QAction, whose declared string property is safe across engines.
    // No QML object from the native tray is moved into this window.
    readonly property var actionOwner: typeof plasmoid !== "undefined" ? plasmoid : Plasmoid
    property var nativeSnapshotAction: actionOwner.internalAction("domainos-tray-items")
    readonly property bool nativeSnapshotAvailable: !!nativeSnapshotAction
    readonly property string availableItemsJson: JSON.stringify(availableItems)
    property var availableItems: {
        if (!nativeSnapshotAction || !nativeSnapshotAction.itemsJson) return [];
        try {
            const items = JSON.parse(nativeSnapshotAction.itemsJson);
            return Array.isArray(items) ? items.filter(item => item && typeof item.id === "string" && typeof item.title === "string") : [];
        } catch (error) { return []; }
    }
    readonly property var orderedItems: {
        const result = [];
        const requested = ConfigUtils.unique(ConfigUtils.copy(cfg_trayOrder));
        for (const id of requested) {
            const item = availableItems.find(item => item.id === id);
            result.push(item ? Object.assign({available: true}, item)
                : {id: id, title: id, available: false, hidden: false});
        }
        for (const item of availableItems) {
            if (!result.some(row => row.id === item.id)) result.push(Object.assign({available: true}, item));
        }
        return result;
    }
    readonly property string orderedItemsJson: JSON.stringify(orderedItems)
    property string visibilityError: ""
    Connections {
        target: page.actionOwner
        function onInternalActionsChanged() { page.nativeSnapshotAction = page.actionOwner.internalAction("domainos-tray-items"); }
    }
    readonly property string nativeContextJson: JSON.stringify({attachedId: Plasmoid.id,
        actionOwnerId: actionOwner.id, bridgePresent: nativeSnapshotAvailable})

    function setItemPolicy(itemId, policy) {
        let shown = ConfigUtils.copy(cfg_trayVisibleItems).filter(id => id !== itemId);
        let hidden = ConfigUtils.copy(cfg_trayHiddenItems).filter(id => id !== itemId);
        if (policy === "visible") shown.push(itemId);
        else if (policy === "hidden") hidden.push(itemId);
        cfg_trayVisibleItems = shown;
        cfg_trayHiddenItems = hidden;
    }
    function setIds(kind, text) {
        const parsed = ConfigUtils.itemIds(text);
        const opposite = ConfigUtils.copy(kind === "visible" ? cfg_trayHiddenItems : cfg_trayVisibleItems);
        if (!parsed.valid || (kind !== "order" && parsed.values.some(id => opposite.indexOf(id) >= 0))) {
            visibilityError = qsTr("Use IDs nativos sem espaços; um item não pode estar nas listas visível e oculta ao mesmo tempo.");
            return false;
        }
        visibilityError = "";
        if (kind === "visible") { if (!ConfigUtils.same(cfg_trayVisibleItems, parsed.values)) cfg_trayVisibleItems = parsed.values; }
        else if (kind === "hidden") { if (!ConfigUtils.same(cfg_trayHiddenItems, parsed.values)) cfg_trayHiddenItems = parsed.values; }
        else if (kind === "order") { if (!ConfigUtils.same(cfg_trayOrder, parsed.values)) cfg_trayOrder = parsed.values; }
        else return false;
        return true;
    }
    function moveItem(itemId, delta) {
        const order = orderedItems.map(item => item.id);
        const index = order.indexOf(itemId);
        if (index < 0 || index + delta < 0 || index + delta >= order.length) return false;
        cfg_trayOrder = ConfigUtils.move(order, index, delta);
        return true;
    }

    footer: DomainOSCategoryDefaults {
        targetPage: page
        configuration: Plasmoid.configuration
        onResetPrepared: page.visibilityError = ""
    }

    Kirigami.FormLayout {
        QQC.Label {
            text: qsTr("Seis posições, em duas linhas de três, mostram os provedores reais. Listas vazias preservam a política nativa da bandeja desta instância. Aplicar não muda bandejas de outros painéis ou usuários.")
            wrapMode: Text.Wrap; Layout.fillWidth: true
        }
        ColumnLayout {
            visible: page.orderedItems.length > 0
            Layout.fillWidth: true
            Kirigami.FormData.label: qsTr("Ordem dos ícones:")
            QQC.Label {
                text: qsTr("Use as setas para mover os itens. Os seis primeiros visíveis ficam na bandeja; os demais seguem a mesma ordem na ▶. Aplicar confirma a nova ordem.")
                wrapMode: Text.Wrap; Layout.fillWidth: true
            }
            Repeater {
                model: page.orderedItems
                delegate: RowLayout {
                    required property int index
                    required property var modelData
                    QQC.Label {
                        text: modelData.available ? modelData.title : modelData.title + "\n" + qsTr("Indisponível; posição preservada")
                        textFormat: Text.PlainText; Layout.fillWidth: true; wrapMode: Text.Wrap
                    }
                    QQC.ToolButton {
                        objectName: "domainosTrayMoveUp_" + modelData.id
                        text: "↑"; enabled: index > 0
                        Accessible.name: qsTr("Mover %1 para cima").arg(modelData.title)
                        onClicked: page.moveItem(modelData.id, -1)
                    }
                    QQC.ToolButton {
                        objectName: "domainosTrayMoveDown_" + modelData.id
                        text: "↓"; enabled: index + 1 < page.orderedItems.length
                        Accessible.name: qsTr("Mover %1 para baixo").arg(modelData.title)
                        onClicked: page.moveItem(modelData.id, 1)
                    }
                    QQC.ComboBox {
                        objectName: "domainosTrayPolicy_" + modelData.id
                        visible: modelData.available
                        model: [qsTr("Política nativa"), qsTr("Visível"), qsTr("Oculto")]
                        currentIndex: page.cfg_trayVisibleItems.indexOf(modelData.id) >= 0 ? 1 : page.cfg_trayHiddenItems.indexOf(modelData.id) >= 0 ? 2 : 0
                        onActivated: index => page.setItemPolicy(modelData.id, index === 1 ? "visible" : index === 2 ? "hidden" : "native")
                    }
                }
            }
        }
        QQC.Button {
            id: advanced
            objectName: "domainosTrayAdvancedToggle"
            text: checked ? qsTr("Ocultar configuração avançada") : qsTr("Configuração avançada")
            checkable: true; checked: false
            Layout.fillWidth: true
        }
        Kirigami.FormLayout {
            objectName: "domainosTrayAdvancedFields"
            visible: advanced.checked; Layout.fillWidth: true
            QQC.TextArea {
                text: ConfigUtils.copy(page.cfg_trayVisibleItems).join("\n")
                placeholderText: qsTr("IDs de plasmoids ou StatusNotifierItems, um por linha")
                onTextChanged: page.setIds("visible", text)
                Kirigami.FormData.label: qsTr("Forçar visíveis:")
                Layout.fillWidth: true; Layout.preferredHeight: 70
            }
            QQC.TextArea {
                text: ConfigUtils.copy(page.cfg_trayHiddenItems).join("\n")
                onTextChanged: page.setIds("hidden", text)
                Kirigami.FormData.label: qsTr("Forçar ocultos:")
                Layout.fillWidth: true; Layout.preferredHeight: 70
            }
            QQC.TextArea {
                text: ConfigUtils.copy(page.cfg_trayOrder).join("\n")
                onTextChanged: page.setIds("order", text)
                Kirigami.FormData.label: qsTr("Ordem preferida dos IDs:")
                Layout.fillWidth: true; Layout.preferredHeight: 70
            }
        }
        QQC.Label { visible: page.visibilityError.length > 0; text: page.visibilityError; wrapMode: Text.Wrap; Layout.fillWidth: true }
        QQC.ComboBox {
            Layout.fillWidth: true
            model: [qsTr("Continuação; paginar se não couber"), qsTr("Paginação")]
            currentIndex: page.cfg_trayOverflowMode === "pagination" ? 1 : 0
            onActivated: index => page.cfg_trayOverflowMode = index === 1 ? "pagination" : "continuation"
            Kirigami.FormData.label: qsTr("Excedentes na ▶:")
        }
        QQC.CheckBox { id: hiddenOverflow; text: qsTr("Incluir também os itens ocultos na ▶") }
        QQC.Label {
            text: qsTr("A ▲ abre status, notificações e acesso aos ocultos. Os gestos e menus pertencem a cada provedor. Abrir o quadro não limpa notificações e não altera Não perturbe. Os IDs são identidades nativas, não os títulos traduzidos dos ícones.")
            wrapMode: Text.Wrap; Layout.fillWidth: true
        }
    }
}
