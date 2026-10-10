// SPDX-FileCopyrightText: 2026 IRIX Classic contributors
// SPDX-License-Identifier: GPL-3.0-or-later
// Own-window proof: checkbox accumulation across two native groups.
#include <QApplication>
#include <QFile>
#include <QImage>
#include <QJsonArray>
#include <QJsonDocument>
#include <QJsonObject>
#include <QMenu>
#include <QSet>
#include <QStyle>
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
static QString firstGroup,secondGroup;
static int phase=0,attempts=0;
static bool preflightDone=false;
static int menuCycle=0;
static bool popupRegression(){return qEnvironmentVariableIntValue("IRIX_DOMAINOS_POPUP_REGRESSION")==1;}
static QObject *find(QObject *object,const QString &name) {
    if(!object)return nullptr;
    if(object->objectName()==name)return object;
    const auto children=reinterpret_cast<Children>(dlsym(RTLD_DEFAULT,"_ZNK10QQuickItem10childItemsEv"));
    if(children && object->inherits("QQuickItem"))for(auto child:children(object))if(auto result=find(child,name))return result;
    return nullptr;
}
static QObject *item(const QString &name,QWindow **owner=nullptr) {
    for(auto candidate:QGuiApplication::allWindows())if(candidate->isVisible())
        if(auto result=find(candidate->property("contentItem").value<QObject *>(),name)) {
            if(owner)*owner=candidate;return result;
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
static bool click(const QString &name,Qt::MouseButton button=Qt::LeftButton) {
    QWindow *owner=nullptr;auto target=item(name,&owner);
    const auto map=reinterpret_cast<Map>(dlsym(RTLD_DEFAULT,"_ZNK10QQuickItem9mapToItemEPKS_RK7QPointF"));
    if(!target || !owner || !map || !target->property("enabled").toBool())return false;
    auto point=map(target,owner->property("contentItem").value<QObject *>(),
        QPointF(target->property("width").toDouble()/2,target->property("height").toDouble()/2));
    QTest::mouseMove(owner,point.toPoint());QTest::mouseClick(owner,button,Qt::NoModifier,point.toPoint());
    return true;
}
static QMenu *visibleNativeMenu() {
    for(auto widget:QApplication::allWidgets())if(auto menu=qobject_cast<QMenu *>(widget);menu && menu->isVisible())return menu;
    return nullptr;
}
static QJsonObject menuGeometry(QMenu *menu) {
    QJsonArray actions;bool allInside=true;int visible=0;
    for(auto action:menu->actions())if(action->isVisible()) {
        const auto rectangle=menu->actionGeometry(action);++visible;
        const bool inside=menu->rect().contains(rectangle);allInside &= inside;
        actions.append(QJsonObject{{"text",action->text()},{"x",rectangle.x()},{"y",rectangle.y()},
            {"width",rectangle.width()},{"height",rectangle.height()},{"inside",inside}});
    }
    return {{"width",menu->width()},{"height",menu->height()},{"visible_actions",visible},{"all_inside",allInside},{"actions",actions}};
}
static bool fullyInside(const QString &name) {
    QWindow *owner=nullptr;auto target=item(name,&owner);
    const auto map=reinterpret_cast<Map>(dlsym(RTLD_DEFAULT,"_ZNK10QQuickItem9mapToItemEPKS_RK7QPointF"));
    if(!target || !owner || !map)return false;
    const auto root=owner->property("contentItem").value<QObject *>();
    const auto top=map(target,root,QPointF(0,0));
    const auto bottom=map(target,root,QPointF(target->property("width").toDouble(),target->property("height").toDouble()));
    return target->property("visible").toBool() && top.x()>=0 && top.y()>=0 && bottom.x()<=owner->width()+1 && bottom.y()<=owner->height()+1;
}
static QJsonObject target(const QJsonObject &snapshot,int index) {
    const auto title=QString("DomainOS CrossGroup %1%2").arg(index<3 ? "A" : "B").arg(index<3 ? index : index-3);
    for(auto value:snapshot["windows"].toArray())if(value.toObject()["title"].toString()==title)return value.toObject();
    return {};
}
static QString key(int index){return identities[index].toObject()["key"].toString();}
static QSet<QString> keys(const QJsonArray &array) {
    QSet<QString> result;for(auto value:array)result.insert(value.toString().remove('{').remove('}'));return result;
}
static QJsonObject groupFor(const QJsonObject &snapshot,const QString &memberKey) {
    for(auto value:snapshot["groups"].toArray()) {
        const auto group=value.toObject();
        for(auto member:group["members"].toArray())if(member.toObject()["key"].toString()==memberKey)return group;
    }
    return {};
}
static QJsonObject material(const QJsonObject &record) {
    return {{"key",record["key"]},{"pid",record["pid"]},{"geometry",record["geometry"]},
        {"minimized",record["minimized"]},{"maximized",record["maximized"]},{"desktops",record["desktopIds"]}};
}
static bool unchanged(const QJsonObject &before,const QJsonObject &after,int index) {
    return !target(before,index).isEmpty() && material(target(before,index))==material(target(after,index));
}
static bool unselectedUnchanged(const QJsonObject &before,const QJsonObject &after) {
    return unchanged(before,after,1) && unchanged(before,after,2) && unchanged(before,after,4);
}
static bool allUnchanged(const QJsonObject &before,const QJsonObject &after) {
    for(int index=0;index<5;++index)if(!unchanged(before,after,index))return false;return true;
}
static bool selectedExactly(const QJsonObject &snapshot) {return keys(snapshot["selected"].toArray())==keys(QJsonArray{key(0),key(3)});}
static QJsonObject lastReport(const QJsonObject &snapshot) {
    const auto reports=snapshot["reports"].toArray();return reports.isEmpty() ? QJsonObject() : reports.last().toObject();
}
static bool reportReady(const QJsonObject &snapshot,int count,const QString &mode) {
    const auto result=lastReport(snapshot);
    return snapshot["reports"].toArray().size()==count && result["ok"].toBool()
        && result["outcome"].toString()=="confirmed" && result["mode"].toString()==mode;
}
static bool reportedExact(const QJsonObject &snapshot) {
    const auto windows=lastReport(snapshot)["windows"].toArray();QJsonArray returned;
    for(auto value:windows) {
        const auto window=value.toObject();returned.append("window:"+window["id"].toString());
        const auto id=window["id"].toString().remove('{').remove('}');
        bool ownedIdentity=false;
        for(int index:{0,3}) {
            const auto record=identities[index].toObject();
            ownedIdentity |= record["windowIds"].toArray().first().toString().remove('{').remove('}')==id
                && record["pid"].toInt()==window["pid"].toInt();
        }
        if(!ownedIdentity)return false;
    }
    return windows.size()==2 && keys(returned)==keys(QJsonArray{key(0),key(3)});
}
static QJsonArray presented(const QJsonObject &snapshot) {
    QJsonArray result;for(auto value:snapshot["rows"].toArray()) {
        const auto row=value.toObject();if(row["group"].toBool())
            for(auto member:row["members"].toArray())result.append(member.toObject()["key"]);
        else result.append(row["key"]);
    }
    return result;
}
static bool capture(const QString &name,const QString &filename) {
    QWindow *owner=nullptr;auto target=item(name,&owner);
    const auto grab=reinterpret_cast<Grab>(dlsym(RTLD_DEFAULT,"_ZN12QQuickWindow10grabWindowEv"));
    return target && owner && grab && grab(owner).save(qEnvironmentVariable("IRIX_DOMAINOS_CROSS_DIR")+"/"+filename);
}
static void complete() {
    QJsonObject environment;
    for(const auto name:QStringList{"HOME","XDG_CONFIG_HOME","XDG_DATA_HOME","XDG_RUNTIME_DIR","WAYLAND_DISPLAY","DBUS_SESSION_BUS_ADDRESS","DBUS_SYSTEM_BUS_ADDRESS","PULSE_SERVER"})
        environment[name]=qEnvironmentVariable(name.toLocal8Bit().constData());
    const auto expectedStyle=qEnvironmentVariable("IRIX_DOMAINOS_EXPECT_STYLE");
    if(!expectedStyle.isEmpty()) checks["requested_private_widget_style_loaded"]=QApplication::style()->objectName().contains(expectedStyle,Qt::CaseInsensitive);
    QJsonObject report{{"checks",checks},{"snapshots",snapshots},{"state",fixture ? state() : QJsonObject()},
        {"identities",identities},{"phase",phase},{"host_pid",int(getpid())},
        {"widget_style",QApplication::style()->objectName()},
        {"host_executable",QFile::symLinkTarget("/proc/self/exe")},{"host_namespace_after_exec",environment}};
    QFile file(qEnvironmentVariable("IRIX_DOMAINOS_CROSS_REPORT"));if(file.open(QIODevice::WriteOnly))file.write(QJsonDocument(report).toJson());
    for(auto widget:owned)widget->close();QCoreApplication::quit();
}
static void tick() {
    if(++attempts>(popupRegression()?300:220)){checks["native_scenario_completed"]=false;complete();return;}
    if(!fixture) {
        fixture=item("domainosCrossGroupsFixture",&host);
        if(!fixture){QTimer::singleShot(100,tick);return;}
        host->resize(594,150);
    }
    const auto current=state();
    if(phase==0) {
        if(current["count"].toInt()!=5 || current["groups"].toArray().size()!=2 || current["rows"].toArray().size()!=2 || !current["backendAvailable"].toBool()) {QTimer::singleShot(100,tick);return;}
        QJsonArray found;QSet<QString> ids;bool valid=true;
        for(int index=0;index<5;++index) {
            const auto record=target(current,index);
            if(record.isEmpty() || record["windowIds"].toArray().isEmpty()){QTimer::singleShot(100,tick);return;}
            const auto id=record["windowIds"].toArray().first().toString();
            const int expected=index<3 ? getpid() : qEnvironmentVariableIntValue(index==3 ? "IRIX_DOMAINOS_CROSS_B0_PID" : "IRIX_DOMAINOS_CROSS_B1_PID");
            valid &= !QUuid(id).isNull() && record["pid"].toInt()==expected;ids.insert(id);found.append(record);
        }
        identities=found;
        const auto a=groupFor(current,key(0)),b=groupFor(current,key(3));
        firstGroup=a["key"].toString();secondGroup=b["key"].toString();
        checks["five_owned_native_uuid_pid_identities"]=valid && ids.size()==5;
        checks["two_real_application_groups_have_three_and_two_members"]=a["members"].toArray().size()==3 && b["members"].toArray().size()==2 && firstGroup!=secondGroup;
        checks["second_group_uses_one_appid_and_two_distinct_owned_processes"]=target(current,3)["appId"]==target(current,4)["appId"] && target(current,3)["appId"]!=target(current,0)["appId"] && target(current,3)["pid"]!=target(current,4)["pid"];
        checks["n_counts_five_before_grouping_into_two"]=current["count"].toInt()==5 && current["rows"].toArray().size()==2;
        if(popupRegression() && !preflightDone) {
            invoke("ordinarySelection",key(0));phase=100;QTimer::singleShot(150,tick);return;
        }
        snapshots["initial"]=current;checks["first_group_opened_by_pointer"]=click("domainosLiveTask_"+firstGroup);phase=1;
    } else if(phase==100) {
        if(!target(current,0)["minimized"].toBool()){QTimer::singleShot(100,tick);return;}
        checks["ordinary_selected_member_has_no_checkbox_intention"]=keys(current["selected"].toArray())==keys(QJsonArray{key(0)}) && current["memberKeys"].toArray().isEmpty() && !current["memberActive"].toBool();
        checks["ordinary_member_group_opened_by_pointer"]=click("domainosLiveTask_"+firstGroup);phase=101;
    } else if(phase==101) {
        if(!current["groupPopup"].toBool() || !item("domainosGroupMemberTitle_"+key(0))){QTimer::singleShot(100,tick);return;}
        checks["ordinary_selected_member_checkbox_is_unchecked"]=!item("domainosGroupMember_"+key(0))->property("checked").toBool() && !current["memberActive"].toBool();
        checks["first_open_footer_and_operations_are_fully_inside_popup"]=fullyInside("domainosGroupContinue") && fullyInside("domainosGroupOrganize");
        checks["ordinary_selected_member_title_clicked_by_pointer"]=click("domainosGroupMemberTitle_"+key(0));phase=102;
    } else if(phase==102) {
        if(current["groupPopup"].toBool() || target(current,0)["minimized"].toBool() || !target(current,0)["active"].toBool()){QTimer::singleShot(100,tick);return;}
        checks["ordinary_title_restores_and_activates_actual_wayland_member_without_checkbox"]=current["memberKeys"].toArray().isEmpty() && keys(current["selected"].toArray())==keys(QJsonArray{key(0)});
        snapshots["title_restored"]=current;invoke("clearPreflight");preflightDone=true;phase=0;
    } else if(phase==1) {
        if(!current["groupPopup"].toBool() || !item("domainosGroupMember_"+key(0))){QTimer::singleShot(100,tick);return;}
        checks["opening_first_group_selects_no_members"]=current["selected"].toArray().isEmpty();
        checks["first_group_checkbox_clicked"]=click("domainosGroupMember_"+key(0));phase=2;
    } else if(phase==2) {
        if(keys(current["selected"].toArray())!=keys(QJsonArray{key(0)})){QTimer::singleShot(100,tick);return;}
        checks["first_checkbox_selects_only_one_uuid_without_operation"]=current["requests"].toArray().isEmpty() && current["reports"].toArray().isEmpty() && allUnchanged(snapshots["initial"].toObject(),current);
        snapshots["first_selected"]=current;checks["continue_selection_clicked"]=click("domainosGroupContinue");phase=3;
    } else if(phase==3) {
        if(current["groupPopup"].toBool()){QTimer::singleShot(100,tick);return;}
        checks["continue_keeps_selection_without_interrupting_with_operations"]=!current["operationsPopup"].toBool() && keys(current["selected"].toArray())==keys(QJsonArray{key(0)}) && current["requests"].toArray().isEmpty();
        snapshots["continued"]=current;checks["second_group_opened_by_pointer"]=click("domainosLiveTask_"+secondGroup);phase=4;
    } else if(phase==4) {
        if(!current["groupPopup"].toBool() || !item("domainosGroupMember_"+key(3))){QTimer::singleShot(100,tick);return;}
        checks["opening_second_group_preserves_first_member_without_selecting_second_group"]=keys(current["selected"].toArray())==keys(QJsonArray{key(0)});
        checks["second_group_checkbox_clicked"]=click("domainosGroupMember_"+key(3));phase=5;
    } else if(phase==5) {
        if(!selectedExactly(current)){QTimer::singleShot(100,tick);return;}
        checks["selection_accumulates_exactly_one_native_member_per_group"]=selectedExactly(current);
        checks["three_unchosen_members_remain_unselected_and_untouched"]=unselectedUnchanged(snapshots["initial"].toObject(),current) && current["selected"].toArray().size()==2;
        checks["checkboxes_do_not_activate_or_start_batch"]=current["requests"].toArray().isEmpty() && current["reports"].toArray().isEmpty() && !current["operationsPopup"].toBool() && allUnchanged(snapshots["initial"].toObject(),current);
        checks["each_group_has_one_partial_checkbox_selection"]=groupFor(current,key(0))["selection"].toObject()["count"].toInt()==1 && groupFor(current,key(3))["selection"].toObject()["count"].toInt()==1;
        checks["second_group_selection_frame_saved"]=capture("domainosGroupMember_"+key(3),"GROUP-B-SELECTED.png");
        snapshots["combined_selected"]=current;checks["continue_second_group_clicked"]=click("domainosGroupContinue");phase=6;
    } else if(phase==6) {
        if(current["groupPopup"].toBool()){QTimer::singleShot(100,tick);return;}
        checks["first_group_reopened_by_pointer"]=click("domainosLiveTask_"+firstGroup);phase=7;
    } else if(phase==7) {
        if(!current["groupPopup"].toBool() || !item("domainosGroupMember_"+key(0))){QTimer::singleShot(100,tick);return;}
        checks["cross_group_selection_survives_continuation_and_reopening"]=selectedExactly(current) && item("domainosGroupMember_"+key(0))->property("checked").toBool() && !item("domainosGroupMember_"+key(1))->property("checked").toBool();
        checks["first_group_selection_frame_saved"]=capture("domainosGroupMember_"+key(0),"GROUP-A-SELECTED.png");
        checks["operations_opened_from_revisited_group"]=click("domainosGroupOrganize");phase=8;
    } else if(phase==8) {
        if(!current["operationsPopup"].toBool()){QTimer::singleShot(100,tick);return;}
        checks["group_unmapped_before_operations_are_visible"]=!current["groupPopup"].toBool();
        checks["first_operations_menu_all_items_fit_native_window"]=fullyInside("domainosBatchColumns") && fullyInside("domainosBatchMinimize");
        checks["columns_menu_clicked_by_pointer"]=click("domainosBatchColumns");phase=9;
    } else if(phase==9) {
        if(!reportReady(current,1,"columns") || target(current,0)["geometry"]==target(snapshots["initial"].toObject(),0)["geometry"] || target(current,3)["geometry"]==target(snapshots["initial"].toObject(),3)["geometry"]){QTimer::singleShot(100,tick);return;}
        checks["columns_backend_confirms_exact_two_uuids_and_pids"]=reportedExact(current);
        checks["columns_native_model_and_client_receive_geometry"]=owned[0]->width()>260 && target(current,0)["geometry"]!=target(current,3)["geometry"];
        checks["columns_excludes_three_unselected_members"]=unselectedUnchanged(snapshots["initial"].toObject(),current);
        checks["columns_preserves_cross_group_selection"]=selectedExactly(current);
        snapshots["columns"]=current;checks["second_group_reopened_after_columns"]=click("domainosLiveTask_"+secondGroup);phase=10;
    } else if(phase==10) {
        if(!current["groupPopup"].toBool()){QTimer::singleShot(100,tick);return;}
        checks["minimize_operations_opened_by_pointer"]=click("domainosGroupOrganize");phase=11;
    } else if(phase==11) {
        if(!current["operationsPopup"].toBool()){QTimer::singleShot(100,tick);return;}
        checks["minimize_menu_clicked_by_pointer"]=click("domainosBatchMinimize");phase=12;
    } else if(phase==12) {
        if(!reportReady(current,2,"minimize") || !target(current,0)["minimized"].toBool() || !target(current,3)["minimized"].toBool()){QTimer::singleShot(100,tick);return;}
        checks["minimize_backend_confirms_exact_two_uuids_and_pids"]=reportedExact(current);
        checks["minimize_is_independently_observed_in_native_tasksmodel"]=target(current,0)["minimized"].toBool() && target(current,3)["minimized"].toBool();
        checks["minimize_excludes_three_unselected_members"]=unselectedUnchanged(snapshots["columns"].toObject(),current);
        checks["minimize_preserves_cross_group_selection"]=selectedExactly(current);
        snapshots["minimized"]=current;invoke("threshold",4);phase=13;
    } else if(phase==13) {
        if(!current["effective"].toBool() || presented(current).size()!=2){QTimer::singleShot(100,tick);return;}
        checks["automatic_n_five_greater_than_l_four_before_filter_and_group"]=current["count"].toInt()==5 && current["threshold"].toInt()==4 && keys(presented(current))==keys(QJsonArray{key(0),key(3)});
        checks["automatic_above_changes_no_native_window"]=allUnchanged(snapshots["minimized"].toObject(),current);
        snapshots["automatic_above"]=current;invoke("threshold",5);phase=14;
    } else if(phase==14) {
        if(current["effective"].toBool() || presented(current).size()!=5){QTimer::singleShot(100,tick);return;}
        checks["automatic_n_equals_l_five_restores_five_windows_two_groups"]=current["count"].toInt()==5 && current["groups"].toArray().size()==2;
        checks["automatic_equal_changes_no_native_window"]=allUnchanged(snapshots["minimized"].toObject(),current);
        snapshots["automatic_equal"]=current;invoke("threshold",6);phase=15;
    } else if(phase==15) {
        if(current["effective"].toBool() || current["threshold"].toInt()!=6 || presented(current).size()!=5){QTimer::singleShot(100,tick);return;}
        checks["automatic_n_five_less_than_l_six_keeps_normal_presentation"]=current["count"].toInt()==5;
        checks["automatic_below_changes_no_native_window_or_selection"]=allUnchanged(snapshots["minimized"].toObject(),current) && selectedExactly(current);
        const auto requests=current["requests"].toArray();
        checks["only_columns_and_minimize_were_requested"]=requests.size()==2 && requests[0].toObject()["action"].toString()=="columns" && requests[1].toObject()["action"].toString()=="minimize";
        checks["all_five_native_identities_survive"]=current["count"].toInt()==5;
        snapshots["final"]=current;
        if(popupRegression()) {checks["native_context_opened_by_right_pointer"]=click("domainosLiveTask_"+firstGroup,Qt::RightButton);phase=200;}
        else {checks["native_scenario_completed"]=true;complete();return;}
    } else if(phase==200) {
        auto menu=visibleNativeMenu();
        if(!menu || !current["nativeMenuOpen"].toBool()){QTimer::singleShot(100,tick);return;}
        const auto geometry=menuGeometry(menu);snapshots["native_context_first_open"]=geometry;
        checks["native_qmenu_natural_first_open_needs_no_expansion"]=geometry["visible_actions"].toInt()>=8 && geometry["all_inside"].toBool() && menu->height()>200;
        checks["native_qmenu_first_open_screenshot_saved"]=menu->grab().save(qEnvironmentVariable("IRIX_DOMAINOS_CROSS_DIR")+"/NATIVE-CONTEXT-FIRST-OPEN.png");
        QTest::keyClick(menu,Qt::Key_Escape);phase=201;
    } else if(phase==201) {
        if(visibleNativeMenu() || current["nativeMenuOpen"].toBool()){QTimer::singleShot(100,tick);return;}
        if(menuCycle++<5) {checks[QString("native_context_alternating_anchor_cycle_%1").arg(menuCycle)]=click("domainosLiveTask_"+(menuCycle%2 ? secondGroup:firstGroup),Qt::RightButton);phase=202;}
        else {invoke("failMenuProvider");checks["provider_fault_opened_by_right_pointer"]=click("domainosLiveTask_"+firstGroup,Qt::RightButton);phase=203;}
    } else if(phase==202) {
        auto menu=visibleNativeMenu();if(!menu){QTimer::singleShot(100,tick);return;}
        checks[QString("native_context_reopen_cycle_%1_all_actions_inside").arg(menuCycle)]=menuGeometry(menu)["all_inside"].toBool();
        QTest::keyClick(menu,Qt::Key_Escape);phase=201;
    } else if(phase==203) {
        if(!current["basicPopup"].toBool() || !current["error"].toString().contains("PRIVATE_PROVIDER_FAILURE")){QTimer::singleShot(100,tick);return;}
        checks["provider_exception_is_reported_and_opens_working_fallback"]=!visibleNativeMenu() && !current["nativeMenuOpen"].toBool() && fullyInside("domainosBasicClose");
        checks["fallback_preserves_exact_cross_group_selection"]=selectedExactly(current);
        checks["native_scenario_completed"]=true;snapshots["provider_fallback"]=current;complete();return;
    }
    QTimer::singleShot(150,tick);
}
extern "C" int interceptedExec() asm("_ZN12QApplication4execEv");
extern "C" int interceptedExec() {
    const auto original=reinterpret_cast<int (*)()>(dlsym(RTLD_NEXT,"_ZN12QApplication4execEv"));if(!original)return 2;
    if(!qEnvironmentVariable("IRIX_DOMAINOS_EXPECT_STYLE").isEmpty()) QApplication::setStyle(qEnvironmentVariable("IRIX_DOMAINOS_EXPECT_STYLE"));
    for(int index=0;index<3;++index) {
        auto widget=new QWidget;widget->setWindowTitle(QString("DomainOS CrossGroup A%1").arg(index));
        widget->resize(260,160);widget->show();owned.append(widget);
    }
    QTimer::singleShot(1200,tick);return original();
}
