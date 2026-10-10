// SPDX-FileCopyrightText: 2026 mrmmx31
// SPDX-License-Identifier: GPL-3.0-or-later
// Bounded private plasmawindowed instrument test; never loaded by a user session.
#include <QApplication>
#include <QFile>
#include <QJsonArray>
#include <QJsonDocument>
#include <QJsonObject>
#include <QImage>
#include <QTimer>
#include <QWindow>
#include <dlfcn.h>

using Children = QList<QObject *> (*)(QObject *);
using Grab = QImage (*)(QWindow *);
static QObject *fixture = nullptr;
static QJsonObject report;
static int stage = 0, retries = 0;
static void step();

static QObject *find(QObject *item, const QString &name, Children children)
{
    if (!item) return nullptr;
    if (item->objectName() == name) return item;
    if (item->inherits("QQuickItem")) {
        for (QObject *child : children(item)) {
            if (QObject *match = find(child,name,children)) return match;
        }
    }
    return nullptr;
}
static void finish(const QString &failure = {})
{
    if (!failure.isEmpty()) report["failure"] = failure;
    QFile output(qEnvironmentVariable("IRIX_DOMAINOS_INSTRUMENT_REPORT"));
    if (output.open(QIODevice::WriteOnly)) output.write(QJsonDocument(report).toJson());
    QCoreApplication::quit();
}
static QJsonObject state()
{
    QJsonObject result;
    for (const char *key : {"timeJson","metricsJson","popupJson","graphJson","configJson"}) {
        const auto bytes = fixture->property(key).toString().toUtf8();
        result[key] = QJsonDocument::fromJson(bytes).object();
    }
    result["mailRequests"] = fixture->property("mailRequests").toInt();
    return result;
}
static void unitStep(const QJsonObject &current, Grab grab)
{
    const auto metrics = current["metricsJson"].toObject();
    const auto primary = metrics["primary"].toObject();
    const auto secondary = metrics["secondary"].toObject();
    const bool histories = !metrics["primaryHistory"].toArray().isEmpty()
        && (stage == 5 || !metrics["secondaryHistory"].toArray().isEmpty());
    const bool ready = stage == 1
        ? primary["available"].toBool() && secondary["available"].toBool()
            && primary["unit"] != secondary["unit"]
        : metrics["available"].toBool() && histories;
    if ((stage == 0 || stage == 1 || stage == 3 || stage == 5)
        && !ready && retries++ < 6) {
        QTimer::singleShot(1000,step); return;
    }
    static const QStringList names{"compatible_network","incompatible_units","stale_history_defense",
        "compatible_recovery","missing_secondary","single_sensor","slow_telemetry_clock","disabled"};
    report[names[stage]] = current;
    for (QWindow *window : QGuiApplication::allWindows()) {
        if (window->isVisible() && window->inherits("QQuickWindow")) {
            grab(window).save(qEnvironmentVariable("IRIX_DOMAINOS_INSTRUMENT_DIR")+"/"+names[stage]+".png");
            break;
        }
    }
    retries = 0;
    if (++stage == names.size()) { report["qt_version"] = qVersion(); finish(); return; }
    fixture->setProperty("scenario",stage);
    QTimer::singleShot(stage == 2 || stage == 7 ? 250 : 2500,step);
}
static void step()
{
    const auto children = reinterpret_cast<Children>(dlsym(RTLD_DEFAULT,"_ZNK10QQuickItem10childItemsEv"));
    const auto grab = reinterpret_cast<Grab>(dlsym(RTLD_DEFAULT,"_ZN12QQuickWindow10grabWindowEv"));
    if (!children || !grab) { finish("QtQuick native adapter unavailable"); return; }
    if (!fixture) {
        for (auto window : QGuiApplication::allWindows()) {
            fixture = find(window->property("contentItem").value<QObject *>(),"domainosInstrumentTestFixture",children);
            if (fixture) break;
        }
    }
    if (!fixture) { finish("Instrument fixture missing"); return; }
    auto current = state();
    if (qEnvironmentVariable("IRIX_DOMAINOS_INSTRUMENT_UNITS_TEST") == "1") {
        unitStep(current,grab); return;
    }
    if (stage == 0 && !current["metricsJson"].toObject()["available"].toBool() && retries++ < 7) {
        QTimer::singleShot(1000,step); return;
    }
    static const QStringList names{"network","clock","calendar","monitor","cpu","unavailable","mail","disabled","calendar_unavailable"};
    report[names[stage]] = current;
    for (QWindow *window : QGuiApplication::allWindows()) {
        if (window->isVisible() && window->inherits("QQuickWindow")) {
            auto content = window->property("contentItem").value<QObject *>();
            if (stage > 0 && stage < 4 && find(content,QStringList{"","domainosTimePopupContent","domainosCalendarPopupContent","domainosMonitorPopupContent"}[stage],children)) {
                grab(window).save(qEnvironmentVariable("IRIX_DOMAINOS_INSTRUMENT_DIR")+"/"+names[stage]+".png");
            }
        }
    }
    if (stage == 3) {
        QObject *monitor = nullptr;
        for (QWindow *window : QGuiApplication::allWindows()) {
            monitor = find(window->property("contentItem").value<QObject *>(),"domainosExistingGrosview",children);
            if (monitor) break;
        }
        report["existing_grosview_loaded"] = monitor != nullptr;
        if (monitor) {
            auto unavailable = monitor->property("unavailableSensors");
            report["grosview_unavailable_sensors"] = unavailable.toInt();
        }
    }
    if (++stage == names.size()) { report["qt_version"] = qVersion(); finish(); return; }
    fixture->setProperty("scenario",stage);
    QTimer::singleShot(stage == 3 || stage == 4 || stage == 5 ? 2500 : 250,step);
}
extern "C" int interceptedExec() asm("_ZN12QApplication4execEv");
extern "C" int interceptedExec()
{
    const auto original = reinterpret_cast<int (*)()>(dlsym(RTLD_NEXT,"_ZN12QApplication4execEv"));
    if (!original || qEnvironmentVariable("IRIX_DOMAINOS_INSTRUMENT_TEST") != "1") return original ? original() : 1;
    QTimer::singleShot(4000,step);
    QTimer::singleShot(25000,[](){ finish("Bounded instrument test timeout"); });
    return original();
}
