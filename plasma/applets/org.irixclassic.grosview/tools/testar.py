#!/usr/bin/env python3
# SPDX-FileCopyrightText: 2026 mrmmx31
# SPDX-License-Identifier: GPL-3.0-or-later
"""Read real metrics and capture only this applet on private D-Bus/XDG/Xvfb.

No injected sensor values or user desktop/settings/bus are used. Qt timers in
the test probe settle three native samples and one window capture only.
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

PACKAGE = Path(__file__).resolve().parents[1]
SENSORS = (
    'cpu/all/usage', 'memory/physical/usedPercent', 'memory/swap/usedPercent',
    'disk/all/read', 'disk/all/write', 'network/all/download', 'network/all/upload',
)


def session(output):
    if os.environ.get('IRIX_GROSVIEW_PRIVATE_SESSION') != '1':
        raise RuntimeError('Internal session requires the disposable fixture')
    daemon_log = (output / 'ksystemstats.log').open('w')
    daemon = subprocess.Popen(['ksystemstats', '--remain'], stdout=daemon_log, stderr=subprocess.STDOUT)
    try:
        environment = os.environ.copy()
        environment.update({
            'LD_PRELOAD': str(output / 'capture.so'), 'IRIX_GROSVIEW_TEST': '1',
            'IRIX_GROSVIEW_REPORT': str(output / 'NATIVO.json'),
            'IRIX_GROSVIEW_CAPTURE': str(output / 'WIDGET.png'),
        })
        host = subprocess.run(['plasmawindowed', 'org.irixclassic.grosview'],
            env=environment, stdout=subprocess.PIPE, stderr=subprocess.STDOUT, text=True, timeout=25)
        (output / 'host.log').write_text(host.stdout)
        if daemon.poll() is not None:
            raise RuntimeError('Private ksystemstats daemon exited unexpectedly')
        return host.returncode
    finally:
        daemon.terminate()
        try:
            daemon.wait(timeout=3)
        except subprocess.TimeoutExpired:
            daemon.kill(); daemon.wait(timeout=3)
        daemon_log.close()


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--saida', type=Path, required=True)
    parser.add_argument('--system-bus-readonly', action='store_true',
        help='Permit the private sensor daemon to read native device metadata on the system bus')
    parser.add_argument('--internal-session', action='store_true', help=argparse.SUPPRESS)
    args = parser.parse_args()
    output = args.saida.absolute()
    if args.internal_session:
        return session(output)
    if not output.is_relative_to(Path('/tmp')) or output.exists():
        raise RuntimeError('Use a new output directory under /tmp')
    output.mkdir(mode=0o700)
    paths = {name: output / name for name in ('home', 'config', 'data', 'cache', 'state', 'runtime')}
    for path in paths.values():
        path.mkdir(mode=0o700)
    plasmoids = paths['data'] / 'plasma/plasmoids'
    plasmoids.mkdir(parents=True)
    shutil.copytree(PACKAGE, plasmoids / 'org.irixclassic.grosview')
    flags = shlex.split(subprocess.check_output(['pkg-config', '--cflags', '--libs', 'Qt6Widgets'], text=True))
    subprocess.run(['c++', '-std=c++17', '-shared', '-fPIC', str(PACKAGE / 'tools/capture.cpp'),
        '-o', str(output / 'capture.so'), *flags, '-ldl'], check=True)
    bus = output / 'private-bus.conf'
    bus.write_text('''<!DOCTYPE busconfig PUBLIC "-//freedesktop//DTD D-Bus Bus Configuration 1.0//EN"
"http://www.freedesktop.org/standards/dbus/1.0/busconfig.dtd">
<busconfig><type>session</type><listen>unix:tmpdir=/tmp</listen><auth>EXTERNAL</auth>
<policy context="default"><allow send_destination="*"/><allow receive_sender="*"/><allow own="*"/></policy>
</busconfig>\n''')
    environment = os.environ.copy()
    for name in ('DBUS_SESSION_BUS_ADDRESS', 'DBUS_STARTER_ADDRESS', 'DBUS_STARTER_BUS_TYPE',
                 'WAYLAND_DISPLAY', 'DISPLAY', 'SESSION_MANAGER', 'QML_IMPORT_PATH',
                 'QML2_IMPORT_PATH', 'QT_QUICK_CONTROLS_STYLE', 'QT_STYLE_OVERRIDE'):
        environment.pop(name, None)
    environment.update({
        'HOME': str(paths['home']), 'XDG_DATA_HOME': str(paths['data']),
        'XDG_CONFIG_HOME': str(paths['config']), 'XDG_CACHE_HOME': str(paths['cache']),
        'XDG_STATE_HOME': str(paths['state']), 'XDG_RUNTIME_DIR': str(paths['runtime']),
        'XDG_DATA_DIRS': '/usr/local/share:/usr/share', 'XDG_CONFIG_DIRS': '/etc/xdg',
        'DBUS_SYSTEM_BUS_ADDRESS': 'unix:path=' + str(paths['runtime'] / 'no-system-bus'),
        'QT_QPA_PLATFORM': 'xcb', 'QT_QPA_PLATFORMTHEME': 'generic',
        'QT_QUICK_BACKEND': 'software', 'QSG_RHI_BACKEND': 'software',
        'LIBGL_ALWAYS_SOFTWARE': '1', 'XDG_CURRENT_DESKTOP': 'NONE',
        'IRIX_GROSVIEW_PRIVATE_SESSION': '1',
    })
    if args.system_bus_readonly:
        # ksystemstats only queries Solid/UDisks/UPower sensor metadata; no
        # desktop session bus, user settings or device actions are requested.
        environment['DBUS_SYSTEM_BUS_ADDRESS'] = 'unix:path=/run/dbus/system_bus_socket'
    command = ['xvfb-run', '--auto-servernum', '--server-args=-screen 0 640x480x24',
        'dbus-run-session', '--config-file=' + str(bus), '--', sys.executable,
        str(Path(__file__).resolve()), '--saida', str(output), '--internal-session']
    run = subprocess.run(command, env=environment, stdout=subprocess.PIPE,
        stderr=subprocess.STDOUT, text=True, timeout=40)
    (output / 'session.log').write_text(run.stdout)
    native = json.loads((output / 'NATIVO.json').read_text()) if (output / 'NATIVO.json').is_file() else {}
    failures = []
    if run.returncode or native.get('failure'):
        failures.append(native.get('failure', 'Native fixture exited: ' + str(run.returncode)))
    host_log = (output / 'host.log').read_text() if (output / 'host.log').is_file() else run.stdout
    for line in host_log.splitlines():
        if any(marker in line for marker in ('ReferenceError:', 'TypeError:', 'is not a type', 'Cannot assign', 'module "', 'failed to load')):
            failures.append(line)
    samples = native.get('samples', [])
    if len(samples) != 3:
        failures.append('Missing three real native samples')
    for sample in samples:
        if [item['sensorId'] for item in sample] != list(SENSORS):
            failures.append('Production sensor rows differ')
        for item in sample:
            if item.get('available') is not True or not item.get('sensor_class', '').endswith('Sensor'):
                failures.append('Real sensor not ready: ' + item['sensorId'])
            value = item.get('value')
            if type(value) not in (int, float) or not math.isfinite(value) or value < 0:
                failures.append('Invalid native value: ' + item['sensorId'])
            if item.get('percentage') and (type(value) not in (int, float) or value > 100):
                failures.append('Percentage outside scale: ' + item['sensorId'])
            if item.get('updateRateLimit') != 1000 or not 0 <= item.get('fraction', -1) <= 1:
                failures.append('Polling/gauge contract differs: ' + item['sensorId'])
            if not item.get('percentage') and type(value) in (int, float) and item.get('scaleMaximum', -1) < value:
                failures.append('Rate peak lags current sample: ' + item['sensorId'])
    if not native.get('captured') or native.get('capture_dimensions') != [280, 220]:
        failures.append('Missing widget-only280x220 capture')
    result = {
        'status': 'passed' if not failures else 'failed', 'failures': failures,
        'native_host': native, 'source_hashes': {
            str(path.relative_to(PACKAGE)): hashlib.sha256(path.read_bytes()).hexdigest()
            for path in sorted(PACKAGE.rglob('*')) if path.is_file()
        },
        'real_sensor_data': True, 'sensor_values_injected': False,
        'private_session_bus': True, 'private_ksystemstats_daemon': True,
        'user_profile_or_desktop_changed': False,
        'system_bus_access': 'read_only_sensor_device_metadata' if args.system_bus_readonly else False,
        'capture_scope': 'native applet window only',
        'limitations': ['Movement and placement in a personal desktop session are handled by the native Plasma edit mode and are not exercised here.',
            'Disk/network meters are per-bar observed peak scales, not percentages of device capacity.',
            'A stopped or unavailable sensor displays a dash; this fixture requires all seven standard sensors to be ready on this computer.',
            'With the system bus blocked, aggregate disk sensors can report zero without enumerated devices; use --system-bus-readonly to validate native device discovery.'],
    }
    if (output / 'WIDGET.png').is_file():
        result['capture_sha256'] = hashlib.sha256((output / 'WIDGET.png').read_bytes()).hexdigest()
    (output / 'RESULTADO.json').write_text(json.dumps(result, ensure_ascii=False, indent=2) + '\n')
    print(json.dumps({'status': result['status'], 'report': str(output / 'RESULTADO.json'),
        'capture': str(output / 'WIDGET.png'), 'failures': failures}, indent=2), flush=True)
    return 0 if not failures else 1


if __name__ == '__main__':
    raise SystemExit(main())
