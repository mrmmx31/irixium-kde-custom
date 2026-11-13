// SPDX-License-Identifier: GPL-3.0-or-later
// Observe only the production DomainOS loaded in a private native Plasma panel.
// No geometry changes, synthetic applet, or personal-session window inspection.
#include <QApplication>
#include <QImage>
#include <QJsonArray>
#include <QJsonDocument>
#include <QJsonObject>
#include <QPointer>
#include <QMetaProperty>
#include <QSaveFile>
#include <QTimer>
#include <QWindow>
#include <dlfcn.h>

using Children = QList<QObject *> (*)(QObject *);
using Map = QPointF (*)(QObject *, const QPointF &);
using Grab = QImage (*)(QWindow *);

static void walk(QObject *object, Children children, QList<QObject *> &seen)
{
    if (!object || seen.contains(object)) return;
    seen.append(object);
    for (QObject *owned : object->children()) walk(owned, children, seen);
    if (object->inherits("QQuickItem"))
        for (QObject *visual : children(object)) walk(visual, children, seen);
}

static void observe()
{
    if (qEnvironmentVariable("IRIX_DOMAINOS_ACTIVATION_PRIVATE") != "1") return;
    auto children = reinterpret_cast<Children>(dlsym(RTLD_DEFAULT, "_ZNK10QQuickItem10childItemsEv"));
    auto map = reinterpret_cast<Map>(dlsym(RTLD_DEFAULT, "_ZNK10QQuickItem10mapToSceneERK7QPointF"));
    auto grab = reinterpret_cast<Grab>(dlsym(RTLD_DEFAULT, "_ZN12QQuickWindow10grabWindowEv"));
    QJsonArray panels, nativeRoots;
    if (children && map && grab) {
        for (QWindow *window : QGuiApplication::allWindows()) {
            if (!window->isVisible() || !window->inherits("QQuickWindow")) continue;
            QList<QObject *> objects;
            walk(window->property("contentItem").value<QObject *>(), children, objects);
            for (QObject *object : objects) {
                if (!object->property("floatingness").isValid()
                    || !object->property("fixedLeftFloatingPadding").isValid()) continue;
                QJsonArray frames;
                int visibleBackgrounds = 0;
                for (QObject *child : children(object)) {
                    if (!child->property("imagePath").isValid()) continue;
                    const QString path = child->property("imagePath").toString();
                    const bool visible = child->property("visible").toBool();
                    if (visible && path.endsWith("widgets/panel-background")) ++visibleBackgrounds;
                    frames.append(QJsonObject{{"imagePath", path}, {"visible", visible},
                        {"x", child->property("x").toDouble()}, {"y", child->property("y").toDouble()},
                        {"width", child->property("width").toDouble()}, {"height", child->property("height").toDouble()}});
                }
                QObject *containment = object->property("containment").value<QObject *>();
                QObject *plasmoid = containment ? containment->property("plasmoid").value<QObject *>() : nullptr;
                QJsonArray exposed;
                if (plasmoid) for (int index = 0; index < plasmoid->metaObject()->propertyCount(); ++index) {
                    const QMetaProperty property = plasmoid->metaObject()->property(index);
                    const QString name = QString::fromUtf8(property.name());
                    if (name.contains("background", Qt::CaseInsensitive) || name == "applets" || name == "pluginName" || name == "id")
                        exposed.append(QJsonObject{{"name", name}, {"writable", property.isWritable()},
                            {"value", QJsonValue::fromVariant(plasmoid->property(property.name()))}});
                }
                const QRect mask = window->mask().boundingRect();
                nativeRoots.append(QJsonObject{{"windowId", double(window->winId())},
                    {"backgroundHints", plasmoid ? plasmoid->property("backgroundHints").toInt() : -1},
                    {"floatingness", object->property("floatingness").toDouble()},
                    {"floating", object->property("floating").toBool()},
                    {"leftFloatingPadding", object->property("leftFloatingPadding").toInt()},
                    {"bottomFloatingPadding", object->property("bottomFloatingPadding").toInt()},
                    {"windowX", window->x()}, {"windowY", window->y()},
                    {"windowWidth", window->width()}, {"windowHeight", window->height()},
                    {"visibleBackgroundCount", visibleBackgrounds}, {"frames", frames}, {"exposed", exposed},
                    {"maskEmpty", window->mask().isEmpty()},
                    {"maskBounds", QJsonObject{{"x", mask.x()}, {"y", mask.y()}, {"width", mask.width()}, {"height", mask.height()}}}});
            }
            for (QObject *object : objects) {
                if (object->objectName() != "domainosPanel") continue;
                const QPointF origin = map(object, {});
                panels.append(QJsonObject{{"width", object->property("width").toDouble()},
                    {"height", object->property("height").toDouble()},
                    {"scale", object->property("drawingScale").toDouble()},
                    {"x", origin.x()}, {"y", origin.y()},
                    {"windowWidth", window->width()}, {"windowHeight", window->height()},
                    {"windowX", window->x()}, {"windowY", window->y()},
                    {"visible", object->property("visible").toBool()}});
                // Overwrite this private capture while the panel is visible;
                // the Python worker parks it at each assertion's checkpoint.
                const QImage image = grab(window);
                if (!image.isNull()) image.save(qEnvironmentVariable("IRIX_DOMAINOS_ACTIVATION_CAPTURE"));
            }
        }
    }
    QSaveFile file(qEnvironmentVariable("IRIX_DOMAINOS_ACTIVATION_UI"));
    if (file.open(QIODevice::WriteOnly)) {
        file.write(QJsonDocument(QJsonObject{{"publicQtSymbols", bool(children && map && grab)},
            {"panels", panels}, {"nativeRoots", nativeRoots}}).toJson());
        file.commit();
    }
    QTimer::singleShot(300, observe);
}

extern "C" int interceptedExec() asm("_ZN12QApplication4execEv");
extern "C" int interceptedExec()
{
    auto original = reinterpret_cast<int (*)()>(dlsym(RTLD_NEXT, "_ZN12QApplication4execEv"));
    if (!original) return 3;
    if (qEnvironmentVariable("IRIX_DOMAINOS_ACTIVATION_PRIVATE") == "1")
        QTimer::singleShot(500, observe);
    return original();
}
