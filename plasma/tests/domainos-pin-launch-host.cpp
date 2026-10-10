// SPDX-FileCopyrightText: 2026 IRIX Classic contributors
// SPDX-License-Identifier: GPL-3.0-or-later
// Controller API only: production Applications -> Runtime Commands -> KIO.
#include <QApplication>
#include <QFile>
#include <QJsonArray>
#include <QJsonDocument>
#include <QJsonObject>
#include <QScreen>
#include <QTimer>
#include <QWindow>
#include <dlfcn.h>
#include <unistd.h>
using Children=QList<QObject *> (*)(QObject *);
static QObject *fixture=nullptr;
static QWindow *window=nullptr;
static QJsonObject checks,snapshots;
static int phase=0,attempts=0;
static const QString desktopId="org.irixclassic.domainos.pin.launch.test.desktop";
static const QString ownTitle="DomainOS F32 own pinned application";
static QObject *find(QObject *object,Children children) {
    if(!object)return nullptr;
    if(object->objectName()=="domainosPinLaunchFixture")return object;
    if(object->inherits("QQuickItem"))for(auto child:children(object))if(auto result=find(child,children))return result;
    return nullptr;
}
static QVariant invoke(const char *method) {
    QVariant result;QMetaObject::invokeMethod(fixture,method,Qt::DirectConnection,Q_RETURN_ARG(QVariant,result));return result;
}
static QJsonObject state(){return QJsonDocument::fromJson(invoke("state").toString().toUtf8()).object();}
static QJsonObject marker() {
    QFile file(qEnvironmentVariable("IRIX_DOMAINOS_PIN_DIR")+"/program-marker.json");
    if(!file.open(QIODevice::ReadOnly))return {};
    return QJsonDocument::fromJson(file.readAll()).object();
}
static void complete() {
    QJsonObject report{{"checks",checks},{"snapshots",snapshots},{"owned_host_pid",getpid()},
        {"final",fixture ? state() : QJsonObject()},{"marker",marker()},
        {"scope","launchPin controller API, no full-panel pointer click; genuine production Runtime/Commands/Activity/helper and private Desktop Entry/KIO/X11 window"}};
    QFile file(qEnvironmentVariable("IRIX_DOMAINOS_PIN_DIR")+"/native.json");
    if(file.open(QIODevice::WriteOnly))file.write(QJsonDocument(report).toJson());
    QCoreApplication::quit();
}
static void tick() {
    if(++attempts>120){checks["native_scenario_completed"]=false;complete();return;}
    if(!fixture) {
        const auto children=reinterpret_cast<Children>(dlsym(RTLD_DEFAULT,"_ZNK10QQuickItem10childItemsEv"));
        for(auto candidate:QGuiApplication::allWindows())if(children && (fixture=find(candidate->property("contentItem").value<QObject *>(),children))){window=candidate;break;}
        if(!fixture){QTimer::singleShot(100,tick);return;}
        window->setFlags(Qt::Tool|Qt::FramelessWindowHint);window->setGeometry(100,500,500,120);window->show();
    }
    const auto current=state();
    if(phase==0) {
        if(!current["pinInfo"].toObject()["available"].toBool() || !current["windows"].toArray().isEmpty()){QTimer::singleShot(100,tick);return;}
        snapshots["initial"]=current;
        checks["pin_native_metadata_available"]=current["pinInfo"].toObject()["desktopId"].toString()==desktopId && !current["pinInfo"].toObject()["title"].toString().isEmpty();
        checks["one_private_pin_before_launch"]=current["pins"].toArray()==QJsonArray{desktopId};
        const auto activity=current["activity"].toObject();
        checks["no_activity_or_launch_on_load"]=activity["sequence"].toInt()==0 && activity["pending"].toInt()==0 && !activity["lit"].toBool() && current["reports"].toArray().isEmpty() && marker().isEmpty();
        checks["native_drawer_opens"]=invoke("showDrawer").toBool();phase=1;
    } else if(phase==1) {
        snapshots["drawer_before_launch"]=current;
        checks["drawer_opening_does_not_launch"]=current["drawer"].toBool() && current["popupVisible"].toBool() && current["reports"].toArray().isEmpty() && marker().isEmpty();
        checks["drawer_screen_capture_saved"]=window->screen()->grabWindow(0).save(qEnvironmentVariable("IRIX_DOMAINOS_PIN_DIR")+"/DRAWER-BEFORE-LAUNCH.png");
        checks["launch_pin_controller_api_accepted"]=invoke("launchPin").toBool();
        const auto immediate=state()["immediate"].toObject();snapshots["immediate_launch"]=immediate;
        checks["activity_token_and_light_immediate"]=immediate["accepted"].toBool() && immediate["sequence"].toInt()==1 && immediate["pending"].toInt()==1 && immediate["lit"].toBool() && immediate["jobs"].toObject().size()==1;
        phase=2;
    } else if(phase==2) {
        auto observation=marker();QJsonObject ownWindow;
        for(auto value:current["windows"].toArray())if(value.toObject()["title"].toString()==ownTitle)ownWindow=value.toObject();
        if(current["report"].toObject()["application"].toString()!=desktopId || observation.isEmpty() || ownWindow.isEmpty()){QTimer::singleShot(100,tick);return;}
        snapshots["native_launch_observed"]=current;snapshots["own_native_window"]=ownWindow;
        const auto result=current["report"].toObject(),activity=current["activity"].toObject();
        checks["helper_reports_accepted_application_id"]=result["ok"].toBool() && result["application"].toString()==desktopId && result["outcome"].toString()=="request-accepted";
        checks["activity_token_matches_helper_result"]=result["token"].toInt()==1 && activity["sequence"].toInt()==1 && current["reports"].toArray().size()==1;
        checks["activity_finishes_while_own_application_remains_open"]=activity["pending"].toInt()==0 && !activity["lit"].toBool() && !activity["tailLit"].toBool() && !activity["keepLightAfterCompletion"].toBool();
        checks["pin_kept_after_launch"]=current["pins"].toArray()==snapshots["initial"].toObject()["pins"].toArray() && current["pinInfo"].toObject()["available"].toBool();
        checks["launch_closes_drawer_popup"]=!current["popupVisible"].toBool();
        checks["new_task_has_observed_owned_pid_and_window_id"]=observation["pid"].toInt()>0 && observation["pid"].toInt()!=getpid() && ownWindow["pid"]==observation["pid"] && ownWindow["windowIds"].toArray().contains(observation["windowId"]);
        checks["task_not_inserted_as_launcher"]=current["launchers"].toArray().isEmpty() && current["windows"].toArray().size()==1;
        const QJsonArray expectedArgs{qEnvironmentVariable("IRIX_DOMAINOS_PIN_DIR")+"/pin-marker.py","pin-directed-positive","argument with spaces"};
        checks["desktop_entry_literal_arguments_observed"]=observation["argv"].toArray()==expectedArgs;
        checks["program_inherits_only_private_namespaces"]=observation["home"].toString()==qEnvironmentVariable("HOME") && observation["config"].toString()==qEnvironmentVariable("XDG_CONFIG_HOME") && observation["data"].toString()==qEnvironmentVariable("XDG_DATA_HOME") && observation["runtime"].toString()==qEnvironmentVariable("XDG_RUNTIME_DIR") && observation["display"].toString()==qEnvironmentVariable("DISPLAY") && observation["bus"].toString()==qEnvironmentVariable("DBUS_SESSION_BUS_ADDRESS");
        checks["test_interceptor_not_in_launched_program"]=observation["ld_preload"].isNull() || observation["ld_preload"].toString().isEmpty();
        checks["own_application_screen_capture_saved"]=window->screen()->grabWindow(0).save(qEnvironmentVariable("IRIX_DOMAINOS_PIN_DIR")+"/OWN-PINNED-APPLICATION.png");
        checks["native_scenario_completed"]=true;complete();return;
    }
    QTimer::singleShot(250,tick);
}
extern "C" int interceptedExec() asm("_ZN12QApplication4execEv");
extern "C" int interceptedExec() {
    const auto original=reinterpret_cast<int (*)()>(dlsym(RTLD_NEXT,"_ZN12QApplication4execEv"));if(!original)return 2;
    // LD_PRELOAD can reach the helper/own launched program. Drive only the
    // explicitly identified Plasma host, never another application's loop.
    if(!QCoreApplication::arguments().contains("org.irixclassic.domainos.pin.launch.test"))return original();
    QTimer::singleShot(1200,tick);return original();
}
