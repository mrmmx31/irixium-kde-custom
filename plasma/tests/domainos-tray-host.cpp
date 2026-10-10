// SPDX-FileCopyrightText: 2026 IRIX Classic contributors
// SPDX-License-Identifier: GPL-3.0-or-later
// Native Plasma host observer and pointer driver; private test use only.
#include <QApplication>
#include <QCursor>
#include <QFile>
#include <QDBusConnection>
#include <QDBusMessage>
#include <QDBusPendingCall>
#include <QImage>
#include <QJsonArray>
#include <QJsonDocument>
#include <QJsonObject>
#include <QMouseEvent>
#include <QProcess>
#include <QScreen>
#include <QTimer>
#include <QTest>
#include <QWindow>
#include <dlfcn.h>

using Children = QList<QObject *> (*)(QObject *);
using Grab = QImage (*)(QWindow *);
using Map = QPointF (*)(const QObject *, const QObject *, const QPointF &);
static QObject *fixture = nullptr;
static QWindow *hostWindow = nullptr;
static QJsonObject report;
static int stage = 0, retries = 0;
static bool finishing = false;
static QJsonArray hoverEvents;
class HoverObserver:public QObject {
    bool eventFilter(QObject *object,QEvent *event) override {
        if(stage>=16 && (event->type()==QEvent::MouseMove || event->type()==QEvent::HoverEnter || event->type()==QEvent::HoverLeave)) {
            QJsonObject entry{{"stage",stage},{"type",int(event->type())},{"class",QString(object->metaObject()->className())},{"name",object->objectName()},{"isSni",fixture && object==fixture->property("hoverSni").value<QObject *>()}};
            if(event->type()==QEvent::MouseMove) {
                const auto mouse=static_cast<QMouseEvent *>(event);
                entry["localX"]=mouse->position().x();entry["localY"]=mouse->position().y();entry["buttons"]=int(mouse->buttons());
            }
            hoverEvents.append(entry);
        }
        return false;
    }
};

