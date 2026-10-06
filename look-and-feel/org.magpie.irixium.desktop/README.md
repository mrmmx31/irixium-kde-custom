# Irixium Look-and-Feel and splash

This directory preserves the installed
`org.magpie.irixium.desktop` Look-and-Feel package. Its splash screen is
contained in `contents/splash/` and consists of `Splash.qml` and
`spinner.svg`.

The installed metadata identifies **Mark Whittaker** and links to the
[Phob1an KDE Store profile](https://www.pling.com/u/phob1an/). The package
contains conflicting license declarations: `metadata.desktop` says `GPL 3+`,
while `metadata.json` says `GPL-2.0+`. Both files are preserved; this
repository does not silently choose one.

The package also references the Irixium icon and Plasma Style packages in its
defaults. See `ORIGEM.json` for the complete provenance record.
