// SPDX-FileCopyrightText: 2026 mrmmx31
// SPDX-License-Identifier: GPL-2.0-or-later
#include "classicshell.h"
#include "core.h"
#include "preview.h"
#include "shelf.h"
#include "dolphinmainwindow.h"
#include "dolphintabwidget.h"
#include "dolphinviewcontainer.h"
#include "views/dolphinview.h"
#include "views/zoomlevelinfo.h"
#include <KActionCollection>
#include <KStandardAction>
#include <KDialogJobUiDelegate>
#include <KIO/OpenUrlJob>
#include <KToolBar>
#include <QAction>
#include <QApplication>
#include <QDir>
#include <QDockWidget>
#include <QDragEnterEvent>
#include <QDropEvent>
#include <QFileInfo>
#include <QGraphicsView>
#include <QHBoxLayout>
#include <QLabel>
#include <QLineEdit>
#include <QMenu>
#include <QMenuBar>
#include <QMimeData>
#include <QScrollArea>
#include <QSettings>
#include <QSignalBlocker>
#include <QSlider>
#include <QSplitter>
#include <QStandardPaths>
#include <QTimer>
#include <QToolButton>
#include <QVBoxLayout>
#include <functional>
#include <stdexcept>

namespace {
QString uiConfig() { return QStandardPaths::writableLocation(QStandardPaths::ConfigLocation) + QStringLiteral("/irixclassic-files-ui.ini"); }
// Navigation-only drop pocket; do not return MoveAction to a drag source.
class DropPocket final : public QToolButton {
public:
    explicit DropPocket(QWidget *parent) : QToolButton(parent) { setAcceptDrops(true); }
    std::function<void(const QUrl &)> navigate;
protected:
    bool valid(const QMimeData *m) const { return m->hasUrls() && m->urls().size()==1 && m->urls().first().isLocalFile() && QFileInfo(m->urls().first().toLocalFile()).isDir(); }
    void dragEnterEvent(QDragEnterEvent *e) override { if (valid(e->mimeData()) && (e->possibleActions() & (Qt::CopyAction|Qt::LinkAction))) e->acceptProposedAction(); else e->ignore(); }
    void dragMoveEvent(QDragMoveEvent *e) override { if (valid(e->mimeData()) && (e->possibleActions() & (Qt::CopyAction|Qt::LinkAction))) e->acceptProposedAction(); else e->ignore(); }
    void dropEvent(QDropEvent *e) override {
        if (!valid(e->mimeData()) || !(e->possibleActions() & (Qt::CopyAction|Qt::LinkAction))) { e->ignore(); return; }
        if (navigate) navigate(e->mimeData()->urls().first());
        e->setDropAction((e->possibleActions() & Qt::LinkAction) ? Qt::LinkAction : Qt::CopyAction); e->accept();
    }
};
void viewPalette(DolphinView *view) {
    QPalette p = view->palette();
    p.setColor(QPalette::Base,QColor("#729C9C")); p.setColor(QPalette::Window,QColor("#729C9C"));
    p.setColor(QPalette::Text,Qt::black); p.setColor(QPalette::WindowText,Qt::black);
    view->setPalette(p);
    for (auto *v : view->findChildren<QGraphicsView *>()) { v->setPalette(p); v->viewport()->setPalette(p); v->viewport()->setAutoFillBackground(true); }
}
}
ClassicShell::ClassicShell(DolphinMainWindow *window) : QObject(window), m_window(window)
{
    auto *oldCentral = window->takeCentralWidget();
    m_tabs = qobject_cast<DolphinTabWidget *>(oldCentral);
    if (!m_tabs) { if (oldCentral) window->setCentralWidget(oldCentral); throw std::runtime_error("Dolphin central widget contract changed"); }
    auto *root = new QWidget(window); root->setObjectName(QStringLiteral("IrixClassicRoot"));
    auto *outer = new QVBoxLayout(root); outer->setContentsMargins(3,3,3,3); outer->setSpacing(3);
    auto *pathRow = new QHBoxLayout; pathRow->setSpacing(3); outer->addLayout(pathRow);
    auto *pocket = new DropPocket(root); pocket->setIcon(QIcon::fromTheme(QStringLiteral("folder")));
    pocket->setIconSize(QSize(28,28)); pocket->setFixedSize(42,42);
    pocket->setToolTip(tr("Drop one folder here to navigate — files are not moved."));
    pocket->setAccessibleName(tr("Folder drop pocket")); pocket->navigate = [this](const QUrl &u) { navigate(u); };
    pathRow->addWidget(pocket);
    auto *pathColumn = new QVBoxLayout; pathColumn->setSpacing(1); pathRow->addLayout(pathColumn,1);
    auto *breadcrumbScroll = new QScrollArea(root); breadcrumbScroll->setWidgetResizable(true);
    breadcrumbScroll->setFrameShape(QFrame::NoFrame); breadcrumbScroll->setFixedHeight(24);
    breadcrumbScroll->setVerticalScrollBarPolicy(Qt::ScrollBarAlwaysOff); breadcrumbScroll->setHorizontalScrollBarPolicy(Qt::ScrollBarAlwaysOff);
    auto *breadcrumb = new QWidget; m_ancestors = new QHBoxLayout(breadcrumb);
    m_ancestors->setContentsMargins(0,0,0,0); m_ancestors->setSpacing(0); breadcrumbScroll->setWidget(breadcrumb);
    pathColumn->addWidget(breadcrumbScroll);
    m_path = new QLineEdit(root); m_path->setAccessibleName(tr("Pathfinder location")); m_path->setObjectName(QStringLiteral("IrixPathfinder"));
    auto pathPal = m_path->palette(); pathPal.setColor(QPalette::Base,QColor("#B98E8E")); pathPal.setColor(QPalette::Text,Qt::black); m_path->setPalette(pathPal);
    pathColumn->addWidget(m_path);
    connect(m_path,&QLineEdit::returnPressed,this,[this] { navigate(Irix::locationFromText(m_path->text(),m_view ? m_view->url() : QUrl::fromLocalFile(QDir::homePath()))); });
    auto *history = new QToolButton(root); history->setIcon(QIcon::fromTheme(QStringLiteral("document-open-recent")));
    history->setFixedSize(42,42); history->setIconSize(QSize(26,26)); history->setPopupMode(QToolButton::InstantPopup);
    history->setToolTip(tr("Recycle: visited locations (not Refresh)"));
    m_historyMenu = new QMenu(history); history->setMenu(m_historyMenu); pathRow->addWidget(history);
    connect(m_historyMenu,&QMenu::aboutToShow,this,[this] {
        m_historyMenu->clear();
        for (const auto &url : m_history) { auto *a=m_historyMenu->addAction(Irix::displayedLocation(url)); connect(a,&QAction::triggered,this,[this,url]{navigate(url);}); }
        if (m_history.isEmpty()) m_historyMenu->addAction(tr("No previous locations"))->setEnabled(false);
    });
    auto *body = new QHBoxLayout; body->setSpacing(3); outer->addLayout(body,1);
    auto *rail = new QVBoxLayout; rail->setSpacing(2); body->addLayout(rail);
    auto button = [&](const QString &id) {
        auto *b = new QToolButton(root); b->setIconSize(QSize(18,18)); b->setFixedSize(27,27);
        if (auto *a = window->actionCollection()->action(id)) b->setDefaultAction(a);
        else { b->setText(QStringLiteral("?")); b->setToolTip(tr("Upstream action unavailable: %1").arg(id)); b->setEnabled(false); }
        rail->addWidget(b); return b;
    };
    button(QStringLiteral("icons")); button(QStringLiteral("compact")); button(QStringLiteral("details"));
    button(QStringLiteral("show_preview")); button(QStringLiteral("show_hidden_files"));
    button(QStringLiteral("go_up")); button(KStandardAction::name(KStandardAction::Redisplay)); button(QStringLiteral("toggle_search"));
    m_zoom = new QSlider(Qt::Vertical,root); m_zoom->setRange(ZoomLevelInfo::minimumLevel(),ZoomLevelInfo::maximumLevel());
    m_zoom->setFixedWidth(27); m_zoom->setMinimumHeight(100); m_zoom->setMaximumHeight(220);
    m_zoom->setToolTip(tr("Icon size — native Dolphin zoom")); m_zoom->setAccessibleName(tr("Vertical icon-size control"));
    rail->addWidget(m_zoom,1);
    auto *reset = button(QStringLiteral("view_zoom_reset")); reset->setToolTip(tr("Restore icon size")); rail->addStretch();
    connect(m_zoom,&QSlider::valueChanged,this,[this](int value) { if (m_view) m_view->view()->setZoomLevel(value); });
    m_split = new QSplitter(Qt::Vertical,root); m_split->setObjectName(QStringLiteral("IrixThreeAreas"));
    m_split->setChildrenCollapsible(false); m_split->setHandleWidth(7); body->addWidget(m_split,1);
    m_split->addWidget(oldCentral);
    m_shelf = new Shelf(m_split); m_shelf->setMinimumHeight(48); m_split->addWidget(m_shelf);
    m_viewer = new ContentViewer(m_split); m_split->addWidget(m_viewer);
    m_split->setStretchFactor(0,4); m_split->setStretchFactor(1,1); m_split->setStretchFactor(2,2);
    m_status = new QLabel(root); m_status->setTextFormat(Qt::PlainText); m_status->setWordWrap(true); outer->addWidget(m_status);
    window->setCentralWidget(root);
    // Original native navigation action remains alive on the hidden toolbar,
    // so Dolphin keeps its history/controller connections and shortcuts.
    if (window->toolBar()) window->toolBar()->hide();
    for (auto *dock : window->findChildren<QDockWidget *>()) dock->hide();
    window->menuBar()->show();
    if (auto *sort = window->actionCollection()->action(QStringLiteral("sort"))) sort->setText(tr("Sort"));
    m_tabs->setTabBarAutoHide(true);
    auto *extras = window->menuBar()->addMenu(tr("Classic"));
    auto *pin = extras->addAction(tr("Pin selected items to Shelf"));
    connect(pin,&QAction::triggered,this,&ClassicShell::pinSelection);
    auto *shelfToggle = extras->addAction(tr("Shelf")); shelfToggle->setCheckable(true);
    auto *viewerToggle = extras->addAction(tr("Content Viewer")); viewerToggle->setCheckable(true);
    QSettings ui(uiConfig(),QSettings::IniFormat);
    const bool shelfVisible = ui.value("shelfVisible",true).toBool();
    const bool viewerVisible = ui.value("viewerVisible",true).toBool();
    shelfToggle->setChecked(shelfVisible); viewerToggle->setChecked(viewerVisible);
    m_shelf->setVisible(shelfVisible); m_viewer->setVisible(viewerVisible);
    connect(shelfToggle,&QAction::toggled,m_shelf,&QWidget::setVisible);
    connect(viewerToggle,&QAction::toggled,this,[this](bool visible) { m_viewer->setVisible(visible); if (!visible) m_viewer->clear(); else if (m_view) { auto s=m_view->view()->selectedItems(); m_viewer->showUrl(s.size()==1 ? s.first().url() : QUrl()); } });
    m_split->setSizes({350,100,160});
    if (ui.contains("splitter")) m_split->restoreState(ui.value("splitter").toByteArray());
    connect(m_shelf,&Shelf::previewRequested,m_viewer,&ContentViewer::showUrl);
    connect(m_shelf,&Shelf::openRequested,this,&ClassicShell::openReference);
    connect(m_shelf,&Shelf::message,m_status,&QLabel::setText);
    connect(m_tabs,&DolphinTabWidget::activeViewChanged,this,&ClassicShell::bindView);
    connect(m_tabs,&DolphinTabWidget::currentUrlChanged,this,[this](const QUrl &) { syncLocation(); });
    connect(qApp,&QCoreApplication::aboutToQuit,this,&ClassicShell::saveLayout);
    bindView(window->activeViewContainer());
}
ClassicShell::~ClassicShell() = default;
void ClassicShell::saveLayout()
{
    QSettings ui(uiConfig(),QSettings::IniFormat);
    ui.setValue("splitter",m_split->saveState()); ui.setValue("shelfVisible",!m_shelf->isHidden()); ui.setValue("viewerVisible",!m_viewer->isHidden());
    ui.sync();
}
void ClassicShell::bindView(DolphinViewContainer *container)
{
    for (const auto &c : m_connections) disconnect(c);
    m_connections.clear(); m_view = container;
    if (!container) { m_viewer->clear(); return; }
    auto *v=container->view(); viewPalette(v);
    m_connections.append(connect(v,&DolphinView::selectionChanged,this,[this](const KFileItemList &s) {
        if (!m_viewer->isHidden()) m_viewer->showUrl(s.size()==1 ? s.first().url() : QUrl());
        m_status->setText(tr("%1 selected — Shelf stores references; Content Viewer is read-only.").arg(s.size()));
    }));
    m_connections.append(connect(v,&DolphinView::urlChanged,this,[this](const QUrl &) { syncLocation(); }));
    m_connections.append(connect(v,&DolphinView::directoryLoadingCompleted,this,[this] { if (m_view) { viewPalette(m_view->view()); syncLocation(); m_status->setText(tr("%1 items — based on Dolphin 25.04.3").arg(m_view->view()->itemsCount())); } }));
    m_connections.append(connect(v,&DolphinView::zoomLevelChanged,this,[this](int current,int) { const QSignalBlocker block(m_zoom); m_zoom->setValue(current); }));
    syncLocation();
}
void ClassicShell::syncLocation()
{
    if (!m_view) return;
    const auto url=m_view->url(); m_path->setText(Irix::displayedLocation(url));
    if (m_history.isEmpty() || m_history.first()!=url) { m_history.removeAll(url); m_history.prepend(url.adjusted(QUrl::RemovePassword)); while(m_history.size()>32) m_history.removeLast(); }
    m_shelf->setLocation(url); m_viewer->clear(); rebuildPath();
    const QSignalBlocker block(m_zoom); m_zoom->setValue(m_view->view()->zoomLevel());
}
void ClassicShell::rebuildPath()
{
    while(auto *item=m_ancestors->takeAt(0)) { delete item->widget(); delete item; }
    if (!m_view) return;
    const auto urls = Irix::ancestors(m_view->url());
    // Keep all ancestors available without forcing the window wider than screen.
    auto *overflow = new QToolButton; overflow->setText(QStringLiteral("…")); overflow->setPopupMode(QToolButton::InstantPopup);
    auto *all = new QMenu(overflow);
    for (const auto &url : urls) { auto *a=all->addAction(Irix::displayedLocation(url)); connect(a,&QAction::triggered,this,[this,url]{navigate(url);}); }
    overflow->setMenu(all); overflow->setAccessibleName(tr("All ancestor directories")); m_ancestors->addWidget(overflow);
    const qsizetype start = qMax<qsizetype>(0,urls.size()-5);
    for(qsizetype i=start;i<urls.size();++i) {
        const auto url=urls.at(i); auto *b=new QToolButton;
        QString label=url.fileName(); if(label.isEmpty()) label=url.isLocalFile() ? QStringLiteral("/") : url.scheme()+QStringLiteral(":/");
        b->setText(label.size()>20 ? label.left(17)+QStringLiteral("…") : label); b->setToolTip(Irix::displayedLocation(url));
        b->setMaximumWidth(145); b->setMinimumWidth(20); b->setAutoRaise(false);
        connect(b,&QToolButton::clicked,this,[this,url]{navigate(url);}); m_ancestors->addWidget(b);
    }
    m_ancestors->addStretch();
}
void ClassicShell::navigate(const QUrl &url)
{
    if (!url.isValid() || url.isEmpty() || url.scheme().isEmpty()) { m_status->setText(tr("Invalid location.")); return; }
    if (url.isLocalFile() && !QFileInfo(url.toLocalFile()).isDir()) { m_status->setText(tr("Pathfinder expects an existing directory.")); return; }
    if (m_view) m_view->setUrl(url);
}
void ClassicShell::pinSelection()
{
    if (!m_view) return;
    QList<QUrl> urls; for(const auto &item : m_view->view()->selectedItems()) urls.append(item.url());
    m_shelf->addReferences(urls);
}
void ClassicShell::openReference(const QUrl &url)
{
    if (!Irix::shelfReferenceAllowed(url)) { m_status->setText(tr("Reference target no longer exists, or is not a local regular file/directory.")); return; }
    if (QFileInfo(url.toLocalFile()).isDir()) { navigate(url); return; }
    auto *job=new KIO::OpenUrlJob(url,this);
    job->setRunExecutables(false);
    job->setUiDelegate(new KDialogJobUiDelegate(KJobUiDelegate::AutoHandlingEnabled,m_window)); job->start();
}
