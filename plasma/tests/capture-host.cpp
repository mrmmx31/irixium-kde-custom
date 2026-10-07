// SPDX-FileCopyrightText: 2026 mrmmx31
// SPDX-License-Identifier: GPL-2.0-or-later
// Test-only interposer for plasmawindowed. Never installed or used by a panel.
// QtQuick headers are deliberately unnecessary here: these three exported
// public Qt 6 methods use the same QObject/QWindow/QPointF/QImage ABI. Every
// symbol is checked before use; runtime and header versions are recorded.

#include <QApplication>
#include <QAbstractItemModel>
#include <QCoreApplication>
#include <QElapsedTimer>
#include <QFile>
#include <QImage>
#include <QJsonArray>
#include <QJsonDocument>
#include <QJsonObject>
#include <QPointer>
#include <QProcess>
#include <QTest>
#include <QTimer>
#include <QWindow>
#include <dlfcn.h>
#include <functional>

using ChildItems = QList<QObject *> (*)(QObject *);
using MapToScene = QPointF (*)(QObject *, const QPointF &);
using GrabWindow = QImage (*)(QWindow *);

static QObject *findItem(QObject *root, const QString &name, ChildItems children)
{
    if (!root) {
        return nullptr;
    }
    if (root->objectName() == name) {
        return root;
    }
    // Repeater delegates belong to the visual tree, which can differ from
    // QObject ownership. Qt 6 QList<T*> has the same pointer-list ABI here.
    if (root->inherits("QQuickItem")) {
        for (QObject *child : children(root)) {
            if (QObject *item = findItem(child, name, children)) {
                return item;
            }
        }
    }
    return nullptr;
}

static QJsonArray rect(QObject *item, MapToScene map)
{
    const QPointF origin = map(item, QPointF());
    return {origin.x(), origin.y(), item->property("width").toDouble(), item->property("height").toDouble()};
}

static void writeReport(const QJsonObject &report)
{
    QFile file(qEnvironmentVariable("IRIX_TEST_REPORT"));
    if (file.open(QIODevice::WriteOnly)) {
        file.write(QJsonDocument(report).toJson());
    } else {
        qCritical("IRIX_NATIVE_REPORT_WRITE_FAILED");
    }
    QCoreApplication::quit();
}

static void collectItems(QObject *root, const QString &name, ChildItems children, QList<QObject *> &items)
{
    if (!root) return;
    if (root->objectName() == name) items.append(root);
    if (root->inherits("QQuickItem")) {
        for (QObject *child : children(root)) collectItems(child, name, children, items);
    }
}

static bool waitFor(const std::function<bool()> &predicate, int timeout = 3000)
{
    QElapsedTimer elapsed;
    elapsed.start();
    while (!predicate() && elapsed.elapsed() < timeout) QTest::qWait(25);
    return predicate();
}

static bool runCommand(const QString &program, const QStringList &args, QString *output = nullptr)
{
    QProcess process;
    process.start(program, args);
    if (!process.waitForStarted(1000) || !process.waitForFinished(3000)) {
        process.kill();
        process.waitForFinished(1000);
        return false;
    }
    if (output) *output = QString::fromUtf8(process.readAllStandardOutput());
    return process.exitStatus() == QProcess::NormalExit && process.exitCode() == 0;
}

static QString normalizedId(QString id)
{
    if (id.endsWith(".desktop")) id.chop(8);
    return id;
}

// Inspect the actual native TasksModel. No delegate roles are injected or mocked.
static QJsonObject taskRoles(QAbstractItemModel *model, int row)
{
    QJsonObject result;
    if (row < 0 || row >= model->rowCount()) return result;
    const auto names = model->roleNames();
    for (auto it = names.cbegin(); it != names.cend(); ++it) {
        const QString name = QString::fromUtf8(it.value());
        if (QStringList{"AppId", "AppPid", "AppName", "IsWindow", "IsLauncher", "IsActive",
                        "IsMinimized", "IsGroupParent", "WinIdList"}.contains(name)) {
            const QVariant value = model->data(model->index(row, 0), it.key());
            result[name] = QJsonValue::fromVariant(value);
        }
    }
    result["row"] = row;
    return result;
}

static QJsonObject rolesFor(QAbstractItemModel *model, const QString &id)
{
    for (int row = 0; row < model->rowCount(); ++row) {
        const QJsonObject roles = taskRoles(model, row);
        if (roles["IsWindow"].toBool() && normalizedId(roles["AppId"].toString()) == id) return roles;
    }
    return {};
}

static QObject *delegateFor(QObject *root, const QString &id, ChildItems children)
{
    QList<QObject *> items;
    collectItems(root, "classicTask", children, items);
    for (QObject *task : items) {
        if (task->property("appId").toString() == id && task->property("isWindow").toBool()
            && !task->property("inPopup").toBool()) return task;
    }
    return nullptr;
}

