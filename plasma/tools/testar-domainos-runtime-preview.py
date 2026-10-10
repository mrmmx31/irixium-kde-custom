#!/usr/bin/env python3
# SPDX-FileCopyrightText: 2026 IRIX Classic contributors
# SPDX-License-Identifier: GPL-3.0-or-later
"""Directed long-output/runtime proof in own Xvfb -> Xephyr/KWin/D-Bus only.

Imports the real preview entry point. The private compiled host adds read-only
input coordinates/modal observations; production QML and its actions are real.
A test-owned Desktop Entry launches only a marker script in the private profile.
"""
import argparse
import importlib.util
import json
import os
from pathlib import Path
import signal
import stat
import subprocess
import sys
import time
from unittest.mock import patch

sys.dont_write_bytecode = True
REPO = Path(__file__).resolve().parents[2]
WRAPPER = REPO / "plasma/tools/prever-domainos-funcional.py"

PROBE = r'''
static void runtimeProbeTargets(QObject *item,QWindow *window,Children children,QJsonArray &targets) {
    if(!item)return;
    const QString name=item->objectName();
    const bool search=item->inherits("QQuickTextField") && !item->property("placeholderText").toString().isEmpty();
    if((name=="domainosIdentity" || name.startsWith("domainosApplicationEntry_") || search)
            && item->property("visible").toBool() && item->property("enabled").toBool()) {
        auto map=reinterpret_cast<MapToScene>(dlsym(RTLD_DEFAULT,"_ZNK10QQuickItem10mapToSceneERK7QPointF"));
        const QPointF local=map(item,QPointF(search ? item->property("width").toDouble()/2 : 30,item->property("height").toDouble()/2));
        const QPoint global=window->mapToGlobal(local.toPoint());
        if(QRect(QPoint(),window->size()).contains(local.toPoint()))targets.append(QJsonObject{
            {"name",search ? "catalog-search" : name},{"text",item->property("text").toString()},
            {"x",global.x()},{"y",global.y()},{"window_id",double(window->winId())},
            {"window_active",window->isActive()},{"window_exposed",window->isExposed()}});
    }
    if(item->inherits("QQuickItem"))for(auto child:children(item))runtimeProbeTargets(child,window,children,targets);
}
static QJsonObject runtimeProbe(QObject *panel,Children children) {
    QJsonObject result;QJsonArray targets;
    for(auto window:QGuiApplication::allWindows())if(window->isVisible())runtimeProbeTargets(window->property("contentItem").value<QObject *>(),window,children,targets);
    result["targets"]=targets;
    auto modal=QApplication::activeModalWidget();
    result["modal_present"]=modal!=nullptr;
    result["modal_title"]=modal ? modal->windowTitle() : QString{};
    auto runtime=panel ? variantObject(panel->property("integration")) : nullptr;
    auto apps=runtime ? variantObject(runtime->property("applications")) : nullptr;
    result["native_applications_controller"]=apps!=nullptr;
    result["popup_visible"]=apps && apps->property("popupVisible").toBool();
    result["search_text"]=apps ? apps->property("searchText").toString() : QString{};
    auto model=apps ? qobject_cast<QAbstractItemModel *>(variantObject(apps->property("filteredModel"))) : nullptr;
    QJsonArray rows;
    if(model) {
        const auto roles=model->roleNames();int favorite=-1,childrenRole=-1;
        for(auto it=roles.begin();it!=roles.end();++it) {
            if(it.value()=="favoriteId")favorite=it.key();
            if(it.value()=="hasChildren")childrenRole=it.key();
        }
        for(int row=0;row<model->rowCount();++row) {
            const auto index=model->index(row,0);
            rows.append(QJsonObject{{"row",row},{"title",model->data(index,Qt::DisplayRole).toString()},
                {"favorite_id",model->data(index,favorite).toString()},
                {"has_children",model->data(index,childrenRole).toBool()}});
        }
    }
    result["native_rows"]=rows;return result;
}
'''


def wrapper_module():
    spec = importlib.util.spec_from_file_location("domainos_preview", WRAPPER)
    module = importlib.util.module_from_spec(spec); spec.loader.exec_module(module)
    return module


def wait_for(predicate, seconds=8):
    deadline = time.monotonic() + seconds
    while time.monotonic() < deadline:
        value = predicate()
        if value: return value
        time.sleep(.025)
    raise RuntimeError("Directed private preview condition did not become true")


def read_json(path):
    try: return json.loads(path.read_text())
    except (FileNotFoundError, json.JSONDecodeError): return None


