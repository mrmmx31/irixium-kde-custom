# IrixClassic Plasma Style

Classic has an independent opaque panel and control vocabulary inspired by SGI
Indigo Magic/Motif: square workstation plates, a dark rim, a two-pixel bevel,
inset housings, and cyan selection on the existing gray palette. It keeps the
compact 64px panel height. The original Irixium base is attributed in ORIGEM.json.

Tasks provide state-specific hover and pressed plates. The separate
org.irixclassic.iconbox widget connects mouse-down directly to that artwork;
stock KDE tasks do not forward that state. Applications, shortcuts, tray and
clock have independent Classic widgets. No system QML is overwritten.

The style also supplies listitem/selected+hover resources and both slider
orientations, preventing those controls from falling back to KDE artwork.
The existing Irixium modern style is independent and is not redesigned.

The Wi-Fi/Bluetooth switch resource comes from the author’s Irixium 6.2
(GPL-2.0-or-later, LICENSE-switch.txt). Newly drawn plates are
GPL-3.0-or-later; upstream files retain their original attribution and license.

Historical references:
- [Indigo Magic User Interface Guidelines](https://techpubs.jurassic.nl/library/manuals/2000/007-2167-002/sgi_html/ch03.html)
- [OSF/Motif Style Guide, 1993](https://www.bitsavers.org/pdf/openSoftwareFoundation/motif/OSF_Motif_Style_Guide_Revision_1.2_1993.pdf)
