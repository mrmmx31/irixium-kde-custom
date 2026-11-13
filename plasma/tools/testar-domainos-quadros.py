#!/usr/bin/env python3
# SPDX-FileCopyrightText: 2026 IRIX Classic contributors
# SPDX-License-Identifier: GPL-3.0-or-later
"""Check seven production Popup.Window frames in an owned graphical preview.

The production preview entry point runs in own Xvfb -> Xephyr/KWin/D-Bus.
Two additional owned xterms form a genuine native TaskManager group; eight
private StatusNotifier services provide real native tray overflow. Dialogs are
only opened/cancelled. No desktop CRUD, power/session, device or audio action
is accepted. Geometry observation belongs only to the disposable native host.
"""
import argparse
import ast
import importlib.util
import json
import os
from pathlib import Path
import signal
import subprocess
import sys
import time

sys.dont_write_bytecode=True
REPO=Path(__file__).resolve().parents[2]
WRAPPER=REPO/"plasma/tools/prever-domainos-funcional.py"
MENUS=REPO/"plasma/tools/testar-domainos-menus.py"
NAMES={"failure":"domainosFailureDialog","help":"domainosLocalHelpDialog","group":"domainosGroupPicker",
       "overflow":"domainosTrayOverflowPopup","status":"domainosTrayStatusPopup",
       "name":"domainosDesktopNameDialog","remove":"domainosDesktopRemoveDialog"}

