// SPDX-FileCopyrightText: 2026 mrmmx31
// SPDX-License-Identifier: GPL-3.0-or-later
// Directed input on exact production pages, in a disposable Plasma/KConfig host.
#include <QApplication>
#include <QAbstractItemModel>
#include <QFile>
#include <QImage>
#include <QJsonArray>
#include <QJsonDocument>
#include <QJsonObject>
#include <QPointer>
#include <QSet>
#include <QTest>
#include <QTimer>
#include <QWindow>
#include <dlfcn.h>

using Children=QList<QObject *> (*)(QObject *);
using Map=QPointF (*)(const QObject *,const QPointF &);
static QPointer<QObject> fixture;
static QPointer<QWindow> window;
static QJsonObject report,checks;
static int phase=0,tries=0;
static const QString beta="domainos-qa-beta.desktop";
static bool countsOnly() {return qEnvironmentVariable("IRIX_DOMAINOS_PREFS_SCENARIO")=="counts";}
static QObject *object(const QVariant &value) {
    if(auto result=value.value<QObject *>())return result;
    if(QByteArray(value.metaType().name())=="QJSValue") {
        const auto convert=reinterpret_cast<QObject *(*)(const void *)>(dlsym(RTLD_DEFAULT,"_ZNK8QJSValue9toQObjectEv"));
        if(convert)return convert(value.constData());
    }
    return nullptr;
}
static QObject *find(QObject *root,const QString &name,QSet<QObject *> &seen) {
    if(!root||seen.contains(root))return nullptr;seen.insert(root);
    if(root->objectName()==name)return root;
    const auto children=reinterpret_cast<Children>(dlsym(RTLD_DEFAULT,"_ZNK10QQuickItem10childItemsEv"));
    if(children&&root->inherits("QQuickItem"))for(auto child:children(root))if(auto result=find(child,name,seen))return result;
    for(auto child:root->children())if(!child->inherits("QQuickItem"))if(auto result=find(child,name,seen))return result;
    return nullptr;
}
static QObject *find(const QString &name) {QSet<QObject *> seen;return fixture?find(fixture,name,seen):nullptr;}
static QObject *page() {return fixture?object(fixture->property("page")):nullptr;}
static QJsonObject saved() {return fixture?QJsonDocument::fromJson(fixture->property("savedJson").toString().toUtf8()).object():QJsonObject{};}
static bool show(const QString &name) {return fixture&&QMetaObject::invokeMethod(fixture,"showPage",Q_ARG(QVariant,name));}
static bool click(QObject *target) {
    QPointer<QObject> guard(target);
    const auto map=reinterpret_cast<Map>(dlsym(RTLD_DEFAULT,"_ZNK10QQuickItem10mapToSceneERK7QPointF"));
    if(!guard||!window||!map||!target->property("enabled").toBool()||!target->property("visible").toBool())return false;
    const auto point=map(target,QPointF(target->property("width").toDouble()/2,target->property("height").toDouble()/2));
    if(!QRectF(QPointF(),window->size()).contains(point))return false;
    window->requestActivate();QTest::mouseMove(window,point.toPoint());
    if(!guard||!window)return false;
    QTest::mouseClick(window,Qt::LeftButton,Qt::NoModifier,point.toPoint());return true;
}
static bool choose(const QString &name,int index) {
    QPointer<QObject> combo=find(name);if(!combo||!click(combo))return false;
    auto popup=object(combo->property("popup"));
    auto popupItem=popup?object(popup->property("contentItem")):nullptr;
    const auto itemWindow=reinterpret_cast<QWindow *(*)(const QObject *)>(dlsym(RTLD_DEFAULT,"_ZNK10QQuickItem6windowEv"));
    QPointer<QWindow> owner=popupItem&&itemWindow?itemWindow(popupItem):window.data();
    if(!owner)return false;
    QTest::keyClick(owner,Qt::Key_Home);
    for(int i=0;i<index&&owner;i++)QTest::keyClick(owner,Qt::Key_Down);
    if(!owner||!combo)return false;
    QTest::keyClick(owner,Qt::Key_Return);return bool(combo);
}
static int mailIndex(const QString &id) {
    // Fixture serializes only public application IDs/names, without accounts.
    const auto clients=QJsonDocument::fromJson(fixture->property("mailChoicesJson").toString().toUtf8()).array();
    for(int i=0;i<clients.size();i++)if(clients[i].toObject()["id"].toString()==id)return i;
    return -1;
}
static bool categories() {
    const auto configModel=reinterpret_cast<QObject *(*)(QObject *)>(dlsym(RTLD_DEFAULT,"_ZNK11PlasmaQuick10ConfigView11configModelEv"));
    QPointer<QWindow> configWindow;
    for(auto owner:QGuiApplication::allWindows())if(owner->inherits("PlasmaQuick::ConfigView")&&owner->isVisible()){configWindow=owner;break;}
    auto model=configWindow&&configModel?qobject_cast<QAbstractItemModel *>(configModel(configWindow)):nullptr;
    if(!model)return false;
    checks["native_configuration_category_model_loaded"]=true;
    const auto roles=model->roleNames();int sourceRole=-1,visibleRole=-1;
    for(auto it=roles.begin();it!=roles.end();++it){if(it.value()=="source")sourceRole=it.key();if(it.value()=="visible")visibleRole=it.key();}
    QJsonArray values;bool holidays=false,pimHidden=false;
    for(int row=0;row<model->rowCount();row++) {
        const auto source=model->data(model->index(row,0),sourceRole).toString();
        const bool visible=model->data(model->index(row,0),visibleRole).toBool();
        values.append(QJsonObject{{"source",source},{"visible",visible}});
        if(source.endsWith("HolidaysConfig.qml"))holidays=visible;
        if(source.endsWith("PimEventsConfig.qml"))pimHidden=!visible;
    }
    report["native_category_sources"]=values;
    checks["selected_holidays_native_configuration_page_visible"]=holidays;
    checks["unselected_pim_configuration_page_hidden"]=pimHidden;
    configWindow->close();return true;
}
static void finish(const QString &failure={}) {
    if(!failure.isEmpty())report["failure"]=failure;
    report["checks"]=checks;report["saved"]=saved();report["host_pid"]=int(QCoreApplication::applicationPid());
    report["input"]=QStringLiteral("QTest QWindow events on native X11 windows; exact production onActivated/onToggled. Apply/Discard are fixture buttons mapping cfg_* to native Plasma KConfig, not the stock AppletConfiguration dialog.");
    QFile file(qEnvironmentVariable("IRIX_DOMAINOS_PREFS_REPORT"));if(file.open(QIODevice::WriteOnly))file.write(QJsonDocument(report).toJson());
    QCoreApplication::quit();
}
static void step() {
    if(++tries>80){finish("Bounded preference observation timeout at phase "+QString::number(phase));return;}
    if(!fixture) {
        for(auto owner:QGuiApplication::allWindows()){QSet<QObject *> seen;if(auto found=find(object(owner->property("contentItem")),"domainosCalendarMailPreferenceFixture",seen)){fixture=found;window=owner;break;}}
        if(!fixture){QTimer::singleShot(100,step);return;}
        window->setGeometry(20,20,860,1100);window->show();
        if(qEnvironmentVariable("IRIX_DOMAINOS_PREFS_MODE")=="reload") {
            if(countsOnly()) {
                checks["mail_count_preference_persisted_after_restart"]=saved()["mailCountsEnabled"].toBool();
                checks["counter_option_did_not_select_calendar_or_mail_application"]=saved()["mailClient"].toString().isEmpty()&&saved()["calendarPlugins"].toArray().isEmpty();
                finish();return;
            }
            const auto values=saved();checks["mail_client_persisted_after_restart"]=values["mailClient"].toString()==beta;
            checks["calendar_provider_persisted_after_restart"]=values["calendarPlugins"].toArray()==QJsonArray{"holidaysevents"};
            checks["thumbnail_mode_persisted_after_restart"]=values["iconboxWindowThumbnails"].toBool()&&!values["iconboxHintsEnabled"].toBool();
            finish();return;
        }
        checks["native_instance_starts_with_empty_calendar_and_client"]=saved()["mailClient"].toString().isEmpty()&&saved()["calendarPlugins"].toArray().isEmpty();
        phase=countsOnly()?501:1;tries=0;
    }
    if(phase==501) {
        auto checkbox=find("domainosMailCountsEnabled");if(!checkbox){QTimer::singleShot(100,step);return;}
        checks["mail_count_preference_defaults_off"]=!saved()["mailCountsEnabled"].toBool()&&!page()->property("cfg_mailCountsEnabled").toBool();
        checks["native_mail_count_checkbox_clicked"]=click(checkbox);phase=502;QTimer::singleShot(100,step);return;
    }
    if(phase==502) {
        checks["mail_count_checkbox_changes_buffer_without_applying"]=page()->property("cfg_mailCountsEnabled").toBool()&&!saved()["mailCountsEnabled"].toBool();
        checks["mail_count_discard_clicked"]=click(find("domainosDirectedDiscard"));phase=503;QTimer::singleShot(100,step);return;
    }
    if(phase==503) {
        checks["mail_count_discard_restores_default_off"]=!page()->property("cfg_mailCountsEnabled").toBool()&&!saved()["mailCountsEnabled"].toBool();
        checks["native_mail_count_checkbox_reselected"]=click(find("domainosMailCountsEnabled"));
        checks["mail_count_apply_clicked"]=click(find("domainosDirectedApply"));phase=504;QTimer::singleShot(100,step);return;
    }
    if(phase==504) {
        checks["mail_count_option_applied_to_native_kconfig"]=saved()["mailCountsEnabled"].toBool();finish();return;
    }
    if(phase==1) {
        const int index=mailIndex(beta);if(index<0){QTimer::singleShot(100,step);return;}
        checks["installed_metadata_catalogue_includes_private_beta"]=true;
        checks["mail_selection_delivered_by_native_keyboard_popup"]=choose("domainosMailClientChoice",index);
        phase=2;tries=0;QTimer::singleShot(100,step);return;
    }
    if(phase==2) {
        checks["mail_onActivated_changes_edit_buffer_only"]=page()->property("cfg_mailClient").toString()==beta&&saved()["mailClient"].toString().isEmpty();
        checks["mail_discard_button_clicked"]=click(find("domainosDirectedDiscard"));phase=3;tries=0;QTimer::singleShot(100,step);return;
    }
    if(phase==3) {
        if(mailIndex(beta)<0){QTimer::singleShot(100,step);return;}
        checks["mail_discard_restores_saved_value"]=page()->property("cfg_mailClient").toString().isEmpty()&&saved()["mailClient"].toString().isEmpty();
        checks["mail_reselection_clicked"]=choose("domainosMailClientChoice",mailIndex(beta));
        checks["mail_apply_button_clicked"]=click(find("domainosDirectedApply"));phase=4;QTimer::singleShot(100,step);return;
    }
    if(phase==4) {
        checks["selected_mail_client_applied_to_native_kconfig"]=saved()["mailClient"].toString()==beta;
        show("ConfigInstruments.qml");phase=5;tries=0;QTimer::singleShot(200,step);return;
    }
    if(phase==5) {
        auto choice=find("domainosCalendarProviderChoice_holidaysevents");if(!choice){QTimer::singleShot(100,step);return;}
        checks["calendar_metadata_listed_without_selecting_source"]=page()->property("availableCalendarProviders").toInt()>=2&&saved()["calendarPlugins"].toArray().isEmpty();
        checks["holiday_checkbox_clicked"]=click(choice);phase=6;QTimer::singleShot(100,step);return;
    }
    if(phase==6) {
        checks["calendar_checkbox_changes_edit_buffer_only"]=page()->property("cfg_calendarPlugins").toStringList()==QStringList{"holidaysevents"}&&saved()["calendarPlugins"].toArray().isEmpty();
        click(find("domainosDirectedDiscard"));phase=7;QTimer::singleShot(100,step);return;
    }
    if(phase==7) {
        checks["calendar_discard_restores_empty_source_selection"]=page()->property("cfg_calendarPlugins").toStringList().isEmpty();
        checks["holiday_reselection_clicked"]=click(find("domainosCalendarProviderChoice_holidaysevents"));
        checks["calendar_apply_button_clicked"]=click(find("domainosDirectedApply"));phase=8;QTimer::singleShot(200,step);return;
    }
    if(phase==8) {
        checks["holiday_selection_applied_to_native_kconfig"]=saved()["calendarPlugins"].toArray()==QJsonArray{"holidaysevents"};
        checks["native_configure_button_clicked"]=click(find("domainosDirectedConfigure"));phase=81;tries=0;QTimer::singleShot(200,step);return;
    }
    if(phase==81) {
        if(!categories()){QTimer::singleShot(100,step);return;}
        show("ConfigIconbox.qml");phase=9;tries=0;QTimer::singleShot(200,step);return;
    }
    if(phase==9) {
        auto combo=find("domainosIconboxWindowPreviewMode");if(!combo){QTimer::singleShot(100,step);return;}
        checks["thumbnail_mode_native_popup_selection_clicked"]=choose("domainosIconboxWindowPreviewMode",1);
        phase=10;QTimer::singleShot(100,step);return;
    }
    if(phase==10) {
        checks["thumbnail_selection_sets_true_and_hints_false_before_apply"]=page()->property("cfg_iconboxWindowThumbnails").toBool()&&!page()->property("cfg_iconboxHintsEnabled").toBool()
            &&!saved()["iconboxWindowThumbnails"].toBool()&&saved()["iconboxHintsEnabled"].toBool();
        click(find("domainosDirectedDiscard"));phase=11;QTimer::singleShot(100,step);return;
    }
    if(phase==11) {
        checks["thumbnail_discard_restores_default_hints_mode"]=!page()->property("cfg_iconboxWindowThumbnails").toBool()&&page()->property("cfg_iconboxHintsEnabled").toBool();
        choose("domainosIconboxWindowPreviewMode",1);click(find("domainosDirectedApply"));phase=12;QTimer::singleShot(100,step);return;
    }
    checks["thumbnail_mode_applied_to_native_kconfig"]=saved()["iconboxWindowThumbnails"].toBool()&&!saved()["iconboxHintsEnabled"].toBool();
    const auto grab=reinterpret_cast<QImage (*)(QWindow *)>(dlsym(RTLD_DEFAULT,"_ZN12QQuickWindow10grabWindowEv"));
    checks["actual_preferences_capture_saved"]=window&&grab&&grab(window).save(qEnvironmentVariable("IRIX_DOMAINOS_PREFS_DIR")+"/PREFERENCIAS-NATIVAS.png");finish();
}
extern "C" int interceptedExec() asm("_ZN12QApplication4execEv");
extern "C" int interceptedExec() {
    auto original=reinterpret_cast<int (*)()>(dlsym(RTLD_NEXT,"_ZN12QApplication4execEv"));if(!original)return 2;
    QTimer::singleShot(1200,step);QTimer::singleShot(22000,[]{finish("Native preference deadline");});return original();
}
