// SPDX-FileCopyrightText: 2026 IRIX Classic contributors
// SPDX-License-Identifier: GPL-3.0-or-later
// Directed native Kicker UI dispatch / real DomainOSActivity observation.
#include <QApplication>
#include <QAbstractItemModel>
#include <QFile>
#include <QJsonArray>
#include <QJsonDocument>
#include <QJsonObject>
#include <QMenu>
#include <QMetaMethod>
#include <QTest>
#include <QTimer>
#include <QWindow>
#include <dlfcn.h>

using Children=QList<QObject *> (*)(QObject *);
static QObject *fixture=nullptr;
static QVariantList leafPath;
static int stage=0,retries=0;
static QJsonObject report,checks;

static QObject *find(QObject *item,const QString &name) {
    if(!item)return nullptr;if(item->objectName()==name)return item;
    const auto children=reinterpret_cast<Children>(dlsym(RTLD_DEFAULT,"_ZNK10QQuickItem10childItemsEv"));
    if(children && item->inherits("QQuickItem"))for(auto child:children(item))if(auto match=find(child,name))return match;
    return nullptr;
}
static QJsonObject snapshot() {return QJsonDocument::fromJson(fixture->property("snapshotJson").toString().toUtf8()).object();}
static QJsonObject activity() {return snapshot()["activity"].toObject();}
static int role(QAbstractItemModel *model,const QByteArray &name) {
    const auto names=model->roleNames();for(auto it=names.begin();it!=names.end();++it)if(it.value()==name)return it.key();return -1;
}
static QAbstractItemModel *childModel(QAbstractItemModel *model,int row) {
    const int index=model->metaObject()->indexOfMethod("modelForRow(int)");if(index<0)return nullptr;
    QObject *child=nullptr;const auto method=model->metaObject()->method(index);
    if(!method.invoke(model,QGenericReturnArgument(method.typeName(),&child),QGenericArgument("int",&row)))return nullptr;
    return qobject_cast<QAbstractItemModel *>(child);
}
static bool findLeaf(QAbstractItemModel *model,QVariantList path={},int depth=0) {
    if(!model || depth>8)return false;
    for(int row=0;row<model->rowCount();++row) {
        auto current=path;current.append(row);const auto index=model->index(row,0);
        if(model->data(index,role(model,"favoriteId")).toString().endsWith("irix-domainos-qa-first.desktop")) {leafPath=current;return true;}
        if(model->data(index,role(model,"hasChildren")).toBool() && findLeaf(childModel(model,row),current,depth+1))return true;
    }
    return false;
}
static bool click(const QString &name,Qt::MouseButton button=Qt::LeftButton) {
    const auto map=reinterpret_cast<QPointF (*)(QObject *,const QPointF &)>(dlsym(RTLD_DEFAULT,"_ZNK10QQuickItem10mapToSceneERK7QPointF"));
    const auto owner=reinterpret_cast<QWindow *(*)(QObject *)>(dlsym(RTLD_DEFAULT,"_ZNK10QQuickItem6windowEv"));
    if(!map || !owner)return false;
    for(auto window:QGuiApplication::allWindows())if(window->isVisible()) {
        auto item=find(window->property("contentItem").value<QObject *>(),name);
        if(!item || !item->property("visible").toBool() || !item->property("enabled").toBool() || owner(item)!=window)continue;
        const auto point=map(item,QPointF(30,item->property("height").toDouble()/2)).toPoint();
        if(!QRect(QPoint(0,0),window->size()).contains(point))continue;
        QTest::mousePress(window,button,Qt::NoModifier,point,0);QCoreApplication::processEvents();QTest::qWait(50);
        const bool held=window->isVisible() && item->property("visible").toBool() && item->property("enabled").toBool() && owner(item)==window;
        auto values=report["window_press_intervals"].toArray();
        values.append(QJsonObject{{"objectName",name},{"text",item->property("text").toString()},
            {"held_50ms_visible_enabled_owner_matches",held},{"window_active_after_press",window->isActive()}});
        report["window_press_intervals"]=values;
        QTest::mouseRelease(window,button,Qt::NoModifier,point,0);return held;
    }
    return false;
}
static bool clickMenu(const QString &text,bool inactive=false) {
    for(auto widget:QApplication::topLevelWidgets())if(auto menu=qobject_cast<QMenu *>(widget))if(menu->isVisible()) {
        for(auto action:menu->actions()) {
            const auto label=action->text().remove('&');
            if(inactive ? (!action->isSeparator() && action->isEnabled()) : (!action->isEnabled() || action->isSeparator() || !label.contains(text,Qt::CaseInsensitive)))continue;
            const auto point=menu->actionGeometry(action).center();
            QTest::mousePress(menu,Qt::LeftButton,Qt::NoModifier,point,0);QCoreApplication::processEvents();QTest::qWait(50);
            const bool held=menu->isVisible();
            auto values=report["menu_press_intervals"].toArray();values.append(QJsonObject{{"text",label},{"held_50ms_visible",held}});report["menu_press_intervals"]=values;
            QTest::mouseRelease(menu,Qt::LeftButton,Qt::NoModifier,point,0);
            if(inactive)menu->close();return held;
        }
    }
    return false;
}
static void finish(const QString &error={}) {
    if(!error.isEmpty())report["failure"]=error;
    report["checks"]=checks;report["qt_version"]=qVersion();report["host_pid"]=int(QCoreApplication::applicationPid());
    report["final_state"]=fixture ? snapshot() : QJsonObject{};
    QFile file(qEnvironmentVariable("IRIX_DOMAINOS_APPLICATIONS_REPORT"));if(file.open(QIODevice::WriteOnly))file.write(QJsonDocument(report).toJson());
    QCoreApplication::quit();
}
static void step();
static void next(int scenario,int delay=150) {fixture->setProperty("activityScenario",scenario);QTimer::singleShot(delay,step);}
static bool reportsHonest(const QJsonObject &state,int count) {
    const auto values=state["reports"].toArray();if(values.size()!=count)return false;
    for(auto value:values) {
        const auto item=value.toObject();if(item["outcome"].toString()!="dispatch-returned" || !item["ok"].toBool()
            || !item["detail"].toString().contains("completion are not observed"))return false;
    }
    return true;
}
static void step() {
    if(!fixture) {
        for(auto window:QGuiApplication::allWindows())if(auto item=find(window->property("contentItem").value<QObject *>(),"domainosApplicationsTestFixture")){fixture=item;break;}
        if(!fixture){finish("Directed application fixture absent");return;}
    }
    if(stage==0) {
        const auto controller=fixture->property("controller").value<QObject *>();
        auto model=qobject_cast<QAbstractItemModel *>(controller->property("catalogModel").value<QObject *>());
        if(!findLeaf(model) && retries++<12){QTimer::singleShot(150,step);return;}
        if(leafPath.isEmpty()){finish("Owned Desktop Entry absent from native Kicker catalog");return;}
        fixture->setProperty("leafPath",leafPath);report["leaf_path"]=QJsonArray::fromVariantList(leafPath);
        int category=-1;for(int row=0;row<model->rowCount();++row)if(model->data(model->index(row,0),role(model,"hasChildren")).toBool()){category=row;break;}
        if(category<0){finish("No native category to navigate");return;}
        fixture->setProperty("categoryRow",category);
        checks["default_activity_starts_disabled_and_empty"]=!activity()["keep"].toBool() && !activity()["lit"].toBool() && activity()["sequence"].toInt()==0;
        stage=1;next(1);return;
    }
    if(stage==1) {
        checks["native_category_clicked"]=click("domainosApplicationEntry_"+QString::number(fixture->property("categoryRow").toInt()));
        stage=2;QTimer::singleShot(100,step);return;
    }
    if(stage==2) {
        report["category"]=snapshot();checks["category_navigation_has_no_dispatch_or_light"]=snapshot()["navigationDepth"].toInt()>0 && activity()["sequence"].toInt()==0 && !activity()["lit"].toBool();
        stage=3;next(2);return;
    }
    if(stage==3) {
        checks["native_catalog_leaf_clicked"]=click("domainosApplicationEntry_0");
        report["catalog_immediate"]=snapshot();stage=4;QTimer::singleShot(500,step);return;
    }
    if(stage==4) {
        const auto state=activity();report["catalog_default"]=snapshot();
        checks["catalog_dispatch_default_finishes_synchronously"]=reportsHonest(state,1) && state["pending"].toInt()==0 && !state["lit"].toBool() && !state["tail"].toBool();
        const auto begins=state["begins"].toArray(),ends=state["finishes"].toArray();
        checks["catalog_begin_observes_actual_activity_immediately"]=begins.size()==1 && begins[0].toObject()["pending"].toInt()==1 && begins[0].toObject()["lit"].toBool();
        checks["catalog_finish_has_no_default_light_delay"]=ends.size()==1 && ends[0].toObject()["pending"].toInt()==0 && !ends[0].toObject()["lit"].toBool();
        stage=5;next(3);return;
    }
    if(stage==5) {
        const bool opened=click("domainosApplicationEntry_0",Qt::RightButton);
        QTimer::singleShot(100,[opened](){checks["favorite_added_through_actual_context"]=opened && clickMenu("Add to Favorites");stage=6;retries=0;QTimer::singleShot(150,step);});return;
    }
    if(stage==6) {
        if(snapshot()["favoritesCount"].toInt()!=1 && retries++<20){QTimer::singleShot(100,step);return;}
        report["favorite_add"]=snapshot();checks["favorite_edit_with_tail_enabled_has_no_activity"]=snapshot()["favoritesCount"].toInt()==1 && activity()["sequence"].toInt()==1 && !activity()["lit"].toBool();
        stage=7;next(4);return;
    }
    if(stage==7) {
        checks["native_favorite_leaf_clicked"]=snapshot()["showingFavorites"].toBool() && click("domainosApplicationEntry_0");
        const auto state=activity();report["favorite_dispatch_immediate"]=snapshot();
        checks["favorite_launcher_uses_same_native_dispatcher"]=reportsHonest(state,2);
        checks["favorite_launch_tail_begins_only_after_return"]=state["pending"].toInt()==0 && state["lit"].toBool() && state["tail"].toBool();
        stage=8;QTimer::singleShot(850,step);return;
    }
    if(stage==8) {
        checks["optional_tail_expires_without_pending_application"]=activity()["pending"].toInt()==0 && !activity()["lit"].toBool();
        report["favorite_tail_expired"]=snapshot();stage=9;next(6);return;
    }
    if(stage==9) {
        const bool opened=click("domainosApplicationEntry_0",Qt::RightButton);
        QTimer::singleShot(100,[opened](){
            checks["native_desktop_action_clicked"]=opened && clickMenu("QA Native Action");
            const auto state=activity();report["context_dispatch_immediate"]=snapshot();
            checks["context_action_uses_native_dispatcher_and_post_return_tail"]=reportsHonest(state,3) && state["pending"].toInt()==0 && state["tail"].toBool();
            stage=10;QTimer::singleShot(500,step);
        });return;
    }
    if(stage==10) {stage=11;next(7);return;}
    if(stage==11) {
        const bool opened=click("domainosApplicationEntry_0",Qt::RightButton);
        QTimer::singleShot(100,[opened](){checks["favorite_removed_through_actual_context"]=opened && clickMenu("Remove from Favorites");stage=12;retries=0;QTimer::singleShot(150,step);});return;
    }
    if(stage==12) {
        if(snapshot()["favoritesCount"].toInt()!=0 && retries++<20){QTimer::singleShot(100,step);return;}
        report["favorite_remove"]=snapshot();checks["favorite_removal_preserves_dispatch_count_and_pins"]=snapshot()["favoritesCount"].toInt()==0 && activity()["sequence"].toInt()==3 && snapshot()["pins"].toArray().isEmpty() && !activity()["lit"].toBool();
        stage=13;next(8);return;
    }
    const bool opened=click("domainosApplicationEntry_0",Qt::RightButton);
    QTimer::singleShot(100,[opened](){
        checks["native_inactive_menu_item_clicked"]=opened && clickMenu({},true);
        checks["inactive_native_menu_item_has_no_activity"]=activity()["sequence"].toInt()==3 && !activity()["lit"].toBool();
        fixture->setProperty("activityScenario",9);const auto error=activity();report["exception_model_double"]=snapshot();
        checks["explicit_exception_is_failed_and_extinguishes_activity"]=!snapshot()["exceptionDispatchResult"].toBool() && error["pending"].toInt()==0 && !error["lit"].toBool()
            && error["reports"].toArray().last().toObject()["outcome"].toString()=="failed" && !error["reports"].toArray().last().toObject()["ok"].toBool();
        fixture->setProperty("activityScenario",10);const auto policy=activity();report["false_policy_model_double"]=snapshot();
        const auto last=policy["reports"].toArray().last().toObject();
        checks["false_close_policy_is_not_reported_as_application_failure"]=!snapshot()["falseDispatchResult"].toBool() && last["ok"].toBool() && last["outcome"].toString()=="dispatch-returned" && !last["closeRequested"].toBool();
        const auto begins=policy["begins"].toArray(),ends=policy["finishes"].toArray(),reports=policy["reports"].toArray();
        bool matching=begins.size()==5 && ends.size()==5 && reports.size()==5;
        for(int i=0;matching && i<5;++i)matching=begins[i].toObject()["token"]==ends[i].toObject()["token"] && begins[i].toObject()["token"]==reports[i].toObject()["token"];
        checks["all_dispatches_finish_with_matching_tokens"]=matching && policy["pending"].toInt()==0 && !policy["lit"].toBool();
        bool held=true;for(auto value:report["window_press_intervals"].toArray())held=held && value.toObject()["held_50ms_visible_enabled_owner_matches"].toBool();
        checks["all_native_window_controls_remain_visible_during_press_release"]=held && !report["window_press_intervals"].toArray().isEmpty();
        bool menusHeld=true;for(auto value:report["menu_press_intervals"].toArray())menusHeld=menusHeld && value.toObject()["held_50ms_visible"].toBool();
        checks["native_context_menus_remain_visible_during_press_release"]=menusHeld && !report["menu_press_intervals"].toArray().isEmpty();
        finish();
    });
}
extern "C" int interceptedExec() asm("_ZN12QApplication4execEv");
extern "C" int interceptedExec() {
    const auto original=reinterpret_cast<int (*)()>(dlsym(RTLD_NEXT,"_ZN12QApplication4execEv"));
    if(!original)return 2;QTimer::singleShot(1500,step);QTimer::singleShot(19000,[]{finish("Bounded native launcher activity test deadline");});return original();
}
