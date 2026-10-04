# Irixium KDE customization

Custom Aurorae/KDE improvements for the Irixium theme:

- keeps title-bar buttons vertically centered when a window is maximized;
- restores the 22x22 transparent Irix-style applications button;
- includes a script to reapply the changes after KDE updates.

## Installation

Run:

```sh
./update-irixium.sh
```

The script installs the user theme files and the patched Aurorae QML component. It preserves the original system component as
`MenuButton.qml.irixium-original` when that backup does not already exist.

The QML component is cached by KWin. Log out and back in after installation so the change is loaded.

## Attribution and licensing

Irixium was created by Phob1an. This repository contains modifications intended for personal use and for contributing improvements upstream. The original theme license is included in `LICENSE`.

The `applications.png` asset is an original 22x22 pixel drawing created for this customization.