QUADROS_PROBE=r'''
static QObject *quadObject(QObject *panel,const QString &name) {
    if(!panel)return nullptr;
    if(panel->objectName()==name)return panel;
    return panel->findChild<QObject *>(name);
}
static QObject *quadRuntime(QObject *panel) {
    return panel ? variantObject(panel->property("integration")) : nullptr;
}
static QJsonObject quadProbe(QObject *panel,QWindow *host,Children children) {
    QJsonObject result;QJsonArray popups;
    using ItemWindow=QWindow *(*)(const QObject *);
    auto itemWindow=reinterpret_cast<ItemWindow>(dlsym(RTLD_DEFAULT,"_ZNK10QQuickItem6windowEv"));
    for(const QString &name:{QStringLiteral("domainosFailureDialog"),QStringLiteral("domainosLocalHelpDialog"),
           QStringLiteral("domainosGroupPicker"),QStringLiteral("domainosTrayOverflowPopup"),QStringLiteral("domainosTrayStatusPopup"),
           QStringLiteral("domainosDesktopNameDialog"),QStringLiteral("domainosDesktopRemoveDialog")}) {
        auto popup=quadObject(panel,name);
        if(!popup)continue;
        auto content=variantObject(popup->property("contentItem"));
        auto parent=variantObject(popup->property("parent"));
        auto window=content && itemWindow ? itemWindow(content) : nullptr;
        QJsonArray targets,labels;
        if(window && popup->property("visible").toBool())menuVisual(window->property("contentItem").value<QObject *>(),window,children,targets,labels);
        popups.append(QJsonObject{{"name",name},{"visible",popup->property("visible").toBool()},
            {"parent_name",parent ? parent->objectName() : QString{}},
            {"width",popup->property("width").toDouble()},{"height",popup->property("height").toDouble()},
            {"implicit_width",popup->property("implicitWidth").toDouble()},{"implicit_height",popup->property("implicitHeight").toDouble()},
            {"window_id",window ? double(window->winId()) : 0},
            {"window_class",window ? QString(window->metaObject()->className()) : QString{}},
            {"geometry",window ? menuRect(window->geometry()) : QJsonObject{}},
            {"available_geometry",window && window->screen() ? menuRect(window->screen()->availableGeometry()) : QJsonObject{}},
            {"labels",labels}});
    }
    result["popups"]=popups;
    auto runtime=quadRuntime(panel);
    auto tasks=runtime ? variantObject(runtime->property("tasks")) : nullptr;
    result["only_group_when_full"]=tasks ? tasks->property("onlyGroupWhenFull").toBool() : true;
    result["task_rows"]=tasks ? QJsonValue::fromVariant(menuVariant(tasks->property("taskRows"))) : QJsonValue{};
    result["window_rows"]=tasks ? QJsonValue::fromVariant(menuVariant(tasks->property("windowRows"))) : QJsonValue{};
    result["group_members"]=tasks ? QJsonValue::fromVariant(menuVariant(tasks->property("groupMembers"))) : QJsonValue{};
    auto tray=find(panel,children,"domainosRealTray");
    if(tray) {
        QVariant snapshot;
        QMetaObject::invokeMethod(tray,"snapshot",Qt::DirectConnection,Q_RETURN_ARG(QVariant,snapshot));
        result["tray"]=QJsonValue::fromVariant(menuVariant(snapshot));
    }
    auto pager=find(panel,children,"domainosRealPager");
    result["desktop_records"]=pager ? QJsonValue::fromVariant(menuVariant(pager->property("desktopRecords"))) : QJsonValue{};
    result["current_desktop_id"]=pager ? pager->property("currentDesktopId").toString() : QString{};
    result["host_geometry"]=host ? menuRect(host->geometry()) : QJsonObject{};
    result["private_bus_address"]=qEnvironmentVariable("DBUS_SESSION_BUS_ADDRESS");
    return result;
}
static void quadAction(QObject *panel,QWindow *host,Children children,const QJsonObject &request) {
    const auto action=request["action"].toString();if(action.isEmpty())return;
    auto runtime=quadRuntime(panel);
    if(action=="prepare-group") {
        auto tasks=runtime ? variantObject(runtime->property("tasks")) : nullptr;
        if(tasks)tasks->setProperty("onlyGroupWhenFull",false);
    } else if(action=="failure") {
        if(runtime)QMetaObject::invokeMethod(runtime,"showFailure",Qt::DirectConnection,Q_ARG(QVariant,QStringLiteral("Own popup geometry test; no operation failed or was dispatched.")));
    } else if(action=="group") {
        auto tasks=runtime ? variantObject(runtime->property("tasks")) : nullptr;
        if(tasks)QMetaObject::invokeMethod(tasks,"selectTask",Qt::DirectConnection,
            Q_ARG(QVariant,request["group_key"].toString()),Q_ARG(QVariant,0));
    } else if(action=="status" || action=="overflow") {
        if(auto tray=find(panel,children,"domainosRealTray"))QMetaObject::invokeMethod(tray,action=="status" ? "showStatus" : "showOverflow",Qt::DirectConnection);
    } else if(action=="name") {
        if(auto pager=find(panel,children,"domainosRealPager"))QMetaObject::invokeMethod(pager,"openNameDialog",Qt::DirectConnection,Q_ARG(QVariant,pager->property("currentDesktopId")));
    } else if(action=="remove") {
        if(auto popup=quadObject(panel,"domainosDesktopRemoveDialog"))QMetaObject::invokeMethod(popup,"open",Qt::DirectConnection);
    } else if(action=="cancel") {
        if(auto popup=quadObject(panel,request["popup_name"].toString()))QMetaObject::invokeMethod(popup,"close",Qt::DirectConnection);
    }
}
'''

POPUP_BOOTSTRAP='''def verify_preview_pager(app, output, state, host, reference):
    """Popup-only fixture bootstrap; does not test desktop switching."""
    checks={"native_initial_scope_has_three_owned_test_windows":len(state.get("preview_native_scope_rows",[]))==3,
        "native_pager_has_two_existing_ids":len(state.get("preview_pager_tiles",[]))==2,
        "owned_panel_running":host.poll() is None}
    for name,window_id,pid in (("panel",int(state["preview_host_window_id"]),host.pid),("reference",int(reference.winId()),os.getpid())):
        observed=subprocess.check_output(["xprop","-id",str(window_id),"_NET_WM_PID"],text=True).split("=",1)[-1].strip()
        checks["owned_"+name+"_x11_pid"]=observed==str(pid)
    checks["private_desktop_starts_at_first"]=subprocess.check_output(["xdotool","get_desktop"],text=True).strip()=="0"
    report={"status":"passed" if all(checks.values()) else "failed","checks":checks,
        "scope":"Disposable popup-only bootstrap. No desktop switches are made or claimed. Existing dedicated Pager proofs retain their separate scope."}
    write_json(output/"QUADROS-BOOTSTRAP.json",report)
    if report["status"]!="passed":raise RuntimeError("Private popup-only bootstrap failed")
    return report
'''


