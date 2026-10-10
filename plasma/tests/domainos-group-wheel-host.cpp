// SPDX-License-Identifier: GPL-3.0-or-later
#include <QApplication>
#include <QFile>
#include <QJsonArray>
#include <QJsonDocument>
#include <QJsonObject>
#include <QProcess>
#include <QTimer>
#include <QWidget>
#include <QWindow>
#include <dlfcn.h>
#include <unistd.h>
#include <X11/Xlib.h>

using Children=QList<QObject *> (*)(QObject *);
static QObject *fixture=nullptr;
static QWindow *host=nullptr;
static QList<QProcess*> owned;
static QJsonObject checks,snapshots;
static int phase=0,attempts=0,cycle=0;
static QString targetKey;
static QObject *findVisual(QObject *item,const QString &name) {
    if(!item)return nullptr;if(item->objectName()==name)return item;
    const auto children=reinterpret_cast<Children>(dlsym(RTLD_DEFAULT,"_ZNK10QQuickItem10childItemsEv"));
    if(item->inherits("QQuickItem") && children)for(auto child:children(item))if(auto found=findVisual(child,name))return found;
    return nullptr;
}
static QVariant invoke(const char *method) {
    QVariant result;QMetaObject::invokeMethod(fixture,method,Qt::DirectConnection,Q_RETURN_ARG(QVariant,result));return result;
}
static QJsonObject state(){return QJsonDocument::fromJson(invoke("state").toString().toUtf8()).object();}
static QJsonObject position(){return QJsonDocument::fromJson(invoke("coordinates").toString().toUtf8()).object();}
static void physical(const QStringList &args) {
    auto process=new QProcess(QCoreApplication::instance());QObject::connect(process,qOverload<int,QProcess::ExitStatus>(&QProcess::finished),process,[process](int,QProcess::ExitStatus){process->deleteLater();});process->start("xdotool",args);
}
static void pointer(int button) {
    auto p=position();physical({"mousemove",QString::number(qRound(p["x"].toDouble())),QString::number(qRound(p["y"].toDouble())),"click",QString::number(button)});
}
static void clearOwnedAttention(const QJsonArray &windows) {
    auto display=XOpenDisplay(nullptr);if(!display)return;
    for(auto value:windows) {
        auto row=value.toObject();if(!row["demandsAttention"].toBool())continue;
        const auto ids=row["windowIds"].toArray();if(ids.isEmpty())continue;
        XEvent event{};event.xclient.type=ClientMessage;event.xclient.window=ids.first().toVariant().toULongLong();
        event.xclient.message_type=XInternAtom(display,"_NET_WM_STATE",False);event.xclient.format=32;
        event.xclient.data.l[0]=0;event.xclient.data.l[1]=XInternAtom(display,"_NET_WM_STATE_DEMANDS_ATTENTION",False);event.xclient.data.l[3]=2;
        XSendEvent(display,DefaultRootWindow(display),False,SubstructureNotifyMask|SubstructureRedirectMask,&event);
    }
    XFlush(display);XCloseDisplay(display);
}
static void complete() {
    QFile file(qEnvironmentVariable("IRIX_DOMAINOS_UNITY_OUTPUT")+"/native.json");
    if(file.open(QIODevice::WriteOnly))file.write(QJsonDocument(QJsonObject{{"checks",checks},{"snapshots",snapshots},{"final",fixture ? state() : QJsonObject()},{"owned_pid",getpid()}}).toJson());
    for(auto process:owned){process->terminate();if(!process->waitForFinished(1000))process->kill();}QCoreApplication::quit();
}
static void tick() {
    if(++attempts>100){checks["native_scenario_completed"]=false;complete();return;}
    if(!fixture) {
        for(auto window:QGuiApplication::allWindows())if((fixture=findVisual(window->property("contentItem").value<QObject*>(),"domainosGroupWheelFixture"))){host=window;break;}
        if(!fixture){QTimer::singleShot(100,tick);return;}
        host->setFlags(Qt::Tool|Qt::FramelessWindowHint);host->setGeometry(200,550,594,150);host->show();
        QJsonArray pids;for(auto process:owned)pids.append(process->processId());
        QMetaObject::invokeMethod(fixture,"setOwnedPids",Qt::DirectConnection,Q_ARG(QVariant,QVariant(QString::fromUtf8(QJsonDocument(pids).toJson(QJsonDocument::Compact)))));
    }
    auto current=state();snapshots["phase_"+QString::number(phase)+"_cycle_"+QString::number(cycle)]=current;
    if(phase==0) {
        if(current["rows"].toArray().size()!=9 || current["windows"].toArray().size()!=18){clearOwnedAttention(current["windows"].toArray());QTimer::singleShot(100,tick);return;}
        checks["nine_native_groups_eighteen_owned_clients"]=true;
        checks["wheel_activation_disabled_by_default"]=!current["wheelActivation"].toBool();
        targetKey=position()["key"].toString();pointer(1);phase=1;
    }else if(phase==1) {
        checks["first_group_click_opens_native_list"]=current["open"].toBool() && current["key"].toString()==targetKey;
        pointer(5);phase=2;
    }else if(phase==2) {
        checks["default_wheel_reaches_second_page"]=current["firstVisible"].toInt()==7;
        checks["default_wheel_does_not_activate_any_owned_window"]=current["requests"].toArray().isEmpty();
        checks["page_change_dismisses_previous_group"]=!current["open"].toBool();
        targetKey=position()["key"].toString();pointer(1);phase=3;
    }else if(phase==3) {
        checks["new_group_after_wheel_opens_on_first_click"]=current["open"].toBool() && current["key"].toString()==targetKey && current["members"].toArray().size()==2;
        QMetaObject::invokeMethod(fixture,"closePicker");phase=4;
    }else if(phase==4) {pointer(4);phase=5;
    }else if(phase==5) {
        checks["default_wheel_returns_first_page"]=current["firstVisible"].toInt()==0;
        targetKey=position()["key"].toString();pointer(1);phase=6;
    }else if(phase==6) {
        checks["original_group_reopens_after_return_wheel_cycle_"+QString::number(cycle)]=current["open"].toBool() && current["key"].toString()==targetKey;
        QMetaObject::invokeMethod(fixture,"closePicker");pointer(5);phase=7;
    }else if(phase==7) {
        targetKey=position()["key"].toString();pointer(1);phase=8;
    }else if(phase==8) {
        checks["second_page_group_reopens_after_wheel_cycle_"+QString::number(cycle)]=current["open"].toBool() && current["key"].toString()==targetKey;
        if(++cycle<3){QMetaObject::invokeMethod(fixture,"closePicker");phase=4;}
        else {checks["wheel_and_group_selection_never_activate_any_window"]=current["requests"].toArray().isEmpty();checks["native_scenario_completed"]=true;complete();return;}
    }
    QTimer::singleShot(350,tick);
}
extern "C" int interceptedExec() asm("_ZN12QApplication4execEv");
extern "C" int interceptedExec() {
    auto original=reinterpret_cast<int (*)()>(dlsym(RTLD_NEXT,"_ZN12QApplication4execEv"));if(!original)return 2;
    for(int index=0;index<18;++index) {
        auto process=new QProcess(QCoreApplication::instance());
        process->start("xterm",{"-class","DomainOSWheel"+QString::number(index/2),"-name","domainos-wheel-"+QString::number(index/2),"-T",QString("DomainOS wheel group %1 member %2").arg(index/2).arg(index%2),"-geometry","20x4+30+40","-e","/bin/sleep","90"});
        process->waitForStarted(1000);owned.append(process);
    }
    QTimer::singleShot(1200,tick);return original();
}
