#!/usr/bin/python3
# SPDX-License-Identifier: GPL-3.0-or-later
"""Real QML: refresh the default client on explicit use, without polls/retries."""
import json
import argparse
import hashlib
import os
from pathlib import Path
import subprocess
import sys
import tempfile

ROOT = Path(__file__).resolve().parents[2]
UI = ROOT / "plasma/applets/org.irixclassic.domainos.panel/contents/ui"


def worker():
    if os.environ.get("DOMAINOS_MAIL_DEFAULT_PRIVATE") != "1":
        raise RuntimeError("Use the private launcher")
    from PyQt6.QtCore import Q_ARG, QCoreApplication, QEvent, QMetaObject, Q_RETURN_ARG, QUrl, Qt
    from PyQt6.QtGui import QGuiApplication
    from PyQt6.QtQml import QQmlComponent, QQmlEngine
    app = QGuiApplication([]); engine = QQmlEngine(); errors = []
    engine.warnings.connect(lambda values: errors.extend(value.toString() for value in values))
    component = QQmlComponent(engine)
    component.setData(('''import QtQuick
import "''' + UI.as_uri() + '''" as Production
Item {
    id:fixture
    QtObject {
        id:metadata
        property var connected:[]
        property var disconnected:[]
        property bool failConnect:false
        property bool failDisconnect:false
        property string synchronousClient:""
        function connectSource(command) {
            connected=connected.concat([command])
            if(synchronousClient)source.handleMetadataResult(command,{stdout:JSON.stringify({ok:true,defaultClient:synchronousClient})})
            if(failConnect)throw new Error("own injected connect failure")
        }
        function disconnectSource(command) {
            disconnected=disconnected.concat([command])
            if(failDisconnect)throw new Error("own injected disconnect failure")
        }
    }
    Production.DomainOSMailState {id:source;enabled:true;metadataSource:metadata}
    function reply(index, client) {source.handleMetadataResult(metadata.connected[index],{stdout:JSON.stringify({ok:true,defaultClient:client})})}
    function refresh(){source.refreshDefaultClient()}
    function explicit(){source.desktopId="thunderbird.desktop";source.refreshDefaultClient()}
    function injectedFailure(){metadata.failConnect=true;source.desktopId="";source.refreshDefaultClient()}
    function synchronous(){metadata.failConnect=true;metadata.failDisconnect=true;metadata.synchronousClient="own-other.desktop";source.refreshDefaultClient()}
    function clearFailure(){metadata.failConnect=false;metadata.failDisconnect=false;metadata.synchronousClient="";source.refreshDefaultClient()}
    function state(){return JSON.stringify({connected:metadata.connected.length,disconnected:metadata.disconnected.length,
        client:source.effectiveDesktopId,supported:source.supportedClient,pending:!!source.metadataCommand,
        dirty:source.metadataDirty,available:source.available,count:source.unreadCount})}
}''').encode(), QUrl.fromLocalFile(str(Path(os.environ["TMPDIR"]) / "own-mail-default.qml")))
    fixture = component.create(); assert fixture, "\n".join(error.toString() for error in component.errors())
    def invoke(method, *args):
        QMetaObject.invokeMethod(fixture, method, Qt.ConnectionType.DirectConnection,
            *(Q_ARG("QVariant", arg) for arg in args))
    def state():
        return json.loads(QMetaObject.invokeMethod(fixture, "state", Qt.ConnectionType.DirectConnection, Q_RETURN_ARG("QVariant")))
    checks = {}
    checks["startup_issues_one_metadata_read_without_fake_zero"] = state()["connected"] == 1 and state()["pending"] \
        and state()["count"] is None and not state()["available"]
    invoke("reply", 0, "thunderbird.desktop")
    checks["first_default_resolved"] = state()["supported"] and not state()["pending"]
    invoke("refresh")
    checks["explicit_refresh_hides_old_clients_badge_until_new_result"] = state()["client"] == "" and state()["count"] is None \
        and state()["connected"] == 2
    invoke("reply", 1, "own-other.desktop")
    checks["changed_global_default_never_keeps_thunderbird_source"] = state()["client"] == "own-other.desktop" and not state()["supported"]
    invoke("refresh"); invoke("refresh"); invoke("refresh")
    checks["overlapping_explicit_uses_coalesce_without_parallel_query"] = state()["connected"] == 3 and state()["dirty"]
    invoke("reply", 2, "thunderbird.desktop")
    checks["older_reply_not_exposed_and_one_fresh_query_follows"] = state()["client"] == "" and state()["connected"] == 4 and state()["pending"]
    invoke("reply", 2, "thunderbird.desktop")
    checks["duplicate_old_result_ignored"] = state()["connected"] == 4 and state()["pending"]
    invoke("reply", 3, "own-current.desktop")
    checks["fresh_result_recovers_without_poll"] = state()["client"] == "own-current.desktop" and not state()["pending"] and not state()["dirty"]
    invoke("explicit")
    checks["explicit_panel_choice_does_not_read_global_metadata"] = state()["connected"] == 4 and state()["supported"]
    invoke("injectedFailure")
    checks["connect_failure_releases_pending_without_retry"] = not state()["pending"] and not state()["dirty"] and state()["client"] == ""
    invoke("synchronous")
    checks["synchronous_result_then_connect_throw_keeps_known_result"] = state()["client"] == "own-other.desktop" and not state()["pending"]
    invoke("clearFailure"); invoke("reply", state()["connected"] - 1, "thunderbird.desktop")
    checks["later_explicit_use_recovers_after_boundary_failures"] = state()["supported"] and not state()["pending"]
    checks["no_qml_runtime_errors"] = not errors
    result = {"checks":checks,"qml_errors":errors,"scope":"Actual production MailState QML and injected metadata boundary; private D-Bus and directories; no client launch, profile or MIME writes.",
        "status":"passed" if all(checks.values()) else "failed"}
    print(json.dumps(result))
    fixture.deleteLater(); QCoreApplication.sendPostedEvents(None, QEvent.Type.DeferredDelete); app.processEvents()
    return 0 if all(checks.values()) else 1


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--worker", action="store_true", help=argparse.SUPPRESS)
    parser.add_argument("--output", type=Path)
    args = parser.parse_args()
    if args.worker: return worker()
    if args.output and (args.output.exists() or not args.output.resolve().is_relative_to("/tmp")):
        parser.error("Use a new result path under /tmp")
    with tempfile.TemporaryDirectory(prefix=".qa-mail-default-", dir=ROOT) as temp:
        base = Path(temp); env = dict(os.environ)
        for key in ("HOME","XDG_CONFIG_HOME","XDG_DATA_HOME","XDG_CACHE_HOME","XDG_STATE_HOME","XDG_RUNTIME_DIR","TMPDIR"):
            path=base/key.lower();path.mkdir(mode=0o700);env[key]=str(path)
        for key in ("DISPLAY","WAYLAND_DISPLAY","DBUS_SESSION_BUS_ADDRESS","QML_IMPORT_PATH","QML2_IMPORT_PATH","LD_PRELOAD"):
            env.pop(key,None)
        config=base/"bus.conf"
        config.write_text('<busconfig><type>session</type><listen>unix:tmpdir=/tmp</listen><auth>EXTERNAL</auth><policy context="default"><allow send_destination="*"/><allow receive_sender="*"/><allow own="*"/></policy></busconfig>')
        env.update(DOMAINOS_MAIL_DEFAULT_PRIVATE="1",QT_QPA_PLATFORM="offscreen",QT_QUICK_BACKEND="software",QT_QPA_PLATFORMTHEME="generic",
            QT_QUICK_CONTROLS_STYLE="Basic",QML_DISABLE_DISK_CACHE="1",PYTHONDONTWRITEBYTECODE="1",
            DBUS_SYSTEM_BUS_ADDRESS="unix:path="+str(base/"disabled-system"))
        result=subprocess.run(["dbus-run-session","--config-file",str(config),"--",sys.executable,str(Path(__file__).resolve()),"--worker"],
            env=env,capture_output=True,text=True,timeout=20)
        if args.output:
            report=json.loads(result.stdout)
            report["worker_returncode"]=result.returncode
            report["source_sha256"]={str(path.relative_to(ROOT)):hashlib.sha256(path.read_bytes()).hexdigest()
                for path in (UI/"DomainOSMailState.qml",UI/"DomainOSRuntime.qml",Path(__file__).resolve())}
            if result.returncode: report["status"]="failed"
            args.output.write_text(json.dumps(report,indent=2)+"\n");args.output.chmod(0o600)
        print(result.stdout);print(result.stderr,file=sys.stderr)
        return result.returncode


if __name__ == "__main__":
    sys.exit(main())
