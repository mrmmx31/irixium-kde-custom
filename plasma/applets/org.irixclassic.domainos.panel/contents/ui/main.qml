// SPDX-FileCopyrightText: 2026 mrmmx31
// SPDX-License-Identifier: GPL-3.0-or-later
import QtQuick
import QtQuick.Window
import QtQuick.Layouts
import org.kde.plasma.core as PlasmaCore
import org.kde.plasma.plasmoid

PlasmoidItem {
    id: host
    objectName: "domainosPanelApplet"
    Plasmoid.backgroundHints: PlasmaCore.Types.NoBackground
    // The applet already draws the complete panel chassis. Hide the native
    // containment's second plate only while this is its sole applet; the
    // previous hint returns if another widget is added or DomainOS is removed.
    readonly property bool soleDomainosPanel: Plasmoid.containment
        && Plasmoid.containment.pluginName === "org.kde.panel"
        && Plasmoid.containment.applets.length === 1
        && Plasmoid.containment.applets[0] === Plasmoid
    Binding {
        target: Plasmoid.containment
        property: "backgroundHints"
        value: PlasmaCore.Types.NoBackground
        when: host.soleDomainosPanel
        restoreMode: Binding.RestoreBindingOrValue
    }
    Plasmoid.constraintHints: Plasmoid.CanFillArea
    Plasmoid.status: Plasmoid.configuration.unhideOnAttention && fullRepresentationItem
        && fullRepresentationItem.integration && fullRepresentationItem.integration.tasks.demandsAttention
        ? PlasmaCore.Types.NeedsAttentionStatus : PlasmaCore.Types.PassiveStatus
    preferredRepresentation: fullRepresentation
    switchWidth: -1
    switchHeight: -1
    Layout.minimumWidth: 971
    Layout.minimumHeight: 109
    Layout.preferredWidth: 1942
    Layout.preferredHeight: 218
    toolTipMainText: "Irix Classic DomainOS"
    toolTipSubText: qsTr("Applications, instruments, windows, desktops and native status")
    readonly property var domainosTrayItems: fullRepresentationItem && fullRepresentationItem.nativeTrayView
        ? fullRepresentationItem.nativeTrayView.availableItems : []
    // ConfigView uses another QML engine. A read-only string on an internal
    // QAction exposes this instance's provider titles without shared files or
    // passing JavaScript objects between engines. It has no user action.
    PlasmaCore.Action {
        id: trayItemsBridge
        property string itemsJson: JSON.stringify(host.domainosTrayItems)
        visible: false
        enabled: false
    }
    // SystemTray owns the generic "configure" action and may redirect it to
    // its internal containment after this component is ready. Keep a separate
    // action for DomainOS; the pinned entry must configure this applet even
    // when the wrapper updates its own action later.
    PlasmaCore.Action {
        id: ownConfiguration
        objectName: "domainosConfigurePanelAction"
        text: qsTr("Configurar DomainOS")
        icon.name: "configure"
        onTriggered: Plasmoid.containment.configureRequested(Plasmoid)
    }
    Component.onCompleted: {
        Plasmoid.setInternalAction("domainos-tray-items", trayItemsBridge)
        Plasmoid.setInternalAction("domainos-configure-panel", ownConfiguration)
    }
    fullRepresentation: DomainOSFunctionalPanel {
        id: panel
        Layout.fillWidth: true
        Layout.fillHeight: true
        Layout.minimumWidth: 971
        Layout.minimumHeight: 109
        Layout.preferredWidth: 1942
        Layout.preferredHeight: 218
        hostItem: host
        settings: Plasmoid.configuration
        instanceId: String(Plasmoid.id)
        nativeTray: Plasmoid.internalSystray
        screenGeometry: Plasmoid.containment ? Plasmoid.containment.screenGeometry
            : Qt.rect(Screen.virtualX, Screen.virtualY, Screen.width, Screen.height)
        screenName: Screen.name
        onConfigureRequested: {
            ownConfiguration.trigger()
        }
        onPinListRequested: pins => {
            Plasmoid.configuration.pinnedApplications = pins
            Plasmoid.configuration.writeConfig()
        }
    }
}
