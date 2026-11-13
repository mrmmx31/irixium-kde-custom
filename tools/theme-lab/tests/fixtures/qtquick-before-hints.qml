
import QtQuick 2.15
import QtQuick.Controls 2.15
import QtQuick.Layouts 1.15

ApplicationWindow {
    id: window
    objectName: "privateQtQuick__MAJOR__Window"
    width: 660
    height: 560
    visible: true
    title: "DomainOS SR10.4 — QtQuick__MAJOR__ / KDE"
    property int selectedRow: -1
    signal actionRecorded(string action, string detail)
    function log(action, detail) {
        statusLabel.text = action + ": " + detail
        actionRecorded(action, String(detail))
    }
    readonly property string nativePalettes: JSON.stringify({
        normalButton: {button: String(pressButton.palette.button),
                       buttonText: String(pressButton.palette.buttonText),
                       window: String(pressButton.palette.window),
                       highlight: String(pressButton.palette.highlight)},
        disabledButton: {button: String(disabledButton.palette.button),
                         buttonText: String(disabledButton.palette.buttonText),
                         window: String(disabledButton.palette.window),
                         highlight: String(disabledButton.palette.highlight)}
    })
    readonly property string nativeFont: pressButton.font.family + ";" + pressButton.font.pointSize
    menuBar: MenuBar {
        Menu {
            title: "Native menu"
            Action { text: "Record activation"; onTriggered: window.log("menu", "activated") }
            Action { text: "Checkable action"; checkable: true; checked: true }
            Action { text: "Unavailable action"; enabled: false }
            MenuSeparator {}
            Menu { title: "Submenu"; Action { text: "Native submenu item" } }
            Action { text: "Close only this gallery"; onTriggered: window.close() }
        }
    }
    ColumnLayout {
        anchors.fill: parent
        anchors.margins: 8
        Label {
            text: "REAL QtQuick__MAJOR__ controls | " + runtimeDescription
            Layout.fillWidth: true
            elide: Text.ElideRight
        }
        TabBar {
            id: pages
            objectName: "qtquick__MAJOR___tabs"
            Layout.fillWidth: true
            TabButton { text: "Controls" }
            TabButton { text: "Table" }
            TabButton { text: "Scroll" }
        }
        StackLayout {
            currentIndex: pages.currentIndex
            Layout.fillWidth: true
            Layout.fillHeight: true
            ColumnLayout {
                GroupBox {
                    title: "Native buttons and selection"
                    Layout.fillWidth: true
                    RowLayout {
                        Button {
                            id: pressButton
                            objectName: "qtquick__MAJOR___pressButton"
                            text: "Press and release"
                            onClicked: window.log("button", "clicked")
                        }
                        Button { text: "Latched"; checkable: true; checked: true }
                        Button {
                            id: disabledButton
                            objectName: "qtquick__MAJOR___disabledButton"
                            text: "Disabled"
                            enabled: false
                        }
                    }
                }
                RowLayout {
                    CheckBox { text: "Off" }
                    CheckBox { text: "Checked"; checked: true }
                    CheckBox { text: "Mixed"; tristate: true; checkState: Qt.PartiallyChecked }
                    CheckBox { text: "Disabled"; checked: true; enabled: false }
                }
                RowLayout {
                    RadioButton { text: "Radio A"; checked: true }
                    RadioButton { text: "Radio B" }
                    Switch {
                        objectName: "qtquick__MAJOR___switch"
                        text: "Native switch"
                        onToggled: window.log("switch", checked)
                    }
                    Switch { text: "Disabled"; checked: true; enabled: false }
                }
                GridLayout {
                    columns: 2
                    Layout.fillWidth: true
                    Label { text: "Combo" }
                    ComboBox {
                        objectName: "qtquick__MAJOR___combo"
                        model: ["First option", "Second option", "Third option"]
                        Layout.fillWidth: true
                        onActivated: window.log("combo", currentText)
                    }
                    Label { text: "Disabled combo" }
                    ComboBox { model: ["Unavailable"]; enabled: false; Layout.fillWidth: true }
                    Label { text: "Spin box" }
                    SpinBox {
                        objectName: "qtquick__MAJOR___spin"
                        from: -99; to: 999; value: 42; editable: true
                        onValueModified: window.log("spin", value)
                    }
                    Label { text: "Disabled spin" }
                    SpinBox { value: 42; enabled: false }
                    Label { text: "Text" }
                    TextField { text: "Editable native TextField"; Layout.fillWidth: true }
                    Label { text: "Disabled text" }
                    TextField { text: "Unavailable"; enabled: false; Layout.fillWidth: true }
                }
                RowLayout {
                    Label { text: "Slider" }
                    Slider {
                        id: slider
                        objectName: "qtquick__MAJOR___slider"
                        from: 0; to: 100; value: 43
                        Layout.fillWidth: true
                        onMoved: window.log("slider", value)
                    }
                    Slider { value: 0.43; enabled: false }
                }
                ProgressBar { from: 0; to: 100; value: slider.value; Layout.fillWidth: true }
                Item { Layout.fillHeight: true }
            }
            Frame {
                ColumnLayout {
                    anchors.fill: parent
                    RowLayout {
                        Repeater {
                            model: ["Item", "State", "Value"]
                            Label { text: modelData; Layout.fillWidth: true }
                        }
                    }
                    TableView {
                        id: table
                        objectName: "qtquick__MAJOR___table"
                        Layout.fillWidth: true
                        Layout.fillHeight: true
                        clip: true
                        model: galleryTableModel
                        columnSpacing: 1
                        rowSpacing: 1
                        delegate: ItemDelegate {
                            implicitWidth: 230
                            implicitHeight: 32
                            text: display
                            highlighted: row === window.selectedRow
                            onClicked: {
                                window.selectedRow = row
                                window.log("table cell", row + "," + column)
                            }
                        }
                        ScrollBar.vertical: ScrollBar { policy: ScrollBar.AlwaysOn }
                        ScrollBar.horizontal: ScrollBar { policy: ScrollBar.AlwaysOn }
                    }
                }
            }
            ScrollView {
                objectName: "qtquick__MAJOR___scrollView"
                clip: true
                ScrollBar.vertical.policy: ScrollBar.AlwaysOn
                ScrollBar.horizontal.policy: ScrollBar.AlwaysOn
                TextArea {
                    objectName: "qtquick__MAJOR___textArea"
                    text: artificialText
                    wrapMode: TextEdit.NoWrap
                    selectByMouse: true
                }
            }
        }
        RowLayout {
            Label {
                id: statusLabel
                text: "Artificial data only; controls inherit the private KDE scheme."
                Layout.fillWidth: true
                elide: Text.ElideRight
            }
            Button { text: "Save window proof"; onClicked: window.log("capture", "requested") }
        }
    }
}