def menus_module():
    spec=importlib.util.spec_from_file_location("domainos_menu_probe",MENUS)
    module=importlib.util.module_from_spec(spec);spec.loader.exec_module(module);return module


def internal_launch(output,source):
    menus=menus_module()
    # Use a clearly recorded disposable entry-point copy to omit the unrelated
    # four-switch Pager self-test. Production wrapper/GUI sources stay intact.
    text=WRAPPER.read_text();tree=ast.parse(text)
    node=next(node for node in tree.body if isinstance(node,ast.FunctionDef) and node.name=="verify_preview_pager")
    lines=text.splitlines(keepends=True)
    text="".join(lines[:node.lineno-1])+POPUP_BOOTSTRAP+"\n"+"".join(lines[node.end_lineno:])
    text=text.replace("REPO = Path(__file__).resolve().parents[2]","REPO = Path("+repr(str(REPO))+")",1)
    text=text.replace('"private_preview_stays_visible_when_native_pager_switches"','"popup_only_bootstrap_ownership_ready"')
    text=text.replace('"pager_visibility_proof":str(output / "PAGER-VERIFICACAO.json")','"popup_bootstrap_proof":str(output / "QUADROS-BOOTSTRAP.json")')
    text=text.replace("The preview-owned panel/reference windows stay visible on both private desktops.","Popup-only fixture bootstrap; native desktop switching is not exercised by this directed test.")
    entry=output.parent/"popup-preview-entry.py";entry.write_text(text)
    spec=importlib.util.spec_from_file_location("domainos_popup_preview",entry)
    module=importlib.util.module_from_spec(spec);spec.loader.exec_module(module)
    if source:
        original=module.shutil.copytree
        def copytree(src,dest,*args,**kwargs):
            if Path(src)==REPO/"plasma/applets"/module.IDENTIFIER:src=source
            return original(src,dest,*args,**kwargs)
        module.shutil.copytree=copytree
    module.HOST_SOURCE=module.HOST_SOURCE.replace("#include <QApplication>","#include <QApplication>\n#include <QScreen>",1)
    # The disposable observer must see all three mapped preview xterms
    # before the wrapper starts switching desktops. Otherwise a late mapping
    # can land on desktop two during that unrelated startup self-test.
    module.HOST_SOURCE=module.HOST_SOURCE.replace('state["catalogCount"].toInt()==0)',
        'state["catalogCount"].toInt()==0 || state["preview_native_scope_rows"].toArray().size()<3)',1)
    module.HOST_SOURCE=module.HOST_SOURCE.replace("static QJsonObject captureState(",menus.PROBE+"\n"+QUADROS_PROBE+"\nstatic QJsonObject captureState(",1)
    module.HOST_SOURCE=module.HOST_SOURCE.replace('state["preview_host_window_id"]=host ? double(host->winId()) : 0;',
        'state["preview_host_window_id"]=host ? double(host->winId()) : 0;\n    state["menu_probe"]=menuProbe(panel,host,children);\n    state["quad_probe"]=quadProbe(panel,host,children);',1)
    module.HOST_SOURCE=module.HOST_SOURCE.replace('auto state=captureState(observedPanel,configured,children);state["request_token"]=token;',
        'static QString actedToken;\n    if(actedToken!=token) { actedToken=token;quadAction(observedPanel,configured,children,QJsonDocument::fromJson(token.toUtf8()).object()); }\n    auto state=captureState(observedPanel,configured,children);state["request_token"]=token;',1)
    sys.argv=[str(WRAPPER),"--saida",str(output),"--titulo","DomainOS — quadros nativos / prova isolada"]
    return module.main()


