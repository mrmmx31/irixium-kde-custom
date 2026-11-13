#!/usr/bin/env python3
# SPDX-FileCopyrightText: 2026 IRIX Classic contributors
# SPDX-License-Identifier: GPL-3.0-or-later
"""Install the optional Classic maintenance hook without a checkout dependency."""
from __future__ import annotations

import argparse
import hashlib
import json
import os
from pathlib import Path
import shutil
import subprocess
import sys
import tempfile

sys.dont_write_bytecode = True
from theme_transaction import Failure, no_links, snapshot
from user_bundle import Bundle, fingerprint

ROOT = Path(__file__).resolve().parents[1]
UNIT = "irix-classic-user.service"
RUNTIME = Path("irixium/hooks/classic")
SHELL_FILES = ("instalar.sh", "hooks/irix-classic-user.sh")


def quoted(value, *, command=True):
    """Quote one systemd token; ExecStart additionally expands dollar signs."""
    text = str(value)
    if any(ord(char) < 32 or ord(char) == 127 for char in text):
        raise Failure("Caractere de controle recusado no caminho do hook.")
    text = text.replace("\\", "\\\\").replace('"', '\\"').replace("%", "%%")
    if command:
        text = text.replace("$", "$$")
    return '"' + text + '"'


def locations(data, config, state):
    paths = tuple(Path(value).expanduser() for value in (data, config, state))
    for path in paths:
        if not path.is_absolute():
            raise Failure("As raízes XDG do hook devem ser absolutas.")
        no_links(path)
        if any(path == base or base in path.parents for base in map(Path, ("/usr", "/etc", "/opt", "/var"))):
            raise Failure("O hook só pode ser instalado no perfil do usuário.")
        existing = next(part for part in (path, *path.parents) if part.exists())
        if existing.stat().st_uid != os.getuid() and existing != Path("/tmp"):
            raise Failure("Destino do hook não pertence ao usuário.")
    data, config, state = paths
    return data / RUNTIME, config / "systemd/user" / UNIT, state / "irixium-classic-hook"


def source_files(source_root):
    classic = Path(source_root) / "decorations/classic"
    no_links(classic)
    manifest = classic / "MANIFEST.json"
    package = classic / "package"
    no_links(manifest)
    expected = json.loads(manifest.read_text())["package"]
    if not isinstance(expected, dict) or fingerprint(package) != expected:
        raise Failure("O pacote Classic difere do manifesto; hook não instalado.")
    files = [(path, "package/" + path.relative_to(package).as_posix())
             for path in sorted(package.rglob("*")) if path.is_file()]
    files += [(manifest, "MANIFEST.json"), (classic / "tools/manage.py", "tools/manage.py")]
    files += [(classic / name, name) for name in SHELL_FILES]
    for path, _ in files:
        no_links(path)
        if not path.is_file():
            raise Failure("Dependência do hook ausente: " + str(path))
    return files


def execution_line(runtime):
    return "ExecStart=/usr/bin/python3 " + quoted(runtime / "tools/manage.py") + " --hook --destino irixium_irix_classic_v4"


def environment_lines(data, config, state):
    # Environment= does not perform $ expansion; only ExecStart needs $$.
    return ["Environment=PYTHONDONTWRITEBYTECODE=1"] + [
        "Environment=" + quoted(key + "=" + str(value), command=False)
        for key, value in (("XDG_DATA_HOME", data), ("XDG_CONFIG_HOME", config), ("XDG_STATE_HOME", state))]


def service_content(runtime, data, config, state):
    return ("[Unit]\nDescription=Garantir decoração IRIX Classic no perfil do usuário\n"
            "After=graphical-session.target\nPartOf=graphical-session.target\n\n"
            "[Service]\nType=oneshot\n" + execution_line(runtime) + "\n"
            + "\n".join(environment_lines(data, config, state))
            + "\n\n[Install]\nWantedBy=graphical-session.target\n").encode()


def exact_command(contents):
    # Native units may repeat Environment=. ConfigParser's strict mode rejects
    # those valid units; inspect only the unique single-line ExecStart instead.
    in_service = False
    service_sections = 0
    commands = []
    for line in contents.splitlines():
        if line.startswith("["):
            in_service = line == "[Service]"
            service_sections += int(in_service)
        elif in_service and line.lstrip().startswith("ExecStart="):
            if not line.startswith("ExecStart=") or line.endswith("\\"):
                return None
            commands.append(line[len("ExecStart="):])
    return commands[0] if service_sections == 1 and len(commands) == 1 and commands[0] else None


def legacy_commands(source_root):
    commands = set()
    for relative in ("classic-rewrite-rc1/hooks/irix-classic-user.sh",
                     "decorations/classic/hooks/irix-classic-user.sh"):
        path = Path(source_root) / relative
        commands.update(("ExecStart=" + str(path), "ExecStart=" + quoted(path)))
    return commands


def migrated_content(contents, runtime, data, config, state):
    lines = contents.splitlines(keepends=True)
    result = []
    in_service = False
    inserted = False
    for line in lines:
        if line.startswith("["):
            if in_service and not inserted:
                result.extend(value + "\n" for value in environment_lines(data, config, state))
                inserted = True
            in_service = line.rstrip("\r\n") == "[Service]"
        if in_service and line.startswith("ExecStart="):
            result.append(execution_line(runtime) + "\n")
        else:
            result.append(line)
    if in_service and not inserted:
        if result and not result[-1].endswith("\n"):
            result[-1] += "\n"
        result.extend(value + "\n" for value in environment_lines(data, config, state))
    return "".join(result).encode()


