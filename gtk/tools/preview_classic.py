#!/usr/bin/env python3
# SPDX-FileCopyrightText: 2026 mrmmx31
# SPDX-License-Identifier: GPL-3.0-or-later
"""Native GTK3 gallery and state captures; run under an isolated Xvfb display.

This host never sets desktop preferences. PNGs contain only its artificial
window, its buttons/fields and its menu. Timed capture is test orchestration,
not an animation or a delayed theme state. Requires GI GTK3 and Pillow.
"""
import argparse
import json
import os
from pathlib import Path
import subprocess
import tempfile
import time

ROOT = Path(__file__).resolve().parents[2]
parser = argparse.ArgumentParser(description=__doc__)
parser.add_argument("--output-dir", type=Path, required=True)
parser.add_argument("--font", default="Nimbus Sans 10.5", help="Private gallery font; theme inherits the profile's gtk-font-name")
args = parser.parse_args()
out = args.output_dir.resolve()
if Path("/tmp") not in out.parents:
    parser.error("Capture output must be a directory under /tmp")
out.mkdir(parents=True, exist_ok=True)
data = tempfile.TemporaryDirectory(prefix="irixclassic-gtk3-", dir="/tmp")
theme_dir = Path(data.name) / "themes"
theme_dir.mkdir()
(theme_dir / "IrixClassic").symlink_to(ROOT / "gtk" / "IrixClassic", target_is_directory=True)
os.environ["XDG_DATA_HOME"] = data.name
os.environ["XDG_CONFIG_HOME"] = str(Path(data.name) / "config")
os.environ["GTK_THEME"] = "IrixClassic"
os.environ["GDK_BACKEND"] = "x11"
os.environ["GTK_OVERLAY_SCROLLING"] = "0"

import gi
gi.require_version("Gtk", "3.0")
gi.require_version("Gdk", "3.0")
gi.require_version("GdkX11", "3.0")
from gi.repository import Gtk, Gdk, GdkX11, GLib
from PIL import Image

Gtk.init([])
Gtk.Settings.get_default().set_property("gtk-theme-name", "IrixClassic")
Gtk.Settings.get_default().set_property("gtk-font-name", args.font)
provider = Gtk.CssProvider()
css_errors = []
provider.connect("parsing-error", lambda p, section, error: css_errors.append(str(error)))
provider.load_from_path(str(ROOT / "gtk" / "IrixClassic" / "gtk-3.0" / "gtk.css"))
Gtk.StyleContext.add_provider_for_screen(Gdk.Screen.get_default(), provider, Gtk.STYLE_PROVIDER_PRIORITY_APPLICATION)
Gtk.Settings.get_default().set_property("gtk-enable-animations", False)
win = Gtk.Window(title=f"IrixClassic GTK3 proof {os.getpid()}")
win.set_decorated(False)
win.set_default_size(940, 650)
win.connect("destroy", Gtk.main_quit)
outer = Gtk.Box(orientation=Gtk.Orientation.VERTICAL, spacing=3)
outer.set_border_width(3)
win.add(outer)
title = Gtk.Label(label="IRIX CLASSIC — native GTK 3 controls")
title.set_xalign(0)
outer.pack_start(title, False, False, 0)
menubar = Gtk.MenuBar()
file_item = Gtk.MenuItem.new_with_label("File")
menu = Gtk.Menu()
for caption in ("Open folder", "Save selection", "Unavailable command"):
    item = Gtk.MenuItem.new_with_label(caption)
    if caption.startswith("Unavailable"):
        item.set_sensitive(False)
    menu.append(item)
menu.append(Gtk.SeparatorMenuItem())
check_menu = Gtk.CheckMenuItem.new_with_label("Show hidden files")
check_menu.set_active(True)
menu.append(check_menu)
submenu_item = Gtk.MenuItem.new_with_label("Options")
submenu = Gtk.Menu()
submenu.append(Gtk.MenuItem.new_with_label("Compact list"))
submenu.append(Gtk.MenuItem.new_with_label("Detailed list"))
submenu_item.set_submenu(submenu)
menu.append(submenu_item)
file_item.set_submenu(menu)
menubar.append(file_item)
for caption in ("Edit", "View", "Help"):
    menubar.append(Gtk.MenuItem.new_with_label(caption))
