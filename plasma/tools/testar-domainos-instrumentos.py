#!/usr/bin/env python3
# SPDX-FileCopyrightText: 2026 mrmmx31
# SPDX-License-Identifier: GPL-3.0-or-later
"""Verify real time/sensors and separate popups on private Plasma/Xvfb/D-Bus.

Only a disposable test plasmoid and a private ksystemstats daemon run. No user
accounts, calendars, mail applications, desktop settings or device actions are
read or changed. An empty calendar-provider list deliberately remains empty.
"""
import argparse
import hashlib
import json
import math
import os
from pathlib import Path
import shlex
import shutil
import subprocess
import sys
import tempfile

sys.dont_write_bytecode = True
REPO = Path(__file__).resolve().parents[2]
PACKAGE = REPO / "plasma/applets/org.irixclassic.domainos.panel"
IDENTIFIER = "org.irixclassic.domainos.instruments.test"


def digest(path):
    return hashlib.sha256(path.read_bytes()).hexdigest() if path.is_file() else None


def session(output):
    if os.environ.get("IRIX_DOMAINOS_INSTRUMENT_PRIVATE_SESSION") != "1":
        raise RuntimeError("Internal test needs the private fixture")
    log = (output / "ksystemstats.log").open("w")
    daemon = subprocess.Popen(["ksystemstats", "--remain"], stdout=log, stderr=subprocess.STDOUT)
    try:
        environment = dict(os.environ,
            LD_PRELOAD=str(output / "instruments-host.so"),
            IRIX_DOMAINOS_INSTRUMENT_TEST="1",
            IRIX_DOMAINOS_INSTRUMENT_REPORT=str(output / "native.json"),
            IRIX_DOMAINOS_INSTRUMENT_DIR=str(output))
        result = subprocess.run(["plasmawindowed",IDENTIFIER],env=environment,
            stdout=subprocess.PIPE,stderr=subprocess.STDOUT,text=True,timeout=30)
        (output / "host.log").write_text(result.stdout)
        return result.returncode
    finally:
        daemon.terminate()
        try:
            daemon.wait(timeout=3)
        except subprocess.TimeoutExpired:
            daemon.kill(); daemon.wait(timeout=3)
        log.close()


