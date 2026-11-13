// SPDX-License-Identifier: GPL-3.0-or-later
// Physical pointer driver: unmodified production model calls and owned clients.
#include <QApplication>
#include <QDir>
#include <QFile>
#include <QJsonArray>
#include <QJsonDocument>
#include <QJsonObject>
#include <QProcess>
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

static QObject *find(QObject *item,Children children) {
    if(!item)return nullptr;
    if(item->objectName()=="domainosMiddleFixture")return item;
    if(item->inherits("QQuickItem"))for(auto child:children(item))if(auto found=find(child,children))return found;
    return nullptr;
}
static QVariant invoke(const char *method,const QVariant &argument=QVariant()) {
    QVariant result;
    if(argument.isValid())QMetaObject::invokeMethod(fixture,method,Qt::DirectConnection,Q_RETURN_ARG(QVariant,result),Q_ARG(QVariant,argument));
    else QMetaObject::invokeMethod(fixture,method,Qt::DirectConnection,Q_RETURN_ARG(QVariant,result));
    return result;
}
static QJsonObject state(){return QJsonDocument::fromJson(invoke("state").toString().toUtf8()).object();}
static QJsonArray familyWindows(const QJsonObject &state,const QString &family) {
    QJsonArray result;
    for(auto value:state["windows"].toArray())if(value.toObject()["launcherUrl"].toString()=="applications:org.irixclassic.qa.middle."+family+".desktop")result.append(value);
    return result;
}
static QJsonObject launchedMarker(const QString &family) {
    const QDir output(qEnvironmentVariable("IRIX_DOMAINOS_MIDDLE_OUTPUT"));
    for(const auto &name:output.entryList({"marker-*.json"},QDir::Files)) {
        QFile file(output.filePath(name));if(!file.open(QIODevice::ReadOnly))continue;
        const auto marker=QJsonDocument::fromJson(file.readAll()).object();
        if(marker["family"].toString()==family && marker["instance"].toString()=="launched")return marker;
    }
    return {};
}
static bool observeLaunched(const QJsonObject &current,const QString &family) {
    const auto marker=launchedMarker(family);if(marker.isEmpty())return false;
    for(auto value:familyWindows(current,family)) {
        const auto row=value.toObject();
        if(row["pid"]==marker["pid"] && row["windowIds"].toArray().contains(marker["windowId"]))return true;
    }
    return false;
}
static bool existingUnminimized(const QJsonObject &before,const QJsonObject &after) {
    const auto observed=after["windows"].toArray();
    for(auto value:before["windows"].toArray()) {
        const auto old=value.toObject();bool found=false;
        for(auto candidate:observed) {
            const auto row=candidate.toObject();
            if(row["pid"]==old["pid"] && row["key"]==old["key"]){found=!row["minimized"].toBool();break;}
        }
        if(!found)return false;
    }
    return true;
}
static bool expectedRequests(const QJsonObject &current,int count) {
    const auto requests=current["requests"].toArray();if(requests.size()!=count)return false;
    for(auto value:requests)if(value.toObject()["action"].toString()!="newInstance")return false;
    return true;
}
static bool clickMiddle(const QString &family) {
    const auto coordinate=QJsonDocument::fromJson(invoke("coordinates",family).toString().toUtf8()).object();
    if(coordinate.isEmpty())return false;
    snapshots[family+"_physical_coordinate"]=coordinate;
    QProcess pointer;
    pointer.start("xdotool",{"mousemove",QString::number(qRound(coordinate["x"].toDouble())),
        QString::number(qRound(coordinate["y"].toDouble())),"click","2"});
    if(!pointer.waitForFinished(2000)){pointer.kill();pointer.waitForFinished(1000);return false;}
    return pointer.exitStatus()==QProcess::NormalExit && pointer.exitCode()==0;
}
static bool capture(const QString &name) {
    return window && window->screen()->grabWindow(0).save(qEnvironmentVariable("IRIX_DOMAINOS_MIDDLE_OUTPUT")+"/"+name);
}
static void complete() {
    QJsonObject report{{"checks",checks},{"snapshots",snapshots},{"final",fixture?state():QJsonObject()},
        {"host_pid",getpid()},{"pointer_method","xdotool XTest button 2 on real Iconbox delegates"},
        {"scope","Native TasksModel; no model double, no app-operation interceptor, no direct middleAction/controller invocation"}};
    QFile file(qEnvironmentVariable("IRIX_DOMAINOS_MIDDLE_OUTPUT")+"/native.json");
    if(file.open(QIODevice::WriteOnly))file.write(QJsonDocument(report).toJson());
    QCoreApplication::quit();
}
static void tick() {
    if(++attempts>130){checks["native_scenario_completed"]=false;complete();return;}
    if(!fixture) {
        const auto children=reinterpret_cast<Children>(dlsym(RTLD_DEFAULT,"_ZNK10QQuickItem10childItemsEv"));
        for(auto candidate:QGuiApplication::allWindows())if(children && (fixture=find(candidate->property("contentItem").value<QObject *>(),children))){window=candidate;break;}
        if(!fixture){QTimer::singleShot(100,tick);return;}
        window->setFlags(Qt::Tool|Qt::FramelessWindowHint);window->setGeometry(200,450,594,150);window->show();
    }
    const auto current=state();
    if(phase==0) {
        if(familyWindows(current,"group").size()!=2 || familyWindows(current,"single").size()!=1
            || !current["groupButtonReady"].toBool() || !current["singleButtonReady"].toBool()
            || current["windows"].toArray().size()!=3){QTimer::singleShot(100,tick);return;}
        snapshots["initial"]=current;
        checks["genuine_native_task_model"]=current["nativeModel"].toString().startsWith("TaskManager::TasksModel(")
            || current["nativeModel"].toString().startsWith("TasksModel(");
        checks["two_owned_clients_grouped_one_singleton"]=current["group"].toObject()["group"].toBool()
            && !current["single"].toObject()["group"].toBool() && current["rows"].toArray().size()==2;
        checks["group_native_can_launch_false"]=current["groupRole"].isBool() && !current["groupRole"].toBool();
        bool membersFalse=true;
        for(auto member:current["group"].toObject()["members"].toArray())membersFalse &= !member.toObject()["canLaunchNewInstance"].toBool();
        checks["group_members_native_can_launch_false"]=membersFalse;
        checks["singleton_native_can_launch_false"]=current["singleRole"].isBool() && !current["singleRole"].toBool()
            && !current["single"].toObject()["canLaunchNewInstance"].toBool();
        checks["default_middle_preference_new_instance"]=current["middlePreference"].toInt()==2;
        checks["no_request_before_pointer"]=current["requests"].toArray().isEmpty() && launchedMarker("group").isEmpty() && launchedMarker("single").isEmpty();
        checks["initial_capture_saved"]=capture("INITIAL-GROUP-SINGLE.png");
        checks["group_physical_middle_click_sent_once"]=clickMiddle("group");phase=1;
    } else if(phase==1) {
        if(familyWindows(current,"group").size()!=3 || !observeLaunched(current,"group")){QTimer::singleShot(100,tick);return;}
        snapshots["after_group_middle"]=current;snapshots["group_launch_marker"]=launchedMarker("group");
        checks["group_one_request_new_instance"]=expectedRequests(current,1);
        checks["group_new_owned_pid_and_native_window_observed"]=observeLaunched(current,"group")
            && launchedMarker("group")["pid"].toInt()!=getpid();
        checks["group_middle_preserves_selection"]=current["selection"]==snapshots["initial"].toObject()["selection"];
        checks["group_middle_no_member_popup_or_error"]=!current["groupPopup"].toBool() && current["lastError"].toString().isEmpty();
        checks["group_middle_never_minimizes_original_clients"]=existingUnminimized(snapshots["initial"].toObject(),current);
        checks["group_capture_saved"]=capture("GROUP-MIDDLE-NEW-WINDOW.png");
        checks["singleton_still_single_before_click"]=familyWindows(current,"single").size()==1 && !current["single"].toObject()["group"].toBool();
        checks["singleton_physical_middle_click_sent_once"]=clickMiddle("single");phase=2;
    } else if(phase==2) {
        if(familyWindows(current,"single").size()!=2 || !observeLaunched(current,"single")){QTimer::singleShot(100,tick);return;}
        snapshots["after_single_middle"]=current;snapshots["single_launch_marker"]=launchedMarker("single");
        checks["singleton_one_extra_request_new_instance"]=expectedRequests(current,2);
        checks["singleton_new_owned_pid_and_native_window_observed"]=observeLaunched(current,"single")
            && launchedMarker("single")["pid"].toInt()!=getpid();
        checks["singleton_middle_preserves_selection"]=current["selection"]==snapshots["initial"].toObject()["selection"];
        checks["singleton_middle_no_member_popup_or_error"]=!current["groupPopup"].toBool() && current["lastError"].toString().isEmpty();
        checks["neither_middle_click_minimizes_original_clients"]=existingUnminimized(snapshots["initial"].toObject(),current);
        checks["two_middle_clicks_add_exactly_two_windows"]=current["windows"].toArray().size()==5;
        checks["final_capture_saved"]=capture("SINGLE-MIDDLE-NEW-WINDOW.png");
        checks["native_scenario_completed"]=true;complete();return;
    }
    QTimer::singleShot(150,tick);
}
extern "C" int interceptedExec() asm("_ZN12QApplication4execEv");
extern "C" int interceptedExec() {
    const auto original=reinterpret_cast<int (*)()>(dlsym(RTLD_NEXT,"_ZN12QApplication4execEv"));
    if(!original)return 2;
    if(!QCoreApplication::arguments().contains("org.irixclassic.qa.middle.fixture"))return original();
    QTimer::singleShot(1200,tick);return original();
}
