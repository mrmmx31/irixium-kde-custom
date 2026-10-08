# Irix Classic DomainOS

An independent Plasma Style for the user's DomainOS panel design. The existing
`IrixClassic` option and its panel are retained unchanged. This option uses the
blue/gray palette and closely spaced woven pixels of the supplied HP workstation
reference: straight stepped light edges, opaque recessed compartments, hatched
command rails, a solid blue clock dial, white hands and a narrow yellow pager
selection border. Button states invert the relief directly, without animation
or an added timer. There are no gradients, blurred shadows or rounded plates.
Each new rim combines four narrow 1px bands: a pale light crest, turquoise
shoulder, shadow counter-relief and pale blue lip. Raised/pressed states reverse
the opposing bands without changing the four-pixel native margins, center tile
period or resource bounds.
The instrument weave alternates dark `#194b63` and pale `#a3d0e6` cells at each
physical pixel, repeating every two pixels. The command rail uses `#3e536e`
and `#c4d5ed`, with **four central grooves**. Each groove has a light row,
checker row and dark row; a dark cap precedes the group and a light cap follows
it. The remaining upper/lower margins retain the checker pattern. Its outer
rim is simple light/dark, without the instruments' turquoise shoulder. These
colors and frequencies were measured in the DomainOS SR10.4 reference; they
replace the earlier sparse diagonal weave and full-height horizontal stripes.
Unlike the instrument weave, the command rail intentionally omits the
nonvisual `hint-tile-center`: KSvg's hint tiles both directions and would repeat
the four grooves vertically. Default center stretching preserves their count.
All visual element IDs/bounds and four-pixel margin hints remain unchanged.
This native fallback stretches checker spacing with its center and may gain
interpolated colors at fractional sizes. The separate production panel draws
the checker in final display pixels; selecting this Style alone cannot provide
that custom rendering or panel geometry.

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
