// SPDX-FileCopyrightText: 2026 IRIX Classic contributors
// SPDX-License-Identifier: GPL-3.0-or-later
// Test-only observer loaded into plasmawindowed on a private Xvfb and bus.
// The actual production KPackage/QML is loaded by plasmawindowed unchanged.
// QtQuick development headers are absent on some test machines: the three
// checked public Qt 6 symbols use QObject/QWindow/QList-pointer-list ABI.
#include <QApplication>
#include <QCoreApplication>
#include <QElapsedTimer>
#include <QFontDatabase>
#include <QFontInfo>
#include <QImage>
#include <QPalette>
#include <QJsonArray>
#include <QJsonDocument>
#include <QJsonObject>
#include <QPointer>
#include <QSaveFile>
#include <QTimer>
#include <QUrl>
#include <QWindow>
#include <dlfcn.h>

using Children = QList<QObject *> (*)(QObject *);
using MapToScene = QPointF (*)(QObject *, const QPointF &);
using GrabWindow = QImage (*)(QWindow *);
static QElapsedTimer elapsed;
static QPointer<QWindow> host;
static QPointer<QObject> panel;
static int ticks = 0;

static void walk(QObject *root, Children children, QList<QObject *> &objects)
{
    if (!root || objects.contains(root)) return;
    objects.append(root);
    for (QObject *owned : root->children()) walk(owned, children, objects);
    if (root->inherits("QQuickItem")) {
        for (QObject *visual : children(root)) walk(visual, children, objects);
    }
}

static void finish(QJsonObject report, bool failed)
{
    report["qt_runtime"] = qVersion();
    report["qt_headers"] = QT_VERSION_STR;
    report["test_helper_only"] = true;
    QSaveFile output(qEnvironmentVariable("IRIX_DOMAINOS_REPORT"));
    if (!output.open(QIODevice::WriteOnly)) {
        qCritical("DOMAINOS_NATIVE_REPORT_OPEN_FAILED");
        QCoreApplication::exit(3); return;
    }
    output.write(QJsonDocument(report).toJson());
    if (!output.commit()) {
        qCritical("DOMAINOS_NATIVE_REPORT_COMMIT_FAILED");
        QCoreApplication::exit(3); return;
    }
    QCoreApplication::exit(failed ? 2 : 0);
}