def test_runtime_guards(module, output):
    record = module.create_private_runtime(output)
    manifest = {"uid":os.getuid(), "private_runtime":record}
    runtime = Path(record["path"])
    checks = {"runtime_0700_current_uid":runtime.stat().st_uid == os.getuid() and stat.S_IMODE(runtime.stat().st_mode) == 0o700,
              "runtime_independent_of_long_output":runtime.parent == Path("/tmp") and len(str(runtime)) < 40 and not runtime.is_relative_to(output)}
    checks["cleanup_deferred_for_own_live_children"] = not module.cleanup_private_runtime(output, manifest, [123])["removed"] and runtime.exists()
    wrong = dict(manifest, private_runtime=dict(record, nonce="0"*32))
    checks["nonce_mismatch_preserves_runtime"] = not module.cleanup_private_runtime(output, wrong)["removed"] and runtime.exists()
    wrong = dict(manifest, private_runtime=dict(record, uid=os.getuid()+1))
    checks["other_uid_refused"] = not module.cleanup_private_runtime(output, wrong)["removed"] and runtime.exists()
    link = runtime.with_name(runtime.name + "-link"); link.symlink_to(runtime, target_is_directory=True)
    try:
        wrong = dict(manifest, private_runtime=dict(record, path=str(link)))
        checks["runtime_symlink_refused"] = not module.cleanup_private_runtime(output, wrong)["removed"] and runtime.exists()
    finally: link.unlink()
    with patch.object(module.os, "getuid", return_value=0), patch.object(module.os, "geteuid", return_value=0):
        try: module.preview_uid(); checks["root_refused"] = False
        except RuntimeError: checks["root_refused"] = True
    checks["own_runtime_removed"] = module.cleanup_private_runtime(output, manifest)["removed"] and not runtime.exists()
    checks["runtime_cleanup_idempotent"] = module.cleanup_private_runtime(output, manifest).get("already_missing") is True
    return checks


def internal_launch(output):
    module = wrapper_module()
    # Extend only the disposable observer compiled by the production wrapper.
    module.HOST_SOURCE = module.HOST_SOURCE.replace("#include <QApplication>", "#include <QApplication>\n#include <QWidget>", 1)
    module.HOST_SOURCE = module.HOST_SOURCE.replace("static QJsonObject captureState(", PROBE + "\nstatic QJsonObject captureState(", 1)
    module.HOST_SOURCE = module.HOST_SOURCE.replace("state[\"preview_host_window_id\"]=host ? double(host->winId()) : 0;",
        "state[\"preview_host_window_id\"]=host ? double(host->winId()) : 0;\n    state[\"runtime_probe\"]=runtimeProbe(panel,children);", 1)
    sys.argv = [str(WRAPPER), "--saida", str(output), "--titulo", "DomainOS — runtime curto / saída longa privada"]
    return module.main()


