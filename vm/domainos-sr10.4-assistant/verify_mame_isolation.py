#!/usr/bin/env python3
"""Fail closed on MAMEs that share a disk, network namespace, or control channel."""
from __future__ import annotations

import argparse
import os
from pathlib import Path
import sys


MAME_NAMES = {"mame", "mame64", "MAME"}


class VerificationError(RuntimeError):
    pass


def _start_time(stat_path):
    """Return Linux /proc stat field 22, which distinguishes PID reuse."""
    content = stat_path.read_text(encoding="utf-8")
    close = content.rfind(")")
    if close < 0:
        raise VerificationError(f"stat inválido em {stat_path}")
    fields = content[close + 1:].split()
    # The first field after comm is field 3 (state); starttime is field 22.
    if len(fields) <= 19:
        raise VerificationError(f"stat incompleto em {stat_path}")
    return fields[19]


def _mame_snapshot(proc_root):
    """Inventory MAME PIDs and start times, failing on unreadable transients."""
    root = Path(proc_root)
    try:
        entries = sorted((path for path in root.iterdir() if path.name.isdigit()),
                         key=lambda path: int(path.name))
    except (OSError, ValueError) as exc:
        raise VerificationError(f"não foi possível enumerar {proc_root}: {exc}") from exc

    found = {}
    for entry in entries:
        try:
            comm = (entry / "comm").read_text(encoding="utf-8").strip()
        except FileNotFoundError as exc:
            # A non-candidate process may exit before its name is read. It is
            # absent at this snapshot; candidate MAMEs are checked strictly below.
            continue
        except PermissionError as exc:
            raise VerificationError(
                f"não foi possível identificar PID {entry.name}: {exc}"
            ) from exc
        except OSError as exc:
            raise VerificationError(
                f"não foi possível identificar PID {entry.name}: {exc}"
            ) from exc
        if comm in MAME_NAMES:
            try:
                found[entry.name] = _start_time(entry / "stat")
            except FileNotFoundError as exc:
                # A MAME candidate vanished after its identity was observed.
                raise VerificationError(
                    f"inventário instável: MAME PID {entry.name} desapareceu durante a leitura"
                ) from exc
            except (PermissionError, OSError) as exc:
                raise VerificationError(
                    f"não foi possível identificar MAME PID {entry.name}: {exc}"
                ) from exc
    return found


def _unique_value(values, label):
    seen = {}
    for item in values:
        value = item[label]
        if value in seen:
            raise VerificationError(
                f"MAME PID {item['pid']} compartilha {label} com PID {seen[value]}"
            )
        seen[value] = item["pid"]


def validate_instances(instances):
    """Validate already identified MAME instance identities."""
    for item in instances:
        for field in ("disk_identity", "network_namespace", "control_directory"):
            if not item.get(field):
                raise VerificationError(f"MAME PID {item['pid']} sem identidade {field}")
    for field in ("disk_identity", "network_namespace", "control_directory"):
        _unique_value(instances, field)
    return instances


def _read_instance(pid, proc_root):
    root = Path(proc_root) / str(pid)
    comm = (root / "comm").read_text(encoding="utf-8").strip()
    if comm not in MAME_NAMES:
        return None

    status = (root / "status").read_text(encoding="utf-8")
    uid_line = next((line for line in status.splitlines() if line.startswith("Uid:")), None)
    if uid_line is None or int(uid_line.split()[1]) != os.getuid():
        raise VerificationError(f"MAME PID {pid} não pertence ao usuário atual")

    args = [os.fsdecode(arg) for arg in (root / "cmdline").read_bytes().split(b"\0") if arg]
    disks = [args[index + 1] for index, arg in enumerate(args[:-1]) if arg == "-disk1"]
    if len(disks) != 1:
        raise VerificationError(f"MAME PID {pid} não tem exatamente um -disk1 explícito")
    disk = Path(disks[0]).resolve(strict=True)
    disk_stat = disk.stat()
    disk_identity = (disk_stat.st_dev, disk_stat.st_ino)
    open_disk_fds = []
    try:
        descriptors = (root / "fd").iterdir()
        for descriptor in descriptors:
            try:
                opened = descriptor.stat()
            except FileNotFoundError:
                # A transient descriptor can close while the inventory runs.
                continue
            except PermissionError as exc:
                raise VerificationError(
                    f"não foi possível verificar descritor de PID {pid}: {exc}"
                ) from exc
            if (opened.st_dev, opened.st_ino) == disk_identity:
                open_disk_fds.append(descriptor.name)
    except OSError as exc:
        raise VerificationError(f"não foi possível ler descritores de PID {pid}: {exc}") from exc
    if not open_disk_fds:
        raise VerificationError(
            f"MAME PID {pid}: o inode do caminho -disk1 não foi confirmado entre os arquivos abertos"
        )

    env = (root / "environ").read_bytes().split(b"\0")
    controls = [os.fsdecode(value.split(b"=", 1)[1]) for value in env
                if value.startswith(b"MAME_CONTROL_DIR=")]
    if len(controls) != 1:
        raise VerificationError(f"MAME PID {pid} não expõe MAME_CONTROL_DIR único")
    control = Path(controls[0]).resolve(strict=True)
    if not control.is_dir():
        raise VerificationError(f"MAME PID {pid} aponta a um canal de controle inválido")

    try:
        network_namespace = (root / "ns/net").readlink().as_posix()
    except OSError as exc:
        raise VerificationError(f"MAME PID {pid} sem namespace de rede identificável: {exc}") from exc

    return {
        "pid": int(pid),
        "disk": str(disk),
        "disk_identity": disk_identity,
        "open_disk_fds": tuple(open_disk_fds),
        "network_namespace": network_namespace,
        "control_directory": str(control),
    }


def discover_instances(proc_root="/proc"):
    before = _mame_snapshot(proc_root)
    rows = []
    for pid, start_time in before.items():
        try:
            row = _read_instance(pid, proc_root)
            if _start_time(Path(proc_root) / pid / "stat") != start_time:
                raise VerificationError(f"PID {pid} foi reutilizado durante o inventário")
        except FileNotFoundError as exc:
            raise VerificationError(
                f"inventário instável: MAME PID {pid} desapareceu durante a leitura"
            ) from exc
        except PermissionError as exc:
            raise VerificationError(f"não foi possível verificar PID {pid}: {exc}") from exc
        if row is not None:
            rows.append(row)
    after = _mame_snapshot(proc_root)
    if before != after:
        raise VerificationError("inventário instável: conjunto de MAMEs mudou durante a verificação")
    return rows


def main(argv=None):
    parser = argparse.ArgumentParser()
    parser.add_argument("--expected-disk", required=True)
    args = parser.parse_args(argv)
    expected = Path(args.expected_disk).resolve(strict=True).stat()
    try:
        rows = validate_instances(discover_instances())
    except (OSError, VerificationError) as exc:
        print(f"Falha fechada: {exc}", file=sys.stderr)
        return 4

    matches = [row for row in rows
               if (expected.st_dev, expected.st_ino) == row["disk_identity"]]
    if len(matches) > 1:
        print("Mais de um MAME aponta ao disco canônico.", file=sys.stderr)
        return 4
    for row in rows:
        role = "usa o disco canônico" if row in matches else "isolado em disco próprio"
        print(f"MAME PID {row['pid']}: {role}; rede e canal de controle exclusivos.")
    if not matches:
        print("Nenhum MAME usa o disco canônico; pré-verificação concluída.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
