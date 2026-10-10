// SPDX-License-Identifier: GPL-3.0-or-later
// Real Unity LauncherEntry D-Bus publisher and owned native client only.
#include <QApplication>
#include <QDBusConnection>
#include <QDBusMessage>
#include <QFile>
#include <QImage>
#include <QJsonArray>
#include <QJsonDocument>
#include <QJsonObject>
#include <QTimer>
#include <QWidget>
#include <QWindow>
#include <dlfcn.h>
#include <unistd.h>

using Children=QList<QObject *> (*)(QObject *);
using Grab=QImage (*)(QWindow *);
static QObject *fixture=nullptr;
static QWindow *host=nullptr;
static QWidget *owned=nullptr;
static QJsonObject checks,snapshots;
static int phase=0,attempts=0;
static QString uri;
static QDBusConnection *publisher=nullptr;
static QObject *find(QObject *item,Children children) {
    if(!item)return nullptr;
    if(item->objectName()=="domainosUnityFixture")return item;
    if(item->inherits("QQuickItem"))for(auto child:children(item))if(auto found=find(child,children))return found;
    return nullptr;
}
static QJsonObject state() {
    QVariant value;
    QMetaObject::invokeMethod(fixture,"snapshot",Qt::DirectConnection,Q_RETURN_ARG(QVariant,value));
    return QJsonDocument::fromJson(value.toString().toUtf8()).object();
}
static bool publish(double progress,qint64 count,bool visible,bool urgent) {
    auto message=QDBusMessage::createSignal("/org/irixclassic/UnityPublisher","com.canonical.Unity.LauncherEntry","Update");
    const QVariantMap fields{{"progress",progress},{"progress-visible",visible},{"count",count},{"count-visible",visible},{"urgent",urgent}};
    message << uri << fields;
    return publisher->send(message);
}
static bool capture(const QString &name) {
    const auto grab=reinterpret_cast<Grab>(dlsym(RTLD_DEFAULT,"_ZN12QQuickWindow10grabWindowEv"));
    return grab && grab(host).save(qEnvironmentVariable("IRIX_DOMAINOS_UNITY_OUTPUT")+"/"+name);
}
static void complete() {
    QJsonObject result{{"checks",checks},{"snapshots",snapshots},{"owned_pid",getpid()},
        {"owned_winid",double(owned->winId())},{"published_uri",uri},{"publisher_unique_name",publisher ? publisher->baseService() : QString()},
        {"publisher_signature","sa{sv}"}};
    QFile file(qEnvironmentVariable("IRIX_DOMAINOS_UNITY_OUTPUT")+"/native.json");
    if(file.open(QIODevice::WriteOnly))file.write(QJsonDocument(result).toJson());
    if(publisher) {QDBusConnection::disconnectFromBus("domainosUnityPublisher");delete publisher;publisher=nullptr;}
    owned->close();QCoreApplication::quit();
}
static void tick() {
    if(++attempts>100){checks["native_scenario_completed"]=false;complete();return;}
    if(!fixture) {
        auto children=reinterpret_cast<Children>(dlsym(RTLD_DEFAULT,"_ZNK10QQuickItem10childItemsEv"));
        for(auto candidate:QGuiApplication::allWindows())if(children && (fixture=find(candidate->property("contentItem").value<QObject *>(),children))){host=candidate;break;}
        if(!fixture){QTimer::singleShot(100,tick);return;}
        host->setFlags(Qt::Tool|Qt::FramelessWindowHint);host->setGeometry(200,450,594,150);host->show();
        QMetaObject::invokeMethod(fixture,"setOwnedPid",Qt::DirectConnection,Q_ARG(QVariant,QVariant(getpid())));
    }
    auto current=state();
    if(phase==0) {
        if(!current["providerReal"].toBool() || current["rows"].toArray().size()!=1){QTimer::singleShot(100,tick);return;}
        snapshots["baseline"]=current;
        checks["owned_client_pid_and_native_window_id"]=current["pid"].toInt()==getpid() && current["winId"].toDouble()==double(owned->winId());
        checks["genuine_smart_launcher_item_bound_to_button"]=current["providerReal"].toBool() && current["providerType"].toString().startsWith("SmartLauncher::Item(");
        checks["owned_desktop_entry_is_native_launcher"]=current["launcher"].toString()=="applications:org.irixclassic.qa.unity.desktop";
        checks["baseline_indicators_hidden"]=!current["progressVisible"].toBool() && !current["countVisible"].toBool() && !current["attention"].toBool();
        uri="application://org.irixclassic.qa.unity.desktop";
        publisher=new QDBusConnection(QDBusConnection::connectToBus(qEnvironmentVariable("DBUS_SESSION_BUS_ADDRESS"),"domainosUnityPublisher"));
        checks["publisher_uses_private_real_bus_connection"]=publisher->isConnected() && publisher->baseService()!=QDBusConnection::sessionBus().baseService()
            && publisher->registerService("org.irixclassic.qa.UnityPublisher");
        checks["first_dbus_update_sent"]=publish(.42,7,true,true);phase=1;
    } else if(phase==1) {
        if(!current["progressVisible"].toBool() || current["progress"].toInt()!=42 || current["count"].toInt()!=7 || !current["urgent"].toBool()) {QTimer::singleShot(100,tick);return;}
        snapshots["first_update"]=current;
        checks["native_dbus_progress_maps_fraction_to_percentage"]=current["progress"].toInt()==42 && current["progressVisible"].toBool();
        checks["native_dbus_count_visible_on_approved_task"]=current["count"].toInt()==7 && current["countVisible"].toBool() && current["countOverlayVisible"].toBool();
        checks["native_dbus_urgent_reaches_task_and_controller"]=current["urgent"].toBool() && current["taskAttention"].toBool() && current["attention"].toBool();
        checks["first_native_capture_saved"]=capture("NATIVE-UNITY-42-7.png");
        checks["second_dbus_update_sent"]=publish(.81,11,true,false);phase=2;
    } else if(phase==2) {
        if(current["progress"].toInt()!=81 || current["count"].toInt()!=11 || current["urgent"].toBool()) {QTimer::singleShot(100,tick);return;}
        snapshots["second_update"]=current;
        checks["second_native_update_repaints_same_live_provider"]=current["providerReal"].toBool() && current["progress"].toInt()==81 && current["count"].toInt()==11;
        checks["native_urgency_clears_without_native_window_attention"]=!current["attention"].toBool() && !current["taskAttention"].toBool();
        checks["second_native_capture_saved"]=capture("NATIVE-UNITY-81-11.png");
        checks["final_dbus_update_sent"]=publish(0,0,false,false);phase=3;
    } else if(phase==3) {
        if(current["progressVisible"].toBool() || current["countVisible"].toBool()) {QTimer::singleShot(100,tick);return;}
        snapshots["hidden_update"]=current;
        checks["native_visibility_update_unloads_both_indicators"]=!current["progressOverlayVisible"].toBool() && !current["countOverlayVisible"].toBool();
        checks["approved_cell_geometry_preserved"]=current["cellWidth"].toInt()==66 && current["cellHeight"].toInt()==98;
        checks["no_application_activation_or_window_operation"]=current["requests"].toArray().isEmpty();
        checks["native_scenario_completed"]=true;complete();return;
    }
    QTimer::singleShot(200,tick);
}
extern "C" int interceptedExec() asm("_ZN12QApplication4execEv");
extern "C" int interceptedExec() {
    auto original=reinterpret_cast<int (*)()>(dlsym(RTLD_NEXT,"_ZN12QApplication4execEv"));
    if(!original)return 2;
    QGuiApplication::setDesktopFileName("org.irixclassic.qa.unity");
    owned=new QWidget;owned->setWindowTitle("DomainOS Unity owned client");owned->resize(300,180);owned->move(80,100);owned->show();
    QTimer::singleShot(1200,tick);return original();
}
