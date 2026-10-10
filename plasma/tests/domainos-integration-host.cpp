// SPDX-License-Identifier: GPL-3.0-or-later
// Test-only observer of production QML in private plasmawindowed.
#include <QApplication>
#include <QFile>
#include <QFileInfo>
#include <QImage>
#include <QJsonDocument>
#include <QJsonArray>
#include <QJsonObject>
#include <QPalette>
#include <QTimer>
#include <QWindow>
#include <dlfcn.h>

using Children = QList<QObject *> (*)(QObject *);
using Grab = QImage (*)(QWindow *);
using ItemWindow = QWindow * (*)(QObject *);
static int attempts = 0;
static QJsonObject finalState;
static QJsonArray popupChecks;
static QWindow *panelHost = nullptr;
static QObject *panelRoot = nullptr;
static int popupIndex = 0;
static const char *popupNames[] = {"domainosLocalHelpDialog", "domainosFailureDialog", "domainosHelpMenu", "domainosSessionMenu"};
static void finish()
{
    finalState["popup_windows"] = popupChecks;
    QFile report(qEnvironmentVariable("IRIX_DOMAINOS_INTEGRATION_REPORT"));
    if (report.open(QIODevice::WriteOnly)) report.write(QJsonDocument(finalState).toJson());
    QCoreApplication::quit();
}
static void popupStep()
{
    if (popupIndex >= 4) { finish(); return; }
    auto popup = panelRoot->findChild<QObject *>(QString::fromLatin1(popupNames[popupIndex]));
    if (popupIndex==0 && popup) {
        auto anchor=panelRoot->findChild<QObject *>("domainosShortcut_help");
        if (anchor) popup->setProperty("parent",QVariant::fromValue(anchor));
    }
    const bool opened = popup && QMetaObject::invokeMethod(popup, "open", Qt::DirectConnection);
    QTimer::singleShot(200, [popup, opened]() {
        const auto itemWindow = reinterpret_cast<ItemWindow>(dlsym(RTLD_DEFAULT, "_ZNK10QQuickItem6windowEv"));
        const auto grab = reinterpret_cast<Grab>(dlsym(RTLD_DEFAULT, "_ZN12QQuickWindow10grabWindowEv"));
        auto content = popup ? popup->property("contentItem").value<QObject *>() : nullptr;
        auto window = content && itemWindow ? itemWindow(content) : nullptr;
        const bool separate = window && window != panelHost && window->isVisible();
        const bool outside = separate && !panelHost->geometry().contains(window->geometry());
        const QString dir = QFileInfo(qEnvironmentVariable("IRIX_DOMAINOS_INTEGRATION_REPORT")).absolutePath();
        const bool saved = separate && grab && grab(window).save(dir + "/" + QString::fromLatin1(popupNames[popupIndex]) + ".png");
        popupChecks.append(QJsonObject{{"name",QString::fromLatin1(popupNames[popupIndex])},
            {"opened",opened},{"separate_window",separate},{"extends_outside_host",outside},{"capture_saved",saved},
            {"host_height",panelHost->height()},{"popup_height",window ? window->height() : 0}});
        if (popup) QMetaObject::invokeMethod(popup,"close",Qt::DirectConnection);
        ++popupIndex;
        QTimer::singleShot(50,popupStep);
    });
}
static QObject *find(QObject *object, Children children)
{
    if (!object) return nullptr;
    if (object->objectName() == "domainosPanel") return object;
    if (object->inherits("QQuickItem")) {
        for (QObject *item : children(object)) if (QObject *match = find(item, children)) return match;
    }
    return nullptr;
}
static void inspect()
{
    const auto children = reinterpret_cast<Children>(dlsym(RTLD_DEFAULT, "_ZNK10QQuickItem10childItemsEv"));
    const auto grab = reinterpret_cast<Grab>(dlsym(RTLD_DEFAULT, "_ZN12QQuickWindow10grabWindowEv"));
    QObject *panel = nullptr;
    QWindow *host = nullptr;
    for (auto window : QGuiApplication::allWindows()) {
        panel = children ? find(window->property("contentItem").value<QObject *>(), children) : nullptr;
        if (panel) { host = window; break; }
    }
    QVariant snapshot;
    if (panel) QMetaObject::invokeMethod(panel, "diagnosticSnapshot", Qt::DirectConnection, Q_RETURN_ARG(QVariant, snapshot));
    QJsonObject state = QJsonDocument::fromJson(snapshot.toString().toUtf8()).object();
    if (++attempts < 20 && (!panel || !state["timeAvailable"].toBool() || !state["sensors"].toObject()["available"].toBool()
            || state["workspaceCount"].toInt() != 1 || state["catalogCount"].toInt() == 0)) {
        QTimer::singleShot(500, inspect); return;
    }
    state["functional_composition_loaded"] = panel != nullptr;
    state["capture_saved"] = host && grab && grab(host).save(qEnvironmentVariable("IRIX_DOMAINOS_INTEGRATION_CAPTURE"));
    state["qt_version"] = qVersion();
    const QPalette palette = QApplication::palette();
    state["application_palette"] = QJsonObject{{"background", palette.color(QPalette::Window).name()},
        {"recessed", palette.color(QPalette::Base).name()}, {"text", palette.color(QPalette::WindowText).name()},
        {"blue", palette.color(QPalette::Highlight).name()}, {"white", palette.color(QPalette::HighlightedText).name()}};
    finalState=state;
    panelHost=host;
    panelRoot=panel;
    if (panel && host) {
        host->setGeometry(80,550,971,109);
        QTimer::singleShot(200,popupStep);
    } else finish();
}
extern "C" int interceptedExec() asm("_ZN12QApplication4execEv");
extern "C" int interceptedExec()
{
    const auto original = reinterpret_cast<int (*)()>(dlsym(RTLD_NEXT, "_ZN12QApplication4execEv"));
    if (!original) return 2;
    QTimer::singleShot(1500, inspect);
    return original();
}
