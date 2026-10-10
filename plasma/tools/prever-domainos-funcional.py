#!/usr/bin/env python3
# SPDX-FileCopyrightText: 2026 IRIX Classic contributors
# SPDX-License-Identifier: GPL-3.0-or-later
"""Open the production DomainOS applet in a new, persistent private Xephyr.

The approved reference is displayed as an unchanged PNG; the lower panel uses
the production main.qml, KWin desktops, real task windows and native providers.
Close the outer Xephyr to stop only this preview's own processes. No installation,
real session bus, system bus, audio server or existing Xephyr is modified.
"""
import argparse
import configparser
import hashlib
import json
import os
from pathlib import Path
import re
import shlex
import shutil
import signal
import stat
import subprocess
import sys
import tempfile
import time

sys.dont_write_bytecode = True
REPO = Path(__file__).resolve().parents[2]
IDENTIFIER = "org.irixclassic.domainos.panel"
REFERENCE = Path("/tmp/irix-classic-domainos-prototipo-aprovado-20261008-160442/prints/PAINEL-APROVADO.png")
ERRORS = re.compile(r"ReferenceError:|TypeError:|SyntaxError:|Cannot assign|Binding loop|module .+ is not installed|is not a type|Type .+ unavailable|Image: Cannot open")
BUNDLE_RESOURCES = ("plasma/applets/" + IDENTIFIER, "plasma/applets/org.irixclassic.grosview",
    "plasma/IrixClassic", "plasma/IrixClassicDomainOS", "kvantum/IrixClassic")


def verified_bundle_resources():
    """Verify the whole portable package before reusing its read-only inputs.

    Package resources may already point to an older immutable package. Hashes
    cover their contents through the current package's relative manifest paths.
    """
    manifest = REPO / "PREVIEW.sha256"
    if not manifest.is_file() or manifest.is_symlink():
        raise RuntimeError("Linked resources require a portable package with PREVIEW.sha256")
    contents = manifest.read_bytes()
    verified = set()
    for line in contents.decode("utf-8").splitlines():
        if not line:
            continue
        match = re.fullmatch(r"([0-9a-f]{64})  (.+)", line)
        if not match:
            raise RuntimeError("Invalid portable package manifest entry")
        checksum, name = match.groups()
        relative = Path(name)
        if relative.is_absolute() or ".." in relative.parts or name in verified:
            raise RuntimeError("Invalid portable package manifest path: " + name)
        path = REPO / relative
        if not path.is_file() or hashlib.sha256(path.read_bytes()).hexdigest() != checksum:
            raise RuntimeError("Portable package integrity mismatch: " + name)
        verified.add(name)
    if not verified:
        raise RuntimeError("Portable package manifest is empty")
    for name in BUNDLE_RESOURCES:
        source = REPO / name
        if not source.is_dir():
            raise RuntimeError("Portable package resource missing: " + name)
        for path in source.rglob("*"):
            if path.is_symlink() and path.is_dir():
                raise RuntimeError("Nested resource directory links are not supported: " + str(path))
            if path.is_file() and path.relative_to(REPO).as_posix() not in verified:
                raise RuntimeError("Portable package resource is not covered by its manifest: " + str(path))
    return {"sha256":hashlib.sha256(contents).hexdigest(), "files":len(verified)}


def stage_resource(source, destination, linked=False):
    if linked:
        if source.relative_to(REPO).as_posix() not in BUNDLE_RESOURCES:
            raise RuntimeError("Only declared package resources may be linked")
        if destination.exists() or destination.is_symlink():
            raise RuntimeError("Private resource destination already exists")
        destination.parent.mkdir(parents=True, exist_ok=True)
        destination.symlink_to(source.resolve(), target_is_directory=True)
    else:
        ignore = shutil.ignore_patterns("__pycache__", "*.pyc") if source.parent == REPO / "plasma/applets" else None
        shutil.copytree(source, destination, ignore=ignore)

