// SPDX-FileCopyrightText: 2026 mrmmx31
// SPDX-License-Identifier: GPL-2.0-or-later
#include "shelf.h"
#include "core.h"
#include <QDir>
#include <QDragEnterEvent>
#include <QDropEvent>
#include <QFile>
#include <QFileInfo>
#include <QFileIconProvider>
#include <QJsonArray>
#include <QJsonDocument>
#include <QJsonObject>
#include <QKeyEvent>
#include <QMenu>
#include <QMimeData>
#include <QSaveFile>
#include <QStandardPaths>

Shelf::Shelf(QWidget *parent) : QListWidget(parent)
{
    setObjectName(QStringLiteral("IrixShelf"));
    setAccessibleName(tr("Shelf: references, not copies"));
    setViewMode(QListView::IconMode); setMovement(QListView::Static);
    setResizeMode(QListView::Adjust); setFlow(QListView::LeftToRight);
    setIconSize(QSize(24,24)); setGridSize(QSize(100,54)); setSpacing(2);
    setSelectionMode(QAbstractItemView::ExtendedSelection);
    setAcceptDrops(true); setDragEnabled(false);
    setHorizontalScrollBarPolicy(Qt::ScrollBarAsNeeded);
    auto pal = palette(); pal.setColor(QPalette::Base, QColor("#5680AB"));
    pal.setColor(QPalette::Text, Qt::black); setPalette(pal);
    setContextMenuPolicy(Qt::CustomContextMenu);
    connect(this, &QListWidget::customContextMenuRequested, this, [this](const QPoint &p) {
        QMenu menu(this);
        auto *open = menu.addAction(tr("Open reference")); open->setEnabled(selectedItems().size() == 1);
        auto *remove = menu.addAction(tr("Remove reference — keep original file")); remove->setEnabled(!selectedItems().isEmpty());
        auto *chosen = menu.exec(viewport()->mapToGlobal(p));
        if (chosen == remove) removeReferences();
        else if (chosen == open && selectedItems().size() == 1) Q_EMIT openRequested(selectedItems().first()->data(Qt::UserRole).toUrl());
    });
    connect(this, &QListWidget::itemSelectionChanged, this, [this] {
        const auto items = selectedItems();
        Q_EMIT previewRequested(items.size() == 1 ? items.first()->data(Qt::UserRole).toUrl() : QUrl());
    });
    connect(this, &QListWidget::itemActivated, this, [this](QListWidgetItem *item) { Q_EMIT openRequested(item->data(Qt::UserRole).toUrl()); });
}
QString Shelf::storageFile() const
{
    return QStandardPaths::writableLocation(QStandardPaths::AppDataLocation) + QStringLiteral("/shelves/") + m_key + QStringLiteral(".json");
}
void Shelf::setLocation(const QUrl &url)
{
    const auto key = Irix::shelfKey(url);
    if (key == m_key) return;
    m_key = key; load();
}
QList<QUrl> Shelf::references() const
{
    QList<QUrl> urls;
    for (int i=0; i<count(); ++i) urls.append(item(i)->data(Qt::UserRole).toUrl());
    return urls;
}
void Shelf::load()
{
    clear();
    setProperty("invalidStorage", false);
    QFile f(storageFile());
    if (!f.exists()) return;
    if (f.size() > 128*1024 || !f.open(QIODevice::ReadOnly)) { Q_EMIT message(tr("Shelf could not be read.")); return; }
    QJsonParseError error;
    const auto doc = QJsonDocument::fromJson(f.readAll(), &error);
    if (error.error != QJsonParseError::NoError || !doc.isObject() || !doc.object().value("urls").isArray()) { Q_EMIT message(tr("Shelf data is invalid; it was not replaced.")); setProperty("invalidStorage", true); return; }
    setProperty("invalidStorage", false);
    QFileIconProvider icons;
    const auto values = doc.object().value("urls").toArray();
    for (const auto &v : values) {
        if (count() >= Irix::MaxShelfItems) break;
        const QUrl url(v.toString());
        if (!url.isLocalFile()) continue;
        QFileInfo info(url.toLocalFile());
        auto *it = new QListWidgetItem(icons.icon(info), info.fileName().isEmpty() ? info.absoluteFilePath() : info.fileName(), this);
        it->setData(Qt::UserRole, url); it->setToolTip(url.toLocalFile());
        if (!info.exists()) it->setForeground(QColor("#404040"));
    }
}
bool Shelf::save()
{
    if (m_key.isEmpty() || property("invalidStorage").toBool()) { Q_EMIT message(tr("Shelf not saved: unknown or invalid storage.")); return false; }
    const QString path = storageFile();
    if (QFileInfo(path).isSymLink() || !QDir().mkpath(QFileInfo(path).absolutePath())) { Q_EMIT message(tr("Shelf destination is not writable.")); return false; }
    QJsonArray urls; for (const auto &url : references()) urls.append(url.toString(QUrl::FullyEncoded));
    QSaveFile f(path); f.setDirectWriteFallback(false);
    const auto data = QJsonDocument(QJsonObject{{"version", 1}, {"urls", urls}}).toJson();
    if (!f.open(QIODevice::WriteOnly) || f.write(data) != data.size() || !f.commit()) { Q_EMIT message(tr("Shelf could not be saved.")); return false; }
    return true;
}
void Shelf::addReferences(const QList<QUrl> &urls)
{
    if (property("invalidStorage").toBool()) { Q_EMIT message(tr("Repair the invalid Shelf file before editing references.")); return; }
    auto known = references(); QFileIconProvider icons;
    for (const auto &url : urls) {
        if (count() >= Irix::MaxShelfItems) { Q_EMIT message(tr("Shelf limit: 128 references per location.")); break; }
        if (!Irix::shelfReferenceAllowed(url) || known.contains(url)) continue;
        QFileInfo info(url.toLocalFile());
        auto *it = new QListWidgetItem(icons.icon(info), info.fileName().isEmpty() ? info.absoluteFilePath() : info.fileName(), this);
        it->setData(Qt::UserRole, url); it->setToolTip(url.toLocalFile()); known.append(url);
    }
    save();
}
void Shelf::removeReferences()
{
    if (property("invalidStorage").toBool()) return;
    const auto selected = selectedItems();
    for (auto *it : selected) delete takeItem(row(it));
    save(); // Only the JSON references are removed. Never call file deletion APIs.
}
void Shelf::dragEnterEvent(QDragEnterEvent *e)
{
    if (e->mimeData()->hasUrls() && (e->possibleActions() & (Qt::CopyAction | Qt::LinkAction))) e->acceptProposedAction(); else e->ignore();
}
void Shelf::dragMoveEvent(QDragMoveEvent *e)
{
    if (e->mimeData()->hasUrls() && (e->possibleActions() & (Qt::CopyAction | Qt::LinkAction))) e->acceptProposedAction(); else e->ignore();
}
void Shelf::dropEvent(QDropEvent *e)
{
    // Never acknowledge MoveAction: a drag source might then remove its files.
    if (!e->mimeData()->hasUrls() || !(e->possibleActions() & (Qt::CopyAction | Qt::LinkAction))) { e->ignore(); return; }
    addReferences(e->mimeData()->urls());
    e->setDropAction((e->possibleActions() & Qt::LinkAction) ? Qt::LinkAction : Qt::CopyAction); e->accept();
}
bool Shelf::event(QEvent *e)
{
    if (e->type() == QEvent::ShortcutOverride) {
        const auto *k = static_cast<QKeyEvent *>(e);
        if (k->key() == Qt::Key_Delete || k->key() == Qt::Key_Backspace) { e->accept(); return true; }
    }
    return QListWidget::event(e);
}
void Shelf::keyPressEvent(QKeyEvent *e)
{
    if (e->key() == Qt::Key_Delete || e->key() == Qt::Key_Backspace) { removeReferences(); e->accept(); return; }
    QListWidget::keyPressEvent(e);
}
