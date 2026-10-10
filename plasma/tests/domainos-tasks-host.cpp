// SPDX-License-Identifier: GPL-3.0-or-later
// Test-only driver inside the real authorized /usr/bin/plasmawindowed host.
// No desktop-file identity, permission policy or production model is replaced.
#include <QApplication>
#include <QFile>
#include <QImage>
#include <QJsonArray>
#include <QJsonDocument>
#include <QJsonObject>
#include <QLabel>
#include <QMouseEvent>
#include <QSet>
#include <QTimer>
#include <QUuid>
#include <QWidget>
#include <QWindow>
#include <dlfcn.h>
#include <unistd.h>

using Children = QList<QObject *> (*)(QObject *);
using Grab = QImage (*)(QWindow *);
static QObject *fixture = nullptr;
static QWindow *host = nullptr;
static QList<QWidget *> owned;
static QJsonArray identities, observations;
static QJsonObject checks;
static int phase = 0, attempts = 0;

static QObject *find(QObject *object, Children children)
{
    if (!object) return nullptr;
    if (object->objectName() == "domainosTasksNativeHost") return object;
    if (object->inherits("QQuickItem"))
        for (auto child : children(object)) if (auto result = find(child, children)) return result;
    return nullptr;
}
static QVariant invoke(const char *method, const QVariant &first = {}, const QVariant &second = {})
{
    QVariant result;
    if (second.isValid()) QMetaObject::invokeMethod(fixture, method, Qt::DirectConnection,
        Q_RETURN_ARG(QVariant, result), Q_ARG(QVariant, first), Q_ARG(QVariant, second));
    else if (first.isValid()) QMetaObject::invokeMethod(fixture, method, Qt::DirectConnection,
        Q_RETURN_ARG(QVariant, result), Q_ARG(QVariant, first));
    else QMetaObject::invokeMethod(fixture, method, Qt::DirectConnection, Q_RETURN_ARG(QVariant, result));
    return result;
}
static QJsonObject state() { return QJsonDocument::fromJson(invoke("state").toString().toUtf8()).object(); }
static QJsonObject byTitle(const QJsonObject &snapshot, int index)
{
    for (const auto value : snapshot["windows"].toArray()) {
        const auto row = value.toObject();
        if (row["title"].toString() == owned[index]->windowTitle()) return row;
    }
    return {};
}
static QJsonObject coordinates(int index)
{
    return QJsonDocument::fromJson(invoke("coordinates", owned[index]->windowTitle()).toString().toUtf8()).object();
}
static void click(int index, Qt::KeyboardModifiers modifiers = Qt::NoModifier)
{
    const auto position = coordinates(index);
    const QPointF local(position["x"].toDouble(), position["y"].toDouble());
    const QPointF global = host->mapToGlobal(local.toPoint());
    QMouseEvent press(QEvent::MouseButtonPress, local, global, Qt::LeftButton, Qt::LeftButton, modifiers);
    QApplication::sendEvent(host, &press);
    QMouseEvent release(QEvent::MouseButtonRelease, local, global, Qt::LeftButton, Qt::NoButton, modifiers);
    QApplication::sendEvent(host, &release);
}
static bool request(int index, const char *action)
{
    const auto identity = identities[index].toObject();
    const auto result = QJsonDocument::fromJson(invoke("action", identity["key"].toString(), QString::fromLatin1(action)).toString().toUtf8()).object();
    observations.append(QJsonObject{{"action", action}, {"result", result}, {"identity", identity}});
    return result["state"].toString() == "requested";
}
static void complete()
{
    const auto grab = reinterpret_cast<Grab>(dlsym(RTLD_DEFAULT, "_ZN12QQuickWindow10grabWindowEv"));
    checks["native_host_frame_capture_saved"] = host && grab && grab(host).save(qEnvironmentVariable("IRIX_DOMAINOS_TASK_CAPTURE"));
    QJsonObject report{{"checks", checks}, {"final_state", fixture ? state() : QJsonObject()},
        {"owned_identities", identities}, {"observations", observations}, {"host_pid", int(getpid())},
        {"host_executable", QFile::symLinkTarget("/proc/self/exe")},
        {"application_name", QCoreApplication::applicationName()}, {"desktop_file_name", QGuiApplication::desktopFileName()}};
    QFile file(qEnvironmentVariable("IRIX_DOMAINOS_TASK_REPORT"));
    if (file.open(QIODevice::WriteOnly)) file.write(QJsonDocument(report).toJson());
    for (auto widget : owned) widget->close();
    QCoreApplication::quit();
}
static void tick()
{
    if (++attempts > 160) { checks["native_scenario_completed"] = false; complete(); return; }
    if (!fixture) {
        const auto children = reinterpret_cast<Children>(dlsym(RTLD_DEFAULT, "_ZNK10QQuickItem10childItemsEv"));
        for (auto candidate : QGuiApplication::allWindows())
            if (children && (fixture = find(candidate->property("contentItem").value<QObject *>(), children))) { host = candidate; break; }
        if (!fixture) { QTimer::singleShot(100, tick); return; }
    }
    const auto snapshot = state();
    if (phase == 0) {
        for (int index = 0; index < 3; ++index) if (coordinates(index).isEmpty()) { QTimer::singleShot(100, tick); return; }
        checks["real_plasma_host_loaded_production_tasks"] = true;
        bool valid = true;
        QSet<QString> ids;
        for (int index = 0; index < 3; ++index) {
            const auto row = byTitle(snapshot, index);
            const auto id = row["windowIds"].toArray().first().toString();
            valid &= !QUuid(id).isNull() && row["pid"].toInt() == getpid() && row["key"].toString() == "window:" + id;
            identities.append(QJsonObject{{"key", row["key"]}, {"windowIds", row["windowIds"]}, {"pid", row["pid"]}, {"title", row["title"]}});
            ids.insert(id);
        }
        checks["three_owned_native_uuid_pid_identities"] = valid && ids.size() == 3;
        checks["privileged_executable_is_real_plasmawindowed"] = QFile::symLinkTarget("/proc/self/exe") == "/usr/bin/plasmawindowed";
        observations.append(QJsonObject{{"phase", "initial"}, {"state", snapshot}});
        click(0);
        checks["single_click_selection_is_immediate"] = state()["selected"].toArray() == QJsonArray{identities[0].toObject()["key"]};
        click(1, Qt::ControlModifier);
        checks["control_click_accumulates_native_identities"] = state()["selected"].toArray().size() == 2;
        checks["native_minimize_request_sent"] = request(1, "minimize");
        phase = 1;
    } else if (phase == 1) {
        if (!byTitle(snapshot, 1)["minimized"].toBool()) { QTimer::singleShot(100, tick); return; }
        checks["native_minimize_state_observed"] = true;
        checks["minimize_affected_only_selected_target"] = !byTitle(snapshot, 0)["minimized"].toBool() && !byTitle(snapshot, 2)["minimized"].toBool();
        observations.append(QJsonObject{{"phase", "minimized"}, {"state", snapshot}});
        checks["native_activation_request_sent"] = request(1, "activate");
        phase = 2;
    } else if (phase == 2) {
        const auto row = byTitle(snapshot, 1);
        if (row["minimized"].toBool() || !row["active"].toBool() || !owned[1]->isActiveWindow()) { QTimer::singleShot(100, tick); return; }
        checks["native_restore_and_activation_observed"] = true;
        checks["activation_confirmed_by_owned_client_focus"] = owned[1]->isActiveWindow();
        observations.append(QJsonObject{{"phase", "activated"}, {"state", snapshot}});
        checks["native_maximize_request_sent"] = request(0, "maximize");
        phase = 3;
    } else if (phase == 3) {
        if (!byTitle(snapshot, 0)["maximized"].toBool() || !owned[0]->isMaximized()) { QTimer::singleShot(100, tick); return; }
        checks["native_maximize_state_observed"] = true;
        checks["maximize_confirmed_by_owned_client_configure"] = owned[0]->isMaximized();
        checks["maximize_affected_only_selected_target"] = !byTitle(snapshot, 1)["maximized"].toBool() && !byTitle(snapshot, 2)["maximized"].toBool();
        observations.append(QJsonObject{{"phase", "maximized"}, {"state", snapshot}});
        checks["native_close_request_sent"] = request(2, "close");
        phase = 4;
    } else if (phase == 4) {
        if (!byTitle(snapshot, 2).isEmpty() || owned[2]->isVisible()) { QTimer::singleShot(100, tick); return; }
        checks["native_close_removes_only_target"] = !byTitle(snapshot, 0).isEmpty() && !byTitle(snapshot, 1).isEmpty() && owned[0]->isVisible() && owned[1]->isVisible();
        const auto selected = snapshot["selected"].toArray();
        checks["native_selection_survives_unselected_target_close"] = selected.size() == 2 && selected.contains(identities[0].toObject()["key"]) && selected.contains(identities[1].toObject()["key"]);
        observations.append(QJsonObject{{"phase", "closed"}, {"state", snapshot}});
        checks["native_scenario_completed"] = true;
        complete(); return;
    }
    QTimer::singleShot(100, tick);
}
extern "C" int interceptedExec() asm("_ZN12QApplication4execEv");
extern "C" int interceptedExec()
{
    const auto original = reinterpret_cast<int (*)()>(dlsym(RTLD_NEXT, "_ZN12QApplication4execEv"));
    if (!original) return 2;
    for (int index = 0; index < 3; ++index) {
        auto widget = new QWidget;
        widget->setWindowTitle(QString("DomainOS owned Wayland task %1").arg(index));
        widget->resize(260, 160);
        auto text = new QLabel(widget->windowTitle(), widget);
        text->setGeometry(10, 10, 240, 130);
        text->setAlignment(Qt::AlignCenter);
        widget->show(); owned.append(widget);
    }
    QTimer::singleShot(1200, tick);
    return original();
}