HOST_SOURCE = r'''// SPDX-License-Identifier: GPL-3.0-or-later
// Preview host only. Production QML is unchanged and stays interactive.
#include <QApplication>
#include <QAbstractItemModel>
#include <QFile>
#include <QFileSystemWatcher>
#include <QImage>
#include <QJsonArray>
#include <QJsonDocument>
#include <QJsonObject>
#include <QPointF>
#include <QPointer>
#include <QTimer>
#include <QWindow>
#include <dlfcn.h>
using Children=QList<QObject *> (*)(QObject *);
using Grab=QImage (*)(QWindow *);
using MapToScene=QPointF (*)(const QObject *,const QPointF &);
static int attempts=0;
static QWindow *configured=nullptr;
static QPointer<QObject> observedPanel;
static QObject *find(QObject *object, Children children, const QString &name="domainosPanel") {
    if(!object)return nullptr;
    if(object->objectName()==name)return object;
    if(object->inherits("QQuickItem"))for(auto child:children(object))if(auto match=find(child,children,name))return match;
    return nullptr;
}
static QObject *variantObject(const QVariant &value) {
    if(auto object=value.value<QObject *>())return object;
    if(QByteArray(value.metaType().name())=="QJSValue") {
        using ToObject=QObject *(*)(const void *);
        auto convert=reinterpret_cast<ToObject>(dlsym(RTLD_DEFAULT,"_ZNK8QJSValue9toQObjectEv"));
        if(convert)return convert(value.constData());
    }
    return nullptr;
}
static QJsonArray nativeTaskRows(QObject *controller, const char *property) {
    auto model=controller ? qobject_cast<QAbstractItemModel *>(variantObject(controller->property(property))) : nullptr;
    QJsonArray rows;if(!model)return rows;
    const auto roles=model->roleNames();int idsRole=-1;
    for(auto it=roles.begin();it!=roles.end();++it)if(it.value()=="WinIdList")idsRole=it.key();
    if(idsRole<0)return rows;
    for(int row=0;row<model->rowCount();++row) {
        const auto index=model->index(row,0);
        rows.append(QJsonObject{{"title",model->data(index,Qt::DisplayRole).toString()},
            {"window_ids",QJsonValue::fromVariant(model->data(index,idsRole))}});
    }
    return rows;
}
static QJsonObject captureState(QObject *panel,QWindow *host,Children children) {
    QVariant result;
    if(panel)QMetaObject::invokeMethod(panel,"diagnosticSnapshot",Qt::DirectConnection,Q_RETURN_ARG(QVariant,result));
    auto state=QJsonDocument::fromJson(result.toString().toUtf8()).object();
    auto tasks=panel ? find(panel,children,"domainosTasks") : nullptr;
    state["preview_tasks_model_found"]=tasks && variantObject(tasks->property("tasksModel"));
    state["preview_native_task_rows"]=nativeTaskRows(tasks,"tasksModel");
    state["preview_native_scope_rows"]=nativeTaskRows(tasks,"scopeModel");
    auto pager=panel ? find(panel,children,"domainosRealPager") : nullptr;
    state["preview_pager_current_desktop_id"]=pager ? pager->property("currentDesktopId").toString() : "";
    state["preview_host_window_id"]=host ? double(host->winId()) : 0;
    return state;
}
static void inspectRequested() {
    if(!configured || !observedPanel)return;
    QFile request(qEnvironmentVariable("IRIX_DOMAINOS_PREVIEW_REQUEST"));
    if(!request.open(QIODevice::ReadOnly))return;
    const auto token=QString::fromUtf8(request.readAll()).trimmed();
    auto children=reinterpret_cast<Children>(dlsym(RTLD_DEFAULT,"_ZNK10QQuickItem10childItemsEv"));
    auto state=captureState(observedPanel,configured,children);state["request_token"]=token;
    QFile report(qEnvironmentVariable("IRIX_DOMAINOS_PREVIEW_OBSERVATION"));
    if(report.open(QIODevice::WriteOnly))report.write(QJsonDocument(state).toJson());
}
static void inspect() {
    auto children=reinterpret_cast<Children>(dlsym(RTLD_DEFAULT,"_ZNK10QQuickItem10childItemsEv"));
    auto grab=reinterpret_cast<Grab>(dlsym(RTLD_DEFAULT,"_ZN12QQuickWindow10grabWindowEv"));
    QObject *panel=nullptr;QWindow *host=nullptr;
    if(children)for(auto window:QGuiApplication::allWindows()) {
        panel=find(window->property("contentItem").value<QObject *>(),children);
        if(panel){host=window;break;}
    }
    if(host && !configured) {
        configured=host;
        observedPanel=panel;
        host->setFlags(Qt::Tool|Qt::FramelessWindowHint);
        host->setTitle("DomainOS SR10.4 — painel funcional isolado");
        host->setGeometry(314,710,971,109);
        host->show();
        const auto request=qEnvironmentVariable("IRIX_DOMAINOS_PREVIEW_REQUEST");
        if(!request.isEmpty()) {
            auto watcher=new QFileSystemWatcher(QCoreApplication::instance());
            watcher->addPath(request);
            QObject::connect(watcher,&QFileSystemWatcher::fileChanged,inspectRequested);
        }
    }
    auto state=captureState(panel,host,children);
    if(++attempts<25 && (!panel || !state["timeAvailable"].toBool() || state["workspaceCount"].toInt()!=2 || state["catalogCount"].toInt()==0)) {
        QTimer::singleShot(350,inspect);return;
    }
    state["functional_composition_loaded"]=panel!=nullptr;
    auto map=reinterpret_cast<MapToScene>(dlsym(RTLD_DEFAULT,"_ZNK10QQuickItem10mapToSceneERK7QPointF"));
    QJsonArray tiles;
    if(panel && host && map)for(int index=0;index<2;++index) {
        if(auto tile=find(panel,children,"domainosDesktopTile_"+QString::number(index))) {
            const QPointF point=map(tile,QPointF(tile->property("width").toDouble()/2,tile->property("height").toDouble()/2));
            const QPoint global=host->mapToGlobal(point.toPoint());
            tiles.append(QJsonObject{{"position",index},{"desktop_id",tile->property("desktopId").toString()},
                {"x",global.x()},{"y",global.y()}});
        }
    }
    state["preview_pager_tiles"]=tiles;
    state["capture_saved"]=host && grab && grab(host).save(qEnvironmentVariable("IRIX_DOMAINOS_PREVIEW_PANEL"));
    state["qt_version"]=qVersion();
    QFile report(qEnvironmentVariable("IRIX_DOMAINOS_PREVIEW_STATE"));
    if(report.open(QIODevice::WriteOnly))report.write(QJsonDocument(state).toJson());
}
extern "C" int interceptedExec() asm("_ZN12QApplication4execEv");
extern "C" int interceptedExec() {
    auto original=reinterpret_cast<int (*)()>(dlsym(RTLD_NEXT,"_ZN12QApplication4execEv"));
    if(!original)return 2;
    QTimer::singleShot(1000,inspect);
    return original();
}
'''


def write_json(path, value):
    path.write_text(json.dumps(value, indent=2, ensure_ascii=False) + "\n")


