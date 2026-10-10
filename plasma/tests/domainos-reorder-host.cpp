// SPDX-FileCopyrightText: 2026 IRIX Classic contributors
// SPDX-License-Identifier: GPL-3.0-or-later
// Native pointer driver; owned widgets and private Plasma/KWin only.
#include <QApplication>
#include <QFile>
#include <QImage>
#include <QJsonArray>
#include <QJsonDocument>
#include <QJsonObject>
#include <QStyleHints>
#include <QProcess>
#include <QWheelEvent>
#include <QTest>
#include <QTimer>
#include <QWidget>
#include <QWindow>
#include <dlfcn.h>
#include <unistd.h>

using Children=QList<QObject *> (*)(QObject *);
using Grab=QImage (*)(QWindow *);
static QObject *fixture=nullptr;
static QWindow *window=nullptr;
static QList<QWidget *> owned;
static QJsonObject checks, snapshots;
static int phase=0,attempts=0;
static QPoint missingPress;
static int beforeWheelRequests=0;
static QObject *find(QObject *object,Children children) {
    if(!object)return nullptr;
    if(object->objectName()=="domainosReorderFixture")return object;
    if(object->inherits("QQuickItem"))for(auto child:children(object))if(auto result=find(child,children))return result;
    return nullptr;
}
static QVariant invoke(const char *method,const QVariant &argument=QVariant()) {
    QVariant result;
    if(argument.isValid())QMetaObject::invokeMethod(fixture,method,Qt::DirectConnection,Q_RETURN_ARG(QVariant,result),Q_ARG(QVariant,argument));
    else QMetaObject::invokeMethod(fixture,method,Qt::DirectConnection,Q_RETURN_ARG(QVariant,result));
    return result;
}
static QJsonObject state() {return QJsonDocument::fromJson(invoke("state").toString().toUtf8()).object();}
static QJsonObject coordinate(const QString &name) {return QJsonDocument::fromJson(invoke("coordinates",name).toString().toUtf8()).object();}
static QPoint point(const QString &name) {auto position=coordinate(name);return QPoint(qRound(position["x"].toDouble()),qRound(position["y"].toDouble()));}
static QJsonArray order(const QJsonObject &snapshot) {return snapshot["order"].toArray();}
static int position(const QJsonObject &snapshot,const QString &name) {
    const auto rows=snapshot["rows"].toArray();
    for(int index=0;index<rows.size();++index)if(rows[index].toObject()["title"].toString()=="DomainOS reorder "+name)return index;
    return -1;
}
static QJsonObject windows(const QJsonObject &snapshot) {
    QJsonObject result;
    for(auto value:snapshot["windows"].toArray()) {
        auto record=value.toObject();
        result[record["key"].toString()]=QJsonObject{{"title",record["title"]},{"pid",record["pid"]},{"geometry",record["geometry"]},
            {"active",record["active"]},{"minimized",record["minimized"]},{"maximized",record["maximized"]}};
    }
    return result;
}
static QStringList identities(const QJsonObject &snapshot) {
    QStringList result;for(auto row:snapshot["windows"].toArray())result.append(row.toObject()["key"].toString());result.sort();return result;
}
static void drag(const QString &source,const QString &target) {
    const QPoint start=point(source),end=point(target);
    const int threshold=QGuiApplication::styleHints()->startDragDistance();
    QTest::mouseMove(window,start);
    QTest::mousePress(window,Qt::LeftButton,Qt::NoModifier,start);
    QTest::mouseMove(window,start+QPoint(threshold+3,0),30);
    QTest::mouseMove(window,end,30);
    QTest::mouseRelease(window,Qt::LeftButton,Qt::NoModifier,end,30);
}
static void physical(const QStringList &arguments) {
    auto process=new QProcess(QCoreApplication::instance());
    QObject::connect(process,qOverload<int,QProcess::ExitStatus>(&QProcess::finished),process,[process](int,QProcess::ExitStatus){process->deleteLater();});
    process->start("xdotool",arguments);
}
static void wheel(const QString &name,int angle) {
    const auto global=window->mapToGlobal(point(name));
    physical({"mousemove",QString::number(global.x()),QString::number(global.y()),"click",angle>0 ? "4" : "5"});
}
static void doubleClick(const QString &name) {
    const auto global=window->mapToGlobal(point(name));
    physical({"mousemove",QString::number(global.x()),QString::number(global.y()),"click","--repeat","2","--delay","100","1"});
}
static void click(const QString &name) {
    const auto global=window->mapToGlobal(point(name));
    physical({"mousemove",QString::number(global.x()),QString::number(global.y()),"click","1"});
}
static void complete() {
    const auto grab=reinterpret_cast<Grab>(dlsym(RTLD_DEFAULT,"_ZN12QQuickWindow10grabWindowEv"));
    QJsonObject report{{"checks",checks},{"snapshots",snapshots},{"state",fixture ? state() : QJsonObject()},
        {"system_drag_distance",QGuiApplication::styleHints()->startDragDistance()},{"owned_pid",getpid()}};
    report["capture_saved"]=window && grab && grab(window).save(qEnvironmentVariable("IRIX_DOMAINOS_REORDER_CAPTURE"));
    QFile file(qEnvironmentVariable("IRIX_DOMAINOS_REORDER_REPORT"));
    if(file.open(QIODevice::WriteOnly))file.write(QJsonDocument(report).toJson());
    for(auto widget:owned)widget->close();
    QCoreApplication::quit();
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
        // Becoming Qt::Tool updates the native task model asynchronously. Wait
        // until its former host row disappears before computing drag targets.
        if(current["windows"].toArray().size()!=3 || current["rows"].toArray().size()!=3 || coordinate("B").isEmpty()){QTimer::singleShot(100,tick);return;}
        snapshots["initial"]=current;
        checks["native_three_owned_windows"]=current["windows"].toArray().size()==3;
        bool pids=true;for(auto value:current["windows"].toArray())pids &= value.toObject()["pid"].toInt()==getpid();
        checks["native_window_ids_and_owned_pid"]=pids && identities(current).size()==3;
        checks["native_sort_mode_manual"]=current["sortMode"].toInt()==1 && current["manualAvailable"].toBool();
        checks["drag_distance_uses_platform_hint"]=coordinate("B")["dragDistance"].toInt()==QGuiApplication::styleHints()->startDragDistance();
        drag("B","A");phase=1;
    } else if(phase==1) {
        snapshots["before_a"]=current;
        checks["pointer_drag_moves_b_before_a"]=position(current,"B")>=0 && position(current,"B")<position(current,"A");
        checks["drag_before_preserves_native_identities"]=identities(current)==identities(snapshots["initial"].toObject());
        checks["drag_before_preserves_windows"]=windows(current)==windows(snapshots["initial"].toObject());
        drag("B","C");phase=2;
    } else if(phase==2) {
        snapshots["after_c"]=current;
        checks["pointer_drag_moves_b_after_c"]=position(current,"B")>position(current,"C") && position(current,"C")>=0;
        checks["drag_after_preserves_native_identities"]=identities(current)==identities(snapshots["initial"].toObject());
        checks["drag_after_preserves_windows"]=windows(current)==windows(snapshots["initial"].toObject());
        checks["reorder_changes_no_pins"]=current["pins"]==snapshots["initial"].toObject()["pins"] && current["launchers"].toArray().isEmpty();
        auto start=point("A");QTest::mouseMove(window,start);QTest::mousePress(window,Qt::LeftButton,Qt::NoModifier,start);
        QTest::mouseMove(window,start+QPoint(qMax(0,QGuiApplication::styleHints()->startDragDistance()-1),0),30);
        checks["below_threshold_does_not_arm_drag"]=!coordinate("A")["dragActive"].toBool();
        QTest::mouseRelease(window,Qt::LeftButton,Qt::NoModifier,start,30);phase=3;
    } else if(phase==3) {
        checks["below_threshold_preserves_native_order"]=order(current)==order(snapshots["after_c"].toObject());
        checks["below_threshold_requests_no_reorder"]=current["requests"].toArray().size()==2;
        invoke("action","alpha");phase=4;
    } else if(phase==4) {
        snapshots["alpha"]=current;
        checks["nonmanual_sort_disables_drag"]=!current["manualAvailable"].toBool() && !coordinate("A")["reorderEnabled"].toBool();
        drag("C","A");phase=5;
    } else if(phase==5) {
        checks["nonmanual_gesture_preserves_native_order"]=order(current)==order(snapshots["alpha"].toObject());
        checks["nonmanual_controller_rejects_move"]=!invoke("action","moveAtoC").toBool();
        invoke("action","manual");phase=6;
    } else if(phase==6) {
        invoke("action","closeGroup");window->requestActivate();phase=59;
    } else if(phase==59) {
        snapshots["keyboard_before"]=current;
        invoke("action","focusA");physical({"key","ctrl+shift+Right"});phase=60;
    } else if(phase==60) {
        checks["native_control_shift_right_reorders_task"]=position(current,"A")==position(snapshots["keyboard_before"].toObject(),"A")+1;
        snapshots["keyboard_right"]=current;
        invoke("action","focusA");physical({"key","ctrl+shift+Left"});phase=61;
    } else if(phase==61) {
        checks["native_control_shift_left_restores_task_order"]=order(current)==order(snapshots["keyboard_before"].toObject());
        snapshots["manual_again"]=current;
        checks["stale_pid_rejected"]=!invoke("action","stalePid").toBool();
        invoke("action","freezeB");
        missingPress=point("B");QTest::mouseMove(window,missingPress);QTest::mousePress(window,Qt::LeftButton,Qt::NoModifier,missingPress);
        QTest::mouseMove(window,missingPress+QPoint(QGuiApplication::styleHints()->startDragDistance()+3,0),30);
        owned[1]->close();phase=7;
    } else if(phase==7) {
        if(current["windows"].toArray().size()!=2){QTimer::singleShot(100,tick);return;}
        snapshots["source_closed_before_release"]=current;
        auto end=point("A");QTest::mouseMove(window,end,30);QTest::mouseRelease(window,Qt::LeftButton,Qt::NoModifier,end,30);
        checks["closed_source_record_rejected"]=!invoke("action","missingSource").toBool();phase=8;
    } else if(phase==8) {
        snapshots["after_closed_drop"]=current;
        checks["closed_source_gesture_does_not_rebind_to_survivor"]=order(current)==order(snapshots["source_closed_before_release"].toObject())
            && current["requests"].toArray().size()==4;
        invoke("action","group");phase=9;
    } else if(phase==9) {
        if(!current["groupAvailable"].toBool()){QTimer::singleShot(100,tick);return;}
        snapshots["group"]=current;
        checks["actual_native_group_available"]=current["groupAvailable"].toBool();
        checks["group_member_not_used_as_top_level_target"]=!invoke("action","groupMember").toBool();
        checks["changed_group_member_pid_rejected"]=!invoke("action","staleGroup").toBool();
        invoke("action","middleClose");QTest::mouseClick(window,Qt::MiddleButton,Qt::NoModifier,point("@group"));phase=10;
    } else if(phase==10) {
        checks["group_middle_close_does_not_close_first_member"]=windows(current)==windows(snapshots["group"].toObject());
        invoke("action","middleMinimize");QTest::mouseClick(window,Qt::MiddleButton,Qt::NoModifier,point("@group"));phase=11;
    } else if(phase==11) {
        checks["group_middle_minimize_does_not_minimize_first_member"]=windows(current)==windows(snapshots["group"].toObject());
        bool reorderOnly=true;for(auto value:current["requests"].toArray())reorderOnly &= value.toObject()["action"].toString()=="reorder";
        checks["no_activate_close_minimize_window_move_request"]=reorderOnly && current["requests"].toArray().size()==4;
        checks["pins_still_independent"]=current["pins"]==snapshots["initial"].toObject()["pins"] && current["launchers"].toArray().isEmpty();
        checks["native_menu_and_status_bridge_constructed"]=current["nativeMenuReady"].toBool();
        QProcess geometry;geometry.start("xprop",{"-id",QString::number(owned[0]->winId()),"_NET_WM_ICON_GEOMETRY"});geometry.waitForFinished(2000);
        const auto iconGeometry=geometry.readAllStandardOutput();snapshots["icon_geometry"]=QString::fromUtf8(iconGeometry);
        checks["native_minimize_icon_geometry_published"]=iconGeometry.contains("CARDINAL") && iconGeometry.contains("66, 98");
        invoke("action","closeGroup");phase=12;
    } else if(phase==12) {
        click("@group");phase=13;
    } else if(phase==13) {
        checks["native_group_first_pointer_click_opens_member_list"]=current["groupPopup"].toBool();
        doubleClick("@group");phase=130;
    } else if(phase==130) {
        checks["native_group_double_click_keeps_member_list"]=current["groupPopup"].toBool();
        invoke("action","closeGroup");beforeWheelRequests=current["requests"].toArray().size();phase=131;
    } else if(phase==131) {
        snapshots["default_wheel_before"]=current;wheel("@group",-120);phase=14;
    } else if(phase==14) {
        checks["native_default_wheel_does_not_activate_any_window"]=current["requests"].toArray().size()==beforeWheelRequests;
        invoke("action","wheelActivation");owned[0]->activateWindow();owned[0]->raise();phase=15;
    } else if(phase==15) {
        snapshots["optional_wheel_before"]=current;
        wheel("@group",-120);phase=16;
    } else if(phase==16) {
        snapshots["optional_wheel_after"]=current;
        checks["native_optional_group_wheel_activates_other_member"]=owned[2]->isActiveWindow();
        invoke("action","ungroup");phase=17;
    } else if(phase==17) {
        doubleClick("C");phase=18;
    } else if(phase==18) {
        checks["native_double_click_active_window_minimizes"]=owned[2]->isMinimized();
        doubleClick("C");phase=19;
    } else if(phase==19) {
        checks["native_double_click_minimized_window_restores_and_focuses"]=!owned[2]->isMinimized() && owned[2]->isActiveWindow();
        physical({"set_window","--urgency","1",QString::number(owned[0]->winId())});phase=20;
    } else if(phase==20) {
        checks["native_urgent_window_updates_attention"]=current["attention"].toBool();
        checks["native_scenario_completed"]=true;complete();return;
    }
    QTimer::singleShot(450,tick);
}
extern "C" int interceptedExec() asm("_ZN12QApplication4execEv");
extern "C" int interceptedExec() {
    auto original=reinterpret_cast<int (*)()>(dlsym(RTLD_NEXT,"_ZN12QApplication4execEv"));
    if(!original)return 2;
    for(int index=0;index<3;++index) {
        auto widget=new QWidget;widget->setWindowTitle("DomainOS reorder "+QString(QChar('A'+index)));
        widget->resize(240,140);widget->move(80+index*280,100);widget->show();owned.append(widget);
    }
    QTimer::singleShot(1200,tick);return original();
}
