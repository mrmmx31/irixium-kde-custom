#!/usr/bin/env python3
# SPDX-FileCopyrightText: 2026 IRIX Classic contributors
# SPDX-License-Identifier: GPL-3.0-or-later
"""Physically click popup launchers twice in an owned Xephyr/KWin session.

Native production popups remain dismissible by their own launcher, Escape and
outside clicks. No power/device/task operation is dispatched; own SNI services
provide tray overflow. All GUI and D-Bus resources belong to this test.
"""
import argparse
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
QUADROS=REPO/"plasma/tools/testar-domainos-quadros.py"
BUTTONS={"clock":("domainosClock","domainosTimePopup"),"calendar":("domainosDate","domainosCalendarPopup"),
    "monitor":("domainosGraph","domainosMonitorPopup"),"applications":("domainosIdentity","domainosApplicationsPopup"),
    "pins":("domainosApplicationsDrawer","domainosApplicationsPopup"),"help":("domainosShortcut_help","domainosHelpMenu"),
    "session":("domainosShortcut_drawer","domainosSessionMenu"),"overflow":("domainosTrayNext","domainosTrayOverflowPopup"),
    "status":("domainosTrayExpand","domainosTrayStatusPopup")}
TOGGLE_PROBE=r'''
static QJsonObject toggleProbe(QObject *panel,Children children) {
    QJsonObject result;
    auto runtime=quadRuntime(panel);
    auto settings=runtime ? variantObject(runtime->property("settings")) : nullptr;
    result["__bar_hints_enabled"]=settings && settings->property("barHintsEnabled").toBool();
    auto iconbox=find(panel,children,QStringLiteral("domainosLiveIconbox"));
    result["__iconbox_last_error"]=iconbox ? iconbox->property("lastError").toString() : QString{};
    auto anchor=iconbox ? variantObject(iconbox->property("groupAnchor")) : nullptr;
    result["__group_anchor"]=anchor ? anchor->objectName() : QString{};
    QJsonArray taskPointers;
    auto tasks=runtime ? variantObject(runtime->property("tasks")) : nullptr;
    const auto rows=tasks ? menuVariant(tasks->property("taskRows")).toList() : QVariantList{};
    for(const auto &value:rows) {
        const auto row=menuVariant(value).toMap();
        auto button=find(panel,children,QStringLiteral("domainosLiveTask_")+row["key"].toString());
        auto preview=button ? variantObject(button->property("windowPreview")) : nullptr;
        auto hintLoader=preview ? preview->findChild<QObject *>(QStringLiteral("domainosWindowTitlesLoader")) : nullptr;
        taskPointers.append(QJsonObject{{"key",row["key"].toString()},
            {"button_found",button!=nullptr},{"preview_found",preview!=nullptr},
            {"pressed",button && button->property("pressed").toBool()},
            {"frozen_record",button ? QJsonValue::fromVariant(menuVariant(button->property("frozenRecord"))) : QJsonValue{}},
            {"preview_active",preview && preview->property("active").toBool()},
            {"preview_hints_enabled",preview && preview->property("hintsEnabled").toBool()},
            {"preview_hovered",preview && preview->property("containsMouse").toBool()},
            {"hint_loader_active",hintLoader && hintLoader->property("active").toBool()},
            {"hint_loader_visible",hintLoader && hintLoader->property("visible").toBool()}});
    }
    result["__task_pointers"]=taskPointers;
    for(const QString &name:{QStringLiteral("domainosTimePopup"),QStringLiteral("domainosCalendarPopup"),
        QStringLiteral("domainosMonitorPopup"),QStringLiteral("domainosApplicationsPopup"),
        QStringLiteral("domainosHelpMenu"),QStringLiteral("domainosSessionMenu"),
        QStringLiteral("domainosLocalHelpDialog"),QStringLiteral("domainosTrayOverflowPopup"),
        QStringLiteral("domainosTrayStatusPopup"),QStringLiteral("domainosGroupPicker"),QStringLiteral("domainosKdeApplicationsMenu")}) {
        auto popup=quadObject(panel,name);
        result[name]=popup ? QJsonValue(popup->property("visible").toBool()) : QJsonValue{};
    }
    return result;
}
'''
def quadros_module():
    spec=importlib.util.spec_from_file_location("domainos_toggle_quadros",QUADROS)
    module=importlib.util.module_from_spec(spec);spec.loader.exec_module(module);return module

