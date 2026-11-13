#!/usr/bin/python3
# SPDX-FileCopyrightText: 2026 mrmmx31
# SPDX-License-Identifier: GPL-3.0-or-later
"""Read installed KHolidays region metadata in an already isolated test HOME."""
import argparse
import json
import os
from pathlib import Path
from PyQt6.QtCore import QUrl
from PyQt6.QtGui import QGuiApplication
from PyQt6.QtQml import QQmlEngine, QQmlComponent

parser = argparse.ArgumentParser(description=__doc__)
parser.add_argument('--region', required=True)
parser.add_argument('--saida', type=Path, required=True)
args = parser.parse_args()
if os.environ.get('IRIX_DOMAINOS_AGENDA_PRIVATE_SESSION') != '1':
    raise SystemExit('Requires private test HOME/XDG paths')
if args.saida.exists():
    raise SystemExit('Do not overwrite evidence')

app = QGuiApplication([])
engine = QQmlEngine()
warnings = []
engine.warnings.connect(lambda values: warnings.extend(e.toString() for e in values))
component = QQmlComponent(engine)
component.setData(b'''import QtQuick
import QtQuick.Window
import org.kde.kholidays as KHolidays
Window {
    id: root
    width: 1; height: 1; visible: true
    property string metadataJson: "[]"
    readonly property int regionCount: regions.count
    function collect() {
        let rows = [];
        for (let i = 0; i < regions.count; ++i) {
            const item = regions.itemAt(i);
            if (item) rows.push({region:item.region, name:item.name, description:item.description});
        }
        metadataJson = JSON.stringify(rows);
    }
    Repeater {
        id: regions
        model: KHolidays.HolidayRegionsModel {}
        delegate: Item {
            required property string region
            required property string name
            required property string description
        }
    }
    Component.onCompleted: Qt.callLater(collect)
}''', QUrl('file:///private-holiday-region-metadata.qml'))
window = component.create()
if window is None:
    raise SystemExit('; '.join(e.toString() for e in component.errors()))
app.processEvents()
rows = json.loads(window.property('metadataJson'))
matched = [r for r in rows if r['region'] == args.region]
checks = {
    'all_native_model_rows_read': len(rows) == window.property('regionCount') and len(rows) > 0,
    'public_regional_code_discovered_exactly_once': len(matched) == 1,
    'regional_display_name_and_description_identify_2026': len(matched) == 1 and '2026' in matched[0]['name'] and '2026' in matched[0]['description'],
    'qml_metadata_warnings_zero': not warnings,
}
report = {'status': 'passed' if all(checks.values()) else 'failed', 'checks': checks,
          'region_count': len(rows), 'matched_region': matched, 'qml_warnings': warnings,
          'scope': 'Installed KHolidays model with copied public Plan2 file in private XDG_DATA_HOME; no event/account/content source.'}
args.saida.write_text(json.dumps(report, indent=2, ensure_ascii=False) + '\n')
window.close()
raise SystemExit(0 if report['status'] == 'passed' else 1)
