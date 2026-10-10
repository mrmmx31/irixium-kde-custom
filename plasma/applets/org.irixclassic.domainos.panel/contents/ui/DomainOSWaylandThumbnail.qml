// SPDX-FileCopyrightText: 2026 IRIX Classic contributors
// SPDX-License-Identifier: GPL-3.0-or-later
import org.kde.pipewire as PipeWire
import org.kde.taskmanager as TaskManager

// Kept in a separate, lazily loaded file: PipeWire is optional and X11 users
// must not import it or create screencasting requests merely to draw a task.
PipeWire.PipeWireSourceItem {
    id: thumbnail
    property var windowId: ""
    readonly property bool available: ready
    nodeId: request.nodeId
    TaskManager.ScreencastingRequest {
        id: request
        uuid: String(thumbnail.windowId)
    }
}
