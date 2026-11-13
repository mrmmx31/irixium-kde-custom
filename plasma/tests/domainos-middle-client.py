#!/usr/bin/env python3
# SPDX-License-Identifier: GPL-3.0-or-later
"""Owned Qt window/marker launched exclusively by the private middle test."""
import argparse
import json
import os
from pathlib import Path
import signal
import sys

if os.environ.get("IRIX_DOMAINOS_UNITY_PRIVATE") != "1":
    raise SystemExit("Private test namespace required")
output = Path(os.environ["IRIX_DOMAINOS_MIDDLE_OUTPUT"])
parser = argparse.ArgumentParser()
parser.add_argument("--family", choices=("group", "single"), required=True)
parser.add_argument("--instance", required=True)
options = parser.parse_args()

# A KDE-launched process may inherit the Plasma host's captured pipe. Own its
# diagnostics explicitly so the host can exit while these windows stay open.
diagnostics = os.open(output / ("client-" + str(os.getpid()) + ".log"),
    os.O_WRONLY | os.O_CREAT | os.O_TRUNC, 0o600)
os.dup2(diagnostics, 1)
os.dup2(diagnostics, 2)
os.close(diagnostics)

from PyQt6.QtCore import QTimer
from PyQt6.QtWidgets import QApplication, QLabel

name = "domainos-middle-" + options.family
app = QApplication([name])
app.setApplicationName(name)
app.setDesktopFileName("org.irixclassic.qa.middle." + options.family)
window = QLabel("Owned native middle-click client; no user application data")
window.setWindowTitle("DomainOS middle " + options.family + " " + options.instance)
window.resize(300, 100)
window.move(40 + (os.getpid() % 3) * 310, 80 + (os.getpid() % 2) * 140)
window.show()
pid = os.getpid()
(output / ("marker-" + str(pid) + ".json")).write_text(json.dumps({
    "pid":pid, "windowId":int(window.winId()), "family":options.family,
    "instance":options.instance, "script":str(Path(__file__).resolve()),
    "display":os.environ.get("DISPLAY"), "bus":os.environ.get("DBUS_SESSION_BUS_ADDRESS"),
    "runtime":os.environ.get("XDG_RUNTIME_DIR"), "data":os.environ.get("XDG_DATA_HOME"),
    "config":os.environ.get("XDG_CONFIG_HOME"), "preload":os.environ.get("LD_PRELOAD")}))
signal.signal(signal.SIGTERM, lambda *arguments: app.quit())
signal_pump = QTimer()
signal_pump.setInterval(100)
signal_pump.timeout.connect(lambda: None)
signal_pump.start()
QTimer.singleShot(45000, app.quit)
result = app.exec()
(output / ("exited-" + str(pid) + ".json")).write_text(json.dumps({"pid":pid,"exit":result}))
raise SystemExit(result)
