#!/usr/bin/env python3
# SPDX-FileCopyrightText: 2026 IRIX Classic contributors
# SPDX-License-Identifier: GPL-3.0-or-later
"""Update an installed panel when only QML/Python/assets changed.

Reuse its native payload only if its manifest matches every current native
build input and runtime ABI. Otherwise use the regular installer/toolchain.
No profile change, panel insertion, process restart or favorites operation.
"""
import argparse
from contextlib import contextmanager
from pathlib import Path
import os
import shutil
import sys
import tempfile

sys.dont_write_bytecode = True

from components import ROOT
from domainos_color_migration import LEGACY_FILENAME
from domainos_native_menu import (BINARY_SOURCE, BUILD_INPUTS, MANIFEST_SOURCE,
    PANEL_SOURCE, regular_bytes, validate_payload)
from install_domainos import TARGETS, check_runtime
from install_suite import roots
from theme_transaction import Failure
from user_bundle import Bundle


@contextmanager
def prepared(installed):
    """Verify before staging; never silently reuse a mismatched native build."""
    files = {name: regular_bytes(ROOT / name) for name in BUILD_INPUTS}
    for name in (BINARY_SOURCE, MANIFEST_SOURCE):
        files[name] = regular_bytes(installed / Path(name).relative_to(PANEL_SOURCE))
    validate_payload(files)
    with tempfile.TemporaryDirectory(prefix='domainos-qml-update-') as work:
        stage = Path(work) / 'panel'
        shutil.copytree(ROOT / PANEL_SOURCE, stage,
            ignore=shutil.ignore_patterns('__pycache__', '*.pyc'))
        for name in (BINARY_SOURCE, MANIFEST_SOURCE):
            (stage / Path(name).relative_to(PANEL_SOURCE)).write_bytes(files[name])
        # Confirm the completed stage as well, before the install transaction.
        validate_payload({name: (stage / Path(name).relative_to(PANEL_SOURCE)).read_bytes()
            if name.startswith(PANEL_SOURCE + '/') else regular_bytes(ROOT / name)
            for name in (*BUILD_INPUTS, BINARY_SOURCE, MANIFEST_SOURCE)})
        yield stage


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--verificar', action='store_true', help='verify without installing')
    args = parser.parse_args()
    if os.geteuid() == 0:
        raise Failure('Execute como usuário normal, sem sudo.')
    data, _, state = roots()
    installed = data / 'plasma/plasmoids/org.irixclassic.domainos.panel'
    check_runtime(data)
    destinations = [data / name for name in TARGETS]
    # Share the regular installer lock and receipt destinations. Only the panel
    # is part of this update; other components are not copied or configured.
    destinations.append(data / 'color-schemes' / LEGACY_FILENAME)
    bundle = Bundle(state / 'irixium-domainos', destinations)
    with prepared(installed) as stage:
        if args.verificar:
            bundle.install([(stage, installed)], dry=True)
        else:
            with bundle.locked():
                bundle.install([(stage, installed)])


if __name__ == '__main__':
    try:
        main()
    except (Failure, OSError, ValueError) as error:
        print('ERRO: ' + str(error), file=sys.stderr)
        raise SystemExit(1)
