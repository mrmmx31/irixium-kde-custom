// SPDX-FileCopyrightText: 2026 mrmmx31
// SPDX-License-Identifier: GPL-2.0-or-later
// Test-only interposer for plasmawindowed. Never installed or used by a panel.
// QtQuick headers are deliberately unnecessary here: these three exported
// public Qt 6 methods use the same QObject/QWindow/QPointF/QImage ABI. Every
// symbol is checked before use; runtime and header versions are recorded.

#include <QApplication>
#include <QCoreApplication>
#include <QFile>
#include <QImage>
#include <QJsonArray>
#include <QJsonDocument>
#include <QJsonObject>
#include <QPointer>
#include <QTest>
#include <QTimer>
#include <QWindow>
#include <dlfcn.h>

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
    for (QWindow *window : QGuiApplication::allWindows()) {
        if (!window->isVisible() || !window->inherits("QQuickWindow")) {
            continue;
        }
        QObject *root = window->property("contentItem").value<QObject *>();
        const QString output = qEnvironmentVariable("IRIX_TEST_CAPTURE");
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
    report["failure"] = "No visible native QQuickWindow found";
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