def unit_checks(native, returncode, diagnostics):
    def metrics(stage):
        return native.get(stage,{}).get("metricsJson",{})

    def graph(stage):
        return native.get(stage,{}).get("graphJson",{})

    def empty_histories(state):
        return all(state.get(key) == [] for key in
            ("primaryHistory","secondaryHistory","primarySampleTimes","secondarySampleTimes"))

    def no_shared_scale(state):
        return state.get("scaleMaximum") is None and state.get("scaleText") == "—" \
            and state.get("primaryFraction") is None and state.get("secondaryFraction") is None

    def graph_empty(stage):
        state = graph(stage)
        return state.get("available") is False and state.get("samples") == 0 \
            and state.get("repeaters") == [0,3,0]

    network = metrics("compatible_network")
    mismatch = metrics("incompatible_units")
    stale = metrics("stale_history_defense")
    recovery = metrics("compatible_recovery")
    missing = metrics("missing_secondary")
    single = metrics("single_sensor")
    slow = metrics("slow_telemetry_clock")
    disabled = metrics("disabled")
    return {
        "native_host_exited":returncode == 0 and not native.get("failure"),
        "baseline_uses_native_rx_tx_ids":network.get("available") is True
            and network.get("primarySensorId") == "network/all/download"
            and network.get("secondarySensorId") == "network/all/upload",
        "baseline_pair_has_same_native_unit":network.get("unitsCompatible") is True
            and network.get("primary",{}).get("unit") == network.get("secondary",{}).get("unit"),
        "baseline_native_samples_are_drawn":bool(network.get("primaryHistory")) and bool(network.get("secondaryHistory"))
            and graph("compatible_network").get("repeaters") ==
                [len(network.get("primaryHistory",[])),3,len(network.get("secondaryHistory",[]))],
        "different_units_observed_in_native_sources":mismatch.get("primarySensorId") == "cpu/all/usage"
            and mismatch.get("secondarySensorId") == "network/all/download"
            and all(mismatch.get(key,{}).get("available") is True for key in ("primary","secondary"))
            and mismatch.get("primary",{}).get("unit") != mismatch.get("secondary",{}).get("unit"),
        "individual_measurements_remain_real":all(isinstance(mismatch.get(key,{}).get("value"),(int,float))
            and math.isfinite(mismatch[key]["value"]) and mismatch[key].get("formattedValue") != "—"
            for key in ("primary","secondary")),
        "incompatible_pair_refused":mismatch.get("available") is False and mismatch.get("unitsCompatible") is False,
        "unit_mismatch_explained":bool(mismatch.get("statusText")) and "units differ" in mismatch.get("statusText", ""),
        "incompatible_pair_has_no_shared_scale":no_shared_scale(mismatch),
        "native_unit_change_clears_both_histories":empty_histories(mismatch),
        "incompatible_pair_draws_no_curves":graph_empty("incompatible_units"),
        "stale_history_fixture_contains_previous_curves":stale.get("primaryHistory") == [17,19]
            and stale.get("secondaryHistory") == [23,29],
        "invalid_graph_ignores_stale_history":graph_empty("stale_history_defense"),
        "compatible_rx_tx_recovery_is_live":recovery.get("available") is True
            and recovery.get("unitsCompatible") is True
            and recovery.get("primarySensorId") == "network/all/download"
            and recovery.get("secondarySensorId") == "network/all/upload",
        "recovery_histories_have_native_timestamps":bool(recovery.get("primaryHistory")) and bool(recovery.get("secondaryHistory"))
            and len(recovery.get("primaryHistory",[])) == len(recovery.get("primarySampleTimes",[]))
            and len(recovery.get("secondaryHistory",[])) == len(recovery.get("secondarySampleTimes",[])),
        "recovery_draws_both_series":graph("compatible_recovery").get("available") is True
            and graph("compatible_recovery").get("repeaters") ==
                [len(recovery.get("primaryHistory",[])),3,len(recovery.get("secondaryHistory",[]))],
        "missing_secondary_is_unavailable_not_zero":missing.get("available") is False
            and missing.get("secondary",{}).get("value") is None
            and missing.get("secondary",{}).get("formattedValue") == "—",
        "missing_secondary_clears_history_scale_and_curves":empty_histories(missing)
            and no_shared_scale(missing) and graph_empty("missing_secondary"),
        "empty_secondary_allows_native_single_metric":single.get("available") is True
            and single.get("primarySensorId") == "cpu/all/usage"
            and single.get("secondarySensorId") == "" and single.get("unitsCompatible") is True,
        "single_metric_has_no_secondary_fraction_or_history":single.get("secondaryFraction") is None
            and single.get("secondaryHistory") == [] and single.get("secondarySampleTimes") == [],
        "single_metric_draws_only_primary_series":bool(single.get("primaryHistory"))
            and graph("single_sensor").get("repeaters") == [len(single.get("primaryHistory",[])),3,0],
        "legacy_requested_interval_preserved_only_for_diagnosis":network.get("requestedSamplingLimitMilliseconds") == 250,
        "effective_interval_is_guarded_to_1000_ms":all(metrics(stage).get("samplingLimitMilliseconds") == 1000
            for stage in ("compatible_network","incompatible_units","compatible_recovery","single_sensor")),
        "native_sensor_rate_limits_use_effective_interval":all(network.get(key,{}).get("rateLimitMilliseconds") == 1000
            for key in ("primary","secondary")),
        "native_clock_source_uses_effective_interval":network.get("clockIntervalMilliseconds") == 1000,
        "production_monitor_page_refuses_subminimum_interval":native.get("compatible_network",{}).get("configJson",{}).get("loaded") is True
            and native["compatible_network"]["configJson"].get("coercedInterval") == 1000,
        "chosen_slow_telemetry_uses_60000_ms":slow.get("requestedSamplingLimitMilliseconds") == 60000
            and slow.get("samplingLimitMilliseconds") == 60000
            and slow.get("primary",{}).get("rateLimitMilliseconds") == 60000,
        "native_clock_interval_is_independent_of_monitor":slow.get("clockIntervalMilliseconds") == 1000,
        "native_clock_advances_with_slow_telemetry":native.get("slow_telemetry_clock",{}).get("timeJson",{}).get("available") is True
            and 1500 <= native["slow_telemetry_clock"]["timeJson"].get("milliseconds",0)
                - native.get("single_sensor",{}).get("timeJson",{}).get("milliseconds",0) < 10000
            and native["slow_telemetry_clock"]["timeJson"].get("time")
                != native.get("single_sensor",{}).get("timeJson",{}).get("time"),
        "disabled_clears_histories_scale_and_curves":disabled.get("available") is False
            and empty_histories(disabled) and no_shared_scale(disabled) and graph_empty("disabled"),
        "approved_graph_geometry_unchanged":all(graph(stage).get("width") == 120 and graph(stage).get("height") == 70
            for stage in ("compatible_network","incompatible_units","stale_history_defense","compatible_recovery","missing_secondary","single_sensor","slow_telemetry_clock","disabled")),
        "qml_diagnostics_zero":not diagnostics}


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--saida",required=True,type=Path,help="New output directory under /tmp")
    parser.add_argument("--unidades",action="store_true",help="Test incompatible native units, graph invalidation and recovery only")
    parser.add_argument("--internal-session",action="store_true",help=argparse.SUPPRESS)
    args = parser.parse_args()
    output = args.saida.absolute()
    if args.internal_session:
        return session(output)
    if not output.is_relative_to(Path("/tmp")) or output.exists():
        parser.error("Use a new output directory under /tmp")
    output.mkdir(mode=0o700)
    report_output = output
    # Keep profiles, QML caches and compiler intermediates off /tmp. Only the
    # compact evidence survives; the owned private namespace is removed at exit.
    workspace = tempfile.TemporaryDirectory(prefix=".domainos-instruments-",dir=REPO)
    output = Path(workspace.name)
    production = {name:PACKAGE / "contents/ui" / name for name in
        ("DomainOSInstruments.qml","DomainOSGraph.qml")}
    source_before = {name:digest(path) for name,path in production.items()}
    protected = [Path.home()/".config"/name for name in
        ("kdeglobals","plasmarc","kwinrc","plasma-org.kde.plasma.desktop-appletsrc")]
    config_before = {str(path):digest(path) for path in protected}
    paths = {key:output/name for key,name in (
        ("HOME","home"),("XDG_CONFIG_HOME","config"),("XDG_DATA_HOME","data"),
        ("XDG_CACHE_HOME","cache"),("XDG_STATE_HOME","state"),("XDG_RUNTIME_DIR","runtime"))}
    for path in paths.values(): path.mkdir(mode=0o700)
    plasmoids = paths["XDG_DATA_HOME"] / "plasma/plasmoids"
    plasmoids.mkdir(parents=True)
    for identifier in ("org.irixclassic.domainos.panel","org.irixclassic.grosview"):
        shutil.copytree(REPO/"plasma/applets"/identifier,plasmoids/identifier,
                        ignore=shutil.ignore_patterns("__pycache__","*.pyc"))
    fixture = plasmoids/IDENTIFIER
    (fixture/"contents/ui").mkdir(parents=True)
    (fixture/"metadata.json").write_text(json.dumps({"KPlugin":{
        "Id":IDENTIFIER,"Name":"DomainOS instruments private test","Version":"1.0",
        "License":"GPL-3.0-or-later"},"KPackageStructure":"Plasma/Applet",
        "X-Plasma-API-Minimum-Version":"6.0"}))
    (fixture/"contents/ui/main.qml").write_text('''import QtQuick
import QtQuick.Layouts
import org.kde.plasma.plasmoid
import org.kde.plasma.core as PlasmaCore
import "../../../org.irixclassic.domainos.panel/contents/ui" as Panel
PlasmoidItem {
    preferredRepresentation: fullRepresentation
    Plasmoid.backgroundHints: PlasmaCore.Types.NoBackground
    fullRepresentation: Item {
        id: fixture
        objectName: "domainosInstrumentTestFixture"
        implicitWidth: 500; implicitHeight: 100
        Layout.minimumWidth: 500; Layout.minimumHeight: 100
        property int scenario: 0
        property int mailRequests: 0
        property bool unitsTest: __UNITS_TEST__
        property var liveController: instruments
        property QtObject domainosPalette: testPalette
        Panel.DomainOSPalette { id: testPalette }
        Component.onCompleted: if (unitsTest) instruments.sampleInterval=250
        property string configJson: JSON.stringify({loaded:monitorConfig.status===Loader.Ready,
            coercedInterval:monitorConfig.item ? monitorConfig.item.cfg_instrumentSampleInterval : null})
        Loader {
            id: monitorConfig; active:fixture.unitsTest; visible:false
            width:500; height:300
            source: "../../../org.irixclassic.domainos.panel/contents/ui/ConfigMonitor.qml"
            onLoaded: item.cfg_instrumentSampleInterval=250
        }
        property string metricsJson: JSON.stringify(instruments.sensorSnapshot())
        property string graphJson: JSON.stringify({available:liveGraph.measurementAvailable,
            samples:liveGraph.samples,width:liveGraph.width,height:liveGraph.height,
            repeaters:liveGraph.children.filter(item => item.count !== undefined).map(item => item.count)})
        property string timeJson: JSON.stringify({available:instruments.timeAvailable,
            milliseconds:instruments.currentDateTime.getTime(),hour:instruments.clockHour,
            minute:instruments.clockMinute,locale:instruments.localeName,date:instruments.dateText,
            fullDate:instruments.fullDateText,time:instruments.timeText,
            timezone:instruments.localTimezone,utc:instruments.timeForZone("UTC"),
            localeDates:{us:instruments.compactDate(instruments.currentDateTime,Qt.locale("en_US")),
                gb:instruments.compactDate(instruments.currentDateTime,Qt.locale("en_GB")),
                br:instruments.compactDate(instruments.currentDateTime,Qt.locale("pt_BR"))}})
        property string popupJson: JSON.stringify({clock:instruments.clockPopupVisible,
            calendar:instruments.calendarPopupVisible,monitor:instruments.monitorPopupVisible,
            agendaConfigured:instruments.agendaConfigured,agendaProvidersUnavailable:instruments.agendaProvidersUnavailable,
            mailState:instruments.mailStateAvailable,
            enabled:instruments.monitoringEnabled})
        Panel.DomainOSInstruments {
            id: instruments
            onMailRequested: fixture.mailRequests++
        }
        Rectangle { anchors.fill:parent;color:"#7894a7" }
        Text { anchors.centerIn:parent;text:instruments.timeText+"  "+instruments.dateText+"\\n"+instruments.primaryText+" / "+instruments.secondaryText }
        Panel.DomainOSGraph {
            id: liveGraph; objectName: "domainosInstrumentTestGraph"
            x: 360; y: 10; width: 120; height: 70
            visible: fixture.unitsTest
            instruments: fixture.liveController
        }
        Item { id: anchor;x:150;y:30;width:100;height:40 }
        onScenarioChanged: {
            if (unitsTest) {
                if (scenario===1) {
                    instruments.metric="custom"
                    instruments.customSensorId="cpu/all/usage"
                    instruments.customSecondarySensorId="network/all/download"
                } else if (scenario===2) {
                    // A stale-history defense is exercised separately from
                    // observations of the real native sensor values.
                    instruments.primaryHistory=[17,19]
                    instruments.secondaryHistory=[23,29]
                } else if (scenario===3) {
                    instruments.customSensorId="network/all/download"
                    instruments.customSecondarySensorId="network/all/upload"
                } else if (scenario===4) {
                    instruments.customSecondarySensorId="irix/nonexistent/sensor"
                } else if (scenario===5) {
                    instruments.customSensorId="cpu/all/usage"
                    instruments.customSecondarySensorId=""
                } else if (scenario===6) instruments.sampleInterval=60000
                else if (scenario===7) instruments.monitoringEnabled=false
                return
            }
            if (scenario===1) instruments.showClock(anchor)
            else if (scenario===2) instruments.showCalendar(anchor)
            else if (scenario===3) instruments.showMonitor(anchor)
            else if (scenario===4) { instruments.closePopups();instruments.metric="cpu" }
            else if (scenario===5) { instruments.metric="custom";instruments.customSensorId="irix/nonexistent/sensor" }
            else if (scenario===6) instruments.requestMail()
            else if (scenario===7) instruments.monitoringEnabled=false
            else if (scenario===8) {
                instruments.monitoringEnabled=true
                instruments.calendarPlugins=["irix-nonexistent-provider"]
                instruments.showCalendar(anchor)
            }
        }
    }
}
'''.replace("__UNITS_TEST__","true" if args.unidades else "false"))
    flags = shlex.split(subprocess.check_output(["pkg-config","--cflags","--libs","Qt6Widgets"],text=True))
    compiler_tmp = output/"compiler"
    compiler_tmp.mkdir(mode=0o700)
    subprocess.run(["c++","-std=c++17","-shared","-fPIC",str(REPO/"plasma/tests/domainos-instruments-host.cpp"),
        "-o",str(output/"instruments-host.so"),*flags,"-ldl"],check=True,
        env=dict(os.environ,TMPDIR=str(compiler_tmp)),timeout=30)
    bus = output/"private-bus.conf"
    bus.write_text('<!DOCTYPE busconfig PUBLIC "-//freedesktop//DTD D-Bus Bus Configuration 1.0//EN"\n'
        '"http://www.freedesktop.org/standards/dbus/1.0/busconfig.dtd">\n'
        '<busconfig><type>session</type><listen>unix:tmpdir=/tmp</listen><auth>EXTERNAL</auth>'
        '<policy context="default"><allow send_destination="*"/><allow receive_sender="*"/>'
        '<allow own="*"/></policy></busconfig>\n')
    environment = os.environ.copy()
    for name in ("DBUS_SESSION_BUS_ADDRESS","DBUS_STARTER_ADDRESS","DBUS_STARTER_BUS_TYPE", "WAYLAND_DISPLAY",
        "DISPLAY","SESSION_MANAGER","QML_IMPORT_PATH","QML2_IMPORT_PATH","QT_QUICK_CONTROLS_STYLE",
        "QT_STYLE_OVERRIDE","LD_PRELOAD","XDG_SESSION_ID","KDE_FULL_SESSION","KDE_SESSION_VERSION"):
        environment.pop(name,None)
    environment.update({key:str(path) for key,path in paths.items()})
    environment["TMPDIR"] = str(compiler_tmp)
    environment.update(XDG_DATA_DIRS="/usr/local/share:/usr/share",XDG_CONFIG_DIRS="/etc/xdg",
        DBUS_SYSTEM_BUS_ADDRESS="unix:path="+str(paths["XDG_RUNTIME_DIR"]/"no-system-bus"),
        QT_QPA_PLATFORM="xcb",QT_QPA_PLATFORMTHEME="generic",QT_QUICK_BACKEND="software",
        LIBGL_ALWAYS_SOFTWARE="1",XDG_CURRENT_DESKTOP="NONE",XDG_SESSION_TYPE="x11",
        IRIX_DOMAINOS_INSTRUMENT_PRIVATE_SESSION="1",
        IRIX_DOMAINOS_INSTRUMENT_UNITS_TEST="1" if args.unidades else "0")
    result = subprocess.run(["xvfb-run","--auto-servernum","--server-args=-screen 0 900x650x24",
        "dbus-run-session","--config-file="+str(bus),"--",sys.executable,str(Path(__file__).resolve()),
        "--saida",str(output),"--internal-session"],env=environment,
        stdout=subprocess.PIPE,stderr=subprocess.STDOUT,text=True,timeout=40)
    (output/"session.log").write_text(result.stdout)
    native = json.loads((output/"native.json").read_text()) if (output/"native.json").is_file() else {}
    log = (output/"host.log").read_text() if (output/"host.log").is_file() else result.stdout
    diagnostics = [line for line in log.splitlines() if any(marker in line for marker in (
        "ReferenceError:","TypeError:","SyntaxError:","is not a type","Cannot assign",
        "Error loading QML","failed to load","is unavailable"))]
    network = native.get("network",{}).get("metricsJson",{})
    time = native.get("network",{}).get("timeJson",{})
    cpu = native.get("cpu",{}).get("metricsJson",{})
    unavailable = native.get("unavailable",{}).get("metricsJson",{})
    checks = {
        "native_host_exited":result.returncode == 0 and not native.get("failure"),
        "native_time_engine_ready":time.get("available") is True,
        "native_time_plausible":isinstance(time.get("milliseconds"),(float,int)) and abs(time["milliseconds"]-__import__("time").time()*1000)<35000,
        "date_and_timezone_follow_native_locale":bool(time.get("locale") and time.get("date") and time.get("timezone") and time.get("utc") != "—"),
        "utc_clock_does_not_print_local_zone":bool(time.get("utc","").endswith(" UTC")),
        "english_regional_date_variants_distinct":bool(time.get("localeDates",{}).get("us")) and time.get("localeDates",{}).get("us") != time.get("localeDates",{}).get("gb"),
        "portuguese_date_format_available":bool(time.get("localeDates",{}).get("br")),
        "network_receive_send_real":network.get("available") is True and network.get("primarySensorId")=="network/all/download" and network.get("secondarySensorId")=="network/all/upload",
        "network_zero_is_valid":all(isinstance(network.get(k,{}).get("value"),(int,float)) and math.isfinite(network[k]["value"]) and network[k]["value"]>=0 for k in ("primary","secondary")),
        "network_history_from_native_samples":bool(network.get("primaryHistory")) and bool(network.get("secondaryHistory")),
        "clock_popup_separate":native.get("clock",{}).get("popupJson",{}).get("clock") is True and native.get("clock",{}).get("popupJson",{}).get("calendar") is False,
        "calendar_popup_separate":native.get("calendar",{}).get("popupJson",{}).get("calendar") is True and native.get("calendar",{}).get("popupJson",{}).get("clock") is False,
        "agenda_not_enabled_implicitly":native.get("calendar",{}).get("popupJson",{}).get("agendaConfigured") is False,
        "unknown_calendar_provider_not_presented_as_available":native.get("calendar_unavailable",{}).get("popupJson",{}).get("agendaConfigured") is False and native.get("calendar_unavailable",{}).get("popupJson",{}).get("agendaProvidersUnavailable") is True,
        "existing_grosview_loaded_in_popup":native.get("existing_grosview_loaded") is True,
        "metric_switch_uses_real_cpu":cpu.get("available") is True and cpu.get("primarySensorId")=="cpu/all/usage" and cpu.get("secondarySensorId")=="" and cpu.get("scaleMaximum")==100,
        "cpu_history_not_contaminated_by_network":bool(cpu.get("primaryHistory")) and all(0<=value<=100 for value in cpu["primaryHistory"]),
        "unknown_sensor_never_fake_zero":unavailable.get("available") is False and unavailable.get("primary",{}).get("value") is None and unavailable.get("primary",{}).get("formattedValue")=="—",
        "mail_dispatches_without_count_or_account":native.get("mail",{}).get("mailRequests")==1 and native.get("mail",{}).get("popupJson",{}).get("mailState") is False,
        "disabled_stops_reporting_available":native.get("disabled",{}).get("popupJson",{}).get("enabled") is False and native.get("disabled",{}).get("timeJson",{}).get("available") is False,
        "qml_diagnostics_zero":not diagnostics,
        "instrument_source_unchanged":source_before == {name:digest(path) for name,path in production.items()},
        "desktop_preferences_unchanged":config_before == {str(path):digest(path) for path in protected}}
    if args.unidades:
        checks = unit_checks(native,result.returncode,diagnostics)
        checks.update(instrument_sources_unchanged=source_before == {name:digest(path) for name,path in production.items()},
            desktop_preferences_unchanged=config_before == {str(path):digest(path) for path in protected})
    report = {"format":1,"status":"passed" if all(checks.values()) else "failed","checks":checks,
        "qml_diagnostics":diagnostics,"native":native,"real_profiles_modified":False,
        "source_hashes":source_before,
        "scope":"Private native ksystemstats units and production graph invalidation/recovery; stale-history injection is an explicit graph-defense fixture" if args.unidades
            else "Private time and ksystemstats sources; no account/calendar/mail/device/session actions"}
    (report_output/"RESULTADO.json").write_text(json.dumps(report,indent=2,ensure_ascii=False)+"\n")
    for name in ("native.json","host.log","session.log","ksystemstats.log",
        "clock.png","calendar.png","monitor.png","compatible_network.png","incompatible_units.png","compatible_recovery.png"):
        if (output/name).is_file(): shutil.copy2(output/name,report_output/name)
    workspace.cleanup()
    print(json.dumps({"status":report["status"],"checks":len(checks),"failed":[k for k,v in checks.items() if not v],"report":str(report_output/"RESULTADO.json")},ensure_ascii=False))
    return 0 if report["status"]=="passed" else 1


if __name__ == "__main__":
    raise SystemExit(main())
