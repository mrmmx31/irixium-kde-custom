// SPDX-FileCopyrightText: 2026 IRIX Classic contributors
// SPDX-License-Identifier: GPL-3.0-or-later
// Directed native occupied/vacant texture regression; private pointer only.
#include <QApplication>
#include <QDBusConnection>
#include <QDBusMessage>
#include <QDBusPendingCall>
#include <QFile>
#include <QImage>
#include <QJsonArray>
#include <QJsonDocument>
#include <QJsonObject>
#include <QProcess>
#include <QSet>
#include <QTimer>
#include <QWindow>
#include <dlfcn.h>

using Children=QList<QObject*>(*)(QObject*);
using Map=QPointF(*)(QObject*,const QPointF&);
using Grab=QImage(*)(QWindow*);
static QObject *fixture=nullptr;
static QWindow *host=nullptr;
static QJsonObject report,checks;
static int stage=0,retries=0;
static bool finishing=false;
static QObject *find(QObject *item,const QString &name) {
    if(!item)return nullptr;
    if(item->objectName()==name)return item;
    const auto children=reinterpret_cast<Children>(dlsym(RTLD_DEFAULT,"_ZNK10QQuickItem10childItemsEv"));
    if(children&&item->inherits("QQuickItem"))for(auto child:children(item))if(auto result=find(child,name))return result;
    return nullptr;
}
static QJsonObject snapshot(){return fixture ? QJsonDocument::fromJson(fixture->property("snapshotJson").toString().toUtf8()).object():QJsonObject{};}
static void gate(const QString &name,bool value){checks[name]=value;}
static bool physical(QObject *item,const QString &event={}) {
    const auto map=reinterpret_cast<Map>(dlsym(RTLD_DEFAULT,"_ZNK10QQuickItem10mapToSceneERK7QPointF"));
    if(!item||!host||!map)return false;
    const auto point=host->mapToGlobal(map(item,QPointF(item->property("width").toDouble()/2,item->property("height").toDouble()/2)).toPoint());
    if(QProcess::execute("xdotool",{"mousemove","--sync",QString::number(point.x()),QString::number(point.y())})!=0)return false;
    return event.isEmpty()||QProcess::execute("xdotool",{event,"1"})==0;
}
static void hover() {
    const auto outside=host->mapToGlobal(QPoint(3,3));
    QProcess::execute("xdotool",{"mousemove","--sync",QString::number(outside.x()),QString::number(outside.y())});
    QTimer::singleShot(100,[](){gate("physical_native_hover",physical(fixture->property("hoverSni").value<QObject*>()));});
}
static QJsonObject pixelProof(const QImage &image) {
    const auto map=reinterpret_cast<Map>(dlsym(RTLD_DEFAULT,"_ZNK10QQuickItem10mapToSceneERK7QPointF"));
    auto slot=find(fixture,"domainosTraySlot_0"),reference=find(fixture,"domainosApprovedTrayReference");
    if(!map||!slot||!reference)return {};
    const auto a=map(slot,QPointF{}).toPoint(),b=map(reference,QPointF{}).toPoint();
    QJsonArray actual,expected;QSet<QRgb> colors;
    // Inside the two-pixel relief, above the 16-pixel centered icon. This proves
    // rendered weave pixels rather than merely the presence of a texture URL.
    for(int y=2;y<4;++y)for(int x=3;x<21;++x) {
        if(!image.rect().contains(a+QPoint(x,y))||!image.rect().contains(b+QPoint(x,y)))return {};
        const auto av=image.pixel(a+QPoint(x,y)),bv=image.pixel(b+QPoint(x,y));colors.insert(av);
        actual.append(QString::number(av,16));expected.append(QString::number(bv,16));
    }
    return {{"actual",actual},{"approvedReference",expected},{"exactMatch",actual==expected},{"colorCount",int(colors.size())}};
}
static bool tooltipVisible() {
    for(auto window:QGuiApplication::allWindows())if(window->isVisible()&&QString(window->metaObject()->className()).contains("ToolTip"))return true;
    return false;
}
static void finish(const QString &failure={}) {
    if(finishing)return;finishing=true;
    if(!failure.isEmpty())report["failure"]=failure;
    report["checks"]=checks;report["hostExecutable"]=QCoreApplication::applicationFilePath();
    const auto call=QDBusMessage::createMethodCall("org.kde.StatusNotifierWatcher","/StatusNotifierWatcher","org.kde.StatusNotifierWatcher","ClearTestItems");
    QDBusConnection::sessionBus().asyncCall(call);
    QTimer::singleShot(350,[](){QFile file(qEnvironmentVariable("IRIX_DOMAINOS_TRAY_REPORT"));if(file.open(QIODevice::WriteOnly))file.write(QJsonDocument(report).toJson());QCoreApplication::quit();});
}
static void step() {
    if(!fixture)for(auto window:QGuiApplication::allWindows())if((fixture=find(window->property("contentItem").value<QObject*>(),"domainosTrayTextureFixture"))) {
        host=window;host->setFlags(Qt::Tool|Qt::FramelessWindowHint);host->setGeometry(180,380,460,180);host->show();
        // Changing X11 flags recreates the window. Let mapping/focus events
        // dispatch before sending a native physical press to its new XID.
        QTimer::singleShot(200,[](){gate("private_window_focus",QProcess::execute("xdotool",{"windowfocus","--sync",QString::number(host->winId())})==0);QTimer::singleShot(100,step);});return;
    }
    if(!fixture){finish("Native texture fixture missing");return;}
    const auto state=snapshot();
    if(stage==0&&state["visible"].toArray()!=QJsonArray{"domainos-fixture-sni-1"}) {
        if(++retries<20){QTimer::singleShot(200,step);return;}finish("One visible native item not ready");return;
    }
    const QStringList names{"occupied","pressed","released","vacant","restored_hints","hints_disabled"};
    report[names[stage]]=state;
    const auto grab=reinterpret_cast<Grab>(dlsym(RTLD_DEFAULT,"_ZN12QQuickWindow10grabWindowEv"));
    const auto image=grab ? grab(host):QImage{};
    gate(names[stage]+"_capture",!image.isNull()&&image.save(qEnvironmentVariable("IRIX_DOMAINOS_TRAY_DIR")+"/"+names[stage]+".png"));
    const auto visual=state["slots"].toArray();
    if(stage==0) {
        const auto pixels=pixelProof(image);report["occupiedPixels"]=pixels;
        gate("occupied_face_matches_approved_rendered_weave",pixels["exactMatch"].toBool()&&pixels["colorCount"].toInt()==2);
        gate("occupied_relief_and_native_item_preserved",visual[0].toObject()["id"].toString()=="domainos-fixture-sni-1"&&!visual[0].toObject()["sunken"].toBool());
        bool empty=true;for(int i=1;i<6;++i)empty&=visual[i].toObject()["id"].toString().isEmpty()&&visual[i].toObject()["texture"].toString().isEmpty();
        gate("five_empty_slots_keep_plain_face",empty);gate("native_hints_default_disabled",!state["hover"].toObject()["active"].toBool());
        gate("physical_press_on_native_item",physical(fixture->property("hoverSni").value<QObject*>(),"mousedown"));
    } else if(stage==1) {
        const auto hoverState=state["hover"].toObject();
        gate("pressed_relief_follows_native_provider_scale",hoverState["iconScale"].toDouble()<1&&visual[0].toObject()["sunken"].toBool());
        gate("physical_release_on_native_item",QProcess::execute("xdotool",{"mouseup","1"})==0);
    } else if(stage==2) {
        gate("release_restores_raised_relief",!visual[0].toObject()["sunken"].toBool());fixture->setProperty("scenario",1);
    } else if(stage==3) {
        const auto pixels=pixelProof(image);report["vacantPixels"]=pixels;
        gate("empty_face_keeps_existing_flat_fill",state["visible"].toArray().isEmpty()&&pixels["colorCount"].toInt()==1&&!pixels["exactMatch"].toBool());
        bool empty=true;for(const auto &row:visual)empty&=row.toObject()["id"].toString().isEmpty()&&row.toObject()["texture"].toString().isEmpty();gate("native_removal_clears_texture_from_every_empty_slot",empty);
        fixture->setProperty("scenario",2);QTimer::singleShot(300,hover);
    } else if(stage==4) {
        const auto pixels=pixelProof(image);report["restoredPixels"]=pixels;
        gate("native_reappearance_restores_approved_face",state["visible"].toArray()==QJsonArray{"domainos-fixture-sni-1"}&&pixels["exactMatch"].toBool()&&pixels["colorCount"].toInt()==2);
        gate("native_hints_binding_restored",state["hover"].toObject()["active"].toBool());gate("real_native_hint_popup_appears",tooltipVisible());
        for(auto window:QGuiApplication::allWindows())if(window->isVisible()&&QString(window->metaObject()->className()).contains("ToolTip"))if(grab)grab(window).save(qEnvironmentVariable("IRIX_DOMAINOS_TRAY_DIR")+"/native-tooltip.png");
        fixture->setProperty("scenario",3);
    } else {
        gate("hints_disable_preserves_native_binding_policy",!state["hover"].toObject()["active"].toBool()&&!tooltipVisible());
        gate("hints_do_not_change_native_item_or_texture",state["visible"].toArray()==QJsonArray{"domainos-fixture-sni-1"}&&visual[0].toObject()["texture"].toString()==report["occupied"].toObject()["slots"].toArray()[0].toObject()["texture"].toString());finish();return;
    }
    ++stage;QTimer::singleShot(stage==4 ? 1800:650,step);
}
extern "C" int interceptedExec() asm("_ZN12QApplication4execEv");
extern "C" int interceptedExec() {
    const auto original=reinterpret_cast<int(*)()>(dlsym(RTLD_NEXT,"_ZN12QApplication4execEv"));
    if(qEnvironmentVariable("IRIX_DOMAINOS_TRAY_TEST")!="1")return original ? original():1;
    QTimer::singleShot(1500,step);QTimer::singleShot(16000,[](){finish("Bounded texture proof timeout");});return original ? original():1;
}
