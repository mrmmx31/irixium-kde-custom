#!/usr/bin/env python3
# SPDX-FileCopyrightText: 2026 mrmmx31
# SPDX-License-Identifier: GPL-3.0-or-later
"""Native GTK2 pixmap-engine gallery in a private Xvfb display.

Requires legacy Gtk-2.0 GI, the external GTK2 pixmap engine and ImageMagick.
Only the gallery process parses the theme. Captures use its own X window.
"""
import argparse
import ctypes as C
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
    parser.error("Capture output must be under /tmp")
out.mkdir(parents=True, exist_ok=True)
private = tempfile.TemporaryDirectory(prefix="irixclassic-gtk2-", dir="/tmp")
os.environ["XDG_CONFIG_HOME"] = private.name
os.environ["GTK_MODULES"] = ""
os.environ["GTK2_RC_FILES"] = str(ROOT / "gtk" / "IrixClassic" / "gtk-2.0" / "gtkrc")
os.environ["GDK_BACKEND"] = "x11"
import gi
gi.require_version("Gtk", "2.0")
from gi.repository import Gtk, GLib, GObject
from PIL import Image

Gtk.init([])
Gtk.Settings.get_default().set_property("gtk-font-name", args.font)
Gtk.rc_parse(os.environ["GTK2_RC_FILES"])
win = Gtk.Window()
title = f"IrixClassic GTK2 proof {os.getpid()}"
win.set_title(title)
win.set_decorated(False)
win.set_default_size(940, 650)
win.connect("destroy", Gtk.main_quit)
outer = Gtk.VBox(spacing=3)
outer.set_border_width(3)
win.add(outer)
outer.pack_start(Gtk.Label(label="IRIX CLASSIC — native GTK 2 controls"), False, False, 0)
bar = Gtk.MenuBar()
file_item = Gtk.MenuItem(label="File")
menu = Gtk.Menu()
for caption in ("Open folder", "Save selection", "Unavailable command"):
    item = Gtk.MenuItem(label=caption)
    item.set_sensitive(not caption.startswith("Unavailable"))
    menu.append(item)
menu.append(Gtk.SeparatorMenuItem())
item = Gtk.CheckMenuItem(label="Show hidden files")
item.set_active(True)
menu.append(item)
file_item.set_submenu(menu)
bar.append(file_item)
for caption in ("Edit", "View", "Help"):
    bar.append(Gtk.MenuItem(label=caption))
outer.pack_start(bar, False, False, 0)
body = Gtk.HPaned()
outer.pack_start(body, True, True, 0)


def listing(rows, headers):
    model = Gtk.ListStore.newv([GObject.TYPE_STRING] * len(headers))
    for values in rows:
        it = model.append()
        for i, value in enumerate(values):
            model.set_value(it, i, value)
    view = Gtk.TreeView(model=model)
    for i, caption in enumerate(headers):
        renderer = Gtk.CellRendererText()
        column = Gtk.TreeViewColumn(title=caption)
        column.pack_start(renderer, True)
        column.add_attribute(renderer, "text", i)
        column.set_min_width(170)
        column.set_resizable(True)
        view.append_column(column)
    return view


sidebar = listing([(x,) for x in ("Home", "Documents", "Pictures", "Applications", "Devices", "Network")], ("Places",))
sidebar.set_name("sidebar")
sidebar.set_headers_visible(False)
sidebar.set_size_request(165, -1)
sidebar.get_selection().select_path(Gtk.TreePath.new_from_string("1"))
body.pack1(sidebar, False, False)
book = Gtk.Notebook()
body.pack2(book, True, False)
page = Gtk.VBox(spacing=3)
page.set_border_width(3)
book.append_page(page, Gtk.Label(label="Controls"))
book.append_page(Gtk.Label(label="Native notebook page"), Gtk.Label(label="Folders"))
buttons = Gtk.HBox(spacing=3)
page.pack_start(buttons, False, False, 0)
command = Gtk.Button(label="Apply")
buttons.pack_start(command, False, False, 0)
default = Gtk.Button(label="Default")
default.set_can_default(True)
buttons.pack_start(default, False, False, 0)
toggle = Gtk.ToggleButton(label="Latched")
toggle.set_active(True)
buttons.pack_start(toggle, False, False, 0)
disabled = Gtk.Button(label="Unavailable")
disabled.set_sensitive(False)
buttons.pack_start(disabled, False, False, 0)
fields = Gtk.HBox(spacing=3)
page.pack_start(fields, False, False, 0)
fields.pack_start(Gtk.Label(label="Folder"), False, False, 0)
entry = Gtk.Entry()
entry.set_text("/home/classic/Documents")
fields.pack_start(entry, False, False, 0)
readonly = Gtk.Entry()
readonly.set_text("Read only")
readonly.set_editable(False)
fields.pack_start(readonly, False, False, 0)
unavailable = Gtk.Entry()
unavailable.set_text("Unavailable field")
unavailable.set_sensitive(False)
fields.pack_start(unavailable, False, False, 0)
checks = Gtk.HBox(spacing=6)
page.pack_start(checks, False, False, 0)
for caption, active, mixed, enabled in (("Option", False, False, True), ("Checked", True, False, True), ("Mixed", True, True, True), ("Unavailable", True, False, False)):
    check = Gtk.CheckButton(label=caption)
    check.set_active(active)
    check.set_inconsistent(mixed)
    check.set_sensitive(enabled)
    checks.pack_start(check, False, False, 0)
