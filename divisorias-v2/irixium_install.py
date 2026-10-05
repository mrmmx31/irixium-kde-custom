#!/usr/bin/env python3
# SPDX-License-Identifier: GPL-2.0-or-later
"""Install/restore the Irixium overlay. Python 3 standard library only.

Run from a normal desktop user, not with sudo. Only copying the system QML
uses pkexec (or sudo when pkexec is not installed). No KWin restart is forced.
"""
from __future__ import annotations

import argparse
import hashlib
import json
import os
from pathlib import Path
import re
import shutil
import stat
import subprocess
import sys
import tempfile
from datetime import datetime, timezone
from typing import Callable

BUNDLE = Path(__file__).resolve().parent
PACKAGE_VERSION = "2"
BASE_COMMIT = "6f12fdc3325c331fe00e54419e9068aac2f3c459"
COLOR_KEYS = {"ActiveTextColor": "0,0,0,255", "InactiveTextColor": "0,0,0,255"}


class InstallError(RuntimeError):
    """An actionable installation failure; do not hide it."""


def digest(data: bytes) -> str:
    return hashlib.sha256(data).hexdigest()


def normalized_qml(data: bytes) -> bytes:
    """Allow CRLF/trailing whitespace, but no unreviewed code differences."""
    return b"\n".join(line.rstrip() for line in data.splitlines() if line.strip())


def replace_title_colors(data: bytes) -> bytes:
    """Change two [General] values without reserializing the other settings."""
    text = data.decode("utf-8")
    eol = "\r\n" if "\r\n" in text else "\n"
    lines = text.splitlines(keepends=True)
    general = [i for i, line in enumerate(lines) if line.strip() == "[General]"]
    if len(general) != 1:
        raise InstallError("O Irixiumrc deve conter exatamente uma seção [General].")
    start = general[0] + 1
    end = next((i for i in range(start, len(lines))
                if re.match(r"^\s*\[", lines[i])), len(lines))
    missing = set(COLOR_KEYS)
    for i in range(start, end):
        match = re.match(r"^(\s*)(ActiveTextColor|InactiveTextColor)(\s*=).*$", lines[i])
        if not match:
            continue
        key = match.group(2)
        if key not in missing:
            raise InstallError(f"Entrada duplicada em [General]: {key}.")
        missing.remove(key)
        lines[i] = f"{match.group(1)}{key}{match.group(3)}{COLOR_KEYS[key]}{eol}"
    if missing:
        if end and not lines[end - 1].endswith(("\n", "\r")):
            lines[end - 1] += eol
        lines[end:end] = [f"{key}={COLOR_KEYS[key]}{eol}" for key in COLOR_KEYS if key in missing]
    return "".join(lines).encode("utf-8")


def atomic_write(path: Path, data: bytes, mode: int = 0o600) -> None:
    """Atomic user-file update; caller must create/validate the parent."""
    fd, name = tempfile.mkstemp(prefix=".irixium-", dir=path.parent)
    temp = Path(name)
    try:
        with os.fdopen(fd, "wb") as out:
            out.write(data)
            out.flush()
            os.fsync(out.fileno())
        temp.chmod(mode)
        os.replace(temp, path)
    finally:
        temp.unlink(missing_ok=True)


def privileged_copy(source: Path, target: Path) -> None:
    install = shutil.which("install")
    if not install:
        raise InstallError("Comando 'install' não encontrado (pacote coreutils).")
    if shutil.which("pkexec"):
        command = [shutil.which("pkexec"), install, "-m", "0644", "--", str(source), str(target)]
    elif shutil.which("sudo"):
        command = [shutil.which("sudo"), install, "-m", "0644", "--", str(source), str(target)]
    else:
        raise InstallError("É necessário pkexec ou sudo para copiar o QML do sistema.")
    result = subprocess.run(command, check=False)
    if result.returncode:
        raise InstallError(f"Cópia administrativa cancelada ou falhou (código {result.returncode}).")