def internal_launch(output,source):
    quad=quadros_module();menus=quad.menus_module()
    menus.PROBE=menus.PROBE.replace('name.startsWith("domainosShortcut_")',
        'name.startsWith("domainosShortcut_") || name=="domainosClock" || name=="domainosDate" || name=="domainosGraph" || name=="domainosIdentity" || name=="domainosApplicationsDrawer" || name=="domainosTrayNext" || name=="domainosTrayExpand"',1)
    quad.menus_module=lambda:menus
    quad.QUADROS_PROBE+=TOGGLE_PROBE
    quad.QUADROS_PROBE=quad.QUADROS_PROBE.replace('if(action=="prepare-group")',
        'if(action=="applications-style-kde") { auto settings=runtime ? variantObject(runtime->property("settings")) : nullptr; if(settings)settings->setProperty("applicationsMenuStyle",QStringLiteral("kde")); } else if(action=="hints-on") { auto settings=runtime ? variantObject(runtime->property("settings")) : nullptr; if(settings)settings->setProperty("barHintsEnabled",true); } else if(action=="prepare-group")',1)
    quad.QUADROS_PROBE=quad.QUADROS_PROBE.replace('static QJsonObject quadProbe(', 'static QJsonObject toggleProbe(QObject *panel,Children children);\nstatic QJsonObject quadProbe(',1)
    quad.QUADROS_PROBE=quad.QUADROS_PROBE.replace('result["popups"]=popups;','result["popups"]=popups;result["toggles"]=toggleProbe(panel,children);',1)
    return quad.internal_launch(output,source)