static bool matchesState(const QJsonObject &roles, bool active, bool minimized)
{
    return roles["IsWindow"].toBool() && !roles["IsLauncher"].toBool()
        && !roles["IsGroupParent"].toBool() && roles["IsActive"].toBool() == active
        && roles["IsMinimized"].toBool() == minimized;
}

static void captureWindowTasks(QWindow *window, QObject *root, QJsonObject report,
                               ChildItems children, MapToScene map, GrabWindow grab)
{
    QObject *iconbox = findItem(root, "classicIconbox", children);
    if (!iconbox) iconbox = window->findChild<QObject *>("classicIconbox");
    if (!iconbox) iconbox = root->findChild<QObject *>("classicIconbox");
    // Plasma may display fullRepresentation without the owning PlasmoidItem
    // itself being in the visual child tree. The real delegate holds its
    // production tasksRoot reference; follow it rather than inventing roles.
    if (!iconbox) {
        QObject *task = findItem(root, "classicTask", children);
        if (task) iconbox = task->property("tasksRoot").value<QObject *>();
    }
    report["iconbox_root_found"] = bool(iconbox);
    if (iconbox) {
        report["iconbox_root_class"] = QString::fromLatin1(iconbox->metaObject()->className());
        const QVariant value = iconbox->property("tasksModel");
        report["model_property_type"] = QString::fromLatin1(value.typeName() ? value.typeName() : "invalid");
        QObject *object = value.value<QObject *>();
        if (object) report["model_property_class"] = QString::fromLatin1(object->metaObject()->className());
    }
    auto model = iconbox ? qobject_cast<QAbstractItemModel *>(iconbox->property("tasksModel").value<QObject *>()) : nullptr;
    report["native_tasks_model"] = bool(model);
    if (!model) {
        QJsonArray ownedNames, visualNames;
        for (QObject *object : window->findChildren<QObject *>()) {
            if (!object->objectName().isEmpty()) ownedNames.append(QJsonObject{{"name", object->objectName()},
                {"class", QString::fromLatin1(object->metaObject()->className())}});
        }
        QList<QObject *> named;
        collectItems(root, "classicTask", children, named);
        for (QObject *object : named) visualNames.append(QString::fromLatin1(object->metaObject()->className()));
        report["owned_names"] = ownedNames;
        report["visual_tasks"] = visualNames;
        report["window_title"] = window->title();
        report["window_size"] = QJsonArray{window->width(), window->height()};
        report["debug_capture"] = grab(window).save(qEnvironmentVariable("IRIX_TEST_CAPTURE") + ".debug.png");
        report["failure"] = "Native QAbstractItemModel TasksModel was not available";
        writeReport(report); return;
    }
    report["model_class"] = QString::fromLatin1(model->metaObject()->className());
    QJsonArray roleNames;
    for (const auto &name : model->roleNames()) roleNames.append(QString::fromUtf8(name));
    report["role_names"] = roleNames;
    QFile fixtureFile(qEnvironmentVariable("IRIX_TEST_WINDOWS"));
    if (!fixtureFile.open(QIODevice::ReadOnly)) {
        report["failure"] = "Disposable window readiness file is missing";
        writeReport(report); return;
    }
    const QJsonArray fixtures = QJsonDocument::fromJson(fixtureFile.readAll()).array();
    if (fixtures.size() != 3) {
        report["failure"] = "Exactly three disposable windows are required";
        writeReport(report); return;
    }
    window->resize(700, 160);
    QTest::qWait(250);
    QJsonArray cases;
    const QString captureBase = qEnvironmentVariable("IRIX_TEST_CAPTURE");
    for (int position = 0; position < fixtures.size(); ++position) {
        const QJsonObject fixture = fixtures[position].toObject();
        const QString id = fixture["desktop_id"].toString();
        const QString stateName = QStringList{"active", "inactive", "minimized"}[position];
        const bool active = position == 0;
        const bool minimized = position == 2;
        QJsonObject result{{"state", stateName}, {"fixture", fixture}};
        // Establish genuine X11 state through the private window manager.
        const QString editorId = fixtures[0].toObject()["win_id"].toString();
        const QString terminalId = fixtures[2].toObject()["win_id"].toString();
        bool arranged = runCommand("xdotool", {"windowmap", editorId})
            && runCommand("xdotool", {"windowmap", fixtures[1].toObject()["win_id"].toString()})
            && runCommand("xdotool", {"windowminimize", terminalId})
            && runCommand("xdotool", {"windowactivate", "--sync", editorId});
        const bool ready = arranged && waitFor([&] { return matchesState(rolesFor(model, id), active, minimized); });
        result["state_ready"] = ready;
        result["before_roles"] = rolesFor(model, id);
        const QJsonObject roles = result["before_roles"].toObject();
        bool idPresent = false;
        const quint64 expectedWin = fixture["win_id"].toString().toULongLong(nullptr, 16);
        for (const auto &nativeId : roles["WinIdList"].toArray()) {
            if (nativeId.toVariant().toULongLong() == expectedWin) idPresent = true;
        }
        result["identity_verified"] = ready && roles["AppPid"].toVariant().toLongLong() == fixture["pid"].toVariant().toLongLong() && idPresent;
        QObject *task = delegateFor(root, id, children);
        QObject *frame = task ? findItem(task, "classicTaskFrame", children) : nullptr;
        result["real_window_delegate"] = bool(task && frame);
        if (!result["identity_verified"].toBool() || !task || !frame) {
            result["failure"] = "Real task state/delegate/PID/native window identity could not be proven";
            cases.append(result); break;
        }
        const QPoint point = map(task, {task->property("width").toDouble() / 2,
                                       task->property("height").toDouble() / 2}).toPoint();
        result["task_rect"] = rect(task, map);
        QTest::mouseMove(window, point);
        QTest::qWait(80);
        const QString normalPath = captureBase + "." + stateName + ".normal.png";
        const QString pressedPath = captureBase + "." + stateName + ".pressed.png";
        result["normal_capture"] = grab(window).save(normalPath);
        result["normal_capture_file"] = normalPath;
        result["normal_prefix"] = frame->property("prefix").toStringList().join(",");
        QElapsedTimer feedback;
        feedback.start();
        QTest::mousePress(window, Qt::LeftButton, Qt::NoModifier, point);
        // Read immediately after event delivery, before qWait/processEvents.
        result["immediate_held_feedback"] = task->property("classicPressed").toBool();
        result["feedback_read_ns"] = double(feedback.nsecsElapsed());
        result["pressed_prefix"] = frame->property("prefix").toStringList().join(",");
        result["held_roles_unchanged"] = matchesState(rolesFor(model, id), active, minimized);
        QTest::qWait(120); // Settle only this optional test's screenshot.
        result["held_settled_roles_unchanged"] = matchesState(rolesFor(model, id), active, minimized);
        result["held_settled_feedback"] = task->property("classicPressed").toBool();
        result["pressed_capture"] = grab(window).save(pressedPath);
        result["pressed_capture_file"] = pressedPath;
        QTest::mouseMove(window, {-100, -100});
        QTest::mouseRelease(window, Qt::LeftButton, Qt::NoModifier, {-100, -100});
        QTest::qWait(80);
        result["cancel_clears_feedback"] = !task->property("classicPressed").toBool();
        result["cancel_roles_unchanged"] = matchesState(rolesFor(model, id), active, minimized);
        QTest::mouseMove(window, point);
        QTest::mousePress(window, Qt::LeftButton, Qt::NoModifier, point);
        result["action_press_feedback"] = task->property("classicPressed").toBool();
        result["action_waited_for_release"] = matchesState(rolesFor(model, id), active, minimized);
        QTest::mouseRelease(window, Qt::LeftButton, Qt::NoModifier, point);
        const bool actionReady = waitFor([&] { return matchesState(rolesFor(model, id), !active, active); });
        result["release_action_verified"] = actionReady;
        result["after_roles"] = rolesFor(model, id);
        result["expected_action"] = active ? "minimize" : (minimized ? "restore_and_activate" : "activate");
        QObject *afterTask = delegateFor(root, id, children);
        result["release_clears_feedback"] = afterTask && !afterTask->property("classicPressed").toBool();
        QString properties, actualActive;
        const bool x11Read = runCommand("xprop", {"-id", fixture["win_id"].toString(), "_NET_WM_STATE", "WM_STATE"}, &properties)
            && runCommand("xdotool", {"getactivewindow"}, &actualActive);
        result["x11_state"] = properties.trimmed();
        result["x11_active_window"] = actualActive.trimmed();
        result["x11_action_verified"] = x11Read && properties.contains("_NET_WM_STATE_HIDDEN") == active
            && (active ? actualActive.trimmed().toULongLong() != expectedWin : actualActive.trimmed().toULongLong() == expectedWin);
        cases.append(result);
        if (!actionReady) break;
    }
    report["window_tasks"] = cases;
    report["captured"] = !grab(window).isNull() && grab(window).save(captureBase);
    report["capture_size"] = QJsonArray{window->width(), window->height()};
    if (cases.size() != 3) report["failure"] = "Not all three genuine window task states were exercised";
    writeReport(report);
}

