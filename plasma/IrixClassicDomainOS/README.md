# Irix Classic DomainOS

An independent Plasma Style for the user's DomainOS panel design. The existing
`IrixClassic` option and its panel are retained unchanged. This option uses the
blue/gray palette and closely spaced woven pixels of the supplied HP workstation
reference: straight stepped light edges, opaque recessed compartments, ruled
command rails, a solid blue clock dial, white hands and a narrow yellow pager
selection border. Button states invert the relief directly, without animation
or an added timer. There are no gradients, blurred shadows or rounded plates.
Each new rim combines four narrow 1px bands: a dark contour, light crest,
counter-relief and blue lip. Raised/pressed states reverse those bands without
changing the four-pixel native margins, center tile period or resource bounds.

The option includes the complete resource vocabulary from Classic, including
switches, horizontal/vertical sliders, popup frames and item selection. The
large housings, Iconbox, instruments, buttons, clock, fields and pager resources
are newly drawn. Small inherited resources retain the original authorship and
GPL attribution; their colors, gradients, alpha blending and corner treatment
are adapted consistently. App icons in the Iconbox continue to come from the
independent IRIX Classic icon theme.

`colors` is the style's local color palette. Selecting this Plasma Style does
not select a KDE application color scheme, alter window decorations, overwrite
GTK/Wine configuration, change workspaces or rearrange a panel. Installation
only makes the style available under **System Settings → Plasma Style**.

The separate `org.irixclassic.domainos.panel` widget provides the requested
unified panel geometry and fixed HP-inspired symbols. A Plasma Style supplies
artwork; it cannot create or position widget containers itself. The widget can
be added explicitly to review this design. Button actions and the final panel
selection/integration tool remain pending the user's individual confirmations.
No system QML is replaced and installing the suite does not change a layout.

Native pager artwork is a border overlay: its centers deliberately draw
nothing so KDE window rectangles remain visible. The underlying panel is fully
opaque. Empty clock glass/shadow placeholders and metadata hints likewise are
not surface transparency.

Rebuild the checked-in SVGs with:

```sh
python3 plasma/IrixClassicDomainOS/tools/build_artwork.py
```

The builder reads Classic as a source and writes only this option. It uses
Python's standard library, retains a source hash inventory in
`CLASSIC-BASELINE.json`, and never reads a user profile. `ORIGEM.json` records
the user-provided reference hashes and inherited resource licenses. The
screenshots are visual references, and are not distributed as theme assets.
