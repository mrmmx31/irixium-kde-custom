// SPDX-FileCopyrightText: 2026 mrmmx31
// SPDX-License-Identifier: GPL-3.0-or-later
// Directed public-holiday test in a disposable production Plasma host.
#include <QApplication>
#include <QAbstractItemModel>
#include <QDateTime>
#include <QFile>
#include <QImage>
#include <QJsonArray>
#include <QJsonDocument>
#include <QJsonObject>
#include <QMetaProperty>
#include <QSignalSpy>
#include <QSet>
#include <QTest>
#include <QTimer>
#include <QTimeZone>
#include <QWindow>
#include <dlfcn.h>

using Children=QList<QObject *> (*)(QObject *);
using Grab=QImage (*)(QWindow *);
using ItemWindow=QWindow *(*)(const QObject *);
using Map=QPointF (*)(const QObject *,const QPointF &);
static QObject *panel=nullptr,*instruments=nullptr,*settings=nullptr,*providers=nullptr,*month=nullptr,*days=nullptr,*agenda=nullptr,*events=nullptr;
static QWindow *host=nullptr;
static QSignalSpy *agendaSpy=nullptr;
static QJsonObject report,checks;
static int phase=0,retries=0;
static QString holidayPlugin;
static const QDate holidayDate=[] {
    const auto value=QDate::fromString(qEnvironmentVariable("IRIX_DOMAINOS_AGENDA_PUBLIC_DATE"),Qt::ISODate);
    return value.isValid()?value:QDate(2027,1,1);
}();
static const QDate absentDate=QDate::fromString(qEnvironmentVariable("IRIX_DOMAINOS_AGENDA_ABSENT_DATE"),Qt::ISODate);
static const QJsonArray regionalProbes=QJsonDocument::fromJson(qgetenv("IRIX_DOMAINOS_AGENDA_REGIONAL_PROBES")).array();
static const bool inspectIdentity=qEnvironmentVariable("IRIX_DOMAINOS_AGENDA_INSPECT_IDENTITY")=="1";
static int regionalProbeIndex=0;
static QObject *variantObject(const QVariant &value);
static QObject *findObserved(QObject *object,const QString &name,QSet<QObject *> &seen) {
    if(!object || seen.contains(object))return nullptr;seen.insert(object);
    if(object->objectName()==name)return object;
    const auto children=reinterpret_cast<Children>(dlsym(RTLD_DEFAULT,"_ZNK10QQuickItem10childItemsEv"));
    if(children && object->inherits("QQuickItem"))for(auto child:children(object))if(auto match=findObserved(child,name,seen))return match;
    for(auto child:object->children())if(!child->inherits("QQuickItem"))if(auto match=findObserved(child,name,seen))return match;
    if(!object->inherits("QQuickItem"))for(const auto property:{"mainItem","contentItem"}) {
        auto item=variantObject(object->property(property));
        if(item && item!=object)if(auto match=findObserved(item,name,seen))return match;
    }
    return nullptr;
}
static QObject *find(QObject *object,const QString &name) { QSet<QObject *> seen;return findObserved(object,name,seen); }
static QObject *findClass(QObject *object,const QByteArray &name) {
    if(!object)return nullptr;if(object->metaObject()->className()==name)return object;
    for(auto child:object->children())if(auto match=findClass(child,name))return match;
    return nullptr;
}
static QObject *variantObject(const QVariant &value) {
    if(auto object=value.value<QObject *>())return object;
    if(QByteArray(value.metaType().name())=="QJSValue") {
        using Convert=QObject *(*)(const void *);
        const auto convert=reinterpret_cast<Convert>(dlsym(RTLD_DEFAULT,"_ZNK8QJSValue9toQObjectEv"));
        if(convert)return convert(value.constData());
    }
    return nullptr;
}
static QVariant gadgetProperty(const QVariant &value,const char *name) {
    const auto meta=value.metaType().metaObject();if(!meta)return {};
    const int index=meta->indexOfProperty(name);if(index<0)return {};
    if(auto object=value.value<QObject *>())return meta->property(index).read(object);
    return meta->property(index).readOnGadget(value.constData());
}
static QJsonArray nativeEvents(const QDate &date=holidayDate) {
    QVariantList values;
    report["events_for_date_invoked"]=QMetaObject::invokeMethod(days,"eventsForDate",Qt::DirectConnection,
        Q_RETURN_ARG(QVariantList,values),Q_ARG(QDate,date));
    QJsonArray result;
    for(const auto &value:values) {
        if(inspectIdentity&&!report.contains("native_event_property_names")) {
            QJsonArray names;
            if(const auto meta=value.metaType().metaObject())for(int i=0;i<meta->propertyCount();++i)names.append(QString::fromLatin1(meta->property(i).name()));
            report["native_event_property_names"]=names;
            report["native_uid_exposed_by_decorator"]=names.contains("uid");
        }
        result.append(QJsonObject{
        {"uid",gadgetProperty(value,"uid").toString()},
        {"title",gadgetProperty(value,"title").toString()},
        {"start",gadgetProperty(value,"startDateTime").toDateTime().toString(Qt::ISODate)},
        {"end",gadgetProperty(value,"endDateTime").toDateTime().toString(Qt::ISODate)},
        {"all_day",gadgetProperty(value,"isAllDay").toBool()},
        {"type",QString::fromLatin1(value.metaType().name())}});
    }
    return result;
}
static QJsonArray labels(QObject *object) {
    QJsonArray result;if(!object)return result;
    const auto text=object->property("text");if(text.isValid())result.append(text.toString());
    const auto children=reinterpret_cast<Children>(dlsym(RTLD_DEFAULT,"_ZNK10QQuickItem10childItemsEv"));
    if(children && object->inherits("QQuickItem"))for(auto child:children(object))for(auto label:labels(child))result.append(label);
    return result;
}
static bool selectRegionalProbe() {
    const auto date=QDate::fromString(regionalProbes[regionalProbeIndex].toObject()["date"].toString(),Qt::ISODate);
    auto backend=findClass(month,"Calendar");
    if(!date.isValid()||!backend)return false;
    const bool navigated=QMetaObject::invokeMethod(backend,"goToYearAndMonth",Q_ARG(int,date.year()),Q_ARG(int,date.month()));
    return navigated&&month->setProperty("currentDate",QDateTime(date,QTime(0,0),QTimeZone::UTC));
}
static bool clickDate() {
    auto button=find(panel,"domainosDate");
    const auto map=reinterpret_cast<Map>(dlsym(RTLD_DEFAULT,"_ZNK10QQuickItem10mapToSceneERK7QPointF"));
    if(!button || !map)return false;
    const auto point=map(button,QPointF(button->property("width").toDouble()/2,button->property("height").toDouble()/2));
    QTest::mouseMove(host,point.toPoint());QTest::mouseClick(host,Qt::LeftButton,Qt::NoModifier,point.toPoint());return true;
}
static void finish(const QString &error={}) {
    if(!error.isEmpty())report["failure"]=error;
    report["checks"]=checks;report["qt_version"]=qVersion();report["host_pid"]=int(QCoreApplication::applicationPid());
    QJsonObject names;for(const auto key:{"HOME","XDG_CONFIG_HOME","XDG_DATA_HOME","DISPLAY","DBUS_SESSION_BUS_ADDRESS"})names[key]=qEnvironmentVariable(key);
    report["private_namespace"]=names;
    QFile output(qEnvironmentVariable("IRIX_DOMAINOS_AGENDA_REPORT"));if(output.open(QIODevice::WriteOnly))output.write(QJsonDocument(report).toJson());
    QCoreApplication::quit();
}
static void step() {
    if(++retries>100){finish("Bounded native holiday observation timeout");return;}
    if(!panel) {
        for(auto window:QGuiApplication::allWindows())if(auto candidate=find(window->property("contentItem").value<QObject *>(),"domainosPanel")){host=window;panel=candidate;break;}
        if(!panel){QTimer::singleShot(100,step);return;}
        host->setGeometry(80,570,971,109);host->show();
        instruments=find(panel,"domainosLiveInstruments");settings=variantObject(panel->property("settings"));
        if(!instruments || !settings){finish("Production instruments/KConfig map absent");return;}
        providers=find(instruments,"domainosCalendarProviders");month=find(instruments,"domainosMonthView");
        agenda=find(instruments,"domainosAgenda");events=find(instruments,"domainosAgendaEvents");
        if(!providers || !month || !agenda || !events){
            report["calendar_object_observation"]=QJsonObject{{"providers",providers!=nullptr},{"month",month!=nullptr},{"agenda",agenda!=nullptr},{"events",events!=nullptr}};
            finish("Production calendar objects absent");return;}
        days=variantObject(month->property("daysModel"));if(!days){finish("Native DaysModel absent");return;}
        agendaSpy=new QSignalSpy(days,SIGNAL(agendaUpdated(QDate)));
        checks["exact_production_composition_and_kconfig_loaded"]=panel->property("phase").toString()=="functional-integration";
        checks["calendar_defaults_empty_in_own_instance"]=settings->property("calendarPlugins").toStringList().isEmpty();
        checks["no_provider_activated_on_startup"]=providers->property("enabledPlugins").toStringList().isEmpty();
        checks["agenda_initially_not_configured"]=!instruments->property("agendaConfigured").toBool();
        checks["native_agenda_updated_observer_attached"]=agendaSpy->isValid();
        auto model=qobject_cast<QAbstractItemModel *>(variantObject(providers->property("model")));
        if(!model){finish("Native provider metadata model absent");return;}
        const auto roles=model->roleNames();int idRole=-1;
        for(auto it=roles.begin();it!=roles.end();++it)if(it.value()=="pluginId")idRole=it.key();
        QJsonArray metadata;
        for(int row=0;row<model->rowCount();++row){const auto id=model->data(model->index(row,0),idRole).toString();metadata.append(id);if(id.contains("holiday",Qt::CaseInsensitive))holidayPlugin=id;}
        report["installed_provider_ids"]=metadata;report["selected_plugin"]=holidayPlugin;
        report["public_region"]=qEnvironmentVariable("IRIX_DOMAINOS_AGENDA_PUBLIC_REGION","us_en-us");report["selected_date"]=holidayDate.toString(Qt::ISODate);
        if(holidayPlugin.isEmpty()){finish("Installed public-holiday plugin was not enumerated");return;}
        checks["unconfigured_calendar_opened_by_actual_date_button"]=clickDate();
        phase=10;retries=0;QTimer::singleShot(200,step);return;
    }
    if(phase==10) {
        if(!instruments->property("calendarPopupVisible").toBool()){QTimer::singleShot(100,step);return;}
        auto label=find(instruments,"domainosCalendarNoSource");
        const auto map=reinterpret_cast<Map>(dlsym(RTLD_DEFAULT,"_ZNK10QQuickItem10mapToSceneERK7QPointF"));
        checks["missing_calendar_source_is_explained"]=label&&label->property("visible").toBool()&&!label->property("text").toString().isEmpty();
        checks["empty_calendar_does_not_activate_a_provider"]=providers->property("enabledPlugins").toStringList().isEmpty();
        if(label&&map) {
            const auto labelTop=map(label,QPointF());const auto monthTop=map(month,QPointF());
            checks["no_source_explanation_does_not_cover_month_view"]=labelTop.y()+label->property("height").toDouble()<=monthTop.y()+1
                &&month->property("height").toDouble()>150;
        } else checks["no_source_explanation_does_not_cover_month_view"]=false;
        const auto grab=reinterpret_cast<Grab>(dlsym(RTLD_DEFAULT,"_ZN12QQuickWindow10grabWindowEv"));
        const auto itemWindow=reinterpret_cast<ItemWindow>(dlsym(RTLD_DEFAULT,"_ZNK10QQuickItem6windowEv"));
        auto calendarWindow=itemWindow?itemWindow(month):nullptr;
        checks["unconfigured_native_calendar_capture_saved"]=calendarWindow&&grab
            &&grab(calendarWindow).save(qEnvironmentVariable("IRIX_DOMAINOS_AGENDA_DIR")+"/CALENDARIO-SEM-FONTE-NATIVO.png");
        checks["unconfigured_calendar_closed_by_actual_date_button"]=clickDate();
        checks["only_public_holiday_provider_explicitly_selected"]=settings->setProperty("calendarPlugins",QStringList{holidayPlugin});
        checks["own_kconfig_write_requested"]=QMetaObject::invokeMethod(settings,"writeConfig");
        phase=1;retries=0;QTimer::singleShot(200,step);return;
    }
    if(phase==1) {
        checks["calendar_kconfig_reaches_production_instruments"]=instruments->property("agendaConfigured").toBool();
        checks["closed_calendar_does_not_load_configured_provider"]=providers->property("enabledPlugins").toStringList().isEmpty();
        checks["real_date_button_opens_calendar"]=clickDate();phase=2;retries=0;QTimer::singleShot(200,step);return;
    }
    if(phase==2) {
        if(!instruments->property("calendarPopupVisible").toBool()){QTimer::singleShot(100,step);return;}
        checks["opened_calendar_enables_only_selected_native_provider"]=providers->property("enabledPlugins").toStringList()==QStringList{holidayPlugin};
        auto backend=findClass(month,"Calendar");if(!backend){finish("Native Calendar backend absent");return;}
        checks["native_calendar_navigated_to_public_holiday_month"]=QMetaObject::invokeMethod(backend,"goToYearAndMonth",Q_ARG(int,holidayDate.year()),Q_ARG(int,holidayDate.month()));
        checks["native_selected_date_updated"]=month->setProperty("currentDate",QDateTime(holidayDate,QTime(0,0),QTimeZone::UTC));
        phase=3;retries=0;QTimer::singleShot(150,step);return;
    }
    if(phase==3) {
        const auto supplied=nativeEvents();const auto shown=labels(events);
        report["native_events"]=supplied;report["agenda_delegate_texts"]=shown;
        if(supplied.isEmpty() || events->property("count").toInt()==0 || shown.isEmpty()){QTimer::singleShot(150,step);return;}
        checks["native_daysmodel_supplies_public_holiday"]=!supplied.isEmpty() && supplied[0].toObject()["all_day"].toBool()
            && supplied[0].toObject()["start"].toString().startsWith(holidayDate.toString(Qt::ISODate));
        checks["native_agenda_updated_observed"]=agendaSpy->count()>0;report["native_agenda_updated_signals"]=agendaSpy->count();
        bool titleShown=false;for(auto event:supplied)for(auto label:shown)if(label.toString()==event.toObject()["title"].toString() && !label.toString().isEmpty())titleShown=true;
        checks["real_agenda_delegate_displays_native_event_title"]=titleShown;
        checks["agenda_count_matches_native_supplied_events"]=events->property("count").toInt()==supplied.size();
        if(inspectIdentity)checks["native_and_visible_agenda_exactly_one_"+holidayDate.toString(Qt::ISODate)]=supplied.size()==1&&events->property("count").toInt()==1;
        checks["configured_agenda_visible"]=agenda->property("visible").toBool();
        const auto grab=reinterpret_cast<Grab>(dlsym(RTLD_DEFAULT,"_ZN12QQuickWindow10grabWindowEv"));
        const auto itemWindow=reinterpret_cast<ItemWindow>(dlsym(RTLD_DEFAULT,"_ZNK10QQuickItem6windowEv"));
        auto calendarWindow=itemWindow ? itemWindow(month) : nullptr;
        bool captured=calendarWindow && calendarWindow!=host && calendarWindow->isVisible() && grab
            && grab(calendarWindow).save(qEnvironmentVariable("IRIX_DOMAINOS_AGENDA_DIR")+"/AGENDA-FERIADO-NATIVO.png");
        report["calendar_window_geometry"]=calendarWindow ? QJsonObject{{"width",calendarWindow->width()},{"height",calendarWindow->height()},{"separate_from_panel",calendarWindow!=host}} : QJsonObject{};
        checks["native_calendar_and_agenda_capture_saved"]=captured;
        if(!regionalProbes.isEmpty()) {
            checks["regional_probe_first_date_selected"]=selectRegionalProbe();
            phase=7;retries=0;QTimer::singleShot(250,step);return;
        }
        if(absentDate.isValid()) {
            report["negative_coverage_date"]=absentDate.toString(Qt::ISODate);
            checks["native_negative_coverage_date_selected"]=month->setProperty("currentDate",QDateTime(absentDate,QTime(0,0),QTimeZone::UTC));
            phase=6;retries=0;QTimer::singleShot(150,step);return;
        }
        checks["calendar_closed_by_actual_date_button"]=clickDate();phase=4;retries=0;QTimer::singleShot(150,step);return;
    }
    if(phase==6) {
        const auto supplied=nativeEvents(absentDate);const auto shown=labels(events);
        report["negative_native_events"]=supplied;report["negative_agenda_delegate_texts"]=shown;
        const bool selected=month->property("currentDate").toDateTime().date()==absentDate;
        if(!selected || events->property("count").toInt()!=0 || !shown.isEmpty()){QTimer::singleShot(150,step);return;}
        checks["installed_region_has_no_local_event_on_negative_date"]=selected&&supplied.isEmpty();
        checks["negative_date_shows_no_fabricated_agenda_delegate"]=events->property("count").toInt()==0&&shown.isEmpty();
        checks["only_national_native_provider_still_selected"]=providers->property("enabledPlugins").toStringList()==QStringList{holidayPlugin};
        const auto grab=reinterpret_cast<Grab>(dlsym(RTLD_DEFAULT,"_ZN12QQuickWindow10grabWindowEv"));
        const auto itemWindow=reinterpret_cast<ItemWindow>(dlsym(RTLD_DEFAULT,"_ZNK10QQuickItem6windowEv"));
        auto calendarWindow=itemWindow?itemWindow(month):nullptr;
        checks["negative_coverage_native_capture_saved"]=calendarWindow&&grab
            &&grab(calendarWindow).save(qEnvironmentVariable("IRIX_DOMAINOS_AGENDA_DIR")+"/AGENDA-SEM-COBERTURA-LOCAL-NATIVO.png");
        checks["calendar_closed_by_actual_date_button"]=clickDate();phase=4;retries=0;QTimer::singleShot(150,step);return;
    }
    if(phase==7) {
        const auto probe=regionalProbes[regionalProbeIndex].toObject();
        const auto date=QDate::fromString(probe["date"].toString(),Qt::ISODate);
        const bool expected=probe["event"].toBool();
        const auto supplied=nativeEvents(date);const auto shown=labels(events);
        const bool selected=month->property("currentDate").toDateTime().date()==date;
        if(!selected||(expected&&(supplied.isEmpty()||events->property("count").toInt()==0||shown.isEmpty()))
           ||(!expected&&(events->property("count").toInt()!=0||!shown.isEmpty()))) {
            QTimer::singleShot(150,step);return;
        }
        const QString key=date.toString(Qt::ISODate);
        bool titleShown=false;for(auto event:supplied)for(auto label:shown)
            if(label.toString()==event.toObject()["title"].toString()&&!label.toString().isEmpty())titleShown=true;
        const bool correct=selected&&(expected?!supplied.isEmpty()&&titleShown:supplied.isEmpty()&&shown.isEmpty());
        checks["native_regional_date_"+key]=correct;
        checks["agenda_matches_regional_date_"+key]=events->property("count").toInt()==supplied.size();
        if(inspectIdentity&&expected)checks["native_and_visible_agenda_exactly_one_"+key]=supplied.size()==1&&events->property("count").toInt()==1;
        auto observations=report["regional_observations"].toArray();
        observations.append(QJsonObject{{"date",key},{"expected_event",expected},{"native_events",supplied},
            {"agenda_delegate_texts",shown},{"agenda_count",events->property("count").toInt()}});
        report["regional_observations"]=observations;
        if(key=="2026-10-24") {
            const auto grab=reinterpret_cast<Grab>(dlsym(RTLD_DEFAULT,"_ZN12QQuickWindow10grabWindowEv"));
            const auto itemWindow=reinterpret_cast<ItemWindow>(dlsym(RTLD_DEFAULT,"_ZNK10QQuickItem6windowEv"));
            auto calendarWindow=itemWindow?itemWindow(month):nullptr;
            checks["manaus_holiday_native_capture_saved"]=calendarWindow&&grab
                &&grab(calendarWindow).save(qEnvironmentVariable("IRIX_DOMAINOS_AGENDA_DIR")+"/AGENDA-MANAUS-2026-NATIVO.png");
        }
        if(inspectIdentity&&(key=="2026-10-12"||key=="2026-12-08"||key=="2026-12-25")) {
            const auto grab=reinterpret_cast<Grab>(dlsym(RTLD_DEFAULT,"_ZN12QQuickWindow10grabWindowEv"));
            const auto itemWindow=reinterpret_cast<ItemWindow>(dlsym(RTLD_DEFAULT,"_ZNK10QQuickItem6windowEv"));
            auto calendarWindow=itemWindow?itemWindow(month):nullptr;
            checks["native_identity_capture_"+key]=calendarWindow&&grab
                &&grab(calendarWindow).save(qEnvironmentVariable("IRIX_DOMAINOS_AGENDA_DIR")+"/AGENDA-IDENTIDADE-"+key+".png");
        }
        if(++regionalProbeIndex<regionalProbes.size()) {
            checks["regional_probe_selected_"+QString::number(regionalProbeIndex)]=selectRegionalProbe();
            retries=0;QTimer::singleShot(250,step);return;
        }
        checks["calendar_closed_by_actual_date_button"]=clickDate();phase=4;retries=0;QTimer::singleShot(150,step);return;
    }
    if(phase==4) {
        checks["closing_calendar_unloads_provider"]=!instruments->property("calendarPopupVisible").toBool() && providers->property("enabledPlugins").toStringList().isEmpty();
        checks["own_calendar_preferences_restored_empty"]=settings->setProperty("calendarPlugins",QStringList{}) && QMetaObject::invokeMethod(settings,"writeConfig");
        phase=5;QTimer::singleShot(100,step);return;
    }
    checks["agenda_unconfigured_after_explicit_removal"]=!instruments->property("agendaConfigured").toBool()
        && settings->property("calendarPlugins").toStringList().isEmpty() && providers->property("enabledPlugins").toStringList().isEmpty();
    checks["mail_state_not_invented_by_calendar"]=!instruments->property("mailStateAvailable").toBool();finish();
}
extern "C" int interceptedExec() asm("_ZN12QApplication4execEv");
extern "C" int interceptedExec() {
    auto original=reinterpret_cast<int (*)()>(dlsym(RTLD_NEXT,"_ZN12QApplication4execEv"));
    if(!original)return 2;QTimer::singleShot(1800,step);QTimer::singleShot(50000,[]{finish("Bounded agenda test deadline");});return original();
}
