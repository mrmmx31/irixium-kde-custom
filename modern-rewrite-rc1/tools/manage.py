#!/usr/bin/env python3
"""Instala a decoração moderna Irixium somente no perfil do usuário."""
from __future__ import annotations
import argparse
from datetime import datetime, timezone
import hashlib
import json
import os
from pathlib import Path
import shutil
import subprocess
import uuid

BUNDLE = Path(__file__).resolve().parents[1]
SOURCE = BUNDLE / "package"
ID = "irixium_modern"
LIBRARY = "org.kde.kwin.aurorae"
GROUP = "org.kde.kdecoration2"
VERSION = "1.0.0"

def config_path() -> Path:
    return Path(os.environ.get("XDG_CONFIG_HOME", Path.home() / ".config")) / "kwinrc"

def data_path() -> Path:
    return Path(os.environ.get("XDG_DATA_HOME", Path.home() / ".local/share")) / "kwin/decorations"

def state_path() -> Path:
    return Path(os.environ.get("XDG_STATE_HOME", Path.home() / ".local/state")) / "irixium-modern"

def hashes(path: Path) -> dict[str, str]:
    return {
        item.relative_to(path).as_posix(): hashlib.sha256(item.read_bytes()).hexdigest()
        for item in sorted(path.rglob("*")) if item.is_file()
    }

def read_manifest() -> dict[str, str]:
    return json.loads((BUNDLE / "MANIFEST.json").read_text())["package"]

def verify() -> Path:
    if hashes(SOURCE) != read_manifest():
        raise RuntimeError("O pacote difere do MANIFEST.json.")
    destination = data_path() / ID
    if destination.exists():
        metadata = json.loads((destination / "metadata.json").read_text())
        if metadata.get("KPlugin", {}).get("Id") != ID:
            raise RuntimeError("O destino não corresponde à decoração moderna.")
    return destination

def write_selection(theme: str) -> None:
    config = config_path()
    config.parent.mkdir(parents=True, exist_ok=True)
    subprocess.run([
        "kwriteconfig6", "--file", str(config), "--group", GROUP,
        "--key", "library", LIBRARY
    ], check=True)
    subprocess.run([
        "kwriteconfig6", "--file", str(config), "--group", GROUP,
        "--key", "theme", theme
    ], check=True)

def install(activate: bool) -> None:
    if os.geteuid() == 0:
        raise RuntimeError("Execute como usuário normal, sem sudo.")
    destination = verify()
    state = state_path()
    state.mkdir(parents=True, exist_ok=True)
    stamp = datetime.now(timezone.utc).strftime("%Y%m%dT%H%M%SZ") + "-" + uuid.uuid4().hex[:8]
    backup = state / "backups" / stamp
    backup.mkdir(parents=True, exist_ok=True, mode=0o700)
    if destination.exists():
        shutil.copytree(destination, backup / "before")
    data_path().mkdir(parents=True, exist_ok=True)
    stage = data_path() / (ID + ".stage-" + uuid.uuid4().hex)
    shutil.copytree(SOURCE, stage)
    try:
        if destination.exists():
            shutil.rmtree(destination)
        os.replace(stage, destination)
        (backup / "receipt.json").write_text(json.dumps({
            "version": VERSION, "destination": str(destination),
            "backup": str(backup), "activate": activate
        }, indent=2) + "\n")
        (state / "latest.json").write_text(json.dumps({"backup": str(backup)}) + "\n")
        if activate:
            write_selection(ID)
    finally:
        if stage.exists():
            shutil.rmtree(stage)
    print(f"Irixium moderno instalado em {destination}")
    if activate:
        print("Irixium moderno selecionado no perfil do usuário.")

def restore() -> None:
    record = json.loads((state_path() / "latest.json").read_text())
    backup = Path(record["backup"])
    destination = data_path() / ID
    if destination.exists():
        shutil.rmtree(destination)
    before = backup / "before"
    if before.exists():
        os.replace(before, destination)
    print(f"Estado anterior restaurado a partir de {backup}")

def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--verificar", action="store_true")
    parser.add_argument("--ativar", action="store_true")
    parser.add_argument("--hook", action="store_true")
    parser.add_argument("--restaurar", action="store_true")
    args = parser.parse_args()
    if args.restaurar:
        record = state_path() / "latest.json"
        if args.verificar:
            print(f"Restauração disponível: {record}")
        else:
            restore()
    else:
        destination = verify()
        if args.verificar:
            print(f"Verificado: {destination}")
        else:
            install(args.ativar)
    return 0

if __name__ == "__main__":
    raise SystemExit(main())
