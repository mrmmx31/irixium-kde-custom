// SPDX-FileCopyrightText: 2026 mrmmx31
// SPDX-License-Identifier: GPL-3.0-or-later
// Real Kicker catalog and private Desktop Entry dispatch; bounded test only.
#include <QApplication>
#include <QAbstractItemModel>
#include <QFile>
#include <QIcon>
#include <QImage>
#include <QJsonArray>
#include <QJsonDocument>
#include <QJsonObject>
#include <QMetaMethod>
#include <QMouseEvent>
#include <QProcess>
#include <QScreen>
#include <QTimer>
#include <QTest>
#include <QWindow>
#include <QMenu>
#include <dlfcn.h>

using Children = QList<QObject *> (*)(QObject *);
using Grab = QImage (*)(QWindow *);
static QObject *fixture = nullptr;
static QJsonObject report;
static int stage = 0, retries = 0;
static QVariantList leafPath;

static QString windowInfo(QWindow *window)
{
    QProcess process;process.start("xwininfo",{"-id",QString::number(window->winId())});
    if(!process.waitForFinished(1000))return "xwininfo timeout";
    return QString::fromUtf8(process.readAllStandardOutput());
}

static QObject *find(QObject *item,const QString &name,Children children)
{
    if (!item) return nullptr;
    if (item->objectName()==name) return item;
    if (item->inherits("QQuickItem")) for (auto child : children(item)) if (auto match=find(child,name,children)) return match;
    return nullptr;
}
static QJsonObject record(QAbstractItemModel *model,int row)
{
    QJsonObject result;
    const auto index=model->index(row,0);
    const auto roles=model->roleNames();
    for (auto it=roles.cbegin();it!=roles.cend();++it) {
        if (it.value()=="display" || it.value()=="favoriteId" || it.value()=="url" || it.value()=="hasChildren" || it.value()=="disabled")
            result[QString::fromUtf8(it.value())]=QJsonValue::fromVariant(model->data(index,it.key()));
    }
    const auto decoration=model->data(index,Qt::DecorationRole);
    const auto icon=decoration.value<QIcon>();
    const QString iconName=decoration.metaType().id()==QMetaType::QString ? decoration.toString() : icon.name();
    result["icon_present"]=!icon.isNull() || !iconName.isEmpty(); result["icon_name"]=iconName;
    return result;
}
static QAbstractItemModel *childModel(QAbstractItemModel *model,int row)
{
    const int index=model->metaObject()->indexOfMethod("modelForRow(int)");
    if (index<0) return nullptr;
    QObject *child=nullptr;
    const auto method=model->metaObject()->method(index);
    if (!method.invoke(model,QGenericReturnArgument(method.typeName(),&child),QGenericArgument("int",&row))) return nullptr;
    return qobject_cast<QAbstractItemModel *>(child);
}
static bool findLeaf(QAbstractItemModel *model,const QString &desktop,QVariantList path,int depth=0)
{
    if (!model || depth>8) return false;
    for (int row=0;row<model->rowCount();row++) {
        auto current=path; current.append(row);
        const auto item=record(model,row);
        if (item["favoriteId"].toString().endsWith(desktop) || item["url"].toString().endsWith(desktop)) { leafPath=current; report["leaf"]=item;return true; }
        if (item["hasChildren"].toBool()) if (findLeaf(childModel(model,row),desktop,current,depth+1)) return true;
    }
    return false;
}
static void finish(const QString &failure={})
{
    if (!failure.isEmpty()) report["failure"]=failure;
    QFile file(qEnvironmentVariable("IRIX_DOMAINOS_APPLICATIONS_REPORT"));
    if (file.open(QIODevice::WriteOnly)) file.write(QJsonDocument(report).toJson());
    QCoreApplication::quit();
}
static bool click(const QString &name)
{
    const auto children=reinterpret_cast<Children>(dlsym(RTLD_DEFAULT,"_ZNK10QQuickItem10childItemsEv"));
    const auto map=reinterpret_cast<QPointF (*)(QObject *,const QPointF &)>(dlsym(RTLD_DEFAULT,"_ZNK10QQuickItem10mapToSceneERK7QPointF"));
    const auto itemWindow=reinterpret_cast<QWindow *(*)(QObject *)>(dlsym(RTLD_DEFAULT,"_ZNK10QQuickItem6windowEv"));
    if (!children || !map || !itemWindow) return false;
    for (auto window:QGuiApplication::allWindows()) {
        if (!window->isVisible()) continue;
        auto item=find(window->property("contentItem").value<QObject *>(),name,children);
        if (!item || !item->property("visible").toBool() || !item->property("enabled").toBool() || itemWindow(item)!=window) continue;
        const auto point=map(item,QPointF(30,item->property("height").toDouble()/2));
        if (!QRect(QPoint(0,0),window->size()).contains(point.toPoint())) continue;
        auto input=report["native_input_targets"].toArray();
        auto widgets=QJsonArray{};
        for(auto widget:QApplication::topLevelWidgets())widgets.append(QJsonObject{{"type",widget->metaObject()->className()},
            {"title",widget->windowTitle()},{"visible",widget->isVisible()},{"modal",widget->isModal()},
            {"active_modal",widget==QApplication::activeModalWidget()},{"active_popup",widget==QApplication::activePopupWidget()}});
        const QString before=windowInfo(window);
        if(input.isEmpty() && window->screen())window->screen()->grabWindow(0).save(qEnvironmentVariable("IRIX_DOMAINOS_APPLICATIONS_DIR")+"/BEFORE-LEAF-INPUT.png");
        QTest::mousePress(window,Qt::LeftButton,Qt::NoModifier,point.toPoint(),0);
        QCoreApplication::processEvents();QTest::qWait(50);
        const bool held=window->isVisible() && item->property("visible").toBool()
            && item->property("enabled").toBool() && itemWindow(item)==window;
        input.append(QJsonObject{{"objectName",name},{"text",item->property("text").toString()},
            {"windowWidth",window->width()},{"windowHeight",window->height()},
            {"x",point.x()},{"y",point.y()},{"visible",true},{"enabled",true},{"owner_window_matches",true},
            {"popup_and_target_visible_after_press",held},{"native_window_active_after_press",window->isActive()},
            {"input_delivery","QtTest press/processEvents/50ms/release in private KWin"},{"window_geometry",QJsonArray{window->x(),window->y(),window->width(),window->height()}},
            {"window_exposed",window->isExposed()},{"native_x11_window_before_press",before},
            {"native_x11_window_after_press",windowInfo(window)}});
        auto last=input.takeAt(input.size()-1).toObject();last["private_native_widgets_before_press"]=widgets;input.append(last);
        report["native_input_targets"]=input;
        QTest::mouseRelease(window,Qt::LeftButton,Qt::NoModifier,point.toPoint(),0);
        return held;
    }
    return false;
}
static bool openContext(bool keyboard)
{
    const auto children=reinterpret_cast<Children>(dlsym(RTLD_DEFAULT,"_ZNK10QQuickItem10childItemsEv"));
    const auto map=reinterpret_cast<QPointF (*)(QObject *,const QPointF &)>(dlsym(RTLD_DEFAULT,"_ZNK10QQuickItem10mapToSceneERK7QPointF"));
    const auto itemWindow=reinterpret_cast<QWindow *(*)(QObject *)>(dlsym(RTLD_DEFAULT,"_ZNK10QQuickItem6windowEv"));
    if (!children || !map || !itemWindow) return false;
    for (auto window:QGuiApplication::allWindows()) {
        if (!window->isVisible()) continue;
        auto item=find(window->property("contentItem").value<QObject *>(),"domainosApplicationEntry_0",children);
        if (!item || !item->property("visible").toBool() || !item->property("enabled").toBool() || itemWindow(item)!=window) continue;
        const auto point=map(item,QPointF(30,item->property("height").toDouble()/2)).toPoint();
        if (!QRect(QPoint(0,0),window->size()).contains(point)) continue;
        if (keyboard) {
            using Focus=void (*)(QObject *);
            const auto focus=reinterpret_cast<Focus>(dlsym(RTLD_DEFAULT,"_ZN10QQuickItem16forceActiveFocusEv"));
            if (!focus) return false;
            window->requestActivate();focus(item);
            QTest::keyClick(window,Qt::Key_Menu,Qt::NoModifier,0);
        } else {
            QTest::mousePress(window,Qt::RightButton,Qt::NoModifier,point,0);
            QCoreApplication::processEvents();QTest::qWait(50);
            const bool held=window->isVisible() && item->property("visible").toBool() && itemWindow(item)==window;
            QTest::mouseRelease(window,Qt::RightButton,Qt::NoModifier,point,0);
            if(!held)return false;
        }
        return true;
    }
    return false;
}
static bool clickFavoriteAction(bool remove)
{
    for (auto widget:QApplication::topLevelWidgets()) {
        auto menu=qobject_cast<QMenu *>(widget);
        if (!menu || !menu->isVisible()) continue;
        for (auto action:menu->actions()) {
            if (!action->isEnabled() || action->isSeparator()) continue;
            const auto text=action->text().remove('&');
            if (!text.contains("Favorites",Qt::CaseInsensitive) || text.contains("Remove",Qt::CaseInsensitive)!=remove) continue;
            const auto point=menu->actionGeometry(action).center();
            QTest::mousePress(menu,Qt::LeftButton,Qt::NoModifier,point,0);
            QCoreApplication::processEvents();QTest::qWait(50);
            const bool held=menu->isVisible() && action->isEnabled();
            QTest::mouseRelease(menu,Qt::LeftButton,Qt::NoModifier,point,0);
            return held;
        }
    }
    return false;
}
static void step()
{
    const auto children=reinterpret_cast<Children>(dlsym(RTLD_DEFAULT,"_ZNK10QQuickItem10childItemsEv"));
    const auto grab=reinterpret_cast<Grab>(dlsym(RTLD_DEFAULT,"_ZN12QQuickWindow10grabWindowEv"));
    if (!children || !grab) {finish("QtQuick native adapter unavailable");return;}
    if (!fixture) for (auto window:QGuiApplication::allWindows()) {
        fixture=find(window->property("contentItem").value<QObject *>(),"domainosApplicationsTestFixture",children);
        if (fixture) break;
    }
    if (!fixture) {finish("Application fixture missing");return;}
    auto controller=fixture->property("controller").value<QObject *>();
    auto catalog=qobject_cast<QAbstractItemModel *>(controller->property("catalogModel").value<QObject *>());
    if (stage==0) {
        if (!findLeaf(catalog,"irix-domainos-qa-first.desktop",{}) && retries++<8) {QTimer::singleShot(500,step);return;}
        if (leafPath.isEmpty()) {finish("Real test Desktop Entry not found in native Kicker catalog");return;}
        QJsonArray rows;for (int row=0;row<catalog->rowCount();row++) rows.append(record(catalog,row));
        report["catalog_root_rows"]=rows;report["leaf_path"]=QJsonArray::fromVariantList(leafPath);
        fixture->setProperty("leafPath",leafPath);
    }
    static const QStringList names{"initial","filtered_dispatch","pin_first","pin_second","move","launch_pin","unpin","bounds","unavailable_pin","remove_unavailable","configure","favorites","favorite_removed","favorite_readded"};
    auto snapshot=QJsonDocument::fromJson(fixture->property("snapshotJson").toString().toUtf8()).object();
    // rowCount() is an invokable, not a QML notify property. Read the settled
    // native proxy directly rather than a cached JSON binding from navigation.
    auto filtered=qobject_cast<QAbstractItemModel *>(controller->property("filteredModel").value<QObject *>());
    if (filtered) snapshot["filteredCount"]=filtered->rowCount();
    auto metadata=qobject_cast<QAbstractItemModel *>(controller->property("pinnedMetadataModel").value<QObject *>());
    QJsonArray pinRows;if (metadata) for (int row=0;row<metadata->rowCount();row++) pinRows.append(record(metadata,row));
    snapshot["native_pin_metadata"]=pinRows;
    report[names[stage]]=snapshot;
    if (stage==8) for (auto window:QGuiApplication::allWindows()) if (window->isVisible() && window->inherits("QQuickWindow")) {
        if (find(window->property("contentItem").value<QObject *>(),"domainosApplicationsPopupContent",children))
            grab(window).save(qEnvironmentVariable("IRIX_DOMAINOS_APPLICATIONS_DIR")+"/DRAWER.png");
    }
    if (++stage==names.size()) {report["qt_version"]=qVersion();finish();return;}
    fixture->setProperty("scenario",stage);
    if (stage==2 || stage==12 || stage==13) QTimer::singleShot(350,[](){
        const bool opened=openContext(stage==13);
        QTimer::singleShot(200,[opened](){
            const QString key=stage==2?"real_favorite_add_context_click":stage==12?"real_favorite_remove_context_click":"real_favorite_keyboard_context_click";
            report[key]=opened && clickFavoriteAction(stage==12);
            QTimer::singleShot(700,step);
        });
    });
    else if (stage==1 || stage==10 || stage==11) QTimer::singleShot(250,[](){
        const QString reportKey=stage==1?"real_leaf_mouse_click":stage==10?"real_configure_mouse_click":"real_favorites_mouse_click";
        const QString target=stage==1?"domainosApplicationEntry_0":stage==10?"domainosPinnedPreferencesEntry":"domainosApplicationsFavoritesButton";
        report[reportKey]=click(target);
        QTimer::singleShot(stage==1?2000:200,step);
    });
    else QTimer::singleShot(300,step);
}
extern "C" int interceptedExec() asm("_ZN12QApplication4execEv");
extern "C" int interceptedExec()
{
    const auto original=reinterpret_cast<int (*)()>(dlsym(RTLD_NEXT,"_ZN12QApplication4execEv"));
    if (!original || qEnvironmentVariable("IRIX_DOMAINOS_APPLICATIONS_TEST")!="1") return original?original():1;
    QTimer::singleShot(1500,step);
    QTimer::singleShot(18000,[](){finish("Bounded application test timeout");});
    return original();
}