static QObject *find(QObject *object, const QString &name)
{
    if (!object) return nullptr;
    if (object->objectName() == name) return object;
    auto children = reinterpret_cast<Children>(dlsym(RTLD_DEFAULT,"_ZNK10QQuickItem10childItemsEv"));
    if (children && object->inherits("QQuickItem")) for (QObject *child : children(object)) {
        if (auto result = find(child,name)) return result;
    }
    return nullptr;
}
static bool click(const QString &name, Qt::MouseButton button = Qt::LeftButton)
{
    const auto map = reinterpret_cast<Map>(dlsym(RTLD_DEFAULT,"_ZNK10QQuickItem9mapToItemEPKS_RK7QPointF"));
    if (!map) return false;
    for (auto window : QGuiApplication::allWindows()) {
        if (!window->isVisible()) continue;
        auto content = window->property("contentItem").value<QObject *>();
        auto target = find(content,name);
        if (!target) continue;
        auto point = map(target,content,QPointF(target->property("width").toDouble()/2,target->property("height").toDouble()/2));
        QTest::mouseMove(window,point.toPoint());
        QTest::mouseClick(window,button,Qt::NoModifier,point.toPoint());
        return true;
    }
    return false;
}
static void finish(const QString &failure = {})
{
    if (finishing) return;
    finishing = true;
    if (!failure.isEmpty()) report["failure"] = failure;
    // Remove fixture-only clients while QApplication still exists. Native
    // DataEngine service jobs retain QEventLoopLockers until their source goes
    // away; leaving artificial clients alive past app destruction is unsafe.
    auto call=QDBusMessage::createMethodCall("org.kde.StatusNotifierWatcher","/StatusNotifierWatcher","org.kde.StatusNotifierWatcher","ClearTestItems");
    QDBusConnection::sessionBus().asyncCall(call);
    QTimer::singleShot(350,[](){
        if (fixture) report["after_fixture_disconnect"]=QJsonDocument::fromJson(fixture->property("snapshotJson").toString().toUtf8()).object();
        QFile file(qEnvironmentVariable("IRIX_DOMAINOS_TRAY_REPORT"));
        if (file.open(QIODevice::WriteOnly)) file.write(QJsonDocument(report).toJson());
        QCoreApplication::quit();
    });
}
static void step()
{
    if (!fixture) for (auto window : QGuiApplication::allWindows()) {
        fixture = find(window->property("contentItem").value<QObject *>(),"domainosTrayFixture");
        if (fixture) {
            hostWindow=window;
            hostWindow->setFlags(Qt::Tool|Qt::FramelessWindowHint);
            hostWindow->setGeometry(200,600,640,109);hostWindow->show();
            break;
        }
    }
    if (!fixture) { finish("Fixture did not load"); return; }
    auto snapshot = QJsonDocument::fromJson(fixture->property("snapshotJson").toString().toUtf8()).object();
    if (stage == 0 && snapshot["visible"].toArray().size() < 10 && ++retries < 20) {
        QTimer::singleShot(500,step); return;
    }
    const QStringList names{"initial","overflow","status","hidden_in_overflow","pagination","reorder","native_notifications","native_network","native_volume","native_bluetooth","sni_activate","sni_context","native_policy_change","width_fallback","overflow_sni_activate","hidden_sni_activate","hints_enabled","hints_disabled","hints_restored"};
    QJsonObject popupWindows;
    QJsonArray nativeTooltipWindows;
    snapshot["hostHeight"]=hostWindow ? hostWindow->height() : -1;
    const auto map=reinterpret_cast<Map>(dlsym(RTLD_DEFAULT,"_ZNK10QQuickItem9mapToItemEPKS_RK7QPointF"));
    auto nativeTrayItem=hostWindow ? find(hostWindow->property("contentItem").value<QObject *>(),"domainosRealTray") : nullptr;
    const auto trayOrigin=nativeTrayItem && map ? map(nativeTrayItem,nullptr,QPointF(0,0)) : QPointF();
    const auto trayRight=nativeTrayItem && map ? map(nativeTrayItem,nullptr,QPointF(nativeTrayItem->property("width").toDouble(),0)) : QPointF();
    const auto grab = reinterpret_cast<Grab>(dlsym(RTLD_DEFAULT,"_ZN12QQuickWindow10grabWindowEv"));
    for (auto window : QGuiApplication::allWindows()) {
        if (!window->isVisible() || !window->inherits("QQuickWindow")) continue;
        auto content=window->property("contentItem").value<QObject *>();
        QString role=window==hostWindow ? "host" : "native";
        if(QString(window->metaObject()->className()).contains("ToolTip")) {
            role="tooltip";
            nativeTooltipWindows.append(QString(window->metaObject()->className()));
        }
        for (const auto kind:QStringList{"Overflow","Status"}) if (find(content,"domainosTray"+kind+"Content")) {
            role=kind.toLower();
            popupWindows[role]=QJsonObject{{"separate",window!=hostWindow},
                {"outsideHost",hostWindow && !hostWindow->geometry().contains(window->geometry())},
                {"aboveTray",hostWindow && window->geometry().bottom()<=hostWindow->y()+trayOrigin.y()-5},
                {"alignedWithTrayRight",hostWindow && qAbs(window->geometry().right()+1-(hostWindow->x()+trayRight.x()))<=1},
                {"width",window->width()},{"height",window->height()},
                {"x",window->x()},{"y",window->y()}};
        }
        if (grab) grab(window).save(qEnvironmentVariable("IRIX_DOMAINOS_TRAY_DIR")+"/"+names[stage]+"-"+role+".png");
    }
    snapshot["popupWindows"]=popupWindows;
    snapshot["nativeTooltipWindows"]=nativeTooltipWindows;
    if(stage>=16)snapshot["hoverEvents"]=hoverEvents;
    if(stage>=16) {
        QJsonArray windows;
        for(auto window:QGuiApplication::allWindows())if(window->isVisible())windows.append(QJsonObject{{"class",QString(window->metaObject()->className())},{"id",QString::number(window->winId())},{"x",window->x()},{"y",window->y()},{"width",window->width()},{"height",window->height()}});
        snapshot["visibleWindows"]=windows;
        QProcess pointer;pointer.start("xdotool",{"getmouselocation","--shell"});pointer.waitForFinished(2000);snapshot["physicalPointer"]=QString::fromUtf8(pointer.readAllStandardOutput());
        if(hostWindow && hostWindow->screen())hostWindow->screen()->grabWindow(0).save(qEnvironmentVariable("IRIX_DOMAINOS_TRAY_DIR")+"/"+names[stage]+"-screen.png");
    }
    report[names[stage]] = snapshot;
    if (++stage == names.size()) { finish(); return; }
    fixture->setProperty("scenario",stage);
    if(stage==16 || stage==18) {
        QTimer::singleShot(100,[map](){
            auto target=fixture->property("hoverSni").value<QObject *>();
            auto content=hostWindow ? hostWindow->property("contentItem").value<QObject *>() : nullptr;
            const bool ready=target && hostWindow && map;
            if(ready) {
                const auto point=map(target,content,QPointF(target->property("width").toDouble()/2,target->property("height").toDouble()/2));
                const auto outside=hostWindow->mapToGlobal(QPoint(5,5));
                QProcess::execute("xdotool",{"mousemove","--sync",QString::number(outside.x()),QString::number(outside.y())});
                const auto global=hostWindow->mapToGlobal(point.toPoint());
                QTimer::singleShot(100,[point,global](){
                    // Keep physical X motion separate from synthetic QTest
                    // pointer devices and allow the outside event to dispatch.
                    QProcess::execute("xdotool",{"mousemove","--sync",QString::number(global.x()),QString::number(global.y())});
                    report[stage==16 ? "native_hover_geometry_enabled" : "native_hover_geometry_restored"]=QJsonObject{{"localX",point.x()},{"localY",point.y()},{"globalX",global.x()},{"globalY",global.y()},{"cursorX",QCursor::pos().x()},{"cursorY",QCursor::pos().y()}};
                });
            }
            report[stage==16 ? "native_hover_hints_enabled" : "native_hover_hints_restored"]=ready;
        });
    }
    if (stage == 1 || stage == 2 || stage == 10 || stage == 11 || stage == 14 || stage == 15) {
        const QString target = stage == 1 ? "domainosTrayNext" : stage == 2 ? "domainosTrayExpand" : stage==14 ? "domainosTrayOverflowSlot_1" : stage==15 ? "domainosTrayHiddenSlot_0" : "domainosTraySlot_0";
        const auto button=stage == 11 ? Qt::RightButton : Qt::LeftButton;
        QTimer::singleShot(100,[target,button,names](){ report["mouse_"+names[stage]] = click(target,button); });
    }
    QTimer::singleShot(stage==16 || stage==18 ? 1300 : 500,step);
}
extern "C" int interceptedExec() asm("_ZN12QApplication4execEv");
extern "C" int interceptedExec()
{
    const auto original = reinterpret_cast<int (*)()>(dlsym(RTLD_NEXT,"_ZN12QApplication4execEv"));
    if (!original || qEnvironmentVariable("IRIX_DOMAINOS_TRAY_TEST") != "1") return original ? original() : 1;
    auto observer=new HoverObserver;observer->setParent(QCoreApplication::instance());QCoreApplication::instance()->installEventFilter(observer);
    QTimer::singleShot(1500,step);
    QTimer::singleShot(22000,[](){ finish("Bounded tray test timeout"); });
    return original();
}
