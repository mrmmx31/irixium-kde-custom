// SPDX-FileCopyrightText: 2026 IRIX Classic contributors
// SPDX-License-Identifier: GPL-3.0-or-later
// Native menu/search gestures; only the private marker desktop entry launches.
#include <QApplication>
#include <QFile>
#include <QImage>
#include <QJsonArray>
#include <QJsonDocument>
#include <QJsonObject>
#include <QTest>
#include <QTimer>
#include <QWindow>
#include <dlfcn.h>
#include <functional>

using Children=QList<QObject *> (*)(QObject *);
using Map=QPointF (*)(const QObject *,const QObject *,const QPointF &);
using Grab=QImage (*)(QWindow *);
static QObject *fixture=nullptr;
static QJsonObject checks,snapshots;
static int phase=0,attempts=0;
static QObject *walk(QObject *object,const std::function<bool(QObject *)> &matches) {
    if(!object)return nullptr;
    if(matches(object))return object;
    const auto children=reinterpret_cast<Children>(dlsym(RTLD_DEFAULT,"_ZNK10QQuickItem10childItemsEv"));
    if(children && object->inherits("QQuickItem"))for(auto child:children(object))if(auto found=walk(child,matches))return found;
    return nullptr;
}
static QObject *item(const QString &name,QWindow **owner=nullptr) {
    for(auto window:QGuiApplication::allWindows())if(window->isVisible()) {
        if(auto found=walk(window->property("contentItem").value<QObject *>(),[&](QObject *object){return object->objectName()==name;})) {
            if(owner)*owner=window;return found;
        }
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
static bool pointerClick(QObject *target,QWindow *owner) {
    const auto map=reinterpret_cast<Map>(dlsym(RTLD_DEFAULT,"_ZNK10QQuickItem9mapToItemEPKS_RK7QPointF"));
    if(!target || !owner || !map)return false;
    auto content=owner->property("contentItem").value<QObject *>();
    auto position=map(target,content,QPointF(target->property("width").toDouble()/2,target->property("height").toDouble()/2)).toPoint();
    if(!QRect(QPoint(0,0),owner->size()).contains(position))return false;
    QTest::mouseMove(owner,position);QTest::mouseClick(owner,Qt::LeftButton,Qt::NoModifier,position);return true;
}
static bool click(const QString &name){QWindow *owner=nullptr;auto target=item(name,&owner);return pointerClick(target,owner);}
static bool capture(const QString &name,const QString &filename) {
    QWindow *owner=nullptr;auto target=item(name,&owner);
    const auto grab=reinterpret_cast<Grab>(dlsym(RTLD_DEFAULT,"_ZN12QQuickWindow10grabWindowEv"));
    return target && owner && grab && grab(owner).save(qEnvironmentVariable("IRIX_DOMAINOS_APPLICATIONS_DIR")+"/"+filename);
}
static QString marker() {
    QFile file(qEnvironmentVariable("IRIX_DOMAINOS_APPLICATIONS_DIR")+"/dispatch.txt");
    return file.open(QIODevice::ReadOnly) ? QString::fromUtf8(file.readAll()) : QString();
}
static void finish(const QString &error={}) {
    QJsonObject report{{"checks",checks},{"snapshots",snapshots},{"state",fixture ? state() : QJsonObject()},{"marker",marker()}};
    if(!error.isEmpty())report["failure"]=error;
    QFile file(qEnvironmentVariable("IRIX_DOMAINOS_APPLICATIONS_REPORT"));if(file.open(QIODevice::WriteOnly))file.write(QJsonDocument(report).toJson());
    QCoreApplication::quit();
}
static void tick() {
    if(++attempts>100){checks["native_scenario_completed"]=false;finish("Bounded native interface timeout");return;}
    if(!fixture) {
        fixture=item("domainosApplicationInterfaceFixture");
        if(!fixture){QTimer::singleShot(100,tick);return;}
    }
    const auto current=state();
    if(phase==0) {
        if(!invoke("action","nativeOpen").toBool()){finish("KDE menu failed to open");return;}phase=1;
    } else if(phase==1) {
        auto bridge=item("domainosKdeApplicationMenu");
        auto representation=bridge ? bridge->property("nativeRepresentation").value<QObject *>() : nullptr;
        if(!current["popup"].toBool() || !representation){QTimer::singleShot(100,tick);return;}
        checks["installed_kde_menu_representation_loaded_without_copy"]=QString(representation->metaObject()->className()).contains("MenuRepresentation");
        checks["native_interface_uses_separate_standard_root_catalog"]=current["kdeRootDistinct"].toBool() && !current["kdeRootFlat"].toBool();
        checks["native_menu_frame_saved"]=capture("domainosKdeApplicationsRepresentation","KDE-NATIVE-MENU.png");
        snapshots["native_open"]=current;
        QObject *search=walk(representation,[](QObject *object){return QString(object->metaObject()->className()).contains("SearchField") && object->property("visible").toBool();});
        if(!search){finish("Installed KDE search field missing");return;}
        checks["installed_native_search_field_accepts_query"]=search->setProperty("text","DomainOS Interface Probe");phase=2;
    } else if(phase==2) {
        QWindow *owner=nullptr;QObject *leaf=nullptr;
        for(auto window:QGuiApplication::allWindows())if(window->isVisible()) {
            leaf=walk(window->property("contentItem").value<QObject *>(),[](QObject *object){return object->property("text").toString()=="DomainOS Interface Probe" && QString(object->metaObject()->className()).contains("Label") && object->property("visible").toBool();});
            if(leaf){owner=window;break;}
        }
        if(!leaf){QTimer::singleShot(100,tick);return;}
        checks["native_application_search_result_clicked_by_pointer"]=pointerClick(leaf,owner);phase=3;
    } else if(phase==3) {
        if(marker()!="probe\n" || current["popup"].toBool()){QTimer::singleShot(100,tick);return;}
        checks["native_model_trigger_launches_only_owned_marker_app"]=true;
        snapshots["native_launched"]=current;
        checks["custom_search_started_outside_target_category"]=invoke("action","customSearchOutsideCategory").toBool();phase=4;
    } else if(phase==4) {
        if(current["searchResults"].toInt()!=1){QTimer::singleShot(100,tick);return;}
        checks["custom_search_is_global_across_catalog_categories"]=current["sourceCountBeforeSearch"].toInt()==0 && current["searchResults"].toInt()==1;
        checks["custom_global_search_frame_saved"]=capture("domainosApplicationsPopupContent","DOMAINOS-GLOBAL-SEARCH.png");
        snapshots["global_search"]=current;
        checks["custom_global_result_clicked_by_pointer"]=click("domainosApplicationEntry_0");phase=5;
    } else if(phase==5) {
        if(marker()!="probe\nprobe\n" || current["popup"].toBool()){QTimer::singleShot(100,tick);return;}
        checks["custom_global_search_activates_only_owned_marker_app"]=true;
        invoke("action","emptyDrawer");phase=6;
    } else if(phase==6) {
        if(!current["popup"].toBool() || !item("domainosPinnedPreferencesEntry")){QTimer::singleShot(100,tick);return;}
        checks["empty_drawer_keeps_preferences_permanently_available"]=current["pins"].toArray().isEmpty();
        checks["empty_drawer_preferences_frame_saved"]=capture("domainosApplicationsPopupContent","DRAWER-PERMANENT-PREFERENCES.png");
        snapshots["empty_drawer"]=current;
        checks["permanent_drawer_preferences_clicked_by_pointer"]=click("domainosPinnedPreferencesEntry");phase=7;
    } else if(phase==7) {
        if(current["configureRequests"].toInt()!=1 || current["popup"].toBool()){QTimer::singleShot(100,tick);return;}
        checks["permanent_preferences_routes_to_own_instance_without_pin_mutation"]=current["pins"].toArray().isEmpty();
        checks["native_scenario_completed"]=true;snapshots["final"]=current;finish();return;
    }
    QTimer::singleShot(150,tick);
}
extern "C" int interceptedExec() asm("_ZN12QApplication4execEv");
extern "C" int interceptedExec() {
    const auto original=reinterpret_cast<int (*)()>(dlsym(RTLD_NEXT,"_ZN12QApplication4execEv"));if(!original)return 2;
    QTimer::singleShot(1200,tick);return original();
}
