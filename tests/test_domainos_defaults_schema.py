"""Keep the all-categories edit buffer complete when the schema grows."""
from pathlib import Path
import re
import unittest
import xml.etree.ElementTree as ET


APPLET = Path(__file__).resolve().parents[1] / "plasma/applets/org.irixclassic.domainos.panel"


class DomainOSDefaultsSchemaTests(unittest.TestCase):
    def test_general_reset_covers_every_schema_entry(self):
        entries = ET.parse(APPLET / "contents/config/main.xml").findall(".//{*}entry")
        keys = {entry.attrib["name"] for entry in entries}
        page = (APPLET / "contents/ui/ConfigDefaults.qml").read_text()
        declarations = re.findall(r"property\s+var\s+cfg_(\w+)\s*:", page)
        self.assertEqual(set(declarations), keys)
        self.assertEqual(len(declarations), len(keys))

    def test_general_page_is_selectable(self):
        model = (APPLET / "contents/config/config.qml").read_text()
        self.assertIn('source: "ConfigDefaults.qml"', model)


if __name__ == "__main__":
    unittest.main()
