// SPDX-FileCopyrightText: 2026 IRIX Classic contributors
// SPDX-License-Identifier: GPL-3.0-or-later
// Physical pointer regression inside the installed Plasma host, private X11.
#include <QApplication>
#include <QFile>
#include <QImage>
#include <QJsonArray>
#include <QJsonDocument>
#include <QJsonObject>
#include <QLabel>
#include <QProcess>
#include <QPushButton>
#include <QTimer>
#include <QVBoxLayout>
#include <QWidget>
#include <QWindow>
#include <dlfcn.h>
#include <unistd.h>

using Children=QList<QObject *> (*)(QObject *);
using Map=QPointF (*)(const QObject *,const QObject *,const QPointF &);
using Grab=QImage (*)(QWindow *);
static QObject *fixture=nullptr;
static QWindow *host=nullptr;
static QWidget *owned=nullptr;
static QPushButton *minimizeButton=nullptr;
static int phase=0,attempts=0;
static QJsonObject checks;
static QJsonArray observations;
static QString key;

static QObject *find(QObject *object,const QString &name) {
    if(!object)return nullptr;
    if(object->objectName()==name)return object;
    const auto children=reinterpret_cast<Children>(dlsym(RTLD_DEFAULT,"_ZNK10QQuickItem10childItemsEv"));
    if(children && object->inherits("QQuickItem"))for(auto child:children(object))if(auto match=find(child,name))return match;
    return nullptr;
}
static QJsonObject state() {
    return fixture ? QJsonDocument::fromJson(fixture->property("snapshotJson").toString().toUtf8()).object() : QJsonObject();
}
static bool physicalClick(const QPoint &point,bool twice=false) {
    if(QProcess::execute("xdotool",{"mousemove","--sync",QString::number(point.x()),QString::number(point.y())})!=0)return false;
    return QProcess::execute("xdotool",twice ? QStringList{"click","--repeat","2","--delay","100","1"} : QStringList{"click","1"})==0;
}
static bool clickTask(bool twice=false) {
    const auto tile=fixture->property("ownedTile").value<QObject *>();
    const auto map=reinterpret_cast<Map>(dlsym(RTLD_DEFAULT,"_ZNK10QQuickItem9mapToItemEPKS_RK7QPointF"));
    if(!tile || !map || !host)return false;
    const auto content=host->property("contentItem").value<QObject *>();
    const auto local=map(tile,content,QPointF(tile->property("width").toDouble()/2,tile->property("height").toDouble()/2));
    return physicalClick(host->mapToGlobal(local.toPoint()),twice);
}
static void capture(const QString &name) {
    observations.append(QJsonObject{{"phase",name},{"state",state()},{"clientMinimized",owned->isMinimized()},{"clientActive",owned->isActiveWindow()}});
    const auto grab=reinterpret_cast<Grab>(dlsym(RTLD_DEFAULT,"_ZN12QQuickWindow10grabWindowEv"));
    if(grab && host)checks[name+"_capture_saved"]=grab(host).save(qEnvironmentVariable("IRIX_DOMAINOS_RELIEF_DIR")+"/"+name+".png");
}
static void finish(const QString &failure={}) {
    QJsonObject report{{"checks",checks},{"observations",observations},{"hostPid",int(getpid())},
        {"hostExecutable",QFile::symLinkTarget("/proc/self/exe")},{"clientWinId",QString::number(owned->winId())}};
    if(!failure.isEmpty())report["failure"]=failure;
    QFile file(qEnvironmentVariable("IRIX_DOMAINOS_RELIEF_DIR")+"/HOST.json");
    if(file.open(QIODevice::WriteOnly))file.write(QJsonDocument(report).toJson());
    owned->close();QCoreApplication::quit();
}
static void tick() {
    if(++attempts>180){finish("Bounded private client regression timeout");return;}
    if(!fixture)for(auto window:QGuiApplication::allWindows())if((fixture=find(window->property("contentItem").value<QObject *>(),"domainosMinimizedReliefFixture"))) {
        host=window;host->setFlags(Qt::Tool|Qt::FramelessWindowHint);host->setGeometry(150,610,610,170);host->show();break;
    }
    if(!fixture){QTimer::singleShot(100,tick);return;}
    const auto snapshot=state(),row=snapshot["row"].toObject(),visual=snapshot["visual"].toObject();
    if(phase==0) {
        if(row.isEmpty() || !fixture->property("ownedTile").value<QObject *>()){QTimer::singleShot(100,tick);return;}
        key=row["key"].toString();
        checks["owned_native_client_pid_winid_exact"]=row["pid"].toInt()==getpid() && row["windowIds"].toArray().contains(QJsonValue(double(owned->winId())));
        checks["physical_single_click_selected_owned_tile"]=clickTask();phase=1;
    }else if(phase==1) {
        if(!visual["selected"].toBool()){QTimer::singleShot(100,tick);return;}
        checks["restored_selected_tile_and_label_initially_sunken"]=visual["bodySunken"].toBool() && visual["labelSunken"].toBool() && !visual["pressed"].toBool();
        capture("RESTORED-SELECTED");
        owned->raise();owned->activateWindow();phase=2;
    }else if(phase==2) {
        if(!owned->isActiveWindow()){QTimer::singleShot(100,tick);return;}
        checks["physical_click_client_minimize_button"]=physicalClick(minimizeButton->mapToGlobal(minimizeButton->rect().center()));phase=3;
    }else if(phase==3) {
        if(!row["minimized"].toBool() || !owned->isMinimized()){QTimer::singleShot(100,tick);return;}
        checks["native_minimized_observed_by_tasks_and_owned_client"]=true;
        checks["minimized_selected_identity_and_pid_preserved"]=row["key"].toString()==key && row["pid"].toInt()==getpid() && visual["selected"].toBool() && snapshot["selected"].toArray()==QJsonArray{key};
        checks["minimized_selected_tile_and_label_are_raised"]=visual["fullyMinimized"].toBool() && !visual["pressed"].toBool() && !visual["bodySunken"].toBool() && !visual["labelSunken"].toBool();
        capture("MINIMIZED-SELECTED");
        checks["physical_double_click_owned_tile"]=clickTask(true);phase=4;
    }else if(phase==4) {
        if(row["minimized"].toBool() || owned->isMinimized() || !owned->isActiveWindow()){QTimer::singleShot(100,tick);return;}
        checks["native_double_click_restores_and_focuses_exact_client"]=row["key"].toString()==key && row["pid"].toInt()==getpid() && row["active"].toBool();
        checks["restored_selected_relief_returns_without_selection_loss"]=snapshot["selected"].toArray()==QJsonArray{key} && visual["selected"].toBool() && !visual["fullyMinimized"].toBool() && !visual["pressed"].toBool() && visual["bodySunken"].toBool() && visual["labelSunken"].toBool();
        capture("RESTORED-AGAIN");checks["native_scenario_completed"]=true;finish();return;
    }
    QTimer::singleShot(100,tick);
}
extern "C" int interceptedExec() asm("_ZN12QApplication4execEv");
extern "C" int interceptedExec() {
    const auto original=reinterpret_cast<int (*)()>(dlsym(RTLD_NEXT,"_ZN12QApplication4execEv"));
    if(qEnvironmentVariable("IRIX_DOMAINOS_RELIEF_PRIVATE")!="1")return original ? original() : 1;
    owned=new QWidget;owned->setWindowTitle("DomainOS owned minimized relief client");owned->resize(380,160);owned->move(700,250);
    auto layout=new QVBoxLayout(owned);layout->addWidget(new QLabel("Private native client; physical pointer only",owned));
    minimizeButton=new QPushButton("Minimizar cliente de teste",owned);layout->addWidget(minimizeButton);
    QObject::connect(minimizeButton,&QPushButton::clicked,owned,&QWidget::showMinimized);owned->show();
    QTimer::singleShot(1000,tick);return original ? original() : 1;
}
