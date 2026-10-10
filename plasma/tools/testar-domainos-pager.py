#!/usr/bin/env python3
# SPDX-FileCopyrightText: 2026 mrmmx31
# SPDX-License-Identifier: GPL-3.0-or-later
"""Test the real DomainOS Pager against private KWin/X11, Xvfb and D-Bus.

Only the private compositor receives desktop/window operations. The component
under test is production QML; no mocked desktop or task models are supplied.
"""
import argparse
import hashlib
import json
import os
from pathlib import Path
import re
import shutil
import subprocess
import sys
import tempfile
import time

sys.dont_write_bytecode = True
REPO = Path(__file__).resolve().parents[2]
APPLET = REPO / "plasma/applets/org.irixclassic.domainos.panel"


def digest(path):
    return hashlib.sha256(path.read_bytes()).hexdigest() if path.is_file() else None


def setup(args):
    output = args.saida.resolve() if args.saida else Path(tempfile.mkdtemp(prefix="irix-domainos-pager-"))
    if output.exists() and any(output.iterdir()):
        raise SystemExit("Output directory must be new or empty")
    output.mkdir(parents=True, exist_ok=True)
    for tool in ("kwin_x11", "xvfb-run", "dbus-run-session", "qdbus6", "xdotool"):
        if not shutil.which(tool):
            raise SystemExit("Missing native test tool: " + tool)
    original_config = Path(os.environ.get("XDG_CONFIG_HOME", str(Path.home() / ".config")))
    protected = [] if args.crud_dialogs_only else [original_config / name for name in ("kdeglobals", "plasmarc", "kwinrc", "kcmfonts", "plasma-org.kde.plasma.desktop-appletsrc")]
    before = {str(path): digest(path) for path in protected}
    temporary = tempfile.TemporaryDirectory(prefix=".qa-pager-crud-", dir=REPO) if args.crud_dialogs_only else None
    fixture_root = Path(temporary.name) if temporary else output / "fixture"
    paths = {name: fixture_root / name for name in ("home", "config", "data", "cache", "state", "runtime")}
    for path in paths.values():
        path.mkdir(mode=0o700, parents=True)
    (paths["config"] / "kwinrc").write_text("[Desktops]\nNumber=1\nRows=1\nName_1=Start\n[Compositing]\nEnabled=false\n[org.kde.kdecoration2]\nlibrary=org.kde.breeze\n")
    (paths["config"] / "kdeglobals").write_text((REPO / "colors/DomainOS-SR10.4.colors").read_text())
    bus = fixture_root / "private-bus.conf"
    bus.write_text('<busconfig><type>session</type><listen>unix:tmpdir=/tmp</listen><auth>EXTERNAL</auth><policy context="default"><allow send_destination="*"/><allow receive_sender="*"/><allow own="*"/></policy></busconfig>')
    env = dict(os.environ)
    for key in ("DISPLAY", "WAYLAND_DISPLAY", "DBUS_SESSION_BUS_ADDRESS", "DBUS_STARTER_ADDRESS", "DBUS_STARTER_BUS_TYPE", "SESSION_MANAGER", "LD_PRELOAD", "QT_QPA_PLATFORMTHEME", "KDE_FULL_SESSION", "KDE_SESSION_VERSION", "XDG_SESSION_ID", "XAUTHORITY", "QML_IMPORT_PATH", "QML2_IMPORT_PATH"):
        env.pop(key, None)
    env.update(HOME=str(paths["home"]), XDG_CONFIG_HOME=str(paths["config"]), XDG_DATA_HOME=str(paths["data"]), XDG_CACHE_HOME=str(paths["cache"]), XDG_STATE_HOME=str(paths["state"]), XDG_RUNTIME_DIR=str(paths["runtime"]), QT_QPA_PLATFORM="xcb", QT_QUICK_BACKEND="software", QT_ACCESSIBILITY="0", LIBGL_ALWAYS_SOFTWARE="1", KWIN_COMPOSE="N", XDG_CURRENT_DESKTOP="NONE", DBUS_SYSTEM_BUS_ADDRESS="unix:path=" + str(paths["runtime"] / "no-system-bus"))
    command = ["xvfb-run", "--auto-servernum", "--server-args=-screen 0 1200x700x24", "dbus-run-session", "--config-file", str(bus), "--", sys.executable, str(Path(__file__).resolve()), "--worker", "--saida", str(output)]
    if args.crud_dialogs_only:
        command.append("--crud-dialogs-only")
        paths["tmp"] = fixture_root / "tmp"
        paths["tmp"].mkdir(mode=0o700)
        env.update(TMPDIR=str(paths["tmp"]), PYTHONDONTWRITEBYTECODE="1")
    try:
        result = subprocess.run(command, env=env, stdout=subprocess.PIPE, stderr=subprocess.STDOUT, text=True, timeout=90)
    finally:
        if temporary:
            temporary.cleanup()
    (output / "native-test.log").write_text(result.stdout)
    native_path = output / "NATIVO.json"
    native = json.loads(native_path.read_text()) if native_path.is_file() else {"checks": {}, "error": result.stdout}
    if args.crud_dialogs_only:
        native["checks"]["no_personal_configuration_paths_read"] = not protected
    else:
        native["checks"]["real_user_configuration_hashes_unchanged"] = before == {str(path): digest(path) for path in protected}
    native["checks"]["native_worker_exited_successfully"] = result.returncode == 0
    native["status"] = "passed" if all(native["checks"].values()) and native["checks"] else "failed"
    native["protected_configuration_hashes_before"] = before
    native["scope"] = "Production QML with real KWin X11, task models, geometry and D-Bus operations; every compositor action occurred in private HOME/XDG/display/session bus. No real user session or frozen Downloads backup was changed. Wayland is not verified by this runner."
    (output / "RESULTADO.json").write_text(json.dumps(native, ensure_ascii=False, indent=2) + "\n")
    print(json.dumps({"status": native["status"], "checks": native["checks"], "report": str(output / "RESULTADO.json")}, ensure_ascii=False, indent=2))
    return 0 if native["status"] == "passed" else 1


