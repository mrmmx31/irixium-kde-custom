// SPDX-FileCopyrightText: 2026 IRIX Classic contributors
// SPDX-License-Identifier: GPL-3.0-or-later
// Installed native QAction and actual TasksModel; private owned windows only.
#include <QAction>
#include <QApplication>
#include <QFile>
#include <QDBusArgument>
#include <QDBusInterface>
#include <QDBusMessage>
#include <QDBusVariant>
#include <QImage>
#include <QJsonArray>
#include <QJsonDocument>
#include <QJsonObject>
#include <QMenu>
#include <QPointer>
#include <QProcess>
#include <QProcessEnvironment>
#include <QTimer>
#include <QWidget>
#include <QWindow>
#include <dlfcn.h>
#include <unistd.h>
#include <X11/Xlib.h>
#ifdef IRIX_MEMBERSHIP_CHILD
int main(int argc,char **argv) {
    QApplication app(argc,argv);app.setApplicationName("plasmawindowed");app.setDesktopFileName("org.kde.plasmawindowed");
    QWidget widget;widget.setWindowTitle("DomainOS desktop membership C");widget.resize(220,140);widget.move(560,80);
    widget.setAttribute(Qt::WA_ShowWithoutActivating);widget.show();QTimer::singleShot(60000,&app,&QCoreApplication::quit);return app.exec();
}
#else
using Children=QList<QObject *> (*)(QObject *);
using Grab=QImage (*)(QWindow *);
static QObject *fixture=nullptr;
static QWindow *window=nullptr;
static QList<QWidget *> owned;
static QJsonObject checks,snapshots,actions;
static int phase=0,attempts=0;
static QPointer<QAction> staleAction;
static QProcess *childProcess=nullptr;
static QString mode;
static bool initialAttentionCleared=false,newAttentionCleared=false;
static QObject *find(QObject *object,Children children) {
    if(!object)return nullptr;
    if(object->objectName()=="domainosDesktopMembershipFixture")return object;
    if(object->inherits("QQuickItem"))for(auto child:children(object))if(auto result=find(child,children))return result;
    return nullptr;
}
static QVariant invoke(const char *method) {
    QVariant result;QMetaObject::invokeMethod(fixture,method,Qt::DirectConnection,Q_RETURN_ARG(QVariant,result));return result;
}
static QJsonObject state(){
    auto result=QJsonDocument::fromJson(invoke("state").toString().toUtf8()).object();
    QDBusInterface properties("org.kde.KWin","/VirtualDesktopManager","org.freedesktop.DBus.Properties",QDBusConnection::sessionBus());
    auto reply=properties.call("Get","org.kde.KWin.VirtualDesktopManager","desktops");
    QJsonArray records;
    if(reply.type()!=QDBusMessage::ErrorMessage && !reply.arguments().isEmpty()) {
        const auto wrapped=qvariant_cast<QDBusVariant>(reply.arguments().first()).variant();
        const auto argument=qvariant_cast<QDBusArgument>(wrapped);
        argument.beginArray();
        while(!argument.atEnd()) {uint position;QString id,name;argument.beginStructure();argument>>position>>id>>name;argument.endStructure();records.append(QJsonObject{{"position",int(position)},{"id",id},{"name",name}});}
        argument.endArray();
    }
    result["kwinDesktopRecords"]=records;
    return result;
}
static QAction *newDesktopAction() {
    // PlasmaExtras.Menu is backed by real QWidget QMenus. Follow their QAction
    // submenus; don't synthesize/call a production adapter operation ourselves.
    for(auto widget:QApplication::allWidgets())if(auto menu=qobject_cast<QMenu *>(widget)) {
        for(auto action:menu->actions()) {
            auto text=action->text();text.remove('&');
            if(text=="New Desktop" && action->isEnabled())return action;
        }
    }
    return nullptr;
}
static QJsonObject windowStates(const QJsonObject &snapshot) {
    QJsonObject result;
    for(auto value:snapshot["windows"].toArray()) {
        const auto row=value.toObject();
        result[row["key"].toString()]=QJsonObject{{"title",row["title"]},{"pid",row["pid"]},{"geometry",row["geometry"]},{"desktops",row["desktopIds"]}};
    }
    return result;
}
static QStringList members(const QJsonObject &snapshot,const char *key="group") {
    QStringList ids;for(auto member:snapshot[key].toObject()["members"].toArray())ids.append(member.toObject()["key"].toString());ids.sort();return ids;
}
static QJsonArray windowDesktops(const QJsonObject &snapshot,const QString &suffix) {
    for(auto value:snapshot["windows"].toArray())if(value.toObject()["title"].toString()=="DomainOS desktop membership "+suffix)return value.toObject()["desktopIds"].toArray();
    return {};
}
static void capture(const QString &name) {
    const auto grab=reinterpret_cast<Grab>(dlsym(RTLD_DEFAULT,"_ZN12QQuickWindow10grabWindowEv"));
    actions["capture_"+name]=window && grab && grab(window).save(qEnvironmentVariable("IRIX_DOMAINOS_MEMBERSHIP_OUTPUT")+"/"+name+".png");
}
static void complete() {
    capture("NATIVE-FINAL");
    QJsonObject report{{"checks",checks},{"snapshots",snapshots},{"actions",actions},{"owned_pid",getpid()},{"mode",mode},{"native_context_menu_source","/usr/share/plasma/plasmoids/org.kde.plasma.taskmanager/contents/ui/ContextMenu.qml"},{"final",fixture ? state() : QJsonObject()}};
    if(childProcess) {
        childProcess->terminate();if(!childProcess->waitForFinished(3000)){childProcess->kill();childProcess->waitForFinished(3000);}
        checks["owned_child_stopped"]=childProcess->state()==QProcess::NotRunning;report["checks"]=checks;
    }
    QFile file(qEnvironmentVariable("IRIX_DOMAINOS_MEMBERSHIP_OUTPUT")+"/state.json");
    if(file.open(QIODevice::WriteOnly))file.write(QJsonDocument(report).toJson());
    for(auto widget:owned)widget->close();QCoreApplication::quit();
}
static QWidget *createOwned(const QString &name) {
    auto widget=new QWidget;widget->setWindowTitle("DomainOS desktop membership "+name);widget->resize(220,140);
    widget->move(60+owned.size()*250,80);widget->setAttribute(Qt::WA_ShowWithoutActivating);widget->show();owned.append(widget);return widget;
}
static void clearOwnedAttention(WId id) {
    // KDE normally excludes demanding-attention tasks from groups. Remove that
    // state on our own inactive test client via the real EWMH protocol instead
    // of overriding the grouping model or activating/dismissing the open menu.
    auto display=XOpenDisplay(nullptr);if(!display)return;
    XEvent event{};event.xclient.type=ClientMessage;event.xclient.window=id;
    event.xclient.message_type=XInternAtom(display,"_NET_WM_STATE",False);event.xclient.format=32;
    event.xclient.data.l[0]=0;event.xclient.data.l[1]=XInternAtom(display,"_NET_WM_STATE_DEMANDS_ATTENTION",False);event.xclient.data.l[3]=2;
    XSendEvent(display,DefaultRootWindow(display),False,SubstructureNotifyMask|SubstructureRedirectMask,&event);XFlush(display);XCloseDisplay(display);
}
static void tick() {
    if(++attempts>90){checks["native_scenario_completed"]=false;complete();return;}
    if(!fixture) {
        const auto children=reinterpret_cast<Children>(dlsym(RTLD_DEFAULT,"_ZNK10QQuickItem10childItemsEv"));
        for(auto candidate:QGuiApplication::allWindows())if(children && (fixture=find(candidate->property("contentItem").value<QObject *>(),children))){window=candidate;break;}
        if(!fixture){QTimer::singleShot(100,tick);return;}
        window->setFlags(Qt::Tool|Qt::FramelessWindowHint);window->setGeometry(200,450,594,150);window->show();
    }
    const auto current=state();
    if(phase==0) {
        if(current["windows"].toArray().size()!=2 || current["rows"].toArray().size()!=2 || current["count"].toInt()!=2){QTimer::singleShot(100,tick);return;}
        bool onlyOwn=true;for(auto value:current["rows"].toArray())onlyOwn &= value.toObject()["title"].toString().startsWith("DomainOS desktop membership ");
        if(!onlyOwn){QTimer::singleShot(100,tick);return;}
        checks["host_tool_removed_before_native_grouping"]=true;
        for(auto widget:owned)clearOwnedAttention(widget->winId());initialAttentionCleared=true;actions["initial_owned_attention_cleared_via_ewmh"]=true;
        invoke("enableGrouping");phase=6;
    } else if(phase==6) {
        QStringList expected;for(auto value:current["windows"].toArray())expected.append(value.toObject()["key"].toString());expected.sort();
        if(members(current)!=expected || expected.size()!=2){QTimer::singleShot(100,tick);return;}
        snapshots["initial"]=current;
        bool pids=true;for(auto value:current["windows"].toArray())pids &= value.toObject()["pid"].toInt()==getpid();
        checks["two_native_owned_windows_grouped"]=pids && members(current).size()==2;
        checks["two_private_desktops_available"]=current["count"].toInt()==2;
        checks["native_kwin_desktop_uuids_observed"]=current["kwinDesktopRecords"].toArray().size()==2 && !current["kwinDesktopRecords"].toArray()[0].toObject()["id"].toString().isEmpty();
        checks["installed_native_menu_source_used"]=current["nativeContextMenu"].toString().endsWith("/usr/share/plasma/plasmoids/org.kde.plasma.taskmanager/contents/ui/ContextMenu.qml");
        checks["captured_group_menu_opened"]=invoke("openCurrent").toBool();phase=1;
    } else if(phase==1) {
        staleAction=newDesktopAction();
        if(!staleAction){QTimer::singleShot(100,tick);return;}
        actions["stale_qaction_class"]=staleAction->metaObject()->className();actions["stale_qaction_text"]=staleAction->text();
        snapshots["menu_open_two_members"]=current;
        checks["real_installed_new_desktop_qaction_found"]=!staleAction.isNull();
        checks["menu_captured_exact_initial_members"]=members(current,"menuTarget")==members(current);
        capture("MENU-TWO-MEMBERS");
        childProcess=new QProcess;auto environment=QProcessEnvironment::systemEnvironment();environment.remove("LD_PRELOAD");childProcess->setProcessEnvironment(environment);
        childProcess->setStandardOutputFile(qEnvironmentVariable("IRIX_DOMAINOS_MEMBERSHIP_OUTPUT")+"/child.log");childProcess->setStandardErrorFile(qEnvironmentVariable("IRIX_DOMAINOS_MEMBERSHIP_OUTPUT")+"/child.log",QIODevice::Append);
        childProcess->start(qEnvironmentVariable("IRIX_DOMAINOS_MEMBERSHIP_OUTPUT")+"/membership-child");phase=2;
    } else if(phase==2) {
        if(current["windows"].toArray().size()!=3){QTimer::singleShot(100,tick);return;}
        if(!newAttentionCleared){snapshots["third_window_before_attention_clear"]=current;for(auto value:current["windows"].toArray()) {
            auto record=value.toObject();if(record["title"].toString().endsWith(" C")) {
                checks["new_member_pid_belongs_to_owned_child"]=childProcess && childProcess->processId()>0 && record["pid"].toInteger()==childProcess->processId() && childProcess->processId()!=getpid();
                actions["owned_child_pid"]=qint64(childProcess ? childProcess->processId() : 0);clearOwnedAttention(record["windowIds"].toArray()[0].toInteger());
            }
        }newAttentionCleared=true;actions["new_owned_attention_cleared_via_ewmh"]=true;QTimer::singleShot(100,tick);return;}
        if(members(current).size()!=3){QTimer::singleShot(100,tick);return;}
        snapshots["three_members_menu_still_captured_two"]=current;
        checks["new_member_native_identity_observed"]=members(current).size()==3;
        checks["menu_target_keeps_original_two"]=members(current,"menuTarget")==members(snapshots["initial"].toObject());
        checks["stale_menu_and_qaction_remained_alive"]=current["menuOpen"].toBool() && !staleAction.isNull();
        if(!staleAction){checks["native_scenario_completed"]=false;complete();return;}
        staleAction->trigger();actions["stale_qaction_triggered"]=true;phase=3;
    } else if(phase==3) {
        snapshots["after_stale_native_action"]=current;
        const auto before=snapshots["three_members_menu_still_captured_two"].toObject();
        checks["stale_action_creates_no_desktop"]=current["desktops"]==before["desktops"] && current["kwinDesktopRecords"]==before["kwinDesktopRecords"];
        checks["stale_action_moves_no_member"]=windowStates(current)==windowStates(before);
        const auto initial=snapshots["initial"].toObject();
        checks["old_desktop_ids_preserved"]=current["desktops"].toArray().contains(initial["desktops"].toArray()[0]) && current["desktops"].toArray().contains(initial["desktops"].toArray()[1]);
        actions["unselected_c_was_moved"]=windowDesktops(current,"C")!=windowDesktops(before,"C");
        if(mode=="before") {
            checks["native_scenario_completed"]=true;complete();return;
        }
        checks["stale_action_informs_reopen"]=!current["lastError"].toString().isEmpty();
        checks["stale_action_emits_no_operation_request"]=current["requests"].toArray().isEmpty();
        const auto activity=current["activity"].toObject();
        checks["stale_action_starts_no_light_operation"]=activity["sequence"].toInt()==0 && activity["pendingCount"].toInt()==0 && !activity["lit"].toBool() && activity["reports"].toArray().isEmpty();
        checks["fresh_group_menu_opened"]=invoke("openCurrent").toBool();phase=4;
    } else if(phase==4) {
        auto action=newDesktopAction();if(!action){QTimer::singleShot(100,tick);return;}
        snapshots["fresh_menu_three_members"]=current;
        checks["fresh_menu_captures_exact_three"]=members(current,"menuTarget")==members(current) && members(current).size()==3;
        actions["fresh_qaction_text"]=action->text();action->trigger();actions["fresh_qaction_triggered"]=true;phase=5;
    } else if(phase==5) {
        const auto before=snapshots["fresh_menu_three_members"].toObject();
        if(current["count"].toInt()!=before["count"].toInt()+1){QTimer::singleShot(100,tick);return;}
        bool allOnNew=true;QJsonValue newId;
        for(auto id:current["desktops"].toArray())if(!before["desktops"].toArray().contains(id))newId=id;
        for(auto value:current["windows"].toArray())allOnNew &= value.toObject()["desktopIds"].toArray()==QJsonArray{newId};
        if(!allOnNew){QTimer::singleShot(100,tick);return;}
        snapshots["after_fresh_native_action"]=current;actions["new_desktop_id"]=newId;
        checks["fresh_action_creates_exactly_one_desktop"]=current["count"].toInt()==before["count"].toInt()+1 && !newId.isNull();
        checks["fresh_action_moves_exact_three_captured_members"]=allOnNew && members(current)==members(before);
        bool sameGeometry=true;const auto left=windowStates(current),right=windowStates(before);
        for(const auto &key:left.keys())sameGeometry &= left[key].toObject()["geometry"]==right[key].toObject()["geometry"] && left[key].toObject()["pid"]==right[key].toObject()["pid"];
        checks["new_desktop_preserves_geometry_and_pids"]=sameGeometry;
        const auto requests=current["requests"].toArray();
        checks["fresh_action_emits_exactly_one_operation_request"]=requests.size()==1;
        const auto request=requests.isEmpty() ? QJsonObject() : requests[0].toObject();
        checks["fresh_operation_request_identifies_captured_group"]=request["action"].toString()=="newVirtualDesktop" && request["state"].toString()=="requested" && request["key"]==before["menuTarget"].toObject()["key"];
        const auto activity=current["activity"].toObject(),report=activity["lastReport"].toObject();
        checks["runtime_reports_request_accepted_without_completion"]=activity["sequence"].toInt()==1 && activity["pendingCount"].toInt()==0 && activity["reports"].toArray().size()==1 && report["ok"].toBool() && report["outcome"].toString()=="request-accepted" && report["action"].toString()=="newVirtualDesktop";
        checks["runtime_optional_tail_lit_after_native_request"]=activity["tailLit"].toBool() && activity["lit"].toBool();
        phase=7;
    } else if(phase==7) {
        const auto activity=current["activity"].toObject();
        if(activity["lit"].toBool()){QTimer::singleShot(100,tick);return;}
        snapshots["after_runtime_tail_extinguished"]=current;
        checks["runtime_optional_tail_extinguished"]=!activity["lit"].toBool() && !activity["tailLit"].toBool() && activity["sequence"].toInt()==1 && activity["pendingCount"].toInt()==0;
        checks["tail_wait_does_not_repeat_or_defer_native_action"]=current["requests"]==snapshots["after_fresh_native_action"].toObject()["requests"] && current["desktops"]==snapshots["after_fresh_native_action"].toObject()["desktops"] && current["kwinDesktopRecords"]==snapshots["after_fresh_native_action"].toObject()["kwinDesktopRecords"] && windowStates(current)==windowStates(snapshots["after_fresh_native_action"].toObject());
        checks["native_scenario_completed"]=true;complete();return;
    }
    QTimer::singleShot(650,tick);
}
extern "C" int interceptedExec() asm("_ZN12QApplication4execEv");
extern "C" int interceptedExec() {
    const auto original=reinterpret_cast<int (*)()>(dlsym(RTLD_NEXT,"_ZN12QApplication4execEv"));if(!original)return 2;
    mode=qEnvironmentVariable("IRIX_DOMAINOS_MEMBERSHIP_MODE");createOwned("A");createOwned("B");QTimer::singleShot(1200,tick);return original();
}

#endif
