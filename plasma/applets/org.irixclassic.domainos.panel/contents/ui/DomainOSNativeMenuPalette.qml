// SPDX-FileCopyrightText: 2026 IRIX Classic contributors
// SPDX-License-Identifier: GPL-3.0-or-later
import org.kde.plasma.core as PlasmaCore
import "../native/menu" as NativeMenu

// Loaded separately so a source checkout without its compiled helper keeps
// the KDE task menu available. Distributed installations verify the helper
// before replacing any resources.
NativeMenu.OwnMenuScope {
    palette: PlasmaCore.Theme.palette
}
