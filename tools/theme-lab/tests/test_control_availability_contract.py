#!/usr/bin/python3
# SPDX-License-Identifier: GPL-3.0-or-later
"""Cross-check the canonical C control IDs, Motif form and GTK2 capturer.

The test does not initialize a GUI.  It compiles a small read-only C probe so
the identifiers come from tl_control_ids instead of a second Python list.
"""
import os
from pathlib import Path
import re
import subprocess
import sys
import tempfile
import unittest


THEME_LAB = Path(__file__).resolve().parents[1]
ROOT = THEME_LAB.parents[1]
sys.path.insert(0, str(THEME_LAB))

import preview_gtk2
from native_scene_gtk2 import scene_records
from scene_contract import CONTROLS


FORM_LABELS = (
    "Botão", "Botão alternável", "Caixa de seleção", "Botão de opção",
    "Entrada de texto", "ComboBox", "SpinBox", "Texto multilinha",
    "Escala horizontal", "Escala vertical", "Rolagem horizontal",
    "Rolagem vertical", "Botão de seta", "Progresso / nível", "Lista", "Moldura",
)


def build_probe(directory):
    output = Path(directory) / "control-availability-probe"
    json_flags = subprocess.check_output(
        ["pkg-config", "--cflags", "--libs", "json-c"], text=True
    ).split()
    command = [
        os.environ.get("CC", "cc"), "-std=c99", "-Wall", "-Wextra", "-Werror",
        "-I", str(THEME_LAB / "include"),
        str(THEME_LAB / "tests/control_availability_probe.c"),
        str(THEME_LAB / "src/model/control_availability.c"),
        str(THEME_LAB / "src/model.c"),
        str(THEME_LAB / "src/model/scrollbar_parts.c"),
        str(THEME_LAB / "src/model/part_states.c"),
        str(THEME_LAB / "src/model/control_dimensions.c"),
        "-lm", *json_flags, "-o", str(output),
    ]
    subprocess.run(command, cwd=ROOT, check=True)
    return output


def probe_rows(executable):
    result = subprocess.run([str(executable)], check=True, text=True,
                            stdout=subprocess.PIPE)
    rows = []
    for line in result.stdout.splitlines():
        index, identifier, motif, gtk2, program, option, argument = line.split("\t")
        rows.append({"index": int(index), "id": identifier,
                     "motif_available": int(motif),
                     "gtk2_available": int(gtk2), "program": program,
                     "option": option, "argument": int(argument)})
    return rows


def gtk2_project():
    count = len(CONTROLS)
    return {"recipes": {"gtk2": {
        "visible_categories": 31,
        "visible_controls": (1 << count) - 1,
        "selected_control": 0,
        "edit_state": 0,
        "positions": [[16 + (i % 4) * 160, 16 + (i // 4) * 80]
                      for i in range(count)],
        "sizes": [[0, 0] for _ in range(count)],
        "length_anchor": [0 for _ in range(count)],
    }}}


class ControlAvailabilityContractTest(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        temp_root = os.environ.get("TMPDIR")
        if not temp_root or not Path(temp_root).resolve().is_relative_to(
                (Path.home() / "tempia").resolve()):
            raise RuntimeError("Defina TMPDIR dentro de ~/tempia para este teste.")
        cls.temporary = tempfile.TemporaryDirectory(
            prefix="theme-lab-control-contract-", dir=temp_root)
        cls.rows = probe_rows(build_probe(cls.temporary.name))

    @classmethod
    def tearDownClass(cls):
        cls.temporary.cleanup()

    def test_c_api_borrows_all_model_ids_once_in_model_order(self):
        self.assertEqual(len(self.rows), len(CONTROLS))
        self.assertEqual([row["index"] for row in self.rows],
                         list(range(len(self.rows))))
        self.assertEqual([row["id"] for row in self.rows], list(CONTROLS))
        self.assertEqual(len({row["id"] for row in self.rows}), len(self.rows))

    def test_main_form_keeps_the_same_sixteen_index_slots(self):
        source = (THEME_LAB / "src/view.c").read_text(encoding="utf-8")
        labels_match = re.search(
            r"control_labels\[TL_CONTROL_COUNT\]\s*=\s*\{(.*?)\};",
            source, re.DOTALL)
        self.assertIsNotNone(labels_match)
        labels = tuple(re.findall(r'"([^"\\]*(?:\\.[^"\\]*)*)"',
                                  labels_match.group(1)))
        self.assertEqual(labels, FORM_LABELS)
        self.assertRegex(source,
                         r"tl_catalog_create\([^;]*control_labels\s*,\s*control_category")
        creator = re.search(
            r"static void motif_controls_create\(.*?^\}", source,
            re.DOTALL | re.MULTILINE)
        self.assertIsNotNone(creator)
        assigned = {int(value) for value in
                    re.findall(r"widgets\[(\d+)\]\s*=", creator.group(0))}
        self.assertEqual(assigned, set(range(len(self.rows))))
        self.assertTrue(all(row["motif_available"] == 1 for row in self.rows))

    def test_every_model_id_reaches_the_matching_gtk2_capture_route(self):
        base = gtk2_project()
        for row in self.rows:
            with self.subTest(control=row["id"]):
                self.assertEqual(row["program"], "preview_gtk2.py")
                self.assertEqual(row["option"], "--capture-control")
                self.assertEqual(row["argument"], row["index"])
                self.assertEqual(row["gtk2_available"], 1)
                candidate = preview_gtk2.private_capture_model(
                    base, row["argument"],
                    {"length_px": 0, "thickness_px": 0, "value": 25,
                     "page_size": 25, "part": "whole", "direction": "auto"})
                records = scene_records(candidate)
                self.assertEqual([(item["index"], item["id"])
                                  for item in records],
                                 [(row["index"], row["id"])])


if __name__ == "__main__":
    unittest.main()
