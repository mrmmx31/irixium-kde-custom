#!/usr/bin/env python3
# SPDX-FileCopyrightText: 2026 mrmmx31
# SPDX-License-Identifier: GPL-3.0-or-later
"""Native GTK4 gallery without a GIR dependency, using GTK's stable C ABI.

Run under Xvfb. Only this process receives the theme override; all PNG captures
are restricted to its artificial window or its own native popup surface.
Requires libgtk-4, xdotool, ImageMagick's import and Pillow, not GTK4 Python GI.
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
data = tempfile.TemporaryDirectory(prefix="irixclassic-gtk4-", dir="/tmp")
themes = Path(data.name) / "themes"
themes.mkdir()
(themes / "IrixClassic").symlink_to(ROOT / "gtk" / "IrixClassic", target_is_directory=True)
os.environ["XDG_DATA_HOME"] = data.name
os.environ["XDG_CONFIG_HOME"] = str(Path(data.name) / "config")
os.environ["GTK_THEME"] = "IrixClassic"
os.environ["GDK_BACKEND"] = "x11"
os.environ["GSK_RENDERER"] = "cairo"
os.environ["GTK_A11Y"] = "none"
from PIL import Image

gtk = C.CDLL("libgtk-4.so.1")
glib = C.CDLL("libglib-2.0.so.0")
obj = C.CDLL("libgobject-2.0.so.0")
gio = C.CDLL("libgio-2.0.so.0")
P, I, S, D = C.c_void_p, C.c_int, C.c_char_p, C.c_double


def bind(lib, name, result, *params):
    fn = getattr(lib, name)
    fn.restype = result
    fn.argtypes = list(params)
    return fn


def api(name, result=P, *params):
    return bind(gtk, name, result, *params)


init = api("gtk_init", None)
init()
settings = api("gtk_settings_get_default")()
settings_set = bind(obj, "g_object_set", None, P, S, S, P)
settings_set(settings, b"gtk-theme-name", b"IrixClassic", None)
settings_set(settings, b"gtk-font-name", args.font.encode(), None)
css_new = api("gtk_css_provider_new")
css_load = api("gtk_css_provider_load_from_path", None, P, S)
css_add = api("gtk_style_context_add_provider_for_display", None, P, P, C.c_uint)
display = api("gdk_display_get_default")()
provider = css_new()
errors = []


class GError(C.Structure):
    _fields_ = [("domain", C.c_uint), ("code", I), ("message", S)]


ERR_CB = C.CFUNCTYPE(None, P, P, P, P)


@ERR_CB
def css_error(_provider, _section, error, _data):
    errors.append(C.cast(error, C.POINTER(GError)).contents.message.decode())


signal_connect = bind(obj, "g_signal_connect_data", C.c_ulong, P, S, P, P, P, C.c_uint)
signal_connect(provider, b"parsing-error", C.cast(css_error, P), None, None, 0)
css_load(provider, os.fsencode(ROOT / "gtk" / "IrixClassic" / "gtk-4.0" / "gtk.css"))
css_add(display, provider, 600)
window_new = api("gtk_window_new")
window_size = api("gtk_window_set_default_size", None, P, I, I)
window_title = api("gtk_window_set_title", None, P, S)
window_decorated = api("gtk_window_set_decorated", None, P, I)
window_child = api("gtk_window_set_child", None, P, P)
present = api("gtk_window_present", None, P)
destroy = api("gtk_window_destroy", None, P)
box_new = api("gtk_box_new", P, I, I)
append = api("gtk_box_append", None, P, P)
label_new = api("gtk_label_new", P, S)
label_xalign = api("gtk_label_set_xalign", None, P, C.c_float)
button_new = api("gtk_button_new_with_label", P, S)
toggle_new = api("gtk_toggle_button_new_with_label", P, S)
toggle_active = api("gtk_toggle_button_set_active", None, P, I)
sensitive = api("gtk_widget_set_sensitive", None, P, I)
size = api("gtk_widget_set_size_request", None, P, I, I)
expand = api("gtk_widget_set_hexpand", None, P, I)
vexpand = api("gtk_widget_set_vexpand", None, P, I)
addclass = api("gtk_widget_add_css_class", None, P, S)
margin_functions = [api("gtk_widget_set_margin_" + side, None, P, I) for side in ("top", "bottom", "start", "end")]
entry_new = api("gtk_entry_new")
editable_text = api("gtk_editable_set_text", None, P, S)
editable_set = api("gtk_editable_set_editable", None, P, I)
check_new = api("gtk_check_button_new_with_label", P, S)
check_active = api("gtk_check_button_set_active", None, P, I)
check_mixed = api("gtk_check_button_set_inconsistent", None, P, I)
check_group = api("gtk_check_button_set_group", None, P, P)
switch_new = api("gtk_switch_new")
switch_active = api("gtk_switch_set_active", None, P, I)
dropdown_new = api("gtk_drop_down_new_from_strings", P, C.POINTER(S))
spin_new = api("gtk_spin_button_new_with_range", P, D, D, D)
spin_value = api("gtk_spin_button_set_value", None, P, D)
notebook_new = api("gtk_notebook_new")
notebook_append = api("gtk_notebook_append_page", I, P, P, P)
list_new = api("gtk_list_box_new")
list_append = api("gtk_list_box_append", None, P, P)
list_row = api("gtk_list_box_get_row_at_index", P, P, I)
list_select = api("gtk_list_box_select_row", None, P, P)
scrolled_new = api("gtk_scrolled_window_new")
scrolled_child = api("gtk_scrolled_window_set_child", None, P, P)
scrolled_policy = api("gtk_scrolled_window_set_policy", None, P, I, I)
scrolled_overlay = api("gtk_scrolled_window_set_overlay_scrolling", None, P, I)
scrolled_frame = api("gtk_scrolled_window_set_has_frame", None, P, I)
scale_new = api("gtk_scale_new_with_range", P, I, D, D, D)
range_value = api("gtk_range_set_value", None, P, D)
scale_value = api("gtk_scale_set_draw_value", None, P, I)
progress_new = api("gtk_progress_bar_new")
progress_fraction = api("gtk_progress_bar_set_fraction", None, P, D)
focus = api("gtk_widget_grab_focus", I, P)
states = api("gtk_widget_get_state_flags", C.c_uint, P)
native_get = api("gtk_widget_get_native", P, P)
surface_get = api("gtk_native_get_surface", P, P)
xid_get = api("gdk_x11_surface_get_xid", C.c_ulong, P)
surface_width = api("gdk_surface_get_width", I, P)
surface_height = api("gdk_surface_get_height", I, P)
first_child = api("gtk_widget_get_first_child", P, P)
next_child = api("gtk_widget_get_next_sibling", P, P)
type_name = bind(obj, "g_type_name_from_instance", S, P)
iterate = bind(glib, "g_main_context_iteration", I, P, I)


class Rect(C.Structure):
    _fields_ = [("x", C.c_float), ("y", C.c_float), ("width", C.c_float), ("height", C.c_float)]


bounds = api("gtk_widget_compute_bounds", I, P, P, C.POINTER(Rect))


def label(caption):
    result = label_new(caption.encode())
    label_xalign(result, 0)
    return result


def row(*widgets):
    result = box_new(0, 3)
    for widget in widgets:
        append(result, widget)
    return result


win = window_new()
window_title(win, f"IrixClassic GTK4 proof {os.getpid()}".encode())
window_size(win, 940, 650)
window_decorated(win, 0)
outer = box_new(1, 3)
for fn in margin_functions:
    fn(outer, 3)
window_child(win, outer)
append(outer, label("IRIX CLASSIC — native GTK 4 controls"))

# Real GMenu models and actions keep popup/check/submenu behavior native.
gmenu_new = bind(gio, "g_menu_new", P)
gmenu_append = bind(gio, "g_menu_append", None, P, S, S)
gmenu_sub = bind(gio, "g_menu_append_submenu", None, P, S, P)
gmenu_section = bind(gio, "g_menu_append_section", None, P, S, P)
action_group_new = bind(gio, "g_simple_action_group_new", P)
action_new = bind(gio, "g_simple_action_new", P, S, P)
action_add = bind(gio, "g_action_map_add_action", None, P, P)
action_enabled = bind(gio, "g_simple_action_set_enabled", None, P, I)
variant_bool = bind(glib, "g_variant_new_boolean", P, I)
action_stateful = bind(gio, "g_simple_action_new_stateful", P, S, P, P)
action_insert = api("gtk_widget_insert_action_group", None, P, S, P)
group = action_group_new()
for caption in ("open", "save", "unavailable", "compact", "detailed"):
    action = action_new(caption.encode(), None)
    action_add(group, action)
    if caption == "unavailable":
        action_enabled(action, 0)
hidden = action_stateful(b"hidden", None, variant_bool(1))
action_add(group, hidden)
action_insert(win, b"demo", group)
menumodel = gmenu_new()
filemodel = gmenu_new()
for caption, name in (("Open folder", "open"), ("Save selection", "save"), ("Unavailable command", "unavailable")):
    gmenu_append(filemodel, caption.encode(), ("demo." + name).encode())
section = gmenu_new()
gmenu_append(section, b"Show hidden files", b"demo.hidden")
options = gmenu_new()
gmenu_append(options, b"Compact list", b"demo.compact")
gmenu_append(options, b"Detailed list", b"demo.detailed")
gmenu_sub(section, b"Options", options)
gmenu_section(filemodel, None, section)
gmenu_sub(menumodel, b"File", filemodel)
for caption in ("Edit", "View", "Help"):
    gmenu_sub(menumodel, caption.encode(), options)
menubar = api("gtk_popover_menu_bar_new_from_model", P, P)(menumodel)
append(outer, menubar)

body = box_new(0, 3)
append(outer, body)
vexpand(body, 1)
sidebar = list_new()
size(sidebar, 165, -1)
addclass(sidebar, b"sidebar")
for caption in ("Home", "Documents", "Pictures", "Applications", "Devices", "Network"):
    list_append(sidebar, label(caption))
list_select(sidebar, list_row(sidebar, 1))
append(body, sidebar)
book = notebook_new()
expand(book, 1)
append(body, book)
page = box_new(1, 3)
for fn in margin_functions:
    fn(page, 3)
notebook_append(book, page, label("Controls"))
notebook_append(book, label("Native notebook page"), label("Folders"))
command = button_new(b"Apply")
default = button_new(b"Default")
addclass(default, b"default")
toggle = toggle_new(b"Latched")
toggle_active(toggle, 1)
disabled = button_new(b"Unavailable")
sensitive(disabled, 0)
append(page, row(command, default, toggle, disabled))
entry = entry_new()
editable_text(entry, b"/home/classic/Documents")
readonly = entry_new()
editable_text(readonly, b"Read only")
editable_set(readonly, 0)
unavailable = entry_new()
editable_text(unavailable, b"Unavailable field")
sensitive(unavailable, 0)
append(page, row(label("Folder"), entry, readonly, unavailable))
checks = row()
for caption, active, mixed, enabled in (("Option", 0, 0, 1), ("Checked", 1, 0, 1), ("Mixed", 1, 1, 1), ("Unavailable", 1, 0, 0)):
    check = check_new(caption.encode())
    check_active(check, active)
    check_mixed(check, mixed)
    sensitive(check, enabled)
    append(checks, check)
append(page, checks)
radio = check_new(b"List")
check_active(radio, 1)
radio2 = check_new(b"Icons")
check_group(radio2, radio)
radios = row(radio, radio2)
for active, enabled in ((0, 1), (1, 1), (1, 0)):
    switch = switch_new()
    switch_active(switch, active)
    sensitive(switch, enabled)
    append(radios, switch)
append(page, radios)
options_text = (S * 4)(b"Compact list", b"Detailed list", b"Icon grid", None)
dropdown = dropdown_new(options_text)
spin = spin_new(0, 100, 1)
spin_value(spin, 42)
append(page, row(dropdown, spin, button_new(b"Toolbar action")))
header = row(button_new(b"Name"), button_new(b"Type"), button_new(b"Contents"))
for child in (first_child(header),):
    size(child, 220, -1)
append(page, header)
listing = list_new()
size(listing, 1000, -1)
for i in range(1, 45):
    item = row(label(f"Folder {i:02d}"), label("Directory"), label("12 items"))
    size(first_child(item), 220, -1)
    list_append(listing, item)
list_select(listing, list_row(listing, 2))
scrolled = scrolled_new()
scrolled_child(scrolled, listing)
scrolled_policy(scrolled, 0, 0)
scrolled_overlay(scrolled, 0)
scrolled_frame(scrolled, 1)
vexpand(scrolled, 1)
append(page, scrolled)
scale = scale_new(0, 0, 100, 1)
range_value(scale, 38)
scale_value(scale, 0)
append(page, scale)
progress = progress_new()
progress_fraction(progress, 0.62)
append(page, progress)
append(outer, label("44 folders — drawing and input belong to GTK"))
present(win)
focus(entry)


def pump(duration=0.15):
    until = time.monotonic() + duration
    while time.monotonic() < until:
        while iterate(None, 0):
            pass
        time.sleep(0.005)


def own_surface(widget):
    return surface_get(native_get(widget))


def capture(widget, name, whole=False):
    surface = own_surface(widget)
    xid = xid_get(surface)
    temporary = out / "gtk4-own-surface.png"
    subprocess.run(["import", "-window", str(xid), str(temporary)], check=True)
    pixels = Image.open(temporary).convert("RGBA")
    if not whole:
        rect = Rect()
        assert bounds(widget, win, C.byref(rect))
        x, y, width, height = round(rect.x), round(rect.y), round(rect.width), round(rect.height)
        pixels = pixels.crop((x, y, x + width, y + height))
    pixels.save(out / name)
    temporary.unlink()
    return pixels


def pointer(widget, action):
    rect = Rect()
    assert bounds(widget, win, C.byref(rect))
    x, y = round(rect.x + rect.width / 2), round(rect.y + rect.height / 2)
    subprocess.run(["xdotool", "mousemove", "--window", str(xid_get(own_surface(win))), str(x), str(y), *action], check=True)
    pump()


def walk(widget):
    yield widget
    child = first_child(widget)
    while child:
        yield from walk(child)
        child = next_child(child)


try:
    pump(0.4)
    assert not errors, errors
    capture(win, "gtk4-gallery.png", whole=True)
    capture(entry, "gtk4-entry-focus.png")
    pointer(command, [])
    normal = capture(command, "gtk4-button-normal.png")
    pointer(command, ["mousedown", "1"])
    pressed = capture(command, "gtk4-button-pressed.png")
    assert states(command) & 1, "Native button did not enter GTK_STATE_FLAG_ACTIVE"
    changed = sum(a != b for a, b in zip(normal.getdata(), pressed.getdata()))
    assert changed > 10, "Pressed bevel did not change"
    assert normal.getpixel((0, 0)) == pressed.getpixel((0, 0)), "Pressed state moved the outer contour"
    subprocess.run(["xdotool", "mouseup", "1"], check=True)
    pump()
    capture(disabled, "gtk4-button-disabled.png")
    pointer(first_child(menubar), ["click", "1"])
    popovers = [w for w in walk(menubar) if type_name(w) == b"GtkPopoverMenu"]
    popup = next(w for w in popovers if own_surface(w) != own_surface(win))
    capture(popup, "gtk4-menu.png", whole=True)
    assert not errors, errors
    gallery = Image.open(out / "gtk4-gallery.png").convert("RGB")
    colors = {c: sum(p == c for p in gallery.getdata()) for c in ((193, 193, 193), (153, 153, 153), (158, 191, 191), (119, 119, 119), (204, 0, 0), (0, 0, 204))}
    assert all(colors.values()), f"Missing Classic color roles: {colors}"
    version = ".".join(str(api("gtk_get_" + n + "_version", C.c_uint)()) for n in ("major", "minor", "micro"))
    report = {"gtk_version": version, "css_diagnostics": errors, "theme_override": "IrixClassic", "fixture_font": args.font,
              "binding": "native GTK4 C ABI via ctypes; GTK4 GIR unavailable on this host",
              "captures_scope": "own artificial window and own popup surface only",
              "native_pressed_pixels_changed": changed,
              "classic_color_pixels": {str(c): n for c, n in colors.items()}}
    pango = C.CDLL("libpango-1.0.so.0")
    context = api("gtk_widget_get_pango_context", P, P)(entry)
    description = bind(pango, "pango_context_get_font_description", P, P)(context)
    report["font"] = bind(pango, "pango_font_description_to_string", S, P)(description).decode()
    theme_name = S()
    bind(obj, "g_object_get", None, P, S, P, P)(settings, b"gtk-theme-name", C.byref(theme_name), None)
    report["theme_name"] = theme_name.value.decode()
    assert report["theme_name"] == "IrixClassic", report
    (out / "gtk4-report.json").write_text(json.dumps(report, indent=2) + "\n")
    print(json.dumps(report), flush=True)
finally:
    destroy(win)
    pump(0.05)
    data.cleanup()
