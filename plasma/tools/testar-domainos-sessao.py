#!/usr/bin/python3
# SPDX-FileCopyrightText: 2026 IRIX Classic contributors
# SPDX-License-Identifier: GPL-3.0-or-later
"""Open a private DomainOS Xephyr from the current user's graphical session.

No installation or change to the user's panel, desktops or preferences. The
preview owns its HOME, compositor, buses and windows. Close its outer window to
stop those processes. Works from a repository or the portable preview bundle.
"""
import argparse
import hashlib
import json
import os
from pathlib import Path
import shutil
import subprocess
import sys
import time
import uuid

sys.dont_write_bytecode = True
ROOT = Path(__file__).resolve().parents[2]
PREVIEW = ROOT / "plasma/tools/prever-domainos-funcional.py"


def preflight(reference):
    errors = []
    if os.geteuid() == 0:
        errors.append("Execute como o próprio usuário, sem sudo.")
    if not os.environ.get("DISPLAY"):
        errors.append("Execute pelo Alt+F2 ou terminal da sessão gráfica KDE.")
    try:
        from PyQt6.QtCore import QT_VERSION_STR
        if tuple(int(part) for part in QT_VERSION_STR.split(".")[:2]) < (6, 8):
            errors.append("O teste requer Qt >= 6.8; encontrado " + QT_VERSION_STR)
    except ImportError:
        errors.append("PyQt6 da distribuição não está disponível em /usr/bin/python3.")
    for command in ("Xephyr", "kwin_x11", "plasmawindowed", "qdbus6",
                    "dbus-run-session", "xterm", "xauth", "xdpyinfo", "xsetroot",
                    "ksystemstats", "c++", "pkg-config", "xdotool", "xprop", "xwininfo"):
        if not shutil.which(command):
            errors.append("Dependência ausente: " + command)
    for resource in (PREVIEW, reference, ROOT / "colors/DomainOS-SR10.4.colors",
                     ROOT / "plasma/applets/org.irixclassic.domainos.panel/metadata.json",
                     ROOT / "plasma/applets/org.irixclassic.grosview/metadata.json",
                     ROOT / "plasma/IrixClassic/metadata.desktop",
                     ROOT / "plasma/IrixClassicDomainOS/metadata.json",
                     ROOT / "icons/themes/IrixClassic-SGI/index.theme",
                     ROOT / "icons/Irixium/index.theme",
                     ROOT / "decorations/classic/package/metadata.json",
                     ROOT / "kvantum/IrixClassic/IrixClassic.kvconfig"):
        if not resource.is_file():
            errors.append("Recurso ausente: " + str(resource))
    manifest = ROOT / "PREVIEW.sha256"
    if manifest.is_file():
        for line in manifest.read_text().splitlines():
            checksum, name = line.split("  ", 1)
            path = ROOT / name
            if not path.is_file() or hashlib.sha256(path.read_bytes()).hexdigest() != checksum:
                errors.append("Integridade inválida: " + name)
    return errors


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--verificar", action="store_true", help="Somente conferir recursos e dependências")
    parser.add_argument("--referencia", type=Path, help="PNG aprovado; apenas lido e copiado")
    parser.add_argument("--saida", type=Path, help="Pasta nova sob /tmp")
    args = parser.parse_args()
    reference = args.referencia or ROOT / "REFERENCIA-APROVADA.png"
    errors = preflight(reference)
    if errors:
        message = "Não foi possível iniciar o teste DomainOS:\n" + "\n".join(errors)
        print(message, file=sys.stderr)
        if not args.verificar and os.environ.get("DISPLAY") and shutil.which("kdialog"):
            subprocess.run(["kdialog", "--title", "Teste DomainOS", "--error", message])
        return 1
    if args.verificar:
        print(json.dumps({"status": "ready", "uid": os.getuid(), "profile_modified": False}, ensure_ascii=False))
        return 0
    output = args.saida or Path("/tmp") / (
        "irix-domainos-teste-uid" + str(os.getuid()) + "-" +
        time.strftime("%Y%m%d-%H%M%S") + "-" + uuid.uuid4().hex[:8])
    command = ["/usr/bin/python3", str(PREVIEW), "--saida", str(output),
               "--referencia", str(reference), "--titulo",
               "DomainOS — teste privado do usuário " + str(os.getuid())]
    if (ROOT / "PREVIEW.sha256").is_file():
        # Preflight verified the package; the child independently verifies it
        # again before linking only immutable applets/styles/theme resources.
        command.append("--recursos-do-pacote")
    result = subprocess.run(command)
    if result.returncode == 0:
        # Publish only verification booleans and result paths. The private
        # profile, bus addresses, settings and screenshots remain in its own
        # directory; another user can inspect this summary without sudo.
        try:
            startup = json.loads((output / "RESULTADO.json").read_text())
            pager = json.loads((output / "PAGER-VERIFICACAO.json").read_text())
            shared = Path("/tmp") / ("irix-domainos-teste-uid" + str(os.getuid()) +
                                      "-" + uuid.uuid4().hex[:12] + "-resumo.json")
            with shared.open("x") as stream:
                json.dump({"uid": os.getuid(), "status_at_startup": startup["status"],
                           "scope": "Private Xephyr only; no installation or real panel replacement",
                           "startup_checks": startup["checks"], "pager_checks": pager["checks"],
                           "private_result": str(output / "RESULTADO.json"),
                           "private_cleanup_result": str(output / "ENCERRADO.json")},
                          stream, indent=2, ensure_ascii=False)
                stream.write("\n")
            shared.chmod(0o644)
            print("Resumo para compartilhar: " + str(shared), flush=True)
        except (OSError, ValueError, KeyError) as error:
            print("Prévia aberta; não foi possível salvar o resumo: " + str(error), file=sys.stderr)
    print("Resultado do teste: " + str(output / "RESULTADO.json"), flush=True)
    print("Troque entre os dois cartões do Pager. O painel deve continuar visível.", flush=True)
    print("Feche a janela externa Xephyr quando terminar; o painel real é preservado.", flush=True)
    return result.returncode


if __name__ == "__main__":
    raise SystemExit(main())
