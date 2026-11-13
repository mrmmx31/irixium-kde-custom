// SPDX-FileCopyrightText: 2026 mrmmx31
// SPDX-License-Identifier: GPL-3.0-or-later
// Observation only: inspect the two genuine KDE programs on the private bus.
#include <QApplication>
#include <QFileInfo>
#include <QJsonArray>
#include <QJsonDocument>
#include <QJsonObject>
#include <QSaveFile>
#include <QSet>
#include <QTimer>
#include <QUrl>
#include <QWindow>
#include <QWidget>
#include <dlfcn.h>
#include <functional>

using QuickChildren = QList<QObject *> (*)(QObject *);
static QString bodyText;
static QJsonArray webViews;

static void inspect(QObject *object, QSet<QObject *> &seen, QJsonArray &items)
{
    if (!object || seen.contains(object) || seen.size() > 20000) return;
    seen.insert(object);
    QJsonObject item{{"class", object->metaObject()->className()}, {"objectName", object->objectName()}};
    for (const auto name : {"text", "title", "url", "currentModule", "header", "visible"}) {
        const auto value = object->property(name);
        if (!value.isValid()) continue;
        if (value.metaType().id() == QMetaType::QUrl) item[name] = value.toUrl().toString();
        else if (value.metaType().id() == QMetaType::Bool) item[name] = value.toBool();
        else if (value.canConvert<QString>() && !value.toString().isEmpty()) item[name] = value.toString().left(3000);
    }
    const QString type = object->metaObject()->className();
    if (item.contains("text") || item.contains("title") || item.contains("url") || type.contains("KCM") || type.contains("KCModule")) items.append(item);
    if (object->inherits("QWebEngineView")) {
        using Page = QObject *(*)(QObject *);
        using Plain = void (*)(QObject *, const std::function<void(const QString &)> &);
        const auto page = reinterpret_cast<Page>(dlsym(RTLD_DEFAULT, "_ZNK14QWebEngineView4pageEv"));
        const auto plain = reinterpret_cast<Plain>(dlsym(RTLD_DEFAULT, "_ZNK14QWebEnginePage11toPlainTextERKSt8functionIFvRK7QStringEE"));
        if (page && plain) plain(page(object), [](const QString &text) { bodyText = text.left(20000); });
        webViews.append(item);
    }
    for (auto child : object->children()) inspect(child, seen, items);
    if (object->inherits("QQuickItem")) {
        const auto children = reinterpret_cast<QuickChildren>(dlsym(RTLD_DEFAULT, "_ZNK10QQuickItem10childItemsEv"));
        if (children) for (auto child : children(object)) inspect(child, seen, items);
    }
}

static void observe()
{
    const auto executable = QFileInfo("/proc/self/exe").symLinkTarget();
    const auto name = QFileInfo(executable).fileName();
    QJsonArray windows, items;
    QSet<QObject *> seen;
    webViews = {};
    for (auto window : QGuiApplication::allWindows()) {
        windows.append(QJsonObject{{"title", window->title()}, {"visible", window->isVisible()},
            {"width", window->width()}, {"height", window->height()},
            {"winId", QString::number(window->winId())}, {"class", window->metaObject()->className()}});
        inspect(window, seen, items);
        inspect(window->property("contentItem").value<QObject *>(), seen, items);
    }
    for (auto widget : QApplication::topLevelWidgets()) inspect(widget, seen, items);
    inspect(QCoreApplication::instance(), seen, items);
    QJsonObject report{{"pid", QCoreApplication::applicationPid()}, {"executable", executable},
        {"argv", QJsonArray::fromStringList(QCoreApplication::arguments())},
        {"home", qEnvironmentVariable("HOME")}, {"config", qEnvironmentVariable("XDG_CONFIG_HOME")},
        {"data", qEnvironmentVariable("XDG_DATA_HOME")}, {"display", qEnvironmentVariable("DISPLAY")},
        {"sessionBus", qEnvironmentVariable("DBUS_SESSION_BUS_ADDRESS")},
        {"systemBus", qEnvironmentVariable("DBUS_SYSTEM_BUS_ADDRESS")},
        {"qtVersion", qVersion()}, {"windows", windows}, {"objects", items},
        {"webViews", webViews}, {"webBody", bodyText}};
    QSaveFile file(qEnvironmentVariable("IRIX_DOMAINOS_APPEARANCE_DIR") + "/" + name + "-observer.json");
    if (file.open(QIODevice::WriteOnly)) { file.write(QJsonDocument(report).toJson()); file.commit(); }
}

extern "C" int interceptedExec() asm("_ZN12QApplication4execEv");
extern "C" int interceptedExec()
{
    const auto original = reinterpret_cast<int (*)()>(dlsym(RTLD_NEXT, "_ZN12QApplication4execEv"));
    const auto name = QFileInfo(QFileInfo("/proc/self/exe").symLinkTarget()).fileName();
    if (original && !qEnvironmentVariable("IRIX_DOMAINOS_APPEARANCE_DIR").isEmpty()
        && (name == "systemsettings" || name == "khelpcenter")) {
        auto timer = new QTimer(QCoreApplication::instance());
        QObject::connect(timer, &QTimer::timeout, QCoreApplication::instance(), observe);
        timer->start(250);
    }
    return original ? original() : 1;
}