def private_test(output):
    module = wrapper_module(); checks = test_runtime_guards(module, output)
    long_output = output / ("saida-deliberadamente-longa-para-comprovar-isolamento-do-runtime-" + "x"*90)
    launcher = None; manifest = None; failure = None; observations = []; presses = []
    def command(*arguments):
        return subprocess.run(arguments, env=inner_env, check=True, capture_output=True, text=True, timeout=4).stdout.strip()
    sequence = 0
    def observe():
        nonlocal sequence
        sequence += 1; token = str(sequence)
        (long_output / "preview-inspect-request").write_text(token)
        value = wait_for(lambda:(data if (data:=read_json(long_output / "preview-observation.json")) and data.get("request_token")==token else None))
        observations.append(value["runtime_probe"])
        return value["runtime_probe"]
    def target(probe, name):
        return next((item for item in probe["targets"] if item["name"]==name), None)
    def click(item):
        if not item: raise RuntimeError("Owned native control not found")
        command("xdotool", "mousemove", str(item["x"]), str(item["y"]), "mousedown", "1")
        time.sleep(.06)
        held = observe(); current = target(held, item["name"])
        presses.append({"target":item["name"], "same_native_owner":bool(current) and current["window_id"]==item["window_id"],
                        "modal_present":held["modal_present"], "window_exposed":bool(current) and current["window_exposed"]})
        command("xdotool", "mouseup", "1")
        time.sleep(.1)
    try:
        launcher = subprocess.Popen([sys.executable, str(Path(__file__).resolve()), "--saida", str(long_output), "--internal-launch"], stdout=subprocess.PIPE, stderr=subprocess.STDOUT, text=True)
        wait_for(lambda:(long_output / "bus.conf").exists(), 20)
        applications = long_output / "data/applications"; applications.mkdir(parents=True, exist_ok=True)
        marker_script = long_output / "own-marker.py"; marker = long_output / "NATIVE-LAUNCH-MARKER.json"
        marker_script.write_text("import json,os\nfrom pathlib import Path\nPath("+repr(str(marker))+ ").write_text(json.dumps({'uid':os.getuid(),'home':os.environ.get('HOME'),'runtime':os.environ.get('XDG_RUNTIME_DIR'),'display':os.environ.get('DISPLAY')}))\n")
        quote = lambda value:'"'+str(value).replace('\\','\\\\').replace('"','\\"')+'"'
        (applications / "irxd-runtime-qa.desktop").write_text("[Desktop Entry]\nType=Application\nName=DomainOS Runtime Own Marker\nExec=/usr/bin/python3 "+quote(marker_script)+"\nIcon=utilities-terminal\nTerminal=false\nDBusActivatable=false\nCategories=Utility;\n")
        stdout = launcher.communicate(timeout=45)[0]; (output / "launcher.log").write_text(stdout)
        if launcher.returncode: raise RuntimeError("Long-output private preview failed startup: "+stdout)
        ready = read_json(long_output / "PRONTO.json"); manifest = read_json(long_output / "MANIFESTO.json")
        inner_env = module.private_environment(long_output, manifest)
        inner_env.update(DISPLAY=manifest["display"], XAUTHORITY=str(long_output / "Xauthority"))
        startup = read_json(long_output / "RESULTADO.json"); pager = read_json(long_output / "PAGER-VERIFICACAO.json")
        checks["long_output_exceeds_socket_limit"] = len(str(long_output / "runtime")) > 108
        checks["wrapper_startup_all_checks"] = all(startup["checks"].values())
        checks["pager_four_clicks_and_visibility"] = pager["status"]=="passed" and [item["requested_position"] for item in pager["clicks"]]==[1,0,1,0]
        checks["manifest_records_short_own_runtime"] = module.private_runtime(long_output,manifest).stat().st_uid==os.getuid() and len(manifest["private_runtime"]["path"])<40
        probe = observe(); checks["native_applications_controller_present"] = probe["native_applications_controller"]
        click(target(probe,"domainosIdentity")); probe = observe()
        checks["native_catalog_popup_opens"] = probe["popup_visible"] and not probe["modal_present"]
        all_apps = next((row for row in probe["native_rows"] if row["title"]=="All Applications" and row["has_children"]),None)
        if not all_apps: raise RuntimeError("Native All Applications category not found")
        click(target(probe,"domainosApplicationEntry_"+str(all_apps["row"]))); probe = observe()
        click(target(probe,"catalog-search"))
        command("xdotool", "key", "ctrl+a", "type", "DomainOS Runtime Own Marker")
        def filtered():
            value=observe()
            return value if len(value["native_rows"])==1 and value["native_rows"][0]["favorite_id"].endswith("irxd-runtime-qa.desktop") else None
        probe = wait_for(filtered, 8)
        checks["owned_entry_in_real_native_catalog"] = probe["native_rows"][0]["title"]=="DomainOS Runtime Own Marker"
        click(target(probe,"domainosApplicationEntry_0")); launched = wait_for(lambda:read_json(marker))
        checks["native_desktop_entry_launched_own_marker"] = launched=={"uid":os.getuid(),"home":str(long_output/"home"),"runtime":manifest["private_runtime"]["path"],"display":manifest["display"]}
        checks["native_controls_preserved_during_press_release"] = bool(presses) and all(item["same_native_owner"] and item["window_exposed"] and not item["modal_present"] for item in presses)
        checks["no_native_modal_observed"] = all(not item["modal_present"] for item in observations)
        command("import", "-window", "root", str(output / "NATIVE-CATALOG-AFTER.png"))
        panel_log = (long_output/"panel.log").read_text()
        checks["no_kio_socket_or_qml_error"] = not module.ERRORS.search(panel_log) and not any(text in panel_log for text in ("ConnectionServer::listenForRemote failed", "Can not create a socket for launching a KIO worker", "KIO Connection server not listening"))
    except Exception as error:
        failure = str(error)
    finally:
        if manifest is None: manifest=read_json(long_output/"MANIFESTO.json")
        processes=read_json(long_output/"PROCESSOS.json")
        if processes and manifest:
            pid=processes["xephyr"]
            try:
                argv=Path("/proc",str(pid),"cmdline").read_bytes().split(b"\0")
                if Path(argv[0].decode()).name != "Xephyr" or manifest["display"].encode() not in argv: raise RuntimeError("Own Xephyr ownership mismatch")
                os.kill(pid,signal.SIGTERM)
            except FileNotFoundError: pass
            closed=wait_for(lambda:read_json(long_output/"ENCERRADO.json"),12)
            checks["own_preview_processes_stopped"] = closed["own_processes_stopped"] and not closed["owned_live_remaining"]
            checks["own_short_runtime_removed_after_processes"] = closed["runtime_cleanup"]["removed"] and not Path(manifest["private_runtime"]["path"]).exists()
            checks["cleanup_hashes_preserved"] = closed["protected_hashes_unchanged"]
        if launcher and launcher.poll() is None: launcher.terminate(); launcher.wait(timeout=5)
    result={"status":"passed" if not failure and all(checks.values()) else "failed", "checks":checks,"error":failure,
            "output":str(long_output), "runtime":manifest.get("private_runtime") if manifest else None,
            "native_observations":observations,"press_intervals":presses,
            "scope":"Own Xvfb -> Xephyr/KWin/D-Bus, actual production QML; read-only disposable observer extension and own Desktop Entry marker. No user session/accounts/global settings. Socket suffix length is inferred from the installed binary; no failing socket path is claimed captured."}
    (output/"RESULTADO.json").write_text(json.dumps(result,indent=2,ensure_ascii=False)+"\n")
    return 0 if result["status"]=="passed" else 1


