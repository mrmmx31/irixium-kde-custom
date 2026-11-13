// SPDX-FileCopyrightText: 2026 mrmmx31
// SPDX-License-Identifier: GPL-3.0-or-later
import QtQuick
import QtQuick.Controls as QQC
import QtQuick.Layouts
import org.kde.kirigami as Kirigami
import org.kde.kcmutils as KCM
import org.kde.plasma.plasmoid
import org.kde.plasma.plasma5support as P5Support
import "ConfigUtils.js" as ConfigUtils

KCM.SimpleKCM {
    id: page
    property string cfg_mailClient: ""
    property bool cfg_mailCountsEnabled: false
    property alias cfg_terminalCommand: terminal.text
    property string mailError: ""
    property var installedMailClients: []
    property string preferredMailClient: ""
    property string clientCatalogError: ""
    property string catalogSource: ""
    readonly property string catalogNonce: Date.now().toString(36)+"-"+Math.random().toString(36).slice(2)
    readonly property var mailClientChoices: {
        const choices = [{id:"",name:qsTr("Seguir o cliente preferido do KDE")}].concat(installedMailClients)
        if (cfg_mailClient.length && !choices.some(client => client.id === cfg_mailClient))
            choices.push({id:cfg_mailClient,name:qsTr("%1 — escolha salva").arg(cfg_mailClient)})
        return choices
    }
    function quote(value) { return "'"+String(value).replace(/'/g,"'\"'\"'")+"'" }
    function releaseCatalog() {
        const source = catalogSource
        catalogSource = ""
        if (!source.length) return
        try { catalog.disconnectSource(source) }
        catch (error) { console.warn("DomainOS mail client catalogue cleanup failed") }
    }
    function refreshMailClients() {
        releaseCatalog()
        clientCatalogError = ""
        const path = decodeURIComponent(Qt.resolvedUrl("../code/commands.py").toString().replace(/^file:\/\//,""))
        catalogSource = "python3 "+quote(path)+" "+quote(JSON.stringify({action:"mail-clients",requestNonce:catalogNonce}))
        try { catalog.connectSource(catalogSource) }
        catch (error) { releaseCatalog(); clientCatalogError = qsTr("Não foi possível listar os clientes instalados.") }
    }
    function readMailClients(source, data) {
        if (source !== catalogSource) return
        releaseCatalog()
        try {
            const result = JSON.parse(data.stdout)
            if (!result.ok || !Array.isArray(result.clients)) throw new Error("Invalid catalogue result")
            installedMailClients = result.clients.filter(client => ConfigUtils.desktopId(client.id) === client.id
                && typeof client.name === "string")
            preferredMailClient = result.defaultClient || ""
        } catch (error) { clientCatalogError = qsTr("Não foi possível ler a lista de clientes instalados.") }
    }
    Component.onCompleted: refreshMailClients()
    Component.onDestruction: releaseCatalog()
    P5Support.DataSource {
        id: catalog
        engine: "executable"
        connectedSources: []
        onNewData: (source, data) => page.readMailClients(source, data)
    }

    footer: DomainOSCategoryDefaults {
        targetPage: page
        configuration: Plasmoid.configuration
        onResetPrepared: page.mailError = ""
    }

    Kirigami.FormLayout {
        QQC.ComboBox {
            id: mailClients
            objectName: "domainosMailClientChoice"
            Kirigami.FormData.label: qsTr("Cliente de correio:")
            Layout.fillWidth: true
            model: page.mailClientChoices
            textRole: "name"
            currentIndex: page.mailClientChoices.findIndex(client => client.id === page.cfg_mailClient)
            onActivated: index => { page.cfg_mailClient = page.mailClientChoices[index].id; page.mailError = "" }
        }
        QQC.Label {
            visible: page.clientCatalogError.length > 0
            text: page.clientCatalogError
            wrapMode: Text.Wrap; Layout.fillWidth: true
        }
        QQC.Label {
            visible: page.cfg_mailClient.length === 0 && page.preferredMailClient.length > 0
            text: qsTr("Preferido atual: %1").arg(page.preferredMailClient)
            wrapMode: Text.Wrap; Layout.fillWidth: true
        }
        QQC.TextField {
            id: mail
            objectName: "domainosMailDesktopId"
            text: page.cfg_mailClient
            placeholderText: qsTr("Opcional: outro aplicativo instalado (*.desktop)")
            Kirigami.FormData.label: qsTr("Outro Desktop ID:")
            Layout.fillWidth: true
            onTextEdited: {
                const candidate = text.trim();
                const id = ConfigUtils.desktopId(candidate);
                page.mailError = candidate.length > 0 && !id ? qsTr("Use um Desktop ID como org.mozilla.thunderbird.desktop, não um comando.") : "";
                if (page.mailError.length === 0) page.cfg_mailClient = id;
            }
        }
        QQC.Label { visible: page.mailError.length > 0; text: page.mailError; wrapMode: Text.Wrap; Layout.fillWidth: true }
        QQC.Label {
            text: qsTr("A escolha vale para este botão do painel. Não altera o cliente padrão do KDE e abre o cliente sem iniciar uma mensagem. A lista usa somente metadados dos aplicativos instalados; a contagem depende da integração escolhida e habilitada no cliente.")
            wrapMode: Text.Wrap; Layout.fillWidth: true
        }
        QQC.CheckBox {
            objectName: "domainosMailCountsEnabled"
            Kirigami.FormData.label: qsTr("Estado das mensagens:")
            text: qsTr("Mostrar a contagem real pela integração do Thunderbird")
            checked: page.cfg_mailCountsEnabled
            onToggled: page.cfg_mailCountsEnabled = checked
        }
        QQC.Label {
            text: qsTr("A contagem exige a extensão e o integrador locais habilitados no Thunderbird. Até a conexão existir, o painel informa que a contagem está indisponível. A integração compartilha apenas estado e total de mensagens não lidas, sem conteúdo das mensagens.")
            wrapMode: Text.Wrap; Layout.fillWidth: true
        }
        QQC.TextField {
            id: terminal
            placeholderText: qsTr("Vazio: terminal preferido do KDE, ou Konsole")
            Kirigami.FormData.label: qsTr("Terminal (executável e argumentos):")
            Layout.fillWidth: true
        }
        QQC.Label {
            text: qsTr("Abre uma nova sessão normal, sem elevar privilégios. Os argumentos são passados ao executável sem shell; operadores como |, > e && não são interpretados.")
            wrapMode: Text.Wrap; Layout.fillWidth: true
        }
        QQC.Label {
            Kirigami.FormData.label: qsTr("Sessão e bloqueio:")
            text: qsTr("O menu de sessão oferece sair, suspender e hibernar conforme o suporte real. Abrir o menu não executa uma ação. O bloqueio solicita o bloqueio real da sessão e informa falhas.")
            wrapMode: Text.Wrap; Layout.fillWidth: true
        }
        QQC.Label {
            Kirigami.FormData.label: qsTr("Aparência e ajuda:")
            text: qsTr("A paleta do rodapé abre Appearance & Style no System Settings. A ajuda mantém a ordem Painel → xman → KDE; o xman acompanha as cores da sessão. Estes acessos não redefinem suas preferências globais ao aplicar esta página.")
            wrapMode: Text.Wrap; Layout.fillWidth: true
        }
    }
}
