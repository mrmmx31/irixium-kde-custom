// SPDX-FileCopyrightText: 2026 mrmmx31
// SPDX-License-Identifier: GPL-3.0-or-later
// Exercise real Plasma KConfigPropertyMap and native applet instances privately.
#include <QApplication>
#include <QAbstractItemModel>
#include <QAction>
#include <QElapsedTimer>
#include <QFile>
#include <QImage>
#include <QJsonArray>
#include <QJsonDocument>
#include <QJsonObject>
#include <QRectF>
#include <QPointer>
#include <QTimer>
#include <QTest>
#include <QUrl>
#include <QWindow>
#include <dlfcn.h>

using Children = QList<QObject *> (*)(QObject *);
using Grab = QImage (*)(QWindow *);
static QObject *fixture = nullptr;
static QObject *secondItem = nullptr;
static QObject *carrierHost = nullptr;
static QObject *firstNativeItem = nullptr;
static QPointer<QWindow> configWindow;
static QObject *configRoot = nullptr;
static QObject *productionSettings = nullptr;
static QObject *productionBridge = nullptr;
static QObject *productionHost = nullptr;
static QObject *secondProductionSettings = nullptr;
static QJsonObject report;
static int stage = 0;
static bool finished = false;
static QElapsedTimer executionTime;
static constexpr int executionDeadlineMilliseconds = 30000;

static QStringList categoryPages()
{
    const auto requested=qEnvironmentVariable("IRIX_DOMAINOS_DEFAULTS_PAGES");
    return requested.isEmpty() ? QStringList{"ConfigIconbox.qml","ConfigTray.qml","ConfigApplications.qml"}
        : requested.split(',',Qt::SkipEmptyParts);
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
    if (finished) return;
    finished = true;
    if (!failure.isEmpty()) report["failure"] = failure;
    report["execution_stage"] = stage;
    report["execution_elapsed_milliseconds"] = executionTime.elapsed();
    report["execution_deadline_milliseconds"] = executionDeadlineMilliseconds;
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
        QTest::mouseMove(window, point.toPoint());
        QTest::mouseClick(window, Qt::LeftButton, Qt::NoModifier, point.toPoint());
        return true;
    }
    return false;
}
static QObject *findButton(QObject *item, Children children, const QString &wanted = QStringLiteral("Apply"))
{
    if (!item) return nullptr;
    QString text = item->property("text").toString().remove('&');
    if (item->inherits("QQuickAbstractButton") && item->property("enabled").toBool()
        && item->property("visible").toBool()
        && (text == wanted || (wanted == "Apply" && text == "Aplicar"))) return item;
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
                           uint instanceId = 101,
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
    auto applet = load(loaderSelf(), plugin, instanceId, {});
    if (!applet) return false;
    addApplet(owner, applet, QRectF(2000, 0, 600, 600));
    secondItem = itemForApplet(applet);
    if (!secondItem) return false;
    for (auto window : QGuiApplication::allWindows()) {
        if (!window->isVisible()) continue;
        auto content = window->property("contentItem").value<QObject *>();
        if (!content) continue;
        setParentItem(secondItem, content);
        secondItem->setProperty("x", instanceId==100 ? 0 : 2000);
        secondItem->setProperty("width", 600);
        secondItem->setProperty("height", 600);
        return true;
    }
    return false;
}

