// SPDX-FileCopyrightText: 2026 mrmmx31
// SPDX-License-Identifier: GPL-3.0-or-later
// Exercise real Plasma KConfigPropertyMap and native applet instances privately.
#include <QApplication>
#include <QAbstractItemModel>
#include <QAction>
#include <QFile>
#include <QImage>
#include <QJsonArray>
#include <QJsonDocument>
#include <QJsonObject>
#include <QLabel>
#include <QMessageBox>
#include <QRectF>
#include <QPointer>
#include <QProcess>
#include <QScreen>
#include <QSignalSpy>
#include <QTimer>
#include <QTest>
#include <QUrl>
#include <QWindow>
#include <QWidget>
#include <dlfcn.h>

using Children = QList<QObject *> (*)(QObject *);
using Grab = QImage (*)(QWindow *);
static QObject *fixture = nullptr;
static QObject *secondItem = nullptr;
static QPointer<QWindow> configWindow;
static QObject *configRoot = nullptr;
static QObject *productionSettings = nullptr;
static QObject *productionBridge = nullptr;
static QObject *productionHost = nullptr;
static QObject *secondProductionSettings = nullptr;
static QJsonObject report;
static int stage = 0;
static QSignalSpy *productionActionSpy = nullptr;
static QPointer<QWindow> productionWindow;
static QPointer<QObject> productionPanel;

static QJsonObject configurationSnapshot(QObject *configuration)
{
    QJsonObject result;
    const auto keys = reinterpret_cast<QStringList (*)(QObject *)>(dlsym(RTLD_DEFAULT, "_ZNK15QQmlPropertyMap4keysEv"));
    if (!configuration || !keys) return result;
    for (const auto &key : keys(configuration)) result[key] = QJsonValue::fromVariant(configuration->property(key.toUtf8().constData()));
    return result;
}

static void captureVisibleContext(const QString &label)
{
    QJsonArray windows, widgets;
    for (auto window : QGuiApplication::allWindows()) if (window->isVisible()) {
        const auto geometry = window->geometry();
        windows.append(QJsonObject{{"class", window->metaObject()->className()}, {"title", window->title()},
            {"winId", QString::number(window->winId())}, {"x", geometry.x()}, {"y", geometry.y()},
            {"width", geometry.width()}, {"height", geometry.height()}, {"active", window->isActive()}});
    }
    for (auto widget : QApplication::topLevelWidgets()) if (widget->isVisible()) {
        QJsonArray text;
        for (auto child : widget->findChildren<QLabel *>()) text.append(child->text().left(4000));
        widgets.append(QJsonObject{{"class", widget->metaObject()->className()}, {"title", widget->windowTitle()},
            {"modal", widget->isModal()}, {"enabled", widget->isEnabled()}, {"labels", text}});
    }
    QJsonObject snapshot{{"stage", label}, {"windows", windows}, {"widgets", widgets}};
    if (auto focus = QGuiApplication::focusWindow()) snapshot["focusWindowClass"] = focus->metaObject()->className();
    if (auto screen = QGuiApplication::primaryScreen()) snapshot["screenCaptureSaved"] = screen->grabWindow(0).save(qEnvironmentVariable("IRIX_DOMAINOS_PREFERENCES_DIR")+"/SCREEN-"+label+".png");
    if (productionActionSpy && productionActionSpy->isValid()) {
        QJsonArray actions;
        for (const auto &arguments : *productionActionSpy) if (!arguments.isEmpty()) actions.append(arguments.first().toString());
        snapshot["panelActions"] = actions;
    }
    auto snapshots = report["ui_diagnostics"].toArray();
    snapshots.append(snapshot);
    report["ui_diagnostics"] = snapshots;
}

