// SPDX-FileCopyrightText: 2026 IRIX Classic contributors
// SPDX-License-Identifier: GPL-3.0-or-later
// Test-only gestures inside the legitimate Wayland plasmawindowed process.
#include <QApplication>
#include <QFile>
#include <QImage>
#include <QJsonArray>
#include <QJsonDocument>
#include <QJsonObject>
#include <QSet>
#include <QTest>
#include <QTimer>
#include <QUuid>
#include <QWidget>
#include <QWindow>
#include <dlfcn.h>
#include <unistd.h>

using Children=QList<QObject *> (*)(QObject *);
using Grab=QImage (*)(QWindow *);
using Map=QPointF (*)(const QObject *,const QObject *,const QPointF &);
static QObject *fixture=nullptr;
static QWindow *host=nullptr;
static QList<QWidget *> owned;
static QJsonArray identities;
static QJsonObject checks,snapshots;
static int phase=0,attempts=0;
static QObject *find(QObject *object,const QString &name) {
    if(!object)return nullptr;
    if(object->objectName()==name)return object;
    const auto children=reinterpret_cast<Children>(dlsym(RTLD_DEFAULT,"_ZNK10QQuickItem10childItemsEv"));
    if(children && object->inherits("QQuickItem"))for(auto child:children(object))if(auto result=find(child,name))return result;
    return nullptr;
}
static QObject *item(const QString &name,QWindow **owner=nullptr) {
    for(auto candidate:QGuiApplication::allWindows())if(candidate->isVisible()) {
        auto content=candidate->property("contentItem").value<QObject *>();
        if(auto result=find(content,name)){if(owner)*owner=candidate;return result;}
    }
    return nullptr;
}
static QVariant invoke(const char *method,const QVariant &argument={}) {
    QVariant result;
    if(argument.isValid())QMetaObject::invokeMethod(fixture,method,Qt::DirectConnection,Q_RETURN_ARG(QVariant,result),Q_ARG(QVariant,argument));
    else QMetaObject::invokeMethod(fixture,method,Qt::DirectConnection,Q_RETURN_ARG(QVariant,result));
    return result;
}
static QJsonObject state(){return QJsonDocument::fromJson(invoke("state").toString().toUtf8()).object();}
static bool click(const QString &name) {
    QWindow *owner=nullptr;auto target=item(name,&owner);
    const auto map=reinterpret_cast<Map>(dlsym(RTLD_DEFAULT,"_ZNK10QQuickItem9mapToItemEPKS_RK7QPointF"));
    if(!target || !owner || !map)return false;
    auto content=owner->property("contentItem").value<QObject *>();
    auto point=map(target,content,QPointF(target->property("width").toDouble()/2,target->property("height").toDouble()/2));
    QTest::mouseMove(owner,point.toPoint());QTest::mouseClick(owner,Qt::LeftButton,Qt::NoModifier,point.toPoint());
    return true;
}
static QJsonObject target(const QJsonObject &snapshot,int index) {
    const QString title=index==3 ? "DomainOS Wayland group outsider" : owned[index]->windowTitle();
    for(auto value:snapshot["windows"].toArray())if(value.toObject()["title"].toString()==title)return value.toObject();
    return {};
}
static QString key(int index){return identities[index].toObject()["key"].toString();}
static QSet<QString> set(const QJsonArray &array) {
    QSet<QString> result;for(auto value:array)result.insert(value.toString().remove('{').remove('}'));return result;
}
static QJsonArray presented(const QJsonObject &snapshot) {
    QJsonArray result;for(auto value:snapshot["rows"].toArray()) {
        auto row=value.toObject();if(row["group"].toBool())for(auto member:row["members"].toArray())result.append(member.toObject()["key"]);
        else result.append(row["key"]);
    }
    return result;
}
static QJsonObject materialState(const QJsonObject &record) {
    return QJsonObject{{"key",record["key"]},{"pid",record["pid"]},{"geometry",record["geometry"]},
        {"minimized",record["minimized"]},{"maximized",record["maximized"]},{"desktops",record["desktopIds"]}};
}
static bool untouched(const QJsonObject &before,const QJsonObject &after,int index) {
    return materialState(target(before,index))==materialState(target(after,index));
}
static bool allMaterialUnchanged(const QJsonObject &before,const QJsonObject &after) {
    for(int index=0;index<4;++index)if(!untouched(before,after,index))return false;return true;
}
static bool selectedExactly(const QJsonObject &snapshot) {return set(snapshot["selected"].toArray())==set(QJsonArray{key(0),key(1)});}
static QJsonObject lastReport(const QJsonObject &snapshot){const auto reports=snapshot["reports"].toArray();return reports.isEmpty() ? QJsonObject() : reports.last().toObject();}
static bool reportReady(const QJsonObject &snapshot,int count,const QString &mode) {
    const auto result=lastReport(snapshot);
    return snapshot["reports"].toArray().size()==count && result["ok"].toBool()
        && result["outcome"].toString()=="confirmed" && result["mode"].toString()==mode;
}
static bool reportOnlySelected(const QJsonObject &snapshot) {
    QJsonArray keys;for(auto value:lastReport(snapshot)["windows"].toArray())keys.append("window:"+value.toObject()["id"].toString());
    return set(keys)==set(QJsonArray{key(0),key(1)});
}
static bool captureItem(const QString &name,const char *variable) {
    QWindow *owner=nullptr;auto target=item(name,&owner);
    const auto grab=reinterpret_cast<Grab>(dlsym(RTLD_DEFAULT,"_ZN12QQuickWindow10grabWindowEv"));
    return target && owner && grab && grab(owner).save(qEnvironmentVariable(variable));
}
static void complete() {
    auto grab=reinterpret_cast<Grab>(dlsym(RTLD_DEFAULT,"_ZN12QQuickWindow10grabWindowEv"));
    checks["native_host_frame_saved"]=host && grab && grab(host).save(qEnvironmentVariable("IRIX_DOMAINOS_GROUP_CAPTURE"));
    QJsonObject report{{"checks",checks},{"snapshots",snapshots},{"state",fixture ? state() : QJsonObject()},
        {"identities",identities},{"host_pid",int(getpid())},{"host_executable",QFile::symLinkTarget("/proc/self/exe")}};
    QJsonObject environment;
    for(const auto name:QStringList{"HOME","XDG_CONFIG_HOME","XDG_DATA_HOME","XDG_RUNTIME_DIR","WAYLAND_DISPLAY","DBUS_SESSION_BUS_ADDRESS","DBUS_SYSTEM_BUS_ADDRESS","PULSE_SERVER"})environment[name]=qEnvironmentVariable(name.toLocal8Bit().constData());
    report["host_namespace_after_exec"]=environment;
    QFile file(qEnvironmentVariable("IRIX_DOMAINOS_GROUP_REPORT"));if(file.open(QIODevice::WriteOnly))file.write(QJsonDocument(report).toJson());
    for(auto widget:owned)widget->close();QCoreApplication::quit();
}
static void tick() {
    if(++attempts>260){checks["native_scenario_completed"]=false;complete();return;}
    if(!fixture) {
        fixture=item("domainosGroupsWaylandFixture",&host);
        if(!fixture){QTimer::singleShot(100,tick);return;}
        host->setFlags(Qt::Tool|Qt::FramelessWindowHint);host->resize(594,150);host->show();
    }
    const auto current=state();
    if(phase==0) {
        if(current["count"].toInt()!=4 || current["rows"].toArray().size()!=2 || current["members"].toArray().size()!=3 || !current["backendAvailable"].toBool()) {QTimer::singleShot(100,tick);return;}
        bool valid=true;QSet<QString> ids;
        for(int index=0;index<4;++index) {
            auto record=target(current,index);if(record.isEmpty()){QTimer::singleShot(100,tick);return;}
            auto id=record["windowIds"].toArray().first().toString();
            valid &= !QUuid(id).isNull() && record["pid"].toInt()==(index<3 ? getpid() : qEnvironmentVariableIntValue("IRIX_DOMAINOS_GROUP_OUTSIDER_PID"));
            ids.insert(id);identities.append(QJsonObject{{"key",record["key"]},{"pid",record["pid"]},{"windowIds",record["windowIds"]},{"title",record["title"]}});
        }
        checks["four_owned_native_uuid_pid_identities"]=valid && ids.size()==4;
        checks["three_windows_one_native_group_plus_independent_task"]=current["members"].toArray().size()==3 && current["rows"].toArray().size()==2 && target(current,3)["appId"]!=target(current,0)["appId"];
        checks["window_count_precedes_native_grouping"]=current["count"].toInt()==4 && current["count"].toInt()>current["rows"].toArray().size();
        checks["legitimate_installed_plasmawindowed_host"]=QFile::symLinkTarget("/proc/self/exe")=="/usr/bin/plasmawindowed";
        snapshots["initial"]=current;owned[0]->showMinimized();phase=-3;
    } else if(phase==-3) {
        if(!target(current,0)["minimized"].toBool()){QTimer::singleShot(100,tick);return;}
        checks["owned_member_is_minimized_before_title_restore"]=true;
        snapshots["before_title_restore"]=current;
        checks["unselected_group_opened_by_actual_pointer"]=click("domainosLiveTask_"+current["groupKey"].toString());phase=-2;
    } else if(phase==-2) {
        if(!current["groupPopup"].toBool() || !item("domainosGroupMemberTitle_"+key(0))){QTimer::singleShot(100,tick);return;}
        checks["unselected_native_group_capture_saved"]=captureItem("domainosGroupMemberTitle_"+key(0),"IRIX_DOMAINOS_GROUP_UNSELECTED_CAPTURE");
        checks["unselected_native_member_title_clicked"]=current["selected"].toArray().isEmpty() && click("domainosGroupMemberTitle_"+key(0));phase=-1;
    } else if(phase==-1) {
        if(target(current,0)["minimized"].toBool() || !target(current,0)["active"].toBool() || !owned[0]->isActiveWindow() || current["groupPopup"].toBool()){QTimer::singleShot(100,tick);return;}
        const auto requests=current["requests"].toArray();
        checks["group_title_restores_and_activates_actual_minimized_owned_client"]=true;
        checks["title_restore_uses_only_clicked_native_uuid_and_pid"]=requests.size()==1
            && requests[0].toObject()["action"].toString()=="activate" && requests[0].toObject()["key"].toString()==key(0)
            && target(current,0)["pid"].toInt()==getpid() && target(current,0)["windowIds"]==identities[0].toObject()["windowIds"];
        checks["native_title_restore_keeps_checkbox_selection_empty"]=current["selected"].toArray().isEmpty();
        checks["native_title_restore_does_not_touch_other_owned_windows"]=untouched(snapshots["before_title_restore"].toObject(),current,1)
            && untouched(snapshots["before_title_restore"].toObject(),current,2) && untouched(snapshots["before_title_restore"].toObject(),current,3);
        snapshots["title_restored"]=current;
        checks["group_opened_by_actual_pointer"]=click("domainosLiveTask_"+current["groupKey"].toString());phase=1;
    } else if(phase==1) {
        if(!current["groupPopup"].toBool() || !item("domainosGroupMember_"+key(0))){QTimer::singleShot(100,tick);return;}
        checks["opening_group_never_selects_all_members"]=current["selected"].toArray().isEmpty();
        QWindow *popup=nullptr;item("domainosGroupMember_"+key(0),&popup);
        checks["checkboxes_live_in_native_popup_window"]=popup && popup!=host;
        checks["first_real_member_checkbox_clicked"]=click("domainosGroupMember_"+key(0));
        checks["second_real_member_checkbox_clicked"]=click("domainosGroupMember_"+key(1));phase=2;
    } else if(phase==2) {
        if(!selectedExactly(current)){QTimer::singleShot(100,tick);return;}
        checks["two_checkboxes_select_exact_native_window_uuids"]=selectedExactly(current);
        checks["remaining_group_member_and_independent_task_not_selected"]=!current["selected"].toArray().contains(key(2)) && !current["selected"].toArray().contains(key(3));
        checks["partial_group_selection_count_is_two"]=current["groupSelection"].toObject()["count"].toInt()==2 && current["groupSelection"].toObject()["partial"].toBool();
        snapshots["selected"]=current;
        checks["selected_native_group_capture_saved"]=captureItem("domainosGroupMemberTitle_"+key(0),"IRIX_DOMAINOS_GROUP_SELECTED_CAPTURE");
        checks["selected_mode_member_title_clicked"]=click("domainosGroupMemberTitle_"+key(2));phase=21;
    } else if(phase==21) {
        if(set(current["selected"].toArray())!=set(QJsonArray{key(0),key(1),key(2)})){QTimer::singleShot(100,tick);return;}
        checks["title_in_checkbox_mode_adds_without_native_activation"]=current["requests"]==snapshots["selected"].toObject()["requests"]
            && allMaterialUnchanged(snapshots["selected"].toObject(),current) && current["groupPopup"].toBool();
        checks["selected_mode_member_title_clicked_again"]=click("domainosGroupMemberTitle_"+key(2));phase=22;
    } else if(phase==22) {
        if(!selectedExactly(current)){QTimer::singleShot(100,tick);return;}
        checks["title_in_checkbox_mode_removes_without_native_activation"]=current["requests"]==snapshots["selected"].toObject()["requests"]
            && allMaterialUnchanged(snapshots["selected"].toObject(),current) && current["groupPopup"].toBool();
        checks["group_operations_button_clicked"]=click("domainosGroupOrganize");phase=3;
    } else if(phase==3) {
        if(!current["operationsPopup"].toBool()){QTimer::singleShot(100,tick);return;}
        checks["columns_menu_clicked"]=click("domainosBatchColumns");phase=4;
    } else if(phase==4) {
        if(!reportReady(current,1,"columns") || target(current,0)["geometry"]==target(snapshots["selected"].toObject(),0)["geometry"]) {QTimer::singleShot(100,tick);return;}
        checks["production_window_ops_columns_confirmed_by_kwin"]=true;
        checks["columns_helper_reports_only_two_selected_uuids"]=reportOnlySelected(current);
        checks["columns_configures_actual_owned_clients"]=owned[0]->width()>260 && owned[1]->width()>260;
        checks["columns_does_not_change_remaining_group_member"]=untouched(snapshots["selected"].toObject(),current,2);
        checks["columns_does_not_change_independent_task"]=untouched(snapshots["selected"].toObject(),current,3);
        checks["selection_survives_confirmed_columns"]=selectedExactly(current);
        snapshots["columns"]=current;
        checks["selected_group_reopened_without_reset"]=click("domainosLiveTask_"+current["groupKey"].toString());phase=5;
    } else if(phase==5) {
        if(!current["groupPopup"].toBool()){QTimer::singleShot(100,tick);return;}
        checks["group_reopen_preserves_member_checkboxes"]=selectedExactly(current);
        checks["minimize_operations_button_clicked"]=click("domainosGroupOrganize");phase=6;
    } else if(phase==6) {
        if(!current["operationsPopup"].toBool()){QTimer::singleShot(100,tick);return;}
        checks["minimize_menu_clicked"]=click("domainosBatchMinimize");phase=7;
    } else if(phase==7) {
        if(!reportReady(current,2,"minimize") || !target(current,0)["minimized"].toBool() || !target(current,1)["minimized"].toBool()) {QTimer::singleShot(100,tick);return;}
        checks["production_window_ops_minimize_confirmed_by_kwin"]=true;
        checks["minimize_helper_reports_only_two_selected_uuids"]=reportOnlySelected(current);
        // xdg_toplevel has no minimized configure state. Observe the actual
        // KWin state through the native TasksModel, independently of the
        // helper's completion callback; QWidget::isMinimized is not proof.
        checks["minimize_confirmed_by_fresh_native_task_model"]=target(current,0)["minimized"].toBool() && target(current,1)["minimized"].toBool() && reportOnlySelected(current);
        checks["batch_minimize_leaves_unselected_group_member_and_task_untouched"]=untouched(snapshots["columns"].toObject(),current,2) && untouched(snapshots["columns"].toObject(),current,3);
        snapshots["minimized"]=current;invoke("action","automatic");phase=8;
    } else if(phase==8) {
        if(!current["effective"].toBool() || presented(current).size()!=2){QTimer::singleShot(100,tick);return;}
        checks["n_greater_than_l_uses_pre_group_pre_filter_count"]=current["count"].toInt()==4 && current["threshold"].toInt()==3 && current["rows"].toArray().size()==1;
        checks["automatic_filter_presents_only_native_minimized_members"]=set(presented(current))==set(QJsonArray{key(0),key(1)});
        checks["enabling_automatic_filter_changes_no_native_window"]=allMaterialUnchanged(snapshots["minimized"].toObject(),current);
        snapshots["automatic_above"]=current;invoke("action","equalFour");phase=9;
    } else if(phase==9) {
        if(current["effective"].toBool() || presented(current).size()!=4){QTimer::singleShot(100,tick);return;}
        checks["n_equals_l_restores_normal_presentation"]=current["count"].toInt()==4 && current["threshold"].toInt()==4 && current["rows"].toArray().size()==2;
        checks["threshold_equality_changes_no_native_window"]=allMaterialUnchanged(snapshots["automatic_above"].toObject(),current);
        snapshots["automatic_equal"]=current;invoke("action","aboveAgain");phase=10;
    } else if(phase==10) {
        if(!current["effective"].toBool() || presented(current).size()!=2){QTimer::singleShot(100,tick);return;}
        checks["explicit_native_restore_request_sent"]=invoke("action","restoreFirst").toBool();phase=11;
    } else if(phase==11) {
        if(target(current,0)["minimized"].toBool() || !target(current,0)["active"].toBool() || !owned[0]->isActiveWindow() || presented(current).size()!=1){QTimer::singleShot(100,tick);return;}
        checks["native_restore_does_not_change_n"]=current["count"].toInt()==4 && current["effective"].toBool();
        checks["native_restore_updates_presentation_without_circular_count"]=set(presented(current))==set(QJsonArray{key(1)});
        checks["native_restore_confirmed_by_actual_client_focus"]=owned[0]->isActiveWindow();
        checks["filter_does_not_reminimize_restored_native_window"]=!target(current,0)["minimized"].toBool();
        snapshots["one_restored"]=current;owned[2]->close();phase=12;
    } else if(phase==12) {
        if(current["count"].toInt()!=3 || current["effective"].toBool() || presented(current).size()!=3){QTimer::singleShot(100,tick);return;}
        checks["native_window_close_recounts_before_filter_and_grouping"]=target(current,2).isEmpty() && current["count"].toInt()==3 && current["rows"].toArray().size()==2;
        checks["n_equals_l_after_real_close_restores_normal_mode"]=current["threshold"].toInt()==3 && set(presented(current))==set(QJsonArray{key(0),key(1),key(3)});
        checks["normal_presentation_keeps_restored_and_unselected_clients_unminimized"]=!target(current,0)["minimized"].toBool() && !target(current,3)["minimized"].toBool() && target(current,1)["minimized"].toBool();
        checks["selection_survives_automatic_filter_and_unselected_close"]=selectedExactly(current);
        snapshots["automatic_after_close"]=current;invoke("action","below");phase=13;
    } else if(phase==13) {
        if(current["threshold"].toInt()!=4 || current["effective"].toBool()){QTimer::singleShot(100,tick);return;}
        checks["n_less_than_l_preserves_normal_presentation"]=current["count"].toInt()==3 && presented(current).size()==3;
        const auto requests=current["requests"].toArray();
        checks["automatic_filter_sends_no_minimize_layout_or_close_operation"]=current["reports"].toArray().size()==2 && requests.size()==4
            && requests[0].toObject()["action"].toString()=="activate" && requests[0].toObject()["key"].toString()==key(0)
            && requests[1].toObject()["action"].toString()=="columns" && requests[2].toObject()["action"].toString()=="minimize"
            && requests[3].toObject()["action"].toString()=="activate" && requests[3].toObject()["key"].toString()==key(0);
        checks["independent_task_remains_untouched_through_filtering"]=untouched(snapshots["minimized"].toObject(),current,3);
        checks["native_scenario_completed"]=true;snapshots["final"]=current;complete();return;
    }
    QTimer::singleShot(150,tick);
}
extern "C" int interceptedExec() asm("_ZN12QApplication4execEv");
extern "C" int interceptedExec() {
    const auto original=reinterpret_cast<int (*)()>(dlsym(RTLD_NEXT,"_ZN12QApplication4execEv"));if(!original)return 2;
    for(int index=0;index<3;++index) {
        auto widget=new QWidget;widget->setWindowTitle(QString("DomainOS Wayland group member %1").arg(index));
        widget->resize(260,160);widget->show();owned.append(widget);
    }
    QTimer::singleShot(1200,tick);return original();
}