def validate_existing(bundle, runtime, expected_runtime):
    latest = bundle.latest()
    if latest and latest[1]["status"] == "prepared":
        raise Failure("Migração do hook interrompida; restaure antes de repetir.")
    if not runtime.exists():
        return
    if not latest:
        raise Failure("Runtime do hook existente sem recibo; pasta preservada.")
    _, record = latest
    entries = [entry for entry in record["entries"] if Path(entry["destination"]) == runtime]
    expected = entries[0]["before" if record["status"] == "restored" else "after"] if entries else expected_runtime
    if fingerprint(runtime) != expected:
        raise Failure("Runtime do hook alterado; nenhuma substituição feita.")


def install_runtime(source_root, data, config, state, content, before, dry=False):
    runtime, service, bookkeeping = locations(data, config, state)
    files = source_files(source_root)
    expected = {relative: hashlib.sha256(path.read_bytes()).hexdigest() for path, relative in files}
    bundle = Bundle(bookkeeping, (runtime, service))
    validate_existing(bundle, runtime, expected)
    if snapshot(service) != before:
        raise Failure("Serviço do hook mudou durante a preparação; preservado.")
    if dry:
        print("Hook Classic autocontido verificado:", runtime)
        print("Serviço do usuário:", service)
        return False
    with bundle.locked():
        validate_existing(bundle, runtime, expected)
        if snapshot(service) != before:
            raise Failure("Serviço do hook mudou antes da instalação; preservado.")
        with tempfile.TemporaryDirectory(prefix=".hook-stage-", dir=bookkeeping) as directory:
            stage = Path(directory)
            payload = stage / "runtime"
            for source, relative in files:
                target = payload / relative
                target.parent.mkdir(parents=True, exist_ok=True)
                shutil.copy2(source, target)
            if fingerprint(payload) != expected:
                raise Failure("Fonte do hook mudou durante o staging; nenhuma instalação feita.")
            unit = stage / UNIT
            unit.write_bytes(content)
            unit.chmod(before.get("mode", 0o644))
            previous = bundle.latest()
            bundle.install(((payload, runtime), (unit, service)))
            current = bundle.latest()
            changed = current != previous
            if changed:
                # A service edit concurrent with staging must be rolled back to
                # the exact newer bytes captured by Bundle, never accepted.
                entry = next((item for item in current[1]["entries"] if Path(item["destination"]) == service), None)
                original = {"@file": before["sha256"]} if before["exists"] else None
                if entry and entry["before"] != original:
                    bundle.restore()
                    raise Failure("Serviço mudou durante o staging; instalação revertida.")
    return changed


def reload_user_manager():
    if os.environ.get("DBUS_SESSION_BUS_ADDRESS") and shutil.which("systemctl"):
        result = subprocess.run(["systemctl", "--user", "daemon-reload"], capture_output=True, text=True)
        if result.returncode:
            print("Aviso: execute systemctl --user daemon-reload antes do próximo login.")


def migrate(source_root, data, config, state, dry=False):
    runtime, service, _ = locations(data, config, state)
    before = snapshot(service)
    if not before["exists"]:
        return False
    contents = service.read_text()
    command = exact_command(contents)
    if command is None or "ExecStart=" + command not in legacy_commands(source_root):
        return False
    content = migrated_content(contents, runtime, data, config, state)
    changed = install_runtime(source_root, data, config, state, content, before, dry)
    if changed:
        reload_user_manager()
    return changed


def install_opt_in(source_root, data, config, state, dry=False):
    runtime, service, _ = locations(data, config, state)
    before = snapshot(service)
    if before["exists"]:
        contents = service.read_text()
        command = exact_command(contents)
        accepted = legacy_commands(source_root) | {execution_line(runtime)}
        if command is None or "ExecStart=" + command not in accepted:
            raise Failure("Serviço personalizado existente; hook não substituído.")
        content = (contents.encode() if "ExecStart=" + command == execution_line(runtime)
                   else migrated_content(contents, runtime, data, config, state))
    else:
        content = service_content(runtime, data, config, state)
    install_runtime(source_root, data, config, state, content, before, dry)
    if not dry:
        # Only the explicitly invoked optional installer enables/starts it.
        for arguments in (("daemon-reload",), ("enable", UNIT), ("start", UNIT)):
            subprocess.run(["systemctl", "--user", *arguments], check=True)
    return runtime


def restore(data, config, state, dry=False):
    runtime, service, bookkeeping = locations(data, config, state)
    bundle = Bundle(bookkeeping, (runtime, service))
    if dry:
        bundle.restore(dry=True)
    else:
        with bundle.locked():
            bundle.restore()
        reload_user_manager()


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--verificar", action="store_true")
    parser.add_argument("--restaurar", action="store_true")
    arguments = parser.parse_args()
    if os.geteuid() == 0:
        raise Failure("Execute como usuário normal, sem sudo.")
    # Lazy: install_suite is also imported from standalone DomainOS packages
    # which do not ship the optional Classic decoration resources.
    from install_suite import roots
    data, config, state = roots()
    if arguments.restaurar:
        restore(data, config, state, arguments.verificar)
    else:
        install_opt_in(ROOT, data, config, state, arguments.verificar)


if __name__ == "__main__":
    try:
        main()
    except (OSError, ValueError, KeyError, RuntimeError, subprocess.SubprocessError) as error:
        sys.exit("ERRO: " + str(error))
