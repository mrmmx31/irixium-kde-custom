#!/usr/bin/env python3
# SPDX-FileCopyrightText: 2026 mrmmx31
# SPDX-License-Identifier: GPL-3.0-or-later
"""Build Classic's KDE color-role variant without modifying standalone artwork.

The generated theme consumes GTK Config's symbolic color names. Theme-provider
fallbacks make it usable outside KDE; KDE's higher-priority colors.css replaces
those fallbacks. Generation does not select a theme or write a user's settings.
Metrics and integer artwork come from IrixClassic. Only color expressions and
the image mechanism change; fixed corners/repeated edge strips avoid filtering.
"""
from __future__ import annotations

import argparse
import hashlib
import json
from pathlib import Path
import re
import sys

HERE = Path(__file__).resolve().parent
ROOT = HERE.parents[1]
sys.path.insert(0, str(ROOT / "tools"))
from gtk2_palette import asset_css_expression  # noqa: E402
from gtk2_scrollbar_assets import adapt_scrollbars  # noqa: E402
import adaptive_assets  # noqa: E402

SOURCE = HERE.parent / "IrixClassic"
DESTINATION = HERE.parent / "IrixClassic-KDE"
VERSION = 1
LICENSE = "/* SPDX-License-Identifier: GPL-3.0-or-later */\n"

