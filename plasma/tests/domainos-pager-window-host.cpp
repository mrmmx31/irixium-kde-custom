// SPDX-FileCopyrightText: 2026 IRIX Classic contributors
// SPDX-License-Identifier: GPL-3.0-or-later
// Runs only inside the installed plasmawindowed in a PRIVATE Wayland session.
#include <QApplication>
#include <QFile>
#include <QJsonArray>
#include <QJsonDocument>
#include <QJsonObject>
#include <QLabel>
#include <QWindow>
#include <QTest>
#include <QTimer>
#include <dlfcn.h>
#include <unistd.h>

static QObject *fixture=nullptr;
static QWindow *host=nullptr;
static QList<QWidget *> owned;
static QJsonObject checks, latest;
static QVariant staleIdentity;
static int stage=0,attempts=0,operationsBefore=0;
static QString firstDesktop, secondDesktop;
using Children=QList<QObject *> (*)(QObject *);
using Map=QPointF (*)(QObject *,const QObject *,const QPointF &);
using Grab=QImage (*)(QWindow *);
static QList<QObject *> descend(QObject *root) {
    QList<QObject *> result;
    if(!root)return result;
    result.append(root);
    const auto children=reinterpret_cast<Children>(dlsym(RTLD_DEFAULT,"_ZNK10QQuickItem10childItemsEv"));
    if(children && root->inherits("QQuickItem"))for(auto child:children(root))result.append(descend(child));
    return result;
}
static QVariant invoke(const char *method,const QVariant &argument={}) {
    QVariant result;
    if(argument.isValid())QMetaObject::invokeMethod(fixture,method,Qt::DirectConnection,Q_RETURN_ARG(QVariant,result),Q_ARG(QVariant,argument));
    else QMetaObject::invokeMethod(fixture,method,Qt::DirectConnection,Q_RETURN_ARG(QVariant,result));
    return result;
}
static void sample(){latest=QJsonDocument::fromJson(invoke("testState").toString().toUtf8()).object();}
static int operations(){return latest["operations"].toInt();}
static QObject *rectangle(const QString &title,const QString &desktop={}) {
    for(auto item:descend(fixture)) {
        if(item->objectName().startsWith("domainosNativeWindow_") && item->property("windowTitle").toString()==title
                && item->property("nativePid").toInt()==getpid()
                && (desktop.isEmpty() || item->objectName().startsWith("domainosNativeWindow_"+desktop+"_")))return item;
    }
    return nullptr;
}
static bool minimized(const QString &title){auto item=rectangle(title);return item && item->property("minimized").toBool();}
static QPoint mapPoint(QObject *item,const QPointF &point){
    const auto map=reinterpret_cast<Map>(dlsym(RTLD_DEFAULT,"_ZNK10QQuickItem9mapToItemEPKS_RK7QPointF"));
    return map ? map(item,host->property("contentItem").value<QObject *>(),point).toPoint() : QPoint(-1,-1);
}
static QPoint position(QObject *item){return mapPoint(item,QPointF(item->property("width").toDouble()/2,item->property("height").toDouble()/2));}
static void click(QObject *item){QTest::mouseClick(host,Qt::LeftButton,Qt::NoModifier,position(item));}
static QString title(int index){return owned[index]->windowTitle();}
static void finish(bool success) {
    checks["native_scenario_completed"]=success;
    sample();
    QFile file(qEnvironmentVariable("IRIX_DOMAINOS_PAGER_WINDOW_DIR")+"/HOST.json");
    QJsonObject result{{"checks",checks},{"state",latest},{"stage",stage},{"host_pid",int(getpid())},{"host_executable",QFile::symLinkTarget("/proc/self/exe")}};
    if(file.open(QIODevice::WriteOnly))file.write(QJsonDocument(result).toJson());
    for(auto source:owned)source->close();
    QCoreApplication::quit();
}
static void tick() {
    if(++attempts>220){finish(false);return;}
    if(!fixture){
        for(auto window:QGuiApplication::allWindows()) {
            if(!window->inherits("QQuickWindow"))continue;
            for(auto item:descend(window->property("contentItem").value<QObject *>()))if(item->objectName()=="domainosPagerOwnedFixture") {
                fixture=item;host=window;host->setTitle("DOMAINOS-GEOMETRY-HOST");invoke("setOwnedPid",int(getpid()));break;
            }
            if(fixture)break;
        }
        if(!fixture){QTimer::singleShot(100,tick);return;}
    }
    sample();
    if(stage==0){
        const auto desktops=latest["desktops"].toArray();
        if(desktops.size()!=2 || !latest["available"].toBool() || latest["hostPresentInPager"].toBool())goto again;
        firstDesktop=desktops[0].toObject()["id"].toString();secondDesktop=desktops[1].toObject()["id"].toString();
        if(!rectangle(title(0),firstDesktop) || !rectangle(title(1),firstDesktop))goto again;
        checks["real_native_wayland_pager_and_two_own_uuid_windows"]=latest["backend"].toString()=="wayland"
            && latest["ownWindows"].toArray().size()==2;
        invoke("activateOwn",title(0));stage=1;
    }else if(stage==1){
        if(!owned[0]->isActiveWindow())goto again;
        auto target=rectangle(title(1),firstDesktop);if(!target)goto again;
        operationsBefore=operations();QTest::mousePress(host,Qt::LeftButton,Qt::NoModifier,position(target));sample();
        checks["geometric_press_has_no_early_operation"]=operations()==operationsBefore;
        checks["geometric_press_captures_native_uuid_and_pid"]=target->property("pressedDesktop").toString()==firstDesktop
            && target->property("nativePid").toInt()==getpid();
        QTest::mouseRelease(host,Qt::LeftButton,Qt::NoModifier,position(target));stage=2;
    }else if(stage==2){
        if(!owned[1]->isActiveWindow())goto again;
        checks["physical_geometric_click_focuses_inactive_window"]=true;
        checks["geometric_click_dispatches_once_and_preserves_desktop"]=operations()==operationsBefore+1
            && latest["lastOperation"].toString()=="activate-pager-window" && latest["current"].toString()==firstDesktop;
        checks["geometric_click_does_not_maximize"]=!owned[1]->isMaximized();
        owned[1]->showMinimized();invoke("activateOwn",title(0));stage=3;
    }else if(stage==3){
        if(!minimized(title(1)) || !owned[0]->isActiveWindow())goto again;
        checks["minimized_geometric_outline_remains_native"]=true;click(rectangle(title(1),firstDesktop));stage=4;
    }else if(stage==4){
        if(!owned[1]->isActiveWindow() || minimized(title(1)))goto again;
        checks["physical_outline_click_restores_and_focuses"]=true;
        const auto grab=reinterpret_cast<Grab>(dlsym(RTLD_DEFAULT,"_ZN12QQuickWindow10grabWindowEv"));
        checks["owned_pager_window_capture_saved"]=grab && grab(host).save(qEnvironmentVariable("IRIX_DOMAINOS_PAGER_WINDOW_DIR")+"/GEOMETRIC-WAYLAND.png");
        invoke("moveOwnSecond",1);stage=5;
    }else if(stage==5){
        if(!rectangle(title(1),secondDesktop) || rectangle(title(1),firstDesktop))goto again;
        staleIdentity=invoke("secondIdentity");operationsBefore=operations();
        checks["wrong_pid_and_desktop_are_rejected"]=invoke("rejectWrongIdentities").toBool();sample();
        checks["rejected_identities_do_not_dispatch"]=operations()==operationsBefore && latest["current"].toString()==firstDesktop;
        click(rectangle(title(1),secondDesktop));stage=6;
    }else if(stage==6){
        if(latest["current"].toString()!=secondDesktop || !owned[1]->isActiveWindow())goto again;
        checks["physical_other_desktop_window_click_switches_and_focuses"]=true;
        invoke("activateDesktopPosition",0);stage=7;
    }else if(stage==7){
        if(latest["current"].toString()!=firstDesktop || latest["pendingActivations"].toInt())goto again;
        QObject *tile=nullptr;
        for(auto item:descend(fixture))if(item->objectName()=="domainosDesktopTile_1")tile=item;
        if(!tile)goto again;
        operationsBefore=operations();
        const auto header=mapPoint(tile,QPointF(tile->property("width").toDouble()/2,12));
        QTest::mouseClick(host,Qt::LeftButton,Qt::NoModifier,header);stage=8;
    }else if(stage==8){
        if(latest["current"].toString()!=secondDesktop || latest["pendingActivations"].toInt())goto again;
        checks["card_header_retains_desktop_activation"]=operations()==operationsBefore+1 && latest["lastOperation"].toString()=="activate-desktop";
        invoke("activateDesktopPosition",0);stage=9;
    }else if(stage==9){
        if(latest["current"].toString()!=firstDesktop || latest["pendingActivations"].toInt() || !rectangle(title(0),firstDesktop))goto again;
        auto target=rectangle(title(0),firstDesktop);operationsBefore=operations();
        QTest::mousePress(host,Qt::LeftButton,Qt::NoModifier,position(target));
        QTest::mouseMove(host,QPoint(host->width()-2,host->height()-2));
        QTest::mouseRelease(host,Qt::LeftButton,Qt::NoModifier,QPoint(host->width()-2,host->height()-2));sample();
        checks["cancelled_geometric_press_has_no_operation"]=operations()==operationsBefore && target->property("pressedDesktop").toString().isEmpty();
        checks["owned_host_native_activation_requested"]=invoke("activateOwnHost").toBool();stage=11;
    }else if(stage==11){
        if(!host->isActive())goto again;
        auto target=rectangle(title(0),firstDesktop);if(!target)goto again;
        const auto focus=reinterpret_cast<void (*)(QObject *)>(dlsym(RTLD_DEFAULT,"_ZN10QQuickItem16forceActiveFocusEv"));
        if(!focus)goto again;
        focus(target);QTest::qWait(100);operationsBefore=operations();
        checks["geometric_window_native_keyboard_focus"]=target->property("activeFocus").toBool();
        QTest::keyPress(host,Qt::Key_Return);sample();
        checks["keyboard_press_captures_identity_without_dispatch"]=target->property("pressedKey").toInt()==Qt::Key_Return && operations()==operationsBefore;
        QTest::keyRelease(host,Qt::Key_Return);stage=12;
    }else if(stage==12){
        if(!owned[0]->isActiveWindow())goto again;
        checks["keyboard_release_focuses_native_window"]=operations()==operationsBefore+1 && latest["lastOperation"].toString()=="activate-pager-window";
        owned[1]->close();stage=10;
    }else if(stage==10){
        if(rectangle(title(1)))goto again;
        operationsBefore=operations();checks["closed_window_identity_rejected"]=!invoke("activateOldIdentity",staleIdentity).toBool();sample();
        checks["closed_identity_cannot_activate_another_window"]=operations()==operationsBefore;
        checks["pager_dimensions_preserved"]=latest["width"].toInt()==342 && latest["height"].toInt()==150;
        finish(true);return;
    }
again: QTimer::singleShot(100,tick);
}
static void start() {
    for(int index=0;index<2;++index){
        auto source=new QLabel(QString("OWN PAGER SOURCE %1").arg(index));
        source->setWindowTitle(QString("DOMAINOS-GEOMETRY-OWN-%1").arg(index));
        source->setGeometry(90+index*540,120+index*100,320,240);source->show();owned.append(source);
    }
    QTimer::singleShot(400,tick);
}
extern "C" int interceptedExec() asm("_ZN12QApplication4execEv");
extern "C" int interceptedExec(){
    const auto original=reinterpret_cast<int (*)()>(dlsym(RTLD_NEXT,"_ZN12QApplication4execEv"));
    if(!original)return 2;
    if(qEnvironmentVariable("IRIX_DOMAINOS_PAGER_WINDOW_PRIVATE")=="1")start();
    return original();
}
