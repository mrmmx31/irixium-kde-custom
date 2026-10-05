import QtQuick
import org.kde.kwin.decoration
Item {
    id: root
    width: 800; height: 600
    property alias config: auroraeTheme
    property alias client: decoration.client
    property alias leftGroup: leftButtonGroup
    property alias rightGroup: rightButtonGroup
    property QtObject borders: QtObject { property int left: 6; property int right: 6; property int top: 34; property int bottom: 6 }
    property QtObject maximizedBorders: QtObject { property int left: 0; property int right: 0; property int top: 34; property int bottom: 0 }
    property QtObject padding: QtObject { property int left: 0; property int right: 0; property int top: 0; property int bottom: 0 }
    QtObject {
        id: decoration
        property QtObject client: QtObject { property bool maximized: false; property bool active: true }
    }
    QtObject {
        id: auroraeTheme
        property string decorationPath: "/fixture/Irixium/decoration.svg"
        property int buttonWidth: 22
        property int buttonHeight: 22
        property int buttonWidthMenu: 22
        property int buttonWidthAppMenu: 22
        property int explicitButtonSpacer: 22
        property int buttonSpacing: 6
        property real buttonSizeFactor: 1
        property int buttonMarginTop: 2
        property int buttonMarginTopMaximized: 2
        property int titleHeight: 26
        property int titleEdgeTop: 7
        property int titleEdgeLeft: 9
        property int titleEdgeRight: 9
        property int titleEdgeTopMaximized: 4
        property int titleEdgeLeftMaximized: 6
        property int titleEdgeRightMaximized: 6
        property bool helpVisible: false
    }
    AuroraeButtonGroup {
        id: leftButtonGroup
        width: childrenRect.width
        buttons: [DecorationOptions.DecorationButtonMenu]
        anchors.left: parent.left
        anchors.leftMargin: decoration.client.maximized ? 6 : 9
    }
    AuroraeButtonGroup {
        id: rightButtonGroup
        width: childrenRect.width
        buttons: [DecorationOptions.DecorationButtonQuickHelp, DecorationOptions.DecorationButtonClose,
                  DecorationOptions.DecorationButtonMaximizeRestore]
        anchors.right: parent.right
        anchors.rightMargin: decoration.client.maximized ? 6 : 9
    }
}
