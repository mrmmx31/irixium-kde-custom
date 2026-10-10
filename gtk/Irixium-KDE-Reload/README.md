# Irixium-KDE

Generated KDE color-role variant of TheJollyDuck’s Irixium. Original Irixium remains unchanged.
CSS retains the original dimensions and bevels. Check/radio artwork is rasterized with native Cairo bilinear sampling from 17px into the unchanged 16px GTK allocation before color separation; other symbolic artwork retains the source PNG pixels.
Upstream code is GPL-3.0; upstream images and their derived masks are CC-BY-NC-SA-4.0 as stated in README.upstream.md.

GTK2 uses the original plain RC without an added engine or image dependency. Native runtime RC reparsing is necessary for open GTK2 applications.
GTK3/4 consume KDE GTK Config’s exported *_breeze names. Automatic reload of already-open GTK4 applications depends on GTK itself; new applications read current colors.
GTK1.2 is intentionally outside this KDE color-role variant.
