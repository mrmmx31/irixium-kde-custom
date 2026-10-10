#!/usr/bin/python3
# SPDX-License-Identifier: GPL-3.0-or-later
"""Interactive Gtk3 native widgets; uses the private session's actual theme settings.
No CSS provider, fake widget painting, theme override or font assignment.
"""
import argparse
import json
import os
import sys
from demo_env import require_private_session

parser = argparse.ArgumentParser(description=__doc__)
parser.add_argument("--verificar", action="store_true", help="Check imports only; never initialize GTK or connect to a display")
args = parser.parse_args()
if args.verificar:
    import ctypes as C
    import gi
    assert "3.0" in gi.Repository.get_default().enumerate_versions("Gtk")
    library = C.CDLL("libgtk-3.so.0")
    versions = []
    for kind in ("major", "minor", "micro"):
        function = getattr(library, "gtk_get_" + kind + "_version")
        function.restype = C.c_uint
        function.argtypes = []
        versions.append(function())
    print(json.dumps({"status":"ready", "toolkit":"GTK3", "version":".".join(map(str,versions)), "gui_started":False, "gtk_initialized":False}))
    raise SystemExit(0)
require_private_session()
import gi
gi.require_version("Gtk", "3.0")
from gi.repository import Gtk, Gio

class Demo(Gtk.Application):
    def __init__(self):
        super().__init__(application_id="org.irixclassic.NativeGTK3Demo", flags=Gio.ApplicationFlags.NON_UNIQUE)
        self.connect("activate", self.activate_demo)
        self.clicks = 0

    def activate_demo(self, app):
        settings = Gtk.Settings.get_default()
        self.window = Gtk.ApplicationWindow(application=app, title="NATIVEAPP GTK3 — integrated theme demo PID %d" % os.getpid())
        self.window.set_default_size(850, 620)
        outer = Gtk.Box(orientation=Gtk.Orientation.VERTICAL, spacing=6)
        outer.set_border_width(6)
        self.window.add(outer)
        theme = settings.get_property("gtk-theme-name")
        font = settings.get_property("gtk-font-name")
        label = Gtk.Label(label="REAL Gtk3 widgets | theme: %s | font: %s" % (theme, font))
        label.set_xalign(0)
        outer.pack_start(label, False, False, 0)
        self.status = Gtk.Label(label="Only artificial controls/data; no files or personal applications are opened")
        self.status.set_xalign(0)
        self.menu_bar(outer)
        book = Gtk.Notebook()
        outer.pack_start(book, True, True, 0)
        controls = Gtk.Box(orientation=Gtk.Orientation.VERTICAL, spacing=8)
        controls.set_border_width(8)
        book.append_page(controls, Gtk.Label(label="Native controls"))
        buttons = self.row()
        command = Gtk.Button(label="Press and release")
        command.connect("clicked", self.clicked)
        command.set_tooltip_text("Native GTK3 button: hold the pointer button to inspect its pressed relief")
        toggle = Gtk.ToggleButton(label="Latched toggle")
        toggle.set_active(True)
        unavailable = Gtk.Button(label="Disabled button")
        unavailable.set_sensitive(False)
        for item in (command, toggle, unavailable): buttons.pack_start(item, False, False, 0)
        controls.pack_start(buttons, False, False, 0)
        fields = self.row()
        for caption, editable, sensitive in (("Editable native Gtk.Entry",True,True),("Read only",False,True),("Disabled field",True,False)):
            entry = Gtk.Entry()
            entry.set_text(caption)
            entry.set_editable(editable)
            entry.set_sensitive(sensitive)
            fields.pack_start(entry, True, True, 0)
        controls.pack_start(fields, False, False, 0)
        checks = self.row()
        for caption, active, mixed, enabled in (("Off",False,False,True),("Checked",True,False,True),("Mixed",True,True,True),("Disabled",True,False,False)):
            check = Gtk.CheckButton(label=caption)
            check.set_active(active)
            check.set_inconsistent(mixed)
            check.set_sensitive(enabled)
            check.connect("toggled", lambda widget:self.status.set_text("Native checkbox state changed: " + str(widget.get_active())))
            checks.pack_start(check, False, False, 0)
        radio1 = Gtk.RadioButton.new_with_label_from_widget(None,"Radio A")
        radio2 = Gtk.RadioButton.new_with_label_from_widget(radio1,"Radio B")
        checks.pack_start(radio1,False,False,0)
        checks.pack_start(radio2,False,False,0)
        controls.pack_start(checks,False,False,0)
        switches = self.row()
        switches.pack_start(Gtk.Label(label="Native Gtk.Switch controls:"),False,False,0)
        for active, enabled in ((False,True),(True,True),(True,False)):
            switch = Gtk.Switch()
            switch.set_active(active)
            switch.set_sensitive(enabled)
            switch.connect("notify::active", lambda widget,_p:self.status.set_text("Native switch is " + ("on" if widget.get_active() else "off")))
            switches.pack_start(switch,False,False,0)
        controls.pack_start(switches,False,False,0)
        values = self.row()
        combo = Gtk.ComboBoxText()
        for caption in ("First option","Second option","Third option"): combo.append_text(caption)
        combo.set_active(0)
        spin = Gtk.SpinButton.new_with_range(0,100,1)
        spin.set_value(42)
        scale = Gtk.Scale.new_with_range(Gtk.Orientation.HORIZONTAL,0,100,1)
        scale.set_value(38)
        scale.set_hexpand(True)
        for item in (combo,spin,scale): values.pack_start(item,True,True,0)
        controls.pack_start(values,False,False,0)
        progress = Gtk.ProgressBar()
        progress.set_fraction(.57)
        progress.set_show_text(True)
        progress.set_text("Native progress 57% (static test data)")
        controls.pack_start(progress,False,False,0)
        model = Gtk.ListStore(str,str,str)
        for index in range(1,41): model.append(("Item %02d" % index,"Artificial row, scroll vertically", "Long text used to inspect a native horizontal scrollbar — " * 3))
        view = Gtk.TreeView(model=model)
        for index,caption in enumerate(("Name","Description","Long column")):
            column = Gtk.TreeViewColumn(caption,Gtk.CellRendererText(),text=index)
            column.set_resizable(True)
            view.append_column(column)
        view.get_selection().select_path(Gtk.TreePath.new_from_string("1"))
        scroll = Gtk.ScrolledWindow()
        scroll.set_overlay_scrolling(False)
        scroll.set_policy(Gtk.PolicyType.ALWAYS,Gtk.PolicyType.ALWAYS)
        scroll.add(view)
        controls.pack_start(scroll,True,True,0)
        text = Gtk.TextView()
        text.get_buffer().set_text("Native Gtk.TextView\nSelect/edit text here.\n" + "A sample paragraph with enough text for scrolling.\n" * 50)
        text_scroll = Gtk.ScrolledWindow()
        text_scroll.set_overlay_scrolling(False)
        text_scroll.add(text)
        book.append_page(text_scroll,Gtk.Label(label="Text and scrolling"))
        outer.pack_end(self.status,False,False,0)
        self.window.show_all()
        print(json.dumps({"status":"opened", "toolkit":"GTK3", "pid":os.getpid(), "theme":theme, "font":font, "custom_css":False}),flush=True)

    def row(self): return Gtk.Box(orientation=Gtk.Orientation.HORIZONTAL,spacing=8)
    def clicked(self,_widget):
        self.clicks += 1
        self.status.set_text("Native clicked signal received %d time(s)" % self.clicks)

    def menu_bar(self,outer):
        bar = Gtk.MenuBar()
        root = Gtk.MenuItem(label="Native Menu")
        menu = Gtk.Menu()
        item = Gtk.MenuItem(label="Record native menu activation")
        item.connect("activate",lambda _item:self.status.set_text("Native Gtk.MenuItem activate signal received"))
        menu.append(item)
        disabled = Gtk.MenuItem(label="Unavailable menu action")
        disabled.set_sensitive(False)
        menu.append(disabled)
        menu.append(Gtk.SeparatorMenuItem())
        checked = Gtk.CheckMenuItem(label="Checkable menu item")
        checked.set_active(True)
        menu.append(checked)
        submenu_item = Gtk.MenuItem(label="Native submenu")
        submenu = Gtk.Menu()
        for caption in ("Submenu A","Submenu B"):
            action = Gtk.MenuItem(label=caption)
            action.connect("activate",lambda item:self.status.set_text("Activated " + item.get_label()))
            submenu.append(action)
        submenu_item.set_submenu(submenu)
        menu.append(submenu_item)
        quit_item = Gtk.MenuItem(label="Close only this demo")
        quit_item.connect("activate",lambda _item:self.quit())
        menu.append(quit_item)
        root.set_submenu(menu)
        bar.append(root)
        outer.pack_start(bar,False,False,0)

raise SystemExit(Demo().run([sys.argv[0]]))
