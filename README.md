# Irixium KDE and GTK customization

This repository combines the Irixium GTK theme with custom Aurorae/KDE
improvements:

- keeps title-bar buttons vertically centered when a window is maximized;
- restores the 22x22 transparent Irix-style applications button;
- includes the GTK 1.2, 2.0, 3.0 and 4.0 themes;
- preserves the chosen Irixium title-bar button order (`M` left and `IA` right);
- includes the reviewed classic-controls v3 package, which reuses the close
  artwork for the minimize button and adds scoped menu-button feedback;
- includes the independent IRIX Classic v4 Aurorae decoration for visual
  testing without replacing shared system QML;
- records the KDE Plasma 6 font and antialiasing profile;
- includes a script to reapply the changes after KDE updates.

## Installation

Run:

```sh
./update-irixium.sh
```

The script installs the user theme files and the patched Aurorae QML component. It preserves the original system component as
`MenuButton.qml.irixium-original` when that backup does not already exist.
The QML component is shared by Aurorae, but its custom image is guarded by
the active decoration path and is rendered only for Irixium. Other Aurorae
themes retain the standard application icon.
It also applies the decoration settings recorded in `kwin-decoration.conf`
without replacing the rest of `kwinrc`.
The KDE font settings are recorded separately in `kde-fonts.conf` and are
written using the KDE 6 `kwriteconfig6` format detected on Plasma 6.3.6.

The QML component is cached by KWin. Log out and back in after installation so the change is loaded.

The `controles-v3/` package provides the guarded installer, restoration tool,
integration helper, tests and provenance for the classic-controls update. It
must be applied separately when installing an existing checkout; the main
`update-irixium.sh` script also preserves its `IA` button-order setting.

The `classic-v4/` package installs a separate `Irixium — IRIX Classic (v4)`
decoration under the user's data directory. Run
`classic-v4/instalar-v4.sh --verificar` first, then
`classic-v4/instalar-v4.sh --ativar` to select it for local visual testing.
It does not modify the shared Aurorae QML, the v2 divider overlay, or the
existing v1/v2/v3 installation. Use `classic-v4/restaurar-v4.sh` to restore
the previous decoration selection.

The `classic-rewrite-rc1/` package is the consolidated IRIX Classic rewrite
(1.0.0-rc2). It updates a selected Classic v4/v5 installation in place,
preserving compatible local settings and creating a verified backup. Its
explicit input state machine removes the old hover/timer behavior and fixes
menu-action double-click handling; use
`classic-rewrite-rc1/instalar.sh --verificar` followed by
`classic-rewrite-rc1/instalar.sh` for local testing. The QtTest runner is
optional; absence is reported rather than treated as a passing runtime test.

The `moderno-geometria/` package is a geometry-only update for the modern
Aurorae Irixium theme. It preserves the artwork, controls, menu component,
fonts, GTK theme and IRIX Classic, while changing only the Irixium layout and
the scoped divider component. It recognizes both Debian Aurorae component
locations, including `/usr/share/kwin/aurorae/`, and must be tested with
`moderno/geometria/instalar.sh --verificar` before installation.

To check the registered upstream sources:

```sh
./check-upstreams.sh
```

Upstream changes are review-only. Never merge or copy them directly into
`main`: prepare one branch and one Pull Request/Merge Request per update,
review the diff, test the theme, and merge only after approval.

## Attribution and licensing

The `aurorae/Irixium/` files in this repository are based on Irixium by Phob1an.
The `gtk/` files are based on Irixium by TheJollyDuck/Shauna Recto.
The original GPL text is retained in `LICENSE` and `gtk/LICENSE`.

The GTK source and images retain their upstream licensing and attribution.
The `applications.png` asset is an original 22x22 pixel drawing created for
this customization. See `gtk/README.md` for the GTK asset licensing notice.

The `#titlediv` branch contains the reviewed `divisorias-v2` proposal. It
corrects v1 handling of the maximize/restore compartment and effective border
widths. It is not installed automatically on `master`; review its QML and
visual result before merging or applying it locally.