def protected_hashes(paths):
    result = {}
    for value in paths:
        path = Path(value)
        try:
            result[value] = hashlib.sha256(path.read_bytes()).hexdigest() if path.is_file() else None
        except PermissionError:
            result[value] = "unreadable"
    return result


def preview_uid():
    uid = os.getuid()
    if uid == 0 or os.geteuid() != uid:
        raise RuntimeError("Run this private preview as the current unprivileged user")
    return uid


def create_private_runtime(output):
    uid = preview_uid()
    path = Path(tempfile.mkdtemp(prefix="irxd-" + str(uid) + "-", dir="/tmp"))
    path.chmod(0o700)
    record = {"path":str(path), "uid":uid, "mode":"0700", "nonce":os.urandom(16).hex(), "output":str(output)}
    write_json(path / "preview-owner.json", record)
    return record


def private_runtime(output, manifest, allow_missing=False):
    uid = preview_uid()
    record = manifest.get("private_runtime", {})
    path = Path(record.get("path", ""))
    if record.get("uid") != uid or record.get("output") != str(output) or not re.fullmatch(r"[0-9a-f]{32}", record.get("nonce", "")) \
            or path.parent != Path("/tmp") or not path.name.startswith("irxd-" + str(uid) + "-"):
        raise RuntimeError("Private runtime ownership record does not match this preview/UID")
    try:
        information = path.lstat()
    except FileNotFoundError:
        if allow_missing:
            return path
        raise RuntimeError("Private preview runtime is missing")
    if not stat.S_ISDIR(information.st_mode) or information.st_uid != uid or stat.S_IMODE(information.st_mode) != 0o700:
        raise RuntimeError("Private runtime must be an owned 0700 directory, without symlinks")
    marker = path / "preview-owner.json"
    marker_info = marker.lstat()
    if not stat.S_ISREG(marker_info.st_mode) or marker_info.st_uid != uid or json.loads(marker.read_text()) != record:
        raise RuntimeError("Private runtime marker does not match this preview")
    return path


def cleanup_private_runtime(output, manifest, remaining=()):
    # Never remove a runtime while recorded, ownership-confirmed children live.
    if remaining:
        return {"removed":False, "reason":"owned processes remain", "remaining":list(remaining)}
    try:
        path = private_runtime(output, manifest, allow_missing=True)
        absent = not path.exists()
        if not absent:
            shutil.rmtree(path)
        return {"path":str(path), "removed":True, "already_missing":absent, "uid":os.getuid()}
    except (OSError, ValueError, RuntimeError) as error:
        return {"removed":False, "reason":str(error)}


def read_preview_manifest(output):
    uid = preview_uid()
    information = output.lstat()
    if not output.is_relative_to(Path("/tmp")) or output == Path("/tmp") or not stat.S_ISDIR(information.st_mode) \
            or information.st_uid != uid or stat.S_IMODE(information.st_mode) != 0o700:
        raise RuntimeError("Private preview directory must be owned by this UID and have mode 0700")
    manifest = json.loads((output / "MANIFESTO.json").read_text())
    if manifest.get("uid") != uid:
        raise RuntimeError("Private preview manifest belongs to another UID")
    return manifest


def private_environment(output, manifest):
    env = os.environ.copy()
    for key in ("DISPLAY", "WAYLAND_DISPLAY", "DBUS_SESSION_BUS_ADDRESS", "DBUS_STARTER_ADDRESS", "DBUS_STARTER_BUS_TYPE", "SESSION_MANAGER", "LD_PRELOAD", "XAUTHORITY", "QML_IMPORT_PATH", "QML2_IMPORT_PATH", "QT_STYLE_OVERRIDE", "QT_QUICK_CONTROLS_STYLE", "KDE_FULL_SESSION", "KDE_SESSION_VERSION", "XDG_SESSION_ID", "SSH_AUTH_SOCK"):
        env.pop(key, None)
    for key, name in (("HOME", "home"), ("XDG_CONFIG_HOME", "config"), ("XDG_DATA_HOME", "data"), ("XDG_CACHE_HOME", "cache"), ("XDG_STATE_HOME", "state")):
        env[key] = str(output / name)
    env["XDG_RUNTIME_DIR"] = str(private_runtime(output, manifest))
    env.update(XDG_DATA_DIRS="/usr/local/share:/usr/share", XDG_CONFIG_DIRS="/etc/xdg", QT_QPA_PLATFORM="xcb", QT_QPA_PLATFORMTHEME="kde", QT_QUICK_BACKEND="software", KWIN_COMPOSE="N", XDG_SESSION_TYPE="x11", XDG_CURRENT_DESKTOP="NONE", DBUS_SYSTEM_BUS_ADDRESS="unix:path=" + str(output / "no-system-bus"), PULSE_SERVER="unix:" + str(output / "no-audio-server"))
    return env


def stop_owned(process):
    if process.poll() is not None:
        return
    process.terminate()
    try:
        process.wait(4)
    except subprocess.TimeoutExpired:
        process.kill()
        process.wait()


