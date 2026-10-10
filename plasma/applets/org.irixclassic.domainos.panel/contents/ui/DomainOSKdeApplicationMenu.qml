// SPDX-FileCopyrightText: 2026 IRIX Classic contributors
// SPDX-License-Identifier: GPL-3.0-or-later
import QtQuick
import QtQuick.Controls as Controls
import QtQuick.Layouts
import QtCore as QtCore
import org.kde.kirigami as Kirigami
import org.kde.ksvg as KSvg
import org.kde.plasma.components as PlasmaComponents3
import org.kde.plasma.private.kicker as Kicker

// Keep KDE's installed menu representation and its delegates intact. This
// context supplies the backend and companion objects expected by that view;
// the enclosing DomainOS applet keeps its own expanded state and preferences.
Item {
    id: kicker
    objectName:"domainosKdeApplicationMenu"
    property Item hostItem: null
    property var catalogModel: null
    property string favoritesClient: "org.irixclassic.domainos.kde-applications"
    property url menuRepresentationSource: QtCore.StandardPaths.locate(QtCore.StandardPaths.GenericDataLocation,
        "plasma/plasmoids/org.kde.plasma.kicker/contents/ui/MenuRepresentation.qml",QtCore.StandardPaths.LocateFile)
    property url subMenuSource: QtCore.StandardPaths.locate(QtCore.StandardPaths.GenericDataLocation,
        "plasma/plasmoids/org.kde.plasma.kicker/contents/ui/ItemListDialog.qml",QtCore.StandardPaths.LocateFile)
    property bool expanded: false
    property bool hideOnWindowDeactivate: true
    property Item dragSource: null
    property Item menuAnchor: null
    property var representationComponent: null
    property Component itemListDialogComponent: null
    readonly property var rootModel: nativeCatalog
    readonly property var globalFavorites: catalogModel ? catalogModel.favoritesModel : rootModel.favoritesModel
    readonly property var systemFavorites: catalogModel ? catalogModel.systemFavoritesModel : rootModel.systemFavoritesModel
    readonly property bool menuVisible: nativePopup.visible
    readonly property Item nativeRepresentation: representation.item
    signal reset()
    signal failure(string reason)

    function closeMenu() { expanded=false;nativePopup.close();reset() }
    function resetDragSource() { dragSource=null }
    function openMenu(anchor) {
        if (!anchor || !anchor.Window.window) { failure(qsTr("O menu de aplicativos do KDE precisa de uma janela visível."));return false }
        menuAnchor=anchor
        if (!representationComponent) {
            if (!menuRepresentationSource || !subMenuSource) {
                failure(qsTr("O menu de aplicativos do KDE não está instalado."));return false
            }
            const submenu=Qt.createComponent(subMenuSource,Component.PreferSynchronous)
            const menu=Qt.createComponent(menuRepresentationSource,Component.PreferSynchronous)
            if (submenu.status!==Component.Ready || menu.status!==Component.Ready) {
                failure(qsTr("O menu de aplicativos do KDE não está disponível nesta instalação.")+"\n"+submenu.errorString()+menu.errorString())
                return false
            }
            itemListDialogComponent=submenu
            representationComponent=menu
        }
        expanded=true
        nativePopup.open()
        if (representation.item) {
            representation.item.reset()
            windowSystem.monitorWindowVisibility(representation.item)
        }
        justOpenedTimer.restart()
        return true
    }
    onExpandedChanged:if (!expanded && nativePopup.visible) nativePopup.close()
    DomainOSPopupPlacement { popup:nativePopup;popupAnchor:kicker.menuAnchor }
    Controls.Popup {
        id:nativePopup
        objectName:"domainosKdeApplicationsMenu"
        popupType:Controls.Popup.Window
        enter:null;exit:null
        closePolicy:Controls.Popup.CloseOnEscape|Controls.Popup.CloseOnPressOutsideParent
        padding:Kirigami.Units.smallSpacing
        width:Math.max(260,representation.item ? representation.item.Layout.minimumWidth+2*padding : 260)
        height:Math.max(100,representation.item ? representation.item.Layout.minimumHeight+2*padding : 100)
        onClosed:{ kicker.expanded=false;kicker.reset() }
        contentItem:Loader {
            id:representation
            objectName:"domainosKdeApplicationsRepresentation"
            sourceComponent:kicker.representationComponent
            onStatusChanged:if(status===Loader.Error) { kicker.failure(qsTr("Não foi possível abrir a interface de aplicativos do KDE."));kicker.closeMenu() }
        }
    }
    Kicker.RootModel {
        id:nativeCatalog
        autoPopulate:kicker.expanded;appNameFormat:0;flat:false;sorted:true;showSeparators:true
        showAllApps:false;showAllAppsCategorized:true;showTopLevelItems:true
        showRecentApps:false;showRecentDocs:false
        appletInterface:kicker.hostItem || kicker
        Component.onCompleted:favoritesModel.initForClient(kicker.favoritesClient)
    }
    Kicker.RunnerModel {
        id:runnerModel
        appletInterface:kicker.hostItem || kicker
        favoritesModel:kicker.globalFavorites
        runners:["krunner_services","krunner_systemsettings","krunner_sessions","krunner_powerdevil","calculator","unitconverter"]
    }
    Kicker.DragHelper { id:dragHelper;dragIconSize:Kirigami.Units.iconSizes.medium }
    Kicker.WindowSystem { id:windowSystem }
    Kicker.ProcessRunner { id:processRunner }
    KSvg.FrameSvgItem { id:highlightItemSvg;visible:false;imagePath:"widgets/viewitem";prefix:"hover" }
    KSvg.FrameSvgItem { id:listItemSvg;visible:false;imagePath:"widgets/listitem";prefix:"normal" }
    KSvg.Svg {
        id:lineSvg
        imagePath:"widgets/line"
        property int horLineHeight:elementSize("horizontal-line").height
        property int vertLineWidth:elementSize("vertical-line").width
    }
    PlasmaComponents3.Label {
        id:toolTipDelegate
        width:contentWidth;height:undefined
        property Item toolTip
        text:toolTip ? toolTip.mainText : ""
        textFormat:Text.PlainText
    }
    // KDE's standard menu uses this grace period only for submenu hover.
    // It is local to this optional menu and never drives window decoration.
    Timer { id:justOpenedTimer;interval:600;repeat:false }
    Connections { target:windowSystem;function onFocusIn(){ kicker.hideOnWindowDeactivate=true } }
    Connections { target:rootModel;function onRefreshed(){ kicker.reset() } }
    Connections { target:dragHelper;function onDropped(){ kicker.resetDragSource() } }
}
