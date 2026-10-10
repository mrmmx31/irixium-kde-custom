#!/usr/bin/env python3
# SPDX-License-Identifier: GPL-3.0-or-later
"""Check functional Iconbox Qt gestures and approved canonical cell geometry."""
import argparse
import hashlib
import json
import os
from pathlib import Path
import sys
import tempfile

sys.dont_write_bytecode=True
REPO=Path(__file__).resolve().parents[2]

def digest(path):
    return hashlib.sha256(path.read_bytes()).hexdigest() if path.is_file() else None

def main():
    parser=argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--saida",type=Path,required=True)
    output=parser.parse_args().saida.resolve()
    if output.exists() and any(output.iterdir()):parser.error("Use a new or empty output")
    output.mkdir(parents=True,exist_ok=True)
    config=Path(os.environ.get("XDG_CONFIG_HOME",str(Path.home()/".config")))
    before={str(config/name):digest(config/name) for name in ("kdeglobals","kwinrc","plasmarc","plasma-org.kde.plasma.desktop-appletsrc")}
    checks,warnings={},[]
    report={"status":"failed","checks":checks,"qml_diagnostics":warnings,"protected_config_sha256":before,
            "scope":"Real Qt inputs against the production Iconbox with private task doubles; no native menu/action claim"}
    def require(name,value):
        checks[name]=bool(value)
        if not value:raise AssertionError(name)
    with tempfile.TemporaryDirectory(prefix="domainos-iconbox-") as folder:
        private=Path(folder)
        for key,name in (("HOME","home"),("XDG_CONFIG_HOME","config"),("XDG_DATA_HOME","data"),("XDG_CACHE_HOME","cache"),("XDG_RUNTIME_DIR","runtime")):
            path=private/name;path.mkdir(mode=0o700);os.environ[key]=str(path)
        for key in ("DISPLAY","WAYLAND_DISPLAY","LD_PRELOAD","QT_STYLE_OVERRIDE","QML_IMPORT_PATH","QML2_IMPORT_PATH"):
            os.environ.pop(key,None)
        os.environ.update(QT_QPA_PLATFORM="offscreen",QT_QPA_PLATFORMTHEME="generic",QT_QUICK_BACKEND="software",
            QT_QUICK_CONTROLS_STYLE="Basic",QT_SCALE_FACTOR="1",QML_DISABLE_DISK_CACHE="1",XDG_CURRENT_DESKTOP="NONE",
            DBUS_SESSION_BUS_ADDRESS="unix:path="+str(private/"disabled-bus"),DBUS_SYSTEM_BUS_ADDRESS="unix:path="+str(private/"disabled-system"))
        from PyQt6 import sip
        from PyQt6.QtCore import QObject,Qt,QUrl,QPointF,QPoint,QMetaObject,Q_ARG,Q_RETURN_ARG
        from PyQt6.QtGui import QGuiApplication,QWheelEvent
        from PyQt6.QtQml import QQmlApplicationEngine
        from PyQt6.QtQuick import QQuickWindow
        from PyQt6.QtTest import QTest
        app=QGuiApplication([sys.argv[0]]);engine=QQmlApplicationEngine()
        engine.warnings.connect(lambda messages:warnings.extend(message.toString() for message in messages))
        engine.load(QUrl.fromLocalFile(str(REPO/"plasma/tests/DomainOSIconboxPreview.qml")))
        require("production_iconbox_loaded",bool(engine.rootObjects()))
        window=sip.cast(engine.rootObjects()[0],QQuickWindow);controller=window.property("controller");box=window.property("iconbox")
        def settle():app.processEvents();QTest.qWait(35);app.processEvents()
        def call(method,*args):
            result=QMetaObject.invokeMethod(window,method,Qt.ConnectionType.DirectConnection,Q_RETURN_ARG("QVariant"),*(Q_ARG("QVariant",value) for value in args))
            settle();return result
        def state():return json.loads(call("uiState"))
        def descendants(root):
            yield root
            for child in root.childItems():yield from descendants(child)
        def find(name):
            result=next((node for candidate in app.allWindows() if isinstance(candidate,QQuickWindow)
                    for node in descendants(candidate.contentItem()) if node.objectName()==name and node.window() is not None),None)
            result=result or window.findChild(QObject,name)
            if result is None:raise AssertionError("Missing item "+name)
            return result
        def point(node):return node.mapToScene(QPointF(node.width()/2,node.height()/2)).toPoint()
        def click(name,mod=Qt.KeyboardModifier.NoModifier,button=Qt.MouseButton.LeftButton,activate=True):
            node=find(name)
            target_window=node.window()
            if target_window is None:raise AssertionError("Missing native window for "+name)
            # QTest delivers pointer events directly; unlike the platform mouse,
            # this does not activate the clicked top-level popup/host itself.
            if activate:target_window.requestActivate();settle()
            QTest.mouseMove(target_window,point(node));app.processEvents()
            QTest.mouseClick(target_window,button,mod,point(node));settle();return state()
        def task(key):return "domainosLiveTask_"+key
        def member(key):return "domainosGroupMember_"+key
        def member_title(key):return "domainosGroupMemberTitle_"+key
        def toggle_state(label):
            toggle=next((node for node in descendants(box) if "DomainOSPopupToggle" in node.metaObject().className()),None)
            button=find(task("group:terminal"))
            anchor=toggle.property("anchor") if toggle else None
            report.setdefault("toggle_events",[]).append({"event":label,"group":state()["group"],
                "helper":{name:toggle.property(name) for name in ("showing","pressCaptured","wasShowing")} if toggle else None,
                "anchor_matches_button":bool(anchor is not None and sip.unwrapinstance(anchor)==sip.unwrapinstance(button)),
                "button_pressed":button.property("pressed")})
        def toggle_click():
            node=find(task("group:terminal"));owner=node.window();position=point(node)
            toggle_state("before_move")
            QTest.mouseMove(owner,position);app.processEvents();toggle_state("after_move")
            QTest.mousePress(owner,Qt.MouseButton.LeftButton,Qt.KeyboardModifier.NoModifier,position);app.processEvents();toggle_state("after_press")
            QTest.mouseRelease(owner,Qt.MouseButton.LeftButton,Qt.KeyboardModifier.NoModifier,position);settle();toggle_state("after_release")
        try:
            settle()
            first=find(task("group:terminal"))
            require("canonical_iconbox_size_preserved",box.width()==594 and box.height()==150)
            require("canonical_first_cell_and_label_preserved",(first.x(),first.y(),first.width(),first.height())==(60,26,66,98)
                    and (find(first.objectName()+"Label").x(),find(first.objectName()+"Label").y())==(2,68))
            require("normal_palette_and_label_font_preserved",find(first.objectName()+"LabelText").property("font").family()=="Nimbus Sans"
                    and find(first.objectName()+"LabelText").property("font").pixelSize()==16)
            click(task("group:terminal"))
            require("group_without_checkbox_selection_sends_no_action",state()["group"] and not state()["selected"] and not state()["requests"])
            require("group_unselected_title_capture_saved",find(member_title("window:2")).window().grabWindow().save(str(output/"ICONBOX-GROUP-NO-SELECTION.png")))
            # These are independent launcher clicks, not the double-click
            # activation gesture checked below. Wait only in the harness.
            QTest.qWait(app.styleHints().mouseDoubleClickInterval()+40)
            toggle_click()
            require("same_group_tile_click_closes_picker_without_selecting_or_activating",not state()["group"] and not state()["selected"] and not state()["requests"])
            QTest.qWait(app.styleHints().mouseDoubleClickInterval()+40)
            click(task("group:terminal"),activate=False)
            require("same_group_tile_reopens_after_toggle_close",state()["group"] and not state()["selected"] and not state()["requests"])
            group_button=find(task("group:terminal"))
            QTest.mouseMove(window,point(group_button));QTest.mouseDClick(window,Qt.MouseButton.LeftButton,Qt.KeyboardModifier.NoModifier,point(group_button));settle()
            require("group_tile_double_click_keeps_picker_without_arbitrary_member_activation",state()["group"] and not state()["selected"] and not state()["requests"])
            QTest.qWait(app.styleHints().mouseDoubleClickInterval()+40)
            require("group_double_click_member_list_remains_available",state()["group"] and not state()["selected"] and not state()["requests"])
            click(member_title("window:2"))
            require("group_title_without_selection_restores_only_clicked_member",not state()["group"] and not state()["selected"]
                    and state()["requests"]==[{"action":"activate","ids":[2],"argument":None}])
            click(task("group:terminal"));requests_before=list(state()["requests"])
            click(member("window:1"))
            require("group_checkbox_selects_without_activation",state()["group"] and state()["selected"]==["window:1"]
                    and state()["requests"]==requests_before)
            require("group_checkbox_selection_capture_saved",find(member_title("window:1")).window().grabWindow().save(str(output/"ICONBOX-GROUP-CHECKBOX-SELECTED.png")))
            click(member_title("window:3"))
            require("group_title_in_checkbox_mode_adds_member_without_activation",set(state()["selected"])=={"window:1","window:3"}
                    and state()["group"] and state()["requests"]==requests_before)
            click(member_title("window:1"))
            require("group_title_in_checkbox_mode_removes_member_without_activation",state()["selected"]==["window:3"]
                    and state()["group"] and state()["requests"]==requests_before)
            click(member_title("window:3"))
            require("group_title_can_empty_checkbox_selection_without_activation",not state()["selected"] and state()["group"]
                    and state()["requests"]==requests_before)
            click(member_title("window:2"))
            require("group_title_returns_to_restore_when_selection_is_empty",not state()["group"] and not state()["selected"]
                    and len(state()["requests"])==len(requests_before)+1 and state()["requests"][-1]["ids"]==[2])
            click(task("group:terminal"));requests_before=list(state()["requests"])
            checkbox=find(member("window:1"));popup_window=checkbox.window();checkbox_point=point(checkbox)
            QTest.mousePress(popup_window,Qt.MouseButton.LeftButton,Qt.KeyboardModifier.NoModifier,checkbox_point);app.processEvents()
            call("mutate",1,"pid",9901)
            QTest.mouseRelease(popup_window,Qt.MouseButton.LeftButton,Qt.KeyboardModifier.NoModifier,checkbox_point);settle()
            require("group_checkbox_stale_pid_rejected_before_selection",not state()["selected"] and state()["requests"]==requests_before)
            call("mutate",1,"pid",501)
            title=find(member_title("window:3"));popup_window=title.window();title_point=point(title)
            QTest.mousePress(popup_window,Qt.MouseButton.LeftButton,Qt.KeyboardModifier.NoModifier,title_point);app.processEvents()
            call("mutate",3,"pid",9903)
            QTest.mouseRelease(popup_window,Qt.MouseButton.LeftButton,Qt.KeyboardModifier.NoModifier,title_point);settle()
            require("group_title_stale_pid_rejected_before_activation",not state()["selected"] and state()["requests"]==requests_before)
            call("resetUi")
            click(task("window:6"));click(task("group:terminal"))
            require("unrelated_individual_selection_does_not_mark_group_checkboxes",state()["selected"]==["window:6"]
                    and not find(member("window:1")).property("checked") and not find(member("window:2")).property("checked"))
            click(member_title("window:2"))
            require("title_without_checkbox_history_restores_despite_unrelated_selection",not state()["group"]
                    and state()["selected"]==["window:6"] and state()["requests"]==[{"action":"activate","ids":[2],"argument":None}])
            call("resetUi")
            click(task("window:6"))
            require("singleton_plain_click_opens_one_member_without_checkbox_intention",state()["group"]
                    and controller.property("pickerSelectionCount")==0 and not controller.property("memberSelectionActive")
                    and not find(member("window:6")).property("checked") and state()["selected"]==["window:6"] and not state()["requests"])
            click(member("window:6"))
            require("singleton_checkbox_enters_explicit_selection_without_activation",find(member("window:6")).property("checked")
                    and controller.property("pickerSelectionCount")==1 and controller.property("memberSelectionActive") and not state()["requests"])
            click(member_title("window:6"))
            require("singleton_title_deselects_only_in_checkbox_mode",state()["group"] and not state()["selected"]
                    and not controller.property("memberSelectionActive") and not state()["requests"])
            click(member_title("window:6"))
            require("singleton_title_without_checkbox_restores_directly",not state()["group"] and state()["requests"]==[{"action":"activate","ids":[6],"argument":None}])
            call("resetUi")
            node=find(task("window:6"));QTest.mousePress(window,Qt.MouseButton.LeftButton,Qt.KeyboardModifier.NoModifier,point(node));app.processEvents()
            require("press_relief_immediate_without_timer",node.property("pressed") and node.property("pressOffset")==2)
            QTest.mouseRelease(window,Qt.MouseButton.LeftButton,Qt.KeyboardModifier.NoModifier,point(node));settle()
            require("single_click_selects_immediately_without_activating",state()["selected"]==["window:6"] and not state()["requests"])
            require("selected_relief_persists_on_release",find(task("window:6")+"Relief").property("sunken") and not node.property("pressed"))
            selected_before=state()["selected"]
            call("mutate",6,"minimized",True)
            node=find(task("window:6"))
            require("minimized_individual_releases_body_and_label_relief_without_clearing_selection",state()["selected"]==selected_before
                    and node.property("selected") and node.property("fullyMinimized") and not node.property("pressed")
                    and not find(task("window:6")+"Relief").property("sunken") and not find(task("window:6")+"Label").property("sunken"))
            require("minimized_individual_keeps_selection_label_color",find(task("window:6")+"Label").property("face")==box.property("colorPalette").property("blue"))
            require("minimized_individual_capture_saved",window.grabWindow().save(str(output/"ICONBOX-MINIMIZED-SELECTED.png")))
            QTest.mousePress(window,Qt.MouseButton.LeftButton,Qt.KeyboardModifier.NoModifier,point(node));app.processEvents()
            require("minimized_individual_press_feedback_still_immediate",node.property("pressed") and node.property("pressOffset")==2
                    and find(task("window:6")+"Relief").property("sunken"))
            QTest.mouseRelease(window,Qt.MouseButton.LeftButton,Qt.KeyboardModifier.NoModifier,point(node));settle()
            require("minimized_individual_release_returns_to_raised_without_losing_selection",not node.property("pressed")
                    and not find(task("window:6")+"Relief").property("sunken") and state()["selected"]==selected_before)
            call("mutate",6,"minimized",False)
            require("restored_individual_selection_relief_returns_with_same_identity",state()["selected"]==selected_before
                    and not find(task("window:6")).property("fullyMinimized") and find(task("window:6")+"Relief").property("sunken"))
            node=find(task("window:6"));owner=node.window();position=point(node)
            # QTest.mouseDClick sends the double-click event only. A platform
            # double click also has the first press/release, which freezes the
            # task identity and active state. Keep that complete input gesture.
            report["singleton_double_click_events"]=[{"phase":"before","state":state()}]
            QTest.mouseMove(owner,position);app.processEvents()
            QTest.mousePress(owner,Qt.MouseButton.LeftButton,Qt.KeyboardModifier.NoModifier,position);app.processEvents()
            report["singleton_double_click_events"].append({"phase":"first_press","state":state(),"pressed":node.property("pressed")})
            QTest.mouseRelease(owner,Qt.MouseButton.LeftButton,Qt.KeyboardModifier.NoModifier,position);app.processEvents()
            report["singleton_double_click_events"].append({"phase":"first_release","state":state()})
            QTest.mouseDClick(owner,Qt.MouseButton.LeftButton,Qt.KeyboardModifier.NoModifier,position);app.processEvents()
            report["singleton_double_click_events"].append({"phase":"double_click","state":state()})
            QTest.mouseRelease(owner,Qt.MouseButton.LeftButton,Qt.KeyboardModifier.NoModifier,position);settle()
            report["singleton_double_click_events"].append({"phase":"second_release","state":state()})
            require("double_click_requests_only_native_activation",state()["requests"][-1]["action"]=="activate" and state()["requests"][-1]["ids"]==[6])
            click(task("window:7"),Qt.KeyboardModifier.ControlModifier)
            require("control_selection_keeps_both_identities",set(state()["selected"])=={"window:6","window:7"})
            QTest.keyPress(window,Qt.Key.Key_Control);QTest.keyRelease(window,Qt.Key.Key_Control);settle()
            require("released_modifiers_open_one_batch_menu",state()["operations"] and state()["operationsOpened"]==1)
            require("batch_geometry_actions_disabled_without_backend",not find("domainosBatchColumns").property("enabled")
                    and not find("domainosBatchMinimize").property("enabled"))
            require("operations_capture_saved",window.grabWindow().save(str(output/"ICONBOX-OPERATIONS.png")))
            QTest.keyClick(window,Qt.Key.Key_Escape);settle()
            require("escape_closes_operations_without_actions",not state()["operations"] and len(state()["requests"])==1)
            click(task("group:terminal"));require("group_popup_has_individual_members",state()["group"] and find("domainosGroupMember_window:1") is not None)
            click("domainosGroupMember_window:1");click("domainosGroupMember_window:3")
            require("group_checkboxes_do_not_select_other_members",set(state()["selected"])=={"window:6","window:7","window:1","window:3"})
            require("checkbox_menu_remains_open_without_organization",state()["group"] and not state()["operations"])
            click(member("window:2"));group_selection_before=state()["selected"]
            require("fully_selected_mixed_group_keeps_selection_relief",find(task("group:terminal")).property("selected")
                    and not find(task("group:terminal")).property("fullyMinimized") and find(task("group:terminal")+"Relief").property("sunken"))
            call("mutate",1,"minimized",True);call("mutate",3,"minimized",True)
            require("fully_minimized_group_releases_both_reliefs_preserving_all_checkboxes",find(task("group:terminal")).property("fullyMinimized")
                    and not find(task("group:terminal")+"Relief").property("sunken") and not find(task("group:terminal")+"Label").property("sunken")
                    and state()["selected"]==group_selection_before and all(find(member("window:"+str(index))).property("checked") for index in (1,2,3)))
            require("fully_minimized_group_capture_saved",window.grabWindow().save(str(output/"ICONBOX-GROUP-FULLY-MINIMIZED.png")))
            call("mutate",1,"minimized",False)
            require("mixed_restored_group_returns_relief_without_losing_checkbox_selection",not find(task("group:terminal")).property("fullyMinimized")
                    and find(task("group:terminal")+"Relief").property("sunken") and find(task("group:terminal")+"Label").property("sunken")
                    and state()["selected"]==group_selection_before and all(find(member("window:"+str(index))).property("checked") for index in (1,2,3)))
            call("mutate",3,"minimized",False);click(member("window:2"))
            require("group_capture_saved",find("domainosGroupMember_window:1").window().grabWindow().save(str(output/"ICONBOX-GROUP.png")))
            click("domainosGroupContinue");require("group_continue_preserves_selection",not state()["group"] and len(state()["selected"])==4)
            click(task("group:browser"));click("domainosGroupMember_window:4")
            require("selection_accumulates_across_group_popups",set(state()["selected"])=={"window:6","window:7","window:1","window:3","window:4"})
            click("domainosGroupContinue")
            for action in (1,3,5):
                box.setProperty("middleClickAction",action)
                selected_before=set(state()["selected"]);requests_before=list(state()["requests"])
                click(task("group:terminal"),button=Qt.MouseButton.MiddleButton)
                require("middle_group_action_%d_requires_member_choice"%action,state()["group"] and set(state()["selected"])==selected_before and state()["requests"]==requests_before)
                click("domainosGroupContinue")
            box.setProperty("middleClickAction",2)
            window.resize(610,109);box.setY(0);settle()
            selected_before=set(state()["selected"]);requests_before=list(state()["requests"])
            click(task("group:terminal"))
            member=find("domainosGroupMember_window:2");popup_window=member.window()
            require("short_panel_group_content_uses_separate_quick_window",window.height()==109
                    and popup_window is not window and popup_window.isVisible() and popup_window.height()>window.height())
            click("domainosGroupMember_window:2")
            require("short_panel_group_member_click_preserves_other_targets",set(state()["selected"])==selected_before|{"window:2"}
                    and state()["requests"]==requests_before and state()["group"])
            require("short_panel_group_capture_saved",popup_window.grabWindow().save(str(output/"ICONBOX-GROUP-SHORT-PANEL.png")))
            click("domainosGroupMember_window:2");click("domainosGroupContinue")
            require("short_panel_group_continue_closes_without_window_action",not state()["group"]
                    and set(state()["selected"])==selected_before and state()["requests"]==requests_before)
            window.requestActivate();settle()
            QTest.keyPress(window,Qt.Key.Key_Control);QTest.keyRelease(window,Qt.Key.Key_Control);settle()
            operations_window=find("domainosBatchColumns").window()
            require("short_panel_operations_use_separate_quick_window",state()["operations"]
                    and operations_window is not window and operations_window.isVisible() and operations_window.height()>window.height())
            require("short_panel_operations_capture_saved",operations_window.grabWindow().save(str(output/"ICONBOX-OPERATIONS-SHORT-PANEL.png")))
            QTest.keyClick(operations_window,Qt.Key.Key_Escape);settle()
            require("short_panel_operations_escape_preserves_targets",not state()["operations"]
                    and set(state()["selected"])==selected_before and state()["requests"]==requests_before)
            window.resize(610,500);box.setY(340);settle()
            original_y=window.y();window.setY(350)
            window.contentItem().setScale(.5);settle();click(task("group:terminal"))
            member=find("domainosGroupMember_window:1");popup_window=member.window()
            anchor_top=box.mapToGlobal(QPointF(0,0)).y()
            popup_bottom=popup_window.frameGeometry().bottom()
            report["scaled_group_anchor"]={"scale":box.property("popupAnchorScale"),
                    "iconbox_global_top":anchor_top,"popup_frame_bottom":popup_bottom,
                    "popup_height":popup_window.height(),"bottom_frame_margin":popup_window.frameMargins().bottom()}
            require("half_scale_group_window_entirely_above_iconbox",box.property("popupAnchorScale")==.5
                    and popup_window is not window and popup_window.height()>100
                    and popup_bottom<=anchor_top+popup_window.frameMargins().bottom())
            require("half_scale_group_capture_saved",popup_window.grabWindow().save(str(output/"ICONBOX-GROUP-HALF-SCALE.png")))
            click("domainosGroupContinue");window.contentItem().setScale(1);window.setY(original_y);settle()
            require("half_scale_group_close_preserves_targets",not state()["group"]
                    and set(state()["selected"])==selected_before and state()["requests"]==requests_before)
            click(task("window:6"),button=Qt.MouseButton.RightButton)
            require("right_click_preserves_selection_and_close",state()["menu"] and len(state()["selected"])==5 and find("domainosBasicClose").property("enabled"))
            require("force_termination_is_submenu_and_disabled_without_service",not find("domainosBasicTerminate").property("enabled"))
            # Start a new selection scenario. Previous checks deliberately
            # accumulated members across groups; a plain click preserves them.
            call("resetUi");call("addGeometryBackend")
            click(task("window:6"));click(task("window:7"),Qt.KeyboardModifier.ControlModifier)
            QTest.keyPress(window,Qt.Key.Key_Control);QTest.keyRelease(window,Qt.Key.Key_Control);settle()
            require("organization_enabled_with_real_provider_contract",find("domainosBatchColumns").property("enabled") and find("domainosBatchMinimize").property("enabled"))
            click("domainosBatchColumns")
            require("batch_menu_requests_current_destination_and_only_chosen",state()["layouts"][-1]["mode"]=="columns"
                    and {row["key"] for row in state()["layouts"][-1]["windows"]}=={"window:6","window:7"})
            call("closeMenus")
            controller.setProperty("groupingMode",0);settle();call("seedMany")
            require("total_tasks_not_limited_to_seven_slots",state()["next"] and controller.property("windowCount")==16)
            click("domainosIconboxNext");require("next_arrow_navigates_exactly_one_page",state()["firstVisible"]==7 and state()["previous"])
            click("domainosIconboxNext");require("last_page_retains_all_remaining_tasks",state()["firstVisible"]==14 and not state()["next"])
            click("domainosIconboxPrevious");require("previous_arrow_restores_previous_page",state()["firstVisible"]==7)
            click("domainosIconboxPrevious")
            node=find(task("window:6"));QTest.mousePress(window,Qt.MouseButton.LeftButton,Qt.KeyboardModifier.NoModifier,point(node));app.processEvents()
            call("mutate",6,"pid",9996)
            QTest.mouseRelease(window,Qt.MouseButton.LeftButton,Qt.KeyboardModifier.NoModifier,point(node));settle()
            require("press_identity_invalidated_before_release_is_rejected","window:6" not in state()["selected"] and state()["errors"])
            selection_before=set(state()["selected"]);node=find(task("window:3"))
            QTest.mousePress(window,Qt.MouseButton.LeftButton,Qt.KeyboardModifier.NoModifier,point(node))
            QTest.mouseMove(window,QPointF(2,2).toPoint());QTest.mouseRelease(window,Qt.MouseButton.LeftButton,Qt.KeyboardModifier.NoModifier,QPointF(2,2).toPoint());settle()
            require("canceled_drag_never_changes_selection",set(state()["selected"])==selection_before)
            controller.setProperty("filterMode","automatic");controller.setProperty("automaticThreshold",1);settle()
            require("automatic_filter_status_is_visible_without_changing_chassis",find("domainosIconboxFilterStatus").isVisible() and box.width()==594 and box.height()==150)
            controller.setProperty("filterMode","normal");settle()
            require("live_capture_saved",window.grabWindow().save(str(output/"ICONBOX-LIVE.png")))
            call("resetUi");controller.setProperty("groupingMode",1);call("seedManyGroups")
            click(task("group:pagegroup0"))
            require("paginated_group_picker_initially_open",state()["group"] and not state()["requests"])
            click("domainosGroupMember_window:100");page_selection=state()["selected"]
            require("paginated_group_checkbox_selected_before_navigation",page_selection==["window:100"] and not state()["requests"])
            def wheel_on(name,angle):
                # Deliver only wheel input to the host. Do not request focus:
                # the popup must be closed by page navigation itself.
                node=find(name);position=point(node)
                event=QWheelEvent(QPointF(position),QPointF(window.mapToGlobal(position)),QPoint(),QPoint(0,angle),
                    Qt.MouseButton.NoButton,Qt.KeyboardModifier.NoModifier,Qt.ScrollPhase.NoScrollPhase,False)
                app.sendEvent(window,event);settle()
            wheel_on(task("group:pagegroup0"),-120)
            require("wheel_pagination_without_focus_request_closes_previous_picker",state()["firstVisible"]==7
                    and not state()["group"] and controller.property("groupSelectorKey")=="" and not state()["requests"])
            click(task("group:pagegroup7"),activate=False)
            require("new_group_after_wheel_opens_on_first_click",state()["group"]
                    and controller.property("groupSelectorKey")=="group:pagegroup7" and not state()["requests"])
            wheel_on(task("group:pagegroup7"),120)
            require("return_wheel_dismisses_second_page_picker_without_actions",state()["firstVisible"]==0
                    and not state()["group"] and not state()["requests"])
            click(task("group:pagegroup0"),activate=False)
            require("original_group_reopens_on_first_click_after_return_wheel",state()["group"]
                    and controller.property("groupSelectorKey")=="group:pagegroup0" and not state()["requests"])
            wheel_on(task("group:pagegroup0"),120)
            require("bounded_wheel_keeps_current_picker_when_page_does_not_change",state()["firstVisible"]==0
                    and state()["group"] and controller.property("groupSelectorKey")=="group:pagegroup0" and not state()["requests"])
            require("page_navigation_preserves_explicit_checkbox_selection",state()["selected"]==page_selection
                    and find("domainosGroupMember_window:100").property("checked"))
            require("qml_diagnostics_zero",not warnings)
            require("real_profiles_unchanged",all(digest(Path(name))==value for name,value in before.items()))
            report.update(status="passed",final_state=state())
        except Exception as error:
            report["error"]=str(error);report["last_state"]=state()
        window.close();app.processEvents()
    (output/"RESULTADO.json").write_text(json.dumps(report,indent=2,ensure_ascii=False)+"\n")
    print(json.dumps({"status":report["status"],"checks":len(checks),"report":str(output/"RESULTADO.json"),"error":report.get("error")}))
    return 0 if report["status"]=="passed" else 1

if __name__=="__main__":sys.exit(main())