def verify_preview_pager(app, output, state, host, reference):
    """Keep only our preview clients on all desktops and click the native pager.

    These X11 commands inherit the worker's private DISPLAY/Xauthority. Every
    target is checked against its owning PID; no real panel is reconfigured.
    """
    def command(*arguments):
        return subprocess.run(arguments, check=True, capture_output=True,
                              text=True, timeout=3).stdout.strip()

    def property_value(window_id, name):
        return command("xprop", "-id", str(window_id), name).split("=", 1)[-1].strip()

    def viewable(window_id):
        return "Map State: IsViewable" in command("xwininfo", "-id", str(window_id))

    def wait_until(predicate, seconds=5):
        deadline = time.monotonic() + seconds
        while time.monotonic() < deadline:
            app.processEvents()
            if predicate():
                return True
            time.sleep(.02)
        return False

    observation_sequence = 0
    def observe_native_tasks():
        nonlocal observation_sequence
        observation_sequence += 1
        token = str(observation_sequence)
        (output / "preview-inspect-request").write_text(token)
        observed = {}
        def received():
            nonlocal observed
            try:
                observed = json.loads((output / "preview-observation.json").read_text())
            except (FileNotFoundError, json.JSONDecodeError):
                return False
            return observed.get("request_token") == token
        if not wait_until(received):
            raise RuntimeError("The private native TasksModel observation was not received")
        return observed

    def native_task_ids(observed):
        return {int(window_id) for key in ("preview_native_task_rows", "preview_native_scope_rows")
                for row in observed.get(key, []) for window_id in row.get("window_ids", [])}

    def settled_tasks(position, desktop_id):
        deadline = time.monotonic() + 5
        observed = {}
        while time.monotonic() < deadline:
            observed = observe_native_tasks()
            identifiers = native_task_ids(observed)
            # This preview starts exactly three regular test windows on area 1.
            # Wait for the asynchronous native filter as well as the pager UUID;
            # EWMH's current property alone can change before its UI model does.
            if observed.get("preview_tasks_model_found") and observed.get("preview_pager_current_desktop_id") == desktop_id \
                    and not ({panel_id,reference_id} & identifiers) and len(identifiers) == (3 if position == 0 else 0):
                return observed
            app.processEvents(); time.sleep(.02)
        raise RuntimeError("The private pager/TasksModel did not settle to the observed desktop: " + json.dumps(observed.get("preview_native_task_rows", [])))

    panel_id = int(state.get("preview_host_window_id", 0))
    reference_id = int(reference.winId())
    targets = (("panel", panel_id, host.pid), ("reference", reference_id, os.getpid()))
    report = {"scope":"Only the two preview-owned X11 clients in the private Xephyr/KWin session are made sticky; production QML and the live user session are unchanged.",
              "own_windows":{}, "clicks":[], "checks":{}}
    try:
        for name, window_id, pid in targets:
            if window_id <= 0 or property_value(window_id, "_NET_WM_PID") != str(pid):
                raise RuntimeError("Preview X11 window ownership was not confirmed: " + name)
            before = property_value(window_id, "_NET_WM_DESKTOP")
            command("xdotool", "set_desktop_for_window", str(window_id), "4294967295")
            confirmed = wait_until(lambda:property_value(window_id, "_NET_WM_DESKTOP") == "4294967295")
            report["own_windows"][name] = {"window_id":window_id,"pid":pid,"desktop_before":before,
                "desktop_after":property_value(window_id, "_NET_WM_DESKTOP"),"sticky_confirmed":confirmed}
            if not confirmed:
                raise RuntimeError("Private KWin did not confirm the sticky preview window: " + name)
        tiles = state.get("preview_pager_tiles", [])
        points = {entry["position"]:entry for entry in tiles}
        if set(points) != {0,1} or len({entry.get("desktop_id") for entry in tiles}) != 2 or any(not entry.get("desktop_id") for entry in tiles):
            raise RuntimeError("The preview did not expose both native pager tile identities")
        if int(command("xdotool", "get_desktop")) != 0:
            raise RuntimeError("The private preview did not start on its first desktop")
        report["initial_native_observation"] = settled_tasks(0, points[0]["desktop_id"])
        report["initial_capture_saved"] = app.primaryScreen().grabWindow(0).save(str(output / "PAGER-ANTES.png"))
        for sequence, position in enumerate((1,0,1,0),1):
            point = points[position]
            command("xdotool", "mousemove", "--sync", str(point["x"]), str(point["y"]), "click", "1")
            activated = wait_until(lambda:int(command("xdotool", "get_desktop")) == position)
            shown = wait_until(lambda:viewable(panel_id) and viewable(reference_id))
            observed = settled_tasks(position, point["desktop_id"])
            capture = "PAGER-CLIQUE-" + str(sequence) + ".png"
            record = {"requested_position":position,"clicked_desktop_id":point["desktop_id"],
                "native_position":int(command("xdotool", "get_desktop")),"activated":activated,
                "panel_viewable":viewable(panel_id),"reference_viewable":viewable(reference_id),
                "both_viewable_confirmed":shown,"panel_process_alive":host.poll() is None,
                "native_task_rows":observed["preview_native_task_rows"],"native_scope_rows":observed["preview_native_scope_rows"],
                "own_preview_ids_absent_from_tasks":not ({panel_id,reference_id} & native_task_ids(observed)),
                "native_pager_uuid_observed":observed["preview_pager_current_desktop_id"],
                "capture":capture,"capture_saved":app.primaryScreen().grabWindow(0).save(str(output / capture))}
            report["clicks"].append(record)
            if not activated or not shown or host.poll() is not None:
                raise RuntimeError("The private preview did not remain visible after its native pager click")
        report["checks"] = {
            "own_panel_sticky_confirmed":report["own_windows"]["panel"]["sticky_confirmed"],
            "own_reference_sticky_confirmed":report["own_windows"]["reference"]["sticky_confirmed"],
            "four_actual_native_pager_clicks_observed":len(report["clicks"]) == 4 and all(row["activated"] for row in report["clicks"]),
            "own_panel_and_reference_visible_on_both_desktops":all(row["panel_viewable"] and row["reference_viewable"] for row in report["clicks"]),
            "own_panel_process_alive_during_switches":all(row["panel_process_alive"] for row in report["clicks"]),
            "own_preview_windows_are_not_tasks":all(row["own_preview_ids_absent_from_tasks"] for row in report["clicks"]),
            "native_task_filter_and_pager_uuid_settle_before_capture":all(len(row["native_scope_rows"]) == (3 if row["requested_position"] == 0 else 0)
                and row["native_pager_uuid_observed"] == row["clicked_desktop_id"] for row in report["clicks"]),
            "private_desktop_returns_to_first":int(command("xdotool", "get_desktop")) == 0,
            "before_and_all_switch_captures_saved":report["initial_capture_saved"] and all(row["capture_saved"] for row in report["clicks"])}
        report["status"] = "passed" if all(report["checks"].values()) else "failed"
    except Exception as error:
        report["status"] = "failed"
        report["error"] = str(error)
        raise
    finally:
        write_json(output / "PAGER-VERIFICACAO.json", report)
    return report


