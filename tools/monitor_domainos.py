#!/usr/bin/env python3
# SPDX-License-Identifier: GPL-3.0-or-later
"""Observe this user's Plasma responsiveness. Never restart or reconfigure it."""
import argparse
from collections import deque
import datetime
import json
import math
import os
from pathlib import Path
import stat
import subprocess
import tempfile
import time

MARKER = "domainos-monitor-responsive"


def bounded_command(arguments, timeout):
    try:
        result = subprocess.run(arguments, capture_output=True, text=True, errors="replace", timeout=timeout)
        return {"ok": result.returncode == 0, "timeout": False, "output": result.stdout}
    except subprocess.TimeoutExpired:
        return {"ok": False, "timeout": True, "output": ""}
    except OSError:
        return {"ok": False, "timeout": False, "output": "", "unavailable": True}


def process_sample(pid, proc_root=Path("/proc")):
    """CPU counters are evidence, never sufficient to declare a freeze."""
    try:
        folder = proc_root / str(pid)
        if folder.stat().st_uid != os.getuid():
            return None
        fields = (folder / "stat").read_text().rsplit(")", 1)[1].split()
        ticks = os.sysconf("SC_CLK_TCK")
        return {"pid": pid, "start": int(fields[19]),
                "cpu": (int(fields[11]) + int(fields[12])) / ticks,
                "monotonic": time.monotonic(),
                "boottime": time.clock_gettime(time.CLOCK_BOOTTIME)}
    except (OSError, ValueError, IndexError):
        return None


class Responsiveness:
    def __init__(self, threshold=3, max_gap=45):
        self.threshold = threshold
        self.max_gap = max_gap
        self.failures = 0
        self.identity = None
        self.previous = None

    def observe(self, service, sample, probe):
        identity = (sample["pid"], sample["start"]) if sample else None
        if identity != self.identity:
            self.failures = 0
            self.previous = None
            self.identity = identity
        cpu_percent = None
        observation_reset = False
        if sample and self.previous:
            elapsed = sample["monotonic"] - self.previous["monotonic"]
            boot_elapsed = sample.get("boottime", sample["monotonic"]) - self.previous.get("boottime", self.previous["monotonic"])
            if elapsed > self.max_gap or boot_elapsed - elapsed > 1:
                self.failures = 0
                observation_reset = True
            elif elapsed > 0:
                cpu_percent = max(0, 100 * (sample["cpu"] - self.previous["cpu"]) / elapsed)
        self.previous = sample
        if not service["ok"]:
            self.failures = 0
            status = "monitor_indisponivel"
        elif not sample:
            self.failures = 0
            status = "plasma_ausente_ou_nao_observavel"
        elif probe.get("unavailable") or (not probe.get("ok") and not probe.get("timeout")):
            self.failures = 0
            status = "sonda_indisponivel"
        elif probe["ok"] and probe["output"].strip() == MARKER:
            self.failures = 0
            status = "respondendo"
        else:
            self.failures += 1
            status = "sem_resposta" if self.failures >= self.threshold else "resposta_inconclusiva"
        return {"status": status, "consecutive_failures": self.failures,
                "pid": sample["pid"] if sample else None,
                "cpu_percent_one_core": cpu_percent, "probe_timeout": probe.get("timeout", False),
                "observation_reset_after_gap": observation_reset}


def write_report(path, report):
    """Keep one bounded report, atomically; do not follow another user's link."""
    parent = path.parent
    info = parent.stat()
    if info.st_uid not in (os.getuid(), 0) or not stat.S_ISDIR(info.st_mode):
        raise ValueError("Diretório de saída não pertence ao usuário")
    if path.is_symlink():
        raise ValueError("Saída não pode ser link simbólico")
    if path.exists() and (path.stat().st_uid != os.getuid() or not path.is_file()):
        raise ValueError("Saída não pertence ao usuário")
    descriptor, temporary = tempfile.mkstemp(prefix=".domainos-monitor-", dir=parent)
    try:
        with os.fdopen(descriptor, "w") as stream:
            json.dump(report, stream, ensure_ascii=False, indent=2)
            stream.write("\n")
        os.replace(temporary, path)
    finally:
        if os.path.exists(temporary):
            os.unlink(temporary)


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--saida", type=Path, required=True)
    parser.add_argument("--follow", action="store_true", help="Observar até Ctrl+C, sem recuperação automática")
    parser.add_argument("--samples", type=int, default=1)
    parser.add_argument("--interval", type=float, default=15)
    parser.add_argument("--timeout", type=float, default=2)
    args = parser.parse_args()
    if args.samples < 1 or not math.isfinite(args.interval) or args.interval < 5:
        parser.error("Use samples >= 1 e interval >= 5 segundos")
    if not math.isfinite(args.timeout) or not 0.1 <= args.timeout <= 5:
        parser.error("Use timeout entre 0.1 e 5 segundos")
    output = args.saida.absolute()
    if not output.parent.exists():
        parser.error("Crie primeiro o diretório de saída")
    observer = Responsiveness(max_gap=max(3 * args.interval, args.interval + 2 * args.timeout))
    history = deque(maxlen=120)
    previous_status = None
    count = 0
    try:
        while args.follow or count < args.samples:
            started = time.monotonic()
            service = bounded_command(["systemctl", "--user", "show", "plasma-plasmashell.service",
                                       "--property=MainPID", "--value"], args.timeout)
            try:
                pid = int(service["output"].strip()) if service["ok"] else 0
            except ValueError:
                pid = 0
            sample = process_sample(pid) if pid > 0 else None
            probe = bounded_command(["qdbus6", "org.kde.plasmashell", "/PlasmaShell",
                "org.kde.PlasmaShell.evaluateScript", 'print("' + MARKER + '");'], args.timeout) if sample else {}
            event = observer.observe(service, sample, probe)
            event["time"] = datetime.datetime.now(datetime.timezone.utc).isoformat()
            history.append(event)
            write_report(output, {"format": 1, "uid": os.getuid(), "mode": "observe_only",
                "scope": "Plasma deste usuário; não identifica qual componente causou demora",
                "automatic_restart": False, "latest": event, "history": list(history)})
            if event["status"] != previous_status:
                print(event["status"] + " · " + str(output), flush=True)
                previous_status = event["status"]
            count += 1
            if args.follow or count < args.samples:
                time.sleep(max(0, args.interval - (time.monotonic() - started)))
    except KeyboardInterrupt:
        print("Monitor encerrado; relatório preservado.", flush=True)
    except (OSError, ValueError) as error:
        parser.exit(1, str(error) + "\n")


if __name__ == "__main__":
    main()
