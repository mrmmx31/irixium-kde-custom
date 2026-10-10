#!/usr/bin/python3
# SPDX-License-Identifier: GPL-3.0-or-later
"""Reject accidental demo launches in the personal profile; no environment edits."""
import os
from pathlib import Path
import pwd


def require_private_session():
    if os.environ.get("IRIX_DOMAINOS_PRIVATE_XEPHYR") != "1":
        raise RuntimeError("Launch only from the coordinated private Xephyr session (IRIX_DOMAINOS_PRIVATE_XEPHYR=1)")
    if not os.environ.get("DISPLAY") or not os.environ.get("DBUS_SESSION_BUS_ADDRESS"):
        raise RuntimeError("The private DISPLAY and session bus must already exist")
    personal = Path(pwd.getpwuid(os.getuid()).pw_dir).resolve()
    base = Path(os.environ.get("IRIX_DOMAINOS_SESSION_ROOT", "")).resolve()
    sandbox_home = Path("/home/domainos-test")
    namespaced = (os.environ.get("IRIX_DOMAINOS_PRIVATE_NAMESPACE") == "bwrap"
                  and base == sandbox_home and personal == sandbox_home
                  and Path(os.environ.get("HOME", "")).resolve() == sandbox_home)
    ordinary = base != personal and base != Path("/tmp") and base.is_relative_to(Path("/tmp"))
    if not (namespaced or ordinary):
        raise RuntimeError("Explicit disposable session root or coordinated bwrap fake-home contract is required")
    for name in ("HOME", "XDG_CONFIG_HOME", "XDG_DATA_HOME", "XDG_CACHE_HOME", "XDG_STATE_HOME"):
        value = os.environ.get(name)
        if not value:
            raise RuntimeError("Missing private " + name)
        path = Path(value).resolve()
        if not path.is_relative_to(base) or (path == personal and not namespaced):
            raise RuntimeError(name + " must point inside the disposable session root")
    runtime = Path(os.environ.get("XDG_RUNTIME_DIR", "")).resolve()
    runtime_allowed = ((runtime.is_relative_to(Path("/tmp")) and runtime != Path("/tmp"))
                       or (namespaced and runtime == Path("/run/user") / str(os.getuid())))
    if not runtime_allowed:
        raise RuntimeError("Private runtime must be under /tmp, or /run/user/UID inside coordinated bwrap")
    if not runtime.is_dir() or runtime.stat().st_uid != os.getuid() or runtime.stat().st_mode & 0o077:
        raise RuntimeError("Private runtime must be an owned0700 directory")
    if os.environ.get("GDK_BACKEND") != "x11":
        raise RuntimeError("GDK_BACKEND=x11 is required for the Xephyr session")