def cleanup_recorded_children(output, manifest):
    """Stop only recorded PIDs that still belong to this exact private profile."""
    paths = (output / "FILHOS.json", output / "PRONTO.json")
    pids = set()
    for path in paths:
        if path.is_file():
            record = json.loads(path.read_text())
            pids.update(record.get("process_pids", []))
            if record.get("worker_pid"): pids.add(record["worker_pid"])
    def owned_live(pid):
        try:
            values = dict(part.split(b"=", 1) for part in Path("/proc", str(pid), "environ").read_bytes().split(b"\0") if b"=" in part)
            state = Path("/proc", str(pid), "stat").read_text().rsplit(")", 1)[1].split()[0]
            return state != "Z" and values.get(b"HOME") == str(output / "home").encode() and values.get(b"DISPLAY") == manifest["display"].encode() \
                and values.get(b"XDG_RUNTIME_DIR") == manifest["private_runtime"]["path"].encode()
        except (FileNotFoundError, ProcessLookupError, PermissionError):
            return False
    for sig in (signal.SIGTERM, signal.SIGKILL):
        for pid in pids:
            if owned_live(pid):
                try: os.kill(pid, sig)
                except ProcessLookupError: pass
        deadline = time.monotonic() + (3 if sig == signal.SIGTERM else 1)
        while time.monotonic() < deadline:
            # A supervisor may have adopted these children after Qt's fatal X11
            # disconnect. Reap our own orphans, never unrelated children.
            for pid in pids:
                try: os.waitpid(pid, os.WNOHANG)
                except (ChildProcessError, ProcessLookupError): pass
            if not any(owned_live(pid) for pid in pids): break
            time.sleep(.05)
    return [pid for pid in pids if owned_live(pid)]


def cleanup_guard(output):
    manifest = read_preview_manifest(output)
    xephyr = json.loads((output / "PROCESSOS.json").read_text())["xephyr"]
    write_json(output / "GUARDIAO.json", {"status":"watching","pid":os.getpid(),"display":manifest["display"]})
    while True:
        try: command = Path("/proc", str(xephyr), "cmdline").read_bytes().split(b"\0")
        except FileNotFoundError: break
        if not command or Path(command[0].decode()).name != "Xephyr" or manifest["display"].encode() not in command: break
        time.sleep(.3)
    remaining = cleanup_recorded_children(output, manifest)
    runtime_cleanup = cleanup_private_runtime(output, manifest, remaining)
    write_json(output / "GUARDIAO.json", {"status":"closed","pid":os.getpid(),"display":manifest["display"],"owned_live_remaining":remaining,"runtime_cleanup":runtime_cleanup})
    return 1 if remaining or not runtime_cleanup["removed"] else 0


