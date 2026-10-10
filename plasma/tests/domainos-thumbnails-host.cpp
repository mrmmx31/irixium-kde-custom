// SPDX-FileCopyrightText: 2026 IRIX Classic contributors
// SPDX-License-Identifier: GPL-3.0-or-later
// Runs inside the genuine installed plasmawindowed with an entirely private
// package/session. Every rendered source window is owned by this test process.
#include <QApplication>
#include <QFile>
#include <QImage>
#include <QJsonArray>
#include <QJsonDocument>
#include <QJsonObject>
#include <QLabel>
#include <QTimer>
#include <QTest>
#include <QWidget>
#include <QWindow>
#include <dlfcn.h>
#include <unistd.h>

using Children=QList<QObject *> (*)(QObject *);
using Grab=QImage (*)(QWindow *);
static QObject *fixture=nullptr;
static QWindow *fixtureWindow=nullptr;
static QList<QWidget *> owned;
static QJsonObject checks;
static QJsonObject latest;
static int stage=0,attempts=0;
static QObject *find(QObject *root,Children children) {
    if(!root)return nullptr;
    if(root->objectName()=="domainosNativeThumbnailsFixture")return root;
    if(root->inherits("QQuickItem"))for(auto child:children(root))if(auto result=find(child,children))return result;
    return nullptr;
}
static QVariant invoke(const char *method,const QVariant &argument={}) {
    QVariant result;
    if(argument.isValid())QMetaObject::invokeMethod(fixture,method,Qt::DirectConnection,Q_RETURN_ARG(QVariant,result),Q_ARG(QVariant,argument));
    else QMetaObject::invokeMethod(fixture,method,Qt::DirectConnection,Q_RETURN_ARG(QVariant,result));
    return result;
}
static QJsonObject state(){return QJsonDocument::fromJson(invoke("testState").toString().toUtf8()).object();}
static QImage capture(const QString &name) {
    const auto grab=reinterpret_cast<Grab>(dlsym(RTLD_DEFAULT,"_ZN12QQuickWindow10grabWindowEv"));
    for(auto window:QGuiApplication::allWindows())if(window->isVisible() && QByteArray(window->metaObject()->className()).contains("ToolTipDialog")) {
        const auto image=grab ? grab(window) : QImage();
        image.save(qEnvironmentVariable("IRIX_DOMAINOS_THUMBNAIL_DIR")+"/"+name);
        return image;
    }
    return {};
}
static int colorPixels(const QImage &image,const QColor &target) {
    int found=0;for(int y=0;y<image.height();++y)for(int x=0;x<image.width();++x){
        const auto pixel=image.pixelColor(x,y);
        if(qAbs(pixel.red()-target.red())<10 && qAbs(pixel.green()-target.green())<10 && qAbs(pixel.blue()-target.blue())<10)++found;
    }return found;
}
static void finish() {
    if(!checks["native_scenario_completed"].toBool())capture("NATIVE-THUMBNAILS-UNAVAILABLE.png");
    QFile file(qEnvironmentVariable("IRIX_DOMAINOS_THUMBNAIL_DIR")+"/HOST.json");
    QJsonObject result{{"checks",checks},{"state",latest},{"host_pid",int(getpid())},{"host_executable",QFile::symLinkTarget("/proc/self/exe")}};
    if(file.open(QIODevice::WriteOnly))file.write(QJsonDocument(result).toJson());
    for(auto window:owned)window->close();QCoreApplication::quit();
}
static void tick() {
    if(++attempts>160){checks["native_scenario_completed"]=false;finish();return;}
    if(!fixture){const auto children=reinterpret_cast<Children>(dlsym(RTLD_DEFAULT,"_ZNK10QQuickItem10childItemsEv"));
        for(auto candidate:QGuiApplication::allWindows())if(children && (fixture=find(candidate->property("contentItem").value<QObject *>(),children))){fixtureWindow=candidate;break;}
        if(!fixture){QTimer::singleShot(100,tick);return;}
    }
    latest=state();
    if(stage==0){
        if(qEnvironmentVariable("IRIX_DOMAINOS_THUMBNAIL_CURRENT_DISPLAY")=="1" && latest["windowCount"].toInt()!=2){
            QVariantList records;
            for(auto window:owned){
                const auto id=uint(window->winId());
                records.append(QVariantMap{{"key",QString("window:%1").arg(id)},{"pid",int(getpid())},{"title",window->windowTitle()},
                    {"windowIds",QVariantList{id}},{"minimized",false},{"group",false}});
            }
            invoke("provideOwnedWindows",records);
            latest=state();
        }
        if(latest["windowCount"].toInt()!=2){QTimer::singleShot(100,tick);return;}
        checks[qEnvironmentVariable("IRIX_DOMAINOS_THUMBNAIL_CURRENT_DISPLAY")=="1" ? "only_explicit_owned_window_ids_supplied" : "native_owned_windows_from_tasksmodel"]=true;
        checks["default_disabled_without_native_providers"]=!latest["enabled"].toBool() && !latest["contentLoaded"].toBool() && latest["providerCount"].toInt()==0;
        fixtureWindow->requestActivate();
        QTest::mouseMove(fixtureWindow,QPoint(90,60));
        invoke("showHints");stage=10;
    }else if(stage==10){
        if(!latest["tooltipVisible"].toBool()){QTimer::singleShot(100,tick);return;}
        const auto image=capture("NATIVE-HINTS.png");
        const auto windows=latest["windows"].toArray();
        checks["default_group_hint_lists_all_owned_titles_in_order"]=latest["hintMainText"].toString()=="Owned windows"
            && latest["hintSubText"].toString()=="1. "+windows[0].toObject()["title"].toString()+"\n2. "+windows[1].toObject()["title"].toString();
        checks["default_hint_does_not_create_native_capture_providers"]=!latest["enabled"].toBool() && latest["loadedProviderCount"].toInt()==0;
        checks["native_group_hint_capture_saved"]=!image.isNull();
        invoke("enablePreview");stage=1;
    }else if(stage==1){
        if(latest["availableCount"].toInt()!=2){QTimer::singleShot(100,tick);return;}
        checks["two_real_native_window_thumbnails_available"]=true;
        const auto image=capture("NATIVE-THUMBNAILS.png");
        checks["native_tooltip_capture_saved"]=!image.isNull();
        checks["native_pixels_match_both_owned_source_windows"]=colorPixels(image,QColor("#c83246"))>100 && colorPixels(image,QColor("#329650"))>100;
        owned.first()->setStyleSheet("background:#304ec0;color:white;");
        // QWidget postpones painting when completely covered. Expose only
        // this own source so the compositor gets a genuine damage event.
        owned.first()->raise();
        // Wayland does not guarantee QWidget::raise(). Request activation of
        // this owned source explicitly; no foreign window is an action target.
        if (owned.first()->windowHandle()) owned.first()->windowHandle()->requestActivate();
        QTest::qWait(200);
        owned.first()->repaint();QTest::qWait(150);
        checks["owned_source_widget_was_repainted_blue"]=colorPixels(owned.first()->grab().toImage(),QColor("#304ec0"))>100;
        fixtureWindow->raise();fixtureWindow->requestActivate();
        invoke("enablePreview");
        stage=2;QTimer::singleShot(2500,tick);return;
    }else if(stage==2){
        // Exposing the own source can deliver a delayed hover-leave event
        // after focus returns. Reopen and wait for the native tooltip instead
        // of interpreting an absent dialog as an unchanged source image.
        if(!latest["tooltipVisible"].toBool()){
            fixtureWindow->requestActivate();
            QTest::mouseMove(fixtureWindow,QPoint(90,60));
            invoke("enablePreview");QTimer::singleShot(300,tick);return;
        }
        if(latest["availableCount"].toInt()!=2){QTimer::singleShot(100,tick);return;}
        const auto image=capture("NATIVE-THUMBNAILS-UPDATED.png");
        checks["native_preview_updates_after_owned_window_repaint"]=colorPixels(image,QColor("#304ec0"))>100 && colorPixels(image,QColor("#c83246"))<100;
        invoke("hidePreview");stage=3;
    }else if(stage==3){
        // Keeping title/card layout prepared under the hovered task is fine;
        // no native WindowThumbnail or PipeWire source may survive hiding.
        checks["hiding_unloads_every_native_provider"]=!latest["tooltipVisible"].toBool() && latest["loadedProviderCount"].toInt()==0;
        invoke("enablePreview");stage=4;
    }else if(stage==4){
        if(latest["availableCount"].toInt()!=2){QTimer::singleShot(100,tick);return;}
        invoke("disablePreview");stage=5;
    }else if(stage==5){
        checks["disabling_unloads_every_native_provider"]=!latest["enabled"].toBool() && !latest["tooltipVisible"].toBool() && !latest["contentLoaded"].toBool() && latest["providerCount"].toInt()==0;
        invoke("disableHints");
        QTest::mouseMove(fixtureWindow,QPoint(300,180));QTest::mouseMove(fixtureWindow,QPoint(90,60));
        stage=11;QTimer::singleShot(1200,tick);return;
    }else if(stage==11){
        checks["none_mode_has_no_tooltip_or_capture_on_hover"]=!latest["hintsEnabled"].toBool() && !latest["enabled"].toBool()
            && !latest["tooltipVisible"].toBool() && latest["loadedProviderCount"].toInt()==0;
        checks["native_scenario_completed"]=true;finish();return;
    }
    QTimer::singleShot(100,tick);
}
static void start() {
    QApplication::instance()->setProperty("domainosThumbnailTest",true);
    for(int index=0;index<2;++index){
        auto window=new QLabel(QString("NATIVE SOURCE %1\nOWNED WINDOW").arg(index+1));
        window->setWindowTitle(QString("DomainOS thumbnail owned %1").arg(index));
        window->resize(320,210);window->move(40+index*360,50);
        window->setAlignment(Qt::AlignCenter);
        window->setStyleSheet(QString("background:%1;color:white;font:22px monospace;").arg(index==0?"#c83246":"#329650"));
        window->show();owned.append(window);
    }
    QTimer::singleShot(400,tick);
}
extern "C" int interceptedExec() asm("_ZN12QApplication4execEv");
extern "C" int interceptedExec(){
    const auto original=reinterpret_cast<int (*)()>(dlsym(RTLD_NEXT,"_ZN12QApplication4execEv"));
    if(!original)return 2;
    if(qEnvironmentVariable("IRIX_DOMAINOS_THUMBNAIL_PRIVATE")=="1")start();
    return original();
}
