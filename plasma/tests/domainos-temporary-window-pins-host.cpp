// SPDX-FileCopyrightText: 2026 IRIX Classic contributors
// SPDX-License-Identifier: GPL-3.0-or-later
// Own native-window proof: accumulated selection and instance-only window pins.
#include <QApplication>
#include <QFile>
#include <QImage>
#include <QJsonArray>
#include <QJsonDocument>
#include <QJsonObject>
#include <QMenu>
#include <QPointer>
#include <QEventLoop>
#include <QScreen>
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
static bool popupRegression(){return false;}
static QPointer<QWindow> enteredWindow;
static int nativeTransitions=0;
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
static bool moveWindow(QWindow *window,const QPoint &point) {
    using Transition=void (*)(QWindow *,QWindow *,const QPointF &,const QPointF &);
    using Flush=bool (*)(QEventLoop::ProcessEventsFlags);
    const auto transition=reinterpret_cast<Transition>(dlsym(RTLD_DEFAULT,"_ZN22QWindowSystemInterface21handleEnterLeaveEventEP7QWindowS1_RK7QPointFS4_"));
    const auto flush=reinterpret_cast<Flush>(dlsym(RTLD_DEFAULT,"_ZN22QWindowSystemInterface23flushWindowSystemEventsE6QFlagsIN10QEventLoop17ProcessEventsFlagEE"));
    QPointer<QWindow> guarded=window;
    if(!guarded || !transition || !flush || !qFuzzyCompare(window->devicePixelRatio(),1.0))return false;
    if(enteredWindow!=window) {
        auto library=dlopen("libQt6WaylandClient.so.6",RTLD_NOW|RTLD_NOLOAD);
        auto grab=library?reinterpret_cast<void **>(dlsym(library,"_ZN15QtWaylandClient14QWaylandWindow10mMouseGrabE")):nullptr;
        const bool absent=grab && !*grab;
        checks["native_qpa_transitions_observe_wayland_mouse_grab_absent"]=absent;
        if(library)dlclose(library);
        if(!absent)return false;
        transition(window,enteredWindow,point,window->mapToGlobal(point));
        flush(QEventLoop::AllEvents);enteredWindow=guarded;++nativeTransitions;
        if(!guarded)return false;
    }
    QTest::mouseMove(guarded,point);return !guarded.isNull();
}
static bool click(const QString &name,Qt::MouseButton button=Qt::LeftButton) {
    QWindow *owner=nullptr;QPointer<QObject> target=item(name,&owner);QPointer<QWindow> guarded=owner;
    const auto map=reinterpret_cast<Map>(dlsym(RTLD_DEFAULT,"_ZNK10QQuickItem9mapToItemEPKS_RK7QPointF"));
    if(!target || !guarded || !map || !target->property("enabled").toBool())return false;
    auto point=map(target,owner->property("contentItem").value<QObject *>(),
        QPointF(target->property("width").toDouble()/2,target->property("height").toDouble()/2)).toPoint();
    if(!moveWindow(guarded,point) || !target || !guarded)return false;
    QTest::mouseClick(guarded,button,Qt::NoModifier,point);return true;
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
        {"widget_style",QApplication::style()->objectName()},{"qpa_enter_leave_transitions",nativeTransitions},
        {"host_executable",QFile::symLinkTarget("/proc/self/exe")},{"host_namespace_after_exec",environment}};
    QFile file(qEnvironmentVariable("IRIX_DOMAINOS_CROSS_REPORT"));if(file.open(QIODevice::WriteOnly))file.write(QJsonDocument(report).toJson());
    for(auto widget:owned)widget->close();QCoreApplication::quit();
}
static bool selected(const QJsonObject &snapshot,const QJsonArray &expected) {
    return keys(snapshot["selected"].toArray())==keys(expected) && snapshot["selected"].toArray().size()==expected.size();
}
static QJsonArray pinKeys(const QJsonObject &snapshot) {
    QJsonArray result;for(auto value:snapshot["pins"].toArray())result.append(value.toObject()["key"]);return result;
}
static bool pinPrefix(const QJsonObject &snapshot,const QJsonArray &expected) {
    const auto rows=snapshot["rows"].toArray();if(rows.size()<expected.size())return false;
    for(int index=0;index<expected.size();++index)if(rows[index].toObject()["key"]!=expected[index]
        || !rows[index].toObject()["temporaryPinned"].toBool() || rows[index].toObject()["group"].toBool())return false;
    return true;
}
static bool noWindowOperation(const QJsonObject &snapshot) {
    return snapshot["requests"].toArray().isEmpty() && snapshot["reports"].toArray().isEmpty();
}
static void tick() {
    if(++attempts>220){checks["native_scenario_completed"]=false;complete();return;}
    if(!fixture) {
        fixture=item("domainosCrossGroupsFixture",&host);
        if(!fixture){QTimer::singleShot(100,tick);return;}
        host->resize(594,150);
    }
    const auto current=state();
    snapshots["latest_phase"]=QJsonObject{{"phase",phase},{"state",current}};
    if(phase==0) {
        if(current["count"].toInt()!=5 || current["groups"].toArray().size()!=2 || current["rows"].toArray().size()!=2 || !current["backendAvailable"].toBool()){QTimer::singleShot(100,tick);return;}
        QJsonArray found;QSet<QString> ids;bool valid=true;
        for(int index=0;index<5;++index) {
            const auto record=target(current,index);
            if(record.isEmpty() || record["windowIds"].toArray().isEmpty()){QTimer::singleShot(100,tick);return;}
            const auto id=record["windowIds"].toArray().first().toString();
            const int expected=index<3 ? getpid() : qEnvironmentVariableIntValue(index==3 ? "IRIX_DOMAINOS_CROSS_B0_PID":"IRIX_DOMAINOS_CROSS_B1_PID");
            valid &= !QUuid(id).isNull() && record["pid"].toInt()==expected;ids.insert(id);found.append(record);
        }
        identities=found;firstGroup=groupFor(current,key(0))["key"].toString();secondGroup=groupFor(current,key(3))["key"].toString();
        checks["five_owned_native_uuid_pid_identities"]=valid && ids.size()==5;
        checks["two_native_groups_begin_with_three_and_two_members"]=groupFor(current,key(0))["members"].toArray().size()==3 && groupFor(current,key(3))["members"].toArray().size()==2;
        snapshots["initial"]=current;checks["first_pin_group_opened_by_pointer"]=click("domainosLiveTask_"+secondGroup);phase=1;
    } else if(phase==1) {
        if(!current["groupPopup"].toBool() || !item("domainosGroupMember_"+key(3))){QTimer::singleShot(100,tick);return;}
        checks["one_window_checkbox_clicked"]=click("domainosGroupMember_"+key(3));phase=2;
    } else if(phase==2) {
        if(!selected(current,QJsonArray{key(3)})){QTimer::singleShot(100,tick);return;}
        checks["one_checkbox_enables_operations_without_window_action"]=item("domainosGroupOrganize") && item("domainosGroupOrganize")->property("enabled").toBool() && noWindowOperation(current);
        checks["one_window_operations_clicked"]=click("domainosGroupOrganize");phase=3;
    } else if(phase==3) {
        if(!current["operationsPopup"].toBool()){QTimer::singleShot(100,tick);return;}
        checks["single_window_operations_contains_enabled_temporary_pin"]=item("domainosTemporaryPinSelection") && item("domainosTemporaryPinSelection")->property("enabled").toBool() && !current["groupPopup"].toBool();
        checks["single_window_geometry_action_remains_disabled"]=item("domainosBatchColumns") && !item("domainosBatchColumns")->property("enabled").toBool();
        checks["first_pin_clicked_by_pointer"]=click("domainosTemporaryPinSelection");phase=4;
    } else if(phase==4) {
        if(current["operationsPopup"].toBool() || !pinPrefix(current,QJsonArray{key(3)})){QTimer::singleShot(100,tick);return;}
        bool individual=false;
        for(auto value:current["rows"].toArray())individual |= value.toObject()["key"].toString()==key(4) && !value.toObject()["group"].toBool();
        checks["first_pin_is_specific_window_at_left_outside_group"]=pinKeys(current)==QJsonArray{key(3)} && individual && current["groups"].toArray().size()==1;
        checks["pin_keeps_n_five_and_every_identity_exactly_once"]=current["count"].toInt()==5 && presented(current).size()==5 && keys(presented(current)).size()==5;
        checks["pin_does_not_activate_minimize_resize_or_move_windows"]=noWindowOperation(current) && allUnchanged(snapshots["initial"].toObject(),current);
        snapshots["first_pin"]=current;invoke("clearPreflight");checks["group_selection_opened_after_first_pin"]=click("domainosLiveTask_"+firstGroup);phase=5;
    } else if(phase==5) {
        if(!current["groupPopup"].toBool() || !item("domainosGroupMember_"+key(0))){QTimer::singleShot(100,tick);return;}
        checks["group_checkbox_clicked_before_continue"]=click("domainosGroupMember_"+key(0));phase=6;
    } else if(phase==6) {
        if(!selected(current,QJsonArray{key(0)})){QTimer::singleShot(100,tick);return;}
        checks["group_continue_clicked"]=click("domainosGroupContinue");phase=7;
    } else if(phase==7) {
        if(current["groupPopup"].toBool()){QTimer::singleShot(100,tick);return;}
        checks["individual_title_opened_after_group_continue"]=click("domainosLiveTask_"+key(4));phase=8;
    } else if(phase==8) {
        if(!current["groupPopup"].toBool() || !item("domainosGroupMember_"+key(4))){QTimer::singleShot(100,tick);return;}
        checks["individual_chooser_preserves_explicit_group_checkbox"]=selected(current,QJsonArray{key(0)}) && current["memberKeys"].toArray()==QJsonArray{key(0)} && current["pickerCount"].toInt()==0;
        checks["individual_checkbox_clicked_after_group_continue"]=click("domainosGroupMember_"+key(4));phase=9;
    } else if(phase==9) {
        if(!selected(current,QJsonArray{key(0),key(4)})){QTimer::singleShot(100,tick);return;}
        checks["selection_accumulates_group_member_and_individual_window"]=current["memberKeys"].toArray()==QJsonArray{key(0),key(4)} && noWindowOperation(current);
        checks["individual_continue_clicked"]=click("domainosGroupContinue");phase=10;
    } else if(phase==10) {
        if(current["groupPopup"].toBool()){QTimer::singleShot(100,tick);return;}
        checks["group_reopened_with_accumulated_individual"]=click("domainosLiveTask_"+firstGroup);phase=11;
    } else if(phase==11) {
        if(!current["groupPopup"].toBool() || !item("domainosGroupMember_"+key(0))){QTimer::singleShot(100,tick);return;}
        checks["revisited_group_keeps_both_exact_checkbox_identities"]=selected(current,QJsonArray{key(0),key(4)}) && item("domainosGroupMember_"+key(0))->property("checked").toBool();
        checks["accumulated_operations_clicked"]=click("domainosGroupOrganize");phase=12;
    } else if(phase==12) {
        if(!current["operationsPopup"].toBool()){QTimer::singleShot(100,tick);return;}
        checks["operations_receives_both_accumulated_windows"]=keys(current["menuSelection"].toArray())==keys(QJsonArray{key(0),key(4)});
        checks["two_more_window_pins_clicked"]=click("domainosTemporaryPinSelection");phase=13;
    } else if(phase==13) {
        if(current["operationsPopup"].toBool() || !pinPrefix(current,QJsonArray{key(3),key(0),key(4)})){QTimer::singleShot(100,tick);return;}
        const auto resolved=QJsonDocument::fromJson(invoke("nativeTarget",key(0)).toString().toUtf8()).object();
        checks["later_pins_append_in_checkbox_choice_order"]=pinKeys(current)==QJsonArray{key(3),key(0),key(4)};
        checks["native_context_resolves_exact_child_uuid_pid_after_projection"]=resolved["key"].toString()==key(0) && resolved["pid"].toInt()==getpid() && resolved["child"].toInt()>=0;
        checks["projected_group_excludes_only_pinned_members"]=groupFor(current,key(1))["members"].toArray().size()==2 && !groupFor(current,key(1))["members"].toArray().contains(identities[0]);
        checks["pinning_batch_preserves_five_without_duplicate_or_backend_request"]=current["count"].toInt()==5 && presented(current).size()==5 && keys(presented(current)).size()==5 && noWindowOperation(current) && allUnchanged(snapshots["initial"].toObject(),current);
        snapshots["three_pins"]=current;checks["pinned_window_context_opened_by_right_pointer"]=click("domainosLiveTask_"+key(0),Qt::RightButton);phase=14;
    } else if(phase==14) {
        auto menu=visibleNativeMenu();if(!menu || !current["nativeMenuOpen"].toBool()){QTimer::singleShot(100,tick);return;}
        const auto actions=menu->actions();const auto first=actions.isEmpty()?nullptr:actions.first();
        checks["native_pinned_menu_first_action_is_unpin"]=first && first->isVisible() && first->isEnabled() && first->text().startsWith("Desafixar");
        checks["native_pinned_context_all_actions_inside"]=menuGeometry(menu)["all_inside"].toBool();
        snapshots["pinned_context"]=menuGeometry(menu);
        checks["native_unpin_first_action_clicked"]=first && (QTest::mouseClick(menu,Qt::LeftButton,Qt::NoModifier,menu->actionGeometry(first).center()),true);phase=15;
    } else if(phase==15) {
        if(visibleNativeMenu() || current["nativeMenuOpen"].toBool() || pinKeys(current)!=QJsonArray{key(3),key(4)}){QTimer::singleShot(100,tick);return;}
        checks["unpin_returns_exact_window_to_native_group"]=groupFor(current,key(0))["members"].toArray().size()==3 && pinPrefix(current,QJsonArray{key(3),key(4)});
        checks["unpin_leaves_other_pins_and_window_states_untouched"]=allUnchanged(snapshots["initial"].toObject(),current) && noWindowOperation(current);
        snapshots["unpin"]=current;invoke("clearPreflight");checks["own_group_opened_for_lifetime_pin"]=click("domainosLiveTask_"+firstGroup);phase=16;
    } else if(phase==16) {
        if(!current["groupPopup"].toBool() || !item("domainosGroupMember_"+key(1))){QTimer::singleShot(100,tick);return;}
        checks["lifetime_window_checkbox_clicked"]=click("domainosGroupMember_"+key(1));phase=17;
    } else if(phase==17) {
        if(!selected(current,QJsonArray{key(1)})){QTimer::singleShot(100,tick);return;}
        checks["lifetime_pin_operations_clicked"]=click("domainosGroupOrganize");phase=18;
    } else if(phase==18) {
        if(!current["operationsPopup"].toBool()){QTimer::singleShot(100,tick);return;}
        checks["lifetime_pin_clicked"]=click("domainosTemporaryPinSelection");phase=19;
    } else if(phase==19) {
        if(current["operationsPopup"].toBool() || pinKeys(current)!=QJsonArray{key(3),key(4),key(1)}){QTimer::singleShot(100,tick);return;}
        checks["lifetime_pin_uses_exact_owned_uuid_pid"]=pinPrefix(current,QJsonArray{key(3),key(4),key(1)}) && target(current,1)["pid"].toInt()==getpid();
        snapshots["before_owned_close"]=current;owned[1]->close();phase=20;
    } else if(phase==20) {
        if(current["count"].toInt()!=4 || pinKeys(current)!=QJsonArray{key(3),key(4)}){QTimer::singleShot(100,tick);return;}
        checks["closing_exact_owned_window_removes_only_its_temporary_pin"]=target(current,1).isEmpty() && pinPrefix(current,QJsonArray{key(3),key(4)});
        checks["closed_identity_removed_from_checkbox_set"]=current["selected"].toArray().isEmpty() && current["memberKeys"].toArray().isEmpty();
        checks["remaining_four_windows_keep_native_state"]=unchanged(snapshots["initial"].toObject(),current,0) && unchanged(snapshots["initial"].toObject(),current,2) && unchanged(snapshots["initial"].toObject(),current,3) && unchanged(snapshots["initial"].toObject(),current,4) && noWindowOperation(current);
        checks["genuine_qpa_enter_leave_transitions_used"]=nativeTransitions>=4;
        checks["native_scenario_completed"]=true;snapshots["final"]=current;complete();return;
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
