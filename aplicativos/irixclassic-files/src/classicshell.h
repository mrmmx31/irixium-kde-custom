// SPDX-FileCopyrightText: 2026 mrmmx31
// SPDX-License-Identifier: GPL-2.0-or-later
#pragma once
#include <QObject>
#include <QPointer>
#include <QList>
#include <QUrl>
class DolphinMainWindow;
class DolphinViewContainer;
class DolphinTabWidget;
class Shelf;
class ContentViewer;
class QLineEdit;
class QHBoxLayout;
class QSlider;
class QLabel;
class QSplitter;
class QMenu;
class ClassicShell final : public QObject {
    Q_OBJECT
public:
    explicit ClassicShell(DolphinMainWindow *window);
    ~ClassicShell() override;
    Shelf *shelf() const { return m_shelf; }
    ContentViewer *viewer() const { return m_viewer; }
    void navigate(const QUrl &url);
    void pinSelection();
private:
    void bindView(DolphinViewContainer *container);
    void syncLocation();
    void rebuildPath();
    void saveLayout();
    void openReference(const QUrl &url);
    DolphinMainWindow *m_window;
    DolphinTabWidget *m_tabs;
    QPointer<DolphinViewContainer> m_view;
    QList<QMetaObject::Connection> m_connections;
    QList<QUrl> m_history;
    Shelf *m_shelf;
    ContentViewer *m_viewer;
    QSplitter *m_split;
    QLineEdit *m_path;
    QHBoxLayout *m_ancestors;
    QSlider *m_zoom;
    QLabel *m_status;
    QMenu *m_historyMenu;
};
