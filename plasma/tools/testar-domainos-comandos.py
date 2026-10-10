#!/usr/bin/env python3
# SPDX-License-Identifier: GPL-3.0-or-later
"""Exercise the real QML command bridge on private Xvfb and a private D-Bus.

Launches test-owned xterms in the private display. A test-owned ScreenSaver service
answers lock requests; no screen, power or host session action is executed.
"""
import argparse
from collections import Counter
import configparser
import hashlib
import json
import os
from pathlib import Path
import shutil
import shlex
import subprocess
import sys
import time

sys.dont_write_bytecode = True
REPO = Path(__file__).resolve().parents[2]
UI = REPO / "plasma/applets/org.irixclassic.domainos.panel/contents/ui"


def inside_launch(output):
    """Specific mail/xman paths; only private Desktop Entries and X11 windows."""
    from PyQt6.QtCore import QUrl, QMetaObject, Q_RETURN_ARG, QObject
    from PyQt6.QtGui import QColor, QPalette
    from PyQt6.QtWidgets import QApplication
    from PyQt6.QtQml import QQmlApplicationEngine
    from PyQt6.QtTest import QTest
    app = QApplication([sys.argv[0]])
    engine = QQmlApplicationEngine()
    warnings = []
    engine.warnings.connect(lambda errors: warnings.extend(error.toString() for error in errors))
    private_apps = Path(os.environ["XDG_DATA_HOME"])/"applications"
    private_apps.mkdir(parents=True)
    marker = output/"mail-marker.py"
    marker.write_text('''import json, os, sys
from pathlib import Path
from PyQt6.QtWidgets import QApplication, QLabel
phase = sys.argv[1]
app = QApplication(sys.argv)
window = QLabel("Test-owned mail launch; no account or messages")
window.setWindowTitle("DomainOS-mail-native-"+phase)
window.resize(390,100); window.show()
Path(__file__).with_name("mail-"+phase+".json").write_text(json.dumps({"pid":os.getpid(),
    "argv":sys.argv,"windowId":int(window.winId()),"home":os.environ.get("HOME"),
    "config":os.environ.get("XDG_CONFIG_HOME"),"display":os.environ.get("DISPLAY"),
    "bus":os.environ.get("DBUS_SESSION_BUS_ADDRESS")}))
app.exec()
''')
    identifiers = {phase:"org.irixclassic.domainos.mail."+phase+".test.desktop"
        for phase in ("explicit","default")}
    for phase,identifier in identifiers.items():
        (private_apps/identifier).write_text("[Desktop Entry]\nType=Application\nName=DomainOS mail native "+phase+
            "\nExec=/usr/bin/python3 "+str(marker)+" "+phase+"\nIcon=mail-message\nTerminal=false\nMimeType=x-scheme-handler/mailto;\n")
    subprocess.run(["/usr/bin/xdg-mime","default",identifiers["default"],"x-scheme-handler/mailto"],check=True)
    mime_path = Path(os.environ["XDG_CONFIG_HOME"])/"mimeapps.list"
    mime_before = mime_path.read_bytes() if mime_path.is_file() else b""
    harness = output/"LaunchHarness.qml"
    harness.write_text('''import QtQuick
import "'''+UI.as_uri()+'''" as Panel
Window {
    id: fixture; width:400; height:180; visible:true; title:"DomainOS launches — private test"
    property string mailClient: ""
    property int localHelpRequests: 0
    Panel.DomainOSPalette { id: colors }
    Panel.DomainOSActivity { id: launchActivity }
    Panel.DomainOSCommands {
        id: commands; palette:colors; activity:launchActivity
        settings:({mailClient:fixture.mailClient})
        onLocalHelpRequested: fixture.localHelpRequests++
    }
    function state(): string { return JSON.stringify({report:commands.lastReport,
        pending:launchActivity.pendingCount,lit:launchActivity.lit,localHelpRequests:localHelpRequests,
        colors:{background:String(colors.background),foreground:String(colors.text),
            selection:String(colors.blue),selectionText:String(colors.white)}}) }
    function mailExplicit() { mailClient="'''+identifiers["explicit"]+'''";commands.openMail() }
    function mailDefault() { mailClient="";commands.openMail() }
    function xman() { commands.openXman() }
    function helpMenu() { commands.showHelp(commands) }
}
''')
    engine.load(QUrl.fromLocalFile(str(harness)))
    if not engine.rootObjects():
        raise RuntimeError("Real launch controller did not load: "+"\n".join(warnings))
    root = engine.rootObjects()[0]
    def call(name):
        QMetaObject.invokeMethod(root,name)
    def state():
        return json.loads(QMetaObject.invokeMethod(root,"state",Q_RETURN_ARG(str)))
    def wait(predicate, timeout=10000):
        deadline = time.monotonic()+timeout/1000
        while time.monotonic()<deadline:
            app.processEvents()
            if predicate(): return True
            QTest.qWait(20)
        return False
    def xwindows():
        result = subprocess.run(["/usr/bin/xdotool","search","--onlyvisible","--class","[Xx]man"],
            capture_output=True,text=True)
        return {int(line) for line in result.stdout.splitlines() if line.isdigit()}
    def contrast(first,second):
        def luminance(color):
            rgb = [int(color[i:i+2],16)/255 for i in (1,3,5)]
            return sum((v/12.92 if v<=.04045 else ((v+.055)/1.055)**2.4)*w
                for v,w in zip(rgb,(.2126,.7152,.0722)))
        lo,hi=sorted((luminance(first),luminance(second)))
        return (hi+.05)/(lo+.05)
    checks = {"no_launch_on_startup":state()["pending"] == 0 and not state()["lit"]}
    mail = {}; xman = {}; own_pids = []
    initial_path = os.environ["PATH"]
    try:
        for phase,function in (("explicit","mailExplicit"),("default","mailDefault")):
            call(function)
            marker_path = output/("mail-"+phase+".json")
            checks["mail_"+phase+"_launcher_accepted"] = wait(lambda:
                state()["report"].get("application")==identifiers[phase]
                and state()["report"].get("outcome")=="request-accepted")
            checks["mail_"+phase+"_application_observed"] = wait(marker_path.is_file)
            observed = json.loads(marker_path.read_text()) if marker_path.is_file() else {}
            mail[phase]={"report":state()["report"],"marker":observed}
            if observed.get("pid"): own_pids.append(observed["pid"])
            window = observed.get("windowId",0)
            image=app.primaryScreen().grabWindow(window).toImage() if window else None
            if image is not None: image.save(str(output/("mail-"+phase+".png")))
            checks["mail_"+phase+"_visible_own_window"] = bool(image is not None and not image.isNull()
                and "DomainOS-mail-native-"+phase in subprocess.run(
                    ["/usr/bin/xwininfo","-id",str(window)],capture_output=True,text=True).stdout)
            checks["mail_"+phase+"_has_no_compose_uri"] = observed.get("argv") == [str(marker),phase]
            checks["mail_"+phase+"_private_namespaces"] = all(observed.get(key)==os.environ[environment]
                for key,environment in (("home","HOME"),("config","XDG_CONFIG_HOME"),("display","DISPLAY"),("bus","DBUS_SESSION_BUS_ADDRESS")))
            checks["mail_"+phase+"_does_not_claim_completion"] = mail[phase]["report"].get("outcome")=="request-accepted"
        checks["mail_default_remains_private_and_unchanged"] = mime_before == (mime_path.read_bytes() if mime_path.is_file() else b"")
        for filename in ("Irixium.colors","DomainOS-SR10.4.colors"):
            scheme=configparser.ConfigParser();scheme.read(REPO/"colors"/filename)
            palette=QPalette()
            for role,section,key in ((QPalette.ColorRole.Window,"Colors:Window","BackgroundNormal"),
                (QPalette.ColorRole.WindowText,"Colors:Window","ForegroundNormal"),
                (QPalette.ColorRole.ButtonText,"Colors:Button","ForegroundNormal"),
                (QPalette.ColorRole.Base,"Colors:View","BackgroundNormal"),
                (QPalette.ColorRole.Highlight,"Colors:Selection","BackgroundNormal"),
                (QPalette.ColorRole.HighlightedText,"Colors:Selection","ForegroundNormal")):
                palette.setColor(role,QColor(*map(int,scheme[section][key].split(","))))
            app.setPalette(palette);app.processEvents();QTest.qWait(100)
            colors=state()["colors"]
            previous=xwindows();previous_token=state()["report"].get("token")
            call("xman")
            checks[filename+"_xman_process_started"] = wait(lambda: state()["report"].get("token")!=previous_token
                and state()["report"].get("outcome")=="process-started")
            result=state()["report"];pid=result.get("pid")
            if pid:own_pids.append(pid)
            commandline=Path("/proc")/str(pid)/"cmdline"
            argv=commandline.read_bytes().decode().strip("\0").split("\0") if commandline.is_file() else []
            checks[filename+"_xman_installed_binary_observed"] = bool(argv and argv[0] in ("xman","/usr/bin/xman"))
            checks[filename+"_xman_window_observed"] = wait(lambda:bool(xwindows()-previous))
            created=sorted(xwindows()-previous)
            counts=Counter()
            for index,window in enumerate(created):
                image=app.primaryScreen().grabWindow(window).toImage()
                image.save(str(output/(filename+"-xman-"+str(index)+".png")))
                for y in range(image.height()):
                    for x in range(image.width()): counts[image.pixelColor(x,y).name()]+=1
            bg=argv[argv.index("-bg")+1] if "-bg" in argv else "#000000"
            fg=argv[argv.index("-fg")+1] if "-fg" in argv else "#000000"
            resources=[argv[i+1] for i,a in enumerate(argv[:-1]) if a=="-xrm"]
            command_bg=next((s.split(": ",1)[1] for s in resources if s.startswith("*Command.background: ")),"#000000")
            command_fg=next((s.split(": ",1)[1] for s in resources if s.startswith("*Command.foreground: ")),"#000000")
            checks[filename+"_current_palette_background_reaches_xman"] = bg==colors["background"] and counts[bg]>20
            checks[filename+"_readable_foreground_observed"] = counts[fg]>5 and contrast(bg,fg)>=4.5
            xman[filename]={"request":result,"currentPalette":colors,"argv":argv,"windowIds":created,
                "backgroundForegroundContrast":contrast(bg,fg),"commandContrast":contrast(command_bg,command_fg),
                "commandColorsPresentInInitialWindow":counts[command_bg]>0 and counts[command_fg]>0,
                "commandColorScope":"Extra resources sent to Xaw; the acceptance gate verifies rendered Window colors/contrast, not Highlight on an unpressed button",
                "observedColorPixels":{color:counts[color] for color in {bg,fg,command_bg,command_fg}}}
            if pid:
                try:os.kill(pid,15)
                except ProcessLookupError:pass
                wait(lambda:not Path("/proc",str(pid)).exists(),timeout=1000)
        call("helpMenu");app.processEvents()
        menu=root.findChild(QObject,"domainosHelpMenu")
        titles=[]
        if menu:
            for child in menu.findChildren(QObject):
                text=child.property("text")
                if text in ("Irix Classic DomainOS help","Unix manual browser (xman)","KDE Help") and text not in titles:titles.append(text)
        checks["native_help_menu_preserves_manual_xman_kde_order"] = titles==["Irix Classic DomainOS help","Unix manual browser (xman)","KDE Help"]
        checks["opening_help_menu_launches_nothing"] = state()["pending"]==0 and not state()["lit"]
        private_bin=output/"no-xman-bin";private_bin.mkdir()
        (private_bin/"python3").symlink_to("/usr/bin/python3")
        os.environ["PATH"]=str(private_bin)
        previous_token=state()["report"].get("token")
        call("xman")
        checks["controlled_missing_xman_returns_explicit_failure"] = wait(lambda:state()["report"].get("token")!=previous_token
            and state()["report"].get("ok") is False and "Requested program is not installed" in state()["report"].get("detail",""))
        missing=state()
        checks["missing_xman_extinguishes_activity"] = missing["pending"]==0 and not missing["lit"]
        checks["qml_diagnostics_zero"]=not warnings
        report={"status":"passed" if all(checks.values()) else "failed","checks":checks,
            "scope":"Production openMail/openXman controller and launcher with only private Desktop Entries/default mailto; real /usr/bin/xman and native palettes; no mail account, Thunderbird or personal session action",
            "mail":mail,"xman":xman,"helpMenuTitles":titles,"missingXman":missing,"qml_diagnostics":warnings,
            "private_display":os.environ.get("DISPLAY"),"real_mail_accounts_read":False}
        (output/"RESULTADO.json").write_text(json.dumps(report,indent=2,ensure_ascii=False)+"\n")
        print(json.dumps({"status":report["status"],"checks":len(checks),"failed":[key for key,value in checks.items() if not value],"result":str(output/"RESULTADO.json")}))
        return 0 if all(checks.values()) else 1
    finally:
        os.environ["PATH"]=initial_path
        for pid in own_pids:
            path=Path("/proc",str(pid),"cmdline")
            if path.is_file() and (str(marker).encode() in path.read_bytes() or b"xman\0" in path.read_bytes()):
                try:os.kill(pid,15)
                except ProcessLookupError:pass


