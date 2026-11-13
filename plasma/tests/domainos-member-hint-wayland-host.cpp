// SPDX-License-Identifier: GPL-3.0-or-later
// Directed Qt input in native private Wayland windows; no compositor-seat claim.
#include <QApplication>
#include <QFile>
#include <QEventLoop>
#include <QImage>
#include <QJsonArray>
#include <QJsonDocument>
#include <QJsonObject>
#include <QLabel>
#include <QMouseEvent>
#include <QPointer>
#include <QScreen>
#include <QSet>
#include <QTest>
#include <QTimer>
#include <QUuid>
#include <QWindow>
#include <dlfcn.h>
#include <unistd.h>

using Children=QList<QObject *> (*)(QObject *);
using Map=QPointF (*)(const QObject *,const QObject *,const QPointF &);
using Grab=QImage (*)(QWindow *);
static QPointer<QObject> fixture;
static QPointer<QWindow> host;
static QList<QLabel *> owned;
static QJsonObject checks,snapshots;
static QJsonArray identities;
static QJsonArray inputTrace;
static QString aKey,bKey,groupKey;
static int phase=0,attempts=0,delay=700;
static QPointer<QObject> oldTip,oldContents;
static QPointer<QWindow> enteredWindow;
static int nativeTransitions=0;
static bool finished=false;
static const QString longTitle=(QString("Z literal <title> & ")+QString("long title ").repeated(30)).trimmed();
class InputProbe:public QObject {
    bool eventFilter(QObject *receiver,QEvent *event) override {
        if((event->type()==QEvent::Enter || event->type()==QEvent::Leave) && receiver->inherits("QWindow")) {
            inputTrace.append(QJsonObject{{"event",event->type()==QEvent::Enter?"enter":"leave"},
                {"receiver",receiver->objectName()},{"class",receiver->metaObject()->className()}});
            if(inputTrace.size()>30)inputTrace.removeAt(0);
        } else if(event->type()==QEvent::MouseMove && receiver->inherits("QWindow")) {
            const auto mouse=static_cast<QMouseEvent *>(event);
            inputTrace.append(QJsonObject{{"event","move"},{"receiver",receiver->objectName()},{"class",receiver->metaObject()->className()},
                {"x",mouse->position().x()},{"y",mouse->position().y()},
                {"globalX",mouse->globalPosition().x()},{"globalY",mouse->globalPosition().y()}});
            if(inputTrace.size()>30)inputTrace.removeAt(0);
        }
        return false;
    }
};
static QObject *find(QObject *object,const QString &name) {
    if(!object)return nullptr;
    if(object->objectName()==name)return object;
    const auto children=reinterpret_cast<Children>(dlsym(RTLD_DEFAULT,"_ZNK10QQuickItem10childItemsEv"));
    if(children && object->inherits("QQuickItem"))for(auto child:children(object))if(auto result=find(child,name))return result;
    return nullptr;
}
static QObject *item(const QString &name,QWindow **owner=nullptr) {
    for(auto candidate:QGuiApplication::allWindows())if(candidate->isVisible())
        if(auto result=find(candidate->property("contentItem").value<QObject *>(),name)) {
            if(owner)*owner=candidate;return result;
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
static QObject *hint(const QString &key){return item("domainosGroupMemberHint_"+key);}
static QWindow *tip(const QString &key){const auto h=hint(key);return h ? qobject_cast<QWindow *>(h->property("tooltipPopup").value<QObject *>()) : nullptr;}
static QWindow *pickerWindow(){QWindow *window=nullptr;item("domainosGroupMemberTitle_"+aKey,&window);return window;}
static QPoint point(QObject *target,QWindow *window) {
    const auto map=reinterpret_cast<Map>(dlsym(RTLD_DEFAULT,"_ZNK10QQuickItem9mapToItemEPKS_RK7QPointF"));
    return map ? map(target,window->property("contentItem").value<QObject *>(),QPointF(target->property("width").toDouble()/2,target->property("height").toDouble()/2)).toPoint() : QPoint();
}
static bool moveWindow(QWindow *window,const QPoint &position) {
    using Transition=void (*)(QWindow *,QWindow *,const QPointF &,const QPointF &);
    using Flush=bool (*)(QEventLoop::ProcessEventsFlags);
    const auto transition=reinterpret_cast<Transition>(dlsym(RTLD_DEFAULT,"_ZN22QWindowSystemInterface21handleEnterLeaveEventEP7QWindowS1_RK7QPointFS4_"));
    const auto flush=reinterpret_cast<Flush>(dlsym(RTLD_DEFAULT,"_ZN22QWindowSystemInterface23flushWindowSystemEventsE6QFlagsIN10QEventLoop17ProcessEventsFlagEE"));
    QPointer<QWindow> guarded=window;
    if(!guarded || !transition || !flush || !window->screen()
        || !qFuzzyCompare(window->devicePixelRatio(),1.0)
        || !qFuzzyCompare(window->screen()->devicePixelRatio(),1.0))return false;
    if(enteredWindow!=window) {
        // Observe the platform's real mouse grab, without changing it. A grab
        // would suppress the normal Wayland surface Enter/Leave sequence.
        auto library=dlopen("libQt6WaylandClient.so.6",RTLD_NOW|RTLD_NOLOAD);
        auto grab=library?reinterpret_cast<void **>(dlsym(library,"_ZN15QtWaylandClient14QWaylandWindow10mMouseGrabE")):nullptr;
        const bool observedAbsent=grab && !*grab;
        snapshots["qt_wayland_mouse_grab"]=QJsonObject{{"export_observed",bool(grab)},{"absent",observedAbsent}};
        checks["native_transitions_observe_wayland_mouse_grab_absent"]=observedAbsent;
        if(library)dlclose(library);
        if(!observedAbsent)return false;
        // Wayland sends a Leave/Enter pair when its pointer crosses surfaces.
        // QTest(QWindow*) only sends MouseMove. Deliver the QPA pair together,
        // then flush it before QTest's synchronous move, without an event-loop
        // turn between Leave and Enter. Scale 1 is required, not simulated.
        transition(window,enteredWindow,position,window->mapToGlobal(position));
        flush(QEventLoop::AllEvents);
        ++nativeTransitions;
        enteredWindow=guarded;
        if(!guarded)return false;
    }
    QTest::mouseMove(guarded,position);
    return !guarded.isNull();
}
static bool hover(const QString &name) {
    QWindow *owner=nullptr;auto target=item(name,&owner);if(!target || !owner)return false;
    QPointer<QObject> guardedTarget=target;
    return moveWindow(owner,point(target,owner)) && guardedTarget;
}
static void checkpoint();
static QJsonObject geometry(const QString &key);
static QObject *findAny(QObject *object,const QString &name,QSet<QObject *> &seen) {
    if(!object || seen.contains(object))return nullptr;seen.insert(object);
    if(object->objectName()==name)return object;
    auto children=object->children();
    const auto visual=reinterpret_cast<Children>(dlsym(RTLD_DEFAULT,"_ZNK10QQuickItem10childItemsEv"));
    if(visual && object->inherits("QQuickItem"))children.append(visual(object));
    for(auto child:children)if(auto match=findAny(child,name,seen))return match;
    return nullptr;
}
static QJsonObject readSelectorPoint(const QString &name="domainosGroupSelectorHover") {
    QObject *target=nullptr;
    for(auto window:QGuiApplication::allWindows())if(window->isVisible()) {
        QSet<QObject *> seen;target=findAny(window->property("contentItem").value<QObject *>(),name,seen);
        if(target)break;
    }
    if(!target)return {};
    return QJsonDocument::fromJson(invoke("selectorPoint",QVariant::fromValue(target)).toString().toUtf8()).object();
}
static bool click(const QString &name) {
    QWindow *owner=nullptr;auto target=item(name,&owner);if(!target || !owner || !target->property("enabled").toBool())return false;
    const auto p=point(target,owner);QPointer<QWindow> guardedWindow=owner;QPointer<QObject> guardedTarget=target;
    const auto before=state();const auto beforeGeometry=owner->geometry();const auto selectorBefore=readSelectorPoint();
    const auto pointerBefore=readSelectorPoint("domainosGroupSelectorPointer");
    const bool moved=moveWindow(owner,p);
    const auto activePopup=reinterpret_cast<QWindow *(*)()>(dlsym(RTLD_DEFAULT,"_ZN22QGuiApplicationPrivate17activePopupWindowEv"));
    const auto popup=activePopup?activePopup():nullptr;
    snapshots["last_click"]=QJsonObject{{"name",name},{"owner_alive_after_move",!guardedWindow.isNull()},
        {"target_alive_after_move",!guardedTarget.isNull()},{"before",before},{"after_move",state()},
        {"pointer_global_x",beforeGeometry.x()+p.x()},{"pointer_global_y",beforeGeometry.y()+p.y()},
        {"active_popup_window",popup?popup->objectName():QString()},{"active_popup_window_class",popup?popup->metaObject()->className():"none"},
        {"selector_point_before",selectorBefore},{"selector_point_after_move",readSelectorPoint()},
        {"pointer_point_before",pointerBefore},{"pointer_point_after_move",readSelectorPoint("domainosGroupSelectorPointer")},
        {"preview_a_after_move",geometry(aKey)},{"preview_b_after_move",geometry(bKey)}};
    checkpoint();
    if(!moved || !guardedWindow || !guardedTarget)return false;
    QTest::mousePress(guardedWindow,Qt::LeftButton,Qt::NoModifier,p);
    auto diagnostic=snapshots["last_click"].toObject();
    diagnostic["owner_alive_after_press"]=!guardedWindow.isNull();diagnostic["target_alive_after_press"]=!guardedTarget.isNull();
    diagnostic["after_press"]=state();snapshots["last_click"]=diagnostic;checkpoint();
    if(!guardedWindow || !guardedTarget)return false;
    QTest::mouseRelease(guardedWindow,Qt::LeftButton,Qt::NoModifier,p);return true;
}
static void leave(){if(auto window=pickerWindow())moveWindow(window,QPoint(window->width()-3,3));}
static bool visible(const QString &key){auto window=tip(key);return window && window->isVisible();}
static QJsonObject target(const QJsonObject &s,const QString &title) {
    for(auto value:s["windows"].toArray())if(value.toObject()["title"].toString()==title)return value.toObject();return {};
}
static QJsonObject rect(QRect r){return {{"x",r.x()},{"y",r.y()},{"width",r.width()},{"height",r.height()}};}
static QJsonObject geometry(const QString &key) {
    QWindow *picker=pickerWindow(),*window=tip(key);auto h=hint(key);
    if(!picker || !window || !h)return {};
    return {{"picker",rect(picker->geometry())},{"tooltip",rect(window->geometry())},
        {"placement",h->property("placement").toString()},
        {"rowX",h->property("rowPosition").toPointF().x()},{"rowY",h->property("rowPosition").toPointF().y()},
        {"transient_parent_matches",window->transientParent()==picker},
        {"row_hovered",h->property("hovered").toBool()},{"preview_hovered",h->property("previewHovered").toBool()},
        {"lease_active",h->property("leaseActive").toBool()},{"hover_suppressed",h->property("hoverSuppressed").toBool()}};
}
static bool aboveAndSafe(const QString &key) {
    QWindow *picker=pickerWindow(),*window=tip(key);if(!picker || !window)return false;
    return window->isVisible() && window->y()+window->height()<=picker->y()+1
        && !window->geometry().intersects(picker->geometry())
        && window->screen()->geometry().adjusted(7,7,-7,-7).contains(window->geometry())
        && window->transientParent()==picker;
}
static bool capture(const QString &key,const QString &filename) {
    auto window=tip(key);const auto grab=reinterpret_cast<Grab>(dlsym(RTLD_DEFAULT,"_ZN12QQuickWindow10grabWindowEv"));
    return window && grab && grab(window).save(qEnvironmentVariable("IRIX_DOMAINOS_HINT_DIR")+"/"+filename);
}
static void complete() {
    if(finished)return;finished=true;
    QJsonObject environment;
    for(const auto name:QStringList{"HOME","XDG_CONFIG_HOME","XDG_DATA_HOME","XDG_RUNTIME_DIR","WAYLAND_DISPLAY","DBUS_SESSION_BUS_ADDRESS","DBUS_SYSTEM_BUS_ADDRESS","PULSE_SERVER"})environment[name]=qEnvironmentVariable(name.toLocal8Bit().constData());
    QJsonObject report{{"checks",checks},{"snapshots",snapshots},{"state",fixture?state():QJsonObject()},
        {"identities",identities},{"phase",phase},{"host_pid",int(getpid())},{"hint_delay_ms",delay},{"input_trace",inputTrace},
        {"host_executable",QFile::symLinkTarget("/proc/self/exe")},{"host_namespace_after_exec",environment},
        {"qpa_surface_transitions",nativeTransitions}};
    QFile file(qEnvironmentVariable("IRIX_DOMAINOS_HINT_REPORT"));if(file.open(QIODevice::WriteOnly))file.write(QJsonDocument(report).toJson());
    for(auto widget:owned)widget->close();QCoreApplication::quit();
}
static void tick();
static void next(int p,int wait=80){phase=p;QTimer::singleShot(wait,tick);}
static void checkpoint() {
    QJsonObject progress{{"phase",phase},{"checks",checks},{"snapshots",snapshots},{"state",fixture?state():QJsonObject()},
        {"host_pid",int(getpid())},{"a_tip",geometry(aKey)},{"b_tip",geometry(bKey)},{"input_trace",inputTrace},
        {"selector_point",readSelectorPoint()},{"selector_pointer",readSelectorPoint("domainosGroupSelectorPointer")}};
    QFile file(qEnvironmentVariable("IRIX_DOMAINOS_HINT_DIR")+"/PROGRESS.json");if(file.open(QIODevice::WriteOnly))file.write(QJsonDocument(progress).toJson());
}
static bool require(const QString &name,bool ok){checks[name]=ok;checkpoint();if(!ok){complete();return false;}return true;}
static void tick() {
    if(finished)return;
    if(++attempts>240){checks["native_scenario_completed"]=false;complete();return;}
    if(!fixture){QWindow *foundHost=nullptr;fixture=item("domainosMemberHintFixture",&foundHost);host=foundHost;if(!fixture){QTimer::singleShot(100,tick);return;}host->resize(900,830);}
    const auto current=state();
    checkpoint();
    if(phase==0) {
        auto a=target(current,"A"),b=target(current,longTitle);
        if(current["count"].toInt()!=2 || a.isEmpty() || b.isEmpty()){QTimer::singleShot(100,tick);return;}
        aKey=a["key"].toString();bKey=b["key"].toString();identities={a,b};delay=current["hintDelay"].toInt();
        bool valid=delay>0 && a["pid"].toInt()==getpid() && b["pid"].toInt()==getpid();
        for(auto record:identities)valid &= !record.toObject()["windowIds"].toArray().isEmpty()
            && !QUuid(record.toObject()["windowIds"].toArray().first().toString()).isNull();
        if(!require("two_own_native_uuid_pid_identities",valid))return;
        snapshots["input_scale"]=QJsonObject{{"window_dpr",host->devicePixelRatio()},{"screen_dpr",host->screen()->devicePixelRatio()}};
        if(!require("native_input_window_and_screen_dpr_one",qFuzzyCompare(host->devicePixelRatio(),1.0) && qFuzzyCompare(host->screen()->devicePixelRatio(),1.0)))return;
        auto shortCell=item("domainosLiveTask_"+aKey),longCell=item("domainosLiveTask_"+bKey);
        auto shortPreview=item("domainosTaskThumbnails_"+aKey),longPreview=item("domainosTaskThumbnails_"+bKey);
        if(!require("actual_short_singleton_has_no_hint",shortCell && shortPreview && !shortCell->property("labelTruncated").toBool() && !shortPreview->property("hintsEnabled").toBool()))return;
        if(!require("actual_elided_singleton_has_hint",longCell && longPreview && longCell->property("labelTruncated").toBool() && longPreview->property("hintsEnabled").toBool()))return;
        invoke("hints",false);next(1);
    } else if(phase==1) {
        if(!require("actual_user_hints_off_disables_both_cells",!item("domainosTaskThumbnails_"+aKey)->property("hintsEnabled").toBool() && !item("domainosTaskThumbnails_"+bKey)->property("hintsEnabled").toBool()))return;
        invoke("hints",true);invoke("grouping",1);next(2);
    } else if(phase==2) {
        const auto rows=current["rows"].toArray();if(rows.size()!=1 || !rows.first().toObject()["group"].toBool()){QTimer::singleShot(100,tick);return;}
        groupKey=rows.first().toObject()["key"].toString();
        if(!require("actual_group_preserves_ordered_hint",item("domainosTaskThumbnails_"+groupKey)->property("hintsEnabled").toBool()))return;
        if(!require("group_opened_by_qt_native_pointer",click("domainosLiveTask_"+groupKey)))return;next(3);
    } else if(phase==3) {
        if(!current["groupPopup"].toBool() || !hint(aKey)){QTimer::singleShot(100,tick);return;}
        snapshots["initial"]=current;leave();hover("domainosGroupMemberTitle_"+aKey);next(4,delay+60);
    } else if(phase==4) {
        if(!require("short_member_title_never_opens_hint",!hint(aKey)->property("titleTruncated").toBool() && !visible(aKey)))return;
        hover("domainosGroupMemberTitle_"+bKey);
        if(!require("elided_member_not_immediate",!visible(bKey)))return;next(5,qMax(1,delay/3));
    } else if(phase==5) {
        if(!require("elided_member_waits_platform_delay",!visible(bKey)))return;next(6,delay+70);
    } else if(phase==6) {
        auto h=hint(bKey);auto window=tip(bKey);auto text=window?find(window->property("contentItem").value<QObject *>(),"domainosMemberHintText"):nullptr;
        if(!require("elided_full_literal_text_after_delay",visible(bKey) && text && text->property("text").toString()==longTitle && text->property("textFormat").toInt()==0))return;
        if(!require("text_hint_above_entire_selector_inside_screen",aboveAndSafe(bKey)))return;
        if(!require("text_hint_no_provider_no_redundant_native_input",!h->property("providersLoaded").toBool() && window->flags().testFlag(Qt::WindowTransparentForInput)))return;
        if(!require("text_hint_preserves_selector_and_no_activation",current["groupPopup"].toBool() && current["requests"].toArray().isEmpty()))return;
        snapshots["text_geometry"]=geometry(bKey);capture(bKey,"TEXT-HINT.png");leave();next(7);
    } else if(phase==7) {
        if(!require("text_hint_closes_on_lateral_leave",!visible(bKey) && !tip(bKey)))return;
        hover("domainosGroupMemberTitle_"+bKey);next(8,qMax(1,delay/3));
    } else if(phase==8) {leave();next(9,delay+70);
    } else if(phase==9) {
        if(!require("leave_before_delay_cancels_native_window",!tip(bKey)))return;
        invoke("previews",true);leave();next(10);
    } else if(phase==10) {hover("domainosGroupMemberTitle_"+aKey);next(11,delay+70);
    } else if(phase==11) {
        auto h=hint(aKey);auto window=tip(aKey);auto loader=h->property("contentsLoader").value<QObject *>();
        if(!require("native_preview_lease_with_real_uuid_provider_contents",window && window->isVisible() && h->property("backend").toString()=="wayland" && loader && loader->property("item").value<QObject *>()))return;
        snapshots["preview_a_geometry"]=geometry(aKey);
        if(!require("preview_above_selector_without_old_popup_height_clipping",aboveAndSafe(aKey) && window->height()>pickerWindow()->height()))return;
        auto text=find(window->property("contentItem").value<QObject *>(),"domainosMemberHintText");
        if(!require("preview_omits_redundant_title_text",text && !text->property("visible").toBool()))return;
        oldTip=window;oldContents=loader->property("item").value<QObject *>();
        snapshots["preview_a_geometry"]=geometry(aKey);capture(aKey,"PREVIEW-A.png");
        if(!require("preview_capture_does_not_invalidate_current_lease",oldTip && oldContents))return;
        hover("domainosGroupMemberTitle_"+bKey);next(12,40);
    } else if(phase==12) {
        if(!require("row_a_to_b_destroys_previous_lease",oldTip.isNull() && oldContents.isNull() && !visible(aKey) && !visible(bKey)))return;next(13,delay+70);
    } else if(phase==13) {
        if(!require("row_b_gets_single_native_lease_after_delay",visible(bKey) && !tip(aKey) && current["groupPopup"].toBool()))return;
        snapshots["preview_b_geometry"]=geometry(bKey);capture(bKey,"PREVIEW-B.png");
        if(!require("own_native_client_received_qpa_surface_transition",moveWindow(owned[0]->windowHandle(),QPoint(20,20))))return;next(32,50);
    } else if(phase==32) {
        if(!require("direct_row_to_other_native_client_outside_both_releases_lease",!tip(bKey) && current["groupPopup"].toBool()))return;
        leave();hover("domainosGroupMemberTitle_"+bKey);next(33,delay+70);
    } else if(phase==33) {
        if(!require("preview_reopens_after_direct_native_client_exit",visible(bKey)))return;
        auto window=pickerWindow();auto h=hint(bKey);const int corridorX=qBound(5,int(h->property("rowPosition").toPointF().x()-window->x()+30),window->width()-5);
        moveWindow(window,QPoint(corridorX,5));next(14,30);
    } else if(phase==14) {
        snapshots["header_bridge_lease"]=visible(bKey);auto window=pickerWindow();moveWindow(window,QPoint(window->width()-2,5));next(15);
    } else if(phase==15) {
        if(!require("row_to_header_to_lateral_exit_releases_orphan_path",!tip(bKey)))return;
        hover("domainosGroupMemberTitle_"+aKey);next(16,delay+70);
    } else if(phase==16) {
        if(!require("preview_reopens_after_genuine_hover_entry",visible(aKey)))return;
        auto scroll=item("domainosGroupScrollView");auto flick=scroll?scroll->property("contentItem").value<QObject *>():nullptr;
        snapshots["before_scroll"]=geometry(aKey);
        if(!require("private_actual_scroll_content_changed",flick && flick->setProperty("contentY",15)))return;next(17);
    } else if(phase==17) {
        if(!require("scroll_closes_stale_native_hint",!tip(aKey)))return;leave();hover("domainosGroupMemberTitle_"+aKey);next(18,delay+70);
    } else if(phase==18) {
        const auto after=geometry(aKey);snapshots["after_scroll"]=after;
        auto h=hint(aKey);auto title=item("domainosGroupMemberTitle_"+aKey);auto window=pickerWindow();
        const auto map=reinterpret_cast<Map>(dlsym(RTLD_DEFAULT,"_ZNK10QQuickItem9mapToItemEPKS_RK7QPointF"));
        if(!require("scroll_rehover_keeps_owned_row_and_selector_present",h && title && window && map))return;
        auto actual=map(title,window->property("contentItem").value<QObject *>(),QPointF(0,0))+QPointF(window->x(),window->y());
        if(!require("scroll_rehover_remeasures_actual_native_row_anchor",visible(aKey) && qAbs(h->property("rowPosition").toPointF().x()-actual.x())<2 && qAbs(h->property("rowPosition").toPointF().y()-actual.y())<2))return;
        invoke("trackHint",QVariant::fromValue(h));
        QWindow *cardWindow=nullptr;auto card=item("domainosThumbnailPointer",&cardWindow);
        if(!require("preview_card_enter_received_qpa_surface_transition",card && cardWindow && moveWindow(cardWindow,point(card,cardWindow))))return;next(34);
    } else if(phase==34) {
        snapshots["preview_enter"]=geometry(aKey);
        if(!require("native_preview_enter_preserves_lease_and_hover",visible(aKey) && hint(aKey)->property("previewHovered").toBool() && current["groupPopup"].toBool()))return;
        if(!require("preview_exit_to_own_native_client_received_transition",moveWindow(owned[0]->windowHandle(),QPoint(20,20))))return;next(35);
    } else if(phase==35) {
        if(!require("direct_preview_to_other_native_client_releases_lease",!tip(aKey) && current["groupPopup"].toBool()))return;
        leave();hover("domainosGroupMemberTitle_"+aKey);next(36,delay+70);
    } else if(phase==36) {
        if(!require("native_preview_reopens_after_direct_preview_exit",visible(aKey)))return;
        if(!require("preview_card_clicked_in_own_native_tooltip_window",click("domainosThumbnailPointer")))return;next(19,200);
    } else if(phase==19) {
        const auto requests=current["requests"].toArray();
        if(!require("native_preview_card_activates_exactly_once_and_closes_parent",requests.size()==1 && requests.first().toObject()["key"].toString()==aKey && requests.first().toObject()["action"].toString()=="activate" && requests.first().toObject()["observedTargetPid"].toInt()==getpid() && !current["groupPopup"].toBool() && !tip(aKey) && target(current,"A")["active"].toBool()))return;
        invoke("clearRequests");click("domainosLiveTask_"+groupKey);next(20);
    } else if(phase==20) {leave();hover("domainosGroupMemberTitle_"+bKey);next(21,delay+70);
    } else if(phase==21) {
        if(!require("preview_child_visible_before_plain_member_title_click",visible(bKey)))return;
        if(!require("plain_member_title_clicked_with_native_child_visible",click("domainosGroupMemberTitle_"+bKey)))return;next(29,200);
    } else if(phase==29) {
        const auto requests=current["requests"].toArray();
        if(!require("plain_member_title_activates_once_and_unmaps_child_before_parent",requests.size()==1 && requests.first().toObject()["key"].toString()==bKey && requests.first().toObject()["action"].toString()=="activate" && requests.first().toObject()["observedTargetPid"].toInt()==getpid() && !current["groupPopup"].toBool() && !tip(bKey) && target(current,longTitle)["active"].toBool()))return;
        invoke("clearRequests");click("domainosLiveTask_"+groupKey);next(30);
    } else if(phase==30) {leave();hover("domainosGroupMemberTitle_"+bKey);next(31,delay+70);
    } else if(phase==31) {
        if(!require("preview_child_visible_before_checkbox_click",visible(bKey)))return;
        if(!require("actual_checkbox_clicked_with_hint_surface_present",click("domainosGroupMember_"+bKey)))return;next(22);
    } else if(phase==22) {
        if(!require("checkbox_releases_hint_and_preserves_selector",current["groupPopup"].toBool() && !tip(bKey) && current["memberKeys"].toArray().size()==1 && current["requests"].toArray().isEmpty()))return;
        click("domainosGroupMember_"+aKey);hover("domainosGroupMemberTitle_"+aKey);next(23,delay+70);
    } else if(phase==23) {
        if(!require("child_hint_visible_before_operations_close_chain",visible(aKey)))return;
        if(!require("operations_clicked_with_preview_child",click("domainosGroupOrganize")))return;next(24,150);
    } else if(phase==24) {
        if(!require("native_hint_released_before_successor_operations_surface",!tip(aKey) && !tip(bKey) && !current["groupPopup"].toBool() && current["operationsPopup"].toBool() && current["requests"].toArray().isEmpty()))return;
        invoke("resetUi");click("domainosLiveTask_"+groupKey);next(25);
    } else if(phase==25) {leave();hover("domainosGroupMemberTitle_"+bKey);next(26,delay+70);
    } else if(phase==26) {
        if(!require("preview_visible_before_outside_client_click",visible(bKey)))return;leave();next(27);
    } else if(phase==27) {
        if(!require("preview_hidden_before_outside_client_click",!tip(bKey)))return;
        QPointer<QWindow> other=owned[0]->windowHandle();
        if(!require("outside_client_pointer_transition_preserves_target",moveWindow(other,QPoint(20,20)) && other))return;
        QTest::mousePress(other,Qt::LeftButton,Qt::NoModifier,QPoint(20,20));
        if(!require("outside_client_press_preserves_own_window",bool(other)))return;
        QTest::mouseRelease(other,Qt::LeftButton,Qt::NoModifier,QPoint(20,20));next(28);
    } else if(phase==28) {
        if(!require("outside_click_other_owned_native_client_still_closes_picker",!current["groupPopup"].toBool()))return;
        checks["all_own_widgets_remain_alive"]=owned[0]->isVisible() && owned[1]->isVisible();checks["native_scenario_completed"]=true;complete();return;
    }
}
extern "C" int _ZN12QApplication4execEv() {
    const auto original=reinterpret_cast<int (*)()>(dlsym(RTLD_NEXT,"_ZN12QApplication4execEv"));
    QApplication::setApplicationName("org.irixclassic.domainos.memberhint.qa");QApplication::setDesktopFileName("org.irixclassic.domainos.memberhint.qa");
    qApp->installEventFilter(new InputProbe);
    for(const auto title:QStringList{"A",longTitle}){auto widget=new QLabel(title);widget->setWindowTitle(title);widget->setStyleSheet("background:#b03040;color:#ffffff");widget->resize(260,160);widget->show();owned.append(widget);}
    QTimer::singleShot(80,tick);QTimer::singleShot(45000,[](){if(!finished){checks["bounded_native_timeout_not_reached"]=false;complete();}});return original();
}
