// SPDX-License-Identifier: GPL-3.0-or-later
// Native QMenu geometry in X11, where global window coordinates are observable.
#include <QApplication>
#include <QFile>
#include <QJsonArray>
#include <QJsonDocument>
#include <QJsonObject>
#include <QMenu>
#include <QScreen>
#include <QStyle>
#include <QTest>
#include <QTimer>
#include <QWidget>
#include <QWindow>
#include <dlfcn.h>
#include <unistd.h>

using Children = QList<QObject *> (*)(QObject *);
using Map = QPointF (*)(const QObject *, const QObject *, const QPointF &);
static QObject *fixture = nullptr, *button = nullptr;
static QWindow *host = nullptr;
static QList<QWidget *> owned;
static QJsonObject checks;
static QJsonArray cases;
static int phase = 0, attempts = 0, currentCase = 0;
static const double scales[] = {0.5, 1.0};

static QObject *find(QObject *node, const QString &name) {
    if (!node) return nullptr;
    if (node->objectName() == name) return node;
    const auto children = reinterpret_cast<Children>(dlsym(RTLD_DEFAULT, "_ZNK10QQuickItem10childItemsEv"));
    if (children && node->inherits("QQuickItem"))
        for (auto child : children(node)) if (auto result = find(child, name)) return result;
    return nullptr;
}
static QVariant invoke(const char *method, const QVariant &argument = {}) {
    QVariant result;
    if (argument.isValid()) QMetaObject::invokeMethod(fixture, method, Qt::DirectConnection,
        Q_RETURN_ARG(QVariant, result), Q_ARG(QVariant, argument));
    else QMetaObject::invokeMethod(fixture, method, Qt::DirectConnection, Q_RETURN_ARG(QVariant, result));
    return result;
}
static QMenu *menu() {
    for (auto widget : QApplication::allWidgets())
        if (auto result = qobject_cast<QMenu *>(widget); result && result->isVisible()) return result;
    return nullptr;
}
static void finish(const QString &error = {}) {
    QJsonObject environment;
    for (const auto name : {"HOME", "XDG_CONFIG_HOME", "XDG_DATA_HOME", "XDG_CACHE_HOME", "XDG_STATE_HOME", "XDG_RUNTIME_DIR", "DBUS_SESSION_BUS_ADDRESS"})
        environment[name] = qEnvironmentVariable(name);
    QJsonObject report{{"checks", checks}, {"cases", cases}, {"error", error},
        {"host_pid", int(getpid())}, {"widget_style", QApplication::style()->objectName()},
        {"namespace", environment},
        {"scope", "Owned X11 QWidget group, actual native KDE QMenu, bottom-edge host, 50% and 100% scales; no real profiles or window actions."}};
    QFile file(qEnvironmentVariable("IRIX_DOMAINOS_MENU_SCALE_REPORT"));
    if (file.open(QIODevice::WriteOnly)) file.write(QJsonDocument(report).toJson());
    for (auto widget : owned) widget->close();
    QCoreApplication::quit();
}
static void tick() {
    if (++attempts > 120) { checks["scenario_completed"] = false; finish("Native menu scenario timed out"); return; }
    if (!fixture) {
        for (auto window : QGuiApplication::allWindows()) if (window->isVisible())
            if (auto result = find(window->property("contentItem").value<QObject *>(), "domainosNativeMenuScaleFixture")) {
                fixture = result; host = window; break;
            }
        if (!fixture) { QTimer::singleShot(100, tick); return; }
        host->resize(594, 150); host->setPosition(100, 740);
    }
    const auto root = host->property("contentItem").value<QObject *>();
    const auto map = reinterpret_cast<Map>(dlsym(RTLD_DEFAULT, "_ZNK10QQuickItem9mapToItemEPKS_RK7QPointF"));
    if (!map) { finish("QtQuick map adapter unavailable"); return; }
    if (phase == 0) {
        const auto key = invoke("configureScale", scales[currentCase]).toString();
        button = find(root, "domainosLiveTask_" + key);
        if (key.isEmpty() || !button) { QTimer::singleShot(100, tick); return; }
        phase = 1; QTimer::singleShot(200, tick); return;
    }
    if (phase == 1) {
        const auto point = map(button, root, QPointF(button->property("width").toDouble()/2,
            button->property("height").toDouble()/2));
        QTest::mouseClick(host, Qt::RightButton, Qt::NoModifier, point.toPoint());
        checks[QString("case_%1_right_button_in_native_window").arg(currentCase)] = true;
        phase = 2; QTimer::singleShot(200, tick); return;
    }
    if (phase == 2) {
        auto popup = menu();
        if (!popup) { QTimer::singleShot(100, tick); return; }
        const auto top = host->mapToGlobal(map(button, root, QPointF(0, 0)).toPoint());
        QJsonArray actions; bool inside = true; int visible = 0;
        for (auto action : popup->actions()) if (action->isVisible()) {
            const auto rectangle = popup->actionGeometry(action);
            inside &= popup->rect().contains(rectangle); ++visible;
            actions.append(QJsonObject{{"text", action->text()}, {"inside", popup->rect().contains(rectangle)}});
        }
        cases.append(QJsonObject{{"scale", scales[currentCase]}, {"menu_x", popup->x()}, {"menu_y", popup->y()},
            {"menu_width", popup->width()}, {"menu_height", popup->height()},
            {"anchor_top", top.y()}, {"all_actions_inside", inside}, {"visible_actions", visible}, {"actions", actions}});
        const auto prefix = QString("case_%1_").arg(currentCase);
        checks[prefix + "all_actions_visible_on_first_open"] = visible >= 8 && inside;
        checks[prefix + "menu_within_real_screen"] = host->screen()->geometry().contains(popup->geometry());
        checks[prefix + "menu_entirely_above_real_anchor"] = popup->geometry().bottom() < top.y();
        checks[prefix + "native_capture_saved"] = popup->grab().save(qEnvironmentVariable("IRIX_DOMAINOS_MENU_SCALE_OUTPUT")
            + QString("/NATIVE-MENU-%1.png").arg(currentCase));
        popup->close(); phase = 3;
    } else if (phase == 3) {
        if (menu()) { QTimer::singleShot(100, tick); return; }
        if (++currentCase < 2) phase = 0;
        else { checks["scenario_completed"] = true; finish(); return; }
    }
    QTimer::singleShot(100, tick);
}
extern "C" int interceptedExec() asm("_ZN12QApplication4execEv");
extern "C" int interceptedExec() {
    const auto original = reinterpret_cast<int (*)()>(dlsym(RTLD_NEXT, "_ZN12QApplication4execEv"));
    if (!original) return 2;
    QApplication::setStyle("kvantum");
    for (int index = 0; index < 3; ++index) {
        auto widget = new QWidget;
        widget->setWindowTitle(QString("DomainOS menu scale owned %1").arg(index));
        widget->resize(260, 160); widget->show(); owned.append(widget);
    }
    QTimer::singleShot(900, tick);
    return original();
}