def private_test(output,source,baseline,hints_enabled=False):
    quad=quadros_module();menus=quad.menus_module();module=menus.wrapper_module();preview=output/"preview"
    checks={};samples=[];failure=None;launcher=None;manifest=None;children=[];sequence=0;last=None
    def command(*args):return subprocess.run(args,env=inner_env,check=True,capture_output=True,text=True,timeout=5).stdout.strip()
    def observe(action=None,**parameters):
        nonlocal sequence,last
        sequence+=1;request=dict(sequence=sequence,**parameters)
        if action:request["action"]=action
        token=json.dumps(request,separators=(",",":"));(preview/"preview-inspect-request").write_text(token)
        last=menus.wait_for(lambda:(data if (data:=menus.read_json(preview/"preview-observation.json")) and data.get("request_token")==token else None))
        return last
    def target(name):return next(item for item in observe()["menu_probe"]["targets"] if item["name"]==name)
    def click(name):
        item=target(name);command("xdotool","mousemove",str(item["x"]),str(item["y"]),"mousedown","1")
        pressed=observe();command("xdotool","mouseup","1");time.sleep(.12)
        return pressed,observe()
    def visible(name):return bool(observe()["quad_probe"]["toggles"].get(name))
    def close(name):
        command("xdotool","key","Escape");time.sleep(.08)
        if visible(name):observe("cancel",popup_name=name)
        menus.wait_for(lambda:not visible(name))
    try:
        args=[sys.executable,str(Path(__file__).resolve()),"--saida",str(preview),"--internal-launch"]
        if source:args.extend(("--source-panel",str(source)))
        launcher=subprocess.Popen(args,stdout=subprocess.PIPE,stderr=subprocess.STDOUT,text=True)
        stdout=launcher.communicate(timeout=45)[0];(output/"launcher.log").write_text(stdout)
        if launcher.returncode:raise RuntimeError("Private preview startup failed: "+stdout)
        manifest=menus.read_json(preview/"MANIFESTO.json");inner_env=module.private_environment(preview,manifest)
        inner_env.update(DISPLAY=manifest["display"],XAUTHORITY=str(preview/"Xauthority"))
        checks["owned_preview_bootstrap_passed"]=all(menus.read_json(preview/"RESULTADO.json")["checks"].values())
        initial=observe();desktop_before=initial["quad_probe"]["desktop_records"]
        inner_env["DBUS_SESSION_BUS_ADDRESS"]=initial["quad_probe"]["private_bus_address"]
        host=str(int(initial["menu_probe"]["host_id"]))
        command("xdotool","windowmove",host,"314","710")
        # A genuine native watcher and eight own SNIs make the ▶ route available.
        modules=Path("/usr/lib/x86_64-linux-gnu/qt6/plugins/kf6/kded")
        (preview/"config/kded6rc").write_text("\n".join("[Module-"+path.stem+"]\nautoload="+("true" if path.stem=="statusnotifierwatcher" else "false")+"\n" for path in modules.glob("*.so")))
        with (output/"kded.log").open("w") as log:
            daemon=subprocess.Popen(["kded6"],env=dict(inner_env,XDG_CURRENT_DESKTOP="KDE",KDE_FULL_SESSION="true",KDE_SESSION_VERSION="6"),stdout=log,stderr=subprocess.STDOUT)
        children.append(daemon)
        def watcher():
            probe=subprocess.run(["qdbus6","org.freedesktop.DBus","/org/freedesktop/DBus","org.freedesktop.DBus.GetConnectionUnixProcessID","org.kde.StatusNotifierWatcher"],env=inner_env,capture_output=True,text=True,timeout=3)
            return probe.returncode==0 and int(probe.stdout.strip())==daemon.pid
        menus.wait_for(watcher,10);checks["own_native_sni_watcher_pid"]=True
        with (output/"sni.log").open("w") as log:
            producer=subprocess.Popen([sys.executable,str(Path(__file__).resolve()),"--saida",str(output),"--sni-worker"],env=inner_env,stdout=log,stderr=subprocess.STDOUT)
        children.append(producer);menus.wait_for(lambda:menus.read_json(output/"SNI-READY.json"),10)
        menus.wait_for(lambda:len((observe()["quad_probe"].get("tray") or {}).get("overflow",[]))>0,12)
        checks["own_native_tray_overflow_available"]=True
        applications=preview/"data/applications";applications.mkdir(parents=True,exist_ok=True)
        (applications/"irxd-own-popup-group.desktop").write_text("[Desktop Entry]\nType=Application\nName=Own popup group\nExec=xterm\nIcon=utilities-terminal\nStartupWMClass=DomainOSPopupGroup\nTerminal=false\n")
        group_children=[]
        for index in range(2):
            with (output/("own-group-"+str(index)+".log")).open("w") as log:
                child=subprocess.Popen(["xterm","-class","DomainOSPopupGroup","-name","domainos-popup-group","-T","Own popup group "+str(index),"-geometry","20x5+100+220","-e","/bin/bash","--noprofile","--norc"],env=inner_env,stdout=log,stderr=subprocess.STDOUT)
            children.append(child);group_children.append(child)
        observe("prepare-group")
        def grouped():
            rows=observe()["quad_probe"]["task_rows"] or []
            return next((row for row in rows if row.get("group") and len(row.get("members",[]))==2 and {member["pid"] for member in row["members"]}=={child.pid for child in group_children}),None)
        group=menus.wait_for(grouped,12)
        checks["genuine_native_group_with_two_own_window_pids"]=len(group["members"])==2
        if hints_enabled:observe("hints-on")
        checks["bar_hints_match_requested_mode"]=observe()["quad_probe"]["toggles"].get("__bar_hints_enabled")==hints_enabled
        buttons={"group":("domainosLiveTask_"+group["key"],"domainosGroupPicker"),**BUTTONS,
            "applications_kde":("domainosIdentity","domainosKdeApplicationsMenu")}
        for kind,(button,popup) in buttons.items():
            if kind=="applications_kde":
                observe("applications-style-kde")
                menus.wait_for(lambda:observe()["quad_probe"]["toggles"].get(popup) is not None)
            hover_observation=None
            if hints_enabled:
                item=target(button);command("xdotool","mousemove",str(item["x"]),str(item["y"]))
                # This wait observes KDE's normal tooltip hover interval in the
                # harness only; no action/painting delay is added to production.
                time.sleep(1.1);hover_observation=observe()
            first_press,first=click(button)
            sample={"kind":kind,"button":button,"popup":popup,"hover_before_click":hover_observation,"first_press":first_press,"first":first}
            samples.append(sample);(output/"SAMPLES.json").write_text(json.dumps(samples,indent=2,ensure_ascii=False)+"\n")
            menus.wait_for(lambda:visible(popup))
            command("import","-window","root",str(output/(kind+"-open.png")))
            press,second=click(button);closed=not visible(popup)
            sample.update(second_press=press,second=second,second_click_closed=closed)
            (output/"SAMPLES.json").write_text(json.dumps(samples,indent=2,ensure_ascii=False)+"\n")
            if not closed:close(popup)
            _,third=click(button);menus.wait_for(lambda:visible(popup))
            sample["third_click_reopened"]=True
            command("xdotool","key","Escape");time.sleep(.12)
            sample["escape_closed"]=not visible(popup)
            if not sample["escape_closed"]:close(popup)
            _,again=click(button);menus.wait_for(lambda:visible(popup))
            command("xdotool","mousemove","1500","500","click","1");time.sleep(.15)
            sample["outside_click_closed"]=not visible(popup)
            if not sample["outside_click_closed"]:close(popup)
            (output/"SAMPLES.json").write_text(json.dumps(samples,indent=2,ensure_ascii=False)+"\n")
        if baseline:checks["baseline_reproduces_same_button_reopen_or_no_close"]=any(not item["second_click_closed"] for item in samples)
        else:
            checks["all_eleven_buttons_close_on_second_physical_click"]=len(samples)==11 and all(item["second_click_closed"] for item in samples)
            checks["all_eleven_buttons_reopen_on_third_click"]=all(item["third_click_reopened"] for item in samples)
            native_windows=[item for item in samples if item["kind"] in ("help","session","overflow","status","group","applications_kde")]
            checks["native_popup_windows_preserve_escape_dismissal"]=len(native_windows)==6 and all(item["escape_closed"] for item in native_windows)
            checks["native_popup_windows_preserve_outside_dismissal"]=len(native_windows)==6 and all(item["outside_click_closed"] for item in native_windows)
        checks["no_command_power_or_session_dispatch"]=all(sample[stage]["menu_probe"]["command_jobs"]=={} and sample[stage]["menu_probe"]["command_report"]=={} for sample in samples for stage in ("first","second_press","second"))
        checks["desktop_ids_unchanged"]=desktop_before==observe()["quad_probe"]["desktop_records"]
        checks["no_qml_errors"]=not module.ERRORS.search((preview/"panel.log").read_text())
    except Exception as error:
        failure=str(error);(output/"FAILED.json").write_text(json.dumps({"error":failure,"last":last},indent=2,ensure_ascii=False)+"\n")
    finally:
        for child in reversed(children):
            if child.poll() is None:child.terminate()
            try:child.wait(timeout=4)
            except subprocess.TimeoutExpired:child.kill();child.wait(timeout=4)
        checks["own_provider_processes_stopped"]=all(child.poll() is not None for child in children)
        calls=menus.read_json(output/"SNI-CALLS.json")
        if calls is not None:checks["no_sni_provider_actions"]=len(calls)==8 and all(not value for value in calls.values())
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
            checks["own_preview_stopped"]=closed["own_processes_stopped"] and not closed["owned_live_remaining"]
            checks["own_runtime_removed"]=closed["runtime_cleanup"]["removed"]
            checks["private_cleanup_preserved_hashes"]=closed["protected_hashes_unchanged"]
        if launcher and launcher.poll() is None:launcher.terminate();launcher.wait(timeout=5)
    result={"status":"passed" if not failure and all(checks.values()) else "failed","checks":checks,"error":failure,"samples":samples,"baseline":baseline,"hints_enabled":hints_enabled,
        "scope":"Actual production QML in owned Xvfb → Xephyr/KWin/D-Bus, native watcher and eight own SNIs. Physical press/release, second/third click, Escape and outside dismissal. No native task/device/power/session action; no personal profile installation."}
    (output/"RESULTADO.json").write_text(json.dumps(result,indent=2,ensure_ascii=False)+"\n")
    return 0 if result["status"]=="passed" else 1