outer.pack_start(menubar, False, False, 0)
body = Gtk.Paned(orientation=Gtk.Orientation.HORIZONTAL)
outer.pack_start(body, True, True, 0)
sidebar = Gtk.ListBox()
sidebar.get_style_context().add_class("sidebar")
sidebar.set_size_request(165, -1)
for caption in ("Home", "Documents", "Pictures", "Applications", "Devices", "Network"):
    label = Gtk.Label(label=caption)
    label.set_xalign(0)
    sidebar.add(label)
sidebar.select_row(sidebar.get_row_at_index(1))
body.pack1(sidebar, False, False)
book = Gtk.Notebook()
body.pack2(book, True, False)
page = Gtk.Box(orientation=Gtk.Orientation.VERTICAL, spacing=3)
page.set_border_width(3)
book.append_page(page, Gtk.Label(label="Controls"))
book.append_page(Gtk.Label(label="Native notebook page"), Gtk.Label(label="Folders"))
buttons = Gtk.Box(spacing=3)
page.pack_start(buttons, False, False, 0)
command = Gtk.Button(label="Apply")
buttons.pack_start(command, False, False, 0)
default = Gtk.Button(label="Default")
default.set_can_default(True)
default.get_style_context().add_class("default")
buttons.pack_start(default, False, False, 0)
toggle = Gtk.ToggleButton(label="Latched")
toggle.set_active(True)
buttons.pack_start(toggle, False, False, 0)
disabled = Gtk.Button(label="Unavailable")
disabled.set_sensitive(False)
buttons.pack_start(disabled, False, False, 0)
grid = Gtk.Grid(column_spacing=3, row_spacing=3)
page.pack_start(grid, False, False, 0)
entry = Gtk.Entry()
entry.set_text("/home/classic/Documents")
grid.attach(Gtk.Label(label="Folder"), 0, 0, 1, 1)
grid.attach(entry, 1, 0, 1, 1)
readonly = Gtk.Entry()
readonly.set_text("Read only")
readonly.set_editable(False)
grid.attach(readonly, 2, 0, 1, 1)
entry_disabled = Gtk.Entry()
entry_disabled.set_text("Unavailable field")
entry_disabled.set_sensitive(False)
grid.attach(entry_disabled, 3, 0, 1, 1)
checks = Gtk.Box(spacing=6)
page.pack_start(checks, False, False, 0)
for caption, active, mixed, sensitive in (("Option", False, False, True), ("Checked", True, False, True), ("Mixed", True, True, True), ("Unavailable", True, False, False)):
    check = Gtk.CheckButton(label=caption)
    check.set_active(active)
    check.set_inconsistent(mixed)
    check.set_sensitive(sensitive)
    checks.pack_start(check, False, False, 0)
radios = Gtk.Box(spacing=6)
page.pack_start(radios, False, False, 0)
radio = Gtk.RadioButton.new_with_label_from_widget(None, "List")
radios.pack_start(radio, False, False, 0)
radios.pack_start(Gtk.RadioButton.new_with_label_from_widget(radio, "Icons"), False, False, 0)
for active in (False, True):
    switch = Gtk.Switch()
    switch.set_active(active)
    radios.pack_start(switch, False, False, 0)
disabled_switch = Gtk.Switch()
disabled_switch.set_active(True)
disabled_switch.set_sensitive(False)
radios.pack_start(disabled_switch, False, False, 0)
inputs = Gtk.Box(spacing=3)
page.pack_start(inputs, False, False, 0)
combo = Gtk.ComboBoxText()
for caption in ("Compact list", "Detailed list", "Icon grid"):
    combo.append_text(caption)
combo.set_active(0)
inputs.pack_start(combo, False, False, 0)
spin = Gtk.SpinButton.new_with_range(0, 100, 1)
spin.set_value(42)
inputs.pack_start(spin, False, False, 0)
inputs.pack_start(Gtk.Button(label="Toolbar action"), False, False, 0)
model = Gtk.ListStore(str, str, str)
for i in range(1, 45):
    model.append([f"Folder {i:02d}", "Directory", "12 items"])
tree = Gtk.TreeView(model=model)
for i, caption in enumerate(("Name", "Type", "Contents")):
    renderer = Gtk.CellRendererText()
    col = Gtk.TreeViewColumn(caption, renderer, text=i)
    col.set_min_width(180)
    col.set_resizable(True)
    tree.append_column(col)
