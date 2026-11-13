#!/usr/bin/env python3
# SPDX-FileCopyrightText: 2026 IRIX Classic contributors
# SPDX-License-Identifier: GPL-3.0-or-later
"""Test category reset isolation/atomicity using the production Qt JS helper."""
import json
from pathlib import Path
import re
import unittest
import xml.etree.ElementTree as ET

from PyQt6.QtCore import QCoreApplication
from PyQt6.QtQml import QJSEngine

APPLET = Path(__file__).resolve().parents[1] / "applets/org.irixclassic.domainos.panel"
UI = APPLET / "contents/ui"
PAGES = ("Activity", "Applications", "Commands", "Iconbox", "Instruments", "Monitor", "Pager", "Tray")


class CategoryDefaults(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.app = QCoreApplication.instance() or QCoreApplication([])
        cls.engine = QJSEngine()
        source = (UI / "ConfigUtils.js").read_text().replace(".pragma library", "")
        result = cls.engine.evaluate(source)
        if result.isError():
            raise RuntimeError(result.toString())
        cls.entries = ET.parse(APPLET / "contents/config/main.xml").getroot().findall("{*}group/{*}entry")
        cls.defaults = {}
        for entry in cls.entries:
            name, kind = entry.attrib["name"], entry.attrib["type"]
            raw = entry.find("{*}default").text or ""
            cls.defaults[name] = raw == "true" if kind == "Bool" else int(raw) if kind in ("Int", "Enum") else raw.split(",") if kind == "StringList" and raw else [] if kind == "StringList" else raw

    def evaluate(self, source):
        result = self.engine.evaluate("(function(){" + source + "})()")
        self.assertFalse(result.isError(), result.toString())
        return result.toVariant()

    def test_every_category_has_an_instance_local_reset_footer(self):
        for name in PAGES:
            source = (UI / ("Config" + name + ".qml")).read_text()
            self.assertIn("footer: DomainOSCategoryDefaults", source, name)
            self.assertIn("configuration: Plasmoid.configuration", source, name)
            self.assertIn("targetPage: page", source, name)
            self.assertNotIn("writeConfig()", source, name)

    def test_every_category_resets_exactly_its_schema_properties(self):
        settings = {name: "saved sentinel" for name in self.defaults}
        settings.update({name + "Default": value for name, value in self.defaults.items()})
        for name in PAGES:
            keys = re.findall(r"property\s+(?:alias|var|string|bool)\s+cfg_(\w+)\s*:", (UI / ("Config" + name + ".qml")).read_text())
            page = {"cfg_" + key: "edited sentinel" for key in keys}
            result = self.evaluate("const settings=" + json.dumps(settings) + ";settings.keys=()=>Object.keys(settings).filter(key=>key!=='keys');"
                                   "const page=" + json.dumps(page) + ";const before=JSON.stringify(settings);"
                                   "const reset=resetCategory(page,settings);return {reset,page,unchanged:before===JSON.stringify(settings)};")
            self.assertTrue(result["reset"]["ok"], name)
            self.assertEqual(set(result["reset"]["keys"]), set(keys), name)
            self.assertEqual(result["page"], {"cfg_" + key: self.defaults[key] for key in keys}, name)
            self.assertTrue(result["unchanged"], name)

    def test_global_reset_covers_schema_and_disables_opt_in_mail_without_saving(self):
        keys = re.findall(r"property\s+(?:alias|var|string|bool)\s+cfg_(\w+)\s*:", (UI / "ConfigDefaults.qml").read_text())
        self.assertEqual(set(keys), set(self.defaults), "Global reset must include every schema setting")
        settings = {name: "saved sentinel" for name in self.defaults}
        settings["mailCountsEnabled"] = True
        settings.update({name + "Default": value for name, value in self.defaults.items()})
        page = {"cfg_" + name: "edited sentinel" for name in keys}
        page["cfg_mailCountsEnabled"] = True
        result = self.evaluate("const settings=" + json.dumps(settings) + ";settings.keys=()=>Object.keys(settings).filter(key=>key!=='keys');"
            "const page=" + json.dumps(page) + ";const before=JSON.stringify(settings);"
            "const reset=resetCategory(page,settings);return {reset,page,unchanged:before===JSON.stringify(settings),savedMail:settings.mailCountsEnabled};")
        self.assertTrue(result["reset"]["ok"])
        self.assertEqual(set(result["reset"]["keys"]), set(self.defaults))
        self.assertEqual(result["page"], {"cfg_" + name: value for name, value in self.defaults.items()})
        self.assertFalse(result["page"]["cfg_mailCountsEnabled"])
        self.assertTrue(result["savedMail"])
        self.assertTrue(result["unchanged"])

    def test_changed_native_defaults_win_over_initial_control_values(self):
        result = self.evaluate("const settings={number:1,numberDefault:37,flag:false,flagDefault:true,text:'old',textDefault:'native schema value',list:[],listDefault:['A','B']};"
                               "settings.keys=()=>Object.keys(settings).filter(key=>key!=='keys');"
                               "const page={cfg_number:9,cfg_flag:false,cfg_text:'initial UI value',cfg_list:['old']};"
                               "const reset=resetCategory(page,settings);return {reset,page};")
        self.assertTrue(result["reset"]["ok"])
        self.assertEqual(result["page"], {"cfg_number": 37, "cfg_flag": True, "cfg_text": "native schema value", "cfg_list": ["A", "B"]})

    def test_missing_default_prevents_every_partial_edit(self):
        result = self.evaluate("const settings={first:5,firstDefault:0,second:6};settings.keys=()=>['first','firstDefault','second'];"
                               "const page={cfg_first:11,cfg_second:12};const reset=resetCategory(page,settings);return {reset,page};")
        self.assertFalse(result["reset"]["ok"])
        self.assertEqual(result["reset"]["missing"], ["second"])
        self.assertEqual(result["page"], {"cfg_first": 11, "cfg_second": 12})

    def test_list_mutation_never_changes_defaults_or_another_instance(self):
        result = self.evaluate("const settings={items:['saved'],itemsDefault:['schema']};settings.keys=()=>['items','itemsDefault'];"
                               "const first={cfg_items:['edit']},second={cfg_items:['other']};"
                               "resetCategory(first,settings);first.cfg_items.push('new edit');return {first,second,settings};")
        self.assertEqual(result["first"]["cfg_items"], ["schema", "new edit"])
        self.assertEqual(result["second"]["cfg_items"], ["other"])
        self.assertEqual(result["settings"]["items"], ["saved"])
        self.assertEqual(result["settings"]["itemsDefault"], ["schema"])

    def test_unavailable_native_map_does_not_change_edits(self):
        result = self.evaluate("const page={cfg_enabled:true};return {reset:resetCategory(page,null),page};")
        self.assertFalse(result["reset"]["ok"])
        self.assertEqual(result["page"], {"cfg_enabled": True})


if __name__ == "__main__":
    unittest.main()
