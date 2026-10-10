#!/usr/bin/env python3
# SPDX-License-Identifier: GPL-3.0-or-later
"""Exercise Qt keyboard/focus behavior on the production controls, isolated."""
import argparse
import hashlib
import json
import os
from pathlib import Path
import sys
import tempfile

sys.dont_write_bytecode=True
REPO=Path(__file__).resolve().parents[2]

def main():
    parser=argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--saida",type=Path,required=True)
    output=parser.parse_args().saida.resolve()
    if output.exists() or not output.is_relative_to(Path("/tmp")): parser.error("Use a new /tmp output directory")
    output.mkdir(mode=0o700)
    config=Path(os.environ.get("XDG_CONFIG_HOME",Path.home()/".config"))
    def hashes():
        return {name:hashlib.sha256((config/name).read_bytes()).hexdigest() if (config/name).is_file() else None
            for name in ("kdeglobals","plasmarc","kwinrc","plasma-org.kde.plasma.desktop-appletsrc")}
    before=hashes();checks={};warnings=[];error=None
    def require(name,value):
        checks[name]=bool(value)
        if not value:raise AssertionError(name)
    with tempfile.TemporaryDirectory(prefix="irix-domainos-keyboard-") as folder:
        private=Path(folder)
        for key,name in (("HOME","home"),("XDG_CONFIG_HOME","config"),("XDG_DATA_HOME","data"),("XDG_CACHE_HOME","cache"),("XDG_RUNTIME_DIR","runtime")):
            path=private/name;path.mkdir(mode=0o700);os.environ[key]=str(path)
        for key in ("DISPLAY","WAYLAND_DISPLAY","LD_PRELOAD","QT_STYLE_OVERRIDE","QML_IMPORT_PATH","QML2_IMPORT_PATH"):
            os.environ.pop(key,None)
        os.environ.update(QT_QPA_PLATFORM="offscreen",QT_QPA_PLATFORMTHEME="generic",QT_QUICK_BACKEND="software",
            QT_QUICK_CONTROLS_STYLE="Basic",XDG_CURRENT_DESKTOP="NONE",
            DBUS_SESSION_BUS_ADDRESS="unix:path="+str(private/"disabled-session"),DBUS_SYSTEM_BUS_ADDRESS="unix:path="+str(private/"disabled-system"))
        from PyQt6 import sip
        from PyQt6.QtCore import Qt,QUrl,QMetaObject,Q_RETURN_ARG
        from PyQt6.QtGui import QGuiApplication
        from PyQt6.QtQml import QQmlApplicationEngine
        from PyQt6.QtQuick import QQuickWindow
        from PyQt6.QtTest import QTest
        app=QGuiApplication([sys.argv[0]]);engine=QQmlApplicationEngine()
        engine.warnings.connect(lambda messages:warnings.extend(message.toString() for message in messages))
        engine.load(QUrl.fromLocalFile(str(REPO/"plasma/tests/DomainOSKeyboardPreview.qml")))
        try:
            require("production_controls_loaded",bool(engine.rootObjects()))
            window=sip.cast(engine.rootObjects()[0],QQuickWindow)
            def settle():app.processEvents();QTest.qWait(30);app.processEvents()
            def descendants(node):
                yield node
                for child in node.childItems():yield from descendants(child)
            def item(name):return next(node for node in descendants(window.contentItem()) if node.objectName()==name)
            def state():return json.loads(QMetaObject.invokeMethod(window,"uiState",Qt.ConnectionType.DirectConnection,Q_RETURN_ARG("QVariant")))
            settle();window.requestActivate();settle()
            instrument=item("domainosKeyboardInstrument")
            instrument.forceActiveFocus();settle()
            require("keyboard_instrument_receives_focus",instrument.hasActiveFocus())
            QTest.keyPress(window,Qt.Key.Key_Space);app.processEvents()
            require("space_relief_is_immediate",instrument.property("pressed") and instrument.property("pressOffset")==2
                and window.property("instrumentClicks")==0)
            QTest.keyRelease(window,Qt.Key.Key_Space);settle()
            require("space_release_runs_action_once",not instrument.property("pressed") and window.property("instrumentClicks")==1)
            QTest.keyPress(window,Qt.Key.Key_Space);QTest.keyClick(window,Qt.Key.Key_Tab);settle()
            require("tab_moves_focus_and_cancels_pending_action",not instrument.hasActiveFocus() and not instrument.property("pressed")
                and window.property("instrumentCancels")==1)
            QTest.keyRelease(window,Qt.Key.Key_Space);settle()
            require("release_after_focus_loss_does_not_execute",window.property("instrumentClicks")==1)
            instrument.forceActiveFocus();QTest.keyClick(window,Qt.Key.Key_Return);settle()
            require("enter_runs_instrument_action_once",window.property("instrumentClicks")==2)
            target=item("domainosLiveTask_window:6");target.forceActiveFocus();settle()
            require("task_cell_receives_keyboard_focus",target.hasActiveFocus())
            initial_requests=len(state()["requests"])
            QTest.keyClick(window,Qt.Key.Key_Space);settle()
            require("space_selects_task_without_activating",state()["selected"]==["window:6"] and len(state()["requests"])==initial_requests)
            target.forceActiveFocus();QTest.keyClick(window,Qt.Key.Key_Return);settle()
            require("enter_requests_task_activation",state()["requests"][-1]["action"]=="activate" and state()["requests"][-1]["ids"]==[6])
            target.forceActiveFocus();QTest.keyClick(window,Qt.Key.Key_Menu);settle()
            require("menu_key_opens_context_without_changing_selection",state()["menu"] and state()["selected"]==["window:6"])
            require("keyboard_capture_saved",window.grabWindow().save(str(output/"KEYBOARD-CONTEXT.png")))
            QTest.keyClick(window,Qt.Key.Key_Escape);settle()
            require("escape_closes_context_without_action",not state()["menu"] and len(state()["requests"])==initial_requests+1)
            require("qml_diagnostics_zero",not warnings)
            window.close();app.processEvents()
        except Exception as exc:error=str(exc)
    after=hashes();checks["host_configs_unchanged"]=before==after
    report={"status":"passed" if all(checks.values()) and error is None else "failed","checks":checks,"error":error,
        "qml_diagnostics":warnings,"protected_configs":{"before":before,"after":after},
        "scope":"Production controls with Qt keyboard events; task provider is a private double. Native activation is verified separately."}
    (output/"RESULTADO.json").write_text(json.dumps(report,indent=2,ensure_ascii=False)+"\n")
    print(json.dumps({"status":report["status"],"checks":len(checks),"result":str(output/"RESULTADO.json"),"error":error}))
    return 0 if report["status"]=="passed" else 1

if __name__=="__main__":raise SystemExit(main())
