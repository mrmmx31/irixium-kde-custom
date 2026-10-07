#!/bin/sh
# SPDX-FileCopyrightText: 2026 mrmmx31
# SPDX-License-Identifier: GPL-2.0-or-later
# Read-only. No dependency installation, no download and no settings changes.
printf '\n=== Base ===\n'
cat /etc/os-release
printf '\n=== Versoes Qt/KDE/Dolphin ===\n'
dpkg-query -W -f='${binary:Package} ${Version}\n' dolphin qt6-base-dev libkf6kio-dev libkf6parts-dev libkf6baloo-dev libkf6baloowidgets-dev extra-cmake-modules 2>/dev/null || true
printf '\n=== Compilacao ===\n'
for t in cmake ninja g++ dpkg-source dbus-run-session python3; do command -v "$t" || true; done
printf '\n=== Sessao ===\n%s\n' "${XDG_SESSION_TYPE:-unknown}"