def sni_worker(output):
    from PyQt6.QtCore import QObject,pyqtClassInfo,pyqtProperty,pyqtSlot
    from PyQt6.QtDBus import QDBusConnection,QDBusInterface,QDBusObjectPath
    from PyQt6.QtWidgets import QApplication
    app=QApplication([]);bus=QDBusConnection.sessionBus()
    watcher=QDBusInterface("org.kde.StatusNotifierWatcher","/StatusNotifierWatcher","org.kde.StatusNotifierWatcher",bus)
    if not watcher.isValid():raise RuntimeError("Private native StatusNotifierWatcher unavailable")
    @pyqtClassInfo("D-Bus Interface","org.kde.StatusNotifierItem")
    class Item(QObject):
        def __init__(self,index):super().__init__();self.index=index;self.calls=[]
        @pyqtProperty(str)
        def Category(self):return "ApplicationStatus"
        @pyqtProperty(str)
        def Id(self):return "domainos-frame-own-sni-"+str(self.index)
        @pyqtProperty(str)
        def Title(self):return "Own popup native tray "+str(self.index)
        @pyqtProperty(str)
        def Status(self):return "Active"
        @pyqtProperty(str)
        def IconName(self):return "utilities-terminal"
        @pyqtProperty(str)
        def AttentionIconName(self):return ""
        @pyqtProperty(str)
        def OverlayIconName(self):return ""
        @pyqtProperty(str)
        def IconThemePath(self):return ""
        @pyqtProperty("uint")
        def WindowId(self):return 0
        @pyqtProperty(bool)
        def ItemIsMenu(self):return False
        @pyqtProperty(QDBusObjectPath)
        def Menu(self):return QDBusObjectPath("/NO_DBUSMENU")
        @pyqtSlot(int,int)
        def Activate(self,x,y):self.calls.append("activate")
        @pyqtSlot(int,int)
        def SecondaryActivate(self,x,y):self.calls.append("secondary")
        @pyqtSlot(int,int)
        def ContextMenu(self,x,y):self.calls.append("menu")
        @pyqtSlot(int,str)
        def Scroll(self,delta,orientation):self.calls.append("scroll")
        @pyqtSlot(str)
        def ProvideXdgActivationToken(self,token):pass
    connections=[];items=[];registrations=[]
    for index in range(8):
        connection=QDBusConnection.connectToBus(QDBusConnection.BusType.SessionBus,"frame-own-"+str(index))
        service="org.irixclassic.DomainOSFrameOwn.Item"+str(index)
        assert connection.registerService(service)
        item=Item(index)
        assert connection.registerObject("/StatusNotifierItem",item,QDBusConnection.RegisterOption.ExportAllSlots|QDBusConnection.RegisterOption.ExportAllProperties)
        reply=watcher.call("RegisterStatusNotifierItem",service)
        registrations.append({"service":service,"error":reply.errorMessage(),"reply_type":reply.type().value})
        connections.append(connection);items.append(item)
    (output/"SNI-READY.json").write_text(json.dumps({"pid":os.getpid(),"registrations":registrations})+"\n")
    running=True
    def stop(signum,frame):
        nonlocal running
        running=False
    signal.signal(signal.SIGTERM,stop);signal.signal(signal.SIGINT,stop)
    while running:app.processEvents();time.sleep(.01)
    (output/"SNI-CALLS.json").write_text(json.dumps({item.Id:item.calls for item in items},indent=2)+"\n")
    return 0