static QObject *find(QObject *item, const QString &name, Children children)
{
    if (!item) return nullptr;
    if (item->objectName() == name) return item;
    if (item->inherits("QQuickItem")) for (auto child : children(item)) if (auto match = find(child, name, children)) return match;
    return nullptr;
}
static void finish(const QString &failure = {})
{
    if (!failure.isEmpty()) report["failure"] = failure;
    QFile file(qEnvironmentVariable("IRIX_DOMAINOS_PREFERENCES_REPORT"));
    if (file.open(QIODevice::WriteOnly)) file.write(QJsonDocument(report).toJson());
    QCoreApplication::quit();
}
static bool click(const QString &name)
{
    const auto children = reinterpret_cast<Children>(dlsym(RTLD_DEFAULT, "_ZNK10QQuickItem10childItemsEv"));
    const auto map = reinterpret_cast<QPointF (*)(QObject *, const QPointF &)>(dlsym(RTLD_DEFAULT, "_ZNK10QQuickItem10mapToSceneERK7QPointF"));
    if (!children || !map) return false;
    for (auto window : QGuiApplication::allWindows()) {
        if (!window->isVisible()) continue;
        auto item = find(window->property("contentItem").value<QObject *>(), name, children);
        if (!item) continue;
        auto point = map(item, QPointF(item->property("width").toDouble()/2, item->property("height").toDouble()/2));
        // QTest delivers QWindow events directly, bypassing the X11 window
        // manager's normal activation on a physical pointer click.
        window->requestActivate();
        QTest::qWait(100);
        QTest::mouseMove(window, point.toPoint());
        QTest::mouseClick(window, Qt::LeftButton, Qt::NoModifier, point.toPoint());
        return true;
    }
    return false;
}
static bool clickPhysical(const QString &name)
{
    const auto children = reinterpret_cast<Children>(dlsym(RTLD_DEFAULT, "_ZNK10QQuickItem10childItemsEv"));
    const auto map = reinterpret_cast<QPointF (*)(QObject *, const QPointF &)>(dlsym(RTLD_DEFAULT, "_ZNK10QQuickItem10mapToSceneERK7QPointF"));
    if (!children || !map) return false;
    for (auto window : QGuiApplication::allWindows()) {
        if (!window->isVisible()) continue;
        auto item = find(window->property("contentItem").value<QObject *>(), name, children);
        if (!item) continue;
        const auto scene = map(item, QPointF(item->property("width").toDouble()/2, item->property("height").toDouble()/2));
        auto point = window->mapToGlobal(scene.toPoint());
        // A render-control host may embed an offscreen QQuickWindow in a
        // QQuickWidget. In that case only the QWidget has a screen position.
        const auto quickWindow = reinterpret_cast<QWindow *(*)(QWidget *)>(dlsym(RTLD_DEFAULT, "_ZNK12QQuickWidget11quickWindowEv"));
        QString ownerClass;
        if (quickWindow) for (auto widget : QApplication::allWidgets()) {
            if (widget->inherits("QQuickWidget") && quickWindow(widget) == window) {
                point = widget->mapToGlobal(scene.toPoint());
                ownerClass = widget->metaObject()->className();
                break;
            }
        }
        report["physical_target_" + name] = QJsonObject{{"windowClass", window->metaObject()->className()},
            {"widgetClass", ownerClass}, {"globalX", point.x()}, {"globalY", point.y()}};
        return QProcess::execute("xdotool", {"mousemove", "--sync", QString::number(point.x()), QString::number(point.y()), "click", "1"}) == 0;
    }
    return false;
}
static bool physicalButton(QObject *button, QWindow *window, const QString &name)
{
    const auto map = reinterpret_cast<QPointF (*)(QObject *, const QPointF &)>(dlsym(RTLD_DEFAULT, "_ZNK10QQuickItem10mapToSceneERK7QPointF"));
    if (!button || !window || !map || !button->property("visible").toBool() || !button->property("enabled").toBool()) return false;
    const auto scene = map(button, QPointF(button->property("width").toDouble()/2, button->property("height").toDouble()/2));
    if (!QRectF(QPointF(), window->size()).contains(scene)) return false;
    const auto point = window->mapToGlobal(scene.toPoint());
    report["physical_target_" + name] = QJsonObject{{"windowClass", window->metaObject()->className()},
        {"globalX", point.x()}, {"globalY", point.y()}, {"text", button->property("text").toString()}};
    return QProcess::execute("xdotool", {"mousemove", "--sync", QString::number(point.x()), QString::number(point.y()), "click", "1"}) == 0;
}
static QObject *findProperty(QObject *item, const char *property, Children children)
{
    if (!item) return nullptr;
    if (item->property(property).isValid()) return item;
    if (item->inherits("QQuickItem")) for (auto child : children(item)) if (auto match = findProperty(child, property, children)) return match;
    return nullptr;
}
static bool descendantText(QObject *item, Children children, const QString &wanted)
{
    if (!item) return false;
    if (item->property("text").toString().remove('&') == wanted) return true;
    if (item->inherits("QQuickItem")) for (auto child : children(item)) if (descendantText(child, children, wanted)) return true;
    return false;
}
static QObject *findButton(QObject *item, Children children, const QString &wanted = QStringLiteral("Apply"))
{
    if (!item) return nullptr;
    QString text = item->property("text").toString().remove('&');
    if (item->inherits("QQuickAbstractButton") && item->property("enabled").toBool()
        && item->property("visible").toBool()
        && (text == wanted || (wanted == "Apply" && text == "Aplicar")
            || (wanted == "Cancel" && text == "Cancelar") || (wanted == "Discard" && text == "Descartar")
            // Plasma ConfigCategoryDelegate leaves ItemDelegate.text empty;
            // its actual category title lives in the nested QQC2.Label.
            || (item->inherits("QQuickItemDelegate") && descendantText(item, children, wanted)))) return item;
    if (item->inherits("QQuickItem")) for (auto child : children(item)) if (auto match = findButton(child, children, wanted)) return match;
    return nullptr;
}
static void recordButtons(QObject *item, Children children, QJsonArray &buttons)
{
    if (!item) return;
    const auto text = item->property("text").toString();
    if (item->inherits("QQuickAbstractButton") || text.contains("Apply")) buttons.append(QJsonObject{{"class", item->metaObject()->className()}, {"text", text}, {"enabled", item->property("enabled").toBool()}});
    if (item->inherits("QQuickItem")) for (auto child : children(item)) recordButtons(child, children, buttons);
}
static bool clickNativeApply()
{
    const auto children = reinterpret_cast<Children>(dlsym(RTLD_DEFAULT, "_ZNK10QQuickItem10childItemsEv"));
    const auto map = reinterpret_cast<QPointF (*)(QObject *, const QPointF &)>(dlsym(RTLD_DEFAULT, "_ZNK10QQuickItem10mapToSceneERK7QPointF"));
    auto button = configRoot && children ? findButton(configRoot, children) : nullptr;
    if (!button || !map || !configWindow) return false;
    const auto point = map(button, QPointF(button->property("width").toDouble()/2, button->property("height").toDouble()/2));
    configWindow->requestActivate();
    QTest::qWait(100);
    QTest::mouseMove(configWindow, point.toPoint());
    QTest::mouseClick(configWindow, Qt::LeftButton, Qt::NoModifier, point.toPoint());
    return true;
}
static bool clickNativeCommand(const QString &text)
{
    const auto children = reinterpret_cast<Children>(dlsym(RTLD_DEFAULT, "_ZNK10QQuickItem10childItemsEv"));
    const auto map = reinterpret_cast<QPointF (*)(QObject *, const QPointF &)>(dlsym(RTLD_DEFAULT, "_ZNK10QQuickItem10mapToSceneERK7QPointF"));
    if (!children || !map) return false;
    for (auto window : QGuiApplication::allWindows()) {
        if (!window->isVisible()) continue;
        auto button = findButton(window->property("contentItem").value<QObject *>(), children, text);
        if (!button) continue;
        auto point = map(button, QPointF(button->property("width").toDouble()/2, button->property("height").toDouble()/2));
        window->requestActivate();
        QTest::mouseMove(window, point.toPoint());
        QTest::mouseClick(window, Qt::LeftButton, Qt::NoModifier, point.toPoint());
        return true;
    }
    return false;
}
static bool secondInstance(QObject *providedHost = nullptr,
                           const QString &plugin = QStringLiteral("org.irixclassic.domainos.preferences.test"))
{
    // The installed runtime exposes these public APIs. Dynamic resolution keeps
    // this test independent of development packages and modifies only its host.
    const auto loaderSelf = reinterpret_cast<QObject *(*)()>(dlsym(RTLD_DEFAULT, "_ZN6Plasma12PluginLoader4selfEv"));
    const auto load = reinterpret_cast<QObject *(*)(QObject *, const QString &, uint, const QVariantList &)>(dlsym(RTLD_DEFAULT, "_ZN6Plasma12PluginLoader10loadAppletERK7QStringjRK5QListI8QVariantE"));
    const auto itemForApplet = reinterpret_cast<QObject *(*)(QObject *)>(dlsym(RTLD_DEFAULT, "_ZN11PlasmaQuick15AppletQuickItem13itemForAppletEPN6Plasma6AppletE"));
    const auto nativeApplet = reinterpret_cast<QObject *(*)(QObject *)>(dlsym(RTLD_DEFAULT, "_ZNK11PlasmaQuick15AppletQuickItem6appletEv"));
    const auto containment = reinterpret_cast<QObject *(*)(QObject *)>(dlsym(RTLD_DEFAULT, "_ZNK6Plasma6Applet11containmentEv"));
    const auto addApplet = reinterpret_cast<void (*)(QObject *, QObject *, const QRectF &)>(dlsym(RTLD_DEFAULT, "_ZN6Plasma11Containment9addAppletEPNS_6AppletERK6QRectF"));
    const auto setParentItem = reinterpret_cast<void (*)(QObject *, QObject *)>(dlsym(RTLD_DEFAULT, "_ZN10QQuickItem13setParentItemEPS_"));
    if (!loaderSelf || !load || !itemForApplet || !setParentItem || !nativeApplet || !containment || !addApplet) return false;
    auto host = providedHost ? providedHost : fixture->property("nativeHost").value<QObject *>();
    if (!host) return false;
    auto owner = containment(nativeApplet(host));
    if (!owner) return false;
    auto applet = load(loaderSelf(), plugin, 101, {});
    if (!applet) return false;
    addApplet(owner, applet, QRectF(2000, 0, 600, 600));
    secondItem = itemForApplet(applet);
    if (!secondItem) return false;
    for (auto window : QGuiApplication::allWindows()) {
        if (!window->isVisible()) continue;
        auto content = window->property("contentItem").value<QObject *>();
        if (!content) continue;
        setParentItem(secondItem, content);
        secondItem->setProperty("x", 2000);
        secondItem->setProperty("width", 600);
        secondItem->setProperty("height", 600);
        return true;
    }
    return false;
}
static QJsonObject taskFilterSnapshot(QObject *panel)
{
    auto runtime = panel ? panel->property("integration").value<QObject *>() : nullptr;
    auto tasks = runtime ? runtime->property("tasks").value<QObject *>() : nullptr;
    auto view = tasks ? tasks->property("tasksModel").value<QObject *>() : nullptr;
    auto scope = tasks ? tasks->property("scopeModel").value<QObject *>() : nullptr;
    return QJsonObject{{"controllerAvailable", tasks != nullptr}, {"viewAvailable", view != nullptr}, {"scopeAvailable", scope != nullptr},
        {"controllerOnlyCurrentScreen", tasks && tasks->property("onlyCurrentScreen").toBool()},
        {"viewFilterByScreen", view && view->property("filterByScreen").toBool()},
        {"scopeFilterByScreen", scope && scope->property("filterByScreen").toBool()}};
}
static void panelPreferencesUiStep()
{
    const auto children = reinterpret_cast<Children>(dlsym(RTLD_DEFAULT, "_ZNK10QQuickItem10childItemsEv"));
    const auto grab = reinterpret_cast<Grab>(dlsym(RTLD_DEFAULT, "_ZN12QQuickWindow10grabWindowEv"));
    const auto nativeApplet = reinterpret_cast<QObject *(*)(QObject *)>(dlsym(RTLD_DEFAULT, "_ZNK11PlasmaQuick15AppletQuickItem6appletEv"));
    const auto action = reinterpret_cast<QObject *(*)(QObject *, const QString &)>(dlsym(RTLD_DEFAULT, "_ZNK6Plasma6Applet14internalActionERK7QString"));
    const auto rootObject = reinterpret_cast<QObject *(*)(QObject *)>(dlsym(RTLD_DEFAULT, "_ZN11PlasmaQuick10ConfigView10rootObjectEv"));
    const auto configModel = reinterpret_cast<QObject *(*)(QObject *)>(dlsym(RTLD_DEFAULT, "_ZNK11PlasmaQuick10ConfigView11configModelEv"));
    const auto viewApplet = reinterpret_cast<QObject *(*)(QObject *)>(dlsym(RTLD_DEFAULT, "_ZN11PlasmaQuick10ConfigView6appletEv"));
    if (!children || !grab || !nativeApplet || !action || !rootObject || !configModel || !viewApplet) { finish("Native panel preferences adapter unavailable"); return; }
    const bool reload = qEnvironmentVariable("IRIX_DOMAINOS_PREFERENCES_MODE") == "panel-ui-reload";
    if (stage == 0) {
        for (auto window : QGuiApplication::allWindows()) {
            auto content = window->property("contentItem").value<QObject *>();
            auto host = find(content, "domainosPanelApplet", children);
            auto panel = find(content, "domainosPanel", children);
            if (host && panel) { productionHost = host; productionPanel = panel; productionWindow = window; break; }
        }
        if (!productionHost || !productionPanel) { finish("Production root missing"); return; }
        productionSettings = productionPanel->property("settings").value<QObject *>();
        auto configure = action(nativeApplet(productionHost), QStringLiteral("domainos-configure-panel"));
        auto tray = action(nativeApplet(productionHost), QStringLiteral("configure"));
        report["configuration_map_available"] = productionSettings != nullptr;
        report["production_applet_id"] = nativeApplet(productionHost)->property("id").toInt();
        report["configuration_action_distinct_from_tray"] = configure && tray && configure != tray;
        report["initial_configuration"] = configurationSnapshot(productionSettings);
        report["initial_task_filter"] = taskFilterSnapshot(productionPanel);
        if (reload) {
            report["reloaded_configuration"] = configurationSnapshot(productionSettings);
            report["reloaded_task_filter"] = taskFilterSnapshot(productionPanel);
            captureVisibleContext("RELOADED");
            finish(); return;
        }
        productionActionSpy = new QSignalSpy(productionPanel, SIGNAL(actionRequested(QString,QVariant)));
        captureVisibleContext("UI-BEFORE-DRAWER");
        report["drawer_button_physical_click"] = clickPhysical("domainosApplicationsDrawer");
    } else if (stage == 1) {
        captureVisibleContext("UI-DRAWER-OPEN");
        report["preferences_entry_physical_click"] = clickPhysical("domainosPinnedPreferencesEntry");
    } else if (stage == 2) {
        for (auto window : QGuiApplication::allWindows()) if (window->inherits("PlasmaQuick::ConfigView") && window->isVisible()) {
            configWindow = window; configRoot = rootObject(window); break;
        }
        if (!configWindow || !configRoot) { finish("Physical preferences entry did not open ConfigView"); return; }
        report["config_view_owner_id"] = viewApplet(configWindow)->property("id").toInt();
        auto model = qobject_cast<QAbstractItemModel *>(configModel(configWindow));
        QJsonArray categories;
        const auto roles = model ? model->roleNames() : QHash<int, QByteArray>{};
        if (model) for (int row = 0; row < model->rowCount(); ++row) {
            QJsonObject category;
            for (auto role = roles.cbegin(); role != roles.cend(); ++role) if (role.value() == "name" || role.value() == "source")
                category[QString::fromUtf8(role.value())] = QJsonValue::fromVariant(model->data(model->index(row, 0), role.key()));
            categories.append(category);
        }
        report["config_categories"] = categories;
        // Keep the private test's controls inside the screen. No applet setting
        // or live user's window is changed by this test-window preparation.
        configWindow->resize(1200, 800);
        QTest::qWait(150);
        report["preferences_capture_saved"] = grab(configWindow).save(qEnvironmentVariable("IRIX_DOMAINOS_PREFERENCES_DIR")+"/UI-PANEL-PREFERENCES.png");
        report["iconbox_category_physical_click"] = physicalButton(findButton(configRoot, children, QStringLiteral("Iconbox")), configWindow, "IconboxCategory");
    } else if (stage == 3) {
        auto page = findProperty(configRoot, "cfg_tasksOnlyCurrentScreen", children);
        report["iconbox_page_loaded"] = page != nullptr;
        report["iconbox_current_source"] = configRoot->property("currentSource").toString();
        if (!page) { finish("Iconbox category click did not load the configuration page"); return; }
        report["second_instance_created"] = secondInstance(productionHost, QStringLiteral("org.irixclassic.domainos.panel"));
    } else if (stage == 4) {
        auto other = find(secondItem, "domainosPanel", children);
        secondProductionSettings = other ? other->property("settings").value<QObject *>() : nullptr;
        report["second_instance_id"] = secondItem ? nativeApplet(secondItem)->property("id").toInt() : -1;
        report["second_configuration_before_edit"] = configurationSnapshot(secondProductionSettings);
        report["screen_checkbox_physical_click"] = physicalButton(findButton(configRoot, children, QStringLiteral("Somente esta tela")), configWindow, "OnlyCurrentScreenCheckbox");
    } else if (stage == 5) {
        auto page = findProperty(configRoot, "cfg_tasksOnlyCurrentScreen", children);
        report["page_screen_preference_after_edit"] = page && page->property("cfg_tasksOnlyCurrentScreen").toBool();
        report["configuration_before_apply"] = configurationSnapshot(productionSettings);
        report["second_configuration_before_apply"] = configurationSnapshot(secondProductionSettings);
        captureVisibleContext("UI-EDITED-UNSAVED");
        report["apply_button_physical_click"] = physicalButton(findButton(configRoot, children), configWindow, "ApplyButton");
    } else if (stage == 6) {
        report["configuration_after_apply"] = configurationSnapshot(productionSettings);
        report["second_configuration_after_apply"] = configurationSnapshot(secondProductionSettings);
        report["task_filter_after_apply"] = taskFilterSnapshot(productionPanel);
        report["apply_button_disabled_after_apply"] = findButton(configRoot, children) == nullptr;
        report["applied_capture_saved"] = grab(configWindow).save(qEnvironmentVariable("IRIX_DOMAINOS_PREFERENCES_DIR")+"/UI-ICONBOX-APPLIED.png");
        captureVisibleContext("UI-APPLIED");
        // Change the same checkbox back without saving, then use the actual
        // native Cancel/Discard controls. The saved preference must stay true.
        report["unsaved_checkbox_physical_click"] = physicalButton(findButton(configRoot, children, QStringLiteral("Somente esta tela")), configWindow, "UnsavedScreenCheckbox");
    } else if (stage == 7) {
        auto page = findProperty(configRoot, "cfg_tasksOnlyCurrentScreen", children);
        report["page_screen_preference_unsaved"] = page && page->property("cfg_tasksOnlyCurrentScreen").toBool();
        report["configuration_before_discard"] = configurationSnapshot(productionSettings);
        report["cancel_button_physical_click"] = physicalButton(findButton(configRoot, children, QStringLiteral("Cancel")), configWindow, "CancelButton");
    } else if (stage == 8) {
        captureVisibleContext("UI-CANCEL-PROMPT");
        // QQC Popup reparents its visual controls to the window's Overlay,
        // a sibling of the configuration root. Inspect the genuine scene.
        auto sceneRoot = configWindow->property("contentItem").value<QObject *>();
        QJsonArray buttons; recordButtons(sceneRoot, children, buttons); report["discard_prompt_buttons"] = buttons;
        report["discard_button_physical_click"] = physicalButton(findButton(sceneRoot, children, QStringLiteral("Discard")), configWindow, "DiscardButton");
    } else if (stage == 9) {
        report["configuration_window_closed_after_discard"] = !configWindow || !configWindow->isVisible();
        report["configuration_after_discard"] = configurationSnapshot(productionSettings);
        report["second_configuration_after_discard"] = configurationSnapshot(secondProductionSettings);
        captureVisibleContext("UI-DISCARDED");
        if (!report["configuration_window_closed_after_discard"].toBool()) { finish("Native Discard did not close the preferences window"); return; }
        configWindow = nullptr; configRoot = nullptr;
        report["reopen_drawer_physical_click"] = clickPhysical("domainosApplicationsDrawer");
    } else if (stage == 10) {
        report["reopen_preferences_physical_click"] = clickPhysical("domainosPinnedPreferencesEntry");
    } else if (stage == 11) {
        for (auto window : QGuiApplication::allWindows()) if (window->inherits("PlasmaQuick::ConfigView") && window->isVisible()) {
            configWindow = window; configRoot = rootObject(window); break;
        }
        if (!configWindow || !configRoot) { finish("Physical Preferences re-open did not show the native dialog"); return; }
        report["reopened_config_view_owner_id"] = viewApplet(configWindow)->property("id").toInt();
        configWindow->resize(1200, 800); QTest::qWait(150);
        report["reopened_iconbox_category_physical_click"] = physicalButton(findButton(configRoot, children, QStringLiteral("Iconbox")), configWindow, "ReopenedIconboxCategory");
    } else {
        auto page = findProperty(configRoot, "cfg_tasksOnlyCurrentScreen", children);
        report["reopened_iconbox_page_loaded"] = page != nullptr;
        report["reopened_screen_preference"] = page && page->property("cfg_tasksOnlyCurrentScreen").toBool();
        report["reopened_configuration"] = configurationSnapshot(productionSettings);
        report["reopened_apply_button_disabled"] = findButton(configRoot, children) == nullptr;
        report["reopened_capture_saved"] = grab(configWindow).save(qEnvironmentVariable("IRIX_DOMAINOS_PREFERENCES_DIR")+"/UI-ICONBOX-REOPENED.png");
        captureVisibleContext("UI-REOPENED");
        finish(); return;
    }
    ++stage;
    QTimer::singleShot(650, panelPreferencesUiStep);
}
static void productionStep()
{
    const auto children = reinterpret_cast<Children>(dlsym(RTLD_DEFAULT, "_ZNK10QQuickItem10childItemsEv"));
    const auto grab = reinterpret_cast<Grab>(dlsym(RTLD_DEFAULT, "_ZN12QQuickWindow10grabWindowEv"));
    const auto nativeApplet = reinterpret_cast<QObject *(*)(QObject *)>(dlsym(RTLD_DEFAULT, "_ZNK11PlasmaQuick15AppletQuickItem6appletEv"));
    const auto action = reinterpret_cast<QObject *(*)(QObject *, const QString &)>(dlsym(RTLD_DEFAULT, "_ZNK6Plasma6Applet14internalActionERK7QString"));
    const auto rootObject = reinterpret_cast<QObject *(*)(QObject *)>(dlsym(RTLD_DEFAULT, "_ZN11PlasmaQuick10ConfigView10rootObjectEv"));
    if (!children || !nativeApplet || !action || !rootObject || !grab) { finish("Native production adapter unavailable"); return; }
    const bool discard = qEnvironmentVariable("IRIX_DOMAINOS_PREFERENCES_MODE") == "tray-discard";
    const bool routing = qEnvironmentVariable("IRIX_DOMAINOS_PREFERENCES_MODE").startsWith("tray-routing");
    const bool physicalRouting = qEnvironmentVariable("IRIX_DOMAINOS_PREFERENCES_MODE") == "tray-routing-physical";
    if (stage == 0) {
        QObject *host = nullptr, *panel = nullptr;
        for (auto window : QGuiApplication::allWindows()) {
            auto content = window->property("contentItem").value<QObject *>();
            if (!host) host = find(content, "domainosPanelApplet", children);
            if (!panel) panel = find(content, "domainosPanel", children);
        }
        if (!host || !panel) { finish("Production root missing"); return; }
        productionHost = host;
        productionSettings = panel->property("settings").value<QObject *>();
        productionBridge = action(nativeApplet(host), QStringLiteral("domainos-tray-items"));
        report["production_bridge_present"] = productionBridge != nullptr;
        report["production_applet_id"] = nativeApplet(host)->property("id").toInt();
        report["native_provider_items"] = productionBridge ? QJsonDocument::fromJson(productionBridge->property("itemsJson").toString().toUtf8()).array() : QJsonArray{};
        report["configuration_map_available"] = productionSettings != nullptr;
        auto configure = qobject_cast<QAction *>(action(nativeApplet(host), QStringLiteral("domainos-configure-panel")));
        auto trayConfigure = qobject_cast<QAction *>(action(nativeApplet(host), QStringLiteral("configure")));
        report["production_configuration_requested"] = configure != nullptr;
        report["production_configuration_action_distinct_from_tray"] = configure && trayConfigure && configure != trayConfigure;
        // Exercise the signal emitted by the pinned Preferences entry, rather
        // than bypassing main.qml's routing with a direct QAction trigger.
        if (routing) {
            report["saved_hidden_before_open"] = productionSettings ? QJsonValue::fromVariant(productionSettings->property("trayHiddenItems")) : QJsonValue{};
        }
        if (physicalRouting) {
            productionActionSpy = new QSignalSpy(panel, SIGNAL(actionRequested(QString,QVariant)));
            report["production_panel_action_spy_valid"] = productionActionSpy->isValid();
            captureVisibleContext("BEFORE-DRAWER");
            // Opening this hide-on-deactivate dialog programmatically while
            // another native window has focus can immediately dismiss it.
            // Reproduce the user's complete route with physical pointer input.
            report["production_pinned_drawer_open_requested"] = clickPhysical("domainosApplicationsDrawer");
        } else report["production_pinned_configuration_route_invoked"] = QMetaObject::invokeMethod(panel, "configureRequested", Qt::DirectConnection);
    } else if (physicalRouting && stage == 1) {
        captureVisibleContext("AFTER-DRAWER");
        report["production_pinned_preferences_physical_click"] = clickPhysical("domainosPinnedPreferencesEntry");
        report["production_pinned_configuration_route_invoked"] = report["production_pinned_preferences_physical_click"].toBool();
    } else if (stage == 1 || (physicalRouting && stage == 2)) {
        for (auto window : QGuiApplication::allWindows()) if (window->inherits("PlasmaQuick::ConfigView") && window->isVisible()) {
            configWindow = window; configRoot = rootObject(window); break;
        }
        report["production_config_view_visible"] = configRoot != nullptr;
        const auto viewApplet = reinterpret_cast<QObject *(*)(QObject *)>(dlsym(RTLD_DEFAULT, "_ZN11PlasmaQuick10ConfigView6appletEv"));
        if (configWindow && viewApplet) report["production_config_applet_id"] = viewApplet(configWindow)->property("id").toInt();
        if (!configRoot) { finish("Production ConfigView missing"); return; }
        const auto configModel = reinterpret_cast<QObject *(*)(QObject *)>(dlsym(RTLD_DEFAULT, "_ZNK11PlasmaQuick10ConfigView11configModelEv"));
        auto model = configModel ? qobject_cast<QAbstractItemModel *>(configModel(configWindow)) : nullptr;
        QJsonArray categories;
        const auto roles = model ? model->roleNames() : QHash<int, QByteArray>{};
        if (model) for (int row = 0; row < model->rowCount(); ++row) {
            QJsonObject category;
            for (auto role = roles.cbegin(); role != roles.cend(); ++role) {
                if (role.value() == "name" || role.value() == "source") category[QString::fromUtf8(role.value())] = QJsonValue::fromVariant(model->data(model->index(row, 0), role.key()));
            }
            categories.append(category);
        }
        report["production_config_categories"] = categories;
        report["production_initial_config_source"] = configRoot->property("currentSource").toString();
        report["production_initial_preferences_capture_saved"] = grab(configWindow).save(qEnvironmentVariable("IRIX_DOMAINOS_PREFERENCES_DIR")+"/PRODUCTION-PANEL-PREFERENCES.png");
        if (routing) {
            report["saved_hidden_after_open"] = productionSettings ? QJsonValue::fromVariant(productionSettings->property("trayHiddenItems")) : QJsonValue{};
            report["qt_version"] = qVersion();
            finish();
            return;
        }
        const QVariant category = QVariantMap{{"name", "Bandeja e notificações"},
            {"source", QUrl::fromLocalFile(qEnvironmentVariable("IRIX_DOMAINOS_PRODUCTION_TRAY_PAGE"))}};
        report["production_tray_category_opened"] = QMetaObject::invokeMethod(configRoot, "open", Qt::DirectConnection, Q_ARG(QVariant, category));
    } else if (stage == 2) {
        auto page = find(configRoot, "domainosTrayConfigPage", children);
        report["production_tray_page_loaded"] = page != nullptr;
        if (!page) { finish("Production tray page missing"); return; }
        report["production_snapshot_available"] = page->property("nativeSnapshotAvailable").toBool();
        report["production_page_context"] = QJsonDocument::fromJson(page->property("nativeContextJson").toString().toUtf8()).object();
        report["configuration_provider_items"] = QJsonDocument::fromJson(page->property("availableItemsJson").toString().toUtf8()).array();
        report["provider_titles_received"] = report["native_provider_items"] == report["configuration_provider_items"];
        report["saved_hidden_before_edit"] = productionSettings ? QJsonValue::fromVariant(productionSettings->property("trayHiddenItems")) : QJsonValue{};
        report["production_policy_control_mouse_click"] = click("domainosTrayPolicy_org.kde.plasma.volume");
        if (report["production_policy_control_mouse_click"].toBool() && configWindow) {
            // Record focus separately: synthetic QWindow events do not prove
            // that the native window manager moved keyboard focus.
            auto keyWindow = QGuiApplication::focusWindow();
            report["production_policy_key_window_is_dialog"] = keyWindow == configWindow;
            report["production_policy_key_window_class"] = keyWindow ? keyWindow->metaObject()->className() : "";
            QTest::keyClick(configWindow, Qt::Key_End);
            QTest::keyClick(configWindow, Qt::Key_Return);
        }
        report["production_policy_edited"] = page->property("cfg_trayHiddenItems").toStringList() == QStringList{"org.kde.plasma.volume"};
        report["production_page_policy_after_edit"] = QJsonArray::fromStringList(page->property("cfg_trayHiddenItems").toStringList());
        if (discard) report["second_production_instance_created"] = secondInstance(productionHost,QStringLiteral("org.irixclassic.domainos.panel"));
    } else if (stage == 3) {
        report["saved_hidden_before_apply"] = productionSettings ? QJsonValue::fromVariant(productionSettings->property("trayHiddenItems")) : QJsonValue{};
        if (discard) {
            auto otherPanel = find(secondItem,"domainosPanel",children);
            secondProductionSettings = otherPanel ? otherPanel->property("settings").value<QObject *>() : nullptr;
            report["second_hidden_before_discard"] = secondProductionSettings ? QJsonValue::fromVariant(secondProductionSettings->property("trayHiddenItems")) : QJsonValue{};
            report["second_instance_id"] = secondItem ? nativeApplet(secondItem)->property("id").toInt() : -1;
            report["production_real_cancel_mouse_click"] = clickNativeCommand(QStringLiteral("Cancel"));
        } else report["production_real_apply_mouse_click"] = clickNativeApply();
    } else if (discard && stage == 4) {
        report["saved_hidden_before_discard"] = QJsonValue::fromVariant(productionSettings->property("trayHiddenItems"));
        report["production_real_discard_mouse_click"] = clickNativeCommand(QStringLiteral("Discard"));
    } else if (discard && stage == 5) {
        report["native_config_closed_after_discard"] = !configWindow || !configWindow->isVisible();
        report["saved_hidden_after_discard"] = QJsonValue::fromVariant(productionSettings->property("trayHiddenItems"));
        report["second_hidden_after_discard"] = secondProductionSettings ? QJsonValue::fromVariant(secondProductionSettings->property("trayHiddenItems")) : QJsonValue{};
        auto configure = qobject_cast<QAction *>(action(nativeApplet(productionHost),QStringLiteral("domainos-configure-panel")));
        report["native_config_reopen_requested"] = configure != nullptr;
        if (configure) configure->trigger();
    } else if (discard && stage == 6) {
        for (auto window : QGuiApplication::allWindows()) if (window->inherits("PlasmaQuick::ConfigView") && window->isVisible()) {
            configWindow=window;configRoot=rootObject(window);break;
        }
        report["native_config_reopened"] = configWindow && configRoot;
        const QVariant category=QVariantMap{{"name","Bandeja e notificações"},{"source",QUrl::fromLocalFile(qEnvironmentVariable("IRIX_DOMAINOS_PRODUCTION_TRAY_PAGE"))}};
        if (configRoot) QMetaObject::invokeMethod(configRoot,"open",Qt::DirectConnection,Q_ARG(QVariant,category));
    } else if (discard) {
        auto page=find(configRoot,"domainosTrayConfigPage",children);
        report["reopened_page_uses_saved_policy"] = page && page->property("cfg_trayHiddenItems").toStringList().isEmpty();
        report["saved_hidden_after_reopen"] = QJsonValue::fromVariant(productionSettings->property("trayHiddenItems"));
        report["second_hidden_after_reopen"] = secondProductionSettings ? QJsonValue::fromVariant(secondProductionSettings->property("trayHiddenItems")) : QJsonValue{};
        report["native_provider_items_after_discard"] = productionBridge ? QJsonDocument::fromJson(productionBridge->property("itemsJson").toString().toUtf8()).array() : QJsonArray{};
        if (configWindow) report["production_capture_saved"] = grab(configWindow).save(qEnvironmentVariable("IRIX_DOMAINOS_PREFERENCES_DIR")+"/PRODUCTION-DISCARD-REOPENED.png");
        report["qt_version"]=qVersion();finish();return;
    } else {
        report["saved_hidden_after_apply"] = productionSettings ? QJsonValue::fromVariant(productionSettings->property("trayHiddenItems")) : QJsonValue{};
        report["native_provider_items_after_apply"] = productionBridge ? QJsonDocument::fromJson(productionBridge->property("itemsJson").toString().toUtf8()).array() : QJsonArray{};
        if (configWindow) report["production_capture_saved"] = grab(configWindow).save(qEnvironmentVariable("IRIX_DOMAINOS_PREFERENCES_DIR") + "/PRODUCTION-TRAY-CONFIGURATION.png");
        finish(); return;
    }
    ++stage;
    QTimer::singleShot(stage == 4 ? 1200 : 650, productionStep);
}
static void step()
{
    const auto children = reinterpret_cast<Children>(dlsym(RTLD_DEFAULT, "_ZNK10QQuickItem10childItemsEv"));
    const auto grab = reinterpret_cast<Grab>(dlsym(RTLD_DEFAULT, "_ZN12QQuickWindow10grabWindowEv"));
    if (!children || !grab) { finish("QtQuick native adapter unavailable"); return; }
    if (!fixture) for (auto window : QGuiApplication::allWindows()) {
        fixture = find(window->property("contentItem").value<QObject *>(), "domainosPreferencesTestFixture", children);
        if (fixture) break;
    }
    if (!fixture) { finish("Native preference fixture missing"); return; }
    const bool reload = qEnvironmentVariable("IRIX_DOMAINOS_PREFERENCES_MODE") == "reload";
    static const QStringList names{"initial", "edited_unsaved", "discarded", "activity_applied", "iconbox_initial", "automatic_without_threshold", "iconbox_edited_unsaved", "iconbox_applied", "pins_initial", "pins_edited_unsaved", "pins_applied", "import_origins", "import_source_unsaved", "import_applied", "monitor", "clock_calendar", "commands", "pager", "tray_initial", "tray_edited_unsaved", "tray_applied", "other_instance", "native_configuration_dialog", "native_dialog_unsaved", "native_dialog_applied"};
    auto snapshot = QJsonDocument::fromJson(fixture->property("snapshotJson").toString().toUtf8()).object();
    report[reload ? "reloaded" : names[stage]] = snapshot;
    QFile progress(qEnvironmentVariable("IRIX_DOMAINOS_PREFERENCES_REPORT"));
    if (progress.open(QIODevice::WriteOnly)) { progress.write(QJsonDocument(report).toJson()); progress.close(); }
    if (!reload && stage == 21) {
        auto second = find(secondItem, "domainosPreferencesTestFixture", children);
        report["second_instance"] = second ? QJsonDocument::fromJson(second->property("snapshotJson").toString().toUtf8()).object() : QJsonObject{{"missing", true}};
    }
    if (!reload && stage == 22) {
        const auto configModel = reinterpret_cast<QObject *(*)(QObject *)>(dlsym(RTLD_DEFAULT, "_ZNK11PlasmaQuick10ConfigView11configModelEv"));
        const auto rootObject = reinterpret_cast<QObject *(*)(QObject *)>(dlsym(RTLD_DEFAULT, "_ZN11PlasmaQuick10ConfigView10rootObjectEv"));
        for (auto window : QGuiApplication::allWindows()) {
            if (!window->inherits("PlasmaQuick::ConfigView") || !window->isVisible()) continue;
            report["native_config_view_visible"] = true;
            auto model = configModel ? qobject_cast<QAbstractItemModel *>(configModel(window)) : nullptr;
            QJsonArray categories;
            const auto roles = model ? model->roleNames() : QHash<int, QByteArray>{};
            if (model) for (int row = 0; row < model->rowCount(); ++row) {
                QJsonObject category;
                for (auto role = roles.cbegin(); role != roles.cend(); ++role) {
                    if (role.value() == "name" || role.value() == "source") category[QString::fromUtf8(role.value())] = QJsonValue::fromVariant(model->data(model->index(row, 0), role.key()));
                }
                categories.append(category);
            }
            report["native_config_categories"] = categories;
            auto root = rootObject ? rootObject(window) : nullptr;
            configWindow = window;
            configRoot = root;
            report["native_config_current_source"] = root ? root->property("currentSource").toString() : "";
            grab(window).save(qEnvironmentVariable("IRIX_DOMAINOS_PREFERENCES_DIR") + "/NATIVE-CONFIGURATION.png");
        }
    }
    if (stage == 0 || stage == 6 || stage == 12 || stage == 15 || stage == 19) {
        for (auto window : QGuiApplication::allWindows()) if (window->isVisible() && window->inherits("QQuickWindow")) {
            grab(window).save(qEnvironmentVariable("IRIX_DOMAINOS_PREFERENCES_DIR") + "/" + (reload ? "RELOAD" : names[stage].toUpper()) + ".png");
            break;
        }
    }
    if (reload || ++stage == names.size()) { report["qt_version"] = qVersion(); finish(); return; }
    fixture->setProperty("scenario", stage);
    if (stage == 11 || stage == 12) {
        const bool clicked = click(stage == 11 ? "domainosChoosePinImportSource" : "domainosImportChosenPinSource");
        report[stage == 11 ? "real_origins_mouse_click" : "real_source_mouse_click"] = clicked;
        QTimer::singleShot(2200, step);
    } else if (stage == 21) {
        report["created_second_native_instance"] = secondInstance();
        QTimer::singleShot(1200, step);
    } else if (stage == 23) {
        auto search = find(configRoot, "domainosTimeZoneSearch", children);
        report["native_clock_search_used"] = search && search->setProperty("text", "Manaus");
        QTimer::singleShot(150, [](){
            report["native_clock_page_edited"] = click("domainosTimeZoneChoice_America/Manaus");
            QTimer::singleShot(150, step);
        });
    } else if (stage == 24) {
        QJsonArray buttons; recordButtons(configRoot, children, buttons); report["native_dialog_buttons"] = buttons;
        report["real_native_apply_mouse_click"] = clickNativeApply();
        QTimer::singleShot(400, step);
    } else QTimer::singleShot(400, step);
}
extern "C" int interceptedExec() asm("_ZN12QApplication4execEv");
extern "C" int interceptedExec()
{
    const auto original = reinterpret_cast<int (*)()>(dlsym(RTLD_NEXT, "_ZN12QApplication4execEv"));
    if (!original || qEnvironmentVariable("IRIX_DOMAINOS_PREFERENCES_TEST") != "1") return original ? original() : 1;
    const auto mode = qEnvironmentVariable("IRIX_DOMAINOS_PREFERENCES_MODE");
    QTimer::singleShot(1700, mode.startsWith("panel-ui-") ? panelPreferencesUiStep : mode.startsWith("tray-") ? productionStep : step);
    QTimer::singleShot(30000, [](){ finish("Bounded preferences test timeout"); });
    return original();
}