def main():
    parser=argparse.ArgumentParser(description=__doc__); parser.add_argument("--saida",type=Path,required=True)
    parser.add_argument("--internal-launch",action="store_true",help=argparse.SUPPRESS)
    parser.add_argument("--internal-test",action="store_true",help=argparse.SUPPRESS)
    args=parser.parse_args(); output=args.saida.resolve()
    if args.internal_launch: return internal_launch(output)
    if args.internal_test: return private_test(output)
    if not output.is_relative_to(Path("/tmp")) or output==Path("/tmp") or output.exists(): parser.error("Use a new test directory under /tmp")
    module=wrapper_module(); before=module.protected_hashes([str(Path.home()/".config"/name) for name in ("kdeglobals","plasmarc","kwinrc","plasma-org.kde.plasma.desktop-appletsrc")])
    wrapper_before=module.protected_hashes([str(WRAPPER)])
    production=[str(path) for path in (REPO/"plasma/applets/org.irixclassic.domainos.panel").rglob("*") if path.is_file()]
    production_before=module.protected_hashes(production)
    output.mkdir(mode=0o700); env=os.environ.copy()
    for name in ("DISPLAY","WAYLAND_DISPLAY","DBUS_SESSION_BUS_ADDRESS","DBUS_STARTER_ADDRESS","DBUS_STARTER_BUS_TYPE","XAUTHORITY","LD_PRELOAD","SESSION_MANAGER","SSH_AUTH_SOCK","XDG_SESSION_ID","KDE_FULL_SESSION","KDE_SESSION_VERSION","QML_IMPORT_PATH","QML2_IMPORT_PATH","QT_STYLE_OVERRIDE","QT_QUICK_CONTROLS_STYLE"): env.pop(name,None)
    for key,folder in (("HOME","outer-home"),("XDG_CONFIG_HOME","outer-config"),("XDG_DATA_HOME","outer-data"),("XDG_CACHE_HOME","outer-cache"),("XDG_STATE_HOME","outer-state")):
        path=output/folder;path.mkdir(mode=0o700);env[key]=str(path)
    env.update(LC_ALL="C.UTF-8",LANG="C.UTF-8",XDG_CURRENT_DESKTOP="NONE",XDG_SESSION_TYPE="x11",DBUS_SYSTEM_BUS_ADDRESS="unix:path="+str(output/"no-system-bus"),PULSE_SERVER="unix:"+str(output/"no-audio"))
    env.pop("XDG_RUNTIME_DIR",None)
    run=subprocess.run(["xvfb-run","--auto-servernum","--server-args=-screen 0 1700x1000x24",sys.executable,str(Path(__file__).resolve()),"--saida",str(output),"--internal-test"],env=env,capture_output=True,text=True,timeout=100)
    (output/"test.log").write_text(run.stdout+run.stderr)
    result=read_json(output/"RESULTADO.json") or {"status":"failed","checks":{},"error":"No private test result; see test.log"}
    result["checks"].update(real_profile_hashes_preserved=before==module.protected_hashes(before),
        wrapper_unchanged_during_test=wrapper_before==module.protected_hashes(wrapper_before),
        production_qml_unchanged=production_before==module.protected_hashes(production_before))
    result["status"]="passed" if run.returncode==0 and all(result["checks"].values()) else "failed"
    result["wrapper_sha256"]=wrapper_before[str(WRAPPER)]
    (output/"RESULTADO.json").write_text(json.dumps(result,indent=2,ensure_ascii=False)+"\n")
    print(json.dumps({"status":result["status"],"checks":len(result["checks"]),"failed":[key for key,value in result["checks"].items() if not value],"error":result.get("error"),"report":str(output/"RESULTADO.json")},ensure_ascii=False))
    return 0 if result["status"]=="passed" else 1


if __name__=="__main__":raise SystemExit(main())