# Public GTK Config 6.3.4 names. Each referenced role has a Theme-priority
# fallback; an absent User provider must never resolve a symbol to transparent.
ROLE_STATES = {
    "window_bg": ("theme_bg_color_breeze", "theme_unfocused_bg_color_breeze", "insensitive_bg_color_breeze", "insensitive_unfocused_bg_color_breeze"),
    "window_fg": ("theme_fg_color_breeze", "theme_unfocused_fg_color_breeze", "insensitive_fg_color_breeze", "insensitive_unfocused_fg_color_breeze"),
    "view_bg": ("theme_base_color_breeze", "theme_unfocused_base_color_breeze", "insensitive_base_color_breeze", "theme_unfocused_view_bg_color_breeze"),
    "view_fg": ("theme_text_color_breeze", "theme_unfocused_text_color_breeze", "insensitive_base_fg_color_breeze", "theme_unfocused_view_text_color_breeze"),
    "selection_bg": ("theme_selected_bg_color_breeze", "theme_unfocused_selected_bg_color_breeze", "insensitive_selected_bg_color_breeze", "insensitive_unfocused_selected_bg_color_breeze"),
    "selection_fg": ("theme_selected_fg_color_breeze", "theme_unfocused_selected_fg_color_breeze", "insensitive_selected_fg_color_breeze", "insensitive_unfocused_selected_fg_color_breeze"),
    "button_bg": ("theme_button_background_normal_breeze", "theme_button_background_backdrop_breeze", "theme_button_background_insensitive_breeze", "theme_button_background_backdrop_insensitive_breeze"),
    "button_fg": ("theme_button_foreground_normal_breeze", "theme_button_foreground_backdrop_breeze", "theme_button_foreground_insensitive_breeze", "theme_button_foreground_backdrop_insensitive_breeze"),
    "header_bg": ("theme_header_background_breeze", "theme_header_background_backdrop_breeze", "theme_header_background_backdrop_breeze", "theme_header_background_backdrop_breeze"),
    "header_fg": ("theme_header_foreground_breeze", "theme_header_foreground_backdrop_breeze", "theme_header_foreground_insensitive_breeze", "theme_header_foreground_insensitive_backdrop_breeze"),
    "titlebar_bg": ("theme_titlebar_background_breeze", "theme_titlebar_background_backdrop_breeze", "theme_titlebar_background_backdrop_breeze", "theme_titlebar_background_backdrop_breeze"),
    "titlebar_fg": ("theme_titlebar_foreground_breeze", "theme_titlebar_foreground_backdrop_breeze", "theme_titlebar_foreground_insensitive_breeze", "theme_titlebar_foreground_insensitive_backdrop_breeze"),
    "borders": ("borders_breeze", "unfocused_borders_breeze", "insensitive_borders_breeze", "unfocused_insensitive_borders_breeze"),
    "error": ("error_color_breeze", "error_color_backdrop_breeze", "error_color_insensitive_breeze", "error_color_insensitive_backdrop_breeze"),
    "warning": ("warning_color_breeze", "warning_color_backdrop_breeze", "warning_color_insensitive_breeze", "warning_color_insensitive_backdrop_breeze"),
    "success": ("success_color_breeze", "success_color_backdrop_breeze", "success_color_insensitive_breeze", "success_color_insensitive_backdrop_breeze"),
    "button_focus": ("theme_button_decoration_focus_breeze", "theme_button_decoration_focus_backdrop_breeze", "theme_button_decoration_focus_insensitive_breeze", "theme_button_decoration_focus_backdrop_insensitive_breeze"),
    "button_hover": ("theme_button_decoration_hover_breeze", "theme_button_decoration_hover_backdrop_breeze", "theme_button_decoration_hover_insensitive_breeze", "theme_button_decoration_hover_backdrop_insensitive_breeze"),
}
STATIC_ROLES = {
    "tooltip_bg": "tooltip_background_breeze", "tooltip_fg": "tooltip_text_breeze",
    "tooltip_border": "tooltip_border_breeze", "link": "link_color_breeze",
    "visited": "link_visited_color_breeze",
}
FALLBACK = {
    "window_bg": ("#c1c1c1", "#c1c1c1", "#c1c1c1", "#c1c1c1"),
    "window_fg": ("#000000", "#000000", "#777777", "#777777"),
    "view_bg": ("#efefef", "#efefef", "#c1c1c1", "#c1c1c1"),
    "view_fg": ("#000000", "#000000", "#777777", "#777777"),
    "selection_bg": ("#9ebfbf", "#b3c3c3", "#b3c3c3", "#b3c3c3"),
    "selection_fg": ("#000000", "#000000", "#777777", "#777777"),
    "button_bg": ("#999999", "#999999", "#999999", "#999999"),
    "button_fg": ("#000000", "#000000", "#777777", "#777777"),
    "header_bg": ("#c1c1c1", "#c1c1c1", "#c1c1c1", "#c1c1c1"),
    "header_fg": ("#000000", "#000000", "#777777", "#777777"),
    "titlebar_bg": ("#a59f80", "#808080", "#808080", "#808080"),
    "titlebar_fg": ("#000000", "#000000", "#777777", "#777777"),
    "borders": ("mix(@theme_bg_color_breeze, @theme_fg_color_breeze, 0.25)",
                "mix(@theme_unfocused_bg_color_breeze, @theme_unfocused_fg_color_breeze, 0.25)",
                "mix(@insensitive_bg_color_breeze, @insensitive_fg_color_breeze, 0.25)",
                "mix(@insensitive_unfocused_bg_color_breeze, @insensitive_unfocused_fg_color_breeze, 0.25)"),
    "error": ("#cc0000", "#cc0000", "#777777", "#777777"),
    "warning": ("#996600", "#996600", "#777777", "#777777"),
    "success": ("#006600", "#006600", "#777777", "#777777"),
    "button_focus": ("#9ebfbf", "#b3c3c3", "#b3c3c3", "#b3c3c3"),
    "button_hover": ("#9ebfbf", "#b3c3c3", "#b3c3c3", "#b3c3c3"),
}
ALIASES = {
    "theme_bg_color": "window_bg", "theme_fg_color": "window_fg",
    "theme_base_color": "view_bg", "theme_text_color": "view_fg",
    "theme_selected_bg_color": "selection_bg", "theme_selected_fg_color": "selection_fg",
    "theme_tooltip_bg_color": "tooltip_bg", "theme_tooltip_fg_color": "tooltip_fg",
    "inactive_selection": "selection_bg", "insensitive_fg_color": "window_fg",
    "insensitive_bg_color": "window_bg", "insensitive_base_color": "view_bg",
    "borders": "borders", "warning_color": "warning", "error_color": "error",
    "success_color": "success", "accent_color": "selection_bg",
    "accent_bg_color": "selection_bg", "accent_fg_color": "selection_fg",
}
COLOR_PROPERTIES = {
    "color", "background-color", "border-color", "border-bottom-color", "border",
    "outline", "box-shadow", "background-image", "border-image-source", "-gtk-icon-source",
}
URL = re.compile(r'url\("([^\"]+\.png)"\)')
HEX = re.compile(r'#[a-fA-F0-9]{6}\b')
SYMBOL = re.compile(r'@([a-zA-Z_][a-zA-Z0-9_]*)')


def role(name: str, state: int = 0) -> str:
    return "@" + (STATIC_ROLES[name] if name in STATIC_ROLES else ROLE_STATES[name][state])


