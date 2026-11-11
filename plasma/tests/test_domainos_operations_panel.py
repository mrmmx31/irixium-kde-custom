#!/usr/bin/env python3
"""P04 prototype smoke test; offscreen is not proof of the live lsi panel."""
import json
import unittest
import test_domainos_middle_click as setup
from PyQt6.QtQml import QQmlApplicationEngine
from PyQt6.QtCore import QUrl
from PyQt6.QtWidgets import QApplication
from PyQt6.QtTest import QTest


class OperationsPanel(unittest.TestCase):
    def test_native_dialog_loads_and_measures_before_show(self):
        app=QApplication.instance() or QApplication([])
        engine=QQmlApplicationEngine(); warnings=[]
        engine.warnings.connect(lambda rows:warnings.extend(row.toString() for row in rows))
        fixture=setup.Path(setup._private.name)/'operations-panel.qml'
        fixture.write_text('''import QtQuick
import "'''+(setup.ROOT/'plasma/tests').as_uri()+'''"
import "'''+(setup.ROOT/'plasma/applets/org.irixclassic.domainos.panel/contents/ui').as_uri()+'''" as UI
DomainOSIconboxPreview {
 id:fixture
 property var commands: []
 property var candidate: UI.DomainOSOperationsPanel {
  iconbox:fixture.iconbox
  onCommandRequested: command => fixture.commands=fixture.commands.concat([command])
 }
 function reset() { resetUi(); addGeometryBackend() }
 function prepare() {
  iconbox.menuSelection=[controller.resolveWindow("window:1").record,controller.resolveWindow("window:3").record]
  return candidate.prepareForAnchor(iconbox)
 }
 function snapshot() {
  return JSON.stringify({width:candidate.preferredWidth,height:candidate.preferredHeight,
    limit:candidate.heightLimit,count:candidate.count,visible:candidate.visible,
    error:candidate.lastError})
 }
}
''')
        engine.load(QUrl.fromLocalFile(str(fixture)))
        self.assertTrue(engine.rootObjects(), '\n'.join(warnings))
        engine.globalObject().setProperty('fixture',engine.newQObject(engine.rootObjects()[0]))
        engine.evaluate('fixture.reset()');app.processEvents();QTest.qWait(50);app.processEvents()
        result=engine.evaluate('fixture.prepare()')
        self.assertFalse(result.isError(),result.toString());self.assertTrue(result.toBool(),engine.evaluate("fixture.snapshot()").toString())
        result=engine.evaluate('fixture.snapshot()');self.assertFalse(result.isError(),result.toString())
        state=json.loads(result.toString())
        self.assertEqual(state['count'],11);self.assertGreater(state['width'],100)
        self.assertGreater(state['height'],100);self.assertFalse(state['visible'])
        self.assertEqual(state['error'],'')
        result=engine.evaluate('fixture.candidate.openAt(fixture.iconbox)')
        self.assertFalse(result.isError(),result.toString());self.assertTrue(result.toBool())
        app.processEvents();QTest.qWait(20);app.processEvents()
        state=json.loads(engine.evaluate('fixture.snapshot()').toString())
        self.assertTrue(state['visible'])
        result=engine.evaluate('fixture.candidate.invoke("restore")')
        self.assertFalse(result.isError(),result.toString());self.assertTrue(result.toBool())
        app.processEvents()
        state=json.loads(engine.evaluate('fixture.snapshot()').toString())
        self.assertFalse(state['visible'])
        self.assertEqual(engine.evaluate('fixture.commands.join(",")').toString(),'restore')
        result=engine.evaluate('fixture.candidate.openAt(null)')
        self.assertFalse(result.isError(),result.toString());self.assertFalse(result.toBool())
        self.assertFalse(json.loads(engine.evaluate('fixture.snapshot()').toString())['visible'])
        engine.rootObjects()[0].close();engine.deleteLater();app.processEvents()
        self.assertFalse(warnings,'\n'.join(warnings))

if __name__=='__main__':unittest.main()
