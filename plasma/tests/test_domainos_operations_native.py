#!/usr/bin/env python3
# SPDX-License-Identifier: GPL-3.0-or-later
"""P04 X11 native-window proof with an owned Xvfb/Openbox, no personal windows.
Run through xvfb-run. Task actions still use model doubles, not real windows.
"""
import os
import json
import configparser
from pathlib import Path
import subprocess
import unittest

native_display = os.environ.get('DISPLAY')
if not native_display:
    raise SystemExit('Run using xvfb-run -a python3 '+__file__)
import test_domainos_operations_handoff as handoff
os.environ.update(DISPLAY=native_display, QT_QPA_PLATFORM='xcb')
from PyQt6.QtCore import QPointF, Qt
from PyQt6.QtQuick import QQuickWindow
from PyQt6.QtTest import QTest

handoff.FIXTURE=handoff.FIXTURE.replace('id:fixture', '''id:fixture
 QtObject {
  id:roles
  property color window: "#eeeeee"
  property color windowText: "#111111"
  property color base: "#ffffff"
  property color text: "#111111"
  property color button: "#dddddd"
  property color buttonText: "#111111"
  property color highlight: "#336699"
  property color highlightedText: "#ffffff"
 }
 property alias testRoles:roles
''')

def evidence_dir():
    path=Path(os.environ.get('P04_NATIVE_EVIDENCE',
        Path(handoff.setup._private.name)/'domainos-operations-native-evidence'))
    path.mkdir(mode=0o700,parents=True,exist_ok=True)
    return path


class NativeOperations(handoff.OperationsHandoff):
    def test_palette_roles_and_pressed_state(self):
        self.evaluate('fixture.iconbox.domainosPalette.system=fixture.testRoles;fixture.iconbox.domainosPalette.followSystem=true')
        schemes={
            'DomainOS':handoff.setup.ROOT/'colors/DomainOS-SR10.4.colors',
            'neutral':Path('/usr/share/color-schemes/BreezeLight.colors'),
            'dark':Path('/usr/share/color-schemes/BreezeDark.colors')}
        inputs=[]
        for name,path in schemes.items():
            cfg=configparser.ConfigParser();cfg.read(path)
            def role(section,key):
                parts=[int(v) for v in cfg[section][key].split(',')]
                return '#'+''.join(f'{v:02x}' for v in parts[:3])
            inputs.append((name,{'window':role('Colors:Window','BackgroundNormal'),
                'windowText':role('Colors:Window','ForegroundNormal'),
                'base':role('Colors:View','BackgroundNormal'),
                'text':role('Colors:View','ForegroundNormal'),
                'button':role('Colors:Button','BackgroundNormal'),
                'buttonText':role('Colors:Button','ForegroundNormal'),
                'highlight':role('Colors:Selection','BackgroundNormal'),
                'highlightedText':role('Colors:Selection','ForegroundNormal')}))
        inputs.append(('yellow-collision',dict(inputs[1][1],window='#eeee44',highlight='#dddd28',highlightedText='#111111')))
        evidence=[]
        for name,roles in inputs:
            for key,value in roles.items(): self.evaluate('fixture.testRoles.'+key+'='+json.dumps(value))
            self.evaluate('fixture.selectTwo();fixture.finish()');self.wait_for_operations();self.settle(100)
            row=self.item('domainosBatchColumns');owner=row.window()
            self.item('domainosBatchRows').forceActiveFocus();self.settle()
            label=row.property('contentItem');background=row.property('background')
            self.assertEqual(label.property('color').name(),roles['windowText'])
            row.forceActiveFocus();self.settle()
            self.assertEqual(label.property('color').name(),roles['highlightedText'])
            self.assertEqual(background.property('face').name(),roles['highlight'])
            point=row.mapToScene(QPointF(row.width()/2,row.height()/2)).toPoint()
            QTest.mousePress(owner,Qt.MouseButton.LeftButton,Qt.KeyboardModifier.NoModifier,point);self.settle()
            self.assertTrue(row.property('down'));self.assertTrue(background.property('sunken'))
            output=evidence_dir()
            self.assertTrue(owner.grabWindow().save(str(output/(name+'.png'))))
            evidence.append({'scheme':name,'text':label.property('color').name(),'face':background.property('face').name(),'pressed':True})
            # Release outside the row: no operation should be dispatched.
            QTest.mouseRelease(owner,Qt.MouseButton.LeftButton,Qt.KeyboardModifier.NoModifier,row.mapToScene(QPointF(-5,-5)).toPoint());self.settle()
            row.setProperty('enabled',False);self.settle()
            self.assertEqual(label.property('color').name(),roles['windowText'])
            self.assertAlmostEqual(label.property('opacity'),.6)
            self.evaluate('fixture.closeMenus()');self.settle()
        self.assertFalse(self.state()['layouts'])
        print('PALETTE_EVIDENCE '+json.dumps(evidence),flush=True)

    def test_position_and_native_keyboard(self):
        self.window.setPosition(120,250)
        self.window.requestActivate();self.settle(100)
        self.evaluate('fixture.showGroup(false);fixture.selectTwo()')
        self.settle(50)
        button=self.item('domainosGroupOrganize')
        origin=button.mapToGlobal(QPointF(0,0))
        self.click('domainosGroupOrganize')
        self.wait_for_operations();self.settle(150)
        menu=self.window.property('iconbox').property('batchContextMenu')
        owner=self.item('domainosBatchColumns').window()
        self.assertLessEqual(owner.y()+owner.height(),origin.y())
        self.assertLessEqual(origin.y()-(owner.y()+owner.height()),8)
        self.assertGreaterEqual(owner.x(),0)
        self.assertLessEqual(owner.x()+owner.width(),owner.screen().geometry().right()+1)
        self.assertIsNotNone(owner.activeFocusItem())
        self.assertTrue(owner.grabWindow().save(str(evidence_dir()/'operations-button-open.png')))
        QTest.keyClick(owner,Qt.Key.Key_Down);self.settle()
        self.assertEqual(menu.property('currentIndex'),3)
        QTest.keyClick(owner,Qt.Key.Key_Escape);self.settle()
        self.assertFalse(self.state()['operations'])

    def test_native_deactivation_closes(self):
        self.evaluate('fixture.showGroup(false);fixture.selectTwo();fixture.finish()')
        self.wait_for_operations();self.settle(100)
        owner=self.item('domainosBatchColumns').window()
        self.assertTrue(owner.isActive())
        other=QQuickWindow();other.setTitle('Owned deactivation target')
        other.resize(100,100);other.setPosition(850,40);other.show();other.requestActivate()
        try:
            self.settle(150)
            self.assertTrue(other.isActive())
            self.assertFalse(self.state()['operations'])
        finally:
            other.close();other.deleteLater();self.app.processEvents()

if __name__=='__main__':
    with open(handoff.setup.Path(handoff.setup._private.name)/'openbox.log','w') as log:
        wm=subprocess.Popen(['openbox','--sm-disable'],stdout=log,stderr=log)
        try:
            import time
            time.sleep(.3)
            if wm.poll() is not None:
                log.flush()
                print((handoff.setup.Path(handoff.setup._private.name)/'openbox.log').read_text())
                raise RuntimeError('Owned Openbox failed')
            suite=unittest.TestSuite(NativeOperations(name) for name in
                ['test_position_and_native_keyboard','test_native_deactivation_closes','test_palette_roles_and_pressed_state'])
            result=unittest.TextTestRunner(verbosity=2).run(suite)
        finally:
            wm.terminate();wm.wait(timeout=5)
    raise SystemExit(0 if result.wasSuccessful() else 1)
