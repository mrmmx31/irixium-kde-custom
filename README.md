# Irixium KDE and GTK customization

This repository combines the Irixium GTK theme with custom Aurorae/KDE
improvements:

- keeps title-bar buttons vertically centered when a window is maximized;
- restores the 22x22 transparent Irix-style applications button;
- includes the GTK 1.2, 2.0, 3.0 and 4.0 themes;
- includes a script to reapply the changes after KDE updates.

## Installation

Run:

```sh
./update-irixium.sh
```

The script installs the user theme files and the patched Aurorae QML component. It preserves the original system component as
`MenuButton.qml.irixium-original` when that backup does not already exist.

The QML component is cached by KWin. Log out and back in after installation so the change is loaded.

To check the registered upstream sources:

```sh
./check-upstreams.sh
```

## Attribution and licensing

The root-level Aurorae files in this repository are based on Irixium by Phob1an.
The `gtk/` files are based on Irixium by TheJollyDuck/Shauna Recto.
The original GPL text is retained in `LICENSE` and `gtk/LICENSE`.

The GTK source and images retain their upstream licensing and attribution.
The `applications.png` asset is an original 22x22 pixel drawing created for
this customization. See `gtk/README.md` for the GTK asset licensing notice.
