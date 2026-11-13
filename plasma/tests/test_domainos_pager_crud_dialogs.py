#!/usr/bin/env python3
# SPDX-License-Identifier: GPL-3.0-or-later
"""Directed helper for the existing private native Pager runner.

Run plasma/tools/testar-domainos-pager.py --crud-dialogs-only --saida NEW_DIR.
The real production Dialog buttons receive XTest pointer clicks under private
KWin/X11. No dialog.accept()/reject(), direct create/rename/remove method call,
native API double, personal session operation or other Pager regression is used.
"""
import hashlib
import json
from pathlib import Path
import subprocess
import time

ROOT = Path(__file__).resolve().parents[2]
UI = ROOT / "plasma/applets/org.irixclassic.domainos.panel/contents/ui"


def exercise(app, engine, window, pager, check, settle, dbus, records, evidence, output):
    from PyQt6.QtCore import QEvent, QObject, QPointF
    from PyQt6.QtQuick import QQuickItem, QQuickWindow
    from PyQt6.QtTest import QTest

    pointer_events = []
    last_click = [None]

    class PointerProbe(QObject):
        def eventFilter(self, obj, event):
            if obj.inherits("QWindow") and event.type() in (
                    QEvent.Type.MouseButtonPress, QEvent.Type.MouseButtonRelease, QEvent.Type.MouseButtonDblClick):
                pointer_events.append({"type": event.type().name, "window": obj.metaObject().className(),
                    "x": event.globalPosition().x(), "y": event.globalPosition().y()})
            return False

    probe = PointerProbe()
    app.installEventFilter(probe)
    evidence["pointer_events"] = pointer_events

    def evaluate(code):
        result = engine.evaluate(code)
        if result.isError():
            raise RuntimeError(result.toString())
        return result

    def completed():
        value = window.property("completedOperations")
        return value.toVariant() if hasattr(value, "toVariant") else value

    def count():
        return int(dbus("org.freedesktop.DBus.Properties.Get", "org.kde.KWin.VirtualDesktopManager", "count"))

    def current():
        return dbus("org.freedesktop.DBus.Properties.Get", "org.kde.KWin.VirtualDesktopManager", "current")

    def install_popup(kind):
        popup = pager.findChild(QObject, "domainosDesktop" + kind + "Dialog")
        check(kind + "_actual_dialog_present", popup is not None)
        engine.globalObject().setProperty("crudDialog", engine.newQObject(popup))
        return popup

    def popup_visible(popup):
        return bool(popup.property("visible"))

    def click_standard(popup, role, case):
        # This public DialogButtonBox method finds the actual standard-button
        # delegate. Clicking uses only XTest, never accepted/rejected signals.
        engine.globalObject().setProperty("crudDialog", engine.newQObject(popup))
        button = evaluate("crudDialog.footer.standardButton(" + str(role) + ")").toQObject()
        check(case + "_standard_button_present", isinstance(button, QQuickItem) and button.isVisible() and button.isEnabled())
        native_window = button.window()
        check(case + "_separate_popup_window", isinstance(native_window, QQuickWindow) and native_window != window and native_window.isVisible())
        check(case + "_button_layout_settled", settle(lambda: button.width() > 0 and button.height() > 0
            and abs(native_window.width() - popup.property("width")) < 1
            and abs(native_window.height() - popup.property("height")) < 1))
        # Let the actual Qt/KWin mapping complete before the first physical
        # pointer sequence, rather than repairing input with QML handler calls.
        app.processEvents()
        QTest.qWait(80)
        # Consecutive removals reuse the same native popup/button. This suite
        # tests single Ok/Cancel, so honor the platform's double-click interval
        # between separate cases rather than accidentally sending a double.
        if last_click[0] is not None:
            remaining = app.styleHints().mouseDoubleClickInterval() / 1000 + .02 - (time.monotonic() - last_click[0])
            if remaining > 0:
                QTest.qWait(int(remaining * 1000) + 1)
        # --sync waits for MotionNotify even when the cursor is already here;
        # consecutive removals reuse the exact button position. Use a real
        # outside motion first, then ordered XTest motion/press/release.
        subprocess.run(["xdotool", "mousemove", str(native_window.x() - 10), str(native_window.y() - 10)], check=True, timeout=3)
        app.processEvents()
        QTest.qWait(30)
        # Measure the live mapping after native size/position events, not before
        # waiting for the popup to map or after a different desktop count.
        native_window = button.window()
        point = button.mapToItem(native_window.contentItem(), QPointF(button.width() / 2, button.height() / 2)).toPoint()
        global_point = native_window.mapToGlobal(point)
        evidence.setdefault("button_input", {})[case] = {
            "native_window": {"x": native_window.x(), "y": native_window.y(), "width": native_window.width(), "height": native_window.height()},
            "button_global": {"x": global_point.x(), "y": global_point.y()},
            "role": role, "button_width": button.width(), "button_height": button.height()}
        subprocess.run(["xdotool", "mousemove", str(global_point.x()), str(global_point.y()), "click", "1"], check=True, timeout=3)
        last_click[0] = time.monotonic()
        check(case + "_dialog_closed_by_button", settle(lambda: not popup_visible(popup)))

    def name_dialog(desktop_id, text, accepted, case):
        before, before_native, before_current, before_ops = records(), count(), current(), len(completed())
        evaluate("pagerTest.openNameDialog(" + json.dumps(desktop_id) + ")")
        popup = install_popup("Name")
        check(case + "_dialog_open", settle(lambda: popup_visible(popup)))
        field = pager.findChild(QQuickItem, "domainosDesktopNameInput")
        check(case + "_production_text_field_focus", field is not None and settle(field.hasActiveFocus))
        subprocess.run(["xdotool", "windowactivate", "--sync", str(int(field.window().winId()))], check=True, timeout=3)
        subprocess.run(["xdotool", "key", "--clearmodifiers", "ctrl+a"], check=True, timeout=3)
        subprocess.run(["xdotool", "type", "--clearmodifiers", "--delay", "1", "--", text], check=True, timeout=3)
        check(case + "_input_received_keys", settle(lambda: field.property("text") == text))
        click_standard(popup, 0x400 if accepted else 0x400000, case)
        if not accepted:
            check(case + "_reject_preserves_native_ids_names_and_count", records() == before and count() == before_native and current() == before_current)
            check(case + "_reject_dispatches_no_operation", len(completed()) == before_ops and not pager.property("mutationPending"))
        return before, before_ops

    def remove_dialog(desktop_id, accepted, case):
        before, before_native, before_current, before_ops = records(), count(), current(), len(completed())
        evaluate("pagerTest.menuDesktopId=" + json.dumps(desktop_id))
        popup = install_popup("Remove")
        evaluate("crudDialog.open()")
        check(case + "_dialog_open", settle(lambda: popup_visible(popup)))
        click_standard(popup, 0x400 if accepted else 0x400000, case)
        if not accepted:
            check(case + "_reject_preserves_native_ids_names_and_count", records() == before and count() == before_native and current() == before_current)
            check(case + "_reject_dispatches_no_operation", len(completed()) == before_ops and not pager.property("mutationPending"))
        return before, before_ops

    def confirmed(operation, before_ops, expected, case):
        check(case + "_native_change_confirmed", settle(lambda: pager.property("available") and not pager.property("mutationPending") and expected(records())))
        reports = completed()[before_ops:]
        check(case + "_exactly_one_successful_operation", len(reports) == 1 and reports[0]["operation"] == operation and reports[0]["success"])
        check(case + "_native_count_agrees", count() == len(records()))

    check("initial_one_native_desktop_ready", settle(lambda: pager.property("available") and pager.property("desktopCount") == 1))
    initial = records()[0]
    check("initial_uuid_is_native", initial["id"] == current() and len(initial["id"]) == 36)
    window.resize(700, 109)
    window.setPosition(100, 500)
    app.processEvents()
    name_dialog("", "Rejected create", False, "create_reject")
    before, ops = name_dialog("", "Second owned area", True, "create_accept_second")
    confirmed("create-desktop", ops, lambda rs: len(rs) == 2 and any(r["name"] == "Second owned area" for r in rs), "create_accept_second")
    second = next(r for r in records() if r["id"] != initial["id"])
    check("create_preserves_original_uuid", records()[0]["id"] == initial["id"])
    name_dialog(second["id"], "Rejected rename", False, "rename_reject")
    before, ops = name_dialog(second["id"], "Renamed owned area", True, "rename_accept")
    confirmed("rename-desktop", ops, lambda rs: any(r["id"] == second["id"] and r["name"] == "Renamed owned area" for r in rs), "rename_accept")
    check("rename_preserves_all_uuids", [r["id"] for r in records()] == [r["id"] for r in before])
    before, ops = name_dialog("", "Third owned area", True, "create_accept_third")
    confirmed("create-desktop", ops, lambda rs: len(rs) == 3 and any(r["name"] == "Third owned area" for r in rs), "create_accept_third")
    third = next(r for r in records() if r["id"] not in [v["id"] for v in before])
    check("multiple_areas_use_distinct_native_uuids", len({r["id"] for r in records()}) == 3)
    remove_dialog(third["id"], False, "remove_reject")
    before, ops = remove_dialog(third["id"], True, "remove_accept_third")
    confirmed("remove-desktop", ops, lambda rs: len(rs) == 2 and not any(r["id"] == third["id"] for r in rs), "remove_accept_third")
    check("remove_keeps_survivor_uuids", {r["id"] for r in records()} == {initial["id"], second["id"]})
    before, ops = remove_dialog(second["id"], True, "remove_accept_second")
    confirmed("remove-desktop", ops, lambda rs: len(rs) == 1 and rs[0]["id"] == initial["id"], "remove_accept_second")
    before, ops = remove_dialog(initial["id"], True, "remove_accept_minimum_guard")
    check("minimum_one_rejects_after_actual_accept", records() == before and count() == 1 and current() == initial["id"] \
        and len(completed()) == ops and not pager.property("mutationPending") and bool(pager.property("lastError")))
    check("private_desktops_return_to_original", records() == [initial])
    evidence["final_desktops"] = records()
    evidence["completed_operations"] = completed()
    evidence["pointer_events"] = pointer_events
    evidence["double_click_interval_ms"] = app.styleHints().mouseDoubleClickInterval()
    check("intended_single_click_sequence_has_no_doubleclick_event", not any(e["type"] == "MouseButtonDblClick" for e in pointer_events))
    app.removeEventFilter(probe)
    evidence["source_sha256"] = {str(p.relative_to(ROOT)): hashlib.sha256(p.read_bytes()).hexdigest()
        for p in (UI / "DomainOSPager.qml", UI / "DomainOSDialogButtonBox.qml", UI / "DomainOSTextField.qml",
                  UI / "DomainOSButton.qml", Path(__file__))}
    evidence["input_scope"] = __doc__