static void capture()
{
    auto children = reinterpret_cast<ChildItems>(dlsym(RTLD_DEFAULT, "_ZNK10QQuickItem10childItemsEv"));
    auto map = reinterpret_cast<MapToScene>(dlsym(RTLD_DEFAULT, "_ZNK10QQuickItem10mapToSceneERK7QPointF"));
    auto grab = reinterpret_cast<GrabWindow>(dlsym(RTLD_DEFAULT, "_ZN12QQuickWindow10grabWindowEv"));
    QJsonObject report{{"format", 1}, {"widget", qEnvironmentVariable("IRIX_TEST_WIDGET")},
                       {"qt_runtime", qVersion()}, {"qt_headers", QT_VERSION_STR},
                       {"public_quick_symbols", bool(children && map && grab)}};
    if (!children || !map || !grab || !QString::fromLatin1(qVersion()).startsWith("6.")) {
        report["failure"] = "Required public Qt 6 Quick symbols are unavailable";
        writeReport(report);
        return;
    }
    QJsonArray candidates;
    for (QWindow *window : QGuiApplication::allWindows()) {
        if (!window->isVisible() || !window->inherits("QQuickWindow")) {
            continue;
        }
        QObject *root = window->property("contentItem").value<QObject *>();
        const QString output = qEnvironmentVariable("IRIX_TEST_CAPTURE");
        if (qEnvironmentVariable("IRIX_TEST_WINDOW_TASKS") == "1") {
            const bool hasTask = findItem(root, "classicTask", children);
            candidates.append(QJsonObject{{"title", window->title()},
                {"size", QJsonArray{window->width(), window->height()}}, {"has_real_task", hasTask}});
            // KWin enables native startup-notification Quick windows too.
            // They are not the applet host and contain no task delegate.
            if (!hasTask
                && !window->findChild<QObject *>("classicIconbox")) continue;
            report["candidate_windows"] = candidates;
            report["selected_window_title"] = window->title();
            captureWindowTasks(window, root, report, children, map, grab);
            return;
        }
        const QImage normal = grab(window);
        report["captured"] = !normal.isNull() && normal.save(output);
        report["capture_size"] = QJsonArray{normal.width(), normal.height()};
        report["window_title"] = window->title();
        if (qEnvironmentVariable("IRIX_TEST_WIDGET") == "systemtray") {
            QObject *tray = findItem(root, "classicTray", children);
            report["tray_root"] = bool(tray);
            report["internal_systray"] = tray && tray->property("internalSystray").value<QObject *>() != nullptr;
        }
        if (qEnvironmentVariable("IRIX_TEST_WIDGET") != "iconbox") {
            writeReport(report);
            return;
        }
        QObject *task = findItem(root, "classicTask", children);
        QObject *frame = task ? findItem(task, "classicTaskFrame", children) : nullptr;
        report["real_task_delegate"] = bool(task && frame);
        if (!task || !frame) {
            report["failure"] = "Native task delegate/frame not found";
            writeReport(report);
            return;
        }
        report["task_rect"] = rect(task, map);
        const QPointF at = map(task, QPointF(task->property("width").toDouble() / 2,
                                           task->property("height").toDouble() / 2));
        QTest::mouseMove(window, at.toPoint());
        QTest::mousePress(window, Qt::LeftButton, Qt::NoModifier, at.toPoint());
        QCoreApplication::processEvents();
        report["held_feedback"] = task->property("classicPressed").toBool();
        report["pressed_prefix"] = frame->property("prefix").toStringList().join(",");
        const QPointer<QWindow> guardedWindow(window);
        const QPointer<QObject> guardedTask(task);
        // This timer settles only the test screenshot. Feedback was already
        // observed synchronously above; no timer is added to the applet.
        QTimer::singleShot(120, [guardedWindow, guardedTask, report, output, grab]() mutable {
            if (!guardedWindow || !guardedTask) {
                report["failure"] = "Task/window destroyed during test";
                writeReport(report);
                return;
            }
            report["pressed_capture"] = grab(guardedWindow).save(output + ".pressed.png");
            // Cancel outside the delegate: no application activation is requested.
            QTest::mouseMove(guardedWindow, QPoint(-100, -100));
            QTest::mouseRelease(guardedWindow, Qt::LeftButton, Qt::NoModifier, QPoint(-100, -100));
            QCoreApplication::processEvents();
            report["cancel_clears_feedback"] = !guardedTask->property("classicPressed").toBool();
            writeReport(report);
        });
        return;
    }
    report["candidate_windows"] = candidates;
    report["failure"] = "No visible native applet QQuickWindow found";
    writeReport(report);
}

extern "C" int interceptedExec() asm("_ZN12QApplication4execEv");
extern "C" int interceptedExec()
{
    const auto original = reinterpret_cast<int (*)()>(dlsym(RTLD_NEXT, "_ZN12QApplication4execEv"));
    if (!original) {
        return 1;
    }
    QTimer::singleShot(4000, capture);
    return original();
}