def inside(output):
    from PyQt6.QtCore import QObject, QUrl, QMetaObject, Q_RETURN_ARG, pyqtClassInfo, pyqtSlot
    from PyQt6.QtDBus import QDBusConnection
    from PyQt6.QtWidgets import QApplication
    from PyQt6.QtQml import QQmlApplicationEngine
    from PyQt6.QtQuick import QQuickWindow
    from PyQt6.QtTest import QTest
    app = QApplication([sys.argv[0]])
    engine = QQmlApplicationEngine()
    warnings = []
    engine.warnings.connect(lambda errors: warnings.extend(error.toString() for error in errors))
    @pyqtClassInfo("D-Bus Interface", "org.freedesktop.ScreenSaver")
    class ScreenSaver(QObject):
        calls = 0
        active = False
        @pyqtSlot()
        def Lock(self):
            self.calls += 1
            self.active = True
        @pyqtSlot(result=bool)
        def GetActive(self):
            return self.active
    service = ScreenSaver()
    bus = QDBusConnection.sessionBus()
    assert bus.registerService("org.freedesktop.ScreenSaver")
    assert bus.registerObject("/ScreenSaver", service, QDBusConnection.RegisterOption.ExportAllSlots)
    harness = output / "CommandsHarness.qml"
    sentinel = output / "shell-quote-should-not-exist"
    literal_title = "DomainOS's $(touch " + str(sentinel) + ") ; quoted"
    terminal_command = "xterm -name DomainOS-command-native-test -title " + shlex.quote(literal_title)
    harness.write_text('''import QtQuick
import "''' + UI.as_uri() + '''" as Panel
Window {
    id: fixture
    width: 400; height: 180; visible: true; title: "DomainOS commands — private test"
    Panel.DomainOSPalette { id: colors }
    Panel.DomainOSActivity { id: activityTracker }
    Panel.DomainOSCommands {
        id: commands; activity: activityTracker; palette: colors
        settings: ({terminalCommand: ''' + json.dumps(terminal_command) + '''})
    }
    Panel.DomainOSActivity { id: parallelActivityA }
    Panel.DomainOSActivity { id: parallelActivityB }
    property var parallelReportsA: []
    property var parallelReportsB: []
    Panel.DomainOSCommands {
        id: parallelA; activity: parallelActivityA; palette: colors; settings: commands.settings
        onReported: report => fixture.parallelReportsA = fixture.parallelReportsA.concat([report])
    }
    Panel.DomainOSCommands {
        id: parallelB; activity: parallelActivityB; palette: colors; settings: commands.settings
        onReported: report => fixture.parallelReportsB = fixture.parallelReportsB.concat([report])
    }
    property var activity: activityTracker
    Rectangle { anchors.centerIn: parent; width: 40; height: 28; color: activityTracker.lit ? "#dddd28" : "#777777" }
    function state(): string { return JSON.stringify({pending: activity.pendingCount, lit: activity.lit,
        tail: activity.tailLit, report: commands.lastReport, activityReport: activity.lastReport,
        parallelA: {pending: parallelActivityA.pendingCount, lit: parallelActivityA.lit, reports: parallelReportsA},
        parallelB: {pending: parallelActivityB.pendingCount, lit: parallelActivityB.lit, reports: parallelReportsB}}) }
    function concurrent(): bool {
        const a = activity.begin("A"), b = activity.begin("B")
        if (!activity.lit || activity.pendingCount !== 2) return false
        activity.finish(a, {outcome: "confirmed"})
        if (!activity.lit || activity.pendingCount !== 1) return false
        activity.finish(b, {outcome: "confirmed"})
        return !activity.lit && activity.pendingCount === 0
    }
    function tail(): bool {
        activity.keepLightAfterCompletion = true; activity.extraLightMilliseconds = 500
        const a = activity.begin("completed"), start = Date.now()
        activity.finish(a, {outcome: "confirmed"})
        return activity.pendingCount === 0 && activity.lit && activity.tailLit && Date.now() - start < 100
    }
    function newDuringTail(): bool {
        const a = activity.begin("new")
        const good = activity.pendingCount === 1 && activity.lit && !activity.tailLit
        activity.keepLightAfterCompletion = false
        activity.finish(a, {outcome: "confirmed"})
        return good && !activity.lit
    }
    function terminal() { commands.openTerminal() }
    function lock() { commands.lock() }
    function missing() { commands.openApplication("does-not-exist-domainos-test.desktop") }
    function idleMenu() { commands.showSession(commands) }
    function parallel(): string {
        const a = parallelA.openTerminal(), b = parallelB.openTerminal(), c = parallelA.openTerminal()
        return JSON.stringify({a: a, b: b, c: c, nonceA: parallelA.instanceNonce, nonceB: parallelB.instanceNonce})
    }
}''')
    engine.load(QUrl.fromLocalFile(str(harness)))
    if not engine.rootObjects():
        raise RuntimeError("Real command components did not load: " + "\n".join(warnings))
    root = engine.rootObjects()[0]
    def call(name, result=None):
        print("Fixture step: " + name, flush=True)
        return QMetaObject.invokeMethod(root, name, Q_RETURN_ARG(result)) if result else QMetaObject.invokeMethod(root, name)
    def state():
        return json.loads(QMetaObject.invokeMethod(root, "state", Q_RETURN_ARG(str)))
    def wait(predicate, timeout=6000):
        deadline = time.monotonic() + timeout / 1000
        while time.monotonic() < deadline:
            app.processEvents()
            if predicate(): return True
            QTest.qWait(20)
        return False
    checks = {}
    checks["no_command_at_startup"] = state()["pending"] == 0 and not state()["lit"] and service.calls == 0
    checks["concurrent_operations_no_false_extinction"] = call("concurrent", bool)
    checks["tail_delays_only_light_not_completion"] = call("tail", bool)
    checks["new_operation_cancels_tail"] = call("newDuringTail", bool)
    call("terminal")
    checks["launch_lights_immediately"] = state()["pending"] == 1 and state()["lit"]
    checks["real_helper_launch_result"] = wait(lambda: state()["report"].get("outcome") == "process-started")
    checks["actual_terminal_on_private_display"] = wait(lambda: "DomainOS-command-native-test" in subprocess.run(
        ["xwininfo", "-root", "-tree"], capture_output=True, text=True).stdout)
    checks["posix_quote_preserves_literal_apostrophe_and_substitution"] = literal_title in subprocess.run(
        ["xwininfo", "-root", "-tree"], capture_output=True, text=True).stdout and not sentinel.exists()
    terminal_pid = state()["report"].get("pid")
    checks["launch_does_not_claim_application_finished"] = state()["report"].get("outcome") == "process-started"
    call("lock")
    checks["lock_uses_native_dbus_reply"] = wait(lambda: state()["report"].get("action") == "lock")
    checks["lock_reaches_only_fixture_service"] = service.calls == 1 and service.active
    checks["lock_confirmation_is_observed"] = state()["report"].get("outcome") == "confirmed"
    call("idleMenu")
    checks["opening_session_menu_executes_nothing"] = state()["pending"] == 0 and service.calls == 1
    call("missing")
    checks["missing_app_is_failure"] = wait(lambda: state()["report"].get("ok") is False)
    checks["missing_application_error_is_reported"] = "Application is not installed" in state()["report"].get("detail", "")
    checks["failure_extinguishes_indicator"] = state()["pending"] == 0 and not state()["lit"]
    duplicate_request = json.loads(call("parallel", str))
    checks["same_action_same_token_has_distinct_instance_nonce"] = duplicate_request["a"] == duplicate_request["b"] == 1 and duplicate_request["nonceA"] != duplicate_request["nonceB"]
    checks["queued_requests_all_light_immediately"] = state()["parallelA"]["pending"] == 2 and state()["parallelB"]["pending"] == 1 and state()["parallelA"]["lit"] and state()["parallelB"]["lit"]
    checks["queued_native_results_all_arrive"] = wait(lambda: len(state()["parallelA"]["reports"]) == 2 and len(state()["parallelB"]["reports"]) == 1)
    parallel_state = state()
    parallel_results = parallel_state["parallelA"]["reports"] + parallel_state["parallelB"]["reports"]
    parallel_pids = [report.get("pid") for report in parallel_results]
    checks["queued_results_keep_each_instance_tokens"] = sorted(report.get("token") for report in parallel_state["parallelA"]["reports"]) == [1, 2] and [report.get("token") for report in parallel_state["parallelB"]["reports"]] == [1]
    checks["identical_requests_spawn_three_distinct_processes"] = len(parallel_pids) == 3 and len(set(parallel_pids)) == 3 and all(report.get("outcome") == "process-started" for report in parallel_results)
    checks["all_queued_completions_extinguish_indicators"] = all(parallel_state[name]["pending"] == 0 and not parallel_state[name]["lit"] for name in ("parallelA", "parallelB"))
    checks["qml_diagnostics_zero"] = not warnings
    from PyQt6 import sip
    sip.cast(root, QQuickWindow).grabWindow().save(str(output / "commands-native.png"))
    report = {"status": "passed" if all(checks.values()) else "failed", "checks": checks,
              "qml_diagnostics": warnings, "last_state": state(), "private_display": os.environ.get("DISPLAY"),
              "real_lock_or_power_action": False, "terminal_pid": terminal_pid,
              "parallel_terminal_pids": parallel_pids}
    (output / "RESULTADO.json").write_text(json.dumps(report, indent=2, ensure_ascii=False) + "\n")
    for pid in [terminal_pid, *parallel_pids]:
        if not pid:
            continue
        # Only the exact process created by this fixture, never a process search.
        try: os.kill(pid, 15)
        except ProcessLookupError: pass
    print(json.dumps({"status": report["status"], "checks": len(checks), "result": str(output / "RESULTADO.json")}))
    return 0 if all(checks.values()) else 1


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--saida", type=Path, required=True)
    parser.add_argument("--inside", action="store_true", help=argparse.SUPPRESS)
    parser.add_argument("--lancamentos",action="store_true",help="Directed private mail/xman launch proof only")
    args = parser.parse_args()
    output = args.saida.resolve()
    if args.inside:
        return inside_launch(output) if args.lancamentos else inside(output)
    if output.exists() and any(output.iterdir()): parser.error("Output must be new or empty")
    output.mkdir(parents=True, exist_ok=True)
    for name in ("xvfb-run", "dbus-run-session", "xterm", "xwininfo"):
        if not shutil.which(name): parser.error("Missing test-only program: " + name)
    env = os.environ.copy()
    real_config = Path(env.get("XDG_CONFIG_HOME", str(Path.home() / ".config")))
    def config_hashes():
        return {name: hashlib.sha256((real_config / name).read_bytes()).hexdigest() if (real_config / name).is_file() else None
                for name in ("kdeglobals", "plasmarc", "kwinrc", "plasma-org.kde.plasma.desktop-appletsrc")}
    before = config_hashes()
    for key in ("DISPLAY", "WAYLAND_DISPLAY", "DBUS_SESSION_BUS_ADDRESS", "DBUS_STARTER_ADDRESS", "DBUS_STARTER_BUS_TYPE",
                "SESSION_MANAGER", "LD_PRELOAD", "QT_STYLE_OVERRIDE", "QT_QUICK_CONTROLS_STYLE", "QML_IMPORT_PATH", "QML2_IMPORT_PATH"):
        env.pop(key, None)
    for key, name in (("HOME", "home"), ("XDG_CONFIG_HOME", "config"), ("XDG_DATA_HOME", "data"),
                      ("XDG_CACHE_HOME", "cache"), ("XDG_STATE_HOME", "state"), ("XDG_RUNTIME_DIR", "runtime")):
        path = output / name; path.mkdir(mode=0o700); env[key] = str(path)
    env.update(QT_QPA_PLATFORM="xcb", QT_QUICK_BACKEND="software", QT_QPA_PLATFORMTHEME="generic",
               XDG_CURRENT_DESKTOP="NONE", XDG_SESSION_TYPE="x11", DBUS_SYSTEM_BUS_ADDRESS="unix:path=" + str(output / "no-system-bus"))
    bus = output / "bus.conf"
    bus.write_text('<busconfig><type>session</type><listen>unix:tmpdir=/tmp</listen><auth>EXTERNAL</auth>'
                   '<policy context="default"><allow send_destination="*"/><allow receive_sender="*"/><allow own="*"/></policy></busconfig>')
    command = ["xvfb-run", "--auto-servernum", "--server-args=-screen 0 1000x600x24", "dbus-run-session", "--config-file", str(bus), "--",
               sys.executable, str(Path(__file__).resolve()), "--saida", str(output), "--inside"]
    if args.lancamentos:command.append("--lancamentos")
    result = subprocess.run(command, env=env, capture_output=True, text=True, timeout=45)
    (output / "native.log").write_text(result.stdout + result.stderr)
    after = config_hashes()
    (output / "protected-configs.json").write_text(json.dumps({"before": before, "after": after, "unchanged": before == after}, indent=2) + "\n")
    print(result.stdout or result.stderr)
    return result.returncode if before == after else 2


if __name__ == "__main__":
    raise SystemExit(main())
