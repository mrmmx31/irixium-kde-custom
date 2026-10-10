// SPDX-License-Identifier: GPL-3.0-or-later
// Runs inside installed plasmawindowed with three owned clients only.
#include <QApplication>
#include <QCursor>
#include <QFile>
#include <QJsonArray>
#include <QJsonDocument>
#include <QJsonObject>
#include <QLabel>
#include <QSettings>
#include <QTest>
#include <QTimer>
#include <dlfcn.h>
#include <unistd.h>

static QObject *fixture=nullptr;
static QWindow *fixtureWindow=nullptr;
static QList<QWidget *> owned;
static QJsonObject checks,state;
static int phase=0,attempts=0,transitions=0;
static QString activated;
static QJsonArray transitionsHistory;
using Children=QList<QObject *> (*)(QObject *);
using Grab=QImage (*)(QWindow *);

static QObject *find(QObject *item,Children children) {
    if (!item) return nullptr;
    if (item->objectName()=="domainosThumbnailLifecycleFixture") return item;
    if(item->inherits("QQuickItem"))for (auto child:children(item)) if (auto result=find(child,children)) return result;
    return nullptr;
}
static QVariant invoke(const char *method,const QVariant &a={},const QVariant &b={}) {
    QVariant result;
    if (b.isValid()) QMetaObject::invokeMethod(fixture,method,Qt::DirectConnection,Q_RETURN_ARG(QVariant,result),Q_ARG(QVariant,a),Q_ARG(QVariant,b));
    else if(a.isValid()) QMetaObject::invokeMethod(fixture,method,Qt::DirectConnection,Q_RETURN_ARG(QVariant,result),Q_ARG(QVariant,a));
    else QMetaObject::invokeMethod(fixture,method,Qt::DirectConnection,Q_RETURN_ARG(QVariant,result));
    return result;
}
static QWindow *tooltip() {
    for (auto window:QGuiApplication::allWindows())
        if(window->isVisible() && QByteArray(window->metaObject()->className()).contains("ToolTipDialog"))
            return window;
    return nullptr;
}
static void capture(const char *filename) {
    const auto grab=reinterpret_cast<Grab>(dlsym(RTLD_DEFAULT,"_ZN12QQuickWindow10grabWindowEv"));
    if (auto window=tooltip();window && grab) grab(window).save(qEnvironmentVariable("IRIX_DOMAINOS_UNITY_OUTPUT")+"/"+filename);
}
static void finish() {
    QFile file(qEnvironmentVariable("IRIX_DOMAINOS_UNITY_OUTPUT")+"/native.json");
    if(file.open(QIODevice::WriteOnly)) file.write(QJsonDocument(QJsonObject{{"checks",checks},{"state",state},{"transitions",transitionsHistory},{"host_executable",QFile::symLinkTarget("/proc/self/exe")}}).toJson());
    for (auto window:owned) {window->close();delete window;}
    QCoreApplication::quit();
}
static void showCell(int which,bool previews) {
    // Use real hover, including the native delay. Keep the fixture near the
    // screen's lower edge like the actual panel; a 396px preview otherwise
    // covers a centered test window's anchor and legitimately retains hover.
    invoke("prepare",which,previews);
    const auto target=QJsonDocument::fromJson(invoke("point",which).toString().toUtf8()).object();
    // QTest::mouseMove(QWindow*) only injects a Qt event; it does not move
    // the native cursor used by ToolTipDialog's Enter/Leave hit testing.
    QCursor::setPos(fixtureWindow->mapToGlobal(QPoint(fixtureWindow->width()-16,fixtureWindow->height()-16)));
    QCoreApplication::processEvents();
    QCursor::setPos(QPoint(qRound(target["x"].toDouble()),qRound(target["y"].toDouble())));
}
static void tick() {
    if (++attempts>120) {checks["bounded_native_scenario_completed"]=false;finish();return;}
    if (!fixture) {
        const auto children=reinterpret_cast<Children>(dlsym(RTLD_DEFAULT,"_ZNK10QQuickItem10childItemsEv"));
        for(auto window:QGuiApplication::allWindows())
            if (children && (fixture=find(window->property("contentItem").value<QObject *>(),children))) {fixtureWindow=window;break;}
        if(!fixture) {QTimer::singleShot(100,tick);return;}
        invoke("setOwnedPid",int(getpid()));
        fixtureWindow->setPosition(QPoint(240,530));
    }
    state=QJsonDocument::fromJson(invoke("state").toString().toUtf8()).object();
    const auto first=state["first"].toObject(),second=state["second"].toObject();
    if(phase==0) {
        if(state["count"].toInt()!=3) {QTimer::singleShot(100,tick);return;}
        checks["three_owned_native_clients_from_real_tasksmodel"]=true;
        checks["default_no_preview_content"]=!first["contentsLoaded"].toBool();
        showCell(0,true);phase=1;
    } else if(phase==1) {
        const auto cards=first["cards"].toArray();
        checks["three_empty_cards_before_provider_frame"]=first["visible"].toBool() && cards.size()==3;
        bool geometry=cards.size()==3,notCapturing=true;
        for(const auto value:cards){const auto card=value.toObject();geometry&=card["width"].toDouble()>=160 && card["height"].toDouble()==178 && !card["live"].toBool();}
        for(const auto value:first["providers"].toArray())notCapturing&=!value.toObject()["active"].toBool() && !value.toObject()["loaded"].toBool();
        checks["empty_cards_have_complete_geometry"]=geometry;
        checks["missing_provider_does_not_block_or_start_capture"]=notCapturing;
        auto window=tooltip();checks["native_empty_card_surface_is_measured"]=window && window->height()>=390;
        capture("EMPTY-CARDS.png");
        if(!window || cards.isEmpty()){checks["empty_card_click_activates_owned_window"]=false;finish();return;}
        const auto card=cards[2].toObject();activated=card["key"].toString();
        const QPoint target(qRound(card["x"].toDouble()),qRound(card["y"].toDouble()));
        QCursor::setPos(target);QCoreApplication::processEvents();
        const QPoint point=window->mapFromGlobal(target);
        QTest::mouseClick(window,Qt::LeftButton,Qt::NoModifier,point);phase=2;
    } else if(phase==2) {
        const auto active=state["active"].toArray();
        if(!active.contains(activated)){QTimer::singleShot(100,tick);return;}
        checks["empty_card_click_activates_owned_window"]=state["requests"].toArray()==QJsonArray{activated};
        showCell(0,false);phase=3;
    } else if(phase==3) {
        auto window=tooltip();const auto grab=reinterpret_cast<Grab>(dlsym(RTLD_DEFAULT,"_ZN12QQuickWindow10grabWindowEv"));
        const auto image=window && grab ? grab(window) : QImage();
        capture("IRIXIUM-HINT-FRAME.png");
        const auto color=image.isNull() ? QColor() : image.pixelColor(image.width()/2,1);
        checks["native_frame_uses_private_irixium_scheme"]=color.isValid() && qAbs(color.red()-color.blue())<=1 && qAbs(color.green()-color.red())<=1;
        checks["switch_back_to_titles_unloads_cards"]=first["visible"].toBool() && !first["contentsLoaded"].toBool() && first["cards"].toArray().isEmpty();
        transitions=0;showCell(0,true);phase=4;
    } else if(phase==4) {
        const bool useFirst=transitions%2==0;
        const auto current=useFirst ? first : second,other=useFirst ? second : first;
        const auto native=tooltip();
        transitionsHistory.append(QJsonObject{{"index",transitions},{"first",first},{"second",second},
            {"fixture_geometry",QJsonArray{fixtureWindow->x(),fixtureWindow->y(),fixtureWindow->width(),fixtureWindow->height()}},
            {"native_cursor",QJsonArray{QCursor::pos().x(),QCursor::pos().y()}},
            {"tooltip_geometry",native ? QJsonArray{native->x(),native->y(),native->width(),native->height()} : QJsonArray{}}});
        checks[QString("owner_transition_%1_never_has_two_owners").arg(transitions)]=int(first["visible"].toBool())+int(second["visible"].toBool())==1;
        checks[QString("owner_transition_%1_has_one_visible_owner").arg(transitions)]=current["visible"].toBool() && !other["visible"].toBool() && !other["bodyVisible"].toBool();
        checks[QString("owner_transition_%1_previous_content_unloaded").arg(transitions)]=!other["contentsLoaded"].toBool();
        if(++transitions<12)showCell(transitions%2,transitions%3==0);
        else {transitions=0;showCell(0,true);phase=5;}
    } else if(phase==5) {
        const bool preview=transitions%2==0;
        checks[QString("mode_transition_%1_matches_preference").arg(transitions)]=first["visible"].toBool() && first["contentsLoaded"].toBool()==preview && !second["visible"].toBool();
        if(++transitions<8)showCell(0,transitions%2==0);
        else {capture("RESTORED-TITLES.png");invoke("hide");phase=6;}
    } else {
        checks["closing_tooltip_releases_all_cards"]=!first["visible"].toBool() && !first["contentsLoaded"].toBool() && !second["visible"].toBool();
        checks["bounded_native_scenario_completed"]=true;finish();return;
    }
    QTimer::singleShot(850,tick);
}
static QColor color(QSettings &config,const QString &group,const QString &key) {
    const auto raw=config.value(group+"/"+key);
    const auto values=raw.metaType().id()==QMetaType::QStringList ? raw.toStringList() : raw.toString().split(',');
    return values.size()==3 ? QColor(values[0].toInt(),values[1].toInt(),values[2].toInt()) : QColor();
}
static void start() {
    // The generic private platform theme does not load KDE's application
    // palette. Load the same selected kdeglobals into this own QApplication.
    QSettings config(qEnvironmentVariable("XDG_CONFIG_HOME")+"/kdeglobals",QSettings::IniFormat);
    auto palette=QApplication::palette();
    for(auto role:{QPalette::Window,QPalette::WindowText,QPalette::Base,QPalette::Text,QPalette::Button,QPalette::ButtonText}){
        const QString group=role==QPalette::Window || role==QPalette::WindowText ? "Colors:Window" : role==QPalette::Button || role==QPalette::ButtonText ? "Colors:Button" : "Colors:View";
        const auto value=color(config,group,role==QPalette::Window || role==QPalette::Base || role==QPalette::Button ? "BackgroundNormal" : "ForegroundNormal");
        if(value.isValid())palette.setColor(role,value);
    }
    QApplication::setPalette(palette);
    const auto expected=color(config,"Colors:Window","BackgroundNormal");
    checks["native_application_uses_private_kdeglobals_window_role"]=expected.isValid() && QApplication::palette().color(QPalette::Window)==expected;
    for(int index=0;index<3;++index){auto window=new QLabel(QString("Owned native preview source %1").arg(index));window->setWindowTitle(QString("DomainOS fallback owned %1").arg(index));window->resize(250,150);window->move(30+index*280,40);window->show();owned.append(window);}
    QTimer::singleShot(250,tick);
}
extern "C" int interceptedExec() asm("_ZN12QApplication4execEv");
extern "C" int interceptedExec() {
    const auto original=reinterpret_cast<int (*)()>(dlsym(RTLD_NEXT,"_ZN12QApplication4execEv"));
    if(!original)return 2;
    if(qEnvironmentVariable("IRIX_DOMAINOS_UNITY_PRIVATE")=="1")start();
    return original();
}
