# IrixClassic Plasma Style

Classic has an independent opaque panel and control vocabulary inspired by SGI
Indigo Magic/Motif: square workstation plates, a dark rim, a two-pixel bevel,
inset housings, and cyan selection on the existing gray palette. It keeps the
compact 64px panel height. The original Irixium base is attributed in ORIGEM.json.

Panel housings and recessed fields use regular integer-pixel stipple, hard
ruled edges and a bitmap heading rail. Centers and borders tile at their native
size instead of stretching the dots. The late-1980s workstation references
guide this denser treatment while the Classic gray/teal palette and compact
layout remain the same. Button faces and task caption strips stay solid for
legibility; pressure feedback comes directly from the native input state.

Tasks use separate square icon wells and caption strips inside a recessed
Iconbox, with a compact heading. Active selection colors the caption rather
than the whole task. The org.irixclassic.iconbox widget connects mouse-down
directly to the icon relief and caption displacement; stock KDE tasks do not
forward that state. Applications, shortcuts, tray and clock have independent
Classic widgets. No system QML is overwritten.

The style also supplies listitem/selected+hover resources and both slider
orientations, preventing those controls from falling back to KDE artwork.
The existing Irixium modern style is independent and is not redesigned.

The tray has a common recessed teal field inside a four-pixel instrument rim.
The analog clock uses a cream dial with solid hour marks and hands in a square
socket. Its rim inverts and the dial moves one pixel while pressed; native time,
timezone and calendar behavior are retained.

Pager frames have recessed edges and a narrow selection rim. Their centers are
transparent because KDE places the frame above the native window outlines;
the opaque panel supplies the background. This keeps those outlines visible.

Wi-Fi/Bluetooth switches have a rectangular lever with grip ridges, a square
focus frame, gray off/teal on tracks and inverted pressed relief. The original
rounded Irixium switch was replaced with independently drawn Classic artwork.
New artwork is GPL-3.0-or-later; upstream files retain their original attribution
and license. LICENSE-switch.txt preserves the license of the former resource.

Historical references:
- [Indigo Magic User Interface Guidelines](https://techpubs.jurassic.nl/library/manuals/2000/007-2167-002/sgi_html/ch03.html)
- [OSF/Motif Style Guide, 1993](https://www.bitsavers.org/pdf/openSoftwareFoundation/motif/OSF_Motif_Style_Guide_Revision_1.2_1993.pdf)
