# Irix Classic DomainOS

An independent Plasma Style for the user's DomainOS panel design. The existing
`IrixClassic` option and its panel are retained unchanged. The geometry follows
the supplied HP workstation reference: straight stepped light edges, opaque
recessed compartments, closely spaced woven pixels, hatched command rails and
a circular clock dial. The functional artwork follows the selected KDE color
scheme; selection and hands use its Highlight/HighlightedText roles. Button
states invert the relief directly, without animation
or an added timer. There are no gradients, blurred shadows or rounded plates.
Each rim combines four narrow 1px bands: light crest, lighter shoulder,
shadow counter-relief and inner light lip. Raised/pressed states reverse
the opposing bands without changing the four-pixel native margins, center tile
period or resource bounds.
The instrument weave alternates darker/lighter cells derived from its KDE
surface at each physical pixel, repeating every two pixels. The command rail
uses two derived shades, with **four central grooves**. Each groove has a light row,
checker row and dark row; a dark cap precedes the group and a light cap follows
it. The remaining upper/lower margins retain the checker pattern. Its outer
rim is simple light/dark, without the instruments' additional shoulder. The
frequencies were measured in the DomainOS SR10.4 reference; they
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

The style omits a local `colors` file so every functional SVG uses the KDE
color scheme selected by the user. Native popup headers use HeaderBackground,
footers and housings Background, controls ButtonBackground, fields
ViewBackground, hints TooltipBackground and selections Highlight. Text and
control glyphs use the corresponding KDE foreground roles. This includes the
actual PlasmoidHeading used by Audio Volume and Notifications; its header and
footer no longer carry the reference blue.

KSvg exposes these semantic roles but no calculated Light/Dark roles. Relief
bands therefore mix an opaque thematic surface with a partial white/black
mathematical endpoint. They retain the surface hue and never substitute a
fixed opaque white/black color for a surface or text role. No independent
blue/gray palette survives in a visible functional paint. The source palette
in the builder and provenance describes the historical reference only.
The style version is bumped when the SVG changes so KSvg can invalidate its
cached theme artwork. The separately selectable `DomainOS-SR10.4` color scheme keeps
the historical reference palette available. Selecting this Plasma Style does
not select an application color scheme, alter window decorations, overwrite
GTK/Wine configuration or change workspaces. Installation only makes the style
available under **System Settings → Plasma Style**. The optional per-user style
bridge described below associates the two Classic styles with their panel layouts.

The separate `org.irixclassic.domainos.panel` widget provides the requested
unified panel geometry and connects applications, instruments, tasks, desktops
and tray items to native KDE providers. A Plasma Style supplies artwork; it
cannot create or position widget containers itself. Use the explicit panel
activator and optional style bridge, or add the widget manually. Its [functional guide](../applets/org.irixclassic.domainos.panel/FUNCTIONAL.md)
describes actions, per-instance preferences and capability limits. Replacing an
existing panel uses `tools/activate_domainos.py`, with a saved layout and verified
native reconstruction. No previous panel is kept hidden. After enabling
`tools/domainos_style_bridge.py --instalar --iniciar`, selecting **IrixClassic**
restores the previous panel and **IrixClassicDomainOS** restores DomainOS with its
saved preferences. Other styles do not change layouts through the bridge.
The bridge belongs only to the current user. No system QML is replaced, and the
component installer itself does not activate a layout.

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

Check the generated SVG roles, Classic source inventory, native IDs/bounds,
headers/footers and Controls in four private test schemes with:

```sh
python3 plasma/IrixClassicDomainOS/tools/verify_artwork.py
```

The test uses real installed KSvg, PlasmoidHeading and Plasma Controls with
synthetic data in private offscreen profiles and D-Bus sessions. It does not
read notifications/accounts, change user schemes or exercise desktop actions.
Running this optional QA verifier requires Python PyQt6 with QtQuick, QtWidgets,
QtSvg and QtQml, a Qt offscreen platform plugin, the installed Plasma/Kirigami/
KSvg QML modules and `dbus-run-session`. These are test tools, not extra runtime
dependencies for installing or using the theme. The verifier reports missing
optional tools instead of installing them. When a previous installed Style is
available, its native SVG IDs/bounds are also compared. On a new computer that
comparison is explicitly reported as skipped; palette/render checks still run
and no claim of preserved legacy bounds is made.
