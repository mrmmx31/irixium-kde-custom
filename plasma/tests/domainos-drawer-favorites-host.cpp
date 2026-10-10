// SPDX-FileCopyrightText: 2026 IRIX Classic contributors
// SPDX-License-Identifier: GPL-3.0-or-later
#include <QApplication>
#include <QCryptographicHash>
#include <QFile>
#include <QImage>
#include <QJsonArray>
#include <QJsonDocument>
#include <QJsonObject>
#include <QTest>
#include <QTimer>
#include <QWindow>
#include <dlfcn.h>
#include <functional>

using Children=QList<QObject *> (*)(QObject *);
using Map=QPointF (*)(const QObject *,const QObject *,const QPointF &);
using Grab=QImage (*)(QWindow *);
static QObject *fixture=nullptr;
static QJsonObject checks,snapshots;
static int phase=0,attempts=0,peerWait=0;
static QString expectedLaunch;
static QByteArray statsBeforeRead,appletsBeforeRead;
static int sequenceBeforeRead=0;
static QByteArray fileHash(const QString &name) {
    QFile file(qEnvironmentVariable("XDG_CONFIG_HOME")+"/"+name);
    return file.open(QIODevice::ReadOnly) ? QCryptographicHash::hash(file.readAll(),QCryptographicHash::Sha256) : QByteArray();
}
static QObject *walk(QObject *object,const std::function<bool(QObject *)> &matches) {
    if(!object)return nullptr;
    if(matches(object))return object;
    const auto children=reinterpret_cast<Children>(dlsym(RTLD_DEFAULT,"_ZNK10QQuickItem10childItemsEv"));
    if(children && object->inherits("QQuickItem"))for(auto child:children(object))if(auto found=walk(child,matches))return found;
    return nullptr;
}
static QObject *item(const QString &name,QWindow **owner=nullptr) {
    for(auto window:QGuiApplication::allWindows())if(window->isVisible()) {
        if(auto found=walk(window->property("contentItem").value<QObject *>(),[&](QObject *object){return object->objectName()==name;})) {
            if(owner)*owner=window;return found;
        }
    }
    return nullptr;
}
static QVariant invoke(const char *method,const QVariant &argument={}) {
    QVariant result;
    if(argument.isValid())QMetaObject::invokeMethod(fixture,method,Qt::DirectConnection,Q_RETURN_ARG(QVariant,result),Q_ARG(QVariant,argument));
    else QMetaObject::invokeMethod(fixture,method,Qt::DirectConnection,Q_RETURN_ARG(QVariant,result));
    return result;
}
static QJsonObject state(){return QJsonDocument::fromJson(invoke("state").toString().toUtf8()).object();}
static QRectF rect(QObject *target,QWindow *owner) {
    const auto map=reinterpret_cast<Map>(dlsym(RTLD_DEFAULT,"_ZNK10QQuickItem9mapToItemEPKS_RK7QPointF"));
    if(!target || !owner || !map)return {};
    return QRectF(map(target,owner->property("contentItem").value<QObject *>(),QPointF()),QSizeF(target->property("width").toDouble(),target->property("height").toDouble()));
}
static bool click(const QString &name) {
    QWindow *owner=nullptr;auto target=item(name,&owner);const auto bounds=rect(target,owner);
    if(!target || !owner || !QRectF(QPointF(),owner->size()).contains(bounds.center()))return false;
    QTest::mouseMove(owner,bounds.center().toPoint());QTest::mouseClick(owner,Qt::LeftButton,Qt::NoModifier,bounds.center().toPoint());return true;
}
static bool capture(const QString &filename) {
    QWindow *owner=nullptr;auto target=item("domainosApplicationsPopupContent",&owner);
    const auto grab=reinterpret_cast<Grab>(dlsym(RTLD_DEFAULT,"_ZN12QQuickWindow10grabWindowEv"));
    return target && owner && grab && grab(owner).save(qEnvironmentVariable("IRIX_DOMAINOS_APPLICATIONS_DIR")+"/"+filename);
}
static QJsonArray ids(const QJsonArray &rows) {
    QJsonArray result;for(const auto &row:rows)result.append(row.toObject()["favoriteId"]);return result;
}
static QJsonArray pins(){return {"domainos-favorite-gamma.desktop","domainos-favorite-alpha.desktop"};}
static bool drawerMatches(const QJsonObject &current) {
    const auto native=current["peer"].toArray(),drawer=current["drawer"].toArray();
    if(native.size()!=drawer.size())return false;
    for(int row=0;row<native.size();++row) {
        const auto a=native[row].toObject(),b=drawer[row].toObject();
        auto delegate=item(QString("domainosSharedFavorite_%1").arg(row));
        if(a["favoriteId"]!=b["favoriteId"] || a["title"]!=b["title"] || !b["available"].toBool() || !delegate || delegate->property("text").toString()!=a["title"].toString())return false;
    }
    return true;
}
static bool drawerMembersMatch(const QJsonObject &current) {
    QStringList native,drawer;
    for(const auto &row:current["native"].toArray())native.append(row.toObject()["favoriteId"].toString());
    for(const auto &row:current["drawer"].toArray())drawer.append(row.toObject()["favoriteId"].toString());
    native.sort();drawer.sort();return native==drawer;
}
static void finish(const QString &error={}) {
    QJsonObject report{{"checks",checks},{"snapshots",snapshots},{"state",fixture ? state() : QJsonObject()}};
    if(!error.isEmpty())report["failure"]=error;
    QFile file(qEnvironmentVariable("IRIX_DOMAINOS_APPLICATIONS_REPORT"));if(file.open(QIODevice::WriteOnly))file.write(QJsonDocument(report).toJson());
    QCoreApplication::quit();
}
static void tick() {
    if(++attempts>160){checks["native_scenario_completed"]=false;finish("Bounded drawer favorites timeout");return;}
    if(!fixture) {fixture=item("domainosDrawerFavoritesFixture");if(!fixture){QTimer::singleShot(100,tick);return;}}
    const auto current=state();
    if(phase==0) {
        checks["default_own_pins_distinct_from_shared_favorites"]=current["pins"].toArray()==pins();
        if(!invoke("action","seed").toBool()){finish("Seed failed");return;}phase=1;
    } else if(phase==1) {
        if(current["native"].toArray().size()!=3 || current["peer"].toArray().size()!=3 || !current["popup"].toBool() || current["orderBusy"].toBool() || !drawerMatches(current)){QTimer::singleShot(100,tick);return;}
        checks["genuine_shared_kastats_model"]=current["nativeFavoriteClass"].toString().contains("KAStats") && current["peerFavoriteClass"].toString().contains("KAStats");
        checks["other_kicker_client_adds_all_three_shared_members"]=true;
        checks["drawer_titles_and_order_equal_external_menu_provider"]=drawerMatches(current);
        checks["existing_external_menu_identified_explicitly"]=current["orderOrigin"].toObject()["location"].toString()=="77/42" && !current["orderMessage"].toString().isEmpty();
        checks["favorites_do_not_repopulate_taskbar_pins"]=current["pins"].toArray()==pins();
        QWindow *owner=nullptr;auto pref=item("domainosPinnedPreferencesEntry",&owner);
        auto firstPin=item("domainosApplicationEntry_0");auto pinHeading=item("domainosTaskbarPinsHeading");auto favoriteHeading=item("domainosSharedFavoritesHeading");auto separator=item("domainosPinnedFavoritesSeparator");
        checks["preferences_first_pins_second_favorites_third"]=pref && firstPin && pinHeading && favoriteHeading && rect(pref,owner).bottom()<=rect(pinHeading,owner).top() && rect(firstPin,owner).bottom()<rect(favoriteHeading,owner).top();
        checks["separator_between_pins_and_favorites"]=separator && rect(separator,owner).top()>=rect(item("domainosApplicationEntry_1"),owner).bottom() && rect(separator,owner).bottom()<=rect(favoriteHeading,owner).top();
        auto firstSeparator=walk(owner ? owner->property("contentItem").value<QObject *>() : nullptr,[&](QObject *object){return QString(object->metaObject()->className()).contains("MenuSeparator") && object->property("visible").toBool() && rect(object,owner).top()>=rect(pref,owner).bottom() && rect(object,owner).bottom()<=rect(pinHeading,owner).top();});
        checks["separator_after_immutable_preferences"]=firstSeparator!=nullptr;
        bool compact=true,names=true;
        for(int row=0;row<2;++row) {
            auto label=item(QString("domainosPinnedName_%1").arg(row));
            names=names && label && label->property("width").toDouble()>=200 && !label->property("truncated").toBool() && !label->property("text").toString().isEmpty();
            for(const auto &action:QStringList{"Remove","Up","Down"}) {
                auto button=item(QString("domainosPinned%1_%2").arg(action).arg(row));
                compact=compact && button && button->property("width").toDouble()<=28.01 && button->property("height").toDouble()<=28.01;
            }
        }
        checks["six_pin_controls_at_most_28px"]=compact;checks["taskbar_pin_names_visible_with_at_least_200px"]=names;
        checks["drawer_native_initial_frame_saved"]=capture("DRAWER-NATIVE-FAVORITES.png");snapshots["initial"]=current;
        invoke("action","peerRemove");phase=2;
    } else if(phase==2) {
        if(current["native"].toArray().size()!=2 || current["peer"].toArray().size()!=2 || !drawerMembersMatch(current)){QTimer::singleShot(100,tick);return;}
        checks["peer_removal_updates_drawer_while_open"]=current["popup"].toBool();
        checks["peer_removal_preserves_taskbar_pins"]=current["pins"].toArray()==pins();snapshots["peer_removed"]=current;
        invoke("action","peerAdd");phase=3;
    } else if(phase==3) {
        if(current["native"].toArray().size()!=3 || current["peer"].toArray().size()!=3 || !drawerMembersMatch(current)){QTimer::singleShot(100,tick);return;}
        checks["peer_readdition_updates_drawer_while_open"]=current["popup"].toBool() && current["pins"].toArray()==pins();
        invoke("action","ownMove");phase=4;
    } else if(phase==4) {
        if(ids(current["native"].toArray()).first()!=current["ownRequestedFirst"] || !drawerMembersMatch(current)){QTimer::singleShot(100,tick);return;}
        checks["own_provider_reorder_does_not_override_external_rank"]=ids(current["drawer"].toArray())==ids(snapshots["initial"].toObject()["drawer"].toArray());
        checks["native_provider_reorder_preserves_pins"]=current["pins"].toArray()==pins();snapshots["own_reordered"]=current;
        invoke("action","peerMove");phase=5;
    } else if(phase==5) {
        if(++peerWait<8 || ids(current["peer"].toArray()).first()!=current["peerRequestedFirst"]){QTimer::singleShot(100,tick);return;}
        checks["peer_reorder_preserves_members_and_pins"]=current["native"].toArray().size()==3 && drawerMembersMatch(current) && current["pins"].toArray()==pins();
        snapshots["peer_reordered_before_reopen"]=current;
        statsBeforeRead=fileHash("kactivitymanagerd-statsrc");appletsBeforeRead=fileHash("plasma-org.kde.plasma.desktop-appletsrc");
        sequenceBeforeRead=current["orderSequence"].toInt();
        invoke("action","coalesced");const auto pending=state();
        checks["rapid_reopens_keep_one_pending_read"]=pending["orderBusy"].toBool() && pending["orderSequence"].toInt()==sequenceBeforeRead+1;
        phase=6;
    } else if(phase==6) {
        if(current["orderBusy"].toBool() || !drawerMatches(current)){QTimer::singleShot(100,tick);return;}
        checks["peer_move_then_reopen_matches_external_exact_order"]=true;
        checks["stale_reopens_coalesce_to_one_final_read"]=current["orderSequence"].toInt()==sequenceBeforeRead+2;
        checks["order_reads_preserve_stats_bytes"]=statsBeforeRead==fileHash("kactivitymanagerd-statsrc");
        checks["order_reads_preserve_applet_metadata_bytes"]=appletsBeforeRead==fileHash("plasma-org.kde.plasma.desktop-appletsrc");
        snapshots["peer_reordered_after_reopen"]=current;
        const auto protocol=QJsonDocument::fromJson(invoke("action","protocolFailures").toString().toUtf8()).object();
        for(auto iterator=protocol.begin();iterator!=protocol.end();++iterator)checks[iterator.key()]=iterator.value();
        checks["pin_up_clicked_by_real_pointer"]=click("domainosPinnedUp_1");phase=7;
    } else if(phase==7) {
        if(current["pins"].toArray()==pins()){QTimer::singleShot(100,tick);return;}
        checks["pin_up_changes_only_own_pin_order"]=current["pins"].toArray()==QJsonArray{"domainos-favorite-alpha.desktop","domainos-favorite-gamma.desktop"} && ids(current["native"].toArray())==ids(snapshots["peer_reordered_after_reopen"].toObject()["native"].toArray());
        checks["pin_down_clicked_by_real_pointer"]=click("domainosPinnedDown_0");phase=8;
    } else if(phase==8) {
        if(current["pins"].toArray()!=pins()){QTimer::singleShot(100,tick);return;}
        checks["pin_down_restores_own_order_without_favorite_mutation"]=drawerMatches(current);
        checks["pin_remove_clicked_by_real_pointer"]=click("domainosPinnedRemove_1");phase=9;
    } else if(phase==9) {
        if(current["pins"].toArray().size()!=1){QTimer::singleShot(100,tick);return;}
        checks["unpin_does_not_remove_shared_favorite"]=current["native"].toArray().size()==3 && drawerMatches(current);
        checks["permanent_preferences_remains_first_after_unpin"]=item("domainosPinnedPreferencesEntry")!=nullptr;
        checks["preferences_clicked_by_real_pointer"]=click("domainosPinnedPreferencesEntry");phase=10;
    } else if(phase==10) {
        if(current["configureRequests"].toInt()!=1 || current["popup"].toBool()){QTimer::singleShot(100,tick);return;}
        checks["preferences_configure_only_own_instance_without_pin_or_favorite_launch"]=current["pins"].toArray()==QJsonArray{"domainos-favorite-gamma.desktop"} && current["native"].toArray().size()==3 && current["pinLaunchRequests"].toInt()==0 && current["dispatchBegins"].toInt()==0;
        invoke("action","kde");phase=11;
    } else if(phase==11) {
        if(!current["nativeKdeMenuSameFavorites"].toBool() || !current["popup"].toBool() || current["orderBusy"].toBool() || !drawerMatches(current)){QTimer::singleShot(100,tick);return;}
        checks["optional_native_kde_menu_and_drawer_share_exact_provider_object"]=true;
        checks["drawer_final_native_frame_saved"]=capture("DRAWER-AFTER-REORDER.png");snapshots["before_launch"]=current;
        expectedLaunch=current["drawer"].toArray().first().toObject()["favoriteId"].toString();
        checks["favorite_overlay_index_differs_from_native_index"]=current["drawer"].toArray().first().toObject()["favoriteId"]!=current["native"].toArray().first().toObject()["favoriteId"];
        checks["native_shared_favorite_clicked_by_real_pointer"]=click("domainosSharedFavorite_0");phase=12;
    } else if(phase==12) {
        QFile marker(qEnvironmentVariable("IRIX_DOMAINOS_APPLICATIONS_DIR")+"/dispatch.txt");const auto dispatched=marker.open(QIODevice::ReadOnly) ? QString::fromUtf8(marker.readAll()).trimmed() : QString();
        if(dispatched!=expectedLaunch || current["popup"].toBool()){QTimer::singleShot(100,tick);return;}
        checks["native_favorite_launch_executes_exact_owned_desktop_entry"]=true;
        checks["favorite_launch_keeps_independent_taskbar_pin"]=current["pins"].toArray()==QJsonArray{"domainos-favorite-gamma.desktop"} && current["pinLaunchRequests"].toInt()==0;
        checks["favorite_launch_uses_native_dispatch_and_activity_contract"]=current["dispatchBegins"].toInt()==1 && current["dispatchReports"].toArray().size()==1;
        checks["native_scenario_completed"]=true;snapshots["final"]=current;finish();return;
    }
    QTimer::singleShot(120,tick);
}
extern "C" int interceptedExec() asm("_ZN12QApplication4execEv");
extern "C" int interceptedExec() {
    const auto original=reinterpret_cast<int (*)()>(dlsym(RTLD_NEXT,"_ZN12QApplication4execEv"));if(!original)return 2;
    QTimer::singleShot(1400,tick);return original();
}
