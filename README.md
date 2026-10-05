# Irixium KDE and GTK customization

This repository combines the Irixium GTK theme with custom Aurorae/KDE
improvements:

- keeps title-bar buttons vertically centered when a window is maximized;
- restores the 22x22 transparent Irix-style applications button;
- includes the GTK 1.2, 2.0, 3.0 and 4.0 themes;
- preserves the chosen Irixium title-bar button order (`M` left and `HXA` right);
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
