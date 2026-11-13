// SPDX-FileCopyrightText: 2026 IRIX Classic contributors
// SPDX-License-Identifier: GPL-3.0-or-later
// Genuine private PulseAudio streams, owned native window and physical clicks.
#include <QApplication>
#include <QFile>
#include <QImage>
#include <QJsonArray>
#include <QJsonDocument>
#include <QJsonObject>
#include <QProcess>
#include <QTimer>
#include <QWidget>
#include <QWindow>
#include <dlfcn.h>
#include <pulse/pulseaudio.h>
#include <unistd.h>
#include <cmath>

using Children=QList<QObject *> (*)(QObject *);
using Grab=QImage (*)(QWindow *);
static QObject *fixture=nullptr;
static QWindow *window=nullptr;
static QWidget *owned=nullptr;
static pa_mainloop *audioLoop=nullptr;
static pa_context *audioContext=nullptr;
static pa_stream *streams[2]={nullptr,nullptr};
static QJsonObject checks,snapshots;
static int phase=0,attempts=0;
static bool streamsStarted=false;

static QObject *find(QObject *object,Children children) {
    if(!object)return nullptr;
    if(object->objectName()=="domainosAudioFixture")return object;
    if(object->inherits("QQuickItem"))for(auto child:children(object))if(auto result=find(child,children))return result;
    return nullptr;
}
static QVariant invoke(const char *method,const QVariant &argument=QVariant()) {
    QVariant result;
    if(argument.isValid())QMetaObject::invokeMethod(fixture,method,Qt::DirectConnection,Q_RETURN_ARG(QVariant,result),Q_ARG(QVariant,argument));
    else QMetaObject::invokeMethod(fixture,method,Qt::DirectConnection,Q_RETURN_ARG(QVariant,result));
    return result;
}
static QJsonObject state() {return QJsonDocument::fromJson(invoke("state").toString().toUtf8()).object();}
static QJsonArray inputs() {
    QProcess query;query.start("pactl",{"--format=json","list","sink-inputs"});query.waitForFinished(2000);
    return QJsonDocument::fromJson(query.readAllStandardOutput()).array();
}
static bool inputsMuted(const QJsonArray &values,bool desired) {
    if(values.size()!=2)return false;
    for(auto value:values)if(value.toObject()["mute"].toBool()!=desired)return false;
    return true;
}
static void capture(const QString &key) {
    const auto grab=reinterpret_cast<Grab>(dlsym(RTLD_DEFAULT,"_ZN12QQuickWindow10grabWindowEv"));
    checks[key+"_capture_saved"]=window && grab && grab(window).save(qEnvironmentVariable("IRIX_DOMAINOS_AUDIO_OUTPUT")+"/"+key+".png");
}
static void physicalAudioClick() {
    const auto position=QJsonDocument::fromJson(invoke("coordinates").toString().toUtf8()).object();
    const auto global=window->mapToGlobal(QPoint(qRound(position["x"].toDouble()),qRound(position["y"].toDouble())));
    auto process=new QProcess(QCoreApplication::instance());
    QObject::connect(process,qOverload<int,QProcess::ExitStatus>(&QProcess::finished),process,[process](int,QProcess::ExitStatus){process->deleteLater();});
    process->start("xdotool",{"mousemove",QString::number(global.x()),QString::number(global.y()),"click","1"});
}
static void writeAudio(pa_stream *stream,size_t requested,void *) {
    // Sound is sent solely to the runner's null sink, never hardware.
    static unsigned long sample=0;
    while(requested>0) {
        int16_t buffer[1024];const size_t bytes=std::min(requested,sizeof(buffer));
        for(size_t index=0;index<bytes/sizeof(int16_t);++index)
            buffer[index]=int16_t(256*std::sin((sample++)*2*3.141592653589793*220/48000));
        pa_stream_write(stream,buffer,bytes,nullptr,0,PA_SEEK_RELATIVE);requested-=bytes;
    }
}
static void pumpAudio() {
    if(!audioLoop)return;
    int result=0;pa_mainloop_iterate(audioLoop,0,&result);
    if(audioContext && pa_context_get_state(audioContext)==PA_CONTEXT_READY && !streamsStarted) {
        streamsStarted=true;
        const pa_sample_spec format={PA_SAMPLE_S16LE,48000,1};
        for(int index=0;index<2;++index) {
            streams[index]=pa_stream_new(audioContext,index ? "DomainOS owned stream B" : "DomainOS owned stream A",&format,nullptr);
            pa_stream_set_write_callback(streams[index],writeAudio,nullptr);
            pa_stream_connect_playback(streams[index],"domainos_private_null",nullptr,PA_STREAM_ADJUST_LATENCY,nullptr,nullptr);
        }
    }
}
static void cork(bool value) {
    for(auto stream:streams)if(stream && pa_stream_get_state(stream)==PA_STREAM_READY) {
        auto operation=pa_stream_cork(stream,value,nullptr,nullptr);if(operation)pa_operation_unref(operation);
    }
}
static void stopAudio() {
    for(auto &stream:streams)if(stream){pa_stream_disconnect(stream);pa_stream_unref(stream);stream=nullptr;}
}
static void complete() {
    QJsonObject report{{"checks",checks},{"snapshots",snapshots},{"state",fixture ? state() : QJsonObject()},
        {"owned_pid",getpid()},{"private_server",qEnvironmentVariable("PULSE_SERVER")},
        {"real_streams_created",streamsStarted}};
    QFile file(qEnvironmentVariable("IRIX_DOMAINOS_AUDIO_OUTPUT")+"/state.json");
    if(file.open(QIODevice::WriteOnly))file.write(QJsonDocument(report).toJson());
    stopAudio();if(audioContext){pa_context_disconnect(audioContext);pa_context_unref(audioContext);audioContext=nullptr;}
    if(audioLoop){pa_mainloop_free(audioLoop);audioLoop=nullptr;}
    if(owned)owned->close();QCoreApplication::quit();
}
static void tick() {
    if(++attempts>100){checks["native_audio_scenario_completed"]=false;complete();return;}
    if(!fixture) {
        const auto children=reinterpret_cast<Children>(dlsym(RTLD_DEFAULT,"_ZNK10QQuickItem10childItemsEv"));
        for(auto candidate:QGuiApplication::allWindows())if(children && (fixture=find(candidate->property("contentItem").value<QObject *>(),children))){window=candidate;break;}
        if(!fixture){QTimer::singleShot(100,tick);return;}
        window->setFlags(Qt::Tool|Qt::FramelessWindowHint);window->setGeometry(200,450,594,150);window->show();
    }
    const auto current=state();
    if(phase==0) {
        if(current["streams"].toInt()!=2 || current["windows"].toArray().size()!=1 || current["rows"].toArray().size()!=1){QTimer::singleShot(100,tick);return;}
        const auto actual=inputs();snapshots["playing"]=QJsonObject{{"qml",current},{"sink_inputs",actual}};
        checks["native_single_owned_window"]=current["windows"].toArray().size()==1 && current["windows"].toArray()[0].toObject()["pid"].toInt()==getpid();
        checks["production_native_audio_provider_loaded"]=current["providerLoaded"].toBool();
        checks["native_two_playing_streams_in_button"]=current["streams"].toInt()==2 && current["playing"].toBool() && current["badgeVisible"].toBool() && !current["muted"].toBool();
        bool ownedInputs=actual.size()==2;
        for(auto value:actual)ownedInputs &= value.toObject()["properties"].toObject()["application.process.id"].toString()==QString::number(getpid());
        checks["two_genuine_sink_inputs_match_owned_pid"]=ownedInputs;
        checks["actual_inputs_initially_unmuted"]=inputsMuted(actual,false);
        capture("AUDIO-PLAYING");physicalAudioClick();phase=1;
    } else if(phase==1) {
        const auto actual=inputs();snapshots["muted"]=QJsonObject{{"qml",current},{"sink_inputs",actual}};
        checks["physical_badge_click_mutes_both_real_streams"]=inputsMuted(actual,true);
        checks["native_button_observes_muted_streams"]=current["muted"].toBool() && current["badgeVisible"].toBool();
        checks["audio_click_does_not_select_or_activate_task"]=current["selected"].toArray().isEmpty() && current["requests"].toArray().isEmpty() && !current["popup"].toBool();
        capture("AUDIO-MUTED");physicalAudioClick();phase=2;
    } else if(phase==2) {
        const auto actual=inputs();snapshots["unmuted"]=QJsonObject{{"qml",current},{"sink_inputs",actual}};
        checks["physical_badge_click_unmutes_both_real_streams"]=inputsMuted(actual,false);
        checks["native_button_observes_unmuted_streams"]=!current["muted"].toBool() && current["playing"].toBool();
        invoke("action","disableMute");phase=3;
    } else if(phase==3) {
        checks["interactive_mute_preference_reaches_native_button"]=!current["interactiveMute"].toBool();
        physicalAudioClick();phase=4;
    } else if(phase==4) {
        checks["disabled_interactive_mute_preserves_real_streams"]=inputsMuted(inputs(),false);
        invoke("action","enableMute");invoke("action","closePicker");cork(true);phase=5;
    } else if(phase==5) {
        snapshots["corked"]=QJsonObject{{"qml",current},{"sink_inputs",inputs()}};
        checks["native_corked_streams_hide_audio_badge"]=current["streams"].toInt()==2 && !current["playing"].toBool() && !current["badgeVisible"].toBool();
        cork(false);phase=6;
    } else if(phase==6) {
        checks["native_resume_restores_audio_badge"]=current["streams"].toInt()==2 && current["playing"].toBool() && current["badgeVisible"].toBool();
        stopAudio();phase=7;
    } else if(phase==7) {
        if(current["streams"].toInt()!=0){QTimer::singleShot(100,tick);return;}
        snapshots["stopped"]=QJsonObject{{"qml",current},{"sink_inputs",inputs()}};
        checks["native_removed_streams_clear_audio_badge"]=!current["playing"].toBool() && !current["muted"].toBool() && !current["badgeVisible"].toBool();
        checks["genuine_streams_removed_from_private_server"]=inputs().isEmpty();
        checks["native_audio_scenario_completed"]=true;complete();return;
    }
    QTimer::singleShot(550,tick);
}
extern "C" int interceptedExec() asm("_ZN12QApplication4execEv");
extern "C" int interceptedExec() {
    auto original=reinterpret_cast<int (*)()>(dlsym(RTLD_NEXT,"_ZN12QApplication4execEv"));
    if(!original || qEnvironmentVariable("IRIX_DOMAINOS_AUDIO_PRIVATE")!="1")return 2;
    owned=new QWidget;owned->setWindowTitle("DomainOS owned audio window");owned->resize(300,180);owned->move(80,100);owned->show();
    audioLoop=pa_mainloop_new();auto properties=pa_proplist_new();
    pa_proplist_sets(properties,PA_PROP_APPLICATION_NAME,"DomainOS private audio proof");
    pa_proplist_sets(properties,PA_PROP_APPLICATION_ID,"org.irixclassic.domainos.audio.test");
    const auto pid=QString::number(getpid()).toUtf8();pa_proplist_sets(properties,PA_PROP_APPLICATION_PROCESS_ID,pid.constData());
    audioContext=pa_context_new_with_proplist(pa_mainloop_get_api(audioLoop),"DomainOS private audio proof",properties);pa_proplist_free(properties);
    pa_context_connect(audioContext,qEnvironmentVariable("PULSE_SERVER").toUtf8().constData(),PA_CONTEXT_NOAUTOSPAWN,nullptr);
    auto timer=new QTimer(QCoreApplication::instance());QObject::connect(timer,&QTimer::timeout,pumpAudio);timer->start(10);
    QTimer::singleShot(1200,tick);return original();
}
