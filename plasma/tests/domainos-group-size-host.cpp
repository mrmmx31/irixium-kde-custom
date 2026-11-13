// SPDX-License-Identifier: GPL-3.0-or-later
#include <QApplication>
#include <QFile>
#include <QImage>
#include <QJsonArray>
#include <QJsonDocument>
#include <QJsonObject>
#include <QProcess>
#include <QScreen>
#include <QSignalSpy>
#include <QMetaProperty>
#include <QPointer>
#include <QTimer>
#include <QWidget>
#include <QWindow>
#include <dlfcn.h>
#include <unistd.h>

using Children=QList<QObject *> (*)(QObject *);
using Grab=QImage (*)(QWindow *);
static QObject *fixture=nullptr;
static QWindow *host=nullptr;
static QList<QWidget*> owned;
static QJsonObject checks,snapshots;
static int phase=0,attempts=0,hoverMoves=0;
static QSignalSpy *hintChanges=nullptr;
static QPointer<QObject> watchedHint,watchedTitle;
static int initialModelChanges=0,initialRowRefreshes=0;
static bool titleUpdates=true;
static QObject *findVisual(QObject *item,const QString &name) {
    if(!item)return nullptr;if(item->objectName()==name)return item;
    const auto children=reinterpret_cast<Children>(dlsym(RTLD_DEFAULT,"_ZNK10QQuickItem10childItemsEv"));
    if(item->inherits("QQuickItem") && children)for(auto child:children(item))if(auto found=findVisual(child,name))return found;
    return nullptr;
}
static QObject *named(const QString &name) {
    if(auto result=fixture->findChild<QObject*>(name,Qt::FindChildrenRecursively))return result;
    for(auto window:QGuiApplication::allWindows())if(auto result=findVisual(window->property("contentItem").value<QObject*>(),name))return result;
    return nullptr;
}
static QVariant invoke(const char *method) {
    QVariant value;QMetaObject::invokeMethod(fixture,method,Qt::DirectConnection,Q_RETURN_ARG(QVariant,value));return value;
}
static QJsonObject state(){return QJsonDocument::fromJson(invoke("state").toString().toUtf8()).object();}
static void physical(const QStringList &args) {
    auto process=new QProcess(QCoreApplication::instance());QObject::connect(process,qOverload<int,QProcess::ExitStatus>(&QProcess::finished),process,[process](int,QProcess::ExitStatus){process->deleteLater();});process->start("xdotool",args);
}
static void openPicker() {
    const auto position=QJsonDocument::fromJson(invoke("coordinates").toString().toUtf8()).object();
    physical({"mousemove",QString::number(qRound(position["x"].toDouble())),QString::number(qRound(position["y"].toDouble())),"click","1"});
}
static QJsonObject metrics() {
    QJsonObject result;
    for(const auto name:{"domainosGroupPicker","domainosGroupHeader","domainosGroupScrollView","domainosGroupMembersColumn","domainosGroupFooter","domainosGroupHorizontalScrollBar","domainosGroupVerticalScrollBar"}) {
        auto object=named(name);QJsonObject fields;
        if(object)for(const auto field:{"width","height","availableWidth","availableHeight","contentWidth","contentHeight","y","implicitHeight","visible","preferredHeight","memberCount","chromeHeight","listHeight"})fields[field]=QJsonValue::fromVariant(object->property(field));
        result[name]=fields;
    }
    return result;
}
static bool capture(const QString &name) {
    auto grab=reinterpret_cast<Grab>(dlsym(RTLD_DEFAULT,"_ZN12QQuickWindow10grabWindowEv"));
    for(auto window:QGuiApplication::allWindows())if(window!=host && window->inherits("QQuickWindow") && window->isVisible())if(grab && grab(window).save(qEnvironmentVariable("IRIX_DOMAINOS_UNITY_OUTPUT")+"/"+name))return true;
    return false;
}
static QPoint memberPoint(QObject *item) {
    using Map=QPointF (*)(const QObject*,const QPointF&);
    const auto map=reinterpret_cast<Map>(dlsym(RTLD_DEFAULT,"_ZNK10QQuickItem11mapToGlobalERK7QPointF"));
    return item && map && item->inherits("QQuickItem") ? map(item,QPointF(item->property("width").toDouble()/2,item->property("height").toDouble()/2)).toPoint() : QPoint();
}
static bool layoutCheck(int count) {
    auto values=metrics();snapshots["layout_"+QString::number(count)+"_"+QString::number(phase)]=values;
    auto popup=values["domainosGroupPicker"].toObject(),scroll=values["domainosGroupScrollView"].toObject(),column=values["domainosGroupMembersColumn"].toObject(),footer=values["domainosGroupFooter"].toObject();
    const QString suffix=QString::number(count)+"_phase"+QString::number(phase);
    checks["width_matches_viewport_"+suffix]=column["width"].toDouble()==scroll["availableWidth"].toDouble() && scroll["contentWidth"].toDouble()==scroll["availableWidth"].toDouble();
    checks["no_horizontal_overflow_"+suffix]=scroll["contentWidth"].toDouble()<=scroll["availableWidth"].toDouble();
    checks["visible_rows_"+suffix]=scroll["availableHeight"].toDouble()>=qMin(count,15)*36;
    checks["footer_inside_popup_"+suffix]=footer["y"].toDouble()+footer["height"].toDouble()<=popup["availableHeight"].toDouble()+.5;
    QWindow *nativePopup=nullptr;
    for(auto window:QGuiApplication::allWindows())
        if(window->isVisible() && window->inherits("QQuickWindow")
                && findVisual(window->property("contentItem").value<QObject*>(),"domainosGroupFooter")) {
            nativePopup=window;break;
        }
    checks["native_surface_contains_popup_"+suffix]=nativePopup && nativePopup->height()+.5>=popup["height"].toDouble();
    checks["native_surface_inside_screen_"+suffix]=nativePopup && nativePopup->screen()->geometry().contains(nativePopup->geometry());
    if(nativePopup)snapshots["native_surface_"+suffix]=QJsonObject{{"height",nativePopup->height()},{"width",nativePopup->width()},
        {"x",nativePopup->x()},{"y",nativePopup->y()}};
    checks["popup_fits_screen_"+suffix]=popup["height"].toDouble()<=host->screen()->geometry().height()-8;
    checks["horizontal_scrollbar_hidden_"+suffix]=!values["domainosGroupHorizontalScrollBar"].toObject()["visible"].toBool();
    checks["vertical_scrollbar_only_when_sixteenth_member_"+suffix]=values["domainosGroupVerticalScrollBar"].toObject()["visible"].toBool()==(count>15);
    return true;
}
static void complete() {
    const auto events=fixture ? state()["popupEvents"].toArray() : QJsonArray();
    bool showReady=true,openedReady=true;int shows=0,opens=0;
    for(const auto &entry:events) {
        const auto event=entry.toObject();const auto signal=event["signal"].toString();
        if(signal!="aboutToShow" && signal!="opened")continue;
        const bool ready=qAbs(event["height"].toDouble()-event["preferred"].toDouble())<.5;
        if(signal=="aboutToShow"){++shows;showReady&=ready;}else{++opens;openedReady&=ready;}
    }
    checks["all_openings_have_final_height_before_about_to_show"]=shows>=7 && showReady;
    checks["all_openings_have_final_height_when_opened"]=opens>=7 && openedReady;
    QFile file(qEnvironmentVariable("IRIX_DOMAINOS_UNITY_OUTPUT")+"/native.json");
    if(file.open(QIODevice::WriteOnly))file.write(QJsonDocument(QJsonObject{{"checks",checks},{"snapshots",snapshots},{"owned_pid",getpid()},{"final",fixture ? state() : QJsonObject()}}).toJson());
    for(auto widget:owned)widget->close();QCoreApplication::quit();
}
static void addWindows(int total) {
    while(owned.size()<total){auto widget=new QWidget;widget->setWindowTitle(QString("DomainOS group owned %1 — um título suficientemente longo para testar elisão sem barras de rolagem horizontais").arg(owned.size()+1));widget->resize(180,90);widget->move(40+owned.size()*18,50+owned.size()*12);widget->show();owned.append(widget);}
}
static void removeWindows(int total) {
    while(owned.size()>total){auto widget=owned.takeLast();widget->close();widget->deleteLater();}
}
static void tick() {
    if(++attempts>150){checks["native_scenario_completed"]=false;complete();return;}
    if(!fixture) {
        for(auto candidate:QGuiApplication::allWindows())if((fixture=findVisual(candidate->property("contentItem").value<QObject*>(),"domainosGroupSizeFixture"))){host=candidate;break;}
        if(!fixture){QTimer::singleShot(100,tick);return;}
        host->setFlags(Qt::Tool|Qt::FramelessWindowHint);host->setGeometry(200,550,594,150);host->show();
        QMetaObject::invokeMethod(fixture,"setOwnedPid",Qt::DirectConnection,Q_ARG(QVariant,QVariant(getpid())));
    }
    auto current=state();
    if(phase==0){if(current["windows"].toArray().size()!=3){QTimer::singleShot(100,tick);return;}QMetaObject::invokeMethod(fixture,"observePicker",Qt::DirectConnection,Q_ARG(QVariant,QVariant::fromValue(named("domainosGroupPicker"))));openPicker();phase=1;}
    else if(phase==1){checks["three_first_open"]=current["open"].toBool();layoutCheck(3);checks["three_capture_saved"]=capture("GROUP-3.png");QMetaObject::invokeMethod(fixture,"observePicker",Qt::DirectConnection,Q_ARG(QVariant,QVariant::fromValue(named("domainosGroupPicker"))));QMetaObject::invokeMethod(fixture,"closePicker");phase=2;}
    else if(phase==2){openPicker();phase=3;}
    else if(phase==3){checks["three_reopen"]=current["open"].toBool();layoutCheck(3);QMetaObject::invokeMethod(fixture,"closePicker");addWindows(15);phase=4;}
    else if(phase==4){if(current["windows"].toArray().size()!=15){QTimer::singleShot(100,tick);return;}openPicker();phase=5;}
    else if(phase==5){checks["fifteen_first_open"]=current["open"].toBool();layoutCheck(15);checks["fifteen_capture_saved"]=capture("GROUP-15.png");QMetaObject::invokeMethod(fixture,"closePicker");phase=6;}
    else if(phase==6){openPicker();phase=7;}
    else if(phase==7){checks["fifteen_reopen"]=current["open"].toBool();layoutCheck(15);QMetaObject::invokeMethod(fixture,"closePicker");addWindows(16);phase=8;}
    else if(phase==8){if(current["windows"].toArray().size()!=16){QTimer::singleShot(100,tick);return;}openPicker();phase=9;}
    else if(phase==9){checks["sixteen_first_open"]=current["open"].toBool();layoutCheck(16);checks["sixteen_capture_saved"]=capture("GROUP-16.png");phase=10;}
    else if(phase==10){
        const auto key=current["members"].toArray().first().toObject()["key"].toString();auto title=named("domainosGroupMemberTitle_"+key);
        auto point=memberPoint(title);snapshots["hover_point"]=QJsonObject{{"x",point.x()},{"y",point.y()}};physical({"mousemove",QString::number(point.x()),QString::number(point.y())});phase=11;
    }else if(phase==11){
        const auto key=current["members"].toArray().first().toObject()["key"].toString();auto hint=named("domainosGroupMemberHint_"+key);
        bool visible=hint && hint->property("tooltipVisible").toBool();
        if(!visible && hoverMoves==0 && attempts<130){QTimer::singleShot(150,tick);return;}
        checks["hover_hint_visible_initially"]=visible;
        if(hoverMoves==0 && hint){auto property=hint->metaObject()->property(hint->metaObject()->indexOfProperty("tooltipVisible"));hintChanges=new QSignalSpy(hint,property.notifySignal());watchedHint=hint;watchedTitle=named("domainosGroupMemberTitle_"+key);initialModelChanges=current["modelChanges"].toInt();initialRowRefreshes=current["rowRefreshes"].toInt();}
        if(hoverMoves<20){auto point=memberPoint(named("domainosGroupMemberTitle_"+key));physical({"mousemove",QString::number(point.x()+(hoverMoves%3)-1),QString::number(point.y()+(hoverMoves%3)-1)});++hoverMoves;phase=12;}
    }else if(phase==12){
        const auto key=current["members"].toArray().first().toObject()["key"].toString();auto hint=named("domainosGroupMemberHint_"+key);
        checks["hover_hint_remains_visible_move_"+QString::number(hoverMoves)]=hint && hint->property("tooltipVisible").toBool();
        checks["member_delegate_and_hint_retained_move_"+QString::number(hoverMoves)]=watchedHint && watchedTitle && named("domainosGroupMemberHint_"+key)==watchedHint && named("domainosGroupMemberTitle_"+key)==watchedTitle;
        if(titleUpdates && hoverMoves<=10)owned[1]->setWindowTitle(QString("DomainOS group owned 2 — atualização real de título %1 sem alterar PID nem WinId").arg(hoverMoves));
        if(hoverMoves<20)phase=11;else {
            auto text=named("domainosMemberHintText");
            if(text){QJsonObject details;for(auto key:{"text","width","height","visible","opacity","color"})details[key]=QJsonValue::fromVariant(text->property(key));snapshots["member_hint_text"]=details;QJsonArray chain;for(QObject* parent=text;parent;parent=parent->property("parent").value<QObject*>()){QJsonObject entry{{"class",parent->metaObject()->className()}};for(auto key:{"x","y","width","height","visible","opacity"})entry[key]=QJsonValue::fromVariant(parent->property(key));chain.append(entry);}snapshots["member_hint_visual_parents"]=chain;bool insideRow=false;for(const auto &entry:chain)insideRow|=entry.toObject()["class"].toString().startsWith("DomainOSGroupMemberHint");checks["hint_text_paints_in_tooltip_not_list_row"]=!insideRow && text->property("visible").toBool() && text->property("width").toDouble()>0;}
            checks["group_hint_capture_saved"]=capture("GROUP-HINT.png");
            checks["native_hint_has_no_hide_show_expiry_during_twenty_moves"]=hintChanges && hintChanges->count()==0;
            if(titleUpdates) {
                checks["ten_real_task_data_changes_during_unchanged_member_hover"]=current["modelChanges"].toInt()-initialModelChanges>=10;
                checks["ten_controller_row_refreshes_preserve_hovered_qobjects"]=current["rowRefreshes"].toInt()-initialRowRefreshes>=10;
            } else {
                checks["static_hover_requires_no_window_model_update"]=current["modelChanges"].toInt()==initialModelChanges;
                checks["static_hover_requires_no_controller_refresh"]=current["rowRefreshes"].toInt()==initialRowRefreshes;
            }
            auto highlight=named("domainosWindowHighlight"),box=named("domainosTestIconbox"),backend=named("domainosNativeTaskBackend");
            checks["compositor_highlight_default_is_off"]=box && !box->property("highlightWindows").toBool() && backend && !backend->property("highlightWindows").toBool();
            checks["text_hover_has_no_highlight_owner"]=highlight && highlight->property("currentRecord").isNull();
            if(highlight && box){
                box->setProperty("highlightWindows",true);
                auto first=current["members"].toArray()[0].toObject().toVariantMap(),second=current["members"].toArray()[1].toObject().toVariantMap();
                QMetaObject::invokeMethod(highlight,"enter",Qt::DirectConnection,Q_ARG(QVariant,QVariant(first)));
                checks["enabled_highlight_accepts_group_child_row"]=highlight->property("currentRecord").toMap()["key"]==first["key"];
                QMetaObject::invokeMethod(highlight,"enter",Qt::DirectConnection,Q_ARG(QVariant,QVariant(second)));
                QMetaObject::invokeMethod(highlight,"leave",Qt::DirectConnection,Q_ARG(QVariant,QVariant(first)));
                checks["late_first_title_exit_keeps_second_owner"]=highlight->property("currentRecord").toMap()["key"]==second["key"];
                QMetaObject::invokeMethod(highlight,"leave",Qt::DirectConnection,Q_ARG(QVariant,QVariant(second)));
                checks["leaving_current_title_clears_owner"]=highlight->property("currentRecord").isNull();
                box->setProperty("highlightWindows",false);
                checks["disabling_highlight_updates_native_backend"]=backend && !backend->property("highlightWindows").toBool();
            }
            // Exercise the production title HoverHandler with an actual pointer,
            // rather than treating direct manager calls as an input proof.
            if(box)box->setProperty("highlightWindows",true);
            auto point=memberPoint(named("domainosGroupMemberTitle_"+current["members"].toArray()[1].toObject()["key"].toString()));
            physical({"mousemove",QString::number(point.x()),QString::number(point.y())});phase=20;
        }
    }else if(phase==20){
        auto highlight=named("domainosWindowHighlight");
        const auto second=current["members"].toArray()[1].toObject()["key"].toString();
        checks["physical_second_title_hover_sets_highlight_owner"]=highlight && highlight->property("currentRecord").toMap()["key"].toString()==second;
        auto point=memberPoint(named("domainosGroupMemberTitle_"+current["members"].toArray()[0].toObject()["key"].toString()));
        physical({"mousemove",QString::number(point.x()),QString::number(point.y())});phase=21;
    }else if(phase==21){
        auto highlight=named("domainosWindowHighlight");
        checks["physical_next_title_hover_replaces_highlight_owner"]=highlight && highlight->property("currentRecord").toMap()["key"].toString()==current["members"].toArray()[0].toObject()["key"].toString();
        physical({"mousemove","1","1"});phase=22;
    }else if(phase==22){
        auto highlight=named("domainosWindowHighlight"),box=named("domainosTestIconbox");
        checks["physical_title_exit_clears_highlight_owner"]=highlight && highlight->property("currentRecord").isNull();
        if(box)box->setProperty("highlightWindows",false);
        QMetaObject::invokeMethod(fixture,"closePicker");phase=13;
    }else if(phase==13){openPicker();phase=14;}
    else if(phase==14){checks["sixteen_reopen"]=current["open"].toBool();layoutCheck(16);removeWindows(3);phase=15;}
    else if(phase==15){
        if(current["windows"].toArray().size()!=3 || current["members"].toArray().size()!=3){QTimer::singleShot(100,tick);return;}
        checks["live_shrink_to_three_keeps_picker_open"]=current["open"].toBool();layoutCheck(3);addWindows(15);phase=16;
    }else if(phase==16){
        if(current["windows"].toArray().size()!=15 || current["members"].toArray().size()!=15){QTimer::singleShot(100,tick);return;}
        checks["live_grow_to_fifteen_keeps_picker_open"]=current["open"].toBool();layoutCheck(15);addWindows(16);phase=17;
    }else if(phase==17){
        if(current["windows"].toArray().size()!=16 || current["members"].toArray().size()!=16){QTimer::singleShot(100,tick);return;}
        checks["live_grow_to_sixteen_keeps_picker_open"]=current["open"].toBool();layoutCheck(16);QMetaObject::invokeMethod(fixture,"closePicker");removeWindows(3);phase=23;
    }else if(phase==23){
        if(current["windows"].toArray().size()!=3){QTimer::singleShot(100,tick);return;}
        openPicker();phase=24;
    }else if(phase==24){
        checks["three_reopen_after_larger_native_surface"]=current["open"].toBool();layoutCheck(3);
        checks["no_window_operation_requested"]=current["requests"].toArray().isEmpty();checks["native_scenario_completed"]=true;complete();return;
    }
    QTimer::singleShot(200,tick);
}
extern "C" int interceptedExec() asm("_ZN12QApplication4execEv");
extern "C" int interceptedExec(){auto original=reinterpret_cast<int (*)()>(dlsym(RTLD_NEXT,"_ZN12QApplication4execEv"));if(!original)return 2;titleUpdates=qEnvironmentVariableIsEmpty("IRIX_DOMAINOS_GROUP_STATIC_HOVER");snapshots["title_updates_during_hover"]=titleUpdates;QGuiApplication::setDesktopFileName("org.irixclassic.qa.unity");addWindows(3);QTimer::singleShot(1200,tick);return original();}
