/*
    SPDX-FileCopyrightText: 2011 Martin Gräßlin <mgraesslin@kde.org>
    SPDX-FileCopyrightText: 2012 Gregor Taetzner <gregor@freenet.de>
    SPDX-FileCopyrightText: 2012 Marco Martin <mart@kde.org>
    SPDX-FileCopyrightText: 2013 David Edmundson <davidedmundson@kde.org>
    SPDX-FileCopyrightText: 2015 Eike Hein <hein@kde.org>
    SPDX-FileCopyrightText: 2021 Mikel Johnson <mikel5764@gmail.com>
    SPDX-FileCopyrightText: 2021 Noah Davis <noahadvs@gmail.com>

    SPDX-License-Identifier: GPL-2.0-or-later
*/

pragma ComponentBehavior: Bound

import QtQuick
import QtQuick.Layouts
import org.kde.plasma.plasmoid
import org.kde.plasma.core as PlasmaCore
import org.kde.ksvg as KSvg
import org.kde.plasma.components as PC3
import org.kde.plasma.private.kicker as Kicker
import org.kde.kirigami as Kirigami

import "code/tools.js" as Tools

PlasmoidItem {
    id: kickoff

    width: Kirigami.Units.iconSizes.huge
    height: Kirigami.Units.iconSizes.huge

    // The properties are defined here instead of the singleton because each
    // instance of Kickoff requires different instances of these properties

    readonly property bool inPanel: [
        PlasmaCore.Types.TopEdge,
        PlasmaCore.Types.RightEdge,
        PlasmaCore.Types.BottomEdge,
        PlasmaCore.Types.LeftEdge,
    ].includes(Plasmoid.location)
    readonly property bool vertical: Plasmoid.formFactor === PlasmaCore.Types.Vertical

    // Used to prevent the width from changing frequently when the scrollbar appears or disappears
    readonly property bool mayHaveGridWithScrollBar: Plasmoid.configuration.applicationsDisplay === 0
        || (Plasmoid.configuration.favoritesDisplay === 0 && kickoff.rootModel.favoritesModel.count > minimumGridRowCount * minimumGridRowCount)

    //BEGIN Models
    readonly property Kicker.RootModel rootModel: Kicker.RootModel {
        autoPopulate: false

        // TODO: appletInterface property now can be ported to "applet" and have the real Applet* assigned directly
        appletInterface: kickoff

        appNameFormat: Plasmoid.configuration.appNameFormat
        flat: true // have categories, but no subcategories
        sorted: Plasmoid.configuration.alphaSort
        showSeparators: true
        showTopLevelItems: true

        showAllApps: true
        showAllAppsCategorized: false
        showRecentApps: false
        showRecentDocs: false
        showPowerSession: false
        showFavoritesPlaceholder: true

        Component.onCompleted: {
            favoritesModel.initForClient("org.kde.plasma.kickoff.favorites.instance-" + Plasmoid.id)

            if (!Plasmoid.configuration.favoritesPortedToKAstats) {
                if (favoritesModel.count < 1) {
                    favoritesModel.portOldFavorites(Plasmoid.configuration.favorites);
                }
                Plasmoid.configuration.favoritesPortedToKAstats = true;
            }
        }
    }

    readonly property Kicker.RunnerModel runnerModel: Kicker.RunnerModel {
        query: kickoff.searchField ? kickoff.searchField.text : ""
        onRequestUpdateQuery: query => {
            if (kickoff.searchField) {
                kickoff.searchField.text = query;
            }
        }
        appletInterface: kickoff
        mergeResults: true
        favoritesModel: rootModel.favoritesModel
    }

    readonly property Kicker.ComputerModel computerModel: Kicker.ComputerModel {
        appletInterface: kickoff
        favoritesModel: rootModel.favoritesModel
        systemApplications: Plasmoid.configuration.systemApplications
        Component.onCompleted: {
            //systemApplications = Plasmoid.configuration.systemApplications;
        }
    }

    readonly property alias recentUsageModel: recentUsageModel
    Kicker.RecentUsageModel {
        id: recentUsageModel
        favoritesModel: rootModel.favoritesModel
    }

    readonly property alias frequentUsageModel: frequentUsageModel
    Kicker.RecentUsageModel {
        id: frequentUsageModel
        favoritesModel: rootModel.favoritesModel
        ordering: 1 // Popular / Frequently Used
    }
    //END

    //BEGIN UI elements
    // Set in FullRepresentation.qml
    property Item header: null

    // Set in Header.qml
    // QTBUG Using PC3.TextField as type makes assignment fail
    // "Cannot assign QObject* to TextField_QMLTYPE_8*"
    property Item searchField: null

    // Set in FullRepresentation.qml, ApplicationPage.qml, PlacesPage.qml
    property Item sideBar: null // is null when searching
    property Item contentArea: null // is searchView when searching

    // Set in NormalPage.qml
    property Item footer: null

    // True when central pane (and header) LayoutMirroring diverges from global
    // LayoutMirroring, in order to achieve the desired sidebar position
    readonly property bool paneSwap: Plasmoid.configuration.paneSwap
    readonly property bool sideBarOnRight: (Qt.application.layoutDirection == Qt.RightToLeft) != paneSwap
    // References to items according to their focus chain order
    readonly property Item firstHeaderItem: header ? (paneSwap ? header.pinButton : header.avatar) : null
    readonly property Item lastHeaderItem: header ? (paneSwap ? header.avatar : header.pinButton) : null
    readonly property Item firstCentralPane: paneSwap ? contentArea : sideBar
    readonly property Item lastCentralPane: paneSwap ? sideBar : contentArea

    readonly property Item dragSource: Item {
        id: dragSource // BUG 449426
        property Item sourceItem
        Drag.dragType: Drag.Automatic
    }
    //END

    //BEGIN Metrics
    readonly property KSvg.FrameSvgItem backgroundMetrics: KSvg.FrameSvgItem {
        // Inset defaults to a negative value when not set by margin hints
        readonly property real leftPadding: Math.round(margins.left - Math.max(inset.left, 0))
        readonly property real rightPadding: Math.round(margins.right - Math.max(inset.right, 0))
        readonly property real topPadding: Math.round(margins.top - Math.max(inset.top, 0))
        readonly property real bottomPadding: Math.round(margins.bottom - Math.max(inset.bottom, 0))
        readonly property real spacing: Math.round(leftPadding)
        visible: false
        imagePath: Plasmoid.formFactor === PlasmaCore.Types.Planar ? "widgets/background" : "dialogs/background"
    }

    // This is here rather than in the singleton with the other metrics items
    // because the list delegate's height depends on a configuration setting
    // and the singleton can't access those
    readonly property real listDelegateHeight: listDelegate.height
    KickoffListDelegate {
        id: listDelegate
        visible: false
        enabled: false
        model: null
        index: -1
        text: "asdf"
        url: ""
        decoration: "start-here-kde"
        description: "asdf"
        action: null
        indicator: null
    }

    // Used to show smaller Kickoff on small screens
    readonly property int minimumGridRowCount: Math.min(Screen.desktopAvailableWidth, Screen.desktopAvailableHeight) * Screen.devicePixelRatio < KickoffSingleton.gridCellSize * 4 + (fullRepresentationItem ? fullRepresentationItem.normalPage.preferredSideBarWidth : KickoffSingleton.gridCellSize * 2) ? 2 : 4
    //END

    Plasmoid.icon: Plasmoid.configuration.icon

    switchWidth: fullRepresentationItem ? fullRepresentationItem.Layout.minimumWidth : -1
    switchHeight: fullRepresentationItem ? fullRepresentationItem.Layout.minimumHeight : -1

    preferredRepresentation: compactRepresentation

    fullRepresentation: FullRepresentation { focus: true }

    // Only exists because the default CompactRepresentation doesn't:
    // - open on drag
    // - allow defining a custom drop handler
    // - expose the ability to show text below or beside the icon
    // TODO remove once it gains those features
    compactRepresentation: MouseArea {
        id: compactRoot

        // Taken from DigitalClock to ensure uniform sizing when next to each other
        readonly property bool tooSmall: Plasmoid.formFactor === PlasmaCore.Types.Horizontal && Math.round(2 * (compactRoot.height / 5)) <= Kirigami.Theme.smallFont.pixelSize

        readonly property bool shouldHaveIcon: Plasmoid.formFactor === PlasmaCore.Types.Vertical || Plasmoid.icon !== ""
        readonly property bool shouldHaveLabel: Plasmoid.formFactor !== PlasmaCore.Types.Vertical && Plasmoid.configuration.menuLabel !== ""

        readonly property int iconSize: Kirigami.Units.iconSizes.large
        readonly property int panelPadding: kickoff.inPanel ? 6 : 0
        readonly property int panelGlyphLimit: 32
        readonly property Item displayedIcon: imageFallback.visible ? imageFallback : (buttonIcon.valid ? buttonIcon : buttonIconFallback)
        readonly property real iconAspect: imageFallback.visible
            ? imageFallback.sourceSize.width / Math.max(1, imageFallback.sourceSize.height)
            : Math.max(1, displayedIcon.implicitWidth) / Math.max(1, displayedIcon.implicitHeight)
        // Outer panel metrics use the old transversal extent, never the inset glyph.
        readonly property real externalIconExtent: Math.min(Kirigami.Units.iconSizes.huge,
            Math.max(1, kickoff.vertical ? compactRoot.width : compactRoot.height))
        // Subpixel widths keep extreme image aspects inside both glyph bounds.
        readonly property real panelGlyphWidth: Math.max(0, Math.min(panelGlyphLimit,
            Math.max(0, compactRoot.width - 2 * panelPadding - 2),
            Math.min(panelGlyphLimit, Math.max(0, compactRoot.height - 2 * panelPadding - 2)) * iconAspect))
        readonly property real panelGlyphHeight: panelGlyphWidth / iconAspect

        readonly property var sizing: {
            const externalWidth = kickoff.inPanel
                ? (kickoff.vertical ? externalIconExtent : externalIconExtent * iconAspect)
                : displayedIcon.width;
            const externalHeight = kickoff.inPanel
                ? (kickoff.vertical ? externalIconExtent / iconAspect : externalIconExtent)
                : displayedIcon.height;

            let impWidth = 0;
            if (shouldHaveIcon) {
                impWidth += externalWidth;
            }
            if (shouldHaveLabel) {
                const captionWidth = kickoff.inPanel ? labelMetrics.contentWidth : labelTextField.contentWidth;
                impWidth += captionWidth + labelTextField.Layout.leftMargin + labelTextField.Layout.rightMargin;
            }
            const impHeight = externalHeight > 0 ? externalHeight : iconSize

            // at least square, but can be wider/taller
            if (kickoff.inPanel) {
                if (kickoff.vertical) {
                    return {
                        preferredWidth: iconSize,
                        preferredHeight: Math.max(impHeight, 2 * panelPadding + 4)
                    };
                } else { // horizontal
                    return {
                        preferredWidth: shouldHaveIcon ? Math.max(impWidth, 2 * panelPadding + 4) : impWidth,
                        preferredHeight: iconSize
                    };
                }
            } else {
                return {
                    preferredWidth: impWidth,
                    preferredHeight: Kirigami.Units.iconSizes.small,
                };
            }
        }

        implicitWidth: iconSize
        implicitHeight: iconSize

        Layout.preferredWidth: sizing.preferredWidth
        Layout.preferredHeight: sizing.preferredHeight
        Layout.minimumWidth: Layout.preferredWidth
        Layout.minimumHeight: Layout.preferredHeight

        hoverEnabled: true

        property bool wasExpanded

        Accessible.name: Plasmoid.title
        Accessible.role: Accessible.Button

        KSvg.FrameSvgItem {
            anchors.fill: parent
            anchors.margins: 2
            z: -1
            imagePath: "widgets/button"
            prefix: compactRoot.pressed ? "pressed" : (compactRoot.containsMouse ? "hover" : "normal")
        }

        onPressed: wasExpanded = kickoff.expanded
        onClicked: kickoff.expanded = !wasExpanded

        DropArea {
            id: compactDragArea
            anchors.fill: parent
            onEntered: drag => {
                if (drag.hasUrls) {
                    expandOnDragTimer.start()
                }
            }
            onExited: expandOnDragTimer.stop()
        }

        Timer {
            id: expandOnDragTimer
            // this is an interaction and not an animation, so we want it as a constant
            interval: 250
            onTriggered: kickoff.expanded = true
        }

        // Preserve the old caption width even when the inset presentation elides.
        PC3.Label {
            id: labelMetrics
            visible: false
            enabled: false
            height: compactRoot.height
            text: labelTextField.text
            textFormat: Text.StyledText
            wrapMode: Text.NoWrap
            font: labelTextField.font
            fontSizeMode: Text.VerticalFit
            minimumPointSize: labelTextField.minimumPointSize
        }

        RowLayout {
            id: iconLabelRow
            anchors.fill: parent
            anchors.margins: compactRoot.panelPadding
            spacing: 0
            transform: Translate {
                x: kickoff.inPanel && compactRoot.pressed ? 1 : 0
                y: kickoff.inPanel && compactRoot.pressed ? 1 : 0
            }

            Kirigami.Icon {
                id: buttonIcon

                Layout.fillWidth: !kickoff.inPanel && kickoff.vertical
                Layout.fillHeight: !kickoff.inPanel && !kickoff.vertical
                Layout.preferredWidth: kickoff.inPanel ? compactRoot.panelGlyphWidth : (kickoff.vertical ? -1 : height / (implicitHeight / implicitWidth))
                Layout.preferredHeight: kickoff.inPanel ? compactRoot.panelGlyphHeight : (!kickoff.vertical ? -1 : width * (implicitHeight / implicitWidth))
                Layout.maximumHeight: kickoff.inPanel ? compactRoot.panelGlyphHeight : Kirigami.Units.iconSizes.huge
                Layout.maximumWidth: kickoff.inPanel ? compactRoot.panelGlyphWidth : Kirigami.Units.iconSizes.huge
                Layout.alignment: Qt.AlignVCenter | Qt.AlignHCenter
                source: Tools.iconOrDefault(Plasmoid.formFactor, Plasmoid.icon)
                active: false // Classic relief belongs to the frame; keep SGI icon colors.
                roundToIconSize: implicitHeight === implicitWidth
                visible: valid && !imageFallback.visible
            }

            Kirigami.Icon {
                id: buttonIconFallback
                // fallback is assumed to be square
                Layout.fillWidth: !kickoff.inPanel && kickoff.vertical
                Layout.fillHeight: !kickoff.inPanel && !kickoff.vertical
                Layout.preferredWidth: kickoff.inPanel ? compactRoot.panelGlyphWidth : (kickoff.vertical ? -1 : height)
                Layout.preferredHeight: kickoff.inPanel ? compactRoot.panelGlyphHeight : (!kickoff.vertical ? -1 : width)
                Layout.maximumWidth: kickoff.inPanel ? compactRoot.panelGlyphWidth : -1
                Layout.maximumHeight: kickoff.inPanel ? compactRoot.panelGlyphHeight : -1
                Layout.alignment: Qt.AlignVCenter | Qt.AlignHCenter

                source: buttonIcon.valid ? null : Tools.defaultIconName
                active: false // Classic relief belongs to the frame; keep SGI icon colors.
                visible: !buttonIcon.valid && Plasmoid.icon !== "" && !imageFallback.visible
            }

            Image {
                id: imageFallback

                readonly property bool nonSquareImage: sourceSize.width != sourceSize.height

                visible: nonSquareImage && status == Image.Ready
                source: {
                    const value = String(Plasmoid.icon);
                    // Theme icon names belong to Kirigami.Icon. Image would
                    // otherwise resolve them as relative filenames.
                    if (value.startsWith(":/")) {
                        return "qrc" + value;
                    }
                    return value.startsWith("/") || /^[A-Za-z][A-Za-z0-9+.-]*:/.test(value)
                        ? value : "";
                }

                Layout.fillWidth: !kickoff.inPanel && kickoff.vertical
                Layout.fillHeight: !kickoff.inPanel && !kickoff.vertical
                Layout.preferredWidth: kickoff.inPanel ? compactRoot.panelGlyphWidth : (kickoff.vertical ? -1 : height / (implicitHeight / implicitWidth))
                Layout.preferredHeight: kickoff.inPanel ? compactRoot.panelGlyphHeight : (!kickoff.vertical ? -1 : width * (implicitHeight / implicitWidth))
                Layout.maximumHeight: kickoff.inPanel ? compactRoot.panelGlyphHeight : (kickoff.vertical ? -1 : Kirigami.Units.iconSizes.huge)
                Layout.maximumWidth: kickoff.inPanel ? compactRoot.panelGlyphWidth : (kickoff.vertical ? Kirigami.Units.iconSizes.huge : -1)
                Layout.alignment: Qt.AlignVCenter | Qt.AlignHCenter
                fillMode: Image.PreserveAspectFit
            }

            PC3.Label {
                id: labelTextField

                Layout.fillHeight: true
                Layout.fillWidth: kickoff.inPanel
                Layout.leftMargin: Kirigami.Units.smallSpacing
                Layout.rightMargin: Kirigami.Units.smallSpacing

                text: Plasmoid.configuration.menuLabel
                textFormat: Text.StyledText
                horizontalAlignment: Text.AlignLeft
                verticalAlignment: Text.AlignVCenter
                wrapMode: Text.NoWrap
                elide: kickoff.inPanel ? Text.ElideRight : Text.ElideNone
                fontSizeMode: kickoff.inPanel ? Text.Fit : Text.VerticalFit
                font.pixelSize: compactRoot.tooSmall ? Kirigami.Theme.defaultFont.pixelSize : Kirigami.Units.iconSizes.roundedIconSize(Kirigami.Units.gridUnit * 2)
                minimumPointSize: Kirigami.Theme.smallFont.pointSize
                visible: compactRoot.shouldHaveLabel
            }
        }
    }

    Kicker.ProcessRunner {
        id: processRunner
    }

    Plasmoid.contextualActions: [
        PlasmaCore.Action {
            text: i18n("Edit Applications…")
            icon.name: "kmenuedit"
            visible: Plasmoid.immutability !== PlasmaCore.Types.SystemImmutable
            onTriggered: processRunner.runMenuEditor()
        }
    ]

    Component.onCompleted: {
        if (Plasmoid.hasOwnProperty("activationTogglesExpanded")) {
            Plasmoid.activationTogglesExpanded = true
        }
    }
} // root