def definitions() -> str:
    values = {}
    for name, names in ROLE_STATES.items():
        for symbol, fallback in zip(names, FALLBACK[name]):
            values.setdefault(symbol, fallback)
    values.update({"tooltip_background_breeze": "#c1c1c1", "tooltip_text_breeze": "#000000",
                   "tooltip_border_breeze": "mix(@tooltip_background_breeze, @tooltip_text_breeze, 0.25)",
                   "link_color_breeze": "#0000aa", "link_visited_color_breeze": "#660066"})
    # Preserve conventional GTK names for application CSS and the original
    # structural rules. Widgets use state-specific native names directly.
    for alias, name in ALIASES.items():
        fixed_state = 1 if alias == "inactive_selection" else 2 if alias.startswith("insensitive_") else 0
        values[alias] = role(name, fixed_state)
    return "".join(f"@define-color {name} {value};\n" for name, value in values.items())


def rules(path: Path) -> list[tuple[str, dict[str, str]]]:
    text = re.sub(r'/\*.*?\*/', '', path.read_text(), flags=re.S)
    text = re.sub(r'^\s*@(define-color|import)\b[^;]*;', '', text, flags=re.M)
    result = []
    for match in re.finditer(r'([^{}]+)\{([^{}]*)\}', text):
        selector, body = match.groups()
        properties = {}
        for declaration in body.split(';'):
            if declaration.strip():
                key, value = declaration.split(':', 1)
                properties[key.strip()] = value.strip()
        result.append((selector.strip(), properties))
    if re.sub(r'([^{}]+)\{([^{}]*)\}', '', text).strip():
        raise ValueError("Unparsed CSS in " + str(path))
    return result


def family(selector: str) -> str:
    leaf = re.split(r'\s+|\s*>\s*', selector)[-1]
    if "tooltip" in selector:
        return "tooltip"
    if "headerbar" in selector or ".titlebar" in selector:
        return "button" if "button" in leaf else "titlebar"
    if re.search(r'\b(button|slider|check|radio|arrow)\b', leaf) or leaf == '.button':
        return "button"
    if "tab" in leaf and "notebook" in selector and ":checked" not in selector:
        return "button"
    if re.search(r'\b(scrollbar|scale|switch|progressbar|levelbar)\b', selector):
        return "button"
    if re.search(r'\b(entry|spinbutton|textview|listview|gridview|columnview|list|treeview|flowbox|iconview)\b', selector) or '.view' in selector:
        if "sidebar" not in selector and " border" not in selector:
            return "view"
    if re.search(r'\b(menubar|toolbar)\b', selector) and "item" not in selector:
        return "header"
    return "window"


def selected(selector: str) -> bool:
    return (":selected" in selector or
            bool(re.search(r'(menuitem|modelbutton|menubar\s*>\s*item).*(:(hover|active|checked))', selector)))


def tone(face: str, value: int, anchor: int) -> str:
    if value == anchor:
        return face
    amount = (anchor-value)/anchor if value < anchor else (value-anchor)/(255-anchor)
    return f"mix({face}, {'#000000' if value < anchor else '#ffffff'}, {amount:.8f})"


def literal_color(color: str, prop: str, selector: str, state: int) -> str:
    group = family(selector)
    face = role(group + "_bg", state)
    foreground = role(group + "_fg", state)
    color = color.lower()
    if prop == "color":
        if "link" in selector:
            return role("visited" if ":visited" in selector else "link")
        if selected(selector):
            return role("selection_fg", state)
        if "error" in selector:
            return role("error", state)
        if "warning" in selector:
            return role("warning", state)
        if color == "#606060":
            return f"mix({foreground}, {face}, 0.3)"
        return foreground
    if prop == "background-color":
        if "error" in selector:
            return f"mix({face}, {role('error', state)}, 0.25)"
        if "warning" in selector:
            return f"mix({face}, {role('warning', state)}, 0.25)"
        if selected(selector) or "switch:checked" in selector:
            return role("selection_bg", state)
        if color in ("#b6b6aa", "#efefef"):
            return role("view_bg", state)
        if color == "#d7e0dc":
            return f"mix({role('view_bg', state)}, {role('selection_bg', state)}, 0.25)"
        if color == "#919191":
            return tone(role("button_bg", state), 145, 153)
        return face
    if prop in ("border", "outline", "box-shadow") and color == "#000000":
        return foreground
    if group == "titlebar":
        return f"mix({face}, {'#ffffff' if color in ('#dad7ca', '#c6c6c6') else '#000000'}, 0.5)"
    rgb = tuple(int(color[i:i+2], 16) for i in (1, 3, 5))
    if len(set(rgb)) != 1:
        raise ValueError(f"Unmapped Classic color {color} in {selector} / {prop}")
    return tone(face, rgb[0], 153 if group == "button" else 193)