def worker(output):
    if os.environ.get("IRIX_DOMAINOS_FUNCTIONAL_PRIVATE") != "1":
        raise RuntimeError("Private preview session required")
    from PyQt6.QtCore import Qt
    from PyQt6.QtGui import QPixmap
    from PyQt6.QtWidgets import QApplication, QLabel, QVBoxLayout, QWidget
    app = QApplication([])
    app.setQuitOnLastWindowClosed(False)
    processes, logs = [], []
    manifest = read_preview_manifest(output)
    if os.environ.get("XDG_RUNTIME_DIR") != str(private_runtime(output, manifest)) or os.environ.get("DISPLAY") != manifest["display"]:
        raise RuntimeError("Private preview environment does not match its recorded runtime/display")
    def requested_stop(signum, frame): raise SystemExit(0)
    signal.signal(signal.SIGTERM, requested_stop)
    signal.signal(signal.SIGINT, requested_stop)
    def start(name, command, environment=None):
        log = (output / (name + ".log")).open("w")
        logs.append(log)
        process = subprocess.Popen(command, env=environment, stdout=log, stderr=subprocess.STDOUT)
        processes.append(process)
        write_json(output / "FILHOS.json", {"worker_pid":os.getpid(),"process_pids":[child.pid for child in processes]})
        return process
    try:
        kwin = start("kwin", ["kwin_x11"])
        for _ in range(120):
            if kwin.poll() is not None:
                raise RuntimeError("Private KWin exited during startup")
            probe = subprocess.run(["qdbus6", "org.kde.KWin", "/VirtualDesktopManager"], capture_output=True, timeout=2)
            if probe.returncode == 0:
                break
            app.processEvents(); time.sleep(.05)
        else:
            raise RuntimeError("Private KWin did not become ready")
        activity = shutil.which("kactivitymanagerd") or "/usr/lib/x86_64-linux-gnu/libexec/kactivitymanagerd"
        start("activities", [activity])
        start("systemstats", ["ksystemstats", "--remain"])
        subprocess.run(["xsetroot", "-solid", manifest["background"]], check=True, capture_output=True)
        reference = QWidget(flags=Qt.WindowType.Tool)
        reference.setWindowTitle("Referência aprovada — imagem estática, sem ações")
        layout = QVBoxLayout(reference); layout.setContentsMargins(0, 0, 0, 0); layout.setSpacing(0)
        caption = QLabel("REFERÊNCIA APROVADA · PNG original · 971 × 109")
        caption.setAlignment(Qt.AlignmentFlag.AlignCenter); caption.setFixedHeight(28)
        label = QLabel(); label.setPixmap(QPixmap(str(output / "REFERENCIA-APROVADA.png")))
        label.setFixedSize(971, 109); layout.addWidget(caption); layout.addWidget(label)
        reference.setFixedSize(971, 137); reference.move(314, 45); reference.show()
        for index, x in enumerate((64, 570, 1076)):
            title = "DomainOS teste " + chr(65 + index)
            environment = dict(os.environ, PS1=title + " $ ")
            start("terminal-" + str(index), ["xterm", "-T", title, "-name", "domainos-preview-" + str(index), "-geometry", "44x17+" + str(x) + "+285", "-fa", "monospace", "-fs", "13", "-bg", manifest["background"], "-fg", manifest["foreground"], "-e", "/bin/bash", "--noprofile", "--norc"], environment)
        (output / "preview-inspect-request").write_text("0")
        host_env = dict(os.environ, LD_PRELOAD=str(output / "preview-host.so"), IRIX_DOMAINOS_PREVIEW_STATE=str(output / "ESTADO-NATIVO.json"), IRIX_DOMAINOS_PREVIEW_PANEL=str(output / "PAINEL-FUNCIONAL.png"),
            IRIX_DOMAINOS_PREVIEW_REQUEST=str(output / "preview-inspect-request"), IRIX_DOMAINOS_PREVIEW_OBSERVATION=str(output / "preview-observation.json"))
        host = start("panel", ["plasmawindowed", IDENTIFIER], host_env)
        deadline = time.monotonic() + 20
        while not (output / "ESTADO-NATIVO.json").is_file() and time.monotonic() < deadline:
            if host.poll() is not None:
                raise RuntimeError("Native panel exited during startup")
            app.processEvents(); time.sleep(.02)
        if not (output / "ESTADO-NATIVO.json").is_file():
            raise RuntimeError("Native panel did not produce its initialization report")
        state = json.loads((output / "ESTADO-NATIVO.json").read_text())
        pager_proof = verify_preview_pager(app, output, state, host, reference)
        diagnostics = [line for line in (output / "panel.log").read_text().splitlines() if ERRORS.search(line)]
        after = protected_hashes(manifest["protected_before"])
        checks = {"production_main_loaded":state.get("functional_composition_loaded") is True,
            "functional_phase":state.get("phase") == "functional-integration",
            "two_private_kwin_desktops":state.get("workspaceCount") == 2,
            "three_own_test_windows_running":all(process.poll() is None for process in processes[-4:-1]),
            "native_tray_available":state.get("tray", {}).get("available") is True,
            "no_startup_commands":state.get("activity") == {"lit":False,"pending":0} and state.get("commands") == {},
            "approved_png_copy_unchanged":hashlib.sha256((output / "REFERENCIA-APROVADA.png").read_bytes()).hexdigest() == manifest["reference_sha256"],
            "protected_hashes_unchanged":after == manifest["protected_before"],
            "qml_errors_zero":not diagnostics}
        checks["private_preview_stays_visible_when_native_pager_switches"] = pager_proof["status"] == "passed"
        capture = app.primaryScreen().grabWindow(0)
        checks["full_private_screen_capture"] = not capture.isNull() and capture.save(str(output / "PREVIA-FUNCIONAL.png"))
        report = {"status":"open" if all(checks.values()) else "failed", "checks":checks, "state":state,
            "qml_diagnostics":diagnostics, "protected_after":after, "pager_visibility_proof":str(output / "PAGER-VERIFICACAO.json"),
            "scope":"Production QML and native KWin/task/tray APIs in private Xephyr. The preview-owned panel/reference windows stay visible on both private desktops. Hardware services, audio and the real user bus are unavailable."}
        write_json(output / "RESULTADO.json", report)
        if not all(checks.values()):
            raise RuntimeError("Preview startup checks failed; see RESULTADO.json")
        write_json(output / "PRONTO.json", {"display":os.environ["DISPLAY"],"worker_pid":os.getpid(),"panel_pid":host.pid,"process_pids":[process.pid for process in processes],"result":str(output / "RESULTADO.json")})
        while True:
            app.processEvents(); time.sleep(.02)
    except Exception as error:
        write_json(output / "ERRO.json", {"error":str(error)})
        return 1
    finally:
        for process in reversed(processes): stop_owned(process)
        for log in logs: log.close()


