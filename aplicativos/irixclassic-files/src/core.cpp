// SPDX-FileCopyrightText: 2026 mrmmx31
// SPDX-License-Identifier: GPL-2.0-or-later
#include "core.h"
#include <QCryptographicHash>
#include <QDir>
#include <QFileInfo>
#include <QRegularExpression>
namespace Irix {
QUrl locationFromText(const QString &raw, const QUrl &base)
{
    QString text = raw.trimmed();
    if (text.isEmpty()) return {};
    if (text == QStringLiteral("~")) text = QDir::homePath();
    else if (text.startsWith(QStringLiteral("~/"))) text = QDir::homePath() + text.mid(1);
    const QRegularExpression scheme(QStringLiteral("^[a-zA-Z][a-zA-Z0-9+.-]*:"));
    if (scheme.match(text).hasMatch()) return QUrl::fromEncoded(text.toUtf8());
    if (text.startsWith(QLatin1Char('/'))) return QUrl::fromLocalFile(QDir::cleanPath(text));
    if (base.isLocalFile()) return QUrl::fromLocalFile(QDir(base.toLocalFile()).absoluteFilePath(text));
    QUrl directory = base;
    if (!directory.path().endsWith(QLatin1Char('/'))) directory.setPath(directory.path() + QLatin1Char('/'));
    return directory.resolved(QUrl(text));
}
QList<QUrl> ancestors(const QUrl &input)
{
    QList<QUrl> result;
    if (!input.isValid() || input.isEmpty()) return result;
    QUrl url = input.adjusted(QUrl::NormalizePathSegments | QUrl::StripTrailingSlash | QUrl::RemoveQuery | QUrl::RemoveFragment);
    QString path = url.path();
    if (!path.startsWith(QLatin1Char('/'))) return {url};
    url.setPath(QStringLiteral("/")); result.append(url);
    QString prefix;
    for (const auto &part : path.split(QLatin1Char('/'), Qt::SkipEmptyParts)) {
        prefix += QLatin1Char('/') + part; url.setPath(prefix); result.append(url);
    }
    return result;
}
QString shelfKey(const QUrl &url)
{
    const auto safe = url.adjusted(QUrl::NormalizePathSegments | QUrl::StripTrailingSlash | QUrl::RemovePassword);
    return QString::fromLatin1(QCryptographicHash::hash(safe.toEncoded(), QCryptographicHash::Sha256).toHex());
}
QString displayedLocation(const QUrl &url)
{
    return url.isLocalFile() ? url.toLocalFile() : url.toDisplayString(QUrl::RemovePassword);
}
bool shelfReferenceAllowed(const QUrl &url)
{
    if (!url.isLocalFile()) return false;
    const QFileInfo info(url.toLocalFile());
    return info.exists() && (info.isFile() || info.isDir());
}
}
