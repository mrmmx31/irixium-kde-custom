// SPDX-FileCopyrightText: 2026 mrmmx31
// SPDX-License-Identifier: GPL-2.0-or-later
#pragma once
#include <QListWidget>
#include <QUrl>
class Shelf final : public QListWidget {
    Q_OBJECT
public:
    explicit Shelf(QWidget *parent = nullptr);
    void setLocation(const QUrl &url);
    void addReferences(const QList<QUrl> &urls);
    void removeReferences();
    QList<QUrl> references() const;
Q_SIGNALS:
    void previewRequested(const QUrl &url);
    void openRequested(const QUrl &url);
    void message(const QString &text);
protected:
    void dragEnterEvent(QDragEnterEvent *) override;
    void dragMoveEvent(QDragMoveEvent *) override;
    void dropEvent(QDropEvent *) override;
    void keyPressEvent(QKeyEvent *) override;
    bool event(QEvent *) override;
private:
    void load();
    bool save();
    QString storageFile() const;
    QString m_key;
};