def color_value(value: str, prop: str, selector: str, state: int) -> str:
    value = HEX.sub(lambda match: literal_color(match.group(), prop, selector, state), value)
    def symbol(match):
        name = match[1]
        if name not in ALIASES:
            raise ValueError("Unmapped Classic symbol: " + name)
        semantic = ALIASES[name]
        if name == "theme_fg_color" and family(selector) == "button":
            semantic = "button_fg"
        if name == "insensitive_fg_color" and family(selector) in ("button", "view"):
            semantic = family(selector) + "_fg"
        return role(semantic, state)
    # Substitute source symbols before producing expressions containing native
    # names; otherwise a later match could accidentally remap generated roles.
    if '@' in value:
        value = SYMBOL.sub(lambda match: match.group() if match[1].endswith('_breeze') else symbol(match), value)
    return value


def asset_resolver(asset: str, color: str, state: int) -> str:
    expression = asset_css_expression(asset, color)
    for symbols in ROLE_STATES.values():
        expression = re.sub(r'@' + re.escape(symbols[0]) + r'\b', '@'+symbols[state], expression)
        # A disabled PNG encodes that state in its name; a backdrop-disabled
        # node must use the corresponding published combination as well.
        if state == 3:
            expression = re.sub(r'@' + re.escape(symbols[2]) + r'\b', '@'+symbols[3], expression)
    return expression


def state_asset(asset: str, state: int, manifest: dict) -> str:
    if state < 2 or asset.endswith('-disabled'):
        return asset
    stem = re.sub(r'-(normal|focused|pressed|toggled)$', '', asset)
    candidates = [stem+'-disabled', asset+'-disabled']
    return next((name for name in candidates if name in manifest["assets"]), asset)


def transformed(selector: str, properties: dict[str, str], state: int,
                manifest: dict, *, colors_only: bool = False) -> dict[str, str]:
    output = {}
    for prop, value in properties.items():
        if colors_only and prop not in COLOR_PROPERTIES:
            continue
        match = URL.fullmatch(value)
        if match:
            asset = state_asset(Path(match[1]).stem, state, manifest)
            image = adaptive_assets.expression(asset, lambda color: asset_resolver(asset, color, state), manifest=manifest)
            if prop == "-gtk-icon-source":
                # Native Gtk icon-source accepts one image. Monochrome arrow
                # glyphs have a single symbolic layer; do not silently drop
                # layers if future artwork becomes multicolored.
                if len(adaptive_assets.slices(asset, manifest=manifest)) != 1 or len(adaptive_assets.slices(asset, manifest=manifest)[0]['layers']) != 1:
                    raise ValueError("Icon-source is not a one-layer glyph: " + asset)
                output[prop] = image['background-image']
            elif prop in ("background-image", "border-image-source"):
                if adaptive_assets.geometry(asset, manifest=manifest)['border']:
                    output.update(image)
                else:
                    # A glyph keeps the source's cascaded geometry: check's
                    # left/top and vertical separator's repeat are declared
                    # in earlier rules. CSS repeats a single position/size
                    # value across layers, so it also fits split color masks.
                    # Setting helper defaults here would mask that cascade.
                    output['background-image'] = image['background-image']
            else:
                raise ValueError("Unexpected Classic image property: " + prop)
        elif prop == "border-image-source" and value == "none":
            output[prop] = value
            output['background-image'] = "none"
        elif prop in COLOR_PROPERTIES:
            output[prop] = color_value(value, prop, selector, state)
        elif not colors_only:
            # Layer-specific geometry generated above replaces the original
            # single-image positions, not the control's requested dimensions.
            if prop.startswith('background-') and prop != 'background-color' and prop in output:
                continue
            output[prop] = value
    return output


def render_rule(selector: str, properties: dict[str, str]) -> str:
    if not properties:
        return ""
    return selector + " {\n" + ''.join(f"  {key}: {value};\n" for key,value in properties.items()) + "}\n"


