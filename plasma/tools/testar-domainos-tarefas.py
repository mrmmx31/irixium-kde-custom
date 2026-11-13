#!/usr/bin/env python3
# SPDX-FileCopyrightText: 2026 IRIX Classic contributors
# SPDX-License-Identifier: GPL-3.0-or-later
"""Verify DomainOS task identities, selection, groups and native request contracts.

Uses real Qt mouse/key input with isolated model doubles. Native providers are
also constructed in an offscreen private session to validate installed QML APIs.
No user window, desktop, preference or process is acted on.
"""
import argparse
import hashlib
import json
import os
from pathlib import Path
import sys
import tempfile

sys.dont_write_bytecode = True
REPO = Path(__file__).resolve().parents[2]


def digest(path):
    return hashlib.sha256(path.read_bytes()).hexdigest() if path.is_file() else None


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--saida", type=Path, required=True, help="New or empty output directory")
    args = parser.parse_args()
    output = args.saida.resolve()
    if output.exists() and any(output.iterdir()):
        parser.error("Output directory must be new or empty")
    output.mkdir(parents=True, exist_ok=True)
    config = Path(os.environ.get("XDG_CONFIG_HOME", str(Path.home() / ".config")))
    protected = {str(config / name): digest(config / name) for name in
                 ("kdeglobals", "plasmarc", "kwinrc", "kcmfonts", "plasma-org.kde.plasma.desktop-appletsrc")}
    owned = [REPO / "plasma/applets/org.irixclassic.domainos.panel/contents/ui" / name for name in
             ("DomainOSTasks.qml", "DomainOSTaskSelection.js")]
    sources = {str(path): digest(path) for path in owned}
    checks, warnings = {}, []
    report = {"status": "failed", "checks": checks, "qml_diagnostics": warnings,
              "scope": "Qt input and provider contracts; private model doubles, no real window actions",
              "desktop_modified": False, "protected_config_sha256": protected, "source_sha256": sources}

    def require(name, condition):
        checks[name] = bool(condition)
        if not condition:
            raise AssertionError(name)

    with tempfile.TemporaryDirectory(prefix="irix-domainos-tasks-") as folder:
        private = Path(folder)
        for key, name in (("HOME", "home"), ("XDG_CONFIG_HOME", "config"), ("XDG_DATA_HOME", "data"),
                          ("XDG_CACHE_HOME", "cache"), ("XDG_STATE_HOME", "state"), ("XDG_RUNTIME_DIR", "runtime")):
            path = private / name
            path.mkdir(mode=0o700)
            os.environ[key] = str(path)
        for key in ("DISPLAY", "WAYLAND_DISPLAY", "LD_PRELOAD", "QT_STYLE_OVERRIDE", "QT_QUICK_CONTROLS_STYLE",
                    "QT_SCREEN_SCALE_FACTORS", "QT_FONT_DPI", "QML_IMPORT_PATH", "QML2_IMPORT_PATH",
                    "DBUS_STARTER_ADDRESS", "DBUS_STARTER_BUS_TYPE", "KDE_SESSION_VERSION"):
            os.environ.pop(key, None)
        os.environ.update(QT_QPA_PLATFORM="offscreen", QT_QUICK_BACKEND="software", QT_QPA_PLATFORMTHEME="generic",
                          QT_SCALE_FACTOR="1", XDG_CURRENT_DESKTOP="NONE",
                          DBUS_SESSION_BUS_ADDRESS="unix:path=" + str(private / "disabled-session-bus"),
                          DBUS_SYSTEM_BUS_ADDRESS="unix:path=" + str(private / "disabled-system-bus"))
        from PyQt6 import sip
        from PyQt6.QtCore import QObject, QPointF, Qt, QUrl, QMetaObject, Q_RETURN_ARG, Q_ARG, qVersion
        from PyQt6.QtGui import QGuiApplication
        from PyQt6.QtQml import QQmlApplicationEngine, QQmlComponent
        from PyQt6.QtQuick import QQuickWindow
        from PyQt6.QtTest import QTest
        app = QGuiApplication([sys.argv[0]])
        engine = QQmlApplicationEngine()
        engine.warnings.connect(lambda messages: warnings.extend(message.toString() for message in messages))
        engine.load(QUrl.fromLocalFile(str(REPO / "plasma/tests/DomainOSTasksPreview.qml")))
        require("task_fixture_loaded", bool(engine.rootObjects()))
        window = sip.cast(engine.rootObjects()[0], QQuickWindow)
        controller = window.property("controller")

        def call(name, *values):
            return QMetaObject.invokeMethod(window, name, Qt.ConnectionType.DirectConnection,
                                           Q_RETURN_ARG("QVariant"), *(Q_ARG("QVariant", value) for value in values))

        def settle():
            app.processEvents()
            QTest.qWait(35)
            app.processEvents()

        def state():
            settle()
            return json.loads(call("state"))

        def item(name):
            def descendants(root):
                yield root
                for child in root.childItems():
                    yield from descendants(child)
            result = next((node for node in descendants(window.contentItem()) if node.objectName() == name), None)
            if result is None:
                raise AssertionError("Missing input item " + name)
            return result

        def click(name, modifiers=Qt.KeyboardModifier.NoModifier, button=Qt.MouseButton.LeftButton):
            node = item(name)
            point = node.mapToScene(QPointF(node.width() / 2, node.height() / 2)).toPoint()
            QTest.mouseClick(window, button, modifiers, point)
            return state()

        def selected(*ids):
            return sorted("window:" + str(value) for value in ids)

        def configure(name, value):
            controller.setProperty(name, value)
            settle()

        try:
            current = state()
            require("count_uses_ungrouped_window_scope", current["windowCount"] == 8)
            require("grouping_preserved_by_default", len(current["rows"]) == 5 and sum(row["group"] for row in current["rows"]) == 2)
            configure("onlyCurrentScreen", True)
            require("screen_scope_uses_instance_filter", state()["windowCount"] == 7)
            configure("onlyCurrentScreen", False)
            configure("onlyCurrentDesktop", False)
            require("desktop_scope_preserved_when_disabled", state()["windowCount"] == 9)
            configure("onlyCurrentDesktop", True)
            current = click("task:window:6")
            require("single_click_selects_without_activation", current["selected"] == selected(6) and current["requests"] == [])
            node = item("task:window:6")
            point = node.mapToScene(QPointF(node.width() / 2, node.height() / 2)).toPoint()
            QTest.mouseDClick(window, Qt.MouseButton.LeftButton, Qt.KeyboardModifier.NoModifier, point)
            require("double_click_requests_native_activation", state()["requests"][-1] == {"action": "activate", "ids": [6], "argument": None})
            current = click("task:window:7", Qt.KeyboardModifier.ControlModifier)
            require("control_adds_window", sorted(current["selected"]) == selected(6, 7))
            current = click("task:window:6", Qt.KeyboardModifier.ControlModifier)
            require("control_removes_window", current["selected"] == selected(7))
            click("task:window:6")
            current = click("task:window:8", Qt.KeyboardModifier.ShiftModifier)
            require("shift_selects_visible_individual_interval", sorted(current["selected"]) == selected(6, 7, 8))
            before = len(current["requests"])
            current = click("task:group:terminal")
            require("group_click_opens_members_without_selecting_all", current["group"] == "group:terminal"
                    and sorted(current["selected"]) == selected(6, 7, 8) and len(current["requests"]) == before)
            current = click("member:window:1")
            current = click("member:window:3")
            require("group_checkbox_selects_individual_members", sorted(current["selected"]) == selected(1, 3, 6, 7, 8))
            current = click("task:group:browser")
            current = click("member:window:4")
            require("selection_accumulates_across_groups", sorted(current["selected"]) == selected(1, 3, 4, 6, 7, 8))
            require("checkbox_never_activates_or_organizes", len(current["requests"]) == before and current["organizationRequests"] == 0)
            QTest.keyPress(window, Qt.Key.Key_Control)
            QTest.keyRelease(window, Qt.Key.Key_Control)
            require("release_does_not_interrupt_group_picker", state()["organizationRequests"] == 0 and controller.property("organizationPending"))
            call("finishGroup", True)
            require("group_completion_opens_one_operations_menu", state()["organizationRequests"] == 1)
            current = click("task:window:6", button=Qt.MouseButton.RightButton)
            require("right_click_requests_native_menu", current["contextRequests"] == 1)
            require("right_click_preserves_selection", sorted(current["selected"]) == selected(1, 3, 4, 6, 7, 8))
            call("reverseWindows")
            current = state()
            require("reordering_preserves_window_identities", sorted(current["selected"]) == selected(1, 3, 4, 6, 7, 8))
            result = json.loads(call("act", "window:6", "close", None))
            require("action_resolves_current_row_by_identity", result["state"] == "requested" and state()["requests"][-1]["ids"] == [6])
            call("mutate", 6, "closable", False)
            result = json.loads(call("act", "window:6", "close", None))
            require("capability_change_refuses_unsupported_close", result["state"] == "unavailable")
            call("removeWindow", 6)
            current = state()
            require("closed_window_removed_from_selection", "window:6" not in current["selected"])
            result = json.loads(call("act", "window:6", "activate", None))
            require("stale_target_never_transfers_to_replacement_row", result["state"] == "unavailable")
            call("addWindow", 60, "app6")
            require("new_window_never_inherits_selection", "window:60" not in state()["selected"])
            configure("filterMode", "automatic")
            require("automatic_filter_needs_user_threshold", state()["thresholdRequired"] and not state()["filter"])
            configure("automaticThreshold", 8)
            require("threshold_equality_restores_normal_view", not state()["filter"])
            configure("automaticThreshold", 7)
            current = state()
            require("automatic_filter_counts_before_grouping_and_filtering", current["windowCount"] == 8 and current["filter"])
            displayed = [key for row in current["rows"] for key in (row["memberKeys"] if row["group"] else [row["key"]])]
            require("automatic_filter_only_presents_minimized_windows", sorted(displayed) == selected(2, 5))
            call("removeWindow", 60)
            require("dropping_to_threshold_restores_normal_view", state()["windowCount"] == 7 and not state()["filter"])
            configure("filterMode", "minimized")
            configure("automaticThreshold", 100)
            require("manual_minimized_mode_independent_of_threshold", state()["filter"])
            configure("filterMode", "normal")
            configure("groupingMode", 0)
            require("grouping_can_be_disabled_without_losing_windows", len(state()["rows"]) == state()["windowCount"])
            click("task:window:1")
            click("task:window:3", Qt.KeyboardModifier.ControlModifier)
            result = json.loads(call("batch", "columns"))
            require("geometry_not_faked_by_interactive_move", result["state"] == "unavailable")
            result = json.loads(call("batch", "minimize"))
            require("batch_minimize_needs_current_destination_backend", result["state"] == "unavailable")
            call("addGeometryBackend")
            result = json.loads(call("batch", "columns"))
            current = state()
            payload = current["layouts"][-1]
            require("layout_dispatches_only_selected_identities", result["state"] == "requested"
                    and sorted(window["key"] for window in payload["windows"]) == selected(1, 3))
            require("layout_has_native_current_desktop_monitor_contract", payload["desktopId"] == 1
                    and payload["availableGeometry"]["height"] == 850 and payload["screenGeometry"]["width"] == 1200)
            require("layout_has_verified_identity_pid_and_capabilities", all(window["windowIds"] and window["pid"] > 0
                    and window["movable"] and window["resizable"] for window in payload["windows"]))
            call("mutate", 3, "resizable", False)
            result = json.loads(call("batch", "mosaic"))
            require("layout_refuses_incapable_window", result["state"] == "unavailable" and len(state()["layouts"]) == 1)
            result = json.loads(call("batch", "minimize"))
            require("minimize_batch_collects_each_selected_window", result["state"] == "requested"
                    and state()["layouts"][-1]["mode"] == "minimize"
                    and {tuple(window["windowIds"]) for window in state()["layouts"][-1]["windows"]} == {(1,), (3,)})
            call("mutate", 1, "minimized", True)
            result = json.loads(call("batch", "minimize"))
            require("minimize_batch_reports_current_state_without_toggle", result["state"] == "requested"
                    and next(window for window in state()["layouts"][-1]["windows"] if window["key"] == "window:1")["minimized"])
            call("mutate", 1, "pid", 9991)
            require("reused_window_id_with_different_pid_loses_selection", "window:1" not in state()["selected"])
            result = json.loads(call("actExpected", "window:1", "close", 501))
            require("stale_menu_pid_cannot_close_reused_window_id", result["state"] == "unavailable")
            click("task:window:1")
            click("task:window:3", Qt.KeyboardModifier.ControlModifier)
            call("mutate", 3, "resizable", True)
            call("mutate", 3, "x", 777)
            result = json.loads(call("batch", "rows"))
            require("layout_payload_uses_current_window_records", result["state"] == "requested"
                    and next(row for row in state()["layouts"][-1]["windows"] if row["key"] == "window:3")["geometry"]["x"] == 777)
            result = json.loads(call("terminate", "window:1"))
            require("termination_unavailable_without_explicit_backend", result["state"] == "unavailable" and state()["terminations"] == [])
            call("addProcessBackend")
            call("mutate", 2, "pid", 9991)
            result = json.loads(call("terminate", "window:1"))
            require("termination_refuses_unselected_sibling_window", result["state"] == "unavailable" and state()["terminations"] == [])
            click("task:window:2", Qt.KeyboardModifier.ControlModifier)
            result = json.loads(call("terminate", "window:1"))
            require("termination_contract_contains_identity_and_all_known_siblings", result["state"] == "requested"
                    and state()["terminations"][-1]["window"]["pid"] == 9991
                    and {row["key"] for row in state()["terminations"][-1]["knownProcessWindows"]} == set(selected(1, 2)))
            call("mutate", 1, "pid", 0)
            result = json.loads(call("terminate", "window:1"))
            require("termination_refuses_unknown_process_identity", result["state"] == "unavailable")
            before = state()["organizationRequests"]
            call("releaseModifiers", int(Qt.KeyboardModifier.ShiftModifier.value))
            require("modifier_release_waits_until_selection_modifiers_are_up", state()["organizationRequests"] == before)
            call("releaseModifiers", 0)
            require("all_modifiers_released_requests_organization_without_timer", state()["organizationRequests"] == before + 1)
            call("addWindow", 70, "launcher")
            call("mutate", 70, "type", "launcher")
            call("addWindow", 71, "startup")
            call("mutate", 71, "type", "startup")
            require("launchers_and_startups_excluded_from_window_count", state()["windowCount"] == 7)
            call("addWindow", 72, "noidentity")
            call("mutate", 72, "ids", [])
            require("unidentified_window_reported_and_never_action_target", state()["identitiesUnavailable"] == 1
                    and state()["windowCount"] == 8 and json.loads(call("act", "window:72", "close", None))["state"] == "unavailable")
            require("fixture_capture_saved", window.grabWindow().save(str(output / "TASKS-SELECTION.png")))
            # Loading real native providers establishes the installed enum and
            # invokable contract; it does not claim real-window action coverage.
            component = QQmlComponent(engine, QUrl.fromLocalFile(str(owned[0])))
            native = component.createWithInitialProperties({"onlyCurrentDesktop": False, "onlyCurrentActivity": False})
            require("native_taskmanager_providers_constructed", native is not None)
            settle()
            require("native_view_and_scope_models_are_distinct", native.property("tasksModel") is not None
                    and native.property("scopeModel") is not None and native.property("tasksModel") != native.property("scopeModel"))
            native.deleteLater()
            require("qml_diagnostics_zero", not warnings)
            require("production_sources_unchanged", all(digest(Path(path)) == expected for path, expected in sources.items()))
            require("real_preferences_unchanged", all(digest(Path(path)) == expected for path, expected in protected.items()))
            report.update(status="passed", qt=qVersion(), final_state=state())
        except Exception as error:
            report["error"] = str(error)
            report["last_state"] = state()
        finally:
            window.close()
            app.processEvents()
            (output / "RESULTADO.json").write_text(json.dumps(report, ensure_ascii=False, indent=2) + "\n")
        print(json.dumps({"status": report["status"], "checks": len(checks), "report": str(output / "RESULTADO.json"),
                          "error": report.get("error")}, ensure_ascii=False))
        return 0 if report["status"] == "passed" else 1


if __name__ == "__main__":
    sys.exit(main())
