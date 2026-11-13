#!/usr/bin/env python3
# SPDX-FileCopyrightText: 2026 mrmmx31
# SPDX-License-Identifier: GPL-3.0-or-later
"""Test native Kicker catalog and instance-owned pins in private Plasma/Xvfb.

A Desktop Entry created in the disposable data directory launches a marker-only
script under /tmp. Real applications, favorites, tasks, account files, desktop
settings and the user's current D-Bus are never modified or activated.
"""
import argparse
import hashlib
import json
import os
from pathlib import Path
import shlex
import shutil
import subprocess
import sys
import tempfile
import time

sys.dont_write_bytecode=True
REPO=Path(__file__).resolve().parents[2]
IDENTIFIER="org.irixclassic.domainos.applications.test"
FIRST="irix-domainos-qa-first.desktop"
SECOND="irix-domainos-qa-second.desktop"


def digest(path):
    return hashlib.sha256(path.read_bytes()).hexdigest() if path.is_file() else None


def session(output):
    if os.environ.get("IRIX_DOMAINOS_APPLICATIONS_PRIVATE_SESSION") != "1":
        raise RuntimeError("Internal test needs a private session")
    processes,logs=[],[]
    try:
        if os.environ.get("IRIX_DOMAINOS_APPLICATIONS_DIAGNOSTIC_NO_WM")!="1":
            wm_log=(output/"kwin.log").open("w");logs.append(wm_log)
            processes.append(subprocess.Popen(["kwin_x11"],stdout=wm_log,stderr=subprocess.STDOUT))
            for _ in range(80):
                if subprocess.run(["qdbus6","org.kde.KWin","/VirtualDesktopManager"],capture_output=True,timeout=2).returncode==0:break
                time.sleep(.05)
            else:raise RuntimeError("Private KWin did not become ready")
        log=(output/"activitymanager.log").open("w");logs.append(log)
        processes.append(subprocess.Popen(["/usr/lib/x86_64-linux-gnu/libexec/kactivitymanagerd"],stdout=log,stderr=subprocess.STDOUT))
        environment=dict(os.environ,LD_PRELOAD=str(output/"applications-host.so"),
            IRIX_DOMAINOS_APPLICATIONS_TEST="1",IRIX_DOMAINOS_APPLICATIONS_REPORT=str(output/"native.json"),
            IRIX_DOMAINOS_APPLICATIONS_DIR=str(output))
        result=subprocess.run(["plasmawindowed",IDENTIFIER],env=environment,stdout=subprocess.PIPE,stderr=subprocess.STDOUT,text=True,timeout=25)
        (output/"host.log").write_text(result.stdout)
        return result.returncode
    finally:
        for daemon in reversed(processes):
            if daemon.poll() is None:
                daemon.terminate()
                try:daemon.wait(timeout=3)
                except subprocess.TimeoutExpired:daemon.kill();daemon.wait(timeout=3)
        (output/"cleanup.json").write_text(json.dumps({"own_daemons_exited":all(p.poll() is not None for p in processes),"own_pids":[p.pid for p in processes]})+"\n")
        for log in logs:log.close()