static QJsonObject nativeValues(QObject *item)
{
    return item ? QJsonDocument::fromJson(item->property("snapshotJson").toString().toUtf8()).object() : QJsonObject{};
}
static QJsonObject editedValues(QObject *page)
{
    QJsonObject result;
    const auto keys=nativeValues(fixture)["values"].toObject().keys();
    using Convert=QVariant (*)(const void *);
    const auto convert=reinterpret_cast<Convert>(dlsym(RTLD_DEFAULT,"_ZNK8QJSValue9toVariantEv"));
    for(const auto &key:keys) {
        const QByteArray name=("cfg_"+key).toUtf8();
        if(page && page->metaObject()->indexOfProperty(name.constData())>=0) {
            auto value=page->property(name.constData());
            if(QByteArray(value.metaType().name())=="QJSValue" && convert)value=convert(value.constData());
            result[key]=QJsonValue::fromVariant(value);
        }
    }
    return result;
}
static QObject *secondFixture(Children children)
{
    return find(secondItem,"domainosDefaultsFixture",children);
}
static void configureDefaults()
{
    const auto nativeApplet=reinterpret_cast<QObject *(*)(QObject *)>(dlsym(RTLD_DEFAULT,"_ZNK11PlasmaQuick15AppletQuickItem6appletEv"));
    const auto internalAction=reinterpret_cast<QObject *(*)(QObject *, const QString &)>(dlsym(RTLD_DEFAULT,"_ZNK6Plasma6Applet14internalActionERK7QString"));
    auto host=fixture->property("nativeHost").value<QObject *>();
    auto configure=nativeApplet && internalAction && host ? qobject_cast<QAction *>(internalAction(nativeApplet(host),QStringLiteral("configure"))) : nullptr;
    if(configure)configure->trigger();
    report["native_configuration_requested"]=configure!=nullptr;
}
static bool currentConfig()
{
    const auto rootObject=reinterpret_cast<QObject *(*)(QObject *)>(dlsym(RTLD_DEFAULT,"_ZN11PlasmaQuick10ConfigView10rootObjectEv"));
    for(auto window:QGuiApplication::allWindows())if(window->inherits("PlasmaQuick::ConfigView") && window->isVisible()) {
        configWindow=window;configRoot=rootObject ? rootObject(window) : nullptr;return configRoot!=nullptr;
    }
    return false;
}
static bool openPage(const QString &name)
{
    // Keep the production category title when selecting through the native API.
    // Using the source filename as item.name would produce a QA-only header.
    const auto configModel=reinterpret_cast<QObject *(*)(QObject *)>(dlsym(RTLD_DEFAULT,"_ZNK11PlasmaQuick10ConfigView11configModelEv"));
    auto model=configModel && configWindow ? qobject_cast<QAbstractItemModel *>(configModel(configWindow)) : nullptr;
    if(!model)return false;
    const auto roles=model->roleNames();
    int sourceRole=-1,nameRole=-1;
    for(auto role=roles.cbegin();role!=roles.cend();++role) {
        if(role.value()=="source")sourceRole=role.key();
        else if(role.value()=="name")nameRole=role.key();
    }
    QString categoryName;
    for(int row=0;sourceRole>=0 && nameRole>=0 && row<model->rowCount();++row) {
        const auto index=model->index(row,0);
        const auto source=model->data(index,sourceRole).toString();
        if(source==name || source.endsWith("/"+name)) {
            categoryName=model->data(index,nameRole).toString();break;
        }
    }
    if(categoryName.isEmpty())return false;
    const QVariant category=QVariantMap{{"name",categoryName},{"source",QUrl::fromLocalFile(qEnvironmentVariable("IRIX_DOMAINOS_DEFAULTS_UI")+"/"+name)}};
    return configRoot && QMetaObject::invokeMethod(configRoot,"open",Qt::DirectConnection,Q_ARG(QVariant,category));
}
static QObject *currentPage(Children children)
{
    // General has a stable object name; category footers expose their owning page.
    if(auto page=find(configRoot,"domainosDefaultsConfigPage",children))return page;
    if(auto reset=find(configRoot,"domainosResetCategory",children)) {
        auto parent=reset->property("parent").value<QObject *>();
        for(int i=0;parent && i<8;++i) {
            const auto target=parent->property("targetPage").value<QObject *>();
            if(target)return target;
            parent=parent->property("parent").value<QObject *>();
        }
    }
    return nullptr;
}
static QObject *findWithProperty(QObject *item, const char *property, Children children)
{
    if (!item) return nullptr;
    if (item->metaObject()->indexOfProperty(property)>=0) return item;
    if (item->inherits("QQuickItem")) for (auto child:children(item))
        if (auto match=findWithProperty(child,property,children)) return match;
    return nullptr;
}
static QJsonObject snapshot(Children children)
{
    const bool alive=configWindow && configWindow->isVisible() && configRoot;
    const auto page=alive ? (qEnvironmentVariable("IRIX_DOMAINOS_DEFAULTS_MODE")=="baseline"
        ? findWithProperty(configRoot,"cfg_keepActivityLight",children) : currentPage(children)) : nullptr;
    auto apply=alive ? findButton(configRoot,children,QStringLiteral("Apply")) : nullptr;
    auto reset=alive ? find(configRoot,"domainosResetAllDefaults",children) : nullptr;
    if(!reset && alive)reset=find(configRoot,"domainosResetCategory",children);
    const auto grab=reinterpret_cast<Grab>(dlsym(RTLD_DEFAULT,"_ZN12QQuickWindow10grabWindowEv"));
    const auto directory=qEnvironmentVariable("IRIX_DOMAINOS_DEFAULTS_DIR");
    if(alive && grab && !directory.isEmpty())
        grab(configWindow).save(directory+"/"+qEnvironmentVariable("IRIX_DOMAINOS_DEFAULTS_MODE")+"-stage-"+QString::number(stage)+".png");
    return {{"first",nativeValues(fixture)},{"second",nativeValues(secondFixture(children))},
        {"edits",editedValues(page)},{"page_loaded",page!=nullptr},
        {"apply_enabled",apply && apply->property("enabled").toBool()},
        {"reset_enabled",reset && reset->property("enabled").toBool()},
        {"reset_present",reset!=nullptr},
        {"config_visible",configWindow && configWindow->isVisible()}};
}
static void defaultsStep()
{
    if (finished) return;
    const auto children=reinterpret_cast<Children>(dlsym(RTLD_DEFAULT,"_ZNK10QQuickItem10childItemsEv"));
    if(!children) {finish("Native visual tree adapter missing");return;}
    if(!carrierHost)for(auto window:QGuiApplication::allWindows()) {
        const auto carrier=find(window->property("contentItem").value<QObject *>(),"domainosDefaultsCarrier",children);
        if(carrier) {carrierHost=carrier->property("nativeHost").value<QObject *>();break;}
    }
    if(!firstNativeItem) {
        if(!carrierHost || !secondInstance(carrierHost,100,QStringLiteral("org.irixclassic.domainos.defaults.test"))) {
            finish("Native carrier/first instance missing");return;
        }
        firstNativeItem=secondItem;secondItem=nullptr;
        QTimer::singleShot(650,defaultsStep);return;
    }
    if(!fixture)fixture=find(firstNativeItem,"domainosDefaultsFixture",children);
    if(!fixture){finish("Defaults fixture not loaded");return;}
    if(qEnvironmentVariable("IRIX_DOMAINOS_DEFAULTS_MODE")=="baseline") {
        if(stage==0) {
            QMetaObject::invokeMethod(fixture,"seed",Qt::DirectConnection);
            report["seeded_first"]=nativeValues(fixture);
            configureDefaults();
        } else {
            const int cycle=(stage-1)/5,offset=(stage-1)%5;
            const auto prefix=QStringLiteral("baseline_")+QString::number(cycle);
            if(offset==0) {
                if(!currentConfig() || !openPage("ConfigActivity.qml")) {
                    finish("Baseline native ConfigActivity missing");return;
                }
            } else if(offset==1) {
                report[prefix+"_opened"]=snapshot(children);
                auto page=findWithProperty(configRoot,"cfg_keepActivityLight",children);
                report[prefix+"_edit_local"]=page && page->setProperty("cfg_keepActivityLight",!page->property("cfg_keepActivityLight").toBool());
            } else if(offset==2) {
                report[prefix+"_pending"]=snapshot(children);
                report[prefix+"_cancel_pointer"]=clickNativeCommand(QStringLiteral("Cancel"));
            } else if(offset==3) {
                report[prefix+"_discard_pointer"]=clickNativeCommand(QStringLiteral("Discard"));
            } else {
                report[prefix+"_discarded"]=snapshot(children);
                if(cycle==2) {finish();return;}
                configureDefaults();
            }
        }
        if (!finished) { ++stage;QTimer::singleShot(650,defaultsStep); }
        return;
    }
    const bool reload=qEnvironmentVariable("IRIX_DOMAINOS_DEFAULTS_MODE")=="reload";
    if(reload) {
        if(stage==0) {
            report["reloaded_first"]=nativeValues(fixture);
            report["second_native_instance_created"]=secondInstance(carrierHost,101,QStringLiteral("org.irixclassic.domainos.defaults.test"));
            configureDefaults();
        } else if(stage==1) {
            report["reloaded_second"]=nativeValues(secondFixture(children));
            if(!currentConfig() || !openPage("ConfigDefaults.qml")){finish("Reload ConfigView missing");return;}
        } else if(stage==2) {
            report["reloaded_general"]=snapshot(children);finish();return;
        }
    } else if(stage==0) {
        report["initial_first"]=nativeValues(fixture);
        QMetaObject::invokeMethod(fixture,"seed",Qt::DirectConnection);
        report["seeded_first"]=nativeValues(fixture);
        report["second_native_instance_created"]=secondInstance(carrierHost,101,QStringLiteral("org.irixclassic.domainos.defaults.test"));
        configureDefaults();
    } else if(stage==1) {
        if(auto other=secondFixture(children))QMetaObject::invokeMethod(other,"seed",Qt::DirectConnection);
        report["seeded_second"]=nativeValues(secondFixture(children));
        if(!currentConfig() || !openPage("ConfigDefaults.qml")){finish("Native general ConfigView missing");return;}
    } else if(stage==2) {
        report["general_open_before_reset"]=snapshot(children);
        report["general_reset_pointer"]=click("domainosResetAllDefaults");
    } else if(stage==3) {
        report["general_prepared_before_discard"]=snapshot(children);
        report["native_cancel_pointer"]=clickNativeCommand(QStringLiteral("Cancel"));
    } else if(stage==4) {
        report["native_discard_pointer"]=clickNativeCommand(QStringLiteral("Discard"));
    } else if(stage==5) {
        report["general_discarded"]=snapshot(children);configureDefaults();
    } else if(stage==6) {
        if(!currentConfig() || !openPage("ConfigDefaults.qml")){finish("Reopened general ConfigView missing");return;}
    } else if(stage==7) {
        report["general_reopened_after_discard"]=snapshot(children);
        report["general_second_reset_pointer"]=click("domainosResetAllDefaults");
    } else if(stage==8) {
        report["general_prepared_before_apply"]=snapshot(children);
        report["native_general_apply_pointer"]=clickNativeApply();
    } else if(stage==9) {
        report["general_applied"]=snapshot(children);
        QMetaObject::invokeMethod(fixture,"seed",Qt::DirectConnection);
        if(!openPage(categoryPages().first())){finish("First category ConfigView missing");return;}
    } else if(stage>=10 && stage<10+3*categoryPages().size()) {
        const auto pages=categoryPages();
        const int index=(stage-10)/3,offset=(stage-10)%3;
        const auto prefix=pages[index];
        if(offset==0) {
            report[prefix+"_before"]=snapshot(children);
            report[prefix+"_reset_pointer"]=click("domainosResetCategory");
        } else if(offset==1) {
            report[prefix+"_prepared"]=snapshot(children);
            report[prefix+"_apply_pointer"]=clickNativeApply();
        } else {
            report[prefix+"_applied"]=snapshot(children);
            QMetaObject::invokeMethod(fixture,"seed",Qt::DirectConnection);
            if(!openPage(index+1<pages.size() ? pages[index+1] : QStringLiteral("ConfigDefaults.qml"))) {
                finish("Next category ConfigView missing");return;
            }
        }
    } else if(stage==10+3*categoryPages().size()) {
        report["final_general_reset_pointer"]=click("domainosResetAllDefaults");
    } else if(stage==11+3*categoryPages().size()) {
        report["final_general_apply_pointer"]=clickNativeApply();
    } else if(stage==12+3*categoryPages().size()) {
        report["final_general_applied"]=snapshot(children);finish();return;
    }
    if (!finished) { ++stage;QTimer::singleShot(650,defaultsStep); }
}
extern "C" int interceptedExec() asm("_ZN12QApplication4execEv");
extern "C" int interceptedExec()
{
    const auto original=reinterpret_cast<int (*)()>(dlsym(RTLD_NEXT,"_ZN12QApplication4execEv"));
    if(!original || qEnvironmentVariable("IRIX_DOMAINOS_DEFAULTS_TEST")!="1")return original ? original() : 1;
    executionTime.start();
    QTimer::singleShot(1000,defaultsStep);
    QTimer::singleShot(executionDeadlineMilliseconds,[](){finish("Bounded native defaults timeout");});
    return original();
}
