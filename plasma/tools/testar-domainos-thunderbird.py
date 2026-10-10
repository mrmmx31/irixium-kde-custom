#!/usr/bin/python3
# SPDX-License-Identifier: GPL-3.0-or-later
"""Exercise the optional Thunderbird bridge on private user/D-Bus namespaces.

Provider mode uses real native-message pipes and KDE SmartLauncher/ServiceWatcher.
Thunderbird mode additionally starts the installed ESR with a disposable local
mail account, its staged XPI and native host. No personal profile or account.
"""
import argparse
import hashlib
import importlib.util
import json
import os
from pathlib import Path
import select
import socket
import struct
import subprocess
import sys
import tempfile
import time

ROOT = Path(__file__).resolve().parents[2]
BASE = ROOT / "integrations/thunderbird-domainos"
UI = ROOT / "plasma/applets/org.irixclassic.domainos.panel/contents/ui"
SERVICE = "org.irixclassic.DomainOS.Thunderbird"
DESKTOP = "org.irixclassic.domainos.thunderbird.counts.desktop"


class Marionette:
    """Small test-only client for Gecko's documented length-prefixed protocol."""
    def __init__(self, port):
        self.socket = socket.create_connection(("127.0.0.1", port), timeout=2)
        self.socket.settimeout(8)
        self.buffer = bytearray()
        self.sequence = 0
        self.greeting = self.read()

    def read(self):
        while b":" not in self.buffer:
            self.buffer.extend(self.socket.recv(4096))
        length, rest = self.buffer.split(b":", 1)
        length = int(length)
        if not 0 < length < 1024 * 1024: raise RuntimeError("Invalid own Marionette packet")
        self.buffer = bytearray(rest)
        while len(self.buffer) < length:
            chunk = self.socket.recv(4096)
            if not chunk: raise RuntimeError("Own Marionette socket closed")
            self.buffer.extend(chunk)
        raw = bytes(self.buffer[:length]); del self.buffer[:length]
        return json.loads(raw)

    def call(self, method, params):
        self.sequence += 1
        raw = json.dumps([0, self.sequence, method, params], separators=(",", ":")).encode()
        self.socket.sendall(str(len(raw)).encode() + b":" + raw)
        result = self.read()
        if result[0] != 1 or result[1] != self.sequence or result[2] is not None:
            raise RuntimeError("Private Marionette request failed: " + json.dumps(result))
        return result[3]

    def script(self, script):
        return self.call("WebDriver:ExecuteScript", {"script": script, "args": [], "newSandbox": False,
            "sandbox": "system", "filename": "domainos-own-count-test", "line": 1})


