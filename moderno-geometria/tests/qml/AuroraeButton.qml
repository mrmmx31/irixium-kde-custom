import QtQuick
import org.kde.kwin.decoration
// Test double: validates Row geometry, not SVG rendering or window operations.
Item {
    property int buttonType: -1
    width: auroraeTheme.buttonWidth * auroraeTheme.buttonSizeFactor
    height: auroraeTheme.buttonHeight * auroraeTheme.buttonSizeFactor
    visible: buttonType !== DecorationOptions.DecorationButtonQuickHelp || auroraeTheme.helpVisible
}