def gtk3_stepper_geometry() -> str:
    """Keep each full stepper image above command-button state geometry.

    A bare ``scrollbar button`` loses to ``button:disabled`` (and the
    pressed/backdrop combinations) in the shared stylesheet. Those rules
    would shrink the 18px arrow into a 3px command-frame corner. Match every
    shared state explicitly; neither the existing images nor metrics change.
    """
    selectors = ["scrollbar button" + interaction + state
                 for state in ("", ":backdrop", ":disabled", ":disabled:backdrop")
                 for interaction in ("", ":hover", ":active", ":checked")]
    return render_rule(',\n'.join(selectors), {
        '-gtk-icon-source': 'none',
        'background-size': '18px 18px',
        'background-position': 'center',
        'background-repeat': 'no-repeat',
        'background-origin': 'border-box',
        'background-clip': 'border-box',
        'border-image-source': 'none',
    })


def stylesheet(source: Path, manifest: dict) -> str:
    source_rules = rules(source)
    output = []
    for selector, properties in source_rules:
        for individual in selector.split(','):
            individual = individual.strip()
            state = int(':backdrop' in individual) + 2*int(':disabled' in individual)
            output.append(render_rule(individual, transformed(individual, properties, state, manifest)))
    # Re-use every semantic rule for Inactive, Disabled and their combination.
    # Source disabled assets/checked glyphs keep their distinct geometry.
    for state, suffix in ((1, ':backdrop'), (2, ':disabled'), (3, ':disabled:backdrop')):
        for selector, properties in source_rules:
            if selector == '*' or not any(prop in COLOR_PROPERTIES for prop in properties):
                continue
            for individual in selector.split(','):
                individual = individual.strip()
                if ':backdrop' in individual or ':disabled' in individual:
                    continue
                target = individual + suffix
                output.append(render_rule(target, transformed(individual, properties, state, manifest, colors_only=True)))
    return LICENSE + ''.join(output)


def gtk4_frame_geometry(source: Path, manifest: dict) -> str:
    """Keep corners fixed; stretch only the constant axis of each edge strip.

    GTK4's Cairo renderer does not reliably repeat the 1px symbolic strips used
    by GTK3. Every frame edge has already been proved uniform on its long axis
    by adaptive_assets.generate(). Stretching that axis therefore preserves its
    exact transverse pixel bands without stretching a corner or a whole frame.
    This overrides only image geometry; colors, masks and widget metrics stay
    in the shared stylesheet, and GTK3 retains its repeated-strip mechanism.
    """
    output = []
    source_rules = rules(source)

    def geometry_rule(selector: str, properties: dict[str, str], state: int) -> str:
        frames = []
        for prop in ('background-image', 'border-image-source'):
            match = URL.fullmatch(properties.get(prop, ''))
            if match:
                asset = state_asset(Path(match[1]).stem, state, manifest)
                if adaptive_assets.geometry(asset, manifest=manifest)['border']:
                    frames.append(asset)
        if not frames:
            return ''
        # A CSS rule can provide only one final background-image. Preserve the
        # same declaration order as transformed() if this ever contains both.
        converted = transformed(selector, properties, state, manifest, colors_only=True)
        sizes = converted['background-size'].split(', ')
        repeats = converted['background-repeat'].split(', ')
        if len(sizes) != len(repeats):
            raise ValueError('Mismatched Classic frame layer geometry')
        for index, repeat in enumerate(repeats):
            width, height = sizes[index].split()
            if repeat == 'repeat-x':
                if width != '1px':
                    raise ValueError('Nonuniform horizontal Classic frame strip')
                sizes[index], repeats[index] = '100% ' + height, 'no-repeat'
            elif repeat == 'repeat-y':
                if height != '1px':
                    raise ValueError('Nonuniform vertical Classic frame strip')
                sizes[index], repeats[index] = width + ' 100%', 'no-repeat'
        return render_rule(selector, {'background-size': ', '.join(sizes),
                                      'background-repeat': ', '.join(repeats)})

    for selector, properties in source_rules:
        for individual in selector.split(','):
            individual = individual.strip()
            state = int(':backdrop' in individual) + 2 * int(':disabled' in individual)
            output.append(geometry_rule(individual, properties, state))
    for state, suffix in ((1, ':backdrop'), (2, ':disabled'), (3, ':disabled:backdrop')):
        for selector, properties in source_rules:
            for individual in selector.split(','):
                individual = individual.strip()
                if ':backdrop' in individual or ':disabled' in individual:
                    continue
                output.append(geometry_rule(individual + suffix, properties, state))
    return ''.join(output)