tree.get_selection().select_path(Gtk.TreePath.new_from_string("2"))
scrolled = Gtk.ScrolledWindow()
scrolled.set_policy(Gtk.PolicyType.ALWAYS, Gtk.PolicyType.ALWAYS)
scrolled.set_overlay_scrolling(False)
scrolled.set_shadow_type(Gtk.ShadowType.IN)
scrolled.add(tree)
page.pack_start(scrolled, True, True, 0)
scale = Gtk.Scale.new_with_range(Gtk.Orientation.HORIZONTAL, 0, 100, 1)
scale.set_value(38)
scale.set_draw_value(False)
page.pack_start(scale, False, False, 0)
progress = Gtk.ProgressBar()
progress.set_fraction(0.62)
page.pack_start(progress, False, False, 0)
status = Gtk.Label(label="44 folders — drawing and input belong to GTK")
status.set_xalign(0)
outer.pack_start(status, False, False, 0)
win.show_all()
entry.grab_focus()


def pump():
    for _ in range(5):
        while Gtk.events_pending():
            Gtk.main_iteration_do(False)
        time.sleep(0.015)


def capture(widget, name):
    gwin = widget.get_window()
    if widget is win or isinstance(widget, Gtk.Menu):
        x = y = 0
        width, height = gwin.get_width(), gwin.get_height()
    else:
        x, y = widget.translate_coordinates(win, 0, 0)
        gwin = win.get_window()
        width, height = widget.get_allocated_width(), widget.get_allocated_height()
    pixbuf = Gdk.pixbuf_get_from_window(gwin, x, y, width, height)
    if pixbuf is None:
        raise RuntimeError(f"No pixels for {name}")
    pixbuf.savev(str(out / name), "png", [], [])
    return Image.open(out / name).convert("RGBA")


def pointer(widget, action):
    x, y = widget.translate_coordinates(win, 0, 0)
    x += widget.get_allocated_width() // 2
    y += widget.get_allocated_height() // 2
    xid = win.get_window().get_xid()
    subprocess.run(["xdotool", "mousemove", "--window", str(xid), str(x), str(y), *action], check=True)
    pump()


def verify():
    try:
        pump()
        capture(win, "gtk3-gallery.png")
        capture(entry, "gtk3-entry-focus.png")
        pointer(command, [])
        normal = capture(command, "gtk3-button-normal.png")
        pointer(command, ["mousedown", "1"])
        pressed = capture(command, "gtk3-button-pressed.png")
        assert command.get_state_flags() & Gtk.StateFlags.ACTIVE, "Native pointer press did not activate the button"
        changed = sum(a != b for a, b in zip(normal.getdata(), pressed.getdata()))
        assert changed > 10, "Pressed bevel did not change"
        assert normal.getpixel((0, 0)) == pressed.getpixel((0, 0)), "Pressed state moved the outer contour"
        subprocess.run(["xdotool", "mouseup", "1"], check=True)
        pump()
        capture(disabled, "gtk3-button-disabled.png")
        pointer(file_item, ["click", "1"])
        capture(menu, "gtk3-menu.png")
        menu.popdown()
        pump()
        gallery = Image.open(out / "gtk3-gallery.png").convert("RGB")
        colors = {c: sum(p == c for p in gallery.getdata()) for c in ((193, 193, 193), (153, 153, 153), (158, 191, 191), (119, 119, 119), (204, 0, 0), (0, 0, 204))}
        assert all(colors.values()), f"Missing Classic color roles: {colors}"
        report = {"gtk_version": f"{Gtk.MAJOR_VERSION}.{Gtk.MINOR_VERSION}.{Gtk.MICRO_VERSION}",
                  "theme_name": Gtk.Settings.get_default().get_property("gtk-theme-name"),
                  "css_diagnostics": css_errors, "fixture_font": args.font, "font": title.get_style_context().get_property("font", Gtk.StateFlags.NORMAL).to_string(),
                  "captures_scope": "own artificial window and own menu only", "native_pressed_pixels_changed": changed,
                  "classic_color_pixels": {str(c): n for c, n in colors.items()}}
        assert not css_errors, css_errors
        assert report["theme_name"] == "IrixClassic", report
        (out / "gtk3-report.json").write_text(json.dumps(report, indent=2) + "\n")
        print(json.dumps(report), flush=True)
    except Exception:
        import traceback
        traceback.print_exc()
        global failed
        failed = True
    finally:
        Gtk.main_quit()
    return False


failed = False
GLib.timeout_add(400, verify)
Gtk.main()
data.cleanup()
raise SystemExit(1 if failed else 0)
