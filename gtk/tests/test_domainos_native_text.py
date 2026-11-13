#!/usr/bin/env python3
# SPDX-License-Identifier: GPL-3.0-or-later
"""Compare painted GTK3 editor text to KDE role snapshots, without session edits.

Use --colors NAME=colors.css for each palette and --output-dir for a new
evidence directory. Offscreen native widgets use artificial text only. Covers
GtkTextView and Mousepad's none -> GtkSourceView Classic configuration, including
backdrop, disabled and selection. Does not assess historical font fidelity.
"""
import argparse
from collections import Counter
import hashlib
import json
from pathlib import Path
import sys
import time

ROOT = Path(__file__).resolve().parents[2]


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--colors', action='append', required=True)
    parser.add_argument('--output-dir', type=Path, required=True)
    args = parser.parse_args()
    args.output_dir.mkdir(parents=True, exist_ok=False)
    import gi
    gi.require_version('Gtk', '3.0')
    gi.require_version('GtkSource', '4')
    from gi.repository import Gtk, GtkSource, Gdk, GLib
    sys.path.insert(0, str(ROOT/'tools'))
    from gtk2_palette import exported_palette

    settings = Gtk.Settings.get_default()
    settings.set_property('gtk-theme-name', 'DomainOS-SR10-4-KDE-Reload')
    settings.set_property('gtk-enable-animations', False)
    settings.set_property('gtk-cursor-blink', False)
    source = ROOT/'gtk/DomainOS-SR10-4-KDE/gtk-3.0/gtk.css'
    theme = Gtk.CssProvider()
    theme.load_from_path(str(source))
    screen = Gdk.Screen.get_default()
    Gtk.StyleContext.add_provider_for_screen(screen, theme, Gtk.STYLE_PROVIDER_PRIORITY_THEME)
    reports = []
    states = (
        ('normal', False, False, False, 'theme_base_color_breeze', 'theme_text_color_breeze'),
        ('backdrop', True, False, False, 'theme_unfocused_base_color_breeze', 'theme_unfocused_text_color_breeze'),
        ('disabled', False, True, False, 'insensitive_base_color_breeze', 'insensitive_base_fg_color_breeze'),
        ('disabled-backdrop', True, True, False, 'theme_unfocused_view_bg_color_breeze', 'theme_unfocused_view_text_color_breeze'),
        ('selection', False, False, True, 'theme_base_color_breeze', 'theme_text_color_breeze'),
        ('selection-backdrop', True, False, True, 'theme_unfocused_base_color_breeze', 'theme_unfocused_text_color_breeze'),
    )

    def settle():
        end = time.monotonic()+0.08
        while time.monotonic() < end:
            while GLib.MainContext.default().pending():
                GLib.MainContext.default().iteration(False)
            time.sleep(0.002)

    def rgb(hex_value):
        return tuple(int(hex_value[i:i+2], 16) for i in (1, 3, 5))

    for item in args.colors:
        name, filename = item.split('=', 1)
        if not name.isidentifier(): raise ValueError('Invalid palette label')
        contents = Path(filename).read_bytes()
        roles = exported_palette(contents)
        palette = Gtk.CssProvider()
        palette.load_from_data(contents)
        Gtk.StyleContext.add_provider_for_screen(screen, palette, Gtk.STYLE_PROVIDER_PRIORITY_USER)
        for cls, label in ((Gtk.TextView, 'textview'), (GtkSource.View, 'mousepad-none-classic')):
            for state, inactive, disabled, selected, bg, fg in states:
                window = Gtk.OffscreenWindow()
                view = cls()
                view.set_size_request(400, 150)
                view.set_left_margin(8); view.set_top_margin(8)
                view.set_monospace(True)
                view.set_cursor_visible(False)
                buffer = view.get_buffer()
                buffer.set_text('MMMMM WWWWW 0123456789\nABCDEFGHIJKLMNOPQRSTUVWXYZ\nTexto artificial de contraste')
                if isinstance(view, GtkSource.View):
                    buffer.set_style_scheme(GtkSource.StyleSchemeManager.get_default().get_scheme('classic'))
                    buffer.set_highlight_syntax(False)
                window.add(view); window.show_all()
                if disabled: view.set_sensitive(False)
                if inactive: view.set_state_flags(Gtk.StateFlags.BACKDROP, False)
                if selected:
                    window.set_focus(view)
                    view.set_state_flags(Gtk.StateFlags.FOCUSED, False)
                    buffer.select_range(buffer.get_start_iter(), buffer.get_iter_at_offset(11))
                settle()
                pix = window.get_pixbuf()
                target = args.output_dir/(name+'-'+label+'-'+state+'.png')
                pix.savev(str(target), 'png', [], [])
                raw, stride, channels = pix.get_pixels(), pix.get_rowstride(), pix.get_n_channels()
                counts = Counter(tuple(raw[y*stride+x*channels:y*stride+x*channels+3])
                                 for y in range(5, 130) for x in range(5, 390))
                checks = {'painted_background_matches_view': counts[rgb(roles[bg])] > 10000,
                          'painted_text_matches_view': counts[rgb(roles[fg])] > 30}
                if selected:
                    prefix = 'theme_unfocused_selected_' if inactive else 'theme_selected_'
                    checks['painted_selection_background'] = counts[rgb(roles[prefix+'bg_color_breeze'])] > 100
                    checks['painted_selection_text'] = counts[rgb(roles[prefix+'fg_color_breeze'])] > 30
                reports.append({'palette': name, 'widget': label, 'state': state,
                    'color_input_sha256': hashlib.sha256(contents).hexdigest(),
                    'background_role': bg, 'text_role': fg, 'checks': checks,
                    'painted_colors': [[list(color), count] for color, count in counts.most_common(5)],
                    'image_sha256': hashlib.sha256(target.read_bytes()).hexdigest()})
                window.destroy()
        Gtk.StyleContext.remove_provider_for_screen(screen, palette)
    result = {'scope': 'GTK3 native painted editor surface; no personal documents or profile edits',
              'passed': all(all(row['checks'].values()) for row in reports), 'cases': reports}
    (args.output_dir/'RESULTADO.json').write_text(json.dumps(result, indent=2)+'\n')
    print(json.dumps({'passed': result['passed'], 'cases': len(reports),
                      'failures': [r for r in reports if not all(r['checks'].values())]}))
    return 0 if result['passed'] else 1


if __name__ == '__main__': sys.exit(main())
