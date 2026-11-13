// SPDX-FileCopyrightText: 2026 mrmmx31
// SPDX-License-Identifier: GPL-3.0-or-later
import QtQuick
import QtQuick.Controls as QQC
import QtQuick.Layouts
import org.kde.kirigami as Kirigami
import org.kde.kcmutils as KCM
import org.kde.plasma.plasmoid
import org.kde.plasma.private.kicker as Kicker
import org.kde.plasma.plasma5support as P5Support
import "ConfigUtils.js" as ConfigUtils

KCM.SimpleKCM {
    id: page
    property var cfg_pinnedApplications: []
    property string cfg_applicationsMenuStyle: "domainos"
    property var importOrigins: []
    property string importMessage: ""
    property string pendingCommand: ""
    property string pendingToken: ""
    property string pendingAction: ""
    property int requestCount: 0
    property var importSource: executable
    readonly property bool importBusy: pendingCommand.length > 0
    readonly property var pinnedMetadataModel: metadata
    readonly property string instanceNonce: Date.now().toString(36) + "-" + Math.random().toString(36).slice(2)

    // In-memory metadata lookup; not the menu's favorite store.
    Kicker.FavoritesModel { id: metadata; favorites: ConfigUtils.copy(page.cfg_pinnedApplications) }
    Repeater {
        id: metadataRows
        model: metadata
        delegate: Item {
            required property var model
            readonly property string desktop: ConfigUtils.desktopId(model.favoriteId || model.url || "")
            readonly property string title: model.display || ""
            visible: false
        }
    }

    function pinTitle(index) {
        const desktop = cfg_pinnedApplications[index];
        for (let row = 0; row < metadataRows.count; ++row) {
            const item = metadataRows.itemAt(row);
            if (item && item.desktop === desktop && item.title) return item.title;
        }
        return desktop;
    }
    function removePin(index) {
        const pins = ConfigUtils.copy(cfg_pinnedApplications);
        if (index < 0 || index >= pins.length) return false;
        pins.splice(index, 1);
        cfg_pinnedApplications = pins;
        return true;
    }
    function movePin(index, delta) { cfg_pinnedApplications = ConfigUtils.move(cfg_pinnedApplications, index, delta); }
    function addList(text) {
        const parsed = ConfigUtils.desktopList(text);
        if (!parsed.valid) {
            importMessage = qsTr("Desktop IDs inválidos: %1").arg(parsed.rejected.join(", "));
            return false;
        }
        cfg_pinnedApplications = ConfigUtils.unique(ConfigUtils.copy(cfg_pinnedApplications).concat(parsed.values));
        importMessage = qsTr("Lista própria preparada. Aplicar salva; Descartar mantém a gaveta anterior.");
        return true;
    }
    function quote(value) { return "'" + String(value).replace(/'/g, "'\"'\"'") + "'"; }
    function requestImport(action, sourceId) {
        if (importBusy || (action !== "origins" && action !== "source")) return false;
        if (action === "source" && !importOrigins.some(origin => origin.id === sourceId)) return false;
        let command="";
        try {
            const token=instanceNonce + "-" + (++requestCount);
            const path=decodeURIComponent(Qt.resolvedUrl("../code/pin_import.py").toString().replace(/^file:\/\//, ""));
            const request={action:action,sourceId:sourceId || "",token:token};
            command="/usr/bin/python3 -B " + quote(path) + " " + quote(JSON.stringify(request));
            pendingToken=token;pendingAction=action;pendingCommand=command;
            importMessage=action === "origins" ? qsTr("Consultando as origens deste usuário…") : qsTr("Importando somente a fonte escolhida…");
            importSource.connectSource(command);
            return true;
        } catch (error) {
            // A provider can complete inline and then throw. Keep a completed
            // result; otherwise release our state before attempting cleanup.
            if (pendingCommand===command) {
                pendingCommand="";pendingToken="";pendingAction="";
                try { if (command) importSource.disconnectSource(command) }
                catch (cleanupError) { console.warn("DomainOS: import source cleanup failed") }
                importMessage=qsTr("Não foi possível consultar a fonte. Nenhuma importação foi repetida.");
            }
            return false;
        }
    }
    function handleImportResult(source,data) {
        if (!pendingCommand || source!==pendingCommand) return false;
        const token=pendingToken,action=pendingAction;
        pendingCommand="";pendingToken="";pendingAction="";
        try { importSource.disconnectSource(source) }
        catch (error) { console.warn("DomainOS: import source disconnect failed") }
        try {
            const result=JSON.parse(String(data && data.stdout || ""));
            if (!result || result.token!==token || typeof result.ok!=="boolean" || !result.ok)
                throw new Error(result && result.detail || "Importação indisponível");
            if (action === "origins") {
                if (!Array.isArray(result.origins) || !result.origins.every(origin=>origin && typeof origin.id==="string" && typeof origin.label==="string"))
                    throw new Error("Invalid launcher origins");
                importOrigins=result.origins;
                importMessage=importOrigins.length ? qsTr("Escolha uma origem identificada. Ela será lida somente ao pressionar Importar fonte selecionada.") : qsTr("Nenhuma lista compatível encontrada neste perfil.");
            } else {
                if (!Array.isArray(result.desktopIds) || !result.desktopIds.every(id=>typeof id==="string"))
                    throw new Error("Invalid launcher identities");
                if (addList(result.desktopIds.join("\n"))) importMessage=qsTr("Fonte importada para a lista própria. A origem permanece intacta; Aplicar salva esta gaveta.");
            }
        } catch (error) { importMessage=qsTr("Não foi possível importar: %1").arg(String(error)); }
        return true;
    }
    P5Support.DataSource {
        id: executable
        engine: "executable"
        connectedSources: []
        onNewData: (source, data) => page.handleImportResult(source,data)
    }

    footer: DomainOSCategoryDefaults {
        targetPage: page
        configuration: Plasmoid.configuration
        resetAllowed: !page.importBusy
        onResetPrepared: { page.importMessage = ""; supplied.text = "" }
    }

    Kirigami.FormLayout {
        QQC.ComboBox {
            objectName:"domainosApplicationsMenuStyle"
            model:[qsTr("DomainOS"),qsTr("Menu de aplicativos do KDE")]
            currentIndex:page.cfg_applicationsMenuStyle === "kde" ? 1 : 0
            onActivated:index=>page.cfg_applicationsMenuStyle=index === 1 ? "kde" : "domainos"
            Kirigami.FormData.label:qsTr("Interface do menu:")
            Layout.fillWidth:true
        }
        QQC.Label {
            text:qsTr("O menu DomainOS é o padrão. Sua busca procura aplicativos em todas as categorias. A outra opção utiliza a interface do menu de aplicativos do KDE instalada neste computador.")
            wrapMode:Text.Wrap;Layout.fillWidth:true
        }
        QQC.Label {
            text: qsTr("A gaveta mantém os pins desta instância e uma seção de favoritos do KDE. Ao abrir, lê a ordem do menu KDE existente; se ele foi removido, identifica a ordem legada compatível. Não altera os favoritos, os pins de outros painéis nem fecha janelas da Iconbox. Cada pin solicita uma nova janela/instância ao aplicativo.")
            wrapMode: Text.Wrap; Layout.fillWidth: true
        }
        ColumnLayout {
            Kirigami.FormData.label: qsTr("Aplicativos fixados:")
            Layout.fillWidth: true
            QQC.Label {
                text:qsTr("Preferências do painel… — item permanente, sempre disponível na gaveta")
                wrapMode:Text.Wrap;Layout.fillWidth:true
            }
            Repeater {
                model: ConfigUtils.copy(page.cfg_pinnedApplications)
                delegate: RowLayout {
                    required property int index
                    required property var modelData
                    QQC.Label { text: page.pinTitle(index) + "\n" + modelData; Layout.fillWidth: true; wrapMode: Text.Wrap }
                    QQC.Button { text: "↑"; enabled: index > 0; Accessible.name: qsTr("Mover para cima"); onClicked: page.movePin(index, -1) }
                    QQC.Button { text: "↓"; enabled: index + 1 < page.cfg_pinnedApplications.length; Accessible.name: qsTr("Mover para baixo"); onClicked: page.movePin(index, 1) }
                    QQC.Button { text: qsTr("Retirar"); onClicked: page.removePin(index) }
                }
            }
            QQC.Label { visible: page.cfg_pinnedApplications.length === 0; text: qsTr("Nenhum aplicativo fixado.") }
        }
        QQC.TextArea {
            id: supplied
            objectName: "domainosSuppliedPinIds"
            placeholderText: qsTr("Desktop IDs fornecidos por você, um por linha; por exemplo org.kde.kate.desktop")
            Kirigami.FormData.label: qsTr("Adicionar lista:")
            Layout.fillWidth: true; Layout.preferredHeight: 80
        }
        QQC.Button { text: qsTr("Adicionar IDs fornecidos"); onClicked: page.addList(supplied.text) }
        QQC.Button {
            objectName: "domainosChoosePinImportSource"
            text: qsTr("Escolher fonte para importar…")
            enabled: !page.importBusy
            onClicked: page.requestImport("origins", "")
            Kirigami.FormData.label: qsTr("Importação opcional:")
        }
        QQC.ComboBox {
            id: origin
            visible: page.importOrigins.length > 0
            model: page.importOrigins; textRole: "label"; valueRole: "id"
            Layout.fillWidth: true
        }
        QQC.Button {
            objectName: "domainosImportChosenPinSource"
            text: qsTr("Importar fonte selecionada")
            visible: page.importOrigins.length > 0; enabled: !page.importBusy && origin.currentIndex >= 0
            onClicked: page.requestImport("source", origin.currentValue)
        }
        QQC.Label { text: page.importMessage; visible: text.length > 0; wrapMode: Text.Wrap; Layout.fillWidth: true }
        QQC.Label {
            text: qsTr("A consulta usa somente listas compatíveis do seu próprio perfil após sua escolha. A importação acrescenta IDs válidos, remove duplicados e deixa a origem intacta. IDs de aplicativos ausentes podem ser retirados normalmente.")
            wrapMode: Text.Wrap; Layout.fillWidth: true
        }
    }
}
