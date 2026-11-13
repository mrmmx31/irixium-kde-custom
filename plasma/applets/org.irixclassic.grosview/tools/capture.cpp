// SPDX-FileCopyrightText: 2026 mrmmx31
// SPDX-License-Identifier: GPL-3.0-or-later
// Test-only native plasmawindowed probe; never preloaded by a desktop session.
#include <QApplication>
#include <QCoreApplication>
#include <QFile>
#include <QImage>
#include <QJsonArray>
#include <QJsonDocument>
#include <QJsonObject>
#include <QTimer>
#include <QWindow>
#include <dlfcn.h>

using Children = QList<QObject *> (*)(QObject *);
using Grab = QImage (*)(QWindow *);

static void collect(QObject *item, const QString &name, Children children, QList<QObject *> &found)
{
    if (!item) return;
    if (item->objectName() == name) found.append(item);
    if (item->inherits("QQuickItem")) {
        for (QObject *child : children(item)) collect(child, name, children, found);
    }
}

static QJsonArray samples;

static void finish(const QJsonObject &result)
{
    QFile output(qEnvironmentVariable("IRIX_GROSVIEW_REPORT"));
    if (output.open(QIODevice::WriteOnly)) output.write(QJsonDocument(result).toJson());
    QCoreApplication::quit();
}

static void inspect()
{
    const auto children = reinterpret_cast<Children>(dlsym(RTLD_DEFAULT, "_ZNK10QQuickItem10childItemsEv"));
    const auto grab = reinterpret_cast<Grab>(dlsym(RTLD_DEFAULT, "_ZN12QQuickWindow10grabWindowEv"));
    if (!children || !grab) {
        finish({{"failure", "QtQuick ABI adapter unavailable"}}); return;
    }
    for (QWindow *window : QGuiApplication::allWindows()) {
        if (!window->isVisible() || !window->inherits("QQuickWindow")) continue;
        QObject *root = window->property("contentItem").value<QObject *>();
        QList<QObject *> instruments;
        collect(root, "grosviewInstrument", children, instruments);
        if (instruments.size() != 1) continue;
        window->setMinimumSize(QSize(280, 220));
        window->setMaximumSize(QSize(280, 220));
        window->resize(280, 220);
        QList<QObject *> rows;
        collect(root, "grosviewSensorRow", children, rows);
        QJsonArray current;
        for (QObject *row : rows) {
            QObject *sensor = row->property("sensor").value<QObject *>();
            QJsonObject entry;
            for (const char *name : {"sensorId", "available", "displayedValue", "fraction", "scaleMaximum", "percentage"}) {
                entry[name] = QJsonValue::fromVariant(row->property(name));
            }
            if (sensor) {
                for (const char *name : {"status", "value", "name", "unit", "updateInterval", "updateRateLimit", "minimum", "maximum"}) {
                    entry[name] = QJsonValue::fromVariant(sensor->property(name));
                }
                entry["sensor_class"] = QString::fromLatin1(sensor->metaObject()->className());
            }
            current.append(entry);
        }
        samples.append(current);
        if (samples.size() < 3) {
            QTimer::singleShot(1000, inspect); return;
        }
        // Let resize/render settle only inside the bounded test process.
        QTimer::singleShot(100, [window, grab]() {
            const QImage image = grab(window);
            finish({{"native_host", true}, {"samples", samples},
                {"captured", !image.isNull() && image.save(qEnvironmentVariable("IRIX_GROSVIEW_CAPTURE"))},
                {"capture_dimensions", QJsonArray{image.width(), image.height()}},
                {"window_title", window->title()}, {"qt_version", qVersion()}});
        });
        return;
    }
    finish({{"failure", "Native gr_osview full representation not found"}});
}

extern "C" int interceptedExec() asm("_ZN12QApplication4execEv");
extern "C" int interceptedExec()
{
    const auto original = reinterpret_cast<int (*)()>(dlsym(RTLD_NEXT, "_ZN12QApplication4execEv"));
    if (!original || qEnvironmentVariable("IRIX_GROSVIEW_TEST") != "1") return original ? original() : 1;
    QTimer::singleShot(4000, inspect);
    QTimer::singleShot(15000, []() { finish({{"failure", "Bounded native test timeout"}}); });
    return original();
}
