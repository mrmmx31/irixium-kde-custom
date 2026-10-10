// SPDX-FileCopyrightText: 2026 mrmmx31
// SPDX-License-Identifier: GPL-2.0-or-later
// Optional native test adapter, compiled only into the temporary test output.
#include <QAbstractButton>
#include <QApplication>
#include <QFile>
#include <QFont>
#include <QImage>
#include <QJsonArray>
#include <QJsonDocument>
#include <QJsonObject>
#include <QSaveFile>
#include <QTimer>
#include <QTreeView>
#include <QTest>
#include <QWindow>
#include <dlfcn.h>

using Children = QList<QObject *> (*)(QObject *);
using Grab = QImage (*)(QWindow *);
static Children children;
static Grab grab;
static QObject *fixture = nullptr;
static QWindow *host = nullptr;
static QJsonArray nativeDialogs;
static QString completedPhase;

static QObject *findFixture(QObject *object)
{
    if (!object) return nullptr;
    if (object->objectName() == "classicLauncherConfigurationFixture") return object;
    if (object->inherits("QQuickItem")) {
        for (QObject *child : children(object)) {
            if (auto *found = findFixture(child)) return found;
        }
    }
    return nullptr;
}

static QModelIndex findApplication(QAbstractItemModel *model, const QModelIndex &parent, const QString &name)
{
    for (int row = 0; row < model->rowCount(parent); ++row) {
        const auto index = model->index(row, 0, parent);
        if (model->data(index).toString() == name) return index;
        const auto found = findApplication(model, index, name);
        if (found.isValid()) return found;
    }
    return {};
}

static void finish(const QString &failure = {})
{
    auto report = fixture ? QJsonDocument::fromJson(fixture->property("testReportJson").toString().toUtf8()).object()
                          : QJsonObject();
    report["native_dialogs"] = nativeDialogs;
    report["qt"] = qVersion();
    report["host"] = "plasmawindowed: real ConfigLaunchers.qml and native Quicklaunch Logic";
    report["full_plasma_configuration_dialog"] = false;
    if (!failure.isEmpty()) report["failure"] = failure;
    if (host && grab) {
        report["host_dimensions"] = QJsonArray{host->width(), host->height()};
        report["captured"] = grab(host).save(qEnvironmentVariable("IRIX_CONFIG_CAPTURE"));
    }
    QSaveFile output(qEnvironmentVariable("IRIX_CONFIG_REPORT"));
    if (output.open(QIODevice::WriteOnly)) {
        output.write(QJsonDocument(report).toJson());
        output.commit();
    }
    QCoreApplication::exit(failure.isEmpty() && report["failed"].toInt() == 0 ? 0 : 2);
}

static void observe()
{
    if (!fixture) {
        for (auto *window : QGuiApplication::allWindows()) {
            if (!window->isVisible() || !window->inherits("QQuickWindow")) continue;
            if (auto *found = findFixture(window->property("contentItem").value<QObject *>())) {
                fixture = found;
                host = window;
                host->setMinimumSize(QSize(520, 520));
                host->resize(520, 520);
                break;
            }
        }
    }
    if (!fixture) return;
    const auto phase = fixture->property("phase").toString();
    if (phase == "done") { finish(); return; }
    if (phase == "failed") { finish("Native QML fixture failed"); return; }
    if (phase == completedPhase || !phase.startsWith("selector_")) return;

    QWidget *dialog = nullptr;
    for (auto *widget : QApplication::topLevelWidgets()) {
        if (widget->isVisible() && widget->inherits("KOpenWithDialog")) {
            dialog = widget;
            break;
        }
    }
    if (!dialog) return;
    QJsonObject record{{"phase", phase}, {"class", QString::fromLatin1(dialog->metaObject()->className())}};
    if (phase == "selector_cancel") {
        record["rejected"] = QMetaObject::invokeMethod(dialog, "reject", Qt::DirectConnection);
        nativeDialogs.append(record);
        completedPhase = phase;
        if (!QMetaObject::invokeMethod(fixture, "afterSelectorCancel", Qt::DirectConnection)) {
            finish("QML cancel callback is unavailable");
        }
        return;
    }

    const QString name = phase == "selector_add" ? "IRIX Fixture Extra" : "IRIX Fixture Files";
    QTreeView *tree = nullptr;
    QModelIndex entry;
    for (auto *candidate : dialog->findChildren<QTreeView *>()) {
        entry = findApplication(candidate->model(), {}, name);
        if (entry.isValid()) { tree = candidate; break; }
    }
    if (!tree) { finish("Native application selector cannot locate " + name); return; }
    for (auto parent = entry.parent(); parent.isValid(); parent = parent.parent()) tree->expand(parent);
    tree->scrollTo(entry);
    tree->setCurrentIndex(entry);
    QApplication::processEvents();
    const auto rect = tree->visualRect(entry);
    if (rect.isEmpty()) { finish("Native selector application row has no click target"); return; }
    QTest::mouseClick(tree->viewport(), Qt::LeftButton, Qt::NoModifier, rect.center());
    QAbstractButton *accept = nullptr;
    for (auto *button : dialog->findChildren<QAbstractButton *>()) {
        if (button->text().remove('&') == "OK") { accept = button; break; }
    }
    if (!accept || !accept->isEnabled()) { finish("Native selector OK button is unavailable"); return; }
    record["application"] = name;
    record["tree"] = QString::fromLatin1(tree->metaObject()->className());
    record["row_clicked"] = true;
    accept->click();
    record["accepted"] = !dialog->isVisible();
    nativeDialogs.append(record);
    completedPhase = phase;
    const char *callback = phase == "selector_add" ? "afterSelectorAdd"
                         : phase == "selector_replace" ? "afterSelectorReplace" : "afterSelectorRace";
    if (!QMetaObject::invokeMethod(fixture, callback, Qt::DirectConnection)) {
        finish("QML selection callback is unavailable");
    }
}

extern "C" int interceptedExec() asm("_ZN12QApplication4execEv");
extern "C" int interceptedExec()
{
    auto original = reinterpret_cast<int (*)()>(dlsym(RTLD_NEXT, "_ZN12QApplication4execEv"));
    children = reinterpret_cast<Children>(dlsym(RTLD_DEFAULT, "_ZNK10QQuickItem10childItemsEv"));
    grab = reinterpret_cast<Grab>(dlsym(RTLD_DEFAULT, "_ZN12QQuickWindow10grabWindowEv"));
    if (!original || !children || !grab) return 3;
    QApplication::setFont(QFont("Nimbus Sans", 12));
    auto *timer = new QTimer(QCoreApplication::instance());
    QObject::connect(timer, &QTimer::timeout, observe);
    timer->start(40);
    QTimer::singleShot(25000, [] { finish("Native configuration fixture timed out"); });
    return original();
}
