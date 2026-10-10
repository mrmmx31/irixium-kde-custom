// SPDX-FileCopyrightText: 2026 IRIX Classic contributors
// SPDX-License-Identifier: GPL-3.0-or-later
// Native ConfigView draft/Discard/Apply and actual provider placement privately.
#include <QApplication>
#include <QAction>
#include <QFile>
#include <QImage>
#include <QJsonArray>
#include <QJsonDocument>
#include <QJsonObject>
#include <QPointer>
#include <QRectF>
#include <QTest>
#include <QTimer>
#include <QUrl>
#include <QWindow>
#include <dlfcn.h>

using Children=QList<QObject *>(*)(QObject *);
using NativeApplet=QObject *(*)(QObject *);
using Action=QObject *(*)(QObject *,const QString &);
static Children children=nullptr;
static NativeApplet nativeApplet=nullptr;
static Action action=nullptr;
static QObject *host=nullptr,*panel=nullptr,*settings=nullptr,*tray=nullptr,*bridge=nullptr;
static QObject *secondItem=nullptr,*secondSettings=nullptr,*configRoot=nullptr;
static QPointer<QWindow> configWindow;
static QJsonObject report,checks,initialSettings,draft;
static const QString absent="domainos-fixture-unavailable-preserved";
static const QStringList initialOrder{absent,"domainos-fixture-sni-0","domainos-fixture-sni-1"};
static int stage=0,attempts=0;