def main():
    parser=argparse.ArgumentParser(description=__doc__);parser.add_argument("--saida",type=Path,required=True)
    parser.add_argument("--source-panel",type=Path);parser.add_argument("--baseline",action="store_true")
    parser.add_argument("--hints-enabled",action="store_true",help="Enable this fixture's bar hints and hover each launcher before its click")
    parser.add_argument("--internal-launch",action="store_true",help=argparse.SUPPRESS)
    parser.add_argument("--internal-test",action="store_true",help=argparse.SUPPRESS)
    parser.add_argument("--sni-worker",action="store_true",help=argparse.SUPPRESS)
    args=parser.parse_args();output=args.saida.resolve();source=args.source_panel.resolve() if args.source_panel else None
    if args.internal_launch:return internal_launch(output,source)
    if args.internal_test:return private_test(output,source,args.baseline,args.hints_enabled)
    if args.sni_worker:return quadros_module().sni_worker(output)
    if not output.is_relative_to(Path("/tmp")) or output==Path("/tmp") or output.exists():parser.error("Use a new directory under /tmp")
    if source and (not source.is_dir() or not source.is_relative_to(Path("/tmp"))):parser.error("Frozen baseline must exist under /tmp")
    menus=quadros_module().menus_module();module=menus.wrapper_module()
    before=module.protected_hashes([str(Path.home()/".config"/name) for name in ("kdeglobals","plasmarc","kwinrc","plasma-org.kde.plasma.desktop-appletsrc")])
    source_dir=source or REPO/"plasma/applets"/module.IDENTIFIER
    source_before=module.protected_hashes([str(path) for path in source_dir.rglob("*") if path.is_file()])
    output.mkdir(mode=0o700);env=os.environ.copy()
    for name in ("DISPLAY","WAYLAND_DISPLAY","DBUS_SESSION_BUS_ADDRESS","DBUS_STARTER_ADDRESS","DBUS_STARTER_BUS_TYPE","XAUTHORITY","LD_PRELOAD","SESSION_MANAGER","SSH_AUTH_SOCK","XDG_SESSION_ID","KDE_FULL_SESSION","KDE_SESSION_VERSION","QML_IMPORT_PATH","QML2_IMPORT_PATH","QT_STYLE_OVERRIDE","QT_QUICK_CONTROLS_STYLE"):env.pop(name,None)
    for key,folder in (("HOME","outer-home"),("XDG_CONFIG_HOME","outer-config"),("XDG_DATA_HOME","outer-data"),("XDG_CACHE_HOME","outer-cache"),("XDG_STATE_HOME","outer-state")):
        path=output/folder;path.mkdir(mode=0o700);env[key]=str(path)
    env.update(LC_ALL="C.UTF-8",LANG="C.UTF-8",XDG_CURRENT_DESKTOP="NONE",XDG_SESSION_TYPE="x11",QML_DISABLE_DISK_CACHE="1",DBUS_SYSTEM_BUS_ADDRESS="unix:path="+str(output/"no-system-bus"),PULSE_SERVER="unix:"+str(output/"no-audio"));env.pop("XDG_RUNTIME_DIR",None)
    arguments=["xvfb-run","--auto-servernum","--server-args=-screen 0 1700x1000x24",sys.executable,str(Path(__file__).resolve()),"--saida",str(output),"--internal-test"]
    if source:arguments.extend(("--source-panel",str(source)))
    if args.baseline:arguments.append("--baseline")
    if args.hints_enabled:arguments.append("--hints-enabled")
    run=subprocess.run(arguments,env=env,capture_output=True,text=True,timeout=180)
    (output/"test.log").write_text(run.stdout+run.stderr)
    result=menus.read_json(output/"RESULTADO.json") or {"status":"failed","checks":{},"error":"No report; see test.log"}
    result["checks"].update(real_profile_hashes_preserved=before==module.protected_hashes(before),test_source_unchanged=source_before==module.protected_hashes(source_before))
    result["status"]="passed" if run.returncode==0 and all(result["checks"].values()) else "failed";result["source_hashes"]=source_before
    (output/"RESULTADO.json").write_text(json.dumps(result,indent=2,ensure_ascii=False)+"\n")
    print(json.dumps({"status":result["status"],"checks":len(result["checks"]),"failed":[key for key,value in result["checks"].items() if not value],"error":result.get("error"),"samples":len(result.get("samples",[])),"report":str(output/"RESULTADO.json")},ensure_ascii=False))
    return 0 if result["status"]=="passed" else 1
if __name__=="__main__":raise SystemExit(main())