def worker(mode, output):
    if os.environ.get("DOMAINOS_THUNDERBIRD_PRIVATE") != "1": raise RuntimeError("Private launcher required")
    from PyQt6.QtCore import QCoreApplication, QEvent, QMetaObject, QObject, QSize, QUrl, Qt
    from PyQt6.QtDBus import QDBusConnection, QDBusMessage
    from PyQt6.QtGui import QGuiApplication
    from PyQt6.QtQml import QQmlComponent, QQmlEngine, qmlRegisterSingletonType
    from PyQt6.QtTest import QTest

    spec = importlib.util.spec_from_file_location("own_bridge_installer", BASE / "install.py")
    installer = importlib.util.module_from_spec(spec); spec.loader.exec_module(installer)
    installed = installer.install(Path(os.environ["HOME"]), Path(os.environ["XDG_DATA_HOME"]))
    subprocess.run(["kbuildsycoca6", "--noincremental"], check=True, capture_output=True, timeout=15)
    if mode == "panel":
        from PyQt6 import sip
        from PyQt6.QtQuick import QQuickItem
        from PyQt6.QtWidgets import QApplication
        app = QApplication([])
        context = Path(os.environ["TMPDIR"]) / "OwnPlasmoidContext.qml"
        context.write_text("pragma Singleton\nimport QtQuick\nimport org.kde.plasma.core as PC\nQtObject {readonly property int formFactor:PC.Types.Planar}\n")
        qmlRegisterSingletonType(QUrl.fromLocalFile(str(context)), "org.kde.plasma.plasmoid", 1, 0, "Plasmoid")
    else:
        app = QGuiApplication([])
    engine = QQmlEngine(); messages = []
    engine.warnings.connect(lambda errors: messages.extend(error.toString() for error in errors))
    component = QQmlComponent(engine)
    body = '''
    property alias source: source
    Production.DomainOSMailState {id:source;enabled:true;desktopId:"thunderbird.desktop"}
'''
    if mode == "panel":
        body = '''
    width:971;height:109;visible:true
    property alias panel:panel
    property alias source:runtime.mailState
    Production.DomainOSPanel {id:panel;anchors.fill:parent}
    Production.DomainOSRuntime {id:runtime;hostItem:null;screenGeometry:Qt.rect(0,0,1200,900);
        colorPalette:panel.colorPalette;instanceId:"own-mail-count-test";
        settings:({mailClient:"thunderbird.desktop",mailCountsEnabled:true,
            tasksOnlyCurrentDesktop:false,tasksOnlyCurrentActivity:false})}
    function attach() {panel.integration=runtime}
'''
    component.setData(('''import QtQuick
import "''' + UI.as_uri() + '''" as Production
''' + ("Window" if mode == "panel" else "Item") + ''' {
    id:fixture
''' + body + '''
    property var availableTransitions: []
    Connections {target:fixture.source;function onAvailableChanged(){if(fixture.source.available)fixture.availableTransitions=fixture.availableTransitions.concat([fixture.source.unreadCount])}}
    function state() {
        const loader=fixture.source.children.find(child=>child.item && child.item.launcher)
        return JSON.stringify({available:fixture.source.available,count:fixture.source.unreadCount,
            rawNativeCount:loader?.item.launcher.count,rawNativeCountVisible:loader?.item.launcher.countVisible,
            status:fixture.source.statusText,transitions:availableTransitions})
    }
}''').encode(), QUrl.fromLocalFile(str(Path(os.environ["TMPDIR"]) / "mail-count-fixture.qml")))
    fixture = component.create()
    assert fixture, "\n".join(error.toString() for error in component.errors())
    if mode == "panel":
        panel = sip.cast(fixture.property("panel"), QQuickItem)
        # Keep the actual count face/controller. Task/pager/tray/graph loaders
        # are unrelated to this proof and must not request native session data.
        for item in panel.findChildren(QObject):
            if item.metaObject().className().startswith("QQuickLoader"):
                item.setProperty("active", False)
        QMetaObject.invokeMethod(fixture, "attach", Qt.ConnectionType.DirectConnection)
    bus = QDBusConnection.sessionBus(); checks, snapshots = {}, {}

    def owner_pid():
        reply = bus.interface().servicePid(SERVICE)
        return reply.value() if reply.isValid() else 0

    def state():
        from PyQt6.QtCore import Q_RETURN_ARG
        value = QMetaObject.invokeMethod(fixture, "state", Qt.ConnectionType.DirectConnection, Q_RETURN_ARG("QVariant"))
        return json.loads(value)

    def wait(predicate, timeout=5):
        end = time.monotonic() + timeout
        while time.monotonic() < end:
            app.processEvents()
            if predicate(): return True
            QTest.qWait(10)
        return False

    def unavailable():
        return not state()["available"] and state()["count"] is None

    def known(count):
        return state()["available"] and state()["count"] == count

    def fake_old_badge():
        message = QDBusMessage.createSignal("/OwnedOldBadge", "com.canonical.Unity.LauncherEntry", "Update")
        message.setArguments(["application://" + DESKTOP, {"count": 12, "count-visible": True}])
        assert bus.send(message)

    hosts = []
    def start_host():
        child = subprocess.Popen([installed["native_host_manifest"] and str(Path(installed["xpi"]).parent / "native_host.py")],
            stdin=subprocess.PIPE, stdout=subprocess.PIPE, stderr=subprocess.PIPE)
        hosts.append(child)
        assert wait(lambda: bus.interface().isServiceRegistered(SERVICE).value())
        return child

    def frame(message):
        raw = json.dumps(message).encode(); return struct.pack("<I", len(raw)) + raw

    def send(child, available, count):
        child.stdin.write(frame({"schema": 1, "type": "counts", "available": available, "unreadCount": count})); child.stdin.flush()
        assert wait(lambda: known(count) if available else unavailable())
        assert select.select([child.stdout], [], [], 2)[0]
        length, = struct.unpack("<I", child.stdout.read(4))
        receipt = json.loads(child.stdout.read(length))
        assert receipt == {"ok": True, "available": available, "unreadCount": count}
        return receipt

    tb = None; marionette = None; native_host_pid = None
    try:
        checks["no_source_is_unknown_not_zero"] = wait(unavailable)
        # Runtime's nested Loader can complete after create() returns. Let its
        # real backend subscribe before publishing the one synthetic old badge.
        assert wait(lambda: isinstance(state().get("rawNativeCount"), int))
        QTest.qWait(100)
        fake_old_badge()
        checks["cached_badge_without_our_owner_stays_unavailable"] = wait(lambda: state().get("rawNativeCount") == 12) and unavailable() \
            and state()["rawNativeCount"] == 12 and state()["rawNativeCountVisible"]
        snapshots["before"] = state()
        if mode in ("provider", "panel"):
            host = start_host(); QTest.qWait(100)
            checks["fresh_host_never_exposes_cached_twelve"] = unavailable() and 12 not in state()["transitions"]
            checks["persistent_owner_matches_actual_host"] = owner_pid() == host.pid
            for value in (0, 3, 2, 0):
                receipt = send(host, True, value); snapshots["count_" + str(value)] = state()
                checks["known_" + str(value) + "_via_native_provider"] = receipt["unreadCount"] == value
                if mode == "panel":
                    caption = panel.findChild(QObject, "domainosMailUnreadText")
                    face = panel.findChild(QObject, "domainosMailUnreadCount")
                    checks["real_panel_caption_" + str(value)] = wait(lambda: caption.property("text") == str(value)) \
                        and face.property("visible")
                    if value == 3:
                        grab = panel.grabToImage(QSize(971, 109)); done = [False]
                        grab.ready.connect(lambda: done.__setitem__(0, True))
                        assert wait(lambda: done[0]) and grab.image().save(str(output / "PANEL-COUNT-3.png"))
            send(host, False, None)
            checks["explicit_unknown_is_null"] = unavailable()
            if mode == "panel":
                checks["real_panel_unknown_is_dash_not_zero"] = wait(lambda: caption.property("text") == "—")
            send(host, True, 7)
            host.stdin.close(); assert wait(unavailable); host.wait(3)
            checks["eof_hides_count_and_releases_owner"] = unavailable() and not bus.interface().isServiceRegistered(SERVICE).value()
            host = start_host(); send(host, True, 9)
            host.kill(); host.wait(3); assert wait(unavailable)
            checks["crash_hides_stale_native_badge"] = unavailable()
            host = start_host(); QTest.qWait(100)
            checks["reconnection_stays_unknown_until_fresh_aggregate"] = unavailable()
            send(host, True, 4)
            checks["valid_update_recovers_after_crash"] = known(4)
            host.stdin.write(struct.pack("<I", 513)); host.stdin.flush()
            assert wait(unavailable); host.wait(3)
            checks["oversized_frame_closes_source_without_stale_count"] = unavailable() and host.returncode == 1
        else:
            profile = Path(os.environ["TMPDIR"]) / "own-thunderbird-profile"
            profile.mkdir(mode=0o700)
            (profile / "extensions").mkdir(mode=0o700)
            xpi = Path(installed["xpi"])
            import shutil
            shutil.copy2(xpi, profile / "extensions/domainos-mail-count@irixclassic.local.xpi")
            local = profile / "Mail/Local Folders"; local.mkdir(parents=True)
            with socket.socket() as listener:
                listener.bind(("127.0.0.1", 0)); port = listener.getsockname()[1]
            prefs = {"mail.accountmanager.accounts": "account1", "mail.accountmanager.defaultaccount": "account1",
                "mail.account.account1.server": "server1", "mail.accountmanager.localfoldersserver": "server1",
                "mail.server.server1.type": "none", "mail.server.server1.hostname": "Local Folders",
                "mail.server.server1.userName": "nobody", "mail.server.server1.directory": str(local),
                "mail.server.server1.name": "Own synthetic local messages", "mailnews.start_page.enabled": False,
                "extensions.autoDisableScopes": 0, "extensions.enabledScopes": 15,
                "extensions.update.enabled": False, "app.update.enabled": False,
                "datareporting.policy.dataSubmissionEnabled": False, "toolkit.telemetry.enabled": False,
                "mail.provider.enabled": False, "marionette.enabled": True, "marionette.port": port,
                "marionette.log.level": "Error"}
            (profile / "user.js").write_text("\n".join("user_pref(" + json.dumps(k) + ", " + json.dumps(v) + ");" for k, v in prefs.items()))
            log = (output / "THUNDERBIRD.log").open("w")
            tb = subprocess.Popen(["thunderbird", "--no-remote", "--profile", str(profile), "--headless",
                "--marionette", "--remote-allow-system-access"], stdout=log, stderr=subprocess.STDOUT)
            def connect_marionette():
                nonlocal marionette
                try: marionette = Marionette(port); return True
                except (ConnectionError, OSError): return False
            assert wait(connect_marionette, 20), "Private Thunderbird Marionette unavailable"
            marionette.call("WebDriver:NewSession", {"capabilities": {}})
            marionette.call("Marionette:SetContext", {"value": "chrome"})
            checks["xpi_native_host_loaded_by_real_thunderbird"] = wait(lambda: bus.interface().isServiceRegistered(SERVICE).value(), 12)
            assert checks["xpi_native_host_loaded_by_real_thunderbird"], "The real XPI did not connect to its staged host"
            native_host_pid = owner_pid()
            setup = marionette.script('''const {MailServices}=ChromeUtils.importESModule("resource:///modules/MailServices.sys.mjs");
const root=MailServices.accounts.localFoldersServer.rootFolder;
let folder=root.getChildNamed("DomainOS QA");if(!folder)folder=root.QueryInterface(Ci.nsIMsgLocalMailFolder).createLocalSubfolder("DomainOS QA");
globalThis.domainosOwnFolder=folder.QueryInterface(Ci.nsIMsgLocalMailFolder);
globalThis.domainosOwnHeaders=[];return {own:true};''')
            checks["synthetic_local_folder_created_only_in_private_profile"] = setup.get("value", setup).get("own") is True
            for number in range(1, 4):
                added = marionette.script('''const message="From - Fri Oct 09 12:00:00 2026\\nX-Mozilla-Status: 0000\\nX-Mozilla-Status2: 00000000\\nFrom: own-test@invalid.local\\nTo: own-test@invalid.local\\nSubject: synthetic count fixture\\nMessage-ID: <domainos-"+Date.now()+"@invalid.local>\\n\\nOnly synthetic test data.\\n";
const header=globalThis.domainosOwnFolder.addMessage(message);globalThis.domainosOwnHeaders.push(header);return {added:true};''')
                assert added.get("value", added).get("added") is True
                assert wait(lambda: known(number)), "Native folder event did not publish unread count " + str(number)
                snapshots["native_folder_count_" + str(number)] = state()
            checks["three_real_folder_events_update_aggregate"] = known(3)
            marionette.script('''globalThis.domainosOwnFolder.markMessagesRead(globalThis.domainosOwnHeaders,true);return {marked:true};''')
            checks["native_mark_read_event_reports_known_zero"] = wait(lambda: known(0))
            checks["native_host_is_separate_persistent_child"] = native_host_pid not in (0, os.getpid(), tb.pid) \
                and owner_pid() == native_host_pid
            marionette.call("Marionette:Quit", {"flags": ["eAttemptQuit"]})
            tb.wait(8)
            checks["thunderbird_exit_removes_source_not_fake_zero"] = wait(unavailable)
        errors = [message for message in messages if any(s in message for s in (
            "Error:", "Binding loop", "Cannot assign", "Unable to assign", "Cannot read", "is not a function"))]
        checks["no_qml_runtime_errors"] = not errors
        snapshots["final"] = state()
        result = {"checks": checks, "snapshots": snapshots, "qml_errors": errors, "mode": mode,
            "source_sha256": {str(path.relative_to(ROOT)): hashlib.sha256(path.read_bytes()).hexdigest()
                for path in (UI / "DomainOSMailState.qml", UI / "DomainOSRuntime.qml", UI / "DomainOSInstruments.qml",
                    UI / "DomainOSPanel.qml", BASE / "native_host.py", BASE / "extension/manifest.json", BASE / "extension/background.js")},
            "scope": __doc__, "native_host_pid": native_host_pid,
            "status": "passed" if all(checks.values()) else "failed"}
        (output / "RESULTADO.json").write_text(json.dumps(result, indent=2, ensure_ascii=False) + "\n")
        print(json.dumps({"status": result["status"], "passed": sum(checks.values()), "total": len(checks)}))
        return 0 if result["status"] == "passed" else 1
    except Exception as error:
        (output / "RESULTADO.json").write_text(json.dumps({"status":"failed","mode":mode,
            "checks":checks,"snapshots":snapshots,"failure":str(error),"scope":__doc__},indent=2)+"\n")
        raise
    finally:
        if marionette: marionette.socket.close()
        if tb and tb.poll() is None:
            tb.terminate()
            try: tb.wait(5)
            except subprocess.TimeoutExpired: tb.kill(); tb.wait(3)
        if native_host_pid and owner_pid() == native_host_pid:
            try: os.kill(native_host_pid, 15)
            except ProcessLookupError: pass
        for host in hosts:
            if host.poll() is None:
                host.terminate()
                try: host.wait(3)
                except subprocess.TimeoutExpired: host.kill(); host.wait(3)
        # Destroy the owned QML tree while the GUI application still exists.
        # Runtime instantiates native controllers with deferred deletions.
        fixture.deleteLater()
        QCoreApplication.sendPostedEvents(None, QEvent.Type.DeferredDelete)
        app.processEvents()
        engine.clearComponentCache()


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--output", type=Path, required=True)
    parser.add_argument("--mode", choices=("provider", "thunderbird", "panel"), default="provider")
    parser.add_argument("--worker", action="store_true", help=argparse.SUPPRESS)
    args = parser.parse_args()
    if args.worker: return worker(args.mode, args.output)
    output = args.output.resolve()
    if output.exists() or not output.is_relative_to('/tmp'): parser.error("Use a new evidence directory under /tmp")
    output.mkdir(mode=0o700)
    with tempfile.TemporaryDirectory(prefix=".qa-thunderbird-count-", dir=ROOT) as temporary:
        base = Path(temporary); env = dict(os.environ)
        for key in ("HOME", "XDG_CONFIG_HOME", "XDG_DATA_HOME", "XDG_CACHE_HOME", "XDG_STATE_HOME", "XDG_RUNTIME_DIR", "TMPDIR"):
            path = base / key.lower(); path.mkdir(mode=0o700); env[key] = str(path)
        for key in ("DISPLAY", "WAYLAND_DISPLAY", "LD_PRELOAD", "DBUS_SESSION_BUS_ADDRESS", "QT_STYLE_OVERRIDE", "QML_IMPORT_PATH", "QML2_IMPORT_PATH"):
            env.pop(key, None)
        conf = base / "bus.conf"
        # No service activation: only processes explicitly owned by this test.
        conf.write_text('<busconfig><type>session</type><listen>unix:tmpdir=/tmp</listen><auth>EXTERNAL</auth><policy context="default"><allow send_destination="*"/><allow receive_sender="*"/><allow own="*"/></policy></busconfig>')
        env.update(DOMAINOS_THUNDERBIRD_PRIVATE="1", QT_QPA_PLATFORM="offscreen", QT_QUICK_BACKEND="software",
            QT_QPA_PLATFORMTHEME="generic", QT_QUICK_CONTROLS_STYLE="Basic", QML_DISABLE_DISK_CACHE="1",
            PYTHONDONTWRITEBYTECODE="1", DBUS_SYSTEM_BUS_ADDRESS="unix:path=" + str(base / "disabled-system"),
            MOZ_DISABLE_CONTENT_SANDBOX="1", MOZ_HEADLESS="1", GIO_USE_VFS="local", XDG_CURRENT_DESKTOP="NONE")
        result = subprocess.run(["dbus-run-session", "--config-file", str(conf), "--", sys.executable,
            str(Path(__file__).resolve()), "--worker", "--mode", args.mode, "--output", str(output)],
            env=env, capture_output=True, text=True, timeout=80 if args.mode == "thunderbird" else 35)
        log = output / "RUNNER.log"; log.write_text(result.stdout + result.stderr); log.chmod(0o600)
        report_path=output/"RESULTADO.json"
        if report_path.exists():
            report=json.loads(report_path.read_text());report["worker_returncode"]=result.returncode
            if result.returncode: report["status"]="failed"
            report_path.write_text(json.dumps(report,indent=2)+"\n");report_path.chmod(0o600)
        print((result.stdout + result.stderr)[-6000:]); return result.returncode


if __name__ == "__main__":
    sys.exit(main())
