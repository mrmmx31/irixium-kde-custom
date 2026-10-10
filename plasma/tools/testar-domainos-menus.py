#!/usr/bin/env python3
# SPDX-FileCopyrightText: 2026 IRIX Classic contributors
# SPDX-License-Identifier: GPL-3.0-or-later
"""Observe production native popups in an owned Xvfb -> Xephyr/KWin preview.

Physical clicks open Help/Session/Pager menus. Selection/basic task menus are
opened through their production API with private window records; no menu action
is triggered. The disposable host only reports window geometry/text/anchors.
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

sys.dont_write_bytecode = True
REPO = Path(__file__).resolve().parents[2]
WRAPPER = REPO / "plasma/tools/prever-domainos-funcional.py"

PROBE = r'''
static QVariant menuVariant(const QVariant &value) {
    if(QByteArray(value.metaType().name())=="QJSValue") {
        using Convert=QVariant (*)(const void *);
        auto convert=reinterpret_cast<Convert>(dlsym(RTLD_DEFAULT,"_ZNK8QJSValue9toVariantEv"));
        if(convert)return convert(value.constData());
    }
    return value;
}
static QJsonObject menuRect(const QRect &rectangle) {
    return {{"x",rectangle.x()},{"y",rectangle.y()},{"width",rectangle.width()},{"height",rectangle.height()}};
}
static void menuVisual(QObject *item,QWindow *window,Children children,QJsonArray &targets,QJsonArray &labels) {
    if(!item)return;
    const auto name=item->objectName();
    if((name.startsWith("domainosShortcut_") || name.startsWith("domainosDesktopTile_")
          || name.startsWith("domainosLiveTask_")) && item->property("visible").toBool()) {
        auto map=reinterpret_cast<MapToScene>(dlsym(RTLD_DEFAULT,"_ZNK10QQuickItem10mapToSceneERK7QPointF"));
        if(map) {
            auto scene=map(item,QPointF(item->property("width").toDouble()/2,item->property("height").toDouble()/2));
            auto global=window->mapToGlobal(scene.toPoint());
            targets.append(QJsonObject{{"name",name},{"x",global.x()},{"y",global.y()},
                {"enabled",item->property("enabled").toBool()},{"window_id",double(window->winId())}});
        }
    }
    const auto text=item->property("text").toString();
    if(!text.isEmpty() && item->property("visible").toBool() && item->inherits("QQuickText")) {
        auto map=reinterpret_cast<MapToScene>(dlsym(RTLD_DEFAULT,"_ZNK10QQuickItem10mapToSceneERK7QPointF"));
        auto local=map ? map(item,QPointF()) : QPointF{};
        auto global=window->mapToGlobal(local.toPoint());
        labels.append(QJsonObject{{"text",text},{"name",name},
            {"geometry",menuRect(QRect(global,QSize(qRound(item->property("width").toDouble()),qRound(item->property("height").toDouble()))))}});
    }
    if(item->inherits("QQuickItem"))for(auto child:children(item))menuVisual(child,window,children,targets,labels);
}
static void menuTestAction(QObject *panel,Children children,const QJsonObject &request) {
    const auto action=request["action"].toString();
    if(action.isEmpty())return;
    auto iconbox=find(panel,children,"domainosLiveIconbox");
    if(!iconbox)return;
    auto controller=variantObject(iconbox->property("controller"));
    const auto rows=controller ? menuVariant(controller->property("windowRows")).toList() : QVariantList{};
    if(action=="operations") {
        QMetaObject::invokeMethod(iconbox,"openOperations",Qt::DirectConnection,Q_ARG(QVariant,QVariant(rows)));
    } else if(action=="basic" && !rows.isEmpty()) {
        iconbox->setProperty("nativeMenusEnabled",false);
        auto anchor=find(panel,children,"domainosShortcut_help");
        QMetaObject::invokeMethod(iconbox,"openContext",Qt::DirectConnection,
            Q_ARG(QVariant,rows.first()),Q_ARG(QVariant,QVariant::fromValue(anchor)),Q_ARG(QVariant,QVariantMap{}));
    }
}
static QJsonObject menuProbe(QObject *panel,QWindow *host,Children children) {
    QJsonObject result;QJsonArray targets,windows;
    for(auto window:QGuiApplication::allWindows())if(window->isVisible()) {
        QJsonArray labels;
        menuVisual(window->property("contentItem").value<QObject *>(),window,children,targets,labels);
        windows.append(QJsonObject{{"id",double(window->winId())},{"class",window->metaObject()->className()},
            {"title",window->title()},{"geometry",menuRect(window->geometry())},
            {"frame_geometry",menuRect(window->frameGeometry())},
            {"available_geometry",window->screen() ? menuRect(window->screen()->availableGeometry()) : QJsonObject{}},
            {"labels",labels}});
    }
    result["targets"]=targets;result["windows"]=windows;
    result["host_id"]=host ? double(host->winId()) : 0;
    auto runtime=panel ? variantObject(panel->property("integration")) : nullptr;
    auto commands=runtime ? variantObject(runtime->property("commands")) : nullptr;
    result["command_jobs"]=commands ? QJsonValue::fromVariant(menuVariant(commands->property("jobs"))) : QJsonValue{};
    result["command_report"]=commands ? QJsonValue::fromVariant(menuVariant(commands->property("lastReport"))) : QJsonValue{};
    auto helpAnchor=commands ? variantObject(commands->property("helpAnchor")) : nullptr;
    auto helpDialog=runtime ? runtime->findChild<QObject *>(QStringLiteral("domainosLocalHelpDialog")) : nullptr;
    auto helpParent=helpDialog ? variantObject(helpDialog->property("parent")) : nullptr;
    result["help_anchor_name"]=helpAnchor ? helpAnchor->objectName() : QString{};
    result["local_help_parent_name"]=helpParent ? helpParent->objectName() : QString{};
    auto activity=runtime ? variantObject(runtime->property("activity")) : nullptr;
    result["activity_pending"]=activity ? activity->property("pendingCount").toInt() : -1;
    return result;
}
'''


def wrapper_module():
    spec = importlib.util.spec_from_file_location("domainos_menu_preview", WRAPPER)
    module = importlib.util.module_from_spec(spec); spec.loader.exec_module(module)
    return module


def read_json(path):
    try: return json.loads(path.read_text())
    except (FileNotFoundError, json.JSONDecodeError): return None


def wait_for(predicate, seconds=8):
    end=time.monotonic()+seconds
    while time.monotonic()<end:
        value=predicate()
        if value:return value
        time.sleep(.025)
    raise RuntimeError("Private native menu condition did not become true")


def internal_launch(output, source_panel):
    module=wrapper_module()
    original=module.shutil.copytree
    def copytree(source,destination,*args,**kwargs):
        source=Path(source);destination=Path(destination)
        if source_panel and source==REPO/"plasma/applets"/module.IDENTIFIER:source=source_panel
        # Icon dependencies are read-only shared inputs. Link them instead of
        # allocating another 28,000 inodes for each disposable menu proof.
        if source in (REPO/"icons/themes/IrixClassic-SGI",REPO/"icons/Irixium"):
            destination.parent.mkdir(parents=True,exist_ok=True)
            destination.symlink_to(source,target_is_directory=True)
            return str(destination)
        return original(source,destination,*args,**kwargs)
    module.shutil.copytree=copytree
    module.HOST_SOURCE=module.HOST_SOURCE.replace("#include <QApplication>","#include <QApplication>\n#include <QScreen>",1)
    module.HOST_SOURCE=module.HOST_SOURCE.replace("static QJsonObject captureState(",PROBE+"\nstatic QJsonObject captureState(",1)
    module.HOST_SOURCE=module.HOST_SOURCE.replace('state["preview_host_window_id"]=host ? double(host->winId()) : 0;',
        'state["preview_host_window_id"]=host ? double(host->winId()) : 0;\n    state["menu_probe"]=menuProbe(panel,host,children);',1)
    module.HOST_SOURCE=module.HOST_SOURCE.replace("auto state=captureState(observedPanel,configured,children);state[\"request_token\"]=token;",
        "menuTestAction(observedPanel,children,QJsonDocument::fromJson(token.toUtf8()).object());\n    auto state=captureState(observedPanel,configured,children);state[\"request_token\"]=token;",1)
    sys.argv=[str(WRAPPER),"--saida",str(output),"--titulo","DomainOS — menus nativos / prova isolada"]
    return module.main()


def contained(rectangle,available):
    return rectangle["width"]>0 and rectangle["height"]>0 and rectangle["x"]>=available["x"] and rectangle["y"]>=available["y"] and rectangle["x"]+rectangle["width"]<=available["x"]+available["width"] and rectangle["y"]+rectangle["height"]<=available["y"]+available["height"]


def private_test(output,source_panel,expect_clipping,extended=False):
    module=wrapper_module();preview=output/"preview"
    launcher=None;manifest=None;failure=None;checks={};samples=[];extras={};sequence=0
    def command(*arguments):
        return subprocess.run(arguments,env=inner_env,check=True,capture_output=True,text=True,timeout=5).stdout.strip()
    def observe(action=None):
        nonlocal sequence
        sequence+=1;request={"sequence":sequence}
        if action:request["action"]=action
        token=json.dumps(request,separators=(",",":"))
        (preview/"preview-inspect-request").write_text(token)
        result=wait_for(lambda:(data if (data:=read_json(preview/"preview-observation.json")) and data.get("request_token")==token else None))
        return result["menu_probe"]
    def native_popups(probe):
        return [window for window in probe["windows"] if "PopupWindow" in window["class"]]
    def close_menu():
        command("xdotool","key","Escape");time.sleep(.075)
        wait_for(lambda:not native_popups(observe()))
    def open_sample(position,menu,probe,action=None,keep_open=False):
        if action:observe(action)
        else:
            name={"help":"domainosShortcut_help","session":"domainosShortcut_drawer","pager":"domainosDesktopTile_0"}[menu]
            target=next((item for item in probe["targets"] if item["name"]==name),None)
            if not target:raise RuntimeError("Native anchor not found: "+name)
            button="3" if menu=="pager" else "1"
            command("xdotool","mousemove",str(target["x"]),str(target["y"]),"mousedown",button)
            time.sleep(.045);command("xdotool","mouseup",button)
        def laid_out():
            value=observe();windows=native_popups(value)
            if not windows:return None
            # A native popup can appear before ListView's polish pass: all
            # delegate labels initially overlap at row zero. Observe genuine
            # laid-out rows rather than accepting that transient tiny frame.
            return value if all(len(window["labels"])>=3 and len({label["geometry"]["y"] for label in window["labels"]})==len(window["labels"]) for window in windows) else None
        probe=wait_for(laid_out)
        windows=native_popups(probe)
        sample={"position":position,"menu":menu,"probe":probe,"popups":windows,
            "all_popups_within_available_screen":all(contained(window["geometry"],window["available_geometry"]) for window in windows),
            "all_labels_within_native_window_and_screen":all(contained(label["geometry"],window["geometry"]) and contained(label["geometry"],window["available_geometry"]) for window in windows for label in window["labels"])}
        samples.append(sample)
        (output/"MENU-SAMPLES.json").write_text(json.dumps(samples,indent=2,ensure_ascii=False)+"\n")
        command("import","-window","root",str(output/(position+"-"+menu+".png")))
        if not keep_open:close_menu()
        return sample
    try:
        arguments=[sys.executable,str(Path(__file__).resolve()),"--saida",str(preview),"--internal-launch"]
        if source_panel:arguments.extend(("--source-panel",str(source_panel)))
        launcher=subprocess.Popen(arguments,stdout=subprocess.PIPE,stderr=subprocess.STDOUT,text=True)
        stdout=launcher.communicate(timeout=45)[0];(output/"launcher.log").write_text(stdout)
        if launcher.returncode:raise RuntimeError("Private wrapper startup failed: "+stdout)
        manifest=read_json(preview/"MANIFESTO.json");inner_env=module.private_environment(preview,manifest)
        inner_env.update(DISPLAY=manifest["display"],XAUTHORITY=str(preview/"Xauthority"))
        startup=read_json(preview/"RESULTADO.json")
        checks["wrapper_startup_passed"]=all(startup["checks"].values())
        icon_inputs={"IrixClassic-SGI":REPO/"icons/themes/IrixClassic-SGI","Irixium":REPO/"icons/Irixium"}
        checks["two_public_icon_inputs_linked_read_only"]=all((preview/"data/icons"/name).is_symlink() and (preview/"data/icons"/name).resolve()==source.resolve() for name,source in icon_inputs.items())
        probe=observe();host=str(int(probe["host_id"]))
        for position,x,y in (("bottom",314,710),("top",314,0),("left",0,710),("right",629,710)):
            command("xdotool","windowmove",host,str(x),str(y));time.sleep(.1)
            for menu in ("help","session","pager"):
                open_sample(position,menu,observe())
            if not expect_clipping:
                open_sample(position,"operations",observe(),"operations")
                open_sample(position,"basic",observe(),"basic")
        checks["actual_help_session_and_pager_clicks"]=all(any(sample["position"]==position and sample["menu"]==menu for sample in samples) for position in ("bottom","top","left","right") for menu in ("help","session","pager"))
        checks["no_command_or_session_action_on_open"]=all(sample["probe"]["command_jobs"]=={} and sample["probe"]["command_report"]=={} for sample in samples)
        clipped=[sample for sample in samples if not sample["all_popups_within_available_screen"] or not sample["all_labels_within_native_window_and_screen"]]
        if expect_clipping:
            checks["baseline_reproduces_help_and_session_clipping"]=all(any(sample["position"]=="bottom" and sample["menu"]==menu and (not sample["all_popups_within_available_screen"] or not sample["all_labels_within_native_window_and_screen"]) for sample in samples) for menu in ("help","session"))
        else:
            checks["native_menu_dimensions_unscaled"]=all(sample["popups"][0]["geometry"]["height"]>=80 and sample["popups"][0]["geometry"]["width"]>=100 for sample in samples if sample["menu"] in ("help","session","pager"))
            checks["all_twenty_menu_placements_within_available_screen"]=len(samples)==20 and not clipped
            checks["production_operations_and_basic_api_opened"]=all(any(sample["position"]==position and sample["menu"]==menu for sample in samples) for position in ("bottom","top","left","right") for menu in ("operations","basic"))
        if extended and not expect_clipping:
            command("xdotool","windowmove",host,"314","710");time.sleep(.1)
            sample=open_sample("help-dialog","help",observe(),keep_open=True)
            label=next(label for label in sample["popups"][0]["labels"] if label["text"]=="Irix Classic DomainOS help")
            rectangle=label["geometry"]
            command("xdotool","mousemove",str(rectangle["x"]+rectangle["width"]//2),str(rectangle["y"]+rectangle["height"]//2),"click","1")
            def help_dialog():
                probe=observe();windows=native_popups(probe)
                return probe if any(any("The GNU/LINUX plate opens applications" in label["text"] for label in window["labels"]) for window in windows) else None
            probe=wait_for(help_dialog)
            # Test observation only: let the new native Dialog complete its
            # first render before taking the user-facing screen capture.
            time.sleep(.3);probe=observe()
            extras["local_help_dialog"]=probe
            checks["local_help_keeps_original_button_anchor"]=probe["help_anchor_name"]=="domainosShortcut_help" and probe["local_help_parent_name"]=="domainosShortcut_help"
            checks["local_help_dialog_within_screen"]=all(contained(window["geometry"],window["available_geometry"]) for window in native_popups(probe))
            checks["local_help_opens_without_command_dispatch"]=probe["command_jobs"]=={} and probe["command_report"]=={}
            command("import","-window","root",str(output/"HELP-DIALOG.png"));close_menu()
            command("xdotool","windowmove",host,"629","710");time.sleep(.1)
            sample=open_sample("right-submenu","basic",observe(),"basic",keep_open=True)
            label=next(label for label in sample["popups"][0]["labels"] if label["text"]=="Processo")
            rectangle=label["geometry"]
            command("xdotool","mousemove",str(rectangle["x"]+rectangle["width"]//2),str(rectangle["y"]+rectangle["height"]//2))
            def process_submenu():
                probe=observe();windows=native_popups(probe)
                return probe if len(windows)>=2 and any(any(label["text"]=="Encerrar à força" for label in window["labels"]) for window in windows) else None
            probe=wait_for(process_submenu)
            extras["process_submenu_right_edge"]=probe
            checks["process_submenu_and_labels_fit_right_edge"]=all(contained(window["geometry"],window["available_geometry"]) and all(contained(label["geometry"],window["geometry"]) and contained(label["geometry"],window["available_geometry"]) for label in window["labels"]) for window in native_popups(probe))
            checks["process_submenu_does_not_execute_action"]=probe["command_jobs"]=={} and probe["command_report"]=={}
            command("import","-window","root",str(output/"PROCESS-SUBMENU-RIGHT.png"))
            command("xdotool","key","Escape","Escape");wait_for(lambda:not native_popups(observe()))
        checks["no_qml_errors"]=not module.ERRORS.search((preview/"panel.log").read_text())
    except Exception as error:failure=str(error)
    finally:
        if manifest is None:manifest=read_json(preview/"MANIFESTO.json")
        processes=read_json(preview/"PROCESSOS.json")
        if manifest and processes:
            pid=processes["xephyr"]
            try:
                argv=Path("/proc",str(pid),"cmdline").read_bytes().split(b"\0")
                if Path(argv[0].decode()).name!="Xephyr" or manifest["display"].encode() not in argv:raise RuntimeError("Own Xephyr ownership mismatch")
                os.kill(pid,signal.SIGTERM)
            except FileNotFoundError:pass
            closed=wait_for(lambda:read_json(preview/"ENCERRADO.json"),12)
            checks["own_processes_stopped"]=closed["own_processes_stopped"] and not closed["owned_live_remaining"]
            checks["own_runtime_removed"]=closed["runtime_cleanup"]["removed"] and not Path(manifest["private_runtime"]["path"]).exists()
            checks["private_cleanup_hashes_preserved"]=closed["protected_hashes_unchanged"]
        if launcher and launcher.poll() is None:launcher.terminate();launcher.wait(timeout=5)
    result={"status":"passed" if not failure and all(checks.values()) else "failed","checks":checks,"error":failure,
        "samples":samples,"extra_observations":extras,"expected_clipping":expect_clipping,"source_panel":str(source_panel) if source_panel else "production",
        "scope":"Actual production wrapper in own Xvfb -> Xephyr/KWin/D-Bus. Help/Session/Pager physical clicks; task menus production open API only. Menu geometry/text observed through native QWindows. No action selected; no real user/session/system-bus changes."}
    (output/"RESULTADO.json").write_text(json.dumps(result,indent=2,ensure_ascii=False)+"\n")
    return 0 if result["status"]=="passed" else 1


def main():
    parser=argparse.ArgumentParser(description=__doc__);parser.add_argument("--saida",type=Path,required=True)
    parser.add_argument("--source-panel",type=Path,help="Optional frozen pre-fix package for baseline only")
    parser.add_argument("--expect-clipping",action="store_true",help="Require Help and Session bottom-edge bug reproduction")
    parser.add_argument("--extended",action="store_true",help="Also open/cancel local help and hover the Process submenu at the right monitor edge")
    parser.add_argument("--internal-launch",action="store_true",help=argparse.SUPPRESS)
    parser.add_argument("--internal-test",action="store_true",help=argparse.SUPPRESS)
    args=parser.parse_args();output=args.saida.resolve();source=args.source_panel.resolve() if args.source_panel else None
    if args.internal_launch:return internal_launch(output,source)
    if args.internal_test:return private_test(output,source,args.expect_clipping,args.extended)
    if not output.is_relative_to(Path("/tmp")) or output==Path("/tmp") or output.exists():parser.error("Use a new test directory under /tmp")
    if source and (not source.is_dir() or not source.is_relative_to(Path("/tmp"))):parser.error("Frozen baseline must be under /tmp")
    module=wrapper_module();protected=[str(Path.home()/".config"/name) for name in ("kdeglobals","plasmarc","kwinrc","plasma-org.kde.plasma.desktop-appletsrc")]
    before=module.protected_hashes(protected)
    icon_indexes=[str(REPO/"icons/themes/IrixClassic-SGI/index.theme"),str(REPO/"icons/Irixium/index.theme")]
    icon_indexes_before=module.protected_hashes(icon_indexes)
    source_dir=source or REPO/"plasma/applets"/module.IDENTIFIER
    source_before=module.protected_hashes([str(path) for path in source_dir.rglob("*") if path.is_file()])
    output.mkdir(mode=0o700);env=os.environ.copy()
    for name in ("DISPLAY","WAYLAND_DISPLAY","DBUS_SESSION_BUS_ADDRESS","DBUS_STARTER_ADDRESS","DBUS_STARTER_BUS_TYPE","XAUTHORITY","LD_PRELOAD","SESSION_MANAGER","SSH_AUTH_SOCK","XDG_SESSION_ID","KDE_FULL_SESSION","KDE_SESSION_VERSION","QML_IMPORT_PATH","QML2_IMPORT_PATH","QT_STYLE_OVERRIDE","QT_QUICK_CONTROLS_STYLE"):env.pop(name,None)
    for key,folder in (("HOME","outer-home"),("XDG_CONFIG_HOME","outer-config"),("XDG_DATA_HOME","outer-data"),("XDG_CACHE_HOME","outer-cache"),("XDG_STATE_HOME","outer-state")):
        path=output/folder;path.mkdir(mode=0o700);env[key]=str(path)
    env.update(LC_ALL="C.UTF-8",LANG="C.UTF-8",XDG_CURRENT_DESKTOP="NONE",XDG_SESSION_TYPE="x11",DBUS_SYSTEM_BUS_ADDRESS="unix:path="+str(output/"no-system-bus"),PULSE_SERVER="unix:"+str(output/"no-audio"))
    env.pop("XDG_RUNTIME_DIR",None)
    arguments=["xvfb-run","--auto-servernum","--server-args=-screen 0 1700x1000x24",sys.executable,str(Path(__file__).resolve()),"--saida",str(output),"--internal-test"]
    if source:arguments.extend(("--source-panel",str(source)))
    if args.expect_clipping:arguments.append("--expect-clipping")
    if args.extended:arguments.append("--extended")
    run=subprocess.run(arguments,env=env,capture_output=True,text=True,timeout=150)
    (output/"test.log").write_text(run.stdout+run.stderr)
    result=read_json(output/"RESULTADO.json") or {"status":"failed","checks":{},"error":"No result; see test.log"}
    result["checks"].update(real_profile_hashes_preserved=before==module.protected_hashes(before),test_source_unchanged=source_before==module.protected_hashes(source_before),two_read_only_icon_indexes_preserved=icon_indexes_before==module.protected_hashes(icon_indexes_before))
    result["status"]="passed" if run.returncode==0 and all(result["checks"].values()) else "failed"
    result["source_hashes"]=source_before
    result["read_only_icon_index_hashes"]=icon_indexes_before
    (output/"RESULTADO.json").write_text(json.dumps(result,indent=2,ensure_ascii=False)+"\n")
    print(json.dumps({"status":result["status"],"checks":len(result["checks"]),"failed":[key for key,value in result["checks"].items() if not value],"error":result.get("error"),"samples":len(result.get("samples",[])),"report":str(output/"RESULTADO.json")},ensure_ascii=False))
    return 0 if result["status"]=="passed" else 1


if __name__=="__main__":raise SystemExit(main())