def discover_qml(explicit: str | None = None) -> Path:
    if explicit:
        target = Path(explicit).expanduser() / "AuroraeButtonGroup.qml"
        if not target.is_file():
            raise InstallError(f"Componente QML não encontrado: {target}")
        if target.is_symlink():
            raise InstallError("O componente QML é um link simbólico; revise o destino antes de instalar.")
        return target.absolute()
    matches: list[Path] = []
    for pattern in ("/usr/lib/*/qt6/qml/org/kde/kwin/decoration/AuroraeButtonGroup.qml",
                    "/usr/lib/qt6/qml/org/kde/kwin/decoration/AuroraeButtonGroup.qml",
                    "/usr/lib64/qt6/qml/org/kde/kwin/decoration/AuroraeButtonGroup.qml"):
        import glob
        matches.extend(Path(p) for p in glob.glob(pattern) if Path(p).is_file())
    unique = sorted({p.resolve() for p in matches})
    if len(unique) != 1:
        raise InstallError("Não foi encontrado um único AuroraeButtonGroup.qml do Qt 6. "
                           "Informe --qml-dir CAMINHO_DO_DIRETORIO; não use uma pasta de Qt 5.")
    return unique[0]


class Installer:
    """All writes are explicit and testable with a sandbox copy function."""
    def __init__(self, qml: Path, rc: Path, state: Path,
                 copy_system: Callable[[Path, Path], None] = privileged_copy,
                 bundle: Path = BUNDLE) -> None:
        self.qml, self.rc, self.state = qml, rc, state
        self.copy_system, self.bundle = copy_system, bundle

    def check(self, keep_color: bool = True) -> tuple[bytes, bytes, bytes, bytes]:
        if not self.qml.is_file() or not self.rc.is_file():
            raise InstallError("O tema Irixium e o módulo Aurorae devem estar instalados primeiro. "
                               "Este pacote é complementar, não contém o tema inteiro.")
        if self.qml.is_symlink() or self.rc.is_symlink():
            raise InstallError("Um dos arquivos de destino é um link simbólico. "
                               "Revise o destino e aplique o diff manualmente.")
        original = (self.bundle / "upstream/AuroraeButtonGroup.qml").read_bytes()
        patched = (self.bundle / "AuroraeButtonGroup.qml").read_bytes()
        current = self.qml.read_bytes()
        previous_v1 = (self.bundle / "compatibilidade/v1/AuroraeButtonGroup.qml").read_bytes()
        known = {normalized_qml(original): "original Plasma 6.3",
                 normalized_qml(previous_v1): "Irixium divisórias v1",
                 normalized_qml(patched): "Irixium divisórias v2"}
        if normalized_qml(current) not in known:
            raise InstallError(
                f"O componente instalado difere da base Plasma 6.3 analisada: {self.qml}\n"
                "Nenhum arquivo foi alterado. Isso pode ser outra versão ou uma customização local.\n"
                "Preserve esse arquivo para adaptar a sobreposição; não force a substituição.")
        print(f"Base reconhecida: {known[normalized_qml(current)]}")
        old_rc = self.rc.read_bytes()
        new_rc = old_rc if keep_color else replace_title_colors(old_rc)
        if not os.access(self.rc.parent, os.W_OK):
            raise InstallError(f"Sem permissão de escrita na pasta do tema: {self.rc.parent}")
        return current, patched, old_rc, new_rc

    def install(self, *, dry_run: bool = False, keep_color: bool = True) -> Path | None:
        old_qml, new_qml, old_rc, new_rc = self.check(keep_color)
        qml_changed, rc_changed = old_qml != new_qml, old_rc != new_rc
        print(f"Componente: {self.qml}")
        print(f"Tema:       {self.rc}")
        print(f"QML: {'será atualizado' if qml_changed else 'já aplicado'}; "
              f"cores do título: {'serão atualizadas' if rc_changed else 'preservadas/sem mudança'}.")
        if dry_run:
            print("Verificação concluída. Nenhuma alteração nem backup foi criado.")
            return None
        if not (qml_changed or rc_changed):
            print("O pacote já está aplicado. Nenhum novo backup foi criado.")
            return None
        self.state.mkdir(parents=True, exist_ok=True, mode=0o700)
        backups = self.state / "backups"
        backups.mkdir(exist_ok=True, mode=0o700)
        stamp = datetime.now(timezone.utc).strftime("%Y%m%dT%H%M%S.%fZ-")
        backup = Path(tempfile.mkdtemp(prefix=stamp, dir=backups))
        atomic_write(backup / "AuroraeButtonGroup.qml", old_qml)
        atomic_write(backup / "Irixiumrc", old_rc)
        previous_backup = None
        latest = self.state / "latest"
        if latest.is_file():
            candidate = Path(latest.read_text().strip())
            try:
                prior = json.loads((candidate / "manifest.json").read_text())
                if (prior.get("format") == 1 and prior.get("status") == "installed"
                        and prior.get("qml_after") == digest(old_qml)
                        and Path(prior["qml_path"]).resolve() == self.qml.resolve()
                        and Path(prior["rc_path"]).resolve() == self.rc.resolve()
                        and candidate.resolve().is_relative_to(backups.resolve())):
                    previous_backup = str(candidate.resolve())
            except (OSError, ValueError, KeyError, TypeError):
                pass  # Never prevent a new backup because an older pointer is stale.
        manifest = {
            "format": 1, "package_version": PACKAGE_VERSION,
            "base_commit": BASE_COMMIT, "status": "prepared",
            "previous_backup": previous_backup,
            "qml_path": str(self.qml), "rc_path": str(self.rc),
            "qml_changed": qml_changed, "rc_changed": rc_changed,
            "qml_before": digest(old_qml), "qml_after": digest(new_qml),
            "rc_before": digest(old_rc), "rc_after": digest(new_rc),
            "rc_mode": stat.S_IMODE(self.rc.stat().st_mode),
        }
        def save_manifest() -> None:
            atomic_write(backup / "manifest.json", (json.dumps(manifest, indent=2) + "\n").encode())
        save_manifest()
        system_done = user_done = False
        try:
            if self.qml.read_bytes() != old_qml or self.rc.read_bytes() != old_rc:
                raise InstallError("Um arquivo mudou durante a preparação. Execute a verificação novamente.")
            if qml_changed:
                # Read back even on failure: a failed copy must not silently leave a partial file.
                try:
                    self.copy_system(self.bundle / "AuroraeButtonGroup.qml", self.qml)
                finally:
                    system_done = not self.qml.is_file() or self.qml.read_bytes() != old_qml
                if self.qml.read_bytes() != new_qml:
                    raise InstallError("A conferência do QML instalado falhou.")
            if rc_changed:
                atomic_write(self.rc, new_rc, manifest["rc_mode"])
                user_done = True
            manifest["status"] = "installed"
            save_manifest()
            atomic_write(self.state / "latest", (str(backup) + "\n").encode())
        except Exception as exc:
            recovery = []
            if user_done:
                try:
                    atomic_write(self.rc, old_rc, manifest["rc_mode"])
                except Exception as restore_exc:
                    recovery.append(f"Irixiumrc: {restore_exc}")
            if system_done:
                try:
                    self.copy_system(backup / "AuroraeButtonGroup.qml", self.qml)
                    if self.qml.read_bytes() != old_qml:
                        raise InstallError("backup do QML não foi restaurado corretamente")
                except Exception as restore_exc:
                    recovery.append(f"QML: {restore_exc}")
            manifest["status"] = "recovery_needed" if recovery else "failed_rolled_back"
            manifest["error"] = str(exc)
            save_manifest()
            extra = "\nRESTAURAÇÃO MANUAL NECESSÁRIA: " + "; ".join(recovery) if recovery else ""
            raise InstallError(f"Instalação interrompida: {exc}\nBackup preservado em: {backup}{extra}") from exc
        print(f"Instalado. Backup: {backup}")
        print("Salve seu trabalho, encerre a sessão do KDE e entre novamente. "
              "O instalador não reiniciou o KWin.")
        return backup

    def restore(self, backup: Path | None = None, *, dry_run: bool = False) -> None:
        if backup is None:
            latest = self.state / "latest"
            if not latest.is_file():
                raise InstallError("Nenhum backup registrado. Informe --backup CAMINHO.")
            backup = Path(latest.read_text().strip())
        backup = backup.expanduser().resolve()
        manifest = json.loads((backup / "manifest.json").read_text())
        if manifest.get("format") != 1 or manifest.get("status") != "installed":
            raise InstallError("O backup não corresponde a uma instalação concluída. "
                               "Consulte manifest.json antes de uma restauração manual.")
        if Path(manifest["qml_path"]).resolve() != self.qml.resolve() or Path(manifest["rc_path"]).resolve() != self.rc.resolve():
            raise InstallError("Os destinos atuais não coincidem com os registrados no backup.")
        old_qml = (backup / "AuroraeButtonGroup.qml").read_bytes()
        old_rc = (backup / "Irixiumrc").read_bytes()
        if digest(old_qml) != manifest["qml_before"] or digest(old_rc) != manifest["rc_before"]:
            raise InstallError("A integridade dos arquivos de backup não confere.")
        for key, path in (("qml", self.qml), ("rc", self.rc)):
            if manifest[f"{key}_changed"] and (not path.is_file() or path.is_symlink()
                    or digest(path.read_bytes()) != manifest[f"{key}_after"]):
                raise InstallError(f"{path} mudou depois da instalação. "
                                   "Restauração automática recusada para não apagar alterações "
                                   "ou reverter uma atualização do KDE. O backup continua disponível.")
        print(f"Backup selecionado: {backup}")
        if dry_run:
            print("Restauração verificada. Nenhum arquivo foi alterado.")
            return
        current_qml = self.qml.read_bytes()
        # Stage current QML for recovery if restoring the user config fails.
        with tempfile.TemporaryDirectory(prefix="irixium-restore-") as td:
            current_copy = Path(td) / "AuroraeButtonGroup.qml"
            current_copy.write_bytes(current_qml)
            system_done = False
            try:
                if manifest["qml_changed"]:
                    try:
                        self.copy_system(backup / "AuroraeButtonGroup.qml", self.qml)
                    finally:
                        system_done = not self.qml.is_file() or self.qml.read_bytes() != current_qml
                    if self.qml.read_bytes() != old_qml:
                        raise InstallError("Falha na conferência do QML restaurado.")
                if manifest["rc_changed"]:
                    atomic_write(self.rc, old_rc, manifest["rc_mode"])
            except Exception as exc:
                if system_done:
                    try:
                        self.copy_system(current_copy, self.qml)
                        if self.qml.read_bytes() != current_qml:
                            raise InstallError("não foi possível recuperar o QML anterior à restauração")
                    except Exception as recovery_exc:
                        raise InstallError(f"Restauração incompleta: {exc}. "
                                           f"Recuperação do QML também falhou: {recovery_exc}. "
                                           f"Arquivos anteriores permanecem em {backup}") from exc
                raise InstallError(f"Restauração interrompida: {exc}") from exc
        manifest["status"] = "restored"
        atomic_write(backup / "manifest.json", (json.dumps(manifest, indent=2) + "\n").encode())
        latest = self.state / "latest"
        if latest.is_file() and latest.read_text().strip() == str(backup):
            previous = manifest.get("previous_backup")
            if previous and Path(previous).is_dir():
                atomic_write(latest, (previous + "\n").encode())
            else:
                latest.unlink()
        print("Estado anterior restaurado. Encerre a sessão do KDE e entre novamente. Backup mantido.")


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("action", choices=("install", "restore"))
    parser.add_argument("--verificar", action="store_true", help="somente conferir; não escrever arquivos")
    colors = parser.add_mutually_exclusive_group()
    colors.add_argument("--manter-cor-titulo", dest="keep_color", action="store_true",
                        help="preservar cores do título (padrão da v2)")
    colors.add_argument("--titulo-preto", dest="keep_color", action="store_false",
                        help="opcional: mudar somente as duas cores do título para preto")
    parser.set_defaults(keep_color=True)
    parser.add_argument("--qml-dir", help="diretório Qt 6 que contém AuroraeButtonGroup.qml")
    parser.add_argument("--backup", type=Path, help="backup específico para restauração")
    args = parser.parse_args(argv)
    try:
        if os.geteuid() == 0:
            raise InstallError("Execute como seu usuário normal, sem sudo. "
                               "A autorização administrativa será solicitada apenas para a cópia do QML.")
        if args.action == "install" and args.backup is not None:
            raise InstallError("--backup é usado apenas com a restauração.")
        if args.action == "restore" and not args.keep_color:
            raise InstallError("--titulo-preto é usado apenas com a instalação.")
        home = Path.home()
        data_home = Path(os.environ.get("XDG_DATA_HOME", str(home / ".local/share"))).expanduser()
        state_home = Path(os.environ.get("XDG_STATE_HOME", str(home / ".local/state"))).expanduser()
        if not data_home.is_absolute() or not state_home.is_absolute():
            raise InstallError("XDG_DATA_HOME e XDG_STATE_HOME devem ser caminhos absolutos.")
        installer = Installer(discover_qml(args.qml_dir), data_home / "aurorae/themes/Irixium/Irixiumrc",
                              state_home / "irixium-divisorias")
        if args.action == "install":
            installer.install(dry_run=args.verificar, keep_color=args.keep_color)
        else:
            installer.restore(args.backup, dry_run=args.verificar)
    except (InstallError, OSError, ValueError, UnicodeError) as exc:
        print(f"ERRO: {exc}", file=sys.stderr)
        return 1
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
