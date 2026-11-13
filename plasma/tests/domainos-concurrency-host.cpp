// SPDX-FileCopyrightText: 2026 IRIX Classic contributors
// SPDX-License-Identifier: GPL-3.0-or-later
// Test-only input/geometry observer in the installed native Plasma host.
#include <QAbstractItemModel>
#include <QAbstractProxyModel>
#include <QConcatenateTablesProxyModel>
#include <QApplication>
#include <QDBusConnection>
#include <QDBusMessage>
#include <QDBusPendingCallWatcher>
#include <QDBusPendingReply>
#include <QElapsedTimer>
#include <QFile>
#include <QJsonArray>
#include <QJsonDocument>
#include <QJsonObject>
#include <QMetaMethod>
#include <QMetaProperty>
#include <QImage>
#include <QWindow>
#include <QSet>
#include <QSignalSpy>
#include <QTest>
#include <QTimer>
#include <dlfcn.h>
#include <time.h>
#include <unistd.h>

using Children=QList<QObject *> (*)(QObject *);
using Map=QPointF (*)(const QObject *,const QObject *,const QPointF &);
using Grab=QImage (*)(QWindow *);
using ForceFocus=void (*)(QObject *);
static QWindow *host=nullptr;
static QObject *panel=nullptr,*clockButton=nullptr,*dateButton=nullptr;
static QObject *instruments=nullptr,*nativeTray=nullptr,*notificationApplet=nullptr;
static QSignalSpy *sensorSpy=nullptr,*attentionSpy=nullptr,*clickedSpy=nullptr,*unreadSpy=nullptr,*addedSpy=nullptr,*replacedSpy=nullptr,*ownedStatusSpy=nullptr;
static QJsonObject checks,baseline,initialState,latency,serverEvidence;
static QJsonArray measurements,historySummaries,historyNotifications,attentionWitnesses;
static qint64 inputStart=0,inputEnd=0,attentionRequestedAt=0;
static int attentionAtInputEnd=-1,attentionBeforeRequest=-1;
static const bool directedAttention=qEnvironmentVariable("IRIX_DOMAINOS_DIRECTED_ATTENTION")=="1";
static const QString ownedSniId="domainos-vf20-native-sni";
static int phase=0,cycle=0,attempts=0,startSensorCount=0,startAttentionCount=0,startSamples=0,startClicks=0;
static bool beforeKeyboardPopup=false;
static bool finishing=false,attentionRegistered=false;
static qint64 monotonicNs() { timespec value{};clock_gettime(CLOCK_MONOTONIC,&value);return qint64(value.tv_sec)*1000000000LL+value.tv_nsec; }

