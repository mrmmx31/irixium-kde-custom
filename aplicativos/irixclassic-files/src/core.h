// SPDX-FileCopyrightText: 2026 mrmmx31
// SPDX-License-Identifier: GPL-2.0-or-later
#pragma once
#include <QList>
#include <QString>
#include <QUrl>

namespace Irix {
constexpr auto AppName = "irixclassic-files";
constexpr auto DesktopId = "io.github.mrmmx31.irixclassic.files";
constexpr auto Version = "0.1.0-alpha2";
constexpr int MaxShelfItems = 128;
QUrl locationFromText(const QString &text, const QUrl &base);
QList<QUrl> ancestors(const QUrl &url);
QString shelfKey(const QUrl &url);
QString displayedLocation(const QUrl &url);
bool shelfReferenceAllowed(const QUrl &url);
}
