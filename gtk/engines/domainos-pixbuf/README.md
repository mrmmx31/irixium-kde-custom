# DomainOS GTK2 pixbuf engine

This GTK2 engine is derived from GTK+ `2.24.33-7`'s `modules/engines/pixbuf`
implementation. The upstream source files retain their copyright and LGPL
notices; `COPYING.LIB` contains the corresponding GNU Library General Public
License text. This module uses distinct `DomainOSPixmap*` GTypes so GTK2 can
load it beside the distribution's `pixmap` engine.

The DomainOS-only paint adaptation resolves an AUTO scrollbar stepper at its
range boundary to the ordinary parent scrollbar palette. It does not change
GtkRange sensitivity or input behavior. Its colors still come from the
generated KDE-role assets in the theme.

The module is built for the local GTK2 ABI during the user-scoped suite install
and placed under `~/.gtk-2.0/2.10.0/engines/`. The installer records and can
restore that file with the rest of its per-user transaction. No personal path
is embedded in the theme or published archive.