static QObject *find(QObject *root,const QString &name) {
    if(!root)return nullptr;if(root->objectName()==name)return root;
    const auto children=reinterpret_cast<Children>(dlsym(RTLD_DEFAULT,"_ZNK10QQuickItem10childItemsEv"));
    if(children && root->inherits("QQuickItem"))for(auto child:children(root))if(auto result=find(child,name))return result;
    return nullptr;
}
static QObject *variantObject(const QVariant &value) {
    if(auto object=value.value<QObject *>())return object;
    if(QByteArray(value.metaType().name())=="QJSValue") {
        using ToObject=QObject *(*)(const void *);
        const auto toObject=reinterpret_cast<ToObject>(dlsym(RTLD_DEFAULT,"_ZNK8QJSValue9toQObjectEv"));
        if(toObject)return toObject(value.constData());
    }
    return nullptr;
}
static QObject *findNativeNotifications(QObject *start) {
    // Walk only existing host-owned QObject/item/provider edges, without
    // creating a QML observer or model that could initialize the server.
    QList<QObject *> pending{start};QSet<QObject *> seen;
    const auto children=reinterpret_cast<Children>(dlsym(RTLD_DEFAULT,"_ZNK10QQuickItem10childItemsEv"));
    for(int count=0;!pending.isEmpty() && count<10000;++count) {
        auto object=pending.takeFirst();if(!object || seen.contains(object))continue;seen.insert(object);
        if(object->inherits("QQuickItem") && object->metaObject()->indexOfProperty("unreadCount")>=0 && object->metaObject()->indexOfProperty("effectiveStatus")>=0)return object;
        pending.append(object->children());if(object->parent())pending.append(object->parent());
        if(children && object->inherits("QQuickItem"))pending.append(children(object));
        for(const auto name:{"applet","rootItem","contentItem","fullRepresentationItem","compactRepresentationItem","nativeTray","internalSystray","visibleLayout","hiddenLayout","model","sourceModel","systemTrayModel"}) {
            if(auto value=variantObject(object->property(name)))pending.append(value);
        }
    }
    return nullptr;
}
static QObject *existingNativeServer() {
    auto ownerMessage=QDBusMessage::createMethodCall("org.freedesktop.DBus","/org/freedesktop/DBus","org.freedesktop.DBus","GetNameOwner");
    ownerMessage.setArguments({"org.freedesktop.Notifications"});
    auto owner=QDBusConnection::sessionBus().call(ownerMessage);
    if(owner.type()==QDBusMessage::ErrorMessage || owner.arguments().isEmpty())return nullptr;
    auto pidMessage=QDBusMessage::createMethodCall("org.freedesktop.DBus","/org/freedesktop/DBus","org.freedesktop.DBus","GetConnectionUnixProcessID");
    pidMessage.setArguments({owner.arguments().first()});
    auto pid=QDBusConnection::sessionBus().call(pidMessage);
    if(pid.type()==QDBusMessage::ErrorMessage || pid.arguments().isEmpty() || pid.arguments().first().toUInt()!=uint(getpid()))return nullptr;
    serverEvidence["natural_server_owner_before_observer"]=owner.arguments().first().toString();
    serverEvidence["natural_server_pid_before_observer"]=int(pid.arguments().first().toUInt());
    // Access the already initialized singleton only after proving production
    // owns its real service. RTLD_NOLOAD cannot create/load an absent provider;
    // init() is never called by this harness.
    QString libraryPath;
    QFile maps("/proc/self/maps");if(maps.open(QIODevice::ReadOnly))for(const auto line:maps.readAll().split('\n')) {
        const auto fields=line.split(' ');if(!fields.isEmpty() && fields.last().contains("/libnotificationmanager.so.")){libraryPath=QString::fromLocal8Bit(fields.last());break;}
    }
    serverEvidence["already_loaded_native_server_library"]=libraryPath;
    auto library=libraryPath.isEmpty() ? nullptr : dlopen(libraryPath.toLocal8Bit().constData(),RTLD_NOW|RTLD_NOLOAD);
    const auto self=library ? reinterpret_cast<QObject *(*)()>(dlsym(library,"_ZN19NotificationManager6Server4selfEv")) : nullptr;
    auto server=self ? self() : nullptr;if(library)dlclose(library);return server;
}
static void focusClock() {
    const auto force=reinterpret_cast<ForceFocus>(dlsym(RTLD_DEFAULT,"_ZN10QQuickItem16forceActiveFocusEv"));
    if(force)force(clockButton);
}
static QPointF map(QObject *item,QObject *target,const QPointF &point) {
    const auto function=reinterpret_cast<Map>(dlsym(RTLD_DEFAULT,"_ZNK10QQuickItem9mapToItemEPKS_RK7QPointF"));
    return function ? function(item,target,point) : QPointF();
}
static QJsonArray nativeModels() {
    QJsonArray result;QList<QObject *> pending{panel};QSet<QObject *> seen;
    const auto children=reinterpret_cast<Children>(dlsym(RTLD_DEFAULT,"_ZNK10QQuickItem10childItemsEv"));
    for(int count=0;!pending.isEmpty() && count<10000;++count) {
        auto object=pending.takeFirst();if(!object || seen.contains(object))continue;seen.insert(object);
        auto model=qobject_cast<QAbstractItemModel *>(object);const QString type=object->metaObject()->className();
        if(model && (type.contains("StatusNotifier") || type.contains("SystemTray") || type.contains("Notification"))) {
            QJsonArray rows;const auto roles=model->roleNames();
            for(int row=0;row<model->rowCount() && row<20;++row) {
                QJsonObject data;for(auto it=roles.begin();it!=roles.end();++it) {
                    const auto value=model->data(model->index(row,0),it.key());
                    if(value.canConvert<QString>())data[QString::fromLatin1(it.value())]=value.toString();
                }
                rows.append(data);
            }
            QJsonObject properties;
            for(const auto field:{"activeNotificationsCount","expiredNotificationsCount","dismissedNotificationsCount","unreadNotificationsCount","lastRead","showExpired","showDismissed","showJobs","showNotifications","urgencies","blacklistedDesktopEntries","blacklistedNotifyRcNames"}) {
                auto value=model->property(field);if(value.isValid())properties[field]=QJsonValue::fromVariant(value);
            }
            result.append(QJsonObject{{"class",type},{"row_count",model->rowCount()},{"rows",rows},{"properties",properties}});
        }
        if(auto proxy=qobject_cast<QAbstractProxyModel *>(object))pending.append(proxy->sourceModel());
        if(auto concatenate=qobject_cast<QConcatenateTablesProxyModel *>(object))for(auto source:concatenate->sourceModels())pending.append(source);
        pending.append(object->children());if(object->parent())pending.append(object->parent());
        if(children && object->inherits("QQuickItem"))pending.append(children(object));
        for(const auto name:{"applet","rootItem","contentItem","fullRepresentationItem","compactRepresentationItem","nativeTray","internalSystray","visibleLayout","hiddenLayout","model","sourceModel","systemTrayModel"})if(auto value=variantObject(object->property(name)))pending.append(value);
    }
    return result;
}
static QJsonObject snapshot() {
    QVariant result;if(panel)QMetaObject::invokeMethod(panel,"diagnosticSnapshot",Qt::DirectConnection,Q_RETURN_ARG(QVariant,result));
    return QJsonDocument::fromJson(result.toString().toUtf8()).object();
}
static QJsonObject geometry() {
    QJsonObject result;
    for(const auto name:QStringList{"domainosPanel","domainosChassis","domainosInstitutional","domainosClock","domainosDate","domainosGraph","domainosMail","domainosLiveIconbox","domainosRealPager","domainosRealTray","domainosLowerRail","domainosIdentity","domainosApplicationsDrawer","domainosRightIndicator"}) {
        auto item=find(host->property("contentItem").value<QObject *>(),name);if(!item)continue;
        const auto position=map(item,panel,QPointF(0,0));
        result[name]=QJsonObject{{"x",position.x()},{"y",position.y()},{"width",item->property("width").toDouble()},{"height",item->property("height").toDouble()},{"scale",item->property("scale").toDouble()}};
    }
    result["host"]=QJsonObject{{"x",host->x()},{"y",host->y()},{"width",host->width()},{"height",host->height()}};
    return result;
}
static void stable(const QString &where) {
    const auto current=geometry();
    const bool equal=current==baseline;
    const auto name="geometry_stable_"+where;
    checks[name]=equal;
    if(!equal)serverEvidence["geometry_failure_"+where]=current;
}
static QSignalSpy *spy(QObject *object,const QByteArray &prefix) {
    if(!object)return nullptr;
    const auto meta=object->metaObject();
    for(int i=0;i<meta->methodCount();++i) {
        auto method=meta->method(i);
        if(method.methodType()==QMetaMethod::Signal && method.methodSignature().startsWith(prefix))return new QSignalSpy(object,method);
    }
    return nullptr;
}
static bool control(const QString &method,const QVariantList &arguments={}) {
    auto message=QDBusMessage::createMethodCall("org.irixclassic.DomainOSVf20.Control","/Events","org.irixclassic.DomainOSVf20.Events",method);
    message.setArguments(arguments);
    const auto reply=QDBusConnection::sessionBus().call(message,QDBus::Block,3000);
    return reply.type()!=QDBusMessage::ErrorMessage;
}
static void requestOwnedAttention(const QString &status,int sequence) {
    const QString check="request_owned_held_attention_state_"+QString::number(sequence);
    checks[check]=false;
    auto message=QDBusMessage::createMethodCall("org.irixclassic.DomainOSVf20.Control","/Events","org.irixclassic.DomainOSVf20.Events","SetOwnedAttention");
    message.setArguments({status,sequence});
    // The producer concurrently calls this host's real Notify server. Keep
    // the native event loop available rather than synchronously waiting on
    // the producer, and require the actual control reply before accepting
    // the model/delegate witness. This changes only the test transport.
    auto watcher=new QDBusPendingCallWatcher(QDBusConnection::sessionBus().asyncCall(message,2000),qApp);
    QObject::connect(watcher,&QDBusPendingCallWatcher::finished,qApp,[check](QDBusPendingCallWatcher *finished) {
        const QDBusPendingReply<> reply(*finished);checks[check]=!reply.isError();
        if(reply.isError())serverEvidence[check+"_dbus_error"]=reply.error().message();
        finished->deleteLater();
    });
}
static void capture(const QString &name) {
    const auto dir=qEnvironmentVariable("IRIX_DOMAINOS_CONCURRENT_DIR");
    const auto grab=reinterpret_cast<Grab>(dlsym(RTLD_DEFAULT,"_ZN12QQuickWindow10grabWindowEv"));
    checks["capture_"+name]=host && grab && grab(host).save(dir+"/"+name+".png");
}
static void observeHistory() {
    if(!notificationApplet)return;
    serverEvidence["unread"]=notificationApplet->property("unreadCount").toInt();
    if(notificationApplet->property("unreadCount").toInt()>0)checks["native_notification_applet_observed_unread"]=true;
    for(auto object:notificationApplet->findChildren<QObject *>()) {
        auto model=qobject_cast<QAbstractItemModel *>(object);
        if(!model || !QByteArray(object->metaObject()->className()).contains("Notification"))continue;
        const auto roles=model->roleNames();int summaryRole=-1;
        for(auto it=roles.begin();it!=roles.end();++it)if(it.value()=="summary")summaryRole=it.key();
        if(summaryRole<0)continue;
        for(int row=0;row<model->rowCount();++row) {
            const auto index=model->index(row,0);
            const auto summary=model->data(index,summaryRole).toString();
            if(summary.startsWith("DomainOS VF20 ") && !historySummaries.contains(summary))historySummaries.append(summary);
            for(int child=0;child<model->rowCount(index);++child) {
                const auto childSummary=model->data(model->index(child,0,index),summaryRole).toString();
                if(childSummary.startsWith("DomainOS VF20 ") && !historySummaries.contains(childSummary))historySummaries.append(childSummary);
            }
        }
    }
    if(directedAttention && inputStart && !inputEnd)for(const auto &model:nativeModels()) {
        const auto entry=model.toObject();if(!entry["class"].toString().contains("Notification"))continue;
        for(const auto &value:entry["rows"].toArray()) {
            const auto row=value.toObject();const auto summary=row["summary"].toString();
            if(!summary.startsWith("DomainOS VF20 ") || row["desktopEntry"].toString()!="org.irixclassic.DomainOSVf20")continue;
            const int id=row["notificationId"].toString().toInt();if(id<=0)continue;
            bool seen=false;for(const auto &previous:historyNotifications)if(previous.toObject()["notification_id"].toInt()==id && previous.toObject()["summary"].toString()==summary)seen=true;
            if(!seen)historyNotifications.append(QJsonObject{{"notification_id",id},{"desktop_entry",row["desktopEntry"]},{"summary",summary},{"cycle",cycle},{"observed_monotonic_ns",double(monotonicNs())},{"native_model_class",entry["class"]}});
        }
    }
}
static QObject *ownedDelegate() {
    QList<QObject *> pending{nativeTray};QSet<QObject *> seen;
    const auto children=reinterpret_cast<Children>(dlsym(RTLD_DEFAULT,"_ZNK10QQuickItem10childItemsEv"));
    while(!pending.isEmpty() && seen.size()<10000) {
        auto object=pending.takeFirst();if(!object || seen.contains(object))continue;seen.insert(object);
        if(object->inherits("QQuickItem") && object->property("itemId").toString()==ownedSniId)return object;
        pending.append(object->children());if(children && object->inherits("QQuickItem"))pending.append(children(object));
    }
    return nullptr;
}
static QJsonObject ownedAttentionWitness(int expectedStatus) {
    QJsonObject result;bool modelConfirmed=false,adapterConfirmed=false;
    for(const auto &value:nativeModels()) {
        const auto model=value.toObject();if(model["class"].toString()!="StatusNotifierModel")continue;
        for(const auto &entry:model["rows"].toArray()) {
            const auto row=entry.toObject();if(row["Id"].toString()!=ownedSniId)continue;
            result["native_model_row"]=row;modelConfirmed=row["Status"].toString().toInt()==expectedStatus;
        }
    }
    const auto tray=snapshot()["tray"].toObject();result["tray_snapshot"]=tray;
    for(const auto &value:tray["types"].toArray()) {
        const auto entry=value.toObject();if(entry["id"].toString()==ownedSniId && entry["status"].toInt()==expectedStatus)adapterConfirmed=true;
    }
    auto item=ownedDelegate();result["native_delegate_present"]=item!=nullptr;
    if(item) {
        result["native_delegate_class"]=QString(item->metaObject()->className());
        result["native_delegate_id"]=item->property("itemId").toString();
        result["native_delegate_status"]=item->property("status").toInt();
        if(!ownedStatusSpy) {
            const int index=item->metaObject()->indexOfProperty("status");
            if(index>=0 && item->metaObject()->property(index).hasNotifySignal())ownedStatusSpy=new QSignalSpy(item,item->metaObject()->property(index).notifySignal());
        }
        result["native_delegate_status_signals"]=ownedStatusSpy ? ownedStatusSpy->count() : -1;
    }
    result["model_and_delegate_confirmed"]=modelConfirmed && adapterConfirmed && item && item->property("status").toInt()==expectedStatus && tray["visible"].toArray().contains(ownedSniId);
    result["pointer_still_pressed"]=clockButton->property("pressed").toBool();
    return result;
}
static void finish(const QString &error={}) {
    if(finishing)return;finishing=true;
    if(!error.isEmpty()){checks["native_scenario_completed"]=false;serverEvidence["failure"]=error;}
    control("StopEvents");
    QTimer::singleShot(400,[](){
        if(panel)stable("after_events");serverEvidence["native_models_after_events"]=nativeModels();
        capture("AFTER-NATIVE-EVENTS");
        QJsonObject report{{"checks",checks},{"initial",initialState},{"final",snapshot()},{"geometry",baseline},
            {"measurements",measurements},{"server",serverEvidence},{"history_test_summaries",historySummaries},
            {"history_test_notifications",historyNotifications},{"directed_attention_witnesses",attentionWitnesses},
            {"input_interval",QJsonObject{{"start_monotonic_ns",double(inputStart)},{"end_monotonic_ns",double(inputEnd)},{"attention_signals_at_end",attentionAtInputEnd}}},
            {"native_sensor_value_signals",sensorSpy ? sensorSpy->count()-startSensorCount : -1},
            {"native_attention_signals",attentionSpy ? attentionSpy->count()-startAttentionCount : -1},
            {"native_notification_added_signals",addedSpy ? addedSpy->count() : -1},
            {"native_notification_replaced_signals",replacedSpy ? replacedSpy->count() : -1},
            {"native_unread_signals",unreadSpy ? unreadSpy->count() : -1},
            {"host_pid",int(getpid())},{"host_executable",QFile::symLinkTarget("/proc/self/exe")}};
        QJsonObject environment;for(const auto key:QStringList{"HOME","XDG_CONFIG_HOME","XDG_DATA_HOME","XDG_RUNTIME_DIR","DISPLAY","DBUS_SESSION_BUS_ADDRESS","DBUS_SYSTEM_BUS_ADDRESS","PULSE_SERVER"})environment[key]=qEnvironmentVariable(key.toLocal8Bit().constData());
        report["host_namespace"]=environment;
        QFile file(qEnvironmentVariable("IRIX_DOMAINOS_CONCURRENT_REPORT"));if(file.open(QIODevice::WriteOnly))file.write(QJsonDocument(report).toJson());
        QCoreApplication::quit();
    });
}
static QPoint clockPoint(){return map(clockButton,host->property("contentItem").value<QObject *>(),QPointF(clockButton->property("width").toDouble()/2,clockButton->property("height").toDouble()/2)).toPoint();}
static void tick() {
    if(++attempts>120){finish("Bounded native observation timeout");return;}
    if(!panel) {
        for(auto window:QGuiApplication::allWindows()) {
            if(auto found=find(window->property("contentItem").value<QObject *>(),"domainosPanel")){host=window;panel=found;break;}
        }
        if(!panel){QTimer::singleShot(100,tick);return;}
        host->setFlags(Qt::Tool|Qt::FramelessWindowHint);host->setGeometry(80,550,971,109);host->show();
        clockButton=find(host->property("contentItem").value<QObject *>(),"domainosClock");dateButton=find(host->property("contentItem").value<QObject *>(),"domainosDate");
        instruments=panel->findChild<QObject *>("domainosLiveInstruments");
        nativeTray=find(host->property("contentItem").value<QObject *>(),"domainosRealTray");
        auto settings=panel->property("settings").value<QObject *>();
        if(!clockButton || !dateButton || !instruments || !nativeTray || !settings){finish("Production controls/providers absent");return;}
        checks["private_instance_cpu_metric_selected"]=settings->setProperty("instrumentMetric","cpu");
        checks["only_owned_sni_explicitly_shown_in_private_instance"]=settings->setProperty("trayVisibleItems",QStringList{"domainos-vf20-native-sni"});
        sensorSpy=spy(panel->findChild<QObject *>("domainosPrimarySensor"),"valueChanged(");
        attentionSpy=spy(nativeTray,"attentionCountChanged(");clickedSpy=spy(clockButton,"clicked(");
    }
    const auto current=snapshot();
    if(phase==0) {
        const auto sensors=current["sensors"].toObject();
        if(nativeTray->property("available").toBool() && !attentionRegistered) {
            checks["producer_registered_after_native_tray_ready"]=control("RegisterAttention");attentionRegistered=true;
        }
        notificationApplet=findNativeNotifications(panel);
        serverEvidence["readiness_last"]=QJsonObject{{"time",current["timeAvailable"]},{"cpu",sensors["available"]},{"samples",sensors["primarySampleTimes"].toArray().size()},
            {"notification_applet",notificationApplet!=nullptr},{"tray",current["tray"]}};
        if(!current["timeAvailable"].toBool() || sensors["metric"].toString()!="cpu" || !sensors["available"].toBool() || sensors["primarySampleTimes"].toArray().size()<2 || !nativeTray->property("available").toBool()
                || !notificationApplet) {QTimer::singleShot(200,tick);return;}
        checks["exact_production_main_functional_composition"]=current["phase"].toString()=="functional-integration";
        checks["genuine_native_time_and_cpu_sensors_active"]=current["timeAvailable"].toBool() && sensors["available"].toBool();
        checks["genuine_native_sensor_signal_observer_attached"]=sensorSpy && sensorSpy->isValid();
        checks["genuine_native_tray_attention_observer_attached"]=attentionSpy && attentionSpy->isValid();
        checks["native_notification_applet_present"]=notificationApplet!=nullptr;
        const auto unreadIndex=notificationApplet->metaObject()->indexOfProperty("unreadCount");
        auto unreadProperty=notificationApplet->metaObject()->property(unreadIndex);
        serverEvidence["native_notification_applet_class"]=QString(notificationApplet->metaObject()->className());
        serverEvidence["native_unread_notify_signature"]=QString::fromLatin1(unreadProperty.notifySignal().methodSignature());
        unreadSpy=unreadProperty.hasNotifySignal() ? new QSignalSpy(notificationApplet,unreadProperty.notifySignal()) : nullptr;
        auto server=existingNativeServer();
        serverEvidence["native_server_object"]=server ? QString(server->metaObject()->className()) : QString();
        serverEvidence["native_server_valid"]=server && server->property("valid").toBool();
        addedSpy=spy(server,"notificationAdded(");replacedSpy=spy(server,"notificationReplaced(");
        serverEvidence["native_models_before_events"]=nativeModels();
        initialState=current;baseline=geometry();startSamples=sensors["primarySampleTimes"].toArray().size();
        startSensorCount=sensorSpy ? sensorSpy->count() : 0;startAttentionCount=attentionSpy ? attentionSpy->count() : 0;
        checks["fourteen_modules_and_host_geometry_recorded"]=baseline.size()==15;
        checks["real_installed_native_plasma_host"]=QFile::symLinkTarget("/proc/self/exe")=="/usr/bin/plasmawindowed";
        capture("BEFORE-NATIVE-EVENTS");checks["private_native_event_producer_started"]=control("BeginEvents");phase=1;
    } else if(phase==1) {
        QMetaObject::invokeMethod(instruments,"closePopups",Qt::DirectConnection);
        QTest::mouseMove(host,clockPoint(),0);
        startClicks=clickedSpy ? clickedSpy->count() : -1;
        const auto pressedAt=monotonicNs();if(!inputStart)inputStart=pressedAt;
        QElapsedTimer timer;timer.start();QTest::mousePress(host,Qt::LeftButton,Qt::NoModifier,clockPoint(),0);
        latency=QJsonObject{{"cycle",cycle},{"pointer_press_us",double(timer.nsecsElapsed()/1000)},{"pointer_press_monotonic_ns",double(pressedAt)}};
        checks["pointer_press_relief_same_dispatch_"+QString::number(cycle)]=clockButton->property("pressed").toBool() && clockButton->property("pressOffset").toInt()==2;
        checks["pointer_press_has_no_action_before_release_"+QString::number(cycle)]=clickedSpy && clickedSpy->count()==startClicks && !instruments->property("clockPopupVisible").toBool();
        stable("press_"+QString::number(cycle));
        if(directedAttention && cycle<6) {
            attentionRequestedAt=monotonicNs();attentionBeforeRequest=attentionSpy ? attentionSpy->count() : -1;
            requestOwnedAttention(cycle%2 ? QString("Active") : QString("NeedsAttention"),cycle);
        }
        if(cycle==1)capture("PRESSED-DURING-NATIVE-EVENTS");phase=2;
    } else if(phase==2) {
        if(directedAttention && cycle<6) {
            auto witness=ownedAttentionWitness(cycle%2 ? 2 : 3);
            const bool consumed=checks["request_owned_held_attention_state_"+QString::number(cycle)].toBool() && witness["model_and_delegate_confirmed"].toBool() && witness["pointer_still_pressed"].toBool() && attentionSpy && attentionSpy->count()>attentionBeforeRequest;
            if(!consumed && monotonicNs()-attentionRequestedAt<2000000000LL){QTimer::singleShot(50,tick);return;}
            checks["owned_attention_state_consumed_during_held_pointer_"+QString::number(cycle)]=consumed;
            witness["id"]=ownedSniId;witness["sequence"]=cycle;witness["requested_status"]=cycle%2 ? "Active" : "NeedsAttention";
            witness["requested_monotonic_ns"]=double(attentionRequestedAt);witness["observed_monotonic_ns"]=double(monotonicNs());
            witness["attention_signals_before_request"]=attentionBeforeRequest;witness["attention_signals_at_observation"]=attentionSpy ? attentionSpy->count() : -1;
            attentionWitnesses.append(witness);
            if(!consumed){serverEvidence["directed_attention_timeout"]=witness;finish("Owned attention state was not consumed by native model/delegate during held input within 2000 ms");return;}
        }
        checks["held_relief_survives_native_updates_"+QString::number(cycle)]=clockButton->property("pressed").toBool() && clockButton->property("pressOffset").toInt()==2;
        stable("held_"+QString::number(cycle));
        QElapsedTimer timer;timer.start();QTest::mouseRelease(host,Qt::LeftButton,Qt::NoModifier,clockPoint(),0);
        latency["pointer_release_monotonic_ns"]=double(monotonicNs());
        latency["pointer_release_us"]=double(timer.nsecsElapsed()/1000);
        checks["pointer_release_action_same_dispatch_"+QString::number(cycle)]=!clockButton->property("pressed").toBool() && clockButton->property("pressOffset").toInt()==0 && clickedSpy && clickedSpy->count()==startClicks+1 && instruments->property("clockPopupVisible").toBool();
        stable("release_"+QString::number(cycle));host->requestActivate();focusClock();phase=3;
    } else if(phase==3) {
        if(!host->isActive() || !clockButton->property("activeFocus").toBool()){QTimer::singleShot(50,tick);return;}
        beforeKeyboardPopup=instruments->property("clockPopupVisible").toBool();startClicks=clickedSpy ? clickedSpy->count() : -1;
        QElapsedTimer timer;timer.start();QTest::keyPress(host,Qt::Key_Space,Qt::NoModifier,0);
        latency["keyboard_press_monotonic_ns"]=double(monotonicNs());
        latency["keyboard_press_us"]=double(timer.nsecsElapsed()/1000);
        checks["native_keyboard_focus_and_press_same_dispatch_"+QString::number(cycle)]=clockButton->property("activeFocus").toBool() && clockButton->property("pressed").toBool() && clockButton->property("pressedKey").toInt()==Qt::Key_Space && clockButton->property("pressOffset").toInt()==2;
        checks["keyboard_press_does_not_act_before_release_"+QString::number(cycle)]=clickedSpy && clickedSpy->count()==startClicks && instruments->property("clockPopupVisible").toBool()==beforeKeyboardPopup;
        stable("keyboard_press_"+QString::number(cycle));phase=4;
    } else if(phase==4) {
        QElapsedTimer timer;timer.start();QTest::keyRelease(host,Qt::Key_Space,Qt::NoModifier,0);
        latency["keyboard_release_monotonic_ns"]=double(monotonicNs());
        if(cycle==11){inputEnd=qint64(latency["keyboard_release_monotonic_ns"].toDouble());attentionAtInputEnd=attentionSpy ? attentionSpy->count()-startAttentionCount : -1;}
        latency["keyboard_release_us"]=double(timer.nsecsElapsed()/1000);
        checks["native_keyboard_release_action_same_dispatch_"+QString::number(cycle)]=!clockButton->property("pressed").toBool() && clockButton->property("pressOffset").toInt()==0 && clickedSpy && clickedSpy->count()==startClicks+1 && instruments->property("clockPopupVisible").toBool()!=beforeKeyboardPopup;
        stable("keyboard_release_"+QString::number(cycle));observeHistory();measurements.append(latency);
        QMetaObject::invokeMethod(instruments,"closePopups",Qt::DirectConnection);
        if(++cycle<12)phase=1;else phase=5;
    } else if(phase==5) {
        const auto samples=current["sensors"].toObject()["primarySampleTimes"].toArray();
        checks["native_sensor_samples_continue_during_input"]=samples.size()>=startSamples+2 && sensorSpy && sensorSpy->count()-startSensorCount>=2;
        checks["native_attention_updates_arrive_during_input"]=attentionSpy && attentionSpy->count()-startAttentionCount>=6;
        if(directedAttention)checks["at_least_six_attention_signals_before_last_input_release"]=attentionAtInputEnd>=6;
        checks["native_notification_server_added_signals_observed"]=addedSpy && addedSpy->isValid() && addedSpy->count()>=2;
        checks["native_notification_server_replaced_signals_observed"]=replacedSpy && replacedSpy->isValid() && replacedSpy->count()>=2;
        QJsonArray payloads;
        if(addedSpy)for(const auto &arguments:*addedSpy)for(const auto &value:arguments) {
            QJsonObject payload;const auto meta=value.metaType().metaObject();
            if(meta)for(int index=0;index<meta->propertyCount();++index) {
                const auto property=meta->property(index);const auto field=property.readOnGadget(value.constData());
                if(field.canConvert<QString>())payload[property.name()]=field.toString();
            }
            payloads.append(payload);
        }
        serverEvidence["native_notification_added_payloads"]=payloads;
        serverEvidence["native_models_while_events_active"]=nativeModels();
        observeHistory();checks["test_owned_summary_observed_in_native_history_model"]=!historySummaries.isEmpty();
        checks["native_notification_unread_updates_observed"]=unreadSpy && unreadSpy->isValid() && unreadSpy->count()>0;
        // Tab reaches the next production control, without invoking it.
        host->requestActivate();focusClock();QTest::keyClick(host,Qt::Key_Tab,Qt::NoModifier,0);
        checks["tab_moves_focus_to_next_production_control"]=dateButton->property("activeFocus").toBool();
        stable("after_concurrent_input");checks["native_scenario_completed"]=true;
        checks["stop_only_owned_notification_replacements"]=control("StopNotificationReplacements");
        phase=6;QTimer::singleShot(2800,tick);return;
    } else if(phase==6) {
        observeHistory();serverEvidence["native_models_after_natural_expiration_before_close"]=nativeModels();
        serverEvidence["native_unread_after_natural_expiration"]=notificationApplet->property("unreadCount").toInt();
        checks["native_notification_unread_updates_observed"]=unreadSpy && unreadSpy->isValid() && unreadSpy->count()>0;
        stable("after_natural_expiration");finish();return;
    }
    QTimer::singleShot(phase==2 ? 180 : 120,tick);
}
extern "C" int interceptedExec() asm("_ZN12QApplication4execEv");
extern "C" int interceptedExec() {
    const auto original=reinterpret_cast<int (*)()>(dlsym(RTLD_NEXT,"_ZN12QApplication4execEv"));if(!original)return 2;
    QTimer::singleShot(1500,tick);return original();
}