def worker(args):
    from PyQt6 import sip
    from PyQt6.QtCore import QObject, QPoint, QPointF, QUrl, Qt, qInstallMessageHandler
    from PyQt6.QtGui import QWheelEvent
    from PyQt6.QtQml import QQmlApplicationEngine
    from PyQt6.QtQuick import QQuickItem, QQuickWindow
    from PyQt6.QtTest import QTest
    from PyQt6.QtWidgets import QApplication, QWidget
    output = args.saida.resolve()
    checks, messages, evidence = {}, [], {}
    qInstallMessageHandler(lambda kind, context, text: messages.append(text))
    compositor_log = (output / "kwin.log").open("w")
    compositor = subprocess.Popen(["kwin_x11", "--replace"], stdout=compositor_log, stderr=subprocess.STDOUT)
    app, engine, windows = None, None, []

    def check(name, condition):
        checks[name] = bool(condition)
        if not condition:
            raise AssertionError(name)

    def settle(predicate, timeout=5):
        end = time.monotonic() + timeout
        while time.monotonic() < end:
            app.processEvents()
            if predicate():
                app.processEvents()
                return True
            time.sleep(0.015)
        return False

    def dbus(member, *arguments):
        return subprocess.check_output(["qdbus6", "org.kde.KWin", "/VirtualDesktopManager", member, *map(str, arguments)], text=True, timeout=8).strip()

    try:
        for _ in range(80):
            ready = subprocess.run(["qdbus6", "org.kde.KWin", "/VirtualDesktopManager"], stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True, timeout=2)
            if ready.returncode == 0:
                break
            time.sleep(.05)
        check("real_private_kwin_started", ready.returncode == 0)
        (output / "kwin-interface.txt").write_text(ready.stdout)
        app = QApplication([])
        app.setApplicationName("irix-domainos-pager-native-test")
        engine = QQmlApplicationEngine()
        engine.load(QUrl.fromLocalFile(str(REPO / "plasma/tests/DomainOSPagerPreview.qml")))
        check("production_pager_qml_loaded", bool(engine.rootObjects()))
        window = engine.rootObjects()[0]
        pager = window.findChild(QQuickItem, "domainosRealPager")
        check("production_component_instance_present", pager is not None)
        engine.globalObject().setProperty("pagerTest", engine.newQObject(pager))

        def evaluate(code):
            result = engine.evaluate(code)
            if result.isError():
                raise RuntimeError(result.toString())
            return result

        def records():
            return json.loads(evaluate("JSON.stringify(pagerTest.desktopRecords)").toString())

        def invoke(expression):
            return evaluate("pagerTest." + expression).toBool()

        def capture(name):
            app.processEvents()
            check("capture_" + name, window.grabWindow().save(str(output / (name + ".png"))))

        def current():
            return dbus("org.freedesktop.DBus.Properties.Get", "org.kde.KWin.VirtualDesktopManager", "current")

        def items():
            def descend(item):
                yield item
                for child in item.childItems():
                    yield from descend(child)
            return [item for candidate in app.allWindows() if isinstance(candidate,QQuickWindow)
                    for item in descend(candidate.contentItem())]

        def find(name):
            return next((item for item in items() if item.objectName() == name), None)

        def tile(position):
            return find("domainosDesktopTile_" + str(position))

        def click(item):
            target_window=item.window()
            point = item.mapToItem(target_window.contentItem(), QPointF(item.width() / 2, item.height() / 2)).toPoint()
            QTest.mouseClick(target_window, Qt.MouseButton.LeftButton, Qt.KeyboardModifier.NoModifier, point)
            app.processEvents()

        def wheel(delta):
            point = QPointF(60, 60)
            event = QWheelEvent(point, QPointF(window.mapToGlobal(point.toPoint())), QPoint(0, 0), QPoint(0, delta), Qt.MouseButton.NoButton, Qt.KeyboardModifier.NoModifier, Qt.ScrollPhase.NoScrollPhase, False)
            app.sendEvent(window, event)
            app.processEvents()

        if args.crud_dialogs_only:
            # Reuse this runner's native/private bootstrap and actual production
            # instance; the directed helper tests only changed Dialog controls.
            import importlib.util
            helper_path = REPO / "plasma/tests/test_domainos_pager_crud_dialogs.py"
            spec = importlib.util.spec_from_file_location("domainos_pager_crud_dialogs", helper_path)
            helper = importlib.util.module_from_spec(spec)
            spec.loader.exec_module(helper)
            helper.exercise(app, engine, window, pager, check, settle, dbus, records, evidence, output)
            qml_errors = [message for message in messages if re.search(r"(ReferenceError:|TypeError:|SyntaxError:|Cannot assign|Type .+ unavailable|is not a type|module .+ is not installed|Binding loop|Error loading QML)", message)]
            evidence["qml_errors"] = qml_errors
            check("qml_runtime_errors_zero", not qml_errors)
            return 0 if all(checks.values()) else 1

        check("one_desktop_model_available", settle(lambda: pager.property("available") and pager.property("desktopCount") == 1))
        initial = records()[0]
        check("one_desktop_uses_whole_module", abs(tile(0).width() - 326) < .01)
        check("one_desktop_does_not_hide_pager", tile(0).isVisible())
        check("one_desktop_has_no_navigation", not pager.property("navigationVisible"))
        check("one_desktop_identity_is_kwin_uuid", initial["id"] == current() and len(initial["id"]) == 36)
        capture("ONE-DESKTOP")
        for title, count in (("Beta", 2), ("Gamma", 3), ("Delta", 4)):
            check("create_" + title + "_request", invoke("createDesktop(" + json.dumps(title) + ")"))
            check("create_" + title + "_confirmed", settle(lambda: pager.property("desktopCount") == count and not pager.property("mutationPending") and pager.property("available")))
            check("create_" + title + "_native_count", int(dbus("org.freedesktop.DBus.Properties.Get", "org.kde.KWin.VirtualDesktopManager", "count")) == count)
            if count == 2:
                check("two_desktops_preserve_card_dimensions", tile(0).width() == 158 and tile(0).height() == 126 and tile(1).width() == 158)
                check("two_desktops_have_no_navigation", not pager.property("navigationVisible"))
                capture("TWO-DESKTOPS")
        check("more_desktops_navigation_below", pager.property("navigationVisible") and tile(0).height() == 98)
        beta = next(record for record in records() if record["name"] == "Beta")
        gamma = next(record for record in records() if record["name"] == "Gamma")
        stable_ids = [record["id"] for record in records()]
        check("rename_request", invoke("renameDesktop(" + json.dumps(beta["id"]) + ", 'Beta renamed')"))
        check("rename_confirmed", settle(lambda: not pager.property("mutationPending") and any(record["name"] == "Beta renamed" for record in records())))
        check("rename_preserves_all_uuids", stable_ids == [record["id"] for record in records()])
        capture("FOUR-DESKTOPS")
        before_wheel = current()
        wheel(-120)
        check("wheel_scrolls_visible_cards", pager.property("firstVisible") == 1)
        check("default_wheel_does_not_switch_native_desktop", current() == before_wheel)
        next_button = find("domainosDesktopNext")
        click(next_button)
        check("next_arrow_navigates_only", pager.property("firstVisible") == 2 and current() == before_wheel)
        check("next_arrow_disables_at_limit", not next_button.isEnabled())
        previous_button = find("domainosDesktopPrevious")
        click(previous_button)
        check("previous_arrow_navigates_only", pager.property("firstVisible") == 0 and current() == before_wheel)
        beta_tile = tile(beta["position"])
        beta_button = find("domainosNativeWorkspace_" + beta["id"])
        point = beta_tile.mapToItem(window.contentItem(), QPointF(beta_tile.width() / 2, beta_tile.height() / 2)).toPoint()
        QTest.mousePress(window, Qt.MouseButton.LeftButton, Qt.KeyboardModifier.NoModifier, point)
        app.processEvents()
        check("unselected_desktop_press_has_immediate_relief", beta_button.property("pressed") and beta_button.property("pressOffset") == 2)
        check("desktop_activation_waits_for_release", current() == initial["id"])
        capture("PRESSED-UNSELECTED")
        QTest.mouseRelease(window, Qt.MouseButton.LeftButton, Qt.KeyboardModifier.NoModifier, point)
        check("click_activates_real_kwin_desktop_uuid", settle(lambda: current() == beta["id"] and pager.property("currentDesktopId") == beta["id"]))
        check("selected_desktop_returns_raised", beta_button.property("selected") and beta_button.property("pressOffset") == 0)
        capture("SELECTED-BETA")
        QTest.mousePress(window, Qt.MouseButton.LeftButton, Qt.KeyboardModifier.NoModifier, point)
        app.processEvents()
        check("selected_desktop_never_sinks_again", beta_button.property("pressOffset") == 0)
        QTest.mouseRelease(window, Qt.MouseButton.LeftButton, Qt.KeyboardModifier.NoModifier, point)
        check("selected_click_has_no_other_command", current() == beta["id"])
        finished_before_rapid = len(window.property("completedOperations").toVariant())
        check("rapid_switch_then_return_requests_accepted", invoke("activateDesktop(" + json.dumps(initial["id"]) + ")") and invoke("activateDesktop(" + json.dumps(beta["id"]) + ")"))
        check("rapid_return_is_not_discarded_as_old_selection", pager.property("pendingActivations") == 2)
        check("rapid_switch_and_return_native_results_confirmed", settle(lambda: pager.property("pendingActivations") == 0 and current() == beta["id"] and pager.property("currentDesktopId") == beta["id"]))
        check("rapid_requests_each_report_completion", len(window.property("completedOperations").toVariant()) == finished_before_rapid + 2)
        pager.setProperty("wheelActivatesDesktop", True)
        wheel(-120)
        check("optional_wheel_activates_real_desktop", settle(lambda: current() == gamma["id"]))
        pager.setProperty("wheelActivatesDesktop", False)
        pager.setProperty("firstVisible", 0)
        app.processEvents()
        held_tile = tile(beta["position"])
        held_button = find("domainosNativeWorkspace_" + beta["id"])
        held_point = held_tile.mapToItem(window.contentItem(), QPointF(held_tile.width() / 2, held_tile.height() / 2)).toPoint()
        QTest.mousePress(window, Qt.MouseButton.LeftButton, Qt.KeyboardModifier.NoModifier, held_point)
        app.processEvents()
        check("press_captures_original_uuid", held_tile.property("pressedDesktopId") == beta["id"])
        # Exercise the dangerous delegate-reuse case directly. KWin stays real:
        # both identities are native UUIDs and release must switch the real WM
        # to the identity captured at press, never this rebound card value.
        held_tile.setProperty("desktopId", initial["id"])
        QTest.mouseRelease(window, Qt.MouseButton.LeftButton, Qt.KeyboardModifier.NoModifier, held_point)
        check("rebound_delegate_release_activates_original_native_uuid", settle(lambda: current() == beta["id"] and pager.property("currentDesktopId") == beta["id"]))
        held_tile.setProperty("desktopId", beta["id"])
        invoke("activateDesktop(" + json.dumps(gamma["id"]) + ")")
        check("return_to_gamma_before_external_insertion", settle(lambda: current() == gamma["id"] and pager.property("currentDesktopId") == gamma["id"]))
        QTest.mousePress(window, Qt.MouseButton.LeftButton, Qt.KeyboardModifier.NoModifier, held_point)
        app.processEvents()
        dbus("org.kde.KWin.VirtualDesktopManager.createDesktop", 0, "Inserted first")
        check("external_insertion_observed", settle(lambda: pager.property("available") and pager.property("desktopCount") == 5))
        replacement_tile = tile(beta["position"])
        check("held_card_model_reordered", replacement_tile.property("desktopId") != beta["id"])
        delegate_destroyed = sip.isdeleted(held_tile)
        surviving_press = not delegate_destroyed and held_button.property("pressed") and held_tile.property("pressedDesktopId") == beta["id"]
        evidence["press_during_external_reorder"] = {"original_uuid": beta["id"],
            "replacement_uuid": replacement_tile.property("desktopId"), "native_gesture_survived": bool(surviving_press),
            "native_repeater_destroyed_held_delegate": delegate_destroyed}
        check("reordering_does_not_activate_before_release", current() == gamma["id"])
        QTest.mouseRelease(window, Qt.MouseButton.LeftButton, Qt.KeyboardModifier.NoModifier, held_point)
        expected_release = beta["id"] if surviving_press else gamma["id"]
        check("reordered_gesture_keeps_uuid_or_cancels", settle(lambda: current() == expected_release))
        check("release_clears_captured_uuid", settle(lambda: all(item.property("pressedDesktopId") == "" for item in items() if item.objectName().startswith("domainosDesktopTile_"))))
        moved_gamma = next(record for record in records() if record["id"] == gamma["id"])
        check("uuid_survives_reordering", moved_gamma["position"] == gamma["position"] + 1 and pager.property("currentDesktopId") == expected_release)
        check("activation_uses_uuid_after_reordering", invoke("activateDesktop(" + json.dumps(beta["id"]) + ")") and settle(lambda: current() == beta["id"]))
        pager.setProperty("firstVisible", 0)
        app.processEvents()
        initial_tile = tile(next(record for record in records() if record["id"] == initial["id"])["position"])
        cancel_point = initial_tile.mapToItem(window.contentItem(), QPointF(initial_tile.width() / 2, initial_tile.height() / 2)).toPoint()
        QTest.mousePress(window, Qt.MouseButton.LeftButton, Qt.KeyboardModifier.NoModifier, cancel_point)
        QTest.mouseMove(window, QPoint(window.width() - 1, window.height() - 1))
        QTest.mouseRelease(window, Qt.MouseButton.LeftButton, Qt.KeyboardModifier.NoModifier, QPoint(window.width() - 1, window.height() - 1))
        app.processEvents()
        check("cancelled_press_cannot_activate_replacement", current() == beta["id"] and initial_tile.property("pressedDesktopId") == "")
        click(initial_tile)
        check("new_press_after_cancellation_uses_current_uuid", settle(lambda: current() == initial["id"] and pager.property("currentDesktopId") == initial["id"]))
        invoke("activateDesktop(" + json.dumps(beta["id"]) + ")")
        check("return_to_beta_before_geometry_probe", settle(lambda: current() == beta["id"] and pager.property("currentDesktopId") == beta["id"]))
        pager.setProperty("firstVisible", next(record for record in records() if record["id"] == beta["id"])["position"])
        app.processEvents()
        sample = QWidget()
        sample.setWindowTitle("IRIX-PAGER-NATIVE-SAMPLE")
        sample.setGeometry(90, 120, 420, 260)
        sample.show()
        windows.append(sample)
        check("sample_native_window_mapped", settle(lambda: sample.isVisible()))
        sample_id = "0x%x" % int(sample.winId())
        subprocess.run(["xdotool", "set_desktop_for_window", sample_id, str(next(record for record in records() if record["id"] == beta["id"])["position"])], check=True, timeout=5)
        def sample_rects():
            return [item for item in items() if item.objectName().startswith("domainosNativeWindow_") and item.property("windowTitle") == "IRIX-PAGER-NATIVE-SAMPLE"]
        check("real_window_geometry_reaches_pager", settle(lambda: any(item.width() > 10 and item.height() > 10 for item in sample_rects())))
        sample.showMinimized()
        check("minimized_state_is_native", settle(lambda: any(item.property("minimized") for item in sample_rects())))
        sample.showNormal()
        check("restored_state_is_native", settle(lambda: any(not item.property("minimized") for item in sample_rects())))
        capture("NATIVE-WINDOW-GEOMETRY")
        evidence["real_geometry_samples"] = [{"object": item.objectName(), "width": item.width(), "height": item.height(), "minimized": item.property("minimized")} for item in sample_rects()]
        sample.close()
        for record in list(records()):
            if record["id"] == initial["id"]:
                continue
            check("remove_" + record["id"] + "_request", invoke("removeDesktop(" + json.dumps(record["id"]) + ")"))
            expected = pager.property("desktopCount") - 1
            check("remove_" + record["id"] + "_confirmed", settle(lambda: not pager.property("mutationPending") and pager.property("desktopCount") == expected and pager.property("available")))
        check("minimum_one_desktop_enforced", not invoke("removeDesktop(" + json.dumps(initial["id"]) + ")") and pager.property("desktopCount") == 1)
        check("minimum_one_confirmed_by_native_kwin", int(dbus("org.freedesktop.DBus.Properties.Get", "org.kde.KWin.VirtualDesktopManager", "count")) == 1)
        check("removed_uuid_cannot_activate_different_desktop", not invoke("activateDesktop(" + json.dumps(beta["id"]) + ")") and current() == initial["id"])
        capture("RETURN-TO-ONE")
        # A real panel host is 109 px tall. Popup.Item can be visible yet
        # clipped there; inspect the actual window containing each popup.
        window.resize(window.width(),109)
        window.setPosition(120,500)
        app.processEvents()
        before_popups=len(window.property("completedOperations").toVariant())
        for name,expression in (("ContextMenu","openContextMenu(50,20)"),
                                ("NameDialog","openNameDialog('')"),
                                ("RemoveDialog",None)):
            popup=pager.findChild(QObject,"domainosDesktop"+name)
            check(name+"_production_popup_present",popup is not None)
            engine.globalObject().setProperty("popupTest",engine.newQObject(popup))
            evaluate("pagerTest."+expression if expression else "popupTest.open()")
            check(name+"_visible_in_short_host",settle(lambda:popup.property("visible")))
            popup_content=popup.property("contentItem")
            popup_window=popup_content.window()
            check(name+"_native_popup_layout_settled",settle(lambda:abs(popup_window.width()-popup.property("width"))<1 and abs(popup_window.height()-popup.property("height"))<1))
            evidence[name+"_native_window"]={"x":popup_window.x(),"y":popup_window.y(),"width":popup_window.width(),"height":popup_window.height(),"host_height":window.height(),"popup_height":popup.property("height"),"popup_implicit_height":popup.property("implicitHeight"),"content_height":popup_content.height()}
            check(name+"_uses_separate_native_window",popup_window is not None and popup_window!=window and popup_window.isVisible())
            check(name+"_full_popup_height_unclipped_by_109px_host",window.height()==109 and popup_window.height()>=popup.property("implicitHeight")-.5)
            if name=="ContextMenu":
                check("ContextMenu_extends_outside_109px_host",not window.geometry().contains(popup_window.geometry()))
            check(name+"_native_popup_capture",popup_window.grabWindow().save(str(output/("SHORT-HOST-"+name+".png"))))
            if name!="ContextMenu":
                check(name+"_focus_enabled",popup.property("focus"))
            if name=="NameDialog":
                name_input=find("domainosDesktopNameInput")
                check("name_dialog_text_input_receives_focus",name_input is not None and settle(name_input.hasActiveFocus))
            evaluate("popupTest.close()")
            check(name+"_closes_without_desktop_mutation",settle(lambda:not popup.property("visible")) and records()==[initial] and len(window.property("completedOperations").toVariant())==before_popups)
        evidence["final_desktops"] = records()
        evidence["completed_operations"] = window.property("completedOperations").toVariant()
        check("all_completed_operations_confirmed", all(item["success"] for item in evidence["completed_operations"]))
        qml_errors = [message for message in messages if re.search(r"(ReferenceError:|TypeError:|SyntaxError:|Cannot assign|Type .+ unavailable|is not a type|module .+ is not installed|Binding loop|Error loading QML)", message)]
        evidence["qml_errors"] = qml_errors
        check("qml_runtime_errors_zero", not qml_errors)
    except BaseException as error:
        evidence["error"] = str(error)
        checks["native_test_completed"] = False
        if engine is not None:
            state = engine.evaluate('JSON.stringify({available:pagerTest.available,desktops:pagerTest.desktopRecords,current:pagerTest.currentDesktopId,error:pagerTest.lastError,count:pagerTest.pagerBackend.count})')
            if not state.isError():
                evidence["state_at_failure"] = state.toString()
    finally:
        evidence["qt_messages"] = messages
        if engine is not None:
            for window in engine.rootObjects():
                window.close()
        for window in windows:
            window.close()
        compositor.terminate()
        try:
            compositor.wait(8)
        except subprocess.TimeoutExpired:
            compositor.kill(); compositor.wait()
        compositor_log.close()
        report = {"status": "passed" if all(checks.values()) else "failed", "checks": checks, "evidence": evidence}
        (output / "NATIVO.json").write_text(json.dumps(report, ensure_ascii=False, indent=2) + "\n")
    return 0 if all(checks.values()) else 1


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--saida", type=Path, help="New or empty output directory")
    parser.add_argument("--worker", action="store_true", help=argparse.SUPPRESS)
    parser.add_argument("--crud-dialogs-only", action="store_true", help="Only the current Pager Dialog controls: native private Accept/Reject and explicit CRUD")
    args = parser.parse_args()
    return worker(args) if args.worker else setup(args)


if __name__ == "__main__":
    raise SystemExit(main())