static QObject *find(QObject *item,const QString &name) {
    if(!item)return nullptr;
    if(item->objectName()==name)return item;
    if(item->inherits("QQuickItem"))for(auto child:children(item))if(auto hit=find(child,name))return hit;
    return nullptr;
}
static QJsonObject jsonProperty(QObject *item,const char *name) {
    return item ? QJsonDocument::fromJson(item->property(name).toString().toUtf8()).object():QJsonObject{};
}
static QJsonArray items() {
    return bridge ? QJsonDocument::fromJson(bridge->property("itemsJson").toString().toUtf8()).array():QJsonArray{};
}
static QJsonArray ids(const QJsonArray &entries,bool visibleOnly=false) {
    QJsonArray result;
    for(const auto &value:entries)if(!visibleOnly||!value.toObject()["hidden"].toBool())result.append(value.toObject()["id"]);
    return result;
}
static QJsonObject saved(QObject *map) {
    QJsonObject result;
    for(const auto name:{"trayOrder","trayVisibleItems","trayHiddenItems","trayIncludeHiddenInOverflow","trayOverflowMode","clockShowDate","barHintsEnabled"})
        result[name]=map ? QJsonValue::fromVariant(map->property(name)):QJsonValue{};
    return result;
}
static void gate(const QString &name,bool passed) { checks[name]=passed; }
static void finish(const QString &failure={}) {
    if(!failure.isEmpty())report["failure"]=failure;
    report["checks"]=checks;report["qtVersion"]=qVersion();report["hostExecutable"]=QCoreApplication::applicationFilePath();
    QFile file(qEnvironmentVariable("IRIX_DOMAINOS_TRAY_REPORT"));
    if(file.open(QIODevice::WriteOnly))file.write(QJsonDocument(report).toJson());
    QCoreApplication::quit();
}
static bool capture(QWindow *window,const QString &name) {
    const auto grab=reinterpret_cast<QImage(*)(QWindow*)>(dlsym(RTLD_DEFAULT,"_ZN12QQuickWindow10grabWindowEv"));
    return window&&grab&&grab(window).save(qEnvironmentVariable("IRIX_DOMAINOS_TRAY_DIR")+"/"+name+".png");
}
static bool pointer(QObject *item,QWindow *window) {
    const auto map=reinterpret_cast<QPointF(*)(QObject*,const QPointF&)>(dlsym(RTLD_DEFAULT,"_ZNK10QQuickItem10mapToSceneERK7QPointF"));
    if(!item||!window||!map||!item->property("enabled").toBool()||!item->property("visible").toBool())return false;
    const auto point=map(item,QPointF(item->property("width").toDouble()/2,item->property("height").toDouble()/2)).toPoint();
    if(!QRect(QPoint{},window->size()).contains(point))return false;
    window->requestActivate();QTest::mouseMove(window,point);QTest::mouseClick(window,Qt::LeftButton,Qt::NoModifier,point);
    return true;
}
static bool click(const QString &name) {
    for(auto window:QGuiApplication::allWindows())if(window->isVisible())if(auto item=find(window->property("contentItem").value<QObject*>(),name))return pointer(item,window);
    return false;
}
static bool clickTray(const QString &name) {
    // The production panel retains a hidden static design with the same button
    // names. Target its live native adapter, not the unrelated hidden preview.
    auto item=find(tray,name);
    for(auto window:QGuiApplication::allWindows())if(window->isVisible()&&find(window->property("contentItem").value<QObject*>(),"domainosRealTray")==tray)return pointer(item,window);
    return false;
}
static QObject *button(QObject *item,const QString &wanted) {
    if(!item)return nullptr;
    const auto text=item->property("text").toString().remove('&');
    if(item->inherits("QQuickAbstractButton")&&item->property("visible").toBool()&&item->property("enabled").toBool()&&text==wanted)return item;
    if(item->inherits("QQuickItem"))for(auto child:children(item))if(auto hit=button(child,wanted))return hit;
    return nullptr;
}
static bool command(const QString &text) {
    for(auto window:QGuiApplication::allWindows())if(window->isVisible())if(auto item=button(window->property("contentItem").value<QObject*>(),text))return pointer(item,window);
    return false;
}
static bool openConfig() {
    auto configure=qobject_cast<QAction*>(action(nativeApplet(host),"configure"));
    if(configure)configure->trigger();
    return configure;
}
static bool openCategory() {
    const auto rootObject=reinterpret_cast<QObject*(*)(QObject*)>(dlsym(RTLD_DEFAULT,"_ZN11PlasmaQuick10ConfigView10rootObjectEv"));
    if(!rootObject)return false;
    for(auto window:QGuiApplication::allWindows())if(window->inherits("PlasmaQuick::ConfigView")&&window->isVisible()) {
        configWindow=window;configRoot=rootObject(window);
        const QVariant category=QVariantMap{{"name","Bandeja e notificações"},{"source",QUrl::fromLocalFile(qEnvironmentVariable("IRIX_DOMAINOS_ORDER_PAGE"))}};
        return configRoot&&QMetaObject::invokeMethod(configRoot,"open",Qt::DirectConnection,Q_ARG(QVariant,category));
    }
    return false;
}
static bool createSecond() {
    const auto self=reinterpret_cast<QObject*(*)()>(dlsym(RTLD_DEFAULT,"_ZN6Plasma12PluginLoader4selfEv"));
    const auto load=reinterpret_cast<QObject*(*)(QObject*,const QString&,uint,const QVariantList&)>(dlsym(RTLD_DEFAULT,"_ZN6Plasma12PluginLoader10loadAppletERK7QStringjRK5QListI8QVariantE"));
    const auto containment=reinterpret_cast<QObject*(*)(QObject*)>(dlsym(RTLD_DEFAULT,"_ZNK6Plasma6Applet11containmentEv"));
    const auto add=reinterpret_cast<void(*)(QObject*,QObject*,const QRectF&)>(dlsym(RTLD_DEFAULT,"_ZN6Plasma11Containment9addAppletEPNS_6AppletERK6QRectF"));
    const auto item=reinterpret_cast<QObject*(*)(QObject*)>(dlsym(RTLD_DEFAULT,"_ZN11PlasmaQuick15AppletQuickItem13itemForAppletEPN6Plasma6AppletE"));
    const auto parent=reinterpret_cast<void(*)(QObject*,QObject*)>(dlsym(RTLD_DEFAULT,"_ZN10QQuickItem13setParentItemEPS_"));
    if(!self||!load||!containment||!add||!item||!parent)return false;
    auto owner=containment(nativeApplet(host));auto applet=load(self(),"org.irixclassic.domainos.panel",101,{});
    if(!owner||!applet)return false;
    add(owner,applet,QRectF(2000,0,600,109));secondItem=item(applet);if(!secondItem)return false;
    for(auto window:QGuiApplication::allWindows())if(window->isVisible()&&!window->inherits("PlasmaQuick::ConfigView")) {
        parent(secondItem,window->property("contentItem").value<QObject*>());secondItem->setProperty("x",2000);secondItem->setProperty("width",600);secondItem->setProperty("height",109);return true;
    }
    return false;
}
static QObject *nativeProvider(QObject *item) {
    if(!item)return nullptr;
    if(item->property("itemId").isValid())return item;
    if(item->inherits("QQuickItem"))for(auto child:children(item))if(auto hit=nativeProvider(child))return hit;
    return nullptr;
}
static QJsonArray slotIds(const QString &prefix,int count) {
    QJsonArray result;
    for(int index=0;index<count;++index) {
        QObject *slot=nullptr;
        for(auto window:QGuiApplication::allWindows())if(window->isVisible())if((slot=find(window->property("contentItem").value<QObject*>(),prefix+QString::number(index))))break;
        auto item=nativeProvider(slot);result.append(item ? item->property("itemId").toString():QString{});
    }
    return result;
}
static QJsonArray slice(const QJsonArray &values,int first,int count=-1) {
    QJsonArray result;for(int i=first;i<values.size()&&(count<0||i<first+count);++i)result.append(values[i]);return result;
}
static void step() {
    if(stage==0) {
        for(auto window:QGuiApplication::allWindows()) {
            auto root=window->property("contentItem").value<QObject*>();
            if(!host)host=find(root,"domainosPanelApplet");if(!panel)panel=find(root,"domainosPanel");if(!tray)tray=find(root,"domainosRealTray");
        }
        if(!host||!panel||!tray){if(++attempts<20){QTimer::singleShot(150,step);return;}finish("Production panel unavailable");return;}
        settings=panel->property("settings").value<QObject*>();bridge=action(nativeApplet(host),"domainos-tray-items");
        if(items().size()<9){if(++attempts<30){QTimer::singleShot(150,step);return;}finish("Native tray has fewer than nine providers");return;}
        gate("native_production_root_and_bridge",settings&&bridge);report["appletId"]=nativeApplet(host)->property("id").toInt();
        QStringList visible{"org.kde.plasma.networkmanagement","org.kde.plasma.volume","org.kde.plasma.bluetooth","org.kde.plasma.notifications"};
        for(int i=0;i<8;++i)visible.append("domainos-fixture-sni-"+QString::number(i));
        settings->setProperty("trayVisibleItems",visible);settings->setProperty("trayHiddenItems",QStringList{"domainos-fixture-sni-8"});settings->setProperty("trayOrder",initialOrder);
        settings->setProperty("trayIncludeHiddenInOverflow",false);settings->setProperty("trayOverflowMode","continuation");
        gate("second_native_instance_created",createSecond());
    } else if(stage==1) {
        auto other=find(secondItem,"domainosPanel");secondSettings=other ? other->property("settings").value<QObject*>():nullptr;
        gate("second_instance_has_distinct_configuration",secondSettings&&secondSettings!=settings&&nativeApplet(secondItem)->property("id").toInt()==101);
        if(secondSettings)secondSettings->setProperty("trayOrder",QStringList{"domainos-fixture-sni-7"});
        initialSettings=saved(settings);report["savedInitial"]=initialSettings;report["otherInitial"]=saved(secondSettings);report["itemsInitial"]=items();
        gate("native_config_requested",openConfig());
    } else if(stage==2)gate("native_tray_category_opened",openCategory());
    else if(stage==3) {
        auto page=find(configRoot,"domainosTrayConfigPage");if(!page){finish("Current production ConfigTray did not load");return;}
        report["draftInitial"]=jsonProperty(page,"draftStateJson");
        const auto rows=QJsonDocument::fromJson(page->property("orderedItemsJson").toString().toUtf8()).array();report["rowsInitial"]=rows;
        gate("native_titles_and_missing_id_visible",rows.size()>=10&&rows[0].toObject()["id"].toString()==absent&&!rows[0].toObject()["available"].toBool()
            &&rows[2].toObject()["title"].toString()=="Native DomainOS fixture 1"&&rows[2].toObject()["available"].toBool());
        auto advanced=find(page,"domainosTrayAdvancedToggle"),fields=find(page,"domainosTrayAdvancedFields");
        gate("raw_id_fields_collapsed_by_default",advanced&&fields&&!advanced->property("checked").toBool()&&!fields->property("visible").toBool());
        auto first=find(page,"domainosTrayMoveUp_"+absent),last=find(page,"domainosTrayMoveDown_"+rows.last().toObject()["id"].toString());
        gate("movement_limits_disabled",first&&last&&!first->property("enabled").toBool()&&!last->property("enabled").toBool());
        gate("initial_configuration_capture",capture(configWindow,"ORDER-INITIAL"));
        gate("draft_first_up_pointer",click("domainosTrayMoveUp_domainos-fixture-sni-1"));
    } else if(stage==4)gate("draft_second_up_pointer",click("domainosTrayMoveUp_domainos-fixture-sni-1"));
    else if(stage==5) {
        auto page=find(configRoot,"domainosTrayConfigPage");draft=jsonProperty(page,"draftStateJson");report["draftBeforeDiscard"]=draft;
        const auto order=draft["order"].toArray();gate("pointer_reorders_native_member_and_preserves_absent",order.size()>=10&&order[0].toString()=="domainos-fixture-sni-1"&&order[1].toString()==absent&&order[2].toString()=="domainos-fixture-sni-0");
        gate("order_edit_is_staged",saved(settings)==initialSettings);gate("other_fields_unchanged_in_draft",draft["hidden"]==initialSettings["trayHiddenItems"]&&draft["visible"]==initialSettings["trayVisibleItems"]&&draft["includeHidden"]==initialSettings["trayIncludeHiddenInOverflow"]&&draft["overflowMode"]==initialSettings["trayOverflowMode"]);
        gate("draft_configuration_capture",capture(configWindow,"ORDER-DRAFT"));gate("native_cancel_pointer",command("Cancel"));
    } else if(stage==6)gate("native_discard_pointer",command("Discard"));
    else if(stage==7) {
        gate("discard_closes_native_dialog",!configWindow||!configWindow->isVisible());gate("discard_preserves_saved_order_and_other_fields",saved(settings)==initialSettings);
        gate("native_config_reopen_requested",openConfig());
    } else if(stage==8)gate("native_tray_category_reopened",openCategory());
    else if(stage==9) {
        auto page=find(configRoot,"domainosTrayConfigPage");auto reopened=jsonProperty(page,"draftStateJson");report["draftAfterDiscard"]=reopened;
        gate("reopen_uses_preexisting_order",reopened["order"].toArray()==QJsonArray::fromStringList(initialOrder));
        gate("reopened_configuration_capture",capture(configWindow,"ORDER-DISCARDED"));gate("apply_first_up_pointer",click("domainosTrayMoveUp_domainos-fixture-sni-1"));
    } else if(stage==10)gate("apply_second_up_pointer",click("domainosTrayMoveUp_domainos-fixture-sni-1"));
    else if(stage==11) {
        draft=jsonProperty(find(configRoot,"domainosTrayConfigPage"),"draftStateJson");report["draftBeforeApply"]=draft;
        gate("second_edit_still_staged",saved(settings)==initialSettings);gate("native_apply_pointer",command("Apply"));
    } else if(stage==12) {
        const auto after=saved(settings);report["savedAfterApply"]=after;report["otherAfterApply"]=saved(secondSettings);report["itemsAfterApply"]=items();
        gate("apply_commits_complete_native_order",after["trayOrder"]==draft["order"]&&after["trayOrder"].toArray().contains(absent));
        auto withoutOrder=after,beforeWithout=initialSettings;withoutOrder.remove("trayOrder");beforeWithout.remove("trayOrder");gate("apply_preserves_visibility_and_other_fields",withoutOrder==beforeWithout);
        gate("other_native_instance_unchanged",saved(secondSettings)==report["otherInitial"].toObject());
        const auto nativeOrder=ids(items());auto expected=draft["order"].toArray();QJsonArray filtered;for(const auto &id:expected)if(id.toString()!=absent)filtered.append(id);
        gate("present_backend_receives_requested_order",nativeOrder==filtered&&!nativeOrder.contains(absent));
        const auto visible=ids(items(),true);const auto actual=slotIds("domainosTraySlot_",6);report["visibleAfterApply"]=visible;report["actualSixSlots"]=actual;
        gate("six_real_native_slots_follow_order",visible.size()>6&&actual==slice(visible,0,6));
        gate("applied_configuration_capture",capture(configWindow,"ORDER-APPLIED"));gate("native_ok_pointer",command("OK"));
    } else if(stage==13)gate("real_overflow_button_pointer",clickTray("domainosTrayNext"));
    else {
        const auto visible=ids(items(),true);const auto actual=slotIds("domainosTrayOverflowSlot_",visible.size()-6);report["actualOverflowSlots"]=actual;
        gate("real_overflow_preserves_remaining_order",actual==slice(visible,6));
        gate("hidden_native_member_stays_hidden",!visible.contains("domainos-fixture-sni-8")&&ids(items()).contains("domainos-fixture-sni-8"));
        bool captured=false;for(auto window:QGuiApplication::allWindows())if(window->isVisible()&&find(window->property("contentItem").value<QObject*>(),"domainosPanel")){captured=capture(window,"ORDER-BACKEND");break;}
        gate("native_backend_capture",captured);finish();return;
    }
    ++stage;QTimer::singleShot(stage==7||stage==13 ? 1000:650,step);
}
extern "C" int interceptedExec() asm("_ZN12QApplication4execEv");
extern "C" int interceptedExec() {
    const auto original=reinterpret_cast<int(*)()>(dlsym(RTLD_NEXT,"_ZN12QApplication4execEv"));
    if(qEnvironmentVariable("IRIX_DOMAINOS_TRAY_TEST")!="1")return original ? original():1;
    children=reinterpret_cast<Children>(dlsym(RTLD_DEFAULT,"_ZNK10QQuickItem10childItemsEv"));
    nativeApplet=reinterpret_cast<NativeApplet>(dlsym(RTLD_DEFAULT,"_ZNK11PlasmaQuick15AppletQuickItem6appletEv"));
    action=reinterpret_cast<Action>(dlsym(RTLD_DEFAULT,"_ZNK6Plasma6Applet14internalActionERK7QString"));
    if(!original||!children||!nativeApplet||!action)return 1;
    QTimer::singleShot(1700,step);QTimer::singleShot(24000,[](){finish("Bounded native order timeout");});return original();
}