static void observe()
{
    auto children = reinterpret_cast<Children>(dlsym(RTLD_DEFAULT, "_ZNK10QQuickItem10childItemsEv"));
    auto map = reinterpret_cast<MapToScene>(dlsym(RTLD_DEFAULT, "_ZNK10QQuickItem10mapToSceneERK7QPointF"));
    auto grab = reinterpret_cast<GrabWindow>(dlsym(RTLD_DEFAULT, "_ZN12QQuickWindow10grabWindowEv"));
    if (!children || !map || !grab || !QString::fromLatin1(qVersion()).startsWith("6.")) {
        finish({{"failure", "The required public Qt 6 Quick symbols are unavailable"}}, true); return;
    }
    if (!panel) {
        for (QWindow *window : QGuiApplication::allWindows()) {
            if (!window->isVisible() || !window->inherits("QQuickWindow")) continue;
            QList<QObject *> objects;
            walk(window->property("contentItem").value<QObject *>(), children, objects);
            for (QObject *object : objects) {
                if (object->objectName() == "domainosPanel") {
                    host = window; panel = object;
                    host->setMinimumSize({1942, 218});
                    host->resize({1942, 218});
                    ticks = 0; break;
                }
            }
            if (panel) break;
        }
    }
    if (!panel) {
        if (elapsed.elapsed() > 15000) {
            finish({{"failure", "The real production DomainOSPanel did not load in plasmawindowed"}}, true); return;
        }
        QTimer::singleShot(100, observe); return;
    }
    // Allow this fixture's resize/image decoder work to settle. There is no
    // product timer, synthetic role model, app launch, pointer or device action.
    if (++ticks < 10) { QTimer::singleShot(100, observe); return; }
    QList<QObject *> objects;
    walk(host->property("contentItem").value<QObject *>(), children, objects);
    walk(panel, children, objects);
    QJsonArray names, images, labels, renderedFonts;
    bool allImagesReady = true;
    int bitmaps = 0;
    for (QObject *object : objects) {
        if (!object->objectName().isEmpty()) names.append(object->objectName());
        if (object->inherits("QQuickImage")) {
            const QUrl renderedSource = object->property("source").toUrl();
            const QUrl source = object->property("assetSource").isValid()
                ? object->property("assetSource").toUrl() : renderedSource;
            if (source.isEmpty()) continue;
            const int status = object->property("status").toInt();
            const bool production = source.toString().contains("org.irixclassic.domainos.panel/contents/images/");
            if (!production) continue;
            allImagesReady = allImagesReady && status == 1; // QQuickImage::Ready
            if (source.toString().contains("/iconbox/")) ++bitmaps;
            images.append(QJsonObject{{"source", source.toString()}, {"status", status},
                                      {"recolored", renderedSource.scheme() == "data"},
                                      {"smooth", object->property("smooth").toBool()},
                                      {"width", object->property("width").toDouble()},
                                      {"height", object->property("height").toDouble()}});
        }
        if (object->inherits("QQuickText")) {
            const auto text = object->property("text").toString();
            if (!text.isEmpty()) {
                labels.append(text);
                const QFont font = object->property("font").value<QFont>();
                renderedFonts.append(QJsonObject{{"text", text}, {"requested", font.family()},
                    {"resolved", QFontInfo(font).family()}, {"pixel_size", QFontInfo(font).pixelSize()}});
            }
        }
    }
    const QPointF origin = map(panel, {});
    const double scale = panel->property("drawingScale").toDouble();
    const QImage full = grab(host);
    const bool saved = !full.isNull() && full.save(qEnvironmentVariable("IRIX_DOMAINOS_CAPTURE"));
    const auto available = [](const QString &family) {
        for (const QString &name : QFontDatabase::families()) {
            // Qt appends foundry labels when duplicate font families exist.
            if (name == family || name.startsWith(family + " [")) return true;
        }
        return false;
    };
    QObject *colors = panel->property("colorPalette").value<QObject *>();
    const QPalette palette = QApplication::palette();
    QJsonObject colorRoles;
    for (const char *role : {"background", "recessed", "blue", "white", "text", "dark", "pale", "metalLight", "metalDark"})
        if (colors) colorRoles[role] = colors->property(role).value<QColor>().name();
    QJsonObject report{{"public_quick_symbols", true}, {"production_panel_loaded", true},
        {"follow_system_colors", panel->property("followSystemColors").toBool()},
        {"panel_color_roles", colorRoles},
        {"application_palette", QJsonObject{{"window", palette.color(QPalette::Window).name()},
            {"base", palette.color(QPalette::Base).name()},
            {"highlight", palette.color(QPalette::Highlight).name()},
            {"highlightedText", palette.color(QPalette::HighlightedText).name()},
            {"windowText", palette.color(QPalette::WindowText).name()}}},
        {"production_panel_visible", panel->property("visible").toBool()},
        {"panel_class", QString::fromLatin1(panel->metaObject()->className())},
        {"phase", panel->property("phase").toString()},
        {"panel_geometry", QJsonArray{origin.x(), origin.y(), panel->property("width").toDouble(), panel->property("height").toDouble()}},
        {"drawing_scale", scale}, {"window_size", QJsonArray{host->width(), host->height()}},
        {"captured", saved}, {"object_names", names}, {"images", images}, {"text", labels},
        {"rendered_fonts", renderedFonts},
        {"all_production_images_ready", allImagesReady}, {"sgi_iconbox_image_items", bitmaps},
        {"task_count", panel->property("taskCount").toInt()},
        {"workspace_count", panel->property("workspaceCount").toInt()},
        {"tray_rows", panel->property("trayRows").toInt()},
        {"tray_columns", panel->property("trayColumns").toInt()},
        {"fonts_available", QJsonObject{{"Nimbus Sans", available("Nimbus Sans")},
                                        {"DejaVu Sans Mono", available("DejaVu Sans Mono")}}},
        {"actions_exercised", false}, {"desktop_modified", false}};
    const bool failed = !saved || !panel->property("visible").toBool() || !allImagesReady || bitmaps != 7 || images.isEmpty() || scale < .95;
    if (failed) report["failure"] = "The production panel failed capture, image-readiness or preferred-size validation";
    finish(report, failed);
}

extern "C" int interceptedExec() asm("_ZN12QApplication4execEv");
extern "C" int interceptedExec()
{
    auto original = reinterpret_cast<int (*)()>(dlsym(RTLD_NEXT, "_ZN12QApplication4execEv"));
    if (!original) return 3;
    elapsed.start();
    QTimer::singleShot(500, observe);
    return original();
}
