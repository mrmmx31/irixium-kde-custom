pragma Singleton
import QtQml
// Test double only. These values are internal to the harness, not KDE ABI values.
QtObject {
    enum Button {
        DecorationButtonExplicitSpacer = 0,
        DecorationButtonMenu = 1,
        DecorationButtonApplicationMenu = 2,
        DecorationButtonMaximizeRestore = 3,
        DecorationButtonQuickHelp = 4,
        DecorationButtonClose = 5,
        DecorationButtonMinimize = 6
    }
}