def main():
    parser=argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--saida",type=Path,required=True,help="New directory under /tmp")
    parser.add_argument("--atividade",action="store_true",help="Directed native catalog/context dispatch and activity-light proof")
    parser.add_argument("--sem-wm-diagnostico",action="store_true",help="Private diagnostic only; omit the window manager to observe a failed input sequence")
    parser.add_argument("--internal-session",action="store_true",help=argparse.SUPPRESS)
    args=parser.parse_args(); output=args.saida.absolute()
    if args.internal_session:return session(output)
    if not output.is_relative_to(Path("/tmp")) or output.exists():parser.error("Use a new output directory under /tmp")
    output.mkdir(mode=0o700)
    source=REPO/"plasma/applets/org.irixclassic.domainos.panel/contents/ui/DomainOSApplications.qml"
    sources=[source,source.with_name("DomainOSApplicationMenu.qml"),source.parent.parent/"code/ApplicationActions.js"]
    before={str(path):digest(path) for path in sources}
    protected=[Path.home()/".config"/name for name in ("kdeglobals","plasmarc","kwinrc","plasma-org.kde.plasma.desktop-appletsrc")]
    config_before={str(path):digest(path) for path in protected}
    paths={key:output/name for key,name in (("HOME","home"),("XDG_CONFIG_HOME","config"),("XDG_DATA_HOME","data"),
        ("XDG_CACHE_HOME","cache"),("XDG_STATE_HOME","state"),("XDG_RUNTIME_DIR","runtime"))}
    # KIO creates Unix sockets below this path. Long report-directory names
    # exhausted the socket address length and opened a modal Error dialog.
    # Keep only the disposable runtime short; all durable evidence stays here.
    private_runtime=tempfile.TemporaryDirectory(prefix="ird-app-",dir="/tmp")
    paths["XDG_RUNTIME_DIR"]=Path(private_runtime.name)
    for path in paths.values():path.mkdir(mode=0o700,exist_ok=True)
    plasmoids=paths["XDG_DATA_HOME"]/"plasma/plasmoids";plasmoids.mkdir(parents=True)
    shutil.copytree(REPO/"plasma/applets/org.irixclassic.domainos.panel",plasmoids/"org.irixclassic.domainos.panel",ignore=shutil.ignore_patterns("__pycache__","*.pyc"))
    fixture=plasmoids/IDENTIFIER;(fixture/"contents/ui").mkdir(parents=True)
    (fixture/"metadata.json").write_text(json.dumps({"KPlugin":{"Id":IDENTIFIER,"Name":"DomainOS applications private test","Version":"1.0","License":"GPL-3.0-or-later"},"KPackageStructure":"Plasma/Applet","X-Plasma-API-Minimum-Version":"6.0"}))
    (fixture/"contents/ui/main.qml").write_text('''import QtQuick
import QtQuick.Layouts
import org.kde.plasma.plasmoid
import org.kde.plasma.core as PlasmaCore
import org.kde.taskmanager as TaskManager
import "../../../org.irixclassic.domainos.panel/contents/ui" as Panel
PlasmoidItem {
    id: host
    preferredRepresentation: fullRepresentation
    Plasmoid.backgroundHints: PlasmaCore.Types.NoBackground
    fullRepresentation: Item {
        id: fixture
        objectName:"domainosApplicationsTestFixture"
        implicitWidth:500;implicitHeight:100
        Layout.minimumWidth:500;Layout.minimumHeight:100
        property int scenario:0
        property var leafPath:[]
        property var pinRequests:[]
        property var applicationRequests:[]
        property var boundsResults:[]
        property bool unavailableLaunchResult:false
        property int configureRequests:0
        property int searchSourceCount:-1
        property int activityScenario:0
        property int categoryRow:-1
        property var nativeReports:[]
        property var nativeBegins:[]
        property var nativeFinishes:[]
        property bool exceptionDispatchResult:true
        property bool falseDispatchResult:true
        readonly property alias activityTracker:nativeActivity
        readonly property alias controller:apps
        property string snapshotJson:JSON.stringify({pins:apps.pins,
            pinRequests:pinRequests,applicationRequests:applicationRequests,
            boundsResults:boundsResults,unavailableLaunchResult:unavailableLaunchResult,
            pinInfo:apps.pins.map((id,index)=>{const info=apps.pinInfo(index);return {desktopId:info.desktopId,title:info.title,available:info.available}}),
            popupVisible:apps.popupVisible,drawer:apps.drawer,
            configureRequests:configureRequests,
            search:apps.searchText,filteredCount:apps.filteredModel.rowCount(),
            searchSourceCount:searchSourceCount,
            favoritesCount:apps.catalogModel.favoritesModel.count,
            peerFavoritesCount:peerApps.catalogModel.favoritesModel.count,
            showingFavorites:apps.currentModel===apps.catalogModel.favoritesModel,
            navigationDepth:apps.navigation.length,
            activity:{pending:nativeActivity.pendingCount,lit:nativeActivity.lit,tail:nativeActivity.tailLit,
                sequence:nativeActivity.sequence,keep:nativeActivity.keepLightAfterCompletion,
                reports:nativeReports,begins:nativeBegins,finishes:nativeFinishes},
            exceptionDispatchResult:exceptionDispatchResult,falseDispatchResult:falseDispatchResult,
            tasksCount:tasks.count,taskLaunchers:tasks.launcherList})
        QtObject {id:fixtureSettings;property var pinnedApplications:[]}
        Panel.DomainOSActivity {id:nativeActivity;extraLightMilliseconds:700}
        QtObject {
            id:fixtureCommands
            function openApplication(desktopId){fixture.applicationRequests=fixture.applicationRequests.concat([desktopId]);return true}
            function begin(label){
                const token=nativeActivity.begin(label)
                fixture.nativeBegins=fixture.nativeBegins.concat([{token:token,pending:nativeActivity.pendingCount,lit:nativeActivity.lit}])
                return token
            }
            function finish(token,report){
                nativeActivity.finish(token,report)
                fixture.nativeReports=fixture.nativeReports.concat([report])
                fixture.nativeFinishes=fixture.nativeFinishes.concat([{token:token,pending:nativeActivity.pendingCount,lit:nativeActivity.lit,tail:nativeActivity.tailLit}])
            }
        }
        TaskManager.TasksModel {id:tasks}
        Panel.DomainOSApplications {
            id:apps;hostItem:host;settings:fixtureSettings;commands:fixtureCommands
            favoritesClient:"org.irixclassic.domainos.private-qa"
            onPinListRequested:pins=>{fixture.pinRequests=fixture.pinRequests.concat([pins.slice()]);fixtureSettings.pinnedApplications=pins.slice()}
            onConfigureRequested:fixture.configureRequests++
        }
        Panel.DomainOSApplications {
            id:peerApps;hostItem:host;settings:fixtureSettings;commands:fixtureCommands
            favoritesClient:"org.irixclassic.domainos.private-qa-peer"
        }
        Rectangle {anchors.fill:parent;color:"#7894a7"}
        Text {anchors.centerIn:parent;text:"Real Kicker catalog and private pins"}
        Item {id:anchor;x:120;y:20;width:100;height:40}
        function prepareLeaf(){
            apps.close();apps.showMenu(anchor)
            let model=apps.catalogModel
            for(let i=0;i<leafPath.length-1;i++)model=model.modelForRow(leafPath[i])
            apps.currentModel=model;apps.searchText="DomainOS QA NeedleZ First"
        }
        onActivityScenarioChanged:{
            if(activityScenario===1)apps.showMenu(anchor)
            else if(activityScenario===2)prepareLeaf()
            else if(activityScenario===3){nativeActivity.keepLightAfterCompletion=true;prepareLeaf()}
            else if(activityScenario===4){apps.close();apps.showMenu(anchor);apps.showFavorites()}
            else if(activityScenario===6)prepareLeaf()
            else if(activityScenario===7){nativeActivity.keepLightAfterCompletion=false;prepareLeaf()}
            else if(activityScenario===8)prepareLeaf()
            else if(activityScenario===9){
                exceptionDispatchResult=apps.dispatchNative({trigger:function(){throw new Error("Owned dispatcher exception")}},0,"owned-exception",null)
            }else if(activityScenario===10){
                falseDispatchResult=apps.dispatchNative({trigger:function(){return false}},0,"owned-false-policy",null)
            }
        }
        onScenarioChanged:{
            if(scenario===1){
                apps.showMenu(anchor)
                // Search from an empty, unrelated view: a category-only filter
                // cannot find the installed private application here.
                apps.currentModel=apps.catalogModel.favoritesModel
                searchSourceCount=apps.currentModel.count
                apps.searchText="DomainOS QA NeedleZ First"
            } else if(scenario===2){
                apps.pin("applications:irix-domainos-qa-first.desktop")
                apps.showMenu(anchor)
                let model=apps.catalogModel
                for(let i=0;i<leafPath.length-1;i++)model=model.modelForRow(leafPath[i])
                apps.currentModel=model;apps.searchText="DomainOS QA NeedleZ First"
            }
            else if(scenario===3)apps.pin("irix-domainos-qa-second.desktop")
            else if(scenario===4)apps.movePin(1,-1)
            else if(scenario===5)apps.launchPin(0)
            else if(scenario===6)apps.unpin(0)
            else if(scenario===7){
                boundsResults=[apps.unpin(-1),apps.unpin(999),apps.movePin(-1,1),apps.movePin(0,-1),apps.pin("bad;command"),apps.pin("irix-domainos-qa-first.desktop")]
            }else if(scenario===8){
                fixtureSettings.pinnedApplications=fixtureSettings.pinnedApplications.concat(["irix-domainos-absent.desktop"])
                apps.showMenu(anchor);apps.showDrawer(anchor)
                unavailableLaunchResult=apps.launchPin(1)
            }else if(scenario===9)apps.unpin(1)
            else if(scenario===11)apps.showMenu(anchor)
            else if(scenario===12){apps.close();apps.showMenu(anchor);apps.showFavorites()}
            else if(scenario===13){
                apps.close();apps.showMenu(anchor)
                let model=apps.catalogModel
                for(let i=0;i<leafPath.length-1;i++)model=model.modelForRow(leafPath[i])
                apps.currentModel=model;apps.searchText="DomainOS QA NeedleZ First"
            }
        }
    }
}
''')
    apps_dir=paths["XDG_DATA_HOME"]/"applications";apps_dir.mkdir()
    marker=output/"desktop-dispatch.txt"
    launcher=output/"desktop-marker.py"
    launcher.write_text("from pathlib import Path\nimport sys\nwith Path("+repr(str(marker))+").open('a') as file:file.write(sys.argv[1]+'\\n')\n")
    def desktop_arg(value):return '"'+str(value).replace('\\','\\\\').replace('"','\\"')+'"'
    for filename,name,key in ((FIRST,"DomainOS QA NeedleZ First","first"),(SECOND,"DomainOS QA NeedleZ Second","second")):
        actions="Actions=QAAction;\n\n[Desktop Action QAAction]\nName=QA Native Action\nExec=/usr/bin/python3 "+desktop_arg(launcher)+" context-"+key+"\n" if args.atividade else ""
        (apps_dir/filename).write_text("[Desktop Entry]\nType=Application\nName="+name+"\nExec=/usr/bin/python3 "+desktop_arg(launcher)+" "+key+"\nIcon=utilities-terminal\nTerminal=false\nDBusActivatable=false\nCategories=Utility;\n"+actions)
    flags=shlex.split(subprocess.check_output(["pkg-config","--cflags","--libs","Qt6Widgets","Qt6Test"],text=True))
    host_source="domainos-applications-activity-host.cpp" if args.atividade else "domainos-applications-host.cpp"
    subprocess.run(["c++","-std=c++17","-shared","-fPIC",str(REPO/"plasma/tests"/host_source),"-o",str(output/"applications-host.so"),*flags,"-ldl"],check=True)
    bus=output/"private-bus.conf"
    bus.write_text('<!DOCTYPE busconfig PUBLIC "-//freedesktop//DTD D-Bus Bus Configuration 1.0//EN"\n"http://www.freedesktop.org/standards/dbus/1.0/busconfig.dtd">\n<busconfig><type>session</type><listen>unix:tmpdir=/tmp</listen><auth>EXTERNAL</auth><policy context="default"><allow send_destination="*"/><allow receive_sender="*"/><allow own="*"/></policy></busconfig>\n')
    environment=os.environ.copy()
    for name in ("DISPLAY","WAYLAND_DISPLAY","DBUS_SESSION_BUS_ADDRESS","DBUS_STARTER_ADDRESS","DBUS_STARTER_BUS_TYPE","SESSION_MANAGER","QML_IMPORT_PATH","QML2_IMPORT_PATH","QT_STYLE_OVERRIDE","QT_QUICK_CONTROLS_STYLE","LD_PRELOAD","XDG_SESSION_ID","KDE_FULL_SESSION","KDE_SESSION_VERSION"):environment.pop(name,None)
    environment.update({key:str(path) for key,path in paths.items()})
    environment.update(XDG_DATA_DIRS="/usr/local/share:/usr/share",XDG_CONFIG_DIRS="/etc/xdg",XDG_CURRENT_DESKTOP="NONE",XDG_SESSION_TYPE="x11",QT_QPA_PLATFORM="xcb",QT_QPA_PLATFORMTHEME="generic",QT_QUICK_BACKEND="software",LIBGL_ALWAYS_SOFTWARE="1",DBUS_SYSTEM_BUS_ADDRESS="unix:path="+str(paths["XDG_RUNTIME_DIR"]/"no-system-bus"),KWIN_COMPOSE="N",PULSE_SERVER="unix:"+str(paths["XDG_RUNTIME_DIR"]/"no-audio"),IRIX_DOMAINOS_APPLICATIONS_DIAGNOSTIC_NO_WM="1" if args.sem_wm_diagnostico else "0")
    cache=subprocess.run(["kbuildsycoca6","--noincremental"],env=dict(environment,QT_QPA_PLATFORM="offscreen"),stdout=subprocess.PIPE,stderr=subprocess.STDOUT,text=True,timeout=20)
    (output/"sycoca.log").write_text(cache.stdout)
    environment.update(IRIX_DOMAINOS_APPLICATIONS_PRIVATE_SESSION="1")
    result=subprocess.run(["xvfb-run","--auto-servernum","--server-args=-screen 0 900x650x24","dbus-run-session","--config-file="+str(bus),"--",sys.executable,str(Path(__file__).resolve()),"--saida",str(output),"--internal-session"],env=environment,stdout=subprocess.PIPE,stderr=subprocess.STDOUT,text=True,timeout=35)
    (output/"session.log").write_text(result.stdout)
    host_log=(output/"host.log").read_text() if (output/"host.log").is_file() else result.stdout
    native=json.loads((output/"native.json").read_text()) if (output/"native.json").is_file() else {}
    diagnostics=[line for line in host_log.splitlines() if any(marker in line for marker in ("ReferenceError:","TypeError:","SyntaxError:","Cannot assign","is not a type","Error loading QML","Type DomainOSApplications unavailable"))]
    cleanup=json.loads((output/"cleanup.json").read_text()) if (output/"cleanup.json").is_file() else {}
    def pins(stage):return native.get(stage,{}).get("pins")
    all_stages=[value for value in native.values() if isinstance(value,dict) and "tasksCount" in value]
    metadata=native.get("pin_second",{}).get("native_pin_metadata",[])
    if args.atividade:
        checks=dict(native.get("checks",{}))
        checks.update(private_desktop_cache_created=cache.returncode==0,
            native_host_exited=result.returncode==0 and not native.get("failure"),
            native_catalog_favorites_context_markers_exact=marker.is_file() and marker.read_text().splitlines()==["first","first","context-first"],
            qml_diagnostics_zero=not diagnostics,
            production_components_unchanged=before=={str(path):digest(path) for path in sources},
            real_desktop_preferences_unchanged=config_before=={str(path):digest(path) for path in protected})
    else: checks={
        "private_desktop_cache_created":cache.returncode==0,
        "native_host_exited":result.returncode==0 and not native.get("failure"),
        "real_kicker_catalog_contains_categories":len(native.get("catalog_root_rows",[]))>1,
        "desktop_entry_found_in_native_catalog":native.get("leaf",{}).get("display")=="DomainOS QA NeedleZ First",
        "filtered_leaf_dispatch_exact":marker.is_file() and marker.read_text().splitlines()==["first"],
        "global_application_search_works_from_empty_unrelated_view":native.get("filtered_dispatch",{}).get("searchSourceCount")==0
            and native.get("filtered_dispatch",{}).get("showingFavorites") is True
            and marker.is_file() and marker.read_text().splitlines()==["first"],
        "leaf_launched_by_real_pointer_click":native.get("real_leaf_mouse_click") is True,
        "pin_first_only_owned_list":pins("pin_first")==[FIRST],
        "pin_second_added":pins("pin_second")==[FIRST,SECOND],
        "pin_move_reorders":pins("move")==[SECOND,FIRST],
        "pin_dispatch_requests_selected_instance":native.get("launch_pin",{}).get("applicationRequests")==[SECOND],
        "unpin_does_not_close_application":pins("unpin")==[FIRST] and native.get("unpin",{}).get("applicationRequests")==[SECOND],
        "invalid_and_duplicate_requests_rejected":native.get("bounds",{}).get("boundsResults")==[False]*6 and pins("bounds")==[FIRST],
        "pin_metadata_has_native_titles_and_icons":len(metadata)==2 and all(row.get("display","").startswith("DomainOS QA NeedleZ") and row.get("icon_present") for row in metadata),
        "menu_to_drawer_keeps_popup_open":native.get("unavailable_pin",{}).get("popupVisible") is True and native.get("unavailable_pin",{}).get("drawer") is True,
        "absent_pin_not_launchable":native.get("unavailable_pin",{}).get("unavailableLaunchResult") is False and native.get("unavailable_pin",{}).get("applicationRequests")==[SECOND],
        "absent_pin_still_removable":pins("remove_unavailable")==[FIRST],
        "task_model_and_launchers_unchanged":bool(all_stages) and len({json.dumps((state["tasksCount"],state["taskLaunchers"])) for state in all_stages})==1,
        "configuration_requested_for_own_instance":native.get("real_configure_mouse_click") is True and native.get("configure",{}).get("configureRequests")==1,
        "native_favorites_have_independent_source":native.get("pin_second",{}).get("favoritesCount")==1 and native.get("move",{}).get("favoritesCount")==1 and native.get("unpin",{}).get("favoritesCount")==1,
        "native_favorites_button_works":native.get("real_favorites_mouse_click") is True and native.get("favorites",{}).get("showingFavorites") is True and native.get("favorites",{}).get("filteredCount")==1,
        "favorite_added_through_native_context_menu":native.get("real_favorite_add_context_click") is True and native.get("pin_first",{}).get("favoritesCount")==1,
        "favorite_removed_through_native_context_menu":native.get("real_favorite_remove_context_click") is True and native.get("favorite_removed",{}).get("favoritesCount")==0 and pins("favorite_removed")==[FIRST],
        "favorite_added_through_keyboard_context_menu":native.get("real_favorite_keyboard_context_click") is True and native.get("favorite_readded",{}).get("favoritesCount")==1 and pins("favorite_readded")==[FIRST],
        "favorite_edit_does_not_launch_or_edit_pins":native.get("favorite_readded",{}).get("applicationRequests")==[SECOND] and marker.is_file() and marker.read_text().splitlines()==["first"],
        "favorite_edits_follow_native_same_user_sharing":bool(all_stages) and all(state.get("peerFavoritesCount")==state.get("favoritesCount") for state in all_stages) and native.get("favorite_removed",{}).get("peerFavoritesCount")==0 and native.get("favorite_readded",{}).get("peerFavoritesCount")==1,
        "qml_diagnostics_zero":not diagnostics,
        "production_component_unchanged":before=={str(path):digest(path) for path in sources},
        "real_desktop_preferences_unchanged":config_before=={str(path):digest(path) for path in protected}}
    if not args.atividade:
        input_targets=native.get("native_input_targets",[])
        checks["native_popup_and_target_remain_visible_during_press_release"]=bool(input_targets) and all(target.get("popup_and_target_visible_after_press") is True for target in input_targets)
        checks["native_inputs_not_blocked_by_modal_error"]=bool(input_targets) and all(
            not any(widget.get("active_modal") for widget in target.get("private_native_widgets_before_press",[]))
            for target in input_targets)
    checks["own_private_daemons_exited"]=cleanup.get("own_daemons_exited") is True
    private_runtime.cleanup()
    checks["short_private_runtime_removed"]=not paths["XDG_RUNTIME_DIR"].exists()
    scope="Native Kicker catalog/favorites/context actions and real DomainOSActivity in a private Plasma host; test-owned Desktop Entry markers only. Mock openApplication remains for pins; exception/false-policy cases are explicitly model doubles, not native launch results." if args.atividade else "Native Kicker catalog and private instance pins; one private marker-only Desktop Entry launched"
    report={"format":1,"status":"passed" if all(checks.values()) else "failed","checks":checks,"qml_diagnostics":diagnostics,"native":native,"source_hashes":before,"real_profiles_modified":False,"scope":scope,"private_window_manager":not args.sem_wm_diagnostico,"private_runtime_directory":str(paths["XDG_RUNTIME_DIR"]),"cleanup":cleanup}
    (output/"RESULTADO.json").write_text(json.dumps(report,indent=2,ensure_ascii=False)+"\n")
    print(json.dumps({"status":report["status"],"checks":len(checks),"failed":[name for name,ok in checks.items() if not ok],"report":str(output/"RESULTADO.json")},ensure_ascii=False))
    return 0 if report["status"]=="passed" else 1


if __name__=="__main__":raise SystemExit(main())
