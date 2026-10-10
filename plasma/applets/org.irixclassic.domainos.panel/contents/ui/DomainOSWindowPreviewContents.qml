// SPDX-License-Identifier: GPL-3.0-or-later
import QtQuick
import QtQuick.Controls as Controls
import QtQuick.Layouts
import org.kde.kirigami as Kirigami
Controls.ScrollView {
    required property var preview

    id: view
    objectName: "domainosThumbnailScrollView"
    implicitWidth: preview.previewWidth * preview.columnCount + (preview.columnCount - 1) * 12 + 16
    implicitHeight: Math.min(preview.contentHeight, preview.maximumHeight)
    contentWidth: availableWidth
    contentHeight: grid.implicitHeight
    clip: true
    Controls.ScrollBar.horizontal:DomainOSViewScrollBar {
        scrollView:view
        colorPalette:preview.colorPalette;policy:Controls.ScrollBar.AlwaysOff
    }
    Controls.ScrollBar.vertical:DomainOSViewScrollBar {
        scrollView:view
        colorPalette:preview.colorPalette
        policy:grid.implicitHeight>view.availableHeight
            ? Controls.ScrollBar.AlwaysOn : Controls.ScrollBar.AlwaysOff
    }
    padding: 8
    // Keep labels and actions synchronous. Native capture belongs only to the
    // visible viewport; scrolling releases providers for cards which left it.
    readonly property real viewportLeft: contentItem && contentItem.contentX !== undefined
        ? contentItem.contentX : 0
    readonly property real viewportTop: contentItem && contentItem.contentY !== undefined
        ? contentItem.contentY : 0
    property var captionHintOwner: null
    function observeCaptionPointer(point) {
        const owner = captionHintOwner
        if (owner && !owner.pointerBelongsToHint(point)) {
            owner.hintRequested = false
            captionHintOwner = null
        }
    }
    function closeCaptionHints() {
        for (let index = 0; index < cards.count; ++index) {
            const card = cards.itemAt(index)
            if (card) card.closeCaptionHint()
        }
        captionHintOwner = null
    }
    // A row's leave signal can retain its last position. Observe fresh motion
    // in the entire owning window, including the frame and popup overlay.
    HoverHandler {
        parent: view.Window.window ? view.Window.window.contentItem : view
        enabled: view.visible && preview.tooltipVisible
        onPointChanged: if (hovered) view.observeCaptionPointer(parent.mapToGlobal(point.position))
        onHoveredChanged: {
            if (hovered) view.observeCaptionPointer(parent.mapToGlobal(point.position))
            else view.closeCaptionHints()
        }
    }
    DomainOSControlPalette { target: view }
    background: Rectangle {
        color: preview.colorPalette ? preview.colorPalette.background : view.Kirigami.Theme.backgroundColor
    }
    GridLayout {
        id: grid
        width: view.availableWidth
        columns: preview.columnCount
        rowSpacing: 12; columnSpacing: 12
        Repeater {
            id: cards
            model: preview.windowRecords
            delegate: Item {
                id: card
                required property var modelData
                objectName: "domainosThumbnailCard"
                Layout.fillWidth: true
                Layout.preferredWidth: preview.previewWidth
                Layout.preferredHeight: 178
                implicitWidth: preview.previewWidth
                implicitHeight: 178
                readonly property var windowId: modelData.windowIds && modelData.windowIds.length
                    ? modelData.windowIds[0] : undefined
                readonly property bool nativeIdentity: preview.backend === "x11"
                    ? Number.isInteger(windowId) && windowId > 0
                    : preview.backend === "wayland" && typeof windowId === "string" && windowId.length > 0
                readonly property bool intersectsViewport: width > 0 && height > 0
                    && x < view.viewportLeft + view.availableWidth && x + width > view.viewportLeft
                    && y < view.viewportTop + view.availableHeight && y + height > view.viewportTop
                readonly property bool liveAvailable: !!nativeImage.item && nativeImage.item.available
                function closeCaptionHint() { caption.hintRequested = false; captionHint.close() }
                readonly property string unavailableReason: {
                    if (preview.backend === "unavailable") return qsTr("Miniatura indisponível nesta sessão.")
                    if (!nativeIdentity) return qsTr("A janela não fornece uma identificação nativa para a miniatura.")
                    if (preview.backend === "x11" && modelData.minimized)
                        return qsTr("Miniatura indisponível enquanto a janela está minimizada em X11.")
                    if (nativeImage.status === Loader.Error)
                        return qsTr("O provedor nativo de miniaturas não está instalado ou disponível.")
                    return qsTr("O compositor ainda não disponibilizou a miniatura desta janela.")
                }
                Bevel {
                    anchors.fill: parent
                    paletteOverride: preview.colorPalette
                    thickness: 1; simpleRelief: true
                    sunken: pointer.pressed
                }
                Rectangle {
                    x: 4; y: 4; width: parent.width - 8; height: 132
                    color: preview.colorPalette ? preview.colorPalette.background : view.Kirigami.Theme.backgroundColor
                }
                Loader {
                    id: nativeImage
                    objectName: "domainosThumbnailNativeProvider"
                    x: 6; y: 6; width: parent.width - 12; height: 130
                    active: view.visible && card.intersectsViewport && preview.previewsEnabled
                        && preview.tooltipVisible && card.nativeIdentity
                        && !(preview.backend === "x11" && card.modelData.minimized)
                    // Loader cancellation discards unfinished incubation when
                    // the owner changes or this card leaves the viewport. Qt
                    // owns object creation; no GUI objects move to workers.
                    asynchronous: true
                    // An invisible WindowThumbnail never gets a scene
                    // graph node and cannot become available. Keep its
                    // loader visible while the provider initializes;
                    // the explicit unavailable label covers it.
                    visible: active
                    source: preview.backend === "wayland" ? "DomainOSWaylandThumbnail.qml" : "DomainOSX11Thumbnail.qml"
                    onLoaded: item.windowId = Qt.binding(() => card.windowId)
                }
                Text {
                    x: 12; y: 12; width: parent.width - 24; height: 118
                    visible: !card.liveAvailable
                    text: card.unavailableReason
                    textFormat: Text.PlainText; wrapMode: Text.Wrap
                    color: preview.colorPalette ? preview.colorPalette.text : view.Kirigami.Theme.textColor
                    horizontalAlignment: Text.AlignHCenter; verticalAlignment: Text.AlignVCenter
                    font.family: "Nimbus Sans"; font.pixelSize: 12; renderType: Text.NativeRendering
                }
                Text {
                    x: 6; y: 138; width: parent.width - 12; height: 34
                    id: caption
                    objectName: "domainosThumbnailCaption"
                    property bool hintRequested: false
                    function pointerBelongsToHint(point) {
                        const local = mapFromGlobal(point.x, point.y)
                        if (local.x >= 0 && local.x <= width && local.y >= 0 && local.y <= height) return true
                        if (!captionHint.visible || !captionHint.contentItem) return false
                        const inner = captionHint.contentItem.mapFromGlobal(point.x, point.y)
                        return inner.x >= -captionHint.leftPadding
                            && inner.x <= captionHint.contentItem.width + captionHint.rightPadding
                            && inner.y >= -captionHint.topPadding
                            && inner.y <= captionHint.contentItem.height + captionHint.bottomPadding
                    }
                    text: card.modelData.title
                    textFormat: Text.PlainText; elide: Text.ElideRight
                    color: preview.colorPalette ? preview.colorPalette.text : view.Kirigami.Theme.textColor
                    horizontalAlignment: Text.AlignHCenter; verticalAlignment: Text.AlignVCenter
                    font.family: "Nimbus Sans"; font.pixelSize: 13; renderType: Text.NativeRendering
                    HoverHandler {
                        id: captionHover
                        onHoveredChanged: {
                            if (hovered) {
                                if (view.captionHintOwner && view.captionHintOwner !== caption)
                                    view.captionHintOwner.hintRequested = false
                                view.captionHintOwner = caption
                                caption.hintRequested = true
                            }
                            else if (!caption.pointerBelongsToHint(caption.mapToGlobal(point.position)))
                                caption.hintRequested = false
                        }
                    }
                    DomainOSControlPalette { target: captionHint }
                    DomainOSControlPalette { target: captionHint.contentItem }
                    DomainOSControlPalette { target: captionHint.background }
                    Controls.ToolTip {
                        id: captionHint
                        objectName: "domainosThumbnailCaptionTooltip"
                        parent: caption
                        popupType: Controls.Popup.Item
                        enabled: true
                        // Preview mode replaces the Iconbox's text hints. Its
                        // elided caption still needs its own full-title hint.
                        visible: caption.hintRequested && caption.truncated
                            && (preview.previewsEnabled || preview.hintsEnabled)
                            && preview.tooltipVisible
                        delay: Kirigami.Units.toolTipDelay
                        timeout: -1
                        enter: null; exit: null
                        width: caption.width
                        height: Math.min(implicitHeight, Math.max(1, caption.y - 8))
                        x: 0; y: -height
                        margins: 0
                        closePolicy: Controls.Popup.NoAutoClose
                        // Long titles scroll within the image area instead of
                        // covering the caption or creating another native popup.
                        contentItem: Controls.ScrollView {
                            id: fullTitle
                            objectName: "domainosThumbnailCaptionHintScrollView"
                            clip: true
                            implicitHeight: Math.min(fullTitleText.implicitHeight,
                                Math.max(1, caption.y - 8 - captionHint.topPadding - captionHint.bottomPadding))
                            contentWidth: availableWidth
                            contentHeight: fullTitleText.implicitHeight
                            Controls.ScrollBar.horizontal:DomainOSViewScrollBar {
                                scrollView:fullTitle
                                colorPalette:preview.colorPalette;policy:Controls.ScrollBar.AlwaysOff
                            }
                            Controls.ScrollBar.vertical:DomainOSViewScrollBar {
                                scrollView:fullTitle
                                colorPalette:preview.colorPalette;policy:Controls.ScrollBar.AsNeeded
                            }
                            Text {
                                id: fullTitleText
                                objectName: "domainosThumbnailCaptionHintText"
                                width: fullTitle.availableWidth
                                text: card.modelData.title
                                textFormat: Text.PlainText; wrapMode: Text.Wrap
                                color: preview.colorPalette ? preview.colorPalette.text : captionHint.Kirigami.Theme.textColor
                                font: caption.font
                            }
                        }
                        HoverHandler {
                            parent: captionHint.background
                            enabled: captionHint.visible
                            onPointChanged: if (hovered && !caption.pointerBelongsToHint(
                                captionHint.background.mapToGlobal(point.position))) caption.hintRequested = false
                            onHoveredChanged: if (!hovered && !captionHover.hovered
                                && !caption.pointerBelongsToHint(captionHint.background.mapToGlobal(point.position)))
                                caption.hintRequested = false
                        }
                    }
                }
                MouseArea {
                    id: pointer
                    objectName: "domainosThumbnailPointer"
                    anchors.fill: parent
                    acceptedButtons: Qt.LeftButton
                    onClicked: {
                        const target = card.modelData
                        const owner = preview
                        owner.hideImmediately()
                        owner.activationRequested(target)
                    }
                }
                Accessible.role: Accessible.Button
                Accessible.name: modelData.title
                Accessible.description: liveAvailable ? qsTr("Prévia da janela; ativar") : unavailableReason
                Accessible.onPressAction: {
                    const target = card.modelData
                    const owner = preview
                    owner.hideImmediately()
                    owner.activationRequested(target)
                }
            }
        }
    }
}