def build(destination: Path = DESTINATION, *, theme_name: str = "IrixClassic-KDE") -> dict:
    if theme_name not in ("IrixClassic-KDE", "IrixClassic-KDE-Reload"):
        raise ValueError("Unknown owned GTK theme identity")
    destination = Path(destination)
    masks = adaptive_assets.generate(destination/'common/adaptive')
    for folder in ('common', 'gtk-2.0', 'gtk-3.0', 'gtk-4.0'):
        (destination/folder).mkdir(parents=True, exist_ok=True)
    (destination/'common/gtk.css').write_text(LICENSE + definitions() + stylesheet(SOURCE/'common/gtk.css', masks))
    for version in ('3.0', '4.0'):
        (destination/f'gtk-{version}/gtk.css').write_text(LICENSE + '@import url("../common/gtk.css");\n@import url("../common/gtk-'+version+'-overrides.css");\n')
        # GtkConfig may request the native dark variant for any selected KDE
        # scheme. Its colors still come from that scheme, not from Adwaita.
        (destination/f'gtk-{version}/gtk-dark.css').write_text(LICENSE + '@import url("gtk.css");\n')
        version_css = stylesheet(SOURCE/f'gtk-{version}/gtk.css', masks)
        if version == '3.0':
            # A stepper is a complete 18px glyph, not a command-frame layer.
            # Reset the inherited multi-layer command geometry and suppress
            # Gtk3's builtin chevron over the already drawn Classic arrow.
            version_css += gtk3_stepper_geometry()
        elif version == '4.0':
            version_css += gtk4_frame_geometry(SOURCE/'common/gtk.css', masks)
            version_css += gtk4_frame_geometry(SOURCE/f'gtk-{version}/gtk.css', masks)
        (destination/f'common/gtk-{version}-overrides.css').write_text(version_css)
    (destination/'index.theme').write_text('[Desktop Entry]\nType=X-GNOME-Metatheme\nName='+theme_name+'\nComment=IRIX Classic geometry following KDE color roles\nEncoding=UTF-8\n\n[X-GNOME-Metatheme]\nGtkTheme='+theme_name+'\n')
    # Gtk2 needs its own pixmap closure. Keep the original palette as fallback;
    # gtk2_palette supplies a journaled native-role overlay for this variant.
    # No runtime reference to a checkout or another installed theme is needed.
    source_rc = (SOURCE/'gtk-2.0/gtkrc').read_bytes()
    gtk2_scrollbars = adapt_scrollbars(source_rc.decode('utf-8'),
                                      lambda name: (SOURCE/'common/assets'/name).read_bytes())
    rc = gtk2_scrollbars.text.encode('utf-8')
    (destination/'gtk-2.0/gtkrc').write_bytes(rc)
    (destination/'common/assets').mkdir(exist_ok=True)
    for name in sorted(set(re.findall(rb'(?:overlay_)?file\s*=\s*"\.\./common/assets/([a-z0-9-]+\.png)"', rc))):
        filename = name.decode('ascii')
        (destination/'common/assets'/filename).write_bytes((SOURCE/'common/assets'/filename).read_bytes())
    (destination/'LICENSE').write_bytes((SOURCE/'LICENSE').read_bytes())
    manifest = {'schema': VERSION, 'name': theme_name,
                'builder_sha256': hashlib.sha256(Path(__file__).read_bytes()).hexdigest(),
                'gtk2_scrollbar_helper_sha256': hashlib.sha256((ROOT/'tools/gtk2_scrollbar_assets.py').read_bytes()).hexdigest(),
                'gtk2_scrollbars': gtk2_scrollbars.manifest,
                'source': {str(path.relative_to(SOURCE)): hashlib.sha256(path.read_bytes()).hexdigest()
                           for path in (SOURCE/'gtk-2.0/gtkrc', SOURCE/'common/gtk.css', SOURCE/'gtk-3.0/gtk.css', SOURCE/'gtk-4.0/gtk.css')},
                'files': {str(path.relative_to(destination)): hashlib.sha256(path.read_bytes()).hexdigest()
                          for path in sorted(destination.rglob('*')) if path.is_file() and path != destination/'MANIFEST.json'}}
    (destination/'MANIFEST.json').write_text(json.dumps(manifest, indent=2)+'\n')
    return manifest


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--output-dir', type=Path, default=DESTINATION)
    parser.add_argument('--theme-name', choices=('IrixClassic-KDE', 'IrixClassic-KDE-Reload'), default='IrixClassic-KDE')
    args = parser.parse_args()
    result = build(args.output_dir, theme_name=args.theme_name)
    print(f"Built {result['name']} / {len(result['files'])} files; no profile selected")


if __name__ == '__main__':
    main()
