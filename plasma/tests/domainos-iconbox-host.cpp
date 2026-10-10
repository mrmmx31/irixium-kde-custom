// SPDX-License-Identifier: GPL-3.0-or-later
// Test-only mouse driver for the production Iconbox in private plasmawindowed.
#include <QApplication>
#include <QFile>
#include <QImage>
#include <QJsonArray>
#include <QJsonDocument>
#include <QJsonObject>
#include <QMenu>
#include <QMouseEvent>
#include <QProcess>
#include <QScreen>
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
static QJsonObject checks;
static int phase=0,attempts=0;
static QObject *find(QObject *root,Children children) {
    if (!root)return nullptr;
    if (root->objectName()=="domainosIconboxNativeCandidate")return root;
    if (root->inherits("QQuickItem"))for(auto child:children(root))if(auto result=find(child,children))return result;
    return nullptr;
}
static QVariant invoke(const char *method,QVariant argument=QVariant()) {
    QVariant result;
    if (argument.isValid())QMetaObject::invokeMethod(fixture,method,Qt::DirectConnection,Q_RETURN_ARG(QVariant,result),Q_ARG(QVariant,argument));
    else QMetaObject::invokeMethod(fixture,method,Qt::DirectConnection,Q_RETURN_ARG(QVariant,result));
    return result;
}
static QJsonObject state() {return QJsonDocument::fromJson(invoke("nativeUiState").toString().toUtf8()).object();}
static QJsonObject coordinate(const QString &title) {return QJsonDocument::fromJson(invoke("coordinates",title).toString().toUtf8()).object();}
static void click(QJsonObject position,Qt::MouseButton button,Qt::KeyboardModifiers modifiers=Qt::NoModifier,bool twice=false) {
    const QPointF local(position["x"].toDouble(),position["y"].toDouble());
    const QPointF global=window->mapToGlobal(local.toPoint());
    if(twice){
        QProcess::execute("xdotool",{"mousemove","--sync",QString::number(qRound(global.x())),QString::number(qRound(global.y())),
            "click","--repeat","2","--delay","80","1"});
        return;
    }
    QMouseEvent press(QEvent::MouseButtonPress,local,global,button,button,modifiers);QApplication::sendEvent(window,&press);
    QMouseEvent release(QEvent::MouseButtonRelease,local,global,button,Qt::NoButton,modifiers);QApplication::sendEvent(window,&release);
}
static void complete() {
    const auto grab=reinterpret_cast<Grab>(dlsym(RTLD_DEFAULT,"_ZN12QQuickWindow10grabWindowEv"));
    QJsonObject report{{"checks",checks},{"state",fixture ? state() : QJsonObject()}};
    report["capture_saved"]=window && grab && grab(window).save(qEnvironmentVariable("IRIX_DOMAINOS_ICONBOX_CAPTURE"));
    QFile file(qEnvironmentVariable("IRIX_DOMAINOS_ICONBOX_REPORT"));
    if(file.open(QIODevice::WriteOnly))file.write(QJsonDocument(report).toJson());
    for(auto widget:owned)widget->close();
    QCoreApplication::quit();
}
static void tick() {
    if(++attempts>80){checks["native_scenario_completed"]=false;complete();return;}
    if(!fixture){
        const auto children=reinterpret_cast<Children>(dlsym(RTLD_DEFAULT,"_ZNK10QQuickItem10childItemsEv"));
        for(auto candidate:QGuiApplication::allWindows())if(children && (fixture=find(candidate->property("contentItem").value<QObject *>(),children))){window=candidate;break;}
        if(!fixture){QTimer::singleShot(100,tick);return;}
    }
    const auto current=state();
    if(phase==0){
        if(coordinate("DomainOS native owned 1").isEmpty()){QTimer::singleShot(100,tick);return;}
        checks["native_iconbox_loaded"]=true;
        checks["native_scope_reads_owned_pid"]=coordinate("DomainOS native owned 1")["pid"].toInt()==getpid();
        click(coordinate("DomainOS native owned 1"),Qt::LeftButton);
        phase=1;
    }else if(phase==1){
        checks["native_single_click_selects_without_activation"]=current["selected"].toArray().contains(coordinate("DomainOS native owned 1")["key"]);
        click(coordinate("DomainOS native owned 2"),Qt::LeftButton,Qt::ControlModifier);
        phase=2;
    }else if(phase==2){
        checks["native_control_click_accumulates_selection"]=current["selected"].toArray().size()==2;
        click(coordinate("DomainOS native owned 1"),Qt::RightButton);
        phase=3;
    }else if(phase==3){
        auto menu=qobject_cast<QMenu *>(QApplication::activePopupWidget());
        if(!menu){QTimer::singleShot(100,tick);return;}
        QJsonArray texts;
        for(auto action:menu->actions())texts.append(action->text().remove('&'));
        checks["installed_native_menu_opened"]=true;
        checks["native_close_preserved"]=texts.contains("Close");
        checks["native_more_actions_preserved"]=texts.contains("More");
        checks["native_pin_preserved_for_drawer"]=texts.contains("Pin to Task Manager");
        checks["organization_added_to_native_menu"]=texts.contains(QString::fromUtf8("Organizar todas as selecionadas"));
        checks["forced_termination_is_submenu"]=texts.contains("Processo");
        QPixmap screenshot=QGuiApplication::primaryScreen()->grabWindow(0);
        checks["native_menu_capture_saved"]=screenshot.save(qEnvironmentVariable("IRIX_DOMAINOS_ICONBOX_MENU_CAPTURE"));
        menu->close();
        phase=4;
    }else if(phase==4){
        click(coordinate("DomainOS native owned 1"),Qt::LeftButton,Qt::NoModifier,true);
        phase=5;
    }else if(phase==5){
        const auto active=current["activeTitles"].toArray();
        if(!active.contains("DomainOS native owned 1")){QTimer::singleShot(100,tick);return;}
        checks["native_double_click_activation_observed"]=true;
        checks["native_scenario_completed"]=true;
        complete();return;
    }
    QTimer::singleShot(150,tick);
}
extern "C" int interceptedExec() asm("_ZN12QApplication4execEv");
extern "C" int interceptedExec() {
    const auto original=reinterpret_cast<int (*)()>(dlsym(RTLD_NEXT,"_ZN12QApplication4execEv"));
    if(!original)return 2;
    for(int index=1;index<=2;++index){auto widget=new QWidget;widget->setWindowTitle(QString("DomainOS native owned %1").arg(index));widget->resize(240,120);widget->move(50+index*260,70);widget->show();owned.append(widget);}
    QTimer::singleShot(1200,tick);
    return original();
}