radios = Gtk.HBox(spacing=6)
page.pack_start(radios, False, False, 0)
radio = Gtk.RadioButton(label="List")
radio2 = Gtk.RadioButton(label="Icons")
radio2.set_group(radio.get_group())
radios.pack_start(radio, False, False, 0)
radios.pack_start(radio2, False, False, 0)
inputs = Gtk.HBox(spacing=3)
page.pack_start(inputs, False, False, 0)
combo = Gtk.ComboBoxText()
for caption in ("Compact list", "Detailed list", "Icon grid"):
    combo.append_text(caption)
combo.set_active(0)
inputs.pack_start(combo, False, False, 0)
spin = Gtk.SpinButton.new_with_range(0, 100, 1)
spin.set_value(42)
inputs.pack_start(spin, False, False, 0)
view = listing([(f"Folder {i:02d}", "Directory", "12 items") for i in range(1, 45)], ("Name", "Type", "Contents"))
view.get_selection().select_path(Gtk.TreePath.new_from_string("2"))
scrolled = Gtk.ScrolledWindow()
scrolled.set_policy(Gtk.PolicyType.ALWAYS, Gtk.PolicyType.ALWAYS)
scrolled.set_shadow_type(Gtk.ShadowType.IN)
scrolled.add(view)
page.pack_start(scrolled, True, True, 0)
scale = Gtk.HScale.new_with_range(0, 100, 1)
scale.set_value(38)
scale.set_draw_value(False)
page.pack_start(scale, False, False, 0)
progress = Gtk.ProgressBar()
progress.set_fraction(0.62)
page.pack_start(progress, False, False, 0)
outer.pack_start(Gtk.Label(label="44 folders — GTK2 has no GtkSwitch widget"), False, False, 0)
win.show_all()
entry.grab_focus()


def pump():
    for _ in range(5):
        while Gtk.events_pending():
            Gtk.main_iteration_do(False)
        time.sleep(0.015)


def capture(widget, name):
    temporary = out / "gtk2-own-window.png"
    subprocess.run(["import", "-window", xid, str(temporary)], check=True)
    image = Image.open(temporary).convert("RGBA")
    if widget is not win:
        x, y = widget.translate_coordinates(win, 0, 0)[-2:]
        allocation = widget.get_allocation()
        image = image.crop((x, y, x + allocation.width, y + allocation.height))
    image.save(out / name)
    temporary.unlink()
    return image


def pointer(widget, action):
    x, y = widget.translate_coordinates(win, 0, 0)[-2:]
    allocation = widget.get_allocation()
    subprocess.run(["xdotool", "mousemove", "--window", xid, str(x + allocation.width // 2), str(y + allocation.height // 2), *action], check=True)
    pump()


def verify():
    global xid, failed
    try:
        pump()
        xid = subprocess.check_output(["xdotool", "search", "--onlyvisible", "--name", "^" + title + "$"], text=True).strip().splitlines()[0]
        capture(win, "gtk2-gallery.png")
        capture(entry, "gtk2-entry-focus.png")
        pointer(command, [])
        normal = capture(command, "gtk2-button-normal.png")
        pointer(command, ["mousedown", "1"])
        pressed = capture(command, "gtk2-button-pressed.png")
        changed = sum(a != b for a, b in zip(normal.getdata(), pressed.getdata()))
        assert changed > 10, "Pixmap engine did not draw the native pressed bevel"
        assert normal.getpixel((0, 0)) == pressed.getpixel((0, 0))
        subprocess.run(["xdotool", "mouseup", "1"], check=True)
        pump()
        capture(disabled, "gtk2-button-disabled.png")
        pointer(file_item, ["click", "1"])
        gdk = C.CDLL("libgdk-x11-2.0.so.0")
        drawable_xid = gdk.gdk_x11_drawable_get_xid
        drawable_xid.argtypes = [C.c_void_p]
        drawable_xid.restype = C.c_ulong
        menu_xid = drawable_xid(hash(menu.get_window()))
        subprocess.run(["import", "-window", str(menu_xid), str(out / "gtk2-menu.png")], check=True)
        menu.popdown()
        pump()
        gallery = Image.open(out / "gtk2-gallery.png").convert("RGB")
        colors = {c: sum(p == c for p in gallery.getdata()) for c in ((193, 193, 193), (153, 153, 153), (158, 191, 191), (119, 119, 119), (204, 0, 0), (0, 0, 204))}
        assert all(colors.values()), f"Missing Classic roles/engine indicators: {colors}"
        libgtk = C.CDLL("libgtk-x11-2.0.so.0")
        version = ".".join(str(C.c_uint.in_dll(libgtk, "gtk_" + n + "_version").value) for n in ("major", "minor", "micro"))
        report = {"gtk_version": version, "engine": "external GTK2 pixmap", "fixture_font": args.font,
                  "font": entry.get_pango_context().get_font_description().to_string(),
                  "captures_scope": "own artificial window and own menu only", "native_pressed_pixels_changed": changed,
                  "classic_color_pixels": {str(c): n for c, n in colors.items()}}
        (out / "gtk2-report.json").write_text(json.dumps(report, indent=2) + "\n")
        print(json.dumps(report), flush=True)
    except Exception:
        import traceback
        traceback.print_exc()
        failed = True
    finally:
        Gtk.main_quit()
    return False


failed = False
xid = ""
GLib.timeout_add(400, verify)
Gtk.main()
private.cleanup()
raise SystemExit(1 if failed else 0)