def supervisor(output):
    manifest = read_preview_manifest(output)
    env = private_environment(output, manifest)
    outer_env = dict(env, DISPLAY=manifest["outer_display"])
    if manifest.get("outer_xauthority"):
        outer_env["XAUTHORITY"] = manifest["outer_xauthority"]
    env.update(DISPLAY=manifest["display"], XAUTHORITY=str(output / "Xauthority"), IRIX_DOMAINOS_FUNCTIONAL_PRIVATE="1")
    processes = []
    # Adopt only descendants from this supervisor when a Qt X11 client exits
    # abruptly; headless --remain services can otherwise outlive the worker.
    import ctypes
    ctypes.CDLL(None).prctl(36, 1, 0, 0, 0)  # PR_SET_CHILD_SUBREAPER
    def requested_stop(signum, frame): raise SystemExit(0)
    signal.signal(signal.SIGTERM, requested_stop)
    signal.signal(signal.SIGINT, requested_stop)
    try:
        with (output / "xephyr.log").open("w") as log:
            xephyr = subprocess.Popen(["Xephyr", manifest["display"], "-screen", "1600x850", "-auth", str(output / "Xauthority"), "-nolisten", "tcp", "-noreset", "-br", "-title", manifest["title"] + "; feche para encerrar"], env=outer_env, stdout=log, stderr=subprocess.STDOUT)
        processes.append(xephyr)
        for _ in range(100):
            if xephyr.poll() is not None:
                raise RuntimeError("New Xephyr failed to start")
            probe = subprocess.run(["xdpyinfo", "-display", manifest["display"]], env=env, capture_output=True, timeout=2)
            if probe.returncode == 0: break
            time.sleep(.05)
        else:
            raise RuntimeError("New Xephyr did not become ready")
        with (output / "session.log").open("w") as log:
            session = subprocess.Popen(["dbus-run-session", "--config-file", str(output / "bus.conf"), "--", sys.executable, str(Path(__file__).resolve()), "--saida", str(output), "--worker"], env=env, stdout=log, stderr=subprocess.STDOUT, start_new_session=True)
        processes.append(session)
        write_json(output / "PROCESSOS.json", {"supervisor":os.getpid(),"xephyr":xephyr.pid,"private_session":session.pid,"display":manifest["display"]})
        while xephyr.poll() is None and session.poll() is None: time.sleep(.2)
    except Exception as error:
        write_json(output / "ERRO.json", {"error":str(error)})
        return 1
    finally:
        # This group was created exclusively for this D-Bus worker. Its child
        # applications inherit the private display, paths and buses.
        if len(processes) > 1 and processes[1].poll() is None:
            try: os.killpg(processes[1].pid, signal.SIGTERM)
            except ProcessLookupError: pass
            try: processes[1].wait(5)
            except subprocess.TimeoutExpired:
                os.killpg(processes[1].pid, signal.SIGKILL); processes[1].wait()
        for process in reversed(processes): stop_owned(process)
        remaining = cleanup_recorded_children(output, manifest)
        runtime_cleanup = cleanup_private_runtime(output, manifest, remaining)
        before = manifest["protected_before"]
        after = protected_hashes(before)
        write_json(output / "ENCERRADO.json", {"protected_before":before,"protected_after":after,"protected_hashes_unchanged":before == after,"own_processes_stopped":not remaining,"owned_live_remaining":remaining,"runtime_cleanup":runtime_cleanup})


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--saida", type=Path, required=True, help="New private directory under /tmp")
    parser.add_argument("--referencia", type=Path, default=REFERENCE, help="Approved reference PNG; read and copied only")
    parser.add_argument("--esquema", default="DomainOS-SR10.4", help="Color scheme stem in repository colors/")
    parser.add_argument("--titulo", default="DomainOS — integração funcional isolada", help="Outer Xephyr window title")
    parser.add_argument("--worker", action="store_true", help=argparse.SUPPRESS)
    parser.add_argument("--supervisor", action="store_true", help=argparse.SUPPRESS)
    parser.add_argument("--cleanup-guard", action="store_true", help=argparse.SUPPRESS)
    parser.add_argument("--recursos-do-pacote", action="store_true", help=argparse.SUPPRESS)
    args = parser.parse_args(); output = args.saida.resolve()
    try: uid = preview_uid()
    except RuntimeError as error: parser.error(str(error))
    if args.worker: return worker(output)
    if args.supervisor: return supervisor(output)
    if args.cleanup_guard:
        if not output.is_relative_to(Path("/tmp")): parser.error("Private preview required")
        return cleanup_guard(output)
    if not output.is_relative_to(Path("/tmp")) or output == Path("/tmp") or output.exists(): parser.error("Use a new directory under /tmp")
    package_resources = None
    if args.recursos_do_pacote:
        try: package_resources = verified_bundle_resources()
        except (OSError, UnicodeError, RuntimeError) as error: parser.error(str(error))
    reference = args.referencia.resolve()
    if not reference.is_file() or reference.suffix.lower() != ".png": parser.error("Reference must be an existing PNG")
    if not re.fullmatch(r"[A-Za-z0-9_.-]+", args.esquema): parser.error("Invalid color scheme stem")
    scheme_path = REPO / "colors" / (args.esquema + ".colors")
    if not scheme_path.is_file(): parser.error("Color scheme not found in repository")
    if not os.environ.get("DISPLAY"): parser.error("Run from the graphical session with DISPLAY set")
    for executable in ("Xephyr", "kwin_x11", "plasmawindowed", "qdbus6", "dbus-run-session", "xterm", "xauth", "xdpyinfo", "xsetroot", "ksystemstats", "c++", "pkg-config", "xdotool", "xprop", "xwininfo"):
        if not shutil.which(executable): parser.error("Missing executable: " + executable)
    # Reserve a separate display; never remove an X lock or reuse existing :4.
    display = next((number for number in range(60, 100) if not Path("/tmp/.X"+str(number)+"-lock").exists() and not Path("/tmp/.X11-unix/X"+str(number)).exists()), None)
    if display is None: parser.error("No unused preview display found")
    config = Path(os.environ.get("XDG_CONFIG_HOME", str(Path.home() / ".config")))
    paths = [str(config / name) for name in ("kdeglobals", "plasmarc", "kwinrc", "plasma-org.kde.plasma.desktop-appletsrc")]
    before = protected_hashes(paths)
    output.mkdir(mode=0o700)
    for name in ("home", "config", "data", "cache", "state"): (output / name).mkdir(mode=0o700)
    shutil.copyfile(reference, output / "REFERENCIA-APROVADA.png")
    data = output / "data"
    for name in (IDENTIFIER, "org.irixclassic.grosview"):
        stage_resource(REPO / "plasma/applets" / name, data / "plasma/plasmoids" / name, args.recursos_do_pacote)
    for name in ("IrixClassic", "IrixClassicDomainOS"):
        stage_resource(REPO / "plasma" / name, data / "plasma/desktoptheme" / name, args.recursos_do_pacote)
    for source, name in ((REPO / "icons/themes/IrixClassic-SGI", "IrixClassic-SGI"), (REPO / "icons/Irixium", "Irixium")):
        # Icon themes are public, read-only inputs. Link them into the private
        # search path instead of creating ~28,000 files for every preview.
        # All writable KDE settings/caches remain in this preview's own roots.
        destination = data / "icons" / name
        destination.parent.mkdir(parents=True, exist_ok=True)
        destination.symlink_to(source.resolve(), target_is_directory=True)
    decoration = data / "aurorae/themes/irixium_irix_classic_v4"
    shutil.copytree(REPO / "decorations/classic/package", decoration)
    metadata = json.loads((decoration / "metadata.json").read_text()); metadata["KPlugin"]["Id"] = decoration.name
    write_json(decoration / "metadata.json", metadata)
    stage_resource(REPO / "kvantum/IrixClassic", output / "config/Kvantum/IrixClassic", args.recursos_do_pacote)
    (output / "config/Kvantum/kvantum.kvconfig").write_text("[General]\ntheme=IrixClassic\n")
    scheme = configparser.ConfigParser(interpolation=None); scheme.optionxform = str; scheme.read(scheme_path)
    scheme["Icons"] = {"Theme":"IrixClassic-SGI"}
    scheme["KDE"] = {"widgetStyle":"Breeze"}
    with (output / "config/kdeglobals").open("w") as handle: scheme.write(handle)
    (output / "config/plasmarc").write_text("[Theme]\nname=IrixClassicDomainOS\n")
    (output / "config/kwinrc").write_text("[Desktops]\nNumber=2\nName_1=Work\nName_2=Procrastination\n[Compositing]\nEnabled=false\n[org.kde.kdecoration2]\nlibrary=org.kde.kwin.aurorae\ntheme=irixium_irix_classic_v4\nButtonsOnLeft=M\nButtonsOnRight=IA\n")
    (output / "bus.conf").write_text('<busconfig><type>session</type><listen>unix:tmpdir=/tmp</listen><auth>EXTERNAL</auth><policy context="default"><allow send_destination="*"/><allow receive_sender="*"/><allow own="*"/></policy></busconfig>')
    subprocess.run(["xauth", "-f", str(output / "Xauthority"), "add", ":"+str(display), "MIT-MAGIC-COOKIE-1", os.urandom(16).hex()], check=True, capture_output=True)
    (output / "preview-host.cpp").write_text(HOST_SOURCE)
    flags = shlex.split(subprocess.check_output(["pkg-config", "--cflags", "--libs", "Qt6Widgets"], text=True))
    subprocess.run(["c++", "-std=c++17", "-shared", "-fPIC", str(output / "preview-host.cpp"), "-o", str(output / "preview-host.so"), *flags, "-ldl"], check=True)
    def color(section, key): return "#" + "".join(f"{int(channel):02x}" for channel in scheme[section][key].split(",")[:3])
    runtime = create_private_runtime(output)
    manifest = {"uid":uid,"private_runtime":runtime,"display":":"+str(display),"outer_display":os.environ["DISPLAY"],"outer_xauthority":os.environ.get("XAUTHORITY"),"scheme":args.esquema,"title":args.titulo,
        "background":color("Colors:Window","BackgroundNormal"),"foreground":color("Colors:Window","ForegroundNormal"),"protected_before":before,
        "package_resources_linked":bool(package_resources), "verified_package_manifest":package_resources,
        "reference_source":str(reference),"reference_sha256":hashlib.sha256(reference.read_bytes()).hexdigest(),"production_main_sha256":hashlib.sha256((REPO / "plasma/applets" / IDENTIFIER / "contents/ui/main.qml").read_bytes()).hexdigest()}
    try:
        write_json(output / "MANIFESTO.json", manifest)
        with (output / "supervisor.log").open("w") as log:
            process = subprocess.Popen([sys.executable, str(Path(__file__).resolve()), "--saida", str(output), "--supervisor"], stdout=log, stderr=subprocess.STDOUT, start_new_session=True)
    except BaseException:
        cleanup_private_runtime(output, manifest)
        raise
    deadline = time.monotonic() + 30
    while time.monotonic() < deadline:
        if (output / "PRONTO.json").is_file():
            ready = json.loads((output / "PRONTO.json").read_text())
            print(json.dumps({"status":"open","display":ready["display"],"supervisor_pid":process.pid,"result":str(output / "RESULTADO.json"),"capture":str(output / "PREVIA-FUNCIONAL.png")}, ensure_ascii=False))
            return 0
        if (output / "ERRO.json").is_file() or process.poll() is not None:
            print((output / "ERRO.json").read_text() if (output / "ERRO.json").is_file() else "Preview supervisor exited", file=sys.stderr)
            return 1
        time.sleep(.1)
    print("Preview startup timed out; inspect " + str(output / "supervisor.log"), file=sys.stderr)
    # Stop this supervisor only; its finally block stops its own nested session.
    process.terminate(); process.wait(8)
    return 1


if __name__ == "__main__": raise SystemExit(main())