def private_test(output,source,baseline):
    menus=menus_module();module=menus.wrapper_module();preview=output/"preview"
    checks={};samples=[];failure=None;launcher=None;manifest=None;children=[];sequence=0;stage="launch-preview";last_observation=None
    def command(*args):return subprocess.run(args,env=inner_env,check=True,capture_output=True,text=True,timeout=5).stdout.strip()
    def observe(action=None,**parameters):
        nonlocal sequence,last_observation
        sequence+=1;request=dict(sequence=sequence,**parameters)
        if action:request["action"]=action
        token=json.dumps(request,separators=(",",":"));(preview/"preview-inspect-request").write_text(token)
        last_observation=menus.wait_for(lambda:(data if (data:=menus.read_json(preview/"preview-observation.json")) and data.get("request_token")==token else None))
        return last_observation
    def wait_stage(name,predicate,seconds=8):
        nonlocal stage
        stage=name
        try:return menus.wait_for(predicate,seconds)
        except RuntimeError as error:raise RuntimeError(name+": "+str(error)) from error
    def popup(data,kind):return next((item for item in data["quad_probe"]["popups"] if item["name"]==NAMES[kind] and item["visible"]),None)
    def cancel(kind):
        command("xdotool","key","Escape");time.sleep(.06)
        if popup(observe(),kind):observe("cancel",popup_name=NAMES[kind])
        menus.wait_for(lambda:not popup(observe(),kind))
    def physical_help():
        data=observe();target=next(item for item in data["menu_probe"]["targets"] if item["name"]=="domainosShortcut_help")
        command("xdotool","mousemove",str(target["x"]),str(target["y"]),"click","1")
        def help_menu():
            data=observe()
            for window in data["menu_probe"]["windows"]:
                if "PopupWindow" in window["class"]:
                    labels=window["labels"]
                    if len(labels)==3 and len({item["geometry"]["y"] for item in labels})==3:
                        label=next((item for item in labels if item["text"]=="Irix Classic DomainOS help"),None)
                        if label:return label
            return None
        label=menus.wait_for(help_menu);rectangle=label["geometry"]
        command("xdotool","mousemove",str(rectangle["x"]+rectangle["width"]//2),str(rectangle["y"]+rectangle["height"]//2),"click","1")
    try:
        arguments=[sys.executable,str(Path(__file__).resolve()),"--saida",str(preview),"--internal-launch"]
        if source:arguments.extend(("--source-panel",str(source)))
        launcher=subprocess.Popen(arguments,stdout=subprocess.PIPE,stderr=subprocess.STDOUT,text=True)
        stdout=launcher.communicate(timeout=45)[0];(output/"launcher.log").write_text(stdout)
        if launcher.returncode:raise RuntimeError("Own preview startup failed: "+stdout)
        manifest=menus.read_json(preview/"MANIFESTO.json");inner_env=module.private_environment(preview,manifest)
        inner_env.update(DISPLAY=manifest["display"],XAUTHORITY=str(preview/"Xauthority"))
        checks["popup_only_bootstrap_passed"]=all(menus.read_json(preview/"RESULTADO.json")["checks"].values())
        initial=observe();desktop_before=initial["quad_probe"]["desktop_records"]
        # The actual wrapper creates its bus inside dbus-run-session; the
        # external test driver must use that owned bus for its SNI producers.
        inner_env["DBUS_SESSION_BUS_ADDRESS"]=initial["quad_probe"]["private_bus_address"]
        if not inner_env["DBUS_SESSION_BUS_ADDRESS"].startswith("unix:"):raise RuntimeError("Own preview did not expose its private Unix bus")
        host=str(int(initial["menu_probe"]["host_id"]))
        applications=preview/"data/applications";applications.mkdir(parents=True,exist_ok=True)
        (applications/"irxd-own-popup-group.desktop").write_text("[Desktop Entry]\nType=Application\nName=Own popup group\nExec=xterm\nIcon=utilities-terminal\nStartupWMClass=DomainOSPopupGroup\nTerminal=false\n")
        for index in range(2):
            log=(output/("own-group-"+str(index)+".log")).open("w")
            child=subprocess.Popen(["xterm","-class","DomainOSPopupGroup","-name","domainos-popup-group","-T","Own popup group "+str(index),"-geometry","20x5+100+220","-e","/bin/bash","--noprofile","--norc"],env=inner_env,stdout=log,stderr=subprocess.STDOUT)
            children.append(child);log.close()
        observe("prepare-group")
        def grouped():
            data=observe();rows=data["quad_probe"]["task_rows"] or []
            return next((row for row in rows if row.get("group") and len(row.get("members",[]))==2 and {member["pid"] for member in row["members"]}=={child.pid for child in children}),None)
        group=wait_stage("real-native-group-two-owned-pids",grouped,12)
        checks["genuine_two_owned_windows_grouped_by_native_tasks"]=len(group["members"])==2
        for phase,kinds in (("core",[kind for kind in NAMES if kind not in ("overflow","status")]),("tray",["overflow","status"])):
            if phase=="tray":
                stage="native-kded-statusnotifierwatcher"
                modules=Path("/usr/lib/x86_64-linux-gnu/qt6/plugins/kf6/kded")
                (preview/"config/kded6rc").write_text("\n".join("[Module-"+path.stem+"]\nautoload="+("true" if path.stem=="statusnotifierwatcher" else "false")+"\n" for path in modules.glob("*.so")))
                log=(output/"kded.log").open("w")
                daemon_env=dict(inner_env,XDG_CURRENT_DESKTOP="KDE",KDE_FULL_SESSION="true",KDE_SESSION_VERSION="6")
                daemon=subprocess.Popen(["kded6"],env=daemon_env,stdout=log,stderr=subprocess.STDOUT)
                children.append(daemon);log.close()
                def watcher_owned():
                    if daemon.poll() is not None:raise RuntimeError("Own native kded process exited; see kded.log")
                    probe=subprocess.run(["qdbus6","org.freedesktop.DBus","/org/freedesktop/DBus","org.freedesktop.DBus.GetConnectionUnixProcessID","org.kde.StatusNotifierWatcher"],env=inner_env,capture_output=True,text=True,timeout=3)
                    if probe.returncode:return None
                    pid=int(probe.stdout.strip())
                    if pid!=daemon.pid:raise RuntimeError("Private SNI watcher owner is not the recorded native kded process")
                    return {"watcher_pid":pid,"own_kded_pid":daemon.pid,"native_module":"statusnotifierwatcher","other_kded_modules_autoload":False}
                watcher=wait_stage("native-watcher-owned-by-recorded-kded",watcher_owned,10)
                (output/"NATIVE-WATCHER.json").write_text(json.dumps(watcher)+"\n")
                checks["native_watcher_owner_is_own_kded_pid"]=watcher["watcher_pid"]==daemon.pid
                log=(output/"sni.log").open("w")
                producer=subprocess.Popen([sys.executable,str(Path(__file__).resolve()),"--saida",str(output),"--sni-worker"],env=inner_env,stdout=log,stderr=subprocess.STDOUT)
                children.append(producer);log.close()
                def sni_ready():
                    if producer.poll() is not None:raise RuntimeError("Own SNI producer exited; see sni.log")
                    return menus.read_json(output/"SNI-READY.json")
                wait_stage("eight-own-sni-registrations",sni_ready,10)
                def overflow_ready():
                    data=observe();tray=data["quad_probe"].get("tray") or {}
                    return tray if tray.get("available") and len(tray.get("visible",[]))>6 and len(tray.get("overflow",[]))>0 else None
                tray=wait_stage("native-visible-over-six-with-eight-own-sni",overflow_ready,12)
                checks["real_native_tray_overflow_from_own_sni_services"]=all("domainos-frame-own-sni-"+str(index) in tray["visible"] for index in range(8))
            for position,x,y in (("bottom",314,710),("top",314,0),("left",0,710),("right",629,710)):
                command("xdotool","windowmove",host,str(x),str(y));time.sleep(.1)
                for kind in kinds:
                    stage=position+"-"+kind
                    if kind=="help":physical_help()
                    else:observe(kind,group_key=group["key"])
                    wait_stage(position+"-"+kind+"-open",lambda:popup(observe(),kind))
                    time.sleep(.25);data=observe();item=popup(data,kind)
                    if not item:raise RuntimeError("Owned popup closed unexpectedly: "+kind)
                    sample={"position":position,"kind":kind,"popup":item,"quad_probe":data["quad_probe"],
                        "menu_probe":data["menu_probe"],"window_fits":menus.contained(item["geometry"],item["available_geometry"]),
                        "labels_fit":all(menus.contained(label["geometry"],item["geometry"]) and menus.contained(label["geometry"],item["available_geometry"]) for label in item["labels"])}
                    samples.append(sample);(output/"QUADROS-SAMPLES.json").write_text(json.dumps(samples,indent=2,ensure_ascii=False)+"\n")
                    command("import","-window","root",str(output/(position+"-"+kind+".png")))
                    cancel(kind)
        checks["seven_production_frames_opened_on_four_edges"]=len(samples)==28 and all(any(sample["kind"]==kind and sample["position"]==position for sample in samples) for kind in NAMES for position in ("bottom","top","left","right"))
        checks["all_popup_windows_native"]=all(sample["popup"]["window_class"]=="QQuickPopupWindow" for sample in samples)
        checks["desktop_crud_not_accepted"]=desktop_before==observe()["quad_probe"]["desktop_records"]
        checks["no_commands_or_session_operations_dispatched"]=all(sample["menu_probe"]["command_jobs"]=={} and sample["menu_probe"]["command_report"]=={} for sample in samples)
        checks["group_picker_contains_real_two_members"]=all(len(sample["quad_probe"]["group_members"])==2 for sample in samples if sample["kind"]=="group")
        clipped=[sample for sample in samples if not sample["window_fits"] or not sample["labels_fit"]]
        if baseline:checks["baseline_reproduces_clipped_production_popup_frames"]=bool(clipped)
        else:checks["all_twenty_eight_frames_and_labels_fit_screen"]=not clipped
        checks["no_qml_errors"]=not module.ERRORS.search((preview/"panel.log").read_text())
    except Exception as error:
        failure=str(error)
        (output/"FAILED-STAGE.json").write_text(json.dumps({"stage":stage,"error":failure,"last_observation":last_observation},indent=2,ensure_ascii=False)+"\n")
    finally:
        for child in reversed(children):
            if child.poll() is None:child.terminate()
            try:child.wait(timeout=4)
            except subprocess.TimeoutExpired:child.kill();child.wait(timeout=4)
        checks["own_provider_and_group_children_stopped"]=all(child.poll() is not None for child in children)
        calls=menus.read_json(output/"SNI-CALLS.json")
        if calls is not None:checks["no_sni_provider_actions_invoked"]=len(calls)==8 and all(not value for value in calls.values())
        if manifest is None:manifest=menus.read_json(preview/"MANIFESTO.json")
        processes=menus.read_json(preview/"PROCESSOS.json")
        if manifest and processes:
            pid=processes["xephyr"]
            try:
                argv=Path("/proc",str(pid),"cmdline").read_bytes().split(b"\0")
                if Path(argv[0].decode()).name!="Xephyr" or manifest["display"].encode() not in argv:raise RuntimeError("Own Xephyr ownership mismatch")
                os.kill(pid,signal.SIGTERM)
            except FileNotFoundError:pass
            closed=menus.wait_for(lambda:menus.read_json(preview/"ENCERRADO.json"),12)
            checks["own_preview_processes_stopped"]=closed["own_processes_stopped"] and not closed["owned_live_remaining"]
            checks["own_runtime_removed"]=closed["runtime_cleanup"]["removed"] and not Path(manifest["private_runtime"]["path"]).exists()
            checks["private_cleanup_hashes_preserved"]=closed["protected_hashes_unchanged"]
        if launcher and launcher.poll() is None:launcher.terminate();launcher.wait(timeout=5)
    result={"status":"passed" if not failure and all(checks.values()) else "failed","checks":checks,"error":failure,"samples":samples,
        "baseline":baseline,"source_panel":str(source) if source else "production",
        "clipped_by_kind":{kind:[sample["position"] for sample in samples if sample["kind"]==kind and (not sample["window_fits"] or not sample["labels_fit"])] for kind in NAMES},
        "scope":"Production preview GUI and seven Popup.Window components through a disposable entry-point copy with popup-only bootstrap (no Pager desktop-switch self-test). Own native xterm group, with transient controller-only grouping threshold disabled, and real own SNI services. APIs open/cancel only; local help physically clicked. No desktop CRUD accepted, no task/device/power/session action selected; real profiles not installed or altered."}
    (output/"RESULTADO.json").write_text(json.dumps(result,indent=2,ensure_ascii=False)+"\n")
    return 0 if result["status"]=="passed" else 1


def main():
    parser=argparse.ArgumentParser(description=__doc__);parser.add_argument("--saida",type=Path,required=True)
    parser.add_argument("--source-panel",type=Path,help="Frozen pre-fix source package under /tmp")
    parser.add_argument("--baseline",action="store_true",help="Require reproduction of clipped production popup frames")
    parser.add_argument("--internal-launch",action="store_true",help=argparse.SUPPRESS)
    parser.add_argument("--internal-test",action="store_true",help=argparse.SUPPRESS)
    parser.add_argument("--sni-worker",action="store_true",help=argparse.SUPPRESS)
    args=parser.parse_args();output=args.saida.resolve();source=args.source_panel.resolve() if args.source_panel else None
    if args.internal_launch:return internal_launch(output,source)
    if args.internal_test:return private_test(output,source,args.baseline)
    if args.sni_worker:return sni_worker(output)
    if not output.is_relative_to(Path("/tmp")) or output==Path("/tmp") or output.exists():parser.error("Use a new owned output directory under /tmp")
    if source and (not source.is_dir() or not source.is_relative_to(Path("/tmp"))):parser.error("Frozen source package must exist under /tmp")
    menus=menus_module();module=menus.wrapper_module();before=module.protected_hashes([str(Path.home()/".config"/name) for name in ("kdeglobals","plasmarc","kwinrc","plasma-org.kde.plasma.desktop-appletsrc")])
    source_dir=source or REPO/"plasma/applets"/module.IDENTIFIER
    source_before=module.protected_hashes([str(path) for path in source_dir.rglob("*") if path.is_file()])
    output.mkdir(mode=0o700);env=os.environ.copy()
    for name in ("DISPLAY","WAYLAND_DISPLAY","DBUS_SESSION_BUS_ADDRESS","DBUS_STARTER_ADDRESS","DBUS_STARTER_BUS_TYPE","XAUTHORITY","LD_PRELOAD","SESSION_MANAGER","SSH_AUTH_SOCK","XDG_SESSION_ID","KDE_FULL_SESSION","KDE_SESSION_VERSION","QML_IMPORT_PATH","QML2_IMPORT_PATH","QT_STYLE_OVERRIDE","QT_QUICK_CONTROLS_STYLE"):env.pop(name,None)
    for key,folder in (("HOME","outer-home"),("XDG_CONFIG_HOME","outer-config"),("XDG_DATA_HOME","outer-data"),("XDG_CACHE_HOME","outer-cache"),("XDG_STATE_HOME","outer-state")):
        path=output/folder;path.mkdir(mode=0o700);env[key]=str(path)
    env.update(LC_ALL="C.UTF-8",LANG="C.UTF-8",XDG_CURRENT_DESKTOP="NONE",XDG_SESSION_TYPE="x11",DBUS_SYSTEM_BUS_ADDRESS="unix:path="+str(output/"no-system-bus"),PULSE_SERVER="unix:"+str(output/"no-audio"));env.pop("XDG_RUNTIME_DIR",None)
    arguments=["xvfb-run","--auto-servernum","--server-args=-screen 0 1700x1000x24",sys.executable,str(Path(__file__).resolve()),"--saida",str(output),"--internal-test"]
    if source:arguments.extend(("--source-panel",str(source)))
    if args.baseline:arguments.append("--baseline")
    run=subprocess.run(arguments,env=env,capture_output=True,text=True,timeout=180)
    (output/"test.log").write_text(run.stdout+run.stderr)
    result=menus.read_json(output/"RESULTADO.json") or {"status":"failed","checks":{},"error":"No result; see test.log"}
    result["checks"].update(real_profile_hashes_preserved=before==module.protected_hashes(before),test_source_unchanged=source_before==module.protected_hashes(source_before))
    result["status"]="passed" if run.returncode==0 and all(result["checks"].values()) else "failed";result["source_hashes"]=source_before
    (output/"RESULTADO.json").write_text(json.dumps(result,indent=2,ensure_ascii=False)+"\n")
    print(json.dumps({"status":result["status"],"checks":len(result["checks"]),"failed":[key for key,value in result["checks"].items() if not value],"error":result.get("error"),"samples":len(result.get("samples",[])),"clipped_by_kind":result.get("clipped_by_kind"),"report":str(output/"RESULTADO.json")},ensure_ascii=False))
    return 0 if result["status"]=="passed" else 1


if __name__=="__main__":raise SystemExit(main())
