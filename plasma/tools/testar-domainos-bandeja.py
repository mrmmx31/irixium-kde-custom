#!/usr/bin/env python3
# SPDX-FileCopyrightText: 2026 IRIX Classic contributors
# SPDX-License-Identifier: GPL-3.0-or-later
"""Test DomainOS with the native Plasma tray containment on private Xvfb/D-Bus.

The fixture supplies real test-owned StatusNotifier D-Bus services. Native Wi-Fi,
Bluetooth, volume and notification applets remain native, with unavailable host
hardware/session services isolated. No real connection, sound, history or user
configuration is changed. Native notification history contents need a shell test.
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
import time

sys.dont_write_bytecode = True
REPO = Path(__file__).resolve().parents[2]
IDENTIFIER = "org.irixclassic.domainos.tray.test"
PROVIDERS = ["org.kde.plasma.networkmanagement", "org.kde.plasma.volume", "org.kde.plasma.bluetooth", "org.kde.plasma.notifications"]


def worker(output):
    if os.environ.get("IRIX_DOMAINOS_TRAY_PRIVATE_SESSION") != "1":
        raise RuntimeError("Private session required")
    from PyQt6.QtCore import QObject, pyqtClassInfo, pyqtProperty, pyqtSignal, pyqtSlot
    from PyQt6.QtDBus import QDBusConnection, QDBusObjectPath
    from PyQt6 import sip
    import ctypes
    from PyQt6.QtWidgets import QApplication
    # The test system bus is also private. Owning these names lets the native
    # tray instantiate Wi-Fi/Bluetooth providers; no real device service exists.
    os.environ["DBUS_SYSTEM_BUS_ADDRESS"] = os.environ["DBUS_SESSION_BUS_ADDRESS"]
    app = QApplication([])
    tooltip_types=ctypes.CDLL(str(output/'native-tooltip-type.so'))
    tooltip_types.domainosFixtureAddSniAdaptor.argtypes=(ctypes.c_void_p,ctypes.c_int)
    tooltip_types.domainosFixtureAddSniAdaptor.restype=None
    bus = QDBusConnection.sessionBus()
    assert bus.registerService("org.freedesktop.NetworkManager")
    assert bus.registerService("org.bluez")
    @pyqtClassInfo("D-Bus Interface", "org.freedesktop.NetworkManager")
    class EmptyNetworkManager(QObject):
        @pyqtProperty("uint")
        def State(self): return 20
        @pyqtProperty(bool)
        def NetworkingEnabled(self): return False
        @pyqtProperty(bool)
        def WirelessEnabled(self): return False
        @pyqtProperty(bool)
        def WirelessHardwareEnabled(self): return False
    unavailable_network=EmptyNetworkManager()
    assert bus.registerObject("/org/freedesktop/NetworkManager",unavailable_network,QDBusConnection.RegisterOption.ExportAllProperties)
    @pyqtClassInfo("D-Bus Interface", "org.kde.StatusNotifierWatcher")
    class Watcher(QObject):
        StatusNotifierItemRegistered = pyqtSignal(str)
        StatusNotifierItemUnregistered = pyqtSignal(str)
        StatusNotifierHostRegistered = pyqtSignal()
        def __init__(self):
            super().__init__(); self.items = []
        @pyqtProperty("QStringList")
        def RegisteredStatusNotifierItems(self): return self.items
        @pyqtProperty(bool)
        def IsStatusNotifierHostRegistered(self): return True
        @pyqtProperty(int)
        def ProtocolVersion(self): return 0
        @pyqtSlot(str)
        def RegisterStatusNotifierItem(self, service):
            source = service + "/StatusNotifierItem"
            if source not in self.items:
                self.items.append(source); self.StatusNotifierItemRegistered.emit(source)
        @pyqtSlot(str)
        def RegisterStatusNotifierHost(self, service): self.StatusNotifierHostRegistered.emit()
        @pyqtSlot()
        def ClearTestItems(self):
            removed=self.items[:];self.items=[]
            for source in removed: self.StatusNotifierItemUnregistered.emit(source)
    @pyqtClassInfo("D-Bus Interface", "org.kde.StatusNotifierItem")
    class Item(QObject):
        NewStatus = pyqtSignal(str)
        NewIcon = pyqtSignal()
        NewAttentionIcon = pyqtSignal()
        NewOverlayIcon = pyqtSignal()
        NewToolTip = pyqtSignal()
        NewTitle = pyqtSignal()
        def __init__(self, index):
            super().__init__(); self.index = index; self.calls = []
        @pyqtProperty(str)
        def Category(self): return "ApplicationStatus"
        @pyqtProperty(str)
        def Id(self): return "domainos-fixture-sni-" + str(self.index)
        @pyqtProperty(str)
        def Title(self): return "Native DomainOS fixture " + str(self.index)
        @pyqtProperty(str)
        def Status(self): return "Passive" if self.index == 8 else "NeedsAttention" if self.index == 0 else "Active"
        @pyqtProperty(str)
        def IconName(self): return "utilities-terminal"
        @pyqtProperty(str)
        def AttentionIconName(self): return "dialog-warning"
        @pyqtProperty(str)
        def OverlayIconName(self): return ""
        @pyqtProperty(str)
        def IconThemePath(self): return ""
        @pyqtProperty("uint")
        def WindowId(self): return 0
        @pyqtProperty(bool)
        def ItemIsMenu(self): return False
        @pyqtProperty(QDBusObjectPath)
        def Menu(self): return QDBusObjectPath("/NO_DBUSMENU")
        @pyqtSlot(int, int)
        def Activate(self, x, y): self.calls.append({"action":"Activate", "x":x, "y":y})
        @pyqtSlot(int, int)
        def SecondaryActivate(self, x, y): self.calls.append({"action":"SecondaryActivate", "x":x, "y":y})
        @pyqtSlot(int, int)
        def ContextMenu(self, x, y): self.calls.append({"action":"ContextMenu", "x":x, "y":y})
        @pyqtSlot(int, str)
        def Scroll(self, delta, orientation): self.calls.append({"action":"Scroll", "delta":delta, "orientation":orientation})
        @pyqtSlot(str)
        def ProvideXdgActivationToken(self, token): pass
    watcher = Watcher()
    assert bus.registerService("org.kde.StatusNotifierWatcher")
    assert bus.registerObject("/StatusNotifierWatcher", watcher, QDBusConnection.RegisterOption.ExportAllSlots | QDBusConnection.RegisterOption.ExportAllProperties | QDBusConnection.RegisterOption.ExportAllSignals)
    items, connections = [], []
    for index in range(9):
        connection = QDBusConnection.connectToBus(QDBusConnection.BusType.SessionBus, "tray-fixture-" + str(index))
        service = "org.irixclassic.DomainOSTrayFixture.Item" + str(index)
        assert connection.registerService(service)
        item = Item(index)
        tooltip_types.domainosFixtureAddSniAdaptor(sip.unwrapinstance(item),index)
        assert connection.registerObject("/StatusNotifierItem", item, QDBusConnection.RegisterOption.ExportAdaptors)
        items.append(item); connections.append(connection); watcher.RegisterStatusNotifierItem(service)
    env = dict(os.environ, LD_PRELOAD=str(output / "tray-host.so"), IRIX_DOMAINOS_TRAY_TEST="1",
               IRIX_DOMAINOS_TRAY_REPORT=str(output / "native.json"), IRIX_DOMAINOS_TRAY_DIR=str(output))
    with (output / "host.log").open("w") as log:
        command=["plasmawindowed",IDENTIFIER]
        if os.environ.get("IRIX_DOMAINOS_TRAY_GDB") == "1":
            preload=env.pop("LD_PRELOAD")
            command=["gdb","--batch","-ex","set environment LD_PRELOAD "+preload,"-ex","run","-ex","bt","--args",*command]
        host = subprocess.Popen(command, env=env, stdout=log, stderr=subprocess.STDOUT)
        deadline = time.monotonic() + 28
        while host.poll() is None and time.monotonic() < deadline:
            app.processEvents(); time.sleep(.01)
        if host.poll() is None:
            host.terminate(); host.wait(3)
    calls = {item.Id:item.calls for item in items}
    (output / "provider-calls.json").write_text(json.dumps(calls, indent=2) + "\n")
    (output / "worker-exit.json").write_text(json.dumps({"returncode":host.returncode}) + "\n")
    return host.returncode


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--saida", type=Path, required=True)
    parser.add_argument("--recursos-encerrados",type=Path,help="Reuse identical immutable resources from a completed owned fixture under /tmp")
    parser.add_argument("--worker", action="store_true", help=argparse.SUPPRESS)
    args = parser.parse_args(); output = args.saida.resolve()
    if args.worker: return worker(output)
    if not output.is_relative_to(Path("/tmp")) or output.exists(): parser.error("Use a new directory under /tmp")
    output.mkdir(mode=0o700)
    env = os.environ.copy()
    config = Path(env.get("XDG_CONFIG_HOME", str(Path.home() / ".config")))
    def hashes():
        return {name:hashlib.sha256((config/name).read_bytes()).hexdigest() if (config/name).is_file() else None
                for name in ("kdeglobals","plasmarc","kwinrc","plasma-org.kde.plasma.desktop-appletsrc")}
    before = hashes()
    for key in ("DISPLAY","WAYLAND_DISPLAY","DBUS_SESSION_BUS_ADDRESS","DBUS_STARTER_ADDRESS","DBUS_STARTER_BUS_TYPE","SESSION_MANAGER","LD_PRELOAD","XAUTHORITY","QML_IMPORT_PATH","QML2_IMPORT_PATH","QT_STYLE_OVERRIDE","QT_QUICK_CONTROLS_STYLE","KDE_FULL_SESSION","KDE_SESSION_VERSION","XDG_SESSION_ID"):
        env.pop(key,None)
    for key,name in (("HOME","home"),("XDG_CONFIG_HOME","config"),("XDG_DATA_HOME","data"),("XDG_CACHE_HOME","cache"),("XDG_STATE_HOME","state"),("XDG_RUNTIME_DIR","runtime")):
        folder=output/name;folder.mkdir(mode=0o700);env[key]=str(folder)
    plasmoids = output/"data/plasma/plasmoids";plasmoids.mkdir(parents=True)
    resource_base=args.recursos_encerrados.resolve() if args.recursos_encerrados else None
    if resource_base:
        if not resource_base.is_relative_to(Path('/tmp')) or resource_base==Path('/tmp') or resource_base.stat().st_uid!=os.getuid():parser.error('Reuse only an owned /tmp fixture')
        resource_report=json.loads((resource_base/'RESULTADO.json').read_text())
        if resource_report.get('checks',{}).get('native_host_exited') is not True:parser.error('The resource fixture must have a confirmed terminal native host')
    def copy_resource(source,target):
        previous=resource_base/Path(target).relative_to(output) if resource_base else None
        if previous and previous.is_file() and not previous.is_symlink() and Path(source).is_file() and previous.read_bytes()==Path(source).read_bytes():
            os.link(previous,target);return str(target)
        return shutil.copy2(source,target)
    shutil.copytree(REPO/"plasma/applets/org.irixclassic.domainos.panel", plasmoids/"org.irixclassic.domainos.panel",ignore=shutil.ignore_patterns("__pycache__","*.pyc"),copy_function=copy_resource)
    for name in ("IrixClassic","IrixClassicDomainOS"):
        shutil.copytree(REPO/"plasma"/name,output/"data/plasma/desktoptheme"/name,copy_function=copy_resource)
    fixture=plasmoids/IDENTIFIER;(fixture/"contents/ui").mkdir(parents=True)
    (fixture/"metadata.json").write_text(json.dumps({"KPlugin":{"Id":IDENTIFIER,"Name":"DomainOS tray private test","Version":"1.0","License":"GPL-3.0-or-later"},"KPackageStructure":"Plasma/Applet","X-Plasma-API-Minimum-Version":"6.0","X-Plasma-RootPath":"org.kde.plasma.systemtray"}))
    (fixture/"contents/ui/main.qml").write_text('''import QtQuick
import QtQuick.Layouts
import org.kde.plasma.plasmoid
import org.kde.plasma.core as PlasmaCore
import "../../../org.irixclassic.domainos.panel/contents/ui" as Panel
PlasmoidItem {
    id:host
    property ContainmentItem internalSystray
    preferredRepresentation:fullRepresentation
    Plasmoid.backgroundHints:PlasmaCore.Types.NoBackground
    function attach() {
        internalSystray=Plasmoid.internalSystray
        if(internalSystray) {
            internalSystray.plasmoid.configuration.shownItems=''' + json.dumps(PROVIDERS + ["domainos-fixture-sni-" + str(index) for index in range(8)]) + '''
            internalSystray.plasmoid.configuration.hiddenItems=["domainos-fixture-sni-8"]
            internalSystray.plasmoid.configuration.extraItems=''' + json.dumps(PROVIDERS) + '''
        }
    }
    Component.onCompleted:attach()
    Connections { target:Plasmoid; function onInternalSystrayChanged(){host.attach()} }
    fullRepresentation:Item {
        id:fixture;objectName:"domainosTrayFixture"
        implicitWidth:640;implicitHeight:109
        Layout.minimumWidth:640;Layout.minimumHeight:109
        readonly property real domainosRenderScale:0.5
        property int scenario:0
        readonly property alias controller:adapter
        readonly property Item hoverSni:adapter.entries.find(entry=>entry.id==="domainos-fixture-sni-1")?.item || null
        property string snapshotJson:JSON.stringify(Object.assign(adapter.snapshot(),{
            activeNativeApplet:host.internalSystray?.systemTrayState.activeApplet?.plasmoid.pluginName || "",
            activeNativeFullRepresentation:!!host.internalSystray?.systemTrayState.activeApplet?.fullRepresentationItem,
            items:adapter.availableItems,hintsEnabled:adapter.barHintsEnabled,
            nativeTooltipPolicy:adapter.entries.map(entry=>({id:entry.id,type:entry.type,active:entry.item.active})),
            hoveredSni:hoverSni ? ({active:hoverSni.active,containsMouse:hoverSni.containsMouse,mainText:hoverSni.mainText,
                width:hoverSni.width,height:hoverSni.height,visible:hoverSni.visible,opacity:hoverSni.opacity,
                parentName:hoverSni.parent?.objectName || "",parentParentName:hoverSni.parent?.parent?.objectName || "",
                effectiveStatus:hoverSni.effectiveStatus,inVisibleLayout:hoverSni.inVisibleLayout,
                toolTipTitle:hoverSni.model?.ToolTipTitle || "",toolTipSubTitle:hoverSni.model?.ToolTipSubTitle || "",
                subText:hoverSni.subText}) : null,
            preferences:{shown:preferences.trayVisibleItems,hidden:preferences.trayHiddenItems},
            viewCounts:{active:host.internalSystray?.visibleLayout.count || 0,hidden:host.internalSystray?.hiddenLayout.count || 0,hiddenWidth:host.internalSystray?.hiddenLayout.width || 0,hiddenHeight:host.internalSystray?.hiddenLayout.height || 0,materialized:adapter.nativeLoaders.length},
            configuration:{shown:host.internalSystray?.plasmoid.configuration.shownItems || [],hidden:host.internalSystray?.plasmoid.configuration.hiddenItems || [],extraItems:host.internalSystray?.plasmoid.configuration.extraItems || []}}))
        QtObject {
            id:preferences
            property var trayVisibleItems:[]
            property var trayHiddenItems:[]
            property var trayOrder:["domainos-fixture-sni-0"]
            property bool trayIncludeHiddenInOverflow:false
            property string trayOverflowMode:"continuation"
            property bool barHintsEnabled:false
        }
        Panel.DomainOSTray { id:adapter; x:80;y:20;width:326;height:150;scale:0.5;transformOrigin:Item.TopLeft;nativeTray:host.internalSystray;settings:preferences;screenGeometry:Qt.rect(0,0,1200,800) }
        function nativeOpen(id) {
            const entry=adapter.entries.find(entry=>entry.id===id)
            if(entry && entry.item.applet) host.internalSystray.systemTrayState.setActiveApplet(entry.item.applet)
        }
        function reopenOverflow() {
            if(adapter.snapshot().overflowOpen)adapter.showOverflow()
            Qt.callLater(adapter.showOverflow)
        }
        onScenarioChanged: {
            if(scenario===3){preferences.trayIncludeHiddenInOverflow=true;Qt.callLater(adapter.showOverflow)}
            else if(scenario===4){preferences.trayOverflowMode="pagination";if(adapter.snapshot().overflowOpen)adapter.showOverflow();Qt.callLater(()=>{adapter.showOverflow();adapter.overflowPage=1})}
            else if(scenario===5){preferences.trayOrder=["domainos-fixture-sni-7","domainos-fixture-sni-0"];adapter.showStatus()}
            else if(scenario===6)adapter.openNotifications()
            else if(scenario===7)nativeOpen("org.kde.plasma.networkmanagement")
            else if(scenario===8)nativeOpen("org.kde.plasma.volume")
            else if(scenario===9)nativeOpen("org.kde.plasma.bluetooth")
            else if(scenario===10){host.internalSystray.systemTrayState.expanded=false;preferences.trayOrder=["domainos-fixture-sni-0"]}
            else if(scenario===12){host.internalSystray.plasmoid.configuration.shownItems=preferences.trayVisibleItems.filter(id=>id!=="domainos-fixture-sni-7");host.internalSystray.plasmoid.configuration.hiddenItems=["domainos-fixture-sni-8","domainos-fixture-sni-7"];host.internalSystray.plasmoid.configuration.writeConfig()}
            else if(scenario===13){preferences.trayHiddenItems=["domainos-fixture-sni-8"];preferences.trayVisibleItems=preferences.trayVisibleItems.concat(["domainos-fixture-sni-7"]);preferences.trayIncludeHiddenInOverflow=false;preferences.trayOverflowMode="continuation";adapter.screenGeometry=Qt.rect(0,0,150,800);reopenOverflow()}
            else if(scenario===14){preferences.trayOrder=[1,2,3,4,5,6,7,0].map(index=>"domainos-fixture-sni-"+index);adapter.screenGeometry=Qt.rect(0,0,1200,800);reopenOverflow()}
            else if(scenario===15)adapter.showStatus()
            else if(scenario===16){adapter.showStatus();preferences.barHintsEnabled=true}
            else if(scenario===17)preferences.barHintsEnabled=false
            else if(scenario===18)preferences.barHintsEnabled=true
        }
    }
}
''')
    (output/"config/kdeglobals").write_text((REPO/"colors/DomainOS-SR10.4.colors").read_text())
    (output/"config/plasmarc").write_text("[Theme]\nname=IrixClassicDomainOS\n")
    flags=shlex.split(subprocess.check_output(["pkg-config","--cflags","--libs","Qt6Widgets","Qt6Test","Qt6DBus"],text=True))
    subprocess.run(["c++","-std=c++17","-shared","-fPIC",str(REPO/"plasma/tests/domainos-tray-host.cpp"),"-o",str(output/"tray-host.so"),*flags,"-ldl"],check=True)
    qt_libexec=Path(subprocess.check_output(["qtpaths6","--query","QT_INSTALL_LIBEXECS"],text=True).strip())
    subprocess.run([str(qt_libexec/'moc'),str(REPO/"plasma/tests/domainos-native-tooltip-type.cpp"),"-o",str(output/"domainos-native-tooltip-type.moc")],check=True)
    subprocess.run(["c++","-std=c++17","-shared","-fPIC",str(REPO/"plasma/tests/domainos-native-tooltip-type.cpp"),"-I",str(output),"-o",str(output/"native-tooltip-type.so"),*flags],check=True)
    env.update(XDG_DATA_DIRS="/usr/local/share:/usr/share",XDG_CONFIG_DIRS="/etc/xdg",QT_QPA_PLATFORM="xcb",QT_QPA_PLATFORMTHEME="kde",QT_QUICK_BACKEND="software",QML_DISABLE_DISK_CACHE="1",XDG_CURRENT_DESKTOP="NONE",XDG_SESSION_TYPE="x11",IRIX_DOMAINOS_TRAY_PRIVATE_SESSION="1",DBUS_SYSTEM_BUS_ADDRESS="unix:path="+str(output/"no-system-bus"),PULSE_SERVER="unix:"+str(output/"no-pulse-server"))
    bus=output/"bus.conf";bus.write_text('<busconfig><type>session</type><listen>unix:tmpdir=/tmp</listen><auth>EXTERNAL</auth><policy context="default"><allow send_destination="*"/><allow receive_sender="*"/><allow own="*"/></policy></busconfig>')
    result=subprocess.run(["xvfb-run","--auto-servernum","--server-args=-screen 0 1200x800x24","dbus-run-session","--config-file",str(bus),"--",sys.executable,str(Path(__file__).resolve()),"--saida",str(output),"--worker"],env=env,capture_output=True,text=True,timeout=38)
    (output/"native.log").write_text(result.stdout+result.stderr)
    native=json.loads((output/"native.json").read_text()) if (output/"native.json").is_file() else {}
    calls=json.loads((output/"provider-calls.json").read_text()) if (output/"provider-calls.json").is_file() else {}
    log=(output/"host.log").read_text() if (output/"host.log").is_file() else result.stderr
    diagnostics=[line for line in log.splitlines() if any(marker in line for marker in ("ReferenceError:","TypeError:","SyntaxError:","Cannot assign","Binding loop","is not a type","Type DomainOSTray unavailable"))]
    initial=native.get("initial",{}); overflow=native.get("overflow",{}); status=native.get("status",{})
    checks={"native_host_exited":result.returncode==0 and not native.get("failure"),
        "native_containment_available":initial.get("available") is True,
        "native_plasma_providers_included":all(provider in initial.get("visible",[]) for provider in PROVIDERS),
        "native_status_notifiers_included":all("domainos-fixture-sni-"+str(index) in initial.get("visible",[]) for index in range(8)),
        "explicit_hidden_policy_preserved":initial.get("hidden")==["domainos-fixture-sni-8"],
        "empty_defaults_copy_existing_native_policy":initial.get("preferences")=={"shown":initial.get("configuration",{}).get("shown"),"hidden":["domainos-fixture-sni-8"]},
        "default_overflow_contains_only_visible_excess":initial.get("overflow")==initial.get("visible",[])[6:],
        "real_attention_preserved":initial.get("attention",0)>0,
        "overflow_opened_by_pointer":native.get("mouse_overflow") is True and overflow.get("overflowOpen") is True,
        "status_is_separate_from_overflow":native.get("mouse_status") is True and status.get("statusOpen") is True and status.get("overflowOpen") is False,
        "native_host_is_only_109_pixels_high":initial.get("hostHeight")==109,
        "overflow_uses_separate_native_window_outside_host":overflow.get("popupWindows",{}).get("overflow",{}).get("separate") is True and overflow.get("popupWindows",{}).get("overflow",{}).get("outsideHost") is True,
        "status_uses_separate_native_window_outside_host":status.get("popupWindows",{}).get("status",{}).get("separate") is True and status.get("popupWindows",{}).get("status",{}).get("outsideHost") is True,
        "overflow_anchor_respects_half_scale_and_stays_above_tray":overflow.get("popupWindows",{}).get("overflow",{}).get("aboveTray") is True and overflow.get("popupWindows",{}).get("overflow",{}).get("alignedWithTrayRight") is True,
        "status_anchor_respects_half_scale_and_stays_above_tray":status.get("popupWindows",{}).get("status",{}).get("aboveTray") is True and status.get("popupWindows",{}).get("status",{}).get("alignedWithTrayRight") is True,
        "hidden_option_appends_after_displaced_items":native.get("hidden_in_overflow",{}).get("overflow")==initial.get("overflow",[])+["domainos-fixture-sni-8"],
        "explicit_pagination_available":native.get("pagination",{}).get("paginated") is True and native.get("pagination",{}).get("page")==1,
        "configured_order_uses_native_identity":native.get("reorder",{}).get("visible",[])[:2]==["domainos-fixture-sni-7","domainos-fixture-sni-0"],
        "native_menu_policy_syncs_to_central_preferences":native.get("native_policy_change",{}).get("preferences",{}).get("hidden")==["domainos-fixture-sni-8","domainos-fixture-sni-7"] and "domainos-fixture-sni-7" in native.get("native_policy_change",{}).get("hidden",[]),
        "preferences_policy_syncs_to_native_containment":native.get("width_fallback",{}).get("configuration",{}).get("hidden")==["domainos-fixture-sni-8"] and "domainos-fixture-sni-7" in native.get("width_fallback",{}).get("visible",[]),
        "continuation_falls_back_to_pagination_on_narrow_screen":native.get("width_fallback",{}).get("paginated") is True and native.get("width_fallback",{}).get("pages",0)>1 and native.get("width_fallback",{}).get("overflowOpen") is True,
        "native_notifications_popup_preserved":native.get("native_notifications",{}).get("activeNativeApplet")=="org.kde.plasma.notifications" and native.get("native_notifications",{}).get("activeNativeFullRepresentation") is True,
        "native_network_popup_preserved":native.get("native_network",{}).get("activeNativeApplet")==PROVIDERS[0] and native.get("native_network",{}).get("activeNativeFullRepresentation") is True,
        "native_volume_popup_preserved":native.get("native_volume",{}).get("activeNativeApplet")==PROVIDERS[1] and native.get("native_volume",{}).get("activeNativeFullRepresentation") is True,
        "native_bluetooth_popup_preserved":native.get("native_bluetooth",{}).get("activeNativeApplet")==PROVIDERS[2] and native.get("native_bluetooth",{}).get("activeNativeFullRepresentation") is True,
        "native_sni_activation_routes_to_original_provider":native.get("mouse_sni_activate") is True and any(call["action"]=="Activate" for call in calls.get("domainos-fixture-sni-0",[])),
        "native_sni_context_routes_to_original_provider":native.get("mouse_sni_context") is True and any(call["action"]=="ContextMenu" for call in calls.get("domainos-fixture-sni-0",[])),
        "overflow_native_sni_delegate_remains_interactive":native.get("mouse_overflow_sni_activate") is True and sum(call["action"]=="Activate" for call in calls.get("domainos-fixture-sni-0",[]))==2,
        "hidden_native_sni_delegate_remains_interactive":native.get("mouse_hidden_sni_activate") is True and any(call["action"]=="Activate" for call in calls.get("domainos-fixture-sni-8",[])),
        "opening_drawers_performs_no_other_sni_action":all(not events for identifier,events in calls.items() if identifier not in ("domainos-fixture-sni-0","domainos-fixture-sni-8")),
        "visibility_changes_do_not_disable_native_providers":all(snapshot.get("configuration",{}).get("extraItems")==PROVIDERS for snapshot in (initial,native.get("native_policy_change",{}),native.get("width_fallback",{}))),
        "native_provider_disconnect_removes_test_clients":all(not identifier.startswith("domainos-fixture-sni-") for identifier in native.get("after_fixture_disconnect",{}).get("visible",[])+native.get("after_fixture_disconnect",{}).get("hidden",[])) and native.get("after_fixture_disconnect",{}).get("available") is True,
        "qml_runtime_errors_zero":not diagnostics,
        "host_configuration_hashes_unchanged":hashes()==before}
    policies=lambda name:{entry['id']:entry['active'] for entry in native.get(name,{}).get('nativeTooltipPolicy',[])}
    initial_policy=policies('initial');enabled_policy=policies('hints_enabled');disabled_policy=policies('hints_disabled');restored_policy=policies('hints_restored')
    checks.update(native_bar_hints_default_off=initial.get('hintsEnabled') is False and bool(initial_policy) and not any(initial_policy.values()),
        native_sni_and_plasmoid_hints_restore_when_enabled=native.get('hints_enabled',{}).get('hintsEnabled') is True
            and all(enabled_policy.get(identifier) is True for identifier in PROVIDERS+['domainos-fixture-sni-'+str(index) for index in range(9)]),
        disabling_hints_suspends_only_native_tooltip_activation=native.get('hints_disabled',{}).get('hintsEnabled') is False
            and set(enabled_policy)==set(disabled_policy) and not any(disabled_policy.values()),
        reenabling_hints_restores_each_native_provider_policy=native.get('hints_restored',{}).get('hintsEnabled') is True and enabled_policy==restored_policy,
        native_sni_hint_really_shows_after_enabling=native.get('native_hover_hints_enabled') is True and bool(native.get('hints_enabled',{}).get('nativeTooltipWindows')),
        native_sni_hint_really_hides_after_disabling=not native.get('hints_disabled',{}).get('nativeTooltipWindows'),
        native_sni_hint_really_shows_again_after_restoring=native.get('native_hover_hints_restored') is True and bool(native.get('hints_restored',{}).get('nativeTooltipWindows')),
        hint_preferences_preserve_native_provider_visibility_and_order=all(native.get(name,{}).get('visible')==native.get('hidden_sni_activate',{}).get('visible')
            and native.get(name,{}).get('hidden')==native.get('hidden_sni_activate',{}).get('hidden') for name in ('hints_enabled','hints_disabled','hints_restored')))
    report={"status":"passed" if all(checks.values()) else "failed","checks":checks,"native":native,"provider_calls":calls,"qml_diagnostics":diagnostics,"scope":"Native Plasma applets and test-owned real SNI services. Real network/audio/Bluetooth hardware and notification history contents are unavailable in this isolated host; no actions were sent to the real user session.","protected_configs_before":before,"protected_configs_after":hashes()}
    (output/"RESULTADO.json").write_text(json.dumps(report,indent=2,ensure_ascii=False)+"\n")
    print(json.dumps({"status":report["status"],"checks":len(checks),"result":str(output/"RESULTADO.json")}))
    return 0 if report["status"]=="passed" else 1


if __name__=="__main__":raise SystemExit(main())
